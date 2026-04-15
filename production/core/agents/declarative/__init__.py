"""
声明式 Agent 定义系统

借鉴 kode-agent 的声明式 Agent 设计模式，允许通过 Markdown + YAML frontmatter
定义 Agent，无需编写 Python 代码。

核心模块：
- models: 数据模型（AgentDefinition, AgentSource, AgentPermissionMode）
- loader: 文件加载器（AgentLoader）
- proxy: Agent 代理（DeclarativeAgent，适配 BaseAgent）
- permissions: 工具权限过滤（ToolPermissionFilter）
- output_styles: 输出风格系统（OutputStyleLoader, OutputStyleDefinition）

使用示例：
    from core.agents.declarative import load_all_agents, DeclarativeAgent

    # 加载所有声明式 Agent
    agents = load_all_agents()

    # 获取特定 Agent 定义
    definition = agents["explorer"]

    # 创建 Agent 实例
    agent_cls = DeclarativeAgent.from_definition(definition)
    agent = agent_cls()

Author: Athena Team
"""

from __future__ import annotations
from .loader import AgentLoader, get_agent, get_loader, load_all_agents
from .models import AgentDefinition, AgentPermissionMode, AgentSource
from .output_styles import (
    OutputStyleDefinition,
    OutputStyleLoader,
    get_available_styles,
    get_style,
    get_style_prompt,
)
from .permissions import ToolPermissionFilter
from .proxy import DeclarativeAgent

__all__ = [
    # 数据模型
    "AgentDefinition",
    "AgentSource",
    "AgentPermissionMode",
    # 加载器
    "AgentLoader",
    "load_all_agents",
    "get_agent",
    "get_loader",
    # 权限
    "ToolPermissionFilter",
    # 代理
    "DeclarativeAgent",
    # 输出风格
    "OutputStyleDefinition",
    "OutputStyleLoader",
    "get_available_styles",
    "get_style",
    "get_style_prompt",
]
