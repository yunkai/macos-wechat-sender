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
import numpy as np
from PIL import Image

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


def find_green_bubble_and_click():
    """
    通过截图分析，找到微信聊天窗口中最新的绿色消息气泡，
    并计算点击位置（气泡偏下区域，URL文字通常在这里）。

    工作流程：
    1. 用 open -a WeChat 激活微信到前台
    2. 用 CGWindowListCopyWindowInfo 获取微信窗口的真实屏幕坐标
    3. 截取全屏截图，在微信窗口区域内找绿色气泡
    4. 计算点击坐标并双击

    Returns:
        tuple: (x, y) 屏幕坐标，点击失败返回 None
    """
    import numpy as np
    from PIL import Image

    # Step 1: 激活微信到前台
    subprocess.run(["open", "-a", "WeChat"])
    time.sleep(0.5)

    # Step 2: 用 CGWindowListCopyWindowInfo 获取微信窗口的真实屏幕坐标
    kExcludeDesktopElements = 2
    kOnScreenOnly = 1
    window_list = Quartz.CGWindowListCopyWindowInfo(
        kExcludeDesktopElements | kOnScreenOnly, Quartz.kCGNullWindowID
    )

    wechat_wins = []
    for win in window_list:
        owner = win.get("kCGWindowOwnerName", "")
        if "WeChat" in owner or "微信" in owner:
            b = win.get("kCGWindowBounds", {})
            x, y = b.get("X", 0), b.get("Y", 0)
            w, h = b.get("Width", 0), b.get("Height", 0)
            layer = win.get("kCGWindowLayer", 0)
            if w > 100 and h > 100:  # 过滤掉很小的窗口
                wechat_wins.append((x, y, w, h, layer))

    if not wechat_wins:
        print("未找到微信窗口")
        return None

    # 按面积排序，取最大的窗口（主窗口）
    wechat_wins.sort(key=lambda w: w[2] * w[3], reverse=True)
    wx, wy, ww, wh = wechat_wins[0][:4]
    print(f"微信主窗口: ({wx},{wy}) {ww}x{wh}")

    # Step 3: 截取全屏截图
    subprocess.run([
        "peekaboo", "image", "--mode", "screen", "--path", "/tmp/wechat_bubble.png"
    ])

    # Step 4: 分析截图，在微信窗口区域内找绿色气泡
    img = Image.open("/tmp/wechat_bubble.png").convert("RGB")
    arr = np.array(img, dtype=np.int32)
    screen_h, screen_w = arr.shape[:2]

    # 确定扫描区域（排除左侧栏约 25% 宽度）
    scan_x1 = int(wx + ww * 0.25)
    scan_x2 = int(wx + ww - 10)
    scan_y1 = int(wy + 50)
    scan_y2 = int(wy + wh - 30)

    greens = []
    for y in range(scan_y1, min(scan_y2, screen_h - 5), 2):
        for x in range(scan_x1, min(scan_x2, screen_w - 5), 2):
            r, g, b = arr[y, x, 0], arr[y, x, 1], arr[y, x, 2]
            if g > r + 25 and g > b + 25 and 120 < g < 225 and r < 180 and b < 180:
                greens.append((x, y))

    if not greens:
        print("未找到绿色气泡")
        return None

    # 按 y 降序，找最新消息（y 最大）
    greens.sort(key=lambda p: p[1], reverse=True)
    top_y = greens[0][1]

    # 取 top_y 附近的消息（最新一条）
    latest = [(x, y) for x, y in greens if y >= top_y - 80]

    if not latest:
        return None

    xs = [p[0] for p in latest]
    ys = [p[1] for p in latest]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)

    print(f"气泡区域(屏幕): x={x_min}-{x_max}, y={y_min}-{y_max}")

    # URL 文字在气泡偏下、偏右的位置
    click_x = int(x_min + (x_max - x_min) * 0.80)
    click_y = int(y_min + (y_max - y_min) * 0.70)

    print(f"计算点击位置(屏幕): ({click_x}, {click_y})")

    return (click_x, click_y)


def get_mouse_position():
    """
    获取当前鼠标的屏幕坐标

    Returns:
        tuple: (x, y) 屏幕坐标
    """
    p = Quartz.CGEventGetLocation(Quartz.CGEventCreate(None))
    return (p.x, p.y)


def open_link_in_browser(via_contact="文件传输助手"):
    """
    打开微信内置浏览器的文章页面。

    工作流程：
    1. 确保在 via_contact 的聊天窗口中
    2. 自动分析截图，找到最新的绿色消息气泡
    3. 在气泡区域计算点击坐标并双击打开文章

    Args:
        via_contact: 作为跳板的联系人（默认"文件传输助手"）

    Returns:
        bool: 是否成功打开了内置浏览器
    """
    # 激活微信
    subprocess.run(["open", "-a", "WeChat"])
    time.sleep(0.3)

    # 搜索并选中跳板联系人
    search_and_select(via_contact)
    time.sleep(0.5)

    # 自动找气泡并点击
    pos = find_green_bubble_and_click()
    if pos is None:
        print("⚠️ 未找到链接气泡，请手动点击")
        return False

    x, y = pos
    print(f"双击中...")
    for _ in range(2):
        e_down = Quartz.CGEventCreateMouseEvent(
            None, Quartz.kCGEventLeftMouseDown, (x, y), Quartz.kCGMouseButtonLeft
        )
        e_up = Quartz.CGEventCreateMouseEvent(
            None, Quartz.kCGEventLeftMouseUp, (x, y), Quartz.kCGMouseButtonLeft
        )
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, e_down)
        time.sleep(0.05)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, e_up)
        time.sleep(0.1)

    print("✅ 已双击，等待文章页面加载...")
    time.sleep(3)
    return True


def send_link(url, wait=2.5):
    """
    发送链接（URL），微信会自动生成预览卡片

    Args:
        url: 要发送的链接
        wait: 等待预览卡片生成的秒数
    """
    pyperclip.copy(url)
    time.sleep(0.2)
    pyautogui.keyDown('command')
    time.sleep(0.05)
    pyautogui.press('v')
    pyautogui.keyUp('command')
    time.sleep(wait)
    pyautogui.press('return')
    time.sleep(0.3)


def find_and_click_element(label_pattern, regex=False):
    """
    通过 peekaboo 查找匹配 label 的元素并点击

    Args:
        label_pattern: 要匹配的 label 文本（或正则表达式）
        regex: 是否使用正则匹配
    Returns:
        bool: 是否成功
    """
    import json
    cmd = ["peekaboo", "see", "--app", "微信", "--json"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return False

    try:
        data = json.loads(result.stdout)
    except:
        return False

    for item in data if isinstance(data, list) else []:
        label = item.get("label", "")
        element_id = item.get("id")
        frame = item.get("frame")
        if not label or not element_id or not frame:
            continue
        if label_pattern in label:
            x, y = frame.get("x", 0), frame.get("y", 0)
            pyautogui.click(x + 5, y + 5)
            time.sleep(0.3)
            return True
    return False


def forward_article_via_browser(article_url, target_contact, via_contact="文件传输助手"):
    """
    通过微信内置浏览器转发公众号文章给指定联系人（卡片形式）

    流程：
    1. 发送文章链接到跳板联系人（默认文件传输助手）
    2. 用户将鼠标悬停到链接上，程序读取坐标并双击打开文章
    3. 点击"转发"按钮
    4. 在转发弹窗中搜索目标联系人并发送

    Args:
        article_url: 公众号文章的 URL
        target_contact: 要转发给谁（联系人名称）
        via_contact: 作为跳板的中间联系人（默认"文件传输助手"）
    Returns:
        bool: 是否成功
    """
    print(f"📤 正在将文章转发给 {target_contact}...")

    # Step 1: 发送链接到跳板联系人
    print(f"  [1/5] 发送链接到 {via_contact}...")
    clean_window()
    search_and_select(via_contact)
    send_link(article_url)
    print(f"  [1/5] ✅ 链接已发送")

    # Step 2: 自动找气泡并双击打开链接
    print("  [2/5] 自动定位链接位置...")
    pos = find_green_bubble_and_click()
    if pos is None:
        print("  [2/5] ⚠️ 未找到链接，请手动点击")
        return False
    x, y = pos
    print(f"  双击中 ({x}, {y})...")
    for _ in range(2):
        e_down = Quartz.CGEventCreateMouseEvent(
            None, Quartz.kCGEventLeftMouseDown, (x, y), Quartz.kCGMouseButtonLeft
        )
        e_up = Quartz.CGEventCreateMouseEvent(
            None, Quartz.kCGEventLeftMouseUp, (x, y), Quartz.kCGMouseButtonLeft
        )
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, e_down)
        time.sleep(0.05)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, e_up)
        time.sleep(0.1)
    print("  [2/5] ✅ 已点击链接，等待文章页面加载...")
    time.sleep(3)

    # Step 3: 点击右上角"..."按钮，在菜单中选"转发给朋友"
    print("  [3/5] 点击右上角菜单按钮...")

    # 先关闭通知中心
    subprocess.run(["killall", "NotificationCenter"])
    time.sleep(0.2)

    # 激活微信
    subprocess.run(["open", "-a", "WeChat"])
    time.sleep(0.3)

    # 获取"微信(窗口)"的边界
    kExcludeDesktopElements = 2
    kOnScreenOnly = 1
    window_list = Quartz.CGWindowListCopyWindowInfo(kExcludeDesktopElements | kOnScreenOnly, Quartz.kCGNullWindowID)

    win_x, win_y, win_w, win_h = None, None, None, None
    for win in window_list:
        owner = win.get("kCGWindowOwnerName", "")
        name = win.get("kCGWindowName", "")
        if ("WeChat" in owner or "微信" in owner) and "窗口" in name:
            b = win.get("kCGWindowBounds", {})
            win_x, win_y = b.get("X"), b.get("Y")
            win_w, win_h = b.get("Width"), b.get("Height")
            break

    if win_x is None:
        # 等待浏览器窗口出现，重试3次
        for retry in range(3):
            time.sleep(1)
            window_list = Quartz.CGWindowListCopyWindowInfo(kExcludeDesktopElements | kOnScreenOnly, Quartz.kCGNullWindowID)
            for win in window_list:
                owner = win.get("kCGWindowOwnerName", "")
                name = win.get("kCGWindowName", "")
                if ("WeChat" in owner or "微信" in owner) and "窗口" in name:
                    b = win.get("kCGWindowBounds", {})
                    win_x, win_y = b.get("X"), b.get("Y")
                    win_w, win_h = b.get("Width"), b.get("Height")
                    print(f"  重试找到窗口: ({win_x},{win_y}) {win_w}x{win_h}")
                    break
            if win_x:
                break

    if win_x is None:
        print("  [3/5] ⚠️ 未找到微信浏览器窗口")
        return False

    # 用相对比例计算"..."按钮位置
    # x = 98.3%窗口宽度, y = 窗口顶部+20像素
    dot_x = int(win_x + win_w * 0.983)
    dot_y = int(win_y + 20)

    print(f"  窗口: ({win_x},{win_y}) {win_w}x{win_h}")
    print(f"  点击菜单按钮: ({dot_x}, {dot_y})")

    # 先把鼠标移到窗口中央，等1秒让通知消失
    move = Quartz.CGEventCreateMouseEvent(
        None, Quartz.kCGEventMouseMoved, (int(win_x + win_w // 2), int(win_y + win_h // 2)), Quartz.kCGMouseButtonLeft
    )
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, move)
    time.sleep(1)

    # 点击"..."按钮
    print(f"  点击菜单按钮 ({dot_x}, {dot_y})...")
    e_down = Quartz.CGEventCreateMouseEvent(
        None, Quartz.kCGEventLeftMouseDown, (dot_x, dot_y), Quartz.kCGMouseButtonLeft
    )
    e_up = Quartz.CGEventCreateMouseEvent(
        None, Quartz.kCGEventLeftMouseUp, (dot_x, dot_y), Quartz.kCGMouseButtonLeft
    )
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, e_down)
    time.sleep(0.05)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, e_up)
    time.sleep(0.8)  # 等待菜单出现

    # 按向下键选中"转发给朋友"，按回车确认
    print("  选择「转发给朋友」...")
    pyautogui.press('down')
    time.sleep(0.3)
    pyautogui.press('return')
    time.sleep(1)
    print("  [3/5] ✅ 已打开转发浮窗")

    # Step 4: 在转发弹窗中搜索目标联系人
    print(f"  [4/5] 在转发弹窗中搜索联系人: {target_contact}...")
    time.sleep(0.8)

    pyperclip.copy(target_contact)
    time.sleep(0.2)

    # Cmd+F 打开搜索框
    pyautogui.keyDown('command')
    time.sleep(0.05)
    pyautogui.press('f')
    pyautogui.keyUp('command')
    time.sleep(0.1)

    # 粘贴联系人名称
    pyautogui.keyDown('command')
    time.sleep(0.05)
    pyautogui.press('v')
    pyautogui.keyUp('command')
    time.sleep(0.2)

    # 键盘向下键选中第一个结果
    pyautogui.press('down')
    time.sleep(0.1)
    # 回车确认选中
    pyautogui.press('return')
    time.sleep(0.3)
    print("  [4/5] ✅ 已选中介联系人")

    # Step 5: 点击发送按钮
    print("  [5/5] 点击发送按钮...")
    time.sleep(0.5)

    result3 = subprocess.run(
        ["peekaboo", "see", "--app", "微信", "--json"],
        capture_output=True, text=True
    )
    send_clicked = False
    if result3.returncode == 0:
        try:
            elements = json.loads(result3.stdout)
            for el in elements if isinstance(elements, list) else []:
                label = el.get("label", "")
                frame = el.get("frame")
                if frame and ("发送" in label or "send" in label.lower()):
                    x, y = frame["x"] + 5, frame["y"] + 5
                    pyautogui.click(x, y)
                    send_clicked = True
                    print("  [5/5] ✅ 已点击发送按钮")
                    break
        except:
            pass

    if not send_clicked:
        print("  [5/5] ⚠️ 未自动找到发送按钮，请手动点击")
        return False

    print(f"✅ 转发成功！文章已以卡片形式发送给 {target_contact}")
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
  python3 send_wechat.py --forward-article "https://mp.weixin.qq.com/s/xxx" 目标联系人

注意：使用 -f 发送文件时，请确保文件路径是绝对路径。
        '''
    )

    parser.add_argument('contact', nargs='?', help='联系人名称')
    parser.add_argument('message', nargs='?', default=None, help='要发送的消息内容')
    parser.add_argument('-f', '--file', dest='file_path', help='要发送的文件路径')
    parser.add_argument('--forward-article', dest='article_url', help='要转发的公众号文章URL')
    parser.add_argument('--via', dest='via_contact', default='文件传输助手',
                        help='作为跳板的中间联系人（默认文件传输助手）')

    args = parser.parse_args()

    # 转发文章模式
    if args.article_url:
        if not args.contact:
            parser.error('转发模式需要指定目标联系人')
        forward_article_via_browser(args.article_url, args.contact)
        return

    # 检查参数
    if not args.contact:
        parser.error('请提供联系人名称')
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
