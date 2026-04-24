#!/usr/bin/env python3
"""
Athena上下文管理监控集成示例
Monitoring Integration Example for Athena Context Management

演示如何使用Prometheus监控上下文管理系统。

作者: Athena平台团队
创建时间: 2026-04-24
"""

import asyncio
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def example_basic_monitoring():
    """示例1: 基础监控使用"""
    from core.context_management.monitoring import (
        get_metrics,
        start_metrics_server,
    )

    logger.info("=== 示例1: 基础监控使用 ===")

    # 启动metrics服务器
    start_metrics_server(port=8000)
    logger.info("✅ Metrics服务器已启动: http://localhost:8000/metrics")

    # 获取metrics实例
    metrics = get_metrics()

    # 记录操作
    metrics.record_operation("create", "task", "success")
    metrics.record_operation("read", "task", "success")
    metrics.record_operation("update", "task", "success")

    # 记录错误
    metrics.record_error("timeout", "read")

    # 更新活跃上下文数量
    metrics.update_active_contexts(42, "task")

    # 更新对象池大小
    metrics.update_pool_size(100, "current")
    metrics.update_pool_size(1000, "max")

    # 更新缓存命中率
    metrics.update_cache_hit_rate(0.85, "memory")

    logger.info("✅ 监控指标已记录")


async def example_tracked_operation():
    """示例2: 使用上下文管理器跟踪操作"""
    from core.context_management.monitoring import track_operation_latency

    logger.info("=== 示例2: 跟踪操作延迟 ===")

    # 模拟一些操作
    async def create_task():
        await asyncio.sleep(0.01)  # 模拟工作
        return {"task_id": "task-123"}

    async def read_task():
        await asyncio.sleep(0.005)  # 模拟工作
        return {"task_id": "task-123", "status": "active"}

    # 使用监控跟踪
    async with track_operation_latency("create", "task"):
        result = await create_task()
        logger.info(f"✅ 创建任务: {result}")

    async with track_operation_latency("read", "task"):
        result = await read_task()
        logger.info(f"✅ 读取任务: {result}")


async def example_decorator_monitoring():
    """示例3: 使用装饰器监控函数"""
    from core.context_management.monitoring import monitor_context_operation

    logger.info("=== 示例3: 装饰器监控 ===")

    @monitor_context_operation("create", "task")
    async def create_task_context(task_id: str, description: str):
        await asyncio.sleep(0.01)
        return {"task_id": task_id, "description": description}

    @monitor_context_operation("process", "task")
    async def process_task(task_id: str):
        await asyncio.sleep(0.02)
        return {"task_id": task_id, "status": "processed"}

    # 调用被监控的函数
    result1 = await create_task_context("task-456", "示例任务")
    logger.info(f"✅ {result1}")

    result2 = await process_task("task-456")
    logger.info(f"✅ {result2}")


async def example_manager_monitoring():
    """示例4: 监控上下文管理器"""
    from core.context_management.monitoring import monitor_context_manager
    from core.context_management.task_context_manager import TaskContextManager

    logger.info("=== 示例4: 管理器监控 ===")

    # 创建原始管理器
    manager = TaskContextManager(
        storage_path=Path("data/example_contexts"),
        enable_metrics=True
    )

    # 包装为监控管理器
    monitored_manager = monitor_context_manager(manager, "task")

    # 所有操作自动被监控
    context = await monitored_manager.create_context(
        task_id="example-001",
        task_description="监控示例任务",
        total_steps=3
    )
    logger.info(f"✅ 创建上下文: {context.task_id}")

    # 读取上下文
    loaded = await monitored_manager.load_context("example-001")
    if loaded:
        logger.info(f"✅ 加载上下文: {loaded.task_id}")

    # 列出上下文
    contexts = await monitored_manager.list_contexts()
    logger.info(f"✅ 上下文列表: {len(contexts)}个")

    # 删除上下文
    await monitored_manager.delete_context("example-001")
    logger.info("✅ 删除上下文")


async def example_pool_monitoring():
    """示例5: 监控对象池"""
    from core.context_management.context_object_pool import get_context_pool

    logger.info("=== 示例5: 对象池监控 ===")

    # 获取对象池（自动启用监控）
    pool = get_context_pool(max_size=100, initial_size=5)

    # 获取对象（自动监控acquire延迟）
    context1 = await pool.acquire("task-001")
    logger.info(f"✅ 获取对象: {context1.task_id}")

    context2 = await pool.acquire("task-002")
    logger.info(f"✅ 获取对象: {context2.task_id}")

    # 释放对象（自动监控release延迟）
    await pool.release(context1)
    logger.info("✅ 释放对象: task-001")

    await pool.release(context2)
    logger.info("✅ 释放对象: task-002")

    # 获取统计信息
    stats = pool.get_stats()
    logger.info(f"📊 池统计: 复用率={stats.reuse_rate:.2%}, 创建率={stats.creation_rate:.2%}")


async def example_cache_monitoring():
    """示例6: 缓存监控"""
    from core.context_management.monitoring import (
        record_cache_hit,
        record_cache_miss,
    )

    logger.info("=== 示例6: 缓存监控 ===")

    # 模拟缓存操作
    cache = {}

    def get_from_cache(key: str):
        if key in cache:
            record_cache_hit("memory")
            return cache[key]
        else:
            record_cache_miss("memory")
            value = f"value_for_{key}"
            cache[key] = value
            return value

    # 执行一些缓存操作
    for i in range(10):
        key = f"key_{i % 3}"  # 3个不同的key
        value = get_from_cache(key)
        logger.info(f"缓存获取: {key} = {value}")

    logger.info("✅ 缓存监控指标已记录")


async def main():
    """运行所有示例"""
    logger.info("🚀 Athena上下文管理监控示例开始")
    logger.info("=" * 50)

    # 示例1: 基础监控
    await example_basic_monitoring()
    await asyncio.sleep(0.5)

    # 示例2: 跟踪操作
    await example_tracked_operation()
    await asyncio.sleep(0.5)

    # 示例3: 装饰器
    await example_decorator_monitoring()
    await asyncio.sleep(0.5)

    # 示例4: 管理器监控
    await example_manager_monitoring()
    await asyncio.sleep(0.5)

    # 示例5: 对象池监控
    await example_pool_monitoring()
    await asyncio.sleep(0.5)

    # 示例6: 缓存监控
    await example_cache_monitoring()

    logger.info("=" * 50)
    logger.info("✅ 所有示例执行完成")
    logger.info("")
    logger.info("📊 查看metrics: http://localhost:8000/metrics")
    logger.info("📈 Prometheus: http://localhost:9090")
    logger.info("📊 Grafana: http://localhost:3000")


if __name__ == "__main__":
    asyncio.run(main())
