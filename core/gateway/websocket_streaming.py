#!/usr/bin/env python3
"""
WebSocket 流式事件转发

将 Agent Loop 的流式事件转发到 WebSocket 客户端。

作者: Athena平台团队
创建时间: 2026-04-20
"""
from __future__ import annotations

import logging
import json
from typing import Any

from core.agents.streaming_handler import StreamingHandler
from core.agents.stream_events import StreamEvent, stream_event_to_json
from core.gateway.websocket_handler import get_global_connection_manager

logger = logging.getLogger(__name__)


class WebSocketStreamingHandler(StreamingHandler):
    """WebSocket 流式处理器

    将流式事件转发到 WebSocket 客户端。
    """

    def __init__(
        self,
        connection_id: str | None = None,
        session_id: str | None = None,
    ):
        """初始化 WebSocket 流式处理器

        Args:
            connection_id: 连接 ID（None = 发送到会话所有连接）
            session_id: 会话 ID
        """
        super().__init__()
        self.connection_id = connection_id
        self.session_id = session_id
        self.connection_manager = get_global_connection_manager()

        logger.info(
            f"📡 WebSocket 流式处理器已创建 "
            f"(connection: {connection_id}, session: {session_id})"
        )

    async def start(self) -> None:
        """启动 WebSocket 流式处理器"""
        # 注册 SSE 输出处理器
        self.on_event(self._websocket_output_handler)
        await super().start()
        logger.info("🚀 WebSocket 流式处理器已启动")

    async def _websocket_output_handler(self, event: StreamEvent) -> None:
        """WebSocket 输出处理器

        Args:
            event: 流式事件
        """
        # 转换为 SSE 格式
        event_json = stream_event_to_json(event)
        sse_message = f"data: {event_json}\n\n"

        # 发送到 WebSocket
        if self.connection_id:
            # 发送到指定连接
            await self.connection_manager.send_to_connection(
                self.connection_id,
                sse_message,
            )
        elif self.session_id:
            # 发送到会话所有连接
            await self.connection_manager.send_to_session(
                self.session_id,
                sse_message,
            )
        else:
            logger.warning("⚠️ 未指定 connection_id 或 session_id，无法发送事件")


class AgentWebSocketStreamer:
    """代理 WebSocket 流式转发器

    管理 Agent Loop 与 WebSocket 的流式事件转发。
    """

    def __init__(self):
        """初始化流式转发器"""
        self.connection_manager = get_global_connection_manager()
        self._active_streamers: dict[str, WebSocketStreamingHandler] = {}

        logger.info("🔄 代理 WebSocket 流式转发器已初始化")

    async def create_streamer(
        self,
        connection_id: str,
        session_id: str | None = None,
    ) -> WebSocketStreamingHandler:
        """创建流式处理器

        Args:
            connection_id: 连接 ID
            session_id: 会话 ID

        Returns:
            WebSocketStreamingHandler: 流式处理器
        """
        streamer = WebSocketStreamingHandler(
            connection_id=connection_id,
            session_id=session_id,
        )

        await streamer.start()
        self._active_streamers[connection_id] = streamer

        logger.info(f"✅ 流式处理器已创建: {connection_id}")
        return streamer

    async def remove_streamer(self, connection_id: str) -> None:
        """移除流式处理器

        Args:
            connection_id: 连接 ID
        """
        if connection_id in self._active_streamers:
            streamer = self._active_streamers[connection_id]
            await streamer.stop()
            del self._active_streamers[connection_id]

            logger.info(f"🗑️ 流式处理器已移除: {connection_id}")

    def get_streamer(self, connection_id: str) -> WebSocketStreamingHandler | None:
        """获取流式处理器

        Args:
            connection_id: 连接 ID

        Returns:
            WebSocketStreamingHandler | None: 流式处理器
        """
        return self._active_streamers.get(connection_id)

    async def stream_agent_loop(
        self,
        connection_id: str,
        agent_loop: Any,  # EnhancedAgentLoop
        user_message: str,
        session_id: str | None = None,
    ) -> None:
        """流式执行 Agent Loop 并转发到 WebSocket

        Args:
            connection_id: 连接 ID
            agent_loop: Agent Loop 实例
            user_message: 用户消息
            session_id: 会话 ID
        """
        # 创建流式处理器
        streamer = await self.create_streamer(connection_id, session_id)

        try:
            # 流式执行
            async for event in agent_loop.run_stream(user_message):
                # 发送到 WebSocket
                await streamer.emit(event)

        finally:
            # 清理流式处理器
            await self.remove_streamer(connection_id)

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息

        Returns:
            dict: 统计信息
        """
        return {
            "active_streamers": len(self._active_streamers),
            "connection_ids": list(self._active_streamers.keys()),
        }


# 全局流式转发器单例
_global_streamer: AgentWebSocketStreamer | None = None


def get_global_streamer() -> AgentWebSocketStreamer:
    """获取全局流式转发器

    Returns:
        AgentWebSocketStreamer: 全局流式转发器
    """
    global _global_streamer
    if _global_streamer is None:
        _global_streamer = AgentWebSocketStreamer()
    return _global_streamer


__all__ = [
    "WebSocketStreamingHandler",
    "AgentWebSocketStreamer",
    "get_global_streamer",
]
