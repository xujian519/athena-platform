from __future__ import annotations
"""
协作协议 - 工具函数
Collaboration Protocols - Utility Functions

作者: Athena AI系统
创建时间: 2025-12-04
重构时间: 2026-01-26
版本: 2.1.0

该模块提供协作协议的便捷工具函数，简化协议会话的创建和管理。
"""

import logging
from typing import Any

from .manager import protocol_manager

logger = logging.getLogger(__name__)


def create_protocol_session(protocol_type: str, participants: list[str]) -> str | None:
    """创建协议会话的便捷函数

    Args:
        protocol_type: 协议类型 ("communication", "coordination", "decision")
        participants: 参与者列表

    Returns:
        协议ID，如果创建失败则返回None
    """
    if protocol_type == "communication":
        return protocol_manager.create_communication_protocol(participants)
    elif protocol_type == "coordination":
        return protocol_manager.create_coordination_protocol(participants)
    elif protocol_type == "decision":
        return protocol_manager.create_decision_protocol(participants)
    else:
        logger.error(f"未知的协议类型: {protocol_type}")
        return None


async def start_protocol_session(protocol_id: str) -> bool:
    """启动协议会话的便捷函数

    Args:
        protocol_id: 协议ID

    Returns:
        是否启动成功
    """
    return await protocol_manager.start_protocol(protocol_id)


def get_protocol_session_status(protocol_id: str) -> dict[str, Any] | None:
    """获取协议会话状态的便捷函数

    Args:
        protocol_id: 协议ID

    Returns:
        协议状态信息，如果协议不存在则返回None
    """
    return protocol_manager.get_protocol_status(protocol_id)


async def shutdown_protocol_manager() -> None:
    """关闭协议管理器的便捷函数

    关闭所有协议并清理资源。
    """
    await protocol_manager.shutdown_all_protocols()
