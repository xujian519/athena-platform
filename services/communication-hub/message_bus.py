"""
统一消息总线
实现AI角色间的实时通信和事件协调
"""

import asyncio
import json
import logging
import uuid
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from websockets.asyncio.server import ServerConnection

from core.logging_config import setup_logging

# 类型别名，保持向后兼容
WebSocketServerProtocol = ServerConnection

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

class MessageType(Enum):
    """消息类型"""
    TASK_CREATED = 'task_created'
    TASK_UPDATED = 'task_updated'
    TASK_COMPLETED = 'task_completed'
    AI_RESPONSE = 'ai_response'
    COLLABORATION_REQUEST = 'collaboration_request'
    COLLABORATION_RESPONSE = 'collaboration_response'
    STATUS_UPDATE = 'status_update'
    SYSTEM_NOTIFICATION = 'system_notification'
    HEARTBEAT = 'heartbeat'

class Priority(Enum):
    """消息优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

@dataclass
class Message:
    """消息定义"""
    id: str
    type: MessageType
    sender: str
    recipient: str | None  # None表示广播
    content: dict[str, Any]
    priority: Priority
    timestamp: datetime
    correlation_id: str | None = None  # 关联ID，用于追踪对话
    ttl: int | None = None  # 生存时间（秒）

@dataclass
class Subscription:
    """订阅信息"""
    subscriber: str
    message_types: list[MessageType]
    callback: Callable
    active: bool = True

class MessageBus:
    """消息总线"""

    def __init__(self):
        self.subscribers: dict[str, list[Subscription]] = defaultdict(list)
        self.message_history: deque = deque(maxlen=1000)  # 保留最近1000条消息
        self.active_connections: dict[str, WebSocketServerProtocol] = {}
        self.pending_messages: dict[str, list[Message]] = defaultdict(list)
        self.message_handlers: dict[MessageType, list[Callable]] = defaultdict(list)

    def subscribe(self, subscriber: str, message_types: list[MessageType], callback: Callable) -> Any:
        """订阅消息"""
        subscription = Subscription(
            subscriber=subscriber,
            message_types=message_types,
            callback=callback
        )
        self.subscribers[subscriber].append(subscription)
        logger.info(f"{subscriber} 已订阅消息类型: {[t.value for t in message_types]}")

    def unsubscribe(self, subscriber: str, message_type: MessageType | None = None) -> Any:
        """取消订阅"""
        if subscriber in self.subscribers:
            if message_type:
                # 取消特定类型的订阅
                self.subscribers[subscriber] = [
                    sub for sub in self.subscribers[subscriber]
                    if message_type not in sub.message_types
                ]
            else:
                # 取消所有订阅
                del self.subscribers[subscriber]
            logger.info(f"{subscriber} 已取消订阅")

    async def publish(self, message: Message) -> bool:
        """发布消息"""
        try:
            # 添加到历史记录
            self.message_history.append(message)

            # 检查TTL
            if message.ttl:
                age = (datetime.now() - message.timestamp).total_seconds()
                if age > message.ttl:
                    logger.warning(f"消息已过期: {message.id}")
                    return False

            # 处理消息处理器
            for handler in self.message_handlers[message.type]:
                try:
                    await handler(message)
                except Exception as e:
                    logger.error(f"消息处理器错误: {e}")

            # 通知订阅者
            delivered = False
            for subscriber, subscriptions in self.subscribers.items():
                # 跳过发送者自己
                if subscriber == message.sender:
                    continue

                for sub in subscriptions:
                    if not sub.active:
                        continue

                    # 检查消息类型匹配
                    if message.type in sub.message_types:
                        # 检查接收者指定
                        if message.recipient is None or message.recipient == subscriber:
                            try:
                                await sub.callback(message)
                                delivered = True
                            except Exception as e:
                                logger.error(f"消息投递失败 {subscriber}: {e}")

            # WebSocket广播
            if message.recipient is None:
                await self._broadcast_websocket(message)

            logger.info(f"消息已发布: {message.type.value} from {message.sender}")
            return delivered

        except Exception as e:
            logger.error(f"发布消息失败: {e}")
            return False

    async def _broadcast_websocket(self, message: Message):
        """WebSocket广播"""
        message_data = {
            'type': message.type.value,
            'sender': message.sender,
            'content': message.content,
            'timestamp': message.timestamp.isoformat(),
            'priority': message.priority.value
        }

        # 发送给所有活跃连接
        for connection_id, ws in list(self.active_connections.items()):
            try:
                await ws.send(json.dumps(message_data))
            except Exception as e:
                logger.warning(f"WebSocket发送失败 {connection_id}: {e}")
                # 清理无效连接
                del self.active_connections[connection_id]

    def register_websocket(self, connection_id: str, websocket: WebSocketServerProtocol) -> Any:
        """注册WebSocket连接"""
        self.active_connections[connection_id] = websocket
        logger.info(f"WebSocket连接已注册: {connection_id}")

    def unregister_websocket(self, connection_id: str) -> Any:
        """注销WebSocket连接"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            logger.info(f"WebSocket连接已注销: {connection_id}")

    async def send_to_ai(self, sender: str, recipient: str, message_type: MessageType,
                        content: dict[str, Any], priority: Priority = Priority.NORMAL) -> str:
        """发送消息给特定AI"""
        message = Message(
            id=str(uuid.uuid4()),
            type=message_type,
            sender=sender,
            recipient=recipient,
            content=content,
            priority=priority,
            timestamp=datetime.now()
        )

        await self.publish(message)
        return message.id

    async def broadcast(self, sender: str, message_type: MessageType,
                       content: dict[str, Any], priority: Priority = Priority.NORMAL) -> str:
        """广播消息"""
        message = Message(
            id=str(uuid.uuid4()),
            type=message_type,
            sender=sender,
            recipient=None,  # 广播
            content=content,
            priority=priority,
            timestamp=datetime.now()
        )

        await self.publish(message)
        return message.id

    def get_message_history(self, limit: int = 100, message_type: MessageType | None = None) -> list[Message]:
        """获取消息历史"""
        messages = list(self.message_history)
        if message_type:
            messages = [m for m in messages if m.type == message_type]
        return messages[-limit:]

    def add_message_handler(self, message_type: MessageType, handler: Callable) -> None:
        """添加消息处理器"""
        self.message_handlers[message_type].append(handler)

    async def start_heartbeat(self):
        """启动心跳机制"""
        while True:
            heartbeat_message = Message(
                id=str(uuid.uuid4()),
                type=MessageType.HEARTBEAT,
                sender='system',
                recipient=None,
                content={'timestamp': datetime.now().isoformat()},
                priority=Priority.LOW,
                timestamp=datetime.now()
            )
            await self.publish(heartbeat_message)
            await asyncio.sleep(30)  # 每30秒发送心跳

# 全局消息总线实例
message_bus = MessageBus()

# 便捷函数
async def send_task_update(sender: str, task_id: str, status: str, details: dict = None):
    """发送任务更新"""
    await message_bus.send_to_ai(
        sender=sender,
        recipient='all',
        message_type=MessageType.TASK_UPDATED,
        content={
            'task_id': task_id,
            'status': status,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        },
        priority=Priority.NORMAL
    )

async def request_collaboration(requester: str, task_info: dict, required_ais: list[str]) -> str:
    """请求协作"""
    message_id = await message_bus.send_to_ai(
        sender=requester,
        recipient='collaboration_hub',
        message_type=MessageType.COLLABORATION_REQUEST,
        content={
            'task_info': task_info,
            'required_ais': required_ais,
            'requester': requester
        },
        priority=Priority.HIGH
    )
    return message_id

async def notify_ai_response(ai_name: str, response: dict, correlation_id: str = None):
    """通知AI响应"""
    await message_bus.send_to_ai(
        sender=ai_name,
        recipient='system',
        message_type=MessageType.AI_RESPONSE,
        content={
            'ai': ai_name,
            'response': response,
            'correlation_id': correlation_id
        },
        priority=Priority.NORMAL
    )
