#!/usr/bin/env python3
"""
生产环境配置
Production Configuration for Athena Platform

包含反思引擎和评估引擎的生产环境配置
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ReflectionConfig:
    """反思引擎配置"""

    # 最大反思迭代次数
    max_refinement_attempts: int = 3

    # 质量阈值
    quality_thresholds: dict[str, float] = field(default_factory=lambda: {
        "excellent": 0.9,
        "good": 0.75,
        "acceptable": 0.6,
        "poor": 0.4,
    })

    # 历史记录大小限制
    max_history_size: int = 1000

    # 是否启用LLM集成
    enable_llm_integration: bool = True

    # 是否启用人工审查
    enable_human_review: bool = True

    # 人工审查阈值
    human_review_threshold: float = 0.8

    # 缓存配置
    enable_cache: bool = True
    cache_ttl: int = 3600  # 秒

    # 日志配置
    enable_detailed_logging: bool = True

    # 性能配置
    enable_parallel_evaluation: bool = True
    max_parallel_workers: int = 4


@dataclass
class EvaluationConfig:
    """评估引擎配置"""

    # 安全性评估配置
    security_checks: list[str] = field(default_factory=lambda: [
        "data_protection",
        "vulnerability_management",
        "authentication",
        "compliance",
    ])

    # 可靠性评估配置
    reliability_metrics: list[str] = field(default_factory=lambda: [
        "availability",
        "mtbf",
        "mttr",
        "error_rate",
        "recovery",
    ])

    # 用户体验评估配置
    ux_metrics: list[str] = field(default_factory=lambda: [
        "usability",
        "performance",
        "satisfaction",
        "accessibility",
        "engagement",
    ])

    # 风险阈值
    risk_thresholds: dict[str, float] = field(default_factory=lambda: {
        "critical": 0.6,
        "high": 0.4,
        "medium": 0.2,
        "low": 0.0,
    })

    # 历史记录大小限制
    max_history_size: int = 1000

    # 是否启用基准对比
    enable_benchmarking: bool = True

    # 基准数据文件路径
    benchmark_data_path: str = "data/benchmarks/"

    # 是否启用趋势分析
    enable_trend_analysis: bool = True

    # 趋势分析窗口大小
    trend_window_size: int = 30


@dataclass
class ProductionConfig:
    """生产环境总配置"""

    # 环境标识
    environment: str = "production"

    # 项目根目录
    project_root: Path = field(default_factory=lambda: Path("/Users/xujian/Athena工作平台"))

    # 反思引擎配置
    reflection: ReflectionConfig = field(default_factory=ReflectionConfig)

    # 评估引擎配置
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)

    # 数据存储配置
    data_dir: Path = field(default_factory=lambda: Path("data/production"))

    # 日志配置
    log_level: str = "INFO"
    log_dir: Path = field(default_factory=lambda: Path("logs/production"))

    # 监控配置
    enable_monitoring: bool = True
    metrics_port: int = 9090

    # 健康检查配置
    health_check_interval: int = 30  # 秒

    # 数据库配置
    database_url: str = "postgresql://user:password@localhost:5432/athena"

    # Redis配置
    redis_url: str = "redis://localhost:6379/0"

    def __post_init__(self):
        """初始化后处理"""
        # 确保数据目录存在
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)


# 默认生产配置
DEFAULT_PRODUCTION_CONFIG = ProductionConfig()


def get_production_config() -> ProductionConfig:
    """获取生产环境配置"""
    return DEFAULT_PRODUCTION_CONFIG


def load_config_from_file(config_path: str) -> ProductionConfig:
    """从文件加载配置"""
    import json

    config_file = Path(config_path)
    if config_file.exists():
        with open(config_file, encoding="utf-8") as f:
            config_data = json.load(f)
            # 这里可以添加更复杂的配置加载逻辑
            return ProductionConfig(**config_data)
    return DEFAULT_PRODUCTION_CONFIG


__all__ = [
    "ReflectionConfig",
    "EvaluationConfig",
    "ProductionConfig",
    "DEFAULT_PRODUCTION_CONFIG",
    "get_production_config",
    "load_config_from_file",
]
