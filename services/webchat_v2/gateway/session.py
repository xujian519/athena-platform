#!/usr/bin/env python3
"""
Gateway会话管理

管理WebSocket连接和会话状态

作者: Athena平台团队
创建时间: 2025-01-31
版本: 2.0.1
"""

import asyncio
import uuid
from typing import Dict, Optional, Set
from fastapi import WebSocket


class GatewaySession:
    """Gateway会话"""

    def __init__(
        self,
        websocket: WebSocket,
        session_id: str,
        user_id: str
    ):
        """
        初始化会话

        Args:
            websocket: WebSocket连接实例
            session_id: 会话ID
            user_id: 用户ID
        """
        self.websocket = websocket
        self.session_id = session_id
        self.user_id = user_id
        self.connected = True
        self.subscriptions: Set[str] = set()  # 事件订阅

        # 配置项
        self.thinking_enabled: bool = False
        self.verbose_enabled: bool = False
        self.model: Optional[str] = None

    async def send_json(self, data: dict) -> bool:
        """
        发送JSON数据

        Args:
            data: 要发送的数据

        Returns:
            是否发送成功
        """
        if not self.connected:
            return False

        try:
            await self.websocket.send_json(data)
            return True
        except Exception:
            self.connected = False
            return False

    def subscribe(self, event_type: str) -> None:
        """订阅事件"""
        self.subscriptions.add(event_type)

    def unsubscribe(self, event_type: str) -> None:
        """取消订阅"""
        self.subscriptions.discard(event_type)

    def is_subscribed(self, event_type: str) -> bool:
        """检查是否订阅了事件"""
        return event_type in self.subscriptions

    def disconnect(self) -> None:
        """断开连接"""
        self.connected = False
        self.subscriptions.clear()


class GatewaySessionManager:
    """Gateway会话管理器（带线程安全保护）"""

    def __init__(self):
        self.sessions: Dict[str, GatewaySession] = {}  # session_id -> session
        self.user_sessions: Dict[str, Set[str]] = {}    # user_id -> set of session_ids
        self._lock: asyncio.Lock = asyncio.Lock()       # 异步锁保护

    async def create_session(
        self,
        websocket: WebSocket,
        user_id: str,
        session_id: Optional[str] = None
    ) -> GatewaySession:
        """
        创建新会话（线程安全）

        Args:
            websocket: WebSocket连接实例
            user_id: 用户ID
            session_id: 会话ID（可选，默认自动生成）

        Returns:
            创建的会话对象
        """
        if not session_id:
            session_id = str(uuid.uuid4())

        session = GatewaySession(
            websocket=websocket,
            session_id=session_id,
            user_id=user_id
        )

        # 使用锁保护共享状态
        async with self._lock:
            self.sessions[session_id] = session

            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = set()
            self.user_sessions[user_id].add(session_id)

        return session

    async def get_session(self, session_id: str) -> Optional[GatewaySession]:
        """
        获取会话（线程安全）

        Args:
            session_id: 会话ID

        Returns:
            会话对象或None
        """
        async with self._lock:
            return self.sessions.get(session_id)

    async def get_user_sessions(self, user_id: str) -> list[GatewaySession]:
        """
        获取用户的所有会话（线程安全）

        Args:
            user_id: 用户ID

        Returns:
            会话列表
        """
        async with self._lock:
            session_ids = self.user_sessions.get(user_id, set())
            return [
                self.sessions[sid]
                for sid in session_ids
                if sid in self.sessions
            ]

    async def close_session(self, session_id: str) -> bool:
        """
        关闭会话（线程安全）

        Args:
            session_id: 会话ID

        Returns:
            是否成功关闭
        """
        async with self._lock:
            session = self.sessions.get(session_id)
            if not session:
                return False

            session.disconnect()

            # 从用户会话列表中移除
            if session.user_id in self.user_sessions:
                self.user_sessions[session.user_id].discard(session_id)

            # 删除会话
            del self.sessions[session_id]
            return True

    async def get_active_count(self) -> int:
        """获取活跃会话数（线程安全）"""
        async with self._lock:
            return len(self.sessions)

    async def get_user_count(self) -> int:
        """获取活跃用户数（线程安全）"""
        async with self._lock:
            return len(self.user_sessions)

    # 同步版本用于非异步上下文（如健康检查）
    def get_active_count_sync(self) -> int:
        """获取活跃会话数（同步版本）"""
        return len(self.sessions)

    def get_user_count_sync(self) -> int:
        """获取活跃用户数（同步版本）"""
        return len(self.user_sessions)
