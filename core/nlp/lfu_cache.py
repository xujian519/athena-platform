#!/usr/bin/env python3
"""
LFU缓存实现
Least Frequently Used Cache Implementation

LFU(最不经常使用)缓存策略,基于访问频率淘汰缓存条目
相比LRU(最近最少使用),LFU更适合NLP重复查询场景

作者: Athena平台团队
创建时间: 2026-01-25
"""

import heapq
import logging
import threading
import time
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple


logger = logging.getLogger(__name__)


class LFUCache:
    """LFU(最不经常使用)缓存实现"""

    def __init__(self, max_size: int = 10000, ttl: int = 3600):
        """
        初始化LFU缓存

        Args:
            max_size: 最大缓存条目数
            ttl: 缓存生存时间(秒)
        """
        self.max_size = max_size
        self.ttl = ttl

        # 缓存存储: key -> (value, frequency, access_time, heap_index)
        self.cache: dict[str, tuple[Any, int, float, int]] = {}

        # 频率堆: (frequency, access_time, key)
        # 使用堆来高效找到访问频率最低的条目
        self.heap: list[tuple[int, float, str]] = []

        # 锁保证线程安全
        self.lock = threading.RLock()

        # 访问计数器(用于打破频率相同的平局)
        self._access_counter = 0

    def _update_heap_index(self, key: str) -> None:
        """更新堆中条目的索引"""
        if key in self.cache:
            value, freq, access_time, _ = self.cache[key]
            # 新堆条目
            new_entry = (freq, access_time, key)
            heapq.heappush(self.heap, new_entry)
            # 更新缓存中的堆索引(简化处理,使用堆长度)
            self.cache[key] = (value, freq, access_time, len(self.heap) - 1)

    def _evict_lfu(self) -> None:
        """淘汰访问频率最低的条目"""
        while self.heap:
            freq, access_time, key = heapq.heappop(self.heap)

            # 检查堆顶条目是否仍在缓存中(且是最新的)
            if key in self.cache:
                _cached_value, cached_freq, cached_time, _ = self.cache[key]

                # 如果堆中的频率和时间与缓存中的匹配,说明这是有效条目
                if freq == cached_freq and access_time == cached_time:
                    del self.cache[key]
                    logger.debug(f"LFU淘汰: key={key[:20]}..., freq={freq}")
                    return
                # 否则,这是一个过时的堆条目,继续查找

    def get(self, key: str) -> Any | None:
        """获取缓存值"""
        with self.lock:
            if key in self.cache:
                value, freq, access_time, _ = self.cache[key]

                # 检查是否过期
                if time.time() - access_time < self.ttl:
                    # 增加访问频率
                    new_freq = freq + 1
                    new_access_time = time.time()

                    self.cache[key] = (value, new_freq, new_access_time, -1)
                    self._update_heap_index(key)

                    return value
                else:
                    # 过期,删除
                    del self.cache[key]

            return None

    def put(self, key: str, value: Any) -> None:
        """存储缓存值"""
        with self.lock:
            current_time = time.time()

            # 如果键已存在,更新频率
            if key in self.cache:
                _old_value, old_freq, _, _ = self.cache[key]
                # 更新并增加频率
                new_freq = old_freq + 1
                self.cache[key] = (value, new_freq, current_time, -1)
                self._update_heap_index(key)
                return

            # 如果缓存满了,淘汰频率最低的条目
            if len(self.cache) >= self.max_size:
                self._evict_lfu()

            # 添加新条目
            new_entry = (1, current_time, key)  # 初始频率为1
            heapq.heappush(self.heap, new_entry)
            self.cache[key] = (value, 1, current_time, len(self.heap) - 1)

    def cleanup_expired(self) -> int:
        """清理过期条目"""
        with self.lock:
            current_time = time.time()
            expired_keys = []

            for key, (_, _, access_time, _) in list(self.cache.items()):
                if current_time - access_time >= self.ttl:
                    expired_keys.append(key)

            for key in expired_keys:
                del self.cache[key]

            # 清理堆中的过期条目(延迟清理)
            if len(expired_keys) > len(self.heap) // 2:
                # 如果过期条目太多,重建堆
                self._rebuild_heap()

            return len(expired_keys)

    def _rebuild_heap(self) -> None:
        """重建堆(移除不存在的键)"""
        new_heap = []
        valid_keys = set(self.cache.keys())

        for entry in self.heap:
            _, _, key = entry
            if key in valid_keys:
                _, freq, access_time, _ = self.cache[key]
                new_heap.append((freq, access_time, key))

        self.heap = new_heap
        heapq.heapify(self.heap)

    def clear(self) -> None:
        """清空缓存"""
        with self.lock:
            self.cache.clear()
            self.heap.clear()

    def size(self) -> int:
        """获取缓存大小"""
        return len(self.cache)

    def get_stats(self) -> dict[str, Any]:
        """获取缓存统计"""
        # 计算平均访问频率
        if self.cache:
            avg_freq = sum(freq for _, freq, _, _ in self.cache.values()) / len(self.cache)
        else:
            avg_freq = 0

        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "usage_percent": (len(self.cache) / self.max_size * 100) if self.max_size > 0 else 0,
            "avg_access_frequency": round(avg_freq, 2),
            "strategy": "LFU",
        }


class HybridCache:
    """混合缓存策略:结合LFU和LRU的优点"""

    def __init__(
        self,
        max_size: int = 10000,
        ttl: int = 3600,
        strategy: str = "lfu",
        lru_window_size: int = 1000,
    ):
        """
        初始化混合缓存

        Args:
            max_size: 最大缓存条目数
            ttl: 缓存生存时间(秒)
            strategy: 缓存策略 ("lfu", "lru", "adaptive")
            lru_window_size: LRU窗口大小(用于adaptive策略)
        """
        self.max_size = max_size
        self.ttl = ttl
        self.strategy = strategy
        self.lru_window_size = lru_window_size

        # LRU缓存(用于最近访问的条目)
        self.lru_cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()

        # LFU缓存(用于长期频繁访问的条目)
        self.lfu_cache: LFUCache = LFUCache(max_size, ttl)

        # 锁保证线程安全
        self.lock = threading.RLock()

        logger.info(
            f"✅ 混合缓存初始化完成 - 策略: {strategy}, " f"最大条目: {max_size}, TTL: {ttl}秒"
        )

    def get(self, key: str) -> Any | None:
        """获取缓存值"""
        with self.lock:
            # 首先尝试从LRU窗口获取
            if self.strategy in ["lru", "adaptive"] and key in self.lru_cache:
                value, timestamp = self.lru_cache[key]
                if time.time() - timestamp < self.ttl:
                    # 移到末尾(标记为最近使用)
                    self.lru_cache.move_to_end(key)
                    return value
                else:
                    del self.lru_cache[key]

            # 尝试从LFU缓存获取
            if self.strategy in ["lfu", "adaptive"]:
                value = self.lfu_cache.get(key)
                if value is not None:
                    # 在LFU缓存中找到,提升到LRU窗口
                    if self.strategy == "adaptive" and len(self.lru_cache) < self.lru_window_size:
                        self.lru_cache[key] = (value, time.time())
                    return value

            return None

    def put(self, key: str, value: Any) -> None:
        """存储缓存值"""
        with self.lock:
            # 首先添加到LFU缓存
            self.lfu_cache.put(key, value)

            # 在adaptive策略下,维护LRU窗口
            if self.strategy == "adaptive":
                self.lru_cache[key] = (value, time.time())

                # 保持LRU窗口大小
                while len(self.lru_cache) > self.lru_window_size:
                    self.lru_cache.popitem(last=False)
            elif self.strategy == "lru":
                self.lru_cache[key] = (value, time.time())

                # 保持总大小限制
                while len(self.lru_cache) > self.max_size:
                    self.lru_cache.popitem(last=False)

    def cleanup_expired(self) -> int:
        """清理过期条目"""
        with self.lock:
            # 清理LRU缓存
            current_time = time.time()
            expired_lru = 0

            expired_keys = [
                k for k, (_, ts) in list(self.lru_cache.items()) if current_time - ts >= self.ttl
            ]
            for key in expired_keys:
                del self.lru_cache[key]
                expired_lru += 1

            # 清理LFU缓存
            expired_lfu = self.lfu_cache.cleanup_expired()

            return expired_lru + expired_lfu

    def clear(self) -> None:
        """清空缓存"""
        with self.lock:
            self.lru_cache.clear()
            self.lfu_cache.clear()

    def size(self) -> int:
        """获取缓存总大小"""
        lru_size = len(self.lru_cache)
        lfu_size = self.lfu_cache.size()
        # 在adaptive模式下,可能有重复计数
        if self.strategy == "adaptive":
            return max(lru_size, lfu_size)
        return lru_size + lfu_size

    def get_stats(self) -> dict[str, Any]:
        """获取缓存统计"""
        lfu_stats = self.lfu_cache.get_stats()

        return {
            "total_size": self.size(),
            "max_size": self.max_size,
            "lru_size": len(self.lru_cache),
            "lfu_size": lfu_stats["size"],
            "usage_percent": (self.size() / self.max_size * 100) if self.max_size > 0 else 0,
            "strategy": self.strategy,
            "avg_access_frequency": lfu_stats.get("avg_access_frequency", 0),
        }


def create_cache(strategy: str = "lfu", max_size: int = 10000, ttl: int = 3600) -> Any:
    """
    创建缓存实例的工厂函数

    Args:
        strategy: 缓存策略 ("lfu", "lru", "hybrid", "adaptive")
        max_size: 最大缓存条目数
        ttl: 缓存生存时间(秒)

    Returns:
        缓存实例
    """
    if strategy == "lfu":
        return LFUCache(max_size, ttl)
    elif strategy == "lru":
        # 返回一个简单的LRU缓存包装器
        from collections import OrderedDict

        class SimpleLRU:
            def __init__(self, max_size: int, ttl: int):
                self.max_size = max_size
                self.ttl = ttl
                self.cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
                self.lock = threading.RLock()

            def get(self, key: str) -> Any | None:
                with self.lock:
                    if key in self.cache:
                        value, timestamp = self.cache[key]
                        if time.time() - timestamp < self.ttl:
                            self.cache.move_to_end(key)
                            return value
                        else:
                            del self.cache[key]
                    return None

            def put(self, key: str, value: Any) -> None:
                with self.lock:
                    if key in self.cache:
                        self.cache[key] = (value, time.time())
                        self.cache.move_to_end(key)
                    else:
                        if len(self.cache) >= self.max_size:
                            self.cache.popitem(last=False)
                        self.cache[key] = (value, time.time())

            def cleanup_expired(self) -> int:
                with self.lock:
                    current_time = time.time()
                    expired = [
                        k
                        for k, (_, ts) in list(self.cache.items())
                        if current_time - ts >= self.ttl
                    ]
                    for k in expired:
                        del self.cache[k]
                    return len(expired)

            def clear(self) -> None:
                with self.lock:
                    self.cache.clear()

            def size(self) -> int:
                return len(self.cache)

            def get_stats(self) -> dict[str, Any]:
                return {
                    "size": len(self.cache),
                    "max_size": self.max_size,
                    "usage_percent": (
                        (len(self.cache) / self.max_size * 100) if self.max_size > 0 else 0
                    ),
                    "strategy": "LRU",
                }

        return SimpleLRU(max_size, ttl)
    elif strategy in ["hybrid", "adaptive"]:
        return HybridCache(max_size, ttl, strategy)
    else:
        raise ValueError(f"Unknown cache strategy: {strategy}")


if __name__ == "__main__":
    # 测试LFU缓存
    print("🧪 测试LFU缓存...")

    cache = create_cache(strategy="lfu", max_size=5, ttl=60)

    # 添加数据
    for i in range(10):
        cache.put(f"key{i}", f"value{i}")

    # 验证只保留最后5个
    print(f"缓存大小: {cache.size()}")  # 应该是5

    # 多次访问某个键增加其频率
    for _ in range(10):
        cache.get("key8")

    # 添加更多数据,key8应该被保留因为频率高
    cache.put("key10", "value10")
    cache.put("key11", "value11")

    # 验证key8仍在缓存中
    result = cache.get("key8")
    print(f"key8仍然存在: {result is not None}")  # 应该是True

    print("✅ LFU缓存测试完成")
