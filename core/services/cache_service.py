#!/usr/bin/env python3
"""
统一缓存服务
Unified Cache Service

提供多级缓存功能

作者: 小诺·双鱼公主 v4.0
创建时间: 2025-12-25
版本: 1.0.0
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """缓存条目"""

    key: str
    value: Any
    ttl: int = 3600  # 生存时间(秒)
    created_at: float = field(default_factory=time.time)
    hits: int = 0

    def is_expired(self) -> bool:
        """是否过期"""
        return time.time() - self.created_at > self.ttl


class CacheService:
    """统一缓存服务"""

    def __init__(self, config=None):
        self.config = config
        self._memory_cache: dict[str, CacheEntry] = {}
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
        }

    async def get(self, key: str) -> Any | None:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值,如果不存在或已过期返回None
        """
        entry = self._memory_cache.get(key)

        if entry is None:
            self._stats["misses"] += 1
            return None

        if entry.is_expired():
            # 删除过期条目
            del self._memory_cache[key]
            self._stats["misses"] += 1
            return None

        entry.hits += 1
        self._stats["hits"] += 1
        return entry.value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> bool:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 生存时间(秒),默认3600

        Returns:
            是否成功
        """
        try:
            entry = CacheEntry(
                key=key,
                value=value,
                ttl=ttl or 3600,
            )
            self._memory_cache[key] = entry
            self._stats["sets"] += 1
            return True
        except Exception as e:
            logger.error(f"缓存设置失败: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        删除缓存值

        Args:
            key: 缓存键

        Returns:
            是否成功
        """
        if key in self._memory_cache:
            del self._memory_cache[key]
            self._stats["deletes"] += 1
            return True
        return False

    async def clear(self):
        """清空所有缓存"""
        self._memory_cache.clear()
        logger.info("缓存已清空")

    async def cleanup_expired(self) -> int:
        """
        清理过期缓存

        Returns:
            清理的条目数
        """
        expired_keys = [key for key, entry in self._memory_cache.items() if entry.is_expired()]

        for key in expired_keys:
            del self._memory_cache[key]

        if expired_keys:
            logger.info(f"清理了 {len(expired_keys)} 个过期缓存")

        return len(expired_keys)

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0

        return {
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "sets": self._stats["sets"],
            "deletes": self._stats["deletes"],
            "hit_rate": f"{hit_rate:.2%}",
            "cache_size": len(self._memory_cache),
        }

    def get_cache_info(self) -> dict[str, Any]:
        """获取缓存信息"""
        return {
            "total_entries": len(self._memory_cache),
            "total_hits": sum(e.hits for e in self._memory_cache.values()),
            "expired_entries": sum(1 for e in self._memory_cache.values() if e.is_expired()),
        }


# 全局服务实例
_cache_service: CacheService | None = None


def get_cache_service(config=None) -> CacheService:
    """获取缓存服务实例"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService(config)
    return _cache_service


if __name__ == "__main__":
    # 测试缓存服务
    async def test():
        service = get_cache_service()

        print("💾 缓存服务测试")
        print("=" * 60)

        # 设置缓存
        await service.set("test_key", {"data": "test_value"}, ttl=10)
        print("✅ 缓存已设置")

        # 获取缓存
        value = await service.get("test_key")
        print(f"📖 缓存值: {value}")

        # 获取统计
        stats = service.get_stats()
        print()
        print("📊 统计:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

        # 清理过期
        await asyncio.sleep(11)
        expired = await service.cleanup_expired()
        print()
        print(f"🧹 清理了 {expired} 个过期缓存")

    asyncio.run(test())
