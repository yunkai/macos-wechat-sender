#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信消息发送回归测试

测试用例：
1. 给"文件传输助手"发送文本消息
2. 给"文件传输助手"发送文件
"""

import sys
import os

# 添加 scripts 目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from send_wechat import clean_window, search_and_select, send_message, send_file


def test_send_message():
    """测试发送文本消息"""
    print("=" * 50)
    print("测试 1: 发送文本消息")
    print("=" * 50)
    
    TARGET = "文件传输助手"
    MESSAGE = "来自AI回归测试！"
    
    try:
        clean_window()
        search_and_select(TARGET)
        send_message(MESSAGE)
        print(f"✅ 测试通过: 消息 '{MESSAGE}' 已发送给 '{TARGET}'")
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_send_file():
    """测试发送文件"""
    print("=" * 50)
    print("测试 2: 发送文件")
    print("=" * 50)
    
    TARGET = "文件传输助手"
    FILE_PATH = "/tmp/abc.pdf"
    
    # 检查文件是否存在
    if not os.path.exists(FILE_PATH):
        print(f"❌ 测试失败: 文件不存在 {FILE_PATH}")
        return False
    
    try:
        clean_window()
        search_and_select(TARGET)
        send_file(FILE_PATH)
        print(f"✅ 测试通过: 文件 '{FILE_PATH}' 已发送给 '{TARGET}'")
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def main():
    print("微信消息发送回归测试")
    print("")
    
    # 执行测试
    result1 = test_send_message()
    print("")
    result2 = test_send_file()
    
    # 输出结果
    print("")
    print("=" * 50)
    print("测试结果汇总")
    print("=" * 50)
    print(f"测试 1 (发送文本消息): {'✅ 通过' if result1 else '❌ 失败'}")
    print(f"测试 2 (发送文件): {'✅ 通过' if result2 else '❌ 失败'}")
    
    if result1 and result2:
        print("")
        print("🎉 所有测试通过！")
        return 0
    else:
        print("")
        print("⚠️ 部分测试失败")
        return 1


if __name__ == '__main__':
    exit(main())
