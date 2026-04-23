#!/usr/bin/env python3

"""
统一缓存系统
Unified Cache System

提供高性能的缓存层，支持：
- Redis后端存储
- 自动TTL管理
- 批量操作
- 缓存统计
"""

import json
import logging
import os
from typing import Any, Optional

import redis

logger = logging.getLogger(__name__)


class UnifiedCache:
    """
    统一缓存管理器

    使用Redis作为后端，提供高性能的缓存服务

    特性：
    - 自动序列化/反序列化
    - TTL管理
    - 批量操作
    - 缓存统计
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        password: str = os.getenv("REDIS_PASSWORD", "redis123"),
        db: int = 0,
        decode_responses: bool = True,
        default_ttl: int = 3600,
    ):
        """
        初始化缓存管理器

        Args:
            host: Redis主机地址
            port: Redis端口
            password: Redis密码
            db: 数据库编号
            decode_responses: 是否自动解码响应
            default_ttl: 默认TTL（秒）
        """
        self.redis_client = redis.Redis(
            host=host,
            port=port,
            password=password,
            db=db,
            decode_responses=decode_responses,
        )
        self.default_ttl = default_ttl

        # 连接测试
        try:
            self.redis_client.ping()
            logger.info("✅ Redis缓存连接成功")
        except Exception as e:
            logger.error(f"❌ Redis缓存连接失败: {e}")
            raise

    async def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值，不存在返回None
        """
        try:
            value = self.redis_client.get(key)
            if value:
                # 反序列化JSON
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"获取缓存失败 [{key}]: {e}")
            return None

    async def set(
        self, key: str, value: Any, ttl: Optional[int] = None
    ) -> bool:
        """
        设置缓存

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None使用默认TTL

        Returns:
            是否成功
        """
        try:
            # 序列化为JSON
            json_value = json.dumps(value, ensure_ascii=False)

            # 设置TTL
            actual_ttl = ttl if ttl is not None else self.default_ttl

            # 存储到Redis
            self.redis_client.setex(key, actual_ttl, json_value)

            logger.debug(f"缓存设置成功 [{key}] TTL={actual_ttl}s")
            return True
        except Exception as e:
            logger.error(f"设置缓存失败 [{key}]: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        删除缓存

        Args:
            key: 缓存键

        Returns:
            是否成功
        """
        try:
            self.redis_client.delete(key)
            logger.debug(f"缓存删除成功 [{key}]")
            return True
        except Exception as e:
            logger.error(f"删除缓存失败 [{key}]: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """
        检查缓存是否存在

        Args:
            key: 缓存键

        Returns:
            是否存在
        """
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"检查缓存存在失败 [{key}]: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """
        清除匹配模式的所有缓存

        Args:
            pattern: 键模式（如 "patent:*"）

        Returns:
            删除的键数量
        """
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                count = self.redis_client.delete(*keys)
                logger.info(f"批量删除缓存成功: {count}个键 (pattern={pattern})")
                return count
            return 0
        except Exception as e:
            logger.error(f"批量删除缓存失败 [{pattern}]: {e}")
            return 0

    async def get_multi(self, keys: list[str]) -> dict[str, Any]:
        """
        批量获取缓存

        Args:
            keys: 缓存键列表

        Returns:
            键值对字典
        """
        try:
            if not keys:
                return {}

            # 批量获取
            values = self.redis_client.mget(keys)

            # 构建结果字典
            result = {}
            for key, value in zip(keys, values, strict=False):
                if value:
                    result[key] = json.loads(value)

            logger.debug(f"批量获取缓存: {len(result)}/{len(keys)}个命中")
            return result
        except Exception as e:
            logger.error(f"批量获取缓存失败: {e}")
            return {}

    async def set_multi(
        self, items: dict[str, Any], ttl: Optional[int] = None
    ) -> bool:
        """
        批量设置缓存

        Args:
            items: 键值对字典
            ttl: 过期时间（秒）

        Returns:
            是否成功
        """
        try:
            if not items:
                return True

            # 序列化所有值
            pipe = self.redis_client.pipeline()
            actual_ttl = ttl if ttl is not None else self.default_ttl

            for key, value in items.items():
                json_value = json.dumps(value, ensure_ascii=False)
                pipe.setex(key, actual_ttl, json_value)

            # 批量执行
            pipe.execute()

            logger.debug(f"批量设置缓存成功: {len(items)}个键")
            return True
        except Exception as e:
            logger.error(f"批量设置缓存失败: {e}")
            return False

    async def get_stats(self) -> dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            统计信息字典
        """
        try:
            info = self.redis_client.info()

            # 计算命中率
            hits = info.get("keyspace_hits", 0)
            misses = info.get("keyspace_misses", 0)
            total = hits + misses
            hit_rate = (hits / total * 100) if total > 0 else 0

            return {
                "hit_rate": round(hit_rate, 2),  # 命中率（百分比）
                "hits": hits,  # 命中次数
                "misses": misses,  # 未命中次数
                "total_requests": total,  # 总请求数
                "memory_usage": info.get("used_memory_human", "0B"),  # 内存使用
                "connected_clients": info.get("connected_clients", 0),  # 连接数
                "total_keys": self.redis_client.dbsize(),  # 总键数
                "uptime_days": info.get("uptime_in_days", 0),  # 运行天数
            }
        except Exception as e:
            logger.error(f"获取缓存统计失败: {e}")
            return {}

    async def increment(self, key: str, amount: int = 1) -> int:
        """
        递增计数器

        Args:
            key: 缓存键
            amount: 递增量

        Returns:
            递增后的值
        """
        try:
            value = self.redis_client.incrby(key, amount)
            return value
        except Exception as e:
            logger.error(f"递增计数器失败 [{key}]: {e}")
            return 0

    async def expire(self, key: str, ttl: int) -> bool:
        """
        设置键的过期时间

        Args:
            key: 缓存键
            ttl: 过期时间（秒）

        Returns:
            是否成功
        """
        try:
            return bool(self.redis_client.expire(key, ttl))
        except Exception as e:
            logger.error(f"设置过期时间失败 [{key}]: {e}")
            return False

    async def ttl(self, key: str) -> int:
        """
        获取键的剩余过期时间

        Args:
            key: 缓存键

        Returns:
            剩余秒数，-1表示永不过期，-2表示键不存在
        """
        try:
            return self.redis_client.ttl(key)
        except Exception as e:
            logger.error(f"获取TTL失败 [{key}]: {e}")
            return -2

    def health_check(self) -> bool:
        """
        健康检查

        Returns:
            是否健康
        """
        try:
            return self.redis_client.ping()
        except Exception as e:
            logger.error(f"Redis健康检查失败: {e}")
            return False


# 全局缓存实例（单例模式）
_cache_instance: Optional[UnifiedCache] = None


async def get_cache() -> UnifiedCache:
    """
    获取全局缓存实例

    Returns:
        UnifiedCache实例
    """
    global _cache_instance

    if _cache_instance is None:
        _cache_instance = UnifiedCache()

    return _cache_instance


async def cache_get(key: str) -> Optional[Any]:
    """
    便捷函数：获取缓存

    Args:
        key: 缓存键

    Returns:
        缓存值
    """
    cache = await get_cache()
    return await cache.get(key)


async def cache_set(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """
    便捷函数：设置缓存

    Args:
        key: 缓存键
        value: 缓存值
        ttl: 过期时间

    Returns:
        是否成功
    """
    cache = await get_cache()
    return await cache.set(key, value, ttl)


# 使用示例
if __name__ == "__main__":
    import asyncio

    async def demo():
        """演示缓存使用"""
        cache = UnifiedCache()

        # 设置缓存
        await cache.set("test_key", {"data": "test_value"}, ttl=60)

        # 获取缓存
        value = await cache.get("test_key")
        print(f"获取缓存: {value}")

        # 批量操作
        await cache.set_multi({
            "key1": "value1",
            "key2": "value2",
            "key3": "value3"
        })

        values = await cache.get_multi(["key1", "key2", "key3"])
        print(f"批量获取: {values}")

        # 获取统计
        stats = await cache.get_stats()
        print(f"缓存统计: {stats}")

        # 清理
        await cache.delete("test_key")

    asyncio.run(demo())

