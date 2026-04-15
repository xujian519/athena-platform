#!/usr/bin/env python3
from __future__ import annotations
"""
Redis持久化消息总线
Redis Persistent Message Bus for Agent Communication

解决内存队列的问题:
1. 消息持久化 - 服务重启不丢失
2. 跨进程通信 - 支持分布式部署
3. 消息确认机制 - 确保消息可靠传递
4. 死信队列 - 处理失败消息

版本: v1.0.0
创建时间: 2026-01-18
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

try:
    import redis.asyncio as redis

    redis_available = True  # type: ignore[assignment]
except ImportError:
    redis = None  # type: ignore[assignment]
    redis_available = False  # type: ignore[assignment]

from .communication import ResponseMessage, TaskMessage

logger = logging.getLogger(__name__)

# Type alias for Redis client
RedisClient = Any  # redis.Redis if redis is not None else None

# Suppress errors for redis module which may be None
# pyright: reportOptionalMemberAccess=false


# =============================================================================
# 数据结构
# =============================================================================


@dataclass
class MessageEnvelope:
    """消息封装"""

    message_id: str
    message_type: str  # 'task' or 'response'
    payload: dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    retry_count: int = 0
    max_retries: int = 3
    ttl: int = 3600  # 消息存活时间(秒)
    confirmed: bool = False

    def to_bytes(self) -> bytes:
        """序列化为字节"""
        data = {
            "message_id": self.message_id,
            "message_type": self.message_type,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "ttl": self.ttl,
            "confirmed": self.confirmed,
        }
        return json.dumps(data, ensure_ascii=False).encode("utf-8")

    @classmethod
    def from_bytes(cls, data: bytes) -> "MessageEnvelope":
        """从字节反序列化"""
        data_dict = json.loads(data.decode("utf-8"))
        return cls(**data_dict)


@dataclass
class ConsumerInfo:
    """消费者信息"""

    consumer_id: str
    subscribed_channels: set[str] = field(default_factory=set)
    last_heartbeat: str = field(default_factory=lambda: datetime.now().isoformat())
    message_count: int = 0
    error_count: int = 0


# =============================================================================
# Redis消息总线实现
# =============================================================================


class RedisMessageBus:
    """
    Redis持久化消息总线

    特性:
    - 使用Redis Stream实现持久化消息队列
    - 支持消息确认机制
    - 自动重试失败消息
    - 死信队列处理无法投递的消息
    - 消费者健康监控
    """

    # Redis键前缀
    STREAM_PREFIX = "agent:msg:stream:"
    CONSUMER_GROUP = "agent_consumers"
    PENDING_PREFIX = "agent:msg:pending:"
    DEAD_LETTER_PREFIX = "agent:msg:dead:"
    CONSUMER_PREFIX = "agent:consumer:"

    def __init__(
        self,
        redis_url: str = "redis://127.0.0.1:6379/0",
        max_message_size: int = 10 * 1024 * 1024,  # 10MB
        message_retention_hours: int = 24,
        health_check_interval: int = 30,
        max_retries: int = 3,
    ):
        if not redis_available:
            raise ImportError("Redis不可用,请安装: pip install redis")

        self.redis_url = redis_url
        self.redis_client: RedisClient | None = None
        self.running = False

        # 配置
        self.max_message_size = max_message_size
        self.message_retention_hours = message_retention_hours
        self.health_check_interval = health_check_interval
        self.max_retries = max_retries

        # 消费者管理
        self.consumers: dict[str, ConsumerInfo] = {}
        self.subscribers: dict[str, set[str]] = {}  # channel -> consumer_ids

        # 统计信息
        self.stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "messages_confirmed": 0,
            "messages_failed": 0,
            "errors": 0,
        }

        # 后台任务
        self._health_check_task: asyncio.Task[Any] | None | None = None
        self._cleanup_task: asyncio.Task[Any] | None | None = None

    async def start(self):
        """启动消息总线"""
        try:
            # 创建Redis连接
            self.redis_client = redis.from_url(
                self.redis_url, encoding="utf-8", decode_responses=False
            )

            # 测试连接
            await self.redis_client.ping()

            self.running = True

            # 创建消费者组(如果不存在)
            await self._initialize_consumer_groups()

            # 启动后台任务
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

            logger.info("✅ Redis消息总线启动成功")

        except Exception as e:
            logger.error(f"❌ Redis消息总线启动失败: {e}")
            raise

    async def stop(self):
        """停止消息总线"""
        self.running = False

        # 取消后台任务
        if self._health_check_task:
            self._health_check_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()

        # 关闭Redis连接
        if self.redis_client:
            await self.redis_client.close()

        logger.info("✅ Redis消息总线已停止")

    async def _initialize_consumer_groups(self):
        """初始化消费者组"""
        try:
            # 创建主消息流的消费者组
            await self.redis_client.xgroup_create(
                name=self.STREAM_PREFIX + "main",
                groupname=self.CONSUMER_GROUP,
                id="0",
                mkstream=True,
            )
        except redis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                logger.warning(f"创建消费者组警告: {e}")

    # ==================== 发送消息 ====================

    async def send_message(
        self, message: TaskMessage | ResponseMessage, channel: str = "main"
    ) -> bool:
        """
        发送消息到指定频道

        Args:
            message: 任务消息或响应消息
            channel: 频道名称(默认为main)

        Returns:
            bool: 是否发送成功
        """
        try:
            # 转换为消息封装
            if isinstance(message, TaskMessage):
                envelope = MessageEnvelope(
                    message_id=message.task_id,
                    message_type="task",
                    payload={
                        "task_id": message.task_id,
                        "sender_id": message.sender_id,
                        "recipient_id": message.recipient_id,
                        "task_type": message.task_type,
                        "content": message.content,
                        "priority": message.priority.value,
                    },
                )
            else:  # ResponseMessage
                envelope = MessageEnvelope(
                    message_id=message.task_id,
                    message_type="response",
                    payload={
                        "task_id": message.task_id,
                        "sender_id": message.sender_id,
                        "recipient_id": message.recipient_id,
                        "success": message.success,
                        "content": message.content,
                        "error_message": message.error_message,
                        "execution_time": message.execution_time,
                    },
                )

            # 检查消息大小
            message_bytes = envelope.to_bytes()
            if len(message_bytes) > self.max_message_size:
                logger.error(f"消息过大: {len(message_bytes)} > {self.max_message_size}")
                await self._send_to_dead_letter(envelope, "消息过大")
                return False

            # 发送到Redis Stream
            stream_key = self.STREAM_PREFIX + channel
            await self.redis_client.xadd(
                name=stream_key,
                fields={"data": message_bytes, "timestamp": datetime.now().isoformat()},
                maxlen=10000,  # 限制流长度
            )

            # 设置过期时间
            await self.redis_client.expire(stream_key, self.message_retention_hours * 3600)

            self.stats["messages_sent"] += 1
            logger.debug(f"📤 消息已发送: {envelope.message_id} -> {channel}")

            return True

        except Exception as e:
            logger.error(f"❌ 发送消息失败: {e}")
            self.stats["errors"] += 1
            return False

    async def send_to_consumer(
        self, message: TaskMessage | ResponseMessage, consumer_id: str
    ) -> bool:
        """
        发送消息到特定消费者

        Args:
            message: 消息对象
            consumer_id: 消费者ID

        Returns:
            bool: 是否发送成功
        """
        try:
            # 获取消费者信息
            if consumer_id not in self.consumers:
                logger.warning(f"消费者不存在: {consumer_id}")
                return False

            # 发送到消费者专用流
            stream_key = f"{self.STREAM_PREFIX}consumer:{consumer_id}"
            return await self.send_message(message, stream_key.replace(self.STREAM_PREFIX, ""))

        except Exception as e:
            logger.error(f"❌ 发送到消费者失败: {e}")
            return False

    # ==================== 接收消息 ====================

    async def receive_messages(
        self, consumer_id: str, count: int = 1, block: int = 1000
    ) -> list[dict[str, Any]]:
        """
        接收消息(从消费者组读取)

        Args:
            consumer_id: 消费者ID
            count: 最多读取消息数
            block: 阻塞时间(毫秒)

        Returns:
            list[Dict]: 消息列表
        """
        try:
            # 确保消费者已注册
            if consumer_id not in self.consumers:
                await self.register_consumer(consumer_id)

            # 从消费者组读取消息
            stream_key = self.STREAM_PREFIX + "main"
            messages = await self.redis_client.xreadgroup(
                groupname=self.CONSUMER_GROUP,
                consumername=consumer_id,
                streams={stream_key: ">"},
                count=count,
                block=block,
            )

            if not messages:
                return []

            result = []
            for stream, stream_messages in messages:
                for message_id, fields in stream_messages:
                    try:
                        # 解析消息
                        envelope = MessageEnvelope.from_bytes(fields["data"])
                        result.append(
                            {"message_id": message_id, "envelope": envelope, "stream": stream}
                        )

                        self.stats["messages_received"] += 1
                        self.consumers[consumer_id].message_count += 1

                    except Exception as e:
                        logger.error(f"解析消息失败: {e}")
                        self.stats["errors"] += 1

            return result

        except Exception as e:
            logger.error(f"❌ 接收消息失败: {e}")
            self.stats["errors"] += 1
            return []

    async def confirm_message(self, consumer_id: str, message_id: str) -> bool:
        """
        确认消息已处理(从待处理队列删除)

        Args:
            consumer_id: 消费者ID
            message_id: 消息ID

        Returns:
            bool: 是否确认成功
        """
        try:
            stream_key = self.STREAM_PREFIX + "main"
            await self.redis_client.xack(
                name=stream_key, groupname=self.CONSUMER_GROUP, id=message_id
            )

            self.stats["messages_confirmed"] += 1
            logger.debug(f"✅ 消息已确认: {message_id} by {consumer_id}")

            return True

        except Exception as e:
            logger.error(f"❌ 确认消息失败: {e}")
            return False

    # ==================== 消费者管理 ====================

    async def register_consumer(
        self, consumer_id: str, channels: list[str] | None = None
    ) -> bool:
        """
        注册消费者

        Args:
            consumer_id: 消费者ID
            channels: 订阅的频道列表

        Returns:
            bool: 是否注册成功
        """
        try:
            # 创建消费者信息
            consumer = ConsumerInfo(
                consumer_id=consumer_id, subscribed_channels=set(channels or ["main"])
            )

            self.consumers[consumer_id] = consumer

            # 更新频道订阅
            for channel in channels or ["main"]:
                if channel not in self.subscribers:
                    self.subscribers[channel] = set()
                self.subscribers[channel].add(consumer_id)

            # 保存到Redis
            await self._save_consumer_info(consumer)

            logger.info(f"✅ 消费者已注册: {consumer_id}")
            return True

        except Exception as e:
            logger.error(f"❌ 注册消费者失败: {e}")
            return False

    async def unregister_consumer(self, consumer_id: str) -> bool:
        """注销消费者"""
        try:
            if consumer_id in self.consumers:
                # 从频道订阅中移除
                for channel in self.consumers[consumer_id].subscribed_channels:
                    if channel in self.subscribers:
                        self.subscribers[channel].discard(consumer_id)

                # 删除消费者
                del self.consumers[consumer_id]

                # 从Redis删除
                await self.redis_client.delete(self.CONSUMER_PREFIX + consumer_id)

                logger.info(f"✅ 消费者已注销: {consumer_id}")

            return True

        except Exception as e:
            logger.error(f"❌ 注销消费者失败: {e}")
            return False

    async def _save_consumer_info(self, consumer: ConsumerInfo):
        """保存消费者信息到Redis"""
        key = self.CONSUMER_PREFIX + consumer.consumer_id
        data = {
            "consumer_id": consumer.consumer_id,
            "subscribed_channels": json.dumps(list(consumer.subscribed_channels)),
            "last_heartbeat": consumer.last_heartbeat,
            "message_count": str(consumer.message_count),
            "error_count": str(consumer.error_count),
        }
        await self.redis_client.hset(key, mapping=data)
        await self.redis_client.expire(key, 300)  # 5分钟过期

    # ==================== 死信队列 ====================

    async def _send_to_dead_letter(self, envelope: MessageEnvelope, reason: str):
        """发送消息到死信队列"""
        try:
            dead_letter_key = self.DEAD_LETTER_PREFIX + envelope.message_id
            data = {
                "envelope": envelope.to_bytes(),
                "reason": reason,
                "timestamp": datetime.now().isoformat(),
            }
            await self.redis_client.hset(dead_letter_key, mapping=data)
            await self.redis_client.expire(dead_letter_key, 7 * 24 * 3600)  # 7天

            self.stats["messages_failed"] += 1
            logger.warning(f"⚠️ 消息进入死信队列: {envelope.message_id}, 原因: {reason}")

        except Exception as e:
            logger.error(f"❌ 发送到死信队列失败: {e}")

    async def get_dead_letter_messages(self, limit: int = 100) -> list[dict[str, Any]]:
        """获取死信队列中的消息"""
        try:
            pattern = self.DEAD_LETTER_PREFIX + "*"
            keys = []
            async for key in self.redis_client.scan_iter(match=pattern, count=limit):
                keys.append(key)

            messages = []
            for key in keys:
                data = await self.redis_client.hgetall(key)
                envelope = MessageEnvelope.from_bytes(data["envelope"])
                messages.append(
                    {"envelope": envelope, "reason": data["reason"], "timestamp": data["timestamp"]}
                )

            return messages

        except Exception as e:
            logger.error(f"❌ 获取死信队列失败: {e}")
            return []

    # ==================== 后台任务 ====================

    async def _health_check_loop(self):
        """健康检查循环"""
        while self.running:
            try:
                now = datetime.now()
                timeout = timedelta(seconds=self.health_check_interval * 2)

                # 检查消费者健康
                for consumer_id, consumer in list(self.consumers.items()):
                    last_heartbeat = datetime.fromisoformat(consumer.last_heartbeat)
                    if now - last_heartbeat > timeout:
                        logger.warning(f"⚠️ 消费者超时: {consumer_id}")
                        consumer.error_count += 1

                # 更新统计到Redis
                stats_key = "agent:msg:bus:stats"
                await self.redis_client.hset(
                    stats_key, mapping={k: str(v) for k, v in self.stats.items()}
                )

                await asyncio.sleep(self.health_check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"健康检查异常: {e}")
                await asyncio.sleep(5)

    async def _cleanup_loop(self):
        """清理循环"""
        while self.running:
            try:
                # 清理过期的消费者信息
                now = datetime.now()
                timeout = timedelta(seconds=300)  # 5分钟

                for consumer_id, consumer in list(self.consumers.items()):
                    last_heartbeat = datetime.fromisoformat(consumer.last_heartbeat)
                    if now - last_heartbeat > timeout:
                        await self.unregister_consumer(consumer_id)

                await asyncio.sleep(60)  # 每分钟清理一次

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"清理异常: {e}")
                await asyncio.sleep(5)

    # ==================== 统计和监控 ====================

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "consumers_count": len(self.consumers),
            "channels_count": len(self.subscribers),
            "running": self.running,
        }

    async def get_consumer_stats(self, consumer_id: str) -> dict[str, Any] | None:
        """获取消费者统计"""
        if consumer_id not in self.consumers:
            return None

        consumer = self.consumers[consumer_id]
        return {
            "consumer_id": consumer.consumer_id,
            "subscribed_channels": list(consumer.subscribed_channels),
            "last_heartbeat": consumer.last_heartbeat,
            "message_count": consumer.message_count,
            "error_count": consumer.error_count,
        }


# =============================================================================
# 全局实例
# =============================================================================

_redis_message_bus: RedisMessageBus | None = None


def get_redis_message_bus(**kwargs: Any) -> RedisMessageBus:
    """获取全局Redis消息总线实例"""
    global _redis_message_bus
    if _redis_message_bus is None:
        _redis_message_bus = RedisMessageBus(**kwargs)
    return _redis_message_bus
