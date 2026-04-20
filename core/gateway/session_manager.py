#!/usr/bin/env python3
"""
会话管理器

管理 Gateway 的会话生命周期和状态。

作者: Athena平台团队
创建时间: 2026-04-20
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict

logger = logging.getLogger(__name__)


@dataclass
class Session:
    """会话"""

    session_id: str
    user_id: str | None = None
    agent_name: str = "xiaona"
    agent_type: str = "legal"
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    state: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def update_activity(self) -> None:
        """更新最后活动时间"""
        self.last_activity = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典

        Returns:
            dict: 会话信息
        """
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "agent_name": self.agent_name,
            "agent_type": self.agent_type,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "state": self.state,
            "metadata": self.metadata,
        }


class SessionManager:
    """会话管理器

    管理所有会话的生命周期。
    """

    def __init__(self, session_timeout: float = 3600.0):
        """初始化会话管理器

        Args:
            session_timeout: 会话超时时间（秒）
        """
        self._sessions: Dict[str, Session] = {}
        self._session_timeout = session_timeout
        self._lock = asyncio.Lock()

        logger.info(f"📋 会话管理器已初始化 (超时: {session_timeout}秒)")

    async def create_session(
        self,
        user_id: str | None = None,
        agent_name: str = "xiaona",
        agent_type: str = "legal",
        metadata: Dict[str, Any] | None = None,
    ) -> Session:
        """创建新会话

        Args:
            user_id: 用户 ID
            agent_name: 代理名称
            agent_type: 代理类型
            metadata: 元数据

        Returns:
            Session: 会话对象
        """
        session_id = str(uuid.uuid4())

        session = Session(
            session_id=session_id,
            user_id=user_id,
            agent_name=agent_name,
            agent_type=agent_type,
            metadata=metadata or {},
        )

        async with self._lock:
            self._sessions[session_id] = session

        logger.info(f"✅ 新会话已创建: {session_id} (user: {user_id}, agent: {agent_name})")

        return session

    async def get_session(self, session_id: str) -> Session | None:
        """获取会话

        Args:
            session_id: 会话 ID

        Returns:
            Session | None: 会话对象
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.update_activity()
            return session

    async def update_session(
        self,
        session_id: str,
        state: Dict[str, Any] | None = None,
        metadata: Dict[str, Any] | None = None,
    ) -> Session | None:
        """更新会话

        Args:
            session_id: 会话 ID
            state: 会话状态
            metadata: 元数据

        Returns:
            Session | None: 更新后的会话对象
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                logger.warning(f"⚠️ 会话不存在: {session_id}")
                return None

            if state:
                session.state.update(state)

            if metadata:
                session.metadata.update(metadata)

            session.update_activity()

            logger.debug(f"📝 会话已更新: {session_id}")
            return session

    async def delete_session(self, session_id: str) -> bool:
        """删除会话

        Args:
            session_id: 会话 ID

        Returns:
            bool: 是否删除成功
        """
        async with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                logger.info(f"🗑️ 会话已删除: {session_id}")
                return True
            return False

    async def cleanup_expired_sessions(self) -> int:
        """清理过期会话

        Returns:
            int: 清理的会话数
        """
        import time

        now = datetime.now()
        expired_sessions = []

        async with self._lock:
            for session_id, session in self._sessions.items():
                elapsed = (now - session.last_activity).total_seconds()
                if elapsed > self._session_timeout:
                    expired_sessions.append(session_id)

            for session_id in expired_sessions:
                del self._sessions[session_id]

        if expired_sessions:
            logger.info(f"🧹 清理了 {len(expired_sessions)} 个过期会话")

        return len(expired_sessions)

    async def get_all_sessions(self) -> list[Session]:
        """获取所有会话

        Returns:
            list[Session]: 会话列表
        """
        async with self._lock:
            return list(self._sessions.values())

    async def get_user_sessions(self, user_id: str) -> list[Session]:
        """获取用户的所有会话

        Args:
            user_id: 用户 ID

        Returns:
            list[Session]: 会话列表
        """
        async with self._lock:
            return [
                session
                for session in self._sessions.values()
                if session.user_id == user_id
            ]

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息

        Returns:
            dict: 统计信息
        """
        return {
            "total_sessions": len(self._sessions),
            "session_timeout": self._session_timeout,
        }

    async def start_cleanup_task(self, interval: float = 300.0) -> None:
        """启动会话清理任务

        Args:
            interval: 清理间隔（秒）
        """
        while True:
            try:
                await asyncio.sleep(interval)
                await self.cleanup_expired_sessions()
            except asyncio.CancelledError:
                logger.info("🛑 会话清理任务已停止")
                break
            except Exception as e:
                logger.error(f"❌ 会话清理任务错误: {e}")


# 全局会话管理器单例
_global_session_manager: SessionManager | None = None


def get_global_session_manager() -> SessionManager:
    """获取全局会话管理器

    Returns:
        SessionManager: 全局会话管理器
    """
    global _global_session_manager
    if _global_session_manager is None:
        _global_session_manager = SessionManager()
    return _global_session_manager


__all__ = [
    "Session",
    "SessionManager",
    "get_global_session_manager",
]
