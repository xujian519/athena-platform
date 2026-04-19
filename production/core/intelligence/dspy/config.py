"""
DSPy配置管理
DSPy Configuration Management for Athena Platform
"""

from __future__ import annotations
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class DSPyConfig:
    """DSPy配置类"""

    # LLM配置
    primary_model: str = "glm-4-plus"
    fallback_model: str = "deepseek-chat"
    temperature: float = 0.7
    max_tokens: int = 4096

    # 优化器配置
    optimizer_type: str = "MIPROv2"  # MIPROv2, BootstrapFewShot, etc.
    max_bootstrapped_demos: int = 3
    max_labeled_demos: int = 5
    max_rounds: int = 3

    # 缓存配置
    enable_cache: bool = True
    cache_dir: Path = field(default_factory=lambda: Path("/Users/xujian/Athena工作平台/cache/dspy"))

    # 调试配置
    debug_mode: bool = False
    log_level: str = "INFO"

    # 集成配置
    enable_vector_retrieval: bool = True
    enable_graph_retrieval: bool = True
    enable_tool_integration: bool = True

    # 人格保护配置
    enable_persona_protection: bool = True
    persona_drift_threshold: float = 0.2  # 20%漂移阈值

    # 回滚配置
    enable_auto_rollback: bool = True
    rollback_on_quality_degradation: bool = True

    @classmethod
    def from_env(cls) -> "DSPyConfig":
        """从环境变量加载配置"""
        return cls(
            primary_model=os.getenv("DSPY_PRIMARY_MODEL", "glm-4-plus"),
            fallback_model=os.getenv("DSPY_FALLBACK_MODEL", "deepseek-chat"),
            temperature=float(os.getenv("DSPY_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("DSPY_MAX_TOKENS", "4096")),
            optimizer_type=os.getenv("DSPY_OPTIMIZER", "MIPROv2"),
            debug_mode=os.getenv("DSPY_DEBUG", "false").lower() == "true",
        )

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "primary_model": self.primary_model,
            "fallback_model": self.fallback_model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "optimizer_type": self.optimizer_type,
            "max_bootstrapped_demos": self.max_bootstrapped_demos,
            "max_labeled_demos": self.max_labeled_demos,
            "max_rounds": self.max_rounds,
            "enable_cache": self.enable_cache,
            "enable_vector_retrieval": self.enable_vector_retrieval,
            "enable_graph_retrieval": self.enable_graph_retrieval,
            "enable_tool_integration": self.enable_tool_integration,
            "enable_persona_protection": self.enable_persona_protection,
            "persona_drift_threshold": self.persona_drift_threshold,
            "enable_auto_rollback": self.enable_auto_rollback,
        }


# 全局配置实例
_config: DSPyConfig | None = None


def get_config() -> DSPyConfig:
    """获取全局DSPy配置"""
    global _config
    if _config is None:
        _config = DSPyConfig.from_env()
    return _config


def configure_dspy(config: DSPyConfig | None = None) -> DSPyConfig:
    """配置DSPy

    Args:
        config: DSPy配置对象,如果为None则使用默认配置

    Returns:
        配置后的DSPyConfig对象
    """
    global _config
    _config = config or DSPyConfig.from_env()

    # 创建缓存目录
    _config.cache_dir.mkdir(parents=True, exist_ok=True)

    return _config
