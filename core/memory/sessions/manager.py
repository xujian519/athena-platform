#!/usr/bin/env python3
"""
会话管理器

管理Agent的会话状态和记忆持久化。

作者: Athena平台团队
创建时间: 2026-04-21
"""
from __future__ import annotations

import logging
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from .types import (
    SessionMessage,
    SessionContext,
    SessionStatus,
    MessageRole,
    SessionMemory,
    SessionSummary,
)
from .storage import SessionStorage

logger = logging.getLogger(__name__)


class SessionManager:
    """会话管理器

    管理多个会话的创建、查询、更新和删除。
    """

    def __init__(
        self,
        storage: SessionStorage | None = None,
        session_timeout: int = 3600,
    ):
        """初始化会话管理器

        Args:
            storage: 会话存储（None表示使用内存存储）
            session_timeout: 会话超时时间（秒）
        """
        self.storage = storage
        self.session_timeout = session_timeout
        self._sessions: dict[str, SessionMemory] = {}
        logger.info("🧠 会话管理器已初始化")

    def create_session(
        self,
        session_id: str,
        user_id: str,
        agent_id: str,
        metadata: dict[str, any] | None = None,
    ) -> SessionMemory:
        """创建新会话

        Args:
            session_id: 会话ID
            user_id: 用户ID
            agent_id: Agent ID
            metadata: 元数据

        Returns:
            SessionMemory: 会话记忆
        """
        context = SessionContext(
            session_id=session_id,
            user_id=user_id,
            agent_id=agent_id,
            metadata=metadata or {},
        )

        memory = SessionMemory(context=context)
        self._sessions[session_id] = memory

        logger.info(f"✅ 创建会话: {session_id}")
        return memory

    def get_session(self, session_id: str) -> SessionMemory | None:
        """获取会话

        Args:
            session_id: 会话ID

        Returns:
            SessionMemory | None: 会话记忆
        """
        return self._sessions.get(session_id)

    def close_session(self, session_id: str) -> bool:
        """关闭会话

        Args:
            session_id: 会话ID

        Returns:
            bool: 是否成功关闭
        """
        memory = self.get_session(session_id)
        if memory:
            memory.context.status = SessionStatus.CLOSED
            logger.info(f"🔒 关闭会话: {session_id}")

            # 保存到存储
            if self.storage:
                self.storage.save(memory)

            return True
        return False

    def delete_session(self, session_id: str) -> bool:
        """删除会话

        Args:
            session_id: 会话ID

        Returns:
            bool: 是否成功删除
        """
        if session_id in self._sessions:
            del self._sessions[session_id]

            # 从存储删除
            if self.storage:
                self.storage.delete(session_id)

            logger.info(f"🗑️ 删除会话: {session_id}")
            return True
        return False

    def add_message(
        self,
        session_id: str,
        role: MessageRole,
        content: str,
        token_count: int = 0,
        metadata: dict[str, any] | None = None,
    ) -> SessionMessage | None:
        """添加消息到会话

        Args:
            session_id: 会话ID
            role: 消息角色
            content: 消息内容
            token_count: token数量
            metadata: 元数据

        Returns:
            SessionMessage | None: 消息对象
        """
        memory = self.get_session(session_id)
        if not memory:
            logger.warning(f"⚠️ 会话不存在: {session_id}")
            return None

        message = SessionMessage(
            role=role,
            content=content,
            token_count=token_count,
            metadata=metadata or {},
        )

        memory.add_message(message)
        logger.debug(f"💬 添加消息到会话 {session_id}: {role.value}")

        return message

    def get_session_messages(
        self,
        session_id: str,
        count: int | None = None,
        role: MessageRole | None = None,
    ) -> list[SessionMessage]:
        """获取会话消息

        Args:
            session_id: 会话ID
            count: 消息数量（None表示全部）
            role: 消息角色（None表示所有）

        Returns:
            list[SessionMessage]: 消息列表
        """
        memory = self.get_session(session_id)
        if not memory:
            return []

        if count is None:
            messages = memory.messages
        else:
            messages = memory.get_recent_messages(count=count)

        if role:
            messages = [m for m in messages if m.role == role]

        return messages

    def get_active_sessions(self, user_id: str | None = None) -> list[SessionMemory]:
        """获取活跃会话

        Args:
            user_id: 用户ID（None表示所有用户）

        Returns:
            list[SessionMemory]: 活跃会话列表
        """
        active_sessions = []

        for memory in self._sessions.values():
            if memory.context.status == SessionStatus.ACTIVE:
                if user_id is None or memory.context.user_id == user_id:
                    active_sessions.append(memory)

        return active_sessions

    def cleanup_expired_sessions(self) -> int:
        """清理过期会话

        Returns:
            int: 清理的会话数量
        """
        expired_count = 0
        expired_sessions = []

        for session_id, memory in self._sessions.items():
            if memory.context.is_expired(self.session_timeout):
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            if self.close_session(session_id):
                expired_count += 1

        if expired_count > 0:
            logger.info(f"🧹 清理了 {expired_count} 个过期会话")

        return expired_count

    def get_session_stats(self) -> dict[str, any]:
        """获取会话统计信息

        Returns:
            dict: 统计信息
        """
        total_sessions = len(self._sessions)
        active_sessions = len([s for s in self._sessions.values() if s.context.status == SessionStatus.ACTIVE])
        total_messages = sum(len(s.messages) for s in self._sessions.values())
        total_tokens = sum(s.context.total_tokens for s in self._sessions.values())

        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "total_messages": total_messages,
            "total_tokens": total_tokens,
        }

    def generate_session_summary(
        self,
        session_id: str,
        title: str,
        summary: str,
        key_points: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> SessionSummary | None:
        """生成会话摘要

        Args:
            session_id: 会话ID
            title: 标题
            summary: 摘要
            key_points: 关键点
            tags: 标签

        Returns:
            SessionSummary | None: 会话摘要
        """
        memory = self.get_session(session_id)
        if not memory:
            return None

        summary_obj = SessionSummary(
            session_id=session_id,
            title=title,
            summary=summary,
            key_points=key_points or [],
            tags=tags or [],
            message_count=len(memory.messages),
        )

        memory.summary = summary_obj
        logger.info(f"📝 生成会话摘要: {session_id}")

        return summary_obj


__all__ = [
    "SessionManager",
]
