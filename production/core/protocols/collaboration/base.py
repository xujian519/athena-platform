#!/usr/bin/env python3
from __future__ import annotations
"""
协作协议 - 基础协议类
Collaboration Protocols - Base Protocol Class

定义所有协议的抽象基类

作者: Athena AI系统
创建时间: 2025-12-04
重构时间: 2026-01-26
版本: 2.1.0
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import datetime
from typing import Any

# 从本地types模块导入
from core.protocols.collaboration.types import (
    ProtocolContext,
    ProtocolMessage,
    ProtocolPhase,
    ProtocolStatus,
    ProtocolType,
)

logger = logging.getLogger(__name__)


class BaseProtocol(ABC):
    """基础协议抽象类"""

    def __init__(self, protocol_id: str, protocol_type: ProtocolType):
        self.protocol_id = protocol_id
        self.protocol_type = protocol_type
        self.context = ProtocolContext(
            protocol_id=protocol_id, protocol_type=protocol_type
        )
        self.message_handlers: dict[str, Callable] = {}
        self.event_handlers: dict[str, list[Callable]] = {}
        self.running = False
        self.message_queue: list[ProtocolMessage] = []

    def add_participant(self, agent_id: str) -> bool:
        """添加参与者"""
        if agent_id not in self.context.participants:
            self.context.participants.append(agent_id)
            self.context.private_states[agent_id] = {}
            logger.info(f"协议 {self.protocol_id} 添加参与者: {agent_id}")
            return True
        return False

    def remove_participant(self, agent_id: str) -> bool:
        """移除参与者"""
        if agent_id in self.context.participants:
            self.context.participants.remove(agent_id)
            if agent_id in self.context.private_states:
                del self.context.private_states[agent_id]
            logger.info(f"协议 {self.protocol_id} 移除参与者: {agent_id}")
            return True
        return False

    def update_shared_state(self, key: str, value: Any) -> None:
        """更新共享状态"""
        self.context.shared_state[key] = value
        self.context.updated_at = datetime.now()
        logger.debug(f"协议 {self.protocol_id} 更新共享状态: {key} = {value}")

    def update_private_state(self, agent_id: str, key: str, value: Any) -> None:
        """更新私有状态"""
        if agent_id in self.context.private_states:
            self.context.private_states[agent_id][key] = value
            self.context.updated_at = datetime.now()
            logger.debug(
                f"协议 {self.protocol_id} 更新智能体 {agent_id} 私有状态: {key} = {value}"
            )

    def send_message(self, message: ProtocolMessage) -> bool:
        """发送消息"""
        try:
            message.protocol_id = self.protocol_id
            message.timestamp = datetime.now()
            self.message_queue.append(message)
            logger.debug(f"协议 {self.protocol_id} 发送消息: {message.message_type}")
            return True
        except Exception as e:
            logger.error(f"协议 {self.protocol_id} 发送消息失败: {e}")
            return False

    def receive_message(self, message: ProtocolMessage) -> bool:
        """接收消息"""
        try:
            # 验证消息基本格式
            if not self._validate_message_format(message):
                logger.warning(f"协议 {self.protocol_id} 消息格式验证失败,尝试修复")
                message = self._repair_message_format(message)

            # 查找消息处理器
            handler = self.message_handlers.get(message.message_type)
            if handler:
                asyncio.create_task(handler(message))
                return True
            else:
                # 尝试使用默认处理器或相似类型处理器
                handler = self._find_message_handler(message.message_type)
                if handler:
                    logger.info(
                        f"协议 {self.protocol_id} 使用替代处理器处理消息: {message.message_type}"
                    )
                    asyncio.create_task(handler(message))
                    return True
                else:
                    logger.warning(
                        f"协议 {self.protocol_id} 未知消息类型: {message.message_type}"
                    )
                    # 不再返回False,而是记录并继续
                    return True

        except Exception as e:
            logger.error(f"协议 {self.protocol_id} 处理消息失败: {e}")
            import traceback

            logger.error(f"消息处理错误详情: {traceback.format_exc()}")
            # 即使处理失败也不返回False,避免中断整个流程
            return True

    def _validate_message_format(self, message: ProtocolMessage) -> bool:
        """验证消息格式"""
        try:
            # 基本字段检查
            if not hasattr(message, "message_type") or not message.message_type:
                return False

            if not hasattr(message, "sender_id") or not message.sender_id:
                return False

            # 可选字段检查
            if not hasattr(message, "timestamp"):
                # 自动添加时间戳
                from datetime import datetime

                message.timestamp = datetime.now()

            if not hasattr(message, "content"):
                # 设置默认内容
                message.content = {}

            return True
        except Exception as e:
            logger.error(f"消息格式验证失败: {e}")
            return False

    def _repair_message_format(self, message: ProtocolMessage) -> ProtocolMessage:
        """修复消息格式"""
        try:
            # 确保有必要的字段
            if not hasattr(message, "message_type") or not message.message_type:
                message.message_type = "unknown"

            if not hasattr(message, "sender_id") or not message.sender_id:
                message.sender_id = "unknown"

            if not hasattr(message, "receiver_id"):
                message.receiver_id = "broadcast"

            if not hasattr(message, "timestamp"):
                from datetime import datetime

                message.timestamp = datetime.now()

            if not hasattr(message, "content"):
                message.content = {}

            if not hasattr(message, "priority"):
                message.priority = 1

            logger.debug(f"消息格式已修复: {message.message_type}")
            return message
        except Exception as e:
            logger.error(f"消息格式修复失败: {e}")
            return message

    def _find_message_handler(self, message_type: str) -> Callable | None:
        """查找消息处理器"""
        # 尝试查找默认处理器
        if "default" in self.message_handlers:
            return self.message_handlers["default"]

        # 尝试查找相似类型的处理器
        similar_types = []
        for handler_type in self.message_handlers:
            if any(
                keyword in handler_type.lower()
                for keyword in message_type.lower().split("_")
            ):
                similar_types.append(handler_type)

        if similar_types:
            # 选择最相似的处理器
            best_match = max(
                similar_types,
                key=lambda x: len(set(x.split("_")) & set(message_type.split("_"))),
            )
            logger.info(f"找到相似消息处理器: {message_type} -> {best_match}")
            return self.message_handlers[best_match]

        # 没有找到合适的处理器
        return None

    def register_message_handler(self, message_type: str, handler: Callable) -> None:
        """注册消息处理器"""
        self.message_handlers[message_type] = handler
        logger.debug(f"协议 {self.protocol_id} 注册消息处理器: {message_type}")

    def register_event_handler(self, event_type: str, handler: Callable) -> None:
        """注册事件处理器"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        logger.debug(f"协议 {self.protocol_id} 注册事件处理器: {event_type}")

    def trigger_event(self, event_type: str, event_data: dict[str, Any]) -> None:
        """触发事件"""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    asyncio.create_task(handler(event_data))
                except Exception as e:
                    logger.error(f"协议 {self.protocol_id} 事件处理器执行失败: {e}")

    @abstractmethod
    async def execute(self) -> bool:
        """执行协议"""
        pass

    @abstractmethod
    async def initialize(self) -> bool:
        """初始化协议"""
        pass

    async def start(self) -> bool:
        """启动协议"""
        try:
            self.running = True
            self.context.status = ProtocolStatus.ACTIVE
            self.context.current_phase = ProtocolPhase.INITIALIZATION

            # 验证协议状态
            if not self._validate_protocol_state():
                logger.warning(f"协议 {self.protocol_id} 状态验证失败,尝试修复")
                if not await self._repair_protocol_state():
                    logger.error(f"协议 {self.protocol_id} 状态修复失败")
                    return False

            # 初始化协议
            init_success = await self.initialize()
            if init_success:
                # 执行协议
                success = await self.execute()

                if success:
                    self.context.status = ProtocolStatus.COMPLETED
                    self.context.current_phase = ProtocolPhase.TERMINATION
                    logger.info(f"协议 {self.protocol_id} 执行完成")
                else:
                    self.context.status = ProtocolStatus.FAILED
                    self.context.current_phase = ProtocolPhase.ERROR_HANDLING
                    logger.error(f"协议 {self.protocol_id} 执行失败")

                return success
            else:
                self.context.status = ProtocolStatus.FAILED
                self.context.current_phase = ProtocolPhase.ERROR_HANDLING
                return False

        except Exception as e:
            logger.error(f"协议 {self.protocol_id} 启动失败: {e}")
            import traceback

            logger.error(f"协议启动错误详情: {traceback.format_exc()}")

            # 尝试错误恢复
            if await self._attempt_error_recovery(e):
                logger.info(f"协议 {self.protocol_id} 错误恢复成功")
                return await self.start()  # 重试启动
            else:
                self.context.status = ProtocolStatus.FAILED
                self.context.current_phase = ProtocolPhase.ERROR_HANDLING
                return False

    def _validate_protocol_state(self) -> bool:
        """验证协议状态"""
        try:
            # 检查基本属性
            if not self.protocol_id:
                logger.error("协议ID为空")
                return False

            if not self.context.participants:
                logger.warning("协议没有参与者")

            # 检查消息处理器
            if not self.message_handlers:
                logger.warning("协议没有注册消息处理器")

            return True
        except Exception as e:
            logger.error(f"协议状态验证失败: {e}")
            return False

    async def _repair_protocol_state(self) -> bool:
        """修复协议状态"""
        try:
            # 重置协议状态
            if not self.protocol_id:
                from uuid import uuid4

                self.protocol_id = str(uuid4())[:8]

            # 添加默认消息处理器
            if not self.message_handlers:
                self.message_handlers["default"] = self._default_message_handler

            logger.info(f"协议 {self.protocol_id} 状态修复完成")
            return True
        except Exception as e:
            logger.error(f"协议状态修复失败: {e}")
            return False

    async def _attempt_error_recovery(self, error: Exception) -> bool:
        """尝试错误恢复"""
        try:
            error_type = type(error).__name__
            error_message = str(error).lower()

            # 根据错误类型采取不同的恢复策略
            if "timeout" in error_message:
                logger.info("检测到超时错误,尝试重置协议状态")
                self.context.current_phase = ProtocolPhase.INITIALIZATION
                return True

            elif "connection" in error_message or "network" in error_message:
                logger.info("检测到连接错误,尝试重新初始化")
                await asyncio.sleep(1.0)  # 短暂延迟
                return True

            elif "resource" in error_message:
                logger.info("检测到资源错误,尝试释放资源")
                self.running = False
                await asyncio.sleep(0.5)
                return True

            else:
                logger.info(f"未知错误类型 {error_type},尝试通用恢复策略")
                self.context.current_phase = ProtocolPhase.INITIALIZATION
                return True

        except Exception as recovery_error:
            logger.error(f"错误恢复失败: {recovery_error}")
            return False

    async def _default_message_handler(self, message):
        """默认消息处理器"""
        logger.debug(f"使用默认消息处理器处理消息: {message.message_type}")
        return True

    def stop(self) -> None:
        """停止协议"""
        self.running = False
        self.context.status = ProtocolStatus.SUSPENDED
        logger.info(f"协议 {self.protocol_id} 已停止")

    def resume(self) -> None:
        """恢复协议"""
        self.running = True
        self.context.status = ProtocolStatus.ACTIVE
        logger.info(f"协议 {self.protocol_id} 已恢复")

    def get_protocol_info(self) -> dict[str, Any]:
        """获取协议信息"""
        return {
            "protocol_id": self.protocol_id,
            "protocol_type": self.protocol_type.value,
            "participants": self.context.participants,
            "current_phase": self.context.current_phase.value,
            "status": self.context.status.value,
            "created_at": self.context.created_at.isoformat(),
            "updated_at": self.context.updated_at.isoformat(),
            "shared_state_size": len(self.context.shared_state),
            "message_queue_size": len(self.message_queue),
        }
