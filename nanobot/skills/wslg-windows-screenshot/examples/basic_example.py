#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础使用示例 - WSLg Windows Screenshot
"""

import sys
sys.path.insert(0, '/mnt/d/fe/nanobot')

from nanobot.skills.wslg_windows_screenshot import WSLgScreenCapture

def main():
    # 初始化工具
    capture = WSLgScreenCapture()
    
    print("=" * 60)
    print("🖥️  WSLg Windows Screenshot 基础示例")
    print("=" * 60)
    
    # 1. 获取屏幕信息
    print("\n📊 1. 获取屏幕信息")
    screen_size = capture.get_screen_size()
    print(f"   屏幕分辨率：{screen_size[0]}x{screen_size[1]}")
    
    mouse_pos = capture.get_mouse_position()
    print(f"   鼠标当前位置：{mouse_pos}")
    
    # 2. 鼠标控制
    print("\n🖱️  2. 鼠标控制")
    
    # 移动到屏幕中心
    center_x = screen_size[0] // 2
    center_y = screen_size[1] // 2
    print(f"   移动到屏幕中心：({center_x}, {center_y})")
    capture.mouse_move(center_x, center_y)
    capture.wait(1)
    
    # 点击
    print("   左键点击")
    capture.click()
    capture.wait(0.5)
    
    # 3. 键盘控制
    print("\n⌨️  3. 键盘控制")
    print("   输入文本：Hello WSLg!")
    capture.type_text("Hello WSLg!", interval=0.05)
    capture.wait(1)
    
    # 4. 截图
    print("\n📸 4. 截图")
    screenshot_path = capture.capture_screen('example_screenshot.png')
    if screenshot_path:
        print(f"   ✅ 截图成功：{screenshot_path}")
    else:
        print("   ❌ 截图失败")
    
    # 5. 截图 + OCR
    print("\n📸 5. 截图 + OCR 识别")
    result = capture.capture_and_ocr('example_ocr.png', lang='eng')
    if result:
        print(f"   ✅ 截图：{result['screenshot']}")
        print(f"   📝 OCR 文本（前 200 字）:")
        print(f"   {result['text'][:200]}")
    
    print("\n" + "=" * 60)
    print("✅ 示例完成")
    print("=" * 60)


if __name__ == '__main__':
    main()
