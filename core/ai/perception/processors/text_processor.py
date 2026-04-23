#!/usr/bin/env python3

"""
文本处理器
Text Processor

负责文本输入的感知和处理,包括语义理解、情感分析、实体识别等功能。

作者: Athena AI系统
创建时间: 2025-12-04
版本: 3.0.0
"""

import logging
import re
from datetime import datetime
from typing import Any, Optional

from .. import BaseProcessor, InputType, PerceptionResult

logger = logging.getLogger(__name__)


class TextProcessor(BaseProcessor):
    """文本处理器"""

    def __init__(self, processor_id: str, config: Optional[dict[str, Any]] = None):
        super().__init__(processor_id, config)

        # 配置参数
        self.max_text_length = config.get("max_text_length", 10000)
        self.enable_sentiment_analysis = config.get("enable_sentiment_analysis", True)
        self.enable_entity_extraction = config.get("enable_entity_extraction", True)
        self.enable_keyword_extraction = config.get("enable_keyword_extraction", True)
        self.language_detection = config.get("language_detection", True)

        logger.info(f"📝 文本处理器初始化: {processor_id}")

    async def initialize(self):
        """初始化文本处理器"""
        if self.initialized:
            return

        logger.info(f"🚀 启动文本处理器: {self.processor_id}")

        try:
            # 加载语言模型和NLP工具
            await self._load_nlp_models()

            self.initialized = True
            logger.info(f"✅ 文本处理器启动完成: {self.processor_id}")

        except Exception as e:
            logger.error(f"❌ 文本处理器启动失败 {self.processor_id}: {e}")
            raise

    async def _load_nlp_models(self):
        """加载NLP模型"""
        # 这里应该加载实际的NLP模型
        # 为了演示,使用简化的实现
        logger.debug("加载NLP模型(简化版本)")

    async def process(self, data: Any, input_type: str) -> PerceptionResult:
        """处理文本输入"""
        try:
            # 预处理文本
            text = self._preprocess_text(data)

            # 基础分析
            basic_features = await self._analyze_basic_features(text)

            # 情感分析
            sentiment_result = {}
            if self.enable_sentiment_analysis:
                sentiment_result = await self._analyze_sentiment(text)

            # 实体提取
            entities = []
            if self.enable_entity_extraction:
                entities = await self._extract_entities(text)

            # 关键词提取
            keywords = []
            if self.enable_keyword_extraction:
                keywords = await self._extract_keywords(text)

            # 语言检测
            language = "unknown"
            if self.language_detection:
                language = await self._detect_language(text)

            # 构建特征字典
            features = {
                "basic_features": basic_features,
                "sentiment": sentiment_result,
                "entities": entities,
                "keywords": keywords,
                "language": language,
                "text_statistics": self._calculate_text_statistics(text),
            }

            # 构建处理结果
            result = PerceptionResult(
                input_type=InputType.TEXT,
                raw_content=data,
                processed_content=text,
                features=features,
                confidence=self._calculate_confidence(features),
                metadata={
                    "processor_id": self.processor_id,
                    "processing_time": None,  # 实际应该记录处理时间
                    "text_length": len(text),
                    "word_count": len(text.split()),
                },
                timestamp=datetime.now(),
            )

            # 触发回调
            await self.trigger_callbacks(
                "text_processed",
                {
                    "text_length": len(text),
                    "language": language,
                    "sentiment": sentiment_result.get("sentiment", "neutral"),
                },
            )

            return result

        except Exception as e:
            logger.error(f"❌ 文本处理失败 {self.processor_id}: {e}")
            raise

    def _preprocess_text(self, data: Any) -> str:
        """预处理文本"""
        if isinstance(data, str):
            text = data
        elif isinstance(data, bytes):
            text = data.decode("utf-8", errors="ignore")
        else:
            text = str(data)

        # 清理文本
        text = text.strip()

        # 限制长度
        if len(text) > self.max_text_length:
            text = text[: self.max_text_length] + "..."
            logger.warning(f"文本长度超过限制,已截断: {len(text)} -> {self.max_text_length}")

        return text

    async def _analyze_basic_features(self, text: str) -> dict[str, Any]:
        """分析基础特征"""
        return {
            "length": len(text),
            "word_count": len(text.split()),
            "sentence_count": len(re.split(r"[.!?]+", text)),
            "paragraph_count": len(re.split(r"\n\n+", text)),
            "uppercase_ratio": sum(1 for c in text if c.isupper()) / max(len(text), 1),
            "digit_ratio": sum(1 for c in text if c.isdigit()) / max(len(text), 1),
            "special_char_ratio": sum(1 for c in text if not c.isalnum() and not c.isspace())
            / max(len(text), 1),
            "has_urls": bool(
                re.search(
                    r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
                    text,
                )
            ),
            "has_emails": bool(
                re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text)
            ),
        }

    async def _analyze_sentiment(self, text: str) -> dict[str, Any]:
        """情感分析(简化版本)"""
        # 简化的情感词典
        positive_words = ["好", "棒", "优秀", "喜欢", "爱", "开心", "快乐", "幸福", "成功", "完美"]
        negative_words = ["坏", "差", "糟糕", "讨厌", "恨", "难过", "痛苦", "失败", "问题", "错误"]

        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)

        if positive_count > negative_count:
            sentiment = "positive"
            confidence = min(
                0.9, (positive_count - negative_count) / max(positive_count + negative_count, 1)
            )
        elif negative_count > positive_count:
            sentiment = "negative"
            confidence = min(
                0.9, (negative_count - positive_count) / max(positive_count + negative_count, 1)
            )
        else:
            sentiment = "neutral"
            confidence = 0.5

        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "positive_score": positive_count,
            "negative_score": negative_count,
            "neutral_score": max(0, len(text.split()) - positive_count - negative_count),
        }

    async def _extract_entities(self, text: str) -> list[dict[str, Any]]:
        """实体提取(简化版本)"""
        entities = []

        # 简化的实体识别规则
        # 日期
        date_pattern = r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b"
        for match in re.finditer(date_pattern, text):
            entities.append(
                {"text": match.group(), "type": "DATE", "start": match.start(), "end": match.end()}
            )

        # 邮箱
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        for match in re.finditer(email_pattern, text):
            entities.append(
                {"text": match.group(), "type": "EMAIL", "start": match.start(), "end": match.end()}
            )

        # 电话号码(支持中国和美国格式)
        phone_patterns = [
            r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",  # 美国格式: 123-456-7890
            r"\b1[3-9]\d{1}-\d{4}-\d{4}\b",  # 中国格式带分隔符: 138-0000-0000
            r"\b1[3-9]\d{9}\b",  # 中国格式无分隔符: 13800000000
        ]
        for phone_pattern in phone_patterns:
            for match in re.finditer(phone_pattern, text):
                entities.append(
                    {
                        "text": match.group(),
                        "type": "PHONE",
                        "start": match.start(),
                        "end": match.end(),
                    }
                )

        # URL
        url_pattern = (
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
        )
        for match in re.finditer(url_pattern, text):
            entities.append(
                {"text": match.group(), "type": "URL", "start": match.start(), "end": match.end()}
            )

        return entities

    async def _extract_keywords(self, text: str) -> list[str]:
        """关键词提取(简化版本)"""
        # 移除标点符号并分词
        words = re.findall(r"\b\w+\b", text.lower())

        # 过滤停用词(简化版本)
        stop_words = {
            "的",
            "了",
            "在",
            "是",
            "我",
            "有",
            "和",
            "就",
            "不",
            "人",
            "都",
            "一",
            "一个",
            "上",
            "也",
            "很",
            "到",
            "说",
            "要",
            "去",
            "你",
            "会",
            "着",
            "没有",
            "看",
            "好",
            "自己",
            "这",
        }

        filtered_words = [word for word in words if word not in stop_words and len(word) > 1]

        # 词频统计
        word_freq = {}
        for word in filtered_words:
            word_freq[word] = word_freq.get(word, 0) + 1

        # 返回频率最高的关键词
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        keywords = [word for word, freq in sorted_words[:10]

        return keywords

    async def _detect_language(self, text: str) -> str:
        """语言检测(简化版本)"""
        # 简化的语言检测规则
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
        english_chars = len(re.findall(r"[a-zA-Z]", text))

        if chinese_chars > english_chars:
            return "chinese"
        elif english_chars > 0:
            return "english"
        else:
            return "unknown"

    def _calculate_text_statistics(self, text: str) -> dict[str, Any]:
        """计算文本统计"""
        words = text.split()

        if len(words) == 0:
            return {"avg_word_length": 0}

        word_lengths = [len(word) for word in words]

        return {
            "avg_word_length": sum(word_lengths) / len(word_lengths),
            "max_word_length": max(word_lengths) if word_lengths else 0,
            "min_word_length": min(word_lengths) if word_lengths else 0,
            "char_count": len(text),
            "char_count_no_spaces": len(text.replace(" ", "")),
            "punctuation_count": sum(1 for c in text if not c.isalnum() and not c.isspace()),
        }

    def _calculate_confidence(self, features: dict[str, Any]) -> float:
        """计算处理置信度"""
        confidence = 0.8  # 基础置信度

        # 根据特征质量调整置信度
        if features.get("sentiment", {}).get("confidence", 0):
            confidence += 0.1

        if len(features.get("entities", [])) > 0:
            confidence += 0.05

        if len(features.get("keywords", [])) > 5:
            confidence += 0.05

        return min(1.0, confidence)

    async def stream_process(self, text_stream):
        """流式文本处理"""
        buffer = ""

        async for chunk in text_stream:
            buffer += chunk

            # 当缓冲区达到一定长度时处理
            if len(buffer) >= 1000:
                yield await self.process(buffer, "text")
                buffer = ""

        # 处理剩余内容
        if buffer:
            yield await self.process(buffer, "text")

    async def cleanup(self):
        """清理处理器"""
        logger.info(f"🧹 清理文本处理器: {self.processor_id}")
        self.initialized = False


__all__ = ["TextProcessor"]

