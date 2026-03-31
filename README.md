# macos-wechat-sender

在 Mac 上通过 Python 自动化发送微信消息的工具。

## 功能

- ✅ 支持给任意微信联系人发送消息
- ✅ 支持中文消息
- ✅ 支持文件发送
- ✅ 支持公众号文章卡片转发（EasyOCR 自动化）
- ✅ 跨平台支持（仅限 macOS）
- ✅ 简单易用的 API

## 前置要求

- macOS 操作系统
- 已安装并登录微信桌面客户端
- Python 3.7+
- ⚠️ **必须关闭 macOS 微信通知权限**（系统设置 → 通知 → 微信 → 关闭）
  - 原因：微信通知弹窗会遮挡 UI 元素，导致自动化脚本点击位置偏移或点击到错误的按钮
  - 此为用户手动配置（2026-03-31）

## 安装

### 1. 克隆项目

```bash
git clone https://github.com/yunkai/macos-wechat-sender.git
cd macos-wechat-sender
```

### 2. 安装依赖

```bash
pip3 install pyautogui pyperclip easyocr numpy pillow
```

## 使用方法

### 命令行使用

```bash
python3 scripts/send_wechat.py <联系人> <消息>

# 示例
python3 scripts/send_wechat.py 文件传输助手 你好
python3 scripts/send_wechat.py 小明 -f /path/to/file.pdf
```

🚨 **重要提醒**：使用前请确保「联系人」的名称完全正确，否则可能会发送给错误的对象！

### 作为模块导入

```python
from scripts.send_wechat import clean_window, search_and_select, send_message

# 清洁窗口（每次发送前必须执行）
clean_window()

# 搜索并选中联系人
search_and_select("联系人名称")

# 发送消息
send_message("消息内容")
```

## 工作原理

1. **clean_window()** - 打开微信窗口，先按 Escape 关闭浮窗，再关闭所有子窗口，确保窗口状态干净
2. **search_and_select(target_name)** - Cmd+F 打开搜索框，粘贴并搜索联系人名称，Enter 打开聊天
3. **send_message(msg)** - 粘贴消息内容，Enter 发送文本消息
4. **send_file(file_path)** - osascript 复制文件到剪贴板，Cmd+V 粘贴，Enter 发送文件
5. **forward_article_via_browser(url, target)** - 发送链接到跳板联系人 → EasyOCR 定位 URL 单击打开文章 → 转发菜单 → 搜索目标联系人 → 发送按钮，文章以卡片形式发出

## 公众号文章卡片转发

使用 `--forward-article` 参数，可将公众号文章以**卡片形式**转发给指定联系人：

```bash
python3 scripts/send_wechat.py 阅品阁休息茶室 --url "https://mp.weixin.qq.com/s/xxx"
```

## 关键技术点

| 技术 | 说明 |
|------|------|
| `pyautogui` | 模拟键盘鼠标操作 |
| `pyperclip` | 解决中文输入问题 |
| `osascript` | 精确关闭微信窗口、复制文件到剪贴板 |
| `subprocess` | 启动和管理应用 |

### 文件发送原理

文件发送的核心是使用 osascript 将文件复制到剪贴板：

```python
script = f'set the clipboard to (POSIX file "{abs_file_path}")'
subprocess.run(['osascript', '-e', script])
```

然后在微信聊天框中 Cmd+V 粘贴，文件就会作为微信文件消息发送。

## 常见问题

### Q: 消息发空了怎么办？
A: 检查 `send_message()` 中的 `pyperclip.copy()` 后是否等了足够的 `time.sleep(0.2)`。

### Q: 搜索词粘贴到了消息框怎么办？
A: `search_and_select()` 开始时会按 Escape 确保不在输入模式。

### Q: 消息发错了联系人怎么办？
A: 每次发送前请确保执行了 `clean_window()`。

### Q: 如何发送文件？
A: 使用 `-f` 选项：`python3 scripts/send_wechat.py 小明 -f /path/to/file.pdf`

## 版本历史

- **v1.5.0** - 新增公众号文章卡片转发功能（EasyOCR URL 识别 + 转发浮窗自动化）
- **v1.2.0** - 初始版本，支持文本消息发送

## 项目结构

```
macos-wechat-sender/
  - README.md          (本文件)
  - SKILL.md           (OpenClaw 技能说明)
  - scripts/
      send_wechat.py  (发送脚本)
```

## 在 OpenClaw 等 Agent 中使用

此项目可以作为 OpenClaw 或其他 AI Agent 的 Skill 来使用。

### 方法一：放入 OpenClaw Skills 目录

```bash
# 复制到 OpenClaw 工作空间
cp -r macos-wechat-sender ~/.openclaw/workspace/skills/

# 或者创建软链接
ln -s $(pwd)/macos-wechat-sender ~/.openclaw/workspace/skills/macos-wechat-sender
```

### 方法二：触发关键词

当对 OpenClaw 说以下内容时，会触发此技能：

- "发送微信消息"
- "给 XXX 发微信消息"
- "给 XXX 发文件"
- "微信自动发送"
- "通过 Python 发送微信消息" "

### 方法三：直接调用脚本

```bash
python3 scripts/send_wechat.py <联系人> <消息>
```

### 方法四：给 AI 一个提示词让它安装

直接把以下提示词发给 AI：

```
请安装 macos-wechat-sender 这个 Skill：
- 项目地址：https://github.com/yunkai/macos-wechat-sender
- 功能：在 Mac 上自动化发送微信消息
- 安装步骤：
  1. git clone https://github.com/yunkai/macos-wechat-sender.git
  2. cd macos-wechat-sender
  3. pip3 install pyautogui pyperclip
  4. 复制到 ~/.openclaw/workspace/skills/macos-wechat-sender
```

### OpenClaw Skill 配置示例 (SKILL.md)

SKILL.md 已包含完整的技能说明，OpenClaw 会自动识别。

## License

MIT License

## 作者

- **Yunkai** - [GitHub](https://github.com/yunkai)
- **OpenClaw**
- **MiniMax-M2.7-highspeed**
