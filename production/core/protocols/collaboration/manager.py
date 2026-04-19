from __future__ import annotations
"""
协作协议 - 管理器
Collaboration Protocols - Manager

作者: Athena AI系统
创建时间: 2025-12-04
重构时间: 2026-01-26
版本: 2.1.0

该模块提供协作协议的管理功能，包括协议的注册、启动、停止和消息路由。
"""

import logging
import uuid
from typing import Any

from .base import BaseProtocol
from .protocols.communication import CommunicationProtocol
from .protocols.coordination import CoordinationProtocol
from .protocols.decision import DecisionProtocol
from .types import ProtocolMessage

logger = logging.getLogger(__name__)


class ProtocolManager:
    """协议管理器 - 管理所有协作协议"""

    def __init__(self):
        self.protocols: dict[str, BaseProtocol] = {}
        self.protocol_templates: dict[str, dict[str, Any]] = {}
        self.active_sessions: dict[str, dict[str, Any]] = {}
        self.message_router: dict[str, list[str]] = {}  # protocol_id -> participants

    def register_protocol(self, protocol: BaseProtocol) -> bool:
        """注册协议"""
        try:
            self.protocols[protocol.protocol_id] = protocol
            self.message_router[protocol.protocol_id] = (
                protocol.context.participants.copy()
            )
            logger.info(f"协议 {protocol.protocol_id} 注册成功")
            return True
        except Exception as e:
            logger.error(f"注册协议失败: {e}")
            return False

    def unregister_protocol(self, protocol_id: str) -> bool:
        """注销协议"""
        try:
            if protocol_id in self.protocols:
                protocol = self.protocols[protocol_id]
                protocol.stop()
                del self.protocols[protocol_id]

                if protocol_id in self.message_router:
                    del self.message_router[protocol_id]

                logger.info(f"协议 {protocol_id} 注销成功")
                return True
            return False
        except Exception as e:
            logger.error(f"注销协议失败: {e}")
            return False

    async def start_protocol(self, protocol_id: str) -> bool:
        """启动协议"""
        try:
            protocol = self.protocols.get(protocol_id)
            if protocol:
                return await protocol.start()
            return False
        except Exception as e:
            logger.error(f"启动协议失败: {e}")
            return False

    async def stop_protocol(self, protocol_id: str) -> bool:
        """停止协议"""
        try:
            protocol = self.protocols.get(protocol_id)
            if protocol:
                protocol.stop()
                return True
            return False
        except Exception as e:
            logger.error(f"停止协议失败: {e}")
            return False

    def get_protocol_status(self, protocol_id: str) -> dict[str, Any] | None:
        """获取协议状态"""
        try:
            protocol = self.protocols.get(protocol_id)
            if protocol:
                return protocol.get_protocol_info()
            return None
        except Exception as e:
            logger.error(f"获取协议状态失败: {e}")
            return None

    def get_all_protocols_status(self) -> dict[str, dict[str, Any]]:
        """获取所有协议状态"""
        status = {}
        for protocol_id in self.protocols:
            protocol_status = self.get_protocol_status(protocol_id)
            if protocol_status:
                status[protocol_id] = protocol_status
        return status

    def route_message(self, message: ProtocolMessage) -> bool:
        """路由消息到相应协议"""
        try:
            protocol_id = message.protocol_id
            protocol = self.protocols.get(protocol_id)

            if protocol:
                return protocol.receive_message(message)
            else:
                logger.warning(f"未找到协议 {protocol_id}")
                return False
        except Exception as e:
            logger.error(f"路由消息失败: {e}")
            return False

    def create_communication_protocol(self, participants: list[str]) -> str:
        """创建通信协议"""
        protocol_id = f"comm_{str(uuid.uuid4())[:8]}"
        protocol = CommunicationProtocol(protocol_id)

        for participant in participants:
            protocol.add_participant(participant)

        self.register_protocol(protocol)
        return protocol_id

    def create_coordination_protocol(self, participants: list[str]) -> str:
        """创建协调协议"""
        protocol_id = f"coord_{str(uuid.uuid4())[:8]}"
        protocol = CoordinationProtocol(protocol_id)

        for participant in participants:
            protocol.add_participant(participant)

        self.register_protocol(protocol)
        return protocol_id

    def create_decision_protocol(self, participants: list[str]) -> str:
        """创建决策协议"""
        protocol_id = f"decision_{str(uuid.uuid4())[:8]}"
        protocol = DecisionProtocol(protocol_id)

        for participant in participants:
            protocol.add_participant(participant)

        self.register_protocol(protocol)
        return protocol_id

    async def shutdown_all_protocols(self) -> None:
        """关闭所有协议"""
        for protocol_id in list(self.protocols.keys()):
            await self.stop_protocol(protocol_id)
            self.unregister_protocol(protocol_id)

        logger.info("所有协议已关闭")


# 全局协议管理器实例
protocol_manager = ProtocolManager()
