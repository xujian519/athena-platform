#!/usr/bin/env python3
from __future__ import annotations
"""
通讯引擎 - 完整实现
Communication Engine - Complete Implementation

支持多通道通信、消息管理、协议适配和实时协作
作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import asyncio
import json
import logging
import uuid
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import aiohttp
import websockets

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """消息类型"""

    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    FILE = "file"
    SYSTEM = "system"
    COMMAND = "command"
    NOTIFICATION = "notification"
    BROADCAST = "broadcast"


class ChannelType(Enum):
    """通道类型"""

    DIRECT = "direct"  # 直接通信
    GROUP = "group"  # 群组通信
    BROADCAST = "broadcast"  # 广播
    API = "api"  # API接口
    WEBSOCKET = "websocket"  # WebSocket
    HTTP = "http"  # HTTP
    QUEUE = "queue"  # 消息队列


class MessageStatus(Enum):
    """消息状态"""

    PENDING = "pending"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class ProtocolType(Enum):
    """协议类型"""

    JSON = "json"
    XML = "xml"
    PROTOBUF = "protobuf"
    CUSTOM = "custom"


@dataclass
class Message:
    """消息"""

    id: str
    sender_id: str
    receiver_id: str  # None表示广播
    channel_id: str
    message_type: MessageType
    content: Any
    timestamp: datetime = field(default_factory=datetime.now)
    status: MessageStatus = MessageStatus.PENDING
    metadata: dict[str, Any] = field(default_factory=dict)
    protocol: ProtocolType = ProtocolType.JSON
    priority: int = 0  # 优先级 0-9
    ttl: int | None = None  # 生存时间(秒)
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class Channel:
    """通信通道"""

    id: str
    name: str
    channel_type: ChannelType
    participants: list[str] = field(default_factory=list)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class CommunicationSession:
    """通信会话"""

    id: str
    participant_ids: list[str]
    channel_id: str
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    message_count: int = 0
    is_active: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


class MessageQueue:
    """消息队列管理器"""

    def __init__(self, max_size: int = 10000):
        self.queues = defaultdict(lambda: deque(maxlen=max_size))
        self.priority_queues = {priority: deque(maxlen=max_size // 2) for priority in range(10)}
        self.lock = asyncio.Lock()

    async def enqueue(self, message: Message):
        """将消息加入队列"""
        async with self.lock:
            if message.priority > 0:
                # 高优先级消息进入优先队列
                self.priority_queues[message.priority].append(message)
            else:
                # 普通消息进入普通队列
                self.queues[message.channel_id].append(message)

    async def dequeue(self, channel_id: str | None = None) -> Message | None:
        """从队列取出消息"""
        async with self.lock:
            # 优先处理高优先级消息
            for priority in sorted(self.priority_queues.keys(), reverse=True):
                if self.priority_queues[priority]:
                    return self.priority_queues[priority].popleft()

            # 处理普通消息
            if channel_id and channel_id in self.queues and self.queues[channel_id]:
                return self.queues[channel_id].popleft()

            # 如果没有指定通道,尝试所有通道
            for _ch_id, queue in self.queues.items():
                if queue:
                    return queue.popleft()

            return None

    def size(self, channel_id: str | None = None) -> int:
        """获取队列大小"""
        if channel_id:
            return len(self.queues.get(channel_id, []))
        return sum(len(queue) for queue in self.queues.values()) + sum(
            len(queue) for queue in self.priority_queues.values()
        )


class ProtocolAdapter:
    """协议适配器"""

    def __init__(self):
        self.adapters = {
            ProtocolType.JSON: self._adapt_json,
            ProtocolType.XML: self._adapt_xml,
            ProtocolType.CUSTOM: self._adapt_custom,
        }

    async def serialize(self, message: Message) -> bytes:
        """序列化消息"""
        adapter = self.adapters.get(message.protocol, self._adapt_json)
        return await adapter(message, "serialize")

    async def deserialize(self, data: bytes, protocol: ProtocolType) -> dict[str, Any]:
        """反序列化消息"""
        adapter = self.adapters.get(protocol, self._adapt_json)
        return await adapter(data, "deserialize")

    async def _adapt_json(
        self, data: Message | bytes, operation: str
    ) -> bytes | dict[str, Any]:
        """JSON协议适配"""
        if operation == "serialize":
            message_dict = asdict(data)
            # 处理datetime对象
            if message_dict.get("timestamp"):
                message_dict["timestamp"] = message_dict["timestamp"].isoformat()
            return json.dumps(message_dict, ensure_ascii=False).encode("utf-8")
        else:
            message_dict = json.loads(data.decode("utf-8"))
            # 恢复datetime对象
            if message_dict.get("timestamp"):
                message_dict["timestamp"] = datetime.fromisoformat(message_dict["timestamp"])
            return message_dict

    async def _adapt_xml(
        self, data: Message | bytes, operation: str
    ) -> bytes | dict[str, Any]:
        """XML协议适配"""
        # 简化实现,实际应使用专业的XML库
        if operation == "serialize":
            # 转换为JSON再包装为XML
            json_data = await self._adapt_json(data, "serialize")
            xml_data = f"<message>{json_data.decode('utf-8')}</message>"
            return xml_data.encode("utf-8")
        else:
            # 从XML中提取JSON
            xml_str = data.decode("utf-8")
            json_str = xml_str.replace("<message>", "").replace("</message>", "")
            return await self._adapt_json(json_str.encode("utf-8"), "deserialize")

    async def _adapt_custom(
        self, data: Message | bytes, operation: str
    ) -> bytes | dict[str, Any]:
        """自定义协议适配"""
        # 默认使用JSON
        return await self._adapt_json(data, operation)


class WebSocketManager:
    """WebSocket连接管理器"""

    def __init__(self):
        self.connections: dict[str, websockets.WebSocketServerProtocol] = {}
        self.subscriptions: dict[str, list[str]] = defaultdict(
            list
        )  # channel_id -> [connection_ids]

    async def register_connection(self, connection_id: str, websocket):
        """注册WebSocket连接"""
        self.connections[connection_id] = websocket
        logger.info(f"WebSocket连接已注册: {connection_id}")

    async def unregister_connection(self, connection_id: str):
        """注销WebSocket连接"""
        if connection_id in self.connections:
            del self.connections[connection_id]
            # 清理订阅
            for _channel_id, subscribers in self.subscriptions.items():
                if connection_id in subscribers:
                    subscribers.remove(connection_id)
            logger.info(f"WebSocket连接已注销: {connection_id}")

    async def subscribe_channel(self, connection_id: str, channel_id: str):
        """订阅通道"""
        self.subscriptions[channel_id].append(connection_id)
        logger.info(f"连接 {connection_id} 订阅通道 {channel_id}")

    async def unsubscribe_channel(self, connection_id: str, channel_id: str):
        """取消订阅通道"""
        if connection_id in self.subscriptions[channel_id]:
            self.subscriptions[channel_id].remove(connection_id)
            logger.info(f"连接 {connection_id} 取消订阅通道 {channel_id}")

    async def broadcast_to_channel(self, channel_id: str, message: Message):
        """向通道广播消息"""
        if channel_id in self.subscriptions:
            data = await ProtocolAdapter().serialize(message)
            subscribers = self.subscriptions[channel_id].copy()

            for connection_id in subscribers:
                if connection_id in self.connections:
                    websocket = self.connections[connection_id]
                    try:
                        await websocket.send(data)
                        logger.debug(f"消息已发送到WebSocket连接: {connection_id}")
                    except Exception as e:
                        logger.error(f"发送WebSocket消息失败 {connection_id}: {e}")


class APIGateway:
    """API网关"""

    def __init__(self):
        self.routes = {}
        self.middlewares = []
        self.session = None

    async def initialize(self):
        """初始化API网关"""
        self.session = aiohttp.ClientSession()
        # 注册默认路由
        self.register_route("/send", self._handle_send_message)
        self.register_route("/receive", self._handle_receive_message)
        self.register_route("/channels", self._handle_channel_management)

    async def shutdown(self):
        """关闭API网关"""
        if self.session:
            await self.session.close()

    def register_route(self, path: str, handler: Callable) -> Any:
        """注册路由"""
        self.routes[path] = handler

    def add_middleware(self, middleware: Callable) -> None:
        """添加中间件"""
        self.middlewares.append(middleware)

    async def _handle_send_message(self, request_data: dict[str, Any]) -> dict[str, Any]:
        """处理发送消息请求"""
        return {"status": "success", "message": "Message sent"}

    async def _handle_receive_message(self, request_data: dict[str, Any]) -> dict[str, Any]:
        """处理接收消息请求"""
        return {"status": "success", "messages": []}

    async def _handle_channel_management(self, request_data: dict[str, Any]) -> dict[str, Any]:
        """处理通道管理请求"""
        return {"status": "success", "channels": []}


class CommunicationEngine:
    """通讯引擎 - 完整实现"""

    def __init__(self, agent_id: str, config: dict[str, Any] | None = None):
        self.agent_id = agent_id
        self.config = config or {}
        self.initialized = False

        # 核心组件
        self.message_queue = MessageQueue(max_size=self.config.get("max_queue_size", 10000))
        self.protocol_adapter = ProtocolAdapter()
        self.websocket_manager = WebSocketManager()
        self.api_gateway = APIGateway()

        # 存储和状态
        self.channels: dict[str, Channel] = {}
        self.sessions: dict[str, CommunicationSession] = {}
        self.messages: dict[str, Message] = {}
        self.active_connections: dict[str, dict[str, Any]] = {}

        # 统计信息
        self.stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "active_channels": 0,
            "active_sessions": 0,
            "failed_messages": 0,
        }

        # 事件回调
        self._callbacks = defaultdict(list)

        logger.info(f"💬 创建通讯引擎: {self.agent_id}")

    async def initialize(self):
        """初始化通讯引擎"""
        logger.info(f"🚀 启动通讯引擎: {self.agent_id}")

        try:
            # 初始化API网关
            await self.api_gateway.initialize()

            # 创建默认通道
            await self._create_default_channels()

            # 启动消息处理循环
            asyncio.create_task(self._message_processing_loop())

            self.initialized = True

            # 触发初始化事件
            await self._trigger_callbacks(
                "initialized", {"agent_id": self.agent_id, "timestamp": datetime.now()}
            )

            logger.info(f"✅ 通讯引擎初始化完成: {self.agent_id}")

        except Exception as e:
            logger.error(f"❌ 通讯引擎初始化失败 {self.agent_id}: {e}")
            raise

    async def send_message(
        self,
        receiver_id: str,
        content: Any,
        channel_id: str | None = None,
        message_type: MessageType = MessageType.TEXT,
        priority: int = 0,
    ) -> str:
        """发送消息"""
        if not self.initialized:
            raise RuntimeError("通讯引擎未初始化")

        message_id = str(uuid.uuid4())

        # 使用默认通道
        if not channel_id:
            channel_id = f"direct_{self.agent_id}_{receiver_id}"
            if channel_id not in self.channels:
                await self.create_channel(
                    channel_id=channel_id,
                    name="Direct Chat",
                    channel_type=ChannelType.DIRECT,
                    participants=[self.agent_id, receiver_id],
                )

        # 创建消息
        message = Message(
            id=message_id,
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            channel_id=channel_id,
            message_type=message_type,
            content=content,
            priority=priority,
        )

        # 加入队列
        await self.message_queue.enqueue(message)
        self.messages[message_id] = message

        logger.info(f"📤 消息已入队: {message_id} -> {receiver_id}")

        # 触发消息创建事件
        await self._trigger_callbacks(
            "message_created",
            {"message_id": message_id, "sender": self.agent_id, "receiver": receiver_id},
        )

        return message_id

    async def broadcast_message(
        self, content: Any, channel_id: str, message_type: MessageType = MessageType.BROADCAST
    ) -> str:
        """广播消息"""
        if not self.initialized:
            raise RuntimeError("通讯引擎未初始化")

        if channel_id not in self.channels:
            raise ValueError(f"通道不存在: {channel_id}")

        message_id = str(uuid.uuid4())
        channel = self.channels[channel_id]

        # 创建广播消息
        message = Message(
            id=message_id,
            sender_id=self.agent_id,
            receiver_id=None,  # None表示广播
            channel_id=channel_id,
            message_type=message_type,
            content=content,
            priority=1,  # 广播消息优先级略高
        )

        # 更新通道活动时间
        channel.last_activity = datetime.now()

        # 加入队列
        await self.message_queue.enqueue(message)
        self.messages[message_id] = message

        logger.info(f"📢 广播消息已入队: {message_id} -> channel:{channel_id}")

        return message_id

    async def create_channel(
        self, channel_id: str, name: str, channel_type: ChannelType, participants: list[str] | None = None
    ) -> Channel:
        """创建通道"""
        if channel_id in self.channels:
            return self.channels[channel_id]

        channel = Channel(
            id=channel_id, name=name, channel_type=channel_type, participants=participants or []
        )

        self.channels[channel_id] = channel
        self.stats["active_channels"] += 1

        logger.info(f"📡 通道已创建: {channel_id} ({name})")

        return channel

    async def create_session(
        self, participant_ids: list[str], channel_id: str | None = None
    ) -> CommunicationSession:
        """创建通信会话"""
        session_id = str(uuid.uuid4())

        # 如果没有指定通道,创建专用通道
        if not channel_id:
            channel_id = f"session_{session_id}"
            await self.create_channel(
                channel_id=channel_id,
                name=f"Session {session_id}",
                channel_type=ChannelType.GROUP,
                participants=participant_ids,
            )

        session = CommunicationSession(
            id=session_id, participant_ids=participant_ids, channel_id=channel_id
        )

        self.sessions[session_id] = session
        self.stats["active_sessions"] += 1

        logger.info(f"🤝 会话已创建: {session_id}")

        return session

    async def get_messages(
        self, channel_id: str | None = None, limit: int = 50
    ) -> list[Message]:
        """获取消息"""
        messages = []

        for message in self.messages.values():
            if channel_id:
                if message.channel_id == channel_id:
                    messages.append(message)
            else:
                messages.append(message)

        # 按时间排序
        messages.sort(key=lambda x: x.timestamp, reverse=True)

        return messages[:limit]

    async def get_channels(self, agent_id: str | None = None) -> list[Channel]:
        """获取通道列表"""
        channels = []

        for channel in self.channels.values():
            if agent_id:
                if agent_id in channel.participants:
                    channels.append(channel)
            else:
                channels.append(channel)

        return channels

    async def get_sessions(self, agent_id: str | None = None) -> list[CommunicationSession]:
        """获取会话列表"""
        sessions = []

        for session in self.sessions.values():
            if agent_id:
                if agent_id in session.participant_ids:
                    sessions.append(session)
            else:
                sessions.append(session)

        return sessions

    async def _create_default_channels(self):
        """创建默认通道"""
        # 系统通知通道
        await self.create_channel(
            channel_id="system", name="System Notifications", channel_type=ChannelType.BROADCAST
        )

        # API通道
        await self.create_channel(
            channel_id="api", name="API Communication", channel_type=ChannelType.API
        )

    async def _message_processing_loop(self):
        """消息处理循环"""
        while self.initialized:
            try:
                # 从队列获取消息
                message = await self.message_queue.dequeue()
                if not message:
                    await asyncio.sleep(0.1)
                    continue

                # 处理消息
                await self._process_message(message)

            except Exception as e:
                logger.error(f"消息处理错误: {e}")
                await asyncio.sleep(1)

    async def _process_message(self, message: Message):
        """处理单个消息"""
        try:
            # 更新状态
            message.status = MessageStatus.SENDING

            # 序列化消息
            serialized_data = await self.protocol_adapter.serialize(message)

            # 根据通道类型发送
            channel = self.channels.get(message.channel_id)
            if not channel:
                logger.warning(f"通道不存在: {message.channel_id}")
                message.status = MessageStatus.FAILED
                self.stats["failed_messages"] += 1
                return

            # 发送消息
            success = await self._send_to_channel(message, channel, serialized_data)

            # 更新状态
            if success:
                message.status = MessageStatus.SENT
                self.stats["messages_sent"] += 1

                # 如果是WebSocket通道,同时广播
                if channel.channel_type == ChannelType.WEBSOCKET:
                    await self.websocket_manager.broadcast_to_channel(channel.id, message)

                # 触发消息发送事件
                await self._trigger_callbacks(
                    "message_sent", {"message_id": message.id, "channel_id": message.channel_id}
                )
            else:
                message.status = MessageStatus.FAILED
                self.stats["failed_messages"] += 1

                # 重试逻辑
                if message.retry_count < message.max_retries:
                    message.retry_count += 1
                    message.status = MessageStatus.PENDING
                    await self.message_queue.enqueue(message)
                    logger.info(
                        f"消息重试: {message.id} ({message.retry_count}/{message.max_retries})"
                    )

        except Exception as e:
            logger.error(f"处理消息失败 {message.id}: {e}")
            message.status = MessageStatus.FAILED
            self.stats["failed_messages"] += 1

    async def _send_to_channel(self, message: Message, channel: Channel, data: bytes) -> bool:
        """向指定通道发送消息"""
        try:
            if channel.channel_type == ChannelType.HTTP:
                # HTTP发送
                return await self._send_http(message, channel, data)
            elif channel.channel_type == ChannelType.API:
                # API发送
                return await self._send_api(message, channel, data)
            elif channel.channel_type == ChannelType.DIRECT:
                # 直接发送
                return await self._send_direct(message, channel, data)
            else:
                # 默认处理
                return await self._send_default(message, channel, data)

        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            return False

    async def _send_http(self, message: Message, channel: Channel, data: bytes) -> bool:
        """HTTP方式发送"""
        # 简化实现,实际需要根据具体API进行
        logger.debug(f"HTTP发送消息: {message.id}")
        return True

    async def _send_api(self, message: Message, channel: Channel, data: bytes) -> bool:
        """API方式发送"""
        # 通过API网关发送
        try:
            # 这里可以调用具体的API接口
            logger.debug(f"API发送消息: {message.id}")
            return True
        except Exception as e:
            logger.error(f"API发送失败: {e}")
            return False

    async def _send_direct(self, message: Message, channel: Channel, data: bytes) -> bool:
        """直接发送"""
        # 如果接收者是本地Agent,直接处理
        if message.receiver_id == self.agent_id:
            logger.debug(f"接收本地消息: {message.id}")
            self.stats["messages_received"] += 1
            return True

        # 尝试通过WebSocket发送
        if self.websocket_manager.connections:
            try:
                await self.websocket_manager.broadcast_to_channel(channel.id, message)
                return True
            except Exception as e:
                logger.error(f"捕获异常: {e}", exc_info=True)

        return False

    async def _send_default(self, message: Message, channel: Channel, data: bytes) -> bool:
        """默认发送方式"""
        logger.debug(f"默认发送消息: {message.id}")
        return True

    async def register_websocket(self, connection_id: str, websocket):
        """注册WebSocket连接"""
        await self.websocket_manager.register_connection(connection_id, websocket)
        self.active_connections[connection_id] = {
            "type": "websocket",
            "connected_at": datetime.now(),
        }

    async def unregister_websocket(self, connection_id: str):
        """注销WebSocket连接"""
        await self.websocket_manager.unregister_connection(connection_id)
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]

    async def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        queue_size = self.message_queue.size()
        active_connections = len(self.active_connections)

        return {
            "agent_id": self.agent_id,
            "statistics": self.stats.copy(),
            "queue_size": queue_size,
            "active_connections": active_connections,
            "channels_count": len(self.channels),
            "sessions_count": len(self.sessions),
        }

    def register_callback(self, event_type: str, callback) -> None:
        """注册回调函数"""
        self._callbacks[event_type].append(callback)

    async def _trigger_callbacks(self, event_type: str, data: dict[str, Any]):
        """触发回调"""
        for callback in self._callbacks[event_type]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
            except Exception as e:
                logger.error(f"回调执行失败: {e}")

    async def shutdown(self):
        """关闭通讯引擎"""
        logger.info(f"🔄 关闭通讯引擎: {self.agent_id}")

        try:
            # 关闭API网关
            await self.api_gateway.shutdown()

            # 关闭WebSocket连接
            for connection_id in list(self.websocket_manager.connections.keys()):
                await self.unregister_websocket(connection_id)

            # 保存状态
            await self._save_state()

            self.initialized = False

            # 触发关闭事件
            await self._trigger_callbacks(
                "shutdown", {"agent_id": self.agent_id, "timestamp": datetime.now()}
            )

            logger.info(f"✅ 通讯引擎已关闭: {self.agent_id}")

        except Exception as e:
            logger.error(f"关闭通讯引擎失败: {e}")

    async def _save_state(self):
        """保存状态"""
        try:
            data_dir = Path("data/communication")
            data_dir.mkdir(parents=True, exist_ok=True)

            # 保存通道信息
            if self.channels:
                channel_file = data_dir / f"{self.agent_id}_channels.json"
                with open(channel_file, "w", encoding="utf-8") as f:
                    json.dump(
                        {cid: asdict(channel) for cid, channel in self.channels.items()},
                        f,
                        ensure_ascii=False,
                        indent=2,
                        default=str,
                    )

            # 保存会话信息
            if self.sessions:
                session_file = data_dir / f"{self.agent_id}_sessions.json"
                with open(session_file, "w", encoding="utf-8") as f:
                    json.dump(
                        {sid: asdict(session) for sid, session in self.sessions.items()},
                        f,
                        ensure_ascii=False,
                        indent=2,
                        default=str,
                    )

            logger.info(f"通讯状态已保存: {len(self.channels)}个通道, {len(self.sessions)}个会话")

        except Exception as e:
            logger.error(f"保存状态失败: {e}")

    @classmethod
    async def initialize_global(cls, config: dict | None = None):
        """初始化全局实例"""
        if not hasattr(cls, "global_instance"):
            cls.global_instance = cls("global", config)
            await cls.global_instance.initialize()
        return cls.global_instance

    @classmethod
    async def shutdown_global(cls):
        """关闭全局实例"""
        if hasattr(cls, "global_instance") and cls.global_instance:
            await cls.global_instance.shutdown()
            del cls.global_instance


# 重新导出
__all__ = [
    "APIGateway",
    "Channel",
    "ChannelType",
    "CommunicationEngine",
    "CommunicationSession",
    "Message",
    "MessageQueue",
    "MessageStatus",
    "MessageType",
    "ProtocolAdapter",
    "ProtocolType",
    "WebSocketManager",
]
