#!/usr/bin/env python3
"""
持久化通信引擎包装器
Persistent Communication Engine Wrapper

为通信引擎添加持久化支持，而不修改原有代码。

功能特性：
- 消息持久化
- 自动恢复
- 死信队列处理
- 消息重试

作者: Athena平台团队
版本: 1.0.0
创建时间: 2026-01-28
"""

import logging
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

from core.communication.types import Message, MessageType, MessageStatus
from core.communication.persistence.base_persistence import MessageState
from core.communication.persistence.persistence_manager import PersistenceManager
from core.communication.persistence.queue_recovery import QueueRecoveryManager

logger = logging.getLogger(__name__)


class PersistentCommunicationEngine:
    """
    持久化通信引擎包装器

    包装现有的通信引擎，添加持久化能力。
    """

    def __init__(
        self,
        base_engine: Any,  # 现有的通信引擎实例
        persistence_config: dict[str, Any] | None = None,
        recovery_config: dict[str, Any] | None = None,
    ):
        """
        初始化持久化通信引擎

        Args:
            base_engine: 基础通信引擎实例
            persistence_config: 持久化配置
            recovery_config: 恢复配置
        """
        self.base_engine = base_engine
        self.persistence = PersistenceManager(persistence_config)
        self.recovery_manager: QueueRecoveryManager | None = None

        # 统计信息
        self._stats = {
            "messages_sent": 0,
            "messages_persisted": 0,
            "messages_recovered": 0,
            "retries_performed": 0,
        }

        self._initialized = False
        self._message_handler = None  # 消息处理回调

    async def initialize(self) -> bool:
        """
        初始化持久化通信引擎

        Returns:
            是否初始化成功
        """
        try:
            logger.info("🔄 初始化持久化通信引擎...")

            # 1. 初始化持久化后端
            if not await self.persistence.initialize():
                logger.error("持久化后端初始化失败")
                return False

            # 2. 创建恢复管理器
            self.recovery_manager = QueueRecoveryManager(
                self.persistence, recovery_config
            )

            # 3. 执行队列恢复
            recovery_stats = await self.recovery_manager.recover_all()
            self._stats["messages_recovered"] = (
                recovery_stats.get("recovered_pending", 0)
                + recovery_stats.get("recovered_processing", 0)
            )

            self._initialized = True
            logger.info("✅ 持久化通信引擎初始化完成")
            return True

        except Exception as e:
            logger.error(f"初始化持久化通信引擎失败: {e}")
            return False

    async def shutdown(self) -> bool:
        """
        关闭持久化通信引擎

        Returns:
            是否关闭成功
        """
        try:
            await self.persistence.shutdown()
            self._initialized = False
            logger.info("持久化通信引擎已关闭")
            return True
        except Exception as e:
            logger.error(f"关闭持久化通信引擎失败: {e}")
            return False

    def set_message_handler(self, handler: Callable):
        """
        设置消息处理器

        Args:
            handler: 消息处理回调函数
        """
        self._message_handler = handler

    async def send_message(
        self,
        sender: str,
        receiver: str,
        content: Any,
        message_type: MessageType = MessageType.TEXT,
        **kwargs,
    ) -> str:
        """
        发送消息（带持久化）

        Args:
            sender: 发送者ID
            receiver: 接收者ID
            content: 消息内容
            message_type: 消息类型
            **kwargs: 其他消息参数

        Returns:
            消息ID
        """
        if not self._initialized:
            raise RuntimeError("持久化通信引擎未初始化")

        # 1. 创建消息
        message = Message(
            id=self._generate_message_id(),
            type=message_type,
            sender=sender,
            receiver=receiver,
            content=content,
            **kwargs,
        )

        # 2. 持久化消息
        await self.persistence.save_message(message, MessageState.PENDING)
        self._stats["messages_persisted"] += 1

        # 3. 发送消息
        try:
            await self._send_to_base_engine(message)
            await self.persistence.update_message_state(
                message.id, MessageState.SENT
            )
            self._stats["messages_sent"] += 1
            logger.debug(f"消息已发送: {message.id}")
        except Exception as e:
            await self.persistence.update_message_state(
                message.id, MessageState.FAILED, str(e)
            )
            logger.error(f"发送消息失败: {message.id}, 错误: {e}")
            raise

        return message.id

    async def _send_to_base_engine(self, message: Message) -> None:
        """
        通过基础引擎发送消息

        Args:
            message: 消息对象
        """
        # 检查基础引擎是否有send_message方法
        if hasattr(self.base_engine, "send_message"):
            # 可能需要转换消息格式
            if hasattr(self.base_engine, "convert_message"):
                await self.base_engine.send_message(
                    self.base_engine.convert_message(message)
                )
            else:
                # 直接调用（假设兼容）
                await self.base_engine.send_message(
                    sender=message.sender,
                    receiver=message.receiver,
                    content=message.content,
                    message_type=message.type,
                    **message.metadata,
                )
        else:
            # 使用基础引擎的其他接口
            logger.warning("基础引擎不支持send_message，尝试备用方法")
            # 这里可以根据实际引擎的API进行适配

    async def receive_message(self, message_id: str) -> Message | None:
        """
        接收消息

        Args:
            message_id: 消息ID

        Returns:
            消息对象，如果不存在返回None
        """
        if not self._initialized:
            raise RuntimeError("持久化通信引擎未初始化")

        persisted = await self.persistence.get_message(message_id)
        if persisted:
            return persisted.message
        return None

    async def process_pending_messages(self) -> int:
        """
        处理所有待处理消息

        Returns:
            处理的消息数量
        """
        if not self._initialized:
            raise RuntimeError("持久化通信引擎未初始化")

        pending = await self.persistence.get_messages_by_state(
            MessageState.PENDING, limit=100
        )

        processed = 0
        for persisted in pending:
            try:
                # 更新为处理中
                await self.persistence.update_message_state(
                    persisted.message.id, MessageState.PROCESSING
                )

                # 调用消息处理器
                if self._message_handler:
                    await self._message_handler(persisted.message)

                # 更新为已处理
                await self.persistence.update_message_state(
                    persisted.message.id, MessageState.DELIVERED
                )
                processed += 1

            except Exception as e:
                await self.persistence.update_message_state(
                    persisted.message.id, MessageState.FAILED, str(e)
                )
                logger.error(f"处理消息失败: {persisted.message.id}, 错误: {e}")

        return processed

    async def retry_failed_messages(self) -> int:
        """
        重试失败的消息

        Returns:
            重试的消息数量
        """
        if not self._initialized:
            raise RuntimeError("持久化通信引擎未初始化")

        retried = await self.persistence.retry_failed_messages(max_retries=3)
        self._stats["retries_performed"] += retried
        return retried

    async def cleanup_expired_messages(self) -> int:
        """
        清理过期消息

        Returns:
            清理的消息数量
        """
        if not self._initialized:
            raise RuntimeError("持久化通信引擎未初始化")

        return await self.persistence.cleanup_expired_messages()

    async def get_queue_stats(self) -> dict[str, Any]:
        """
        获取队列统计信息

        Returns:
            统计信息字典
        """
        if not self._initialized:
            raise RuntimeError("持久化通信引擎未初始化")

        return {
            "pending": await self.persistence.get_queue_size(MessageState.PENDING),
            "processing": await self.persistence.get_queue_size(
                MessageState.PROCESSING
            ),
            "sent": await self.persistence.get_queue_size(MessageState.SENT),
            "failed": await self.persistence.get_queue_size(MessageState.FAILED),
            "dead_letter": await self.persistence.get_queue_size(
                MessageState.DEAD_LETTER
            ),
        }

    async def get_stats(self) -> dict[str, Any]:
        """
        获取引擎统计信息

        Returns:
            统计信息字典
        """
        return {
            **self._stats,
            "queue_stats": await self.get_queue_stats(),
            "recovery_stats": (
                await self.recovery_manager.get_recovery_stats()
                if self.recovery_manager
                else {}
            ),
        }

    def _generate_message_id(self) -> str:
        """生成消息ID"""
        import uuid

        return f"msg_{datetime.now().timestamp()}_{uuid.uuid4().hex[:8]}"


async def create_persistent_engine(
    base_engine: Any,
    persistence_backend: str = "memory",
    persistence_config: dict[str, Any] | None = None,
    recovery_config: dict[str, Any] | None = None,
) -> PersistentCommunicationEngine:
    """
    便捷函数：创建持久化通信引擎

    Args:
        base_engine: 基础通信引擎
        persistence_backend: 持久化后端（memory、redis、file）
        persistence_config: 持久化配置
        recovery_config: 恢复配置

    Returns:
        持久化通信引擎实例
    """
    engine = PersistentCommunicationEngine(
        base_engine,
        {"backend": persistence_backend, "backend_config": persistence_config},
        recovery_config,
    )
    await engine.initialize()
    return engine


__all__ = [
    "PersistentCommunicationEngine",
    "create_persistent_engine",
]
