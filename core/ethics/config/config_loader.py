"""
伦理框架配置加载器
Ethics Framework Configuration Loader

从YAML文件加载伦理框架配置
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml


@dataclass
class EthicsConfig:
    """伦理框架配置"""

    # 评估器配置
    max_history_size: int = 1000
    default_confidence_threshold: float = 0.7

    # 约束执行配置
    auto_block_critical: bool = True
    auto_negotiate_uncertain: bool = True
    auto_escalate_high_severity: bool = True

    # 监控配置
    alert_threshold_violation_rate: float = 0.1
    alert_threshold_critical: int = 3
    window_size: int = 100

    # 敏感信息过滤配置
    sensitive_fields: set[str] = field(default_factory=set)
    sensitive_patterns: list[dict[str, Any]] = field(default_factory=list)
    filter_enabled: bool = True

    # AI身份诚实配置
    prohibited_claims: list[str] = field(default_factory=list)

    # 无害原则配置
    harmful_keywords: list[str] = field(default_factory=list)
    harmful_patterns: list[dict[str, Any]] = field(default_factory=list)

    # Prometheus配置
    prometheus_port: int = 9091
    prometheus_enable_endpoint: bool = True
    prometheus_duration_buckets: list[float] = field(default_factory=list)

    # 维特根斯坦守护配置
    global_confidence_threshold: float = 0.7
    default_uncertainty_strategy: str = "negotiate"
    language_games_config: dict[str, dict[str, Any]] = field(default_factory=dict)


class ConfigLoader:
    """配置加载器"""

    # 默认配置路径
    DEFAULT_CONFIG_PATH = Path(__file__).parent / "ethics_config.yaml"

    # 环境变量名
    CONFIG_ENV_VAR = "ETHICS_CONFIG_PATH"

    def __init__(self, config_path: Path | None = None):
        """初始化配置加载器

        Args:
            config_path: 配置文件路径,如果为None则使用默认路径
        """
        if config_path is None:
            # 优先使用环境变量
            env_path = os.getenv(self.CONFIG_ENV_VAR)
            config_path = Path(env_path) if env_path else self.DEFAULT_CONFIG_PATH

        self.config_path = config_path
        self._config: EthicsConfig | None = None

    def load_config(self) -> EthicsConfig:
        """加载配置文件

        Returns:
            伦理框架配置

        Raises:
            FileNotFoundError: 配置文件不存在
            yaml.YAMLError: YAML解析错误
        """
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"配置文件不存在: {self.config_path}\n"
                f"请检查路径或设置环境变量 {self.CONFIG_ENV_VAR}"
            )

        with open(self.config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return self._parse_config(data)

    def _parse_config(self, data: dict[str, Any]) -> EthicsConfig:
        """解析配置数据

        Args:
            data: YAML加载的字典数据

        Returns:
            伦理框架配置
        """
        # 获取各部分配置
        ethics_config = data.get("ethics", {})
        evaluator_config = ethics_config.get("evaluator", {})
        constraints_config = ethics_config.get("constraints", {})
        monitoring_config = ethics_config.get("monitoring", {})

        # 敏感信息过滤配置
        filter_config = data.get("sensitive_data_filter", {})
        sensitive_fields = set(filter_config.get("sensitive_fields", []))
        sensitive_patterns = filter_config.get("patterns", [])

        # AI身份诚实配置
        identity_config = data.get("ai_identity_honesty", {})
        prohibited_claims = identity_config.get("prohibited_claims", [])

        # 无害原则配置
        harmless_config = data.get("harmless_principle", {})
        harmful_keywords = harmless_config.get("harmful_keywords", [])
        harmful_patterns = harmless_config.get("harmful_patterns", [])

        # Prometheus配置
        prometheus_config = data.get("prometheus", {})
        duration_buckets = prometheus_config.get("duration_buckets", [])

        # 维特根斯坦守护配置
        guard_config = data.get("wittgenstein_guard", {})
        language_games_config = guard_config.get("language_games", {})

        return EthicsConfig(
            # 评估器配置
            max_history_size=evaluator_config.get("max_history_size", 1000),
            default_confidence_threshold=evaluator_config.get("default_confidence_threshold", 0.7),
            # 约束执行配置
            auto_block_critical=constraints_config.get("auto_block_critical", True),
            auto_negotiate_uncertain=constraints_config.get("auto_negotiate_uncertain", True),
            auto_escalate_high_severity=constraints_config.get("auto_escalate_high_severity", True),
            # 监控配置
            alert_threshold_violation_rate=monitoring_config.get(
                "alert_threshold_violation_rate", 0.1
            ),
            alert_threshold_critical=monitoring_config.get("alert_threshold_critical", 3),
            window_size=monitoring_config.get("window_size", 100),
            # 敏感信息过滤配置
            sensitive_fields=sensitive_fields,
            sensitive_patterns=sensitive_patterns,
            filter_enabled=filter_config.get("enabled", True),
            # AI身份诚实配置
            prohibited_claims=prohibited_claims,
            # 无害原则配置
            harmful_keywords=harmful_keywords,
            harmful_patterns=harmful_patterns,
            # Prometheus配置
            prometheus_port=prometheus_config.get("port", 9091),
            prometheus_enable_endpoint=prometheus_config.get("enable_endpoint", True),
            prometheus_duration_buckets=duration_buckets,
            # 维特根斯坦守护配置
            global_confidence_threshold=guard_config.get("global_confidence_threshold", 0.7),
            default_uncertainty_strategy=guard_config.get(
                "default_uncertainty_strategy", "negotiate"
            ),
            language_games_config=language_games_config,
        )

    @property
    def config(self) -> EthicsConfig:
        """获取配置(懒加载)"""
        if self._config is None:
            self._config = self.load_config()
        return self._config

    def reload(self) -> EthicsConfig:
        """重新加载配置"""
        self._config = None
        return self.config


# 全局配置加载器实例
_global_config_loader: ConfigLoader | None = None


def get_config_loader(config_path: Path | None = None) -> ConfigLoader:
    """获取全局配置加载器

    Args:
        config_path: 可选的配置文件路径

    Returns:
        配置加载器实例
    """
    global _global_config_loader
    if _global_config_loader is None or config_path is not None:
        _global_config_loader = ConfigLoader(config_path)
    return _global_config_loader


def load_ethics_config(config_path: Path | None = None) -> EthicsConfig:
    """加载伦理框架配置(便捷函数)

    Args:
        config_path: 可选的配置文件路径

    Returns:
        伦理框架配置
    """
    loader = get_config_loader(config_path)
    return loader.config


def get_prohibited_claims() -> list[str]:
    """获取禁止的声称列表(便捷函数)

    Returns:
        禁止的声称列表
    """
    config = load_ethics_config()
    return config.prohibited_claims


def get_harmful_keywords() -> list[str]:
    """获取有害关键词列表(便捷函数)

    Returns:
        有害关键词列表
    """
    config = load_ethics_config()
    return config.harmful_keywords


def get_sensitive_fields() -> set[str]:
    """获取敏感字段名集合(便捷函数)

    Returns:
        敏感字段名集合
    """
    config = load_ethics_config()
    return config.sensitive_fields
