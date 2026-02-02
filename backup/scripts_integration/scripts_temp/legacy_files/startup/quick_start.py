#!/usr/bin/env python3
"""
Athena智能体平台 - 快速启动脚本
"""

import asyncio
import logging
import os
import sys

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.insert(0, os.getcwd())

async def quick_start():
    """快速启动核心功能"""
    logger.info("\n🚀 Athena智能体平台 - 快速启动")
    logger.info(str('=' * 50))

    # 检测系统信息
    try:
        import platform
        logger.info(f"\n📱 系统信息:")
        logger.info(f"  • 处理器: {platform.processor()}")
        logger.info(f"  • 架构: {platform.machine()}")

        # 检查Apple Silicon
        if platform.machine() in ['arm64', 'arm']:
            logger.info('  • ✅ Apple Silicon 检测到')

            # 检查MPS
            try:
                import torch
                if torch.backends.mps.is_available():
                    logger.info('  • ✅ MPS加速可用')
                else:
                    logger.info('  • ⚠️ MPS加速不可用')
            except:
                logger.info('  • ⚠️ PyTorch未安装')
    except:
        pass

    # 初始化核心模块
    logger.info(f"\n📦 初始化核心模块...")

    initialized = []

    # 1. 决策框架
    try:
        from core.cognition.explainable_decision_framework import (
            explainable_decision_engine,
        )
        initialized.append('可解释决策框架')
    except Exception as e:
        logger.warning(f"决策框架: {e}")

    # 2. 智能记忆
    try:
        from core.memory.smart_forgetting_strategy import smart_forgetting_strategy
        initialized.append('智能记忆系统')
    except Exception as e:
        logger.warning(f"记忆系统: {e}")

    # 3. 并发控制
    try:
        from core.execution.fine_grained_concurrency import (
            fine_grained_concurrency_controller,
        )
        await fine_grained_concurrency_controller.start()
        initialized.append('并发控制系统')
    except Exception as e:
        logger.warning(f"并发控制: {e}")

    # 4. 实时监控
    try:
        from core.execution.real_time_monitor import real_time_monitor
        await real_time_monitor.start()
        initialized.append('实时监控系统')
    except Exception as e:
        logger.warning(f"实时监控: {e}")

    # 5. 快速学习
    try:
        from core.learning.rapid_learning import rapid_learning_engine
        initialized.append('快速学习引擎')
    except Exception as e:
        logger.warning(f"快速学习: {e}")

    # 显示初始化结果
    logger.info("\n✅ 成功初始化:")
    for module in initialized:
        logger.info(f"  • {module}")

    # 显示系统状态
    logger.info("\n🎯 系统状态:")
    logger.info(f"  • 已初始化模块: {len(initialized)}个")
    logger.info(str(f"  • WebSocket监控: ws://localhost:8765' if '实时监控系统' in initialized else '  • WebSocket监控: 未启用"))
    logger.info(f"  • 状态: 运行中")

    # 性能提示
    if 'Apple Silicon 检测到' in str(platform.machine()):
        logger.info("\n💡 Apple Silicon优化提示:")
        logger.info('  • 系统自动检测到M4芯片')
        logger.info('  • GPU加速已启用（如果可用）')
        logger.info('  • 推荐使用MPS后端加速')

    logger.info("\n📌 下一步操作:")
    logger.info('  1. 运行性能检查: python3 check_performance.py')
    logger.info('  2. 查看实时监控: 连接 ws://localhost:8765')
    logger.info('  3. 使用API进行任务处理')

    # 保持运行
    logger.info("\n🔄 系统正在运行中...")
    logger.info('按 Ctrl+C 停止')

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("\n\n👋 正在关闭系统...")

        # 清理资源
        try:
            if '并发控制系统' in initialized:
                await fine_grained_concurrency_controller.stop()
                logger.info('✅ 并发控制已停止')
        except:
            pass

        try:
            if '实时监控系统' in initialized:
                from core.execution.real_time_monitor import stop_real_time_monitoring
                await stop_real_time_monitoring()
                logger.info('✅ 实时监控已停止')
        except:
            pass

        logger.info("\n🎯 系统已安全关闭")


if __name__ == '__main__':
    try:
        asyncio.run(quick_start())
    except Exception as e:
        logger.error(f"启动失败: {e}")
        sys.exit(1)