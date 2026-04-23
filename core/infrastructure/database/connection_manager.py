
"""
数据库连接管理器
统一管理所有数据库连接池和连接配置
"""

import logging
from contextlib import asynccontextmanager
from typing import Any, Optional

# 异步依赖 - 设为可选以支持同步脚本
# 使用官方redis库的asyncio模块（替代已弃用的aioredis）
try:
    from redis import asyncio as aioredis

    AIOREDIS_AVAILABLE = True
except ImportError:
    AIOREDIS_AVAILABLE = False
    logging.warning("redis.asyncio 不可用,异步Redis功能将受限")

try:
    from core.infrastructure.database.unified_connection import get_postgres_pool

    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False
    logging.warning("asyncpg 不可用,异步PostgreSQL功能将受限")

try:
    import motor.motor_asyncio

    MOTOR_AVAILABLE = True
except ImportError:
    MOTOR_AVAILABLE = False
    logging.warning("motor 不可用,异步MongoDB功能将受限")

try:
    from elasticsearch import AsyncElasticsearch

    ELASTICSEARCH_AVAILABLE = True
except ImportError:
    ELASTICSEARCH_AVAILABLE = False
    logging.warning("AsyncElasticsearch 不可用")

try:
    from neo4j import AsyncGraphDatabase

    ASYNC_NEO4J_AVAILABLE = True
except ImportError:
    ASYNC_NEO4J_AVAILABLE = False
    logging.warning("AsyncGraphDatabase 不可用")

logger = logging.getLogger(__name__)


class DatabaseConnectionManager:
    """数据库连接管理器"""

    def __init__(self):
        self.connections: dict[str, Any] = {}
        self.configs: dict[str, dict] = {}
        self._initialized = False

    async def initialize(self, configs: dict[str, dict]):
        """初始化所有数据库连接"""
        self.configs = configs

        # 初始化PostgreSQL连接
        if "postgres" in configs:
            await self._init_postgres(configs["postgres"])

        # 初始化Redis连接
        if "redis" in configs:
            await self._init_redis(configs["redis"])

        # 初始化MongoDB连接(如果需要)
        if "mongodb" in configs:
            await self._init_mongodb(configs["mongodb"])

        # 初始化Neo4j连接
        if "neo4j" in configs:
            await self._init_neo4j(configs["neo4j"])

        # 初始化Elasticsearch连接
        if "elasticsearch" in configs:
            await self._init_elasticsearch(configs["elasticsearch"])

        self._initialized = True
        logger.info("所有数据库连接初始化完成")

    async def _init_postgres(self, config: dict):
        """初始化PostgreSQL连接池"""
        if not ASYNCPG_AVAILABLE:
            raise RuntimeError("asyncpg 不可用,无法初始化异步PostgreSQL连接")

        try:
            dsn = (
                f"postgresql://{config['user']}:{config['password']}"
                f"@{config['host']}:{config['port']}/{config['database']}"
            )

            pool = await get_postgres_pool(
                dsn,
                min_size=config.get("min_size", 5),
                max_size=config.get("max_size", 20),
                command_timeout=config.get("command_timeout", 60),
                server_settings={"application_name": "athena_platform", "jit": "off"},
            )

            self.connections["postgres"] = pool
            logger.info(f"PostgreSQL连接池创建成功: {config['host']}:{config['port']}")

        except Exception as e:
            logger.error(f"PostgreSQL连接失败: {e}")
            raise

    async def _init_redis(self, config: dict):
        """初始化Redis连接池（使用redis.asyncio）"""
        if not AIOREDIS_AVAILABLE:
            raise RuntimeError("redis.asyncio 不可用,无法初始化异步Redis连接")

        try:
            # 使用redis.asyncio的ConnectionPool
            pool = aioredis.ConnectionPool.from_url(
                f"redis://{config.get('host', 'localhost')}:{config.get('port', 6379)}/{config.get('db', 0)}",
                password=config.get("password"),
                max_connections=config.get("max_connections", 50),
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={},
                decode_responses=True,  # 自动解码响应为字符串
            )

            client = aioredis.Redis(connection_pool=pool)
            self.connections["redis"] = client

            # 测试连接
            await client.ping()
            logger.info(f"Redis连接创建成功: {config['host']}:{config['port']}")

        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            raise

    async def _init_mongodb(self, config: dict):
        """初始化MongoDB连接"""
        if not MOTOR_AVAILABLE:
            raise RuntimeError("motor 不可用,无法初始化异步MongoDB连接")

        try:
            connection_string = (
                f"mongodb://{config['user']}:{config['password']}"
                f"@{config['host']}:{config['port']}/{config['database']}"
            )

            client = motor.motor_asyncio.AsyncIOMotorClient(
                connection_string,
                max_pool_size=config.get("max_pool_size", 20),
                min_pool_size=config.get("min_pool_size", 5),
            )

            # 测试连接
            await client.admin.command("ping")

            self.connections["mongodb"] = client[config["database"]
            logger.info(f"MongoDB连接创建成功: {config['host']}:{config['port']}")

        except Exception as e:
            logger.error(f"MongoDB连接失败: {e}")
            raise

    async def _init_neo4j(self, config: dict):
        """初始化Neo4j连接"""
        if not ASYNC_NEO4J_AVAILABLE:
            raise RuntimeError("AsyncGraphDatabase 不可用,无法初始化异步Neo4j连接")

        try:
            driver = AsyncGraphDatabase.driver(
                config["uri"],
                auth=(config["user"], config["password"]),
                max_connection_lifetime=config.get("max_connection_lifetime", 3600),
                max_connection_pool_size=config.get("max_connection_pool_size", 50),
                connection_acquisition_timeout=config.get("connection_acquisition_timeout", 60),
            )

            # 测试连接
            await driver.verify_connectivity()

            self.connections["neo4j"] = driver
            logger.info(f"Neo4j连接创建成功: {config['uri']}")

        except Exception as e:
            logger.error(f"Neo4j连接失败: {e}")
            raise

    async def _init_elasticsearch(self, config: dict):
        """初始化Elasticsearch连接"""
        if not ELASTICSEARCH_AVAILABLE:
            raise RuntimeError("AsyncElasticsearch 不可用,无法初始化异步Elasticsearch连接")

        try:
            hosts = [{"host": config["host"], "port": config["port"], "scheme": "http"}]

            if "username" in config and "password" in config:
                hosts[0]["http_auth"] = (config["username"], config["password"])

            client = AsyncElasticsearch(
                hosts=hosts,
                timeout=config.get("timeout", 30),
                max_retries=config.get("max_retries", 3),
                retry_on_timeout=True,
            )

            # 测试连接
            await client.ping()

            self.connections["elasticsearch"] = client
            logger.info(f"Elasticsearch连接创建成功: {config['host']}:{config['port']}")

        except Exception as e:
            logger.error(f"Elasticsearch连接失败: {e}")
            raise

    @asynccontextmanager
    async def get_postgres(self):
        """获取PostgreSQL连接"""
        if "postgres" not in self.connections:
            raise RuntimeError("PostgreSQL连接未初始化")

        async with self.connections["postgres"].acquire() as conn:
            yield conn

    @asynccontextmanager
    async def get_postgres_transaction(self):
        """获取PostgreSQL事务连接"""
        if "postgres" not in self.connections:
            raise RuntimeError("PostgreSQL连接未初始化")

        async with self.connections["postgres"].acquire() as conn, conn.transaction():
            yield conn

    async def get_redis(self) -> aioredis.Redis:  # type: ignore[valid-type]
        """获取Redis连接"""
        if "redis" not in self.connections:
            raise RuntimeError("Redis连接未初始化")

        return self.connections["redis"]

    async def get_mongodb(self):
        """获取MongoDB连接"""
        if "mongodb" not in self.connections:
            raise RuntimeError("MongoDB连接未初始化")

        return self.connections["mongodb"]

    @asynccontextmanager
    async def get_neo4j_session(self):
        """获取Neo4j会话"""
        if "neo4j" not in self.connections:
            raise RuntimeError("Neo4j连接未初始化")

        async with self.connections["neo4j"].session() as session:
            yield session

    async def get_elasticsearch(self) -> Any:  # AsyncElasticsearch if available
        """获取Elasticsearch连接"""
        if "elasticsearch" not in self.connections:
            raise RuntimeError("Elasticsearch连接未初始化")

        return self.connections["elasticsearch"]

    @asynccontextmanager
    async def session(self):
        """
        获取Neo4j会话（同步兼容方法）

        为了兼容scenario_rule_retriever_optimized.py中的同步调用
        """
        async with self.get_neo4j_session() as session:
            yield session

    async def health_check(self) -> dict[str, Any]:
        """检查所有数据库连接的健康状态"""
        health_status = {}

        # PostgreSQL健康检查
        if "postgres" in self.connections:
            try:
                async with self.get_postgres() as conn:
                    await conn.fetchval("SELECT 1")
                health_status["postgres"]] = {"status": "healthy", "error": None}
            except Exception as e:
                health_status["postgres"]] = {"status": "unhealthy", "error": str(e)}

        # Redis健康检查
        if "redis" in self.connections:
            try:
                redis = await self.get_redis()
                await redis.ping()
                health_status["redis"]] = {"status": "healthy", "error": None}
            except Exception as e:
                health_status["redis"]] = {"status": "unhealthy", "error": str(e)}

        # MongoDB健康检查
        if "mongodb" in self.connections:
            try:
                mongodb = await self.get_mongodb()
                await mongodb.command("ping")
                health_status["mongodb"]] = {"status": "healthy", "error": None}
            except Exception as e:
                health_status["mongodb"]] = {"status": "unhealthy", "error": str(e)}

        # Neo4j健康检查
        if "neo4j" in self.connections:
            try:
                async with self.get_neo4j_session() as session:
                    await session.run("RETURN 1")
                health_status["neo4j"]] = {"status": "healthy", "error": None}
            except Exception as e:
                health_status["neo4j"]] = {"status": "unhealthy", "error": str(e)}

        # Elasticsearch健康检查
        if "elasticsearch" in self.connections:
            try:
                es = await self.get_elasticsearch()
                await es.ping()
                health_status["elasticsearch"]] = {"status": "healthy", "error": None}
            except Exception as e:
                health_status["elasticsearch"]] = {"status": "unhealthy", "error": str(e)}

        return health_status

    async def get_pool_stats(self) -> dict[str, Any]:
        """获取连接池统计信息"""
        stats = {}

        if "postgres" in self.connections:
            pool = self.connections["postgres"]
            stats["postgres"]] = {
                "size": pool.get_size(),
                "idle": pool.get_idle_size(),
                "max_size": pool.get_max_size(),
                "min_size": pool.get_min_size(),
            }

        if "redis" in self.connections:
            pool = self.connections["redis"].connection_pool
            stats["redis"]] = {
                "max_connections": pool.max_connections,
                "created_connections": pool.created_connections,
                "available_connections": len(pool._available_connections),
            }

        return stats

    async def close_all(self):
        """关闭所有数据库连接"""
        if "postgres" in self.connections:
            await self.connections["postgres"].close()
            logger.info("PostgreSQL连接池已关闭")

        if "redis" in self.connections:
            await self.connections["redis"].close()
            logger.info("Redis连接已关闭")

        if "mongodb" in self.connections:
            self.connections["mongodb"].client.close()
            logger.info("MongoDB连接已关闭")

        if "neo4j" in self.connections:
            await self.connections["neo4j"].close()
            logger.info("Neo4j连接已关闭")

        if "elasticsearch" in self.connections:
            await self.connections["elasticsearch"].close()
            logger.info("Elasticsearch连接已关闭")

        self.connections.clear()
        self._initialized = False
        logger.info("所有数据库连接已关闭")

    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        return self._initialized


# 全局数据库连接管理器实例
db_manager = DatabaseConnectionManager()


# 便捷函数
async def get_db_manager(configs: Optional[dict[str, Any]] = None) -> DatabaseConnectionManager:
    """获取数据库管理器实例"""
    global db_manager

    if not db_manager.is_initialized():
        if not configs:
            raise RuntimeError("数据库配置未提供")
        await db_manager.initialize(configs)

    return db_manager


# 数据库上下文管理器
@asynccontextmanager
async def postgres_connection():
    """PostgreSQL连接上下文管理器"""
    async with db_manager.get_postgres() as conn:
        yield conn


@asynccontextmanager
async def postgres_transaction():
    """PostgreSQL事务上下文管理器"""
    async with db_manager.get_postgres_transaction() as conn:
        yield conn


async def redis_connection() -> aioredis.Redis:  # type: ignore[valid-type]
    """Redis连接函数"""
    return await db_manager.get_redis()


@asynccontextmanager
async def neo4j_session():
    """Neo4j会话上下文管理器"""
    async with db_manager.get_neo4j_session() as session:
        yield session


async def elasticsearch_connection() -> Any:  # AsyncElasticsearch if available
    """Elasticsearch连接函数"""
    return await db_manager.get_elasticsearch()


# =============================================================================
# 同步版本的连接管理器 (用于migration脚本)
# =============================================================================

import logging

# 修复: core.neo4j 模块遮蔽了官方 neo4j 包
# GraphDatabase 类在 neo4j 包的根级别,不是在 graph_database 子模块中
import sys
from collections.abc import Generator
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import execute_batch
from qdrant_client import QdrantClient

# 移除可能被遮蔽的 neo4j 模块引用
if "neo4j" in sys.modules:
    neo4j_mod = sys.modules.get("neo4j")
    if neo4j_mod and "site-packages" not in getattr(neo4j_mod, "__file__", ""):
        # 如果当前 neo4j 模块不是来自 site-packages,删除它
        del sys.modules["neo4j"]

# 现在导入 neo4j,应该会从 site-packages 找到官方包
import neo4j

SyncGraphDatabase = neo4j.GraphDatabase
Neo4jSession = neo4j.Session

from .config import DatabaseConfig
from .constants import DEFAULT_BATCH_SIZE

logger = logging.getLogger(__name__)


class SyncDatabaseConnectionManager:
    """
    同步版本的数据库连接管理器

    专为migration脚本设计,使用同步的psycopg2、neo4j库
    使用上下文管理器确保资源正确释放,避免连接泄漏
    """

    def __init__(self):
        """初始化连接管理器"""
        self.pg_config = DatabaseConfig.get_postgresql_config()
        self.neo4j_config = DatabaseConfig.get_neo4j_config()
        self.qdrant_config = DatabaseConfig.get_qdrant_config()

        # 验证配置
        try:
            DatabaseConfig.validate_config()
        except ValueError as e:
            logger.warning(f"⚠️ 配置验证失败: {e}")
            logger.warning("将使用默认配置,请在.env文件中设置正确的密码")

        logger.info("✅ 同步数据库连接管理器初始化成功")

    @contextmanager
    def postgresql_connection(
        self, autocommit: bool = True
    ) -> Generator[psycopg2.extensions.connection, None, None]:
        """
        PostgreSQL连接上下文管理器

        Args:
            autocommit: 是否自动提交,默认True

        Yields:
            PostgreSQL连接对象

        Example:
            >>> db = SyncDatabaseConnectionManager()
            >>> with db.postgresql_connection() as conn:
            ...     cursor = conn.cursor()
            ...     cursor.execute("SELECT 1")
        """
        conn = None
        try:
            conn = psycopg2.connect(**self.pg_config)
            conn.autocommit = autocommit
            yield conn
        except Exception as e:
            logger.error(f"❌ PostgreSQL连接失败: {e}")
            raise
        finally:
            if conn:
                conn.close()
                logger.debug("🔒 PostgreSQL连接已关闭")

    @contextmanager
    def postgresql_cursor(
        self, autocommit: Optional[bool] = None, cursor_factory: Optional[object] = None
    ) -> Generator[psycopg2.extensions.cursor, None, None]:
        """
        PostgreSQL游标上下文管理器

        Args:
            autocommit: 是否自动提交
            cursor_factory: 游标工厂类,如RealDictCursor

        Yields:
            PostgreSQL游标对象

        Example:
            >>> db = SyncDatabaseConnectionManager()
            >>> with db.postgresql_cursor() as cursor:
            ...     cursor.execute("SELECT * FROM table")
            ...     results = cursor.fetchall()
        """
        with self.postgresql_connection(autocommit=autocommit) as conn:
            cursor = None
            try:
                cursor = conn.cursor(cursor_factory=cursor_factory)
                yield cursor
            except Exception as e:
                logger.error(f"❌ PostgreSQL游标操作失败: {e}")
                raise
            finally:
                if cursor:
                    cursor.close()
                    logger.debug("🔒 PostgreSQL游标已关闭")

    @contextmanager
    def neo4j_session(self) -> Generator[Neo4jSession, None, None]:
        """
        Neo4j会话上下文管理器

        Yields:
            Neo4j会话对象

        Example:
            >>> db = SyncDatabaseConnectionManager()
            >>> with db.neo4j_session() as session:
            ...     result = session.run("MATCH (n) RETURN n LIMIT 1")
        """
        driver = None
        session = None
        try:
            driver = SyncGraphDatabase.driver(
                self.neo4j_config["uri"],
                auth=(self.neo4j_config["user"], self.neo4j_config["password"]),
            )
            session = driver.session()
            yield session
        except Exception as e:
            logger.error(f"❌ Neo4j连接失败: {e}")
            raise
        finally:
            if session:
                session.close()
                logger.debug("🔒 Neo4j会话已关闭")
            if driver:
                driver.close()
                logger.debug("🔒 Neo4j驱动已关闭")

    # 别名方法: 为了兼容 scenario_rule_retriever_optimized.py 的调用
    def session(self):
        """
        session() 方法别名,指向 neo4j_session()

        为了兼容 scenario_rule_retriever_optimized.py 中的调用:
            with self.db_manager.session() as session:
        """
        return self.neo4j_session()

    def get_qdrant_client(self) -> QdrantClient:
        """
        获取Qdrant客户端

        Returns:
            QdrantClient实例

        Example:
            >>> db = SyncDatabaseConnectionManager()
            >>> client = db.get_qdrant_client()
            >>> results = client.query(...)
        """
        try:
            client = QdrantClient(**self.qdrant_config)
            logger.info("✅ Qdrant客户端创建成功")
            return client
        except Exception as e:
            logger.error(f"❌ Qdrant客户端创建失败: {e}")
            raise

    def execute_batch(self, sql: str, params_list: list, batch_size: Optional[int] = None) -> None:
        """
        批量执行SQL语句

        Args:
            sql: SQL语句模板
            params_list: 参数列表
            batch_size: 批次大小,默认使用DEFAULT_BATCH_SIZE

        Example:
            >>> db = SyncDatabaseConnectionManager()
            >>> db.execute_batch(
            ...     "INSERT INTO table (col1, col2) VALUES (%s, %s)",
            ...     [('val1', 'val2'), ('val3', 'val4')]
            ... )
        """
        batch_size = batch_size or DEFAULT_BATCH_SIZE

        with self.postgresql_connection(autocommit=True) as conn:
            cursor = conn.cursor()
            execute_batch(cursor, sql, params_list, page_size=batch_size)
            cursor.close()

        logger.debug(f"✅ 批量执行完成: {len(params_list)}条记录")

    def health_check(self) -> dict:
        """
        检查所有数据库连接的健康状态

        Returns:
            包含各数据库健康状态的字典
        """
        health_status = {}

        # PostgreSQL健康检查
        try:
            with self.postgresql_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
            health_status["postgresql"]] = {"status": "healthy", "error": None}
        except Exception as e:
            health_status["postgresql"]] = {"status": "unhealthy", "error": str(e)}

        # Neo4j健康检查
        try:
            with self.neo4j_session() as session:
                session.run("RETURN 1")
            health_status["neo4j"]] = {"status": "healthy", "error": None}
        except Exception as e:
            health_status["neo4j"]] = {"status": "unhealthy", "error": str(e)}

        # Qdrant健康检查
        try:
            client = self.get_qdrant_client()
            client.get_collections()
            health_status["qdrant"]] = {"status": "healthy", "error": None}
        except Exception as e:
            health_status["qdrant"]] = {"status": "unhealthy", "error": str(e)}

        return health_status


# 创建全局同步数据库管理器实例
_sync_db_manager: Optional[SyncDatabaseConnectionManager] = None


def get_sync_db_manager() -> SyncDatabaseConnectionManager:
    """
    获取全局同步数据库管理器实例(单例模式)

    Returns:
        SyncDatabaseConnectionManager实例

    Example:
        >>> from core.infrastructure.database.connection_manager import get_sync_db_manager
        >>> db = get_sync_db_manager()
        >>> with db.postgresql_cursor() as cursor:
        ...     cursor.execute("SELECT 1")
    """
    global _sync_db_manager

    if _sync_db_manager is None:
        _sync_db_manager = SyncDatabaseConnectionManager()

    return _sync_db_manager

