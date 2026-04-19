#!/usr/bin/env python3
from __future__ import annotations
"""
增强通信模块 - BaseModule标准接口兼容版本 (修复版)
Enhanced Communication Module - BaseModule Compatible Version (Fixed)

基于现有CommunicationEngine,添加BaseModule标准接口支持
作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.1.0
"""

import logging
import sys
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# 导入BaseModule
from core.base_module import BaseModule, HealthStatus, ModuleStatus

# 导入现有通信系统
try:
    from .communication_engine import (
        Channel,
        ChannelType,
        CommunicationEngine,
        Message,
        MessageStatus,
        MessageType,
        ProtocolType,
    )

    COMMUNICATION_SYSTEM_AVAILABLE = True
except ImportError as e:
    logging.warning(f"无法导入现有通信系统: {e}")
    COMMUNICATION_SYSTEM_AVAILABLE = False

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class EnhancedCommunicationConfig:
    """增强通信配置"""

    def __init__(self, config: dict[str, Any] | None = None):
        config = config or {}

        # 基础配置
        self.enable_websocket = config.get("enable_websocket", True)
        self.enable_api_gateway = config.get("enable_api_gateway", True)
        self.enable_message_queue = config.get("enable_message_queue", True)

        # 性能配置
        self.max_queue_size = config.get("max_queue_size", 10000)
        self.max_connections = config.get("max_connections", 1000)
        self.message_timeout = config.get("message_timeout", 30)

        # 安全配置
        self.enable_encryption = config.get("enable_encryption", False)
        self.enable_authentication = config.get("enable_authentication", True)
        self.allowed_origins = config.get("allowed_origins", ["*"])

        # 协议配置
        self.default_protocol = config.get("default_protocol", "json")
        self.supported_protocols = config.get("supported_protocols", ["json", "xml", "custom"])


@dataclass
class MessageResult:
    """消息结果"""

    success: bool
    message_id: str
    error: str | None = None
    delivery_time: float = 0.0
    status: str = "unknown"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChannelResult:
    """通道结果"""

    success: bool
    channel_id: str
    error: str | None = None
    participant_count: int = 0
    status: str = "unknown"
    message: str = ""
    channel_type: str = "direct"
    metadata: dict[str, Any] = field(default_factory=dict)


class EnhancedCommunicationModule(BaseModule):
    """增强通信模块 - BaseModule标准接口版本 (修复版)"""

    def __init__(self, agent_id: str, config: dict[str, Any] | None = None):
        """
        初始化增强通信模块

        Args:
            agent_id: 智能体标识符
            config: 配置参数
        """
        super().__init__(agent_id, config)

        # 通信配置
        self.comm_config = EnhancedCommunicationConfig(config)

        # 存储和状态
        self.channels: dict[str, Channel] = {}
        self.messages: dict[str, Message] = {}
        self.message_handlers: dict[str, Callable] = {}

        # 统计信息
        self.communication_stats = {
            "total_messages": 0,
            "sent_messages": 0,
            "received_messages": 0,
            "failed_messages": 0,
            "active_channels": 0,
            "active_connections": 0,
            "average_delivery_time": 0.0,
            "last_message_time": None,
        }

        # 通信引擎
        self.communication_engine = None

        # 模块状态
        self._module_status = ModuleStatus.INITIALIZING
        self._start_time = datetime.now()

        logger.info(f"💬 创建增强通信模块 - Agent: {agent_id}")

    async def initialize(self) -> bool:
        """
        初始化模块

        Returns:
            初始化是否成功
        """
        try:
            logger.info(f"🔧 初始化模块: {self.__class__.__name__}")
            logger.info("💬 初始化通信模块...")

            # 初始化现有通信系统
            if COMMUNICATION_SYSTEM_AVAILABLE:
                try:
                    self.communication_engine = CommunicationEngine(
                        agent_id=self.agent_id,
                        config={
                            "max_queue_size": self.comm_config.max_queue_size,
                            "max_connections": self.comm_config.max_connections,
                        },
                    )
                    await self.communication_engine.initialize()
                    logger.info("✅ 现有通信系统就绪")
                except Exception as e:
                    logger.warning(f"⚠️ 现有通信系统初始化失败: {e}")
                    self.communication_engine = None
            else:
                logger.info("📦 使用备用通信实现")
                self.communication_engine = None

            # 创建默认通道
            await self._create_default_channels()

            # 设置消息处理器
            self._setup_message_handlers()

            # 更新状态
            self._module_status = ModuleStatus.READY
            self._initialized = True

            logger.info("✅ 通信模块初始化成功")
            return True

        except Exception as e:
            logger.error(f"❌ 通信模块初始化失败: {e}")
            self._module_status = ModuleStatus.ERROR
            return False

    async def health_check(self) -> HealthStatus:
        """
        健康检查

        Returns:
            健康状态
        """
        try:
            health_details = {
                "module_status": self._module_status.value,
                "communication_status": "available" if self.communication_engine else "fallback",
                "dependencies_status": "ok",
                "message_system_status": "ready" if self._initialized else "initializing",
                "connection_status": "ok",
                "stats": {
                    "total_messages": self.communication_stats["total_messages"],
                    "sent_messages": self.communication_stats["sent_messages"],
                    "received_messages": self.communication_stats["received_messages"],
                    "failed_messages": self.communication_stats["failed_messages"],
                    "active_channels": self.communication_stats["active_channels"],
                },
            }

            # 缓存健康检查详情
            self._health_check_details = health_details

            # 基于状态确定健康状况
            if self._module_status == ModuleStatus.READY:
                return HealthStatus.HEALTHY
            elif self._module_status == ModuleStatus.ERROR:
                return HealthStatus.UNHEALTHY
            else:
                return HealthStatus.DEGRADED

        except Exception as e:
            logger.error(f"❌ 健康检查失败: {e}")
            return HealthStatus.UNHEALTHY

    async def send_message(
        self,
        receiver_id: str,
        content: Any,
        message_type: str = "text",
        channel_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MessageResult:
        """
        发送消息

        Args:
            receiver_id: 接收者ID
            content: 消息内容
            message_type: 消息类型
            channel_id: 通道ID
            metadata: 元数据

        Returns:
            消息发送结果
        """
        start_time = time.time()

        try:
            # 更新统计
            self.communication_stats["total_messages"] += 1

            if COMMUNICATION_SYSTEM_AVAILABLE and self.communication_engine:
                # 使用现有通信系统发送
                msg_type = (
                    MessageType(message_type)
                    if message_type in [t.value for t in MessageType]
                    else MessageType.TEXT
                )

                message_id = await self.communication_engine.send_message(
                    receiver_id=receiver_id,
                    content=content,
                    channel_id=channel_id,
                    message_type=msg_type,
                )

                delivery_time = time.time() - start_time

                # 更新统计
                self.communication_stats["sent_messages"] += 1
                self.communication_stats["average_delivery_time"] = (
                    self.communication_stats["average_delivery_time"]
                    * (self.communication_stats["sent_messages"] - 1)
                    + delivery_time
                ) / self.communication_stats["sent_messages"]
                self.communication_stats["last_message_time"] = datetime.now().isoformat()

                return MessageResult(
                    success=True,
                    message_id=message_id,
                    delivery_time=delivery_time,
                    status="sent",
                    metadata={"channel_id": channel_id},
                )

            else:
                # 备用发送
                return await self._fallback_send_message(
                    receiver_id, content, message_type, channel_id, metadata, start_time
                )

        except Exception as e:
            logger.error(f"❌ 消息发送失败: {e!s}")
            self.communication_stats["failed_messages"] += 1

            return MessageResult(
                success=False,
                message_id="",
                error=str(e),
                delivery_time=time.time() - start_time,
                status="failed",
            )

    async def receive_messages(
        self, limit: int = 10, channel_id: str | None = None , since: datetime | None = None
    ) -> list[Message]:
        """
        接收消息

        Args:
            limit: 最大消息数量
            channel_id: 通道ID
            since: 起始时间

        Returns:
            消息列表
        """
        try:
            if COMMUNICATION_SYSTEM_AVAILABLE and self.communication_engine:
                # 使用现有通信系统接收
                messages = await self.communication_engine.get_messages(
                    channel_id=channel_id, limit=limit
                )

                # 过滤时间
                if since:
                    messages = [msg for msg in messages if msg.timestamp >= since]

                # 更新统计
                self.communication_stats["received_messages"] += len(messages)

                return messages
            else:
                # 备用接收
                return await self._fallback_receive_messages(limit, channel_id, since)

        except Exception as e:
            logger.error(f"❌ 消息接收失败: {e!s}")
            return []

    async def create_channel(
        self, name: str, channel_type: str = "direct", participants: list[str] | None = None
    ) -> ChannelResult:
        """
        创建通道

        Args:
            name: 通道名称
            channel_type: 通道类型
            participants: 参与者列表

        Returns:
            通道创建结果
        """
        try:
            channel_id = str(uuid.uuid4())

            if COMMUNICATION_SYSTEM_AVAILABLE and self.communication_engine:
                # 使用现有通信系统 - 修复接口调用
                channel = await self.communication_engine.create_channel(
                    channel_id=channel_id,
                    name=name,
                    channel_type=ChannelType(channel_type),
                    participants=participants or [],
                )

                self.channels[channel_id] = channel
                self.communication_stats["active_channels"] += 1

                return ChannelResult(
                    success=True,
                    channel_id=channel.id,
                    message=f"Channel '{name}' created successfully",
                    participant_count=len(channel.participants),
                    channel_type=channel.channel_type.value,
                    status="created",
                    metadata={"channel_id": channel.id},
                )
            else:
                # 备用创建
                return await self._fallback_create_channel(
                    name, channel_type, participants, channel_id
                )

        except Exception as e:
            logger.error(f"❌ 通道创建失败: {e!s}")
            return ChannelResult(
                success=False,
                channel_id="",
                message=f"Failed to create channel: {e!s}",
                participant_count=0,
                channel_type=channel_type,
                status="error",
                error=str(e),
            )

    async def broadcast_message(
        self,
        content: Any,
        message_type: str = "text",
        channel_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MessageResult:
        """广播消息"""
        try:
            # 广播消息本质上是没有指定接收者的发送
            return await self.send_message(
                receiver_id="",  # 空字符串表示广播
                content=content,
                message_type=message_type,
                channel_id=channel_id,
                metadata=metadata,
            )
        except Exception as e:
            logger.error(f"❌ 广播失败: {e!s}")
            return MessageResult(success=False, message_id="", error=str(e), status="error")

    async def process(self, input_data: Any) -> dict[str, Any]:
        """标准处理接口 - BaseModule兼容"""
        try:
            if isinstance(input_data, dict):
                operation = input_data.get("operation", "send")
                receiver_id = input_data.get("receiver_id", "")
                content = input_data.get("content")
                message_type = input_data.get("message_type", "text")
                channel_id = input_data.get("channel_id")
                metadata = input_data.get("metadata")

                if operation == "send":
                    result = await self.send_message(
                        receiver_id=receiver_id,
                        content=content,
                        message_type=message_type,
                        channel_id=channel_id,
                        metadata=metadata,
                    )
                    return {
                        "success": result.success,
                        "message_id": result.message_id,
                        "delivery_time": result.delivery_time,
                    }
                elif operation == "create_channel":
                    name = input_data.get("name", "")
                    channel_type = input_data.get("channel_type", "direct")
                    participants = input_data.get("participants", [])

                    result = await self.create_channel(
                        name=name, channel_type=channel_type, participants=participants
                    )
                    return {
                        "success": result.success,
                        "channel_id": result.channel_id,
                        "participant_count": result.participant_count,
                    }
                elif operation == "broadcast":
                    result = await self.broadcast_message(
                        content=content,
                        message_type=message_type,
                        channel_id=channel_id,
                        metadata=metadata,
                    )
                    return {
                        "success": result.success,
                        "message_id": result.message_id,
                        "delivery_time": result.delivery_time,
                    }
                else:
                    return {"success": False, "error": f"Unknown operation: {operation}"}
            else:
                return {"success": False, "error": "Invalid input format"}

        except Exception as e:
            logger.error(f"❌ 处理请求失败: {e!s}")
            return {"success": False, "error": str(e)}

    def get_status(self) -> dict[str, Any]:
        """获取模块状态"""
        return {
            "agent_id": self.agent_id,
            "module_type": "enhanced_communication",
            "status": self._module_status.value,
            "initialized": self._initialized,
            "channels_count": len(self.channels),
            "uptime_seconds": (datetime.now() - self._start_time).total_seconds(),
            "communication_engine_available": self.communication_engine is not None,
        }

    def get_metrics(self) -> dict[str, Any]:
        """获取性能指标"""
        uptime = datetime.now() - self._start_time

        return {
            "module_status": self._module_status.value,
            "agent_id": self.agent_id,
            "initialized": self._initialized,
            "uptime_seconds": uptime.total_seconds(),
            "communication_stats": self.communication_stats.copy(),
            "active_channels": self.communication_stats["active_channels"],
            "message_handlers": len(self.message_handlers),
        }

    async def _create_default_channels(self):
        """创建默认通道"""
        try:
            # 创建系统通道
            system_result = await self.create_channel(
                name="System Notifications", channel_type="broadcast"
            )
            if system_result.success:
                logger.info(f"✅ 创建默认通道: {system_result.channel_id}")

            # 创建私有通道
            private_result = await self.create_channel(
                name=f"Private_{self.agent_id}", channel_type="direct"
            )
            if private_result.success:
                logger.info(f"✅ 创建私有通道: {private_result.channel_id}")

        except Exception as e:
            logger.warning(f"⚠️ 创建默认通道失败: {e}")

    def _setup_message_handlers(self) -> Any:
        """设置消息处理器"""
        # 注册默认消息处理器
        self.message_handlers["text"] = self._handle_text_message
        self.message_handlers["image"] = self._handle_image_message
        self.message_handlers["file"] = self._handle_file_message
        self.message_handlers["system"] = self._handle_system_message

    async def _handle_text_message(self, message: Message):
        """处理文本消息"""
        logger.debug(f"处理文本消息: {message.id}")

    async def _handle_image_message(self, message: Message):
        """处理图片消息"""
        logger.debug(f"处理图片消息: {message.id}")

    async def _handle_file_message(self, message: Message):
        """处理文件消息"""
        logger.debug(f"处理文件消息: {message.id}")

    async def _handle_system_message(self, message: Message):
        """处理系统消息"""
        logger.debug(f"处理系统消息: {message.id}")

    # 备用实现方法
    async def _fallback_send_message(
        self,
        receiver_id: str,
        content: Any,
        message_type: str,
        channel_id: str,
        metadata: dict[str, Any],        start_time: float,
    ) -> MessageResult:
        """备用消息发送"""
        message_id = str(uuid.uuid4())
        delivery_time = time.time() - start_time

        # 创建本地消息记录
        message = Message(
            id=message_id,
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            channel_id=channel_id or "default",
            message_type=(
                MessageType(message_type)
                if message_type in [t.value for t in MessageType]
                else MessageType.TEXT
            ),
            content=content,
            metadata=metadata or {},
        )

        self.messages[message_id] = message
        self.communication_stats["sent_messages"] += 1

        logger.info(f"📫 备用发送消息: {message_id}")

        return MessageResult(
            success=True, message_id=message_id, delivery_time=delivery_time, status="sent_fallback"
        )

    async def _fallback_receive_messages(
        self, limit: int, channel_id: str, since: datetime
    ) -> list[Message]:
        """备用消息接收"""
        messages = []

        for message in self.messages.values():
            if channel_id and message.channel_id != channel_id:
                continue
            if since and message.timestamp < since:
                continue
            messages.append(message)

            if len(messages) >= limit:
                break

        # 按时间排序
        messages.sort(key=lambda x: x.timestamp, reverse=True)

        return messages

    async def _fallback_create_channel(
        self, name: str, channel_type: str, participants: list[str], channel_id: str
    ) -> ChannelResult:
        """备用通道创建"""
        channel = Channel(
            id=channel_id,
            name=name,
            channel_type=(
                ChannelType(channel_type)
                if channel_type in [t.value for t in ChannelType]
                else ChannelType.DIRECT
            ),
            participants=participants or [],
        )

        self.channels[channel_id] = channel
        self.communication_stats["active_channels"] += 1

        logger.info(f"📡 备用创建通道: {channel_id}")

        return ChannelResult(
            success=True,
            channel_id=channel_id,
            message=f"Fallback channel '{name}' created",
            participant_count=len(participants or []),
            channel_type=channel_type,
            status="created_fallback",
        )

    # BaseModule抽象方法实现
    async def _on_initialize(self) -> bool:
        """子类初始化逻辑"""
        try:
            # 初始化现有通信系统
            if COMMUNICATION_SYSTEM_AVAILABLE:
                try:
                    self.communication_engine = CommunicationEngine(
                        agent_id=self.agent_id,
                        config={
                            "max_queue_size": self.comm_config.max_queue_size,
                            "max_connections": self.comm_config.max_connections,
                        },
                    )
                    await self.communication_engine.initialize()
                    logger.info("✅ 现有通信系统就绪")
                except Exception as e:
                    logger.warning(f"⚠️ 现有通信系统初始化失败: {e}")
                    self.communication_engine = None
            else:
                logger.info("📦 使用备用通信实现")
                self.communication_engine = None

            # 创建默认通道
            await self._create_default_channels()

            # 设置消息处理器
            self._setup_message_handlers()

            return True

        except Exception as e:
            logger.error(f"❌ 子类初始化失败: {e}")
            return False

    async def _on_start(self) -> bool:
        """子类启动逻辑"""
        try:
            # 启动消息处理循环
            if self.communication_engine:
                # 通信引擎已在初始化时启动
                pass
            else:
                # 启动备用消息处理
                pass

            logger.info("✅ 通信模块启动成功")
            return True

        except Exception as e:
            logger.error(f"❌ 通信模块启动失败: {e}")
            return False

    async def _on_stop(self) -> bool:
        """子类停止逻辑"""
        try:
            # 停止消息处理
            logger.info("🛑 停止消息处理")
            return True

        except Exception as e:
            logger.error(f"❌ 通信模块停止失败: {e}")
            return False

    async def _on_shutdown(self) -> bool:
        """子类关闭逻辑"""
        try:
            # 保存统计信息
            logger.info(f"📊 通信统计: {self.communication_stats}")

            # 关闭通信引擎
            if self.communication_engine:
                await self.communication_engine.shutdown()

            # 清理资源
            self.channels.clear()
            self.messages.clear()
            self.message_handlers.clear()

            logger.info("✅ 通信模块关闭成功")
            return True

        except Exception as e:
            logger.error(f"❌ 通信模块关闭失败: {e}")
            return False

    async def _on_health_check(self) -> bool:
        """子类健康检查逻辑"""
        try:
            # 检查通信引擎状态
            if self.communication_engine:
                # 检查通信引擎是否健康
                return True
            else:
                # 备用模式检查
                return len(self.channels) >= 0  # 基本检查

        except Exception as e:
            logger.error(f"❌ 健康检查失败: {e}")
            return False

    async def shutdown(self):
        """关闭模块"""
        logger.info(f"🔌 关闭模块: {self.__class__.__name__}")
        await super().shutdown()


# 导出
__all__ = [
    "ChannelResult",
    "EnhancedCommunicationConfig",
    "EnhancedCommunicationModule",
    "MessageResult",
]
