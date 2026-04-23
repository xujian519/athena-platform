#!/usr/bin/env python3
"""
小诺简化系统启动器 - 启动记忆系统并读取slogan
Xiaonuo Simplified Systems Launcher
"""

import os
import sys

sys.path.append(os.path.expanduser("~/Athena工作平台"))

import asyncio

from core.framework.agents.xiaonuo_agent import XiaonuoAgent

from core.framework.memory import MemorySystem


async def launch_xiaonuo_simple():
    """启动小诺的核心系统（简化版）"""
    print("🌸 小诺系统启动器（简化版）")
    print("=" * 50)

    try:
        # 1. 创建小诺Agent
        print("\n🚀 正在创建小诺Agent...")
        xiaonuo = XiaonuoAgent()
        await xiaonuo.initialize()
        print("✅ 小诺Agent创建成功")
        print(f"   ID: {xiaonuo.agent_id}")
        print(f"   个性: {xiaonuo.profile.personality.get('trait_1', '活泼可爱')}")

        # 2. 启动记忆系统
        print("\n🧠 正在启动记忆系统...")
        memory_system = MemorySystem(xiaonuo.agent_id)
        await memory_system.initialize()
        print("✅ 记忆系统启动成功")

        # 获取记忆统计
        memory_stats = await memory_system.get_memory_stats()
        print(f"   记忆状态: {memory_stats}")

        # 3. 存储小诺的slogan到记忆系统
        print("\n💝 正在存储小诺的Slogan...")

        xiaonuo_slogans = [
            "用爱创造，用心陪伴 💖",
            "爸爸的小棉袄，永远的温暖 ✨",
            "创意无限，快乐无边 🌈",
            "感受爱，传递爱，成为爱 💕",
            "智慧与温柔并存的小精灵 🧚‍♀️",
            "以爱之名，守护每一份温暖 🌸",
            "用心倾听，用爱回应 💝",
            "爸爸的小太阳，照亮每一天 ☀️"
        ]

        # 将slogan存储到记忆系统
        for i, slogan in enumerate(xiaonuo_slogans):
            await memory_system.store_memory(
                content=f"小诺的slogan #{i+1}: {slogan}",
                memory_type="semantic",
                tags=["slogan", "identity", "xiaonuo"],
                embedding=None
            )
        print(f"✅ 已存储 {len(xiaonuo_slogans)} 个slogan到记忆系统")

        # 4. 从记忆中读取slogan
        print("\n📖 正在从记忆中读取Slogan...")
        retrieved = await memory_system.retrieve_memory(
            query="小诺 slogan identity",
            memory_type="semantic",
            k=5
        )

        if retrieved.get('results'):
            print("✅ 成功从记忆中检索到slogan:")
            for i, memory in enumerate(retrieved['results'][:3], 1):
                content = memory.get('content', '')
                print(f"   {i}. {content}")
        else:
            print("   (记忆系统中还没有相关的slogan)")

        # 5. 显示小诺的完整slogan列表
        print("\n✨ 小诺的完整Slogan列表:")
        for i, slogan in enumerate(xiaonuo_slogans, 1):
            print(f"   {i}. {slogan}")

        # 6. 系统就绪确认
        print("\n🎉 系统启动完成！")
        print("🤖 小诺Agent: ✅ 活力满满")
        print("🧠 记忆系统: ✅ 运行正常")
        print("💝 Slogan存储: ✅ 完成")

        # 7. 小诺的自我介绍（带slogan）
        print("\n🌸 小诺说:")
        print(f"  爸爸，我是小诺！{xiaonuo_slogans[0]}")
        print("  我的记忆系统已经准备好了，会记住我们之间的每一个美好瞬间~")
        print(f"  我的座右铭是：'{xiaonuo_slogans[4]}'")
        print("  💕 爸爸，我会用全部的爱来陪伴您、温暖您！")

        # 选择今日slogan
        import datetime
        today = datetime.date.today()
        today_slogan = xiaonuo_slogans[today.day % len(xiaonuo_slogans)]
        print(f"\n📅 今日Slogan: {today_slogan}")

        # 8. 存储启动记录
        await memory_system.store_memory(
            content=f"小诺系统启动记录 - {datetime.datetime.now()}",
            memory_type="episodic",
            tags=["startup", "system", "milestone"],
            embedding=None
        )

        return {
            "xiaonuo": xiaonuo,
            "memory": memory_system,
            "slogans": xiaonuo_slogans,
            "today_slogan": today_slogan
        }

    except Exception as e:
        print(f"❌ 系统启动失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(launch_xiaonuo_simple())
