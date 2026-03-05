"""
WSL client for Windows Screen Capture Service.

Connects to Windows service via AF_UNIX socket (through Windows named pipes)
and captures screen frames as JPEG images.
"""

import asyncio
import struct
from dataclasses import dataclass
from pathlib import Path
from loguru import logger
from typing import Optional


@dataclass
class CaptureClientConfig:
    """Configuration for capture client."""
    
    # Windows socket path (accessible from WSL via /mnt/wslg/ or TCP)
    socket_path: str = "/tmp/nanobot-capture.sock"
    # Connection timeout (seconds)
    timeout_seconds: int = 5
    # Maximum reconnection attempts
    max_retries: int = 3
    # Reconnection delay (seconds)
    reconnect_delay: float = 0.5


class CaptureClient:
    """
    Client for Windows Screen Capture Service.
    
    Usage:
        config = CaptureClientConfig()
        client = CaptureClient(config)
        
        # Capture screen
        path = await client.capture("/tmp/screen.jpg")
        
        # Close connection
        await client.close()
    """
    
    def __init__(self, config: Optional[CaptureClientConfig] = None):
        self.config = config or CaptureClientConfig()
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._reconnect_attempts = 0
        self._lock = asyncio.Lock()
        
        logger.debug(f"CaptureClient initialized with socket: {self.config.socket_path}")
    
    async def _ensure_connected(self) -> None:
        """Establish or restore connection to Windows service."""
        async with self._lock:
            if self._writer is not None:
                return
            
            try:
                logger.info(f"Connecting to {self.config.socket_path}...")
                
                # Try AF_UNIX socket first
                try:
                    self._reader, self._writer = await asyncio.open_unix_connection(
                        self.config.socket_path
                    )
                    logger.info("Connected via AF_UNIX socket")
                except FileNotFoundError:
                    # Fallback: Try TCP connection to Windows service
                    # Windows service can be configured to listen on TCP
                    host = "127.0.0.1"
                    port = 18791
                    logger.info(f"AF_UNIX not available, trying TCP {host}:{port}...")
                    self._reader, self._writer = await asyncio.open_connection(host, port)
                    logger.info(f"Connected via TCP {host}:{port}")
                
                self._reconnect_attempts = 0
                
            except FileNotFoundError:
                raise RuntimeError(
                    f"Windows capture service not running. "
                    f"Socket not found: {self.config.socket_path}. "
                    f"Please run: powershell.exe -File install-service.ps1"
                )
            except ConnectionRefusedError:
                raise RuntimeError(
                    f"Windows capture service refused connection. "
                    f"Please ensure the service is running on Windows."
                )
            except Exception as e:
                raise RuntimeError(f"Failed to connect: {e}")
    
    async def capture(self, output_path: str) -> str:
        """
        Capture screen and save to file.
        
        Args:
            output_path: Path to save the JPEG image (WSL path)
        
        Returns:
            Path to the saved image
        
        Raises:
            RuntimeError: If service is unavailable
        """
        await self._ensure_connected()
        
        try:
            # Send CAPTURE command
            # Protocol: 4 bytes command length + command string
            cmd = b"CAPTURE"
            cmd_len = struct.pack(">I", len(cmd))
            
            self._writer.write(cmd_len + cmd)
            await self._writer.drain()
            
            # Read response header (4 bytes: data length)
            header = await self._reader.readexactly(4)
            data_length = struct.unpack(">I", header)[0]
            
            if data_length == 0:
                raise RuntimeError("Service returned empty frame")
            
            # Read JPEG data
            jpeg_data = await self._reader.readexactly(data_length)
            
            # Save to file
            output = Path(output_path)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(jpeg_data)
            
            logger.debug(f"Captured {len(jpeg_data)} bytes to {output}")
            
            return str(output)
            
        except (ConnectionResetError, BrokenPipeError, asyncio.IncompleteReadError) as e:
            # Connection lost
            logger.warning(f"Connection lost: {e}")
            self._writer = None
            self._reconnect_attempts += 1
            
            if self._reconnect_attempts > self.config.max_retries:
                raise RuntimeError(
                    f"Max reconnection attempts exceeded ({self.config.max_retries})"
                )
            
            # Retry after delay
            logger.info(f"Reconnecting (attempt {self._reconnect_attempts}/{self.config.max_retries})...")
            await asyncio.sleep(self.config.reconnect_delay)
            return await self.capture(output_path)
        
        except Exception as e:
            logger.error(f"Capture failed: {e}")
            raise
    
    async def capture_to_memory(self) -> bytes:
        """
        Capture screen and return as bytes (without saving to file).
        
        Returns:
            JPEG image bytes
        """
        await self._ensure_connected()
        
        try:
            # Send CAPTURE command
            cmd = b"CAPTURE"
            cmd_len = struct.pack(">I", len(cmd))
            
            self._writer.write(cmd_len + cmd)
            await self._writer.drain()
            
            # Read response header
            header = await self._reader.readexactly(4)
            data_length = struct.unpack(">I", header)[0]
            
            if data_length == 0:
                raise RuntimeError("Service returned empty frame")
            
            # Read JPEG data
            jpeg_data = await self._reader.readexactly(data_length)
            
            logger.debug(f"Captured {len(jpeg_data)} bytes to memory")
            
            return jpeg_data
            
        except Exception as e:
            logger.error(f"Capture to memory failed: {e}")
            raise
    
    async def ping(self) -> bool:
        """
        Check if service is responsive.
        
        Returns:
            True if service responds to PING
        """
        await self._ensure_connected()
        
        try:
            # Send PING command
            cmd = b"PING"
            cmd_len = struct.pack(">I", len(cmd))
            
            self._writer.write(cmd_len + cmd)
            await self._writer.drain()
            
            # Read response
            header = await self._reader.readexactly(4)
            data_length = struct.unpack(">I", header)[0]
            
            response = await self._reader.readexactly(data_length)
            
            return response == b"PONG"
            
        except Exception as e:
            logger.error(f"Ping failed: {e}")
            return False
    
    async def close(self) -> None:
        """Close connection to service."""
        async with self._lock:
            if self._writer:
                try:
                    # Send QUIT command
                    cmd = b"QUIT"
                    cmd_len = struct.pack(">I", len(cmd))
                    self._writer.write(cmd_len + cmd)
                    await self._writer.drain()
                except Exception:
                    pass
                
                try:
                    self._writer.close()
                    await self._writer.wait_closed()
                except Exception:
                    pass
                
                self._writer = None
                self._reader = None
                logger.debug("Connection closed")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_connected()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Convenience function for synchronous usage
def capture_screen_sync(output_path: str = "/tmp/screen.jpg") -> str:
    """
    Synchronous wrapper for capture.
    
    Args:
        output_path: Path to save the JPEG image
    
    Returns:
        Path to the saved image
    """
    config = CaptureClientConfig()
    client = CaptureClient(config)
    
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(client.capture(output_path))
    finally:
        try:
            loop.run_until_complete(client.close())
        except Exception:
            pass
