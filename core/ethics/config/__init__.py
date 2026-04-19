from __future__ import annotations
"""
伦理框架配置模块
Ethics Framework Configuration Module
"""

from .config_loader import (
    ConfigLoader,
    EthicsConfig,
    get_config_loader,
    get_harmful_keywords,
    get_prohibited_claims,
    get_sensitive_fields,
    load_ethics_config,
)

__all__ = [
    "ConfigLoader",
    "EthicsConfig",
    "get_config_loader",
    "get_harmful_keywords",
    "get_prohibited_claims",
    "get_sensitive_fields",
    "load_ethics_config",
]
