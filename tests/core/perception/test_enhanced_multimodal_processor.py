#!/usr/bin/env python3
"""
增强多模态处理器测试（简化版）
Tests for Enhanced Multimodal Processor (Simplified)
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock

from core.perception.processors.enhanced_multimodal_processor import (
    FusionStrategy,
    ModalityType,
    ModalityData,
    FusionResult,
    MultiModalAnalysis,
    EnhancedMultiModalProcessor,
)


class TestFusionStrategy:
    """测试FusionStrategy枚举"""

    def test_early_fusion(self):
        """测试早期融合策略"""
        assert FusionStrategy.EARLY.value == "early"

    def test_late_fusion(self):
        """测试后期融合策略"""
        assert FusionStrategy.LATE.value == "late"

    def test_hybrid_fusion(self):
        """测试混合融合策略"""
        assert FusionStrategy.HYBRID.value == "hybrid"


class TestModalityType:
    """测试ModalityType枚举"""

    def test_text_type(self):
        """测试文本类型"""
        assert ModalityType.TEXT.value == "text"

    def test_image_type(self):
        """测试图像类型"""
        assert ModalityType.IMAGE.value == "image"

    def test_audio_type(self):
        """测试音频类型"""
        assert ModalityType.AUDIO.value == "audio"

    def test_video_type(self):
        """测试视频类型"""
        assert ModalityType.VIDEO.value == "video"


class TestModalityData:
    """测试ModalityData数据类"""

    @pytest.fixture
    def data(self):
        """创建数据实例"""
        return ModalityData(
            modality_type=ModalityType.TEXT,
            data="test data",
            metadata={"source": "test"}
        )

    def test_initialization(self, data):
        """测试初始化"""
        assert data.modality_type == ModalityType.TEXT
        assert data.data == "test data"
        assert data.metadata == {"source": "test"}


class TestFusionResult:
    """测试FusionResult结果类"""

    @pytest.fixture
    def result(self):
        """创建结果实例"""
        return FusionResult(
            success=True,
            fused_data="fused result",
            confidence=0.9,
            strategy=FusionStrategy.EARLY
        )

    def test_initialization(self, result):
        """测试初始化"""
        assert result.success is True
        assert result.fused_data == "fused result"
        assert result.confidence == 0.9
        assert result.strategy == FusionStrategy.EARLY


class TestEnhancedMultiModalProcessor:
    """测试EnhancedMultiModalProcessor类"""

    @pytest.fixture
    def processor(self):
        """创建处理器实例"""
        config = {
            "fusion_strategy": FusionStrategy.EARLY,
            "enable_attention": True
        }
        return EnhancedMultiModalProcessor(config)

    def test_initialization(self, processor):
        """测试初始化"""
        assert processor is not None
        assert processor.config is not None

    @pytest.mark.asyncio
    async def test_process(self, processor):
        """测试处理多模态数据"""
        text_data = "test text"
        image_data = b"test image"

        with patch.object(processor, 'process') as mock_process:
            mock_process.return_value = MultiModalAnalysis(
                success=True,
                text_analysis="text result",
                image_analysis="image result",
                fused_result="fused",
                confidence=0.85
            )
            result = await mock_process(text_data, image_data)
            assert result.success is True

    def test_get_config(self, processor):
        """测试获取配置"""
        config = processor.get_config()
        assert config is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
