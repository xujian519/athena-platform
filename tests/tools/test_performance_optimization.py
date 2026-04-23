#!/usr/bin/env python3
"""
工具系统性能优化测试

测试缓存、并行执行等性能优化功能，生成对比报告。
"""

import asyncio
import time

import pytest

from core.tools.base import (
    ToolCapability,
    ToolCategory,
    ToolDefinition,
    ToolRegistry,
)


class PerformanceTestUtils:
    """性能测试工具"""

    @staticmethod
    def measure_execution_time(func, *args, **kwargs):
        """测量执行时间"""
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        return end - start, result

    @staticmethod
    async def measure_async_execution_time(func, *args, **kwargs):
        """测量异步执行时间"""
        start = time.time()
        result = await func(*args, **kwargs)
        end = time.time()
        return end - start, result


class TestCachingPerformance:
    """缓存性能测试 (P2-1)"""

    def test_find_by_category_cache_hit_rate(self):
        """测试分类查找缓存命中率"""
        registry = ToolRegistry()

        # 注册100个工具
        for i in range(100):
            tool = ToolDefinition(
                tool_id=f"tool_{i}",
                name=f"Tool {i}",
                description=f"Test tool {i}",
                category=ToolCategory.PATENT_SEARCH if i % 2 == 0 else ToolCategory.ACADEMIC_SEARCH,
                capability=ToolCapability(
                    input_types=["text"],
                    output_types=["json"],
                    domains=["test"],
                    task_types=["search"],
                ),
            )
            registry.register(tool)

        # 第一次查询（缓存未命中）
        start = time.time()
        tools1 = registry.find_by_category(ToolCategory.PATENT_SEARCH)
        first_query_time = time.time() - start

        # 后续99次查询（缓存命中）
        start = time.time()
        for _ in range(99):
            registry.find_by_category(ToolCategory.PATENT_SEARCH)
        cached_queries_time = time.time() - start

        # 缓存统计
        stats = registry.get_statistics()
        cache_info = stats["cache_performance"]["find_by_category"]

        print("\n📊 分类查找缓存性能:")
        print(f"  首次查询时间: {first_query_time * 1000:.2f}ms")
        print(f"  99次缓存查询时间: {cached_queries_time * 1000:.2f}ms")
        print(f"  平均缓存查询时间: {(cached_queries_time / 99) * 1000:.2f}ms")
        print(f"  缓存命中数: {cache_info['hits']}")
        print(f"  缓存未命中数: {cache_info['misses']}")
        print(f"  缓存命中率: {cache_info['hit_rate']:.2%}")

        # 验证
        assert len(tools1) == 50  # 100个工具中50个PATENT_SEARCH
        assert cache_info["hits"] >= 99  # 至少99次命中
        assert cache_info["hit_rate"] > 0.95  # 命中率>95%

    def test_find_by_domain_cache_hit_rate(self):
        """测试领域查找缓存命中率"""
        registry = ToolRegistry()

        # 注册100个工具（多个领域）
        domains = ["patent", "legal", "academic", "technical", "medical"]
        for i in range(100):
            tool = ToolDefinition(
                tool_id=f"tool_{i}",
                name=f"Tool {i}",
                description=f"Test tool {i}",
                category=ToolCategory.PATENT_SEARCH,
                capability=ToolCapability(
                    input_types=["text"],
                    output_types=["json"],
                    domains=[domains[i % len(domains)],
                    task_types=["search"],
                ),
            )
            registry.register(tool)

        # 查询每个领域100次
        for domain in domains:
            for _ in range(100):
                registry.find_by_domain(domain)

        # 缓存统计
        stats = registry.get_statistics()
        cache_info = stats["cache_performance"]["find_by_domain"]

        print("\n📊 领域查找缓存性能:")
        print(f"  总查询数: {cache_info['hits'] + cache_info['misses']}")
        print(f"  缓存命中数: {cache_info['hits']}")
        print(f"  缓存未命中数: {cache_info['misses']}")
        print(f"  缓存命中率: {cache_info['hit_rate']:.2%}")

        # 验证：首次查询未命中，后续命中
        assert cache_info["misses"] == len(domains)  # 每个领域首次查询未命中
        assert cache_info["hits"] == 100 * len(domains) - len(domains)
        assert cache_info["hit_rate"] > 0.95

    def test_cache_invalidation_on_registration(self):
        """测试工具注册时缓存失效"""
        registry = ToolRegistry()

        # 注册初始工具
        tool1 = ToolDefinition(
            tool_id="tool1",
            name="Tool 1",
            description="Test",
            category=ToolCategory.PATENT_SEARCH,
            capability=ToolCapability(
                input_types=["text"], output_types=["json"], domains=["test"], task_types=["search"]
            ),
        )
        registry.register(tool1)

        # 第一次查询
        tools1 = registry.find_by_category(ToolCategory.PATENT_SEARCH)
        assert len(tools1) == 1

        # 注册新工具（应该清除缓存）
        tool2 = ToolDefinition(
            tool_id="tool2",
            name="Tool 2",
            description="Test",
            category=ToolCategory.PATENT_SEARCH,
            capability=ToolCapability(
                input_types=["text"], output_types=["json"], domains=["test"], task_types=["search"]
            ),
        )
        registry.register(tool2)

        # 再次查询（应该返回新工具）
        tools2 = registry.find_by_category(ToolCategory.PATENT_SEARCH)
        assert len(tools2) == 2


class TestParallelExecutionPerformance:
    """并行执行性能测试 (P2-2)"""

    @pytest.mark.asyncio
    async def test_parallel_vs_serial_execution_time(self):
        """测试并行vs串行执行时间"""
        from core.tools.tool_call_manager import ToolCallManager

        manager = ToolCallManager()

        # 注册模拟工具
        async def mock_handler(params):
            await asyncio.sleep(0.1)  # 模拟100ms执行
            return {"result": "success"}

        for i in range(10):
            tool = ToolDefinition(
                tool_id=f"tool_{i}",
                name=f"Tool {i}",
                description=f"Test tool {i}",
                category=ToolCategory.PATENT_SEARCH,
                capability=ToolCapability(
                    input_types=["text"], output_types=["json"], domains=["test"], task_types=["search"]
                ),
                handler=mock_handler,
            )
            manager.register_tool(tool)

        # 准备工具调用（无依赖，可并行）
        tool_calls = [
            {"tool_name": f"tool_{i}", "parameters": {}} for i in range(10)
        ]

        # 测试串行执行
        start = time.time()
        serial_results = []
        for call in tool_calls:
            result = await manager.call_tool(
                tool_name=call["tool_name"],
                parameters=call["parameters"],
            )
            serial_results.append(result)
        serial_time = time.time() - start

        # 测试并行执行
        start = time.time()
        parallel_results = await manager.call_tools_parallel(
            tool_calls=tool_calls,
            max_concurrency=10,
        )
        parallel_time = time.time() - start

        # 计算加速比
        speedup = serial_time / parallel_time

        print("\n📊 并行执行性能对比:")
        print(f"  串行执行时间: {serial_time * 1000:.2f}ms")
        print(f"  并行执行时间: {parallel_time * 1000:.2f}ms")
        print(f"  加速比: {speedup:.2f}x")
        print(f"  性能提升: {(1 - parallel_time / serial_time) * 100:.1f}%")

        # 验证
        assert len(serial_results) == 10
        assert len(parallel_results) == 10
        assert speedup > 2.0  # 至少2x加速


class TestOverallPerformance:
    """整体性能测试"""

    def test_combined_performance_improvements(self):
        """测试组合性能优化"""
        registry = ToolRegistry()

        # 注册大量工具
        num_tools = 200
        categories = list(ToolCategory)
        domains = ["patent", "legal", "academic", "technical", "medical"]

        for i in range(num_tools):
            tool = ToolDefinition(
                tool_id=f"tool_{i}",
                name=f"Tool {i}",
                description=f"Test tool {i}",
                category=categories[i % len(categories)],
                capability=ToolCapability(
                    input_types=["text"],
                    output_types=["json"],
                    domains=[domains[i % len(domains)],
                    task_types=["search"],
                ),
            )
            registry.register(tool)

        # 测试查询性能（预热）
        for _ in range(10):
            registry.find_by_category(ToolCategory.PATENT_SEARCH)
            registry.find_by_domain("patent")

        # 测试查询性能（测量）
        start = time.time()
        for _ in range(100):
            registry.find_by_category(ToolCategory.PATENT_SEARCH)
            registry.find_by_domain("patent")
        query_time = time.time() - start

        # 获取缓存统计
        stats = registry.get_statistics()
        category_hit_rate = stats["cache_performance"]["find_by_category"]["hit_rate"]
        domain_hit_rate = stats["cache_performance"]["find_by_domain"]["hit_rate"]

        print("\n📊 整体性能测试:")
        print(f"  工具数量: {num_tools}")
        print(f"  200次查询总时间: {query_time * 1000:.2f}ms")
        print(f"  平均查询时间: {(query_time / 200) * 1000:.2f}ms")
        print(f"  分类查找缓存命中率: {category_hit_rate:.2%}")
        print(f"  领域查找缓存命中率: {domain_hit_rate:.2%}")

        # 验证性能指标
        assert category_hit_rate > 0.90  # 缓存命中率>90%
        assert domain_hit_rate > 0.90
        assert (query_time / 200) < 0.01  # 平均查询时间<10ms


if __name__ == "__main__":
    # 运行性能测试
    print("🚀 开始性能优化测试\n")

    pytest.main([__file__, "-v", "-s"])
