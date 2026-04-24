"""
兼容适配层 - 向后兼容的适配器

提供3个原有注册表的兼容接口，重定向到统一注册中心。
"""

from core.registry_center.adapters.agent_collaboration_adapter import AgentRegistry as AgentCollaborationRegistry
from core.registry_center.adapters.framework_adapter import AgentRegistry as FrameworkAgentRegistry
from core.registry_center.adapters.subagent_adapter import SubagentRegistry

__all__ = [
    "AgentCollaborationRegistry",
    "FrameworkAgentRegistry",
    "SubagentRegistry",
]
