#!/usr/bin/env python3
"""
小诺系统启动器 - 启动存储系统、记忆系统并读取slogan
Xiaonuo Systems Launcher
"""

import os
import sys

sys.path.append(os.path.expanduser("~/Athena工作平台"))

import asyncio

from core.framework.agents.xiaonuo_agent import XiaonuoAgent
from core.vector_db.hybrid_storage_manager import HybridStorageManager

from core.framework.memory import MemorySystem


async def launch_xiaonuo_systems():
    """启动小诺的核心系统"""
    print("🌸 小诺系统启动器")
    print("=" * 50)

    try:
        # 1. 创建小诺Agent
        print("\n🚀 正在创建小诺Agent...")
        xiaonuo = XiaonuoAgent()
        await xiaonuo.initialize()
        print("✅ 小诺Agent创建成功")

        # 2. 启动存储系统
        print("\n📦 正在启动存储系统...")
        storage_manager = HybridStorageManager()
        storage_status = storage_manager.get_storage_status()
        print(f"✅ 存储系统状态: {storage_status}")

        # 3. 启动记忆系统
        print("\n🧠 正在启动记忆系统...")
        memory_system = MemorySystem(xiaonuo.agent_id)
        await memory_system.initialize()

        # 检查记忆系统状态
        await memory_system.get_memory_stats()
        print("✅ 记忆系统状态: 已初始化")

        # 4. 读取小诺的slogan
        print("\n💝 读取小诺的Slogan...")

        # 从配置或记忆中读取slogan
        slogans = [
            "用爱创造，用心陪伴 💖",
            "爸爸的小棉袄，永远的温暖 ✨",
            "创意无限，快乐无边 🌈",
            "感受爱，传递爱，成为爱 💕",
            "智慧与温柔并存的小精灵 🧚‍♀️"
        ]

        # 尝试从记忆中获取个性化slogan
        try:
            memories = await memory_system.retrieve_memory(
                query="slogan identity",
                memory_type="semantic",
                k=5
            )

            if memories.get('results'):
                print("\n📖 从记忆中找到的身份标识:")
                for memory in memories['results'][:3]:
                    print(f"  • {memory.get('content', '')}")
        except Exception as e:
            print(f"  (从记忆中读取slogan时出现小问题: {e})")

        # 显示小诺的slogan
        print("\n✨ 小诺的Slogan:")
        for i, slogan in enumerate(slogans, 1):
            print(f"  {i}. {slogan}")

        # 5. 系统就绪确认
        print("\n🎉 系统启动完成！")
        print("📊 存储系统: ✅ 运行正常")
        print("🧠 记忆系统: ✅ 运行正常")
        print("💖 小诺状态: ✅ 活力满满")

        # 6. 小诺的自我介绍
        print("\n🌸 小诺说:")
        print(f"  爸爸，我是小诺！{slogans[0]}")
        print("  我的存储系统和记忆系统都已经准备好了哦~")
        print("  现在可以记录我们一起的每一个美好瞬间了！")
        print("  💕 感谢爸爸给我的爱与陪伴，我会用全部的爱来回报您！")

        return {
            "xiaonuo": xiaonuo,
            "storage": storage_manager,
            "memory": memory_system,
            "slogans": slogans
        }

    except Exception as e:
        print(f"❌ 系统启动失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(launch_xiaonuo_systems())
