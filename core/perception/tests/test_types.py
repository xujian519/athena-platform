#!/usr/bin/env python3
from __future__ import annotations
"""
测试：感知模块类型定义
Test: Perception Module Type Definitions
"""

import sys
from pathlib import Path

import pytest

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.perception.types import (
    CacheConfig,
    ConfidenceLevel,
    InputType,
    PerceptionConfig,
    PerceptionResult,
    ProcessingMode,
    StreamConfig,
    StreamType,
)


class TestInputType:
    """测试输入类型枚举"""

    def test_input_type_values(self):
        """测试输入类型值"""
        assert InputType.TEXT.value == "text"
        assert InputType.IMAGE.value == "image"
        assert InputType.AUDIO.value == "audio"
        assert InputType.VIDEO.value == "video"
        assert InputType.MULTIMODAL.value == "multimodal"

    def test_input_type_from_string(self):
        """测试从字符串创建输入类型"""
        assert InputType("text") == InputType.TEXT
        assert InputType("image") == InputType.IMAGE


class TestPerceptionResult:
    """测试感知结果类"""

    def test_create_perception_result(self):
        """测试创建感知结果"""
        from datetime import datetime
        result = PerceptionResult(
            input_type=InputType.TEXT,
            raw_content="test data",
            processed_content="processed data",
            features={"length": 9},
            confidence=0.95,
            metadata={},
            timestamp=datetime.now()
        )
        assert result.input_type == InputType.TEXT
        assert result.raw_content == "test data"
        assert result.confidence == 0.95
        assert result.features["length"] == 9

    def test_perception_result_with_features(self):
        """测试带特征的感知结果"""
        from datetime import datetime
        result = PerceptionResult(
            input_type=InputType.TEXT,
            raw_content="test",
            processed_content="processed",
            features={"lang": "zh", "length": 4},
            confidence=0.95,
            metadata={"model": "bert"},
            timestamp=datetime.now()
        )
        assert result.features["lang"] == "zh"
        assert result.metadata["model"] == "bert"


class TestPerceptionConfig:
    """测试感知配置类"""

    def test_create_config(self):
        """测试创建配置"""
        from datetime import timedelta
        config = PerceptionConfig(
            max_concurrent_documents=100,
            enable_multimodal=True,
            cache_ttl=timedelta(hours=1)
        )
        assert config.max_concurrent_documents == 100
        assert config.enable_multimodal is True
        assert config.cache_ttl == timedelta(hours=1)


class TestConfidenceLevel:
    """测试置信度级别枚举"""

    def test_confidence_levels(self):
        """测试置信度级别"""
        levels = list(ConfidenceLevel)
        assert len(levels) > 0
        # 检查有多个级别
        assert len(levels) >= 3


class TestProcessingMode:
    """测试处理模式枚举"""

    def test_processing_modes(self):
        """测试处理模式"""
        modes = list(ProcessingMode)
        assert len(modes) > 0


class TestStreamType:
    """测试流类型枚举"""

    def test_stream_types(self):
        """测试流类型"""
        types = list(StreamType)
        assert len(types) > 0


class TestStreamConfig:
    """测试流配置类"""

    def test_create_stream_config(self):
        """测试创建流配置"""
        config = StreamConfig(
            chunk_size=1024,
            buffer_size=8192,
            max_queue_size=100
        )
        assert config.chunk_size == 1024
        assert config.max_queue_size == 100
        assert config.buffer_size == 8192


class TestCacheConfig:
    """测试缓存配置类"""

    def test_create_cache_config(self):
        """测试创建缓存配置"""
        from datetime import timedelta
        config = CacheConfig(
            lru_max_size=1000,
            ocr_cache_ttl=timedelta(hours=1)
        )
        assert config.lru_max_size == 1000
        assert config.ocr_cache_ttl == timedelta(hours=1)


class TestEdgeCases:
    """测试边界情况"""

    def test_perception_result_with_minimal_fields(self):
        """测试使用最小字段创建感知结果"""
        from datetime import datetime
        result = PerceptionResult(
            input_type=InputType.TEXT,
            raw_content="test",
            processed_content="test processed",
            features={},
            confidence=0.0,
            metadata={},
            timestamp=datetime.now()
        )
        assert result.confidence == 0.0
        assert result.raw_content == "test"


class TestResultValidation:
    """测试结果验证"""

    def test_perception_result_creation(self):
        """测试创建感知结果"""
        from datetime import datetime
        result = PerceptionResult(
            input_type=InputType.TEXT,
            raw_content="test content",
            processed_content="processed",
            features={"key": "value"},
            confidence=0.95,
            metadata={"processor": "test"},
            timestamp=datetime.now()
        )
        assert result.input_type == InputType.TEXT
        assert result.raw_content == "test content"
        assert result.confidence == 0.95
        assert "key" in result.features


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
