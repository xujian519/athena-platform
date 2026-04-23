#!/usr/bin/env python3
from __future__ import annotations
"""
智能缓存淘汰策略
Intelligent Cache Eviction Policy

基于多种策略智能地淘汰缓存条目,优化缓存命中率。

功能特性:
1. 多种淘汰策略
2. 混合策略支持
3. 自适应调整
4. 访问模式学习
5. 内存管理

淘汰策略:
- LRU (Least Recently Used) - 最近最少使用
- LFU (Least Frequently Used) - 最不经常使用
- FIFO (First In First Out) - 先进先出
- LFRU (Least Frequently Recently Used) - 混合策略
- ARC (Adaptive Replacement Cache) - 自适应替换
- SIZE - 基于大小淘汰
- TTL - 基于时间淘汰

作者: Athena AI系统
创建时间: 2026-01-25
版本: 1.0.0
"""

import heapq
import logging
import time
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class EvictionPolicy(Enum):
    """淘汰策略"""

    LRU = "lru"  # 最近最少使用
    LFU = "lfu"  # 最不经常使用
    FIFO = "fifo"  # 先进先出
    LFRU = "lfru"  # 最不频繁最近使用
    ARC = "arc"  # 自适应替换
    SIZE = "size"  # 基于大小
    TTL = "ttl"  # 基于时间
    ADAPTIVE = "adaptive"  # 自适应


@dataclass
class CacheEntry:
    """缓存条目"""

    key: str
    value: Any
    size: int = 1  # 条目大小(字节)
    access_count: int = 0  # 访问次数
    last_access: float = field(default_factory=time.time)  # 最后访问时间
    created_at: float = field(default_factory=time.time)  # 创建时间
    expires_at: Optional[float] = None  # 过期时间
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def age(self) -> float:
        """条目年龄(秒)"""
        return time.time() - self.created_at

    @property
    def time_since_last_access(self) -> float:
        """距最后访问时间(秒)"""
        return time.time() - self.last_access

    @property
    def is_expired(self) -> bool:
        """是否过期"""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at

    def touch(self) -> None:
        """更新访问信息"""
        self.access_count += 1
        self.last_access = time.time()


@dataclass
class EvictionResult:
    """淘汰结果"""

    evicted_keys: list[str]  # 被淘汰的键
    evicted_size: int = 0  # 淘汰的总大小
    evicted_count: int = 0  # 淘汰的条目数
    reason: str = ""  # 淘汰原因
    timestamp: float = field(default_factory=time.time)


@dataclass
class CacheStats:
    """缓存统计"""

    total_hits: int = 0
    total_misses: int = 0
    total_evictions: int = 0
    total_size: int = 0  # 总大小(字节)
    entry_count: int = 0  # 条目数量

    # 访问模式
    access_frequency: dict[str, int] = field(default_factory=dict)
    access_pattern: dict[str, list[float]] = field(default_factory=dict)

    # 性能指标
    avg_access_time: float = 0.0

    @property
    def hit_rate(self) -> float:
        """命中率"""
        total = self.total_hits + self.total_misses
        return self.total_hits / max(total, 1)

    @property
    def miss_rate(self) -> float:
        """未命中率"""
        return 1.0 - self.hit_rate


class LRUPolicy:
    """LRU淘汰策略"""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()

    def get(self, key: str) -> CacheEntry | None:
        """获取条目"""
        if key in self._cache:
            # 移到末尾(最近使用)
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    def put(self, key: str, entry: CacheEntry) -> bool:
        """添加条目"""
        if key in self._cache:
            self._cache.move_to_end(key)
        else:
            self._cache[key] = entry

        # 检查是否需要淘汰
        while len(self._cache) > self.max_size:
            self._cache.popitem(last=False)  # 移除最旧的
            return True
        return False

    def evict(self, count: int = 1) -> EvictionResult:
        """淘汰条目"""
        evicted_keys = []
        evicted_size = 0

        for _ in range(count):
            if not self._cache:
                break
            key, entry = self._cache.popitem(last=False)
            evicted_keys.append(key)
            evicted_size += entry.size

        return EvictionResult(
            evicted_keys=evicted_keys,
            evicted_size=evicted_size,
            evicted_count=len(evicted_keys),
            reason="LRU",
        )


class LFUPolicy:
    """LFU淘汰策略"""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: dict[str, CacheEntry] = {}
        self._min_heap: list[tuple[int, float, str]] = []  # (access_count, last_access, key)

    def get(self, key: str) -> CacheEntry | None:
        if key in self._cache:
            entry = self._cache[key]
            entry.touch()
            return entry
        return None

    def put(self, key: str, entry: CacheEntry) -> bool:
        """添加条目"""
        entry.touch()
        self._cache[key] = entry

        # 更新堆
        heapq.heappush(self._min_heap, (entry.access_count, entry.last_access, key))

        # 检查是否需要淘汰
        while len(self._cache) > self.max_size:
            self._evict_one()
            return True
        return False

    def _evict_one(self) -> None:
        """淘汰一个条目"""
        while self._min_heap:
            access_count, last_access, key = self._min_heap[0]

            # 检查是否是过时的堆条目
            if key in self._cache:
                entry = self._cache[key]
                if (entry.access_count, entry.last_access) == (access_count, last_access):
                    heapq.heappop(self._min_heap)
                    del self._cache[key]
                    return

            heapq.heappop(self._min_heap)

    def evict(self, count: int = 1) -> EvictionResult:
        evicted_keys = []
        evicted_size = 0

        for _ in range(count):
            if not self._cache:
                break

            # 找到访问次数最少的
            min_key = min(self._cache.keys(), key=lambda k: self._cache[k].access_count)
            entry = self._cache.pop(min_key)
            evicted_keys.append(min_key)
            evicted_size += entry.size

        return EvictionResult(
            evicted_keys=evicted_keys,
            evicted_size=evicted_size,
            evicted_count=len(evicted_keys),
            reason="LFU",
        )


class FIFOPolicy:
    """FIFO淘汰策略"""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._queue: list[str] = []

    def get(self, key: str) -> CacheEntry | None:
        if key in self._cache:
            return self._cache[key]
        return None

    def put(self, key: str, entry: CacheEntry) -> bool:
        if key not in self._cache:
            self._cache[key] = entry
            self._queue.append(key)
        else:
            self._cache[key] = entry

        # 检查是否需要淘汰
        while len(self._cache) > self.max_size:
            if self._queue:
                oldest = self._queue.pop(0)
                if oldest in self._cache:
                    del self._cache[oldest]
                    return True
        return False

    def evict(self, count: int = 1) -> EvictionResult:
        evicted_keys = []
        evicted_size = 0

        for _ in range(count):
            if not self._queue:
                break

            key = self._queue.pop(0)
            if key in self._cache:
                entry = self._cache.pop(key)
                evicted_keys.append(key)
                evicted_size += entry.size

        return EvictionResult(
            evicted_keys=evicted_keys,
            evicted_size=evicted_size,
            evicted_count=len(evicted_keys),
            reason="FIFO",
        )


class TTLPolicy:
    """TTL淘汰策略"""

    def __init__(self, default_ttl: float = 3600.0):
        self.default_ttl = default_ttl  # 默认TTL(秒)
        self._cache: dict[str, CacheEntry] = {}

    def get(self, key: str) -> CacheEntry | None:
        if key in self._cache:
            entry = self._cache[key]
            if entry.is_expired:
                del self._cache[key]
                return None
            entry.touch()
            return entry
        return None

    def put(
        self,
        key: str,
        entry: CacheEntry,
        ttl: Optional[float] = None,
    ) -> bool:
        """添加条目

        Args:
            key: 键
            entry: 条目
            ttl: 生存时间(秒),如果为None使用默认值
        """
        if ttl is not None:
            entry.expires_at = time.time() + ttl
        elif entry.expires_at is None:
            entry.expires_at = time.time() + self.default_ttl

        self._cache[key] = entry
        return False

    def evict_expired(self) -> EvictionResult:
        """淘汰过期条目"""
        evicted_keys = []
        evicted_size = 0

        expired_keys = [key for key, entry in self._cache.items() if entry.is_expired]

        for key in expired_keys:
            entry = self._cache.pop(key)
            evicted_keys.append(key)
            evicted_size += entry.size

        return EvictionResult(
            evicted_keys=evicted_keys,
            evicted_size=evicted_size,
            evicted_count=len(evicted_keys),
            reason="TTL expired",
        )

    def evict(self, count: int = 1) -> EvictionResult:
        """淘汰条目(按过期时间)"""
        evicted_keys = []
        evicted_size = 0

        # 按过期时间排序
        sorted_entries = sorted(
            self._cache.items(),
            key=lambda x: x[1].expires_at or float("inf"),
        )

        for i, (key, entry) in enumerate(sorted_entries):
            if i >= count:
                break
            del self._cache[key]
            evicted_keys.append(key)
            evicted_size += entry.size

        return EvictionResult(
            evicted_keys=evicted_keys,
            evicted_size=evicted_size,
            evicted_count=len(evicted_keys),
            reason="TTL",
        )


class AdaptivePolicy:
    """自适应淘汰策略

    根据访问模式动态选择最优的淘汰策略。
    """

    def __init__(
        self,
        max_size: int = 1000,
        max_memory: int = 1024 * 1024 * 1024,  # 1GB
        evaluation_interval: int = 100,  # 每100次访问评估一次
    ):
        self.max_size = max_size
        self.max_memory = max_memory
        self.evaluation_interval = evaluation_interval

        self._cache: dict[str, CacheEntry] = {}
        self._access_count = 0
        self._current_policy = EvictionPolicy.LRU
        self._policy_performance: dict[EvictionPolicy, list[float]] = defaultdict(list)

        self._stats = CacheStats()

    def get(self, key: str) -> CacheEntry | None:
        entry = self._cache.get(key)
        if entry:
            if not entry.is_expired:
                entry.touch()
                self._stats.total_hits += 1
                return entry
            else:
                # 过期,移除
                del self._cache[key]

        self._stats.total_misses += 1
        return None

    def put(self, key: str, entry: CacheEntry) -> bool:
        entry.touch()
        self._cache[key] = entry
        self._stats.entry_count = len(self._cache)
        self._stats.total_size = sum(e.size for e in self._cache.values())

        # 定期评估策略
        self._access_count += 1
        if self._access_count % self.evaluation_interval == 0:
            self._evaluate_and_adjust_policy()

        # 检查是否需要淘汰
        if self._should_evict():
            self._evict_with_current_policy()
            return True
        return False

    def _should_evict(self) -> bool:
        """检查是否需要淘汰"""
        # 检查条目数量
        if len(self._cache) > self.max_size:
            return True

        # 检查内存使用
        total_size = sum(e.size for e in self._cache.values())
        return total_size > self.max_memory

    def _evict_with_current_policy(self, count: int = 1) -> EvictionResult:
        """使用当前策略淘汰条目"""
        if self._current_policy == EvictionPolicy.LRU:
            return self._evict_lru(count)
        elif self._current_policy == EvictionPolicy.LFU:
            return self._evict_lfu(count)
        else:
            return self._evict_lru(count)

    def _evict_lru(self, count: int) -> EvictionResult:
        """LRU淘汰"""
        # 按最后访问时间排序
        sorted_entries = sorted(
            self._cache.items(),
            key=lambda x: x[1].last_access,
        )

        evicted_keys = []
        evicted_size = 0

        for i, (key, entry) in enumerate(sorted_entries):
            if i >= count:
                break
            del self._cache[key]
            evicted_keys.append(key)
            evicted_size += entry.size

        self._stats.total_evictions += len(evicted_keys)

        return EvictionResult(
            evicted_keys=evicted_keys,
            evicted_size=evicted_size,
            evicted_count=len(evicted_keys),
            reason=f"Adaptive ({self._current_policy.value})",
        )

    def _evict_lfu(self, count: int) -> EvictionResult:
        """LFU淘汰"""
        # 按访问次数排序
        sorted_entries = sorted(
            self._cache.items(),
            key=lambda x: x[1].access_count,
        )

        evicted_keys = []
        evicted_size = 0

        for i, (key, entry) in enumerate(sorted_entries):
            if i >= count:
                break
            del self._cache[key]
            evicted_keys.append(key)
            evicted_size += entry.size

        self._stats.total_evictions += len(evicted_keys)

        return EvictionResult(
            evicted_keys=evicted_keys,
            evicted_size=evicted_size,
            evicted_count=len(evicted_keys),
            reason=f"Adaptive ({self._current_policy.value})",
        )

    def _evaluate_and_adjust_policy(self) -> None:
        """评估并调整策略"""
        # 计算当前命中率
        hit_rate = self._stats.hit_rate

        # 记录当前策略性能
        self._policy_performance[self._current_policy].append(hit_rate)

        # 评估所有策略的性能
        if len(self._policy_performance[self._current_policy]) > 5:
            # 找到表现最好的策略
            best_policy = max(
                self._policy_performance.keys(),
                key=lambda p: sum(self._policy_performance[p]) / len(self._policy_performance[p]),
            )

            if best_policy != self._current_policy:
                logger.info(
                    f"🔄 策略切换: {self._current_policy.value} -> {best_policy.value} "
                    f"(命中率: {hit_rate:.2%})"
                )
                self._current_policy = best_policy

    def evict(self, count: int = 1) -> EvictionResult:
        return self._evict_with_current_policy(count)

    def get_stats(self) -> CacheStats:
        """获取统计信息"""
        return self._stats


class IntelligentCacheEvictor:
    """智能缓存淘汰器

    支持多种淘汰策略,并提供统一的接口。

    使用示例:
        >>> evictor = IntelligentCacheEvictor(
        >>>     policy=EvictionPolicy.ADAPTIVE,
        >>>     max_size=10000
        >>> )
        >>>
        >>> # 添加条目
        >>> entry = CacheEntry(key="key1", value=data)
        >>> evictor.put("key1", entry)
        >>>
        >>> # 获取条目
        >>> entry = evictor.get("key1")
        >>>
        >>> # 淘汰条目
        >>> result = evictor.evict(count=10)
    """

    def __init__(
        self,
        policy: EvictionPolicy = EvictionPolicy.ADAPTIVE,
        max_size: int = 10000,
        max_memory: int = 1024 * 1024 * 1024,  # 1GB
        default_ttl: Optional[float] = None,
    ):
        """初始化淘汰器

        Args:
            policy: 淘汰策略
            max_size: 最大条目数
            max_memory: 最大内存使用(字节)
            default_ttl: 默认TTL(秒)
        """
        self.policy = policy
        self.max_size = max_size
        self.max_memory = max_memory
        self.default_ttl = default_ttl

        # 根据策略创建具体实现
        if policy == EvictionPolicy.LRU:
            self._impl = LRUPolicy(max_size)
        elif policy == EvictionPolicy.LFU:
            self._impl = LFUPolicy(max_size)
        elif policy == EvictionPolicy.FIFO:
            self._impl = FIFOPolicy(max_size)
        elif policy == EvictionPolicy.TTL:
            self._impl = TTLPolicy(default_ttl or 3600.0)
        else:  # ADAPTIVE
            self._impl = AdaptivePolicy(max_size, max_memory)

        logger.info(f"🗑️ 初始化智能缓存淘汰器 (策略={policy.value})")

    def get(self, key: str) -> CacheEntry | None:
        """获取缓存条目"""
        return self._impl.get(key)

    def put(
        self,
        key: str,
        value: Any,
        size: int = 1,
        ttl: Optional[float] = None,
        **metadata: Any,
    ) -> bool:
        """添加缓存条目

        Args:
            key: 键
            value: 值
            size: 条目大小
            ttl: 生存时间(秒)
            **metadata: 额外元数据

        Returns:
            是否触发了淘汰
        """
        entry = CacheEntry(
            key=key,
            value=value,
            size=size,
            metadata=metadata,
        )

        # 设置TTL
        if ttl is not None:
            entry.expires_at = time.time() + ttl
        elif self.default_ttl is not None:
            entry.expires_at = time.time() + self.default_ttl

        return self._impl.put(key, entry)

    def evict(self, count: int = 1) -> EvictionResult:
        """淘汰条目"""
        return self._impl.evict(count)

    def get_stats(self) -> CacheStats:
        """获取统计信息"""
        if hasattr(self._impl, "get_stats"):
            return self._impl.get_stats()
        return CacheStats()


# 便捷函数
def create_cache_evictor(
    policy: EvictionPolicy = EvictionPolicy.ADAPTIVE,
    max_size: int = 10000,
) -> IntelligentCacheEvictor:
    """创建缓存淘汰器"""
    return IntelligentCacheEvictor(
        policy=policy,
        max_size=max_size,
    )


__all__ = [
    "CacheEntry",
    "CacheStats",
    "EvictionPolicy",
    "EvictionResult",
    "IntelligentCacheEvictor",
    "create_cache_evictor",
]
