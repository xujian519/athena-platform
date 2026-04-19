from __future__ import annotations
"""
内存缓存实现
使用Python字典作为内存缓存存储
"""

import threading
import time
from typing import Any


class MemoryCache:
    """内存缓存类"""

    def __init__(self, default_ttl: int = 300):
        """
        初始化内存缓存

        Args:
            default_ttl: 默认生存时间（秒）
        """
        self._cache: dict[str, dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._default_ttl = default_ttl

    def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 生存时间（秒），None表示使用默认值

        Returns:
            是否设置成功
        """
        with self._lock:
            expiry = time.time() + (ttl if ttl is not None else self._default_ttl)
            self._cache[key] = {"value": value, "expiry": expiry}
            return True

    def get(self, key: str) -> Any | None:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值，如果不存在或已过期则返回None
        """
        with self._lock:
            if key not in self._cache:
                return None

            item = self._cache[key]
            if time.time() > item["expiry"]:
                # 已过期，删除
                del self._cache[key]
                return None

            return item["value"]

    def delete(self, key: str) -> bool:
        """
        删除缓存值

        Args:
            key: 缓存键

        Returns:
            是否删除成功
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

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
        with self._lock:
            self._cache.clear()
            return True

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
        with self._lock:
            for key, value in mapping.items():
                self.set(key, value)
            return True

    def delete_many(self, keys: list[str]) -> bool:
        """
        批量删除缓存值

        Args:
            keys: 缓存键列表

        Returns:
            是否删除成功
        """
        with self._lock:
            for key in keys:
                if key in self._cache:
                    del self._cache[key]
            return True

    def cleanup(self) -> int:
        """
        清理已过期的缓存项

        Returns:
            清理的项数
        """
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, item in self._cache.items() if current_time > item["expiry"]
            ]
            for key in expired_keys:
                del self._cache[key]
            return len(expired_keys)

    def size(self) -> int:
        """
        获取缓存大小

        Returns:
            缓存项数量
        """
        with self._lock:
            return len(self._cache)

    def keys(self) -> list[str]:
        """
        获取所有缓存键

        Returns:
            缓存键列表
        """
        with self._lock:
            return list(self._cache.keys())

    def values(self) -> list[Any]:
        """
        获取所有缓存值

        Returns:
            缓存值列表
        """
        with self._lock:
            return [item["value"] for item in self._cache.values()]

    def items(self) -> dict[str, Any]:
        """
        获取所有缓存项

        Returns:
            缓存键值对字典
        """
        with self._lock:
            return {key: item["value"] for key, item in self._cache.items()}

    def __len__(self) -> int:
        """获取缓存大小"""
        return self.size()

    def __contains__(self, key: str) -> bool:
        """检查键是否存在"""
        return self.exists(key)
