#!/usr/bin/env python3
from __future__ import annotations
"""
统一缓存接口
Unified Cache Interface

整合所有缓存系统（语义缓存、多级缓存等）到统一接口

作者: Athena平台团队
创建时间: 2026-03-17
版本: v1.0.0
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class UnifiedCacheInterface(ABC):
    """统一缓存接口基类"""

    @abstractmethod
    def get(self, key: str) -> Any | None:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值，不存在返回None
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        删除缓存

        Args:
            key: 缓存键

        Returns:
            是否删除成功
        """
        pass

    @abstractmethod
    def clear(self) -> bool:
        """
        清空所有缓存

        Returns:
            是否清空成功
        """
        pass

    @abstractmethod
    def get_stats(self) -> dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            统计信息字典
        """
        pass


class SemanticCacheAdapter(UnifiedCacheInterface):
    """语义缓存适配器"""

    def __init__(self, cache_instance):
        """
        初始化适配器

        Args:
            cache_instance: SemanticCache实例
        """
        self.cache = cache_instance

    def get(self, key: str) -> Any | None:
        """获取缓存"""
        try:
            return self.cache.get(key)
        except Exception as e:
            logger.warning(f"⚠️ 语义缓存获取失败: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """设置缓存"""
        try:
            self.cache.set(key, value, ttl=ttl)
            return True
        except Exception as e:
            logger.warning(f"⚠️ 语义缓存设置失败: {e}")
            return False

    def delete(self, key: str) -> bool:
        """删除缓存（语义缓存不支持精确删除）"""
        logger.warning("⚠️ 语义缓存不支持精确删除")
        return False

    def clear(self) -> bool:
        """清空缓存"""
        try:
            self.cache.clear()
            return True
        except Exception as e:
            logger.warning(f"⚠️ 语义缓存清空失败: {e}")
            return False

    def get_stats(self) -> dict[str, Any]:
        """获取统计"""
        try:
            return self.cache.get_stats()
        except Exception as e:
            logger.warning(f"⚠️ 获取统计失败: {e}")
            return {}


class MultiLevelCacheAdapter(UnifiedCacheInterface):
    """多级缓存适配器"""

    def __init__(self, cache_instance):
        """
        初始化适配器

        Args:
            cache_instance: MultiLevelCacheManager实例
        """
        self.cache = cache_instance

    def get(self, key: str) -> Any | None:
        """获取缓存"""
        try:
            return self.cache.get(key)
        except Exception as e:
            logger.warning(f"⚠️ 多级缓存获取失败: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """设置缓存"""
        try:
            self.cache.set(key, value, ttl=ttl)
            return True
        except Exception as e:
            logger.warning(f"⚠️ 多级缓存设置失败: {e}")
            return False

    def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            self.cache.delete(key)
            return True
        except Exception as e:
            logger.warning(f"⚠️ 多级缓存删除失败: {e}")
            return False

    def clear(self) -> bool:
        """清空缓存"""
        try:
            self.cache.clear()
            return True
        except Exception as e:
            logger.warning(f"⚠️ 多级缓存清空失败: {e}")
            return False

    def get_stats(self) -> dict[str, Any]:
        """获取统计"""
        try:
            return self.cache.get_stats()
        except Exception as e:
            logger.warning(f"⚠️ 获取统计失败: {e}")
            return {}


class UnifiedCacheManager:
    """统一缓存管理器"""

    def __init__(self):
        """初始化缓存管理器"""
        self.caches: dict[str, UnifiedCacheInterface] = {}
        self.stats = {
            'total_gets': 0,
            'total_sets': 0,
            'total_deletes': 0,
            'hits': 0,
            'misses': 0,
        }

        logger.info("✅ 统一缓存管理器初始化完成")

    def register_cache(self, name: str, cache: UnifiedCacheInterface) -> bool:
        """
        注册缓存

        Args:
            name: 缓存名称
            cache: 缓存实例

        Returns:
            是否注册成功
        """
        if name in self.caches:
            logger.warning(f"⚠️ 缓存 '{name}' 已存在，将被覆盖")

        self.caches[name] = cache
        logger.info(f"✅ 缓存 '{name}' 注册成功")
        return True

    def get(self, cache_name: str, key: str) -> Any | None:
        """
        从指定缓存获取值

        Args:
            cache_name: 缓存名称
            key: 缓存键

        Returns:
            缓存值
        """
        self.stats['total_gets'] += 1

        if cache_name not in self.caches:
            logger.warning(f"⚠️ 缓存 '{cache_name}' 不存在")
            self.stats['misses'] += 1
            return None

        result = self.caches[cache_name].get(key)
        if result is not None:
            self.stats['hits'] += 1
        else:
            self.stats['misses'] += 1

        return result

    def set(self, cache_name: str, key: str, value: Any, ttl: int | None = None) -> bool:
        """
        设置缓存值

        Args:
            cache_name: 缓存名称
            key: 缓存键
            value: 缓存值
            ttl: 生存时间

        Returns:
            是否设置成功
        """
        self.stats['total_sets'] += 1

        if cache_name not in self.caches:
            logger.warning(f"⚠️ 缓存 '{cache_name}' 不存在")
            return False

        return self.caches[cache_name].set(key, value, ttl=ttl)

    def delete(self, cache_name: str, key: str) -> bool:
        """
        删除缓存

        Args:
            cache_name: 缓存名称
            key: 缓存键

        Returns:
            是否删除成功
        """
        self.stats['total_deletes'] += 1

        if cache_name not in self.caches:
            logger.warning(f"⚠️ 缓存 '{cache_name}' 不存在")
            return False

        return self.caches[cache_name].delete(key)

    def clear(self, cache_name: str | None = None) -> bool:
        """
        清空缓存

        Args:
            cache_name: 缓存名称，None表示清空所有

        Returns:
            是否清空成功
        """
        if cache_name:
            if cache_name not in self.caches:
                logger.warning(f"⚠️ 缓存 '{cache_name}' 不存在")
                return False
            return self.caches[cache_name].clear()
        else:
            # 清空所有
            success = True
            for name, cache in self.caches.items():
                if not cache.clear():
                    logger.warning(f"⚠️ 清空缓存 '{name}' 失败")
                    success = False
            return success

    def get_stats(self, cache_name: str | None = None) -> dict[str, Any]:
        """
        获取统计信息

        Args:
            cache_name: 缓存名称，None表示获取所有

        Returns:
            统计信息
        """
        if cache_name:
            if cache_name not in self.caches:
                return {}
            return self.caches[cache_name].get_stats()
        else:
            # 返回所有缓存统计
            all_stats = {
                'manager_stats': self.stats.copy(),
                'cache_stats': {}
            }

            if self.stats['total_gets'] > 0:
                all_stats['manager_stats']['hit_rate'] = (
                    self.stats['hits'] / self.stats['total_gets']
                )
            else:
                all_stats['manager_stats']['hit_rate'] = 0.0

            for name, cache in self.caches.items():
                all_stats['cache_stats'][name] = cache.get_stats()

            return all_stats


# 全局缓存管理器
_cache_manager: UnifiedCacheManager | None = None


def get_unified_cache_manager() -> UnifiedCacheManager:
    """
    获取全局缓存管理器

    Returns:
        UnifiedCacheManager实例
    """
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = UnifiedCacheManager()

        # 自动注册现有缓存
        try:
            from core.cache.semantic_cache import get_semantic_cache
            semantic_cache = get_semantic_cache()
            _cache_manager.register_cache('semantic', SemanticCacheAdapter(semantic_cache))
        except Exception as e:
            logger.warning(f"⚠️ 注册语义缓存失败: {e}")

        try:
            from core.cache.multi_level_cache import get_cache_manager
            multi_cache = get_cache_manager()
            _cache_manager.register_cache('multi_level', MultiLevelCacheAdapter(multi_cache))
        except Exception as e:
            logger.warning(f"⚠️ 注册多级缓存失败: {e}")

    return _cache_manager


# 导出
__all__ = [
    'UnifiedCacheInterface',
    'SemanticCacheAdapter',
    'MultiLevelCacheAdapter',
    'UnifiedCacheManager',
    'get_unified_cache_manager',
]
