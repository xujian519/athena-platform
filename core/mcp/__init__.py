"""
mcp - MCP标准集成模块

遵循Anthropic MCP标准,实现:
1. MCP服务器 - 将Athena能力暴露为标准工具和资源
2. MCP客户端 - 连接并使用MCP服务器
3. 工具调用器 - 便捷的工具调用接口
4. MCP服务集成 - MCP服务注册、发现和监控
5. 深度MCP集成 - 有状态/无状态客户端管理 (Phase 1)

主要组件:
- AthenaMCPServer: MCP服务器
- AthenaMCPClient: 遗留MCP客户端
- MCPToolInvoker: 工具调用器
- MCPServiceRegistry: MCP服务注册中心
- MCPClientManager: MCP客户端管理器 (Phase 1)
- StatefulMCPClient: 有状态MCP客户端 (Phase 1)
- StatelessMCPClient: 无状态MCP客户端 (Phase 1)

作者: 小诺·双鱼座, Athena平台团队
版本: v1.1.0 "Phase 1"
"""

from .mcp_client_manager import (
    ClientConfig,
    ClientInfo,
    ClientStatus,
    ClientType,
    MCPClientManager,
    get_client_manager,
)
from .mcp_integration import (
    MCPCallMetrics,
    MCPRetryPolicy,
    MCPServiceInfo,
    MCPServiceRegistry,
    MCPServiceStatus,
)

__all__ = [
    # 客户端
    "AthenaMCPClient",
    "ClientConfig",
    "ClientInfo",
    "ClientStatus",
    # ========== Phase 1: 深度MCP集成 ==========
    # 客户端管理器
    "ClientType",
    # 无状态客户端
    "ConnectionTimeoutError",
    "MCPCallMetrics",
    "MCPClientManager",
    "MCPRetryPolicy",
    "MCPServiceInfo",
    "MCPServiceRegistry",
    # MCP服务集成
    "MCPServiceStatus",
    "MCPToolInvoker",
    # 有状态客户端
    "SessionTimeoutError",
    "StatefulMCPClient",
    "StatelessMCPClient",
    # ========== 遗留组件 ==========
    # 服务器
    "athena_mcp_server_app",
    "get_client_manager",
    # 便捷函数
    "get_mcp_client",
    "get_mcp_invoker",
]

__version__ = "1.1.0"
__author__ = "小诺·双鱼座, Athena平台团队"
