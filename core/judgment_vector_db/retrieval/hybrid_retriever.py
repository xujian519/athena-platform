#!/usr/bin/env python3
"""
混合检索引擎
Hybrid Retrieval Engine for Patent Judgments

功能:
- 向量检索
- 全文检索
- 知识图谱检索
- 结果融合与排序
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


logger = logging.getLogger(__name__)


class RetrievalStrategy(Enum):
    """检索策略枚举"""

    VECTOR_ONLY = "vector_only"  # 仅向量检索
    FULLTEXT_ONLY = "fulltext_only"  # 仅全文检索
    GRAPH_ONLY = "graph_only"  # 仅图谱检索
    HYBRID_STANDARD = "hybrid_standard"  # 标准混合(向量60% + 全文30% + 图谱10%)
    HYBRID_DEEP = "hybrid_deep"  # 深度混合(向量50% + 全文25% + 图谱25%)
    GRAPH_FIRST = "graph_first"  # 图谱优先
    FULLTEXT_PRIMARY = "fulltext_primary"  # 全文优先
    AGGREGATION_MODE = "aggregation_mode"  # 聚合模式


@dataclass
class RetrievalResult:
    """检索结果"""

    id: str  # 结果ID
    content: str  # 内容
    source: str  # 来源(vector/fulltext/graph)
    score: float  # 相似度分数
    metadata: dict[str, Any]  # 元数据
    layer: str  # 所属层级(L1/L2/L3)


@dataclass
class HybridResult:
    """混合检索结果"""

    query: str  # 查询文本
    results: list[RetrievalResult]  # 融合后的结果列表
    strategy_used: str  # 使用的策略
    component_scores: dict[str, float]  # 各组件分数
    total_retrieved: int  # 总检索数量
    fusion_method: str  # 融合方法


class HybridRetriever:
    """混合检索引擎"""

    def __init__(
        self,
        qdrant_client,
        postgres_client,
        nebula_client,
        vectorizer,
        config: dict[str, Any] | None = None,
    ):
        """
        初始化混合检索引擎

        Args:
            qdrant_client: Qdrant客户端
            postgres_client: PostgreSQL客户端
            nebula_client: NebulaGraph客户端
            vectorizer: 向量化器
            config: 配置字典
        """
        self.qdrant_client = qdrant_client
        self.postgres_client = postgres_client
        self.nebula_client = nebula_client
        self.vectorizer = vectorizer
        self.config = config or {}

        # 检索权重配置
        self.weights = self.config.get(
            "retrieval_weights", {"vector": 0.60, "fulltext": 0.30, "graph": 0.10}
        )

        # 默认参数
        self.default_limit = self.config.get("default_limit", 20)
        self.score_threshold = self.config.get("score_threshold", 0.5)

    def retrieve(
        self,
        query: str,
        strategy: RetrievalStrategy = RetrievalStrategy.HYBRID_STANDARD,
        layer: str = "L3",
        limit: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> HybridResult:
        """
        执行混合检索

        Args:
            query: 查询文本
            strategy: 检索策略
            layer: 目标层级(L1/L2/L3)
            limit: 返回数量
            filters: 过滤条件

        Returns:
            HybridResult对象
        """
        logger.info(f"🔍 执行检索: strategy={strategy.value}, layer={layer}")

        # 根据策略执行检索
        if strategy == RetrievalStrategy.VECTOR_ONLY:
            return self._vector_only_retrieve(query, layer, limit, filters)
        elif strategy == RetrievalStrategy.FULLTEXT_ONLY:
            return self._fulltext_only_retrieve(query, limit, filters)
        elif strategy == RetrievalStrategy.GRAPH_ONLY:
            return self._graph_only_retrieve(query, limit, filters)
        elif strategy == RetrievalStrategy.GRAPH_FIRST:
            return self._graph_first_retrieve(query, layer, limit, filters)
        elif strategy == RetrievalStrategy.FULLTEXT_PRIMARY:
            return self._fulltext_primary_retrieve(query, layer, limit, filters)
        elif strategy == RetrievalStrategy.HYBRID_DEEP:
            return self._hybrid_deep_retrieve(query, layer, limit, filters)
        elif strategy == RetrievalStrategy.AGGREGATION_MODE:
            return self._aggregation_retrieve(query, layer, limit, filters)
        else:  # HYBRID_STANDARD
            return self._hybrid_standard_retrieve(query, layer, limit, filters)

    def _hybrid_standard_retrieve(
        self, query: str, layer: str, limit: int, filters: dict[str, Any]
    ) -> HybridResult:
        """标准混合检索(向量60% + 全文30% + 图谱10%)"""
        # 1. 向量检索
        vector_results = self._vector_search(query, layer, limit * 2, filters)

        # 2. 全文检索
        fulltext_results = self._fulltext_search(query, limit * 2, filters)

        # 3. 知识图谱检索
        graph_results = self._graph_search(query, limit, filters)

        # 4. 融合结果
        fused_results = self._fuse_results(
            [
                (vector_results, self.weights["vector"]),
                (fulltext_results, self.weights["fulltext"]),
                (graph_results, self.weights["graph"]),
            ],
            method="weighted_score",
        )

        return HybridResult(
            query=query,
            results=fused_results[:limit],
            strategy_used="hybrid_standard",
            component_scores={
                "vector": len(vector_results),
                "fulltext": len(fulltext_results),
                "graph": len(graph_results),
            },
            total_retrieved=len(vector_results) + len(fulltext_results) + len(graph_results),
            fusion_method="weighted_score",
        )

    def _hybrid_deep_retrieve(
        self, query: str, layer: str, limit: int, filters: dict[str, Any]
    ) -> HybridResult:
        """深度混合检索(向量50% + 全文25% + 图谱25%)"""
        # 执行检索
        vector_results = self._vector_search(query, layer, limit * 2, filters)
        fulltext_results = self._fulltext_search(query, limit * 2, filters)
        graph_results = self._graph_search(query, limit * 2, filters)

        # 融合(提高图谱权重)
        fused_results = self._fuse_results(
            [(vector_results, 0.50), (fulltext_results, 0.25), (graph_results, 0.25)],
            method="weighted_score",
        )

        return HybridResult(
            query=query,
            results=fused_results[:limit],
            strategy_used="hybrid_deep",
            component_scores={
                "vector": len(vector_results),
                "fulltext": len(fulltext_results),
                "graph": len(graph_results),
            },
            total_retrieved=len(vector_results) + len(fulltext_results) + len(graph_results),
            fusion_method="weighted_score_deep",
        )

    def _vector_only_retrieve(
        self, query: str, layer: str, limit: int, filters: dict[str, Any]
    ) -> HybridResult:
        """仅向量检索"""
        results = self._vector_search(query, layer, limit, filters)

        return HybridResult(
            query=query,
            results=results,
            strategy_used="vector_only",
            component_scores={"vector": len(results)},
            total_retrieved=len(results),
            fusion_method="none",
        )

    def _fulltext_only_retrieve(
        self, query: str, limit: int, filters: dict[str, Any]
    ) -> HybridResult:
        """仅全文检索"""
        results = self._fulltext_search(query, limit, filters)

        return HybridResult(
            query=query,
            results=results,
            strategy_used="fulltext_only",
            component_scores={"fulltext": len(results)},
            total_retrieved=len(results),
            fusion_method="none",
        )

    def _graph_only_retrieve(
        self, query: str, limit: int, filters: dict[str, Any]
    ) -> HybridResult:
        """仅图谱检索"""
        results = self._graph_search(query, limit, filters)

        return HybridResult(
            query=query,
            results=results,
            strategy_used="graph_only",
            component_scores={"graph": len(results)},
            total_retrieved=len(results),
            fusion_method="none",
        )

    def _graph_first_retrieve(
        self, query: str, layer: str, limit: int, filters: dict[str, Any]
    ) -> HybridResult:
        """图谱优先检索"""
        # 先图谱检索
        graph_results = self._graph_search(query, limit, filters)

        # 如果图谱结果不足,用向量补充
        if len(graph_results) < limit:
            needed = limit - len(graph_results)
            vector_results = self._vector_search(query, layer, needed, filters)
            graph_results.extend(vector_results)

        return HybridResult(
            query=query,
            results=graph_results[:limit],
            strategy_used="graph_first",
            component_scores={
                "graph": len(graph_results),
                "vector": len(graph_results) - len(graph_results),
            },
            total_retrieved=len(graph_results),
            fusion_method="graph_first_fallback",
        )

    def _fulltext_primary_retrieve(
        self, query: str, layer: str, limit: int, filters: dict[str, Any]
    ) -> HybridResult:
        """全文优先检索"""
        # 先全文检索
        fulltext_results = self._fulltext_search(query, limit, filters)

        # 向量检索补充
        vector_results = self._vector_search(query, layer, limit, filters)

        # 融合(全文权重更高)
        fused = self._fuse_results(
            [(fulltext_results, 0.7), (vector_results, 0.3)], method="weighted_score"
        )

        return HybridResult(
            query=query,
            results=fused[:limit],
            strategy_used="fulltext_primary",
            component_scores={"fulltext": len(fulltext_results), "vector": len(vector_results)},
            total_retrieved=len(fulltext_results) + len(vector_results),
            fusion_method="fulltext_primary_fusion",
        )

    def _aggregation_retrieve(
        self, query: str, layer: str, limit: int, filters: dict[str, Any]
    ) -> HybridResult:
        """聚合模式检索(用于观点汇总)"""
        # 获取更多结果
        vector_results = self._vector_search(query, layer, limit * 3, filters)
        fulltext_results = self._fulltext_search(query, limit * 2, filters)

        # 合并去重
        all_results = self._merge_and_deduplicate(vector_results, fulltext_results)

        return HybridResult(
            query=query,
            results=all_results[:limit],
            strategy_used="aggregation_mode",
            component_scores={
                "vector": len(vector_results),
                "fulltext": len(fulltext_results),
                "merged": len(all_results),
            },
            total_retrieved=len(vector_results) + len(fulltext_results),
            fusion_method="merge_deduplicate",
        )

    def _vector_search(
        self, query: str, layer: str, limit: int, filters: dict[str, Any]
    ) -> list[RetrievalResult]:
        """向量搜索"""
        try:
            # 向量化查询
            query_vector = self.vectorizer.encode_query(query, normalize=True)

            # Qdrant搜索
            qdrant_results = self.qdrant_client.search(
                layer=layer,
                query_vector=query_vector.tolist(),
                limit=limit,
                score_threshold=self.score_threshold,
                filters=filters,
            )

            # 转换为RetrievalResult
            results = []
            for result in qdrant_results:
                results.append(
                    RetrievalResult(
                        id=str(result["id"]),
                        content=result["payload"].get("content", ""),
                        source="vector",
                        score=result["score"],
                        metadata=result["payload"],
                        layer=layer,
                    )
                )

            return results

        except Exception as e:
            logger.error(f"❌ 向量搜索失败: {e!s}")
            return []

    def _fulltext_search(
        self, query: str, limit: int, filters: dict[str, Any]
    ) -> list[RetrievalResult]:
        """全文搜索"""
        try:
            # PostgreSQL全文检索
            # 先在判决书中搜索
            judgment_results = self.postgres_client.fulltext_search(
                query=query, table="patent_judgments", limit=limit
            )

            results = []
            for result in judgment_results:
                results.append(
                    RetrievalResult(
                        id=result["case_id"],
                        content=f"{result.get('court', '')} - {result.get('case_type', '')}",
                        source="fulltext",
                        score=result.get("rank", 0.5),
                        metadata=result,
                        layer="judgment",
                    )
                )

            # 如果结果不足,在论点中搜索
            if len(results) < limit:
                argument_results = self.postgres_client.fulltext_search(
                    query=query, table="judgment_arguments", limit=limit - len(results)
                )

                for result in argument_results:
                    results.append(
                        RetrievalResult(
                            id=result["argument_id"],
                            content=result.get("dispute_focus", ""),
                            source="fulltext",
                            score=result.get("rank", 0.5),
                            metadata=result,
                            layer="argument",
                        )
                    )

            return results

        except Exception as e:
            logger.error(f"❌ 全文搜索失败: {e!s}")
            return []

    def _graph_search(
        self, query: str, limit: int, filters: dict[str, Any]
    ) -> list[RetrievalResult]:
        """知识图谱搜索"""
        if not self.nebula_client or not self.nebula_client.is_connected:
            return []

        try:
            # 简化实现:先尝试法条查询
            # TODO: 实现更复杂的图谱遍历
            results = []

            # 这里可以根据查询类型执行不同的图谱查询
            # 目前简化为返回空列表

            return results

        except Exception as e:
            logger.error(f"❌ 图谱搜索失败: {e!s}")
            return []

    def _fuse_results(
        self,
        weighted_results: list[tuple[list[RetrievalResult], float]],
        method: str = "weighted_score",
    ) -> list[RetrievalResult]:
        """
        融合多个检索结果

        Args:
            weighted_results: [(结果列表, 权重), ...]
            method: 融合方法

        Returns:
            融合后的结果列表
        """
        if method == "weighted_score":
            return self._weighted_score_fusion(weighted_results)
        elif method == "merge_deduplicate":
            return self._merge_deduplicate_fusion(weighted_results)
        else:
            return self._weighted_score_fusion(weighted_results)

    def _weighted_score_fusion(
        self, weighted_results: list[tuple[list[RetrievalResult], float]]
    ) -> list[RetrievalResult]:
        """加权分数融合"""
        # 收集所有结果
        all_results = {}  # id -> (result, accumulated_score)

        for results, weight in weighted_results:
            for result in results:
                if result.id not in all_results:
                    all_results[result.id] = (result, result.score * weight)
                else:
                    existing, accum_score = all_results[result.id]
                    # 更新分数
                    accum_score += result.score * weight
                    all_results[result.id] = (existing, accum_score)

        # 按融合分数排序
        sorted_results = sorted(all_results.values(), key=lambda x: x[1], reverse=True)

        # 更新最终分数
        final_results = []
        for result, score in sorted_results:
            result.score = score
            final_results.append(result)

        return final_results

    def _merge_deduplicate_fusion(
        self, weighted_results: list[tuple[list[RetrievalResult], float]]
    ) -> list[RetrievalResult]:
        """合并去重融合"""
        seen_ids = set()
        unique_results = []

        for results, _ in weighted_results:
            for result in results:
                if result.id not in seen_ids:
                    seen_ids.add(result.id)
                    unique_results.append(result)

        # 按原始分数排序
        return sorted(unique_results, key=lambda x: x.score, reverse=True)

    def _merge_and_deduplicate(self, *result_lists: list[RetrievalResult]) -> list[RetrievalResult]:
        """合并并去重多个结果列表"""
        seen_ids = set()
        unique_results = []

        for results in result_lists:
            for result in results:
                if result.id not in seen_ids:
                    seen_ids.add(result.id)
                    unique_results.append(result)

        return unique_results


# 便捷函数
def create_hybrid_retriever(
    qdrant_client,
    postgres_client,
    nebula_client,
    vectorizer,
    config: dict[str, Any] | None = None,
) -> HybridRetriever:
    """
    创建混合检索引擎

    Args:
        qdrant_client: Qdrant客户端
        postgres_client: PostgreSQL客户端
        nebula_client: NebulaGraph客户端
        vectorizer: 向量化器
        config: 配置字典

    Returns:
        HybridRetriever实例
    """
    return HybridRetriever(
        qdrant_client=qdrant_client,
        postgres_client=postgres_client,
        nebula_client=nebula_client,
        vectorizer=vectorizer,
        config=config,
    )
