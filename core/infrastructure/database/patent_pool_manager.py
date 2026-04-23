#!/usr/bin/env python3

"""
Patent数据库优化连接池管理器
针对2800万+专利数据的优化连接池
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Optional

import asyncpg

from core.infrastructure.database.unified_connection import get_postgres_pool

logger = logging.getLogger(__name__)


@dataclass
class PatentPoolConfig:
    """Patent数据库连接池配置"""

    min_connections: int = 20
    max_connections: int = 100
    connection_timeout: float = 10.0
    idle_timeout: float = 600.0
    max_lifetime: float = 7200.0
    health_check_interval: float = 60.0
    command_timeout: float = 30.0

    # 性能优化
    enable_query_cache: bool = True
    query_cache_size: int = 1000
    batch_size: int = 1000


class PatentDBPoolManager:
    """Patent数据库连接池管理器(优化版)"""

    _instance: Optional[PatentDBPoolManager] = None
    _pool: asyncpg.Optional[Pool] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            self.config = PatentPoolConfig()
            self.initialized = False
            self._query_cache = {}

    async def initialize(self, db_config: Optional[dict[str, Any]] = None):
        """初始化连接池"""
        if self.initialized:
            return

        config = db_config or {
            "host": "localhost",
            "port": 5432,
            "database": "patent_db",
            "user": "xujian",
        }

        try:
            logger.info("🔧 初始化Patent数据库连接池(优化版)...")

            self._db = await get_postgres_pool(
                host=config.get("host", "localhost"),
                port=config.get("port", 5432),
                database=config.get("database", "patent_db"),
                user=config.get("user", "xujian"),
                password=config.get("password", ""),
                min_size=self.config.min_connections,
                max_size=self.config.max_connections,
                command_timeout=self.config.command_timeout,
                timeout=self.config.connection_timeout,
                max_inactive_connection_lifetime=self.config.idle_timeout,
                max_lifetime=self.config.max_lifetime,
                server_settings={"application_name": "athena_patent_optimized", "timezone": "UTC"},
            )

            self.initialized = True
            logger.info("✅ Patent数据库连接池初始化成功")
            logger.info(
                f"   连接池大小: {self.config.min_connections}-{self.config.max_connections}"
            )
            logger.info(f"   超时设置: {self.config.command_timeout}秒")
            logger.info(f'   查询缓存: {"启用" if self.config.enable_query_cache else "禁用"}')

        except Exception as e:
            logger.error(f"❌ Patent数据库连接池初始化失败: {e}")
            raise

    async def execute_query(
        self, query: str, *args, fetch: str = "all", use_cache: bool = True
    ) -> Any:
        """执行查询(带缓存)"""
        if not self._pool:
            await self.initialize()

        # 检查缓存
        cache_key = f"{query}:{args}" if use_cache else None
        if cache_key and self.config.enable_query_cache and cache_key in self._query_cache:
            logger.debug(f"🎯 缓存命中: {query[:50]}...")
            return self._query_cache[cache_key]

        async with self._pool.acquire() as conn:
            try:
                if fetch == "all":
                    result = await conn.fetch(query, *args)
                elif fetch == "one":
                    result = await conn.fetchrow(query, *args)
                elif fetch == "val":
                    result = await conn.fetchval(query, *args)
                else:
                    result = await conn.execute(query, *args)

                # 更新缓存
                if cache_key and len(self._query_cache) < self.config.query_cache_size:
                    self._query_cache[cache_key] = result

                return result

            except Exception as e:
                logger.error(f"❌ 查询执行失败: {e}")
                logger.error(f"   SQL: {query[:100]}...")
                raise

    async def batch_insert(
        self, table: str, data: list[dict[str, Any], batch_size: Optional[int] = None
    ) -> int:
        """批量插入(优化版)"""
        if not data:
            return 0

        batch_size = batch_size or self.config.batch_size
        total_inserted = 0

        # 分批插入
        for i in range(0, len(data), batch_size):
            batch = data[i : i + batch_size]

            # 构建批量插入SQL
            columns = list(batch[0].keys())
            placeholders = ", ".join([f"${j+1}" for j in range(len(columns))])
            sql = f"""
                INSERT INTO {table} ({', '.join(columns)})
                VALUES ({placeholders})
                ON CONFLICT DO NOTHING
            """

            # 执行批量插入
            async with self._pool.acquire() as conn:
                for row in batch:
                    values = [row[col] for col in columns]
                    await conn.execute(sql, *values)
                    total_inserted += 1

            logger.info(f"✅ 批量插入进度: {total_inserted}/{len(data)}")

        return total_inserted

    async def get_stats(self) -> dict[str, Any]:
        """获取连接池统计信息"""
        if not self._pool:
            return {}

        return {
            "min_size": self._pool.get_min_size(),
            "max_size": self._pool.get_max_size(),
            "size": self._pool.get_size(),
            "available": self._pool.get_idle_size(),
            "cache_size": len(self._query_cache),
            "initialized": self.initialized,
        }

    async def close(self):
        """关闭连接池"""
        if self._pool:
            await self._pool.close()
            self.initialized = False
            logger.info("🔒 Patent数据库连接池已关闭")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()
        return False


# 全局单例
_patent_pool_manager: Optional[PatentDBPoolManager] = None


async def get_patent_pool() -> PatentDBPoolManager:
    """获取Patent数据库连接池单例"""
    global _patent_pool_manager
    if _patent_pool_manager is None:
        _patent_pool_manager = PatentDBPoolManager()
        await _patent_pool_manager.initialize()
    return _patent_pool_manager


# 使用示例
async def example_usage():
    """使用示例"""
    # 获取连接池
    pool = await get_patent_pool()

    # 执行查询
    count = await pool.execute_query("SELECT COUNT(*) FROM patents", fetch="val")
    print(f"专利总数: {count:,}")

    # 批量查询
    patents = await pool.execute_query(
        """
        SELECT application_number, patent_name
        FROM patents
        WHERE ipc_main_class LIKE 'G06F%'
        LIMIT 10
    """,
        fetch="all",
    )

    for patent in patents:
        print(f'{patent["application_number"]}: {patent["patent_name"]}')

    # 获取统计信息
    stats = await pool.get_stats()
    print(f"\n连接池状态: {stats}")


if __name__ == "__main__":
    asyncio.run(example_usage())

