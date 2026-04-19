#!/usr/bin/env python3
from __future__ import annotations
"""
Athena记忆模块 - 生产环境配置加载器
Production Environment Configuration Loader

此模块从环境变量加载记忆系统的生产配置，确保安全性和灵活性。

使用方法:
    from core.memory.config import MemorySystemConfig
    config = MemorySystemConfig.from_env()

作者: Athena平台团队
创建时间: 2026-01-24
版本: 1.0.0
"""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class PostgreSQLConfig:
    """PostgreSQL数据库配置"""

    host: str
    port: int
    database: str
    user: str
    password: str
    pool_min: int = 5
    pool_max: int = 20
    timeout: int = 60

    @classmethod
    def from_env(cls) -> 'PostgreSQLConfig':
        """从环境变量加载配置"""
        return cls(
            host=os.getenv('MEMORY_DB_HOST', 'localhost'),
            port=int(os.getenv('MEMORY_DB_PORT', '5432')),
            database=os.getenv('MEMORY_DB_NAME', 'athena_memory'),
            user=os.getenv('MEMORY_DB_USER', 'athena_admin'),
            password=os.getenv('MEMORY_DB_PASSWORD', ''),
            pool_min=int(os.getenv('MEMORY_DB_POOL_MIN', '5')),
            pool_max=int(os.getenv('MEMORY_DB_POOL_MAX', '20')),
            timeout=int(os.getenv('MEMORY_DB_TIMEOUT', '60'))
        )

    def get_dsn(self) -> str:
        """获取PostgreSQL DSN连接字符串"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    def validate(self) -> bool:
        """验证配置有效性"""
        if not self.password:
            logger.warning("⚠️ PostgreSQL密码未设置，可能无法连接数据库")
            return False
        return True


@dataclass
class RedisConfig:
    """Redis缓存配置"""

    host: str
    port: int
    db: int
    password: str | None = None
    ttl: dict[str, int] = field(default_factory=dict)

    @classmethod
    def from_env(cls) -> 'RedisConfig':
        """从环境变量加载配置"""
        return cls(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', '6379')),
            db=int(os.getenv('REDIS_DB', '0')),
            password=os.getenv('REDIS_PASSWORD'),
            ttl={
                'agent_stats': int(os.getenv('REDIS_TTL_AGENT_STATS', '300')),
                'search_results': int(os.getenv('REDIS_TTL_SEARCH_RESULTS', '60')),
                'memory_data': int(os.getenv('REDIS_TTL_MEMORY_DATA', '180')),
                'hot_memory': int(os.getenv('REDIS_TTL_HOT_MEMORY', '600'))
            }
        )

    def get_url(self) -> str:
        """获取Redis连接URL"""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"

    def validate(self) -> bool:
        """验证配置有效性"""
        return True  # Redis是可选的，不强制要求密码


@dataclass
class QdrantConfig:
    """Qdrant向量数据库配置"""

    host: str
    port: int
    api_key: str | None = None
    collections: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_env(cls) -> 'QdrantConfig':
        """从环境变量加载配置"""
        return cls(
            host=os.getenv('QDRANT_HOST', 'localhost'),
            port=int(os.getenv('QDRANT_PORT', '6333')),
            api_key=os.getenv('QDRANT_API_KEY'),
            collections={
                'main': os.getenv('QDRANT_COLLECTION_MAIN', 'athena_memories'),
                'episodic': os.getenv('QDRANT_COLLECTION_EPISODIC', 'episodic_memories'),
                'semantic': os.getenv('QDRANT_COLLECTION_SEMANTIC', 'semantic_memories')
            }
        )

    def get_url(self) -> str:
        """获取Qdrant基础URL"""
        return f"http://{self.host}:{self.port}"

    def validate(self) -> bool:
        """验证配置有效性"""
        return True


@dataclass
class EmbeddingConfig:
    """嵌入模型配置"""

    enable_real_embeddings: bool = True
    model_type: str = "local"  # local, openai, md5
    model_name: str = "BAAI/bge-m3"
    model_path: str | None = None
    openai_api_key: str | None = None
    dimension: int = 1024

    @classmethod
    def from_env(cls) -> 'EmbeddingConfig':
        """从环境变量加载配置"""
        enable_real = os.getenv('ENABLE_REAL_EMBEDDINGS', 'true').lower() == 'true'
        has_openai_key = bool(os.getenv('OPENAI_API_KEY'))

        model_type = "local"
        model_name = "BAAI/bge-m3"

        if has_openai_key and not enable_real:
            model_type = "openai"
            model_name = os.getenv('OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')
        elif not enable_real:
            model_type = "md5"
            model_name = "md5-fallback"

        # 设置维度
        dimension = 1024  # BGE-M3默认
        if model_type == "openai":
            dimension = 1536 if "3-small" in model_name or "3-large" in model_name else 1536
        elif model_type == "md5":
            dimension = 1024

        return cls(
            enable_real_embeddings=enable_real,
            model_type=model_type,
            model_name=model_name,
            model_path=os.getenv('BGE_M3_MODEL_PATH'),
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            dimension=dimension
        )

    def validate(self) -> bool:
        """验证配置有效性"""
        if self.model_type == "openai" and not self.openai_api_key:
            logger.warning("⚠️ OpenAI嵌入模型已选择但API密钥未设置")
            return False
        return True


@dataclass
class PerformanceConfig:
    """性能配置"""

    hot_cache_limit: int = 50
    batch_size: int = 100
    query_timeout: int = 30

    @classmethod
    def from_env(cls) -> 'PerformanceConfig':
        """从环境变量加载配置"""
        return cls(
            hot_cache_limit=int(os.getenv('HOT_CACHE_LIMIT', '50')),
            batch_size=int(os.getenv('BATCH_SIZE', '100')),
            query_timeout=int(os.getenv('QUERY_TIMEOUT', '30'))
        )


@dataclass
class SecurityConfig:
    """安全配置"""

    environment: str = "production"
    debug_mode: bool = False
    cors_allowed_origins: str = "*"

    @classmethod
    def from_env(cls) -> 'SecurityConfig':
        """从环境变量加载配置"""
        return cls(
            environment=os.getenv('ENVIRONMENT', 'production'),
            debug_mode=os.getenv('DEBUG_MODE', 'false').lower() == 'true',
            cors_allowed_origins=os.getenv('CORS_ALLOWED_ORIGINS', '*')
        )


@dataclass
class MemorySystemConfig:
    """记忆系统完整配置"""

    postgresql: PostgreSQLConfig
    redis: RedisConfig
    qdrant: QdrantConfig
    embedding: EmbeddingConfig
    performance: PerformanceConfig
    security: SecurityConfig

    @classmethod
    def from_env(cls) -> 'MemorySystemConfig':
        """从环境变量加载所有配置"""
        return cls(
            postgresql=PostgreSQLConfig.from_env(),
            redis=RedisConfig.from_env(),
            qdrant=QdrantConfig.from_env(),
            embedding=EmbeddingConfig.from_env(),
            performance=PerformanceConfig.from_env(),
            security=SecurityConfig.from_env()
        )

    def to_db_config(self) -> dict[str, Any]:
        """
        转换为UnifiedAgentMemorySystem所需的db_config格式

        Returns:
            符合现有系统的配置字典
        """
        return {
            'postgresql': {
                'host': self.postgresql.host,
                'port': self.postgresql.port,
                'database': self.postgresql.database,
                'user': self.postgresql.user,
                'password': self.postgresql.password
            },
            'redis': {
                'host': self.redis.host,
                'port': self.redis.port,
                'db': self.redis.db,
                'password': self.redis.password or '',
                'decode_responses': True,
                'ttl': self.redis.ttl
            },
            'qdrant': {
                'host': self.qdrant.host,
                'port': self.qdrant.port,
                'api_key': self.qdrant.api_key,
                'collections': self.qdrant.collections
            },
            'knowledge_backend': {
                'url': os.getenv('KNOWLEDGE_GRAPH_URL', 'http://localhost:8080'),
                'health_endpoint': os.getenv('KNOWLEDGE_GRAPH_HEALTH_ENDPOINT', '/health')
            }
        }

    def validate(self) -> bool:
        """验证所有配置"""
        all_valid = True

        if not self.postgresql.validate():
            logger.error("❌ PostgreSQL配置验证失败")
            all_valid = False

        if not self.redis.validate():
            logger.warning("⚠️ Redis配置验证失败（可选）")

        if not self.qdrant.validate():
            logger.warning("⚠️ Qdrant配置验证失败（可选）")

        if not self.embedding.validate():
            logger.error("❌ 嵌入模型配置验证失败")
            all_valid = False

        return all_valid

    def print_summary(self) -> None:
        """打印配置摘要（隐藏敏感信息）"""
        logger.info("=" * 50)
        logger.info("📋 Athena记忆模块配置摘要")
        logger.info("=" * 50)
        logger.info(f"环境: {self.security.environment}")
        logger.info(f"调试模式: {self.security.debug_mode}")
        logger.info("")
        logger.info("PostgreSQL:")
        logger.info(f"  主机: {self.postgresql.host}:{self.postgresql.port}")
        logger.info(f"  数据库: {self.postgresql.database}")
        logger.info(f"  用户: {self.postgresql.user}")
        logger.info(f"  密码: {'***' if self.postgresql.password else '(未设置)'}")
        logger.info("")
        logger.info("Redis:")
        logger.info(f"  主机: {self.redis.host}:{self.redis.port}")
        logger.info(f"  密码: {'***' if self.redis.password else '(未设置)'}")
        logger.info("")
        logger.info("Qdrant:")
        logger.info(f"  主机: {self.qdrant.host}:{self.qdrant.port}")
        logger.info("")
        logger.info("嵌入模型:")
        logger.info(f"  类型: {self.embedding.model_type}")
        logger.info(f"  模型: {self.embedding.model_name}")
        logger.info(f"  维度: {self.embedding.dimension}")
        logger.info(f"  路径: {self.embedding.model_path or '(默认)'}")
        logger.info("")
        logger.info("性能:")
        logger.info(f"  热缓存限制: {self.performance.hot_cache_limit}")
        logger.info(f"  批量大小: {self.performance.batch_size}")
        logger.info(f"  查询超时: {self.performance.query_timeout}s")
        logger.info("=" * 50)


def load_production_config(env_file: str | None = None) -> MemorySystemConfig:
    """
    加载生产环境配置

    Args:
        env_file: 可选的.env文件路径

    Returns:
        MemorySystemConfig配置对象
    """
    # 如果指定了.env文件，先加载它
    if env_file:
        env_path = Path(env_file)
        if env_path.exists():
            from dotenv import load_dotenv
            load_dotenv(env_path)
            logger.info(f"✅ 已加载环境配置文件: {env_file}")
        else:
            logger.warning(f"⚠️ 环境配置文件不存在: {env_file}")

    # 从环境变量加载配置
    config = MemorySystemConfig.from_env()

    # 验证配置
    config.validate()

    # 打印摘要
    if logger.isEnabledFor(logging.INFO):
        config.print_summary()

    return config


# 导出
__all__ = [
    'EmbeddingConfig',
    'MemorySystemConfig',
    'PerformanceConfig',
    'PostgreSQLConfig',
    'QdrantConfig',
    'RedisConfig',
    'SecurityConfig',
    'load_production_config'
]
