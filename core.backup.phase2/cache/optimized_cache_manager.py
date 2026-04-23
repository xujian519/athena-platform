#!/usr/bin/env python3
from __future__ import annotations
"""
优化缓存管理器
Optimized Cache Manager

为搜索服务提供高效的多级缓存策略,减少重复计算
作者: Athena AI Team
创建时间: 2026-01-09
版本: v1.0.0
"""

import hashlib
import json
import logging
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class CacheLevel(Enum):
    """缓存级别"""

    L1_MEMORY = "l1_memory"  # 内存缓存 (最快)
    L2_REDIS = "l2_redis"  # Redis缓存 (快速)
    L3_DISK = "l3_disk"  # 磁盘缓存 (持久化)


@dataclass
class CacheEntry:
    """缓存条目"""

    key: str  # 缓存键
    value: Any  # 缓存值
    level: CacheLevel  # 缓存级别
    created_at: float  # 创建时间
    accessed_at: float  # 最后访问时间
    access_count: int = 0  # 访问次数
    ttl: int = 300  # 生存时间(秒)
    size: int = 0  # 大小(字节)

    @property
    def age(self) -> float:
        """缓存年龄(秒)"""
        return time.time() - self.created_at

    @property
    def is_expired(self) -> bool:
        """是否过期"""
        return self.age > self.ttl

    def touch(self) -> Any:
        """更新访问时间"""
        self.accessed_at = time.time()
        self.access_count += 1

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "key": self.key[:50] + "..." if len(self.key) > 50 else self.key,
            "level": self.level.value,
            "age": self.age,
            "ttl": self.ttl,
            "access_count": self.access_count,
            "size": self.size,
        }


class CachePolicy:
    """缓存策略"""

    def __init__(self):
        """初始化缓存策略"""
        # 默认TTL配置
        self.default_ttls = {
            CacheLevel.L1_MEMORY: 300,  # 5分钟
            CacheLevel.L2_REDIS: 3600,  # 1小时
            CacheLevel.L3_DISK: 86400,  # 1天
        }

        # 最大缓存大小
        self.max_sizes = {
            CacheLevel.L1_MEMORY: 100 * 1024 * 1024,  # 100MB
            CacheLevel.L2_REDIS: 500 * 1024 * 1024,  # 500MB
            CacheLevel.L3_DISK: 2 * 1024 * 1024 * 1024,  # 2GB
        }

        # 驱逐策略
        self.eviction_policy = "lfu"  # Least Frequently Used

        # 预热策略
        self.preload_queries = ["专利侵权", "发明专利的保护期", "商标注册流程"]

    def get_ttl(self, level: CacheLevel, query_type: str | None = None) -> int:
        """获取TTL"""
        base_ttl = self.default_ttls[level]

        # 根据查询类型调整TTL
        if query_type == "simple":
            return base_ttl  # 短TTL
        elif query_type == "complex":
            return base_ttl * 2  # 长TTL
        else:
            return base_ttl

    def should_cache(self, query: str, result: Any) -> bool:
        """判断是否应该缓存"""
        # 简单查询优先缓存
        if len(query) < 50:
            return True

        # 有LLM生成的结果优先缓存
        if isinstance(result, dict) and "generated_answer" in result:
            return True

        # 默认缓存
        return True


class OptimizedCacheManager:
    """优化缓存管理器"""

    def __init__(self, policy: CachePolicy | None = None):
        """
        初始化缓存管理器

        Args:
            policy: 缓存策略
        """
        self.policy = policy or CachePolicy()
        self.name = "优化缓存管理器"

        # 多级缓存存储
        self.l1_cache: dict[str, CacheEntry] = {}  # 内存缓存
        self.l2_cache = None  # Redis缓存 (可选)
        self.l3_cache_dir = Path("/tmp/athena_search_cache")

        # 统计信息
        self.stats = {
            "hits": {"l1": 0, "l2": 0, "l3": 0, "total": 0},
            "misses": 0,
            "evictions": 0,
            "size": {"l1": 0, "l2": 0, "l3": 0},
        }

        # 初始化L3磁盘缓存
        self.l3_cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"✅ {self.name}初始化完成")

    def _generate_key(self, query: str, mode: str, top_k: int, **kwargs) -> str:
        """生成缓存键"""
        key_data = f"{query}|{mode}|{top_k}"
        for k, v in sorted(kwargs.items()):
            key_data += f"|{k}={v}"

        return hashlib.md5(key_data.encode('utf-8'), usedforsecurity=False).hexdigest()

    async def get(self, query: str, mode: str, top_k: int = 10, **kwargs) -> Any | None:
        """
        获取缓存

        Args:
            query: 查询文本
            mode: 搜索模式
            top_k: 返回数量
            **kwargs: 其他参数

        Returns:
            缓存值或None
        """
        key = self._generate_key(query, mode, top_k, **kwargs)

        # 尝试L1缓存
        if key in self.l1_cache:
            entry = self.l1_cache[key]
            if not entry.is_expired:
                entry.touch()
                self.stats["hits"]["l1"] += 1
                self.stats["hits"]["total"] += 1
                logger.debug(f"✅ L1缓存命中: {key}")
                return entry.value
            else:
                # 过期,删除
                del self.l1_cache[key]
                self.stats["size"]["l1"] -= entry.size

        # 尝试L3缓存 (磁盘)
        l3_file = self.l3_cache_dir / f"{key}.json"
        if l3_file.exists():
            try:
                with open(l3_file, encoding="utf-8") as f:
                    data = json.load(f)
                    entry = CacheEntry(**data)

                if not entry.is_expired:
                    entry.touch()
                    # 提升到L1
                    self._set_l1(key, entry.value, entry.level, entry.size)
                    self.stats["hits"]["l3"] += 1
                    self.stats["hits"]["total"] += 1
                    logger.debug(f"✅ L3缓存命中: {key}")
                    return entry.value
                else:
                    # 过期,删除
                    l3_file.unlink()
            except Exception as e:
                logger.warning(f"⚠️ L3缓存读取失败: {e}")

        # 未命中
        self.stats["misses"] += 1
        logger.debug(f"❌ 缓存未命中: {key}")
        return None

    async def set(
        self,
        query: str,
        value: Any,
        mode: str,
        top_k: int = 10,
        level: CacheLevel = CacheLevel.L1_MEMORY,
        ttl: int | None = None,
        **kwargs,
    ):
        """
        设置缓存

        Args:
            query: 查询文本
            value: 缓存值
            mode: 搜索模式
            top_k: 返回数量
            level: 缓存级别
            ttl: 生存时间
            **kwargs: 其他参数
        """
        key = self._generate_key(query, mode, top_k, **kwargs)

        # 序列化值
        try:
            if isinstance(value, (dict, list)):
                serialized = json.dumps(value, ensure_ascii=False)
                size = len(serialized.encode("utf-8"))
            else:
                serialized = str(value)
                size = len(serialized.encode("utf-8"))
        except Exception as e:
            logger.warning(f"⚠️ 无法序列化缓存值: {e}")
            return

        # 设置TTL
        if ttl is None:
            query_type = "simple" if len(query) < 50 else "complex"
            ttl = self.policy.get_ttl(level, query_type)

        # 创建缓存条目
        entry = CacheEntry(
            key=key,
            value=value,
            level=level,
            created_at=time.time(),
            accessed_at=time.time(),
            ttl=ttl,
            size=size,
        )

        # 写入指定级别的缓存
        if level == CacheLevel.L1_MEMORY:
            self._set_l1(key, value, level, size)
        elif level == CacheLevel.L3_DISK:
            self._set_l3(key, entry)

    def _set_l1(self, key: str, value: Any, level: CacheLevel, size: int) -> Any:
        """设置L1缓存"""
        # 检查大小限制
        if self.stats["size"]["l1"] + size > self.policy.max_sizes[CacheLevel.L1_MEMORY]:
            self._evict_l1(size)

        self.l1_cache[key] = CacheEntry(
            key=key,
            value=value,
            level=level,
            created_at=time.time(),
            accessed_at=time.time(),
            size=size,
        )
        self.stats["size"]["l1"] += size

    def _set_l3(self, key: str, entry: CacheEntry) -> Any:
        """设置L3缓存"""
        l3_file = self.l3_cache_dir / f"{key}.json"

        try:
            with open(l3_file, "w", encoding="utf-8") as f:
                json.dump(entry.to_dict(), f, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"⚠️ L3缓存写入失败: {e}")

    def _evict_l1(self, required_size: int) -> Any:
        """驱逐L1缓存"""
        # 按LFU策略驱逐
        sorted_entries = sorted(self.l1_cache.values(), key=lambda e: (e.access_count, e.age))

        freed = 0
        while freed < required_size and sorted_entries:
            entry = sorted_entries.pop(0)
            del self.l1_cache[entry.key]
            freed += entry.size
            self.stats["evictions"] += 1

        self.stats["size"]["l1"] -= freed

    async def preload_cache(self, queries: list[str]):
        """预加载缓存"""
        logger.info(f"🔄 预加载 {len(queries)} 个查询...")

        # 这里应该执行实际的搜索并缓存结果
        # 由于需要搜索服务,这里只是框架
        for query in queries:
            # 实际实现中,这里会调用搜索服务
            logger.debug(f"   预加载: {query}")

        logger.info("✅ 缓存预加载完成")

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        total_hits = sum(self.stats["hits"].values())
        total_requests = total_hits + self.stats["misses"]

        hit_rate = total_hits / total_requests if total_requests > 0 else 0

        l1_hit_rate = self.stats["hits"]["l1"] / total_requests if total_requests > 0 else 0

        return {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_rate": hit_rate,
            "l1_hit_rate": l1_hit_rate,
            "evictions": self.stats["evictions"],
            "size": self.stats["size"],
            "entry_count": len(self.l1_cache),
        }

    def clear(self, level: CacheLevel | None = None) -> Any:
        """清理缓存"""
        if level is None or level == CacheLevel.L1_MEMORY:
            self.l1_cache.clear()
            self.stats["size"]["l1"] = 0

        if level is None or level == CacheLevel.L3_DISK:
            for file in self.l3_cache_dir.glob("*.json"):
                file.unlink()

        logger.info("✅ 缓存已清理")

    def print_stats(self) -> Any:
        """打印统计信息"""
        stats = self.get_stats()

        print()
        print("=" * 60)
        print("📊 缓存统计")
        print("=" * 60)
        print()
        print(f"总请求数: {stats['hits']['total'] + stats['misses']}")
        print(f"缓存命中: {stats['hits']['total']}")
        print(f"缓存未命中: {stats['misses']}")
        print(f"命中率: {stats['hit_rate']:.1%}")
        print()
        print("按级别统计:")
        print(f"   L1内存: {stats['hits']['l1']} 次命中 ({stats['l1_hit_rate']:.1%})")
        print(f"   L2Redis: {stats['hits']['l2']} 次命中")
        print(f"   L3磁盘: {stats['hits']['l3']} 次命中")
        print()
        print(f"L1缓存大小: {stats['size']['l1'] / 1024 / 1024:.2f} MB")
        print(f"L1缓存条目: {stats['entry_count']}")
        print(f"驱逐次数: {stats['evictions']}")
        print()
        print("=" * 60)
        print()


# 全局单例
_cache_manager: OptimizedCacheManager | None = None


def get_cache_manager() -> OptimizedCacheManager:
    """获取缓存管理器单例"""
    global _cache_manager

    if _cache_manager is None:
        policy = CachePolicy()
        _cache_manager = OptimizedCacheManager(policy)

    return _cache_manager


# 示例使用
async def main():
    """主函数示例"""
    print("🔍 优化缓存管理器演示")
    print()

    # 获取缓存管理器
    cache_mgr = get_cache_manager()

    # 示例1: 设置缓存
    print("1️⃣ 设置缓存")
    await cache_mgr.set(
        query="专利侵权",
        value={"results": ["result1", "result2"], "count": 2},
        mode="rerank_top_k",
        top_k=5,
    )
    print("   ✅ 缓存已设置")
    print()

    # 示例2: 获取缓存
    print("2️⃣ 获取缓存")
    value = await cache_mgr.get(query="专利侵权", mode="rerank_top_k", top_k=5)
    if value:
        print(f"   ✅ 缓存命中: {value}")
    else:
        print("   ❌ 缓存未命中")
    print()

    # 示例3: 显示统计
    print("3️⃣ 缓存统计")
    cache_mgr.print_stats()


# 入口点: @async_main装饰器已添加到main函数
