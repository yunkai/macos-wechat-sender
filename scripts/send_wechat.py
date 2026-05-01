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
import cv2
from PIL import Image

# 全局 RapidOCR 阅读器（启动时初始化一次，比 EasyOCR 快很多）
from rapidocr import RapidOCR
RAPIDOCR_READER = RapidOCR()

# 禁用 pyautogui 安全保护
pyautogui.FAILSAFE = False


def clean_window():
    """
    清洁微信窗口状态（优化版：减少迭代次数和等待时间）

    清洁步骤：
    1. 打开微信窗口
    2. 最多循环3次：Escape 关闭浮窗 + Cmd+W 关闭窗口
    3. 检查是否还有子窗口，没有则提前退出
    """
    # 打开微信
    subprocess.run(["open", "-a", "WeChat"])
    time.sleep(0.3)

    # 最多3次迭代，通常1-2次就能关闭所有窗口
    for i in range(3):
        # 先按 Escape 关闭浮窗
        escape_script = '''
        tell application "System Events"
            tell process "WeChat"
                set frontmost to true
                key code 53
            end tell
        end tell
        '''
        subprocess.run(['osascript', '-e', escape_script])
        time.sleep(0.1)

        # Cmd+W 关闭窗口
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

    # 确保主窗口正常
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
    time.sleep(0.1)

    # 当目标联系人比较久没联系，需要按两次回车才能激活输入窗口
    pyautogui.press('return')
    time.sleep(0.1)


def send_message(msg):
    """
    发送文本消息

    Args:
        msg: 要发送的消息内容（支持中文）
    """
    # 复制消息到剪贴板
    pyperclip.copy(msg)
    time.sleep(0.5)

    # Cmd+V 粘贴消息
    pyautogui.keyDown('command')
    time.sleep(0.05)
    pyautogui.press('v')
    pyautogui.keyUp('command')
    time.sleep(0.5)

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


def find_url_text_and_click(target_url=None):
    """
    通过 RapidOCR 识别截图中的 URL 文字区域，找到目标 URL 的中心点作为点击坐标。

    Args:
        target_url: 要点击的目标 URL（模糊匹配），如果指定则只点击匹配的 URL

    工作流程：
    1. 用 open -a WeChat 激活微信到前台
    2. 截取全屏截图
    3. 用 RapidOCR 识别所有包含 "weixin" 或 "http" 的文字
    4. 如果指定了 target_url，优先找与之匹配的 URL
    5. 否则取 y 坐标最大的（最底部 = 最新消息）的 URL 区域中心作为点击坐标

    Returns:
        tuple: (x, y) 屏幕坐标，点击失败返回 None
    """
    import numpy as np
    from PIL import Image

    # Step 1: 激活微信到前台
    subprocess.run(["open", "-a", "WeChat"])
    time.sleep(0.5)

    # Step 2: 获取微信窗口坐标
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
            if w > 100 and h > 100:
                wechat_wins.append((x, y, w, h))

    if not wechat_wins:
        print("未找到微信窗口")
        return None

    # 取非全屏的普通窗口（排除全屏窗口）
    normal_wins = [w for w in wechat_wins if w[2] < 1400]  # 全屏窗口宽约 1512
    wins_to_use = normal_wins if normal_wins else wechat_wins
    wins_to_use.sort(key=lambda w: w[2] * w[3], reverse=True)
    wx, wy, ww, wh = wins_to_use[0]
    print(f"微信窗口: ({wx},{wy}) {ww}x{wh}")

    # Step 3: 截图
    subprocess.run([
        "peekaboo", "image", "--mode", "screen", "--path", "/tmp/wechat_bubble.png"
    ])

    # Step 4: 从底部往上扫描，找绿色气泡的上下边缘
    img = Image.open("/tmp/wechat_bubble.png").convert("RGB")
    arr = np.array(img, dtype=np.int32)
    screen_h, screen_w = arr.shape[:2]

    # 扫描区域：只取聊天消息区域，排除标题栏、搜索栏、侧边栏、底部输入框
    # 标题栏~50 + 搜索栏~60 = 从顶部跳过 120px；底部输入框~100px
    scan_x1 = int(wx + ww * 0.25)
    scan_x2 = int(wx + ww - 10)
    scan_y_top = int(wy + 120)                    # 跳过标题栏+搜索栏
    scan_y_bottom = int(wy + wh - 100)            # 跳过底部输入框

    # 使用 RapidOCR 识别截图中的 URL 文字区域
    ocr_result = RAPIDOCR_READER("/tmp/wechat_bubble.png")

    url_results = []
    if ocr_result:
        txts = ocr_result.txts
        boxes = ocr_result.boxes
        scores = ocr_result.scores
        for i, text in enumerate(txts):
            if text.lower().startswith('http://') or text.lower().startswith('https://'):
                bbox = boxes[i]
                prob = scores[i]
                xs = [p[0] for p in bbox]
                ys = [p[1] for p in bbox]
                cx = int((min(xs) + max(xs)) // 2)
                cy = int((min(ys) + max(ys)) // 2)
                # 过滤掉聊天区域外的 URL（避免点击到搜索框、输入法候选、侧边栏等）
                if not (scan_x1 <= cx <= scan_x2 and scan_y_top <= cy <= scan_y_bottom):
                    print(f"  [过滤] URL不在聊天区域内，跳过: {text[:50]} ({cx},{cy})")
                    continue
                url_results.append((cx, cy, text, prob))

    if not url_results:
        print("⚠️ RapidOCR 未找到 URL")
        return None

    # 如果指定了目标 URL，优先找匹配的
    best = None
    if target_url:
        # 提取目标 URL 的关键部分用于匹配（如 biz 和 mid）
        import re
        biz_match = re.search(r'__biz=([^&]+)', target_url)
        biz_key = biz_match.group(1) if biz_match else ""
        mid_match = re.search(r'mid=(\d+)', target_url)
        mid_key = mid_match.group(1) if mid_match else ""

        for result in url_results:
            _, _, text, _ = result
            # 检查 URL 是否包含相同的关键参数
            text_biz = re.search(r'__biz=([^&]+)', text) if isinstance(text, str) else None
            text_mid = re.search(r'mid=(\d+)', text) if isinstance(text, str) else None
            biz_ok = not biz_match or (text_biz and text_biz.group(1) == biz_key)
            mid_ok = not mid_match or (text_mid and text_mid.group(1) == mid_key)
            if biz_ok and mid_ok:
                best = result
                print(f"  [匹配] 找到目标 URL: {text[:50]}")
                break

    # 如果没找到匹配的，取最底部的 URL
    if not best:
        best = max(url_results, key=lambda x: x[1])
    click_x, click_y, text, prob = best
    print(f"RapidOCR URL: {text!r} 置信度: {prob:.2f}")
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

    # 自动找气泡并点击
    pos = find_url_text_and_click()
    if pos is None:
        print("⚠️ 未找到链接气泡，请手动点击")
        return False

    x, y = pos
    print(f"单击 ({x}, {y})...")
    e_down = Quartz.CGEventCreateMouseEvent(
        None, Quartz.kCGEventLeftMouseDown, (x, y), Quartz.kCGMouseButtonLeft
    )
    e_up = Quartz.CGEventCreateMouseEvent(
        None, Quartz.kCGEventLeftMouseUp, (x, y), Quartz.kCGMouseButtonLeft
    )
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, e_down)
    time.sleep(0.05)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, e_up)

    print("✅ 已双击，等待文章页面加载...")
    time.sleep(3)
    return True


def send_link(url):
    """
     直接发送链接（URL），微信不会自动生成预览卡片

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
    time.sleep(0.05)
    pyautogui.press('return')
    time.sleep(1) #对话框加载完


def wait_for_browser_window(timeout=20, interval=1.0):
    """
    等待微信内置浏览器窗口出现

    通过检测窗口尺寸变化来判断文章页面是否加载完成。
    微信内置浏览器窗口比普通聊天窗口更大（通常是全屏或接近全屏）。

    Args:
        timeout: 最大等待秒数
        interval: 轮询间隔秒数
    Returns:
        tuple: (win_x, win_y, win_w, win_h) 窗口坐标，失败返回 None
    """
    kExcludeDesktopElements = 2
    kOnScreenOnly = 1

    start = time.time()
    last_state = None
    stable_count = 0  # 连续几次窗口状态相同说明已稳定

    while time.time() - start < timeout:
        window_list = Quartz.CGWindowListCopyWindowInfo(
            kExcludeDesktopElements | kOnScreenOnly, Quartz.kCGNullWindowID
        )

        for win in window_list:
            owner = win.get("kCGWindowOwnerName", "")
            name = win.get("kCGWindowName", "")
            if ("WeChat" in owner or "微信" in owner) and "窗口" in name:
                b = win.get("kCGWindowBounds", {})
                x, y = b.get("X", 0), b.get("Y", 0)
                w, h = b.get("Width", 0), b.get("Height", 0)
                if w > 100 and h > 100:
                    state = (x, y, w, h)
                    if state == last_state:
                        stable_count += 1
                        if stable_count >= 2:  # 连续2次状态相同，认为已稳定
                            print(f"  [wait] 窗口稳定: ({x},{y}) {w}x{h}，耗时 {time.time()-start:.1f}s")
                            return (x, y, w, h)
                    else:
                        stable_count = 0
                    last_state = state
                    break

        time.sleep(interval)

    print(f"  [wait] 等待浏览器窗口超时（{timeout}s）")
    return None


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
    pos = find_url_text_and_click(article_url)
    if pos is None:
        print("  [2/5] ⚠️ 未找到链接，请手动点击")
        return False
    x, y = pos
    print(f"  单击 ({x}, {y})...")
    e_down = Quartz.CGEventCreateMouseEvent(
        None, Quartz.kCGEventLeftMouseDown, (x, y), Quartz.kCGMouseButtonLeft
    )
    e_up = Quartz.CGEventCreateMouseEvent(
        None, Quartz.kCGEventLeftMouseUp, (x, y), Quartz.kCGMouseButtonLeft
    )
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, e_down)
    time.sleep(0.05)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, e_up)
    print("  [2/5] ✅ 已点击链接，等待文章页面加载...")

    # Step 3: 点击右上角"..."按钮，在菜单中选"转发"
    print("  [3/5] 点击右上角菜单按钮...")

    # 先关闭通知中心
    subprocess.run(["killall", "NotificationCenter"])
    time.sleep(0.1)

    # 等待浏览器窗口出现（单击后先等1.5秒让窗口打开，再开始轮询）
    # 注意：不要在这里激活微信，否则会把刚打开的浏览器窗口盖住
    print("  [wait] 等待内置浏览器窗口出现（先等1.5秒）...")
    time.sleep(1.5)
    browser_win = wait_for_browser_window(timeout=20, interval=1.0)

    win_x, win_y, win_w, win_h = None, None, None, None
    if browser_win:
        win_x, win_y, win_w, win_h = browser_win
    else:
        # fallback：尝试传统检测
        kExcludeDesktopElements = 2
        kOnScreenOnly = 1
        window_list = Quartz.CGWindowListCopyWindowInfo(kExcludeDesktopElements | kOnScreenOnly, Quartz.kCGNullWindowID)
        for win in window_list:
            owner = win.get("kCGWindowOwnerName", "")
            name = win.get("kCGWindowName", "")
            if ("WeChat" in owner or "微信" in owner) and "窗口" in name:
                b = win.get("kCGWindowBounds", {})
                win_x, win_y = b.get("X"), b.get("Y")
                win_w, win_h = b.get("Width"), b.get("Height")
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

    # 先把鼠标移到窗口中央，等通知消失
    move = Quartz.CGEventCreateMouseEvent(
        None, Quartz.kCGEventMouseMoved, (int(win_x + win_w // 2), int(win_y + win_h // 2)), Quartz.kCGMouseButtonLeft
    )
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, move)
    time.sleep(0.3)

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
    time.sleep(0.4)  # 等待菜单出现

    # 用 RapidOCR 识别菜单项，找到"转发给朋友"并点击
    print("  截图识别菜单项...")
    subprocess.run(["peekaboo", "image", "--mode", "screen", "--path", "/tmp/menu_items.png"])
    menu_ocr = RAPIDOCR_READER("/tmp/menu_items.png")

    clicked = False
    if menu_ocr:
        for i, text in enumerate(menu_ocr.txts):
            if "转发" in text:
                bbox = menu_ocr.boxes[i]
                xs = [p[0] for p in bbox]
                ys = [p[1] for p in bbox]
                cx = int((min(xs) + max(xs)) // 2)
                cy = int((min(ys) + max(ys)) // 2)
                print(f"  找到「{text}」at ({cx},{cy})")

                # 点击该项
                e_down = Quartz.CGEventCreateMouseEvent(
                    None, Quartz.kCGEventLeftMouseDown, (cx, cy), Quartz.kCGMouseButtonLeft
                )
                e_up = Quartz.CGEventCreateMouseEvent(
                    None, Quartz.kCGEventLeftMouseUp, (cx, cy), Quartz.kCGMouseButtonLeft
                )
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, e_down)
                time.sleep(0.05)
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, e_up)
                clicked = True
                break

    if not clicked:
        import shutil
        from datetime import datetime
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup = f"/tmp/menu_items_FAILED_{ts}.png"
        shutil.copy("/tmp/menu_items.png", backup)
        print(f"  [调试] 截图已备份: {backup}")
        # 打印 OCR 结果供调试
        if menu_ocr:
            print(f"  [调试] OCR 识别到的文字: {[t for t in menu_ocr.txts if t.strip()]}")
        print("  ❌ 未找到「转发」菜单项，退出")
        return False

    time.sleep(0.5)
    print("  [3/5] ✅ 已打开转发浮窗")

    # 检测并保存转发弹窗的窗口 bounds（Step 5 需要裁剪该区域来定位发送按钮）
    popup_bounds = None
    k_excl = 2; k_on_screen = 1
    wl = Quartz.CGWindowListCopyWindowInfo(k_excl | k_on_screen, Quartz.kCGNullWindowID)
    candidates = []
    for win in wl:
        owner = win.get("kCGWindowOwnerName", "")
        if "微信" in owner or "WeChat" in owner:
            b = win.get("kCGWindowBounds", {})
            w = b.get("Width", 0); h = b.get("Height", 0)
            # 弹窗比浏览器窗口小（浏览器是 1512x876），但比引用菜单大（引用菜单约 210x368）
            # 典型转发弹窗约 500x400 到 700x500
            if 300 < w < 1200 and 200 < h < 700 and w < 1400:
                name = win.get("kCGWindowName", "")
                candidates.append({
                    "x": b.get("X", 0), "y": b.get("Y", 0), "w": w, "h": h,
                    "name": name,
                    "is_main": name == "微信"
                })
    # 优先选弹窗（名称不是"微信"），排除被误识别的主窗口
    for c in candidates:
        if not c["is_main"]:
            popup_bounds = {"x": c["x"], "y": c["y"], "w": c["w"], "h": c["h"]}
            break
    # 如果没有弹窗窗口，回退到全屏（不选主窗口，避免裁剪错区域）
    if popup_bounds:
        print(f"  [弹窗] 位置({popup_bounds['x']:.0f},{popup_bounds['y']:.0f}) 大小{popup_bounds['w']:.0f}x{popup_bounds['h']:.0f}")
    else:
        print("  [弹窗] 未检测到独立弹窗窗口，Step 5 将使用全屏截图")

    # Step 4: 在转发弹窗中搜索目标联系人
    print(f"  [4/5] 在转发弹窗中搜索联系人: {target_contact}...")
    time.sleep(0.3)

    pyperclip.copy(target_contact)
    time.sleep(0.1)

    # Cmd+F 打开搜索框
    pyautogui.keyDown('command')
    time.sleep(0.05)
    pyautogui.press('f')
    pyautogui.keyUp('command')
    time.sleep(0.05)

    # 粘贴联系人名称
    pyautogui.keyDown('command')
    time.sleep(0.05)
    pyautogui.press('v')
    pyautogui.keyUp('command')
    time.sleep(0.1)

    # 键盘向下键选中第一个结果
    pyautogui.press('down')
    time.sleep(0.05)
    # 回车确认选中
    pyautogui.press('return')
    time.sleep(0.15)
    print("  [4/5] ✅ 已选中介联系人")

    # Step 5: 点击发送按钮（使用 RapidOCR 定位"发送"文字）
    print("  [5/5] 点击发送按钮...")
    time.sleep(0.3)

    # 截图
    subprocess.run(["peekaboo", "image", "--mode", "screen", "--path", "/tmp/send_button.png"])

    # 如果有弹窗 bounds，先裁剪弹窗区域来识别（避免搜索框等干扰）
    send_ocr = None
    if popup_bounds:
        img = Image.open("/tmp/send_button.png")
        crop = img.crop((
            int(popup_bounds["x"]), int(popup_bounds["y"]),
            int(popup_bounds["x"] + popup_bounds["w"]), int(popup_bounds["y"] + popup_bounds["h"])
        ))
        crop.save("/tmp/send_button_crop.png")
        send_ocr = RAPIDOCR_READER("/tmp/send_button_crop.png")
        print(f"  [弹窗裁剪] {popup_bounds['w']:.0f}x{popup_bounds['h']:.0f} 区域识别")

    # 如果裁剪区域没找到，回退到全屏识别
    if not send_ocr or not send_ocr.txts:
        send_ocr = RAPIDOCR_READER("/tmp/send_button.png")
        print("  [全屏识别] 弹窗区域未找到，回退全屏")

    # 在 OCR 结果中查找"发送"按钮，返回 (cx, cy) 或 None
    def _find_send_in_ocr(ocr_result, ox=0, oy=0):
        if not ocr_result or not ocr_result.txts:
            return None
        for i, text in enumerate(ocr_result.txts):
            t = text.strip()
            if t == "发送" or t == "发送 ":
                bbox = ocr_result.boxes[i]
                xs = [p[0] for p in bbox]
                ys = [p[1] for p in bbox]
                return (int((min(xs) + max(xs)) // 2) + ox,
                        int((min(ys) + max(ys)) // 2) + oy)
        return None

    # 先在裁剪区域中查找
    click_pos = None
    send_clicked = False
    if popup_bounds and send_ocr:
        click_pos = _find_send_in_ocr(send_ocr,
                                      int(popup_bounds["x"]),
                                      int(popup_bounds["y"]))

    if click_pos:
        cx, cy = click_pos
        print(f"  找到发送按钮: ({cx}, {cy})")
        # 点击前在截图上画蓝色圆圈标记（调试用）
        import cv2
        marker_img = cv2.imread("/tmp/send_button.png")
        cv2.circle(marker_img, (cx, cy), 15, (255, 0, 0), 3)  # 蓝色圆圈
        cv2.imwrite("/tmp/send_button_MARKER.png", marker_img)
        print(f"  [调试] 已标记点击位置到 /tmp/send_button_MARKER.png")
        pyautogui.click(cx, cy)
        send_clicked = True
        print("  [5/5] ✅ 已点击发送按钮")

    if not send_clicked:
        print("  [5/5] ⚠️ 未自动找到发送按钮，请手动点击")
        import shutil
        from datetime import datetime
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup = f"/tmp/send_button_FAILED_{ts}.png"
        shutil.copy("/tmp/send_button.png", backup)
        print(f"  [调试] 截图已备份: {backup}")
        return False

    print(f"✅ 转发成功！文章已以卡片形式发送给 {target_contact}")
    return True


def find_card_center(known_title=None):
    """
    通过 OCR 识别文章标题文字，找到聊天窗口中最新的卡片式链接中心坐标

    原理：微信卡片有白色/深色背景，下方有一条分隔线（仅卡片宽度，非全屏）。
          通过检测文字下方是否有分隔线来确认卡片位置。

    Args:
        known_title: 可选的已知文章标题，精确匹配卡片位置

    Returns:
        tuple: (x, y) 卡片中心屏幕坐标，失败返回 None
    """
    import cv2
    import numpy as np

    # 获取微信窗口坐标
    kExcludeDesktopElements = 2
    kOnScreenOnly = 1
    window_list = Quartz.CGWindowListCopyWindowInfo(
        kExcludeDesktopElements | kOnScreenOnly, Quartz.kCGNullWindowID
    )
    wx, wy, ww, wh = 0, 0, 0, 0
    for win in window_list:
        owner = win.get("kCGWindowOwnerName", "")
        name = win.get("kCGWindowName", "")
        if "微信" in owner or "WeChat" in owner:
            if "窗口" not in name:
                b = win.get("kCGWindowBounds", {})
                wx, wy = b.get("X", 0), b.get("Y", 0)
                ww, wh = b.get("Width", 0), b.get("Height", 0)
                print(f"  [卡片检测] 窗口(pts): ({wx}, {wy}) {ww}x{wh}")
                break

    # 截取微信窗口截图
    subprocess.run(
        ["peekaboo", "image", "--app", "WeChat", "--mode", "frontmost", "--path", "/tmp/wechat_window.png"],
        capture_output=True
    )
    time.sleep(0.3)

    img = cv2.imread("/tmp/wechat_window.png")
    if img is None:
        print("  [卡片检测] 无法读取截图")
        return None

    h, w = img.shape[:2]
    print(f"  [卡片检测] 截图: {w}x{h}")

    result = RAPIDOCR_READER("/tmp/wechat_window.png")
    if not result or not result.txts:
        print("  [卡片检测] OCR 未找到文字")
        return None

    boxes = result.boxes
    txts = result.txts

    # Step 1: 如果有已知标题，优先精确匹配
    if known_title:
        for i, text in enumerate(txts):
            if known_title in text:
                bbox = boxes[i]
                xs = [p[0] for p in bbox]
                ys = [p[1] for p in bbox]
                cx = int((min(xs) + max(xs)) // 2)
                cy = int((max(ys) + min(ys)) // 2)
                print(f"  [卡片检测] 精确匹配到标题「{known_title}」在 ({cx},{cy})")
                card_cy = cy + 40
                screen_cx = int(wx) + cx
                screen_cy = int(wy) + card_cy
                print(f"  [卡片检测] 卡片中心(屏幕): ({screen_cx}, {screen_cy})")
                return (screen_cx, screen_cy)

    # Step 2: 分割线检测法（主力方法）
    # 原理：卡片文字下方有一条分割线，其宽度有限（仅卡片宽度），
    #        而输入框顶部分隔线横跨全窗口。通过测量线宽来区分。
    article_candidates = []
    for i, text in enumerate(txts):
        if not text or len(text.strip()) < 4:
            continue

        bbox = boxes[i]
        xs = [p[0] for p in bbox]
        ys = [p[1] for p in bbox]
        x1, y1 = int(min(xs)), int(min(ys))
        x2, y2 = int(max(xs)), int(max(ys))
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2

        # 聊天区域右侧 = 我的消息
        if cx < int(w * 0.55):
            continue

        # 排除顶部标题栏/搜索栏区域 (< 80px)
        if cy < 80:
            continue

        # 排除底部输入框区域 (> 窗口高度 - 100)
        if cy > h - 120:
            continue

        # 采样文字背景（取四角）
        corners = [
            img[max(0, y1-15):min(h, y1+5), max(0, x1-15):min(w, x1+5)],
            img[max(0, y1-15):min(h, y1+5), max(0, x2-5):min(w, x2+15)],
            img[max(0, y2-5):min(h, y2+15), max(0, x1-15):min(w, x1+5)],
            img[max(0, y2-5):min(h, y2+15), max(0, x2-5):min(w, x2+15)],
        ]
        corner_colors = []
        for corner in corners:
            if corner.size > 0:
                corner_colors.append(np.mean(corner, axis=(0, 1)))
        if not corner_colors:
            continue
        avg_bg = np.mean(corner_colors, axis=0)

        is_white_bg = all(c > 180 for c in avg_bg)
        is_dark_bg = all(c < 120 for c in avg_bg)  # 放宽到120，夜间卡片可能偏灰
        if not is_white_bg and not is_dark_bg:
            continue

        # 文字高度过滤（卡片标题通常 14-30px）
        text_height = y2 - y1
        if text_height < 10 or text_height > 40:
            continue

        # 在文字下方检测分割线（30~120px 范围内）
        # 要求：
        #   1. 存在一条直线（灰色/浅色，横向连续像素 > 50）
        #   2. 线宽在 40 ~ 窗口宽度50%（排除极小UI元素和全屏输入框分隔线）
        #   3. 分割线上方紧邻的区域是卡片背景色（验证是卡片底边）
        found_line = False
        line_y = None
        line_width = 0

        for offset in range(30, 120, 5):
            scan_y = cy + offset
            if scan_y >= h - 20:
                break

            # 扫描范围宽一些，以便测量线宽
            scan_x_start = max(0, cx - 250)
            scan_x_end = min(w, cx + 250)
            scan_region = img[scan_y:scan_y+3, scan_x_start:scan_x_end]

            # --- 白天模式：灰色直线 ---
            gray_mask = cv2.inRange(scan_region, np.array([150,150,150]), np.array([210,210,210]))
            if cv2.countNonZero(gray_mask) > 50:
                # 测量线宽
                gray_binary = cv2.inRange(scan_region, np.array([150,150,150]), np.array([220,220,220]))
                line_pixels = np.sum(gray_binary > 0, axis=0)
                non_zero = np.where(line_pixels > 0)[0]
                if len(non_zero) > 0:
                    measured_width = non_zero[-1] - non_zero[0]
                else:
                    measured_width = scan_x_end - scan_x_start
                # 全屏分割线跳过
                if measured_width > w * 0.5:
                    print(f"  [卡片检测] y={scan_y} 线宽 {measured_width}px > 50%窗口，跳过")
                    continue
                # 太短的分割线（<40px）跳过（可能是UI装饰元素）
                if measured_width < 40:
                    print(f"  [卡片检测] y={scan_y} 线宽 {measured_width}px < 40px，跳过（非卡片分隔线）")
                    continue
                # 验证：分割线上方的像素颜色 = 卡片背景色（白色/亮色）
                # 采样线上面 5px 处，与文字背景对比
                above_line = img[scan_y-5:scan_y, max(0, cx-80):min(w, cx+80)]
                if above_line.size > 0:
                    above_color = np.mean(above_line, axis=(0, 1))
                    # 如果是白天模式（is_white_bg），上面应该是白色（>180）
                    # 如果是夜间模式（is_dark_bg），上面应该是深色（<100）
                    if is_white_bg:
                        if not all(c > 170 for c in above_color):
                            print(f"  [卡片检测] y={scan_y} 线上方颜色{above_color.astype(int)} 非卡片白色，跳过")
                            continue
                    elif is_dark_bg:
                        if not all(c < 130 for c in above_color):
                            print(f"  [卡片检测] y={scan_y} 线上方颜色{above_color.astype(int)} 非卡片深色，跳过")
                            continue
                found_line = True
                line_y = scan_y
                line_width = measured_width
                break

            # --- 夜间模式：浅色直线（比深色背景亮） ---
            if is_dark_bg:
                bg_brightness = np.mean(scan_region)
                light_mask = scan_region > (bg_brightness + 15)
                if np.sum(light_mask) > 50:
                    # 测量线宽
                    light_binary = (scan_region > (bg_brightness + 15)).astype(np.uint8)
                    line_pixels = np.sum(light_binary > 0, axis=0)
                    non_zero = np.where(line_pixels > 0)[0]
                    if len(non_zero) > 0:
                        measured_width = non_zero[-1] - non_zero[0]
                    else:
                        measured_width = scan_x_end - scan_x_start
                    # 全屏分割线跳过
                    if measured_width > w * 0.5:
                        print(f"  [卡片检测] y={scan_y} 线宽 {measured_width}px > 50%窗口，跳过")
                        continue
                    # 太短的分割线跳过
                    if measured_width < 40:
                        print(f"  [卡片检测] y={scan_y} 线宽 {measured_width}px < 40px，跳过（非卡片分隔线）")
                        continue
                    # 验证：分割线上方必须是深色（卡片背景色）
                    above_line = img[scan_y-5:scan_y, max(0, cx-80):min(w, cx+80)]
                    if above_line.size > 0:
                        above_color = np.mean(above_line, axis=(0, 1))
                        # 卡片上方应该是深色背景
                        if not all(c < 130 for c in above_color):
                            print(f"  [卡片检测] y={scan_y} 线上方颜色{above_color.astype(int)} 非卡片深色，跳过（可能是聊天区域分隔线）")
                            continue
                    found_line = True
                    line_y = scan_y
                    line_width = measured_width
                    break

        if found_line:
            article_candidates.append((cx, cy, text, text_height, line_y, line_width))

    # Step 2: 分割线检测法
    # 原理：文字下方有分割线 → 这是卡片
    # 卡片中心在文字位置（cy），分割线只是验证卡片存在的标志

    print(f"  [卡片检测] 分割线检测找到 {len(article_candidates)} 个候选")
    for c in article_candidates:
        print(f"    ({c[0]},{c[1]}) '{c[2][:20]}' h={c[3]} line_y={c[4]} w={c[5]})")

    if not article_candidates:
        print("  [卡片检测] 未找到卡片")
        return None

    # 按 Y 坐标排序，取最新的（最大的 y = 最底部）
    article_candidates.sort(key=lambda c: c[1], reverse=True)
    best = article_candidates[0]
    cx, cy, line_y = best[0], best[1], best[4]
    print(f"  [卡片检测] 选中底部: ({cx}, {cy}) '{best[2][:20]}' 分割线 y={line_y}")

    # 卡片中心在文字位置上方约 30px（标题区域）
    # OCR 能检测到的是卡片底部的来源名（如「正法文集」），
    # 真正的标题在来源名上方，偏移太小则点击来源名，偏移太大则脱离卡片
    card_cy = max(cy - 30, 80)

    # 转换到屏幕坐标
    screen_cx = int(wx) + cx
    screen_cy = int(wy) + card_cy
    print(f"  [卡片检测] 卡片中心(屏幕): ({screen_cx}, {screen_cy})")
    return (screen_cx, screen_cy)


def wait_for_confirm(step_msg, sleep_sec=1.0):
    """等待用户确认，如果是非交互式则跳过"""
    if sys.stdin.isatty():
        time.sleep(sleep_sec)
        input(f"\n[按回车继续] {step_msg}")
    else:
        print(f"\n[跳过确认] {step_msg} (非交互模式)")


def forward_article_with_quote(article_url, target_contact, quote_message, via_contact="文件传输助手", debug=False, article_title=None):
    """
    转发公众号文章卡片并引用该卡片发送文本消息

    流程：
    1. 向目标联系人转发文章卡片
    2. 在目标聊天窗口找到卡片
    3. 右键点击卡片，选择"引用"
    4. 在引用输入框中发送消息

    Args:
        debug: 是否开启调试模式（检测右键菜单是否出现）
    """
    print(f"📤 开始执行：转发文章 + 引用消息 -> {target_contact}")

    # Step 1: 转发文章卡片
    print("\n[步骤 1/4] 转发文章卡片...")
    success = forward_article_via_browser(article_url, target_contact, via_contact)
    if not success:
        print("❌ 文章转发失败，退出")
        return False
    print("✅ 文章转发成功\n")
    wait_for_confirm("步骤1完成，请确认...", sleep_sec=1.0)

    # Step 2: 打开目标聊天窗口
    print("[步骤 2/4] 打开目标聊天窗口...")
    clean_window()
    search_and_select(target_contact)
    print("  ✅ 已打开目标聊天窗口\n")
    wait_for_confirm("步骤2完成，请确认...", sleep_sec=1.0)

    # Step 3: 定位卡片
    print("[步骤 3/4] 在目标窗口中定位卡片...")
    card_pos = find_card_center(known_title=article_title)
    if card_pos is None:
        print("  ⚠️ 未找到卡片，退出")
        return False
    print(f"  ✅ 找到卡片位置: {card_pos}\n")

    # Debug: 在截图上画红圈标记卡片位置
    if debug:
        img = cv2.imread("/tmp/wechat_window.png")
        if img is not None:
            # card_pos 是屏幕坐标，需要转回截图内坐标
            # 重新获取窗口偏移
            k = 2
            window_list = Quartz.CGWindowListCopyWindowInfo(k | 1, Quartz.kCGNullWindowID)
            wx, wy = 0, 0
            for win in window_list:
                owner = win.get("kCGWindowOwnerName", "")
                name = win.get("kCGWindowName", "")
                if "微信" in owner and "窗口" not in name:
                    b = win.get("kCGWindowBounds", {})
                    wx, wy = b.get("X", 0), b.get("Y", 0)
                    break
            # 屏幕坐标转截图内坐标
            cx_in_img = int(card_pos[0] - wx)
            cy_in_img = int(card_pos[1] - wy)
            cv2.circle(img, (cx_in_img, cy_in_img), 25, (0, 0, 255), 4)
            cv2.imwrite("/tmp/card_position_debug.png", img)
            print(f"  [DEBUG] 已保存标记图到 /tmp/card_position_debug.png")

    # Step 4: 右键点击并选择引用
    print("[步骤 4/4] 右键点击卡片...")

    # 等待界面稳定
    time.sleep(0.5)

    # 使用 pyautogui 右键点击
    click_x = int(card_pos[0])
    click_y = int(card_pos[1])
    pyautogui.moveTo(click_x, click_y, duration=0.2)
    time.sleep(0.3)
    # 模拟右键按下
    pyautogui.mouseDown(button='right')
    time.sleep(0.05)
    pyautogui.mouseUp(button='right')
    time.sleep(0.5)

    print(f"  已右键点击 ({click_x}, {click_y})")

    # 检查右键菜单是否出现（仅调试模式）- 用全屏截图才能看到浮窗
    menu_visible = True  # 默认认为成功
    if debug:
        subprocess.run(["peekaboo", "image", "--mode", "screen", "--path", "/tmp/menu_check.png"], capture_output=True)
        menu_ocr = RAPIDOCR_READER("/tmp/menu_check.png")
        menu_visible = False
        if menu_ocr:
            for text in menu_ocr.txts:
                if any(kw in text for kw in ['打开方式', '转发', '收藏', '提醒', '多选', '引用']):
                    menu_visible = True
                    print(f"  ✅ 右键菜单已打开\n")
                    break

        if not menu_visible:
            print(f"  ❌ 右键菜单未出现: {card_pos}")
            pyautogui.press('escape')
        time.sleep(0.2)
        return False

    wait_for_confirm("步骤4完成，请确认...")

    # 选择"引用"——右键点击后截图，用OCR识别菜单项并点击
    print("[步骤 4/4] 选择「引用」...")
    time.sleep(0.5)  # 等待菜单完全渲染

    # 动态获取所有微信窗口，找到最小的那个（右键弹出菜单）
    kExcludeDesktopElements = 2
    kOnScreenOnly = 1
    window_list = Quartz.CGWindowListCopyWindowInfo(
        kExcludeDesktopElements | kOnScreenOnly, Quartz.kCGNullWindowID
    )
    popup_win = None

    # 先按尺寸过滤：找宽<600且高<600的微信子窗口（白天约210x310，夜间可能更宽）
    candidate_wins = []
    for win in window_list:
        owner = win.get("kCGWindowOwnerName", "")
        if "微信" in owner or "WeChat" in owner:
            b = win.get("kCGWindowBounds", {})
            w = b.get("Width", 0)
            h = b.get("Height", 0)
            if 50 < w < 600 and 50 < h < 600:
                candidate_wins.append({
                    "x": b.get("X", 0),
                    "y": b.get("Y", 0),
                    "w": w,
                    "h": h,
                })

    if candidate_wins:
        # 按面积从小到大排序，取最小的（右键菜单通常比主窗口小得多）
        candidate_wins.sort(key=lambda w: w["w"] * w["h"])
        popup_win = candidate_wins[0]
        print(f"  [菜单窗口] 位置({popup_win['x']:.0f},{popup_win['y']:.0f}) 大小{popup_win['w']:.0f}x{popup_win['h']:.0f}")

    # fallback：如果窗口检测没找到，直接在全屏截图里搜索右键点击位置附近的"引用"
    if popup_win is None:
        print("  [菜单窗口] CGWindow未找到菜单弹窗，尝试 OCR fallback...")
        subprocess.run(["peekaboo", "image", "--mode", "screen", "--path", "/tmp/quote_menu.png"])
        menu_ocr = RAPIDOCR_READER("/tmp/quote_menu.png")
        if menu_ocr:
            for i, text in enumerate(menu_ocr.txts):
                t = text.strip()
                if "引用" in t or t in ["引用", "引用 "]:
                    bbox = menu_ocr.boxes[i]
                    xs = [p[0] for p in bbox]
                    ys = [p[1] for p in bbox]
                    cx = int((min(xs) + max(xs)) // 2)
                    cy = int((min(ys) + max(ys)) // 2)
                    print(f"  [Fallback] 找到「{text}」at ({cx},{cy})")
                    # 限制菜单区域：只取点击位置附近的"引用"（排除聊天区域的"引用"）
                    if abs(cx - click_x) < 500 and abs(cy - click_y) < 500:
                        popup_win = {
                            "x": max(0, cx - 200),
                            "y": max(0, cy - 100),
                            "w": 400,
                            "h": 300,
                        }
                        # 记录原坐标（后续直接点击，不裁剪）
                        print(f"  [Fallback] 构建虚拟弹窗区域，直接点击 ({cx},{cy})")
                        e_down = Quartz.CGEventCreateMouseEvent(
                            None, Quartz.kCGEventLeftMouseDown, (cx, cy), Quartz.kCGMouseButtonLeft
                        )
                        e_up = Quartz.CGEventCreateMouseEvent(
                            None, Quartz.kCGEventLeftMouseUp, (cx, cy), Quartz.kCGMouseButtonLeft
                        )
                        Quartz.CGEventPost(Quartz.kCGHIDEventTap, e_down)
                        time.sleep(0.05)
                        Quartz.CGEventPost(Quartz.kCGHIDEventTap, e_up)
                        print("  ✅ 已通过 fallback 点击「引用」")
                        time.sleep(0.3)
                        print("  ✅ 已进入引用输入模式\n")
                        # 粘贴并发送引用消息
                        pyperclip.copy(quote_message)
                        time.sleep(0.1)
                        pyautogui.keyDown('command')
                        pyautogui.press('v')
                        pyautogui.keyUp('command')
                        time.sleep(0.1)
                        pyautogui.press('return')
                        time.sleep(0.2)
                        print(f"✅ 引用消息已发送: \"{quote_message[:30]}...\" -> {target_contact}")
                        return True

    if popup_win is None:
        raise RuntimeError("[步骤 4/4] 未找到菜单弹出窗口，也无法通过 OCR 找到「引用」，请检查右键是否成功弹出菜单")

    # 只截取菜单弹出窗口（避免全屏其他"引用"字样干扰）
    # peekaboo 的 --window-id 需要数值ID，用 --app WeChat --mode frontmost 截主窗口
    # 但菜单弹出时主窗口可能不是 frontmost，用窗口列表找到的 bounds 直接裁剪
    subprocess.run(["peekaboo", "image", "--mode", "screen", "--path", "/tmp/quote_menu.png"])
    # 用 PIL 裁剪出菜单区域（坐标已经是屏幕坐标）
    menu_img = Image.open("/tmp/quote_menu.png")
    cropped = menu_img.crop((
        int(popup_win["x"]), int(popup_win["y"]),
        int(popup_win["x"] + popup_win["w"]), int(popup_win["y"] + popup_win["h"])
    ))
    cropped.save("/tmp/quote_menu_crop.png")
    menu_ocr = RAPIDOCR_READER("/tmp/quote_menu_crop.png")

    quote_clicked = False
    if menu_ocr:
        for i, text in enumerate(menu_ocr.txts):
            t = text.strip()
            # 模糊匹配：OCR可能把"引用"识别成各种形式
            if "引用" in t or t in ["引用", "引用 "]:
                bbox = menu_ocr.boxes[i]
                xs = [p[0] for p in bbox]
                ys = [p[1] for p in bbox]
                # OCR 坐标是相对于裁剪图片的，转为屏幕坐标
                cx = int((min(xs) + max(xs)) // 2) + int(popup_win["x"])
                cy = int((min(ys) + max(ys)) // 2) + int(popup_win["y"])
                print(f"  找到「{text}」at ({cx},{cy})")
                e_down = Quartz.CGEventCreateMouseEvent(
                    None, Quartz.kCGEventLeftMouseDown, (cx, cy), Quartz.kCGMouseButtonLeft
                )
                e_up = Quartz.CGEventCreateMouseEvent(
                    None, Quartz.kCGEventLeftMouseUp, (cx, cy), Quartz.kCGMouseButtonLeft
                )
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, e_down)
                time.sleep(0.05)
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, e_up)
                quote_clicked = True
                break

    if not quote_clicked:
        raise RuntimeError("[步骤 4/4] OCR未找到「引用」菜单项，请检查菜单是否正常弹出")

    time.sleep(0.3)
    print("  ✅ 已进入引用输入模式\n")

    # 粘贴并发送引用消息
    pyperclip.copy(quote_message)
    time.sleep(0.1)
    pyautogui.keyDown('command')
    pyautogui.press('v')
    pyautogui.keyUp('command')
    time.sleep(0.1)
    pyautogui.press('return')
    time.sleep(0.2)

    print(f"✅ 引用消息已发送: \"{quote_message[:30]}...\" -> {target_contact}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description='微信消息自动发送工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
使用示例：
  python3 send_wechat.py 文件传输助手 你好
  python3 send_wechat.py 小明 -f /path/to/file.pdf
  python3 send_wechat.py 小明 -f document.docx
  python3 send_wechat.py 家人群 -l "https://mp.weixin.qq.com/s/xxx"

注意：使用 -f 发送文件时，请确保文件路径是绝对路径。
        '''
    )

    parser.add_argument('contact', nargs='?', help='联系人名称')
    parser.add_argument('message', nargs='?', default=None, help='要发送的消息内容')
    parser.add_argument('-f', '--file', dest='file_path', help='要发送的文件路径')
    parser.add_argument('-l', '--url', dest='article_url', help='要转发的公众号文章URL')
    parser.add_argument('-q', '--quote', dest='quote_message', help='转发后引用的文本消息（需要配合 -l 使用）')
    parser.add_argument('--via', dest='via_contact', default='文件传输助手',
                        help='作为跳板的中间联系人（默认文件传输助手）')

    args = parser.parse_args()

    # 转发文章 + 引用消息模式
    if args.article_url and args.quote_message:
        if not args.contact:
            parser.error('转发+引用模式需要指定目标联系人')
        forward_article_with_quote(args.article_url, args.contact, args.quote_message, args.via_contact)
        return

    # 转发文章模式（纯转发，不引用）
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
