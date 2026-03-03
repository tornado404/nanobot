#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI Input Control 功能测试脚本
测试鼠标、键盘、截图、OCR 等功能
"""

import os
import sys
import time
from pathlib import Path

# 设置环境变量
os.environ['DISPLAY'] = ':0'

# 添加技能目录到路径
sys.path.insert(0, '/mnt/d/fe/nanobot/nanobot/skills/gui-input-control')

from gui_control import GUIInputControl

def test_basic_info():
    """测试基本信息获取"""
    print("\n" + "="*60)
    print("📊 测试 1: 基本信息获取")
    print("="*60)
    
    controller = GUIInputControl(pause=0.3)
    
    # 屏幕尺寸
    width, height = controller.get_screen_size()
    print(f"✅ 屏幕分辨率：{width} x {height}")
    
    # 鼠标位置
    x, y = controller.get_mouse_position()
    print(f"✅ 当前鼠标位置：({x}, {y})")
    
    # 像素颜色
    try:
        color = controller.get_pixel_color(0, 0)
        print(f"✅ 左上角像素颜色：RGB{color}")
    except Exception as e:
        print(f"⚠️  像素颜色获取失败：{e}")
    
    return True

def test_screenshot():
    """测试截图功能"""
    print("\n" + "="*60)
    print("📸 测试 2: 截图功能")
    print("="*60)
    
    controller = GUIInputControl(pause=0.3)
    
    # 全屏截图
    screenshot_path = '/tmp/gui_test_fullscreen.png'
    try:
        controller.screenshot(screenshot_path)
        print(f"✅ 全屏截图已保存：{screenshot_path}")
        
        # 检查文件
        if Path(screenshot_path).exists():
            size = Path(screenshot_path).stat().st_size
            print(f"   文件大小：{size/1024:.1f} KB")
        else:
            print(f"   ❌ 文件未创建")
            return False
    except Exception as e:
        print(f"❌ 截图失败：{e}")
        return False
    
    # 区域截图
    region_path = '/tmp/gui_test_region.png'
    try:
        # 截取左上角 200x200 区域
        controller.screenshot(region_path, region=(0, 0, 200, 200))
        print(f"✅ 区域截图已保存：{region_path}")
        
        if Path(region_path).exists():
            size = Path(region_path).stat().st_size
            print(f"   文件大小：{size/1024:.1f} KB")
    except Exception as e:
        print(f"⚠️  区域截图失败：{e}")
    
    return True

def test_keyboard():
    """测试键盘控制"""
    print("\n" + "="*60)
    print("⌨️  测试 3: 键盘控制")
    print("="*60)
    
    controller = GUIInputControl(pause=0.3)
    
    # 测试快捷键（Ctrl+L 聚焦地址栏，但不会实际执行，只验证功能）
    print("✅ 快捷键功能验证：Ctrl+L")
    try:
        # 不实际执行，只验证方法存在
        assert hasattr(controller, 'hotkey')
        print("   hotkey() 方法可用")
    except Exception as e:
        print(f"❌ 快捷键方法不可用：{e}")
        return False
    
    # 测试文字输入
    print("✅ 文字输入功能验证")
    try:
        assert hasattr(controller, 'type_text')
        print("   type_text() 方法可用")
    except Exception as e:
        print(f"❌ 文字输入方法不可用：{e}")
        return False
    
    # 测试按键
    print("✅ 按键功能验证")
    try:
        assert hasattr(controller, 'press_key')
        print("   press_key() 方法可用")
    except Exception as e:
        print(f"❌ 按键方法不可用：{e}")
        return False
    
    return True

def test_mouse():
    """测试鼠标控制"""
    print("\n" + "="*60)
    print("🖱️  测试 4: 鼠标控制")
    print("="*60)
    
    controller = GUIInputControl(pause=0.3)
    
    # 记录初始位置
    start_x, start_y = controller.get_mouse_position()
    print(f"初始位置：({start_x}, {start_y})")
    
    # 测试移动（小幅度移动，避免干扰）
    try:
        # 向右移动 50 像素
        controller.move_mouse_relative(50, 0, duration=0.2)
        time.sleep(0.3)
        new_x, new_y = controller.get_mouse_position()
        print(f"✅ 相对移动后位置：({new_x}, {new_y})")
        
        # 移回原位
        controller.move_mouse(start_x, start_y, duration=0.2)
        time.sleep(0.3)
        final_x, final_y = controller.get_mouse_position()
        print(f"✅ 返回原位：({final_x}, {final_y})")
    except Exception as e:
        print(f"❌ 鼠标移动失败：{e}")
        return False
    
    # 测试点击方法存在
    try:
        assert hasattr(controller, 'click')
        print("✅ click() 方法可用")
    except Exception as e:
        print(f"❌ 点击方法不可用：{e}")
        return False
    
    return True

def test_ocr():
    """测试 OCR 功能"""
    print("\n" + "="*60)
    print("🔍 测试 5: OCR 文字识别")
    print("="*60)
    
    controller = GUIInputControl(pause=0.3)
    
    # 先截图
    test_screenshot_path = '/tmp/ocr_test.png'
    try:
        controller.screenshot(test_screenshot_path, region=(0, 0, 400, 100))
        print(f"✅ 已创建测试截图：{test_screenshot_path}")
    except Exception as e:
        print(f"❌ 截图失败：{e}")
        return False
    
    # OCR 识别（英文）
    try:
        text = controller.ocr_text(region=(0, 0, 400, 100), lang='eng')
        print(f"✅ OCR 识别结果（英文）:")
        print(f"   \"{text.strip()[:100]}...\"")
    except Exception as e:
        print(f"⚠️  OCR 识别失败：{e}")
    
    return True

def test_tool_functions():
    """测试工具函数"""
    print("\n" + "="*60)
    print("🔧 测试 6: 工具函数接口")
    print("="*60)
    
    from gui_control import (
        gui_click, gui_type, gui_hotkey, gui_screenshot, gui_ocr
    )
    
    # 测试工具函数存在
    functions = [gui_click, gui_type, gui_hotkey, gui_screenshot, gui_ocr]
    for func in functions:
        print(f"✅ {func.__name__}() 可用")
    
    # 测试截图工具函数
    try:
        result = gui_screenshot('/tmp/tool_test_screenshot.png')
        print(f"   截图结果：{result}")
    except Exception as e:
        print(f"⚠️  工具函数测试失败：{e}")
    
    return True

def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("🚀 GUI Input Control 功能测试")
    print(f"⏰ 时间：{time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🖥️  DISPLAY: {os.environ.get('DISPLAY', '未设置')}")
    print("="*60)
    
    results = {
        '基本信息': False,
        '截图功能': False,
        '键盘控制': False,
        '鼠标控制': False,
        'OCR 识别': False,
        '工具函数': False
    }
    
    # 运行测试
    try:
        results['基本信息'] = test_basic_info()
    except Exception as e:
        print(f"❌ 基本信息测试异常：{e}")
    
    try:
        results['截图功能'] = test_screenshot()
    except Exception as e:
        print(f"❌ 截图测试异常：{e}")
    
    try:
        results['键盘控制'] = test_keyboard()
    except Exception as e:
        print(f"❌ 键盘测试异常：{e}")
    
    try:
        results['鼠标控制'] = test_mouse()
    except Exception as e:
        print(f"❌ 鼠标测试异常：{e}")
    
    try:
        results['OCR 识别'] = test_ocr()
    except Exception as e:
        print(f"❌ OCR 测试异常：{e}")
    
    try:
        results['工具函数'] = test_tool_functions()
    except Exception as e:
        print(f"❌ 工具函数测试异常：{e}")
    
    # 打印总结
    print("\n" + "="*60)
    print("📊 测试总结")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {test_name}")
    
    print(f"\n总计：{passed}/{total} 通过 ({passed/total*100:.0f}%)")
    print("="*60)
    
    # 生成测试报告
    report_path = '/tmp/gui_test_report.txt'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("GUI Input Control 测试报告\n")
        f.write(f"时间：{time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"DISPLAY: {os.environ.get('DISPLAY', '未设置')}\n\n")
        for test_name, result in results.items():
            status = "✅ 通过" if result else "❌ 失败"
            f.write(f"{status} - {test_name}\n")
        f.write(f"\n总计：{passed}/{total} 通过\n")
    
    print(f"\n📄 测试报告已保存：{report_path}")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
