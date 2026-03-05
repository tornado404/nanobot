// main.rs - nanobot Windows Screen Capture Service
// 
// This service captures the Windows desktop using Windows.Graphics.Capture API
// and streams JPEG frames to WSL via AF_UNIX socket.

mod capture;
mod encoder;
mod server;

use anyhow::{Context, Result};
use log::{error, info, LevelFilter};
use std::env;
use std::path::Path;
use tokio::signal;
use tokio::sync::broadcast;

use crate::server::{CaptureServer, ServerConfig};

/// Service configuration loaded from environment or config file
#[derive(Debug, Clone)]
struct Config {
    socket_path: String,
    jpeg_quality: u8,
    log_level: String,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            socket_path: env::var("NANOBOT_SOCKET_PATH")
                .unwrap_or_else(|_| "\\\\.\\pipe\\nanobot-capture".to_string()),
            jpeg_quality: env::var("NANOBOT_JPEG_QUALITY")
                .ok()
                .and_then(|s| s.parse().ok())
                .unwrap_or(85),
            log_level: env::var("NANOBOT_LOG_LEVEL")
                .unwrap_or_else(|_| "info".to_string()),
        }
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize logging
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info"))
        .format(|buf, record| {
            use std::io::Write;
            writeln!(
                buf,
                "{} [{}] {}",
                chrono::Local::now().format("%Y-%m-%d %H:%M:%S"),
                record.level(),
                record.args()
            )
        })
        .init();

    info!("╔════════════════════════════════════════════════════════╗");
    info!("║  nanobot Windows Screen Capture Service                ║");
    info!("║  Using Windows.Graphics.Capture API                    ║");
    info!("╚════════════════════════════════════════════════════════╝");

    // Load configuration
    let config = Config::default();
    info!("Configuration:");
    info!("  Socket path: {}", config.socket_path);
    info!("  JPEG quality: {}", config.jpeg_quality);
    info!("  Log level: {}", config.log_level);

    // Create and start server
    let server_config = ServerConfig {
        socket_path: config.socket_path.clone(),
        jpeg_quality: config.jpeg_quality,
        max_connections: 5,
    };

    info!("Initializing capture server...");
    let server = CaptureServer::new(server_config)
        .context("Failed to create capture server")?;

    // Create shutdown channel
    let (shutdown_tx, mut shutdown_rx) = broadcast::channel::<()>(1);

    // Spawn server task
    let server_handle = {
        let server = server.clone();
        let mut shutdown_rx = shutdown_tx.subscribe();
        
        tokio::spawn(async move {
            tokio::select! {
                result = server.run() => {
                    if let Err(e) = result {
                        error!("Server error: {:?}", e);
                    }
                }
                _ = shutdown_rx.recv() => {
                    info!("Received shutdown signal");
                }
            }
        })
    };

    info!("Service started successfully");
    info!("Press Ctrl+C to stop...");

    // Wait for shutdown signal
    let shutdown_server = server.clone();
    tokio::spawn(async move {
        match signal::ctrl_c().await {
            Ok(()) => {
                info!("Ctrl+C detected");
                let _ = shutdown_tx.send(());
                shutdown_server.stop().await;
            }
            Err(e) => {
                error!("Failed to listen for shutdown signal: {:?}", e);
            }
        }
    });

    // Wait for server to complete
    let _ = server_handle.await;

    info!("Service stopped");
    info!("╔════════════════════════════════════════════════════════╗");
    info!("║  Goodbye! 👋                                           ║");
    info!("╚════════════════════════════════════════════════════════╝");

    Ok(())
}

// Add chrono dependency for timestamp formatting
// This needs to be added to Cargo.toml
