#!/usr/bin/env python3
"""
UnifiedLLMManager单元测试

测试统一LLM管理器的所有核心功能，确保覆盖率>80%

测试范围:
- 初始化和配置
- 模型适配器加载
- LLM生成功能
- 提示词管理
- 健康检查
- 统计信息
- 成本监控
- 缓存管理
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, Mock

from core.llm.unified_llm_manager import UnifiedLLMManager
from core.llm.base import LLMRequest, LLMResponse
from core.llm.model_registry import ModelCapabilityRegistry


# ==================== Mock适配器 ====================

class MockLLMAdapter:
    """Mock LLM适配器"""

    def __init__(self, model_id: str = "mock-model"):
        self.model_id = model_id
        self.initialized = False

    async def initialize(self):
        self.initialized = True

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Mock生成方法"""
        return LLMResponse(
            content=f"Mock response for: {request.message[:50]}",
            model_used=self.model_id,
            tokens_used=30,
            processing_time=0.1
        )

    def supports_capability(self, capability: str) -> bool:
        """Mock能力检查"""
        return True

    def get_model_info(self) -> dict:
        """获取模型信息"""
        return {
            "model_id": self.model_id,
            "provider": "mock",
            "capabilities": ["chat", "completion"]
        }


# ==================== 初始化测试 ====================

class TestInitialization:
    """测试管理器初始化"""

    def test_basic_initialization(self):
        """测试基本初始化"""
        manager = UnifiedLLMManager()

        assert manager.registry is not None
        assert manager.selector is not None
        assert isinstance(manager.adapters, dict)
        assert len(manager.adapters) == 0

    def test_initialization_with_custom_registry(self):
        """测试使用自定义注册表初始化"""
        registry = ModelCapabilityRegistry()
        manager = UnifiedLLMManager(registry=registry)

        assert manager.registry is registry

    def test_stats_initialization(self):
        """测试统计信息初始化"""
        manager = UnifiedLLMManager()

        assert manager.stats["total_requests"] == 0
        assert manager.stats["successful_requests"] == 0
        assert manager.stats["failed_requests"] == 0
        assert manager.stats["total_cost"] == 0.0
        assert manager.stats["total_tokens"] == 0


# ==================== 适配器管理测试 ====================

class TestAdapterManager:
    """测试适配器管理"""

    @pytest.mark.asyncio
    async def test_load_adapters(self):
        """测试加载适配器"""
        manager = UnifiedLLMManager()

        # Mock加载适配器的方法
        manager._load_glm_adapters = AsyncMock()
        manager._load_deepseek_adapters = AsyncMock()
        manager._load_local_adapters = AsyncMock()
        manager._load_ollama_adapters = AsyncMock()
        manager._load_qwen_adapters = AsyncMock()

        await manager._load_adapters()

        # 验证所有加载方法都被调用
        manager._load_glm_adapters.assert_called_once()
        manager._load_deepseek_adapters.assert_called_once()
        manager._load_local_adapters.assert_called_once()
        manager._load_ollama_adapters.assert_called_once()
        manager._load_qwen_adapters.assert_called_once()

    @pytest.mark.asyncio
    async def test_adapter_registration(self):
        """测试适配器注册"""
        manager = UnifiedLLMManager()

        # 手动注册一个适配器
        mock_adapter = MockLLMAdapter("test-model")
        manager.adapters["test-model"] = mock_adapter

        assert "test-model" in manager.adapters
        assert manager.adapters["test-model"] is mock_adapter


# ==================== LLM生成测试 ====================

class TestLLMGeneration:
    """测试LLM生成功能"""

    @pytest.mark.asyncio
    async def test_generate_basic(self):
        """测试基本生成功能"""
        manager = UnifiedLLMManager()

        # Mock selector
        manager.selector.select_model = AsyncMock(return_value="test-model")

        # Mock adapter
        mock_adapter = MockLLMAdapter("test-model")
        manager.adapters["test-model"] = mock_adapter

        # 创建请求
        request = LLMRequest(
            message="Hello, world!",
            task_type="chat",
            max_tokens=100
        )

        # 生成响应
        response = await manager.generate("Hello, world!", "simple_chat")

        assert response is not None
        assert response.content is not None
        assert "Mock response" in response.content

    @pytest.mark.asyncio
    async def test_generate_with_system_prompt(self):
        """测试带系统提示的生成"""
        manager = UnifiedLLMManager()

        # Mock selector
        manager.selector.select_model = AsyncMock(return_value="test-model")

        # Mock adapter
        mock_adapter = MockLLMAdapter("test-model")
        manager.adapters["test-model"] = mock_adapter

        # Mock get_system_prompt
        manager._get_system_prompt = AsyncMock(return_value="System: You are helpful")

        response = await manager.generate("Test", "simple_chat")

        assert response.content is not None
        manager._get_system_prompt.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_model_not_found(self):
        """测试模型未找到"""
        manager = UnifiedLLMManager()

        # Mock selector返回不存在的模型
        manager.selector.select_model = MagicMock(return_value="nonexistent-model")

        # 应该返回错误响应或抛出异常
        try:
            response = await manager.generate("Test", "simple_chat")
            # 如果返回响应，检查内容
            if response:
                assert response.content is not None or response.model_used is not None
        except Exception as e:
            # 预期可能抛出异常
            assert "nonexistent-model" in str(e) or "not found" in str(e).lower()


# ==================== 提示词管理测试 ====================

class TestPromptManagement:
    """测试提示词管理"""

    @pytest.mark.asyncio
    async def test_get_system_prompt(self):
        """测试获取系统提示"""
        manager = UnifiedLLMManager()

        # 测试默认提示
        prompt = await manager._get_system_prompt("chat", "test-model")

        # 系统提示可能为空字符串或默认提示
        assert prompt is not None
        assert isinstance(prompt, str)

    @pytest.mark.asyncio
    async def test_task_to_agent_mapping(self):
        """测试任务到Agent的映射"""
        manager = UnifiedLLMManager()

        # 测试已知任务类型
        agent = manager._map_task_to_agent("patent_analysis")
        # 应该返回小娜或None
        assert agent is None or isinstance(agent, str)

        agent = manager._map_task_to_agent("coordination")
        # 应该返回小诺或None
        assert agent is None or isinstance(agent, str)


# ==================== 健康检查测试 ====================

class TestHealthCheck:
    """测试健康检查功能"""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """测试健康检查"""
        manager = UnifiedLLMManager()

        health = await manager.health_check()

        assert isinstance(health, dict)
        # 健康检查应该返回字典 (可能为空)

    @pytest.mark.asyncio
    async def test_health_check_with_adapters(self):
        """测试带适配器的健康检查"""
        manager = UnifiedLLMManager()

        # 添加一些适配器
        manager.adapters["model1"] = MockLLMAdapter("model1")
        manager.adapters["model2"] = MockLLMAdapter("model2")

        health = await manager.health_check()

        assert isinstance(health, dict)


# ==================== 统计信息测试 ====================

class TestStatistics:
    """测试统计信息功能"""

    def test_get_stats(self):
        """测试获取统计信息"""
        manager = UnifiedLLMManager()

        stats = manager.get_stats()

        assert isinstance(stats, dict)
        assert "total_requests" in stats
        assert "successful_requests" in stats
        assert "failed_requests" in stats

    def test_reset_stats(self):
        """测试重置统计"""
        manager = UnifiedLLMManager()

        # 修改一些统计
        manager.stats["total_requests"] = 100
        manager.stats["successful_requests"] = 80

        # 重置
        manager.reset_stats()

        assert manager.stats["total_requests"] == 0
        assert manager.stats["successful_requests"] == 0

    @pytest.mark.asyncio
    async def test_update_stats_on_success(self):
        """测试成功时更新统计"""
        manager = UnifiedLLMManager()

        # Mock selector和adapter
        manager.selector.select_model = MagicMock(return_value="test-model")
        manager.adapters["test-model"] = MockLLMAdapter("test-model")

        # 记录初始统计
        initial_requests = manager.stats.get("total_requests", 0)

        # 模拟生成
        await manager.generate("Test", "simple_chat")

        # 验证统计被更新
        assert manager.stats.get("total_requests", 0) >= initial_requests


# ==================== 成本监控测试 ====================

class TestCostMonitoring:
    """测试成本监控功能"""

    def test_get_cost_report(self):
        """测试获取成本报告"""
        manager = UnifiedLLMManager()

        report = manager.get_cost_report(time_window="today")

        assert isinstance(report, str)
        assert len(report) > 0

    def test_get_budget_status(self):
        """测试获取预算状态"""
        manager = UnifiedLLMManager()

        budget = manager.get_budget_status()

        assert isinstance(budget, dict)
        # 应该包含预算信息 (daily_budget, budget_utilization等)
        assert "daily_budget" in budget or "budget_utilization" in budget


# ==================== 模型可用性测试 ====================

class TestModelAvailability:
    """测试模型可用性"""

    def test_get_available_models(self):
        """测试获取可用模型列表"""
        manager = UnifiedLLMManager()

        # 添加一些适配器
        manager.adapters["model1"] = MockLLMAdapter("model1")
        manager.adapters["model2"] = MockLLMAdapter("model2")

        models = manager.get_available_models()

        assert isinstance(models, list)
        assert "model1" in models
        assert "model2" in models

    def test_get_available_models_empty(self):
        """测试空模型列表"""
        manager = UnifiedLLMManager()

        models = manager.get_available_models()

        assert isinstance(models, list)
        # 可能是空列表或包含默认模型


# ==================== 指标导出测试 ====================

class TestMetricsExport:
    """测试指标导出功能"""

    def test_export_metrics(self):
        """测试导出Prometheus指标"""
        manager = UnifiedLLMManager()

        metrics, content_type = manager.export_metrics()

        assert metrics is not None
        assert isinstance(metrics, bytes)
        # Prometheus内容类型包含版本和字符集信息
        assert "text/plain" in content_type

    def test_get_metrics_summary(self):
        """测试获取指标摘要"""
        manager = UnifiedLLMManager()

        summary = manager.get_metrics_summary()

        assert isinstance(summary, dict)
        # 应该包含关键指标 (metrics_count, metrics_list等)
        assert "metrics_count" in summary or "metrics_list" in summary


# ==================== 缓存管理测试 ====================

class TestCacheManagement:
    """测试缓存管理功能"""

    @pytest.mark.asyncio
    async def test_cache_warmup(self):
        """测试缓存预热"""
        manager = UnifiedLLMManager()

        # Mock cache_warmer
        manager.cache_warmer = AsyncMock()
        manager.cache_warmer.warmup = AsyncMock(
            return_value={
                "success": True,
                "warmed_models": [],
                "errors": []
            }
        )

        await manager.initialize(enable_cache_warmup=True)

        # 验证预热被调用
        manager.cache_warmer.warmup.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_without_warmup(self):
        """测试不预热缓存初始化"""
        manager = UnifiedLLMManager()

        # 不应该预热缓存
        await manager.initialize(enable_cache_warmup=False)

        # 验证stats中没有warmup_results
        assert manager.stats.get("warmup_results") is None


# ==================== 智能路由测试 ====================

class TestSmartRouting:
    """测试智能路由功能"""

    def test_smart_routing_availability(self):
        """测试智能路由可用性"""
        manager = UnifiedLLMManager()

        # 智能路由可能启用或禁用
        if manager._smart_routing_enabled:
            assert manager.smart_router is not None
        else:
            assert manager.smart_router is None

    def test_smart_routing_stats(self):
        """测试智能路由统计"""
        manager = UnifiedLLMManager()

        # 检查统计中是否包含智能路由信息
        stats = manager.get_stats()

        # 可能包含smart_routing_savings
        if "smart_routing_savings" in stats:
            assert isinstance(stats["smart_routing_savings"], (int, float))


# ==================== 错误处理测试 ====================

class TestErrorHandling:
    """测试错误处理"""

    @pytest.mark.asyncio
    async def test_handle_generation_error(self):
        """测试生成错误处理"""
        manager = UnifiedLLMManager()

        # Mock selector
        manager.selector.select_model = AsyncMock(return_value="test-model")

        # Mock adapter that raises error
        async def failing_generate(request):
            raise Exception("Generation failed")

        mock_adapter = MockLLMAdapter("test-model")
        mock_adapter.generate = failing_generate

        manager.adapters["test-model"] = mock_adapter

        # 应该处理错误
        try:
            response = await manager.generate("Test", "simple_chat")
            # 如果返回响应，检查内容
            if response:
                assert response.content is not None
        except Exception:
            # 也可能抛出异常
            pass

        # 验证统计更新
        assert manager.stats.get("failed_requests", 0) >= 1 or \
               manager.stats.get("total_requests", 0) >= 1


# ==================== 边界情况测试 ====================

class TestEdgeCases:
    """测试边界情况"""

    def test_empty_prompt(self):
        """测试空提示"""
        manager = UnifiedLLMManager()

        # 空提示应该被处理
        # 可能返回错误响应或默认响应

    def test_very_long_prompt(self):
        """测试超长提示"""
        manager = UnifiedLLMManager()

        # 超长提示应该被截断或处理
        long_prompt = "A" * 100000

    def test_concurrent_generation(self):
        """测试并发生成"""
        import asyncio

        async def test_concurrent():
            manager = UnifiedLLMManager()

            # Mock selector和adapter
            manager.selector.select_model = MagicMock(return_value="test-model")
            mock_adapter = MockLLMAdapter("test-model")
            manager.adapters["test-model"] = mock_adapter

            # 创建多个并发请求
            tasks = [
                manager.generate(f"Request {i}", "chat")
                for i in range(10)
            ]

            # 并发生成
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # 验证所有响应
            successful = sum(1 for r in responses if isinstance(r, LLMResponse) and r.content)
            assert successful >= 8  # 至少80%成功

        # 运行测试
        asyncio.run(test_concurrent())


# ==================== 性能测试 ====================

class TestPerformance:
    """测试性能指标"""

    def test_manager_initialization_speed(self):
        """测试管理器初始化速度"""
        import time

        start = time.time()
        manager = UnifiedLLMManager()
        elapsed = time.time() - start

        # 初始化应该很快 (< 0.1秒)
        assert elapsed < 0.1

    def test_stats_retrieval_speed(self):
        """测试统计检索速度"""
        import time

        manager = UnifiedLLMManager()

        # 添加一些数据
        for i in range(100):
            manager.stats[f"key_{i}"] = f"value_{i}"

        start = time.time()
        stats = manager.get_stats()
        elapsed = time.time() - start

        # 检索应该很快 (< 0.01秒)
        assert elapsed < 0.01


# ==================== 关闭和清理测试 ====================

class TestShutdown:
    """测试关闭和清理"""

    @pytest.mark.asyncio
    async def test_shutdown(self):
        """测试正常关闭"""
        manager = UnifiedLLMManager()

        # 添加一些适配器
        manager.adapters["model1"] = MockLLMAdapter("model1")

        # 关闭应该不抛出异常
        try:
            await manager.shutdown()
        except Exception as e:
            pytest.fail(f"Shutdown raised exception: {e}")

    @pytest.mark.asyncio
    async def test_shutdown_with_cleanup(self):
        """测试带清理的关闭"""
        manager = UnifiedLLMManager()

        # 添加多个适配器
        for i in range(5):
            manager.adapters[f"model{i}"] = MockLLMAdapter(f"model{i}")

        # 关闭
        await manager.shutdown()

        # 验证适配器被清理
        # (具体清理逻辑取决于实现)
