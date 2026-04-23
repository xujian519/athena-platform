"""
Agent适配器模块

将不同类型的Agent转换为统一的可调用接口，支持注册到FunctionCallingSystem。

Author: Athena平台团队
创建时间: 2026-04-21
"""

from .agent_adapter import AgentAdapter
from .proxy_adapter import ProxyAgentAdapter
from .registry import AgentToolRegistry

__all__ = [
    "AgentAdapter",
    "ProxyAgentAdapter",
    "AgentToolRegistry",
]
