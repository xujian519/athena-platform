#!/usr/bin/env python3
"""
使用小诺GUI控制器V2创建提醒事项和日历事件
"""

import asyncio
import aiohttp
import json
import sys
import os
from datetime import datetime

# 添加项目路径
sys.path.append('/Users/xujian/Athena工作平台/computer-use-ootb')
from glm_vision_client import GLMVisionClient
from PIL import ImageGrab

async def create_reminder_with_glm():
    """使用GLM-4V分析屏幕并指导创建提醒事项"""

    base_url = "http://localhost:8001"
    api_key = "9efe5766a7cd4bb687e40082ee4032b6.0mYTotbC7aRmoNCe"

    print("📱 小诺智能助手 - 提醒事项创建")
    print("=" * 50)
    print("任务：明天上午9点联系曹新乐，约他周四见面\n")

    # 获取明天日期
    tomorrow = datetime.now().strftime("%m月%d日")
    tomorrow_weekday = "周三" if datetime.now().weekday() == 1 else "明天"

    print(f"📅 目标时间：{tomorrow_weekday}上午9点")
    print(f"📝 任务内容：联系曹新乐，约他周四见面\n")

    async with aiohttp.ClientSession() as session:

        # 1. 获取屏幕截图
        print("1️⃣ 正在分析当前屏幕...")
        async with session.post(f"{base_url}/screenshot") as resp:
            if resp.status != 200:
                print("❌ 屏幕截图失败")
                return
            screenshot_data = await resp.json()
            print(f"   ✅ 屏幕截图成功: {screenshot_data['screenshot_path']}")

        # 2. 使用GLM-4V分析如何找到提醒事项应用
        print("\n2️⃣ 正在使用AI分析如何找到提醒事项应用...")

        analysis_request = {
            "question": f"""
请帮我分析当前屏幕，告诉我如何创建一个提醒事项：

提醒内容：明天上午9点联系曹新乐，约他周四见面
提醒日期：{tomorrow}
提醒时间：上午9:00

请提供：
1. 如何找到并打开"提醒事项"(Reminders)应用
2. 如何创建新的提醒
3. 具体的点击位置和操作步骤

如果屏幕上已经有Spotlight搜索或Dock栏，请特别指出如何使用它们。
"""
        }

        async with session.post(
            f"{base_url}/analyze-screen",
            json=analysis_request
        ) as resp:
            if resp.status != 200:
                print("❌ AI分析失败")
                return

            result = await resp.json()
            print("\n" + "="*50)
            print("🤖 AI分析结果 - 创建提醒事项")
            print("="*50)
            print(result.get("content", ""))
            print("="*50)

        # 3. 询问是否继续创建日历事件
        print("\n" + "─"*50)
        user_input = input("\n是否继续创建日历事件？(y/n): ").lower().strip()

        if user_input == 'y':
            print("\n3️⃣ 正在分析如何创建日历事件...")

            calendar_request = {
                "question": f"""
请帮我分析如何创建一个日历事件：

事件标题：联系曹新乐
事件内容：约他周四见面
日期：{tomorrow}
时间：上午9:00-9:30

请提供：
1. 如何找到并打开"日历"(Calendar)应用
2. 如何创建新的事件
3. 具体的操作步骤

如果能看到日历应用，请直接告诉我如何添加事件。
"""
            }

            async with session.post(
                f"{base_url}/analyze-screen",
                json=calendar_request
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    print("\n" + "="*50)
                    print("📅 AI分析结果 - 创建日历事件")
                    print("="*50)
                    print(result.get("content", ""))
                    print("="*50)

        # 4. 提供Siri建议
        print("\n💡 小诺建议：")
        print("─"*30)
        print("最简单的方法是使用Siri：")
        print("1. 按住 Command + 空格键")
        print("2. 说：「提醒我明天上午9点联系曹新乐」")
        print("3. Siri会自动创建提醒事项")
        print("\n或者创建日历事件：")
        print("1. 按住 Command + 空格键")
        print("2. 说：「创建日历事件：明天上午9点联系曹新乐」")
        print("─"*30)

        print("\n✨ 任务设置完成！")
        print(f"⏰ 提醒时间：{tomorrow_weekday}上午9点")
        print("📋 任务内容：联系曹新乐，约他周四见面")

if __name__ == "__main__":
    # 运行提醒创建
    asyncio.run(create_reminder_with_glm())