#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WeChat Send Message - 微信消息自动发送工具

功能：通过 Python 自动化发送微信消息，支持给任意联系人发送中文消息和文件。
作者：Yunkai, OpenClaw, MiniMax-M2.7-highspeed
平台：Mac OS
依赖：pyautogui, pyperclip
"""

import pyautogui
import pyperclip
import time
import Quartz
import subprocess
import sys
import os
import argparse

# 禁用 pyautogui 安全保护
pyautogui.FAILSAFE = False


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
    1. 按 Escape 确保不在输入模式
    2. Cmd+F 打开搜索框
    3. 粘贴联系人名称
    4. Enter 确认搜索并打开聊天
    """
    # 将联系人名称复制到剪贴板
    pyperclip.copy(target_name)

    # 按 Escape 确保不在输入模式
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
    time.sleep(0.1)

    # Enter 确认搜索并打开聊天
    pyautogui.press('return')
    time.sleep(0.05)


def send_message(msg):
    """
    发送文本消息

    Args:
        msg: 要发送的消息内容（支持中文）
    """
    # 复制消息到剪贴板
    pyperclip.copy(msg)
    time.sleep(0.2)

    # Cmd+V 粘贴消息
    pyautogui.keyDown('command')
    time.sleep(0.05)
    pyautogui.press('v')
    pyautogui.keyUp('command')
    time.sleep(0.2)

    # Enter 发送消息
    pyautogui.press('return')
    time.sleep(0.3)


def send_file(file_path):
    """
    发送文件（通过剪贴板粘贴）

    Args:
        file_path: 要发送的文件路径（支持绝对路径和相对路径）

    工作流程：
    1. 确保文件路径是绝对路径
    2. 用 osascript 将文件复制到剪贴板
    3. 在聊天框中 Cmd+V 粘贴文件
    4. 按 Enter 发送
    """
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return False

    # 转换为绝对路径
    abs_file_path = os.path.abspath(file_path)

    # 用 osascript 将文件复制到剪贴板
    script = f'set the clipboard to (POSIX file "{abs_file_path}")'
    subprocess.run(['osascript', '-e', script])
    time.sleep(1) #等久一点，大文件可能要复制更多时间

    # Cmd+V 粘贴文件
    pyautogui.keyDown('command')
    time.sleep(0.05)
    pyautogui.press('v')
    pyautogui.keyUp('command')
    time.sleep(0.5)

    # 按 Enter 发送
    pyautogui.press('return')
    time.sleep(0.3)

    return True


def main():
    parser = argparse.ArgumentParser(
        description='微信消息自动发送工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
使用示例：
  python3 send_wechat.py 文件传输助手 你好
  python3 send_wechat.py 小明 -f /path/to/file.pdf
  python3 send_wechat.py 小明 你好 -f document.docx

注意：使用 -f 发送文件时，请确保文件路径是绝对路径。
        '''
    )

    parser.add_argument('contact', help='联系人名称')
    parser.add_argument('message', nargs='?', default=None, help='要发送的消息内容')
    parser.add_argument('-f', '--file', dest='file_path', help='要发送的文件路径')

    args = parser.parse_args()

    # 检查参数
    if not args.message and not args.file_path:
        parser.error('请提供消息内容或文件路径')

    # 执行发送流程
    clean_window()
    search_and_select(args.contact)

    if args.file_path:
        # 发送文件
        if send_file(args.file_path):
            print(f"✅ 文件已发送: {args.file_path} -> {args.contact}")
        else:
            print(f"❌ 文件发送失败")
    else:
        # 发送消息
        send_message(args.message)
        print(f"✅ 消息已发送: {args.message} -> {args.contact}")


if __name__ == '__main__':
    main()
