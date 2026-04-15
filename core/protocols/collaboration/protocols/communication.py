#!/usr/bin/env python3
from __future__ import annotations
"""
协作协议 - 通信协议实现
Collaboration Protocols - Communication Protocol Implementation

处理智能体间的标准化通信

作者: Athena AI系统
创建时间: 2025-12-04
重构时间: 2026-01-26
版本: 2.1.0
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta

# 从本地模块导入
from core.protocols.collaboration.base import BaseProtocol
from core.protocols.collaboration.types import (
    ProtocolMessage,
    ProtocolPhase,
    ProtocolType,
)

logger = logging.getLogger(__name__)


class CommunicationProtocol(BaseProtocol):
    """通信协议 - 处理智能体间的标准化通信"""

    def __init__(self, protocol_id: str):
        super().__init__(protocol_id, ProtocolType.COMMUNICATION)
        self.communication_rules: dict[str, any] = {}
        self.message_formats: dict[str, dict[str, any]] = {}
        self.communication_channels: dict[str, list[str]] = (
            {}
        )  # channel -> participants

    async def initialize(self) -> bool:
        """初始化通信协议"""
        try:
            # 设置默认通信规则
            self.communication_rules = {
                "require_ack": True,
                "max_message_size": 1024 * 1024,  # 1MB
                "message_retention": timedelta(hours=24),
                "retry_policy": {
                    "max_retries": 3,
                    "backoff_factor": 2,
                    "initial_delay": timedelta(seconds=1),
                },
            }

            # 设置消息格式
            self.message_formats = {
                "request": {
                    "required_fields": ["request_id", "action", "parameters"],
                    "optional_fields": ["priority", "timeout", "metadata"],
                },
                "response": {
                    "required_fields": ["request_id", "status", "result"],
                    "optional_fields": ["error", "metadata"],
                },
                "notification": {
                    "required_fields": ["event_type", "event_data"],
                    "optional_fields": ["severity", "metadata"],
                },
                "heartbeat": {
                    "required_fields": ["agent_id", "timestamp", "status"],
                    "optional_fields": ["metrics", "metadata"],
                },
            }

            # 注册消息处理器
            self.register_message_handler("request", self._handle_request)
            self.register_message_handler("response", self._handle_response)
            self.register_message_handler("notification", self._handle_notification)
            self.register_message_handler("heartbeat", self._handle_heartbeat)

            # 创建默认通信通道
            self.communication_channels["broadcast"] = self.context.participants.copy()
            for participant in self.context.participants:
                self.communication_channels[f"direct_{participant}"] = [participant]

            logger.info(f"通信协议 {self.protocol_id} 初始化完成")
            return True

        except Exception as e:
            logger.error(f"通信协议 {self.protocol_id} 初始化失败: {e}")
            return False

    async def execute(self) -> bool:
        """执行通信协议"""
        try:
            self.context.current_phase = ProtocolPhase.EXECUTION

            # 处理消息队列
            while self.running and self.message_queue:
                message = self.message_queue.pop(0)
                await self._process_message(message)

            # 保持通信活跃
            self.context.current_phase = ProtocolPhase.MONITORING
            await self._maintain_communication()

            return True

        except Exception as e:
            logger.error(f"通信协议 {self.protocol_id} 执行失败: {e}")
            return False

    async def _process_message(self, message: ProtocolMessage) -> None:
        """处理消息"""
        try:
            # 验证消息格式
            if not self._validate_message(message):
                logger.warning(f"消息格式验证失败: {message.message_id}")
                return

            # 路由消息
            if message.receiver_id == "broadcast":
                # 广播消息
                await self._broadcast_message(message)
            else:
                # 点对点消息
                await self._send_direct_message(message)

            # 处理消息
            self.receive_message(message)

        except Exception as e:
            logger.error(f"处理消息失败: {e}")

    def _validate_message(self, message: ProtocolMessage) -> bool:
        """验证消息格式"""
        try:
            format_def = self.message_formats.get(message.message_type)
            if not format_def:
                return False

            # 检查必需字段
            content = message.content
            for field in format_def["required_fields"]:
                if field not in content:
                    return False

            # 检查消息大小
            message_size = len(json.dumps(content, default=str))
            return not message_size > self.communication_rules["max_message_size"]

        except Exception as e:
            logger.error(f"消息格式验证失败: {e}")
            return False

    async def _broadcast_message(self, message: ProtocolMessage) -> None:
        """广播消息"""
        participants = self.communication_channels.get("broadcast", [])
        logger.debug(f"广播消息给 {len(participants)} 个参与者")

    async def _send_direct_message(self, message: ProtocolMessage) -> None:
        """发送直接消息"""
        channel = f"direct_{message.receiver_id}"
        if channel in self.communication_channels:
            logger.debug(f"发送直接消息给 {message.receiver_id}")

    async def _maintain_communication(self) -> None:
        """维护通信"""
        try:
            # 发送心跳消息
            heartbeat_interval = timedelta(seconds=30)
            while self.running:
                await asyncio.sleep(heartbeat_interval.total_seconds())

                # 检查参与者活跃状态
                for participant in self.context.participants:
                    last_heartbeat = self.context.private_states[participant].get(
                        "last_heartbeat"
                    )
                    if (
                        not last_heartbeat
                        or (datetime.now() - last_heartbeat) > heartbeat_interval * 2
                    ):
                        # 参与者可能不活跃
                        self.trigger_event(
                            "participant_inactive",
                            {
                                "participant_id": participant,
                                "last_heartbeat": (
                                    last_heartbeat.isoformat()
                                    if last_heartbeat
                                    else None
                                ),
                            },
                        )

        except Exception as e:
            logger.error(f"维护通信失败: {e}")

    async def _handle_request(self, message: ProtocolMessage) -> None:
        """处理请求消息"""
        # 发送确认
        if message.requires_ack:
            ack_message = ProtocolMessage(
                sender_id="communication_protocol",
                receiver_id=message.sender_id,
                message_type="response",
                content={
                    "request_id": message.content.get("request_id"),
                    "status": "acknowledged",
                    "result": {"message": "Request received"},
                },
            )
            self.send_message(ack_message)

    async def _handle_response(self, message: ProtocolMessage) -> None:
        """处理响应消息"""
        # 更新请求状态
        request_id = message.content.get("request_id")
        if request_id:
            self.update_shared_state(
                f"request_{request_id}_status", message.content.get("status")
            )
            self.update_shared_state(
                f"request_{request_id}_result", message.content.get("result")
            )

    async def _handle_notification(self, message: ProtocolMessage) -> None:
        """处理通知消息"""
        event_type = message.content.get("event_type")
        event_data = message.content.get("event_data")

        if event_type:
            self.trigger_event(event_type, event_data)

    async def _handle_heartbeat(self, message: ProtocolMessage) -> None:
        """处理心跳消息"""
        agent_id = message.content.get("agent_id")
        if agent_id:
            self.update_private_state(agent_id, "last_heartbeat", datetime.now())
            self.update_private_state(
                agent_id, "status", message.content.get("status", "unknown")
            )
            self.update_private_state(
                agent_id, "metrics", message.content.get("metrics", {})
            )
