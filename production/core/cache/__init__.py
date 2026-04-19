"""
缓存模块
提供统一的缓存接口和多种缓存实现
"""

from __future__ import annotations
from .cache_manager import CacheManager
from .memory_cache import MemoryCache
from .redis_cache import RedisCache

__all__ = ["MemoryCache", "RedisCache", "CacheManager"]
