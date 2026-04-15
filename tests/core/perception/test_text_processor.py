#!/usr/bin/env python3
"""
文本处理器单元测试
Text Processor Unit Tests
"""

import asyncio
import sys
from pathlib import Path

import pytest

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from core.perception import TextProcessor
from core.perception.types import InputType


@pytest.mark.asyncio
@pytest.mark.unit
class TestTextProcessor:
    """文本处理器测试类"""

    async def test_initialization(self):
        """测试初始化"""
        processor = TextProcessor("test_processor", {})
        assert processor.processor_id == "test_processor"
        assert not processor.initialized
        assert processor.max_text_length == 10000

    async def test_initialize(self):
        """测试启动"""
        processor = TextProcessor("test_processor", {})
        await processor.initialize()
        assert processor.initialized

    async def test_process_short_text(self):
        """测试短文本处理"""
        processor = TextProcessor("test_processor", {})
        await processor.initialize()

        result = await processor.process("测试文本", "text")

        assert result.input_type == InputType.TEXT
        assert result.confidence > 0
        assert "sentiment" in result.features
        assert "entities" in result.features
        assert "keywords" in result.features
        assert "language" in result.features

    async def test_preprocess_text(self):
        """测试文本预处理"""
        processor = TextProcessor("test_processor", {})

        # 测试字符串
        text = processor._preprocess_text("测试文本")
        assert text == "测试文本"

        # 测试字节
        text = processor._preprocess_text(b"bytes")
        assert text == "bytes"

        # 测试超长文本
        long_text = "a" * 20000
        text = processor._preprocess_text(long_text)
        assert len(text) == 10003  # 10000 + '...'
        assert text.endswith("...")

    async def test_sentiment_analysis(self):
        """测试情感分析"""
        processor = TextProcessor("test_processor", {})

        # 正面情感
        result = await processor._analyze_sentiment("这个产品很优秀，我非常喜欢！")
        assert result["sentiment"] == "positive"
        assert result["confidence"] > 0

        # 负面情感
        result = await processor._analyze_sentiment("这个产品很糟糕，我很讨厌。")
        assert result["sentiment"] == "negative"

        # 中性情感
        result = await processor._analyze_sentiment("这是一个陈述句。")
        assert result["sentiment"] == "neutral"

    async def test_entity_extraction(self):
        """测试实体提取"""
        processor = TextProcessor("test_processor", {})

        text = "联系邮箱：test@example.com，电话：138-0000-0000，日期：2024-01-15"
        entities = await processor._extract_entities(text)

        # 应该提取出邮箱、电话、日期
        entity_types = [e["type"] for e in entities]
        assert "EMAIL" in entity_types
        assert "PHONE" in entity_types
        assert "DATE" in entity_types

    async def test_keyword_extraction(self):
        """测试关键词提取"""
        processor = TextProcessor("test_processor", {})

        text = "人工智能 机器学习 深度学习 神经网络 算法 数据"
        keywords = await processor._extract_keywords(text)

        assert len(keywords) > 0
        assert "人工智能" in keywords or "机器学习" in keywords

    async def test_language_detection(self):
        """测试语言检测"""
        processor = TextProcessor("test_processor", {})

        # 中文
        lang = await processor._detect_language("这是中文文本")
        assert lang == "chinese"

        # 英文
        lang = await processor._detect_language("This is English text")
        assert lang == "english"

    async def test_stream_process(self):
        """测试流式处理"""
        processor = TextProcessor("test_processor", {})
        await processor.initialize()

        async def text_stream():
            yield "这是第一段。"
            yield "这是第二段。"
            yield "这是第三段。"

        results = []
        async for result in processor.stream_process(text_stream()):
            results.append(result)

        assert len(results) > 0

    async def test_cleanup(self):
        """测试清理"""
        processor = TextProcessor("test_processor", {})
        await processor.initialize()
        assert processor.initialized

        await processor.cleanup()
        assert not processor.initialized


@pytest.mark.asyncio
@pytest.mark.unit
class TestTextProcessorEdgeCases:
    """文本处理器边界情况测试"""

    async def test_empty_text(self):
        """测试空文本"""
        processor = TextProcessor("test_processor", {})
        await processor.initialize()

        result = await processor.process("", "text")
        assert result is not None

    async def test_special_characters(self):
        """测试特殊字符"""
        processor = TextProcessor("test_processor", {})

        special_text = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        result = processor._preprocess_text(special_text)  # 不是异步函数
        assert len(result) > 0

    async def test_mixed_language(self):
        """测试混合语言"""
        processor = TextProcessor("test_processor", {})

        mixed = "这是中文 and this is English 混合文本"
        lang = await processor._detect_language(mixed)
        assert lang in ["chinese", "english", "unknown"]

    async def test_urls_and_emails(self):
        """测试URL和邮箱"""
        processor = TextProcessor("test_processor", {})

        text = "访问 https://www.example.com 联系 support@example.com"
        entities = await processor._extract_entities(text)

        entity_types = [e["type"] for e in entities]
        assert "URL" in entity_types
        assert "EMAIL" in entity_types


@pytest.mark.asyncio
@pytest.mark.performance
class TestTextProcessorPerformance:
    """文本处理器性能测试"""

    async def test_large_text_performance(self):
        """测试大文本性能"""
        processor = TextProcessor("test_processor", {})
        await processor.initialize()

        large_text = "测试内容 " * 1000  # 约8000字

        import time

        start = time.time()
        result = await processor.process(large_text, "text")
        elapsed = time.time() - start

        assert result is not None
        assert elapsed < 5.0  # 应该在5秒内完成

    async def test_concurrent_processing(self):
        """测试并发处理"""
        processor = TextProcessor("test_processor", {})
        await processor.initialize()

        async def process_text(text):
            return await processor.process(text, "text")

        tasks = [process_text(f"测试文本 {i}") for i in range(100)]

        import time

        start = time.time()
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start

        assert len(results) == 100
        assert elapsed < 10.0  # 100个文本应在10秒内完成


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
