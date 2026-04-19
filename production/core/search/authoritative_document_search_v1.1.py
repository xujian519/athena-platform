#!/usr/bin/env python3
from __future__ import annotations
"""
权威文档检索系统 - 修复版 v1.1
P1-6修复: 实现完整的L1向量搜索功能
作者: Athena AI Team
创建时间: 2026-01-19
版本: v1.1.0
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
    l1_similarity_threshold: float = 0.1  # 相似度阈值

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
    """权威文档检索系统 (P1-6修复版)"""

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

        # P1-6修复: 延迟导入embedding模型
        self.embedding_model = None
        self._init_embedding_model()

        logger.info("✅ 权威文档检索系统初始化完成 v1.1")
        logger.info(f"   L1 Top-K: {self.config.l1_top_k}")
        logger.info(f"   L2 扩展: {'启用' if self.config.l2_enable else '禁用'}")
        logger.info(f"   L3 Top-K: {self.config.l3_top_k}")
        logger.info(f"   L4 Top-K: {self.config.l4_top_k}")

    def _init_embedding_model(self) -> Any:
        """初始化embedding模型 (P1-6新增)"""
        try:
            # 尝试导入sentence-transformers
            from sentence_transformers import SentenceTransformer

            model_path = "/Users/xujian/Athena工作平台/models/converted/bge-m3"

            logger.info(f"🔄 加载embedding模型: {model_path}")

            self.embedding_model = SentenceTransformer(model_path)
            logger.info("✅ Embedding模型加载完成")

        except Exception as e:
            logger.warning(f"⚠️ Embedding模型加载失败: {e}")
            logger.info("   将使用全文搜索作为回退方案")
            self.embedding_model = None

    def _get_query_embedding(self, query: str) -> list[float | None]:
        """
        获取查询的向量表示 (P1-6新增)

        Args:
            query: 查询文本

        Returns:
            查询向量,如果模型不可用则返回None
        """
        if not self.embedding_model:
            return None

        try:
            embedding = self.embedding_model.encode(query, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"❌ 向量化失败: {e}")
            return None

    def search(self, query: str, db_connection=None, kg_connection=None) -> SearchResult:
        """
        执行四阶段检索 (P1-6修复: 完整实现L1向量搜索)

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

    def _l1_vector_search(self, query: str, db_connection) -> list[dict[str, Any]]:
        """
        L1: 向量粗排 (P1-6修复: 完整实现)

        使用PostgreSQL + pgvector进行向量相似度检索
        如果embedding模型不可用,回退到全文搜索
        """
        if db_connection is None:
            logger.warning("   数据库连接未提供,返回空结果")
            return []

        try:
            cursor = db_connection.cursor()

            # P1-6修复: 优先使用向量搜索
            if self.embedding_model:
                return self._vector_search_with_embedding(query, cursor)
            else:
                # 回退到全文搜索
                logger.info("   使用全文搜索回退方案")
                return self._full_text_search(query, cursor)

        except Exception as e:
            logger.error(f"   L1检索失败: {e}")
            return []

    def _vector_search_with_embedding(self, query: str, cursor) -> list[dict[str, Any]]:
        """
        使用embedding模型进行向量搜索 (P1-6新增)

        Args:
            query: 查询文本
            cursor: 数据库游标

        Returns:
            检索结果列表
        """
        # 1. 获取查询向量
        query_embedding = self._get_query_embedding(query)
        if not query_embedding:
            logger.warning("   查询向量化失败,回退到全文搜索")
            return self._full_text_search(query, cursor)

        # 2. 执行向量相似度搜索
        # 使用pgvector的<=>操作符 (余弦距离)
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

        search_sql = """
            SELECT
                id,
                article_id,
                article_type,
                hierarchy_level,
                title,
                LEFT(content, 500) as content,
                full_path,
                metadata,
                1 - (embedding <=> %s::vector) as similarity
            FROM patent_rules_unified
            WHERE article_type IN ('law', 'guideline', 'rule')
                AND embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """

        cursor.execute(search_sql, (embedding_str, embedding_str, self.config.l1_top_k))
        results = cursor.fetchall()

        # 3. 转换结果
        documents = []
        for row in results:
            if hasattr(row, "_asdict"):
                doc = dict(row)
            else:
                doc = {
                    "id": row[0],
                    "article_id": row[1],
                    "article_type": row[2],
                    "hierarchy_level": row[3],
                    "title": row[4],
                    "content": row[5],
                    "full_path": row[6],
                    "metadata": row[7],
                    "score": float(row[8]),  # similarity
                }
            documents.append(doc)

        return documents

    def _full_text_search(self, query: str, cursor) -> list[dict[str, Any]]:
        """
        全文搜索回退方案 (P1-6新增)

        Args:
            query: 查询文本
            cursor: 数据库游标

        Returns:
            检索结果列表
        """
        # 使用PostgreSQL的全文搜索
        search_sql = """
            SELECT
                id,
                article_id,
                article_type,
                hierarchy_level,
                title,
                LEFT(content, 500) as content,
                full_path,
                metadata,
                ts_rank(to_tsvector('chinese', COALESCE(content, '')), plainto_tsquery('chinese', %s)) +
                ts_rank(to_tsvector('chinese', COALESCE(title, '')), plainto_tsquery('chinese', %s)) as score
            FROM patent_rules_unified
            WHERE article_type IN ('law', 'guideline', 'rule')
                AND (
                    to_tsvector('chinese', COALESCE(title, '')) @@ plainto_tsquery('chinese', %s)
                    OR to_tsvector('chinese', COALESCE(content, '')) @@ plainto_tsquery('chinese', %s)
                )
            ORDER BY score DESC
            LIMIT %s
        """

        cursor.execute(search_sql, (query, query, query, query, self.config.l1_top_k))
        results = cursor.fetchall()

        # 转换结果
        documents = []
        for row in results:
            if hasattr(row, "_asdict"):
                doc = dict(row)
                # 归一化分数到0-1
                doc["score"] = min(1.0, doc.get("score", 0.0) / 10.0)
            else:
                doc = {
                    "id": row[0],
                    "article_id": row[1],
                    "article_type": row[2],
                    "hierarchy_level": row[3],
                    "title": row[4],
                    "content": row[5],
                    "full_path": row[6],
                    "metadata": row[7],
                    "score": min(1.0, float(row[8]) / 10.0),
                }
            documents.append(doc)

        return documents

    def _l2_kg_expansion(
        self, query: str, l1_results: list[dict[str, Any]], kg_connection
    ) -> list[dict[str, Any]]:
        """L2: 知识图谱扩展"""
        # TD-001: 使用Neo4j版本的kg_expansion
        try:
            from core.kg.neo4j_kg_expansion import get_kg_expander

            expander = get_kg_expander()
            expanded = expander.expand_by_citations(l1_results, kg_connection)

            return expanded
        except Exception as e:
            logger.warning(f"   知识图谱扩展失败: {e}")
            return l1_results

    def _l3_rerank(self, query: str, l2_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """L3: Rerank精排"""
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
    print("🧪 权威文档检索系统测试 v1.1")
    print("=" * 80)
    print()

    # 创建搜索系统
    search_system = get_authoritative_search()

    # 模拟检索(不使用实际数据库连接)
    query = "专利创造性判断标准"

    print(f"查询: {query}")
    print("\n_P1-6修复内容:")
    print("- 实现了完整的L1向量搜索")
    print("- 添加了embedding模型加载")
    print("- 实现了全文搜索回退方案")
    print("- 添加了pgvector相似度计算")
    print("- 完整的查询-文档匹配逻辑")

    print("\n" + "=" * 80)
