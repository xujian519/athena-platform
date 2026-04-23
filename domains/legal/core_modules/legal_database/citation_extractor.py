#!/usr/bin/env python3
from __future__ import annotations

"""
法律引用关系抽取器
Legal Citation Relation Extractor

从法律条款中抽取法规之间的引用关系
"""

import logging
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ExtractedCitation:
    """抽取的引用关系"""

    source_clause_id: str  # 当前条款ID
    target_norm_name: str  # 被引用的法规名称
    citation_type: str  # 引用类型:direct/indirect/article
    context: str  # 引用上下文
    confidence: float  # 置信度


class CitationExtractor:
    """法律引用关系抽取器"""

    # 直接引用完整法律的模式
    DIRECT_PATTERNS = [
        r"根据《([^》]{2,30})》",
        r"依照《([^》]{2,30})》",
        r"按照《([^》]{2,30})》",
        r"参照《([^》]{2,30})》",
        r"依据《([^》]{2,30})》",
        r"遵循《([^》]{2,30})》",
        r"执行《([^》]{2,30})》",
        r"适用《([^》]{2,30})》",
        r"援引《([^》]{2,30})》",
    ]

    # 条款内部引用模式
    ARTICLE_PATTERNS = [
        r"依照本法第([一二三四五六七八九十百千万零\d]+)条",
        r"按照本法第([一二三四五六七八九十百千万零\d]+)条",
        r"根据本法第([一二三四五六七八九十百千万零\d]+)条",
        r"遵循本法第([一二三四五六七八九十百千万零\d]+)条",
        r"本法第([一二三四五六七八九十百千万零\d]+)条.*规定",
    ]

    # 间接引用模式
    INDIRECT_PATTERNS = [
        r"([^\s《]{2,20})法[的规定]+",
        r"([^\s《]{2,20})条例[的规定]+",
        r"([^\s《]{2,20})规定[的规定]+",
        r"([^\s《]{2,20})办法[的规定]+",
        r"([^\s《]{2,20})细则[的规定]+",
    ]

    def __init__(self):
        """初始化抽取器"""
        self.stats = {
            "total_clauses": 0,
            "direct_citations": 0,
            "article_citations": 0,
            "indirect_citations": 0,
        }

    def extract_from_clause(self, clause_text: str, clause_id: str) -> list[ExtractedCitation]:
        """
        从条款中抽取引用关系

        Args:
            clause_text: 条款文本
            clause_id: 条款ID

        Returns:
            抽取的引用关系列表
        """
        self.stats["total_clauses"] += 1
        citations = []

        # 1. 抽取直接引用
        for pattern in self.DIRECT_PATTERNS:
            try:
                matches = re.finditer(pattern, clause_text)
                for match in matches:
                    norm_name = match.group(1).strip()
                    # 过滤过短或过长的匹配
                    if 2 <= len(norm_name) <= 30:
                        citations.append(
                            ExtractedCitation(
                                source_clause_id=clause_id,
                                target_norm_name=norm_name,
                                citation_type="direct",
                                context=match.group(0),
                                confidence=0.95,
                            )
                        )
                        self.stats["direct_citations"] += 1
            except Exception as e:
                logger.warning(f"⚠️  直接引用模式匹配失败: {pattern}, 错误: {e}")

        # 2. 抽取条款引用
        for pattern in self.ARTICLE_PATTERNS:
            try:
                matches = re.finditer(pattern, clause_text)
                for match in matches:
                    # 条款内部引用不创建外部引用关系
                    # 但可以记录为自引用
                    citations.append(
                        ExtractedCitation(
                            source_clause_id=clause_id,
                            target_norm_name="[同一法规]",  # 自引用标记
                            citation_type="article",
                            context=match.group(0),
                            confidence=0.90,
                        )
                    )
                    self.stats["article_citations"] += 1
            except Exception as e:
                logger.warning(f"⚠️  条款引用模式匹配失败: {pattern}, 错误: {e}")

        # 3. 抽取间接引用
        for pattern in self.INDIRECT_PATTERNS:
            try:
                matches = re.finditer(pattern, clause_text)
                for match in matches:
                    norm_name = match.group(1).strip()
                    # 过滤过短或无效的匹配
                    if 2 <= len(norm_name) <= 20:
                        citations.append(
                            ExtractedCitation(
                                source_clause_id=clause_id,
                                target_norm_name=norm_name + "法",  # 补全"法"字
                                citation_type="indirect",
                                context=match.group(0),
                                confidence=0.70,
                            )
                        )
                        self.stats["indirect_citations"] += 1
            except Exception as e:
                logger.warning(f"⚠️  间接引用模式匹配失败: {pattern}, 错误: {e}")

        return citations

    def print_stats(self) -> Any:
        """打印统计信息"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 引用关系抽取统计")
        logger.info("=" * 60)
        logger.info(f"总条款数: {self.stats['total_clauses']}")
        logger.info(f"直接引用: {self.stats['direct_citations']}条")
        logger.info(f"条款引用: {self.stats['article_citations']}条")
        logger.info(f"间接引用: {self.stats['indirect_citations']}条")
        logger.info(f"总计: {sum(v for k, v in self.stats.items() if k != 'total_clauses')}条")
        logger.info("=" * 60 + "\n")


# ========== 便捷函数 ==========


def extract_citations_from_text(text: str, clause_id: str) -> list[ExtractedCitation]:
    """
    从文本中抽取引用关系的便捷函数

    Args:
        text: 条款文本
        clause_id: 条款ID

    Returns:
        抽取的引用关系列表
    """
    extractor = CitationExtractor()
    return extractor.extract_from_clause(text, clause_id)
