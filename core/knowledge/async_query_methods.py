#!/usr/bin/env python3
from __future__ import annotations
"""
异步批量查询扩展模块
Async Batch Query Extension Module

为知识图谱添加批量异步查询能力

作者: Athena平台团队
创建时间: 2026-03-17
版本: v1.0.0
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class AsyncQueryMixin:
    """异步查询混入类"""

    async def search_patents_batch(
        self,
        queries: list[dict[str, Any]],
        limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        批量异步搜索专利

        Args:
            queries: 查询列表 [{"patent_id": str, "title": str}, ...]
            limit: 每个查询返回的结果数量

        Returns:
            搜索结果列表
        """
        tasks = [
            self.analyze_patent_context(query)
            for query in queries
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常，返回有效结果
        return [
            r if not isinstance(r, Exception) else {"error": str(r), "query": queries[i]}
            for i, r in enumerate(results)
        ]

    async def get_patent_with_relations(
        self,
        patent_id: str
    ) -> dict[str, Any]:
        """
        获取专利及其关系（异步并行）

        Args:
            patent_id: 专利ID

        Returns:
            包含专利信息和关系的字典
        """
        # 并行获取专利信息和关系
        patent_task = self._get_patent_by_id(patent_id)
        citations_task = self._get_patent_citations(patent_id)
        similar_task = self._get_similar_patents(patent_id)

        patent, citations, similar = await asyncio.gather(
            patent_task, citations_task, similar_task, return_exceptions=True
        )

        return {
            "patent": patent if not isinstance(patent, Exception) else None,
            "citations": citations if not isinstance(citations, Exception) else [],
            "similar": similar if not isinstance(similar, Exception) else [],
            "timestamp": datetime.now().isoformat()
        }

    async def _get_patent_by_id(self, patent_id: str) -> Optional[dict[str, Any]]:
        """
        根据ID获取专利（异步）

        Args:
            patent_id: 专利ID

        Returns:
            专利信息字典
        """
        try:
            # 使用现有的搜索方法
            from core.kg_unified.models.patent import NodeType
            results = await self.search_nodes(patent_id, [NodeType.PATENT], limit=1)

            if results:
                node = results[0]
                return {
                    "patent_id": node.node_id,
                    "title": node.title,
                    "description": node.description,
                    "properties": node.properties
                }
            return None
        except Exception as e:
            logger.error(f"获取专利失败: {e}")
            return None

    async def _get_patent_citations(self, patent_id: str) -> list[dict[str, Any]]:
        """
        获取专利引用关系（异步）

        Args:
            patent_id: 专利ID

        Returns:
            引用关系列表
        """
        try:
            # 使用现有方法获取关系
            from core.kg_unified.models.patent import RelationType
            relations = await self.get_node_relations(
                patent_id,
                relation_type=RelationType.CITES,
                limit=20
            )

            return [
                {
                    "source_id": rel.source_id,
                    "target_id": rel.target_id,
                    "weight": rel.weight,
                    "type": "citation"
                }
                for rel in relations
            ]
        except Exception as e:
            logger.error(f"获取引用关系失败: {e}")
            return []

    async def _get_similar_patents(self, patent_id: str) -> list[dict[str, Any]]:
        """
        获取相似专利（异步）

        Args:
            patent_id: 专利ID

        Returns:
            相似专利列表
        """
        try:
            # 使用现有方法获取相似专利
            from core.kg_unified.models.patent import RelationType
            relations = await self.get_node_relations(
                patent_id,
                relation_type=RelationType.SIMILAR_TO,
                limit=10
            )

            return [
                {
                    "patent_id": rel.target_id,
                    "similarity": rel.weight,
                    "type": "similar"
                }
                for rel in relations
            ]
        except Exception as e:
            logger.error(f"获取相似专利失败: {e}")
            return []

    async def search_technologies_batch(
        self,
        keywords_list: list[list[str]],
        limit: int = 10
    ) -> list[list[Any]]:
        """
        批量异步搜索技术节点

        Args:
            keywords_list: 关键词列表的列表
            limit: 每个查询返回的结果数量

        Returns:
            搜索结果列表的列表
        """
        from core.kg_unified.models.patent import NodeType

        tasks = [
            self.search_nodes(" ".join(keywords), [NodeType.TECHNOLOGY], limit=limit)
            for keywords in keywords_list
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        return [
            r if not isinstance(r, Exception) else []
            for r in results
        ]

    async def get_innovation_analysis(
        self,
        patent_ids: list[str]
    ) -> dict[str, Any]:
        """
        获取创新分析（批量异步）

        Args:
            patent_ids: 专利ID列表

        Returns:
            创新分析结果
        """
        # 并行分析多个专利
        tasks = [
            self.analyze_patent_context({"patent_id": pid})
            for pid in patent_ids
        ]

        analyses = await asyncio.gather(*tasks, return_exceptions=True)

        # 汇总分析
        valid_analyses = [a for a in analyses if not isinstance(a, Exception)]

        all_keywords = []
        all_technologies = []
        all_cases = []

        for analysis in valid_analyses:
            if analysis:
                all_keywords.extend(analysis.get("keywords", []))
                all_technologies.extend(analysis.get("related_technologies", []))
                all_cases.extend(analysis.get("related_cases", []))

        # 去重和统计
        from collections import Counter

        keyword_freq = Counter(all_keywords)
        tech_freq = Counter(all_technologies)
        case_freq = Counter(all_cases)

        return {
            "total_patents": len(patent_ids),
            "analyzed_patents": len(valid_analyses),
            "top_keywords": keyword_freq.most_common(10),
            "top_technologies": tech_freq.most_common(10),
            "top_cases": case_freq.most_common(5),
            "innovation_trends": {
                "emerging_techs": [t for t, _ in tech_freq.most_common(5)],
                "key_concepts": [k for k, _ in keyword_freq.most_common(5)]
            }
        }


# 导出
__all__ = ['AsyncQueryMixin']
