#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标准化模块测试
Standardized Modules Test

测试BaseModule标准化接口的核心模块

作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import asyncio
import logging
import os
import sys
import traceback
from datetime import datetime

logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.insert(0, '/Users/xujian/Athena工作平台')

async def test_base_module():
    """测试BaseModule基类"""
    logger.info("\n🏗️ 1. BaseModule基类测试")
    logger.info(str('-' * 60))

    try:
        from core.base_module import BaseModule, HealthStatus, ModuleStatus

        # 创建测试模块
        class TestModule(BaseModule):
            async def _on_initialize(self) -> bool:
                return True

            async def _on_start(self) -> bool:
                return True

            async def _on_stop(self) -> bool:
                return True

            async def _on_shutdown(self) -> bool:
                return True

            async def _on_health_check(self) -> bool:
                return True

        # 创建测试实例
        test_module = TestModule(agent_id='test_agent')
        logger.info('✅ BaseModule实例创建成功')

        # 测试初始化
        init_result = await test_module.initialize()
        logger.info(f"✅ 初始化结果: {init_result}")

        # 测试状态获取
        status = test_module.get_status()
        logger.info(f"✅ 模块状态: {status['status']}")

        # 测试启动
        start_result = await test_module.start()
        logger.info(f"✅ 启动结果: {start_result}")

        # 测试健康检查
        health = await test_module.health_check()
        logger.info(f"✅ 健康状态: {health.value}")

        # 测试停止
        stop_result = await test_module.stop()
        logger.info(f"✅ 停止结果: {stop_result}")

        # 测试关闭
        shutdown_result = await test_module.shutdown()
        logger.info(f"✅ 关闭结果: {shutdown_result}")

        return True

    except Exception as e:
        logger.info(f"❌ BaseModule测试失败: {e}")
        traceback.print_exc()
        return False

async def test_task_models():
    """测试Task模型"""
    logger.info("\n📋 2. Task模型测试")
    logger.info(str('-' * 60))

    try:
        from core.task_models import (
            Task,
            TaskPriority,
            TaskQueue,
            TaskResult,
            TaskStatus,
            TaskType,
        )

        # 创建任务
        task = Task(
            name='测试任务',
            task_type=TaskType.FUNCTION_CALL,
            action='print',
            action_data={'message': 'Hello World'},
            priority=TaskPriority.HIGH,
            agent_id='test_agent'
        )
        logger.info('✅ Task创建成功')

        # 测试任务状态
        logger.info(f"✅ 任务ID: {task.id}")
        logger.info(f"✅ 任务状态: {task.status.value}")
        logger.info(f"✅ 任务优先级: {task.priority.name}")

        # 测试任务执行
        task.start()
        logger.info(f"✅ 任务开始: {task.status.value}")

        task.complete(success=True, data='Task completed')
        logger.info(f"✅ 任务完成: {task.status.value}")

        # 测试TaskQueue
        queue = TaskQueue(max_size=100)
        logger.info('✅ TaskQueue创建成功')

        # 入队
        enqueue_result = queue.enqueue(task)
        logger.info(f"✅ 任务入队: {enqueue_result}")

        # 查看队首
        peek_task = queue.peek()
        logger.info(f"✅ 队首任务: {peek_task.name if peek_task else 'None'}")

        # 出队
        dequeued_task = queue.dequeue()
        logger.info(f"✅ 任务出队: {dequeued_task.name if dequeued_task else 'None'}")

        # 测试序列化
        task_dict = task.to_dict()
        logger.info(f"✅ 任务序列化成功，字段数: {len(task_dict)}")

        return True

    except Exception as e:
        logger.info(f"❌ Task模型测试失败: {e}")
        traceback.print_exc()
        return False

async def test_simple_integration():
    """测试简单集成"""
    logger.info("\n🔗 3. 简单集成测试")
    logger.info(str('-' * 60))

    try:
        from core.base_module import BaseModule
        from core.task_models import Task, TaskPriority, TaskType

        # 创建一个简单的集成测试
        class MockExecutionModule(BaseModule):
            def __init__(self, agent_id: str):
                super().__init__(agent_id)
                self.tasks = {}

            async def _on_initialize(self) -> bool:
                return True

            async def _on_start(self) -> bool:
                return True

            async def _on_stop(self) -> bool:
                return True

            async def _on_shutdown(self) -> bool:
                return True

            async def _on_health_check(self) -> bool:
                return True

            async def execute_task(self, task: Task) -> str:
                """模拟任务执行"""
                task.start()
                await asyncio.sleep(0.1)  # 模拟执行时间
                task.complete(success=True, data=f"Task {task.name} completed")
                self.tasks[task.id] = task
                return task.id

            def get_task(self, task_id: str) -> Task:
                return self.tasks.get(task_id)

        # 创建测试模块
        executor = MockExecutionModule(agent_id='test_integration')
        await executor.initialize()
        await executor.start()
        logger.info('✅ 模拟执行模块创建和启动成功')

        # 创建测试任务
        task = Task(
            name='集成测试任务',
            task_type=TaskType.FUNCTION_CALL,
            action='test',
            priority=TaskPriority.NORMAL,
            agent_id='test_integration'
        )
        logger.info('✅ 测试任务创建成功')

        # 执行任务
        task_id = await executor.execute_task(task)
        logger.info(f"✅ 任务执行成功: {task_id}")

        # 获取任务结果
        executed_task = executor.get_task(task_id)
        if executed_task and executed_task.result:
            logger.info(f"✅ 任务结果: {executed_task.result.data}")
            logger.info(f"✅ 任务成功: {executed_task.result.success}")

        # 清理
        await executor.stop()
        await executor.shutdown()
        logger.info('✅ 模块清理完成')

        return True

    except Exception as e:
        logger.info(f"❌ 简单集成测试失败: {e}")
        traceback.print_exc()
        return False

async def test_configuration_compatibility():
    """测试配置兼容性"""
    logger.info("\n⚙️ 4. 配置兼容性测试")
    logger.info(str('-' * 60))

    try:
        from core.base_module import BaseModule
        from core.task_models import TaskFactory

        # 测试不同配置的模块创建
        configs = [
            {'max_workers': 4, 'timeout': 30},
            {'learning_rate': 0.01, 'strategy': 'hybrid'},
            {'logging_level': 'DEBUG', 'metrics_enabled': True},
            {}  # 空配置
        ]

        for i, config in enumerate(configs):
            class ConfigurableModule(BaseModule):
                async def _on_initialize(self) -> bool:
                    return True

                async def _on_start(self) -> bool:
                    return True

                async def _on_stop(self) -> bool:
                    return True

                async def _on_shutdown(self) -> bool:
                    return True

                async def _on_health_check(self) -> bool:
                    return True

            module = ConfigurableModule(agent_id=f"config_test_{i}", config=config)
            await module.initialize()
            logger.info(f"✅ 配置 {i+1} 模块创建成功")

            # 验证配置
            if config:
                logger.info(f"   配置参数: {list(config.keys())}")

            await module.shutdown()

        # 测试TaskFactory
        from core.task_models import TaskType
        tasks = [
            TaskFactory.create_task(
                TaskType.FUNCTION_CALL,
                name='打印任务',
                func_name='print',
                args=['Hello from factory'],
                agent_id='test'
            ),
            TaskFactory.create_task(
                TaskType.API_CALL,
                name='API任务',
                url='https://api.example.com',
                method='GET',
                agent_id='test'
            )
        ]

        logger.info(f"✅ TaskFactory创建成功，任务数: {len(tasks)}")
        for task in tasks:
            logger.info(f"   任务: {task.name} ({task.task_type.value})")

        return True

    except Exception as e:
        logger.info(f"❌ 配置兼容性测试失败: {e}")
        traceback.print_exc()
        return False

def generate_summary_report(results):
    """生成总结报告"""
    logger.info(str("\n" + '=' * 80))
    logger.info('📊 标准化模块测试总结报告')
    logger.info(str('=' * 80))
    logger.info(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(str('=' * 80))

    total_tests = len(results)
    passed_tests = sum(1 for _, result in results if result)
    failed_tests = total_tests - passed_tests
    pass_rate = (passed_tests / total_tests) * 100

    logger.info(f"\n📈 测试统计:")
    logger.info(f"   总测试数: {total_tests}")
    logger.info(f"   ✅ 通过: {passed_tests}")
    logger.info(f"   ❌ 失败: {failed_tests}")
    logger.info(f"   📊 通过率: {pass_rate:.1f}%")

    logger.info(f"\n📝 测试详情:")
    for test_name, result in results:
        status = '✅ PASSED' if result else '❌ FAILED'
        logger.info(f"   {test_name:<25} {status}")

    # 分析
    logger.info(f"\n🔍 成功验证:")
    if results[0][1]:  # BaseModule
        logger.info('   • BaseModule基类接口标准化成功')
        logger.info('   • 模块生命周期管理正常')
        logger.info('   • 健康检查机制有效')
    if results[1][1]:  # Task模型
        logger.info('   • Task模型标准化成功')
        logger.info('   • 任务状态管理完善')
        logger.info('   • 任务队列机制正常')
    if results[2][1]:  # 集成测试
        logger.info('   • 模块间集成无问题')
        logger.info('   • 标准化接口兼容性好')
    if results[3][1]:  # 配置兼容性
        logger.info('   • 配置系统灵活可用')
        logger.info('   • 工厂模式实现成功')

    # 建议
    logger.info(f"\n💡 改进建议:")
    if pass_rate == 100:
        logger.info('   • 标准化工作效果显著，可以推广到其他模块')
        logger.info('   • 开始实现增强执行引擎和学习引擎')
        logger.info('   • 编写详细的使用文档和最佳实践')
    else:
        logger.info('   • 修复失败的测试用例')
        logger.info('   • 检查模块导入路径问题')
        logger.info('   • 完善错误处理机制')

    logger.info(f"\n🎯 第一阶段评估:")
    if pass_rate >= 75:
        logger.info('   🎉 第一阶段目标基本达成')
        logger.info('   ✅ 接口标准化成功')
        logger.info('   ✅ 基础架构稳定')
        logger.info('   🚀 可以进入第二阶段')
    elif pass_rate >= 50:
        logger.info('   ⚠️ 第一阶段部分达成')
        logger.info('   ✅ 核心功能可用')
        logger.info('   ❌ 需要修复部分问题')
        logger.info('   🔧 继续完善后进入第二阶段')
    else:
        logger.info('   ❌ 第一阶段目标未达成')
        logger.info('   🔧 需要重大调整')
        logger.info('   📋 重新评估设计方案')

    logger.info(str("\n" + '=' * 80))

async def main():
    """主函数"""
    logger.info('🚀 Athena工作平台标准化模块测试')
    logger.info('验证BaseModule和Task模型的标准化工作')

    # 运行测试
    tests = [
        ('BaseModule基类', test_base_module),
        ('Task模型', test_task_models),
        ('简单集成', test_simple_integration),
        ('配置兼容性', test_configuration_compatibility)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.info(f"❌ {test_name}测试异常: {e}")
            results.append((test_name, False))

        # 测试间隔
        await asyncio.sleep(0.5)

    # 生成报告
    generate_summary_report(results)

if __name__ == '__main__':
    asyncio.run(main())