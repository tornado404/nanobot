#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI 自动化示例 - WSLg Windows Screenshot
"""

import sys
sys.path.insert(0, '/mnt/d/fe/nanobot')

from nanobot.skills.wslg_windows_screenshot import WSLgScreenCapture
import time

def automate_browser_search():
    """自动化浏览器搜索示例"""
    capture = WSLgScreenCapture()
    
    print("=" * 60)
    print("🌐 自动化浏览器搜索示例")
    print("=" * 60)
    
    # 获取屏幕信息
    screen_w, screen_h = capture.get_screen_size()
    print(f"屏幕分辨率：{screen_w}x{screen_h}")
    
    # 步骤 1: 打开浏览器（假设浏览器已经打开）
    print("\n1️⃣  激活浏览器窗口")
    capture.click(screen_w // 2, screen_h // 2)  # 点击屏幕中心
    capture.wait(1)
    
    # 步骤 2: 点击地址栏
    print("2️⃣  点击地址栏")
    # 假设地址栏在顶部中间位置
    address_bar_x = screen_w // 2
    address_bar_y = 50
    capture.click(address_bar_x, address_bar_y)
    capture.wait(0.5)
    
    # 步骤 3: 输入网址
    print("3️⃣  输入网址")
    capture.type_text("https://www.google.com", interval=0.05)
    capture.wait(0.5)
    
    # 步骤 4: 按回车
    print("4️⃣  按回车键")
    capture.press_key('enter')
    capture.wait(3)  # 等待页面加载
    
    # 步骤 5: 截图
    print("5️⃣  截图")
    screenshot = capture.capture_screen('browser_search.png')
    if screenshot:
        print(f"✅ 截图：{screenshot}")
    
    # 步骤 6: 搜索
    print("6️⃣  输入搜索内容")
    # 假设搜索框在页面上部
    search_x = screen_w // 2
    search_y = 300
    capture.click(search_x, search_y)
    capture.wait(0.5)
    
    capture.type_text("WSLg screenshot", interval=0.1)
    capture.wait(0.5)
    capture.press_key('enter')
    capture.wait(3)
    
    # 步骤 7: 截图搜索结果
    print("7️⃣  截图搜索结果")
    screenshot = capture.capture_screen('search_result.png')
    if screenshot:
        print(f"✅ 截图：{screenshot}")
    
    # 步骤 8: OCR 识别搜索结果
    print("8️⃣  OCR 识别搜索结果")
    result = capture.capture_and_ocr('search_result_ocr.png', lang='eng')
    if result:
        print(f"📝 识别到的文本（前 300 字）:")
        print(result['text'][:300])
    
    print("\n" + "=" * 60)
    print("✅ 自动化完成")
    print("=" * 60)


def automate_file_explorer():
    """自动化文件管理器示例"""
    capture = WSLgScreenCapture()
    
    print("=" * 60)
    print("📁 自动化文件管理器示例")
    print("=" * 60)
    
    screen_w, screen_h = capture.get_screen_size()
    
    # 步骤 1: 打开文件管理器（Win + E）
    print("1️⃣  打开文件管理器")
    capture.hotkey('win', 'e')
    capture.wait(2)
    
    # 步骤 2: 截图
    print("2️⃣  截图")
    capture.capture_screen('file_explorer.png')
    
    # 步骤 3: 导航到指定目录
    print("3️⃣  导航到地址栏")
    # 点击地址栏
    capture.click(screen_w // 3, 80)
    capture.wait(0.5)
    
    # 全选地址栏内容
    capture.hotkey('ctrl', 'a')
    capture.wait(0.3)
    
    # 输入新路径
    capture.type_text("C:\\Users", interval=0.05)
    capture.wait(0.5)
    capture.press_key('enter')
    capture.wait(2)
    
    # 步骤 4: 截图
    print("4️⃣  截图")
    capture.capture_screen('users_folder.png')
    
    print("\n" + "=" * 60)
    print("✅ 自动化完成")
    print("=" * 60)


def main():
    """主函数"""
    print("\n请选择示例:")
    print("1. 浏览器搜索自动化")
    print("2. 文件管理器自动化")
    print("q. 退出")
    
    choice = input("\n请输入选项：").strip()
    
    if choice == '1':
        automate_browser_search()
    elif choice == '2':
        automate_file_explorer()
    elif choice == 'q':
        print("退出")
    else:
        print("无效选项")


if __name__ == '__main__':
    main()
