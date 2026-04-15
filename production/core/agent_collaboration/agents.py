#!/usr/bin/env python3
"""
专业化Agent实现 - 向后兼容重定向
Specialized Agents Implementation - Backward Compatibility Redirect

⚠️  此文件已重构，所有功能已迁移到新位置

新位置: core.agent_collaboration.specialized_agents

作者: Athena AI系统
创建时间: 2025-12-04
重构时间: 2026-01-26
版本: 2.1.0-refactored

--- 迁移指南 ---

旧导入:
  from core.agent_collaboration.agents import SearchAgent

新导入:
  from core.agent_collaboration.specialized_agents import SearchAgent
  # 或
  from core.agent_collaboration.specialized_agents.search_agent import SearchAgent

--- 文件结构 ---

core/agent_collaboration/specialized_agents/
├── __init__.py              # 公共接口导出
├── search_agent.py          # 搜索Agent (707行)
├── analysis_agent.py        # 分析Agent (613行)
└── creative_agent.py        # 创意Agent (432行)

总计: ~1771行 (原文件: 1634行)

--- 使用示例 ---

# 推荐导入方式
from core.agent_collaboration.specialized_agents import (
    SearchAgent,
    AnalysisAgent,
    CreativeAgent,
)

"""

from __future__ import annotations
import logging
import warnings

logger = logging.getLogger(__name__)

# 向后兼容重定向
from core.agent_collaboration.specialized_agents import (  # type: ignore
    AnalysisAgent,
    CreativeAgent,
    SearchAgent,
)

# 发出迁移警告
warnings.warn(
    "agents.py 已重构，请使用新导入路径: "
    "from core.agent_collaboration.specialized_agents import SearchAgent",
    DeprecationWarning,
    stacklevel=2,
)

logger.info("⚠️  使用已重构的agents.py，建议更新导入路径")

# 导出所有公共接口以保持向后兼容
__all__ = [
    "SearchAgent",
    "AnalysisAgent",
    "CreativeAgent",
]
