"""
缓存管理器
统一的缓存管理接口，支持多级缓存
"""

from typing import Any

from .memory_cache import MemoryCache
from .redis_cache import RedisCache


class CacheManager:
    """缓存管理器类"""

    def __init__(
        self, use_redis: bool | None = None, redis_config: dict | None = None, default_ttl: int = 300
    ):
        """
        初始化缓存管理器

        Args:
            use_redis: 是否使用Redis
            redis_config: Redis配置
            default_ttl: 默认生存时间
        """
        self._default_ttl = default_ttl

        # 初始化L1缓存（内存缓存）
        self._l1_cache = MemoryCache(default_ttl=default_ttl)

        # 初始化L2缓存（Redis缓存）
        self._l2_cache = None
        if use_redis:
            redis_config = redis_config or {}
            self._l2_cache = RedisCache(default_ttl=default_ttl, **redis_config)

    def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """
        设置缓存值（多级缓存）

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 生存时间

        Returns:
            是否设置成功
        """
        ttl = ttl if ttl is not None else self._default_ttl
        success = True

        # 写入L1缓存
        if not self._l1_cache.set(key, value, ttl):
            success = False

        # 写入L2缓存
        if self._l2_cache:
            if not self._l2_cache.set(key, value, ttl):
                success = False

        return success

    def get(self, key: str) -> Any | None:
        """
        获取缓存值（先查L1，再查L2）

        Args:
            key: 缓存键

        Returns:
            缓存值
        """
        # 先查L1缓存
        value = self._l1_cache.get(key)
        if value is not None:
            return value

        # 再查L2缓存
        if self._l2_cache:
            value = self._l2_cache.get(key)
            if value is not None:
                # 回填L1缓存
                self._l1_cache.set(key, value, self._default_ttl)
                return value

        return None

    def delete(self, key: str) -> bool:
        """
        删除缓存值（多级删除）

        Args:
            key: 缓存键

        Returns:
            是否删除成功
        """
        success = True

        # 删除L1缓存
        if not self._l1_cache.delete(key):
            success = False

        # 删除L2缓存
        if self._l2_cache:
            if not self._l2_cache.delete(key):
                success = False

        return success

    def exists(self, key: str) -> bool:
        """
        检查缓存键是否存在

        Args:
            key: 缓存键

        Returns:
            是否存在
        """
        return self.get(key) is not None

    def clear(self) -> bool:
        """
        清空所有缓存

        Returns:
            是否清空成功
        """
        success = True

        # 清空L1缓存
        if not self._l1_cache.clear():
            success = False

        # 清空L2缓存
        if self._l2_cache:
            if not self._l2_cache.clear():
                success = False

        return success

    def get_many(self, keys: list[str]) -> dict[str, Any]:
        """
        批量获取缓存值

        Args:
            keys: 缓存键列表

        Returns:
            键值对字典
        """
        result = {}
        for key in keys:
            value = self.get(key)
            if value is not None:
                result[key] = value
        return result

    def set_many(self, mapping: dict[str, Any]) -> bool:
        """
        批量设置缓存值

        Args:
            mapping: 键值对字典

        Returns:
            是否设置成功
        """
        success = True
        for key, value in mapping.items():
            if not self.set(key, value):
                success = False
        return success

    def delete_many(self, keys: list[str]) -> bool:
        """
        批量删除缓存值

        Args:
            keys: 缓存键列表

        Returns:
            是否删除成功
        """
        success = True
        for key in keys:
            if not self.delete(key):
                success = False
        return success

    def cleanup(self) -> int:
        """
        清理已过期的缓存项

        Returns:
            清理的项数
        """
        count = self._l1_cache.cleanup()
        return count

    def stats(self) -> dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            统计信息字典
        """
        stats = {
            "l1_size": self._l1_cache.size(),
            "l2_available": self._l2_cache is not None,
        }

        if self._l2_cache:
            stats["l2_size"] = self._l2_cache.size()
            stats["l2_ping"] = self._l2_cache.ping()

        return stats

    def __len__(self) -> int:
        """获取缓存大小"""
        return self._l1_cache.size()
