#!/usr/bin/env python3
"""
统一日志系统使用示例
Unified Logging System Usage Examples
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.logging import LogLevel, get_logger


def example_basic_logging():
    """示例1: 基础日志记录"""
    print("\n=== 示例1: 基础日志记录 ===\n")

    logger = get_logger("test_service", level=LogLevel.INFO)

    # 不同级别的日志
    logger.debug("这是DEBUG级别的日志（默认不显示）")
    logger.info("这是INFO级别的日志")
    logger.warning("这是WARNING级别的日志")
    logger.error("这是ERROR级别的日志")
    logger.critical("这是CRITICAL级别的日志")


def example_context_logging():
    """示例2: 上下文日志记录"""
    print("\n=== 示例2: 上下文日志记录 ===\n")

    logger = get_logger("test_service")

    # 添加上下文信息
    logger.add_context("request_id", "req-12345")
    logger.add_context("user_id", "user-67890")
    logger.add_context("session_id", "sess-abc")

    # 日志会自动包含上下文
    logger.info("处理用户请求")

    # 清除上下文
    logger.clear_context()
    logger.info("上下文已清除")


def example_extra_fields():
    """示例3: 额外字段"""
    print("\n=== 示例3: 额外字段 ===\n")

    logger = get_logger("test_service")

    # 添加额外字段
    logger.info(
        "任务完成",
        extra={
            "task_id": "task-001",
            "duration_ms": 1234,
            "status": "success"
        }
    )


def example_exception_logging():
    """示例4: 异常日志记录"""
    print("\n=== 示例4: 异常日志记录 ===\n")

    logger = get_logger("test_service")

    try:
        # 模拟一个错误
        pass
    except Exception as e:
        # 记录异常
        logger.error("计算错误", exception=e)

    # 或者使用exception方法
    try:
        int("invalid")
    except ValueError:
        logger.exception("类型转换失败")


def example_service_logging():
    """示例5: 服务日志记录"""
    print("\n=== 示例5: 服务日志记录 ===\n")

    # 模拟小娜服务
    xiaona_logger = get_logger("xiaona", level=LogLevel.INFO)

    xiaona_logger.add_context("request_id", "req-xiaona-001")
    xiaona_logger.info("开始专利分析")
    xiaona_logger.info("加载专利数据", extra={"patent_id": "CN123456789A"})
    xiaona_logger.info("执行创造性分析", extra={"model": "claude-sonnet-4-6"})
    xiaona_logger.info("分析完成", extra={"duration_ms": 2345, "creativity_score": 0.85})

    # 模拟小诺服务
    xiaonuo_logger = get_logger("xiaonuo", level=LogLevel.INFO)

    xiaonuo_logger.add_context("task_id", "task-xiaonuo-001")
    xiaonuo_logger.info("任务开始")
    xiaonuo_logger.info("协调Agent执行任务")
    xiaonuo_logger.info("任务完成", extra={"status": "success", "duration_ms": 5678})


async def example_async_logging():
    """示例6: 异步日志记录"""
    print("\n=== 示例6: 异步日志记录 ===\n")

    logger = get_logger("async_service")

    async def process_task(task_id: str):
        """处理任务"""
        logger.add_context("task_id", task_id)
        logger.info(f"任务开始: {task_id}")

        await asyncio.sleep(0.1)
        logger.info("任务进行中...")

        await asyncio.sleep(0.1)
        logger.info("任务完成", extra={"duration_ms": 200})

    # 并发执行多个任务
    tasks = [
        process_task(f"task-{i}")
        for i in range(3)
    ]

    await asyncio.gather(*tasks)


def example_performance_logging():
    """示例7: 性能日志记录"""
    print("\n=== 示例7: 性能日志记录 ===\n")

    logger = get_logger("performance_service")

    import time

    # 测试日志性能
    iterations = 100
    start = time.time()

    for i in range(iterations):
        logger.info(f"性能测试日志 {i}")

    elapsed = time.time() - start

    logger.info(
        "性能测试完成",
        extra={
            "iterations": iterations,
            "total_time_ms": elapsed * 1000,
            "avg_time_ms": (elapsed * 1000) / iterations
        }
    )


def main():
    """主函数"""
    print("=" * 60)
    print("统一日志系统使用示例")
    print("=" * 60)

    # 运行所有示例
    example_basic_logging()
    example_context_logging()
    example_extra_fields()
    example_exception_logging()
    example_service_logging()
    asyncio.run(example_async_logging())
    example_performance_logging()

    print("\n" + "=" * 60)
    print("所有示例运行完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
