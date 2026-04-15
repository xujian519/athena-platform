#!/usr/bin/env python3
"""
Athena生产环境启动脚本
Production Environment Startup Script

启动所有核心服务，包括:
- 核心引擎 (学习、通信、评估)
- API服务
- 记忆系统
- 工具系统

作者: Athena AI系统
版本: v1.0.0
"""

from __future__ import annotations
import asyncio
import signal
import sys
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.communication import CommunicationEngine
from core.evaluation import EvaluationEngine
from core.learning import LearningEngine

# 全局变量
services: dict = {}
running = True


class AthenaProductionService:
    """Athena生产服务"""

    def __init__(self):
        self.learning_engine = None
        self.communication_engine = None
        self.evaluation_engine = None
        self.initialized = False

    async def initialize(self):
        """初始化所有服务"""
        print("\n" + "=" * 70)
        print("🚀 Athena生产环境启动".center(70))
        print("=" * 70 + "\n")

        # 1. 学习引擎
        print("📚 [1/3] 启动学习引擎...")
        self.learning_engine = LearningEngine("production_learning")
        await self.learning_engine.initialize()
        print("   ✅ 学习引擎已启动\n")

        # 2. 通信引擎
        print("💬 [2/3] 启动通信引擎...")
        self.communication_engine = CommunicationEngine("production_comm")
        await self.communication_engine.initialize()
        print("   ✅ 通信引擎已启动\n")

        # 3. 评估引擎
        print("📊 [3/3] 启动评估引擎...")
        self.evaluation_engine = EvaluationEngine("production_eval")
        await self.evaluation_engine.initialize()
        print("   ✅ 评估引擎已启动\n")

        self.initialized = True

        print("=" * 70)
        print("✅ 所有服务启动完成！".center(70))
        print("=" * 70)
        print("\n📊 服务状态:")
        print("   📚 学习引擎:  运行中")
        print("   💬 通信引擎:  运行中")
        print("   📊 评估引擎:  运行中")
        print("\n💡 提示:")
        print("   • 按 Ctrl+C 停止所有服务")
        print("   • 查看日志: tail -f production/logs/services.log")
        print("=" * 70 + "\n")

    async def shutdown(self):
        """关闭所有服务"""
        print("\n" + "=" * 70)
        print("🔄 正在停止所有服务...".center(70))
        print("=" * 70 + "\n")

        if self.learning_engine:
            await self.learning_engine.shutdown()
            print("   ✅ 学习引擎已停止")

        if self.communication_engine:
            await self.communication_engine.shutdown()
            print("   ✅ 通信引擎已停止")

        if self.evaluation_engine:
            await self.evaluation_engine.shutdown()
            print("   ✅ 评估引擎已停止")

        print("\n" + "=" * 70)
        print("✅ 所有服务已安全停止".center(70))
        print("=" * 70 + "\n")

    async def run(self):
        """运行服务（保持活跃）"""
        while running:
            await asyncio.sleep(1)


# 信号处理
production_service = None


def signal_handler(sig, frame):
    """处理停止信号"""
    global running
    print("\n\n⚠️  接收到停止信号...")
    running = False


async def main():
    """主函数"""
    global production_service

    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 创建服务
    production_service = AthenaProductionService()

    try:
        # 初始化
        await production_service.initialize()

        # 保持运行
        await production_service.run()

    except KeyboardInterrupt:
        print("\n⚠️  键盘中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理
        if production_service.initialized:
            await production_service.shutdown()


if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                         ║
║           🚀 Athena生产环境启动脚本 🚀                                   ║
║                                                                         ║
║  启动的服务:                                                             ║
║  • 学习引擎 (Learning Engine)                                            ║
║  • 通信引擎 (Communication Engine)                                       ║
║  • 评估引擎 (Evaluation Engine)                                          ║
║                                                                         ║
╚═══════════════════════════════════════════════════════════════════════╝
""")

    asyncio.run(main())
