#!/usr/bin/env python3
"""
Athena智能体平台 - 优化版启动脚本
"""

# Numpy兼容性导入
from config.numpy_compatibility import array, zeros, ones, random, mean, sum, dot
import asyncio
import logging
import os
import sys
import time
from datetime import datetime

import numpy as np

# 添加项目路径
sys.path.insert(0, os.getcwd())

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OptimizedAthenaPlatform:
    """优化版Athena平台主类"""

    def __init__(self):
        self.initialized_modules = {}
        self.start_time = datetime.now()

    async def initialize(self):
        """初始化所有模块"""
        logger.info("\n🚀 启动Athena智能体平台 - 优化版")
        logger.info(str('=' * 60))

        # 1. 初始化核心模块
        await self._initialize_core_modules()

        # 2. 初始化优化模块
        await self._initialize_optimization_modules()

        # 3. 启动监控
        await self._start_monitoring()

        # 4. 显示系统状态
        self._show_system_status()

    async def _initialize_core_modules(self):
        """初始化核心模块"""
        logger.info("\n📦 初始化核心模块...")

        # 决策框架
        try:
            from core.cognition.explainable_decision_framework import (
                explainable_decision_engine,
            )
            self.initialized_modules['decision_framework'] = explainable_decision_engine
            logger.info('  ✅ 可解释决策框架')
        except Exception as e:
            logger.error(f"决策框架初始化失败: {e}")

        # 记忆系统
        try:
            from core.memory.federated_memory_system import initialize_federated_memory
            from core.memory.smart_forgetting_strategy import smart_forgetting_strategy
            self.initialized_modules['memory'] = smart_forgetting_strategy
            self.initialized_modules['federated_memory'] = initialize_federated_memory(
                agent_id='athena_optimized',
                agent_name='Athena优化版',
                agent_type='cognitive_agent',
                capabilities=['perception', 'cognition', 'memory', 'learning']
            )
            logger.info('  ✅ 智能记忆系统（含联邦记忆）')
        except Exception as e:
            logger.error(f"记忆系统初始化失败: {e}")

    async def _initialize_optimization_modules(self):
        """初始化优化模块"""
        logger.info("\n⚡ 初始化优化模块...")

        # Apple Silicon优化
        try:
            from core.acceleration.apple_silicon_optimizer import (
                apple_silicon_optimizer,
            )
            await apple_silicon_optimizer.initialize()
            self.initialized_modules['apple_silicon'] = apple_silicon_optimizer
            logger.info('  ✅ Apple Silicon优化引擎')
        except Exception as e:
            logger.error(f"Apple Silicon优化失败: {e}")

        # 并发控制
        try:
            from core.execution.fine_grained_concurrency import (
                fine_grained_concurrency_controller,
            )
            await fine_grained_concurrency_controller.start()
            self.initialized_modules['concurrency'] = fine_grained_concurrency_controller
            logger.info('  ✅ 细粒度并发控制')
        except Exception as e:
            logger.error(f"并发控制初始化失败: {e}")

        # 实时监控
        try:
            from core.execution.real_time_monitor import real_time_monitor
            await real_time_monitor.start()
            self.initialized_modules['monitor'] = real_time_monitor
            logger.info('  ✅ 实时监控系统 (ws://localhost:8765)')
        except Exception as e:
            logger.error(f"实时监控初始化失败: {e}")

        # 快速学习
        try:
            from core.learning.rapid_learning import rapid_learning_engine
            self.initialized_modules['learning'] = rapid_learning_engine
            logger.info('  ✅ 快速学习引擎')

            # 迁移学习
            try:
                from core.learning.transfer_learning_framework import (
                    transfer_learning_framework,
                )
                self.initialized_modules['transfer_learning'] = transfer_learning_framework
                logger.info('  ✅ 迁移学习框架')
            except Exception as e:
                logger.warning(f"迁移学习框架初始化失败: {e}")
        except Exception as e:
            logger.error(f"学习系统初始化失败: {e}")

    async def _start_monitoring(self):
        """启动监控"""
        logger.info("\n📈 启动系统监控...")

        # 记录自定义指标
        try:
            from core.execution.real_time_monitor import record_custom_metric
            await record_custom_metric('system_startup_time', 1.0)
            await record_custom_metric('modules_initialized', len(self.initialized_modules))
        except Exception as e:
            logger.error(f"监控启动失败: {e}")

    def _show_system_status(self):
        """显示系统状态"""
        logger.info("\n🎉 Athena优化版启动成功！")
        logger.info(str('=' * 60))

        # 启动时间
        startup_time = (datetime.now() - self.start_time).total_seconds()
        logger.info(f"⏱️  启动耗时: {startup_time:.2f}秒")

        # 已初始化模块
        logger.info(f"\n📋 已初始化模块 ({len(self.initialized_modules)}个):")
        for module_name in self.initialized_modules:
            logger.info(f"  • {module_name}")

        # 性能提示
        logger.info("\n💡 性能优化特性:")
        logger.info('  • Apple Silicon M4 GPU加速')
        logger.info('  • 细粒度并发控制')
        logger.info('  • 智能记忆管理')
        logger.info('  • 实时性能监控')
        logger.info('  • 快速自适应学习')

        # 使用提示
        logger.info("\n🔧 使用方法:")
        logger.info('  1. WebSocket监控: ws://localhost:8765')
        logger.info('  2. 运行演示: python3 demo_optimized_features.py')
        logger.info('  3. 查看性能报告: python3 check_performance.py')

    async def run_demo(self):
        """运行演示"""
        logger.info("\n🎯 运行优化功能演示...")

        # 演示并发处理
        await self._demo_concurrency()

        # 演示快速学习
        await self._demo_rapid_learning()

        # 演示智能记忆
        await self._demo_smart_memory()

        logger.info("\n✅ 演示完成！系统已就绪。")

    async def _demo_concurrency(self):
        """演示并发处理"""
        logger.info("\n⚙️  演示细粒度并发控制...")

        try:
            from core.execution.fine_grained_concurrency import (
                Priority,
                submit_concurrent_task,
            )

            # 提交不同优先级的任务
            tasks = []
            for i in range(5):
                task_id = await submit_concurrent_task(
                    self._sample_task,
                    f"Task-{i}",
                    priority=Priority.HIGH if i % 2 == 0 else Priority.NORMAL
                )
                tasks.append(task_id)

            logger.info(f"  提交了 {len(tasks)} 个并发任务")

            # 等待完成
            await asyncio.sleep(1)

            # 获取统计
            from core.execution.fine_grained_concurrency import get_concurrency_stats
            stats = await get_concurrency_stats()
            logger.info(f"  活动任务: {stats['task_stats']['active_tasks']}")
            logger.info(f"  平均执行时间: {stats['task_stats']['avg_execution_time']:.3f}秒")

        except Exception as e:
            logger.error(f"并发演示失败: {e}")

    async def _demo_rapid_learning(self):
        """演示快速学习"""
        logger.info("\n🎓 演示快速学习机制...")

        try:
            from core.learning.rapid_learning import (
                create_learning_task,
                learn_from_data,
            )

            # 创建学习任务
            await create_learning_task('demo_task', 'neural_network')

            # 从数据学习
            for i in range(10):
                await learn_from_data(
                    input_data=random((10)),
                    output_data=random((1)),
                    importance=0.8
                )

            # 获取学习统计
            from core.learning.rapid_learning import get_learning_stats
            stats = get_learning_stats()
            logger.info(f"  学习经验数: {stats['total_experiences']}")
            logger.info(f"  活动任务: {stats['active_tasks']}")
            logger.info(f"  平均性能: {stats['avg_performance']:.3f}")

        except Exception as e:
            logger.error(f"学习演示失败: {e}")

    async def _demo_smart_memory(self):
        """演示智能记忆"""
        logger.info("\n🧠 演示智能记忆管理...")

        try:
            from core.memory.smart_forgetting_strategy import (
                MemoryPriority,
                add_memory_with_forgetting,
            )

            # 添加不同优先级的记忆
            memories = [
                ('重要决策', '优化系统性能', MemoryPriority.CRITICAL),
                ('日常任务', '处理邮件', MemoryPriority.NORMAL),
                ('临时笔记', '购物清单', MemoryPriority.EPHEMERAL)
            ]

            for content, desc, priority in memories:
                await add_memory_with_forgetting(
                    memory_id=f"mem_{content}",
                    content=f"{desc} - {datetime.now()}",
                    memory_type='note',
                    priority=priority
                )

            # 获取记忆洞察
            from core.memory.smart_forgetting_strategy import get_memory_insights
            insights = await get_memory_insights()
            logger.info(f"  记忆洞察数: {len(insights)}")

        except Exception as e:
            logger.error(f"记忆演示失败: {e}")

    @staticmethod
    async def _sample_task(task_name: str):
        """示例任务"""
        await asyncio.sleep(0.1)
        return f"Task {task_name} completed"


async def main():
    """主函数"""
    # 创建平台实例
    platform = OptimizedAthenaPlatform()

    # 初始化系统
    await platform.initialize()

    # 询问是否运行演示
    logger.info(str("\n❓ 是否运行功能演示？(y/n)): ", end='')
    choice = input().strip().lower()

    if choice in ['y', 'yes', '是']:
        await platform.run_demo()

    # 保持运行
    logger.info("\n🔄 系统正在运行中...按 Ctrl+C 停止")
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("\n\n👋 正在关闭系统...")

        # 清理资源
        try:
            from core.execution.real_time_monitor import stop_real_time_monitoring
            await stop_real_time_monitoring()
            logger.info('✅ 实时监控已停止')
        except:
            pass

        try:
            from core.execution.fine_grained_concurrency import (
                fine_grained_concurrency_controller,
            )
            await fine_grained_concurrency_controller.stop()
            logger.info('✅ 并发控制器已停止')
        except:
            pass

        logger.info("\n🎯 Athena智能体平台已安全关闭")


if __name__ == '__main__':
    asyncio.run(main())