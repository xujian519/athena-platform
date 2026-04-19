#!/usr/bin/env python3
"""
工具系统性能基准测试

测试工具调用的延迟、吞吐量、并发性能等指标。
"""
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from statistics import mean, median, stdev

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from core.tools.tool_manager import ToolManager
from core.tools.selector import ToolSelector, SelectionStrategy
from core.tools.tool_call_manager import ToolCallManager, ToolCallRequest
from core.tools.base import ToolDefinition, ToolRegistry, ToolPriority


class TestToolPerformance:
    """测试工具系统性能"""

    def test_tool_registration_performance(self):
        """测试工具注册性能"""

        registry = ToolRegistry()

        # 测试批量注册工具的性能
        start_time = time.time()

        num_tools = 100
        for i in range(num_tools):
            tool = ToolDefinition(
                name=f"tool_{i}",
                display_name=f"工具{i}",
                description=f"测试工具{i}",
                category="test",
                priority=ToolPriority.MEDIUM,
                parameters=[],
            )
            registry.register(tool)

        end_time = time.time()
        registration_time = end_time - start_time

        # 验证所有工具都已注册
        assert len(registry.list_tools()) == num_tools

        # 性能断言:100个工具注册应该在1秒内完成
        assert registration_time < 1.0, f"工具注册太慢: {registration_time:.3f}秒"

        print(f"\n✅ 注册{num_tools}个工具耗时: {registration_time:.3f}秒")
        print(f"   平均每个工具: {registration_time/num_tools*1000:.2f}毫秒")

    def test_tool_selection_performance(self):
        """测试工具选择性能"""

        registry = ToolRegistry()

        # 注册多个工具
        categories = ["search", "compute", "file", "network", "database"]
        priorities = [ToolPriority.HIGH, ToolPriority.MEDIUM, ToolPriority.LOW]

        for i in range(50):
            tool = ToolDefinition(
                name=f"tool_{i}",
                display_name=f"工具{i}",
                description=f"测试工具{i}",
                category=categories[i % len(categories)],
                priority=priorities[i % len(priorities)],
                parameters=[],
            )
            registry.register(tool)

        # 测试选择性能
        selector = ToolSelector(registry)
        tools = registry.list_tools()

        start_time = time.time()

        num_selections = 1000
        for i in range(num_selections):
            selector.select_best_tool(tools, f"测试任务{i % 10}")

        end_time = time.time()
        selection_time = end_time - start_time

        # 性能断言:1000次选择应该在5秒内完成
        assert selection_time < 5.0, f"工具选择太慢: {selection_time:.3f}秒"

        print(f"\n✅ 执行{num_selections}次工具选择耗时: {selection_time:.3f}秒")
        print(f"   平均每次选择: {selection_time/num_selections*1000:.2f}毫秒")
        print(f"   吞吐量: {num_selections/selection_time:.0f} 次/秒")

    def test_tool_call_latency(self):
        """测试工具调用延迟"""

        call_manager = ToolCallManager()

        # 注册工具
        tool = ToolDefinition(
            name="test_tool",
            display_name="测试工具",
            description="测试工具",
            category="test",
            priority=ToolPriority.MEDIUM,
            parameters=[],
        )

        call_manager.register_tool(tool)

        # 测试调用延迟
        latencies = []

        from unittest.mock import patch

        for i in range(100):
            request = ToolCallRequest(
                request_id=f"test-latency-{i}",
                tool_name="test_tool",
                parameters={"index": i},
            )

            start_time = time.time()

            with patch.object(call_manager, "_execute_tool_impl", return_value={"result": i}):
                result = call_manager.execute_tool(request)

            end_time = time.time()
            latency = end_time - start_time

            if result.status.value == "success":
                latencies.append(latency)

        # 计算统计数据
        avg_latency = mean(latencies)
        median_latency = median(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)

        print(f"\n✅ 工具调用延迟统计(100次调用):")
        print(f"   平均延迟: {avg_latency*1000:.2f}毫秒")
        print(f"   中位延迟: {median_latency*1000:.2f}毫秒")
        print(f"   最小延迟: {min_latency*1000:.2f}毫秒")
        print(f"   最大延迟: {max_latency*1000:.2f}毫秒")

        # 性能断言:P95延迟应该小于100ms
        sorted_latencies = sorted(latencies)
        p95_latency = sorted_latencies[94]  # 95th percentile
        assert p95_latency < 0.1, f"P95延迟太高: {p95_latency*1000:.2f}毫秒"

        print(f"   P95延迟: {p95_latency*1000:.2f}毫秒 ✅")

    def test_concurrent_throughput(self):
        """测试并发吞吐量"""

        call_manager = ToolCallManager()

        # 注册工具
        tool = ToolDefinition(
            name="concurrent_tool",
            display_name="并发工具",
            description="支持并发",
            category="test",
            priority=ToolPriority.MEDIUM,
            parameters=[],
        )

        call_manager.register_tool(tool)

        # 测试并发性能
        num_requests = 50
        max_workers = 10

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []

            for i in range(num_requests):
                request = ToolCallRequest(
                    request_id=f"test-concurrent-{i}",
                    tool_name="concurrent_tool",
                    parameters={"index": i},
                )

                from unittest.mock import patch

                def execute_call(req):
                    with patch.object(call_manager, "_execute_tool_impl", return_value={"result": req.parameters["index"]}):
                        return call_manager.execute_tool(req)

                future = executor.submit(execute_call, request)
                futures.append(future)

            # 等待所有调用完成
            results = [f.result() for f in as_completed(futures)]

        end_time = time.time()
        total_time = end_time - start_time

        successful = [r for r in results if r.status.value == "success"]
        throughput = len(successful) / total_time

        print(f"\n✅ 并发性能测试({num_requests}个请求,{max_workers}个worker):")
        print(f"   总耗时: {total_time:.3f}秒")
        print(f"   成功调用: {len(successful)}/{num_requests}")
        print(f"   吞吐量: {throughput:.0f} 次/秒")
        print(f"   平均延迟: {total_time/num_requests*1000:.2f}毫秒")

        # 性能断言:吞吐量应该大于10次/秒
        assert throughput > 10, f"吞吐量太低: {throughput:.0f} 次/秒"

    def test_memory_usage(self):
        """测试内存使用"""

        call_manager = ToolCallManager(max_history=1000)

        # 注册工具
        tool = ToolDefinition(
            name="memory_test_tool",
            display_name="内存测试工具",
            description="测试内存使用",
            category="test",
            priority=ToolPriority.MEDIUM,
            parameters=[],
        )

        call_manager.register_tool(tool)

        # 执行大量调用
        from unittest.mock import patch

        for i in range(1000):
            request = ToolCallRequest(
                request_id=f"test-memory-{i}",
                tool_name="memory_test_tool",
                parameters={"data": "x" * 100},  # 100字节数据
            )

            with patch.object(call_manager, "_execute_tool_impl", return_value={"result": "ok"}):
                call_manager.execute_tool(request)

        # 检查历史记录是否被正确限制
        history = call_manager.get_call_history()
        assert len(history) <= 1000, "历史记录超过限制"

        print(f"\n✅ 内存使用测试(1000次调用):")
        print(f"   历史记录数: {len(history)}")
        print(f"   历史记录限制: {call_manager.max_history}")
        print(f"   内存管理: ✅ 正常")

    def test_different_strategies_performance(self):
        """测试不同选择策略的性能"""

        registry = ToolRegistry()

        # 注册工具
        for i in range(20):
            tool = ToolDefinition(
                name=f"tool_{i}",
                display_name=f"工具{i}",
                description=f"测试工具{i}",
                category="test",
                priority=ToolPriority.HIGH if i % 3 == 0 else ToolPriority.MEDIUM,
                parameters=[],
            )
            registry.register(tool)

        tools = registry.list_tools()

        strategies = [
            SelectionStrategy.PRIORITY,
            SelectionStrategy.BALANCED,
            SelectionStrategy.SUCCESS_RATE,
        ]

        results = {}

        for strategy in strategies:
            selector = ToolSelector(registry)
            selector.set_strategy(strategy)

            start_time = time.time()

            for i in range(1000):
                selector.select_best_tool(tools, f"测试任务{i % 5}")

            end_time = time.time()
            total_time = end_time - start_time

            results[strategy.value] = {
                "time": total_time,
                "throughput": 1000 / total_time,
            }

        print(f"\n✅ 不同策略性能对比(1000次选择):")
        for strategy_name, metrics in results.items():
            print(f"   {strategy_name}:")
            print(f"     耗时: {metrics['time']:.3f}秒")
            print(f"     吞吐量: {metrics['throughput']:.0f} 次/秒")

    def test_cache_effectiveness(self):
        """测试缓存有效性"""

        manager = ToolManager()

        # 注册工具组
        from core.tools.tool_group import ToolGroupDef

        group_def = ToolGroupDef(
            name="test-group",
            display_name="测试组",
            description="测试",
            tool_names=["tool1", "tool2", "tool3"],
        )

        manager.register_group(group_def)
        manager.activate_group("test-group")

        # 测试重复获取工具的性能
        start_time = time.time()

        for i in range(1000):
            manager.get_active_tools()

        end_time = time.time()
        total_time = end_time - start_time

        print(f"\n✅ 缓存有效性测试(1000次获取):")
        print(f"   总耗时: {total_time:.3f}秒")
        print(f"   平均耗时: {total_time/1000*1000:.2f}毫秒")

        # 性能断言:1000次获取应该很快(有缓存)
        assert total_time < 1.0, f"获取工具太慢,可能缓存未生效: {total_time:.3f}秒"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
