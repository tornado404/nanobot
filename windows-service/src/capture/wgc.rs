// capture/wgc.rs - Windows.Graphics.Capture implementation

use anyhow::{Context, Result};
use log::{debug, error, info};
use windows::core::{ComInterface, IInspectable, IUnknown};
use windows::{
    Foundation::Numerics::Vector2,
    Foundation::Size,
    Graphics::Capture::*,
    Graphics::DirectX::*,
    Graphics::DirectX::Direct3D11::*,
    Win32::Foundation::*,
    Win32::Graphics::Direct3D::D3D_DRIVER_TYPE_HARDWARE,
    Win32::Graphics::Direct3D11::*,
    Win32::Graphics::Dxgi::*,
    Win32::Graphics::Dxgi::Common::{DXGI_FORMAT_B8G8R8A8_UNORM, DXGI_SAMPLE_DESC},
    Win32::System::Com::*,
    Win32::System::Threading::*,
    Win32::System::WinRT::Direct3D11::CreateDirect3D11DeviceFromDXGIDevice,
    Win32::System::WinRT::Graphics::Capture::IGraphicsCaptureItemInterop,
    Win32::Graphics::Gdi::{MonitorFromPoint, MONITOR_DEFAULTTOPRIMARY, HMONITOR},
};

/// Windows Graphics Capture wrapper
pub struct WindowsGraphicsCapture {
    device: ID3D11Device,
    context: ID3D11DeviceContext,
    item: GraphicsCaptureItem,
    frame_pool: Direct3D11CaptureFramePool,
    session: GraphicsCaptureSession,
    width: u32,
    height: u32,
}

impl WindowsGraphicsCapture {
    /// Initialize Windows Graphics Capture for the entire desktop
    pub fn new() -> Result<Self> {
        // Initialize COM (required for WinRT)
        unsafe {
            CoInitializeEx(None, COINIT_MULTITHREADED)
                .ok()
                .context("Failed to initialize COM")?;
        }

        info!("Initializing Windows.Graphics.Capture...");

        // 1. Create D3D11 device with BGRA support
        let device = Self::create_d3d11_device()?;
        let context = unsafe { device.GetImmediateContext()? };
        
        // Create WinRT Direct3D device from D3D11 device
        let dxgi_device = device.cast::<IDXGIDevice>()?;
        let d3d_device_inspectable = unsafe { CreateDirect3D11DeviceFromDXGIDevice(&dxgi_device)? };
        let d3d_device: IDirect3DDevice = d3d_device_inspectable.cast()?;

        // 2. Get the primary monitor's GraphicsCaptureItem
        let item = Self::create_capture_item_for_monitor()?;
        
        // 3. Get item size
        let size = item.Size()?;
        let width = size.Width as u32;
        let height = size.Height as u32;

        info!("Capture item size: {}x{}", width, height);

        // 4. Create frame pool (free-threaded for better performance)
        let frame_pool = Direct3D11CaptureFramePool::CreateFreeThreaded(
            &d3d_device,
            DirectXPixelFormat::B8G8R8A8UIntNormalized,
            2, // buffer count
            size,
        )?;

        // 5. Create capture session
        let session = frame_pool.CreateCaptureSession(&item)?;

        // 6. Configure session (Windows 10 1809+)
        // Note: These may not be available on all versions
        #[cfg(feature = "win10_1809")]
        {
            let _ = session.SetIsCursorCaptureEnabled(true);
            let _ = session.SetIsBorderRequired(false);
        }

        // 7. Start capture
        session.StartCapture()?;

        info!("Windows.Graphics.Capture initialized successfully");

        Ok(Self {
            device,
            context,
            item,
            frame_pool,
            session,
            width,
            height,
        })
    }

    /// Create D3D11 device for capture
    fn create_d3d11_device() -> Result<ID3D11Device> {
        unsafe {
            let mut device: Option<ID3D11Device> = None;
            let mut context: Option<ID3D11DeviceContext> = None;

            D3D11CreateDevice(
                None,
                D3D_DRIVER_TYPE_HARDWARE,
                None,
                D3D11_CREATE_DEVICE_BGRA_SUPPORT,
                None,
                D3D11_SDK_VERSION,
                Some(&mut device),
                None,
                Some(&mut context),
            )
            .ok()
            .context("Failed to create D3D11 device")?;

            device.ok_or_else(|| anyhow::anyhow!("Device creation failed"))
        }
    }

    /// Create capture item for the primary monitor
    fn create_capture_item_for_monitor() -> Result<GraphicsCaptureItem> {
        // Get primary monitor handle
        let point = POINT { x: 0, y: 0 };
        let monitor = unsafe { MonitorFromPoint(point, MONITOR_DEFAULTTOPRIMARY) };
        
        if monitor.is_invalid() {
            anyhow::bail!("Failed to get primary monitor handle");
        }

        // Create GraphicsCaptureItem from monitor handle using interop
        let interop = windows::core::factory::<GraphicsCaptureItem, IGraphicsCaptureItemInterop>()?;
        let item: GraphicsCaptureItem = unsafe { interop.CreateForMonitor(monitor) }?;
        
        let name = item.DisplayName().unwrap_or_default();
        debug!("Found capture item: {}", name);
        
        Ok(item)
    }

    /// Capture a single frame and return BGRA data
    pub fn capture_frame(&mut self) -> Result<Vec<u8>> {
        // 1. Try to get the next frame (100ms timeout)
        let frame = match self.frame_pool.TryGetNextFrame() {
            Ok(frame) => frame,
            Err(e) => {
                // Check if it's a timeout or other error
                // In some versions, TryGetNextFrame might return null/None equivalent via error?
                // Actually, Windows 0.52 TryGetNextFrame returns Result<Direct3D11CaptureFrame>
                // If no frame is available, it might block or throw.
                // However, usually it blocks until frame arrives or returns error.
                // If we want non-blocking, we need to handle FrameArrived event, 
                // but here we are polling.
                error!("Failed to get frame: {:?}", e);
                return Err(anyhow::anyhow!("Frame acquisition failed: {:?}", e));
            }
        };

        // 2. Get the surface texture
        let surface = frame.Surface()?;

        // 3. Cast to D3D11 texture
        let texture = {
            let dxgi_surface = surface.cast::<IDXGISurface>()?;
            
            // Get the D3D11 texture from the DXGI surface
            unsafe {
                let device_any = self.device.cast::<IUnknown>()?;
                let resource: ID3D11Resource = dxgi_surface.cast()?;
                
                // Copy to staging texture for CPU access
                let staging = self.create_staging_texture()?;
                self.context.CopyResource(&staging, &resource);
                
                staging
            }
        };

        // 4. Map the staging texture to CPU memory
        let mapped = unsafe {
            let mut mapped = D3D11_MAPPED_SUBRESOURCE::default();
            self.context.Map(&texture, 0, D3D11_MAP_READ, 0, Some(&mut mapped))?;
            mapped
        };

        // 5. Copy BGRA data
        let row_pitch = mapped.RowPitch as usize;
        let data_slice = unsafe {
            std::slice::from_raw_parts(
                mapped.pData as *const u8,
                row_pitch * self.height as usize,
            )
        };

        // 6. Convert to contiguous BGRA (remove padding)
        let bgra_data = self.remove_padding(data_slice, row_pitch)?;

        // 7. Unmap
        unsafe {
            self.context.Unmap(&texture, 0);
        }

        debug!("Captured frame: {} bytes", bgra_data.len());

        Ok(bgra_data)
    }

    /// Create staging texture for CPU access
    fn create_staging_texture(&self) -> Result<ID3D11Texture2D> {
        let desc = D3D11_TEXTURE2D_DESC {
            Width: self.width,
            Height: self.height,
            MipLevels: 1,
            ArraySize: 1,
            Format: DXGI_FORMAT_B8G8R8A8_UNORM,
            SampleDesc: DXGI_SAMPLE_DESC {
                Count: 1,
                Quality: 0,
            },
            Usage: D3D11_USAGE_STAGING,
            BindFlags: 0,
            CPUAccessFlags: D3D11_CPU_ACCESS_READ.0 as u32,
            MiscFlags: 0,
        };

        unsafe {
            let mut texture = None;
            self.device
                .CreateTexture2D(&desc, None, Some(&mut texture))
                .context("Failed to create staging texture")?;
            
            texture.ok_or_else(|| anyhow::anyhow!("Created texture is null"))
        }
    }

    /// Remove row padding from BGRA data
    fn remove_padding(&self, data: &[u8], row_pitch: usize) -> Result<Vec<u8>> {
        let stride = self.width as usize * 4; // BGRA = 4 bytes per pixel
        
        if row_pitch == stride {
            // No padding
            return Ok(data.to_vec());
        }

        let mut result = Vec::with_capacity(stride * self.height as usize);
        
        for row in 0..self.height as usize {
            let start = row * row_pitch;
            let end = start + stride;
            result.extend_from_slice(&data[start..end]);
        }

        Ok(result)
    }

    /// Get capture dimensions
    pub fn width(&self) -> u32 {
        self.width
    }

    pub fn height(&self) -> u32 {
        self.height
    }
}

impl Drop for WindowsGraphicsCapture {
    fn drop(&mut self) {
        info!("Shutting down Windows.Graphics.Capture...");
        
        // Stop capture session
        let _ = self.session.Close();
        
        // Close frame pool
        let _ = self.frame_pool.Close();
        
        debug!("Windows.Graphics.Capture shut down");
    }
}
