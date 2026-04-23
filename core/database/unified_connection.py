#!/usr/bin/env python3
from __future__ import annotations
"""
统一数据库连接管理模块
Unified Database Connection Manager

提供统一的数据库连接接口,支持PostgreSQL、SQLite等

作者: Athena平台团队
版本: v1.0.0
"""

import logging
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# PostgreSQL连接管理
class PostgreSQLConnection:
    """PostgreSQL连接管理器(使用asyncpg)"""

    def __init__(self, dsn: str, **kwargs):
        self.dsn = dsn
        self.kwargs = kwargs
        self._pool = None

    async def create_pool(self, min_size: int = 5, max_size: int = 20):
        """创建连接池"""
        try:
            from core.database.unified_connection import get_postgres_pool

            self._db = await get_postgres_pool(
                self.dsn, min_size=min_size, max_size=max_size, **self.kwargs
            )
            logger.info(f"PostgreSQL连接池已创建: {min_size}-{max_size}")
            return self._pool
        except ImportError:
            raise ImportError("需要安装asyncpg: pip install asyncpg") from None

    @asynccontextmanager
    async def connection(self):
        """获取连接上下文管理器"""
        if self._pool is None:
            await self.create_pool()

        async with self._pool.acquire() as conn:
            yield conn

    @asynccontextmanager
    async def transaction(self):
        """获取事务上下文管理器"""
        if self._pool is None:
            await self.create_pool()

        async with self._pool.acquire() as conn, conn.transaction():
            yield conn

    async def execute(self, query: str, *args, timeout: Optional[float] = None) -> str:
        """执行SQL(不返回结果)"""
        async with self.connection() as conn:
            return await conn.execute(query, *args, timeout=timeout)

    async def fetch(self, query: str, *args, timeout: Optional[float] = None) -> list[dict]:
        """查询并返回所有行"""
        async with self.connection() as conn:
            rows = await conn.fetch(query, *args, timeout=timeout)
            return [dict(r) for r in rows]

    async def fetchone(self, query: str, *args, timeout: Optional[float] = None) -> dict | None:
        """查询并返回一行"""
        async with self.connection() as conn:
            row = await conn.fetchrow(query, *args, timeout=timeout)
            return dict(row) if row else None

    async def fetchval(
        self, query: str, *args, column: int = 0, timeout: Optional[float] = None
    ) -> Any:
        """查询单个值"""
        async with self.connection() as conn:
            return await conn.fetchval(query, *args, column=column, timeout=timeout)

    async def close(self):
        """关闭连接池"""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("PostgreSQL连接池已关闭")


# SQLite连接管理
class SQLiteConnection:
    """SQLite连接管理器"""

    def __init__(self, db_path: str | Path, **kwargs):
        self.db_path = Path(db_path)
        self.kwargs = kwargs
        self._conn = None

    def connect(self):
        """创建连接"""
        import sqlite3

        # 确保目录存在
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._conn = sqlite3.connect(str(self.db_path), **self.kwargs)
        self._conn.row_factory = sqlite3.Row
        logger.info(f"SQLite连接已创建: {self.db_path}")
        return self._conn

    @contextmanager
    def connection(self):
        """获取连接上下文管理器"""
        if self._conn is None:
            self.connect()

        yield self._conn

    @contextmanager
    def transaction(self):
        """获取事务上下文管理器"""
        if self._conn is None:
            self.connect()

        try:
            yield self._conn
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise

    def execute(self, query: str, *args) -> Any:
        """执行SQL"""
        with self.connection() as conn:
            cursor = conn.execute(query, args)
            return cursor

    def fetchall(self, query: str, *args) -> list[dict]:
        """查询所有行"""
        with self.connection() as conn:
            cursor = conn.execute(query, args)
            return [dict(row) for row in cursor.fetchall()]

    def fetchone(self, query: str, *args) -> dict | None:
        """查询一行"""
        with self.connection() as conn:
            cursor = conn.execute(query, args)
            row = cursor.fetchone()
            return dict(row) if row else None

    def fetchval(self, query: str, *args, column: int = 0) -> Any:
        """查询单个值"""
        row = self.fetchone(query, *args)
        if row:
            values = list(row.values())
            if column < len(values):
                return values[column]
        return None

    def close(self):
        """关闭连接"""
        if self._conn:
            self._conn.close()
            self._conn = None
            logger.info("SQLite连接已关闭")


# 统一接口
class DatabaseConnection:
    """
    统一数据库连接接口

    根据DSN类型自动选择合适的连接器
    """

    @staticmethod
    def from_dsn(dsn: str, **kwargs):
        """
        从DSN创建连接

        DSN格式:
        - PostgreSQL: postgresql://user:pass@host:port/db
        - SQLite: sqlite:///path/to/db.sqlite

        Examples:
            >>> db = DatabaseConnection.from_dsn("postgresql://localhost/mydb")
            >>> db = DatabaseConnection.from_dsn("sqlite:///data/mydb.sqlite")
        """
        if dsn.startswith("postgresql://") or dsn.startswith("postgres://"):
            return PostgreSQLConnection(dsn, **kwargs)
        elif dsn.startswith("sqlite:///") or dsn.startswith("sqlite://"):
            # 提取路径
            path = dsn.replace("sqlite:///", "").replace("sqlite://", "")
            return SQLiteConnection(path, **kwargs)
        else:
            raise ValueError(f"不支持的DSN格式: {dsn}")

    @staticmethod
    def postgresql(host: str, database: str, user: str, password: str, port: int = 5432, **kwargs):
        """创建PostgreSQL连接"""
        dsn = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        return PostgreSQLConnection(dsn, **kwargs)

    @staticmethod
    def sqlite(db_path: str | Path, **kwargs):
        """创建SQLite连接"""
        return SQLiteConnection(db_path, **kwargs)


# 便捷函数
async def get_postgres_pool(dsn: str, **kwargs) -> PostgreSQLConnection:
    """获取PostgreSQL连接池"""
    db = PostgreSQLConnection(dsn, **kwargs)
    await db.create_pool()
    return db


def get_sqlite_conn(db_path: str | Path, **kwargs) -> SQLiteConnection:
    """获取SQLite连接"""
    return SQLiteConnection(db_path, **kwargs)


# 上下文管理器
@asynccontextmanager
async def postgres_context(dsn: str, **kwargs):
    """PostgreSQL连接上下文管理器"""
    db = PostgreSQLConnection(dsn, **kwargs)
    await db.create_pool()
    try:
        yield db
    finally:
        await db.close()


@contextmanager
def sqlite_context(db_path: str | Path, **kwargs):
    """SQLite连接上下文管理器"""
    db = SQLiteConnection(db_path, **kwargs)
    try:
        yield db
    finally:
        db.close()


# 旧代码兼容(psycopg2同步接口)
class Psycopg2Connection:
    """psycopg2连接封装(向后兼容)"""

    def __init__(
        self, host: str, database: str, user: str, password: str, port: int = 5432, **kwargs
    ):
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.port = port
        self.kwargs = kwargs
        self._conn = None

    def connect(self):
        """创建连接"""
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
        except ImportError:
            raise ImportError("需要安装psycopg2: pip install psycopg2-binary") from None

        self._conn = psycopg2.connect(
            host=self.host,
            database=self.database,
            user=self.user,
            password=self.password,
            port=self.port,
            **self.kwargs,
        )
        logger.info(f"psycopg2连接已创建: {self.database}@{self.host}")
        return self._conn

    @contextmanager
    def cursor(self):
        """获取游标"""
        if self._conn is None:
            self.connect()

        from psycopg2.extras import RealDictCursor

        cursor = self._conn.cursor(cursor_factory=RealDictCursor)
        try:
            yield cursor
        finally:
            cursor.close()

    def execute(self, query: str, params: tuple | None = None):
        """执行SQL"""
        with self.cursor() as cur:
            cur.execute(query, params)
            return cur

    def fetchall(self, query: str, params: tuple | None = None) -> list[dict]:
        """查询所有行"""
        with self.cursor() as cur:
            cur.execute(query, params)
            return [dict(row) for row in cur.fetchall()]

    def fetchone(self, query: str, params: tuple | None = None) -> dict | None:
        """查询一行"""
        with self.cursor() as cur:
            cur.execute(query, params)
            row = cur.fetchone()
            return dict(row) if row else None

    def close(self):
        """关闭连接"""
        if self._conn:
            self._conn.close()
            self._conn = None
            logger.info("psycopg2连接已关闭")


# 模块导出
__all__ = [
    "DatabaseConnection",
    "PostgreSQLConnection",
    "Psycopg2Connection",
    "SQLiteConnection",
    "get_postgres_pool",
    "get_sqlite_conn",
    "postgres_context",
    "sqlite_context",
]
