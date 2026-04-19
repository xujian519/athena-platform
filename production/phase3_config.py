#!/usr/bin/env python3
"""
Athena知识图谱系统 - Phase 3 生产环境配置
专家级推理引擎与规则系统
"""

from __future__ import annotations
import logging
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class Environment(Enum):
    """环境类型"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"
    STAGING = "staging"

class LogLevel(Enum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

@dataclass
class DatabaseConfig:
    """数据库配置"""
    # PostgreSQL配置
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_database: str = "athena_patent_production"
    postgres_user: str = "athena_admin"
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "secure_password_2024")
    postgres_pool_size: int = 20
    postgres_max_overflow: int = 10

    # Redis缓存配置
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = os.getenv("REDIS_PASSWORD", "")
    redis_pool_size: int = 15

    # Elasticsearch配置
    elasticsearch_host: str = "localhost"
    elasticsearch_port: int = 9200
    elasticsearch_index_prefix: str = "athena_production"

    # Qdrant向量数据库配置
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "patent_vectors_production"

@dataclass
class ReasoningConfig:
    """推理引擎配置"""
    # ExpertRuleEngine配置
    expert_engine_rules_file: str = "production/data/expert_rules.json"
    expert_engine_cache_size: int = 1000
    expert_engine_timeout: int = 30  # 秒

    # PatentRuleChainEngine配置
    patent_rules_file: str = "production/data/patent_rules.json"
    compliance_threshold: float = 0.75
    rule_chain_timeout: int = 45  # 秒

    # PriorArtAnalyzer配置
    knowledge_graph_depth: int = 5
    similarity_threshold: float = 0.8
    evolution_analysis_timeout: int = 60  # 秒

    # LLMEnhancedJudgment配置
    llm_provider: str = "local"  # local, openai, claude, etc.
    llm_model: str = "qwen2.5:14b"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 4096
    judgment_cache_ttl: int = 3600  # 秒

    # RoadmapGenerator配置
    roadmap_time_horizon: int = 36  # 月
    roadmap_complexity_level: str = "advanced"  # basic, intermediate, advanced
    roadmap_generation_timeout: int = 120  # 秒

    # ComplianceJudge配置
    compliance_dimensions: list[str] | None = None
    expert_review_timeout: int = 90  # 秒
    risk_assessment_enabled: bool = True

    def __post_init__(self):
        if self.compliance_dimensions is None:
            self.compliance_dimensions = [
                "novelty", "inventiveness", "utility",
                "disclosure", "claim_scope", "prior_art",
                "technical_contribution", "industrial_applicability", "clarity"
            ]

@dataclass
class PerformanceConfig:
    """性能配置"""
    # 并发配置
    max_concurrent_reasoning: int = 50
    max_concurrent_judgments: int = 30
    max_concurrent_compliance: int = 20

    # 缓存配置
    cache_strategy: str = "lru"  # lru, fifo, lfu
    cache_max_size: int = 10000
    cache_ttl: int = 7200  # 秒

    # 批处理配置
    batch_size: int = 100
    batch_timeout: int = 300  # 秒

    # 内存配置
    memory_limit_mb: int = 8192  # 8GB
    gc_threshold: float = 0.8

@dataclass
class MonitoringConfig:
    """监控配置"""
    # 日志配置
    log_level: str = "INFO"
    log_file: str = "production/logs/phase3_reasoning.log"
    log_rotation: str = "daily"
    log_retention: int = 30  # 天

    # 指标配置
    metrics_enabled: bool = True
    metrics_port: int = 8090
    health_check_interval: int = 30  # 秒

    # 告警配置
    alert_threshold_error_rate: float = 0.05  # 5%
    alert_threshold_response_time: float = 5.0  # 秒
    alert_email_enabled: bool = True
    alert_email_recipients: list[str] | None = None

    def __post_init__(self):
        if self.alert_email_recipients is None:
            self.alert_email_recipients = ["admin@athena-patent.com"]

@dataclass
class SecurityConfig:
    """安全配置"""
    # API配置
    api_key_required: bool = True
    api_key_header: str = "X-API-Key"
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 100

    # 数据加密
    encryption_enabled: bool = True
    encryption_key_rotation_days: int = 90

    # 访问控制
    authentication_required: bool = True
    session_timeout: int = 3600  # 秒

    # 审计日志
    audit_logging_enabled: bool = True
    audit_log_file: str = "production/logs/audit.log"

class Phase3ProductionConfig:
    """Phase 3生产环境主配置类"""

    def __init__(self, environment: Environment = Environment.PRODUCTION):
        self.environment = environment
        self.base_path = Path(__file__).parent.parent

        # 加载各模块配置
        self.database = DatabaseConfig()
        self.reasoning = ReasoningConfig()
        self.performance = PerformanceConfig()
        self.monitoring = MonitoringConfig()
        self.security = SecurityConfig()

        # 根据环境调整配置
        self._adjust_for_environment()

        # 验证配置
        self._validate_config()

        # 设置日志
        self._setup_logging()

    def _adjust_for_environment(self) -> Any:
        """根据环境调整配置"""
        if self.environment == Environment.PRODUCTION:
            # 生产环境优化配置
            self.database.postgres_pool_size = 50
            self.database.redis_pool_size = 30
            self.performance.max_concurrent_reasoning = 100
            self.performance.memory_limit_mb = 16384  # 16GB
            self.monitoring.log_level = "INFO"

        elif self.environment == Environment.DEVELOPMENT:
            # 开发环境配置
            self.database.postgres_pool_size = 5
            self.database.redis_pool_size = 5
            self.performance.max_concurrent_reasoning = 10
            self.performance.memory_limit_mb = 2048  # 2GB
            self.monitoring.log_level = "DEBUG"
            self.security.api_key_required = False

        elif self.environment == Environment.TESTING:
            # 测试环境配置
            self.database.postgres_database = "athena_patent_test"
            self.database.qdrant_collection = "patent_vectors_test"
            self.database.elasticsearch_index_prefix = "athena_test"
            self.monitoring.log_level = "WARNING"

    def _validate_config(self) -> Any:
        """验证配置有效性"""
        # 验证路径
        for path_attr in ['expert_engine_rules_file', 'patent_rules_file',
                         'log_file', 'audit_log_file']:
            full_path = self.base_path / getattr(self.reasoning, path_attr, "")
            if path_attr in ['expert_engine_rules_file', 'patent_rules_file']:
                full_path.parent.mkdir(parents=True, exist_ok=True)

        # 验证数值范围
        assert 0.0 <= self.reasoning.compliance_threshold <= 1.0, "合规性阈值必须在0-1之间"
        assert 0.0 <= self.reasoning.llm_temperature <= 2.0, "LLM温度必须在0-2之间"
        assert self.performance.memory_limit_mb > 0, "内存限制必须大于0"

    def _setup_logging(self) -> Any:
        """设置日志系统"""
        log_level = getattr(logging, self.monitoring.log_level)

        # 创建日志目录
        log_file_path = self.base_path / self.monitoring.log_file
        log_file_path.parent.mkdir(parents=True, exist_ok=True)

        # 配置根日志记录器
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.file_handler(log_file_path),
                logging.stream_handler()
            ]
        )

        # 设置第三方库日志级别
        logging.getLogger('urllib3').set_level(logging.WARNING)
        logging.getLogger('asyncio').set_level(logging.WARNING)

    def get_database_url(self) -> str:
        """获取PostgreSQL连接URL"""
        return (f"postgresql://{self.database.postgres_user}:{self.database.postgres_password}"
                f"@{self.database.postgres_host}:{self.database.postgres_port}"
                f"/{self.database.postgres_database}")

    def get_redis_url(self) -> str:
        """获取Redis连接URL"""
        auth_part = f":{self.database.redis_password}@" if self.database.redis_password else ""
        return f"redis://{auth_part}{self.database.redis_host}:{self.database.redis_port}/{self.database.redis_db}"

    def get_elasticsearch_url(self) -> str:
        """获取Elasticsearch连接URL"""
        return f"http://{self.database.elasticsearch_host}:{self.database.elasticsearch_port}"

    def get_qdrant_url(self) -> str:
        """获取Qdrant连接URL"""
        return f"http://{self.database.qdrant_host}:{self.database.qdrant_port}"

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        return {
            "environment": self.environment.value,
            "infrastructure/infrastructure/database": self.database.__dict__,
            "reasoning": self.reasoning.__dict__,
            "performance": self.performance.__dict__,
            "infrastructure/infrastructure/monitoring": self.monitoring.__dict__,
            "security": self.security.__dict__,
            "urls": {
                "database_url": self.get_database_url(),
                "redis_url": self.get_redis_url(),
                "elasticsearch_url": self.get_elasticsearch_url(),
                "qdrant_url": self.get_qdrant_url()
            }
        }

    def save_config(self, file_path: str = None) -> None:
        """保存配置到文件"""
        if file_path is None:
            file_path = self.base_path / "production" / "config" / "phase3_production_config.json"

        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        import json
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

        print(f"✅ Phase 3生产环境配置已保存到: {file_path}")

    @classmethod
    def load_config(cls, file_path: str = None) -> 'Phase3ProductionConfig':
        """从文件加载配置"""
        if file_path is None:
            file_path = Path(__file__).parent / "config" / "phase3_production_config.json"

        import json
        with open(file_path, encoding='utf-8') as f:
            config_data = json.load(f)

        config = cls(Environment(config_data["environment"]))

        # 更新配置数据
        for key, value in config_data.items():
            if key != "environment" and hasattr(config, key):
                if isinstance(value, dict):
                    getattr(config, key).__dict__.update(value)

        return config

# 全局配置实例
_production_config = None

def get_production_config(environment: Environment = Environment.PRODUCTION) -> Phase3ProductionConfig:
    """获取生产环境配置实例"""
    global _production_config
    if _production_config is None:
        _production_config = Phase3ProductionConfig(environment)
    return _production_config

def reload_production_config(environment: Environment = Environment.PRODUCTION) -> Phase3ProductionConfig:
    """重新加载生产环境配置"""
    global _production_config
    _production_config = Phase3ProductionConfig(environment)
    return _production_config

# 命令行工具
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Athena Phase 3生产环境配置工具")
    parser.add_argument("--env", choices=["development", "testing", "production", "staging"],
                       default="production", help="环境类型")
    parser.add_argument("--save", action="store_true", help="保存配置到文件")
    parser.add_argument("--show", action="store_true", help="显示配置信息")

    args = parser.parse_args()

    env = Environment(args.env)
    config = get_production_config(env)

    if args.save:
        config.save_config()

    if args.show:
        import json
        print(json.dumps(config.to_dict(), indent=2, ensure_ascii=False))
