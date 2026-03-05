# Windows Screen Capture Skill

## Overview

在 WSL2 环境下捕获 Windows 桌面画面。通过 Windows.Graphics.Capture API 获取屏幕内容，经 JPEG 编码后通过 AF_UNIX Socket 传输到 WSL。

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    WSL2 (nanobot)                            │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  capture_screen() tool                                 │ │
│  │  ┌──────────────────┐                                  │ │
│  │  │  CaptureClient   │ (Python)                        │ │
│  │  └──────────────────┘                                  │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────┬──────────────────────────────────┘
                           │ AF_UNIX Socket
┌──────────────────────────▼──────────────────────────────────┐
│                   Windows Host                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  nanobot-capture-service.exe                           │ │
│  │  ┌──────────────────────────────────────────────────┐ │ │
│  │  │  Windows.Graphics.Capture                        │ │ │
│  │  │  → image crate (JPEG)                            │ │ │
│  │  │  → AF_UNIX Socket Server                         │ │ │
│  │  └──────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

### 1. Windows Service Installation

在 Windows 上安装并启动捕获服务：

```powershell
# 1. 构建服务 (在 Windows 上)
cd /mnt/d/fe/nanobot/windows-service
cargo build --release

# 2. 安装服务
powershell.exe -File scripts/install-service.ps1

# 3. 启动服务
powershell.exe -File scripts/start-service.ps1

# 4. 验证服务运行
powershell.exe -Command "Get-ScheduledTask -TaskName NanobotCaptureService"
```

### 2. WSL Client Dependencies

```bash
# Python dependencies
pip install pillow pytesseract loguru

# Optional: For OCR support
sudo apt install tesseract-ocr tesseract-ocr-chi-sim tesseract-ocr-eng
```

## Usage

### Basic Usage

```python
from nanobot.skills.windows_screen_capture import CaptureClient, CaptureClientConfig

# Initialize client
config = CaptureClientConfig(socket_path="/tmp/nanobot-capture.sock")
client = CaptureClient(config)

# Capture screen
path = await client.capture("/tmp/screen.jpg")
print(f"Captured: {path}")

# Close connection
await client.close()
```

### Using Agent Tool

在 nanobot 对话中直接使用：

```
用户："帮我看看现在桌面上打开了什么窗口"

Agent 自动调用：capture_screen()
→ 捕获屏幕
→ 分析图像内容
→ 返回结果
```

### With OCR

```python
from nanobot.skills.windows_screen_capture.tool import capture_screen

result = await capture_screen(
    output="/tmp/screen.jpg",
    ocr=True,
    lang="eng+chi_sim"
)

print(f"Path: {result['path']}")
print(f"OCR: {result['ocr_text']}")
print(f"Size: {result['width']}x{result['height']}")
```

### Check Service Status

```python
from nanobot.skills.windows_screen_capture.tool import check_service_status

status = await check_service_status()

if status["running"]:
    print("✅ Service is running")
else:
    print(f"❌ {status['message']}")
```

### Context Manager

```python
from nanobot.skills.windows_screen_capture import CaptureClient, CaptureClientConfig

config = CaptureClientConfig()

async with CaptureClient(config) as client:
    path = await client.capture("/tmp/screen.jpg")
    print(f"Captured: {path}")
# Connection automatically closed
```

## API Reference

### CaptureClientConfig

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `socket_path` | str | `/tmp/nanobot-capture.sock` | Socket path (AF_UNIX or TCP) |
| `timeout_seconds` | int | `5` | Connection timeout |
| `max_retries` | int | `3` | Maximum reconnection attempts |
| `reconnect_delay` | float | `0.5` | Delay between retries (seconds) |

### CaptureClient Methods

#### `capture(output_path: str) -> str`

捕获屏幕并保存到文件。

**Args:**
- `output_path`: 输出文件路径

**Returns:**
- 保存的文件路径

**Raises:**
- `RuntimeError`: 如果服务不可用

---

#### `capture_to_memory() -> bytes`

捕获屏幕并返回字节数据（不保存文件）。

**Returns:**
- JPEG 图像字节

---

#### `ping() -> bool`

检查服务是否响应。

**Returns:**
- `True` 如果服务响应 PING

---

#### `close() -> None`

关闭连接。

### Tool Functions

#### `capture_screen(output, ocr, lang) -> dict`

完整的截图工具（带 OCR 选项）。

**Returns:**
```python
{
    "path": "/tmp/screen.jpg",
    "ocr_text": "识别的文本",  # 仅当 ocr=True
    "width": 1920,
    "height": 1080
}
```

#### `check_service_status() -> dict`

检查服务状态。

**Returns:**
```python
{
    "running": True,
    "message": "Windows capture service is running"
}
```

## Configuration

### Windows Service Configuration

通过环境变量配置 Windows 服务：

```powershell
# 设置 socket 路径
$env:NANOBOT_SOCKET_PATH = "\\.\pipe\nanobot-capture"

# 设置 JPEG 质量 (1-100)
$env:NANOBOT_JPEG_QUALITY = "85"

# 设置日志级别
$env:NANOBOT_LOG_LEVEL = "info"
```

### WSL Client Configuration

```python
from nanobot.skills.windows_screen_capture import CaptureClientConfig

config = CaptureClientConfig(
    socket_path="/tmp/nanobot-capture.sock",  # 或 TCP: "127.0.0.1:18791"
    timeout_seconds=5,
    max_retries=3,
    reconnect_delay=0.5
)
```

## Troubleshooting

### "Socket not found" Error

**Problem:**
```
RuntimeError: Socket not found: /tmp/nanobot-capture.sock
```

**Solution:**
1. 确保 Windows 服务正在运行
2. 检查 WSL 是否可以访问 Windows named pipe
3. 尝试使用 TCP 模式：`socket_path="127.0.0.1:18791"`

### "Connection refused" Error

**Problem:**
```
RuntimeError: Windows capture service refused connection
```

**Solution:**
1. 重启 Windows 服务
2. 检查防火墙设置
3. 验证 socket 路径正确

### Slow Capture

**Problem:**
捕获速度慢 (>500ms)

**Solution:**
1. 降低 JPEG 质量：`jpeg_quality=75`
2. 减少捕获频率
3. 检查网络延迟（如果使用 TCP）

### Service Not Starting

**Problem:**
Windows 服务无法启动

**Solution:**
```powershell
# 手动运行服务查看错误
cd C:\Program Files\Nanobot
.\nanobot-capture-service.exe

# 查看事件日志
Get-EventLog -LogName Application -Source "nanobot-capture-service" -Newest 10
```

## Performance

| Metric | Target | Typical |
|--------|--------|---------|
| Capture Latency | <100ms | 50-80ms |
| Frame Rate | ≥15 FPS | 20-30 FPS |
| JPEG Size (1080p) | <500KB | 200-300KB |
| Memory Usage | <100MB | 50-80MB |

## Security Notes

⚠️ **Current Implementation**: No authentication

- Socket accessible to all local users
- Plan to add token authentication in future version

**Mitigation:**
- Socket only accessible from localhost
- Windows ACL restricts named pipe access

## Related Files

- `capture_client.py` - WSL 客户端实现
- `tool.py` - Agent Tool 接口
- `/mnt/d/fe/nanobot/windows-service/` - Windows 服务 (Rust)

## Examples

### Example 1: Basic Capture

```python
import asyncio
from nanobot.skills.windows_screen_capture import CaptureClient, CaptureClientConfig

async def main():
    config = CaptureClientConfig()
    client = CaptureClient(config)
    
    try:
        path = await client.capture("/tmp/screen.jpg")
        print(f"✅ Captured: {path}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    finally:
        await client.close()

asyncio.run(main())
```

### Example 2: Continuous Monitoring

```python
import asyncio
from nanobot.skills.windows_screen_capture import CaptureClient, CaptureClientConfig

async def monitor_screen(interval=1.0):
    config = CaptureClientConfig()
    client = CaptureClient(config)
    
    frame_count = 0
    
    try:
        while True:
            path = await client.capture(f"/tmp/screen_{frame_count:04d}.jpg")
            print(f"Frame {frame_count}: {path}")
            frame_count += 1
            await asyncio.sleep(interval)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        await client.close()

asyncio.run(monitor_screen())
```

### Example 3: Change Detection

```python
import asyncio
import hashlib
from nanobot.skills.windows_screen_capture import CaptureClient

async def detect_changes():
    client = CaptureClient(CaptureClientConfig())
    last_hash = None
    
    try:
        while True:
            data = await client.capture_to_memory()
            current_hash = hashlib.md5(data).hexdigest()
            
            if current_hash != last_hash:
                print(f"Screen changed! Hash: {current_hash}")
                last_hash = current_hash
            
            await asyncio.sleep(0.5)
    finally:
        await client.close()

asyncio.run(detect_changes())
```

---

*Last updated: 2026-03-04*
*Version: 1.0.0*
