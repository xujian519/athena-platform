#!/usr/bin/env python3
from __future__ import annotations
"""
消息持久化管理器
Message Persistence Manager

统一管理消息持久化后端，提供：
- 多后端支持（Redis、文件、内存）
- 自动降级机制
- 配置管理
- 健康检查

作者: Athena平台团队
版本: 1.0.0
创建时间: 2026-01-28
"""

import logging
from typing import Any

from .base_persistence import (
    BaseMessagePersistence,
    InMemoryPersistence,
    MessageState,
    PersistedMessage,
)
from .file_persistence import FilePersistence
from .redis_persistence import RedisPersistence

logger = logging.getLogger(__name__)


class PersistenceManager:
    """
    持久化管理器

    负责创建和管理消息持久化后端。
    """

    # 后端类型
    BACKEND_MEMORY = "memory"
    BACKEND_REDIS = "redis"
    BACKEND_FILE = "file"

    def __init__(self, config: dict[str, Any] | None = None):
        """
        初始化持久化管理器

        Args:
            config: 配置参数
                - backend: 后端类型（memory、redis、file）
                - backend_config: 后端特定配置
                - auto_init: 是否自动初始化（默认：True）
        """
        self.config = config or {}
        self.backend_type = self.config.get("backend", self.BACKEND_MEMORY)
        self.backend_config = self.config.get("backend_config", {})
        self.backend: BaseMessagePersistence | None = None
        self._initialized = False

    async def initialize(self) -> bool:
        """
        初始化持久化后端

        Returns:
            是否初始化成功
        """
        if self._initialized:
            return True

        try:
            # 创建后端实例
            self.backend = self._create_backend(self.backend_type, self.backend_config)

            # 初始化后端
            if not await self.backend.initialize():
                logger.error("持久化后端初始化失败")
                return False

            self._initialized = True
            logger.info(f"持久化管理器初始化成功: {self.backend_type}")
            return True

        except Exception as e:
            logger.error(f"持久化管理器初始化失败: {e}")
            return False

    async def shutdown(self) -> bool:
        """
        关闭持久化管理器

        Returns:
            是否关闭成功
        """
        if self.backend:
            return await self.backend.shutdown()
        return True

    def _create_backend(
        self, backend_type: str, config: dict[str, Any]
    ) -> BaseMessagePersistence:
        """
        创建持久化后端实例

        Args:
            backend_type: 后端类型
            config: 配置参数

        Returns:
            持久化后端实例
        """
        if backend_type == self.BACKEND_REDIS:
            return RedisPersistence(config)
        elif backend_type == self.BACKEND_FILE:
            return FilePersistence(config)
        else:
            logger.warning(f"未知后端类型 {backend_type}，使用内存后端")
            return InMemoryPersistence(config)

    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            是否健康
        """
        if not self._initialized or not self.backend:
            return False

        try:
            # 尝试获取队列大小
            await self.backend.get_queue_size()
            return True
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return False

    # 委托方法到后端

    async def save_message(
        self, message, state: MessageState = MessageState.PENDING
    ) -> bool:
        """保存消息"""
        if not self._initialized:
            raise RuntimeError("持久化管理器未初始化")
        return await self.backend.save_message(message, state)

    async def get_message(self, message_id: str) -> PersistedMessage | None:
        """获取消息"""
        if not self._initialized:
            raise RuntimeError("持久化管理器未初始化")
        return await self.backend.get_message(message_id)

    async def update_message_state(
        self, message_id: str, state: MessageState, error_message: str | None = None
    ) -> bool:
        """更新消息状态"""
        if not self._initialized:
            raise RuntimeError("持久化管理器未初始化")
        return await self.backend.update_message_state(
            message_id, state, error_message
        )

    async def increment_attempt(self, message_id: str) -> bool:
        """增加尝试次数"""
        if not self._initialized:
            raise RuntimeError("持久化管理器未初始化")
        return await self.backend.increment_attempt(message_id)

    async def delete_message(self, message_id: str) -> bool:
        """删除消息"""
        if not self._initialized:
            raise RuntimeError("持久化管理器未初始化")
        return await self.backend.delete_message(message_id)

    async def get_messages_by_state(
        self, state: MessageState, limit: int = 100
    ) -> list[PersistedMessage]:
        """按状态获取消息"""
        if not self._initialized:
            raise RuntimeError("持久化管理器未初始化")
        return await self.backend.get_messages_by_state(state, limit)

    async def get_expired_messages(self) -> list[PersistedMessage]:
        """获取过期消息"""
        if not self._initialized:
            raise RuntimeError("持久化管理器未初始化")
        return await self.backend.get_expired_messages()

    async def get_failed_messages(self) -> list[PersistedMessage]:
        """获取失败消息"""
        if not self._initialized:
            raise RuntimeError("持久化管理器未初始化")
        return await self.backend.get_failed_messages()

    async def move_to_dead_letter(
        self, message_id: str, reason: str
    ) -> bool:
        """移至死信队列"""
        if not self._initialized:
            raise RuntimeError("持久化管理器未初始化")
        return await self.backend.move_to_dead_letter(message_id, reason)

    async def get_dead_letter_messages(self) -> list[PersistedMessage]:
        """获取死信消息"""
        if not self._initialized:
            raise RuntimeError("持久化管理器未初始化")
        return await self.backend.get_dead_letter_messages()

    async def clear_dead_letter(self, older_than) -> int:
        """清理死信队列"""
        if not self._initialized:
            raise RuntimeError("持久化管理器未初始化")
        return await self.backend.clear_dead_letter(older_than)

    async def get_queue_size(self, state: MessageState | None = None) -> int:
        """获取队列大小"""
        if not self._initialized:
            raise RuntimeError("持久化管理器未初始化")
        return await self.backend.get_queue_size(state)


def create_persistence_manager(
    backend_type: str = "memory", backend_config: dict[str, Any] | None = None
) -> PersistenceManager:
    """
    便捷函数：创建持久化管理器

    Args:
        backend_type: 后端类型（memory、redis、file）
        backend_config: 后端配置

    Returns:
        持久化管理器实例
    """
    return PersistenceManager(
        {"backend": backend_type, "backend_config": backend_config or {}}
    )


# 为保持兼容性，提供 get_persistence_manager 作为别名
get_persistence_manager = create_persistence_manager


__all__ = [
    "PersistenceManager",
    "create_persistence_manager",
    "get_persistence_manager",  # 别名
]
