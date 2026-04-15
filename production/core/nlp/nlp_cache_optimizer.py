#!/usr/bin/env python3
"""
NLP缓存优化器 - 提升NLP处理性能(增强版 v2.0)
NLP Cache Optimizer - Boost NLP Processing Performance

通过智能缓存策略大幅提升NLP操作性能,包括:
1. 语义分析缓存
2. 意图识别缓存
3. 实体提取缓存
4. 向量嵌入缓存

核心优化:
- 🔧 新增:LFU缓存算法(最适合NLP重复查询场景)
- 🔧 新增:混合缓存策略(LFU + LRU)
- 语义哈希键
- 批处理优化
- 自动缓存清理
- 内存限制和主动淘汰策略

作者: 小诺AI团队
创建时间: 2025-01-09
更新时间: 2026-01-25(升级LFU缓存策略)
"""

from __future__ import annotations
import hashlib
import json
import logging
import os
import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)

# 导入新的LFU缓存系统
_lfu_available: bool = False
create_cache: Callable[..., Any] | None = None
LFUCache: Any | None = None
HybridCache: Any | None = None

try:
    from core.nlp.lfu_cache import HybridCache, LFUCache, create_cache

    _lfu_available = True
except ImportError:
    _lfu_available = False
    logger.warning("⚠️ LFU缓存模块不可用,将使用LRU缓存")

# 向后兼容的别名
LFU_AVAILABLE = _lfu_available


class LRUCache:
    """带LRU淘汰策略的缓存实现"""

    def __init__(self, max_size: int = 10000, ttl: int = 3600):
        """
        初始化LRU缓存

        Args:
            max_size: 最大缓存条目数
            ttl: 缓存生存时间(秒)
        """
        self.max_size = max_size
        self.ttl = ttl
        self.cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self.lock = threading.RLock()

    def get(self, key: str) -> Any | None:
        """获取缓存值"""
        with self.lock:
            if key in self.cache:
                value, timestamp = self.cache[key]
                if time.time() - timestamp < self.ttl:
                    # 移到末尾(标记为最近使用)
                    self.cache.move_to_end(key)
                    return value
                else:
                    # 过期,删除
                    del self.cache[key]
            return None

    def put(self, key: str, value: Any) -> None:
        """存储缓存值"""
        with self.lock:
            # 如果键已存在,更新并移到末尾
            if key in self.cache:
                self.cache[key] = (value, time.time())
                self.cache.move_to_end(key)
                return

            # 如果缓存满了,删除最旧的条目
            if len(self.cache) >= self.max_size:
                self.cache.popitem(last=False)

            # 添加新条目到末尾
            self.cache[key] = (value, time.time())

    def cleanup_expired(self) -> int:
        """清理过期条目"""
        with self.lock:
            expired_keys = [k for k, (_, ts) in self.cache.items() if time.time() - ts >= self.ttl]
            for key in expired_keys:
                del self.cache[key]
            return len(expired_keys)

    def clear(self) -> None:
        """清空缓存"""
        with self.lock:
            self.cache.clear()

    def size(self) -> int:
        """获取缓存大小"""
        return len(self.cache)

    def get_stats(self) -> dict[str, Any]:
        """获取缓存统计"""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "usage_percent": (len(self.cache) / self.max_size * 100) if self.max_size > 0 else 0,
        }


class NLPCacheOptimizer:
    """NLP缓存优化器(v2.0:LFU策略 + 内存限制 + 主动淘汰)"""

    # 默认配置
    DEFAULT_MAX_CACHE_SIZE = 10000
    DEFAULT_TTL = 3600  # 1小时
    DEFAULT_MEMORY_LIMIT_MB = 500  # 500MB内存限制
    DEFAULT_CACHE_STRATEGY = "lfu"  # 默认使用LFU策略

    def __init__(
        self,
        max_cache_size: int = DEFAULT_MAX_CACHE_SIZE,
        ttl: int = DEFAULT_TTL,
        memory_limit_mb: int = DEFAULT_MEMORY_LIMIT_MB,
        enable_aggressive_cleanup: bool = True,
        cache_strategy: str = DEFAULT_CACHE_STRATEGY,
    ):
        """
        初始化NLP缓存优化器(v2.0)

        Args:
            max_cache_size: 单个缓存的最大条目数
            ttl: 缓存生存时间(秒)
            memory_limit_mb: 总内存限制(MB)
            enable_aggressive_cleanup: 是否启用主动清理
            cache_strategy: 缓存策略 ("lfu", "lru", "adaptive")
        """
        self.max_cache_size = max_cache_size
        self.ttl = ttl
        self.memory_limit_mb = memory_limit_mb
        self.enable_aggressive_cleanup = enable_aggressive_cleanup
        self.cache_strategy = cache_strategy

        # 🔧 根据策略创建缓存实例
        if _lfu_available and create_cache is not None and cache_strategy in ["lfu", "adaptive"]:
            # 使用LFU或混合缓存
            self._semantic_cache = create_cache(cache_strategy, max_cache_size, ttl)
            self._intent_cache = create_cache(cache_strategy, max_cache_size, ttl)
            self._entity_cache = create_cache(cache_strategy, max_cache_size, ttl)
            self._embedding_cache = create_cache(cache_strategy, max_cache_size, ttl)
            logger.info(f"✅ 使用{cache_strategy.upper()}缓存策略")
        else:
            # 回退到LRU缓存
            self._semantic_cache = LRUCache(max_cache_size, ttl)
            self._intent_cache = LRUCache(max_cache_size, ttl)
            self._entity_cache = LRUCache(max_cache_size, ttl)
            self._embedding_cache = LRUCache(max_cache_size, ttl)
            logger.info("✅ 使用LRU缓存策略")

        # 缓存统计
        self._cache_stats = {
            "semantic": {"hits": 0, "misses": 0, "evictions": 0},
            "intent": {"hits": 0, "misses": 0, "evictions": 0},
            "entity": {"hits": 0, "misses": 0, "evictions": 0},
            "embedding": {"hits": 0, "misses": 0, "evictions": 0},
        }

        # 缓存映射(用于统一访问)
        self._caches = {
            "semantic": self._semantic_cache,
            "intent": self._intent_cache,
            "entity": self._entity_cache,
            "embedding": self._embedding_cache,
        }

        logger.info(
            f"✅ NLP缓存优化器v2.0初始化完成"
            f" - 策略: {cache_strategy.upper()}, "
            f"最大条目: {max_cache_size}, "
            f"内存限制: {memory_limit_mb}MB, "
            f"TTL: {ttl}秒"
        )

    def _generate_cache_key(self, text: str, operation: str, **kwargs: Any) -> str:
        """
        生成缓存键

        Args:
            text: 输入文本
            operation: 操作类型
            **kwargs: 额外参数

        Returns:
            缓存键
        """
        # 创建规范化输入
        normalized_text = text.strip().lower()

        # 创建参数字符串
        params_str = json.dumps(kwargs, sort_keys=True)

        # 生成哈希键
        key_data = f"{operation}:{normalized_text}:{params_str}"
        cache_key = hashlib.sha256(key_data.encode()).hexdigest()[:32]

        return cache_key

    def _is_expired(self, timestamp: float) -> bool:
        """检查缓存是否过期"""
        return time.time() - timestamp > self.ttl

    def _check_memory_usage(self) -> float:
        """检查当前进程内存使用(MB)"""
        try:
            import psutil

            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024  # 转换为MB
        except ImportError:
            # 如果psutil不可用,返回0表示无法检测
            return 0.0

    def _aggressive_cleanup_if_needed(self) -> None:
        """如果内存使用过高,执行主动清理"""
        if not self.enable_aggressive_cleanup:
            return

        memory_mb = self._check_memory_usage()
        if memory_mb > self.memory_limit_mb:
            logger.warning(
                f"⚠️ 内存使用过高: {memory_mb:.1f}MB > {self.memory_limit_mb}MB, " "执行主动清理"
            )
            # 清理所有缓存的过期条目
            for cache_name, cache in self._caches.items():
                removed = cache.cleanup_expired()
                if removed > 0:
                    self._cache_stats[cache_name]["evictions"] += removed
                    logger.info(f"  🧹 {cache_name}缓存: 清理{removed}条过期数据")

    def get_from_semantic_cache(
        self, text: str, operation: str = "semantic", **kwargs: Any
    ) -> Any | None:
        """从语义缓存获取结果"""
        cache_key = self._generate_cache_key(text, operation, **kwargs)
        result = self._semantic_cache.get(cache_key)

        if result is not None:
            self._cache_stats["semantic"]["hits"] += 1
        else:
            self._cache_stats["semantic"]["misses"] += 1

        return result

    def put_to_semantic_cache(
        self, text: str, result: Any, operation: str = "semantic", **kwargs: Any
    ) -> None:
        """存储结果到语义缓存"""
        cache_key = self._generate_cache_key(text, operation, **kwargs)
        self._semantic_cache.put(cache_key, result)

        # 检查是否需要主动清理
        self._aggressive_cleanup_if_needed()

    def get_from_intent_cache(
        self, text: str, operation: str = "intent", **kwargs: Any
    ) -> Any | None:
        """从意图缓存获取结果"""
        cache_key = self._generate_cache_key(text, operation, **kwargs)
        result = self._intent_cache.get(cache_key)

        if result is not None:
            self._cache_stats["intent"]["hits"] += 1
        else:
            self._cache_stats["intent"]["misses"] += 1

        return result

    def put_to_intent_cache(
        self, text: str, result: Any, operation: str = "intent", **kwargs: Any
    ) -> None:
        """存储结果到意图缓存"""
        cache_key = self._generate_cache_key(text, operation, **kwargs)
        self._intent_cache.put(cache_key, result)
        self._aggressive_cleanup_if_needed()

    def get_from_entity_cache(
        self, text: str, operation: str = "entity", **kwargs: Any
    ) -> Any | None:
        """从实体缓存获取结果"""
        cache_key = self._generate_cache_key(text, operation, **kwargs)
        result = self._entity_cache.get(cache_key)

        if result is not None:
            self._cache_stats["entity"]["hits"] += 1
        else:
            self._cache_stats["entity"]["misses"] += 1

        return result

    def put_to_entity_cache(
        self, text: str, result: Any, operation: str = "entity", **kwargs: Any
    ) -> None:
        """存储结果到实体缓存"""
        cache_key = self._generate_cache_key(text, operation, **kwargs)
        self._entity_cache.put(cache_key, result)
        self._aggressive_cleanup_if_needed()

    def get_from_embedding_cache(
        self, text: str, operation: str = "embedding", **kwargs: Any
    ) -> Any | None:
        """从向量嵌入缓存获取结果"""
        cache_key = self._generate_cache_key(text, operation, **kwargs)
        result = self._embedding_cache.get(cache_key)

        if result is not None:
            self._cache_stats["embedding"]["hits"] += 1
        else:
            self._cache_stats["embedding"]["misses"] += 1

        return result

    def put_to_embedding_cache(
        self, text: str, result: Any, operation: str = "embedding", **kwargs: Any
    ) -> None:
        """存储结果到向量嵌入缓存"""
        cache_key = self._generate_cache_key(text, operation, **kwargs)
        self._embedding_cache.put(cache_key, result)
        self._aggressive_cleanup_if_needed()

    def get_cache_stats(self) -> dict[str, Any]:
        """获取缓存统计信息(增强版)"""
        stats = {}

        for cache_type, counter in self._cache_stats.items():
            total = counter["hits"] + counter["misses"]
            hit_rate = (counter["hits"] / total * 100) if total > 0 else 0

            # 获取缓存状态
            cache = self._caches.get(cache_type)
            cache_info = cache.get_stats() if cache else {}

            stats[cache_type] = {
                "hits": counter["hits"],
                "misses": counter["misses"],
                "evictions": counter.get("evictions", 0),
                "hit_rate": f"{hit_rate:.2f}%",
                "total_requests": total,
                "cache_size": cache_info.get("size", 0),
                "cache_usage": f"{cache_info.get('usage_percent', 0):.1f}%",
            }

        # 添加内存使用信息
        stats["memory_usage_mb"] = self._check_memory_usage()
        stats["memory_limit_mb"] = self.memory_limit_mb

        return stats

    def clear_all_caches(self) -> None:
        """清空所有缓存"""
        for cache in self._caches.values():
            cache.clear()

        # 重置统计
        for cache_type in self._cache_stats:
            self._cache_stats[cache_type] = {"hits": 0, "misses": 0, "evictions": 0}

        logger.info("🧹 所有NLP缓存已清空")

    def cleanup_expired_entries(self) -> dict[str, int]:
        """清理所有过期缓存"""
        results = {}

        for cache_name, cache in self._caches.items():
            removed = cache.cleanup_expired()
            results[cache_name] = removed
            if removed > 0:
                self._cache_stats[cache_name]["evictions"] += removed

        total_cleaned = sum(results.values())
        if total_cleaned > 0:
            logger.info(f"🧹 清理了 {total_cleaned} 条过期缓存")

        return results


# 装饰器:自动缓存NLP操作
def cached_nlp_operation(
    cache_type: str = "semantic",
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    NLP操作缓存装饰器

    Args:
        cache_type: 缓存类型 (semantic, intent, entity, embedding)
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(self, *args: Any, **kwargs: Any) -> Any:
            # 确保优化器存在
            if not hasattr(self, "nlp_cache_optimizer"):
                return func(self, *args, **kwargs)

            optimizer = self.nlp_cache_optimizer
            text = args[0] if args else kwargs.get("text", "")

            # 尝试从缓存获取
            cache_getter = getattr(optimizer, f"get_from_{cache_type}_cache")
            cache_putter = getattr(optimizer, f"put_to_{cache_type}_cache")

            cached_result = cache_getter(text, **kwargs)
            if cached_result is not None:
                return cached_result

            # 执行原函数
            result = func(self, *args, **kwargs)

            # 存储到缓存
            cache_putter(text, result, **kwargs)

            return result

        return wrapper

    return decorator


# 装饰器:批处理优化
def batch_processing(batch_size: int = 32) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    批处理优化装饰器

    Args:
        batch_size: 批处理大小
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(self, texts: list[str], **kwargs: Any) -> Any:
            if len(texts) <= batch_size:
                return func(self, texts, **kwargs)

            # 分批处理
            results = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                batch_results = func(self, batch, **kwargs)
                results.extend(batch_results)

            return results

        return wrapper

    return decorator


# 全局优化器实例
_global_optimizer: NLPCacheOptimizer | None = None


def get_nlp_cache_optimizer() -> NLPCacheOptimizer:
    """获取全局NLP缓存优化器"""
    global _global_optimizer
    if _global_optimizer is None:
        _global_optimizer = NLPCacheOptimizer()
    return _global_optimizer


if __name__ == "__main__":
    # 测试缓存优化器
    optimizer = NLPCacheOptimizer(max_cache_size=100, ttl=60)

    print("🧪 测试NLP缓存优化器...")

    # 测试语义缓存
    text1 = "什么是专利申请?"
    result1 = optimizer.get_from_semantic_cache(text1)
    print(f"第一次查询: {result1}")  # 应该是None

    optimizer.put_to_semantic_cache(text1, "专利申请是向专利局提交申请的法律程序...")
    result2 = optimizer.get_from_semantic_cache(text1)
    print(f"第二次查询: {result2}")  # 应该有结果

    # 查看统计
    stats = optimizer.get_cache_stats()
    print("\n📊 缓存统计:")
    for cache_type, stat in stats.items():
        print(f"  {cache_type}: 命中率 {stat['hit_rate']}")
