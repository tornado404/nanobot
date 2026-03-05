"""
WSLg Windows Screenshot Skill

在 WSL2 + WSLg 环境下，通过调用 Windows PowerShell 实现屏幕截图
"""

from .wslg_screenshot import WSLgScreenCapture, capture_screen, capture_and_ocr

__all__ = [
    'WSLgScreenCapture',
    'capture_screen',
    'capture_and_ocr',
]

__version__ = '1.0.0'
