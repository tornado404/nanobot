// encoder/jpeg.rs - JPEG encoder using image crate

use anyhow::{Context, Result};
use image::{ImageBuffer, ColorType, ImageFormat};
use log::debug;
use std::io::Cursor;

/// JPEG encoder configuration
#[derive(Debug, Clone)]
pub struct JpegEncoderConfig {
    /// JPEG quality (1-100)
    pub quality: u8,
    /// Image width
    pub width: u32,
    /// Image height
    pub height: u32,
}

impl Default for JpegEncoderConfig {
    fn default() -> Self {
        Self {
            quality: 85,
            width: 1920,
            height: 1080,
        }
    }
}

/// JPEG encoder using image crate
pub struct JpegEncoder {
    pub config: JpegEncoderConfig,
}

impl JpegEncoder {
    /// Create a new JPEG encoder
    pub fn new(config: JpegEncoderConfig) -> Self {
        Self { config }
    }

    /// Create encoder with default config
    pub fn with_defaults() -> Self {
        Self::new(JpegEncoderConfig::default())
    }

    /// Encode BGRA data to JPEG
    /// 
    /// # Arguments
    /// * `bgra_data` - Raw BGRA pixel data (width * height * 4 bytes)
    /// 
    /// # Returns
    /// * `Vec<u8>` - JPEG encoded bytes
    pub fn encode(&self, bgra_data: &[u8]) -> Result<Vec<u8>> {
        debug!(
            "Encoding {}x{} frame ({} bytes) to JPEG",
            self.config.width,
            self.config.height,
            bgra_data.len()
        );

        // 1. Create RGB image from BGRA data
        // image crate expects RGB, but DXGI gives us BGRA
        let rgb_data = self.bgra_to_rgb(bgra_data);

        // 2. Create ImageBuffer
        let img: ImageBuffer<image::Rgb<u8>, Vec<u8>> = ImageBuffer::from_raw(
            self.config.width,
            self.config.height,
            rgb_data,
        )
        .context("Failed to create image buffer")?;

        // 3. Encode to JPEG
        let mut jpeg_data = Cursor::new(Vec::new());
        
        let mut jpeg_encoder = image::codecs::jpeg::JpegEncoder::new_with_quality(
            &mut jpeg_data,
            self.config.quality,
        );

        jpeg_encoder
            .encode(
                img.as_raw(),
                self.config.width,
                self.config.height,
                ColorType::Rgb8,
            )
            .context("Failed to encode JPEG")?;

        let result = jpeg_data.into_inner();

        debug!(
            "JPEG encoded: {} bytes (compression ratio: {:.2}x)",
            result.len(),
            bgra_data.len() as f64 / result.len() as f64
        );

        Ok(result)
    }

    /// Convert BGRA to RGB
    fn bgra_to_rgb(&self, bgra: &[u8]) -> Vec<u8> {
        let pixel_count = bgra.len() / 4;
        let mut rgb = Vec::with_capacity(pixel_count * 3);

        for chunk in bgra.chunks_exact(4) {
            // BGRA -> RGB (skip alpha)
            rgb.push(chunk[2]); // R
            rgb.push(chunk[1]); // G
            rgb.push(chunk[0]); // B
        }

        rgb
    }

    /// Update quality setting
    pub fn set_quality(&mut self, quality: u8) {
        self.config.quality = quality.clamp(1, 100);
        debug!("JPEG quality set to {}", self.config.quality);
    }

    /// Update dimensions
    pub fn set_dimensions(&mut self, width: u32, height: u32) {
        self.config.width = width;
        self.config.height = height;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_jpeg_encoder() {
        let encoder = JpegEncoder::with_defaults();
        
        // Create test BGRA data (red square)
        let width = 100;
        let height = 100;
        let mut bgra = Vec::new();
        
        for _ in 0..(width * height) {
            bgra.extend_from_slice(&[0, 0, 255, 255]); // BGRA: Red
        }

        let jpeg_data = encoder.encode(&bgra).unwrap();
        
        assert!(jpeg_data.len() < bgra.len(), "JPEG should be smaller than BGRA");
        assert!(jpeg_data.len() > 0, "JPEG data should not be empty");
    }
}
