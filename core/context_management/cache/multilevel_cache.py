#!/usr/bin/env python3
"""
多级缓存管理器 - Phase 2.2架构优化

Multi-Level Cache Manager - 统一的多级缓存管理

核心功能:
- 三级缓存协调（L1→L2→L3）
- 智能回填策略
- 缓存穿透保护
- 统计信息汇总

性能目标:
- L1命中率 > 70%
- L2命中率 > 20%
- 总命中率 > 90%
- 平均延迟 < 1ms（L1命中）

作者: Athena平台团队
创建时间: 2026-04-24
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .l1_memory import L1MemoryCache
from .l2_redis import L2RedisCache
from .l3_sqlite import L3SQLiteBackend

logger = logging.getLogger(__name__)


class CacheLevel(Enum):
    """缓存级别枚举"""

    L1_MEMORY = "L1"
    L2_REDIS = "L2"
    L3_SQLITE = "L3"


@dataclass
class CacheEntry:
    """缓存条目"""

    key: str
    value: Any
    level: CacheLevel
    hit: bool = True
    latency_ms: float = 0.0


@dataclass
class CacheStatistics:
    """缓存统计信息"""

    # 各级命中次数
    l1_hits: int = 0
    l2_hits: int = 0
    l3_hits: int = 0
    misses: int = 0

    # 延迟统计（毫秒）
    l1_latency_total: float = 0.0
    l2_latency_total: float = 0.0
    l3_latency_total: float = 0.0

    # 淘汰统计
    l1_evictions: int = 0
    l2_errors: int = 0
    l3_errors: int = 0

    # 操作计数
    total_gets: int = 0
    total_sets: int = 0
    total_deletes: int = 0

    @property
    def total_requests(self) -> int:
        """总请求数"""
        return self.l1_hits + self.l2_hits + self.l3_hits + self.misses

    @property
    def overall_hit_rate(self) -> float:
        """总体命中率"""
        if self.total_requests == 0:
            return 0.0
        hits = self.l1_hits + self.l2_hits + self.l3_hits
        return hits / self.total_requests

    @property
    def l1_hit_rate(self) -> float:
        """L1命中率"""
        if self.total_requests == 0:
            return 0.0
        return self.l1_hits / self.total_requests

    @property
    def l2_hit_rate(self) -> float:
        """L2命中率"""
        if self.total_requests == 0:
            return 0.0
        return self.l2_hits / self.total_requests

    @property
    def l3_hit_rate(self) -> float:
        """L3命中率"""
        if self.total_requests == 0:
            return 0.0
        return self.l3_hits / self.total_requests

    @property
    def average_latency_ms(self) -> float:
        """平均延迟（毫秒）"""
        total_latency = (
            self.l1_latency_total
            + self.l2_latency_total
            + self.l3_latency_total
        )
        hits = self.l1_hits + self.l2_hits + self.l3_hits
        return total_latency / hits if hits > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "total_requests": self.total_requests,
            "overall_hit_rate": self.overall_hit_rate,
            "l1_hits": self.l1_hits,
            "l1_hit_rate": self.l1_hit_rate,
            "l2_hits": self.l2_hits,
            "l2_hit_rate": self.l2_hit_rate,
            "l3_hits": self.l3_hits,
            "l3_hit_rate": self.l3_hit_rate,
            "misses": self.misses,
            "average_latency_ms": self.average_latency_ms,
            "l1_evictions": self.l1_evictions,
            "l2_errors": self.l2_errors,
            "l3_errors": self.l3_errors,
            "total_gets": self.total_gets,
            "total_sets": self.total_sets,
            "total_deletes": self.total_deletes,
        }


@dataclass
class CacheConfig:
    """缓存配置"""

    # L1配置
    l1_capacity: int = 1000
    l1_ttl_seconds: int = 300
    l1_max_memory_mb: int = 100

    # L2配置
    l2_enabled: bool = True
    l2_host: str = "localhost"
    l2_port: int = 6379
    l2_password: Optional[str] = None
    l2_db: int = 0
    l2_ttl_seconds: int = 3600
    l2_pool_size: int = 10

    # L3配置
    l3_db_path: Optional[str] = None

    # 策略配置
    write_through: bool = True  # 写入时同时更新所有层级
    write_back: bool = False  # 写回策略（异步更新下层）
    populate_lower: bool = True  # 命中上级时回填下级

    # 保护配置
    enable_null_cache: bool = False  # 是否缓存空值（防止穿透）


class MultiLevelCacheManager:
    """
    多级缓存管理器

    实现三级缓存架构：
    1. L1: 内存缓存（最快，容量小）
    2. L2: Redis缓存（快，容量中等）
    3. L3: SQLite持久化（慢，容量无限）

    读取策略：依次尝试L1→L2→L3，找到后回填到上级
    写入策略：同时写入L1、L2、L3（write-through）
    """

    def __init__(self, config: Optional[CacheConfig] = None):
        """
        初始化多级缓存管理器

        Args:
            config: 缓存配置
        """
        self.config = config or CacheConfig()
        self._stats = CacheStatistics()
        self._lock = asyncio.Lock()

        # 初始化各级缓存
        self.l1 = L1MemoryCache(
            capacity=self.config.l1_capacity,
            ttl_seconds=self.config.l1_ttl_seconds,
            max_memory_mb=self.config.l1_max_memory_mb,
        )

        self.l2 = L2RedisCache(
            host=self.config.l2_host,
            port=self.config.l2_port,
            password=self.config.l2_password,
            db=self.config.l2_db,
            ttl_seconds=self.config.l2_ttl_seconds,
            pool_size=self.config.l2_pool_size,
            enabled=self.config.l2_enabled,
        )

        self.l3 = L3SQLiteBackend(db_path=self.config.l3_db_path)

        # 空值缓存（防止穿透）
        self._null_cache: set[str] = set()
        self._null_cache_lock = asyncio.Lock()

        logger.info("✅ 多级缓存管理器初始化完成")

    async def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值（依次尝试L1→L2→L3）

        Args:
            key: 缓存键

        Returns:
            Any: 缓存值，不存在返回None
        """
        start_time = time.time()
        self._stats.total_gets += 1

        # 检查空值缓存
        if not self.config.enable_null_cache:
            async with self._null_cache_lock:
                if key in self._null_cache:
                    self._stats.misses += 1
                    logger.debug(f"空值缓存命中: {key}")
                    return None

        # 尝试L1
        value = await self._get_from_l1(key)
        if value is not None:
            latency = (time.time() - start_time) * 1000
            self._stats.l1_latency_total += latency
            self._stats.l1_hits += 1
            logger.debug(f"L1命中: {key} ({latency:.2f}ms)")
            return value

        # 尝试L2
        value = await self._get_from_l2(key)
        if value is not None:
            latency = (time.time() - start_time) * 1000
            self._stats.l2_latency_total += latency
            self._stats.l2_hits += 1

            # 回填L1
            if self.config.populate_lower:
                await self.l1.set(key, value)

            logger.debug(f"L2命中: {key} ({latency:.2f}ms)")
            return value

        # 尝试L3
        value = await self._get_from_l3(key)
        if value is not None:
            latency = (time.time() - start_time) * 1000
            self._stats.l3_latency_total += latency
            self._stats.l3_hits += 1

            # 回填L2和L1
            if self.config.populate_lower:
                await self.l2.set(key, value)
                await self.l1.set(key, value)

            logger.debug(f"L3命中: {key} ({latency:.2f}ms)")
            return value

        # 未命中
        self._stats.misses += 1

        # 记录空值缓存
        if not self.config.enable_null_cache:
            async with self._null_cache_lock:
                self._null_cache.add(key)

        logger.debug(f"缓存未命中: {key}")
        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
    ) -> bool:
        """
        设置缓存值（同时写入所有层级）

        Args:
            key: 缓存键
            value: 缓存值
            ttl_seconds: 自定义TTL（可选）

        Returns:
            bool: 全部成功返回True
        """
        self._stats.total_sets += 1

        # 从空值缓存移除
        async with self._null_cache_lock:
            self._null_cache.discard(key)

        # 写入L1（必须成功）
        l1_ok = await self.l1.set(key, value, ttl_seconds)

        # 写入L2和L3（并发）
        if self.config.write_through:
            tasks = []
            if self.config.l2_enabled:
                tasks.append(self.l2.set(key, value, ttl_seconds))
            tasks.append(self.l3.set(key, value, ttl_seconds))

            # 并发执行，但不阻塞（使用gather但不等待结果）
            if tasks:
                try:
                    await asyncio.gather(*tasks, return_exceptions=True)
                except Exception as e:
                    logger.debug(f"后台写入异常: {e}")

        success = l1_ok  # L1成功即认为成功
        logger.debug(f"设置缓存: {key}, 结果: {success}")
        return success

    async def delete(self, key: str) -> bool:
        """
        删除缓存值（所有层级）

        Args:
            key: 缓存键

        Returns:
            bool: 删除成功返回True
        """
        self._stats.total_deletes += 1

        # 从空值缓存移除
        async with self._null_cache_lock:
            self._null_cache.discard(key)

        # 并发删除所有层级
        results = await asyncio.gather(
            self.l1.delete(key),
            self.l2.delete(key),
            self.l3.delete(key),
            return_exceptions=True,
        )

        # 至少一个成功即认为成功
        success = any(r is True for r in results)
        logger.debug(f"删除缓存: {key}, 结果: {success}")
        return success

    async def exists(self, key: str) -> bool:
        """
        检查键是否存在（任意层级）

        Args:
            key: 缓存键

        Returns:
            bool: 存在返回True
        """
        # 依次检查
        if await self.l1.contains(key):
            return True
        if await self.l2.exists(key):
            return True
        if await self.l3.exists(key):
            return True
        return False

    async def get_many(self, keys: list[str]) -> Dict[str, Any]:
        """
        批量获取缓存值

        Args:
            keys: 缓存键列表

        Returns:
            Dict[str, Any]: 键到值的映射
        """
        if not keys:
            return {}

        result = {}
        remaining_keys = keys.copy()

        # 先批量检查L1
        l1_results = {}
        for key in remaining_keys:
            value = await self.l1.get(key)
            if value is not None:
                l1_results[key] = value
                self._stats.l1_hits += 1

        result.update(l1_results)
        remaining_keys = [k for k in remaining_keys if k not in l1_results]

        if not remaining_keys:
            return result

        # 批量检查L2
        l2_results = await self.l2.get_many(remaining_keys)
        result.update(l2_results)
        self._stats.l2_hits += len(l2_results)
        remaining_keys = [k for k in remaining_keys if k not in l2_results]

        if not remaining_keys:
            # 回填L1
            for key, value in l2_results.items():
                await self.l1.set(key, value)
            return result

        # 批量检查L3
        l3_results = await self.l3.get_many(remaining_keys)
        result.update(l3_results)
        self._stats.l3_hits += len(l3_results)

        # 回填
        for key, value in l3_results.items():
            await self.l2.set(key, value)
            await self.l1.set(key, value)

        return result

    async def set_many(
        self, mapping: dict[str, Any], ttl_seconds: Optional[int] = None
    ) -> int:
        """
        批量设置缓存值

        Args:
            mapping: 键到值的映射
            ttl_seconds: TTL（秒）

        Returns:
            int: 成功设置的数量
        """
        if not mapping:
            return 0

        count = 0
        for key, value in mapping.items():
            if await self.set(key, value, ttl_seconds):
                count += 1

        return count

    async def clear(self) -> None:
        """清空所有缓存"""
        await asyncio.gather(
            self.l1.clear(),
            self.l2.clear(),
            self.l3.clear(),
        )
        self._null_cache.clear()
        logger.info("多级缓存已清空")

    async def cleanup_expired(self) -> Dict[str, int]:
        """
        清理所有层级的过期条目

        Returns:
            Dict[str, int]: 各层级清理的条目数
        """
        results = await asyncio.gather(
            self.l1.cleanup_expired(),
            self.l3.cleanup_expired(),
            return_exceptions=True,
        )

        return {
            "L1": results[0] if isinstance(results[0], int) else 0,
            "L3": results[1] if isinstance(results[1], int) else 0,
        }

    async def health_check(self) -> Dict[str, bool]:
        """
        健康检查

        Returns:
            Dict[str, bool]: 各层级健康状态
        """
        l2_healthy = await self.l2.health_check()

        return {
            "L1": True,  # 内存缓存总是健康
            "L2": l2_healthy,
            "L3": True,  # SQLite总是健康（除非磁盘问题）
        }

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取汇总统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "manager": self._stats.to_dict(),
            "l1": self.l1.get_statistics(),
            "l2": self.l2.get_statistics(),
            "l3": asyncio.create_task(self.l3.get_statistics())
            if not asyncio.get_event_loop().is_running()
            else {"note": "async call required"},
        }

    async def get_full_statistics(self) -> Dict[str, Any]:
        """
        获取完整统计信息（包含异步统计）

        Returns:
            Dict[str, Any]: 完整统计信息
        """
        l3_stats = await self.l3.get_statistics()

        return {
            "manager": self._stats.to_dict(),
            "l1": self.l1.get_statistics(),
            "l2": self.l2.get_statistics(),
            "l3": l3_stats,
        }

    async def _get_from_l1(self, key: str) -> Optional[Any]:
        """从L1获取"""
        return await self.l1.get(key)

    async def _get_from_l2(self, key: str) -> Optional[Any]:
        """从L2获取"""
        return await self.l2.get(key)

    async def _get_from_l3(self, key: str) -> Optional[Any]:
        """从L3获取"""
        return await self.l3.get(key)

    async def warm_up(self, data: dict[str, Any]) -> int:
        """
        缓存预热

        Args:
            data: 预热数据

        Returns:
            int: 成功预热的条目数
        """
        count = 0
        for key, value in data.items():
            if await self.set(key, value):
                count += 1

        logger.info(f"缓存预热完成: {count}/{len(data)}条")
        return count

    async def close(self) -> None:
        """关闭管理器，释放资源"""
        await self.l2.close()
        logger.info("多级缓存管理器已关闭")


__all__ = [
    "CacheLevel",
    "CacheEntry",
    "CacheStatistics",
    "CacheConfig",
    "MultiLevelCacheManager",
]
