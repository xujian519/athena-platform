#!/usr/bin/env python3
"""
优化数据库连接池
Optimized Database Connection Pool

提供高性能的数据库连接池管理

作者: 小诺·双鱼公主 v4.0
创建时间: 2025-12-25
版本: 1.0.0
"""

import logging
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool, QueuePool

logger = logging.getLogger(__name__)


class DatabaseConnectionPool:
    """数据库连接池"""

    def __init__(self, config=None):
        self.config = config
        self._engine = None
        self._session_factory = None
        self._initialized = False

    async def initialize(self, db_url: str):
        """初始化连接池"""
        if self._initialized:
            return

        # 创建引擎 (性能优化配置)
        self._engine = create_async_engine(
            db_url,
            # 连接池配置 - 根据性能分析优化
            poolclass=QueuePool,
            pool_size=50,  # 20 → 50 (高并发优化)
            max_overflow=20,  # 10 → 20 (峰值扩容)
            pool_timeout=10,  # 30 → 10 (快速失败)
            pool_recycle=1800,  # 3600 → 1800 (30分钟回收)
            pool_pre_ping=True,  # 保持启用连接健康检查
            # 性能优化参数
            echo=False,  # 不输出SQL日志(生产环境)
            echo_pool=False,  # 不输出连接池日志
            future=True,  # 使用SQLAlchemy 2.0语法
            pool_use_lifo=True,  # 使用LIFO减少连接 stale
            connect_args={
                "connect_timeout": 10,
                "command_timeout": 30,
                "server_settings": {
                    "jit": "off",  # 关闭JIT提升简单查询性能
                    "application_name": "athena_platform",
                },
            },
        )

        # 创建会话工厂
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        self._initialized = True
        logger.info("✅ 数据库连接池初始化完成")

    @asynccontextmanager
    async def get_session(self):
        """获取数据库会话"""
        if not self._initialized:
            raise RuntimeError("连接池未初始化")

        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def close(self):
        """关闭连接池"""
        if self._engine:
            await self._engine.dispose()
            self._initialized = False
            logger.info("✅ 数据库连接池已关闭")

    def get_pool_status(self) -> dict:
        """获取连接池状态 (增强版)"""
        if not self._engine or not self._engine.pool:
            return {"status": "not_initialized"}

        pool = self._engine.pool
        size = pool.size()
        checked_out = pool.checkedout()

        # 计算使用率
        usage_rate = checked_out / size if size > 0 else 0

        return {
            "status": "initialized",
            "size": size,
            "checked_in": pool.checkedin(),
            "checked_out": checked_out,
            "overflow": pool.overflow(),
            "usage_rate": f"{usage_rate:.2%}",
            "max_capacity": size + pool.max_overflow,
        }


# 全局连接池实例
_connection_pool: DatabaseConnectionPool | None = None


async def get_connection_pool(config=None, db_url: str | None = None) -> DatabaseConnectionPool:
    """获取连接池实例"""
    global _connection_pool

    if _connection_pool is None:
        _connection_pool = DatabaseConnectionPool(config)

        if db_url is None:
            from config.central_config import get_config

            config_obj = get_config()
            db_url = config_obj.get_database_url()

        await _connection_pool.initialize(db_url)

    return _connection_pool


# 别名,保持向后兼容
get_database_pool = get_connection_pool
