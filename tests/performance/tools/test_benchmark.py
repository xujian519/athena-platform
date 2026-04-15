#!/usr/bin/env python3
"""
工具库性能基准测试

测试工具管理、选择和注册的性能指标。

作者: Athena平台团队
创建时间: 2026-01-28
版本: v1.0.0
"""

import pytest

pytestmark = pytest.mark.skip(reason="Missing required modules: ")

import asyncio
import sys
import time
from pathlib import Path
from statistics import mean, median

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.tools import (
    ToolCapability,
    ToolCategory,
    ToolDefinition,
    ToolManager,
    ToolPriority,
    ToolRegistry,
    ToolSelector,
)


class TestRegistryBenchmark:
    """注册中心性能基准测试"""

    def test_registration_performance(self):
        """测试注册性能"""
        registry = ToolRegistry()

        # 测试注册1000个工具的时间
        start = time.time()

        for i in range(1000):
            tool = ToolDefinition(
                tool_id=f"tool_{i}",
                name=f"工具{i}",
                description="性能测试工具",
                category=ToolCategory.PATENT_SEARCH,
                priority=ToolPriority.MEDIUM,
                capability=ToolCapability(
                    input_types=["text"],
                    output_types=["json"],
                    domains=["test"],
                    task_types=["test"],
                ),
            )
            registry.register(tool)

        elapsed = time.time() - start

        print(f"\n注册1000个工具耗时: {elapsed:.4f}秒")
        print(f"平均每个工具: {elapsed/1000*1000:.4f}毫秒")
        print(f"注册速度: {1000/elapsed:.0f} 工具/秒")

        # 性能要求: 1000个工具应该在1秒内完成
        assert elapsed < 1.0, f"注册性能不达标: {elapsed:.4f}秒"

    def test_query_performance(self):
        """测试查询性能"""
        registry = ToolRegistry()

        # 注册1000个工具
        for i in range(1000):
            tool = ToolDefinition(
                tool_id=f"tool_{i}",
                name=f"工具{i}",
                description="查询测试工具",
                category=ToolCategory.PATENT_SEARCH if i % 2 == 0 else ToolCategory.ACADEMIC_SEARCH,
                priority=ToolPriority.HIGH if i % 3 == 0 else ToolPriority.MEDIUM,
                capability=ToolCapability(
                    input_types=["text"],
                    output_types=["json"],
                    domains=["test", f"domain_{i % 10}"],
                    task_types=["test"],
                ),
                tags={f"tag_{i % 20}"},
            )
            registry.register(tool)

        # 测试查询性能
        times = []
        for _ in range(100):
            start = time.time()
            results = registry.search_tools(
                category=ToolCategory.PATENT_SEARCH,
                domain="test",
            )
            elapsed = time.time() - start
            times.append(elapsed)

            assert len(results) > 0

        avg_time = mean(times)
        median_time = median(times)
        max_time = max(times)

        print("\n查询性能统计 (100次):")
        print(f"  平均: {avg_time*1000:.4f}毫秒")
        print(f"  中位数: {median_time*1000:.4f}毫秒")
        print(f"  最大: {max_time*1000:.4f}毫秒")

        # 性能要求: 平均查询时间应该 < 1ms
        assert avg_time < 0.001, f"查询性能不达标: {avg_time*1000:.4f}毫秒"

    def test_performance_update_overhead(self):
        """测试性能更新开销"""
        registry = ToolRegistry()

        tool = ToolDefinition(
            tool_id="perf_tool",
            name="性能测试工具",
            description="性能更新测试",
            category=ToolCategory.PATENT_SEARCH,
            priority=ToolPriority.HIGH,
            capability=ToolCapability(
                input_types=["text"],
                output_types=["json"],
                domains=["test"],
                task_types=["test"],
            ),
        )
        registry.register(tool)

        # 测试1000次性能更新
        times = []
        for i in range(1000):
            start = time.time()
            registry.update_tool_performance("perf_tool", 0.5, i % 10 != 0)
            elapsed = time.time() - start
            times.append(elapsed)

        avg_time = mean(times)
        total_time = sum(times)

        print("\n性能更新统计 (1000次):")
        print(f"  总耗时: {total_time:.4f}秒")
        print(f"  平均每次: {avg_time*1000:.4f}毫秒")
        print(f"  更新速度: {1000/total_time:.0f} 次/秒")

        # 性能要求: 更新速度应该 > 10000次/秒
        assert 1000/total_time > 10000, f"更新性能不达标: {1000/total_time:.0f}次/秒"


class TestSelectorBenchmark:
    """选择器性能基准测试"""

    def test_selection_performance(self):
        """测试选择性能"""
        registry = ToolRegistry()

        # 注册100个工具
        for i in range(100):
            tool = ToolDefinition(
                tool_id=f"tool_{i}",
                name=f"工具{i}",
                description="选择测试工具",
                category=ToolCategory.PATENT_SEARCH,
                priority=ToolPriority.HIGH if i < 20 else ToolPriority.MEDIUM,
                capability=ToolCapability(
                    input_types=["text"],
                    output_types=["json"],
                    domains=["patent"],
                    task_types=["search"],
                ),
            )
            # 设置不同的成功率
            for _ in range(i):
                tool.performance.update(0.5, i % 2 == 0)

            registry.register(tool)

        selector = ToolSelector(registry)

        # 测试选择性能
        async def run_benchmark():
            times = []
            for _ in range(100):
                start = time.time()
                tool = await selector.select_tool(
                    task_type="search",
                    domain="patent",
                )
                elapsed = time.time() - start
                times.append(elapsed)

                assert tool is not None

            avg_time = mean(times)
            median_time = median(times)

            print("\n工具选择性能统计 (100次):")
            print(f"  平均: {avg_time*1000:.4f}毫秒")
            print(f"  中位数: {median_time*1000:.4f}毫秒")

            return avg_time

        avg_time = asyncio.run(run_benchmark())

        # 性能要求: 平均选择时间应该 < 5ms
        assert avg_time < 0.005, f"选择性能不达标: {avg_time*1000:.4f}毫秒"

    def test_multi_selection_performance(self):
        """测试多工具选择性能"""
        registry = ToolRegistry()

        for i in range(50):
            tool = ToolDefinition(
                tool_id=f"tool_{i}",
                name=f"工具{i}",
                description="多选测试工具",
                category=ToolCategory.PATENT_SEARCH,
                priority=ToolPriority.HIGH,
                capability=ToolCapability(
                    input_types=["text"],
                    output_types=["json"],
                    domains=["patent"],
                    task_types=["search"],
                ),
            )
            registry.register(tool)

        selector = ToolSelector(registry)

        async def run_benchmark():
            times = []
            for _ in range(50):
                start = time.time()
                tools = await selector.select_tools(
                    task_type="search",
                    domain="patent",
                    max_tools=10,
                )
                elapsed = time.time() - start
                times.append(elapsed)

                assert len(tools) <= 10

            avg_time = mean(times)

            print("\n多工具选择性能统计 (50次):")
            print(f"  平均: {avg_time*1000:.4f}毫秒")

            return avg_time

        avg_time = asyncio.run(run_benchmark())

        # 性能要求: 平均选择时间应该 < 10ms
        assert avg_time < 0.010, f"多选性能不达标: {avg_time*1000:.4f}毫秒"


class TestManagerBenchmark:
    """管理器性能基准测试"""

    def test_group_activation_performance(self):
        """测试工具组激活性能"""
        manager = ToolManager()

        # 注册工具
        for i in range(100):
            tool = ToolDefinition(
                tool_id=f"tool_{i}",
                name=f"工具{i}",
                description="组激活测试工具",
                category=ToolCategory.PATENT_SEARCH,
                priority=ToolPriority.MEDIUM,
                capability=ToolCapability(
                    input_types=["text"],
                    output_types=["json"],
                    domains=["test"],
                    task_types=["test"],
                ),
            )
            manager.registry.register(tool)

        from core.tools.tool_group import GroupActivationRule, ToolGroupDef

        # 创建工具组
        group = ToolGroupDef(
            name="test_group",
            display_name="测试组",
            description="性能测试组",
            tool_ids=[f"tool_{i}" for i in range(100)],
            activation_rules=[
                GroupActivationRule(
                    rule_type=GroupActivationRule.KEYWORD,
                    keywords=["test"],
                    priority=1,
                )
            ],
        )
        manager.register_group(group)

        # 测试激活性能
        times = []
        for _ in range(50):
            start = time.time()
            manager.activate_group("test_group")
            elapsed = time.time() - start
            times.append(elapsed)

            manager.deactivate_group("test_group")

        avg_time = mean(times)

        print("\n工具组激活性能统计 (50次):")
        print(f"  平均: {avg_time*1000:.4f}毫秒")

        # 性能要求: 平均激活时间应该 < 10ms
        assert avg_time < 0.010, f"激活性能不达标: {avg_time*1000:.4f}毫秒"

    def test_get_active_tools_performance(self):
        """测试获取激活工具性能"""
        manager = ToolManager()

        # 注册并激活工具
        from core.tools.tool_group import GroupActivationRule, ToolGroupDef

        for i in range(100):
            tool = ToolDefinition(
                tool_id=f"tool_{i}",
                name=f"工具{i}",
                description="获取测试工具",
                category=ToolCategory.PATENT_SEARCH,
                priority=ToolPriority.MEDIUM,
                capability=ToolCapability(
                    input_types=["text"],
                    output_types=["json"],
                    domains=["test"],
                    task_types=["test"],
                ),
            )
            manager.registry.register(tool)

        group = ToolGroupDef(
            name="test_group",
            display_name="测试组",
            description="测试",
            tool_ids=[f"tool_{i}" for i in range(100)],
            activation_rules=[
                GroupActivationRule(
                    rule_type=GroupActivationRule.KEYWORD,
                    keywords=["test"],
                    priority=1,
                )
            ],
        )
        manager.register_group(group)
        manager.activate_group("test_group")

        # 测试获取性能
        times = []
        for _ in range(100):
            start = time.time()
            tools = manager.get_all_active_tools()
            elapsed = time.time() - start
            times.append(elapsed)

            assert len(tools) == 100

        avg_time = mean(times)

        print("\n获取激活工具性能统计 (100次):")
        print(f"  平均: {avg_time*1000:.4f}毫秒")

        # 性能要求: 平均获取时间应该 < 1ms
        assert avg_time < 0.001, f"获取性能不达标: {avg_time*1000:.4f}毫秒"
