#!/usr/bin/env python3
from __future__ import annotations
"""
中文NLP处理器
Chinese NLP Processor

提供中文文本处理功能，包括分词、词性标注、命名实体识别等
"""

import logging
import re
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger(__name__)

# 尝试导入jieba作为底层分词器
try:
    import jieba
    import jieba.posseg as pseg

    JIEBA_AVAILABLE = True
    logger.info("✅ jieba分词器已加载")
except ImportError:
    JIEBA_AVAILABLE = False
    logger.warning("⚠️ jieba未安装，使用简单分词")


@dataclass
class ProcessResult:
    """NLP处理结果"""

    text: str
    tokens: list[str]
    pos_tags: list[tuple[str, str]
    entities: list[dict[str, Any]
    keywords: list[str]
    confidence: float
    metadata: dict[str, Any]


class ChineseNLPProcessor:
    """中文NLP处理器"""

    def __init__(self, use_jieba: bool = True):
        """初始化处理器"""
        self.use_jieba = use_jieba and JIEBA_AVAILABLE

        # 法律领域专有词汇
        self.legal_terms = {
            "专利": "n",
            "侵权": "vn",
            "无效宣告": "n",
            "权利要求": "n",
            "说明书": "n",
            "实施例": "n",
            "创造性": "n",
            "新颖性": "n",
            "实用性": "n",
            "现有技术": "n",
            "优先权": "n",
            "审查意见": "n",
        }

        # 添加法律词典
        if self.use_jieba:
            for term, tag in self.legal_terms.items():
                jieba.add_word(term, tag=tag)

        logger.info(f"✅ 中文NLP处理器初始化完成 (jieba: {self.use_jieba})")

    def process(self, text: str) -> ProcessResult:
        """处理中文文本"""
        if not text:
            return ProcessResult(
                text="",
                tokens=[],
                pos_tags=[],
                entities=[],
                keywords=[],
                confidence=0.0,
                metadata={},
            )

        # 分词
        tokens = self._tokenize(text)

        # 词性标注
        pos_tags = self._pos_tag(tokens)

        # 实体识别
        entities = self._extract_entities(text, tokens)

        # 关键词提取
        keywords = self._extract_keywords(tokens)

        return ProcessResult(
            text=text,
            tokens=tokens,
            pos_tags=pos_tags,
            entities=entities,
            keywords=keywords,
            confidence=0.85 if self.use_jieba else 0.6,
            metadata={"processor": "jieba" if self.use_jieba else "simple"},
        )

    def _tokenize(self, text: str) -> list[str]:
        """分词"""
        if self.use_jieba:
            return list(jieba.cut(text))
        else:
            # 简单分词：按标点和空格分割
            pattern = r"[，。！？、；："r"''（）【】\s]+"
            return [t for t in re.split(pattern, text) if t]

    def _pos_tag(self, tokens: list[str]) -> list[tuple[str, str]:
        """词性标注"""
        if self.use_jieba:
            text = "".join(tokens)
            return [(w, flag) for w, flag in pseg.cut(text)]
        else:
            # 简单标注
            return [(t, "x") for t in tokens]

    def _extract_entities(self, text: str, tokens: list[str]) -> list[dict[str, Any]:
        """提取命名实体"""
        entities = []

        # 专利号模式
        patent_pattern = r"CN\d{12}[A-Z]|ZL\d{12}\.\d"
        for match in re.finditer(patent_pattern, text):
            entities.append(
                {
                    "text": match.group(),
                    "type": "PATENT_NUMBER",
                    "start": match.start(),
                    "end": match.end(),
                }
            )

        # 法律术语
        for term in self.legal_terms:
            if term in text:
                entities.append(
                    {
                        "text": term,
                        "type": "LEGAL_TERM",
                        "start": text.find(term),
                        "end": text.find(term) + len(term),
                    }
                )

        return entities

    def _extract_keywords(self, tokens: list[str]) -> list[str]:
        """提取关键词"""
        # 停用词
        stopwords = {"的", "了", "是", "在", "和", "与", "或", "等", "及", "中"}

        keywords = []
        for token in tokens:
            if len(token) >= 2 and token not in stopwords:
                keywords.append(token)

        return list(set(keywords))[:20]

    def segment(self, text: str) -> list[str]:
        """分词接口"""
        return self._tokenize(text)

    def extract_keywords(self, text: str) -> list[str]:
        """提取关键词接口"""
        tokens = self._tokenize(text)
        return self._extract_keywords(tokens)


# 模块级单例
_processor: Optional[ChineseNLPProcessor] = None


def get_processor() -> ChineseNLPProcessor:
    """获取NLP处理器单例"""
    global _processor
    if _processor is None:
        _processor = ChineseNLPProcessor()
    return _processor


# 导出
__all__ = ["ChineseNLPProcessor", "ProcessResult", "get_processor"]
