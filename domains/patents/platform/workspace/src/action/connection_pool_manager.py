#!/usr/bin/env python3
"""
连接池管理器
Connection Pool Manager

功能特性：
- LLM客户端连接池
- 数据库连接池
- HTTP连接池
- 连接池监控和统计

Created by Athena AI系统
Date: 2025-12-14
Version: 1.0.0
"""

import asyncio
import logging
import time
from collections import deque
from collections.abc import Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class PoolConfig:
    """连接池配置"""
    min_size: int = 2           # 最小连接数
    max_size: int = 10          # 最大连接数
    max_idle_time: int = 300    # 最大空闲时间（秒）
    acquire_timeout: int = 30   # 获取连接超时（秒）
    idle_timeout: int = 600     # 空闲超时（秒）
    block: bool = False         # 连接池满时是否阻塞


@dataclass
class PoolStats:
    """连接池统计"""
    total_created: int = 0
    total_acquired: int = 0
    total_released: int = 0
    total_errors: int = 0
    current_size: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    waiting_requests: int = 0


class ConnectionPool:
    """通用连接池基类"""

    def __init__(self,
                 name: str,
                 config: PoolConfig,
                 factory: Callable):
        """
        初始化连接池

        Args:
            name: 连接池名称
            config: 连接池配置
            factory: 连接工厂函数
        """
        self.name = name
        self.config = config
        self.factory = factory
        self.logger = logging.getLogger(f"{__name__}.{name}")

        # 连接池
        self._pool: deque = deque()
        self._active_connections: set = set()

        # 统计信息
        self.stats = PoolStats()

        # 同步原语
        self._lock = asyncio.Lock()
        self._condition = asyncio.Condition(self._lock)

        # 关闭标志
        self._closed = False

        self.logger.info(f"✅ {name} 连接池初始化完成 (min={config.min_size}, max={config.max_size})")

    async def initialize(self):
        """初始化连接池（创建最小连接数）"""
        async with self._lock:
            if self._closed:
                raise RuntimeError(f"{self.name} 连接池已关闭")

            # 创建最小连接数
            for _ in range(self.config.min_size):
                conn = await self._create_connection()
                self._pool.append(conn)
                self.stats.total_created += 1

            self.stats.current_size = len(self._pool)
            self.stats.idle_connections = len(self._pool)

            self.logger.info(f"✅ {self.name} 连接池初始化完成，创建了 {len(self._pool)} 个连接")

    async def acquire(self) -> Any:
        """
        获取连接

        Returns:
            连接对象
        """
        async with self._condition:
            if self._closed:
                raise RuntimeError(f"{self.name} 连接池已关闭")

            # 等待直到有可用连接
            while True:
                # 尝试从池中获取连接
                if self._pool:
                    conn = self._pool.popleft()
                    self._active_connections.add(conn)
                    self.stats.total_acquired += 1
                    self.stats.active_connections = len(self._active_connections)
                    self.stats.idle_connections = len(self._pool)
                    return conn

                # 池中无连接，检查是否可以创建新连接
                if self.stats.current_size < self.config.max_size:
                    # 可以创建新连接
                    try:
                        conn = await self._create_connection()
                        self._active_connections.add(conn)
                        self.stats.total_created += 1
                        self.stats.total_acquired += 1
                        self.stats.current_size += 1
                        self.stats.active_connections = len(self._active_connections)
                        return conn
                    except Exception as e:
                        self.stats.total_errors += 1
                        self.logger.error(f"❌ 创建连接失败: {e}")
                        raise

                # 已达最大连接数，等待或抛出异常
                if self.config.block:
                    # 等待其他连接释放
                    self.stats.waiting_requests += 1
                    try:
                        await asyncio.wait_for(
                            self._condition.wait(),
                            timeout=self.config.acquire_timeout
                        )
                        self.stats.waiting_requests -= 1
                    except TimeoutError:
                        self.stats.waiting_requests -= 1
                        raise TimeoutError(f"{self.name} 获取连接超时")
                else:
                    raise RuntimeError(f"{self.name} 连接池已耗尽")

    async def release(self, conn: Any):
        """
        释放连接

        Args:
            conn: 连接对象
        """
        async with self._condition:
            if conn in self._active_connections:
                self._active_connections.remove(conn)
                self.stats.total_released += 1

                # 检查连接是否有效
                if await self._validate_connection(conn):
                    self._pool.append(conn)
                else:
                    # 连接无效，移除并创建新连接
                    await self._close_connection(conn)
                    self.stats.current_size -= 1
                    if self.stats.current_size >= self.config.min_size:
                        try:
                            new_conn = await self._create_connection()
                            self._pool.append(new_conn)
                            self.stats.total_created += 1
                        except Exception as e:
                            self.logger.warning(f"⚠️ 创建替换连接失败: {e}")

                self.stats.active_connections = len(self._active_connections)
                self.stats.idle_connections = len(self._pool)

                # 通知等待的请求
                self._condition.notify(1)

    @asynccontextmanager
    async def connection(self):
        """连接上下文管理器"""
        conn = await self.acquire()
        try:
            yield conn
        finally:
            await self.release(conn)

    async def _create_connection(self) -> Any:
        """创建新连接（子类实现）"""
        return await self.factory()

    async def _validate_connection(self, conn: Any) -> bool:
        """验证连接是否有效（子类实现）"""
        return True

    async def _close_connection(self, conn: Any):
        """关闭连接（子类实现）"""
        pass

    async def close(self):
        """关闭连接池"""
        async with self._lock:
            if self._closed:
                return

            self._closed = True

            # 关闭所有连接
            all_conns = list(self._pool) + list(self._active_connections)
            for conn in all_conns:
                await self._close_connection(conn)

            self._pool.clear()
            self._active_connections.clear()
            self.stats.current_size = 0
            self.stats.active_connections = 0
            self.stats.idle_connections = 0

            self.logger.info(f"🔌 {self.name} 连接池已关闭")

    def get_stats(self) -> dict[str, Any]:
        """获取连接池统计"""
        return {
            'name': self.name,
            'total_created': self.stats.total_created,
            'total_acquired': self.stats.total_acquired,
            'total_released': self.stats.total_released,
            'total_errors': self.stats.total_errors,
            'current_size': self.stats.current_size,
            'active_connections': self.stats.active_connections,
            'idle_connections': self.stats.idle_connections,
            'waiting_requests': self.stats.waiting_requests,
            'utilization': self.stats.active_connections / self.config.max_size if self.config.max_size > 0 else 0
        }


# =============================================================================
# LLM客户端连接池
# =============================================================================

class LLMConnectionPool(ConnectionPool):
    """LLM客户端连接池"""

    def __init__(self, config: PoolConfig | None = None):
        if config is None:
            config = PoolConfig(min_size=2, max_size=10)

        # 动态导入LLM服务以避免循环依赖
        try:
            from patent_executors_platform_llm import PlatformLLMService
            factory = self._create_llm_service
        except ImportError:
            # Fallback factory
            def factory():
                return asyncio.sleep(0)

        super().__init__("LLMConnectionPool", config, factory)
        self._llm_services: list = []

    async def _create_connection(self) -> Any:
        """创建LLM服务实例"""
        from patent_executors_platform_llm import PlatformLLMService
        service = PlatformLLMService()
        self._llm_services.append(service)
        return service

    async def _validate_connection(self, conn: Any) -> bool:
        """验证LLM服务是否可用"""
        # LLM服务通常是无状态的，总是有效
        return True

    async def _close_connection(self, conn: Any):
        """关闭LLM服务"""
        if conn in self._llm_services:
            self._llm_services.remove(conn)
        # LLM服务通常不需要显式关闭

    async def analyze_with_pool(self,
                               patent_data: dict[str, Any],
                               analysis_type: str) -> dict[str, Any]:
        """
        使用连接池进行分析

        Args:
            patent_data: 专利数据
            analysis_type: 分析类型

        Returns:
            分析结果
        """
        async with self.connection() as llm_service:
            return await llm_service.analyze_patent(
                patent_data=patent_data,
                analysis_type=analysis_type
            )


# =============================================================================
# 数据库连接池
# =============================================================================

class DatabaseConnectionPool(ConnectionPool):
    """数据库连接池"""

    def __init__(self,
                 database_url: str,
                 config: PoolConfig | None = None):
        """
        初始化数据库连接池

        Args:
            database_url: 数据库连接URL
            config: 连接池配置
        """
        if config is None:
            config = PoolConfig(min_size=1, max_size=5)

        self.database_url = database_url
        super().__init__("DatabaseConnectionPool", config, self._create_db_connection)

    async def _create_connection(self) -> Any:
        """创建数据库连接"""
        try:
            # 尝试使用asyncpg（PostgreSQL）
            import asyncpg
            return await asyncpg.connect(self.database_url)
        except ImportError:
            try:
                # 尝试使用aiosqlite
                import aiosqlite
                return await aiosqlite.connect(self.database_url)
            except ImportError:
                # Fallback到模拟连接
                self.logger.warning("⚠️ 未安装数据库驱动，使用模拟连接")
                return MockDatabaseConnection()

    async def _validate_connection(self, conn: Any) -> bool:
        """验证数据库连接是否有效"""
        try:
            # 尝试执行简单查询
            if hasattr(conn, 'fetchval'):
                await conn.fetchval('SELECT 1')
            elif hasattr(conn, 'execute'):
                await conn.execute('SELECT 1')
            return True
        except Exception:
            return False

    async def _close_connection(self, conn: Any):
        """关闭数据库连接"""
        if hasattr(conn, 'close'):
            await conn.close()

    async def execute_query(self, query: str, *args) -> Any:
        """
        执行查询

        Args:
            query: SQL查询
            *args: 查询参数

        Returns:
            查询结果
        """
        async with self.connection() as conn:
            if hasattr(conn, 'fetch'):
                return await conn.fetch(query, *args)
            elif hasattr(conn, 'execute'):
                cursor = await conn.execute(query, *args)
                if hasattr(cursor, 'fetchall'):
                    return await cursor.fetchall()
                return cursor
            else:
                raise NotImplementedError("不支持的连接类型")


class MockDatabaseConnection:
    """模拟数据库连接（用于测试）"""

    async def fetch(self, query, *args):
        return []

    async def fetchval(self, query, *args):
        return 1

    async def execute(self, query, *args):
        return None

    async def close(self):
        pass


# =============================================================================
# HTTP连接池
# =============================================================================

class HTTPConnectionPool:
    """HTTP连接池"""

    def __init__(self, max_size: int = 100):
        """
        初始化HTTP连接池

        Args:
            max_size: 最大连接数
        """
        self.max_size = max_size
        self.logger = logging.getLogger(f"{__name__}.HTTPConnectionPool")
        self._session = None

    async def get_session(self):
        """获取HTTP会话"""
        if self._session is None or self._session.closed:
            import aiohttp
            timeout = aiohttp.ClientTimeout(total=30)
            connector = aiohttp.TCPConnector(
                limit=self.max_size,
                limit_per_host=20,
                enable_cleanup_closed=True
            )
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector
            )
            self.logger.info(f"✅ HTTP会话已创建 (max_connections={self.max_size})")

        return self._session

    async def close(self):
        """关闭HTTP连接池"""
        if self._session and not self._session.closed:
            await self._session.close()
            self.logger.info("🔌 HTTP连接池已关闭")

    async def get(self, url: str, **kwargs) -> Any:
        """发送GET请求"""
        session = await self.get_session()
        async with session.get(url, **kwargs) as response:
            return await response.json()

    async def post(self, url: str, **kwargs) -> Any:
        """发送POST请求"""
        session = await self.get_session()
        async with session.post(url, **kwargs) as response:
            return await response.json()


# =============================================================================
# 全局连接池管理器
# =============================================================================

_global_pools: dict[str, Any] = {}


def get_llm_pool() -> LLMConnectionPool:
    """获取LLM连接池（单例）"""
    if 'llm' not in _global_pools:
        _global_pools['llm'] = LLMConnectionPool()
    return _global_pools['llm']


def get_database_pool(database_url: str) -> DatabaseConnectionPool:
    """获取数据库连接池（单例）"""
    if 'database' not in _global_pools:
        _global_pools['database'] = DatabaseConnectionPool(database_url)
    return _global_pools['database']


def get_http_pool() -> HTTPConnectionPool:
    """获取HTTP连接池（单例）"""
    if 'http' not in _global_pools:
        _global_pools['http'] = HTTPConnectionPool()
    return _global_pools['http']


async def close_all_pools():
    """关闭所有连接池"""
    for name, pool in _global_pools.items():
        try:
            await pool.close()
        except Exception as e:
            logger.error(f"❌ 关闭 {name} 连接池失败: {e}")
    _global_pools.clear()


# =============================================================================
# 测试代码
# =============================================================================

async def test_connection_pools():
    """测试连接池"""
    logger.info("="*60)
    logger.info("🧪 测试连接池")
    logger.info("="*60)

    # 测试1: LLM连接池
    logger.info("\n📝 测试1: LLM连接池")
    llm_pool = get_llm_pool()
    await llm_pool.initialize()
    logger.info(f"✅ LLM连接池统计: {llm_pool.get_stats()}")

    # 测试2: 数据库连接池
    logger.info("\n📝 测试2: 数据库连接池")
    db_pool = get_database_pool('sqlite:///:memory:')
    await db_pool.initialize()
    logger.info(f"✅ 数据库连接池统计: {db_pool.get_stats()}")

    # 测试3: HTTP连接池
    logger.info("\n📝 测试3: HTTP连接池")
    http_pool = get_http_pool()
    await http_pool.get_session()
    logger.info("✅ HTTP会话已创建")

    # 测试4: 并发获取连接
    logger.info("\n📝 测试4: 并发获取连接")
    async def acquire_and_release(pool, delay):
        async with pool.connection():
            await asyncio.sleep(delay)
            return True

    start = time.time()
    tasks = [acquire_and_release(llm_pool, 0.1) for _ in range(5)]
    results = await asyncio.gather(*tasks)
    elapsed = time.time() - start

    logger.info(f"✅ 并发测试完成: {len(results)} 个任务, 耗时: {elapsed:.2f}秒")
    logger.info(f"   LLM连接池统计: {llm_pool.get_stats()}")

    # 清理
    await close_all_pools()

    logger.info("\n" + "="*60)
    logger.info("🎉 测试完成！")
    logger.info("="*60)


if __name__ == '__main__':
    asyncio.run(test_connection_pools())
