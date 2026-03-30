#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WeChat Send Message - 微信消息自动发送工具

功能：通过 Python 自动化发送微信消息，支持给任意联系人发送中文消息。
作者：OpenClaw
平台：Mac OS
依赖：pyautogui, pyperclip
"""

import pyautogui
import pyperclip
import time
import Quartz
import subprocess
import sys

# 禁用 pyautogui 安全保护
# 解释：pyautogui 默认在鼠标移到屏幕左上角时抛出异常
#       禁用后可以自由移动鼠标，但请注意不要让鼠标卡在某处
pyautogui.FAILSAFE = False


def get_wechat_bounds():
    """
    获取微信窗口的位置和尺寸

    Returns:
        tuple: (x, y, width, height) 窗口位置和尺寸
        None: 如果找不到微信窗口

    注意：这里没有用到这个函数，但保留作为参考
          可以用于更精确的坐标定位
    """
    options = Quartz.kCGWindowListOptionOnScreenOnly
    window_list = Quartz.CGWindowListCopyWindowInfo(options, Quartz.kCGNullWindowID)

    for win in window_list:
        if '微信' in win.get('kCGWindowOwnerName', ''):
            bounds = win['kCGWindowBounds']
            return (
                int(bounds['X']),
                int(bounds['Y']),
                int(bounds['Width']),
                int(bounds['Height'])
            )
    return None


def clean_window():
    """
    清洁微信窗口状态

    为什么需要清洁窗口？
    - 微信可能打开多个窗口（主窗口、搜索弹窗、聊天窗口等）
    - 上一次搜索可能留下搜索框
    - 上一次操作可能选中了某个聊天

    清洁步骤：
    1. 打开微信窗口
    2. 使用 System Events 发送 Cmd+W 关闭所有子窗口
    3. 重复直到窗口全部关闭
    """
    # 打开微信
    subprocess.run(["open", "-a", "WeChat"])
    time.sleep(0.5)

    # 使用 AppleScript + System Events 精确关闭所有窗口
    # 优点：比循环 pyautogui 更可靠，能精确判断窗口数量
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
        check = '''
        tell application "System Events"
            tell process "WeChat"
                return (count of windows)
            end tell
        end tell
        '''
        result = subprocess.run(['osascript', '-e', check], capture_output=True, text=True)
        try:
            count = int(result.stdout.strip())
            if count == 0:
                break
        except:
            pass

    # 再次打开微信，确保主窗口正常
    subprocess.run(["open", "-a", "WeChat"])
    time.sleep(0.1)


def search_and_select(target_name):
    """
    搜索并选中目标联系人

    Args:
        target_name: 联系人名称（支持中文）

    工作流程：
    1. 按 Escape 确保不在输入模式（避免搜索词发到消息框）
    2. Cmd+F 打开搜索框
    3. 粘贴联系人名称
    4. Enter 确认搜索并打开聊天

    关键点：
    - 使用 pyperclip.copy() 而非 typewrite()，因为 typewrite 不支持中文
    - 操作速度要快（0.05秒），太慢会导致搜索结果变化
    """
    # 将联系人名称复制到剪贴板
    pyperclip.copy(target_name)

    # 按 Escape 确保不在输入模式
    # 解释：如果上一次操作导致光标在消息输入框里，
    #       直接粘贴会发送到当前聊天而不是搜索框
    pyautogui.press('escape')
    time.sleep(0.05)

    # Cmd+F 打开搜索框
    pyautogui.keyDown('command')
    time.sleep(0.05)
    pyautogui.press('f')
    pyautogui.keyUp('command')
    time.sleep(0.05)

    # Cmd+V 粘贴联系人名称
    pyautogui.keyDown('command')
    time.sleep(0.05)
    pyautogui.press('v')
    pyautogui.keyUp('command')

    # 等待搜索结果加载
    # 关键：0.1秒是经验值，太快结果没出来，太慢列表会变化
    time.sleep(0.1)

    # Enter 确认搜索并打开聊天
    pyautogui.press('return')
    time.sleep(0.05)


def send_message(msg):
    """
    发送消息

    Args:
        msg: 要发送的消息内容（支持中文）

    工作流程：
    1. 复制消息到剪贴板
    2. 粘贴消息
    3. 按 Enter 发送
    """
    # 复制消息到剪贴板
    pyperclip.copy(msg)
    time.sleep(0.2)  # 等待剪贴板写入完成，如果太快就会发空消息

    # Cmd+V 粘贴消息
    pyautogui.keyDown('command')
    time.sleep(0.05)
    pyautogui.press('v')
    pyautogui.keyUp('command')
    time.sleep(0.2)  # 等待粘贴完成

    # Enter 发送消息
    pyautogui.press('return')
    time.sleep(0.3)  # 等待消息发送完成


def main():
    """
    主函数

    支持两种使用方式：
    1. 命令行参数：python3 send_wechat.py <联系人> <消息>
    2. 直接修改代码中的 TARGET 和 MESSAGE
    """
    # 解析命令行参数
    if len(sys.argv) >= 3:
        target = sys.argv[1]
        message = sys.argv[2]
    else:
        # 默认测试参数
        target = "文件传输助手"
        message = "这是一条测试消息"

    # 执行发送流程
    clean_window()              # 1. 清洁窗口
    search_and_select(target)  # 2. 搜索并选中
    send_message(message)       # 3. 发送消息

    print(f"✅ 消息已发送: {message} -> {target}")


if __name__ == '__main__':
    main()
