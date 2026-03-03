# GUI Input Control 功能更新说明

## 📦 更新内容

本次更新为 nanobot 项目添加了**系统级图形界面输入控制能力**，支持：

- ✅ 鼠标控制（移动、点击、拖拽）
- ✅ 键盘控制（输入、快捷键）
- ✅ 屏幕截图
- ✅ OCR 文字识别
- ✅ 图像定位与识别
- ✅ WSL + WSLg 环境支持

## 🌿 分支信息

- **分支名称**: `feature/gui-input-control`
- **基于版本**: upstream main (c05cb2e) - 2026-03-03 最新版本
- **本地改动**: 已合并 local/customizations 分支
- **远程仓库**: https://github.com/tornado404/nanobot

## 📝 提交历史

```
6ce3a2a Merge local/customizations: token limits, bailian provider, version tracking
8788390 feat: add GUI input control skill for mouse/keyboard/screen automation
c05cb2e refactor(cron): remove CLI cron commands and unify scheduling via cron tool
```

## 🚀 安装依赖

```bash
# 系统工具
sudo apt install -y xdotool scrot maim tesseract-ocr tesseract-ocr-chi-sim

# Python 依赖
pip install pyautogui pillow pytesseract
```

## 📖 使用方式

### 1. 环境变量设置（WSL 环境）

```bash
export DISPLAY=:0
```

### 2. 在 nanobot 中使用

```python
# nanobot 会自动加载技能
# 使用 gui_control 工具

# 示例：点击坐标
gui_control(action='click', x=100, y=200)

# 示例：输入文字
gui_control(action='type', text='Hello World')

# 示例：快捷键
gui_control(action='hotkey', keys=['ctrl', 'c'])

# 示例：截图
gui_control(action='screenshot', filename='screen.png')

# 示例：OCR 识别
gui_control(action='ocr', region='100,100,300,200')

# 示例：查找并点击图片
gui_control(action='click_image', image_path='/path/to/button.png')
```

### 3. 直接使用 Python 模块

```python
from nanobot.skills.gui_input_control.gui_control import GUIInputControl

controller = GUIInputControl(pause=0.5)

# 鼠标控制
controller.click(100, 200)
controller.move_mouse(500, 500, duration=1.0)
controller.drag_to(600, 600)

# 键盘控制
controller.type_text('Hello')
controller.hotkey('ctrl', 'l')

# 屏幕分析
screenshot = controller.screenshot('screen.png')
text = controller.ocr_text()
location = controller.locate_image('button.png')
```

## 📂 文件结构

```
nanobot/skills/gui-input-control/
├── SKILL.md                      # 技能文档
├── gui_control.py                # 核心控制模块
├── tool.py                       # nanobot 工具包装器
└── examples/
    └── basic_example.py          # 使用示例
```

## 🔧 本地改动合并

本次更新已合并以下本地 customizations：

1. **Token 限制功能**
   - `max_context_tokens` 配置
   - LiteLLM token 计数
   - 自动截断旧历史

2. **阿里云百炼支持**
   - Bailian provider
   - 默认模型：`bailian/qwen3.5-plus`

3. **版本管理**
   - `sync-upstream.sh` - 同步上游代码
   - `check-upstream.sh` - 检查更新
   - `VERSION_CONTROL_STRATEGY.md` - 版本管理策略

## 📋 下一步操作

### 选项 1: 创建 Pull Request 到上游

```bash
# 如果需要贡献给官方仓库
git remote add upstream https://github.com/HKUDS/nanobot.git
git push upstream feature/gui-input-control
# 然后在 GitHub 创建 PR
```

### 选项 2: 合并到 main 分支

```bash
# 合并到你的 fork 的 main 分支
git checkout main
git merge feature/gui-input-control
git push fork main
```

### 选项 3: 保持独立分支

```bash
# 保持功能分支，按需使用
git checkout feature/gui-input-control
```

## ⚠️ 注意事项

1. **WSL 环境**: 必须设置 `DISPLAY=:0`
2. **安全性**: 鼠标移到屏幕左上角会触发紧急停止
3. **权限**: 某些操作可能需要 root 权限
4. **屏幕缩放**: 高 DPI 屏幕可能需要调整坐标

## 📞 问题反馈

如有问题，请提交到：https://github.com/tornado404/nanobot/issues

---

**更新时间**: 2026-03-03 15:00 CST
**作者**: nanobot team
