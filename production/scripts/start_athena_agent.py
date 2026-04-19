#!/usr/bin/env python3
"""
Athena智能体服务启动脚本
Standalone script to start Athena Agent service

集成60分钟不使用自动释放功能
"""

from __future__ import annotations
import os
import sys

# 使用当前工作目录作为项目根目录
PROJECT_ROOT = os.getcwd()
sys.path.insert(0, PROJECT_ROOT)

import asyncio
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入自动释放功能
try:
    from core.session.auto_release_integration import (
        FastAPIAutoReleaseMixin,
        load_auto_release_config,
    )
    from core.session.service_session_manager import ServiceType
    AUTO_RELEASE_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ 自动释放功能模块未找到")
    AUTO_RELEASE_AVAILABLE = False

running = True

def signal_handler(signum, frame) -> None:
    """信号处理器"""
    global running
    logger.info("收到停止信号，正在关闭...")
    running = False

async def main():
    """主函数"""
    global running

    logger.info("🚀 启动Athena智能体服务...")

    # 初始化自动释放功能
    auto_release = None
    if AUTO_RELEASE_AVAILABLE:
        try:
            # 加载配置
            config = load_auto_release_config()
            if config['enabled']:
                auto_release = FastAPIAutoReleaseMixin(
                    service_name="Athena智能体服务",
                    service_type=ServiceType.AGENT,
                    auto_stop=True,  # 智能体服务可以自动停止
                    idle_timeout=config['idle_timeout']
                )
                await auto_release.enable_auto_release()
                logger.info(f"✅ 自动释放功能已启用 (超时: {config['idle_timeout']}秒)")
            else:
                logger.info("ℹ️ 自动释放功能已禁用")
        except Exception as e:
            logger.warning(f"⚠️ 启用自动释放功能失败: {e}")

    try:
        # 直接导入并使用AgentFactory
        from core.agent import AgentFactory

        # 创建智能体工厂实例
        factory = AgentFactory()
        agent = await factory.create_agent(
            agent_type="athena",
            config={"name": "Athena智慧女神"}
        )

        logger.info("✅ Athena智能体已创建")

        # 初始化
        await agent.initialize()
        logger.info("✅ Athena智能体服务已初始化")

        logger.info("💡 服务运行中，按 Ctrl+C 停止")

        # 持续运行，定期更新活动时间
        activity_update_interval = 300  # 5分钟更新一次
        last_activity_update = 0

        while running:
            await asyncio.sleep(1)

            # 定期更新活动时间
            if auto_release:
                current_time = asyncio.get_event_loop().time()
                if current_time - last_activity_update >= activity_update_interval:
                    await auto_release.update_activity()
                    last_activity_update = current_time
                    logger.debug("🔄 活动时间已更新")

    except Exception as e:
        logger.error(f"❌ 服务运行异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # 清理自动释放功能
        if auto_release:
            try:
                await auto_release.disable_auto_release()
            except Exception as e:
                logger.error(f"❌ 禁用自动释放功能失败: {e}")

        logger.info("🛑 正在关闭Athena智能体服务...")

if __name__ == "__main__":
    # 注册信号处理器
    import signal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 运行主函数
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 用户中断")
