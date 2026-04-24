#!/usr/bin/env python3
"""
L1内存缓存实现 - Phase 2.2架构优化

L1 Memory Cache - 高速内存缓存层

特性:
- LRU淘汰策略
- TTL自动过期
- 线程安全（asyncio.Lock）
- 内存占用限制

配置:
- 容量: 1000条（可配置）
- TTL: 5分钟（300秒）
- 最大内存: 100MB（可配置）

作者: Athena平台团队
创建时间: 2026-04-24
"""

import asyncio
import logging
import pickle
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class MemoryCacheEntry:
    """内存缓存条目"""

    key: str
    value: Any
    created_at: float
    expires_at: float
    access_count: int = 0
    size_bytes: int = 0

    @property
    def is_expired(self) -> bool:
        """检查是否过期"""
        return time.time() > self.expires_at

    @property
    def age_seconds(self) -> float:
        """获取条目年龄（秒）"""
        return time.time() - self.created_at


class L1MemoryCache:
    """
    L1内存缓存

    使用OrderedDict实现LRU淘汰策略。
    """

    def __init__(
        self,
        capacity: int = 1000,
        ttl_seconds: int = 300,
        max_memory_mb: int = 100,
    ):
        """
        初始化L1内存缓存

        Args:
            capacity: 最大缓存条目数
            ttl_seconds: 默认TTL（秒）
            max_memory_mb: 最大内存占用（MB）
        """
        self.capacity = capacity
        self.ttl_seconds = ttl_seconds
        self.max_memory_bytes = max_memory_mb * 1024 * 1024

        # OrderedDict用于实现LRU
        self._cache: OrderedDict[str, MemoryCacheEntry] = OrderedDict()
        self._lock = asyncio.Lock()

        # 统计信息
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._current_memory_bytes = 0

        logger.info(
            f"✅ L1内存缓存初始化: capacity={capacity}, ttl={ttl_seconds}s, max_memory={max_memory_mb}MB"
        )

    async def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            Any: 缓存值，不存在或过期返回None
        """
        async with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self._misses += 1
                logger.debug(f"L1未命中: {key}")
                return None

            if entry.is_expired:
                # 删除过期条目
                del self._cache[key]
                self._current_memory_bytes -= entry.size_bytes
                self._misses += 1
                logger.debug(f"L1过期: {key}")
                return None

            # LRU: 移到末尾（最近使用）
            self._cache.move_to_end(key)
            entry.access_count += 1
            self._hits += 1

            logger.debug(f"L1命中: {key} (访问次数: {entry.access_count})")
            return entry.value

    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl_seconds: 自定义TTL（可选）

        Returns:
            bool: 设置成功返回True
        """
        ttl = ttl_seconds or self.ttl_seconds
        now = time.time()
        expires_at = now + ttl

        # 序列化计算大小
        try:
            value_bytes = pickle.dumps(value)
            size_bytes = len(value_bytes)
        except Exception as e:
            logger.error(f"序列化失败: {e}")
            return False

        async with self._lock:
            # 如果键已存在，先删除旧值
            if key in self._cache:
                old_entry = self._cache[key]
                self._current_memory_bytes -= old_entry.size_bytes
                del self._cache[key]

            # 检查内存限制
            if size_bytes > self.max_memory_bytes:
                logger.warning(f"值过大，无法缓存: {key} ({size_bytes} bytes)")
                return False

            # 淘汰空间（按LRU）
            await self._ensure_capacity(size_bytes)

            # 创建新条目
            entry = MemoryCacheEntry(
                key=key,
                value=value,
                created_at=now,
                expires_at=expires_at,
                size_bytes=size_bytes,
            )

            self._cache[key] = entry
            self._current_memory_bytes += size_bytes

            logger.debug(f"L1设置: {key} (TTL: {ttl}s, 大小: {size_bytes} bytes)")
            return True

    async def delete(self, key: str) -> bool:
        """
        删除缓存值

        Args:
            key: 缓存键

        Returns:
            bool: 删除成功返回True
        """
        async with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                self._current_memory_bytes -= entry.size_bytes
                del self._cache[key]
                logger.debug(f"L1删除: {key}")
                return True
            return False

    async def clear(self) -> None:
        """清空所有缓存"""
        async with self._lock:
            self._cache.clear()
            self._current_memory_bytes = 0
            logger.info("L1缓存已清空")

    async def cleanup_expired(self) -> int:
        """
        清理过期条目

        Returns:
            int: 清理的条目数
        """
        async with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items() if entry.is_expired
            ]

            for key in expired_keys:
                entry = self._cache[key]
                self._current_memory_bytes -= entry.size_bytes
                del self._cache[key]
                self._evictions += 1

            if expired_keys:
                logger.info(f"L1清理过期条目: {len(expired_keys)}个")

            return len(expired_keys)

    async def _ensure_capacity(self, required_bytes: int) -> None:
        """
        确保有足够容量（按LRU淘汰）

        Args:
            required_bytes: 需要的字节数
        """
        # 检查条目数限制
        while len(self._cache) >= self.capacity and self._cache:
            oldest_key = next(iter(self._cache))
            entry = self._cache[oldest_key]
            self._current_memory_bytes -= entry.size_bytes
            del self._cache[oldest_key]
            self._evictions += 1

        # 检查内存限制
        while (
            self._current_memory_bytes + required_bytes > self.max_memory_bytes
            and self._cache
        ):
            oldest_key = next(iter(self._cache))
            entry = self._cache[oldest_key]
            self._current_memory_bytes -= entry.size_bytes
            del self._cache[oldest_key]
            self._evictions += 1

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0

        return {
            "level": "L1",
            "type": "memory",
            "hits": self._hits,
            "misses": self._misses,
            "evictions": self._evictions,
            "hit_rate": hit_rate,
            "size": len(self._cache),
            "capacity": self.capacity,
            "memory_bytes": self._current_memory_bytes,
            "memory_mb": self._current_memory_bytes / (1024 * 1024),
            "max_memory_mb": self.max_memory_bytes / (1024 * 1024),
            "utilization": len(self._cache) / self.capacity if self.capacity > 0 else 0,
        }

    async def get_keys(self) -> List[str]:
        """
        获取所有缓存键

        Returns:
            List[str]: 缓存键列表
        """
        async with self._lock:
            return list(self._cache.keys())

    async def contains(self, key: str) -> bool:
        """
        检查键是否存在（且未过期）

        Args:
            key: 缓存键

        Returns:
            bool: 存在且未过期返回True
        """
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return False
            if entry.is_expired:
                # 异步删除过期条目
                await self.delete(key)
                return False
            return True

    async def get_size_info(self, key: str) -> Optional[Dict[str, Any]]:
        """
        获取特定键的大小信息

        Args:
            key: 缓存键

        Returns:
            Dict[str, Any] | None: 大小信息
        """
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            return {
                "key": key,
                "size_bytes": entry.size_bytes,
                "age_seconds": entry.age_seconds,
                "access_count": entry.access_count,
                "is_expired": entry.is_expired,
            }


__all__ = ["L1MemoryCache", "MemoryCacheEntry"]
