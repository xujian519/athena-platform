#!/usr/bin/env python3
"""
兼容层: 旧base_module的迁移桥接

此模块提供向后兼容的导入，但会发出deprecation警告。
请使用新的core/agents/架构。
"""

from __future__ import annotations
import warnings

# 发出deprecation警告
warnings.warn(
    "core.base_module已废弃，请迁移到core.agents架构",
    DeprecationWarning,
    stacklevel=2
)

# 尝试从legacy目录导入
try:
    from core.legacy.base_module import *  # noqa: F401, F403
except ImportError:
    raise ImportError(
        "core.base_module已被移除。"
        "请使用新的core.agents架构:\n"
        "  from core.agents.base import BaseAgent"
    ) from None
