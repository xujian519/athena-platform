#!/usr/bin/env python3
"""
WebSocket 端点处理器

实现 Gateway 的 WebSocket 端点，支持流式事件转发。

作者: Athena平台团队
创建时间: 2026-04-20
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Set

logger = logging.getLogger(__name__)


@dataclass
class WebSocketConnection:
    """WebSocket 连接"""

    connection_id: str
    websocket: Any  # websocket 对象
    session_id: str | None = None
    user_id: str | None = None
    connected_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)

    async def send(self, message: str | dict) -> None:
        """发送消息

        Args:
            message: 消息内容（字符串或字典）
        """
        if isinstance(message, dict):
            message = json.dumps(message, ensure_ascii=False)

        try:
            await self.websocket.send(message)
            self.last_activity = datetime.now()
        except Exception as e:
            logger.error(f"❌ 发送消息失败 ({self.connection_id}): {e}")
            raise

    async def close(self, code: int = 1000, reason: str = "") -> None:
        """关闭连接

        Args:
            code: 关闭代码
            reason: 关闭原因
        """
        try:
            await self.websocket.close(code=code, reason=reason)
            logger.info(f"🔌 连接已关闭: {self.connection_id}")
        except Exception as e:
            logger.error(f"❌ 关闭连接失败 ({self.connection_id}): {e}")


class WebSocketConnectionManager:
    """WebSocket 连接管理器

    管理所有 WebSocket 连接。
    """

    def __init__(self):
        """初始化连接管理器"""
        self._connections: Dict[str, WebSocketConnection] = {}
        self._session_connections: Dict[str, Set[str]] = {}  # session_id -> connection_ids
        self._lock = asyncio.Lock()

        logger.info("🔌 WebSocket 连接管理器已初始化")

    async def connect(
        self,
        websocket: Any,
        session_id: str | None = None,
        user_id: str | None = None,
    ) -> WebSocketConnection:
        """接受新连接

        Args:
            websocket: WebSocket 对象
            session_id: 会话 ID
            user_id: 用户 ID

        Returns:
            WebSocketConnection: 连接对象
        """
        connection_id = str(uuid.uuid4())

        connection = WebSocketConnection(
            connection_id=connection_id,
            websocket=websocket,
            session_id=session_id,
            user_id=user_id,
        )

        async with self._lock:
            self._connections[connection_id] = connection

            if session_id:
                if session_id not in self._session_connections:
                    self._session_connections[session_id] = set()
                self._session_connections[session_id].add(connection_id)

        logger.info(
            f"✅ 新连接建立: {connection_id} "
            f"(session: {session_id}, user: {user_id})"
        )

        # 发送欢迎消息
        await connection.send({
            "type": "connected",
            "connection_id": connection_id,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
        })

        return connection

    async def disconnect(self, connection_id: str) -> None:
        """断开连接

        Args:
            connection_id: 连接 ID
        """
        async with self._lock:
            connection = self._connections.get(connection_id)
            if not connection:
                logger.warning(f"⚠️ 连接不存在: {connection_id}")
                return

            # 从会话映射中移除
            if connection.session_id:
                self._session_connections[connection.session_id].discard(connection_id)
                if not self._session_connections[connection.session_id]:
                    del self._session_connections[connection.session_id]

            # 删除连接
            del self._connections[connection_id]

        logger.info(f"🔌 连接已断开: {connection_id}")

    async def send_to_connection(
        self,
        connection_id: str,
        message: str | dict,
    ) -> bool:
        """发送消息到指定连接

        Args:
            connection_id: 连接 ID
            message: 消息内容

        Returns:
            bool: 是否发送成功
        """
        connection = self._connections.get(connection_id)
        if not connection:
            logger.warning(f"⚠️ 连接不存在: {connection_id}")
            return False

        try:
            await connection.send(message)
            return True
        except Exception as e:
            logger.error(f"❌ 发送消息失败 ({connection_id}): {e}")
            await self.disconnect(connection_id)
            return False

    async def send_to_session(
        self,
        session_id: str,
        message: str | dict,
        exclude_connection: str | None = None,
    ) -> int:
        """发送消息到会话的所有连接

        Args:
            session_id: 会话 ID
            message: 消息内容
            exclude_connection: 排除的连接 ID

        Returns:
            int: 成功发送的连接数
        """
        connection_ids = self._session_connections.get(session_id, set())
        success_count = 0

        for connection_id in connection_ids:
            if exclude_connection and connection_id == exclude_connection:
                continue

            if await self.send_to_connection(connection_id, message):
                success_count += 1

        return success_count

    async def broadcast(
        self,
        message: str | dict,
        exclude_sessions: Set[str] | None = None,
    ) -> int:
        """广播消息到所有连接

        Args:
            message: 消息内容
            exclude_sessions: 排除的会话 ID 集合

        Returns:
            int: 成功发送的连接数
        """
        exclude_sessions = exclude_sessions or set()
        success_count = 0

        async with self._lock:
            for connection_id, connection in self._connections.items():
                if connection.session_id in exclude_sessions:
                    continue

                if await self.send_to_connection(connection_id, message):
                    success_count += 1

        return success_count

    async def close_connection(
        self,
        connection_id: str,
        code: int = 1000,
        reason: str = "",
    ) -> None:
        """关闭指定连接

        Args:
            connection_id: 连接 ID
            code: 关闭代码
            reason: 关闭原因
        """
        connection = self._connections.get(connection_id)
        if connection:
            await connection.close(code=code, reason=reason)
            await self.disconnect(connection_id)

    async def close_session(
        self,
        session_id: str,
        code: int = 1000,
        reason: str = "",
    ) -> int:
        """关闭会话的所有连接

        Args:
            session_id: 会话 ID
            code: 关闭代码
            reason: 关闭原因

        Returns:
            int: 关闭的连接数
        """
        connection_ids = self._session_connections.get(session_id, set()).copy()
        closed_count = 0

        for connection_id in connection_ids:
            await self.close_connection(connection_id, code, reason)
            closed_count += 1

        return closed_count

    def get_connection(self, connection_id: str) -> WebSocketConnection | None:
        """获取连接对象

        Args:
            connection_id: 连接 ID

        Returns:
            WebSocketConnection | None: 连接对象
        """
        return self._connections.get(connection_id)

    def get_session_connections(self, session_id: str) -> Set[str]:
        """获取会话的所有连接 ID

        Args:
            session_id: 会话 ID

        Returns:
            set[str]: 连接 ID 集合
        """
        return self._session_connections.get(session_id, set()).copy()

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息

        Returns:
            dict: 统计信息
        """
        return {
            "total_connections": len(self._connections),
            "total_sessions": len(self._session_connections),
            "connections_by_session": {
                session_id: len(connections)
                for session_id, connections in self._session_connections.items()
            },
        }


# 全局连接管理器单例
_global_connection_manager: WebSocketConnectionManager | None = None


def get_global_connection_manager() -> WebSocketConnectionManager:
    """获取全局连接管理器

    Returns:
        WebSocketConnectionManager: 全局连接管理器
    """
    global _global_connection_manager
    if _global_connection_manager is None:
        _global_connection_manager = WebSocketConnectionManager()
    return _global_connection_manager


__all__ = [
    "WebSocketConnection",
    "WebSocketConnectionManager",
    "get_global_connection_manager",
]
