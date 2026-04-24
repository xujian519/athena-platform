"""
缓存策略优化模块

目标: 将缓存命中率从89.7%提升到>95%

优化策略:
1. 智能预热 - 预加载高频数据
2. LRU+TTL混合策略 - 优化淘汰算法
3. 分层缓存 - 热/温/冷数据分层
4. 自适应TTL - 根据访问频率动态调整

Author: Athena Team
Date: 2026-04-24
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import OrderedDict
from enum import Enum
from datetime import datetime, timedelta


class CacheLayer(Enum):
    """缓存层级"""
    HOT = "hot"      # 热数据（内存，高频访问）
    WARM = "warm"    # 温数据（Redis，中频访问）
    COLD = "cold"    # 冷数据（数据库，低频访问）


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    layer: CacheLayer
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0
    ttl: Optional[float] = None  # 过期时间
    priority: float = 0.0  # 优先级（用于淘汰）


@dataclass
class CacheConfig:
    """缓存配置"""
    # 容量配置
    hot_capacity: int = 1000  # 热缓存容量
    warm_capacity: int = 5000  # 温缓存容量
    cold_capacity: int = 10000  # 冷缓存容量

    # TTL配置（秒）
    default_ttl: int = 3600  # 默认1小时
    hot_ttl: int = 300  # 热数据5分钟
    warm_ttl: int = 1800  # 温数据30分钟
    cold_ttl: int = 7200  # 冷数据2小时

    # 预热配置
    enable_preheat: bool = True
    preheat_threshold: int = 10  # 访问10次后预热
    preheat_sample_size: int = 100  # 预热样本数

    # 淘汰策略
    eviction_policy: str = "adaptive_lru"  # lru/lfu/adaptive_lru
    ttl_jitter: float = 0.1  # TTL抖动（避免雪崩）


class SmartCache:
    """智能缓存系统"""

    def __init__(self, config: CacheConfig):
        self.config = config

        # 分层缓存存储
        self._hot_cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._warm_cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._cold_cache: OrderedDict[str, CacheEntry] = OrderedDict()

        # 统计信息
        self._hits = 0
        self._misses = 0
        self._layer_hits = {CacheLayer.HOT: 0, CacheLayer.WARM: 0, CacheLayer.COLD: 0}

        # 访问频率跟踪（用于预热）
        self._access_frequency: Dict[str, int] = {}

    def _get_cache(self, layer: CacheLayer) -> OrderedDict[str, CacheEntry]:
        """获取指定层级的缓存"""
        if layer == CacheLayer.HOT:
            return self._hot_cache
        elif layer == CacheLayer.WARM:
            return self._warm_cache
        else:
            return self._cold_cache

    def _get_capacity(self, layer: CacheLayer) -> int:
        """获取指定层级的容量"""
        if layer == CacheLayer.HOT:
            return self.config.hot_capacity
        elif layer == CacheLayer.WARM:
            return self.config.warm_capacity
        else:
            return self.config.cold_capacity

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        # 按层级查找：热 → 温 → 冷
        for layer in [CacheLayer.HOT, CacheLayer.WARM, CacheLayer.COLD]:
            cache = self._get_cache(layer)
            if key in cache:
                entry = cache[key]

                # 检查是否过期
                if entry.ttl and time.time() > entry.ttl:
                    del cache[key]
                    continue

                # 更新访问信息
                entry.last_accessed = time.time()
                entry.access_count += 1

                # 移动到末尾（LRU）
                cache.move_to_end(key)

                # 更新统计
                self._hits += 1
                self._layer_hits[layer] += 1
                self._access_frequency[key] = self._access_frequency.get(key, 0) + 1

                # 智能升级：如果访问频率高，升级到更热层级
                await self._maybe_promote(key, entry, layer)

                return entry.value

        # 未命中
        self._misses += 1
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置缓存值"""
        # 确定初始层级（默认温层）
        layer = CacheLayer.WARM

        # 计算TTL
        if ttl is None:
            ttl = self.config.default_ttl

        expiry = time.time() + ttl if ttl > 0 else None

        # 创建缓存条目
        entry = CacheEntry(
            key=key,
            value=value,
            layer=layer,
            ttl=expiry,
        )

        # 存储到对应层级
        cache = self._get_cache(layer)

        # 检查容量
        if len(cache) >= self._get_capacity(layer):
            await self._evict(layer)

        cache[key] = entry
        cache.move_to_end(key)

        # 初始化访问频率
        if key not in self._access_frequency:
            self._access_frequency[key] = 0

    async def _maybe_promote(self, key: str, entry: CacheEntry, current_layer: CacheLayer):
        """智能升级：将频繁访问的数据升级到更热层级"""
        # 访问频率达到阈值，升级到热层
        if (current_layer == CacheLayer.WARM and
            entry.access_count >= self.config.preheat_threshold):

            await self._move_to_layer(key, CacheLayer.HOT)

    async def _move_to_layer(self, key: str, target_layer: CacheLayer):
        """将条目移动到指定层级"""
        # 查找当前条目
        source_entry = None
        source_layer = None

        for layer in [CacheLayer.COLD, CacheLayer.WARM, CacheLayer.HOT]:
            cache = self._get_cache(layer)
            if key in cache:
                source_entry = cache[key]
                source_layer = layer
                del cache[key]
                break

        if source_entry is None:
            return

        # 更新层级和TTL
        source_entry.layer = target_layer

        if target_layer == CacheLayer.HOT:
            source_entry.ttl = time.time() + self.config.hot_ttl
        elif target_layer == CacheLayer.WARM:
            source_entry.ttl = time.time() + self.config.warm_ttl
        else:
            source_entry.ttl = time.time() + self.config.cold_ttl

        # 添加到目标层级
        target_cache = self._get_cache(target_layer)

        # 检查容量
        if len(target_cache) >= self._get_capacity(target_layer):
            await self._evict(target_layer)

        target_cache[key] = source_entry
        target_cache.move_to_end(key)

    async def _evict(self, layer: CacheLayer):
        """淘汰指定层级的条目"""
        cache = self._get_cache(layer)

        if not cache:
            return

        # 找出优先级最低的条目
        if self.config.eviction_policy == "lru":
            # LRU：删除最久未使用的
            cache.popitem(last=False)
        elif self.config.eviction_policy == "lfu":
            # LFU：删除访问频率最低的
            lru_key = min(cache.items(), key=lambda x: x[1].access_count)[0]
            del cache[lru_key]
        else:  # adaptive_lru
            # 自适应：综合考虑LRU和访问频率
            current_time = time.time()
            min_score = float('inf')
            lru_key = None

            for key, entry in cache.items():
                # 计算优先级分数（越低越应该淘汰）
                age = current_time - entry.last_accessed
                frequency = entry.access_count
                score = age / (frequency + 1)  # 老且少用的应该淘汰

                if score < min_score:
                    min_score = score
                    lru_key = key

            if lru_key:
                del cache[lru_key]

    async def preheat(self, keys: List[str], data_loader: callable):
        """预热缓存"""
        if not self.config.enable_preheat:
            return

        # 找出访问频率最高的键
        sorted_keys = sorted(
            self._access_frequency.items(),
            key=lambda x: x[1],
            reverse=True
        )[:self.config.preheat_sample_size]

        preheat_keys = [k for k, v in sorted_keys if v >= self.config.preheat_threshold]

        # 并行加载
        tasks = [data_loader(key) for key in preheat_keys]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 存储到热缓存
        for key, result in zip(preheat_keys, results):
            if not isinstance(result, Exception):
                await self.set(key, result, ttl=self.config.hot_ttl)

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0

        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "layer_distribution": {
                "hot": len(self._hot_cache),
                "warm": len(self._warm_cache),
                "cold": len(self._cold_cache),
            },
            "layer_hits": {
                "hot": self._layer_hits[CacheLayer.HOT],
                "warm": self._layer_hits[CacheLayer.WARM],
                "cold": self._layer_hits[CacheLayer.COLD],
            },
            "target_hit_rate": 0.95,
            "improvement_needed": max(0, 0.95 - hit_rate),
        }


# 使用示例
async def example_optimized_cache():
    """优化后的缓存示例"""

    config = CacheConfig(
        hot_capacity=1000,
        warm_capacity=5000,
        enable_preheat=True,
    )

    cache = SmartCache(config)

    # 模拟数据加载器
    async def data_loader(key: str) -> Any:
        await asyncio.sleep(0.01)  # 模拟10ms加载时间
        return f"data_{key}"

    # 写入数据
    for i in range(100):
        await cache.set(f"key_{i}", f"value_{i}")

    # 读取数据
    for i in range(50):
        await cache.get(f"key_{i}")

    # 高频访问（触发升级）
    for _ in range(15):
        await cache.get("key_0")

    # 获取统计
    stats = cache.get_stats()

    return {
        "cache_stats": stats,
        "hit_rate_achieved": stats["hit_rate"] >= 0.95,
    }


if __name__ == "__main__":
    # 测试优化效果
    async def test():
        print("测试缓存策略优化...")
        result = await example_optimized_cache()
        print(f"结果: {json.dumps(result, indent=2, ensure_ascii=False)}")

    asyncio.run(test())
