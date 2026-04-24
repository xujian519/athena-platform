#!/usr/bin/env python3
"""
L2 Redis缓存实现 - Phase 2.2架构优化

L2 Redis Cache - 分布式Redis缓存层

特性:
- 异步Redis连接池
- 自动重连机制
- 容量限制（通过Redis maxmemory策略）
- 分布式共享缓存

配置:
- 容量: 10000条（Redis配置）
- TTL: 1小时（3600秒）
- 连接池: 10个连接

依赖:
- pip install redis[hiredis]

作者: Athena平台团队
创建时间: 2026-04-24
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None

logger = logging.getLogger(__name__)


class L2RedisCache:
    """
    L2 Redis缓存

    提供分布式、持久化的二级缓存。
    如果Redis不可用，会优雅降级（返回None，不影响主流程）。
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        password: Optional[str] = None,
        db: int = 0,
        ttl_seconds: int = 3600,
        pool_size: int = 10,
        key_prefix: str = "athena_ctx:",
        enabled: bool = True,
    ):
        """
        初始化L2 Redis缓存

        Args:
            host: Redis主机
            port: Redis端口
            password: Redis密码
            db: Redis数据库编号
            ttl_seconds: 默认TTL（秒）
            pool_size: 连接池大小
            key_prefix: 键前缀
            enabled: 是否启用Redis缓存
        """
        self.host = host
        self.port = port
        self.password = password
        self.db = db
        self.ttl_seconds = ttl_seconds
        self.pool_size = pool_size
        self.key_prefix = key_prefix
        self.enabled = enabled and aioredis is not None

        self._pool: Any = None
        self._lock = asyncio.Lock()

        # 统计信息
        self._hits = 0
        self._misses = 0
        self._errors = 0
        self._reconnects = 0

        if self.enabled:
            logger.info(
                f"✅ L2 Redis缓存配置: {host}:{port}, ttl={ttl_seconds}s, pool={pool_size}"
            )
        else:
            logger.warning("⚠️ L2 Redis缓存已禁用或redis未安装")

    async def _get_pool(self):
        """获取Redis连接池"""
        if not self.enabled:
            return None

        if self._pool is None:
            async with self._lock:
                if self._pool is None:
                    try:
                        self._pool = await aioredis.ConnectionPool(
                            host=self.host,
                            port=self.port,
                            password=self.password,
                            db=self.db,
                            max_connections=self.pool_size,
                            decode_responses=False,  # 使用bytes模式
                            retry_on_timeout=True,
                            retry_on_error=[aioredis.ConnectionError],
                        )
                        logger.info(f"✅ Redis连接池创建成功: {self.host}:{self.port}")
                    except Exception as e:
                        logger.error(f"❌ Redis连接失败: {e}")
                        self.enabled = False
                        self._errors += 1
                        return None

        return self._pool

    def _make_key(self, key: str) -> str:
        """生成带前缀的Redis键"""
        return f"{self.key_prefix}{key}"

    async def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            Any: 缓存值，不存在返回None
        """
        if not self.enabled:
            return None

        try:
            pool = await self._get_pool()
            if pool is None:
                return None

            async with aioredis.Redis(connection_pool=pool) as client:
                redis_key = self._make_key(key)
                data = await client.get(redis_key)

                if data is None:
                    self._misses += 1
                    logger.debug(f"L2未命中: {key}")
                    return None

                # 反序列化
                try:
                    value = json.loads(data)
                    self._hits += 1
                    logger.debug(f"L2命中: {key}")
                    return value
                except json.JSONDecodeError:
                    # 尝试作为字符串返回
                    self._hits += 1
                    return data.decode("utf-8")

        except Exception as e:
            logger.error(f"L2获取失败: {key}, 错误: {e}")
            self._errors += 1
            # 尝试重连
            await self._reconnect()
            return None

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
        if not self.enabled:
            return False

        try:
            pool = await self._get_pool()
            if pool is None:
                return False

            ttl = ttl_seconds or self.ttl_seconds

            # 序列化
            try:
                data = json.dumps(value, ensure_ascii=False)
            except (TypeError, ValueError):
                # 无法JSON序列化，转为字符串
                data = str(value)

            async with aioredis.Redis(connection_pool=pool) as client:
                redis_key = self._make_key(key)
                await client.setex(redis_key, ttl, data)
                logger.debug(f"L2设置: {key} (TTL: {ttl}s)")
                return True

        except Exception as e:
            logger.error(f"L2设置失败: {key}, 错误: {e}")
            self._errors += 1
            await self._reconnect()
            return False

    async def delete(self, key: str) -> bool:
        """
        删除缓存值

        Args:
            key: 缓存键

        Returns:
            bool: 删除成功返回True
        """
        if not self.enabled:
            return False

        try:
            pool = await self._get_pool()
            if pool is None:
                return False

            async with aioredis.Redis(connection_pool=pool) as client:
                redis_key = self._make_key(key)
                result = await client.delete(redis_key)
                logger.debug(f"L2删除: {key}, 结果: {result}")
                return result > 0

        except Exception as e:
            logger.error(f"L2删除失败: {key}, 错误: {e}")
            self._errors += 1
            return False

    async def clear(self) -> bool:
        """
        清空所有带前缀的缓存

        Returns:
            bool: 清空成功返回True
        """
        if not self.enabled:
            return False

        try:
            pool = await self._get_pool()
            if pool is None:
                return False

            async with aioredis.Redis(connection_pool=pool) as client:
                # 扫描并删除所有前缀键
                pattern = f"{self.key_prefix}*"
                count = 0

                async for key in client.scan_iter(match=pattern, count=100):
                    await client.delete(key)
                    count += 1

                logger.info(f"L2清空: 删除了{count}个键")
                return True

        except Exception as e:
            logger.error(f"L2清空失败: {e}")
            self._errors += 1
            return False

    async def exists(self, key: str) -> bool:
        """
        检查键是否存在

        Args:
            key: 缓存键

        Returns:
            bool: 存在返回True
        """
        if not self.enabled:
            return False

        try:
            pool = await self._get_pool()
            if pool is None:
                return False

            async with aioredis.Redis(connection_pool=pool) as client:
                redis_key = self._make_key(key)
                result = await client.exists(redis_key)
                return result > 0

        except Exception as e:
            logger.error(f"L2存在检查失败: {key}, 错误: {e}")
            self._errors += 1
            return False

    async def get_many(self, keys: list[str]) -> Dict[str, Any]:
        """
        批量获取缓存值

        Args:
            keys: 缓存键列表

        Returns:
            Dict[str, Any]: 键到值的映射
        """
        if not self.enabled or not keys:
            return {}

        try:
            pool = await self._get_pool()
            if pool is None:
                return {}

            redis_keys = [self._make_key(k) for k in keys]

            async with aioredis.Redis(connection_pool=pool) as client:
                values = await client.mget(redis_keys)

                result = {}
                for key, value in zip(keys, values):
                    if value is not None:
                        try:
                            result[key] = json.loads(value)
                            self._hits += 1
                        except json.JSONDecodeError:
                            result[key] = value.decode("utf-8")
                            self._hits += 1
                    else:
                        self._misses += 1

                return result

        except Exception as e:
            logger.error(f"L2批量获取失败: {e}")
            self._errors += 1
            return {}

    async def set_many(
        self, mapping: dict[str, Any], ttl_seconds: Optional[int] = None
    ) -> int:
        """
        批量设置缓存值

        Args:
            mapping: 键到值的映射
            ttl_seconds: 自定义TTL（可选）

        Returns:
            int: 成功设置的数量
        """
        if not self.enabled or not mapping:
            return 0

        ttl = ttl_seconds or self.ttl_seconds
        count = 0

        for key, value in mapping.items():
            if await self.set(key, value, ttl):
                count += 1

        return count

    async def _reconnect(self) -> None:
        """重新连接Redis"""
        async with self._lock:
            if self._pool is not None:
                try:
                    await self._pool.aclose()
                except Exception:
                    pass
                self._pool = None
                self._reconnects += 1
                logger.info("L2 Redis重连")

    async def close(self) -> None:
        """关闭连接池"""
        if self._pool is not None:
            try:
                await self._pool.aclose()
                logger.info("L2 Redis连接池已关闭")
            except Exception as e:
                logger.error(f"关闭Redis连接池失败: {e}")
            self._pool = None

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0

        return {
            "level": "L2",
            "type": "redis",
            "enabled": self.enabled,
            "host": f"{self.host}:{self.port}",
            "db": self.db,
            "hits": self._hits,
            "misses": self._misses,
            "errors": self._errors,
            "reconnects": self._reconnects,
            "hit_rate": hit_rate,
            "ttl_seconds": self.ttl_seconds,
            "pool_size": self.pool_size,
            "key_prefix": self.key_prefix,
        }

    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            bool: 健康返回True
        """
        if not self.enabled:
            return False

        try:
            pool = await self._get_pool()
            if pool is None:
                return False

            async with aioredis.Redis(connection_pool=pool) as client:
                await client.ping()
                return True

        except Exception as e:
            logger.error(f"L2健康检查失败: {e}")
            return False


__all__ = ["L2RedisCache"]
