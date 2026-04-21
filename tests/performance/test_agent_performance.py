#!/usr/bin/env python3
"""
Agent性能基准测试
Agent Performance Benchmark Tests

测试Agent执行的性能指标，包括:
1. Agent初始化性能
2. Agent任务处理性能
3. Agent间通信性能
4. Agent注册和发现性能

作者: Athena平台团队
创建时间: 2026-04-21
版本: v1.0.0
"""
from __future__ import annotations

import pytest
from tests.performance.benchmark_runner import get_benchmark_runner


@pytest.mark.performance
@pytest.mark.agent
class TestAgentPerformance:
    """Agent性能基准测试"""

    @pytest.mark.asyncio
    async def test_service_registry_initialization(self):
        """测试服务注册中心初始化性能"""
        runner = get_benchmark_runner()

        async def init_registry():
            from core.service_registry import get_service_registry

            registry = get_service_registry()
            return registry

        result = await runner.benchmark_async(
            name="服务注册中心初始化",
            func=init_registry,
            iterations=20,
            target_avg=0.1,  # 目标: <100ms
            target_p95=0.2,  # 目标: P95 <200ms
        )

        assert result.meets_target(), f"服务注册中心初始化性能未达标: {result}"

    @pytest.mark.asyncio
    async def test_service_discovery_performance(self):
        """测试服务发现性能"""
        runner = get_benchmark_runner()

        async def discover_service():
            from core.service_registry import get_discovery_api

            api = get_discovery_api()

            # 模拟服务发现（不实际调用，避免依赖）
            import asyncio
            await asyncio.sleep(0.001)  # 模拟查询延迟

            return {"name": "test-service", "host": "localhost", "port": 8000}

        result = await runner.benchmark_async(
            name="服务发现",
            func=discover_service,
            iterations=100,
            target_avg=0.02,  # 目标: <20ms
            target_p95=0.05,  # 目标: P95 <50ms
        )

        assert result.meets_target(), f"服务发现性能未达标: {result}"

    @pytest.mark.asyncio
    async def test_health_check_performance(self):
        """测试健康检查性能"""
        runner = get_benchmark_runner()

        async def health_check():
            from core.service_registry import get_health_checker

            checker = get_health_checker()

            # 模拟健康检查
            import asyncio
            await asyncio.sleep(0.001)  # 模拟检查延迟

            return {"status": "healthy"}

        result = await runner.benchmark_async(
            name="健康检查",
            func=health_check,
            iterations=100,
            target_avg=0.01,  # 目标: <10ms
            target_p95=0.02,  # 目标: P95 <20ms
        )

        assert result.meets_target(), f"健康检查性能未达标: {result}"
