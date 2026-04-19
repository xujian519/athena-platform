#!/usr/bin/env python3
"""
查询缓存模块
Query Cache for Athena Intelligent Router
"""

from __future__ import annotations
import hashlib
import os
import time
from typing import Any


class QueryCache:
    """查询结果缓存"""

    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl  # 秒
        self.cache: dict[str, dict] = {}

    def _generate_key(self, query: str, limit: int) -> str:
        """生成缓存键"""
        key_data = f"{query}:{limit}"
        return hashlib.md5(key_data.encode('utf-8'), usedforsecurity=False).hexdigest()

    def get(self, query: str, limit: int) -> Any | None:
        """获取缓存"""
        key = self._generate_key(query, limit)

        if key not in self.cache:
            return None

        entry = self.cache[key]

        # 检查是否过期
        if time.time() - entry["timestamp"] > self.ttl:
            del self.cache[key]
            return None

        return entry["data"]

    def set(self, query: str, limit: int, data: Any) -> None:
        """设置缓存"""
        # 如果缓存满了,删除最旧的25%
        if len(self.cache) >= self.max_size:
            keys_to_delete = list(self.cache.keys())[: self.max_size // 4]
            for k in keys_to_delete:
                del self.cache[k]

        key = self._generate_key(query, limit)
        self.cache[key] = {"data": data, "timestamp": time.time()}

    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()

    def get_stats(self) -> dict:
        """获取缓存统计"""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl": self.ttl,
            "usage_percent": len(self.cache) / self.max_size * 100,
        }


# 全局缓存实例
_query_cache = None


def get_query_cache() -> QueryCache:
    """获取缓存实例"""
    global _query_cache
    if _query_cache is None:
        _query_cache = QueryCache(
            max_size=int(os.getenv("CACHE_MAX_SIZE", "1000")),
            ttl=int(os.getenv("CACHE_TTL", "3600")),
        )
    return _query_cache
