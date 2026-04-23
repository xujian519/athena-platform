#!/usr/bin/env python3
from __future__ import annotations
"""
兼容层: 旧base_agent_with_memory的迁移桥接

此模块提供向后兼容的导入，但会发出deprecation警告。
请使用新的core/agents/架构。

迁移指南:
- 旧: from core.base_agent_with_memory import MemoryEnabledAgent
- 新: from core.agents.base import BaseAgent
"""

import warnings

# 发出deprecation警告
warnings.warn(
    "core.base_agent_with_memory已废弃，请迁移到core.agents架构",
    DeprecationWarning,
    stacklevel=2
)

# 尝试从legacy目录导入
try:
    from core.legacy.base_agent_with_memory import *  # noqa: F401, F403
except ImportError:
    # 如果legacy不存在，说明文件已被完全移除
    raise ImportError(
        "core.base_agent_with_memory已被移除。"
        "请使用新的core.agents架构:\n"
        "  from core.agents.base import BaseAgent\n"
        "  from core.agents.xiaona_legal import XiaonaLegalAgent\n"
        "  # 替换为: from core.agents.xiaonuo.xiaonuo_agent_v2 import XiaonuoAgentV2 as XiaonuoAgent\n"
        "  from core.agents.athena_advisor import AthenaAdvisorAgent"
    ) from None
