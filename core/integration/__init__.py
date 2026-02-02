"""
integration - 系统集成模块

提供各个模块之间的集成功能:
1. 规划引擎网关集成
2. MCP工具集成
3. LLM能力集成

作者: 小诺·双鱼座
版本: v1.0.0
"""

from .planning_gateway_integration import (
    PlanningGatewayIntegration,
    get_planning_gateway_integration,
)

__all__ = ["PlanningGatewayIntegration", "get_planning_gateway_integration"]

__version__ = "1.0.0"
__author__ = "小诺·双鱼座"
