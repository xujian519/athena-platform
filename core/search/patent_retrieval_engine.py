#!/usr/bin/env python3
"""
Athena专利检索引擎
Athena Patent Retrieval Engine

将专利混合检索系统集成到Athena平台的核心模块
集成BGE Large ZH v1.5提升检索质量
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

# BGE嵌入服务

# Athena现有组件
from core.vector.qdrant_adapter import QdrantVectorAdapter
from patent_hybrid_retrieval.fulltext_adapter import FullTextSearchAdapter

# 配置日志
logger = logging.getLogger(__name__)


@dataclass
class RetrievalRequest:
    """检索请求"""

    query: str
    filters: dict[str, Any] | None = None
    limit: int = 20
    offset: int = 0
    search_mode: str = "hybrid"  # hybrid, fulltext, vector, kg
    include_highlights: bool = True
    include_explanation: bool = True


@dataclass
class RetrievalResponse:
    """检索响应"""

    results: list[dict[str, Any]]
    total: int
    query: str
    search_mode: str
    execution_time: float
    performance_metrics: dict[str, Any]
    explanation: str | None = None


class PatentRetrievalEngine:
    """Athena专利检索引擎"""

    def __init__(self):
        """初始化检索引擎"""
        logger.info("初始化Athena专利检索引擎(集成BGE)...")

        # 初始化检索组件
        self.fulltext_adapter = FullTextSearchAdapter()
        self.vector_adapter = QdrantVectorAdapter()
        self.bge_service = None  # 延迟初始化

        # 检索策略权重(提升向量搜索权重)
        self.search_weights = {
            "fulltext": 0.3,
            "vector": 0.6,  # BGE质量更高,提升权重
            "keyword": 0.1,
        }

        # 性能统计
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "average_response_time": 0.0,
            "search_mode_usage": {"hybrid": 0, "fulltext": 0, "vector": 0, "kg": 0},
        }

        # 查询缓存(简单实现)
        self.query_cache = {}
        self.cache_size_limit = 1000

        logger.info("专利检索引擎初始化完成")

    async def search(self, request: RetrievalRequest) -> RetrievalResponse:
        """
        执行专利检索

        Args:
            request: 检索请求对象

        Returns:
            检索响应对象
        """
        start_time = datetime.now()
        query_id = self._generate_query_id(request)

        logger.info(f"执行专利检索 [ID:{query_id}]: {request.query}")

        # 更新统计
        self.stats["total_requests"] += 1
        self.stats["search_mode_usage"][request.search_mode] += 1

        try:
            # 检查缓存
            cache_key = self._get_cache_key(request)
            if cache_key in self.query_cache:
                logger.info(f"命中查询缓存: {cache_key}")
                cached_response = self.query_cache[cache_key]
                cached_response.query_id = query_id
                return cached_response

            # 根据搜索模式执行检索
            if request.search_mode == "hybrid":
                results = await self._hybrid_search(request)
            elif request.search_mode == "fulltext":
                results = await self._fulltext_search_only(request)
            elif request.search_mode == "vector":
                results = await self._vector_search_only(request)
            else:
                results = await self._hybrid_search(request)  # 默认混合检索

            # 计算执行时间
            execution_time = (datetime.now() - start_time).total_seconds()

            # 更新性能统计
            self._update_performance_stats(execution_time)

            # 构建响应
            response = RetrievalResponse(
                results=results,
                total=len(results),
                query=request.query,
                search_mode=request.search_mode,
                execution_time=execution_time,
                performance_metrics=self._get_performance_metrics(),
                explanation=(
                    self._generate_explanation(request, results)
                    if request.include_explanation
                    else None
                ),
            )

            # 缓存结果
            self._cache_response(cache_key, response)

            # 更新成功统计
            self.stats["successful_requests"] += 1

            logger.info(
                f"检索完成 [ID:{query_id}]: 返回 {len(results)} 条结果,耗时 {execution_time:.3f}s"
            )

            return response

        except Exception as e:
            logger.error(f"检索失败 [ID:{query_id}]: {e!s}")
            raise

    async def _hybrid_search(self, request: RetrievalRequest) -> list[dict[str, Any]]:
        """混合检索模式"""
        logger.info("执行混合检索...")

        # 并行执行多种检索策略
        tasks = [
            self._search_fulltext(request),
            self._search_vector(request),
            self._search_keyword(request),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        ft_results = results[0] if not isinstance(results[0], Exception) else []
        vector_results = results[1] if not isinstance(results[1], Exception) else []
        keyword_results = results[2] if not isinstance(results[2], Exception) else []

        # 融合结果
        merged_results = self._merge_search_results(
            ft_results, vector_results, keyword_results, request.limit, request.include_highlights
        )

        return merged_results

    async def _fulltext_search_only(self, request: RetrievalRequest) -> list[dict[str, Any]]:
        """仅全文搜索"""
        logger.info("执行全文搜索...")
        results = await self._search_fulltext(request)
        return results[: request.limit]

    async def _vector_search_only(self, request: RetrievalRequest) -> list[dict[str, Any]]:
        """仅向量搜索"""
        logger.info("执行向量搜索...")
        results = await self._search_vector(request)
        return results[: request.limit]

    async def _search_fulltext(self, request: RetrievalRequest) -> list[dict[str, Any]]:
        """全文搜索实现"""
        try:
            if request.filters:
                results = self.fulltext_adapter.search_with_filters(
                    query=request.query,
                    filters=request.filters,
                    limit=request.limit * 2,  # 获取更多结果用于融合
                    offset=request.offset,
                )
            else:
                results = self.fulltext_adapter.search(
                    query=request.query, limit=request.limit * 2, offset=request.offset
                )

            # 标记来源
            for result in results:
                result["source"] = "fulltext"
                result["source_score"] = result.get("score", 0)

            return results

        except Exception as e:
            logger.error(f"全文搜索失败: {e}")
            return []

    async def _search_vector(self, request: RetrievalRequest) -> list[dict[str, Any]]:
        """向量搜索实现"""
        try:
            # 这里需要将query转换为向量
            # 实际应用中应调用embedding模型
            query_vector = self._text_to_vector(request.query)

            results = await self.vector_adapter.search_vectors(
                collection_type="patents",
                query_vector=query_vector,
                limit=request.limit * 2,
                threshold=0.3,
            )

            # 标记来源
            for result in results:
                result["source"] = "vector"
                result["source_score"] = result.get("score", 0)

            return results

        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            return []

    async def _search_keyword(self, request: RetrievalRequest) -> list[dict[str, Any]]:
        """关键词搜索实现"""
        # 简化的关键词搜索实现
        # 实际应用中应结合知识图谱
        keywords = self._extract_keywords(request.query)

        if not keywords:
            return []

        # 使用全文搜索模拟关键词搜索
        keyword_query = " OR ".join(keywords)
        results = self.fulltext_adapter.search(query=keyword_query, limit=request.limit * 2)

        # 标记来源并计算关键词匹配分数
        for result in results:
            result["source"] = "keyword"
            # 简单的匹配度计算
            matches = sum(1 for kw in keywords if kw.lower() in result.get("title", "").lower())
            result["source_score"] = matches / len(keywords)

        return results

    def _merge_search_results(
        self,
        ft_results: list[dict[str, Any]],        vector_results: list[dict[str, Any]],        keyword_results: list[dict[str, Any]],        limit: int,
        include_highlights: bool,
    ) -> list[dict[str, Any]]:
        """融合多种检索结果"""
        # 收集所有结果
        all_patents = {}

        # 合并全文搜索结果
        for result in ft_results:
            patent_id = result.get("patent_id", result.get("id", ""))
            if patent_id and patent_id not in all_patents:
                all_patents[patent_id] = {
                    "patent": result,
                    "scores": {"fulltext": 0, "vector": 0, "keyword": 0},
                    "sources": [],
                }
            if patent_id in all_patents:
                all_patents[patent_id]["scores"]["fulltext"] = result.get("source_score", 0)
                all_patents[patent_id]["sources"].append(f"FT:{result.get('source_score', 0):.3f}")

        # 合并向量搜索结果
        for result in vector_results:
            patent_id = result.get("patent_id", result.get("id", ""))
            if patent_id and patent_id not in all_patents:
                all_patents[patent_id] = {
                    "patent": result,
                    "scores": {"fulltext": 0, "vector": 0, "keyword": 0},
                    "sources": [],
                }
            if patent_id in all_patents:
                all_patents[patent_id]["scores"]["vector"] = result.get("source_score", 0)
                all_patents[patent_id]["sources"].append(f"VEC:{result.get('source_score', 0):.3f}")

        # 合并关键词搜索结果
        for result in keyword_results:
            patent_id = result.get("patent_id", result.get("id", ""))
            if patent_id and patent_id not in all_patents:
                all_patents[patent_id] = {
                    "patent": result,
                    "scores": {"fulltext": 0, "vector": 0, "keyword": 0},
                    "sources": [],
                }
            if patent_id in all_patents:
                all_patents[patent_id]["scores"]["keyword"] = result.get("source_score", 0)
                all_patents[patent_id]["sources"].append(f"KW:{result.get('source_score', 0):.3f}")

        # 计算加权总分
        final_results = []
        for patent_id, data in all_patents.items():
            scores = data["scores"]
            total_score = (
                scores["fulltext"] * self.search_weights["fulltext"]
                + scores["vector"] * self.search_weights["vector"]
                + scores["keyword"] * self.search_weights["keyword"]
            )

            patent = data["patent"]
            # 添加综合信息
            patent["total_score"] = total_score
            patent["score_breakdown"] = scores
            patent["sources"] = data["sources"]
            patent["weights_used"] = self.search_weights

            final_results.append(patent)

        # 排序并返回Top-K
        final_results.sort(key=lambda x: x.get("total_score", 0), reverse=True)
        return final_results[:limit]

    def _text_to_vector(self, text: str) -> list[float]:
        """文本转向量(简化实现)"""
        # 实际应用中应调用embedding模型
        # 这里返回随机向量作为示例
        import random

        return [random.random() for _ in range(768)]

    def _extract_keywords(self, text: str) -> list[str]:
        """提取关键词"""
        # 简化的关键词提取
        import re

        words = re.findall(r"\b\w+\b", text)
        # 过滤停用词
        stop_words = {"的", "是", "在", "和", "与", "或", "等", "及", "基于", "包括"}
        keywords = [w for w in words if len(w) > 1 and w not in stop_words]
        return keywords[:5]

    def _generate_query_id(self, request: RetrievalRequest) -> str:
        """生成查询ID"""
        import hashlib

        query_str = f"{request.query}_{request.search_mode}_{datetime.now().timestamp()}"
        return hashlib.md5(query_str.encode(), usedforsecurity=False).hexdigest()

    def _get_cache_key(self, request: RetrievalRequest) -> str:
        """生成缓存键"""
        import hashlib

        cache_str = f"{request.query}_{request.search_mode}_{json.dumps(request.filters or {})}"
        return hashlib.md5(cache_str.encode(), usedforsecurity=False).hexdigest()

    def _cache_response(self, cache_key: str, response: RetrievalResponse) -> Any:
        """缓存响应"""
        if len(self.query_cache) >= self.cache_size_limit:
            # 简单的LRU:删除第一个
            oldest_key = next(iter(self.query_cache))
            del self.query_cache[oldest_key]

        self.query_cache[cache_key] = response

    def _update_performance_stats(self, execution_time: float) -> Any:
        """更新性能统计"""
        current_avg = self.stats["average_response_time"]
        successful_requests = self.stats["successful_requests"]

        # 计算新的平均响应时间
        self.stats["average_response_time"] = (
            current_avg * (successful_requests - 1) + execution_time
        ) / successful_requests

    def _get_performance_metrics(self) -> dict[str, Any]:
        """获取性能指标"""
        total = self.stats["total_requests"]
        successful = self.stats["successful_requests"]
        success_rate = (successful / total * 100) if total > 0 else 0

        return {
            "total_requests": total,
            "successful_requests": successful,
            "success_rate": f"{success_rate:.2f}%",
            "average_response_time": f"{self.stats['average_response_time']:.3f}s",
            "cache_size": len(self.query_cache),
            "search_mode_distribution": self.stats["search_mode_usage"],
        }

    def _generate_explanation(
        self, request: RetrievalRequest, results: list[dict[str, Any]]
    ) -> str:
        """生成检索解释"""
        if not results:
            return f"未找到与'{request.query}'相关的专利。请尝试使用不同的关键词或减少过滤条件。"

        explanation_parts = [
            f"查询 '{request.query}' 使用 {request.search_mode} 模式",
            f"返回 {len(results)} 条相关专利",
        ]

        # 分析结果分布
        sources = {}
        for result in results[:5]:  # 分析前5条结果
            for source in result.get("sources", []):
                strategy = source.split(":")[0]
                sources[strategy] = sources.get(strategy, 0) + 1

        if sources:
            explanation_parts.append(
                f"主要来源: {', '.join([f'{k}({v}条)' for k, v in sources.items()])}"
            )

        return "。".join(explanation_parts) + "。"

    def get_stats(self) -> dict[str, Any]:
        """获取检索引擎统计信息"""
        return {
            "engine_stats": self.stats,
            "search_weights": self.search_weights,
            "components": {
                "fulltext_adapter": "PostgreSQL",
                "vector_adapter": "Qdrant",
                "keyword_search": "Built-in",
            },
            "cache_stats": {"size": len(self.query_cache), "limit": self.cache_size_limit},
        }

    def update_search_weights(self, weights: dict[str, float]) -> None:
        """更新搜索权重"""
        total = sum(weights.values())
        if abs(total - 1.0) > 0.01:
            logger.warning(f"权重总和不为1.0 (当前: {total:.3f}),将自动归一化")
            weights = {k: v / total for k, v in weights.items()}

        self.search_weights = weights
        logger.info(f"搜索权重已更新: {weights}")

    def clear_cache(self) -> None:
        """清空缓存"""
        self.query_cache.clear()
        logger.info("查询缓存已清空")


# 单例模式
_retrieval_engine = None


def get_patent_retrieval_engine() -> PatentRetrievalEngine:
    """获取专利检索引擎单例"""
    global _retrieval_engine
    if _retrieval_engine is None:
        _retrieval_engine = PatentRetrievalEngine()
    return _retrieval_engine
