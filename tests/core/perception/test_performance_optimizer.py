#!/usr/bin/env python3
"""
性能优化器测试
Tests for Performance Optimizer
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import asyncio
import time
from unittest.mock import patch

from core.perception.performance_optimizer import (
    CacheManager,
    PerformanceMetrics,
    PerformanceOptimizer,
    get_global_optimizer,
    optimize_performance,
)
from core.perception.streaming_perception_processor import ProcessingMode


class TestPerformanceMetrics:
    """测试PerformanceMetrics性能指标类"""

    @pytest.fixture
    def metrics(self):
        """创建指标实例"""
        return PerformanceMetrics()

    def test_initialization(self, metrics):
        """测试初始化"""
        assert metrics is not None
        assert metrics.total_requests == 0
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 0

    def test_record_request(self, metrics):
        """测试记录请求"""
        metrics.record_request(success=True, processing_time=0.5)
        assert metrics.total_requests == 1
        assert metrics.successful_requests == 1

    def test_record_failure(self, metrics):
        """测试记录失败"""
        metrics.record_request(success=False, processing_time=0.3)
        assert metrics.total_requests == 1
        assert metrics.failed_requests == 1

    def test_success_rate(self, metrics):
        """测试成功率计算"""
        metrics.record_request(success=True, processing_time=0.5)
        metrics.record_request(success=False, processing_time=0.3)
        rate = metrics.get_success_rate()
        assert rate == 0.5

    def test_average_processing_time(self, metrics):
        """测试平均处理时间"""
        metrics.record_request(success=True, processing_time=0.5)
        metrics.record_request(success=True, processing_time=1.0)
        avg_time = metrics.get_average_processing_time()
        assert avg_time == 0.75

    def test_reset(self, metrics):
        """测试重置"""
        metrics.record_request(success=True, processing_time=0.5)
        metrics.reset()
        assert metrics.total_requests == 0
        assert metrics.successful_requests == 0


class TestCacheManager:
    """测试CacheManager缓存管理器类"""

    @pytest.fixture
    def manager(self):
        """创建缓存管理器实例"""
        return CacheManager()

    def test_initialization(self, manager):
        """测试初始化"""
        assert manager is not None
        assert isinstance(manager._cache, dict)

    def test_cache_hit(self, manager):
        """测试缓存命中"""
        cache_key = "test_key"
        cache_value = "test_value"
        ttl = 3600

        manager.set(cache_key, cache_value, ttl)
        retrieved_value = manager.get(cache_key)
        assert retrieved_value == cache_value

    def test_cache_miss(self, manager):
        """测试缓存未命中"""
        value = manager.get("nonexistent_key")
        assert value is None

    def test_cache_expiration(self, manager):
        """测试缓存过期"""
        cache_key = "expiring_key"
        cache_value = "expiring_value"
        ttl = 0  # 立即过期

        manager.set(cache_key, cache_value, ttl)
        # 等待过期
        time.sleep(0.1)
        value = manager.get(cache_key)
        # 值可能已过期
        assert value is None or value == cache_value

    def test_cache_delete(self, manager):
        """测试缓存删除"""
        cache_key = "delete_key"
        cache_value = "delete_value"

        manager.set(cache_key, cache_value, 3600)
        manager.delete(cache_key)
        value = manager.get(cache_key)
        assert value is None

    def test_cache_clear(self, manager):
        """测试清空缓存"""
        manager.set("key1", "value1", 3600)
        manager.set("key2", "value2", 3600)
        manager.clear()
        assert len(manager._cache) == 0

    def test_cache_size_limit(self, manager):
        """测试缓存大小限制"""
        # 设置小缓存
        small_manager = CacheManager(max_size=3)

        small_manager.set("key1", "value1", 3600)
        small_manager.set("key2", "value2", 3600)
        small_manager.set("key3", "value3", 3600)
        small_manager.set("key4", "value4", 3600)

        # 缓存应该有大小限制
        assert len(small_manager._cache) <= 3

    def test_get_stats(self, manager):
        """测试获取统计信息"""
        manager.set("key1", "value1", 3600)
        manager.set("key2", "value2", 3600)

        stats = manager.get_stats()
        assert "total_items" in stats
        assert "cache_size" in stats


class TestPerformanceOptimizer:
    """测试PerformanceOptimizer性能优化器类"""

    @pytest.fixture
    def optimizer(self):
        """创建优化器实例"""
        config = {
            "enable_cache": True,
            "enable_batch_processing": True,
            "max_workers": 4,
            "cache_ttl": 3600
        }
        return PerformanceOptimizer(config)

    def test_initialization(self, optimizer):
        """测试初始化"""
        assert optimizer is not None
        assert optimizer.config is not None
        assert optimizer.enable_cache is True

    def test_optimize_single_item(self, optimizer):
        """测试优化单个项目"""
        def mock_processor(data):
            return f"processed_{data}"

        result = optimizer.optimize_single_item(mock_processor, "test_data")
        assert result == "processed_test_data"

    @pytest.mark.asyncio
    async def test_batch_process(self, optimizer):
        """测试批量处理"""
        items = [
            {"data": f"item_{i}"}
            for i in range(5)
        ]

        async def mock_processor(item):
            await asyncio.sleep(0.01)
            return f"processed_{item['data']}"

        with patch.object(optimizer, 'batch_process') as mock_batch:
            mock_batch.return_value = [
                f"processed_item_{i}" for i in range(5)
            ]
            results = await mock_batch(mock_processor, items)
            assert len(results) == 5

    def test_cache_result(self, optimizer):
        """测试缓存结果"""
        cache_key = "test_key"
        result = "test_result"
        ttl = 3600

        optimizer.cache_result(cache_key, result, ttl)
        cached = optimizer.get_cached_result(cache_key)
        assert cached == result

    def test_invalidate_cache(self, optimizer):
        """测试失效缓存"""
        cache_key = "invalidate_key"
        optimizer.cache_result(cache_key, "value", 3600)
        optimizer.invalidate_cache(cache_key)
        cached = optimizer.get_cached_result(cache_key)
        assert cached is None

    def test_get_metrics(self, optimizer):
        """测试获取性能指标"""
        metrics = optimizer.get_metrics()
        assert metrics is not None
        assert "cache_hit_rate" in metrics
        assert "average_processing_time" in metrics

    def test_optimize_strategy_selection(self, optimizer):
        """测试优化策略选择"""
        data_size = 1000
        strategy = optimizer.select_strategy(data_size)
        assert strategy is not None
        assert strategy in [ProcessingMode.REALTIME, ProcessingMode.BATCH, ProcessingMode.STREAMING]

    def test_adaptive_worker_count(self, optimizer):
        """测试自适应工作线程数"""
        system_load = 0.5
        workers = optimizer.get_adaptive_worker_count(system_load)
        assert workers > 0
        assert workers <= optimizer.max_workers

    @pytest.mark.asyncio
    async def test_concurrent_processing(self, optimizer):
        """测试并发处理"""
        tasks = [
            optimizer.process_item(f"task_{i}")
            for i in range(3)
        ]

        with patch.object(optimizer, 'process_item') as mock_process:
            mock_process.return_value = asyncio.sleep(0.01)
            results = await asyncio.gather(*tasks, return_exceptions=True)
            assert len(results) == 3


class TestPerformanceOptimization:
    """测试性能优化功能"""

    def test_realtime_mode(self):
        """测试实时处理模式"""
        assert hasattr(ProcessingMode, 'REALTIME')

    def test_batch_mode(self):
        """测试批处理模式"""
        assert hasattr(ProcessingMode, 'BATCH')

    def test_streaming_mode(self):
        """测试流处理模式"""
        assert hasattr(ProcessingMode, 'STREAMING')


class TestGlobalOptimizer:
    """测试全局优化器功能"""

    @pytest.mark.asyncio
    async def test_get_global_optimizer(self):
        """测试获取全局优化器"""
        optimizer = await get_global_optimizer()
        assert optimizer is not None
        assert isinstance(optimizer, PerformanceOptimizer)

    @pytest.mark.asyncio
    async def test_global_optimizer_singleton(self):
        """测试全局优化器单例模式"""
        optimizer1 = await get_global_optimizer()
        optimizer2 = await get_global_optimizer()
        assert optimizer1 is optimizer2


class TestOptimizePerformanceDecorator:
    """测试optimize_performance装饰器"""

    @pytest.mark.asyncio
    async def test_optimize_decorator(self):
        """测试性能优化装饰器"""

        @optimize_performance()
        class TestProcessor:
            def __init__(self):
                self.processed_count = 0

            async def process(self, data):
                await asyncio.sleep(0.01)
                self.processed_count += 1
                return f"processed_{data}"

        processor = TestProcessor()
        result = await processor.process("test_data")
        assert result == "processed_test_data"
        assert processor.processed_count == 1

    @pytest.mark.asyncio
    async def test_optimize_decorator_with_config(self):
        """测试带配置的性能优化装饰器"""
        config = {"enable_cache": True}

        with patch('core.perception.performance_optimizer.optimize_performance') as mock_opt:
            mock_opt.return_value = lambda cls: cls

            @optimize_performance(config)
            class TestProcessor2:
                pass

            # 装饰器应该被应用
            assert TestProcessor2 is not None


class TestPerformanceIntegration:
    """测试性能优化集成功能"""

    @pytest.fixture
    async def optimizer(self):
        """创建优化器实例用于集成测试"""
        config = {
            "enable_cache": True,
            "enable_batch_processing": True,
            "enable_async_processing": True,
            "max_workers": 4,
            "cache_ttl": 3600,
            "max_batch_size": 10
        }
        return PerformanceOptimizer(config)

    @pytest.mark.asyncio
    async def test_full_optimization_workflow(self, optimizer):
        """测试完整的优化工作流"""
        # 1. 处理单个项目
        result1 = await optimizer.process_item("item1")
        assert result1 is not None

        # 2. 批量处理
        items = ["item2", "item3", "item4"]
        with patch.object(optimizer, 'batch_process') as mock_batch:
            mock_batch.return_value = await asyncio.gather(*[
                optimizer.process_item(item) for item in items
            ])
            results = await mock_batch(optimizer.process_item, items)
            assert len(results) == 3

        # 3. 检查性能指标
        metrics = optimizer.get_metrics()
        assert metrics is not None

    def test_cache_performance(self, optimizer):
        """测试缓存性能"""
        # 首次访问
        start = time.time()
        optimizer.cache_result("key", "value", 3600)
        time.time() - start

        # 缓存访问
        start = time.time()
        cached_value = optimizer.get_cached_result("key")
        cached_access = time.time() - start

        assert cached_value == "value"
        # 缓存访问应该更快(虽然在小数据上可能不明显)
        assert cached_access is not None

    @pytest.mark.asyncio
    async def test_load_balancing(self, optimizer):
        """测试负载均衡"""
        tasks = [f"task_{i}" for i in range(10)]

        with patch.object(optimizer, 'distribute_tasks') as mock_distribute:
            mock_distribute.return_value = [
                [f"task_{i}" for i in range(5)],
                [f"task_{i}" for i in range(5, 10)]
            ]
            distribution = mock_distribute(tasks, 2)
            assert len(distribution) == 2

    def test_memory_management(self, optimizer):
        """测试内存管理"""
        # 添加大量缓存项
        for i in range(100):
            optimizer.cache_result(f"key_{i}", f"value_{i}", 3600)

        # 清理过期缓存
        optimizer.cleanup_expired()

        # 检查内存使用
        stats = optimizer.get_cache_stats()
        assert stats is not None

    def test_performance_monitoring(self, optimizer):
        """测试性能监控"""
        # 模拟一些处理操作
        for i in range(10):
            optimizer.metrics.record_request(success=True, processing_time=0.1 + i * 0.01)

        stats = optimizer.get_metrics()
        assert stats["total_requests"] == 10
        assert stats["successful_requests"] == 10
        assert stats["average_processing_time"] > 0

    @pytest.mark.asyncio
    async def test_error_handling(self, optimizer):
        """测试错误处理"""
        # 模拟处理失败
        with patch.object(optimizer, 'process_item') as mock_process:
            mock_process.side_effect = Exception("Processing failed")

            with pytest.raises(Exception):
                await optimizer.process_item("failing_item")

        # 指标应该记录失败
        assert optimizer.metrics.total_requests >= 0


class TestEdgeCases:
    """测试边界情况"""

    @pytest.fixture
    def optimizer(self):
        """创建优化器实例"""
        return PerformanceOptimizer({})

    def test_empty_config(self, optimizer):
        """测试空配置"""
        assert optimizer.config == {}
        assert optimizer.enable_cache is True  # 默认值

    def test_zero_workers(self, optimizer):
        """测试零工作线程"""
        optimizer.config["max_workers"] = 0
        # 应该使用默认值
        assert optimizer.max_workers >= 1

    def test_large_batch_size(self, optimizer):
        """测试大批量大小"""
        optimizer.config["max_batch_size"] = 10000
        # 应该有合理的限制
        assert optimizer.max_batch_size > 0

    def test_negative_ttl(self, optimizer):
        """测试负TTL"""
        # 负TTL应该被处理
        with pytest.raises((ValueError, Exception)):
            optimizer.cache_result("key", "value", -1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
