#!/usr/bin/env python3
"""
统一监控系统使用示例
Unified Monitoring System Usage Examples
"""
import sys
import asyncio
import time
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.monitoring.unified_metrics import (
    get_metrics_collector,
    monitor_performance
)


def example_basic_metrics():
    """示例1: 基础指标记录"""
    print("\n=== 示例1: 基础指标记录 ===\n")

    collector = get_metrics_collector("test_service")

    # 记录HTTP请求
    collector.record_http_request(
        method="GET",
        endpoint="/api/patents",
        status=200,
        duration=0.123
    )

    # 记录服务任务
    collector.record_service_task(
        task_type="patent_analysis",
        status="success",
        duration=1.234
    )

    # 记录错误
    collector.record_error(error_type="TimeoutError")

    # 记录LLM请求
    collector.record_llm_request(
        provider="anthropic",
        model="claude-sonnet-4-6",
        duration=2.345
    )

    # 记录缓存
    collector.record_cache_hit(cache_type="vector")
    collector.record_cache_miss(cache_type="llm")

    print("✓ 所有指标已记录")


def example_decorator_monitoring():
    """示例2: 装饰器监控"""
    print("\n=== 示例2: 装饰器监控 ===\n")

    collector = get_metrics_collector("test_service")

    @monitor_performance(collector, "calculation")
    def calculate_metric(data: list) -> float:
        """计算指标（带监控）"""
        time.sleep(0.1)  # 模拟处理
        return sum(data) / len(data)

    # 调用函数
    result = calculate_metric([1, 2, 3, 4, 5])
    print(f"✓ 计算结果: {result}")

    # 异步函数监控
    @monitor_performance(collector, "async_task")
    async def async_task():
        """异步任务（带监控）"""
        await asyncio.sleep(0.1)
        return "任务完成"

    result = asyncio.run(async_task())
    print(f"✓ {result}")


def example_service_metrics():
    """示例3: 服务指标记录"""
    print("\n=== 示例3: 服务指标记录 ===\n")

    # 小娜服务指标
    xiaona_collector = get_metrics_collector("xiaona")

    xiaona_collector.record_service_task(
        task_type="patent_analysis",
        status="success",
        duration=5.678
    )

    xiaona_collector.record_llm_request(
        provider="anthropic",
        model="claude-sonnet-4-6",
        duration=2.345
    )

    print("✓ 小娜服务指标已记录")

    # 小诺服务指标
    xiaonuo_collector = get_metrics_collector("xiaonuo")

    xiaonuo_collector.record_service_task(
        task_type="task_coordination",
        status="success",
        duration=0.567
    )

    print("✓ 小诺服务指标已记录")


def example_error_tracking():
    """示例4: 错误跟踪"""
    print("\n=== 示例4: 错误跟踪 ===\n")

    collector = get_metrics_collector("test_service")

    try:
        # 模拟一个错误
        raise ValueError("测试错误")
    except ValueError as e:
        collector.record_error("ValueError")
        print(f"✓ 错误已记录: {type(e).__name__}")

    try:
        # 模拟另一个错误
        raise TimeoutError("超时错误")
    except TimeoutError as e:
        collector.record_error("TimeoutError")
        print(f"✓ 错误已记录: {type(e).__name__}")


async def example_llm_monitoring():
    """示例5: LLM调用监控"""
    print("\n=== 示例5: LLM调用监控 ===\n")

    collector = get_metrics_collector("test_service")

    async def mock_llm_call(provider: str, model: str):
        """模拟LLM调用"""
        start_time = time.time()
        await asyncio.sleep(0.2)  # 模拟网络延迟
        duration = time.time() - start_time

        collector.record_llm_request(provider, model, duration)
        print(f"✓ LLM调用已记录: {provider}/{model}")

    # 调用不同的LLM
    await mock_llm_call("anthropic", "claude-sonnet-4-6")
    await mock_llm_call("openai", "gpt-4")
    await mock_llm_call("deepseek", "deepseek-chat")


def example_cache_monitoring():
    """示例6: 缓存监控"""
    print("\n=== 示例6: 缓存监控 ===\n")

    collector = get_metrics_collector("test_service")

    # 模拟缓存操作
    cache_data = {"key1": "value1", "key2": "value2"}

    # 缓存命中
    for key in ["key1", "key2"]:
        if key in cache_data:
            collector.record_cache_hit("memory")
            print(f"✓ 缓存命中: {key}")

    # 缓存未命中
    for key in ["key3", "key4"]:
        if key not in cache_data:
            collector.record_cache_miss("memory")
            print(f"✓ 缓存未命中: {key}")


async def example_concurrent_monitoring():
    """示例7: 并发监控"""
    print("\n=== 示例7: 并发监控 ===\n")

    collector = get_metrics_collector("test_service")

    @monitor_performance(collector, "concurrent_task")
    async def concurrent_task(task_id: int):
        """并发任务"""
        await asyncio.sleep(0.1)
        return f"任务{task_id}完成"

    # 并发执行多个任务
    tasks = [concurrent_task(i) for i in range(5)]
    results = await asyncio.gather(*tasks)

    for result in results:
        print(f"✓ {result}")


def example_prometheus_export():
    """示例8: Prometheus指标导出"""
    print("\n=== 示例8: Prometheus指标导出 ===\n")

    collector = get_metrics_collector("test_service")

    # 记录一些指标
    collector.record_http_request("GET", "/api/test", 200, 0.1)
    collector.record_http_request("POST", "/api/test", 201, 0.2)

    # 导出Prometheus格式
    metrics = collector.get_metrics()
    print("✓ Prometheus格式指标:")
    print("-" * 60)
    print(metrics.decode()[:500] + "...")
    print("-" * 60)


def main():
    """主函数"""
    print("=" * 60)
    print("统一监控系统使用示例")
    print("=" * 60)

    # 运行所有示例
    example_basic_metrics()
    example_decorator_monitoring()
    example_service_metrics()
    example_error_tracking()
    asyncio.run(example_llm_monitoring())
    example_cache_monitoring()
    asyncio.run(example_concurrent_monitoring())
    example_prometheus_export()

    print("\n" + "=" * 60)
    print("所有示例运行完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
