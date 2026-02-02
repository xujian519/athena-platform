#!/usr/bin/env python3
"""
Reranker增强的向量搜索引擎
Enhanced Vector Search with Reranker

集成BGE-Reranker模型,提供高精度的向量检索服务
作者: Athena AI Team
创建时间: 2026-01-09
版本: v1.0.0
"""

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union


from core.nlp.bge_embedding_service import get_bge_service

# 导入现有模块
from core.reranking.bge_reranker import BGEReranker, RerankConfig, RerankMode, RerankResult
from core.vector_db.unified_search_interface import UnifiedVectorSearcher, VectorQuery, VectorResult

logger = logging.getLogger(__name__)


class SearchMode(Enum):
    """搜索模式"""

    VECTOR_ONLY = "vector_only"  # 仅向量搜索
    RERANK_TOP_K = "rerank_top_k"  # Rerank Top-K
    RERANK_FULL = "rerank_full"  # 全量Rerank
    RERANK_ADAPTIVE = "rerank_adaptive"  # 自适应Rerank


@dataclass
class EnhancedSearchConfig:
    """增强搜索配置 - 生产优化版本"""

    mode: SearchMode = SearchMode.RERANK_TOP_K  # ✅ 默认启用Reranker
    initial_top_k: int = 100  # ✅ 增加初始检索数量(50→100)
    final_top_k: int = 10  # 最终返回数量
    rerank_threshold: float = 0.2  # ✅ 降低阈值(0.3→0.2)
    enable_cache: bool = True  # ✅ 启用缓存
    cache_ttl: int = 600  # ✅ 延长缓存时间(300→600秒)

    # 性能优化
    batch_size: int = 16  # ✅ 增加批处理大小(8→16)
    parallel_search: bool = True  # 并行搜索

    # 调试选项
    debug_mode: bool = False  # 调试模式
    log_performance: bool = False  # ✅ 生产环境关闭详细日志


@dataclass
class EnhancedSearchResult:
    """增强搜索结果"""

    query: str
    results: list[VectorResult]
    total_found: int
    search_time: float
    mode_used: SearchMode

    # 性能指标
    vector_search_time: float = 0.0
    rerank_time: float = 0.0
    total_time: float = 0.0

    # 质量指标
    average_score: float = 0.0
    score_distribution: dict[str, int] = field(default_factory=dict)

    # 元数据
    metadata: dict[str, Any] = field(default_factory=dict)


class EnhancedVectorSearchWithReranker:
    """
    Reranker增强的向量搜索引擎

    特性:
    - 向量检索 + BGE-Reranker重排序
    - 多种Rerank模式
    - 性能监控和优化
    - 缓存机制
    """

    def __init__(self, config: EnhancedSearchConfig = None):
        """
        初始化增强搜索引擎

        Args:
            config: 搜索配置
        """
        self.config = config or EnhancedSearchConfig()
        self.name = "Reranker增强向量搜索引擎"
        self.version = "1.0.0"

        logger.info(f"🔍 初始化{self.name}...")

        # 初始化组件
        self.vector_searcher = None  # 延迟加载
        self.reranker = None  # 延迟加载
        self.bge_service = None  # 延迟加载

        # 缓存
        self.cache = {}
        self.cache_stats = {"hits": 0, "misses": 0, "total_queries": 0}

        # 性能统计
        self.performance_stats = {
            "total_searches": 0,
            "total_time": 0.0,
            "avg_time": 0.0,
            "mode_usage": {mode.value: 0 for mode in SearchMode},
        }

        logger.info(f"✅ {self.name}初始化完成")
        logger.info(f"   搜索模式: {self.config.mode.value}")
        logger.info(f"   初始Top-K: {self.config.initial_top_k}")
        logger.info(f"   最终Top-K: {self.config.final_top_k}")

    async def _ensure_components(self):
        """确保组件已加载"""
        if self.vector_searcher is None:
            self.vector_searcher = UnifiedVectorSearcher()
            logger.info("✅ 向量搜索器已加载")

        if self.reranker is None:
            # 配置Reranker
            rerank_config = RerankConfig(
                mode=RerankMode.TOP_K_RERANK,
                top_k=self.config.initial_top_k,
                final_top_k=self.config.final_top_k,
                threshold=self.config.rerank_threshold,
                batch_size=self.config.batch_size,
                use_cache=self.config.enable_cache,
                cache_ttl=self.config.cache_ttl,
            )

            self.reranker = BGEReranker(config=rerank_config)
            await self.reranker.initialize_async()
            logger.info("✅ BGE-Reranker已加载")

        if self.bge_service is None:
            self.bge_service = await get_bge_service()
            logger.info("✅ BGE嵌入服务已加载")

    async def search(
        self, query: str, mode: SearchMode | None = None, top_k: int | None = None
    ) -> EnhancedSearchResult:
        """
        执行增强搜索

        Args:
            query: 查询文本
            mode: 搜索模式 (None则使用配置默认值)
            top_k: 返回结果数量 (None则使用配置默认值)

        Returns:
            增强搜索结果
        """
        start_time = time.time()

        # 确保组件已加载
        await self._ensure_components()

        # 使用指定的模式或默认模式
        search_mode = mode or self.config.mode
        final_top_k = top_k or self.config.final_top_k

        logger.info(f"🔍 执行搜索: {query[:50]}...")
        logger.info(f"   模式: {search_mode.value}")
        logger.info(f"   Top-K: {final_top_k}")

        try:
            # 检查缓存
            if self.config.enable_cache:
                cache_key = self._generate_cache_key(query, search_mode, final_top_k)
                cached_result = self._get_from_cache(cache_key)
                if cached_result:
                    self.cache_stats["hits"] += 1
                    logger.info("✅ 从缓存返回结果")
                    return cached_result
                else:
                    self.cache_stats["misses"] += 1

            self.cache_stats["total_queries"] += 1
            self.performance_stats["total_searches"] += 1
            self.performance_stats["mode_usage"][search_mode.value] += 1

            # 根据模式执行搜索
            if search_mode == SearchMode.VECTOR_ONLY:
                result = await self._vector_only_search(query, final_top_k)
            elif search_mode == SearchMode.RERANK_TOP_K:
                result = await self._rerank_top_k_search(query, final_top_k)
            elif search_mode == SearchMode.RERANK_FULL:
                result = await self._rerank_full_search(query, final_top_k)
            else:  # RERANK_ADAPTIVE
                result = await self._adaptive_search(query, final_top_k)

            # 更新性能统计
            total_time = time.time() - start_time
            result.total_time = total_time
            result.mode_used = search_mode

            self.performance_stats["total_time"] += total_time
            self.performance_stats["avg_time"] = (
                self.performance_stats["total_time"] / self.performance_stats["total_searches"]
            )

            # 缓存结果
            if self.config.enable_cache:
                self._save_to_cache(cache_key, result)

            logger.info(f"✅ 搜索完成: {len(result.results)} 个结果,耗时 {total_time:.2f}秒")

            return result

        except Exception as e:
            logger.error(f"❌ 搜索失败: {e}")
            # 返回降级结果(仅向量搜索)
            return await self._vector_only_search(query, final_top_k)

    async def _vector_only_search(self, query: str, top_k: int) -> EnhancedSearchResult:
        """仅向量搜索"""
        start_time = time.time()

        # 生成查询向量
        query_vector_result = await self.bge_service.encode([query])
        query_vector = (
            query_vector_result.embeddings[0].tolist()
            if hasattr(query_vector_result.embeddings[0], "tolist")
            else query_vector_result.embeddings[0]
        )

        # 执行向量搜索
        vector_query = VectorQuery(vector=query_vector, limit=top_k)  # 使用 limit 参数而不是 top_k

        # 搜索所有集合
        all_results = []
        for collection_name in self.vector_searcher.vector_db_manager.existing_collections:
            try:
                results = self.vector_searcher.vector_db_manager.search_in_collection(
                    collection_name=collection_name, query=vector_query
                )
                all_results.extend(results)
            except Exception as e:
                logger.warning(f"⚠️ 集合 {collection_name} 搜索失败: {e}")

        # 排序并取Top-K
        all_results.sort(key=lambda x: x.score, reverse=True)
        top_results = all_results[:top_k]

        search_time = time.time() - start_time

        return EnhancedSearchResult(
            query=query,
            results=top_results,
            total_found=len(all_results),
            search_time=search_time,
            mode_used=SearchMode.VECTOR_ONLY,
            vector_search_time=search_time,
            average_score=np.mean([r.score for r in top_results]) if top_results else 0.0,
            metadata={"search_method": "vector_only"},
        )

    async def _rerank_top_k_search(self, query: str, top_k: int) -> EnhancedSearchResult:
        """Rerank Top-K搜索 (推荐模式)"""
        vector_start = time.time()

        # 1. 向量搜索获取更多候选
        initial_results = await self._vector_only_search(query, self.config.initial_top_k)

        vector_time = time.time() - vector_start

        if not initial_results.results:
            return initial_results

        # 2. 准备Rerank输入
        rerank_start = time.time()
        rerank_items = []
        for r in initial_results.results:
            # 从payload中提取所有可用文本字段
            text_parts = []

            # 优先使用content字段
            content = r.payload.get("content", "")
            if content:
                text_parts.append(content)

            # 如果content为空,尝试其他字段
            if not text_parts:
                # 尝试常见的文本字段
                for key in ["title", "description", "text", "question", "answer"]:
                    value = r.payload.get(key, "")
                    if value:
                        text_parts.append(str(value))

                # 尝试法律相关字段
                for key in ["law_name", "article_number", "article_id", "chapter", "section"]:
                    value = r.payload.get(key, "")
                    if value:
                        text_parts.append(str(value))

                # 如果仍然没有文本,使用所有字符串字段
                if not text_parts:
                    for key, value in r.payload.items():
                        if isinstance(value, str) and value and len(value) > 0:
                            text_parts.append(value)

            # 组合所有文本部分
            combined_text = " ".join(text_parts)[:500]  # 限制总长度

            rerank_items.append(
                {"id": r.id, "content": combined_text, "score": r.score, "metadata": r.payload}
            )

        # 3. 执行Rerank
        rerank_result = self.reranker.rerank(query=query, items=rerank_items)

        rerank_time = time.time() - rerank_start

        # 4. 转换回VectorResult格式
        reranked_results = [
            VectorResult(id=item["id"], score=score, payload=item.get("metadata", {}))
            for item, score in zip(rerank_result.reranked_items, rerank_result.reranked_scores, strict=False)
        ][:top_k]

        return EnhancedSearchResult(
            query=query,
            results=reranked_results,
            total_found=initial_results.total_found,
            search_time=vector_time + rerank_time,
            mode_used=SearchMode.RERANK_TOP_K,
            vector_search_time=vector_time,
            rerank_time=rerank_time,
            average_score=np.mean([r.score for r in reranked_results]) if reranked_results else 0.0,
            metadata={
                "search_method": "rerank_top_k",
                "initial_count": len(initial_results.results),
                "rerank_method": rerank_result.mode.value,
            },
        )

    async def _rerank_full_search(self, query: str, top_k: int) -> EnhancedSearchResult:
        """全量Rerank搜索"""
        # 使用Reranker的全量模式
        vector_start = time.time()

        # 向量搜索
        initial_results = await self._vector_only_search(query, self.config.initial_top_k)

        vector_time = time.time() - vector_start

        if not initial_results.results:
            return initial_results

        # 全量Rerank
        rerank_start = time.time()

        rerank_items = []
        for r in initial_results.results:
            # 从payload中提取所有可用文本字段
            text_parts = []

            # 优先使用content字段
            content = r.payload.get("content", "")
            if content:
                text_parts.append(content)

            # 如果content为空,尝试其他字段
            if not text_parts:
                # 尝试常见的文本字段
                for key in ["title", "description", "text", "question", "answer"]:
                    value = r.payload.get(key, "")
                    if value:
                        text_parts.append(str(value))

                # 尝试法律相关字段
                for key in ["law_name", "article_number", "article_id", "chapter", "section"]:
                    value = r.payload.get(key, "")
                    if value:
                        text_parts.append(str(value))

                # 如果仍然没有文本,使用所有字符串字段
                if not text_parts:
                    for key, value in r.payload.items():
                        if isinstance(value, str) and value and len(value) > 0:
                            text_parts.append(value)

            # 组合所有文本部分
            combined_text = " ".join(text_parts)[:500]  # 限制总长度

            rerank_items.append(
                {"id": r.id, "content": combined_text, "score": r.score, "metadata": r.payload}
            )

        rerank_result = self.reranker.rerank(
            query=query, items=rerank_items, config=RerankConfig(mode=RerankMode.FULL_RERANK)
        )

        rerank_time = time.time() - rerank_start

        reranked_results = [
            VectorResult(id=item["id"], score=score, payload=item.get("metadata", {}))
            for item, score in zip(rerank_result.reranked_items, rerank_result.reranked_scores, strict=False)
        ][:top_k]

        return EnhancedSearchResult(
            query=query,
            results=reranked_results,
            total_found=initial_results.total_found,
            search_time=vector_time + rerank_time,
            mode_used=SearchMode.RERANK_FULL,
            vector_search_time=vector_time,
            rerank_time=rerank_time,
            average_score=np.mean([r.score for r in reranked_results]) if reranked_results else 0.0,
            metadata={"search_method": "rerank_full"},
        )

    async def _adaptive_search(self, query: str, top_k: int) -> EnhancedSearchResult:
        """自适应搜索"""
        # 根据查询特征自动选择策略
        query_length = len(query)
        has_question = "?" in query or "?" in query

        # 复杂查询使用Rerank
        if query_length > 50 or has_question:
            logger.info("📊 检测到复杂查询,使用Rerank模式")
            return await self._rerank_top_k_search(query, top_k)
        else:
            logger.info("📊 检测到简单查询,使用向量模式")
            return await self._vector_only_search(query, top_k)

    def _generate_cache_key(self, query: str, mode: SearchMode, top_k: int) -> str:
        """生成缓存键"""
        import hashlib

        key_data = f"{query}|{mode.value}|{top_k}"
        return hashlib.md5(key_data.encode('utf-8'), usedforsecurity=False).hexdigest()

    def _get_from_cache(self, cache_key: str) -> EnhancedSearchResult | None:
        """从缓存获取"""
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.config.cache_ttl:
                return cached_data
            else:
                del self.cache[cache_key]
        return None

    def _save_to_cache(self, cache_key: str, result: EnhancedSearchResult) -> Any:
        """保存到缓存"""
        self.cache[cache_key] = (result, time.time())

        # 清理过期缓存
        current_time = time.time()
        expired_keys = [
            key
            for key, (_, timestamp) in self.cache.items()
            if current_time - timestamp > self.config.cache_ttl
        ]
        for key in expired_keys:
            del self.cache[key]

    def get_performance_stats(self) -> dict[str, Any]:
        """获取性能统计"""
        cache_hit_rate = (
            self.cache_stats["hits"] / self.cache_stats["total_queries"]
            if self.cache_stats["total_queries"] > 0
            else 0.0
        )

        return {
            "search_stats": {
                "total_searches": self.performance_stats["total_searches"],
                "avg_time": self.performance_stats["avg_time"],
                "mode_usage": self.performance_stats["mode_usage"],
            },
            "cache_stats": {
                "size": len(self.cache),
                "hit_rate": cache_hit_rate,
                "hits": self.cache_stats["hits"],
                "misses": self.cache_stats["misses"],
                "total_queries": self.cache_stats["total_queries"],
            },
            "config": {
                "mode": self.config.mode.value,
                "initial_top_k": self.config.initial_top_k,
                "final_top_k": self.config.final_top_k,
                "cache_enabled": self.config.enable_cache,
            },
        }

    async def close(self):
        """关闭搜索引擎"""
        if self.reranker:
            await self.reranker.close()

        # 清理缓存
        self.cache.clear()

        logger.info("✅ 搜索引擎已关闭")


# 全局单例
_enhanced_searcher: EnhancedVectorSearchWithReranker | None = None


async def get_enhanced_searcher(
    config: EnhancedSearchConfig = None,
) -> EnhancedVectorSearchWithReranker:
    """获取增强搜索引擎单例"""
    global _enhanced_searcher

    if _enhanced_searcher is None:
        _enhanced_searcher = EnhancedVectorSearchWithReranker(config)
        await _enhanced_searcher._ensure_components()

    return _enhanced_searcher


# 便捷函数
async def enhanced_search(
    query: str, mode: SearchMode = SearchMode.RERANK_TOP_K, top_k: int = 10
) -> EnhancedSearchResult:
    """便捷函数:增强搜索"""
    searcher = await get_enhanced_searcher()
    return await searcher.search(query, mode, top_k)
