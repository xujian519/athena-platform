#!/usr/bin/env python3
"""
语义缓存模块
Semantic Cache Module

为搜索系统提供智能的语义缓存,支持相似查询的缓存命中

作者: Athena AI系统
创建时间: 2025-12-19
版本: 1.0.0
"""

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """缓存条目"""

    query: str
    query_embedding: np.ndarray  # 查询的向量表示
    results: dict[str, Any]  # 搜索结果
    timestamp: float  # 缓存时间戳
    ttl: int  # 生存时间(秒)
    hit_count: int = 0  # 命中次数

    @property
    def age(self) -> float:
        """获取缓存年龄(秒)"""
        return time.time() - self.timestamp

    @property
    def is_expired(self) -> bool:
        """检查缓存是否过期"""
        return self.age > self.ttl


class SemanticCache:
    """语义缓存器(基于相似度的智能缓存)"""

    def __init__(
        self,
        similarity_threshold: float = 0.85,
        default_ttl: int = 3600,
        max_size: int = 1000,
        model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
    ):
        """
        初始化语义缓存

        Args:
            similarity_threshold: 相似度阈值(0-1),高于此值的查询会被认为是相似的
            default_ttl: 默认缓存生存时间(秒)
            max_size: 最大缓存条目数
            model_name: 使用的语义模型名称
        """
        self.similarity_threshold = similarity_threshold
        self.default_ttl = default_ttl
        self.max_size = max_size

        # 缓存存储: query_hash -> CacheEntry
        self._cache: dict[str, CacheEntry] = {}

        # 查询到缓存键的映射: query_embedding_hash -> cache_key
        self._embedding_index: dict[str, str] = {}

        # 语义模型(懒加载)
        self._model: SentenceTransformer | None = None
        self._model_name = model_name

        logger.info(
            f"✅ 语义缓存初始化完成 "
            f"(相似度阈值: {similarity_threshold}, TTL: {default_ttl}s, 最大容量: {max_size})"
        )

    def _get_model(self) -> SentenceTransformer:
        """获取语义模型(懒加载)"""
        if self._model is None:
            logger.info(f"📥 加载语义模型: {self._model_name}")
            self._model = SentenceTransformer(self._model_name, device="cpu")
            logger.info("✅ 语义模型加载完成")
        return self._model

    def _get_cache_key(self, query: str) -> str:
        """
        生成缓存键

        Args:
            query: 搜索查询

        Returns:
            缓存键(MD5哈希)
        """
        normalized = query.strip().lower()
        return hashlib.md5(normalized.encode('utf-8'), usedforsecurity=False).hexdigest()

    def _get_embedding_hash(self, embedding: np.ndarray) -> str:
        """
        生成向量哈希

        Args:
            embedding: 向量表示

        Returns:
            向量哈希
        """
        # 将向量转换为字节数组并计算哈希
        embedding_bytes = embedding.tobytes()
        return hashlib.sha256(embedding_bytes).hexdigest()[:16]

    def _compute_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """
        计算两个向量的余弦相似度

        Args:
            emb1: 向量1
            emb2: 向量2

        Returns:
            相似度(0-1)
        """
        # 余弦相似度
        dot_product = np.dot(emb1, emb2)
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def _evict_expired(self) -> Any:
        """清理过期的缓存条目"""
        expired_keys = [key for key, entry in self._cache.items() if entry.is_expired]

        for key in expired_keys:
            entry = self._cache.pop(key, None)
            if entry and entry.query_embedding is not None:
                emb_hash = self._get_embedding_hash(entry.query_embedding)
                self._embedding_index.pop(emb_hash, None)

        if expired_keys:
            logger.debug(f"🧹 清理了 {len(expired_keys)} 个过期缓存条目")

    def _evict_lru(self) -> Any:
        """使用LRU策略淘汰缓存(当缓存满时)"""
        if len(self._cache) <= self.max_size:
            return

        # 按命中次数和时间排序
        sorted_entries = sorted(
            self._cache.items(),
            key=lambda x: (x[1].hit_count, x[1].timestamp),
        )

        # 淘汰最不常用的条目
        num_to_evict = len(self._cache) - self.max_size
        for key, _ in sorted_entries[:num_to_evict]:
            entry = self._cache.pop(key, None)
            if entry and entry.query_embedding is not None:
                emb_hash = self._get_embedding_hash(entry.query_embedding)
                self._embedding_index.pop(emb_hash, None)

        logger.debug(f"🗑️ 使用LRU策略淘汰了 {num_to_evict} 个缓存条目")

    def get(self, query: str) -> dict[str, Any] | None:
        """
        从缓存中获取搜索结果

        Args:
            query: 搜索查询

        Returns:
            缓存的搜索结果,如果未找到则返回None
        """
        # 首先尝试精确匹配
        exact_key = self._get_cache_key(query)
        if exact_key in self._cache:
            entry = self._cache[exact_key]
            if not entry.is_expired:
                entry.hit_count += 1
                logger.debug(f"✅ 缓存精确命中: {query[:50]}...")
                return entry.results
            else:
                # 清理过期缓存
                self._cache.pop(exact_key)

        # 尝试语义匹配
        try:
            model = self._get_model()
            query_embedding = model.encode([query])[0]

            # 检查是否有相似的查询
            for _cache_key, entry in self._cache.items():
                if entry.query_embedding is None:
                    continue

                similarity = self._compute_similarity(query_embedding, entry.query_embedding)

                if similarity >= self.similarity_threshold and not entry.is_expired:
                    entry.hit_count += 1
                    logger.debug(f"✅ 缓存语义命中 (相似度: {similarity:.3f}): {query[:50]}...")
                    return entry.results

        except Exception as e:
            logger.warning(f"⚠️ 语义匹配失败: {e}")

        return None

    def set(
        self,
        query: str,
        results: dict[str, Any],        ttl: int | None = None,
        compute_embedding: bool = True,
    ):
        """
        将搜索结果存入缓存

        Args:
            query: 搜索查询
            results: 搜索结果
            ttl: 生存时间(秒),None表示使用默认值
            compute_embedding: 是否计算语义向量
        """
        # 先进行清理
        self._evict_expired()
        self._evict_lru()

        cache_key = self._get_cache_key(query)
        ttl = ttl or self.default_ttl

        # 计算语义向量
        query_embedding = None
        if compute_embedding:
            try:
                model = self._get_model()
                query_embedding = model.encode([query])[0]
            except Exception as e:
                logger.warning(f"⚠️ 计算语义向量失败: {e}")

        # 创建缓存条目
        entry = CacheEntry(
            query=query,
            query_embedding=query_embedding,
            results=results,
            timestamp=time.time(),
            ttl=ttl,
            hit_count=0,
        )

        # 存储缓存
        self._cache[cache_key] = entry

        # 更新向量索引
        if query_embedding is not None:
            emb_hash = self._get_embedding_hash(query_embedding)
            self._embedding_index[emb_hash] = cache_key

        logger.debug(f"💾 已缓存查询: {query[:50]}... (TTL: {ttl}s)")

    def clear(self) -> Any:
        """清空所有缓存"""
        self._cache.clear()
        self._embedding_index.clear()
        logger.info("🧹 已清空所有缓存")

    def get_stats(self) -> dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            统计信息字典
        """
        total_hits = sum(entry.hit_count for entry in self._cache.values())

        return {
            "total_entries": len(self._cache),
            "total_hits": total_hits,
            "avg_hit_count": total_hits / len(self._cache) if self._cache else 0,
            "max_size": self.max_size,
            "similarity_threshold": self.similarity_threshold,
            "default_ttl": self.default_ttl,
            "model_name": self._model_name,
        }


class SimpleCache:
    """简单内存缓存(不使用语义相似度)"""

    def __init__(self, default_ttl: int = 3600, max_size: int = 10000):
        """
        初始化简单缓存

        Args:
            default_ttl: 默认缓存生存时间(秒)
            max_size: 最大缓存条目数
        """
        self.default_ttl = default_ttl
        self.max_size = max_size
        self._cache: dict[str, tuple[float, dict[str, Any]]] = {}

        logger.info(f"✅ 简单缓存初始化完成 (TTL: {default_ttl}s, 最大容量: {max_size})")

    def _get_cache_key(self, *args, **kwargs) -> str:
        """
        生成缓存键

        Args:
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            缓存键
        """
        key_dict = {"args": args, "kwargs": kwargs}
        key_str = json.dumps(key_dict, sort_keys=True, default=str)
        return hashlib.sha256(key_str.encode()).hexdigest()

    def get(self, *args, **kwargs) -> dict[str, Any] | None:
        """
        从缓存中获取结果

        Args:
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            缓存的结果,如果未找到则返回None
        """
        key = self._get_cache_key(*args, **kwargs)

        if key in self._cache:
            timestamp, result = self._cache[key]

            # 检查是否过期
            if time.time() - timestamp < self.default_ttl:
                return result
            else:
                # 清理过期缓存
                del self._cache[key]

        return None

    def set(self, result: dict[int, Any] | None, *args) -> Any:
        """
        将结果存入缓存

        Args:
            result: 要缓存的结果
            ttl: 生存时间(秒),None表示使用默认值
            *args: 位置参数
            **kwargs: 关键字参数
        """
        key = self._get_cache_key(*args, **kwargs)
        ttl = ttl or self.default_ttl

        # 如果缓存已满,清理所有过期的条目
        if len(self._cache) >= self.max_size:
            current_time = time.time()
            expired_keys = [
                k for k, (ts, _) in self._cache.items() if current_time - ts >= self.default_ttl
            ]
            for k in expired_keys:
                del self._cache[k]

        # 如果仍然满了,删除最旧的条目
        if len(self._cache) >= self.max_size:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][0])
            del self._cache[oldest_key]

        self._cache[key] = (time.time(), result)

    def clear(self) -> Any:
        """清空所有缓存"""
        self._cache.clear()
        logger.info("🧹 已清空所有简单缓存")

    def get_stats(self) -> dict[str, Any]:
        """获取缓存统计信息"""
        return {
            "total_entries": len(self._cache),
            "max_size": self.max_size,
            "default_ttl": self.default_ttl,
        }


# 全局缓存实例
_semantic_cache: SemanticCache | None = None
_simple_cache: SimpleCache | None = None


def get_semantic_cache() -> SemanticCache:
    """获取全局语义缓存实例"""
    global _semantic_cache
    if _semantic_cache is None:
        _semantic_cache = SemanticCache()
    return _semantic_cache


def get_simple_cache() -> SimpleCache:
    """获取全局简单缓存实例"""
    global _simple_cache
    if _simple_cache is None:
        _simple_cache = SimpleCache()
    return _simple_cache


# 导出
__all__ = [
    "CacheEntry",
    "SemanticCache",
    "SimpleCache",
    "get_semantic_cache",
    "get_simple_cache",
]
