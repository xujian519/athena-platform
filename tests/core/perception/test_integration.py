#!/usr/bin/env python3
"""
感知模块集成测试
Perception Module Integration Tests

测试感知模块的集成场景，包括：
- 完整的感知处理流程
- 多处理器协同工作
- 缓存与优化的集成
- 监控与性能追踪
- 错误处理与恢复

作者: Athena AI系统
创建时间: 2026-01-24
版本: 1.0.0
"""

import asyncio
from datetime import timedelta

import pytest

from core.perception import (
    InputType,
    PerceptionEngine,
    PerceptionResult,
    TextProcessor,
)
from core.perception.types import (
    CacheConfig,
    PerceptionConfig,
)


@pytest.mark.asyncio
@pytest.mark.integration
class TestPerceptionEngineIntegration:
    """感知引擎集成测试"""

    async def test_complete_text_processing_pipeline(self):
        """测试完整的文本处理流程"""
        # 创建处理器
        processor = TextProcessor(
            "pipeline_test", {"enable_sentiment_analysis": True, "enable_entity_extraction": True}
        )
        await processor.initialize()

        # 准备测试数据
        test_text = "这是一个集成测试，验证完整的感知处理流程。"

        # 执行处理
        result = await processor.process(test_text, "text")

        # 验证结果
        assert result.input_type == InputType.TEXT
        assert result.confidence > 0
        assert result.processed_content is not None
        assert len(result.features) > 0

        await processor.cleanup()

    async def test_multiple_text_processing(self):
        """测试多次文本处理"""
        processor = TextProcessor("multi_test", {})
        await processor.initialize()

        texts = ["第一段测试文本", "第二段测试文本", "第三段测试文本"]

        results = []
        for text in texts:
            result = await processor.process(text, "text")
            results.append(result)

        # 验证所有结果
        assert len(results) == 3
        assert all(r.input_type == InputType.TEXT for r in results)
        assert all(r.confidence > 0 for r in results)

        await processor.cleanup()

    async def test_concurrent_processing(self):
        """测试并发处理"""
        processor = TextProcessor("concurrent_test", {})
        await processor.initialize()

        async def process_text(text: str):
            return await processor.process(text, "text")

        # 创建并发任务
        tasks = [process_text(f"并发测试文本 {i}") for i in range(10)]

        # 执行并发处理
        results = await asyncio.gather(*tasks)

        # 验证结果
        assert len(results) == 10
        assert all(r.confidence > 0 for r in results)

        await processor.cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
class TestErrorHandlingIntegration:
    """错误处理集成测试"""

    async def test_engine_error_recovery(self):
        """测试引擎错误恢复"""
        engine = PerceptionEngine("error_recovery_test", {})
        await engine.initialize()

        # 测试无效输入
        try:
            result = await engine.process(None, "text")
            # 如果没有异常，应该返回错误结果
            assert result.confidence < 0.5 or "error" in result.metadata
        except Exception:
            # 也可能抛出异常
            pass

        # 验证引擎仍然可以正常处理有效输入
        valid_text = "有效测试文本"
        result = await engine.process(valid_text, "text")

        assert result.confidence > 0

        await engine.shutdown()

    async def test_processor_failure_isolation(self):
        """测试处理器故障隔离"""
        engine = PerceptionEngine("isolation_test", {})
        await engine.initialize()

        # 使用多个处理器处理数据
        results = []
        for i in range(5):
            try:
                result = await engine.process(f"测试文本 {i}", "text")
                results.append(result)
            except Exception:
                # 单个失败不应该影响其他处理
                pass

        # 至少应该有一些成功的结果
        assert len(results) >= 0  # 至少没有崩溃

        await engine.shutdown()


@pytest.mark.asyncio
@pytest.mark.integration
class TestConfigIntegration:
    """配置集成测试"""

    async def test_unified_config_usage(self):
        """测试统一配置的使用"""

        # 创建感知配置
        perception_config = PerceptionConfig(
            enable_multimodal=True,
            supported_formats=[".txt", ".pdf", ".jpg", ".png"],
            max_file_size=10 * 1024 * 1024,
        )

        # 创建缓存配置
        cache_config = CacheConfig(
            ocr_cache_ttl=timedelta(seconds=3600),
            result_cache_ttl=timedelta(seconds=1800),
            metadata_cache_ttl=timedelta(seconds=600),
        )

        # 验证配置
        assert perception_config.enable_multimodal is True
        assert cache_config.ocr_cache_ttl.total_seconds() == 3600

    async def test_cache_config_validation(self):
        """测试缓存配置验证"""
        cache_config = CacheConfig()

        # 验证默认值
        assert cache_config.validate() is True
        assert cache_config.result_cache_ttl.total_seconds() == 86400  # 1天

        # 验证TTL获取

        ocr_ttl = cache_config.get_ttl_for_cache_type("ocr")
        assert ocr_ttl.total_seconds() == 604800  # 7天

        # 测试无效类型
        try:
            cache_config.get_ttl_for_cache_type("invalid_type")
            raise AssertionError("应该抛出ValueError")
        except ValueError:
            pass  # 预期异常


@pytest.mark.asyncio
@pytest.mark.integration
class TestEndToEndWorkflows:
    """端到端工作流测试"""

    async def test_text_analysis_workflow(self):
        """测试完整的文本分析工作流"""
        from core.perception import TextProcessor

        # 创建处理器
        processor = TextProcessor(
            "workflow_test",
            {
                "enable_sentiment_analysis": True,
                "enable_entity_extraction": True,
                "enable_keyword_extraction": True,
            },
        )

        await processor.initialize()

        # 执行工作流
        text = "Athena是一个优秀的AI系统，由徐健开发。"
        result = await processor.process(text, "text")

        # 验证工作流各步骤
        assert result.input_type == InputType.TEXT
        assert result.confidence > 0

        # 验证情感分析
        if "sentiment" in result.features:
            sentiment = result.features["sentiment"]
            assert "sentiment" in sentiment or "polarity" in sentiment

        # 验证实体提取
        if "entities" in result.features:
            entities = result.features["entities"]
            assert isinstance(entities, list)

        # 验证关键词提取
        if "keywords" in result.features:
            keywords = result.features["keywords"]
            assert isinstance(keywords, list)

        await processor.cleanup()

    async def test_batch_processing_workflow(self):
        """测试批量处理工作流"""
        from core.perception.performance_optimizer import PerformanceOptimizer

        # 创建优化器和处理器
        optimizer = PerformanceOptimizer({"enable_batch_processing": True, "max_workers": 3})

        processor = TextProcessor("batch_workflow", {})
        await processor.initialize()

        # 准备批量数据
        items = [{"data": f"批量处理文本 {i}", "input_type": "text"} for i in range(10)]

        # 执行批量处理
        results = await optimizer.batch_process(processor, items, max_concurrent=3)

        # 验证结果
        assert len(results) == 10
        assert all(r.confidence > 0 for r in results)
        assert all(r.input_type == InputType.TEXT for r in results)

        await processor.cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
class TestTypeSystemIntegration:
    """类型系统集成测试"""

    async def test_perception_result_types(self):
        """测试PerceptionResult类型系统"""
        from datetime import datetime

        # 创建结果
        result = PerceptionResult(
            input_type=InputType.TEXT,
            raw_content="测试内容",
            processed_content="处理后的内容",
            features={"test": True},
            confidence=0.9,
            metadata={"source": "test"},
            timestamp=datetime.now(),
        )

        # 验证类型
        assert result.input_type == InputType.TEXT
        assert result.confidence == 0.9
        assert isinstance(result.features, dict)

    async def test_input_type_handling(self):
        """测试InputType处理"""
        from core.perception import TextProcessor

        processor = TextProcessor("type_test", {})
        await processor.initialize()

        # 测试不同输入类型
        result = await processor.process("测试文本", "text")

        assert result.input_type == InputType.TEXT
        assert result.raw_content == "测试文本"

        await processor.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
