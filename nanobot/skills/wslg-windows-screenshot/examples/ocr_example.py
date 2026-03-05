#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR 识别示例 - WSLg Windows Screenshot
"""

import sys
sys.path.insert(0, '/mnt/d/fe/nanobot')

from nanobot.skills.wslg_windows_screenshot import WSLgScreenCapture

def main():
    capture = WSLgScreenCapture()
    
    print("=" * 60)
    print("📝 OCR 识别示例")
    print("=" * 60)
    
    # 示例 1: 英文 OCR
    print("\n📄 示例 1: 英文 OCR")
    result_en = capture.capture_and_ocr('ocr_english.png', lang='eng')
    if result_en:
        print(f"✅ 截图：{result_en['screenshot']}")
        print(f"📝 识别文本:")
        print("-" * 40)
        print(result_en['text'])
        print("-" * 40)
    
    # 示例 2: 中文 OCR
    print("\n📄 示例 2: 中文 OCR")
    result_cn = capture.capture_and_ocr('ocr_chinese.png', lang='chi_sim')
    if result_cn:
        print(f"✅ 截图：{result_cn['screenshot']}")
        print(f"📝 识别文本:")
        print("-" * 40)
        print(result_cn['text'])
        print("-" * 40)
    
    # 示例 3: 中英文混合 OCR
    print("\n📄 示例 3: 中英文混合 OCR")
    result_mix = capture.capture_and_ocr('ocr_mixed.png', lang='eng+chi_sim')
    if result_mix:
        print(f"✅ 截图：{result_mix['screenshot']}")
        print(f"📝 识别文本:")
        print("-" * 40)
        print(result_mix['text'])
        print("-" * 40)
    
    # 示例 4: 截图后处理
    print("\n📄 示例 4: 截图后处理")
    screenshot_path = capture.capture_screen('ocr_process.png')
    if screenshot_path:
        from PIL import Image
        
        # 打开图像
        img = Image.open(screenshot_path)
        print(f"图像尺寸：{img.size}")
        print(f"图像模式：{img.mode}")
        
        # 裁剪感兴趣区域（示例：左上角 500x300）
        roi = img.crop((0, 0, 500, 300))
        roi.save('ocr_roi.png')
        print("已保存裁剪区域：ocr_roi.png")
        
        # 对裁剪区域进行 OCR
        import pytesseract
        text = pytesseract.image_to_string(roi, lang='eng+chi_sim')
        print(f"📝 ROI 区域文本:")
        print("-" * 40)
        print(text)
        print("-" * 40)
    
    print("\n" + "=" * 60)
    print("✅ OCR 示例完成")
    print("=" * 60)


if __name__ == '__main__':
    main()
