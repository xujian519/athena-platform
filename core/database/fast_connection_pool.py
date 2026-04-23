#!/usr/bin/env python3
from __future__ import annotations
"""
本地高性能 PostgreSQL 连接池管理器
针对本地使用场景优化,提供更快的连接和查询速度
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

import asyncpg

from core.database.unified_connection import get_postgres_pool

logger = logging.getLogger(__name__)


@dataclass
class FastPoolConfig:
    """本地高性能连接池配置"""

    # 本地环境可以使用更大的连接池
    min_connections: int = 10  # 最小连接数
    max_connections: int = 50  # 最大连接数
    connection_timeout: float = 3.0  # 连接超时(秒)- 本地环境可以更短
    command_timeout: float = 10.0  # 命令超时(秒)
    max_queries: int = 50000  # 每个连接最大查询数
    max_inactive_connection_lifetime: float = 300.0  # 空闲连接最大生命周期

    # 本地优化参数
    enable_prepared_statements: bool = True  # 启用预编译语句
    enable_statement_cache: bool = True  # 启用语句缓存
    statement_cache_size: int = 100  # 语句缓存大小


class FastPostgreSQLPool:
    """本地高性能 PostgreSQL 连接池"""

    def __init__(self, dsn: str, config: FastPoolConfig | None = None):
        self.dsn = dsn
        self.config = config or FastPoolConfig()
        self.pool: asyncpg.Pool | None = None
        self._initialized = False
        self._connect_time: Optional[float] = None
        self._query_count = 0
        self._total_query_time = 0.0

    async def initialize(self):
        """初始化连接池"""
        if self._initialized:
            return

        start_time = time.time()
        logger.info("🔧 初始化高性能 PostgreSQL 连接池...")

        try:
            # 创建连接池 - 本地优化配置
            self.db = await get_postgres_pool(
                self.dsn,
                min_size=self.config.min_connections,
                max_size=self.config.max_connections,
                command_timeout=self.config.command_timeout,
                max_queries=self.config.max_queries,
                max_inactive_connection_lifetime=self.config.max_inactive_connection_lifetime,
                # 本地性能优化
                server_settings={
                    "application_name": "athena_platform_fast",
                    "timezone": "UTC",
                    # JIT 编译对简单查询可能更慢
                    "jit": "off",
                    # 本地优化
                    "shared_buffers": "2GB",
                    "effective_cache_size": "12GB",
                    "work_mem": "32MB",
                    "random_page_cost": "1.1",
                },
                # 连接建立时立即执行测试查询
                init_command="SET synchronous_commit = off",  # 本地开发可以关闭同步提交
            )

            self._connect_time = time.time() - start_time
            self._initialized = True

            logger.info(f"✅ 高性能连接池初始化成功 (耗时: {self._connect_time:.3f}s)")
            logger.info(
                f"   - 连接池大小: {self.config.min_connections}-{self.config.max_connections}"
            )
            logger.info(f"   - 连接超时: {self.config.connection_timeout}s")
            logger.info(f"   - 命令超时: {self.config.command_timeout}s")

            # 预热连接池
            await self._warm_up_pool()

        except Exception as e:
            logger.error(f"❌ 连接池初始化失败: {e}")
            raise

    async def _warm_up_pool(self):
        """预热连接池 - 提前建立最小连接数"""
        if not self.pool:
            return

        logger.info("🔥 预热连接池...")
        start_time = time.time()

        # 并发建立最小连接
        tasks = [self.pool.acquire() for _ in range(self.config.min_connections)]
        connections = await asyncio.gather(*tasks, return_exceptions=True)

        # 立即释放连接
        for conn in connections:
            if isinstance(conn, Exception):
                logger.warning(f"预热连接警告: {conn}")
            elif self.pool:
                await self.pool.release(conn)

        warm_time = time.time() - start_time
        logger.info(f"✅ 连接池预热完成 (耗时: {warm_time:.3f}s)")

    @asynccontextmanager
    async def acquire(self):
        """获取数据库连接上下文管理器"""
        if not self._initialized or not self.pool:
            raise RuntimeError("连接池未初始化")

        async with self.pool.acquire() as connection:
            yield connection

    async def fetch(self, query: str, *args: Any, timeout: Optional[float] = None) -> list:
        """执行查询并返回所有结果"""
        start_time = time.time()

        async with self.acquire() as conn:
            try:
                result = await conn.fetch(query, *args, timeout=timeout)
                self._track_query(start_time)
                return result
            except Exception as e:
                logger.error(f"查询执行失败: {e}")
                raise

    async def fetchrow(
        self, query: Optional[str] = None, *args, timeout: Optional[float] = None
    ) -> asyncpg.Record | None:
        """执行查询并返回一行结果"""
        start_time = time.time()

        async with self.acquire() as conn:
            try:
                result = await conn.fetchrow(query, *args, timeout=timeout)
                self._track_query(start_time)
                return result
            except Exception as e:
                logger.error(f"查询执行失败: {e}")
                raise

    async def fetchval(
        self, query: str, *args, column: int = 0, timeout: Optional[float] = None
    ) -> Any:
        """执行查询并返回单个值"""
        start_time = time.time()

        async with self.acquire() as conn:
            try:
                result = await conn.fetchval(query, *args, column=column, timeout=timeout)
                self._track_query(start_time)
                return result
            except Exception as e:
                logger.error(f"查询执行失败: {e}")
                raise

    async def execute(self, query: str, *args, timeout: Optional[float] = None) -> str:
        """执行查询并返回状态字符串"""
        start_time = time.time()

        async with self.acquire() as conn:
            try:
                result = await conn.execute(query, *args, timeout=timeout)
                self._track_query(start_time)
                return result
            except Exception as e:
                logger.error(f"查询执行失败: {e}")
                raise

    async def executemany(self, command: str, args, timeout: Optional[float] = None):
        """批量执行命令"""
        start_time = time.time()

        async with self.acquire() as conn:
            try:
                result = await conn.executemany(command, args, timeout=timeout)
                self._track_query(start_time)
                return result
            except Exception as e:
                logger.error(f"批量执行失败: {e}")
                raise

    @asynccontextmanager
    async def transaction(self):
        """事务上下文管理器"""
        async with self.acquire() as conn, conn.transaction():
            yield conn

    def _track_query(self, start_time: float) -> Any:
        """跟踪查询统计信息"""
        query_time = time.time() - start_time
        self._query_count += 1
        self._total_query_time += query_time

        # 慢查询警告
        if query_time > 1.0:
            logger.warning(f"⚠️ 慢查询检测: {query_time:.3f}s")

    def get_stats(self) -> dict:
        """获取连接池统计信息"""
        if not self.pool:
            return {"status": "not_initialized"}

        return {
            "status": "initialized",
            "connect_time": self._connect_time,
            "query_count": self._query_count,
            "total_query_time": self._total_query_time,
            "avg_query_time": (
                self._total_query_time / self._query_count if self._query_count > 0 else 0
            ),
            "pool_size": self.pool.get_size(),
            "pool_max_size": self.pool.get_max_size(),
            "pool_idle_size": self.pool.get_idle_size(),
        }

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            result = await self.fetchval("SELECT 1")
            return result == 1
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return False

    async def close(self):
        """关闭连接池"""
        if self.pool:
            await self.pool.close()
            self._initialized = False
            logger.info("✅ 连接池已关闭")

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


class FastConnectionManager:
    """快速连接管理器"""

    def __init__(self):
        self.pools: dict[str, FastPostgreSQLPool] = {}

    async def get_pool(self, dsn: str, name: str = "default") -> FastPostgreSQLPool:
        """获取或创建连接池"""
        if name not in self.pools:
            pool = FastPostgreSQLPool(dsn)
            await pool.initialize()
            self.pools[name] = pool

        return self.pools[name]

    async def close_all(self):
        """关闭所有连接池"""
        for _name, pool in self.pools.items():
            await pool.close()
        self.pools.clear()


# 全局快速连接管理器
fast_db_manager = FastConnectionManager()


async def get_fast_postgres_pool(
    host: str = "localhost",
    port: int = 5432,
    database: str = "postgres",
    user: str = "postgres",
    password: str = "",
) -> FastPostgreSQLPool:
    """获取快速 PostgreSQL 连接池的便捷函数"""
    dsn = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    return await fast_db_manager.get_pool(dsn)


# 使用示例
async def example_usage():
    """使用示例"""
    # 获取连接池
    pool = await get_fast_postgres_pool(
        host="localhost", port=5432, database="postgres", user="postgres", password="your_password"
    )

    # 执行查询
    rows = await pool.fetch("SELECT * FROM patent_rules LIMIT 10")
    for row in rows:
        print(row)

    # 获取统计信息
    stats = pool.get_stats()
    print(f"统计信息: {stats}")


if __name__ == "__main__":
    asyncio.run(example_usage())
