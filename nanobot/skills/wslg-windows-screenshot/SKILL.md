# WSLg Windows Screenshot Skill

> **💡 Standalone Package Available**: 
> Install with `pip install git+https://YOUR_TOKEN@github.com/YOUR_USERNAME/wslg-screenshot.git`
> See: https://github.com/YOUR_USERNAME/wslg-screenshot

## 📋 技能概述

在 WSL2 + WSLg 环境下，通过调用 Windows PowerShell 实现屏幕截图，解决 WSL 侧无法直接截图的问题。

**核心思路**：
1. WSL 中执行鼠标键盘控制（pyautogui 可用）
2. 调用 Windows PowerShell 进行截图
3. 截图保存到 Windows 临时目录
4. WSL 读取截图文件进行处理

---

## 🎯 适用场景

- WSL2 + WSLg 环境下的 GUI 自动化
- 需要屏幕截图进行 OCR 识别
- 需要屏幕截图进行图像分析
- 浏览器自动化（配合 Playwright 更佳）

---

## 📦 依赖安装

### 系统依赖

```bash
# 确保可以调用 Windows PowerShell
which powershell.exe

# 测试 WSL 互操作
powershell.exe -Command "Write-Host 'WSL interop works!'"
```

### Python 依赖

```bash
pip install pillow pytesseract loguru
```

---

## 🔧 使用方法

### 基础用法

```python
from nanobot.skills.wslg_windows_screenshot.wslg_screenshot import WSLgScreenCapture

# 初始化
capture = WSLgScreenCapture()

# 全屏截图
screenshot_path = capture.capture_screen()
print(f"截图保存至：{screenshot_path}")

# 截图并 OCR 识别
result = capture.capture_and_ocr(lang='eng+chi_sim')
print(f"截图：{result['screenshot']}")
print(f"OCR 文本：{result['text']}")
```

### 高级用法

```python
from nanobot.skills.wslg_windows_screenshot.wslg_screenshot import WSLgScreenCapture

capture = WSLgScreenCapture()

# 1. 鼠标移动到指定位置
capture.mouse_move(500, 300)

# 2. 点击
capture.click()

# 3. 等待操作生效
import time
time.sleep(1)

# 4. 截图
screenshot_path = capture.capture_screen(output_name='after_click.png')

# 5. 图像分析
from PIL import Image
img = Image.open(screenshot_path)
print(f"图像尺寸：{img.size}")
```

---

## 📚 API 参考

### WSLgScreenCapture 类

#### 初始化

```python
capture = WSLgScreenCapture(
    output_dir='/mnt/d/fe/nanobot/workspace',  # WSL 侧输出目录
    win_temp_dir='C:\\Windows\\Temp',          # Windows 侧临时目录
    display=':0',                               # X11 DISPLAY
    xauthority='/dev/null'                      # XAUTHORITY
)
```

#### 方法

##### `capture_screen(output_name='screenshot.png')`
捕获全屏截图

**参数**:
- `output_name`: 输出文件名（WSL 侧路径）

**返回**: 截图文件路径（WSL 侧），失败返回 None

---

##### `capture_and_ocr(output_name='screenshot.png', lang='eng+chi_sim')`
截图并进行 OCR 识别

**参数**:
- `output_name`: 输出文件名
- `lang`: OCR 语言（'eng', 'chi_sim', 'eng+chi_sim'）

**返回**: 
```python
{
    'screenshot': '/path/to/screenshot.png',
    'text': '识别的文本内容'
}
```

---

##### `mouse_move(x, y)`
移动鼠标到指定位置

**参数**:
- `x`: X 坐标
- `y`: Y 坐标

---

##### `click(x=None, y=None, button='left')`
鼠标点击

**参数**:
- `x`: X 坐标（可选，不指定则在当前位置）
- `y`: Y 坐标（可选）
- `button`: 按钮类型（'left', 'right', 'middle'）

---

##### `type_text(text, interval=0.1)`
输入文本

**参数**:
- `text`: 要输入的文本
- `interval`: 字符间隔（秒）

---

##### `press_key(key)`
按下键盘按键

**参数**:
- `key`: 按键名称（'enter', 'ctrl', 'alt', 'tab' 等）

---

##### `get_screen_size()`
获取屏幕分辨率

**返回**: `(width, height)` 元组

---

##### `get_mouse_position()`
获取鼠标当前位置

**返回**: `(x, y)` 元组

---

## 🔍 工作原理

```
┌─────────────────────────────────────────────────────────┐
│                     WSL2 环境                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Python 脚本                                     │   │
│  │  1. pyautogui 控制鼠标键盘 ───────────────┐     │   │
│  │  2. 调用 PowerShell 截图 ────────┐        │     │   │
│  │  3. 读取截图文件 ────────┐       │        │     │   │
│  │                          │       │        │     │   │
│  └──────────────────────────│───────│────────│─────┘   │
│                             │       │        │         │
└─────────────────────────────│───────│────────│─────────┘
                              │       │        │
                              ▼       ▼        ▼
┌─────────────────────────────────────────────────────────┐
│                   Windows 环境                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │  PowerShell.exe                                  │   │
│  │  1. 接收截图命令                                 │   │
│  │  2. 使用 .NET System.Drawing 截图               │   │
│  │  3. 保存到 C:\Windows\Temp\screen.png           │   │
│  └─────────────────────────────────────────────────┘   │
│                             │                           │
│                             ▼                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Windows 文件系统                                │   │
│  │  C:\Windows\Temp\screen.png ← 截图文件          │   │
│  │  ↓ 通过 /mnt/c/ 挂载                            │   │
│  └─────────────────────────────────────────────────┘   │
│                             │                           │
└─────────────────────────────│───────────────────────────┘
                              │
                              ▼
                    WSL 读取 /mnt/c/Windows/Temp/screen.png
```

---

## 📁 文件结构

```
wslg-windows-screenshot/
├── SKILL.md                      # 技能说明文档
├── wslg_screenshot.py            # 核心实现
├── tool.py                       # 工具函数
├── __init__.py                   # 模块导入
├── examples/
│   ├── basic_example.py          # 基础示例
│   ├── ocr_example.py            # OCR 示例
│   └── automation_example.py     # 自动化示例
└── test_wslg_screenshot.py       # 测试脚本
```

---

## ⚠️ 注意事项

### 1. 路径转换

Windows 路径和 WSL 路径需要正确转换：
- Windows: `C:\Windows\Temp\screen.png`
- WSL: `/mnt/c/Windows/Temp/screen.png`

### 2. 权限问题

确保 WSL 可以访问 Windows 临时目录：
```bash
ls -la /mnt/c/Windows/Temp/
```

### 3. PowerShell 执行策略

如果遇到 PowerShell 执行错误，可能需要调整执行策略：
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 4. 性能考虑

- PowerShell 启动有约 0.5-1 秒开销
- 截图文件传输需要时间
- 建议批量操作后统一截图

---

## 🧪 测试

运行测试脚本：

```bash
cd /mnt/d/fe/nanobot/nanobot/skills/wslg-windows-screenshot
python3 test_wslg_screenshot.py
```

测试项目：
- ✅ 全屏截图
- ✅ 截图 + OCR
- ✅ 鼠标控制
- ✅ 键盘控制
- ✅ 屏幕信息获取

---

## 🔗 相关技能

- **gui-input-control**: GUI 输入控制（鼠标键盘）
- **opencode-coding-screenshot**: 编码任务截图
- **windows-screen-capture**: Windows 屏幕捕获服务（Rust 实现）

---

## 📝 更新日志

### v1.0.0 (2026-03-05)
- ✅ 添加独立包引用说明
- ✅ 更新使用示例

### v1.0.0 (2026-03-03)
- ✅ 初始版本
- ✅ WSL → Windows 截图
- ✅ 截图 + OCR 识别
- ✅ 鼠标键盘控制
- ✅ 完整测试套件

---

*作者：nanobot 🐈*  
*最后更新：2026-03-05*
