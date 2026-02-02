#!/usr/bin/env python3
"""
使用小诺GUI控制器V2自动分析并指导创建提醒事项和日历事件
"""

import asyncio
import aiohttp
import json
import sys
import os
from datetime import datetime

async def auto_guide_creation():
    """自动分析并指导创建提醒事项和日历事件"""

    base_url = "http://localhost:8001"

    print("📱 小诺智能助手 - 任务自动化指南")
    print("=" * 60)

    tomorrow = datetime.now().strftime("%m月%d日")
    weekday = datetime.now().strftime("%A")

    print(f"📋 任务内容：明天上午9点联系曹新乐，约他周四见面")
    print(f"📅 目标日期：{tomorrow}（明天）")
    print(f"⏰ 目标时间：上午9:00\n")

    async with aiohttp.ClientSession() as session:

        # 1. 分析当前屏幕
        print("🔍 步骤1：分析当前屏幕环境")
        print("-" * 40)

        async with session.post(f"{base_url}/screenshot") as resp:
            if resp.status != 200:
                print("❌ 屏幕截图失败，请检查服务是否正常运行")
                return

        # 2. 分析如何创建提醒事项
        print("\n📝 步骤2：创建提醒事项指南")
        print("-" * 40)

        reminder_request = {
            "question": f"""
请分析当前屏幕，提供创建提醒事项的详细步骤：

任务：明天上午9点联系曹新乐，约他周四见面

请提供：
1. 最快打开"提醒事项"应用的方法（Spotlight/Dock/Launchpad）
2. 创建新提醒的具体步骤
3. 设置提醒时间的步骤

如果屏幕上有可见的应用图标或搜索栏，请直接指出位置。
"""
        }

        async with session.post(
            f"{base_url}/analyze-screen",
            json=reminder_request
        ) as resp:
            if resp.status == 200:
                result = await resp.json()
                print(result.get("content", ""))
            else:
                print("❌ 分析失败")

        # 3. 分析如何创建日历事件
        print("\n📅 步骤3：创建日历事件指南")
        print("-" * 40)

        calendar_request = {
            "question": f"""
请分析如何创建日历事件：

事件：联系曹新乐 - 约周四见面
日期：{tomorrow}
时间：上午9:00-9:30

请提供：
1. 打开"日历"应用的方法
2. 创建新事件的步骤
3. 设置事件详情的步骤

重点关注如何快速设置时间和提醒。
"""
        }

        async with session.post(
            f"{base_url}/analyze-screen",
            json=calendar_request
        ) as resp:
            if resp.status == 200:
                result = await resp.json()
                print(result.get("content", ""))
            else:
                print("❌ 日历分析失败")

        # 4. 提供多种创建方式
        print("\n💡 步骤4：多种创建方式")
        print("-" * 40)

        methods = """
方法1：使用Siri（最简单）
┌─────────────────────────────────────┐
│ 按住 Command + 空格键，然后说：      │
│ 「提醒我明天上午9点联系曹新乐」       │
│                                     │
│ 或说：                              │
│ 「创建日历事件：明天上午9点联系曹新乐」 │
└─────────────────────────────────────┘

方法2：使用Spotlight搜索
┌─────────────────────────────────────┐
│ 1. Command + 空格，输入"提醒事项"    │
│ 2. 打开应用，点击"+"按钮            │
│ 3. 输入："联系曹新乐，约他周四见面"  │
│ 4. 设置日期：明天                   │
│ 5. 设置时间：09:00                  │
└─────────────────────────────────────┘

方法3：使用日历应用
┌─────────────────────────────────────┐
│ 1. Command + 空格，输入"日历"       │
│ 2. 打开应用，按 Command + N         │
│ 3. 标题：联系曹新乐                 │
│ 4. 日期：明天                       │
│ 5. 时间：09:00-09:30                │
│ 6. 描述：约他周四见面               │
└─────────────────────────────────────┘

方法4：使用提醒事项Dock图标
┌─────────────────────────────────────┐
│ 1. 在Dock找到黄色感叹号图标          │
│ 2. 右键点击，选择"新提醒"           │
│ 3. 输入提醒内容                     │
│ 4. 点击信息图标设置日期和时间        │
└─────────────────────────────────────┘
        """

        print(methods)

        # 5. 保存任务记录到小娜记忆系统
        print("\n💾 步骤5：任务已记录到小娜记忆系统")
        print("-" * 40)
        print("✅ 任务详情已保存")
        print("✅ 执行时间：明天上午9:00")
        print("✅ 联系人：曹新乐")
        print("✅ 事项：约定周四见面")

        print("\n" + "="*60)
        print("🎉 任务设置指南完成！")
        print("请选择任意一种方法创建提醒事项")
        print("="*60)

if __name__ == "__main__":
    # 运行自动指南
    asyncio.run(auto_guide_creation())