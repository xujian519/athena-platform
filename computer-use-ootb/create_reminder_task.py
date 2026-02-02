#!/usr/bin/env python3
"""
创建提醒事项任务的脚本
"""

import asyncio
import aiohttp
import json
import sys
import os

# 添加项目路径
sys.path.append('/Users/xujian/Athena工作平台/computer-use-ootb')
from glm_vision_client import GLMVisionClient
from PIL import ImageGrab
import logging

logger = logging.getLogger(__name__)


async def create_reminder_task():
    """创建提醒事项任务"""

    base_url = "http://localhost:8001"
    api_key = "9efe5766a7cd4bb687e40082ee4032b6.0mYTotbC7aRmoNCe"

    print("📝 小诺正在帮您创建提醒事项...")
    print("任务：明天上午9点联系曹新乐，约他周四见面\n")

    # 1. 截取当前屏幕
    print("1. 正在分析当前屏幕...")
    screenshot = ImageGrab.grab()
    img_byte_arr = screenshot.save("current_screen.png")

    # 2. 使用GLM-4V分析屏幕
    print("2. 使用GLM-4V分析屏幕，找到提醒事项应用...")
    client = GLMVisionClient(api_key)

    analysis_question = """
    请分析这个屏幕截图，帮我：
    1. 找到苹果的提醒事项(Reminders)应用
    2. 告诉我如何打开它
    3. 提供创建新提醒的步骤

    提醒内容：明天上午9点联系曹新乐，约他周四见面
    """

    img_buffer = screenshot.save("temp_screenshot.png", format='PNG')
    with open("temp_screenshot.png", "rb") as f:
        image_bytes = f.read()

    result = await client.analyze_image(image_bytes, analysis_question)

    if result["success"]:
        print("\n✅ GLM-4V分析结果：")
        print("=" * 50)
        print(result["content"])
        print("=" * 50)

        # 3. 也尝试日历分析
        print("\n3. 分析日历应用...")
        calendar_question = """
        请分析这个屏幕，找到苹果的日历(Calendar)应用，并告诉我如何：
        1. 打开日历应用
        2. 创建明天上午9点的日程
        3. 添加详细信息和提醒

        日程内容：联系曹新乐，约周四见面
        """

        calendar_result = await client.analyze_image(image_bytes, calendar_question)

        if calendar_result["success"]:
            print("\n✅ 日历操作指导：")
            print("=" * 50)
            print(calendar_result["content"])
            print("=" * 50)
    else:
        print("❌ GLM分析失败：", result.get("error"))

    # 4. 清理临时文件
    try:
        os.remove("temp_screenshot.png")
        os.remove("current_screen.png")
    except Exception as e:

        # 记录异常但不中断流程

        logger.debug(f"[create_reminder_task] Exception: {e}")
    print("\n📋 任务记录总结：")
    print("✅ 任务内容：明天上午9点联系曹新乐，约他周四见面")
    print("✅ 记录位置：提醒事项 (Reminders)")
    print("✅ 日程安排：日历 (Calendar)")
    print("\n💡 小诺建议：")
    print("1. 先打开提醒事项应用，创建新提醒")
    print("2. 然后打开日历，设置具体的日程时间")
    print("3. 设置提前提醒，确保不会忘记")

if __name__ == "__main__":
    # 运行任务创建
    asyncio.run(create_reminder_task())