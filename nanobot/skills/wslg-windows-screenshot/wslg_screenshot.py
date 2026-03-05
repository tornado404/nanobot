#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WSLg Windows Screenshot - 核心实现

在 WSL2 + WSLg 环境下，通过调用 Windows PowerShell 实现屏幕截图
"""

import os
import subprocess
import time
import shutil
from pathlib import Path
from typing import Optional, Dict, Tuple
from loguru import logger

# 配置日志
logger.add("/tmp/wslg_screenshot.log", rotation="10 MB", retention="7 days")


class WSLgScreenCapture:
    """WSLg 环境屏幕捕获工具 - 通过 Windows PowerShell 实现截图"""
    
    def __init__(
        self,
        output_dir: str = '/mnt/d/fe/nanobot/workspace',
        win_temp_dir: str = 'C:\\Windows\\Temp',
        display: str = ':0',
        xauthority: str = '/dev/null'
    ):
        """
        初始化 WSLgScreenCapture
        
        Args:
            output_dir: WSL 侧输出目录
            win_temp_dir: Windows 侧临时目录
            display: X11 DISPLAY 环境变量
            xauthority: XAUTHORITY 环境变量
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.win_temp_dir = win_temp_dir
        self.win_temp_path = win_temp_dir.replace('C:\\', '/mnt/c/').replace('\\', '/')
        
        # 设置环境变量
        os.environ['DISPLAY'] = display
        os.environ['XAUTHORITY'] = xauthority
        
        # PowerShell 路径
        self.powershell_path = '/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe'
        
        # 检查 PowerShell 是否可用
        if not Path(self.powershell_path).exists():
            logger.error(f"PowerShell 不存在：{self.powershell_path}")
            raise FileNotFoundError(f"PowerShell not found: {self.powershell_path}")
        
        logger.info(f"WSLgScreenCapture 初始化完成，输出目录：{self.output_dir}")
    
    def _win_to_wsl_path(self, win_path: str) -> str:
        """Windows 路径转 WSL 路径"""
        return win_path.replace('C:\\', '/mnt/c/').replace('\\', '/')
    
    def _wsl_to_win_path(self, wsl_path: str) -> str:
        """WSL 路径转 Windows 路径"""
        return wsl_path.replace('/mnt/c/', 'C:\\').replace('/', '\\')
    
    def capture_screen(self, output_name: str = 'screenshot.png') -> Optional[str]:
        """
        捕获全屏截图
        
        Args:
            output_name: 输出文件名（WSL 侧路径）
            
        Returns:
            截图文件路径（WSL 侧），失败返回 None
        """
        # Windows 侧临时文件路径
        win_filename = f"wslg_screen_{int(time.time())}.png"
        win_output_path = os.path.join(self.win_temp_dir, win_filename)
        wsl_output_path = self._win_to_wsl_path(win_output_path)
        
        # PowerShell 截图脚本
        ps_script = f"""
        Add-Type -AssemblyName System.Windows.Forms
        Add-Type -AssemblyName System.Drawing
        
        $screen = [System.Windows.Forms.Screen]::PrimaryScreen
        $bitmap = New-Object System.Drawing.Bitmap $screen.Bounds.Width, $screen.Bounds.Height
        $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
        $graphics.CopyFromScreen($screen.Bounds.X, $screen.Bounds.Y, 0, 0, $screen.Bounds.Size)
        $bitmap.Save('{win_output_path}')
        $graphics.Dispose()
        $bitmap.Dispose()
        
        Write-Host "Screenshot saved to: {win_output_path}"
        """
        
        logger.info(f"执行 PowerShell 截图：{win_output_path}")
        
        try:
            result = subprocess.run(
                [self.powershell_path, '-Command', ps_script],
                capture_output=True,
                timeout=30,
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode != 0:
                logger.error(f"PowerShell 执行失败：{result.stderr}")
                return None
            
            # 等待文件写入完成
            time.sleep(0.5)
            
            # 检查文件是否存在
            if not Path(wsl_output_path).exists():
                logger.error(f"截图文件不存在：{wsl_output_path}")
                return None
            
            # 复制到目标位置
            final_path = self.output_dir / output_name
            shutil.copy(wsl_output_path, final_path)
            
            # 清理临时文件
            try:
                Path(wsl_output_path).unlink()
            except Exception as e:
                logger.warning(f"清理临时文件失败：{e}")
            
            logger.success(f"截图成功：{final_path}")
            return str(final_path)
            
        except subprocess.TimeoutExpired:
            logger.error("PowerShell 执行超时")
            return None
        except Exception as e:
            logger.error(f"截图失败：{e}")
            return None
    
    def capture_and_ocr(
        self,
        output_name: str = 'screenshot.png',
        lang: str = 'eng+chi_sim'
    ) -> Optional[Dict[str, str]]:
        """
        截图并进行 OCR 识别
        
        Args:
            output_name: 输出文件名
            lang: OCR 语言（'eng', 'chi_sim', 'eng+chi_sim'）
            
        Returns:
            {'screenshot': 截图路径，'text': OCR 文本}，失败返回 None
        """
        try:
            import pytesseract
            from PIL import Image
        except ImportError:
            logger.error("需要安装依赖：pip install pytesseract pillow")
            return None
        
        # 先截图
        screenshot_path = self.capture_screen(output_name)
        if not screenshot_path:
            return None
        
        # OCR 识别
        try:
            img = Image.open(screenshot_path)
            text = pytesseract.image_to_string(img, lang=lang)
            
            result = {
                'screenshot': screenshot_path,
                'text': text
            }
            
            logger.info(f"OCR 识别完成，文本长度：{len(text)}")
            return result
            
        except Exception as e:
            logger.error(f"OCR 识别失败：{e}")
            return {'screenshot': screenshot_path, 'text': ''}
    
    def mouse_move(self, x: int, y: int) -> bool:
        """
        移动鼠标到指定位置
        
        Args:
            x: X 坐标
            y: Y 坐标
            
        Returns:
            成功返回 True，失败返回 False
        """
        try:
            import pyautogui
            pyautogui.moveTo(x, y, duration=0.3)
            logger.info(f"鼠标移动到：({x}, {y})")
            return True
        except Exception as e:
            logger.error(f"鼠标移动失败：{e}")
            return False
    
    def click(
        self,
        x: Optional[int] = None,
        y: Optional[int] = None,
        button: str = 'left'
    ) -> bool:
        """
        鼠标点击
        
        Args:
            x: X 坐标（可选）
            y: Y 坐标（可选）
            button: 按钮类型（'left', 'right', 'middle'）
            
        Returns:
            成功返回 True，失败返回 False
        """
        try:
            import pyautogui
            
            if x is not None and y is not None:
                pyautogui.click(x, y, button=button)
                logger.info(f"鼠标点击：({x}, {y}) {button}")
            else:
                pyautogui.click(button=button)
                logger.info(f"鼠标点击：当前位置 {button}")
            
            return True
        except Exception as e:
            logger.error(f"鼠标点击失败：{e}")
            return False
    
    def double_click(self, x: Optional[int] = None, y: Optional[int] = None) -> bool:
        """
        鼠标双击
        
        Args:
            x: X 坐标（可选）
            y: Y 坐标（可选）
            
        Returns:
            成功返回 True，失败返回 False
        """
        try:
            import pyautogui
            
            if x is not None and y is not None:
                pyautogui.doubleClick(x, y)
                logger.info(f"鼠标双击：({x}, {y})")
            else:
                pyautogui.doubleClick()
                logger.info(f"鼠标双击：当前位置")
            
            return True
        except Exception as e:
            logger.error(f"鼠标双击失败：{e}")
            return False
    
    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.5) -> bool:
        """
        鼠标拖拽
        
        Args:
            start_x: 起始 X 坐标
            start_y: 起始 Y 坐标
            end_x: 结束 X 坐标
            end_y: 结束 Y 坐标
            duration: 拖拽持续时间（秒）
            
        Returns:
            成功返回 True，失败返回 False
        """
        try:
            import pyautogui
            pyautogui.moveTo(start_x, start_y, duration=0.2)
            pyautogui.drag(end_x - start_x, end_y - start_y, duration=duration, button='left')
            logger.info(f"鼠标拖拽：({start_x}, {start_y}) → ({end_x}, {end_y})")
            return True
        except Exception as e:
            logger.error(f"鼠标拖拽失败：{e}")
            return False
    
    def scroll(self, clicks: int, x: Optional[int] = None, y: Optional[int] = None) -> bool:
        """
        鼠标滚动
        
        Args:
            clicks: 滚动量（正数向上，负数向下）
            x: X 坐标（可选）
            y: Y 坐标（可选）
            
        Returns:
            成功返回 True，失败返回 False
        """
        try:
            import pyautogui
            if x is not None and y is not None:
                pyautogui.moveTo(x, y)
            pyautogui.scroll(clicks)
            logger.info(f"鼠标滚动：{clicks}")
            return True
        except Exception as e:
            logger.error(f"鼠标滚动失败：{e}")
            return False
    
    def type_text(self, text: str, interval: float = 0.1) -> bool:
        """
        输入文本
        
        Args:
            text: 要输入的文本
            interval: 字符间隔（秒）
            
        Returns:
            成功返回 True，失败返回 False
        """
        try:
            import pyautogui
            pyautogui.write(text, interval=interval)
            logger.info(f"输入文本：{text[:50]}...")
            return True
        except Exception as e:
            logger.error(f"输入文本失败：{e}")
            return False
    
    def press_key(self, key: str) -> bool:
        """
        按下键盘按键
        
        Args:
            key: 按键名称（'enter', 'ctrl', 'alt', 'tab', 'win' 等）
            
        Returns:
            成功返回 True，失败返回 False
        """
        try:
            import pyautogui
            pyautogui.press(key)
            logger.info(f"按下按键：{key}")
            return True
        except Exception as e:
            logger.error(f"按下按键失败：{e}")
            return False
    
    def hotkey(self, *keys: str) -> bool:
        """
        按下组合键
        
        Args:
            keys: 按键列表（'ctrl', 'c' 等）
            
        Returns:
            成功返回 True，失败返回 False
        """
        try:
            import pyautogui
            pyautogui.hotkey(*keys)
            logger.info(f"组合键：{'+'.join(keys)}")
            return True
        except Exception as e:
            logger.error(f"组合键失败：{e}")
            return False
    
    def get_screen_size(self) -> Tuple[int, int]:
        """
        获取屏幕分辨率
        
        Returns:
            (width, height) 元组
        """
        try:
            import pyautogui
            size = pyautogui.size()
            logger.info(f"屏幕分辨率：{size}")
            return (size.width, size.height)
        except Exception as e:
            logger.error(f"获取屏幕分辨率失败：{e}")
            return (0, 0)
    
    def get_mouse_position(self) -> Tuple[int, int]:
        """
        获取鼠标当前位置
        
        Returns:
            (x, y) 元组
        """
        try:
            import pyautogui
            pos = pyautogui.position()
            logger.info(f"鼠标位置：{pos}")
            return (pos.x, pos.y)
        except Exception as e:
            logger.error(f"获取鼠标位置失败：{e}")
            return (0, 0)
    
    def wait(self, seconds: float) -> None:
        """
        等待指定时间
        
        Args:
            seconds: 等待时间（秒）
        """
        time.sleep(seconds)
        logger.info(f"等待：{seconds}秒")


# 便捷函数
def capture_screen(output_name: str = 'screenshot.png') -> Optional[str]:
    """快捷截图函数"""
    capture = WSLgScreenCapture()
    return capture.capture_screen(output_name)


def capture_and_ocr(output_name: str = 'screenshot.png', lang: str = 'eng+chi_sim') -> Optional[Dict[str, str]]:
    """快捷截图 + OCR 函数"""
    capture = WSLgScreenCapture()
    return capture.capture_and_ocr(output_name, lang)


if __name__ == '__main__':
    # 测试
    print("=" * 60)
    print("🖥️  WSLg Windows Screenshot 测试")
    print("=" * 60)
    
    capture = WSLgScreenCapture()
    
    # 测试截图
    print("\n📸 测试截图...")
    path = capture.capture_screen('test_wslg.png')
    if path:
        print(f"✅ 截图成功：{path}")
    
    # 测试屏幕信息
    print("\n📊 屏幕信息:")
    size = capture.get_screen_size()
    print(f"  分辨率：{size[0]}x{size[1]}")
    
    pos = capture.get_mouse_position()
    print(f"  鼠标位置：{pos}")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)
