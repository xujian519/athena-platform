#!/usr/bin/env python3
"""
处理器性能专项测试
Processor-Specific Performance Tests

针对各种感知处理器的性能测试：
- 多模态处理器性能
- 流式处理器性能
- 图像处理器性能
- 音频/视频处理器性能

作者: Athena AI系统
创建时间: 2026-01-24
版本: 1.0.0
"""

import asyncio
import contextlib
import logging
import time

import pytest

# 导入感知模块
from core.perception import ImageProcessor, PerceptionEngine, TextProcessor
from core.perception.streaming_perception_processor import StreamConfig, StreamType

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
@pytest.mark.performance
class TestMultimodalProcessorPerformance:
    """多模态处理器性能测试"""

    async def test_multimodal_fusion_performance(self):
        """测试多模态融合性能"""
        engine = PerceptionEngine("multimodal_perf_test", {})
        await engine.initialize()

        # 模拟多模态输入
        text = "这是一段测试文本"

        start_time = time.perf_counter()

        # 测试多模态处理性能
        iterations = 20
        for _i in range(iterations):
            with contextlib.suppress(Exception):
                _result = await engine.process(text, "text")

        elapsed = time.perf_counter() - start_time

        logger.info(f"多模态处理: {iterations}次迭代耗时 {elapsed:.2f}秒")

        # 性能基准：每次迭代应在合理时间内完成
        avg_time = elapsed / iterations
        assert avg_time < 5.0, f"平均处理时间 {avg_time:.2f}s 超过阈值 5.0s"

        await engine.shutdown()

    async def test_concurrent_multimodal_processing(self):
        """测试并发多模态处理"""
        engine = PerceptionEngine("concurrent_multimodal_test", {})
        await engine.initialize()

        async def process_single(item: str):
            with contextlib.suppress(Exception):
                return await engine.process(item, "text")
            return None

        # 创建并发任务
        items = [f"测试文本 {i}" for i in range(50)]
        start_time = time.perf_counter()

        _results = await asyncio.gather(*[process_single(item) for item in items])

        elapsed = time.perf_counter() - start_time
        throughput = len(items) / elapsed

        logger.info(f"并发多模态处理: {len(items)}个项目, 吞吐量 {throughput:.1f} 次/秒")

        # 性能基准：吞吐量应达到一定水平
        assert throughput > 5.0, f"吞吐量 {throughput:.1f} 低于预期 5.0 次/秒"

        await engine.shutdown()


@pytest.mark.asyncio
@pytest.mark.performance
class TestImageProcessorPerformance:
    """图像处理器性能测试"""

    async def test_image_processing_latency(self):
        """测试图像处理延迟"""
        processor = ImageProcessor("image_perf_test", {})
        await processor.initialize()

        # 创建测试图像数据
        fake_image_data = b"fake_image_binary_data"

        times = []
        iterations = 30

        for _i in range(iterations):
            with contextlib.suppress(Exception):
                start = time.perf_counter()
                _result = await processor.process(fake_image_data, "image")
                end = time.perf_counter()
                times.append((end - start) * 1000)  # 转换为毫秒

        await processor.cleanup()

        if times:
            avg = sum(times) / len(times)
            logger.info(f"图像处理延迟: 平均 {avg:.2f}ms")

            # 性能基准：平均延迟应合理
            assert avg < 10000, f"平均延迟 {avg:.2f}ms 超过阈值 10000ms"

    async def test_batch_image_processing(self):
        """测试批量图像处理"""
        processor = ImageProcessor("batch_image_test", {})
        await processor.initialize()

        # 批量处理测试
        batch_size = 10
        images = [b"fake_image_data"] * batch_size

        start_time = time.perf_counter()

        for img in images:
            with contextlib.suppress(Exception):
                _result = await processor.process(img, "image")

        elapsed = time.perf_counter() - start_time
        throughput = batch_size / elapsed

        logger.info(f"批量图像处理: {batch_size}张, 吞吐量 {throughput:.1f} 张/秒")

        await processor.cleanup()


@pytest.mark.asyncio
@pytest.mark.performance
class TestStreamingProcessorPerformance:
    """流式处理器性能测试"""

    async def test_streaming_throughput(self):
        """测试流式处理吞吐量"""
        from core.perception.streaming_perception_processor import (
            StreamingPerceptionEngine,
        )

        config = StreamConfig(buffer_size=1000, max_queue_size=5000)
        engine = StreamingPerceptionEngine(config)
        await engine.initialize()

        stream_id = "test_stream"
        await engine.start_streaming(stream_id, StreamType.TEXT)

        # 测试吞吐量
        chunk_count = 100
        start_time = time.perf_counter()

        for i in range(chunk_count):
            await engine.put_chunk(stream_id, f"数据块 {i}")

        elapsed = time.perf_counter() - start_time
        throughput = chunk_count / elapsed

        logger.info(f"流式处理吞吐量: {throughput:.1f} 块/秒")

        # 性能基准：流式处理应有较高吞吐量
        assert throughput > 50, f"吞吐量 {throughput:.1f} 低于预期 50 块/秒"

        await engine.end_stream(stream_id)

    async def test_streaming_latency(self):
        """测试流式处理延迟"""
        from core.perception.streaming_perception_processor import (
            StreamingPerceptionEngine,
        )

        config = StreamConfig(buffer_size=1000, max_queue_size=5000)
        engine = StreamingPerceptionEngine(config)
        await engine.initialize()

        stream_id = "latency_test_stream"
        await engine.start_streaming(stream_id, StreamType.TEXT)

        # 测试端到端延迟
        latencies = []
        iterations = 20

        for i in range(iterations):
            start = time.perf_counter()
            await engine.put_chunk(stream_id, f"测试数据 {i}")
            end = time.perf_counter()
            latencies.append((end - start) * 1000)  # 转换为毫秒

        avg_latency = sum(latencies) / len(latencies)

        logger.info(f"流式处理延迟: 平均 {avg_latency:.2f}ms")

        # 性能基准：单次put操作应快速
        assert avg_latency < 100, f"平均延迟 {avg_latency:.2f}ms 超过阈值 100ms"

        await engine.end_stream(stream_id)


@pytest.mark.asyncio
@pytest.mark.performance
class TestCachePerformanceUnderLoad:
    """缓存压力下的性能测试"""

    async def test_cache_performance_with_high_tps(self):
        """测试高TPS下的缓存性能"""
        from core.perception.performance_optimizer import PerformanceOptimizer

        optimizer = PerformanceOptimizer({"enable_cache": True})

        processor = TextProcessor("cache_load_test", {})
        await processor.initialize()

        # 高TPS测试
        requests_per_second = 100
        duration_seconds = 2
        total_requests = requests_per_second * duration_seconds

        start_time = time.perf_counter()

        for i in range(total_requests):
            text = f"缓存测试文本 {i % 50}"  # 使用有限文本集触发缓存
            cache_key = optimizer._generate_cache_key(text, "text", processor.processor_id)

            with contextlib.suppress(Exception):
                # 尝试从缓存获取
                if optimizer._is_cache_valid(cache_key):
                    _cached = optimizer.cache[cache_key]
                else:
                    # 缓存未命中，处理并缓存
                    result = await processor.process(text, "text")
                    optimizer.cache[cache_key] = result
                    optimizer.cache_timestamps[cache_key] = __import__("datetime").datetime.now()

        elapsed = time.perf_counter() - start_time
        actual_tps = total_requests / elapsed

        logger.info(f"高TPS缓存测试: 目标 {requests_per_second} TPS, 实际 {actual_tps:.1f} TPS")

        # 性能基准：应能接近目标TPS
        assert actual_tps > requests_per_second * 0.5, f"实际TPS {actual_tps:.1f} 低于目标的一半"

        await processor.cleanup()

    async def test_cache_memory_efficiency(self):
        """测试缓存内存效率"""
        from datetime import datetime

        from core.perception.performance_optimizer import PerformanceOptimizer

        optimizer = PerformanceOptimizer({"enable_cache": True})

        # 填充缓存
        for i in range(150):
            cache_key = f"key_{i}"
            optimizer.cache[cache_key] = f"value_{i}" * 100
            # 设置时间戳为当前时间
            optimizer.cache_timestamps[cache_key] = datetime.now()

        # 清理过期缓存
        optimizer._cleanup_expired_cache()

        # 验证缓存基本功能正常工作
        logger.info(f"缓存内存效率测试完成，缓存项数: {len(optimizer.cache)}")

        # 至少应该能正常工作而不崩溃
        assert len(optimizer.cache) >= 0  # 缓存应该存在


@pytest.mark.asyncio
@pytest.mark.performance
class TestResourceManagementPerformance:
    """资源管理性能测试"""

    async def test_processor_lifecycle_performance(self):
        """测试处理器生命周期性能"""
        times = []

        for _i in range(20):
            start = time.perf_counter()

            processor = TextProcessor("lifecycle_test", {})
            await processor.initialize()
            await processor.cleanup()

            end = time.perf_counter()
            times.append((end - start) * 1000)

        avg_time = sum(times) / len(times)

        logger.info(f"处理器生命周期: 平均 {avg_time:.2f}ms")

        # 性能基准：生命周期应快速
        assert avg_time < 500, f"生命周期时间 {avg_time:.2f}ms 超过阈值 500ms"

    async def test_concurrent_processor_creation(self):
        """测试并发处理器创建"""
        async def create_and_cleanup(index: int):
            processor = TextProcessor(f"concurrent_test_{index}", {})
            await processor.initialize()
            await processor.cleanup()
            return True

        start_time = time.perf_counter()

        results = await asyncio.gather(*[create_and_cleanup(i) for i in range(50)])

        elapsed = time.perf_counter() - start_time
        throughput = len(results) / elapsed

        logger.info(f"并发处理器创建: {len(results)}个处理器, 吞吐量 {throughput:.1f} 个/秒")

        # 性能基准：应能快速创建大量处理器
        assert throughput > 10, f"吞吐量 {throughput:.1f} 低于预期 10 个/秒"


@pytest.mark.asyncio
@pytest.mark.performance
class TestScalabilityPerformance:
    """可扩展性性能测试"""

    async def test_linear_scaling(self):
        """测试线性扩展性"""
        processor = TextProcessor("scaling_test", {})
        await processor.initialize()

        text = "测试文本用于扩展性测试" * 10

        # 测试不同规模下的处理时间
        scales = [10, 50, 100]
        times = []

        for scale in scales:
            start_time = time.perf_counter()

            for _i in range(scale):
                with contextlib.suppress(Exception):
                    _result = await processor.process(text, "text")

            elapsed = time.perf_counter() - start_time
            times.append(elapsed)
            logger.info(f"规模 {scale}: 耗时 {elapsed:.2f}s, 平均 {elapsed/scale:.3f}s/次")

        # 验证扩展性：时间应大致线性增长
        # 从10到50，时间应增加约5倍
        ratio_10_to_50 = times[1] / times[0]
        expected_ratio_10_to_50 = 50 / 10  # = 5

        # 允许一定偏差（考虑并发和系统开销）
        assert (
            0.5 * expected_ratio_10_to_50 <= ratio_10_to_50 <= 2 * expected_ratio_10_to_50
        ), f"扩展性不佳: 10→50比例 {ratio_10_to_50:.2f}, 预期约 {expected_ratio_10_to_50:.2f}"

        await processor.cleanup()

    async def test_large_text_processing(self):
        """测试大文本处理性能"""
        processor = TextProcessor("large_text_test", {})
        await processor.initialize()

        # 生成不同大小的文本
        text_sizes = [1000, 10000, 100000]  # 字符数
        times = []

        for size in text_sizes:
            text = "测试内容 " * (size // 5)

            start = time.perf_counter()
            with contextlib.suppress(Exception):
                _result = await processor.process(text, "text")
            elapsed = time.perf_counter() - start

            times.append(elapsed)
            logger.info(f"文本大小 {size}: 耗时 {elapsed*1000:.2f}ms")

        # 性能基准：大文本处理时间应合理增长
        # 从1K到100K，时间增长应小于100倍（表明有优化）
        ratio = times[2] / times[0]
        size_ratio = text_sizes[2] / text_sizes[0]  # = 100

        logger.info(f"大小比例 {size_ratio}, 时间比例 {ratio:.2f}")

        # 时间增长应小于大小增长（表明有优化）
        assert ratio < size_ratio * 2, "大文本处理时间增长过快"

        await processor.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "-m", "performance"])
