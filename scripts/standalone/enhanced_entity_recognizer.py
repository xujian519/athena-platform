#!/usr/bin/env python3
from __future__ import annotations
"""
增强实体识别器
Enhanced Entity Recognizer

提供专利法律领域的增强实体识别能力
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class EntityType(Enum):
    """实体类型"""

    PATENT_NUMBER = "专利号"
    APPLICANT = "申请人"
    INVENTOR = "发明人"
    LEGAL_TERM = "法律术语"
    TECHNICAL_TERM = "技术术语"
    DATE = "日期"
    ORGANIZATION = "组织机构"
    LOCATION = "地点"
    LAW_ARTICLE = "法条"
    IPC_CLASS = "IPC分类号"


@dataclass
class RecognitionResult:
    """识别结果"""

    text: str
    entities: list[dict[str, Any]
    confidence: float
    metadata: dict[str, Any]


class EnhancedEntityRecognizer:
    """增强实体识别器"""

    def __init__(self):
        """初始化识别器"""
        # 专利号模式
        self.patterns = {
            # 中国专利号
            "patent_cn": r"(CN|ZL)\d{12}[A-Z]?",
            # PCT专利号
            "patent_pct": r"PCT/[A-Z]{2}/\d{4}/\d+",
            # 日期
            "date": r"\d{4}[-年]\d{1,2}[-月]\d{1,2}[日]?",
            # IPC分类号
            "ipc": r"[A-H]\d{2}[A-Z]\s*\d+/\d+",
            # 电话号码
            "phone": r"1[3-9]\d{9}",
            # 邮箱
            "email": r"[\w.-]+@[\w.-]+\.\w+",
        }

        # 法律术语词典
        self.legal_terms = {
            "权利要求": EntityType.LEGAL_TERM,
            "说明书": EntityType.LEGAL_TERM,
            "摘要": EntityType.LEGAL_TERM,
            "附图": EntityType.LEGAL_TERM,
            "实施例": EntityType.LEGAL_TERM,
            "创造性": EntityType.LEGAL_TERM,
            "新颖性": EntityType.LEGAL_TERM,
            "实用性": EntityType.LEGAL_TERM,
            "侵权": EntityType.LEGAL_TERM,
            "无效宣告": EntityType.LEGAL_TERM,
            "优先权": EntityType.LEGAL_TERM,
            "审查意见": EntityType.LEGAL_TERM,
            "驳回": EntityType.LEGAL_TERM,
            "授权": EntityType.LEGAL_TERM,
            "专利权": EntityType.LEGAL_TERM,
        }

        # 法条模式
        self.law_article_pattern = r"第[一二三四五六七八九十百]+条|第\d+条"

        # 技术术语
        self.technical_terms = {
            "半导体": EntityType.TECHNICAL_TERM,
            "人工智能": EntityType.TECHNICAL_TERM,
            "机器学习": EntityType.TECHNICAL_TERM,
            "深度学习": EntityType.TECHNICAL_TERM,
            "神经网络": EntityType.TECHNICAL_TERM,
            "算法": EntityType.TECHNICAL_TERM,
            "数据结构": EntityType.TECHNICAL_TERM,
            "处理器": EntityType.TECHNICAL_TERM,
            "存储器": EntityType.TECHNICAL_TERM,
            "传感器": EntityType.TECHNICAL_TERM,
        }

        logger.info("✅ 增强实体识别器初始化完成")

    def recognize(self, text: str) -> RecognitionResult:
        """识别文本中的实体"""
        if not text:
            return RecognitionResult(
                text="", entities=[], confidence=0.0, metadata={}
            )

        entities = []

        # 1. 模式匹配实体
        entities.extend(self._pattern_match(text))

        # 2. 词典匹配实体
        entities.extend(self._dict_match(text))

        # 3. 去重和排序
        entities = self._deduplicate(entities)

        # 计算置信度
        confidence = self._calculate_confidence(entities, text)

        return RecognitionResult(
            text=text,
            entities=entities,
            confidence=confidence,
            metadata={"recognizer": "enhanced", "entity_count": len(entities)},
        )

    def _pattern_match(self, text: str) -> list[dict[str, Any]:
        """模式匹配"""
        entities = []

        # 专利号
        for match in re.finditer(self.patterns["patent_cn"], text):
            entities.append(
                {
                    "text": match.group(),
                    "type": EntityType.PATENT_NUMBER.value,
                    "start": match.start(),
                    "end": match.end(),
                    "source": "pattern",
                }
            )

        # PCT专利号
        for match in re.finditer(self.patterns["patent_pct"], text):
            entities.append(
                {
                    "text": match.group(),
                    "type": EntityType.PATENT_NUMBER.value,
                    "start": match.start(),
                    "end": match.end(),
                    "source": "pattern",
                }
            )

        # 日期
        for match in re.finditer(self.patterns["date"], text):
            entities.append(
                {
                    "text": match.group(),
                    "type": EntityType.DATE.value,
                    "start": match.start(),
                    "end": match.end(),
                    "source": "pattern",
                }
            )

        # IPC分类号
        for match in re.finditer(self.patterns["ipc"], text):
            entities.append(
                {
                    "text": match.group(),
                    "type": EntityType.IPC_CLASS.value,
                    "start": match.start(),
                    "end": match.end(),
                    "source": "pattern",
                }
            )

        # 法条
        for match in re.finditer(self.law_article_pattern, text):
            entities.append(
                {
                    "text": match.group(),
                    "type": EntityType.LAW_ARTICLE.value,
                    "start": match.start(),
                    "end": match.end(),
                    "source": "pattern",
                }
            )

        return entities

    def _dict_match(self, text: str) -> list[dict[str, Any]:
        """词典匹配"""
        entities = []

        # 法律术语
        for term, entity_type in self.legal_terms.items():
            start = 0
            while True:
                pos = text.find(term, start)
                if pos == -1:
                    break
                entities.append(
                    {
                        "text": term,
                        "type": entity_type.value,
                        "start": pos,
                        "end": pos + len(term),
                        "source": "dict",
                    }
                )
                start = pos + 1

        # 技术术语
        for term, entity_type in self.technical_terms.items():
            start = 0
            while True:
                pos = text.find(term, start)
                if pos == -1:
                    break
                entities.append(
                    {
                        "text": term,
                        "type": entity_type.value,
                        "start": pos,
                        "end": pos + len(term),
                        "source": "dict",
                    }
                )
                start = pos + 1

        return entities

    def _deduplicate(self, entities: list[dict[str, Any]) -> list[dict[str, Any]:
        """去重"""
        seen = set()
        unique = []

        for entity in entities:
            key = (entity["text"], entity["type"], entity["start"])
            if key not in seen:
                seen.add(key)
                unique.append(entity)

        return sorted(unique, key=lambda x: x["start"])

    def _calculate_confidence(self, entities: list[dict[str, Any], text: str) -> float:
        """计算置信度"""
        if not entities:
            return 0.0

        # 基于实体覆盖率和类型多样性
        pattern_entities = sum(1 for e in entities if e.get("source") == "pattern")
        dict_entities = sum(1 for e in entities if e.get("source") == "dict")

        # 模式匹配实体权重更高
        confidence = min(0.95, 0.5 + 0.1 * pattern_entities + 0.05 * dict_entities)

        return confidence

    def get_entities_by_type(
        self, text: str, entity_type: EntityType
    ) -> list[dict[str, Any]:
        """按类型获取实体"""
        result = self.recognize(text)
        return [e for e in result.entities if e["type"] == entity_type.value]

    def extract_patent_numbers(self, text: str) -> list[str]:
        """提取专利号"""
        entities = self.get_entities_by_type(text, EntityType.PATENT_NUMBER)
        return [e["text"] for e in entities]

    def extract_legal_terms(self, text: str) -> list[str]:
        """提取法律术语"""
        entities = self.get_entities_by_type(text, EntityType.LEGAL_TERM)
        return [e["text"] for e in entities]


# 模块级单例
_recognizer: Optional[EnhancedEntityRecognizer] = None


def get_recognizer() -> EnhancedEntityRecognizer:
    """获取识别器单例"""
    global _recognizer
    if _recognizer is None:
        _recognizer = EnhancedEntityRecognizer()
    return _recognizer


# 导出
__all__ = [
    "EnhancedEntityRecognizer",
    "EntityType",
    "RecognitionResult",
    "get_recognizer",
]
