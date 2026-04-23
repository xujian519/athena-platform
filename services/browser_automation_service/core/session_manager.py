#!/usr/bin/env python3
"""
会话管理器
Session Manager for Browser Automation Service

作者: 小诺·双鱼公主
版本: 1.0.0
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from config.settings import logger, settings
from playwright.async_api import BrowserContext, Page

from core.exceptions import SessionLimitExceededError, generate_error_id


@dataclass
class Session:
    """浏览器会话"""

    session_id: str
    context_id: str
    page: Page
    context: BrowserContext
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self, timeout_seconds: int | None = None) -> bool:
        """检查会话是否过期"""
        timeout = timeout_seconds or settings.SESSION_TIMEOUT
        return (datetime.now() - self.last_activity).total_seconds() > timeout

    def update_activity(self) -> None:
        """更新最后活动时间"""
        self.last_activity = datetime.now()


class SessionManager:
    """
    会话管理器

    管理浏览器会话的生命周期，支持会话创建、查询、删除和过期清理
    """

    def __init__(self):
        """初始化会话管理器"""
        self.sessions: dict[str, Session] = {}
        self._cleanup_task: asyncio.Task | None = None
        self._running = False
        self._total_created = 0  # 历史创建总数
        self._total_deleted = 0  # 历史删除总数

    async def create_session(
        self,
        page: Page,
        context: BrowserContext,
        context_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> Session:
        """
        创建新会话

        Args:
            page: 页面对象
            context: 浏览器上下文
            context_id: 上下文ID
            metadata: 元数据

        Returns:
            Session: 创建的会话

        Raises:
            SessionLimitExceededError: 会话数量超过限制
        """
        # 检查会话数量限制
        active_count = len(self.sessions)
        if active_count >= settings.MAX_CONCURRENT_SESSIONS:
            error_id = generate_error_id()
            logger.warning(
                f"⚠️ 会话数量已达上限: {active_count}/{settings.MAX_CONCURRENT_SESSIONS} "
                f"[{error_id}]"
            )
            raise SessionLimitExceededError(
                message=f"会话数量已达上限 ({settings.MAX_CONCURRENT_SESSIONS})",
                limit=settings.MAX_CONCURRENT_SESSIONS,
                details={
                    "current_count": active_count,
                    "error_id": error_id,
                },
            )

        session_id = str(uuid.uuid4())

        session = Session(
            session_id=session_id,
            context_id=context_id,
            page=page,
            context=context,
            metadata=metadata or {},
        )

        self.sessions[session_id] = session
        self._total_created += 1
        logger.info(f"✅ 创建会话: {session_id} (当前: {len(self.sessions)}/{settings.MAX_CONCURRENT_SESSIONS})")

        return session

    async def get_session(self, session_id: str) -> Session | None:
        """
        获取会话

        Args:
            session_id: 会话ID

        Returns:
            Session | None: 会话对象或None
        """
        session = self.sessions.get(session_id)
        if session:
            session.update_activity()
        return session

    async def get_or_create_default_session(
        self,
        page: Page,
        context: BrowserContext,
        context_id: str,
    ) -> Session:
        """
        获取或创建默认会话

        Args:
            page: 页面对象
            context: 浏览器上下文
            context_id: 上下文ID

        Returns:
            Session: 会话对象
        """
        # 查找默认会话
        for session in self.sessions.values():
            if session.context_id == context_id and not session.is_expired:
                session.update_activity()
                return session

        # 创建新会话
        return await self.create_session(page, context, context_id)

    async def delete_session(self, session_id: str) -> bool:
        """
        删除会话

        Args:
            session_id: 会话ID

        Returns:
            bool: 是否删除成功
        """
        session = self.sessions.pop(session_id, None)
        if session:
            try:
                await session.page.close()
            except Exception as e:
                logger.warning(f"关闭页面时出错: {e}")
            self._total_deleted += 1
            logger.info(f"🗑️  删除会话: {session_id}")
            return True
        return False

    async def list_sessions(self) -> list[dict[str, Any]:
        """
        列出所有会话

        Returns:
            list[dict]: 会话信息列表
        """
        return [
            {
                "session_id": s.session_id,
                "context_id": s.context_id,
                "created_at": s.created_at.isoformat(),
                "last_activity": s.last_activity.isoformat(),
                "is_expired": s.is_expired,
                "metadata": s.metadata,
            }
            for s in self.sessions.values()
        ]

    async def cleanup_expired_sessions(self) -> int:
        """
        清理过期会话

        Returns:
            int: 清理的会话数量
        """
        expired_sessions = [
            session_id
            for session_id, session in self.sessions.items()
            if session.is_expired
        ]

        for session_id in expired_sessions:
            await self.delete_session(session_id)

        if expired_sessions:
            logger.info(f"🧹 清理了 {len(expired_sessions)} 个过期会话")

        return len(expired_sessions)

    async def start_cleanup_task(self) -> None:
        """启动会话清理任务"""
        if self._running:
            return

        self._running = True

        async def cleanup_loop():
            while self._running:
                try:
                    await asyncio.sleep(settings.SESSION_CLEANUP_INTERVAL)
                    await self.cleanup_expired_sessions()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"清理任务出错: {e}")

        self._cleanup_task = asyncio.create_task(cleanup_loop())
        logger.info("🔄 会话清理任务已启动")

    async def stop_cleanup_task(self) -> None:
        """停止会话清理任务"""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
        logger.info("🛑 会话清理任务已停止")

    @property
    def active_count(self) -> int:
        """活跃会话数量"""
        return len(self.sessions)

    @property
    def total_count(self) -> int:
        """总会话数量（包括历史）"""
        return self._total_created

    async def shutdown(self) -> None:
        """关闭会话管理器"""
        # 停止清理任务
        await self.stop_cleanup_task()

        # 关闭所有会话
        for session_id in list(self.sessions.keys()):
            await self.delete_session(session_id)

        logger.info("🛑 会话管理器已关闭")


# 全局会话管理器实例
_session_manager: SessionManager | None = None


def get_session_manager() -> SessionManager:
    """获取全局会话管理器实例"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


# 导出
__all__ = [
    "Session",
    "SessionManager",
    "get_session_manager",
]
