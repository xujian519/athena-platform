"""
database模块

提供统一的数据库连接管理和常量定义
"""

from .connection_manager import (
    # 异步版本
    DatabaseConnectionManager,
    # 同步版本(用于migration脚本)
    SyncDatabaseConnectionManager,
    elasticsearch_connection,
    get_db_manager,
    get_sync_db_manager,
    neo4j_session,
    postgres_connection,
    postgres_transaction,
    redis_connection,
)
from .constants import (
    BGE_M3_DIM,
    BGE_M3_MAX_SEQ_LENGTH,
    DEFAULT_BATCH_SIZE,
    DEFAULT_CONCURRENT_WORKERS,
    DEFAULT_EMBEDDING_BATCH_SIZE,
    DEFAULT_NEO4J_PORT,
    DEFAULT_PG_PORT,
    DEFAULT_QDRANT_PORT,
    MAX_RETRIES,
    TIMEOUT_SECONDS,
    UUID_NAMESPACE,
    CaseTypes,
    DocumentTypes,
    EntityLabels,
    ErrorMessages,
    RelationTypes,
)

__all__ = [
    "BGE_M3_DIM",
    "BGE_M3_MAX_SEQ_LENGTH",
    "DEFAULT_BATCH_SIZE",
    "DEFAULT_CONCURRENT_WORKERS",
    "DEFAULT_EMBEDDING_BATCH_SIZE",
    "DEFAULT_NEO4J_PORT",
    "DEFAULT_PG_PORT",
    "DEFAULT_QDRANT_PORT",
    "MAX_RETRIES",
    "TIMEOUT_SECONDS",
    # 常量
    "UUID_NAMESPACE",
    "CaseTypes",
    # 配置
    "DatabaseConfig",
    # 异步连接管理
    "DatabaseConnectionManager",
    "DocumentTypes",
    # 枚举类
    "EntityLabels",
    "ErrorMessages",
    "RelationTypes",
    # 同步连接管理
    "SyncDatabaseConnectionManager",
    "elasticsearch_connection",
    "get_db_manager",
    "get_sync_db_manager",
    "neo4j_session",
    "postgres_connection",
    "postgres_transaction",
    "redis_connection",
]
