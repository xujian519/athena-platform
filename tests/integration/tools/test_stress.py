#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具系统压力测试

测试工具库在高负载下的表现

作者: Athena平台团队
创建时间: 2026-01-25
"""

import pytest
import asyncio
import time
from pathlib import Path
import sys
from concurrent.futures import ThreadPoolExecutor
import threading

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from core.tools.base import (
    ToolDefinition,
    ToolCategory,
    ToolRegistry,
    ToolPerformance,
    ToolPriority,
    ToolCapability
)
from core.tools.selector import ToolSelector
from core.tools.tool_call_manager import ToolCallManager, CallStatus


@pytest.mark.performance
@pytest.mark.stress
class TestToolStress:
    """工具系统压力测试"""

    @pytest.mark.asyncio
    async def test_concurrent_tool_registration(self):
        """测试并发工具注册"""
        registry = ToolRegistry()
        errors = []

        def register_tools(thread_id):
            try:
                for i in range(100):
                    tool = ToolDefinition(
                        tool_id=f"tool_{thread_id}_{i}",
                        name=f"工具{thread_id}_{i}",
                        category=ToolCategory.CODE_ANALYSIS,
                        description=f"测试工具{i}"
                    )
                    registry.register(tool)
            except Exception as e:
                errors.append(e)

        # 创建10个线程，每个注册100个工具
        threads = []
        for i in range(10):
            t = threading.Thread(target=register_tools, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # 验证没有错误
        assert len(errors) == 0

        # 验证所有工具都已注册
        stats = registry.get_statistics()
        assert stats["total_tools"] == 1000

    @pytest.mark.asyncio
    async def test_high_volume_tool_calls(self):
        """测试大量工具调用"""
        manager = ToolCallManager(
            enable_rate_limit=False,
            max_history=10000
        )

        # 创建测试工具
        async def fast_handler(params, context):
            return {"result": "ok"}

        tool = ToolDefinition(
            tool_id="fast_tool",
            name="快速工具",
            category=ToolCategory.CODE_ANALYSIS,
            description="快速测试工具",
            handler=fast_handler,
            timeout=30.0
        )
        manager.register_tool(tool)

        # 并发调用1000次
        start = time.perf_counter()

        tasks = [
            manager.call_tool("fast_tool", {"input": f"test_{i}"})
            for i in range(1000)
        ]

        results = await asyncio.gather(*tasks)

        elapsed = time.perf_counter() - start

        # 验证所有调用都成功
        assert all(r.status == CallStatus.SUCCESS for r in results)

        # 验证性能
        assert elapsed < 5.0, f"1000次调用耗时过长: {elapsed:.2f}秒"

        # 验证统计
        stats = manager.get_stats()
        assert stats["total_calls"] == 1000
        assert stats["successful_calls"] == 1000

    @pytest.mark.asyncio
    async def test_rate_limiting_under_load(self):
        """测试高负载下的速率限制"""
        manager = ToolCallManager(
            enable_rate_limit=True,
            max_calls_per_minute=100
        )

        # 创建测试工具
        async def handler(params, context):
            await asyncio.sleep(0.01)  # 模拟工作
            return {"result": "ok"}

        tool = ToolDefinition(
            tool_id="test_tool",
            name="测试工具",
            category=ToolCategory.CODE_ANALYSIS,
            description="测试",
            handler=handler,
            timeout=30.0
        )
        manager.register_tool(tool)

        # 前100次调用应该成功
        successful_calls = 0
        rate_limited_calls = 0

        for i in range(100):
            result = await manager.call_tool("test_tool", {})
            if result.status == CallStatus.SUCCESS:
                successful_calls += 1
            elif result.status == CallStatus.FAILED and "速率限制" in result.error:
                rate_limited_calls += 1

        assert successful_calls == 100
        assert rate_limited_calls == 0

        # 第101次调用应该被速率限制
        result = await manager.call_tool("test_tool", {}, timeout=0)
        assert result.status == CallStatus.FAILED

    @pytest.mark.asyncio
    async def test_memory_leak_prevention(self):
        """测试内存泄漏预防"""
        manager = ToolCallManager(
            max_history=100,
            enable_rate_limit=False
        )

        # 创建测试工具
        async def handler(params, context):
            return {"result": "ok"}

        tool = ToolDefinition(
            tool_id="test_tool",
            name="测试工具",
            category=ToolCategory.CODE_ANALYSIS,
            description="测试",
            handler=handler,
            timeout=30.0
        )
        manager.register_tool(tool)

        # 调用1000次，历史记录应该被限制在100条
        for _ in range(1000):
            await manager.call_tool("test_tool", {})

        assert len(manager.call_history) <= 100

    @pytest.mark.asyncio
    async def test_selector_performance_with_large_registry(self):
        """测试选择器在大规模注册表下的性能"""
        registry = ToolRegistry()

        # 定义所有优先级
        priorities = [ToolPriority.CRITICAL, ToolPriority.HIGH, ToolPriority.MEDIUM, ToolPriority.LOW]

        # 注册1000个工具
        for i in range(1000):
            tool = ToolDefinition(
                tool_id=f"tool_{i}",
                name=f"工具{i}",
                category=ToolCategory.CODE_ANALYSIS,
                description=f"测试工具{i}",
                priority=priorities[i % 4],
                capability=ToolCapability(
                    input_types=["input"],
                    output_types=["output"],
                    domains=["test"],
                    task_types=["test"]
                )
            )
            registry.register(tool)

        # 创建选择器
        selector = ToolSelector(registry=registry)

        # 测量选择性能
        start = time.perf_counter()

        for _ in range(100):
            tool = await selector.select_tool(task_type="test", domain="test")
            assert tool is not None

        elapsed = time.perf_counter() - start

        # 平均每次选择应该很快
        avg_time = elapsed / 100
        assert avg_time < 0.01, f"选择时间过长: {avg_time:.4f}秒"

    @pytest.mark.asyncio
    async def test_performance_tracking_accuracy(self):
        """测试性能跟踪准确性"""
        perf = ToolPerformance()

        # 模拟1000次调用，成功率85%
        execution_times = [0.001 * (i % 10) for i in range(1000)]
        successes = [i % 100 < 85 for i in range(1000)]

        for exec_time, success in zip(execution_times, successes):
            perf.update(exec_time, success)

        # 验证统计准确性
        assert perf.total_calls == 1000
        assert perf.successful_calls == 850
        assert perf.failed_calls == 150
        assert perf.success_rate == 0.85

        # 验证执行时间统计
        expected_avg = sum(execution_times) / len(execution_times)
        assert abs(perf.avg_execution_time - expected_avg) < 0.0001

    @pytest.mark.asyncio
    async def test_concurrent_access_to_shared_registry(self):
        """测试对共享注册中心的并发访问"""
        registry = ToolRegistry()
        results = {"success": 0, "error": 0}
        lock = threading.Lock()

        async def register_and_retrieve(tool_id):
            try:
                # 注册工具
                tool = ToolDefinition(
                    tool_id=tool_id,
                    name=f"工具{tool_id}",
                    category=ToolCategory.CODE_ANALYSIS,
                    description="测试"
                )
                registry.register(tool)

                # 检索工具
                retrieved = registry.get_tool(tool_id)
                assert retrieved is not None
                assert retrieved.tool_id == tool_id

                with lock:
                    results["success"] += 1
            except Exception as e:
                with lock:
                    results["error"] += 1

        # 并发注册和检索100个工具
        tasks = [
            register_and_retrieve(f"tool_{i}")
            for i in range(100)
        ]

        await asyncio.gather(*tasks)

        # 验证所有操作都成功
        assert results["success"] == 100
        assert results["error"] == 0


@pytest.mark.performance
@pytest.mark.stress
class TestToolSystemBenchmarks:
    """工具系统基准测试"""

    @pytest.mark.asyncio
    async def test_registration_throughput(self):
        """测试工具注册吞吐量"""
        registry = ToolRegistry()

        start = time.perf_counter()

        # 注册100个工具
        for i in range(100):
            tool = ToolDefinition(
                tool_id=f"tool_{i}",
                name=f"工具{i}",
                category=ToolCategory.CODE_ANALYSIS,
                description="测试"
            )
            registry.register(tool)

        elapsed = time.perf_counter() - start

        # 注册100个工具应该很快
        assert elapsed < 0.1, f"注册耗时过长: {elapsed:.4f}秒"

        # 验证吞吐量
        throughput = 100 / elapsed
        assert throughput > 1000, f"注册吞吐量过低: {throughput:.0f} 工具/秒"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "performance or stress", "--tb=short"])
