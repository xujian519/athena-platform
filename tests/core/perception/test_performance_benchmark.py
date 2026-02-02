#!/usr/bin/env python3
"""
感知模块性能基准测试
Perception Module Performance Benchmark Tests

测试各种感知操作的性能指标，包括：
- 处理延迟
- 吞吐量
- 内存使用
- 缓存命中率
- 并发处理能力

作者: Athena AI系统
创建时间: 2026-01-24
版本: 1.0.0
"""

import asyncio
import gc
import logging
import random
import string
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import pytest

# 导入感知模块
from core.perception import (
    PerceptionEngine,
    TextProcessor,
)
from core.perception.types import (
    CacheConfig,
    InputType,
)

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """基准测试结果"""

    test_name: str
    operations: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    p50_time: float
    p95_time: float
    p99_time: float
    throughput: float  # 操作/秒
    memory_mb: float
    timestamp: datetime = field(default_factory=datetime.now)


class PerformanceBenchmark:
    """性能基准测试类"""

    def __init__(self):
        self.results: list[BenchmarkResult] = []

    def generate_test_text(self, length: int = 1000) -> str:
        """生成测试文本"""
        words = []
        while len(" ".join(words)) < length:
            word_length = random.randint(3, 10)
            word = "".join(random.choices(string.ascii_letters + "中文测试", k=word_length))
            words.append(word)
        return " ".join(words)[:length]

    def calculate_percentiles(self, times: list[float]) -> dict[str, float]:
        """计算百分位数"""
        sorted_times = sorted(times)
        n = len(sorted_times)
        return {
            "min": sorted_times[0],
            "max": sorted_times[-1],
            "p50": sorted_times[int(n * 0.50)],
            "p95": sorted_times[int(n * 0.95)],
            "p99": sorted_times[int(n * 0.99)],
        }

    def get_memory_usage_mb(self) -> float:
        """获取内存使用量（MB）"""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024


@pytest.mark.performance
class TestTextProcessorPerformance:
    """文本处理器性能测试"""

    @pytest.fixture
    def processor(self):
        """创建测试用处理器"""
        # 同步fixture，在测试中手动初始化
        return TextProcessor(
            "benchmark_processor",
            {
                "max_text_length": 10000,
                "enable_sentiment_analysis": True,
                "enable_entity_extraction": True,
            },
        )

    @pytest.mark.asyncio
    async def test_single_text_processing_latency(self, processor):
        """测试单个文本处理延迟"""
        await processor.initialize()

        times = []
        iterations = 100

        for _ in range(iterations):
            text = "这是一个测试文本，用于测量处理延迟。"
            start = time.perf_counter()
            _result = await processor.process(text, "text")
            end = time.perf_counter()
            times.append((end - start) * 1000)  # 转换为毫秒

        await processor.cleanup()

        avg = sum(times) / len(times)
        print("\n📊 单个文本处理延迟:")
        print(f"  平均: {avg:.2f}ms")
        print(f"  最小: {min(times):.2f}ms")
        print(f"  最大: {max(times):.2f}ms")

        # 验证平均延迟在合理范围内
        assert avg < 100, f"平均延迟过高: {avg:.2f}ms"

    @pytest.mark.asyncio
    async def test_batch_processing_throughput(self, processor):
        """测试批量处理吞吐量"""
        await processor.initialize()

        batch_size = 50
        texts = [f"测试文本 {i}，包含一些内容用于性能测试。" for i in range(batch_size)]

        start = time.perf_counter()
        tasks = [processor.process(text, "text") for text in texts]
        results = await asyncio.gather(*tasks)
        end = time.perf_counter()

        await processor.cleanup()

        total_time = end - start
        throughput = batch_size / total_time

        print("\n📊 批量处理吞吐量:")
        print(f"  批次大小: {batch_size}")
        print(f"  总时间: {total_time:.2f}s")
        print(f"  吞吐量: {throughput:.2f} 文本/秒")

        assert len(results) == batch_size
        assert all(r.confidence > 0 for r in results)

    @pytest.mark.asyncio
    async def test_large_text_performance(self, processor):
        """测试大文本处理性能"""
        await processor.initialize()

        large_text = "这是一段很长的文本。" * 1000  # 约15000字符

        start = time.perf_counter()
        result = await processor.process(large_text, "text")
        end = time.perf_counter()

        processing_time = (end - start) * 1000

        await processor.cleanup()

        print("\n📊 大文本处理性能:")
        print(f"  文本长度: {len(large_text)} 字符")
        print(f"  处理时间: {processing_time:.2f}ms")
        print(f"  处理速度: {len(large_text) / processing_time:.0f} 字符/毫秒")

        assert result.confidence > 0
        assert processing_time < 500, f"大文本处理时间过长: {processing_time:.2f}ms"

    @pytest.mark.asyncio
    async def test_concurrent_processing(self, processor):
        """测试并发处理性能"""
        await processor.initialize()

        concurrent_tasks = 10
        texts_per_task = 10

        async def process_batch(task_id: int):
            """处理一批文本"""
            results = []
            for i in range(texts_per_task):
                text = f"任务{task_id} - 文本{i}，用于并发性能测试。"
                start = time.perf_counter()
                result = await processor.process(text, "text")
                end = time.perf_counter()
                results.append(
                    {
                        "task_id": task_id,
                        "text_id": i,
                        "time": (end - start) * 1000,
                        "confidence": result.confidence,
                    }
                )
            return results

        start = time.perf_counter()
        tasks = [process_batch(i) for i in range(concurrent_tasks)]
        all_results = await asyncio.gather(*tasks)
        end = time.perf_counter()

        await processor.cleanup()

        total_time = end - start
        total_operations = concurrent_tasks * texts_per_task
        throughput = total_operations / total_time

        all_times = [r["time"] for batch in all_results for r in batch]

        print("\n📊 并发处理性能:")
        print(f"  并发任务数: {concurrent_tasks}")
        print(f"  每任务处理数: {texts_per_task}")
        print(f"  总操作数: {total_operations}")
        print(f"  总时间: {total_time:.2f}s")
        print(f"  吞吐量: {throughput:.2f} 操作/秒")
        print(f"  平均延迟: {sum(all_times) / len(all_times):.2f}ms")

        assert throughput > 5, f"并发吞吐量过低: {throughput:.2f} 操作/秒"


@pytest.mark.performance
@pytest.mark.usefixtures("event_loop_policy")
class TestCachePerformance:
    """缓存性能测试"""

    @pytest.mark.asyncio
    async def test_cache_hit_rate(self):
        """测试缓存命中率"""
        from core.perception.performance_optimizer import PerformanceOptimizer

        optimizer = PerformanceOptimizer({"enable_cache": True})

        # 模拟相同的请求
        same_text = "这是一个会被缓存的测试文本。"
        cache_key = optimizer._generate_cache_key(same_text, "text", "test")

        # 首次请求 - 应该是缓存未命中
        result1 = optimizer._is_cache_valid(cache_key)
        assert not result1, "首次请求应该是缓存未命中"

        # 模拟缓存结果
        from datetime import datetime

        from core.perception import PerceptionResult

        cached_result = PerceptionResult(
            input_type=InputType.TEXT,
            raw_content=same_text,
            processed_content=same_text,
            features={"test": True},
            confidence=0.9,
            metadata={},
            timestamp=datetime.now(),
        )
        optimizer.cache[cache_key] = cached_result
        optimizer.cache_timestamps[cache_key] = datetime.now()

        # 二次请求 - 应该是缓存命中
        result2 = optimizer._is_cache_valid(cache_key)
        assert result2, "二次请求应该是缓存命中"

    @pytest.mark.asyncio
    async def test_cache_expiration(self):
        """测试缓存过期"""
        from datetime import datetime

        from core.perception.performance_optimizer import PerformanceOptimizer

        # 使用短TTL的配置
        optimizer = PerformanceOptimizer(
            {
                "enable_cache": True,
                "cache_config": {"performance_cache_ttl": timedelta(seconds=1)},  # 1秒TTL
            }
        )

        cache_key = "test_key"
        from core.perception import PerceptionResult

        cached_result = PerceptionResult(
            input_type=InputType.TEXT,
            raw_content="test",
            processed_content="test",
            features={},
            confidence=0.9,
            metadata={},
            timestamp=datetime.now(),
        )

        # 添加缓存
        optimizer.cache[cache_key] = cached_result
        optimizer.cache_timestamps[cache_key] = datetime.now()

        # 立即检查 - 应该命中
        assert optimizer._is_cache_valid(cache_key), "缓存应该立即有效"

        # 直接修改时间戳模拟过期
        optimizer.cache_timestamps[cache_key] = datetime.now() - timedelta(seconds=2)

        # 再次检查 - 应该过期
        assert not optimizer._is_cache_valid(cache_key), "缓存应该已过期"

    @pytest.mark.asyncio
    async def test_cache_size_limits(self):
        """测试缓存大小限制"""
        from datetime import datetime

        from core.perception import PerceptionResult
        from core.perception.performance_optimizer import PerformanceOptimizer

        # 配置最大缓存大小
        optimizer = PerformanceOptimizer({"enable_cache": True, "cache_ttl": 3600})

        # 添加大量缓存项
        for i in range(100):
            cache_key = f"test_key_{i}"
            result = PerceptionResult(
                input_type=InputType.TEXT,
                raw_content="x" * 100,  # 每个结果约100字节
                processed_content="x" * 100,
                features={},
                confidence=0.9,
                metadata={},
                timestamp=datetime.now(),
            )
            optimizer.cache[cache_key] = result
            optimizer.cache_timestamps[cache_key] = datetime.now()

        # 清理过期缓存
        optimizer._cleanup_expired_cache()

        # 验证缓存功能正常
        cache_size = sum(len(str(v)) for v in optimizer.cache.values())
        print("\n📊 缓存大小测试:")
        print(f"  缓存项数: {len(optimizer.cache)}")
        print(f"  缓存大小: {cache_size} 字节")

        # 验证缓存可用
        assert len(optimizer.cache) > 0, "缓存应该有内容"
        assert optimizer._is_cache_valid("test_key_0"), "缓存项应该有效"


@pytest.mark.performance
@pytest.mark.usefixtures("event_loop_policy")
class TestMemoryPerformance:
    """内存性能测试"""

    @pytest.mark.asyncio
    async def test_memory_leak_detection(self):
        """检测内存泄漏"""
        from core.perception import TextProcessor

        # 记录初始内存
        gc.collect()
        initial_memory = self._get_memory_mb()

        # 创建并使用处理器
        processor = TextProcessor("memory_test", {})
        await processor.initialize()

        # 执行大量操作
        for i in range(100):
            text = f"内存测试文本 {i}，" * 10
            _result = await processor.process(text, "text")

        # 清理
        await processor.cleanup()
        del processor

        # 强制垃圾回收
        gc.collect()
        final_memory = self._get_memory_mb()

        memory_increase = final_memory - initial_memory

        print("\n📊 内存泄漏检测:")
        print(f"  初始内存: {initial_memory:.2f}MB")
        print(f"  最终内存: {final_memory:.2f}MB")
        print(f"  内存增长: {memory_increase:.2f}MB")

        # 内存增长应小于10MB
        assert memory_increase < 10, f"可能存在内存泄漏，增长了 {memory_increase:.2f}MB"

    def _get_memory_mb(self) -> float:
        """获取当前进程内存使用量（MB）"""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024


@pytest.mark.performance
@pytest.mark.usefixtures("event_loop_policy")
class TestSemaphoreConcurrency:
    """信号量并发控制测试"""

    @pytest.mark.asyncio
    async def test_semaphore_batch_processing(self):
        """测试使用信号量的批量处理"""
        from core.perception import TextProcessor
        from core.perception.performance_optimizer import PerformanceOptimizer

        # 创建优化器，限制并发数为3
        optimizer = PerformanceOptimizer(
            {"enable_batch_processing": True, "max_workers": 3}  # 最大并发3
        )

        # 创建文本处理器
        processor = TextProcessor("semaphore_test", {})
        await processor.initialize()

        # 准备批量数据（10个文本）
        items = [
            {"data": f"测试文本 {i}，用于信号量并发测试。", "input_type": "text"} for i in range(10)
        ]

        start = time.perf_counter()
        results = await optimizer.batch_process(processor, items)
        end = time.perf_counter()

        await processor.cleanup()

        processing_time = end - start

        print("\n📊 信号量批量处理:")
        print(f"  项目数: {len(items)}")
        print("  并发限制: 3")
        print(f"  处理时间: {processing_time:.2f}s")
        print(f"  成功处理: {len(results)}")

        # 验证结果
        assert len(results) == len(items), "结果数量应该等于项目数量"
        assert all(r.confidence > 0 for r in results), "所有结果应该有效"

    @pytest.mark.asyncio
    async def test_semaphore_custom_concurrency(self):
        """测试自定义并发数"""
        from core.perception import TextProcessor
        from core.perception.performance_optimizer import PerformanceOptimizer

        optimizer = PerformanceOptimizer({"enable_batch_processing": True})
        processor = TextProcessor("custom_concurrency_test", {})
        await processor.initialize()

        items = [{"data": f"自定义并发测试 {i}", "input_type": "text"} for i in range(6)]

        # 使用不同的并发数
        for max_concurrent in [1, 2, 3]:
            start = time.perf_counter()
            results = await optimizer.batch_process(processor, items, max_concurrent=max_concurrent)
            end = time.perf_counter()

            processing_time = end - start

            print(f"\n📊 自定义并发测试 (并发数={max_concurrent}):")
            print(f"  处理时间: {processing_time:.2f}s")
            print(f"  吞吐量: {len(items) / processing_time:.2f} 项/秒")

            assert len(results) == len(items)

        await processor.cleanup()

    @pytest.mark.asyncio
    async def test_semaphore_error_handling(self):
        """测试信号量并发下的错误处理"""
        from core.perception.performance_optimizer import PerformanceOptimizer

        optimizer = PerformanceOptimizer({"enable_batch_processing": True, "max_workers": 2})

        # 创建模拟处理器
        class MockProcessor:
            def __init__(self):
                self.processor_id = "mock"
                self.initialized = True

            async def process(self, data: str, input_type: str):
                # 模拟部分请求失败
                if "fail" in data:
                    raise ValueError("模拟处理失败")
                await asyncio.sleep(0.01)
                from datetime import datetime

                from core.perception import InputType, PerceptionResult

                return PerceptionResult(
                    input_type=InputType.TEXT,
                    raw_content=data,
                    processed_content=data,
                    features={},
                    confidence=0.9,
                    metadata={},
                    timestamp=datetime.now(),
                )

        processor = MockProcessor()

        # 包含失败项目的批量数据
        items = [
            {"data": "success 1", "input_type": "text"},
            {"data": "fail item", "input_type": "text"},  # 这个会失败
            {"data": "success 2", "input_type": "text"},
            {"data": "fail another", "input_type": "text"},  # 这个会失败
            {"data": "success 3", "input_type": "text"},
        ]

        results = await optimizer.batch_process(processor, items)

        print("\n📊 错误处理测试:")
        print(f"  总项目: {len(items)}")
        print(f"  成功: {sum(1 for r in results if r.confidence > 0)}")
        print(f"  失败: {sum(1 for r in results if r.confidence == 0)}")

        # 验证所有项目都返回了结果（成功或失败）
        assert len(results) == len(items)


@pytest.mark.performance
@pytest.mark.usefixtures("event_loop_policy")
class TestCacheConfigPerformance:
    """缓存配置性能测试"""

    @pytest.mark.asyncio
    async def test_cache_config_ttl_validation(self):
        """测试缓存配置TTL验证"""
        from datetime import timedelta

        # 默认配置
        config = CacheConfig()
        assert config.ocr_cache_ttl == timedelta(days=7)
        assert config.result_cache_ttl == timedelta(days=1)
        assert config.metadata_cache_ttl == timedelta(hours=1)

        # 验证配置有效性
        assert config.validate()

        # 测试get_ttl_for_cache_type
        ocr_ttl = config.get_ttl_for_cache_type("ocr")
        assert ocr_ttl == timedelta(days=7)

        # 测试无效缓存类型
        with pytest.raises(ValueError):
            config.get_ttl_for_cache_type("invalid_type")

    @pytest.mark.asyncio
    async def test_cache_config_custom_values(self):
        """测试自定义缓存配置"""
        from datetime import timedelta

        custom_config = CacheConfig(
            ocr_cache_ttl=timedelta(hours=24),
            result_cache_ttl=timedelta(hours=12),
            metadata_cache_ttl=timedelta(minutes=30),
        )

        assert custom_config.ocr_cache_ttl == timedelta(hours=24)
        assert custom_config.result_cache_ttl == timedelta(hours=12)
        assert custom_config.metadata_cache_ttl == timedelta(minutes=30)

        # 验证自定义配置也有效
        assert custom_config.validate()


@pytest.mark.performance
@pytest.mark.usefixtures("event_loop_policy")
class TestSystemWidePerformance:
    """系统级性能测试"""

    @pytest.mark.asyncio
    async def test_end_to_end_latency(self):
        """测试端到端延迟"""

        engine = PerceptionEngine("performance_test", {"text": {"max_text_length": 10000}})
        await engine.initialize()

        times = []
        for i in range(20):
            text = f"端到端性能测试文本 {i}"
            start = time.perf_counter()
            _result = await engine.process(text, "text")
            end = time.perf_counter()
            times.append((end - start) * 1000)

        await engine.shutdown()

        avg = sum(times) / len(times)
        sorted_times = sorted(times)
        p95 = sorted_times[int(len(times) * 0.95)]

        print("\n📊 端到端延迟:")
        print(f"  平均: {avg:.2f}ms")
        print(f"  P95: {p95:.2f}ms")

        # P95延迟应小于200ms
        assert p95 < 200, f"P95延迟过高: {p95:.2f}ms"

    @pytest.mark.asyncio
    async def test_sustained_load(self):
        """测试持续负载"""

        engine = PerceptionEngine("sustained_load_test", {})
        await engine.initialize()

        duration_seconds = 5
        start_time = time.time()
        operations = 0
        errors = 0

        while time.time() - start_time < duration_seconds:
            try:
                text = f"持续负载测试文本 {operations}"
                await engine.process(text, "text")
                operations += 1
            except Exception as e:
                errors += 1
                logger.error(f"操作失败: {e}")

        await engine.shutdown()

        throughput = operations / duration_seconds
        error_rate = errors / max(operations, 1)

        print("\n📊 持续负载测试:")
        print(f"  持续时间: {duration_seconds}s")
        print(f"  总操作数: {operations}")
        print(f"  吞吐量: {throughput:.2f} 操作/秒")
        print(f"  错误率: {error_rate:.2%}")

        assert throughput > 1, f"吞吐量过低: {throughput:.2f} 操作/秒"
        assert error_rate < 0.05, f"错误率过高: {error_rate:.2%}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "-m", "performance"])
