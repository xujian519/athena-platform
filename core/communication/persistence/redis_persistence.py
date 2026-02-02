#!/usr/bin/env python3
"""
Redis消息持久化实现
Redis Message Persistence Implementation

使用Redis作为消息持久化后端，提供高性能、可靠的消息存储。

功能特性：
- 消息持久化
- 消息状态跟踪
- 过期消息自动清理
- 死信队列管理
- 消息重试机制

作者: Athena平台团队
版本: 1.0.0
创建时间: 2026-01-28
"""

import json
import logging
from datetime import datetime
from typing import Any

from core.communication.types import Message
from .base_persistence import (
    BaseMessagePersistence,
    InMemoryPersistence,
    MessageState,
    PersistedMessage,
)

logger = logging.getLogger(__name__)


class RedisPersistence(BaseMessagePersistence):
    """
    Redis持久化实现

    使用Redis Sorted Set和Hash实现消息队列和状态管理。
    """

    # Redis键前缀
    KEY_PREFIX = "athena:msg"
    MESSAGE_DATA_KEY = f"{KEY_PREFIX}:data"  # Hash: message_id -> JSON
    MESSAGE_STATE_KEY = f"{KEY_PREFIX}:state"  # Sorted Set: score=timestamp
    DEAD_LETTER_KEY = f"{KEY_PREFIX}:dead"  # Sorted Set: score=timestamp
    INDEX_KEY = f"{KEY_PREFIX}:index"  # Hash: state -> set of message_ids

    def __init__(self, config: dict[str, Any] | None = None):
        """
        初始化Redis持久化

        Args:
            config: 配置参数
                - host: Redis主机地址（默认：localhost）
                - port: Redis端口（默认：6379）
                - db: Redis数据库编号（默认：0）
                - password: Redis密码（可选）
                - message_ttl: 消息默认TTL（秒，默认：86400=1天）
                - dead_letter_ttl: 死信TTL（秒，默认：604800=7天）
        """
        super().__init__(config)
        self._redis = None
        self._fallback = None  # 降级到内存存储

        # 配置参数
        self.host = config.get("host", "localhost")
        self.port = config.get("port", 6379)
        self.db = config.get("db", 0)
        self.password = config.get("password")
        self.message_ttl = config.get("message_ttl", 86400)
        self.dead_letter_ttl = config.get("dead_letter_ttl", 604800)

    async def initialize(self) -> bool:
        """初始化Redis连接"""
        try:
            import redis.asyncio as aioredis

            self._redis = await aioredis.from_url(
                f"redis://{self.host}:{self.port}/{self.db}",
                password=self.password,
                encoding="utf-8",
                decode_responses=True,
            )
            # 测试连接
            await self._redis.ping()
            self.logger.info(
                f"Redis持久化初始化成功: {self.host}:{self.port}/{self.db}"
            )
            return True

        except ImportError:
            self.logger.warning("redis模块未安装，降级到内存持久化")
            self._fallback = InMemoryPersistence(self.config)
            return await self._fallback.initialize()

        except Exception as e:
            self.logger.error(f"Redis连接失败: {e}，降级到内存持久化")
            self._fallback = InMemoryPersistence(self.config)
            return await self._fallback.initialize()

    async def shutdown(self) -> bool:
        """关闭Redis连接"""
        if self._redis:
            await self._redis.close()
            self.logger.info("Redis连接已关闭")
            return True
        if self._fallback:
            return await self._fallback.shutdown()
        return True

    def _use_fallback(self):
        """检查是否使用降级存储"""
        return self._fallback is not None

    def _get_message_key(self, message_id: str) -> str:
        """获取消息数据键"""
        return f"{self.MESSAGE_DATA_KEY}:{message_id}"

    def _get_state_key(self, state: MessageState) -> str:
        """获取状态队列键"""
        return f"{self.MESSAGE_STATE_KEY}:{state.value}"

    async def save_message(
        self, message: Message, state: MessageState = MessageState.PENDING
    ) -> bool:
        """保存消息"""
        if self._use_fallback():
            return await self._fallback.save_message(message, state)

        try:
            persisted = PersistedMessage(message=message, state=state)
            pipe = self._redis.pipeline()

            # 保存消息数据
            message_key = self._get_message_key(message.id)
            pipe.hset(
                self.MESSAGE_DATA_KEY,
                message.id,
                json.dumps(persisted.to_dict()),
            )
            pipe.expire(message_key, self.message_ttl)

            # 添加到状态队列
            state_key = self._get_state_key(state)
            pipe.zadd(state_key, {message.id: datetime.now().timestamp()})

            # 更新索引
            pipe.hset(self.INDEX_KEY, message.id, state.value)

            await pipe.execute()
            return True

        except Exception as e:
            self.logger.error(f"保存消息失败: {e}")
            return False

    async def get_message(self, message_id: str) -> PersistedMessage | None:
        """获取消息"""
        if self._use_fallback():
            return await self._fallback.get_message(message_id)

        try:
            data = await self._redis.hget(self.MESSAGE_DATA_KEY, message_id)
            if not data:
                return None
            return PersistedMessage.from_dict(json.loads(data))
        except Exception as e:
            self.logger.error(f"获取消息失败: {e}")
            return None

    async def update_message_state(
        self, message_id: str, state: MessageState, error_message: str | None = None
    ) -> bool:
        """更新消息状态"""
        if self._use_fallback():
            return await self._fallback.update_message_state(
                message_id, state, error_message
            )

        try:
            # 获取当前消息
            current_state_str = await self._redis.hget(self.INDEX_KEY, message_id)
            if not current_state_str:
                return False

            current_state = MessageState(current_state_str)
            persisted = await self.get_message(message_id)
            if not persisted:
                return False

            # 更新状态
            persisted.state = state
            persisted.updated_at = datetime.now()
            if error_message:
                persisted.error_message = error_message

            pipe = self._redis.pipeline()

            # 更新消息数据
            await self._redis.hset(
                self.MESSAGE_DATA_KEY,
                message_id,
                json.dumps(persisted.to_dict()),
            )

            # 从旧状态队列移除
            old_state_key = self._get_state_key(current_state)
            pipe.zrem(old_state_key, message_id)

            # 添加到新状态队列
            new_state_key = self._get_state_key(state)
            pipe.zadd(new_state_key, {message_id: datetime.now().timestamp()})

            # 更新索引
            pipe.hset(self.INDEX_KEY, message_id, state.value)

            await pipe.execute()
            return True

        except Exception as e:
            self.logger.error(f"更新消息状态失败: {e}")
            return False

    async def increment_attempt(self, message_id: str) -> bool:
        """增加尝试次数"""
        if self._use_fallback():
            return await self._fallback.increment_attempt(message_id)

        try:
            persisted = await self.get_message(message_id)
            if not persisted:
                return False

            persisted.attempt_count += 1
            persisted.updated_at = datetime.now()

            await self._redis.hset(
                self.MESSAGE_DATA_KEY,
                message_id,
                json.dumps(persisted.to_dict()),
            )
            return True

        except Exception as e:
            self.logger.error(f"增加尝试次数失败: {e}")
            return False

    async def delete_message(self, message_id: str) -> bool:
        """删除消息"""
        if self._use_fallback():
            return await self._fallback.delete_message(message_id)

        try:
            # 获取当前状态
            state_str = await self._redis.hget(self.INDEX_KEY, message_id)
            pipe = self._redis.pipeline()

            # 删除消息数据
            pipe.hdel(self.MESSAGE_DATA_KEY, message_id)

            # 从状态队列移除
            if state_str:
                state_key = self._get_state_key(MessageState(state_str))
                pipe.zrem(state_key, message_id)

            # 删除索引
            pipe.hdel(self.INDEX_KEY, message_id)

            await pipe.execute()
            return True

        except Exception as e:
            self.logger.error(f"删除消息失败: {e}")
            return False

    async def get_messages_by_state(
        self, state: MessageState, limit: int = 100
    ) -> list[PersistedMessage]:
        """按状态获取消息"""
        if self._use_fallback():
            return await self._fallback.get_messages_by_state(state, limit)

        try:
            state_key = self._get_state_key(state)
            # 获取最早的消息（按时间戳）
            message_ids = await self._redis.zrange(state_key, 0, limit - 1)

            messages = []
            for mid in message_ids:
                msg = await self.get_message(mid)
                if msg:
                    messages.append(msg)

            return messages

        except Exception as e:
            self.logger.error(f"按状态获取消息失败: {e}")
            return []

    async def get_expired_messages(self) -> list[PersistedMessage]:
        """获取过期消息"""
        if self._use_fallback():
            return await self._fallback.get_expired_messages()

        try:
            now = datetime.now().timestamp()
            expired = []

            # 检查所有状态队列
            for state in MessageState:
                state_key = self._get_state_key(state)
                # 获取所有过期消息
                message_ids = await self._redis.zrangebyscore(
                    state_key, min=0, max=now
                )

                for mid in message_ids:
                    msg = await self.get_message(mid)
                    if msg and msg.expires_at and msg.expires_at < datetime.now():
                        expired.append(msg)

            return expired

        except Exception as e:
            self.logger.error(f"获取过期消息失败: {e}")
            return []

    async def get_failed_messages(self) -> list[PersistedMessage]:
        """获取失败消息"""
        return await self.get_messages_by_state(MessageState.FAILED, limit=1000)

    async def move_to_dead_letter(
        self, message_id: str, reason: str
    ) -> bool:
        """移至死信队列"""
        if self._use_fallback():
            return await self._fallback.move_to_dead_letter(message_id, reason)

        try:
            persisted = await self.get_message(message_id)
            if not persisted:
                return False

            pipe = self._redis.pipeline()

            # 更新状态和元数据
            persisted.state = MessageState.DEAD_LETTER
            persisted.updated_at = datetime.now()
            persisted.metadata["dead_letter_reason"] = reason

            # 保存更新
            await self._redis.hset(
                self.MESSAGE_DATA_KEY,
                message_id,
                json.dumps(persisted.to_dict()),
            )

            # 从当前状态队列移除
            current_state = await self._redis.hget(self.INDEX_KEY, message_id)
            if current_state:
                old_state_key = self._get_state_key(MessageState(current_state))
                pipe.zrem(old_state_key, message_id)

            # 添加到死信队列
            pipe.zadd(
                self.DEAD_LETTER_KEY, {message_id: datetime.now().timestamp()}
            )
            pipe.expire(self.DEAD_LETTER_KEY, self.dead_letter_ttl)

            # 更新索引
            pipe.hset(self.INDEX_KEY, message_id, MessageState.DEAD_LETTER.value)

            await pipe.execute()
            return True

        except Exception as e:
            self.logger.error(f"移至死信队列失败: {e}")
            return False

    async def get_dead_letter_messages(self) -> list[PersistedMessage]:
        """获取死信消息"""
        if self._use_fallback():
            return await self._fallback.get_dead_letter_messages()

        try:
            message_ids = await self._redis.zrevrange(
                self.DEAD_LETTER_KEY, 0, 999
            )

            messages = []
            for mid in message_ids:
                msg = await self.get_message(mid)
                if msg:
                    messages.append(msg)

            return messages

        except Exception as e:
            self.logger.error(f"获取死信消息失败: {e}")
            return []

    async def clear_dead_letter(self, older_than: datetime | None = None) -> int:
        """清理死信队列"""
        if self._use_fallback():
            return await self._fallback.clear_dead_letter(older_than)

        try:
            if older_than is None:
                # 清理全部
                count = await self._redis.zcard(self.DEAD_LETTER_KEY)
                await self._redis.delete(self.DEAD_LETTER_KEY)
                return count
            else:
                # 清理指定时间之前的
                timestamp = older_than.timestamp()
                message_ids = await self._redis.zrangebyscore(
                    self.DEAD_LETTER_KEY, min=0, max=timestamp
                )

                if message_ids:
                    pipe = self._redis.pipeline()
                    for mid in message_ids:
                        pipe.zrem(self.DEAD_LETTER_KEY, mid)
                        pipe.hdel(self.INDEX_KEY, mid)
                        pipe.hdel(self.MESSAGE_DATA_KEY, mid)
                    await pipe.execute()

                return len(message_ids)

        except Exception as e:
            self.logger.error(f"清理死信队列失败: {e}")
            return 0

    async def get_queue_size(self, state: MessageState | None = None) -> int:
        """获取队列大小"""
        if self._use_fallback():
            return await self._fallback.get_queue_size(state)

        try:
            if state is None:
                return await self._redis.hlen(self.INDEX_KEY)
            state_key = self._get_state_key(state)
            return await self._redis.zcard(state_key)

        except Exception as e:
            self.logger.error(f"获取队列大小失败: {e}")
            return 0


__all__ = ["RedisPersistence"]
