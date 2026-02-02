#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强模块验证测试
Enhanced Modules Verification Test

测试标准化后的核心模块功能

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
sys.path.insert(0, '/Users/xujian/Athena工作平台/core')

async def test_base_module():
    """测试BaseModule基类"""
    logger.info("\n🏗️ 1. BaseModule基类测试")
    logger.info(str('-' * 60))

    try:
        from base_module import BaseModule, HealthStatus, ModuleStatus

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
        from task_models import (
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

async def test_enhanced_execution_engine():
    """测试增强执行引擎"""
    logger.info("\n🚀 3. 增强执行引擎测试")
    logger.info(str('-' * 60))

    try:
        from execution.enhanced_execution_engine import EnhancedExecutionEngine
        from task_models import Task, TaskType

        # 创建执行引擎
        executor = EnhancedExecutionEngine(
            agent_id='test_agent',
            config={
                'max_workers': 2,
                'max_concurrent': 3,
                'task_timeout': 30.0
            }
        )
        logger.info('✅ EnhancedExecutionEngine创建成功')

        # 初始化
        init_result = await executor.initialize()
        logger.info(f"✅ 初始化结果: {init_result}")

        # 启动
        start_result = await executor.start()
        logger.info(f"✅ 启动结果: {start_result}")

        # 创建测试任务
        test_task = Task(
            name='打印任务',
            task_type=TaskType.FUNCTION_CALL,
            action='print',
            action_data={'args': ['Hello from Enhanced Execution Engine!']},
            agent_id='test_agent'
        )
        logger.info('✅ 测试任务创建成功')

        # 执行任务
        task_id = await executor.execute_task(test_task)
        logger.info(f"✅ 任务提交成功: {task_id}")

        # 等待任务完成
        await asyncio.sleep(2)

        # 获取任务状态
        executed_task = executor.get_task(task_id)
        if executed_task:
            logger.info(f"✅ 任务状态: {executed_task.status.value}")
            logger.info(f"✅ 任务结果: {executed_task.result.data if executed_task.result else 'None'}")

        # 创建工作流
        workflow_id = await executor.create_workflow(
            name='测试工作流',
            tasks_data=[
                {
                    'name': '步骤1',
                    'type': 'function_call',
                    'action': 'print',
                    'data': {'args': ['工作流步骤1']},
                    'priority': 2
                },
                {
                    'name': '步骤2',
                    'type': 'function_call',
                    'action': 'print',
                    'data': {'args': ['工作流步骤2']},
                    'priority': 2
                }
            ]
        )
        logger.info(f"✅ 工作流创建成功: {workflow_id}")

        # 等待工作流完成
        await asyncio.sleep(3)

        # 获取统计信息
        stats = executor.get_statistics()
        logger.info(f"✅ 执行统计: {stats['stats']}")

        # 健康检查
        health = await executor.health_check()
        logger.info(f"✅ 健康检查: {health.value}")

        # 停止
        stop_result = await executor.stop()
        logger.info(f"✅ 停止结果: {stop_result}")

        return True

    except Exception as e:
        logger.info(f"❌ 增强执行引擎测试失败: {e}")
        traceback.print_exc()
        return False

async def test_enhanced_learning_engine():
    """测试增强学习引擎"""
    logger.info("\n🧠 4. 增强学习引擎测试")
    logger.info(str('-' * 60))

    try:
        from learning.enhanced_learning_engine import EnhancedLearningEngine

        # 创建学习引擎
        learner = EnhancedLearningEngine(
            agent_id='test_agent',
            config={
                'learning_strategy': 'hybrid',
                'adaptation_mode': 'reactive',
                'max_experiences': 1000,
                'learning_rate': 0.01
            }
        )
        logger.info('✅ EnhancedLearningEngine创建成功')

        # 初始化
        init_result = await learner.initialize()
        logger.info(f"✅ 初始化结果: {init_result}")

        # 启动
        start_result = await learner.start()
        logger.info(f"✅ 启动结果: {start_result}")

        # 创建测试经验
        test_experience = {
            'task': 'test_task',
            'action': 'print_message',
            'result': 'success',
            'reward': 0.8,
            'context': {
                'task_type': 'communication',
                'difficulty': 'easy',
                'environment': 'test'
            }
        }

        # 处理经验
        learning_result = await learner.process_experience(test_experience)
        logger.info(f"✅ 经验处理成功: {learning_result.success}")
        logger.info(f"✅ 学习策略: {learning_result.strategy_used.value}")
        logger.info(f"✅ 性能分数: {learning_result.performance_score:.2f}")
        logger.info(f"✅ 适应应用: {learning_result.adaptation_applied}")
        if learning_result.insights:
            logger.info(f"✅ 学习洞察: {learning_result.insights[0]}")

        # 获取任务策略
        strategy = await learner.get_strategy('test_task')
        logger.info(f"✅ 策略获取: {strategy['strategy']}")
        logger.info(f"✅ 置信度: {strategy['confidence']:.2f}")

        # 处理更多经验
        for i in range(5):
            experience = {
                'task': 'test_task',
                'action': f"action_{i}",
                'result': 'success',
                'reward': 0.5 + i * 0.1,
                'context': {'task_type': 'communication'}
            }
            await learner.process_experience(experience)

        # 获取统计信息
        stats = await learner.get_statistics()
        logger.info(f"✅ 学习统计:")
        logger.info(f"   总经验数: {stats['metrics']['total_experiences']}")
        logger.info(f"   成功率: {stats['metrics']['success_rate']:.2f}")
        logger.info(f"   平均奖励: {stats['metrics']['average_reward']:.2f}")

        # 测试策略适应
        adapt_result = await learner.adapt_strategy(0.6, 0.9)
        logger.info(f"✅ 策略适应: {adapt_result}")

        # 健康检查
        health = await learner.health_check()
        logger.info(f"✅ 健康检查: {health.value}")

        # 停止
        stop_result = await learner.stop()
        logger.info(f"✅ 停止结果: {stop_result}")

        return True

    except Exception as e:
        logger.info(f"❌ 增强学习引擎测试失败: {e}")
        traceback.print_exc()
        return False

async def test_module_integration():
    """测试模块集成"""
    logger.info("\n🔗 5. 模块集成测试")
    logger.info(str('-' * 60))

    try:
        from execution.enhanced_execution_engine import EnhancedExecutionEngine
        from learning.enhanced_learning_engine import EnhancedLearningEngine
        from task_models import Task, TaskType

        # 创建执行引擎和学习引擎
        executor = EnhancedExecutionEngine(agent_id='integration_test')
        learner = EnhancedLearningEngine(agent_id='integration_test')

        # 初始化两个模块
        await executor.initialize()
        await learner.initialize()

        await executor.start()
        await learner.start()

        logger.info('✅ 两个模块初始化和启动成功')

        # 创建并执行任务
        task = Task(
            name='集成测试任务',
            task_type=TaskType.FUNCTION_CALL,
            action='print',
            action_data={'args': ['Integration test task']},
            agent_id='integration_test'
        )

        task_id = await executor.execute_task(task)
        await asyncio.sleep(2)

        # 获取执行结果并转换为学习经验
        executed_task = executor.get_task(task_id)
        if executed_task and executed_task.result:
            experience = {
                'task': executed_task.name,
                'action': executed_task.action,
                'result': executed_task.result.data,
                'reward': 0.9 if executed_task.result.success else 0.1,
                'context': {'integration_test': True}
            }

            # 学习引擎处理经验
            learning_result = await learner.process_experience(experience)
            logger.info(f"✅ 集成学习成功: {learning_result.success}")

        # 获取综合统计
        exec_stats = executor.get_statistics()
        learn_stats = await learner.get_statistics()

        logger.info(f"✅ 执行引擎统计: {exec_stats['stats']['total_tasks']} 个任务")
        logger.info(f"✅ 学习引擎统计: {learn_stats['metrics']['total_experiences']} 个经验")

        # 清理
        await executor.stop()
        await learner.stop()

        return True

    except Exception as e:
        logger.info(f"❌ 模块集成测试失败: {e}")
        traceback.print_exc()
        return False

def generate_test_summary(results):
    """生成测试总结"""
    logger.info(str("\n" + '=' * 80))
    logger.info('📊 增强模块测试总结')
    logger.info(str('=' * 80))
    logger.info(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(str('=' * 80))

    total_tests = len(results)
    passed_tests = sum(1 for _, result in results if result)
    failed_tests = total_tests - passed_tests
    pass_rate = (passed_tests / total_tests) * 100

    logger.info(f"\n📈 测试结果统计:")
    logger.info(f"   总测试数: {total_tests}")
    logger.info(f"   ✅ 通过: {passed_tests}")
    logger.info(f"   ❌ 失败: {failed_tests}")
    logger.info(f"   📊 通过率: {pass_rate:.1f}%")

    logger.info(f"\n📝 详细结果:")
    for test_name, result in results:
        status = '✅ PASSED' if result else '❌ FAILED'
        logger.info(f"   {test_name:<25} {status}")

    # 评估
    if pass_rate >= 80:
        assessment = '🎉 优秀！模块标准化效果显著'
    elif pass_rate >= 60:
        assessment = '👍 良好！主要功能正常，部分细节需要完善'
    elif pass_rate >= 40:
        assessment = '⚠️ 一般！基础架构可用，需要大量改进'
    else:
        assessment = '❌ 较差！需要重新设计'

    logger.info(f"\n🎯 总体评估:")
    logger.info(f"   {assessment}")

    # 建议
    logger.info(f"\n💡 改进建议:")
    if pass_rate < 100:
        logger.info('   • 修复失败的测试用例')
        logger.info('   • 增强错误处理机制')
        logger.info('   • 完善日志记录')

    if pass_rate >= 80:
        logger.info('   • 开始应用到其他模块')
        logger.info('   • 编写详细的使用文档')
        logger.info('   • 考虑性能优化')

    logger.info(f"\n🔄 下一步工作:")
    logger.info('   • 继续修复通信模块接口')
    logger.info('   • 完善评估引擎标准方法')
    logger.info('   • 解决工具库模块导入问题')
    logger.info('   • 建立全局配置管理系统')

    logger.info(str("\n" + '=' * 80))

async def main():
    """主函数"""
    logger.info('🚀 增强模块验证测试')
    logger.info('测试BaseModule标准化和增强模块')

    # 运行测试
    tests = [
        ('BaseModule基类', test_base_module),
        ('Task模型', test_task_models),
        ('增强执行引擎', test_enhanced_execution_engine),
        ('增强学习引擎', test_enhanced_learning_engine),
        ('模块集成', test_module_integration)
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
        await asyncio.sleep(1)

    # 生成总结
    generate_test_summary(results)

if __name__ == '__main__':
    asyncio.run(main())