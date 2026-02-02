#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库连接池管理器
Database Connection Pool Manager

提供高效的PostgreSQL连接池管理,支持连接复用、健康检查和自动恢复
"""

import logging
import time
import threading
from contextlib import contextmanager
from typing import Optional, Dict, Any, Generator
from queue import Queue, Empty, Full

import psycopg2
from psycopg2 import pool
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor

from core.config.search_config import get_search_config

logger = logging.getLogger(__name__)


# =============================================================================
# 连接池配置
# =============================================================================

class ConnectionPoolConfig:
    """连接池配置"""

    def __init__(
        self,
        min_connections: int = 2,
        max_connections: int = 20,
        connection_timeout: float = 10.0,
        idle_timeout: float = 300.0,
        max_lifetime: float = 3600.0,
        health_check_interval: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        初始化连接池配置

        Args:
            min_connections: 最小连接数
            max_connections: 最大连接数
            connection_timeout: 获取连接超时(秒)
            idle_timeout: 空闲连接超时(秒)
            max_lifetime: 连接最大生命周期(秒)
            health_check_interval: 健康检查间隔(秒)
            max_retries: 最大重试次数
            retry_delay: 重试延迟(秒)
        """
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.idle_timeout = idle_timeout
        self.max_lifetime = max_lifetime
        self.health_check_interval = health_check_interval
        self.max_retries = max_retries
        self.retry_delay = retry_delay


# =============================================================================
# 连接包装器
# =============================================================================

class PooledConnection:
    """
    连接包装器

    包装原始连接,提供额外功能:
    - 连接健康检查
    - 使用时间跟踪
    - 自动归还
    """

    def __init__(
        self,
        conn: connection,
        pool: 'ConnectionPoolManager',
        created_at: float
    ):
        """
        初始化连接包装器

        Args:
            conn: 原始连接
            pool: 所属连接池
            created_at: 创建时间
        """
        self._conn = conn
        self._pool = pool
        self._created_at = created_at
        self._last_used_at = created_at
        self._in_use = False

    @property
    def conn(self) -> connection:
        """获取原始连接"""
        return self._conn

    @property
    def age(self) -> float:
        """连接年龄(秒)"""
        return time.time() - self._created_at

    @property
    def idle_time(self) -> float:
        """空闲时间(秒)"""
        return time.time() - self._last_used_at

    @property
    def is_healthy(self) -> bool:
        """检查连接是否健康"""
        try:
            # 执行简单查询检查连接
            with self._conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return True
        except Exception:
            return False

    def mark_used(self):
        """标记连接为已使用"""
        self._last_used_at = time.time()
        self._in_use = True

    def mark_returned(self):
        """标记连接为已归还"""
        self._in_use = False

    def close(self):
        """关闭连接"""
        try:
            if self._conn and not self._conn.closed:
                self._conn.close()
                logger.debug("连接已关闭")
        except Exception as e:
            logger.error(f"关闭连接时出错: {e}")

    def __enter__(self):
        """上下文管理器入口"""
        self.mark_used()
        return self._conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self._pool.return_connection(self)


# =============================================================================
# 连接池管理器
# =============================================================================

class ConnectionPoolManager:
    """
    连接池管理器

    提供高效的PostgreSQL连接池管理功能

    Examples:
        >>> pool_manager = ConnectionPoolManager.get_instance()
        >>>
        >>> with pool_manager.get_connection() as conn:
        >>>     with conn.cursor() as cursor:
        >>>         cursor.execute("SELECT * FROM users")
        >>>         results = cursor.fetchall()
    """

    _instance: 'ConnectionPoolManager' | None = None
    _lock = threading.Lock()

    def __init__(self, config: ConnectionPoolConfig | None = None):
        """
        初始化连接池管理器(单例模式,请使用get_instance())

        Args:
            config: 连接池配置
        """
        self.config = config or ConnectionPoolConfig()
        self._pool: pool.ThreadedConnectionPool | None = None
        self._initialized = False
        self._last_health_check = 0.0

        logger.info("连接池管理器初始化")

    @classmethod
    def get_instance(cls, config: ConnectionPoolConfig | None = None) -> 'ConnectionPoolManager':
        """
        获取连接池管理器单例

        Args:
            config: 连接池配置(仅首次初始化时使用)

        Returns:
            连接池管理器实例
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(config)
        return cls._instance

    def initialize(self):
        """初始化连接池"""
        if self._initialized:
            return

        try:
            # 获取数据库配置
            search_config = get_search_config()
            db_config = search_config.database.to_dict()

            # 创建连接池
            self._pool = pool.ThreadedConnectionPool(
                minconn=self.config.min_connections,
                maxconn=self.config.max_connections,
                **db_config
            )

            self._initialized = True
            logger.info(
                f"✅ 连接池初始化成功: "
                f"min={self.config.min_connections}, "
                f"max={self.config.max_connections}"
            )

        except Exception as e:
            logger.error(f"❌ 连接池初始化失败: {e}")
            raise

    @contextmanager
    def get_connection(
        self,
        retry: bool = True
    ) -> Generator[PooledConnection, None, None]:
        """
        获取数据库连接(上下文管理器)

        Args:
            retry: 是否在连接失败时重试

        Yields:
            连接包装器

        Raises:
            Exception: 连接失败且重试耗尽
        """
        if not self._initialized:
            self.initialize()

        conn = None
        attempts = 0
        max_attempts = self.config.max_retries if retry else 1

        while attempts < max_attempts:
            try:
                # 从连接池获取连接
                raw_conn = self._pool.get(
                    timeout=self.config.connection_timeout
                )

                # 创建包装器
                conn = PooledConnection(
                    raw_conn,
                    self,
                    time.time()
                )

                # 健康检查
                if not conn.is_healthy:
                    logger.warning("获取的连接不健康,关闭并重试")
                    conn.close()
                    attempts += 1
                    time.sleep(self.config.retry_delay)
                    continue

                yield conn
                return

            except Empty:
                attempts += 1
                if attempts < max_attempts:
                    logger.warning(
                        f"连接池耗尽,重试 {attempts}/{max_attempts}"
                    )
                    time.sleep(self.config.retry_delay)
                else:
                    raise Exception(
                        f"无法从连接池获取连接 "
                        f"(超时: {self.config.connection_timeout}s)"
                    )

            except Exception as e:
                if conn:
                    conn.close()
                attempts += 1
                if attempts < max_attempts:
                    logger.warning(
                        f"获取连接失败: {e}, 重试 {attempts}/{max_attempts}"
                    )
                    time.sleep(self.config.retry_delay)
                else:
                    logger.error(f"获取连接失败: {e}")
                    raise

        finally:
            if conn:
                self.return_connection(conn)

    def return_connection(self, conn: PooledConnection):
        """
        归还连接到连接池

        Args:
            conn: 连接包装器
        """
        try:
            if conn and conn._conn and not conn._conn.closed:
                self._pool.putconn(conn._conn)
                conn.mark_returned()
        except Exception as e:
            logger.error(f"归还连接失败: {e}")
            try:
                conn.close()
            except Exception:
                pass

    def health_check(self) -> dict[str, Any]:
        """
        执行健康检查

        Returns:
            健康状态字典
        """
        now = time.time()

        # 避免频繁检查
        if now - self._last_health_check < self.config.health_check_interval:
            return {'status': 'healthy', 'skipped': True}

        self._last_health_check = now

        if not self._initialized or not self._pool:
            return {'status': 'unhealthy', 'reason': 'not initialized'}

        try:
            # 测试获取连接
            with self.get_connection(retry=False) as conn:
                with conn._conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()

            return {
                'status': 'healthy',
                'pool_size': self._pool._maxconn,
                'available': self._pool._pool.qsize() if hasattr(self._pool._pool, 'qsize') else 'unknown'
            }

        except Exception as e:
            return {'status': 'unhealthy', 'reason': str(e)}

    def get_stats(self) -> dict[str, Any]:
        """
        获取连接池统计信息

        Returns:
            统计信息字典
        """
        if not self._initialized or not self._pool:
            return {
                'initialized': False,
                'min_connections': self.config.min_connections,
                'max_connections': self.config.max_connections
            }

        return {
            'initialized': True,
            'min_connections': self.config.min_connections,
            'max_connections': self.config.max_connections,
            'closed': self._pool._closed,
            'health_check': self.health_check()
        }

    def close(self):
        """关闭连接池"""
        if self._pool and not self._pool._closed:
            try:
                self._pool.closeall()
                logger.info("连接池已关闭")
            except Exception as e:
                logger.error(f"关闭连接池时出错: {e}")
        self._initialized = False


# =============================================================================
# 便捷函数
# =============================================================================

def get_connection_pool() -> ConnectionPoolManager:
    """获取全局连接池管理器实例"""
    return ConnectionPoolManager.get_instance()


@contextmanager
def get_db_connection():
    """
    获取数据库连接的便捷函数

    Examples:
        >>> with get_db_connection() as conn:
        >>>     with conn.cursor() as cursor:
        >>>         cursor.execute("SELECT * FROM users")
        >>>         results = cursor.fetchall()
    """
    pool_manager = get_connection_pool()
    with pool_manager.get_connection() as pooled_conn:
        yield pooled_conn._conn


# =============================================================================
# 导出
# =============================================================================

__all__ = [
    'ConnectionPoolConfig',
    'PooledConnection',
    'ConnectionPoolManager',
    'get_connection_pool',
    'get_db_connection',
]
