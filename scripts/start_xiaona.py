#!/usr/bin/env python3
"""小娜专业版启动脚本 - 修正版"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'core' / 'reasoning'))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    print("启动小娜·天秤女神...")

    try:
        # 初始化提示词系统
        try:
            from core.agents.prompts.xiaona_prompts import get_system_prompt
            from core.prompts.output_styles import get_style_manager

            # 预热输出风格管理器
            style_mgr = get_style_manager()
            style_mgr.load_all_styles()
            logger.info("提示词系统已初始化 (OutputStyleManager 已加载)")

            # 预热条件化提示词组装
            _ = get_system_prompt()
            logger.info("条件化提示词组装已就绪")
        except Exception as e:
            logger.warning(f"提示词系统初始化警告（不影响启动）: {e}")

        # 初始化声明式 Agent
        try:
            from core.agents.declarative import load_all_agents
            definitions = load_all_agents()
            logger.info(f"声明式 Agent 已加载: {list(definitions.keys())}")
        except Exception as e:
            logger.warning(f"声明式 Agent 加载跳过: {e}")

        # 导入小娜智能体
        from core.agents.xiaona_professional import XiaonaProfessionalAgent

        # 初始化小娜（使用config字典）
        config = {
            "llm_provider": "anthropic",
            "llm_model": "claude-3-5-sonnet-20241022",
        }

        agent = XiaonaProfessionalAgent(config=config)

        # 初始化智能体
        await agent.initialize()

        print("✅ 小娜已初始化")
        print("📱 小娜服务就绪")
        print("🌸 小娜正在等待任务...")

        # 保持运行
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 小娜正在关闭...")
            await agent.shutdown()
            print("✅ 小娜已关闭")

    except Exception as e:
        logger.error(f"❌ 小娜启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
