#!/usr/bin/env python3
"""
小诺协调器生产环境启动脚本
Xiaonuo Coordinator Production Startup Script
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent  # 指向Athena工作平台根目录
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'core' / 'reasoning'))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(PROJECT_ROOT / 'logs/xiaonuo.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def start_xiaonuo_coordinator():
    """启动小诺协调器"""
    print("=" * 60)
    print("启动小诺·双鱼公主协调器...")
    print("=" * 60)

    try:
        # 初始化提示词系统
        try:
            from core.prompts.output_styles import get_style_manager

            # 预热输出风格管理器
            style_mgr = get_style_manager()
            style_mgr.load_all_styles()
            logger.info("提示词系统已初始化 (OutputStyleManager 已加载)")
        except Exception as e:
            logger.warning(f"提示词系统初始化警告（不影响启动）: {e}")

        # 初始化声明式 Agent
        try:
            from core.agents.declarative import load_all_agents
            definitions = load_all_agents()
            logger.info(f"声明式 Agent 已加载: {list(definitions.keys())}")
        except Exception as e:
            logger.warning(f"声明式 Agent 加载跳过: {e}")

        # 导入小诺协调器
        from core.agents.xiaonuo_coordinator import XiaonuoAgent

        # 配置
        config = {
            'agent_id': 'xiaonuo-pisces-v3',
            'name': '小诺·双鱼公主',
            'role': '平台协调官',
            'enable_planning': True,
            'enable_memory': True,
            'llm_provider': 'anthropic',
            'llm_model': 'claude-3-5-sonnet-20241022'
        }

        # 创建小诺实例
        logger.info("初始化小诺协调器...")
        agent = XiaonuoAgent(config)

        # 初始化
        logger.info("启动小诺系统...")
        await agent.initialize()

        print("\n" + "=" * 60)
        print("✅ 小诺协调器启动成功！")
        print("=" * 60)
        print(f"🤖 智能体ID: {config['agent_id']}")
        print(f"📋 名称: {config['name']}")
        print(f"🎯 角色: {config['role']}")
        print("💾 记忆系统: 已启用")
        print("🧠 智能规划: 已启用")
        print("=" * 60)
        print("\n🌸 小诺正在等待任务...\n")

        # 保持运行
        try:
            while True:
                await asyncio.sleep(10)
        except KeyboardInterrupt:
            print("\n👋 正在关闭小诺...")
            await agent.shutdown()
            print("✅ 小诺已关闭")

    except Exception as e:
        logger.error(f"小诺启动失败: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    # 创建必要目录
    os.makedirs(PROJECT_ROOT / 'logs', exist_ok=True)
    os.makedirs(PROJECT_ROOT / 'data', exist_ok=True)

    # 启动小诺
    asyncio.run(start_xiaonuo_coordinator())
