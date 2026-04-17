---
name: wechat-send-message
description: 在 Mac 上通过 Python pyautogui 自动化发送微信消息，支持发送文本消息、文件、公众号文章卡片转发，以及转发后引用消息。触发场景：用户说"发送微信消息"、"给 XXX 发消息"、"给 XXX 发文件"、"微信自动发送"、"转发文章"、"给 XXX 发文章"、"转发文章并引用"、或需要通过 Python 代码控制微信发送消息或文件。
version: 1.14.0
---

# WeChat Send Message v1.14.0

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
4. **通知已关闭** - ⚠️ **必须手动关闭 macOS 微信通知权限**（系统设置 → 通知 → 微信 → 关闭）
   - 原因：微信通知弹窗会遮挡 UI 元素，导致自动化脚本点击位置偏移或点击到错误的按钮
   - 此为用户手动配置（2026-03-31）

## 工作流程

1. **clean_window()** - 打开微信窗口，先按 Escape 关闭浮窗，再用 Cmd+W 关闭所有子窗口，确保窗口处于干净状态
2. **search_and_select(target_name)** - 按 Escape 确保不在输入模式，Cmd+F 打开搜索框，粘贴联系人名称并搜索，Enter 打开聊天
3. **send_message(msg)** - 粘贴消息内容，Enter 发送文本消息
4. **send_file(file_path)** - osascript 复制文件到剪贴板，Cmd+V 粘贴，Enter 发送文件
5. **forward_article_via_browser(url, target)** - 发送链接到跳板联系人 → RapidOCR 定位 URL 单击打开文章 → 转发菜单 → 搜索目标联系人 → 发送按钮，文章以卡片形式发出
6. **forward_article_with_quote(url, target, quote_msg)** - 在 forward_article_via_browser 基础上，额外在目标聊天窗口找到卡片 → 右键选择「引用」→ 在引用输入框中发送指定文本

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
        # 先按 Escape 关闭浮窗（如转发浮窗无法用 Cmd+W 直接关闭）
        escape_script = '''
        tell application "System Events"
            tell process "WeChat"
                set frontmost to true
                key code 53
            end tell
        end tell
        '''
        subprocess.run(['osascript', '-e', escape_script])
        time.sleep(0.3)

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
pip3 install pyautogui pyperclip rapidocr numpy pillow
```

⚠️ **注意**：微信桌面客户端必须是已登录状态，此脚本才能正常发送消息。

## 项目结构

```
macos-wechat-sender/
├── SKILL.md                 # 技能说明文档
├── README.md                # 项目说明文档
├── scripts/
│   ├── send_wechat.py       # 可执行的发送脚本
│   └── test_send_wechat.py  # 回归测试
└── tests/
    └── test.pdf             # 测试用PDF文件
```

## 转发公众号文章（卡片形式）

微信公众号文章的链接直接粘贴到微信里只会显示普通文本链接，无法生成卡片。如果需要以**卡片式链接**转发文章，必须通过微信内置浏览器的转发功能。

### 原理

微信内置浏览器打开文章后，文章页面会有一个「转发」按钮。点击转发后，选择联系人并发送，微信会自动生成带缩略图和标题的卡片样式。

### 工作流程

1. **发送链接到跳板联系人**（默认用"文件传输助手"）
2. **自动定位**：程序截图后用 RapidOCR 识别聊天中的 URL 文字区域，计算 URL 中心位置，单击打开文章（完全自动，无需人工干预）
3. **点击"..."菜单** → 选择"转发给朋友"，弹出转发浮窗
4. **在浮窗中搜索目标联系人** → Cmd+F 打开搜索 → 粘贴联系人名称 → 向下键选中 → 回车确认
5. **点击"发送"按钮**（RapidOCR 精确识别"发送"文字位置），文章以卡片形式发出

### 命令行使用

```bash
python3 send_wechat.py <目标联系人> -l "https://mp.weixin.qq.com/s/xxx"

# 示例：将文章转发给"老王"
python3 send_wechat.py 老王 --url "https://mp.weixin.qq.com/s/abc123"

# 通过其他联系人作为跳板（默认是文件传输助手）
python3 send_wechat.py 老王 -l "https://mp.weixin.qq.com/s/abc123" --via 文件传输助手
```

### 作为模块导入

```python
from send_wechat import forward_article_via_browser

# 将文章转发给指定联系人（卡片形式）
forward_article_via_browser(
    article_url="https://mp.weixin.qq.com/s/abc123",
    target_contact="老王"
)
```

### 转发文章+引用消息

使用 `forward_article_with_quote` 函数，可以将文章卡片转发后，引用该卡片发送一条文本消息。

**使用场景**：
- 转发文章时附带推荐语或说明
- 需要引用原卡片内容再发表观点

**工作流程**：
1. 将文章卡片转发给目标联系人
2. 在目标聊天窗口中找到刚发送的卡片
3. 右键点击卡片，选择「引用」
4. 在引用输入框中输入指定文本并发送

**命令行使用**：
```bash
python3 send_wechat.py 老王 -l "https://mp.weixin.qq.com/s/xxx" -q "这篇文章写得很好，推荐看看"
```

**作为模块导入**：
```python
from send_wechat import forward_article_with_quote

# 转发文章并引用消息
forward_article_with_quote(
    article_url="https://mp.weixin.qq.com/s/abc123",
    target_contact="老王",
    quote_message="这篇文章写得很好，推荐看看"
)
```

**卡片检测原理**：
1. 使用 RapidOCR 识别聊天中的文章标题（含「《」符号）
2. 检查标题周围背景颜色（白色=卡片，彩色气泡=普通文字消息）
3. 取右侧区域（我的卡片在右侧）+ Y坐标最大（最新消息）
4. 计算卡片中心位置（标题下方约50像素）

⚠️ **注意事项**
- `-l` / `--url` 模式下，`联系人` 参数是**转发目标**，不是跳板联系人
- 跳板联系人默认是"文件传输助手"，可通过 `--via` 参数修改
- 步骤2（点击链接）完全自动化：程序通过 RapidOCR 识别聊天中的 URL 文字区域，单击打开文章
- `-q` / `--quote` 必须在 `-l` / `--url` 模式下使用
- 如果未找到卡片，函数会返回 False 并不发送引用消息
- 此功能依赖 CGEvent（Quartz）、CGWindowListCopyWindowInfo 和 RapidOCR
- 首次使用 RapidOCR 会下载模型（约 300MB），后续调用直接复用

## 使用方法

### 命令行使用
```bash
python3 send_wechat.py <联系人> <消息>

# 示例
python3 send_wechat.py 文件传输助手 你好
python3 send_wechat.py 小明 -f /path/to/file.pdf
python3 send_wechat.py 家人群 -l "https://mp.weixin.qq.com/s/xxx"
python3 send_wechat.py 老王 -l "https://mp.weixin.qq.com/s/xxx" -q "这篇文章写得很好，推荐看看"
```

⚠️ **重要提醒**：使用前请确保「联系人」的名称完全正确，否则可能会发送给错误的对象！

### 作为模块导入
```python
from send_wechat import clean_window, search_and_select, send_message, send_file
from send_wechat import forward_article_via_browser, forward_article_with_quote

# 发送文本消息
send_message("你好")

# 发送文件
send_file("/path/to/file.pdf")

# 转发文章（卡片形式）
forward_article_via_browser(
    article_url="https://mp.weixin.qq.com/s/abc123",
    target_contact="老王"
)

# 转发文章并引用消息
forward_article_with_quote(
    article_url="https://mp.weixin.qq.com/s/abc123",
    target_contact="老王",
    quote_message="这篇文章写得很好，推荐看看"
)
```

## 常见问题

### Q: 消息发空了怎么办？
A: 检查 `send_message()` 中的 `pyperclip.copy()` 后是否等了足够的 `time.sleep(0.2)`。太短会导致剪贴板内容还没写入。

### Q: 搜索词粘贴到了消息框怎么办？
A: 在 `search_and_select()` 开始时按了 Escape，确保不在输入模式。

### Q: 消息发错了联系人怎么办？
A: 检查是否每次都执行了 `clean_window()`，窗口状态可能混乱了。

### Q: 如何发送文件？
A: 使用 `-f` 选项：`python3 send_wechat.py 小明 -f /path/to/file.pdf`

### Q: skill_view 找不到这个 skill 怎么办？
A: 这个 skill 的目录名是 `macos-wechat-sender`，而 front matter 中的 `name: wechat-send-message` 是展示名。直接用目录名调用：
```bash
skill_view(name='macos-wechat-sender')
```

### Q: 外部脚本 import 报错 `ModuleNotFoundError: No module named 'send_wechat'`？
A: 这是因为 skill 的安装路径变了。**正确路径**是 `~/.hermes/skills/openclaw-imports/macos-wechat-sender/scripts`（注意不是 `~/.openclaw/workspace/skills/...`）。

正确的 import 方式：
```python
import os
import sys

SKILL_DIR = os.path.expanduser('~/.hermes/skills/openclaw-imports/macos-wechat-sender/scripts')
sys.path.insert(0, SKILL_DIR)

from send_wechat import forward_article_with_quote

# 使用
forward_article_with_quote(
    article_url="https://mp.weixin.qq.com/s/xxx",
    target_contact="果光",
    quote_message="师兄们早安[太阳][合十]，今日共读共修："
)
```

⚠️ **警惕路径陷阱**：如果脚本里有 `~/.openclaw/workspace/skills/macos-wechat-sender/scripts` 这个路径，它是**旧的**，需要改成 `~/.hermes/skills/openclaw-imports/macos-wechat-sender/scripts`。

### Q: 支持语音消息吗？
A: 不支持。语音消息需要更复杂的原生接口支持。

### Q: 通过 cron 或 isolated agent 运行时，peekaboo 报 "Screen recording permission is required"？
A: 这是 TCC（Transparency, Consent, and Control）权限问题。`peekaboo` 截图工具需要屏幕录制权限。当通过 cron 定时任务或 Hermes isolated agent node 运行时，需要额外授权：

1. **确定 node 路径**：`which node` 或 `ls -la /opt/homebrew/bin/node`（Homebrew 安装的 node 是符号链接）
2. **添加到屏幕录制白名单**：打开 **系统设置 → 隐私与安全性 → 屏幕录制**，点击 + 添加对应的 node 可执行文件
   - 如果用 cron 触发：添加 `/opt/homebrew/bin/node`（或实际 node 路径，如 `/opt/homebrew/Cellar/node/xx.x.x/bin/node`）
   - 如果用 Hermes isolated agent：需要给 hermes-agent 的 node 进程授权
3. **TCC 缓存需要登出/登录才能生效**：仅添加权限可能不够，需要完全登出后重新登录 macOS
4. **验证方法**：手动运行 `peekaboo image --mode screen --path /tmp/test.png`，如果成功说明权限已生效

⚠️ 注意：macOS TCC 权限是针对 .app bundle 授予的，CLI 工具（如 `peekaboo`）本身无法被系统识别为"已授权应用"。正确做法是给**启动 CLI 的解释器或 agent 进程**（即 node）授予屏幕录制权限。

### Q: 转发文章时报"未找到微信浏览器窗口"？
A: 这是 `wait_for_browser_window()` 函数的时机问题，**不是窗口名检测问题**。调试经验（2026-04-17）：

**已确认的事实**：
- 微信内置浏览器窗口名**确实包含"窗口"**，原文是 `微信 (窗口)`
- 原检测逻辑 `and "窗口" in name` **本身是正确的**，无需修改

**真正原因**：单击链接打开浏览器窗口后，在等待期间执行了 `open -a WeChat` 或第二次点击把聊天主窗口又激活到最前面，把刚打开的浏览器窗口盖住了。

**修复方法**：
1. 单击链接即可打开内置浏览器（**不要双击**，第二次点击会触发聊天窗口抢占）
2. 单击后先等 **1.5 秒**再开始轮询，给窗口打开时间
3. 等待期间**不要**执行 `open -a WeChat`，否则会把浏览器窗口盖住
4. 超时保持 **20 秒**

已在 `send_wechat.py` 中修复。如遇此问题，确认 `send_wechat.py` 已更新到最新版本。
