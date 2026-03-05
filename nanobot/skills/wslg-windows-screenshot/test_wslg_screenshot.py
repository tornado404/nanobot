#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WSLg Windows Screenshot 综合测试脚本
"""

import sys
sys.path.insert(0, '/mnt/d/fe/nanobot')

from nanobot.skills.wslg_windows_screenshot import WSLgScreenCapture
from pathlib import Path
import time

def test_screenshot():
    """测试截图功能"""
    print("\n" + "=" * 60)
    print("📸 测试 1: 截图功能")
    print("=" * 60)
    
    capture = WSLgScreenCapture()
    
    # 测试截图
    path = capture.capture_screen('test_screenshot.png')
    
    if path and Path(path).exists():
        size = Path(path).stat().st_size
        print(f"✅ 截图成功")
        print(f"   文件：{path}")
        print(f"   大小：{size} 字节")
        return True
    else:
        print(f"❌ 截图失败")
        return False


def test_ocr():
    """测试 OCR 功能"""
    print("\n" + "=" * 60)
    print("📝 测试 2: OCR 识别")
    print("=" * 60)
    
    capture = WSLgScreenCapture()
    
    # 测试 OCR
    result = capture.capture_and_ocr('test_ocr.png', lang='eng')
    
    if result and result['screenshot']:
        print(f"✅ OCR 成功")
        print(f"   截图：{result['screenshot']}")
        print(f"   文本长度：{len(result['text'])} 字符")
        if result['text']:
            print(f"   文本预览：{result['text'][:100]}...")
        return True
    else:
        print(f"❌ OCR 失败")
        return False


def test_mouse_control():
    """测试鼠标控制"""
    print("\n" + "=" * 60)
    print("🖱️  测试 3: 鼠标控制")
    print("=" * 60)
    
    capture = WSLgScreenCapture()
    
    tests_passed = 0
    total_tests = 5
    
    # 1. 获取鼠标位置
    print("1. 获取鼠标位置...")
    pos = capture.get_mouse_position()
    if pos[0] >= 0 and pos[1] >= 0:
        print(f"   ✅ 鼠标位置：{pos}")
        tests_passed += 1
    else:
        print(f"   ❌ 获取失败")
    
    # 2. 获取屏幕分辨率
    print("2. 获取屏幕分辨率...")
    size = capture.get_screen_size()
    if size[0] > 0 and size[1] > 0:
        print(f"   ✅ 分辨率：{size[0]}x{size[1]}")
        tests_passed += 1
    else:
        print(f"   ❌ 获取失败")
    
    # 3. 鼠标移动
    print("3. 鼠标移动...")
    center_x, center_y = size[0] // 2, size[1] // 2
    if capture.mouse_move(center_x, center_y):
        print(f"   ✅ 移动到：({center_x}, {center_y})")
        tests_passed += 1
    else:
        print(f"   ❌ 移动失败")
    
    # 4. 鼠标点击
    print("4. 鼠标点击...")
    if capture.click():
        print(f"   ✅ 点击成功")
        tests_passed += 1
    else:
        print(f"   ❌ 点击失败")
    
    # 5. 鼠标双击
    print("5. 鼠标双击...")
    if capture.double_click():
        print(f"   ✅ 双击成功")
        tests_passed += 1
    else:
        print(f"   ❌ 双击失败")
    
    print(f"\n鼠标控制测试：{tests_passed}/{total_tests} 通过")
    return tests_passed == total_tests


def test_keyboard_control():
    """测试键盘控制"""
    print("\n" + "=" * 60)
    print("⌨️  测试 4: 键盘控制")
    print("=" * 60)
    
    capture = WSLgScreenCapture()
    
    tests_passed = 0
    total_tests = 3
    
    # 1. 输入文本
    print("1. 输入文本...")
    if capture.type_text("Test123", interval=0.05):
        print(f"   ✅ 输入成功")
        tests_passed += 1
    else:
        print(f"   ❌ 输入失败")
    
    # 2. 按下按键
    print("2. 按下按键 (enter)...")
    if capture.press_key('enter'):
        print(f"   ✅ 按键成功")
        tests_passed += 1
    else:
        print(f"   ❌ 按键失败")
    
    # 3. 组合键
    print("3. 组合键 (ctrl+a)...")
    if capture.hotkey('ctrl', 'a'):
        print(f"   ✅ 组合键成功")
        tests_passed += 1
    else:
        print(f"   ❌ 组合键失败")
    
    print(f"\n键盘控制测试：{tests_passed}/{total_tests} 通过")
    return tests_passed == total_tests


def test_drag_scroll():
    """测试拖拽和滚动"""
    print("\n" + "=" * 60)
    print("🖱️  测试 5: 拖拽和滚动")
    print("=" * 60)
    
    capture = WSLgScreenCapture()
    screen_w, screen_h = capture.get_screen_size()
    
    tests_passed = 0
    total_tests = 2
    
    # 1. 拖拽
    print("1. 鼠标拖拽...")
    start_x, start_y = 100, 100
    end_x, end_y = 200, 200
    if capture.drag(start_x, start_y, end_x, end_y, duration=0.5):
        print(f"   ✅ 拖拽成功：({start_x},{start_y}) → ({end_x},{end_y})")
        tests_passed += 1
    else:
        print(f"   ❌ 拖拽失败")
    
    # 2. 滚动
    print("2. 鼠标滚动...")
    if capture.scroll(100):
        print(f"   ✅ 滚动成功")
        tests_passed += 1
    else:
        print(f"   ❌ 滚动失败")
    
    print(f"\n拖拽滚动测试：{tests_passed}/{total_tests} 通过")
    return tests_passed == total_tests


def main():
    """主测试函数"""
    print("=" * 60)
    print("🧪 WSLg Windows Screenshot 综合测试")
    print("=" * 60)
    print(f"测试时间：{time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        '截图功能': test_screenshot(),
        'OCR 识别': test_ocr(),
        '鼠标控制': test_mouse_control(),
        '键盘控制': test_keyboard_control(),
        '拖拽滚动': test_drag_scroll(),
    }
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    print(f"\n总计：{passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return 1


if __name__ == '__main__':
    exit(main())
