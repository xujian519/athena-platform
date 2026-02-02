#!/usr/bin/env python3
"""
增强执行引擎测试脚本
Test Enhanced Execution Engine

验证BaseModule兼容性和任务执行功能
作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.execution.enhanced_execution_engine import EnhancedExecutionEngine
from core.task_models import Task, TaskPriority, TaskType

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def sample_function(x: int, y: int) -> int:
    """示例函数"""
    return x + y


async def async_sample_function(message: str, delay: float = 0.1) -> str:
    """示例异步函数"""
    await asyncio.sleep(delay)
    return f"处理完成: {message}"


def failing_function() -> Any:
    """总是失败的函数"""
    raise ValueError("这是一个测试错误")


async def test_enhanced_execution_engine():
    """测试增强执行引擎"""
    logger.info("\n🔧 增强执行引擎测试")
    logger.info(str("=" * 60))

    try:
        # 1. 创建引擎实例
        logger.info("\n1. 创建增强执行引擎...")
        execution_engine = EnhancedExecutionEngine(
            agent_id="test_execution_agent_001",
            config={"max_workers": 4, "max_concurrent": 3, "task_timeout": 10.0},
        )
        logger.info("✅ 执行引擎创建成功")

        # 2. 初始化引擎
        logger.info("\n2. 初始化执行引擎...")
        init_success = await execution_engine.initialize()
        if init_success:
            logger.info("✅ 执行引擎初始化成功")
        else:
            logger.info("❌ 执行引擎初始化失败")
            return False

        # 3. 健康检查
        logger.info("\n3. 执行健康检查...")
        health_status = await execution_engine.health_check()
        logger.info("✅ 健康检查结果:")
        logger.info(f"   - 健康状态: {'健康' if health_status.value == 'healthy' else '不健康'}")
        logger.info(f"   - 状态值: {health_status.value}")

        # 获取健康检查详情
        if hasattr(execution_engine, "_health_check_details"):
            details = execution_engine._health_check_details
            logger.info(f"   - 执行器状态: {details.get('executor_status', 'unknown')}")
            logger.info(f"   - 任务队列状态: {details.get('queue_status', 'unknown')}")
            logger.info(f"   - 线程池状态: {details.get('thread_pool_status', 'unknown')}")

            stats = details.get("stats", {})
            if stats:
                logger.info(
                    f"   - 任务统计: 总计{stats.get('total_tasks', 0)}, 完成{stats.get('completed_tasks', 0)}"
                )

        # 4. 测试任务执行
        logger.info("\n4. 测试任务执行...")

        # 创建测试任务
        test_tasks = [
            Task(
                name="加法任务",
                task_type=TaskType.FUNCTION_CALL,
                action="sample_function",
                parameters={"x": 5, "y": 3},
                priority=TaskPriority.NORMAL,
            ),
            Task(
                name="异步任务",
                task_type=TaskType.FUNCTION_CALL,
                action="async_sample_function",
                parameters={"message": "Hello World", "delay": 0.1},
                priority=TaskPriority.HIGH,
            ),
            Task(
                name="失败任务",
                task_type=TaskType.FUNCTION_CALL,
                action="failing_function",
                parameters={},
                priority=TaskPriority.LOW,
            ),
        ]

        executed_tasks = []
        for task in test_tasks:
            # 注册执行器
            if task.action == "sample_function":
                execution_engine.register_executor("sample_function", sample_function)
            elif task.action == "async_sample_function":
                execution_engine.register_executor("async_sample_function", async_sample_function)
            elif task.action == "failing_function":
                execution_engine.register_executor("failing_function", failing_function)

            # 执行任务
            result = await execution_engine.execute_task(task)
            executed_tasks.append((task, result))
            status = "成功" if result.success else "失败"
            logger.info(f"   {task.name}: {status}")
            if result.success:
                logger.info(f"     结果: {result.data}")
            else:
                logger.info(f"     错误: {result.error}")

        # 5. 测试任务队列
        logger.info("\n5. 测试任务队列...")

        # 创建批量任务
        batch_tasks = []
        for i in range(5):
            task = Task(
                name=f"批量任务_{i+1}",
                task_type=TaskType.FUNCTION_CALL,
                action="sample_function",
                parameters={"x": i, "y": i + 1},
                priority=TaskPriority.NORMAL if i % 2 == 0 else TaskPriority.HIGH,
            )
            batch_tasks.append(task)

        # 批量提交任务
        submitted_count = 0
        for task in batch_tasks:
            if execution_engine.submit_task(task):
                submitted_count += 1

        logger.info(f"   提交任务: {submitted_count}/{len(batch_tasks)}")

        # 等待任务完成
        await asyncio.sleep(1.0)

        # 6. 测试工作流
        logger.info("\n6. 测试工作流...")

        workflow_tasks = [
            Task(
                name="步骤1: 数据准备",
                task_type=TaskType.FUNCTION_CALL,
                action="sample_function",
                parameters={"x": 10, "y": 5},
            ),
            Task(
                name="步骤2: 数据处理",
                task_type=TaskType.FUNCTION_CALL,
                action="sample_function",
                parameters={"x": 15, "y": 3},
                dependencies=[TaskDependency("step1")],
            ),
        ]

        # 设置依赖关系
        workflow_tasks[1].dependencies[0].task_id = workflow_tasks[0].id

        workflow_result = await execution_engine.execute_workflow(workflow_tasks)
        logger.info(f"   工作流执行: {'成功' if workflow_result else '失败'}")

        # 7. 获取任务统计
        logger.info("\n7. 获取任务统计...")
        task_stats = execution_engine.get_task_stats()
        logger.info("✅ 统计获取完成")
        logger.info(f"   - 总任务数: {task_stats.get('total_tasks', 0)}")
        logger.info(f"   - 已完成任务: {task_stats.get('completed_tasks', 0)}")
        logger.info(f"   - 失败任务: {task_stats.get('failed_tasks', 0)}")
        logger.info(f"   - 队列大小: {task_stats.get('queue_size', 0)}")
        logger.info(f"   - 平均执行时间: {task_stats.get('average_execution_time', 0):.3f}s")

        # 8. 获取模块状态
        logger.info("\n8. 获取模块状态...")
        status = execution_engine.get_status()
        logger.info("✅ 状态获取完成")
        logger.info(f"   - 智能体ID: {status.get('agent_id', 'unknown')}")
        logger.info(f"   - 模块类型: {status.get('module_type', 'unknown')}")
        logger.info(f"   - 运行状态: {status.get('status', 'unknown')}")

        # 9. 获取性能指标
        logger.info("\n9. 获取性能指标...")
        metrics = execution_engine.get_metrics()
        logger.info("✅ 指标获取完成")
        logger.info(f"   - 模块状态: {metrics.get('module_status', 'unknown')}")
        logger.info(f"   - 代理ID: {metrics.get('agent_id', 'unknown')}")
        logger.info(f"   - 初始化状态: {metrics.get('initialized', False)}")
        logger.info(f"   - 运行时长: {metrics.get('uptime_seconds', 0):.2f}s")

        execution_stats = metrics.get("execution_stats", {})
        if execution_stats:
            logger.info("   - 执行统计:")
            logger.info(f"     * 总任务数: {execution_stats.get('total_tasks', 0)}")
            logger.info(f"     * 成功任务: {execution_stats.get('successful_tasks', 0)}")
            logger.info(f"     * 失败任务: {execution_stats.get('failed_tasks', 0)}")
            logger.info(f"     * 最大工作者: {execution_stats.get('max_workers', 0)}")

        # 10. 测试关闭
        logger.info("\n10. 测试引擎关闭...")
        await execution_engine.shutdown()
        logger.info("✅ 引擎关闭成功")

        logger.info(str("\n" + "=" * 60))
        logger.info("🎉 增强执行引擎测试完成 - 所有测试通过!")
        return True

    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e!s}")
        import traceback

        traceback.print_exc()
        return False


async def test_task_types():
    """测试不同类型的任务"""
    logger.info("\n🔄 任务类型测试")
    logger.info(str("=" * 60))

    try:
        execution_engine = EnhancedExecutionEngine(
            agent_id="task_type_test_agent", config={"max_workers": 2, "max_concurrent": 2}
        )

        await execution_engine.initialize()

        # 注册不同类型的执行器
        execution_engine.register_executor("math_add", lambda a, b: a + b)
        execution_engine.register_executor("string_process", lambda s: s.upper())
        execution_engine.register_executor("async_delay", async_sample_function)

        # 测试不同类型的任务
        task_types = [
            {
                "name": "数学计算",
                "type": TaskType.FUNCTION_CALL,
                "action": "math_add",
                "params": {"a": 10, "b": 20},
            },
            {
                "name": "字符串处理",
                "type": TaskType.FUNCTION_CALL,
                "action": "string_process",
                "params": {"s": "hello"},
            },
            {
                "name": "异步处理",
                "type": TaskType.FUNCTION_CALL,
                "action": "async_delay",
                "params": {"message": "延迟测试", "delay": 0.1},
            },
        ]

        for i, test_case in enumerate(task_types, 1):
            logger.info(f"\n{i}. 测试{test_case['name']}...")

            task = Task(
                name=test_case["name"],
                task_type=test_case["type"],
                action=test_case["action"],
                parameters=test_case["params"],
            )

            result = await execution_engine.execute_task(task)
            logger.info(f"   执行结果: {'✅ 成功' if result.success else '❌ 失败'}")
            if result.success:
                logger.info(f"   输出: {result.data}")
            else:
                logger.info(f"   错误: {result.error}")

        await execution_engine.shutdown()
        return True

    except Exception as e:
        logger.error(f"❌ 任务类型测试失败: {e!s}")
        return False


async def main():
    """主测试函数"""
    logger.info("🚀 增强执行引擎完整测试套件")
    logger.info(str("=" * 80))

    # 基础功能测试
    basic_test_passed = await test_enhanced_execution_engine()

    # 任务类型测试
    task_type_test_passed = await test_task_types()

    # 测试总结
    logger.info(str("\n" + "=" * 80))
    logger.info("📊 测试总结")
    logger.info(str("=" * 80))
    logger.info(f"基础功能测试: {'✅ 通过' if basic_test_passed else '❌ 失败'}")
    logger.info(f"任务类型测试: {'✅ 通过' if task_type_test_passed else '❌ 失败'}")

    overall_success = basic_test_passed and task_type_test_passed
    logger.info(f"\n🎯 总体结果: {'✅ 全部测试通过' if overall_success else '❌ 存在失败测试'}")

    return overall_success


if __name__ == "__main__":
    asyncio.run(main())
