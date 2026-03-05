"""
Agent tool for Windows screen capture.

Registers the capture_screen() tool with nanobot's tool registry.
"""

from pathlib import Path
from typing import Optional
from loguru import logger

from .capture_client import CaptureClient, CaptureClientConfig


async def capture_screen(
    output: str = "/tmp/screen_capture.jpg",
    ocr: bool = False,
    lang: str = "eng+chi_sim"
) -> dict:
    """
    Capture Windows desktop screen.
    
    This tool captures the current Windows desktop画面 and saves it as a JPEG image.
    Requires the Windows capture service to be running.
    
    Args:
        output: Output file path (default: /tmp/screen_capture.jpg)
        ocr: Whether to perform OCR on the captured image (default: False)
        lang: OCR language (default: eng+chi_sim)
    
    Returns:
        dict with keys:
            - path: Path to the saved image
            - ocr_text: OCR result (only if ocr=True)
            - width: Image width
            - height: Image height
    
    Raises:
        RuntimeError: If Windows capture service is not running
    """
    logger.info(f"Capturing screen to {output}...")
    
    config = CaptureClientConfig()
    client = CaptureClient(config)
    
    try:
        # Capture screen
        path = await client.capture(output)
        logger.info(f"Screen captured: {path}")
        
        result = {
            "path": path,
            "width": 0,
            "height": 0,
        }
        
        # Get image dimensions
        try:
            from PIL import Image
            with Image.open(path) as img:
                result["width"] = img.width
                result["height"] = img.height
        except Exception as e:
            logger.warning(f"Failed to get image dimensions: {e}")
        
        # Perform OCR if requested
        if ocr:
            try:
                import pytesseract
                from PIL import Image
                
                with Image.open(path) as img:
                    ocr_text = pytesseract.image_to_string(img, lang=lang)
                    result["ocr_text"] = ocr_text
                    logger.info(f"OCR completed: {len(ocr_text)} characters")
            except Exception as e:
                logger.error(f"OCR failed: {e}")
                result["ocr_text"] = f"OCR error: {e}"
        
        return result
        
    finally:
        await client.close()


async def capture_screen_to_memory() -> bytes:
    """
    Capture screen and return as bytes.
    
    Returns:
        JPEG image bytes
    """
    config = CaptureClientConfig()
    client = CaptureClient(config)
    
    try:
        jpeg_data = await client.capture_to_memory()
        logger.info(f"Captured {len(jpeg_data)} bytes to memory")
        return jpeg_data
    finally:
        await client.close()


async def check_service_status() -> dict:
    """
    Check if Windows capture service is running.
    
    Returns:
        dict with keys:
            - running: bool
            - message: str
    """
    config = CaptureClientConfig()
    client = CaptureClient(config)
    
    try:
        is_running = await client.ping()
        
        if is_running:
            return {
                "running": True,
                "message": "Windows capture service is running"
            }
        else:
            return {
                "running": False,
                "message": "Service responded but PING failed"
            }
            
    except Exception as e:
        return {
            "running": False,
            "message": f"Service unavailable: {e}"
        }
    finally:
        await client.close()


# Tool registration for nanobot
TOOL_DEFINITIONS = [
    {
        "name": "capture_screen",
        "description": "Capture Windows desktop screen as JPEG image",
        "function": capture_screen,
        "parameters": {
            "type": "object",
            "properties": {
                "output": {
                    "type": "string",
                    "description": "Output file path (default: /tmp/screen_capture.jpg)"
                },
                "ocr": {
                    "type": "boolean",
                    "description": "Whether to perform OCR on the captured image"
                },
                "lang": {
                    "type": "string",
                    "description": "OCR language (default: eng+chi_sim)"
                }
            }
        }
    },
    {
        "name": "check_capture_service",
        "description": "Check if Windows capture service is running",
        "function": check_service_status,
        "parameters": {}
    }
]
