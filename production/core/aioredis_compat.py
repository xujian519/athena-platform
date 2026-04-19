"""
aioredis兼容层 - 使用官方redis.asyncio替代已弃用的aioredis库
Compatibility layer for aioredis -> redis.asyncio

此模块提供统一的接口,兼容旧的aioredis API和新的redis.asyncio API
版本: 2.0.0
更新时间: 2026-01-26
"""

# 使用官方redis库的asyncio模块（替代已弃用的aioredis）
from __future__ import annotations
try:
    from redis import asyncio as aioredis

    # 导出核心类
    Redis = aioredis.Redis
    ConnectionPool = aioredis.ConnectionPool

    # 提供from_url便捷函数
    def from_redis_url(url: str, **kwargs):
        """从URL创建Redis连接"""
        return aioredis.Redis.from_url(url, **kwargs)

    from_redis_url = from_redis_url

except ImportError:
    # 如果redis也不可用,创建模拟实现用于开发测试
    import logging

    logging.warning("⚠️ redis.asyncio 不可用,使用模拟Redis实现")

    class MockRedis:
        """模拟Redis客户端（用于开发测试）"""

        async def get(self, key: str):
            return None

        async def set(self, key: str, value: str, ex: int | None = None):
            return True

        async def delete(self, key: str):
            return 1

        async def exists(self, key: str):
            return 0

        async def ping(self):
            return True

        async def close(self):
            pass

        async def aclose(self):
            """异步关闭连接（redis>=5.0接口）"""
            await self.close()

    Redis = MockRedis
    ConnectionPool = None
    from_redis_url = None


__all__ = ["ConnectionPool", "Redis", "from_redis_url"]
