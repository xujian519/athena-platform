#!/usr/bin/env python3
from __future__ import annotations
"""
搜索引擎配置管理
统一管理所有搜索引擎相关的配置

使用统一环境变量加载器,支持:
- 从.env文件自动加载
- 类型安全的环境变量获取
- 配置验证和默认值
- 密码安全存储
"""

import logging
from dataclasses import dataclass, field
from typing import Any

# 导入统一环境变量加载器
from .env_loader import (
    get_env_bool,
    get_env_float,
    get_env_int,
    get_env_str,
)

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """数据库配置"""

    host: str = "localhost"
    port: int = 5432
    database: str = "patent_legal_db"
    user: str = "athena"
    password: str = ""

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """从环境变量加载配置(使用统一加载器)"""
        return cls(
            host=get_env_str("DB_HOST", "localhost"),
            port=get_env_int("DB_PORT", 5432),
            database=get_env_str("DB_NAME", "patent_legal_db"),
            user=get_env_str("DB_USER", "athena"),
            password=get_env_str("DB_PASSWORD", "", required=False),
        )

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式,用于psycopg2.connect"""
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "user": self.user,
            "password": self.password,
        }


@dataclass
class QdrantConfig:
    """Qdrant向量数据库配置"""

    host: str = "localhost"
    port: int = 6333
    timeout: int = 30
    check_compatibility: bool = False

    @classmethod
    def from_env(cls) -> "QdrantConfig":
        """从环境变量加载配置(使用统一加载器)"""
        return cls(
            host=get_env_str("QDRANT_HOST", "localhost"),
            port=get_env_int("QDRANT_PORT", 6333),
            timeout=get_env_int("QDRANT_TIMEOUT", 30),
            check_compatibility=get_env_bool("QDRANT_CHECK_COMPATIBILITY", False),
        )


@dataclass
class EmbeddingConfig:
    """嵌入模型配置"""

    model_name: str = "bge-m3"
    device: str = "auto"  # auto, mps, cuda, cpu
    batch_size: int = 32

    @classmethod
    def from_env(cls) -> "EmbeddingConfig":
        """从环境变量加载配置(使用统一加载器)"""
        return cls(
            model_name=get_env_str("EMBEDDING_MODEL", "bge-m3"),
            device=get_env_str("EMBEDDING_DEVICE", "auto"),
            batch_size=get_env_int("EMBEDDING_BATCH_SIZE", 32),
        )


@dataclass
class SearchConfig:
    """搜索配置"""

    # 向量集合配置
    vector_collections: list[str] = field(
        default_factory=lambda: [
            "legal_documents_enhanced",
            "legal_clauses_1024",
            "patent_rules_unified_1024",
            "ai_technical_terms_1024",
        ]
    )

    # 搜索参数
    max_results_per_source: int = 100
    rerank_top_k: int = 50
    diversification_factor: float = 0.3
    temporal_decay: float = 0.95
    graph_depth_limit: int = 3

    # 缓存配置
    cache_enabled: bool = True
    cache_ttl: int = 3600
    cache_size_limit: int = 1000

    @classmethod
    def from_env(cls) -> "SearchConfig":
        """从环境变量加载配置(使用统一加载器)"""
        return cls(
            max_results_per_source=get_env_int("SEARCH_MAX_RESULTS", 100),
            rerank_top_k=get_env_int("SEARCH_RERANK_TOP_K", 50),
            diversification_factor=get_env_float("SEARCH_DIVERSIFICATION_FACTOR", 0.3),
            temporal_decay=get_env_float("SEARCH_TEMPORAL_DECAY", 0.95),
            graph_depth_limit=get_env_int("SEARCH_GRAPH_DEPTH_LIMIT", 3),
            cache_enabled=get_env_bool("SEARCH_CACHE_ENABLED", True),
            cache_ttl=get_env_int("SEARCH_CACHE_TTL", 3600),
            cache_size_limit=get_env_int("SEARCH_CACHE_SIZE_LIMIT", 1000),
        )


@dataclass
class UnifiedSearchConfig:
    """统一搜索配置"""

    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    qdrant: QdrantConfig = field(default_factory=QdrantConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    search: SearchConfig = field(default_factory=SearchConfig)

    @classmethod
    def from_env(cls) -> "UnifiedSearchConfig":
        """从环境变量加载所有配置"""
        logger.info("🔧 从环境变量加载搜索配置...")

        config = cls(
            database=DatabaseConfig.from_env(),
            qdrant=QdrantConfig.from_env(),
            embedding=EmbeddingConfig.from_env(),
            search=SearchConfig.from_env(),
        )

        # 验证配置
        config._validate()

        logger.info("✅ 搜索配置加载完成")
        return config

    def _validate(self) -> None:
        """验证配置"""
        if not self.database.password:
            logger.warning("⚠️ 数据库密码未设置,请设置DB_PASSWORD环境变量")

        if self.search.max_results_per_source < 1:
            raise ValueError("SEARCH_MAX_RESULTS必须大于0")

        if not (0 <= self.search.diversification_factor <= 1):
            raise ValueError("SEARCH_DIVERSIFICATION_FACTOR必须在0-1之间")

    def log_config(self) -> None:
        """记录配置信息(隐藏敏感信息)"""
        logger.info("📋 搜索配置信息:")
        logger.info(
            f"  • 数据库: {self.database.user}@{self.database.host}:{self.database.port}/{self.database.database}"
        )
        logger.info(f"  • Qdrant: {self.qdrant.host}:{self.qdrant.port}")
        logger.info(f"  • 嵌入模型: {self.embedding.model_name} (设备: {self.embedding.device})")
        logger.info(f"  • 最大结果数: {self.search.max_results_per_source}")
        logger.info(f"  • 缓存: {'启用' if self.search.cache_enabled else '禁用'}")


# 全局配置实例
_global_config: UnifiedSearchConfig | None = None


def get_search_config() -> UnifiedSearchConfig:
    """获取全局搜索配置实例"""
    global _global_config
    if _global_config is None:
        _global_config = UnifiedSearchConfig.from_env()
    return _global_config


def reset_search_config() -> None:
    """重置全局配置(主要用于测试)"""
    global _global_config
    _global_config = None
