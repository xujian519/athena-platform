#!/usr/bin/env python3
"""
生产环境配置
Production Environment Configuration

管理生产环境的所有配置参数

作者: Athena平台团队
创建时间: 2025-12-25
"""

from __future__ import annotations
import logging
import os
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from core.config.secure_config import get_config

config = get_config()


# 添加项目路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入安全配置
try:
    from production.config import get_nebula_config
except ImportError:
    def get_nebula_config() -> Any | None:
        return {
            'host': 'localhost',
            'port': 9669,
            'user': 'root',
            "password": config.get("NEBULA_PASSWORD", required=True),
            'space': 'patent_full_text_v2'
        }

logger = logging.getLogger(__name__)


class LogLevel(Enum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class QdrantConfig:
    """Qdrant配置"""
    host: str = "localhost"
    port: int = 6333
    timeout: int = 60
    collection_name: str = "patent_full_text_v2"
    vector_size: int = 768
    distance: str = "Cosine"
    api_key: str | None = None
    https: bool = False


@dataclass
class NebulaConfig:
    """NebulaGraph配置 - 从环境变量读取"""
    host: str = "127.0.0.1"
    port: int = 9669
    space_name: str = "patent_full_text_v2"
    username: str = "root"
    timeout: int = 30
    pool_size: int = 10

    @property
    def password(self) -> str:
        """从配置获取密码"""
        nebula_config = get_nebula_config()
        return nebula_config.get("password", config.get("NEBULA_PASSWORD", required=True))


@dataclass
class RedisConfig:
    """Redis配置"""
    host: str = "localhost"
    port: int = 6379
    password: str | None = None
    db: int = 0
    max_connections: int = 50
    socket_timeout: int = 5
    socket_connect_timeout: int = 5


@dataclass
class ModelConfig:
    """模型配置"""
    # 向量化模型
    embedding_model_name: str = "BAAI/bge-m3"
    embedding_model_path: str = "/app/models/bge-base-zh-v1.5"
    embedding_batch_size: int = 32
    embedding_max_length: int = 512

    # 序列标注模型
    sequence_tagger_name: str = "chinese_legal_electra"
    sequence_tagger_path: str = "/app/models/chinese_legal_electra"
    sequence_tagger_batch_size: int = 16
    sequence_tagger_max_length: int = 256

    # 模型缓存
    cache_size: int = 3
    unload_after: int = 3600  # 秒


@dataclass
class CacheConfig:
    """缓存配置"""
    # 内存缓存
    enable_memory: bool = True
    memory_max_size: int = 10000
    memory_ttl: int = 3600

    # Redis缓存
    enable_redis: bool = True
    redis_ttl: int = 7200
    redis_key_prefix: str = "patent:"

    # 缓存策略
    cache_level: str = "modules/modules/memory/modules/memory/modules/memory/memory"  # modules/memory/redis/both


@dataclass
class ProcessingConfig:
    """处理配置"""
    # 批处理
    batch_size: int = 10
    max_workers: int = 4
    use_threading: bool = True

    # 重试
    max_retries: int = 3
    backoff_factor: float = 2.0
    retry_timeout: int = 300

    # 超时
    request_timeout: int = 60
    processing_timeout: int = 300


@dataclass
class VectorizationConfig:
    """向量化配置"""
    # 层级配置
    enable_layer1: bool = True  # 标题/摘要/IPC
    enable_layer2: bool = True  # 权利要求
    enable_layer3: bool = True  # 发明内容

    # Layer 2配置
    enable_per_claim_vectorization: bool = True
    max_claims: int = 50

    # Layer 3配置
    enable_structured_chunking: bool = True
    chunk_max_size: int = 500
    chunk_overlap: int = 50
    max_chunks: int = 20


@dataclass
class TripleExtractionConfig:
    """三元组提取配置"""
    # 提取策略
    strategy: str = "hybrid"  # rules/model/hybrid

    # 规则提取
    enable_rules: bool = True
    rule_confidence_threshold: float = 0.6

    # 模型提取
    enable_model: bool = False
    model_confidence_threshold: float = 0.7

    # 云端LLM
    enable_cloud_llm: bool = False
    cloud_llm_provider: str = "qwen"  # qwen/deepseek
    cloud_llm_api_key: str | None = None


@dataclass
class KnowledgeGraphConfig:
    """知识图谱配置"""
    # 保存配置
    auto_save: bool = False
    batch_insert: bool = True
    batch_size: int = 100

    # 图谱配置
    enable_triples: bool = True
    enable_feature_relations: bool = True
    enable_contrast_analysis: bool = False


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"

    # 文件日志
    enable_file: bool = True
    log_dir: str = "/app/logs"
    log_file: str = "patent_processing.log"
    max_bytes: int = 10485760  # 10MB
    backup_count: int = 5

    # 结构化日志
    enable_json: bool = False
    json_file: str = "patent_processing.jsonl"


@dataclass
class MonitoringConfig:
    """监控配置"""
    # 性能监控
    enable_performance_monitoring: bool = True
    metrics_retention: int = 86400  # 24小时

    # 健康检查
    enable_health_check: bool = True
    health_check_interval: int = 30  # 秒

    # 告警
    enable_alerts: bool = False
    alert_threshold: float = 0.95  # 成功率阈值


@dataclass
class APIServerConfig:
    """API服务配置"""
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    reload: bool = False
    log_level: str = "info"

    # 限流
    enable_rate_limit: bool = True
    rate_limit: int = 100  # 每分钟请求数

    # 超时
    request_timeout: int = 300
    keepalive_timeout: int = 65


@dataclass
class ProductionConfig:
    """
    生产环境总配置

    从环境变量加载配置，提供默认值
    """
    # 环境信息
    environment: str = "production"
    debug: bool = False

    # 子配置
    qdrant: QdrantConfig = field(default_factory=QdrantConfig)
    nebula: NebulaConfig = field(default_factory=NebulaConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    vectorization: VectorizationConfig = field(default_factory=VectorizationConfig)
    triple_extraction: TripleExtractionConfig = field(default_factory=TripleExtractionConfig)
    knowledge_graph: KnowledgeGraphConfig = field(default_factory=KnowledgeGraphConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    api_server: APIServerConfig = field(default_factory=APIServerConfig)

    @classmethod
    def from_env(cls) -> "ProductionConfig":
        """
        从环境变量加载配置

        Returns:
            ProductionConfig
        """
        config = cls()

        # 环境和调试
        config.environment = os.getenv("APP_ENV", "production")
        config.debug = os.getenv("APP_DEBUG", "false").lower() == "true"

        # Qdrant
        config.qdrant.host = os.getenv("QDRANT_HOST", "localhost")
        config.qdrant.port = int(os.getenv("QDRANT_PORT", "6333"))
        config.qdrant.api_key = os.getenv("QDRANT_API_KEY")

        # NebulaGraph
        config.nebula.host = os.getenv("NEBULA_HOST", "127.0.0.1")
        config.nebula.port = int(os.getenv("NEBULA_PORT", "9669"))
        config.nebula.username = os.getenv("NEBULA_USERNAME", "root")
        # config.nebula.password 从配置读取(已通过property处理)

        # Redis
        config.redis.host = os.getenv("REDIS_HOST", "localhost")
        config.redis.port = int(os.getenv("REDIS_PORT", "6379"))
        config.redis.password = os.getenv("REDIS_PASSWORD")

        # 模型
        config.model.embedding_model_path = os.getenv(
            "EMBEDDING_MODEL_PATH",
            config.model.embedding_model_path
        )
        config.model.sequence_tagger_path = os.getenv(
            "SEQUENCE_TAGGER_PATH",
            config.model.sequence_tagger_path
        )

        # 缓存
        config.cache.enable_memory = os.getenv("ENABLE_CACHE", "true").lower() == "true"
        config.cache.enable_redis = os.getenv("ENABLE_REDIS", "true").lower() == "true"

        # 处理
        config.processing.batch_size = int(os.getenv("BATCH_SIZE", "10"))
        config.processing.max_workers = int(os.getenv("MAX_WORKERS", "4"))

        # 日志
        config.logging.level = os.getenv("APP_LOG_LEVEL", "INFO")
        config.logging.log_dir = os.getenv("LOG_DIR", "/app/logs")

        # API服务
        config.api_server.workers = int(os.getenv("APP_WORKERS", "4"))
        config.api_server.port = int(os.getenv("APP_PORT", "8000"))

        return config

    def validate(self) -> list[str]:
        """
        验证配置

        Returns:
            错误信息列表，空列表表示验证通过
        """
        errors = []

        # 验证模型路径
        model_path = Path(self.model.embedding_model_path)
        if not model_path.exists():
            errors.append(f"向量化模型路径不存在: {self.model.embedding_model_path}")

        # 验证日志目录
        log_dir = Path(self.logging.log_dir)
        if not log_dir.exists():
            try:
                log_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"日志目录创建失败: {self.logging.log_dir}: {e}")

        # 验证端口范围
        if not (1 <= self.api_server.port <= 65535):
            errors.append(f"API服务端口无效: {self.api_server.port}")

        if not (1 <= self.qdrant.port <= 65535):
            errors.append(f"Qdrant端口无效: {self.qdrant.port}")

        if not (1 <= self.nebula.port <= 65535):
            errors.append(f"NebulaGraph端口无效: {self.nebula.port}")

        return errors

    def get_summary(self) -> dict[str, Any]:
        """
        获取配置摘要

        Returns:
            配置摘要
        """
        return {
            "environment": self.environment,
            "debug": self.debug,
            "databases": {
                "qdrant": f"{self.qdrant.host}:{self.qdrant.port}",
                "nebula": f"{self.nebula.host}:{self.nebula.port}",
                "redis": f"{self.redis.host}:{self.redis.port}" if self.cache.enable_redis else "disabled"
            },
            "models": {
                "embedding": self.model.embedding_model_name,
                "sequence_tagger": self.model.sequence_tagger_name
            },
            "processing": {
                "batch_size": self.processing.batch_size,
                "max_workers": self.processing.max_workers,
                "cache_enabled": self.cache.enable_memory or self.cache.enable_redis
            },
            "api": {
                "host": self.api_server.host,
                "port": self.api_server.port,
                "workers": self.api_server.workers
            }
        }


# ========== 便捷函数 ==========

def load_production_config(env_file: str | None = None) -> ProductionConfig:
    """
    加载生产配置

    Args:
        env_file: 环境变量文件路径

    Returns:
        ProductionConfig
    """
    # 加载.env文件
    if env_file:
        env_path = Path(env_file)
        if env_path.exists():
            from dotenv import load_dotenv
            load_dotenv(env_path)
            logger.info(f"✅ 已加载环境变量文件: {env_file}")

    # 从环境变量创建配置
    config = ProductionConfig.from_env()

    # 验证配置
    errors = config.validate()
    if errors:
        logger.error("❌ 配置验证失败:")
        for error in errors:
            logger.error(f"  - {error}")
        raise ValueError("配置验证失败")

    return config


def get_development_config() -> ProductionConfig:
    """获取开发环境配置"""
    config = ProductionConfig()
    config.environment = "development"
    config.debug = True
    config.logging.level = "DEBUG"
    config.api_server.reload = True
    config.cache.enable_redis = False
    config.knowledge_graph.auto_save = False
    return config


def get_staging_config() -> ProductionConfig:
    """获取预发布环境配置"""
    config = ProductionConfig()
    config.environment = "staging"
    config.debug = False
    config.logging.level = "INFO"
    config.api_server.workers = 2
    config.monitoring.enable_alerts = True
    return config


# ========== 示例使用 ==========

def main() -> None:
    """示例使用"""
    print("=" * 70)
    print("生产环境配置示例")
    print("=" * 70)

    # 加载生产配置
    print("\n📋 加载生产配置...")
    config = load_production_config()

    # 配置摘要
    print("\n📊 配置摘要:")
    summary = config.get_summary()
    print(f"  环境: {summary['environment']}")
    print(f"  调试模式: {summary['debug']}")

    print("\n  数据库:")
    for name, endpoint in summary['databases'].items():
        print(f"    {name}: {endpoint}")

    print("\n  模型:")
    for name, model in summary['models'].items():
        print(f"    {name}: {model}")

    print("\n  处理:")
    for key, value in summary['processing'].items():
        print(f"    {key}: {value}")

    print("\n  API服务:")
    for key, value in summary['api'].items():
        print(f"    {key}: {value}")

    # 配置详情
    print("\n🔧 Qdrant配置:")
    print(f"  集合名称: {config.qdrant.collection_name}")
    print(f"  向量维度: {config.qdrant.vector_size}")
    print(f"  距离度量: {config.qdrant.distance}")

    print("\n🔧 NebulaGraph配置:")
    print(f"  空间名称: {config.nebula.space_name}")
    print(f"  连接池大小: {config.nebula.pool_size}")

    print("\n🔧 向量化配置:")
    print(f"  Layer 1 (标题/摘要/IPC): {config.vectorization.enable_layer1}")
    print(f"  Layer 2 (权利要求): {config.vectorization.enable_layer2}")
    print(f"  Layer 3 (发明内容): {config.vectorization.enable_layer3}")

    print("\n🔧 三元组提取配置:")
    print(f"  提取策略: {config.triple_extraction.strategy}")
    print(f"  规则提取: {config.triple_extraction.enable_rules}")
    print(f"  模型提取: {config.triple_extraction.enable_model}")
    print(f"  云端LLM: {config.triple_extraction.enable_cloud_llm}")


if __name__ == "__main__":
    main()
