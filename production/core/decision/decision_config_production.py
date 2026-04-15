#!/usr/bin/env python3
"""
生产环境决策服务配置
Production Decision Service Configuration
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass
class DecisionEngineConfig:
    """决策引擎配置"""
    # 规则引擎
    rule_engine_enabled: bool = True
    rule_engine_weight: float = 0.4

    # ML引擎
    ml_engine_enabled: bool = True
    ml_engine_weight: float = 0.3
    ml_model_path: str = "models/decision_ml/"

    # RL引擎
    rl_engine_enabled: bool = True
    rl_engine_weight: float = 0.3
    rl_learning_rate: float = 0.1
    rl_discount_factor: float = 0.95
    rl_exploration_rate: float = 0.2

    # 集成投票
    ensemble_voting_enabled: bool = True


@dataclass
class DecisionCacheConfig:
    """决策缓存配置"""
    enabled: bool = True
    ttl_seconds: int = 300
    max_size: int = 10000
    eviction_policy: str = "lru"  # lru, lfu, fifo


@dataclass
class DecisionMonitoringConfig:
    """决策监控配置"""
    enabled: bool = True
    metrics_interval_seconds: int = 60
    alert_threshold_confidence: float = 0.5
    alert_threshold_latency_ms: float = 5000.0
    log_decisions: bool = True
    log_level: str = "INFO"


@dataclass
class DecisionFeedbackConfig:
    """决策反馈配置"""
    enabled: bool = True
    auto_learn: bool = True
    feedback_window_hours: int = 24
    min_feedback_samples: int = 10


@dataclass
class ProductionDecisionConfig:
    """生产环境决策服务完整配置"""
    engine: DecisionEngineConfig = None
    cache: DecisionCacheConfig = None
    monitoring: DecisionMonitoringConfig = None
    feedback: DecisionFeedbackConfig = None

    def __post_init__(self):
        if self.engine is None:
            self.engine = DecisionEngineConfig()
        if self.cache is None:
            self.cache = DecisionCacheConfig()
        if self.monitoring is None:
            self.monitoring = DecisionMonitoringConfig()
        if self.feedback is None:
            self.feedback = DecisionFeedbackConfig()

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "engine": {
                "rule_engine_enabled": self.engine.rule_engine_enabled,
                "rule_engine_weight": self.engine.rule_engine_weight,
                "ml_engine_enabled": self.engine.ml_engine_enabled,
                "ml_engine_weight": self.engine.ml_engine_weight,
                "rl_engine_enabled": self.engine.rl_engine_enabled,
                "rl_engine_weight": self.engine.rl_engine_weight,
                "rl_learning_rate": self.engine.rl_learning_rate,
                "rl_discount_factor": self.engine.rl_discount_factor,
                "rl_exploration_rate": self.engine.rl_exploration_rate,
                "ensemble_voting_enabled": self.engine.ensemble_voting_enabled,
            },
            "cache": {
                "enabled": self.cache.enabled,
                "ttl_seconds": self.cache.ttl_seconds,
                "max_size": self.cache.max_size,
                "eviction_policy": self.cache.eviction_policy,
            },
            "monitoring": {
                "enabled": self.monitoring.enabled,
                "metrics_interval_seconds": self.monitoring.metrics_interval_seconds,
                "alert_threshold_confidence": self.monitoring.alert_threshold_confidence,
                "alert_threshold_latency_ms": self.monitoring.alert_threshold_latency_ms,
                "log_decisions": self.monitoring.log_decisions,
                "log_level": self.monitoring.log_level,
            },
            "feedback": {
                "enabled": self.feedback.enabled,
                "auto_learn": self.feedback.auto_learn,
                "feedback_window_hours": self.feedback.feedback_window_hours,
                "min_feedback_samples": self.feedback.min_feedback_samples,
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProductionDecisionConfig":
        """从字典创建"""
        engine_data = data.get("engine", {})
        cache_data = data.get("cache", {})
        monitoring_data = data.get("monitoring", {})
        feedback_data = data.get("feedback", {})

        return cls(
            engine=DecisionEngineConfig(
                rule_engine_enabled=engine_data.get("rule_engine_enabled", True),
                rule_engine_weight=engine_data.get("rule_engine_weight", 0.4),
                ml_engine_enabled=engine_data.get("ml_engine_enabled", True),
                ml_engine_weight=engine_data.get("ml_engine_weight", 0.3),
                rl_engine_enabled=engine_data.get("rl_engine_enabled", True),
                rl_engine_weight=engine_data.get("rl_engine_weight", 0.3),
                rl_learning_rate=engine_data.get("rl_learning_rate", 0.1),
                rl_discount_factor=engine_data.get("rl_discount_factor", 0.95),
                rl_exploration_rate=engine_data.get("rl_exploration_rate", 0.2),
                ensemble_voting_enabled=engine_data.get("ensemble_voting_enabled", True),
            ),
            cache=DecisionCacheConfig(
                enabled=cache_data.get("enabled", True),
                ttl_seconds=cache_data.get("ttl_seconds", 300),
                max_size=cache_data.get("max_size", 10000),
                eviction_policy=cache_data.get("eviction_policy", "lru"),
            ),
            monitoring=DecisionMonitoringConfig(
                enabled=monitoring_data.get("enabled", True),
                metrics_interval_seconds=monitoring_data.get("metrics_interval_seconds", 60),
                alert_threshold_confidence=monitoring_data.get("alert_threshold_confidence", 0.5),
                alert_threshold_latency_ms=monitoring_data.get("alert_threshold_latency_ms", 5000.0),
                log_decisions=monitoring_data.get("log_decisions", True),
                log_level=monitoring_data.get("log_level", "INFO"),
            ),
            feedback=DecisionFeedbackConfig(
                enabled=feedback_data.get("enabled", True),
                auto_learn=feedback_data.get("auto_learn", True),
                feedback_window_hours=feedback_data.get("feedback_window_hours", 24),
                min_feedback_samples=feedback_data.get("min_feedback_samples", 10),
            ),
        )


# 默认生产环境配置
DEFAULT_PRODUCTION_CONFIG = ProductionDecisionConfig()


def get_production_config() -> ProductionDecisionConfig:
    """获取生产环境配置"""
    return DEFAULT_PRODUCTION_CONFIG
