#!/usr/bin/env python3
"""
Athena核心引擎演示脚本
Core Engines Demo Script

演示学习、通信、评估三个核心引擎的协同工作

作者: Athena AI系统
版本: v1.0.0
"""

from __future__ import annotations
import asyncio
import sys
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.communication import CommunicationEngine
from core.evaluation import EvaluationEngine
from core.learning import LearningEngine


class AthenaCoreSystem:
    """Athena核心系统 - 整合三大引擎"""

    def __init__(self, agent_id: str = "athena_demo"):
        self.agent_id = agent_id
        self.learning_engine = None
        self.communication_engine = None
        self.evaluation_engine = None
        self.initialized = False

    async def initialize(self):
        """初始化所有引擎"""
        print("\n" + "=" * 60)
        print("🚀 Athena核心系统初始化".center(60))
        print("=" * 60 + "\n")

        # 1. 初始化学习引擎
        print("📚 [1/3] 初始化学习引擎...")
        self.learning_engine = LearningEngine(f"{self.agent_id}_learning")
        await self.learning_engine.initialize()
        print("   ✅ 学习引擎已就绪\n")

        # 2. 初始化通信引擎
        print("💬 [2/3] 初始化通信引擎...")
        self.communication_engine = CommunicationEngine(f"{self.agent_id}_comm")
        await self.communication_engine.initialize()
        print("   ✅ 通信引擎已就绪\n")

        # 3. 初始化评估引擎
        print("📊 [3/3] 初始化评估引擎...")
        self.evaluation_engine = EvaluationEngine(f"{self.agent_id}_eval")
        await self.evaluation_engine.initialize()
        print("   ✅ 评估引擎已就绪\n")

        self.initialized = True
        print("=" * 60)
        print("✅ Athena核心系统初始化完成！".center(60))
        print("=" * 60 + "\n")

    async def process_user_input(self, user_input: str) -> dict:
        """处理用户输入 - 三引擎协同"""
        print(f"\n{'─' * 60}")
        print(f"👤 用户输入: {user_input}")
        print(f"{'─' * 60}\n")

        # 1. 通信引擎接收消息
        print("💬 通信处理...")
        comm_result = await self.communication_engine.send_message(
            {"content": user_input, "type": "user_input"}
        )
        print(f"   → 消息已路由: {comm_result['status']}")

        # 2. 学习引擎分析并学习
        print("\n📚 学习处理...")
        learning_result = await self.learning_engine.learn({
            "input": user_input,
            "context": "demo"
        })
        print(f"   → 学习状态: {learning_result['status']}")

        # 3. 评估引擎给出评估
        print("\n📊 评估处理...")
        eval_result = await self.evaluation_engine.evaluate({
            "input": user_input,
            "quality": "demo"
        })
        print(f"   → 评估分数: {eval_result['score']}")
        print(f"   → 反馈: {eval_result['feedback']}")

        return {
            "communication": comm_result,
            "learning": learning_result,
            "evaluation": eval_result
        }

    async def demo_conversation(self):
        """演示对话流程"""
        if not self.initialized:
            await self.initialize()

        # 演示对话
        conversations = [
            "你好，Athena！",
            "什么是机器学习？",
            "帮我分析一下这个问题",
            "谢谢你的帮助！"
        ]

        for conv in conversations:
            await self.process_user_input(conv)
            await asyncio.sleep(0.5)  # 模拟处理时间

    async def shutdown(self):
        """关闭所有引擎"""
        print("\n" + "=" * 60)
        print("🔄 关闭Athena核心系统".center(60))
        print("=" * 60 + "\n")

        if self.learning_engine:
            await self.learning_engine.shutdown()
            print("   ✅ 学习引擎已关闭")

        if self.communication_engine:
            await self.communication_engine.shutdown()
            print("   ✅ 通信引擎已关闭")

        if self.evaluation_engine:
            await self.evaluation_engine.shutdown()
            print("   ✅ 评估引擎已关闭")

        print("\n✅ 所有引擎已安全关闭\n")
        print("=" * 60 + "\n")


async def main():
    """主函数"""
    # 创建系统
    athena = AthenaCoreSystem()

    try:
        # 初始化
        await athena.initialize()

        # 运行演示对话
        print("\n🎬 开始演示对话流程...\n")
        await athena.demo_conversation()

        print("\n" + "=" * 60)
        print("🎉 演示完成！".center(60))
        print("=" * 60)

    finally:
        # 确保关闭
        await athena.shutdown()


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║        🤖 Athena核心引擎演示程序 🤖                         ║
║                                                            ║
║  演示内容:                                                 ║
║  • 学习引擎 (Learning Engine) - 从交互中学习                ║
║  • 通信引擎 (Communication Engine) - 处理消息通信           ║
║  • 评估引擎 (Evaluation Engine) - 评估响应质量             ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
""")

    asyncio.run(main())
