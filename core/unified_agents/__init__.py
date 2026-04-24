"""
统一Agent系统

整合两套Agent架构的最佳实践，提供统一的Agent接口。
支持双接口模式实现向后兼容，可选集成Gateway和记忆系统。

Author: Athena Team
Version: 1.0.0
Date: 2026-04-24
"""

__version__ = "1.0.0"

# 基础类型 - 直接导入避免循环
from core.unified_agents.base import (
    AgentCapability,
    AgentMetadata,
    AgentRequest,
    AgentResponse,
    AgentStatus,
    HealthStatus,
    MessageConverter,
    ResponseMessage,
    SimpleAgentResponse,
    TaskMessage,
    MessageType,
)

# 配置
from core.unified_agents.config import (
    ConfigTemplates,
    UnifiedAgentConfig,
    UnifiedAgentConfigBuilder,
)

# 基类
from core.unified_agents.base_agent import UnifiedBaseAgent

# 适配器
from core.unified_agents.adapters import (
    AdapterFactory,
    LegacyAgentAdapter,
    SimpleAgentAdapter,
)

__all__ = [
    # 版本
    "__version__",
    # 基础类型
    "AgentCapability",
    "AgentMetadata",
    "AgentRequest",
    "AgentResponse",
    "AgentStatus",
    "HealthStatus",
    "MessageConverter",
    "ResponseMessage",
    "SimpleAgentResponse",
    "TaskMessage",
    "MessageType",
    # 配置
    "UnifiedAgentConfig",
    "UnifiedAgentConfigBuilder",
    "ConfigTemplates",
    # 基类
    "UnifiedBaseAgent",
    # 适配器
    "LegacyAgentAdapter",
    "SimpleAgentAdapter",
    "AdapterFactory",
]
