#!/usr/bin/env python3
"""
结构化感知引擎 - 兼容性实现
Structured Perception Engine - Compatibility Implementation

⚠️ DEPRECATED - 此模块已被弃用

弃用时间: 2026-01-25
弃用原因: 功能已整合到 `unified_optimized_processor.py`
迁移指南: 请使用 `core.perception.UnifiedOptimizedProcessor` 替代

新模块提供:
- 统一的结构化感知接口
- 更好的类型安全
- 更完善的文档处理
- 更强的扩展性

此文件保留用于向后兼容,但将在未来版本中移除。

---

为优化后的系统提供结构化感知功能的兼容性接口
作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import warnings

# 发出弃用警告
warnings.warn(
    "structured_perception_engine.py 已被弃用,请使用 unified_optimized_processor.py。"
    "此模块将在未来版本中移除。",
    DeprecationWarning,
    stacklevel=2,
)

import logging
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class PerceptionType(Enum):
    """感知类型"""

    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"


class StructuredPerceptionEngine:
    """结构化感知引擎"""

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.ocr_processor = None
        self.nlp_processor = None
        self.image_analyzer = None
        self.initialized = False

    async def initialize(self):
        """初始化感知引擎"""
        if self.initialized:
            return

        try:
            # 初始化OCR处理器
            from core.perception.optimized_perception_module import (
                OptimizedPerceptionModule,
            )

            self.ocr_processor = OptimizedPerceptionModule("perception_engine", self.config)
            await self.ocr_processor.initialize()

            # 初始化NLP处理器
            self.nlp_processor = await self._create_nlp_processor()

            self.initialized = True
            logger.info("✅ 结构化感知引擎初始化完成")

        except Exception as e:
            logger.error(f"❌ 结构化感知引擎初始化失败: {e}")
            raise

    async def _create_nlp_processor(self):
        """创建NLP处理器"""
        try:
            # 尝试导入现有的NLP适配器
            from core.nlp.enhanced_nlp_adapter import EnhancedNLPAdapter

            nlp = EnhancedNLPAdapter(self.config.get("nlp", {}))
            await nlp.initialize()
            return nlp
        except Exception:
            # 创建简单的NLP处理器
            return SimpleNLPProcessor()

    async def perceive(
        self, input_data: Any, perception_type: PerceptionType = PerceptionType.TEXT, **kwargs
    ) -> dict[str, Any]:
        """
        结构化感知输入

        Args:
            input_data: 输入数据
            perception_type: 感知类型
            **kwargs: 其他参数

        Returns:
            感知结果字典
        """
        if not self.initialized:
            await self.initialize()

        try:
            # 根据类型选择处理方式
            if perception_type == PerceptionType.TEXT:
                return await self._process_text(input_data, **kwargs)
            elif perception_type == PerceptionType.IMAGE:
                return await self._process_image(input_data, **kwargs)
            elif perception_type == PerceptionType.DOCUMENT:
                return await self._process_document(input_data, **kwargs)
            elif perception_type == PerceptionType.AUDIO:
                return await self._process_audio(input_data, **kwargs)
            else:
                raise ValueError(f"不支持的感知类型: {perception_type}")

        except Exception as e:
            logger.error(f"感知处理失败: {perception_type} - {e}")
            return {
                "success": False,
                "error": str(e),
                "perception_type": perception_type.value,
                "timestamp": datetime.now().isoformat(),
            }

    async def _process_text(self, text: str, **kwargs) -> dict[str, Any]:
        """处理文本输入"""
        try:
            # NLP处理
            if self.nlp_processor:
                nlp_result = await self.nlp_processor.process_text(text)
            else:
                nlp_result = {"text": text, "tokens": text.split()}

            # 结构化结果
            return {
                "success": True,
                "perception_type": PerceptionType.TEXT.value,
                "input": text,
                "nlp_analysis": nlp_result,
                "structured_output": {
                    "text_length": len(text),
                    "word_count": len(text.split()),
                    "language": self._detect_language(text),
                    "sentiment": self._analyze_sentiment(text),
                    "entities": nlp_result.get("entities", []),
                    "keywords": nlp_result.get("keywords", []),
                },
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"文本处理失败: {e}")
            raise

    async def _process_image(self, image_data: Any, **kwargs) -> dict[str, Any]:
        """处理图像输入"""
        try:
            # 简化的图像处理
            return {
                "success": True,
                "perception_type": PerceptionType.IMAGE.value,
                "input_type": type(image_data).__name__,
                "structured_output": {
                    "format": self._detect_image_format(image_data),
                    "size": self._get_image_size(image_data),
                    "features": self._extract_image_features(image_data),
                    "objects": [],  # 需要实际的对象检测
                    "scene": "unknown",
                },
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"图像处理失败: {e}")
            raise

    async def _process_document(self, document_data: Any, **kwargs) -> dict[str, Any]:
        """处理文档输入"""
        try:
            # 使用优化后的OCR处理器
            ocr_result = await self.ocr_processor.process_document(document_data)

            return {
                "success": True,
                "perception_type": PerceptionType.DOCUMENT.value,
                "structured_output": {
                    "document_type": kwargs.get("doc_type", "unknown"),
                    "page_count": ocr_result.get("page_count", 1),
                    "text_content": ocr_result.get("text", ""),
                    "structure": ocr_result.get("structure", {}),
                    "confidence": ocr_result.get("confidence", 0.0),
                },
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"文档处理失败: {e}")
            raise

    async def _process_audio(self, audio_data: Any, **kwargs) -> dict[str, Any]:
        """处理音频输入"""
        try:
            # 简化的音频处理
            return {
                "success": True,
                "perception_type": PerceptionType.AUDIO.value,
                "input_type": type(audio_data).__name__,
                "structured_output": {
                    "duration": 0.0,
                    "format": "unknown",
                    "sample_rate": 44100,
                    "channels": 1,
                    "transcript": "",  # 需要语音识别
                    "features": [],
                },
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"音频处理失败: {e}")
            raise

    def _detect_language(self, text: str) -> str:
        """检测语言"""
        # 简化的语言检测
        if any(ord(char) > 127 for char in text):
            return "zh"
        else:
            return "en"

    def _analyze_sentiment(self, text: str) -> str:
        """分析情感"""
        # 简化的情感分析
        positive_words = ["good", "great", "excellent", "好", "优秀", "很好"]
        negative_words = ["bad", "poor", "terrible", "差", "糟糕", "不好"]

        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"

    def _detect_image_format(self, image_data: Any) -> str:
        """检测图像格式"""
        # 简化实现
        if hasattr(image_data, "format"):
            return image_data.format.lower()
        else:
            return "unknown"

    def _get_image_size(self, image_data: Any) -> dict[str, int]:
        """获取图像尺寸"""
        # 简化实现
        if hasattr(image_data, "size"):
            width, height = image_data.size
            return {"width": width, "height": height}
        else:
            return {"width": 0, "height": 0}

    def _extract_image_features(self, image_data: Any) -> list[str]:
        """提取图像特征"""
        # 简化实现
        return ["color_histogram", "edge_detection", "texture_features"]


class SimpleNLPProcessor:
    """简单NLP处理器"""

    async def process_text(self, text: str) -> dict[str, Any]:
        """处理文本"""
        return {
            "text": text,
            "tokens": text.split(),
            "entities": [],
            "keywords": self._extract_keywords(text),
            "pos_tags": [(word, "NN") for word in text.split()],
        }

    def _extract_keywords(self, text: str) -> list[str]:
        """提取关键词"""
        # 简化的关键词提取
        words = text.lower().split()
        # 过滤停用词
        stop_words = {"the", "a", "an", "and", "or", "but", "的", "了", "在", "是"}
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        return keywords[:10]  # 返回前10个关键词


# 兼容性函数
def create_structured_perception_engine(
    config: Optional[dict[str, Any]] = None,
) -> StructuredPerceptionEngine:
    """创建结构化感知引擎实例"""
    return StructuredPerceptionEngine(config)
