#!/usr/bin/env python3
"""
多级缓存系统 - Phase 2.2架构优化

Multi-Level Cache System - 三级缓存架构提升上下文访问性能

核心组件:
- L1MemoryCache: 内存缓存（LRU，1000条，TTL 5分钟）
- L2RedisCache: Redis缓存（10000条，TTL 1小时）
- L3SQLiteBackend: SQLite持久化（无限容量）
- MultiLevelCacheManager: 统一的多级缓存管理器

性能目标:
- 缓存命中率 > 90%
- 访问延迟降低 50%
- L1命中率 > 70%
- L2命中率 > 20%

作者: Athena平台团队
创建时间: 2026-04-24
版本: v2.2.0 "多级缓存"
"""

from .l1_memory import L1MemoryCache
from .l2_redis import L2RedisCache
from .l3_sqlite import L3SQLiteBackend
from .multilevel_cache import (
    CacheConfig,
    CacheEntry,
    CacheLevel,
    CacheStatistics,
    MultiLevelCacheManager,
)

__all__ = [
    "L1MemoryCache",
    "L2RedisCache",
    "L3SQLiteBackend",
    "MultiLevelCacheManager",
    "CacheConfig",
    "CacheEntry",
    "CacheLevel",
    "CacheStatistics",
]
