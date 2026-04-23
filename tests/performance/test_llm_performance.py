#!/usr/bin/env python3
"""
LLM性能基准测试
LLM Performance Benchmark Tests

测试LLM服务的性能指标，包括:
1. LLM管理器初始化性能
2. 模型选择性能
3. 响应缓存性能
4. 智能路由性能

作者: Athena平台团队
创建时间: 2026-04-21
版本: v1.0.0
"""

import pytest

from tests.performance.benchmark_runner import get_benchmark_runner


@pytest.mark.performance
@pytest.mark.llm
class TestLLMPerformance:
    """LLM性能基准测试"""

    @pytest.mark.asyncio
    async def test_llm_manager_initialization(self):
        """测试LLM管理器初始化性能"""
        runner = get_benchmark_runner()

        async def init_manager():
            from core.ai.llm.unified_llm_manager import UnifiedLLMManager
            manager = UnifiedLLMManager()
            return manager

        result = await runner.benchmark_async(
            name="LLM管理器初始化",
            func=init_manager,
            iterations=20,
            target_avg=0.5,  # 目标: <500ms
            target_p95=1.0,  # 目标: P95 <1s
        )

        assert result.meets_target(), f"LLM管理器初始化性能未达标: {result}"

    @pytest.mark.asyncio
    async def test_model_selection_performance(self):
        """测试模型选择性能"""
        runner = get_benchmark_runner()

        async def select_model():
            from core.ai.llm.model_registry import get_model_registry
            from core.ai.llm.model_selector import IntelligentModelSelector

            registry = get_model_registry()
            selector = IntelligentModelSelector(registry)

            # 模拟模型选择
            from core.ai.llm.base import LLMRequest, SelectionCriteria, SelectionStrategy

            criteria = SelectionCriteria(
                task_type="creativity_analysis",
                strategy=SelectionStrategy.BALANCED,
            )

            request = LLMRequest(
                prompt="测试提示",
                criteria=criteria,
            )

            model = selector.select_model(request)
            return model

        result = await runner.benchmark_async(
            name="模型选择",
            func=select_model,
            iterations=100,
            target_avg=0.01,  # 目标: <10ms
            target_p95=0.02,  # 目标: P95 <20ms
        )

        assert result.meets_target(), f"模型选择性能未达标: {result}"

    @pytest.mark.asyncio
    async def test_response_cache_performance(self):
        """测试响应缓存性能"""
        runner = get_benchmark_runner()

        async def cache_operation():
            from core.ai.llm.response_cache import get_response_cache

            cache = get_response_cache()

            # 模拟缓存操作
            import asyncio
            await asyncio.sleep(0.001)  # 模拟缓存延迟

            # 测试缓存键生成
            cache_key = cache._generate_cache_key(
                prompt="测试提示",
                model="test-model",
                parameters={},
            )

            return cache_key

        result = await runner.benchmark_async(
            name="响应缓存操作",
            func=cache_operation,
            iterations=1000,
            target_avg=0.005,  # 目标: <5ms
            target_p95=0.01,  # 目标: P95 <10ms
        )

        assert result.meets_target(), f"响应缓存性能未达标: {result}"

    @pytest.mark.asyncio
    async def test_smart_routing_performance(self):
        """测试智能路由性能"""
        runner = get_benchmark_runner()

        async def routing_decision():
            from core.ai.llm.smart_model_routing import TaskComplexityAnalyzer

            analyzer = TaskComplexityAnalyzer()

            # 模拟复杂度分析
            complexity = analyzer.analyze_complexity(
                message="这是一个简单的测试消息",
                task_type="general_chat",
                context={},
            )

            return complexity

        result = await runner.benchmark_async(
            name="智能路由决策",
            func=routing_decision,
            iterations=100,
            target_avg=0.02,  # 目标: <20ms
            target_p95=0.05,  # 目标: P95 <50ms
        )

        assert result.meets_target(), f"智能路由性能未达标: {result}"

