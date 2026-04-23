"""
Athena Gateway WebSocket Agent适配器

提供Python Agent与Gateway的WebSocket通信能力。
"""
from .client import (
    AgentType,
    ErrorResponse,
    Message,
    MessageType,
    ProgressUpdate,
    TaskRequest,
    WebSocketClient,
    create_client,
)
from .xiaonuo_adapter import (
    XiaonuoAgentAdapter,
    YunxiAgentAdapter,
    create_xiaonuo_agent,
    create_yunxi_agent,
)

__all__ = [
    # 客户端
    "WebSocketClient",
    "create_client",

    # 消息类型
    "Message",
    "MessageType",
    "AgentType",
    "TaskRequest",
    "ProgressUpdate",
    "ErrorResponse",

    # Agent适配器
    "BaseAgentAdapter",
    "XiaonaAgentAdapter",
    "XiaonuoAgentAdapter",
    "YunxiAgentAdapter",

    # 便捷函数
    "create_xiaona_agent",
    "create_xiaonuo_agent",
    "create_yunxi_agent",
]


__version__ = "1.0.0"
__author__ = "Athena Platform Team"

