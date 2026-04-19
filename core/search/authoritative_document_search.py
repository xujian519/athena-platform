#!/usr/bin/env python3
from __future__ import annotations
"""
权威文档检索系统
Authoritative Document Search System

整合向量搜索、知识图谱扩展和BGE Reranker的四阶段检索架构
作者: Athena AI Team
创建时间: 2026-01-19
版本: v1.0.0
"""

import logging
import time
from dataclasses import dataclass
from typing import Any

from core.reranking.authoritative_document_reranker import (
    AuthoritativeDocumentReranker,
    get_authoritative_reranker,
)

logger = logging.getLogger(__name__)


@dataclass
class SearchConfig:
    """检索配置"""

    # L1: 向量检索
    l1_top_k: int = 100  # 向量检索召回数量

    # L2: 知识图谱扩展
    l2_enable: bool = True  # 是否启用知识图谱扩展
    l2_expansion_factor: float = 1.5  # 扩展因子

    # L3: Rerank精排
    l3_top_k: int = 20  # Rerank后保留数量

    # L4: 最终结果
    l4_top_k: int = 10  # 最终返回数量


@dataclass
class SearchResult:
    """检索结果"""

    query: str
    total_candidates: int
    l1_count: int
    l2_count: int
    l3_count: int
    l4_count: int
    results: list[dict[str, Any]]
    latency_ms: float
    stage_latencies: dict[str, float]


class AuthoritativeDocumentSearch:
    """权威文档检索系统"""

    def __init__(
        self,
        reranker: AuthoritativeDocumentReranker | None = None,
        config: SearchConfig | None = None,
    ):
        """
        初始化检索系统

        Args:
            reranker: 权威文档重排序引擎
            config: 检索配置
        """
        self.config = config or SearchConfig()
        self.reranker = reranker or get_authoritative_reranker()

        logger.info("✅ 权威文档检索系统初始化完成")
        logger.info(f"   L1 Top-K: {self.config.l1_top_k}")
        logger.info(f"   L2 扩展: {'启用' if self.config.l2_enable else '禁用'}")
        logger.info(f"   L3 Top-K: {self.config.l3_top_k}")
        logger.info(f"   L4 Top-K: {self.config.l4_top_k}")

    def search(
        self, query: str, db_connection: Any | None = None, kg_connection: Any | None = None
    ) -> SearchResult:
        """
        执行四阶段检索

        Args:
            query: 用户查询
            db_connection: 数据库连接 (PostgreSQL)
            kg_connection: 知识图谱连接 (NebulaGraph)

        Returns:
            SearchResult: 检索结果
        """
        start_time = time.time()
        stage_latencies = {}

        logger.info(f"🔍 开始检索: {query[:50]}...")

        # ===== L1: 向量粗排 =====
        l1_start = time.time()
        l1_results = self._l1_vector_search(query, db_connection)
        stage_latencies["l1"] = (time.time() - l1_start) * 1000

        logger.info(f"   L1向量检索: {len(l1_results)} 候选 ({stage_latencies['l1']:.1f}ms)")

        if not l1_results:
            return self._empty_result(query, time.time() - start_time)

        # ===== L2: 知识图谱扩展 =====
        l2_start = time.time()
        if self.config.l2_enable and kg_connection:
            l2_results = self._l2_kg_expansion(query, l1_results, kg_connection)
        else:
            l2_results = l1_results
        stage_latencies["l2"] = (time.time() - l2_start) * 1000

        logger.info(f"   L2知识图谱扩展: {len(l2_results)} 候选 ({stage_latencies['l2']:.1f}ms)")

        # ===== L3: Rerank精排 =====
        l3_start = time.time()
        l3_results = self._l3_rerank(query, l2_results)
        stage_latencies["l3"] = (time.time() - l3_start) * 1000

        logger.info(f"   L3 Rerank精排: {len(l3_results)} 候选 ({stage_latencies['l3']:.1f}ms)")

        # ===== L4: 最终Top-K =====
        l4_results = l3_results[: self.config.l4_top_k]

        total_time = (time.time() - start_time) * 1000

        result = SearchResult(
            query=query,
            total_candidates=len(l2_results),
            l1_count=len(l1_results),
            l2_count=len(l2_results),
            l3_count=len(l3_results),
            l4_count=len(l4_results),
            results=l4_results,
            latency_ms=total_time,
            stage_latencies=stage_latencies,
        )

        logger.info(f"✅ 检索完成: 返回{len(l4_results)}结果 (总耗时: {total_time:.1f}ms)")

        return result

    def _l1_vector_search(self, query: str, db_connection: Any,) -> list[dict[str, Any]]:
        """
        L1: 向量粗排

        使用PostgreSQL + pgvector进行向量相似度检索
        """
        if db_connection is None:
            logger.warning("   数据库连接未提供,返回空结果")
            return []

        try:
            # 生成查询向量 (这里简化,实际应使用embedding模型)
            # query_embedding = get_embedding(query)

            # 执行向量相似度搜索

            # 这里简化实现,实际需要:
            # 1. 生成查询向量
            # 2. 执行向量搜索SQL
            # 3. 返回结果

            logger.warning("   向量搜索需要实际的embedding实现")
            return []

        except Exception as e:
            logger.error(f"   L1向量检索失败: {e}")
            return []

    def _l2_kg_expansion(
        self, query: str, l1_results: list[dict[str, Any]], kg_connection: Any,
    ) -> list[dict[str, Any]]:
        """
        L2: 知识图谱扩展

        利用引用关系扩展候选文档
        """
        if kg_connection is None:
            return l1_results

        try:
            # 提取L1结果的article_id
            [doc.get("article_id") for doc in l1_results]

            # 通过知识图谱查询引用关系
            # 简化实现: 添加被引用的文档
            expanded_results = list(l1_results)

            for doc in l1_results:
                metadata = doc.get("metadata", {}) or {}
                references = metadata.get("references", [])

                # 这里应该从知识图谱或数据库查询引用的文档
                # 简化实现: 假设我们添加了引用文档
                for _ref_id in references:
                    # 查询引用文档并添加到结果
                    # ref_doc = query_document_by_id(ref_id)
                    # if ref_doc and ref_doc not in expanded_results:
                    #     expanded_results.append(ref_doc)
                    pass

            logger.debug(f"   知识图谱扩展: {len(l1_results)} -> {len(expanded_results)}")
            return expanded_results

        except Exception as e:
            logger.warning(f"   L2知识图谱扩展失败: {e},返回L1结果")
            return l1_results

    def _l3_rerank(self, query: str, l2_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        L3: Rerank精排

        使用权威文档专用Reranker进行多维特征重排序
        """
        try:
            reranked = self.reranker.rerank(
                query=query, documents=l2_results, top_k=self.config.l3_top_k
            )
            return reranked
        except Exception as e:
            logger.error(f"   L3 Rerank失败: {e}")
            # 回退: 按原始分数排序
            return sorted(l2_results, key=lambda x: x.get("score", 0), reverse=True)[
                : self.config.l3_top_k
            ]

    def _empty_result(self, query: str, elapsed_time: float) -> SearchResult:
        """创建空结果"""
        return SearchResult(
            query=query,
            total_candidates=0,
            l1_count=0,
            l2_count=0,
            l3_count=0,
            l4_count=0,
            results=[],
            latency_ms=elapsed_time * 1000,
            stage_latencies={},
        )


# 全局单例
_search_instance: AuthoritativeDocumentSearch | None = None


def get_authoritative_search(config: SearchConfig | None = None) -> AuthoritativeDocumentSearch:
    """
    获取权威文档检索系统单例

    Args:
        config: 检索配置

    Returns:
        AuthoritativeDocumentSearch实例
    """
    global _search_instance

    if _search_instance is None:
        _search_instance = AuthoritativeDocumentSearch(config=config)

    return _search_instance


# 使用示例
if __name__ == "__main__":
    print("=" * 80)
    print("🧪 权威文档检索系统测试")
    print("=" * 80)
    print()

    # 测试查询
    query = "专利创造性判断标准"

    # 创建模拟数据
    mock_documents = [
        {
            "id": "1",
            "article_id": "L1_2",
            "article_type": "law",
            "title": "专利法",
            "content": "专利法规定,授予专利权的发明和实用新型,应当具备新颖性、创造性和实用性。",
            "hierarchy_level": 0,
            "score": 0.75,
            "metadata": {},
        },
        {
            "id": "2",
            "article_id": "L2_2_3",
            "article_type": "guideline",
            "title": "审查指南",
            "content": "创造性是指与现有技术相比,该发明有突出的实质性特点和显著的进步。判断发明是否具有创造性,应当考虑所属技术领域、现有技术状况、技术问题、技术方案和技术效果等因素。",
            "hierarchy_level": 1,
            "score": 0.85,
            "metadata": {"references": ["L1_2"]},
        },
        {
            "id": "3",
            "article_id": "L2_2_3_1",
            "article_type": "guideline",
            "title": "创造性判断",
            "content": "在判断创造性时,应当将发明作为一个整体考虑,全面分析其技术特征、技术问题和技术效果。",
            "hierarchy_level": 2,
            "score": 0.82,
            "metadata": {"references": ["L2_2_3"]},
        },
        {
            "id": "4",
            "article_id": "R1",
            "article_type": "rule",
            "title": "审查规则",
            "content": "专利审查指南规定了创造性判断的具体步骤和评价标准。",
            "hierarchy_level": 1,
            "score": 0.70,
            "metadata": {},
        },
    ]

    print(f"查询: {query}")
    print(f"模拟数据: {len(mock_documents)} 条文档")
    print()

    # 获取检索系统
    search_system = get_authoritative_search()

    # 手动测试Reranker (因为缺少实际的数据库连接)
    print("测试权威文档Reranker...")
    reranked_results = search_system.reranker.rerank(query, mock_documents, top_k=3)

    print("\n检索结果 (Top-3):")
    print("-" * 80)
    for i, doc in enumerate(reranked_results, 1):
        print(
            f"\n{i}. [{doc['article_id']}] {doc['article_type'].upper()} - {doc.get('title', 'N/A')}"
        )
        print(f"   内容: {doc['content'][:80]}...")
        print(f"   综合分数: {doc['rerank_score']:.3f}")
        if "feature_scores" in doc:
            fs = doc["feature_scores"]
            print("   特征分解:")
            print(
                f"      BGE相关性: {fs['bge']:.3f} (权重{search_system.reranker.config.bge_score_weight})"
            )
            print(
                f"      权威性:    {fs['authority']:.3f} (权重{search_system.reranker.config.authority_weight})"
            )
            print(
                f"      引用关系:  {fs['citation']:.3f} (权重{search_system.reranker.config.citation_weight})"
            )
            print(
                f"      时效性:    {fs['recency']:.3f} (权重{search_system.reranker.config.recency_weight})"
            )

    print("\n" + "=" * 80)
    print("📊 特征权重说明:")
    print("   - BGE相关性 (50%): 基于语义理解的查询-文档相关性")
    print("   - 权威性 (25%): 文档类型层级 (law>guideline>rule>decision)")
    print("   - 引用关系 (15%): 被引用次数作为重要性信号")
    print("   - 时效性 (10%): 文档更新时间衰减")
    print("=" * 80)
