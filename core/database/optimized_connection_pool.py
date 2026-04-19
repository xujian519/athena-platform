#!/usr/bin/env python3
from __future__ import annotations
"""
优化的数据库连接池管理器
支持PostgreSQL、Redis等多数据库的连接池优化和监控
"""

import asyncio
import json
import time
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import asyncpg
import redis.asyncio as redis
from redis.asyncio import ConnectionPool

from core.database.unified_connection import get_postgres_pool
from core.logging_config import setup_logging

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


@dataclass
class PoolConfig:
    """连接池配置"""

    min_connections: int = 10
    max_connections: int = 50
    connection_timeout: float = 5.0
    idle_timeout: float = 300.0  # 5分钟
    max_lifetime: float = 3600.0  # 1小时
    health_check_interval: float = 30.0
    retry_attempts: int = 3
    retry_delay: float = 1.0


@dataclass
class PoolStats:
    """连接池统计信息"""

    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    failed_connections: int = 0
    avg_response_time: float = 0.0
    last_health_check: datetime | None = None
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class PostgreSQLPool:
    """优化的PostgreSQL连接池"""

    def __init__(self, config: dict[str, Any], pool_config: PoolConfig):
        self.config = config
        self.pool_config = pool_config
        self.pool: asyncpg.Pool | None = None
        self.stats = PoolStats()
        self._lock = asyncio.Lock()
        self._response_times: list[float] = []
        self._health_check_task: asyncio.Task | None = None

    async def initialize(self):
        """初始化连接池"""
        logger.info("🔧 初始化PostgreSQL连接池...")

        try:
            self.db = await get_postgres_pool(
                host=self.config.get("host", "localhost"),
                port=self.config.get("port", 5432),
                database=self.config.get("infrastructure/infrastructure/database"),
                user=self.config.get("user"),
                password=self.config.get("password"),
                min_size=self.pool_config.min_connections,
                max_size=self.pool_config.max_connections,
                command_timeout=self.pool_config.connection_timeout,
                server_settings={"application_name": "athena_legal_platform", "timezone": "UTC"},
            )

            # 启动健康检查任务
            self._health_check_task = _task_3_a08b6d = asyncio.create_task(
                self._health_check_loop()
            )

            logger.info(
                f"✅ PostgreSQL连接池初始化成功 (min: {self.pool_config.min_connections}, max: {self.pool_config.max_connections})"
            )

        except Exception as e:
            logger.error(f"❌ PostgreSQL连接池初始化失败: {e}")
            raise

    async def execute_query(self, query: str, *args, fetch: str = "all") -> Any:
        """执行查询"""
        if not self.pool:
            raise RuntimeError("连接池未初始化")

        start_time = time.time()

        try:
            async with self.pool.acquire() as conn:
                if fetch == "all":
                    result = await conn.fetch(query, *args)
                elif fetch == "one":
                    result = await conn.fetchrow(query, *args)
                elif fetch == "val":
                    result = await conn.fetchval(query, *args)
                else:
                    result = await conn.execute(query, *args)

                # 更新统计信息
                response_time = time.time() - start_time
                self._update_response_time(response_time)
                self.stats.active_connections += 1

                return result

        except Exception as e:
            self.stats.failed_connections += 1
            logger.error(f"查询执行失败: {e}")
            raise

    async def execute_transaction(self, queries: list[tuple]) -> Any:
        """执行事务"""
        if not self.pool:
            raise RuntimeError("连接池未初始化")

        start_time = time.time()

        try:
            async with self.pool.acquire() as conn, conn.transaction():
                results = []
                for query, args in queries:
                    if len(args) == 0:
                        result = await conn.execute(query)
                    else:
                        result = await conn.fetch(query, *args)
                    results.append(result)

                response_time = time.time() - start_time
                self._update_response_time(response_time)
                self.stats.active_connections += 1

                return results

        except Exception as e:
            self.stats.failed_connections += 1
            logger.error(f"事务执行失败: {e}")
            raise

    @asynccontextmanager
    async def get_connection(self):
        """获取连接上下文管理器"""
        if not self.pool:
            raise RuntimeError("连接池未初始化")

        start_time = time.time()

        try:
            async with self.pool.acquire() as conn:
                yield conn
                response_time = time.time() - start_time
                self._update_response_time(response_time)

        except Exception:
            self.stats.failed_connections += 1
            raise

    def _update_response_time(self, response_time: float) -> Any:
        """更新响应时间统计"""
        self._response_times.append(response_time)
        if len(self._response_times) > 100:  # 只保留最近100次
            self._response_times.pop(0)
        self.stats.avg_response_time = sum(self._response_times) / len(self._response_times)

    async def _health_check_loop(self):
        """健康检查循环"""
        while True:
            try:
                await asyncio.sleep(self.pool_config.health_check_interval)
                await self._perform_health_check()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"健康检查失败: {e}")

    async def _perform_health_check(self):
        """执行健康检查"""
        try:
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
                self.stats.last_health_check = datetime.now()

        except Exception as e:
            logger.error(f"PostgreSQL健康检查失败: {e}")
            self.stats.failed_connections += 1

    async def get_stats(self) -> PoolStats:
        """获取连接池统计信息"""
        if self.pool:
            self.stats.total_connections = self.pool.size
            self.stats.idle_connections = self.pool.size - self.pool._queue.qsize()

        return self.stats

    async def close(self):
        """关闭连接池"""
        logger.info("🔒 关闭PostgreSQL连接池...")

        if self._health_check_task:
            self._health_check_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._health_check_task

        if self.pool:
            await self.pool.close()
            self.pool = None

        logger.info("✅ PostgreSQL连接池已关闭")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()
        return False


class RedisPool:
    """优化的Redis连接池"""

    def __init__(self, config: dict[str, Any], pool_config: PoolConfig):
        self.config = config
        self.pool_config = pool_config
        self.pool: ConnectionPool | None = None
        self.stats = PoolStats()
        self._lock = asyncio.Lock()
        self._response_times: list[float] = []
        self._health_check_task: asyncio.Task | None = None

    async def initialize(self):
        """初始化Redis连接池"""
        logger.info("🔧 初始化Redis连接池...")

        try:
            self.pool = ConnectionPool.from_url(
                f"redis://{self.config.get('host', 'localhost')}:{self.config.get('port', 6379)}",
                max_connections=self.pool_config.max_connections,
                retry_on_timeout=True,
                socket_timeout=self.pool_config.connection_timeout,
                socket_connect_timeout=self.pool_config.connection_timeout,
                health_check_interval=self.pool_config.health_check_interval,
            )

            # 启动健康检查任务
            self._health_check_task = _task_3_a08b6d = asyncio.create_task(
                self._health_check_loop()
            )

            logger.info(f"✅ Redis连接池初始化成功 (max: {self.pool_config.max_connections})")

        except Exception as e:
            logger.error(f"❌ Redis连接池初始化失败: {e}")
            raise

    async def get_redis(self):
        """获取Redis连接"""
        if not self.pool:
            raise RuntimeError("Redis连接池未初始化")

        start_time = time.time()

        try:
            redis_client = redis.Redis(connection_pool=self.pool)

            # 测试连接
            await redis_client.ping()

            response_time = time.time() - start_time
            self._update_response_time(response_time)
            self.stats.active_connections += 1

            return redis_client

        except Exception as e:
            self.stats.failed_connections += 1
            logger.error(f"Redis连接失败: {e}")
            raise

    async def execute_command(self, command: str, *args) -> Any:
        """执行Redis命令"""
        redis_client = await self.get_redis()

        try:
            if command.lower() == "get":
                return await redis_client.get(*args)
            elif command.lower() == "set":
                return await redis_client.set(*args)
            elif command.lower() == "del":
                return await redis_client.delete(*args)
            elif command.lower() == "exists":
                return await redis_client.exists(*args)
            elif command.lower() == "hget":
                return await redis_client.hget(*args)
            elif command.lower() == "hset":
                return await redis_client.hset(*args)
            elif command.lower() == "hgetall":
                return await redis_client.hgetall(*args)
            else:
                # 执行任意命令
                return await redis_client.execute_command(command, *args)

        except Exception as e:
            logger.error(f"Redis命令执行失败: {command} - {e}")
            raise

    def _update_response_time(self, response_time: float) -> Any:
        """更新响应时间统计"""
        self._response_times.append(response_time)
        if len(self._response_times) > 100:
            self._response_times.pop(0)
        self.stats.avg_response_time = sum(self._response_times) / len(self._response_times)

    async def _health_check_loop(self):
        """健康检查循环"""
        while True:
            try:
                await asyncio.sleep(self.pool_config.health_check_interval)
                await self._perform_health_check()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Redis健康检查失败: {e}")

    async def _perform_health_check(self):
        """执行健康检查"""
        try:
            redis_client = await self.get_redis()
            await redis_client.ping()
            self.stats.last_health_check = datetime.now()

        except Exception as e:
            logger.error(f"Redis健康检查失败: {e}")
            self.stats.failed_connections += 1

    async def get_stats(self) -> PoolStats:
        """获取连接池统计信息"""
        if self.pool:
            self.stats.total_connections = self.pool.max_connections
            self.stats.idle_connections = self.pool.max_connections - len(
                self.pool._available_connections
            )

        return self.stats

    async def close(self):
        """关闭Redis连接池"""
        logger.info("🔒 关闭Redis连接池...")

        if self._health_check_task:
            self._health_check_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._health_check_task

        if self.pool:
            await self.pool.disconnect()
            self.pool = None

        logger.info("✅ Redis连接池已关闭")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()
        return False


class OptimizedConnectionManager:
    """优化的连接管理器"""

    def __init__(self):
        self.postgres_pools: dict[str, PostgreSQLPool] = {}
        self.redis_pools: dict[str, RedisPool] = {}
        self.configs: dict[str, dict] = {}
        self.pool_config = PoolConfig()

    def load_config(self, config_path: str | None = None) -> Any | None:
        """加载数据库配置"""
        if config_path:
            with open(config_path, encoding="utf-8") as f:
                self.configs = json.load(f)
        else:
            # 默认配置
            self.configs = {
                "postgresql": {
                    "patent_legal_db": {
                        "host": "localhost",
                        "port": 5432,
                        "infrastructure/infrastructure/database": "patent_legal_db",
                        "user": "postgres",
                        "password": "password",
                    },
                    "legal_world_model": {
                        "host": "localhost",
                        "port": 5432,
                        "infrastructure/infrastructure/database": "legal_world_model",
                        "user": "postgres",
                        "password": "password",
                    },
                },
                "redis": {
                    "default": {"host": "localhost", "port": 6379, "db": 0},
                    "cache": {"host": "localhost", "port": 6379, "db": 1},
                },
            }

    async def initialize(self, config_path: str | None = None):
        """初始化所有连接池"""
        logger.info("🚀 初始化优化连接管理器...")

        self.load_config(config_path)

        # 初始化PostgreSQL连接池
        for name, config in self.configs.get("postgresql", {}).items():
            try:
                pool = PostgreSQLPool(config, self.pool_config)
                await pool.initialize()
                self.postgres_pools[name] = pool
                logger.info(f"✅ PostgreSQL连接池 '{name}' 初始化成功")
            except Exception as e:
                logger.error(f"❌ PostgreSQL连接池 '{name}' 初始化失败: {e}")

        # 初始化Redis连接池
        for name, config in self.configs.get("redis", {}).items():
            try:
                pool = RedisPool(config, self.pool_config)
                await pool.initialize()
                self.redis_pools[name] = pool
                logger.info(f"✅ Redis连接池 '{name}' 初始化成功")
            except Exception as e:
                logger.error(f"❌ Redis连接池 '{name}' 初始化失败: {e}")

        logger.info("✅ 优化连接管理器初始化完成")

    async def get_postgres_pool(self, name: str = "patent_legal_db") -> PostgreSQLPool:
        """获取PostgreSQL连接池"""
        if name not in self.postgres_pools:
            raise ValueError(f"PostgreSQL连接池 '{name}' 不存在")
        return self.postgres_pools[name]

    async def get_redis_pool(self, name: str = "default") -> RedisPool:
        """获取Redis连接池"""
        if name not in self.redis_pools:
            raise ValueError(f"Redis连接池 '{name}' 不存在")
        return self.redis_pools[name]

    @asynccontextmanager
    async def get_postgres_connection(self, name: str = "patent_legal_db"):
        """获取PostgreSQL连接上下文管理器"""
        pool = await self.get_postgres_pool(name)
        async with pool.get_connection() as conn:
            yield conn

    async def get_redis_connection(self, name: str = "default"):
        """获取Redis连接"""
        pool = await self.get_redis_pool(name)
        return await pool.get_redis()

    async def get_all_stats(self) -> dict[str, Any]:
        """获取所有连接池的统计信息"""
        stats = {"timestamp": datetime.now().isoformat(), "postgresql": {}, "redis": {}}

        for name, pool in self.postgres_pools.items():
            pool_stats = await pool.get_stats()
            stats["postgresql"][name] = {
                "total_connections": pool_stats.total_connections,
                "active_connections": pool_stats.active_connections,
                "idle_connections": pool_stats.idle_connections,
                "failed_connections": pool_stats.failed_connections,
                "avg_response_time": pool_stats.avg_response_time,
                "last_health_check": (
                    pool_stats.last_health_check.isoformat()
                    if pool_stats.last_health_check
                    else None
                ),
            }

        for name, pool in self.redis_pools.items():
            pool_stats = await pool.get_stats()
            stats["redis"][name] = {
                "total_connections": pool_stats.total_connections,
                "active_connections": pool_stats.active_connections,
                "idle_connections": pool_stats.idle_connections,
                "failed_connections": pool_stats.failed_connections,
                "avg_response_time": pool_stats.avg_response_time,
                "last_health_check": (
                    pool_stats.last_health_check.isoformat()
                    if pool_stats.last_health_check
                    else None
                ),
            }

        return stats

    async def health_check(self) -> dict[str, bool]:
        """执行所有连接池的健康检查"""
        health_status = {"postgresql": {}, "redis": {}, "overall": True}

        all_healthy = True

        # 检查PostgreSQL连接池
        for name, pool in self.postgres_pools.items():
            try:
                async with pool.get_connection() as conn:
                    await conn.fetchval("SELECT 1")
                health_status["postgresql"][name] = True
            except Exception as e:
                logger.error(f"PostgreSQL连接池 '{name}' 健康检查失败: {e}")
                health_status["postgresql"][name] = False
                all_healthy = False

        # 检查Redis连接池
        for name, pool in self.redis_pools.items():
            try:
                redis_client = await pool.get_redis()
                await redis_client.ping()
                health_status["redis"][name] = True
            except Exception as e:
                logger.error(f"Redis连接池 '{name}' 健康检查失败: {e}")
                health_status["redis"][name] = False
                all_healthy = False

        health_status["overall"] = all_healthy
        return health_status

    async def close_all(self):
        """关闭所有连接池"""
        logger.info("🔒 关闭所有连接池...")

        # 关闭PostgreSQL连接池
        for name, pool in self.postgres_pools.items():
            try:
                await pool.close()
                logger.info(f"✅ PostgreSQL连接池 '{name}' 已关闭")
            except Exception as e:
                logger.error(f"❌ PostgreSQL连接池 '{name}' 关闭失败: {e}")

        # 关闭Redis连接池
        for name, pool in self.redis_pools.items():
            try:
                await pool.close()
                logger.info(f"✅ Redis连接池 '{name}' 已关闭")
            except Exception as e:
                logger.error(f"❌ Redis连接池 '{name}' 关闭失败: {e}")

        logger.info("✅ 所有连接池已关闭")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close_all()
        return False


# 全局连接管理器实例
connection_manager = OptimizedConnectionManager()


# 便捷函数
async def initialize_connection_manager(config_path: str | None = None):
    """初始化连接管理器"""
    await connection_manager.initialize(config_path)


async def get_patent_legal_db():
    """获取专利法律数据库连接池"""
    return await connection_manager.get_postgres_pool("patent_legal_db")


async def get_legal_world_model_db():
    """获取法律世界模型数据库连接池 (原athena_db)"""
    return await connection_manager.get_postgres_pool("legal_world_model")


# 兼容性别名
async def get_athena_db():
    """获取Athena数据库连接池 (兼容性别名，已更改为legal_world_model)"""
    return await get_legal_world_model_db()


async def get_default_redis():
    """获取默认Redis连接"""
    return await connection_manager.get_redis_connection("default")


async def get_cache_redis():
    """获取缓存Redis连接"""
    return await connection_manager.get_redis_connection("cache")


@asynccontextmanager
async def patent_legal_db_transaction():
    """专利法律数据库事务上下文管理器"""
    async with connection_manager.get_postgres_connection("patent_legal_db") as conn:
        async with conn.transaction():
            yield conn


# 示例使用
async def example_usage():
    """示例用法"""
    # 初始化连接管理器
    await initialize_connection_manager()

    try:
        # 使用PostgreSQL连接池
        patent_db = await get_patent_legal_db()
        results = await patent_db.execute_query(
            "SELECT COUNT(*) FROM legal_entities WHERE entity_type = %s",
            "legal_concept",
            fetch="val",
        )
        print(f"法律概念数量: {results}")

        # 使用Redis连接池
        redis_client = await get_default_redis()
        await redis_client.set("test_key", "test_value", ex=3600)
        value = await redis_client.get("test_key")
        print(f"Redis值: {value}")

        # 使用事务
        async with patent_legal_db_transaction() as conn:
            await conn.execute(
                "INSERT INTO legal_entities (entity_text, entity_type) VALUES (%s, %s)",
                "测试实体",
                "test_type",
            )

        # 获取统计信息
        stats = await connection_manager.get_all_stats()
        print("连接池统计:", json.dumps(stats, indent=2, ensure_ascii=False))

        # 健康检查
        health = await connection_manager.health_check()
        print("健康状态:", health)

    finally:
        # 关闭所有连接池
        await connection_manager.close_all()


if __name__ == "__main__":
    asyncio.run(example_usage())
