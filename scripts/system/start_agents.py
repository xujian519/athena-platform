#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一Agent启动脚本
Unified Agent Startup Script

同时启动小诺和Athena智能体

作者: Athena AI系统
版本: v1.0.0
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Any

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局变量
running = True
xiaonuo_agent = None
athena_agent = None


def signal_handler(signum, frame):
    """信号处理器"""
    global running
    logger.info("收到停止信号，正在关闭...")
    running = False


async def create_xiaonuo_agent():
    """创建小诺智能体"""
    from core.agent import AgentFactory

    factory = AgentFactory()
    await factory.initialize()

    agent = await factory.create_agent(
        agent_type="xiaonuo",
        config={
            "name": "小诺",
            "perception": {
                "emotional_sensitivity": 0.95,
                "creativity_mode": "high",
                "family_context": True,
            },
        }
    )

    return agent, factory


async def create_athena_agent():
    """创建Athena智能体"""
    from core.agent import AgentFactory

    factory = AgentFactory()
    await factory.initialize()

    agent = await factory.create_agent(
        agent_type="athena",
        config={
            "name": "Athena",
            "perception": {
                "analytical_mode": True,
                "technical_context": True,
                "business_context": True,
            },
        }
    )

    return agent, factory


async def agent_interaction_loop(xiaonuo, athena):
    """智能体交互循环"""
    logger.info("💬 智能体交互循环启动...")

    interaction_count = 0
    while running:
        try:
            await asyncio.sleep(5)

            interaction_count += 1
            if interaction_count % 60 == 1:  # 每分钟打印一次状态
                status_xiaonuo = await xiaonuo.get_status()
                status_athena = await athena.get_status()

                logger.info(f"📊 小诺状态: {status_xiaonuo['state']}")
                logger.info(f"📊 Athena状态: {status_athena['state']}")

        except asyncio.CancelledError:
            logger.info("交互循环被取消")
            break
        except Exception as e:
            logger.error(f"交互循环错误: {e}")
            await asyncio.sleep(1)


async def main():
    """主函数"""
    global xiaonuo_agent, athena_agent, running

    print("""
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                         ║
║           🚀 Athena工作平台 - 统一Agent启动器 🚀                       ║
║                                                                         ║
║  启动的智能体:                                                           ║
║  • 🌸 小诺 (Xiaonuo) - 情感精灵                                         ║
║  • 🦊 Athena (Athena) - 智慧女神                                        ║
║                                                                         ║
╚═══════════════════════════════════════════════════════════════════════╝
""")

    xiaonuo_factory = None
    athena_factory = None

    try:
        # 创建小诺智能体
        logger.info("🌸 创建小诺智能体...")
        xiaonuo_agent, xiaonuo_factory = await create_xiaonuo_agent()
        logger.info(f"✅ 小诺智能体已创建: {xiaonuo_agent.agent_id}")

        # 创建Athena智能体
        logger.info("🦊 创建Athena智能体...")
        athena_agent, athena_factory = await create_athena_agent()
        logger.info(f"✅ Athena智能体已创建: {athena_agent.agent_id}")

        # 建立姐妹关系
        logger.info("💕 建立姐妹关系...")
        await xiaonuo_factory._establish_sister_relationship(xiaonuo_agent, athena_agent)
        logger.info("✅ 姐妹关系已建立")

        print("\n" + "=" * 70)
        print("✅ 所有智能体启动完成！".center(70))
        print("=" * 70)
        print("\n📊 智能体状态:")
        print(f"   🌸 小诺: {xiaonuo_agent.agent_id} - {xiaonuo_agent.state.value}")
        print(f"   🦊 Athena: {athena_agent.agent_id} - {athena_agent.state.value}")
        print("\n💡 提示:")
        print("   • 按 Ctrl+C 停止所有智能体")
        print("   • 智能体将保持运行状态")
        print("=" * 70 + "\n")

        # 启动交互循环
        await agent_interaction_loop(xiaonuo_agent, athena_agent)

    except KeyboardInterrupt:
        logger.info("\n⚠️ 键盘中断")
    except Exception as e:
        logger.error(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理
        logger.info("🔄 正在关闭智能体...")

        if xiaonuo_agent:
            try:
                await xiaonuo_agent.shutdown()
                logger.info("✅ 小诺智能体已关闭")
            except Exception as e:
                logger.error(f"❌ 关闭小诺失败: {e}")

        if athena_agent:
            try:
                await athena_agent.shutdown()
                logger.info("✅ Athena智能体已关闭")
            except Exception as e:
                logger.error(f"❌ 关闭Athena失败: {e}")

        if xiaonuo_factory:
            try:
                await xiaonuo_factory.shutdown_all_agents()
            except Exception:
                pass

        if athena_factory:
            try:
                await athena_factory.shutdown_all_agents()
            except Exception:
                pass

        logger.info("✅ 所有智能体已安全停止")


if __name__ == "__main__":
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 运行主函数
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 用户中断")
    finally:
        print("\n👋 智能体系统已退出")
