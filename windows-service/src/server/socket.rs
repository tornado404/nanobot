// server/socket.rs - AF_UNIX socket server for WSL communication

use anyhow::{Context, Result};
use log::{debug, error, info, warn};
use std::path::Path;
use std::sync::Arc;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::windows::named_pipe::{ServerOptions, NamedPipeServer};
use tokio::sync::Mutex;

use crate::capture::WindowsGraphicsCapture;
use crate::encoder::JpegEncoder;

/// Capture server configuration
#[derive(Debug, Clone)]
pub struct ServerConfig {
    /// Socket path (Windows named pipe path for AF_UNIX compatibility)
    pub socket_path: String,
    /// JPEG quality (1-100)
    pub jpeg_quality: u8,
    /// Maximum concurrent connections
    pub max_connections: usize,
}

impl Default for ServerConfig {
    fn default() -> Self {
        Self {
            // Use Windows named pipe path that WSL can access via /mnt/wslg/
            socket_path: "\\\\.\\pipe\\nanobot-capture".to_string(),
            jpeg_quality: 85,
            max_connections: 5,
        }
    }
}

/// Capture server - handles incoming capture requests
#[derive(Clone)]
pub struct CaptureServer {
    config: ServerConfig,
    capture: Arc<Mutex<WindowsGraphicsCapture>>,
    encoder: Arc<Mutex<JpegEncoder>>,
    running: Arc<Mutex<bool>>,
}

impl CaptureServer {
    /// Create a new capture server
    pub fn new(config: ServerConfig) -> Result<Self> {
        info!("Initializing capture server...");

        // Initialize capture
        let capture = WindowsGraphicsCapture::new()
            .context("Failed to initialize Windows Graphics Capture")?;

        // Initialize encoder with capture dimensions
        let mut encoder = JpegEncoder::with_defaults();
        encoder.set_dimensions(capture.width(), capture.height());

        info!(
            "Capture server initialized: {}x{} @ quality {}",
            capture.width(),
            capture.height(),
            config.jpeg_quality
        );

        Ok(Self {
            config,
            capture: Arc::new(Mutex::new(capture)),
            encoder: Arc::new(Mutex::new(encoder)),
            running: Arc::new(Mutex::new(false)),
        })
    }

    /// Start the server
    pub async fn run(&self) -> Result<()> {
        let mut running = self.running.lock().await;
        *running = true;
        drop(running);

        info!("Starting Named Pipe server on {}", self.config.socket_path);

        // Create first instance of named pipe server
        let mut server = ServerOptions::new()
            .first_pipe_instance(true)
            .create(&self.config.socket_path)
            .context("Failed to create named pipe server")?;

        info!("Server listening for connections...");

        let mut connection_count = 0;

        loop {
            // Wait for connection
            if let Err(e) = server.connect().await {
                error!("Connect error: {:?}", e);
                // Try to recover by recreating server instance?
                // Or just break loop? usually we recreate.
                tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
                continue;
            }

            // Connection established
            connection_count += 1;
            debug!("Client connected (total: {})", connection_count);

            // Construct next server instance before moving current one to handler
            let next_server = match ServerOptions::new()
                .create(&self.config.socket_path) 
            {
                Ok(s) => s,
                Err(e) => {
                    error!("Failed to create next server instance: {:?}", e);
                    break;
                }
            };

            // Current connected server instance
            let client = server;
            server = next_server;

            // Clone Arcs for the connection handler
            let capture = Arc::clone(&self.capture);
            let encoder = Arc::clone(&self.encoder);

            // Spawn handler task
            tokio::spawn(async move {
                if let Err(e) = Self::handle_connection(client, capture, encoder).await {
                    error!("Connection handler error: {:?}", e);
                }
            });

            // Check if we should stop
            if !*self.running.lock().await {
                info!("Server shutting down...");
                break;
            }
        }

        Ok(())
    }

    /// Handle a single client connection
    async fn handle_connection(
        stream: NamedPipeServer,
        capture: Arc<Mutex<WindowsGraphicsCapture>>,
        encoder: Arc<Mutex<JpegEncoder>>,
    ) -> Result<()> {
        let (mut reader, mut writer) = tokio::io::split(stream);

        loop {
            // Read command (4 bytes for command length + command)
            let mut cmd_len_buf = [0u8; 4];
            
            match reader.read_exact(&mut cmd_len_buf).await {
                Ok(_) => {}
                Err(e) => {
                    if e.kind() != std::io::ErrorKind::UnexpectedEof {
                        warn!("Client disconnected: {:?}", e);
                    }
                    break;
                }
            }

            let cmd_len = u32::from_be_bytes(cmd_len_buf) as usize;
            
            // Read command
            let mut cmd_buf = vec![0u8; cmd_len];
            reader.read_exact(&mut cmd_buf).await?;
            
            let command = String::from_utf8_lossy(&cmd_buf);
            debug!("Received command: {}", command.trim());

            // Process command
            match command.trim() {
                "CAPTURE" => {
                    match Self::handle_capture(&capture, &encoder).await {
                        Ok(jpeg_data) => {
                            // Send response: 4 bytes length + JPEG data
                            let len_bytes = (jpeg_data.len() as u32).to_be_bytes();
                            writer.write_all(&len_bytes).await?;
                            writer.write_all(&jpeg_data).await?;
                            writer.flush().await?;
                            
                            debug!("Sent {} byte JPEG frame", jpeg_data.len());
                        }
                        Err(e) => {
                            error!("Capture error: {:?}", e);
                            // Send error response (0 length)
                            let len_bytes = 0u32.to_be_bytes();
                            writer.write_all(&len_bytes).await?;
                        }
                    }
                }
                "PING" => {
                    // Health check
                    writer.write_all(b"PONG").await?;
                    writer.flush().await?;
                }
                "QUIT" => {
                    info!("Client requested disconnect");
                    break;
                }
                cmd => {
                    warn!("Unknown command: {}", cmd);
                    // Send error response
                    let error_msg = b"Unknown command";
                    let len_bytes = (error_msg.len() as u32).to_be_bytes();
                    writer.write_all(&len_bytes).await?;
                    writer.write_all(error_msg).await?;
                }
            }
        }

        Ok(())
    }

    /// Handle CAPTURE command
    async fn handle_capture(
        capture: &Mutex<WindowsGraphicsCapture>,
        encoder: &Mutex<JpegEncoder>,
    ) -> Result<Vec<u8>> {
        // Capture frame
        let bgra_data = {
            let mut capture = capture.lock().await;
            capture.capture_frame()?
        };

        // Encode to JPEG
        let jpeg_data = {
            let encoder = encoder.lock().await;
            encoder.encode(&bgra_data)?
        };

        Ok(jpeg_data)
    }

    /// Stop the server
    pub async fn stop(&self) {
        let mut running = self.running.lock().await;
        *running = false;
        info!("Server stop requested");
    }

    /// Check if server is running
    pub async fn is_running(&self) -> bool {
        *self.running.lock().await
    }

    /// Get current JPEG quality
    pub async fn get_quality(&self) -> u8 {
        self.encoder.lock().await.config.quality
    }

    /// Update JPEG quality
    pub async fn set_quality(&self, quality: u8) {
        let mut encoder = self.encoder.lock().await;
        encoder.set_quality(quality);
        info!("JPEG quality updated to {}", quality);
    }
}

impl Drop for CaptureServer {
    fn drop(&mut self) {
        // Clean up socket file
        let path = Path::new(&self.config.socket_path);
        if path.exists() {
            let _ = std::fs::remove_file(path);
            debug!("Socket file cleaned up");
        }
    }
}
