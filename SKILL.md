---
name: wechat-send-message
description: 在 Mac 上通过 Python pyautogui 自动化发送微信消息。触发场景：用户说"发送微信消息"、"给 XXX 发消息"、"微信自动发送"、或需要通过 Python 代码控制微信发送消息。
version: 1.1.1
---

# WeChat Send Message v1.1.1

在 Mac 上自动化发送微信消息的技能。

## 功能概述

通过 Python pyautogui 模拟键盘鼠标操作，实现微信消息的自动发送。
- 支持给任意微信联系人发送消息
- 支持中文消息
- 自动化程度高，仅需几行代码即可完成发送

## 前置要求

⚠️ **重要**：使用此技能前，必须满足以下条件：

1. **已登录微信** - Mac 上已安装并成功登录微信桌面客户端
2. **微信在前台** - 执行期间微信窗口需要保持打开状态
3. **依赖已安装** - `pyautogui` 和 `pyperclip` 已通过 pip 安装

## 工作流程

1. **clean_window()** - 打开微信窗口，使用 AppleScript 关闭所有子窗口，确保窗口处于干净状态
2. **search_and_select(target_name)** - 按 Escape 确保不在输入模式，Cmd+F 打开搜索框，粘贴联系人名称并搜索，Enter 打开聊天
3. **send_message(msg)** - 粘贴消息内容，Enter 发送文本消息
4. **send_file(file_path)** - osascript 复制文件到剪贴板，Cmd+V 粘贴，Enter 发送文件

## 核心代码模板

```python
import pyautogui
import pyperclip
import time
import Quartz
import subprocess
import sys

# 禁用 pyautogui 安全保护
pyautogui.FAILSAFE = False

def clean_window():
    """清洁微信窗口状态"""
    subprocess.run(["open", "-a", "WeChat"])
    time.sleep(0.5)

    # 使用 AppleScript + System Events 精确关闭所有窗口
    for i in range(10):
        script = '''
        tell application "System Events"
            tell process "WeChat"
                set frontmost to true
                keystroke "w" using command down
            end tell
        end tell
        '''
        subprocess.run(['osascript', '-e', script])
        time.sleep(0.05)

        # 检查是否还有窗口
        check = '''...'''
        result = subprocess.run(['osascript', '-e', check], capture_output=True, text=True)
        try:
            count = int(result.stdout.strip())
            if count == 0:
                break
        except:
            pass

    subprocess.run(["open", "-a", "WeChat"])
    time.sleep(0.1)

def search_and_select(target_name):
    """搜索并选中目标联系人"""
    pyperclip.copy(target_name)
    pyautogui.press('escape')
    time.sleep(0.05)

    pyautogui.keyDown('command')
    time.sleep(0.05)
    pyautogui.press('f')
    pyautogui.keyUp('command')
    time.sleep(0.05)

    pyautogui.keyDown('command')
    time.sleep(0.05)
    pyautogui.press('v')
    pyautogui.keyUp('command')
    time.sleep(0.1)  # 关键：等待搜索结果加载，太快太慢都会出问题

    pyautogui.press('return')
    time.sleep(0.05)

def send_message(msg):
    """发送消息"""
    pyperclip.copy(msg)
    time.sleep(0.2)  # 等待剪贴板写入完成，如果太快就会发空消息

    pyautogui.keyDown('command')
    time.sleep(0.05)
    pyautogui.press('v')
    pyautogui.keyUp('command')
    time.sleep(0.2)  # 等待粘贴完成

    pyautogui.press('return')
    time.sleep(0.3)  # 等待消息发送完成

# 使用
TARGET = "联系人名称"  # ⚠️ 必须完全正确，否则会发错人！
MESSAGE = "消息内容"

clean_window()
search_and_select(TARGET)
send_message(MESSAGE)
```

## 关键要点

### 1. 速度是关键
- 所有 `time.sleep` 使用极短时间（0.05~0.2秒）
- 原因：微信搜索结果的第一个条目会随时间变化
- 太慢会导致选错联系人

### 2. 清洁窗口必须执行
- 每次发送前必须调用 `clean_window()`
- 使用 AppleScript + System Events 精确关闭所有窗口
- 比循环发送 Cmd+W 更可靠

### 3. 使用 pyperclip 而非 typewrite
- `pyautogui.typewrite()` 不支持中文
- `pyperclip` + `Cmd+V` 可以完美解决中文输入问题

### 4. 剪贴板等待时间
- `pyperclip.copy()` 后至少等待 **0.2 秒**
- 太短会导致剪贴板内容还没写入，粘贴出来是空的
- 这是发送空消息的常见原因

### 5. 关闭窗口的优化
- 使用 `osascript` + `System Events` 向微信进程发送 Cmd+W
- 每次发送后检查窗口数量，确保全部关闭
- 比纯 pyautogui 循环更精确可靠

### 6. 文件发送原理
- 使用 osascript 将文件直接复制到剪贴板
- 然后在微信中 Cmd+V 粘贴即可发送文件
- 大文件需要等待更长时间（1秒）确保复制完成

## 依赖安装

```bash
# 安装 Python 依赖
pip3 install pyautogui pyperclip
```

⚠️ **注意**：微信桌面客户端必须是已登录状态，此脚本才能正常发送消息。

## 项目结构

```
wechat-send-message/
├── SKILL.md              # 技能说明文档
└── scripts/
    └── send_wechat.py    # 可执行的发送脚本
```

## 使用方法

### 命令行使用
```bash
python3 send_wechat.py <联系人> <消息>

# 示例
python3 send_wechat.py 文件传输助手 你好
python3 send_wechat.py 小明 -f /path/to/file.pdf
python3 send_wechat.py 小明 你好 -f document.docx
```

⚠️ **重要提醒**：使用前请确保「联系人」的名称完全正确，否则可能会发送给错误的对象！

### 作为模块导入
```python
from send_wechat import clean_window, search_and_select, send_message, send_file

# 发送文本消息
send_message("你好")

# 发送文件
send_file("/path/to/file.pdf")

clean_window()
search_and_select("联系人名称")
send_message("消息内容")
```

## 常见问题

### Q: 消息发空了怎么办？
A: 检查 `send_message()` 中的 `pyperclip.copy()` 后是否等了足够的 `time.sleep(0.2)`。太短会导致剪贴板内容还没写入。

### Q: 搜索词粘贴到了消息框怎么办？
A: 在 `search_and_select()` 开始时按了 Escape，确保不在输入模式。

### Q: 消息发错了联系人怎么办？
A: 检查是否每次都执行了 `clean_window()`，窗口状态可能混乱了。

### Q: 如何发送特殊消息（如图片、文件）？
A: 当前版本仅支持文本消息。图片/文件发送需要额外的剪贴板操作。

### Q: 支持语音消息吗？
A: 不支持。语音消息需要更复杂的原生接口支持。
