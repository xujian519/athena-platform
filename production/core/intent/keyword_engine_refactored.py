from __future__ import annotations
"""
意图识别服务 - 重构后的关键词引擎示例

展示如何使用BaseIntentEngine和公共工具函数。

Author: Xiaonuo
Created: 2025-01-17
Version: 1.0.0
"""

import time

from core.intent.base_engine import (
    BaseIntentEngine,
    IntentCategory,
    IntentResult,
    IntentType,
)
from core.intent.exceptions import ValidationError
from core.intent.utils import EntityExtractor, KeywordMatcher, TextPreprocessor


class KeywordIntentEngine(BaseIntentEngine):
    """
    基于关键词的意图识别引擎(重构版)

    继承BaseIntentEngine,使用公共工具函数,消除代码重复。
    """

    engine_name = "keyword_engine"
    engine_version = "2.0.0"
    supported_intents = {
        IntentType.PATENT_SEARCH,
        IntentType.PATENT_ANALYSIS,
        IntentType.PATENT_DRAFTING,
        IntentType.CODE_GENERATION,
        IntentType.CODE_REVIEW,
        IntentType.GENERAL_CHAT,
    }

    def _initialize(self) -> None:
        """初始化引擎"""
        self.preprocessor = TextPreprocessor()
        self.entity_extractor = EntityExtractor()
        self.keyword_matcher = KeywordMatcher()

        # 从配置获取最大输入长度
        self.max_input_length = self.config.get("max_input_length", 10000)

        self.logger.info(f"{self.engine_name} v{self.engine_version} 初始化完成")

    def recognize_intent(self, text: str, context: dict | None = None) -> IntentResult:
        """
        识别意图(使用公共工具方法)

        Args:
            text: 输入文本
            context: 上下文信息(可选)

        Returns:
            意图识别结果
        """
        start_time = time.perf_counter()

        try:
            # 1. 验证输入(使用基类方法)
            self._validate_input(text)

            # 2. 预处理文本(使用公共工具)
            normalized_text = self._normalize_text(text)
            cleaned_text = self.preprocessor.clean_text(normalized_text)

            # 3. 检测意图(使用关键词匹配器)
            detected_intent = self._detect_intent_by_keywords(cleaned_text)

            # 4. 提取实体(使用基类方法)
            entities = self._extract_entities(cleaned_text)

            # 5. 确定类别
            category = self._determine_category(detected_intent)

            # 6. 计算置信度
            confidence = self._calculate_confidence(detected_intent, cleaned_text, entities)

            # 7. 创建结果
            processing_time = (time.perf_counter() - start_time) * 1000
            result = IntentResult(
                intent=detected_intent,
                confidence=confidence,
                entities=entities,
                category=category,
                raw_text=text,
                processing_time_ms=processing_time,
                model_version=self.engine_version,
                metadata={"method": "keyword_matching", "cleaned_text_length": len(cleaned_text)},
            )

            # 8. 更新统计信息
            self._update_stats(success=True, processing_time_ms=processing_time, cache_hit=False)

            return result

        except ValidationError:
            # 输入验证失败
            raise

        except Exception as e:
            # 其他错误
            self.logger.error(f"意图识别失败: {e}")
            processing_time = (time.perf_counter() - start_time) * 1000

            self._update_stats(success=False, processing_time_ms=processing_time, cache_hit=False)

            # 返回默认结果
            from core.intent.base_engine import create_default_result

            return create_default_result(
                text=text, processing_time_ms=processing_time, model_version=self.engine_version
            )

    def _detect_intent_by_keywords(self, text: str) -> IntentType:
        """
        使用关键词检测意图

        Args:
            text: 预处理后的文本

        Returns:
            检测到的意图类型
        """
        # 使用关键词匹配器
        detected = self.keyword_matcher.detect_intent_from_keywords(text)

        # 映射到IntentType
        intent_mapping = {
            "PATENT_SEARCH": IntentType.PATENT_SEARCH,
            "PATENT_ANALYSIS": IntentType.PATENT_ANALYSIS,
            "PATENT_DRAFTING": IntentType.PATENT_DRAFTING,
            "CODE": IntentType.CODE_GENERATION,
            "LEGAL": IntentType.LEGAL_CONSULTING,
        }

        return intent_mapping.get(detected, IntentType.GENERAL_CHAT)

    def _determine_category(self, intent: IntentType) -> IntentCategory:
        """
        确定意图类别

        Args:
            intent: 意图类型

        Returns:
            意图类别
        """
        category_mapping = {
            IntentType.PATENT_SEARCH: IntentCategory.PATENT,
            IntentType.PATENT_ANALYSIS: IntentCategory.PATENT,
            IntentType.PATENT_DRAFTING: IntentCategory.PATENT,
            IntentType.CODE_GENERATION: IntentCategory.CODE,
            IntentType.CODE_REVIEW: IntentCategory.CODE,
            IntentType.LEGAL_CONSULTING: IntentCategory.LEGAL,
        }

        return category_mapping.get(intent, IntentCategory.GENERAL)

    def _calculate_confidence(self, intent: IntentType, text: str, entities: list[str]) -> float:
        """
        计算置信度

        Args:
            intent: 检测到的意图
            text: 输入文本
            entities: 提取的实体

        Returns:
            置信度(0-1)
        """
        confidence = 0.5  # 基础置信度

        # 如果有实体,增加置信度
        if entities:
            confidence += 0.2

        # 根据文本长度调整(较短文本通常更明确)
        if len(text.split()) <= 10:
            confidence += 0.15

        # 根据关键词匹配度调整
        keyword_count = sum(
            1 for kw in self.keyword_matcher.PATENT_KEYWORDS["search"] if kw in text
        )
        confidence += min(keyword_count * 0.05, 0.15)

        return min(confidence, 0.95)  # 最高不超过0.95


# ========================================================================
# 工厂注册
# ========================================================================

from core.intent.base_engine import IntentEngineFactory

# 注册引擎
IntentEngineFactory.register("keyword", KeywordIntentEngine)


# ========================================================================
# 使用示例
# ========================================================================


def create_keyword_engine(config: dict | None = None) -> KeywordIntentEngine:
    """
    创建关键词引擎实例

    Args:
        config: 配置字典

    Returns:
        关键词引擎实例
    """
    if config is None:
        config = {"max_input_length": 10000}

    return KeywordIntentEngine(config)


if __name__ == "__main__":
    # 测试代码
    engine = create_keyword_engine()

    test_cases = [
        "帮我检索关于人工智能的专利",
        "分析这个专利的技术方案",
        "写一个快速排序算法",
        "你好,今天天气怎么样",
    ]

    for text in test_cases:
        result = engine.recognize_intent(text)
        print(f"\n输入: {text}")
        print(f"意图: {result.intent}")
        print(f"置信度: {result.confidence:.2f}")
        print(f"实体: {result.entities}")
        print(f"处理时间: {result.processing_time_ms:.2f}ms")

    # 显示统计信息
    stats = engine.get_stats()
    print("\n统计信息:")
    print(f"总请求数: {stats.total_requests}")
    print(f"成功率: {stats.successful_requests}/{stats.total_requests}")
    print(f"平均处理时间: {stats.avg_processing_time_ms:.2f}ms")
