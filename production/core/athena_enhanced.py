#!/usr/bin/env python3
from __future__ import annotations
"""
兼容层: 旧athena_enhanced的迁移桥接

此模块提供向后兼容的导入，但会发出deprecation警告。
请使用新的core/agents/athena_advisor模块。
"""

import warnings

# 发出deprecation警告
warnings.warn(
    "core.athena_enhanced已废弃，请使用core.agents.athena_advisor",
    DeprecationWarning,
    stacklevel=2
)

# 尝试从legacy目录导入
try:
    from core.legacy.athena_enhanced import *  # noqa: F401, F403
except ImportError:
    raise ImportError(
        "core.athena_enhanced已被移除。"
        "请使用新的AthenaAdvisorAgent:\n"
        "  from core.agents.athena_advisor import AthenaAdvisorAgent"
    ) from None
