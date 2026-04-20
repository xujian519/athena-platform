#!/usr/bin/env python3
"""
WebSocket 端点实现

提供 Gateway 的 WebSocket 服务端点。

作者: Athena平台团队
创建时间: 2026-04-20
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from .websocket_handler import get_global_connection_manager

logger = logging.getLogger(__name__)


class WebSocketEndpoint:
    """WebSocket 端点

    处理 WebSocket 连接和消息路由。
    """

    def __init__(self, path: str = "/ws"):
        """初始化 WebSocket 端点

        Args:
            path: WebSocket 路径
        """
        self.path = path
        self.connection_manager = get_global_connection_manager()

        logger.info(f"🌐 WebSocket 端点已初始化: {path}")

    async def handle_connection(
        self,
        websocket: Any,
        session_id: str | None = None,
        user_id: str | None = None,
    ) -> None:
        """处理 WebSocket 连接

        Args:
            websocket: WebSocket 对象
            session_id: 会话 ID
            user_id: 用户 ID
        """
        connection = None

        try:
            # 接受连接
            connection = await self.connection_manager.connect(
                websocket=websocket,
                session_id=session_id,
                user_id=user_id,
            )

            logger.info(f"🔗 WebSocket 连接已建立: {connection.connection_id}")

            # 消息处理循环
            async for message in self._receive_messages(websocket):
                await self._handle_message(connection, message)

        except Exception as e:
            logger.error(f"❌ WebSocket 连接错误: {e}")

        finally:
            # 清理连接
            if connection:
                await self.connection_manager.disconnect(connection.connection_id)

    async def _receive_messages(self, websocket: Any):
        """接收消息

        Args:
            websocket: WebSocket 对象

        Yields:
            str: 接收到的消息
        """
        try:
            async for message in websocket:
                yield message
        except Exception as e:
            logger.error(f"❌ 接收消息错误: {e}")
            raise

    async def _handle_message(
        self,
        connection: Any,
        message: str,
    ) -> None:
        """处理接收到的消息

        Args:
            connection: 连接对象
            message: 消息内容
        """
        try:
            # 解析 JSON
            import json

            data = json.loads(message)

            # 获取消息类型
            msg_type = data.get("type", "unknown")

            logger.debug(f"📨 收到消息: {msg_type} from {connection.connection_id}")

            # 路由消息
            if msg_type == "ping":
                await self._handle_ping(connection, data)
            elif msg_type == "agent_request":
                await self._handle_agent_request(connection, data)
            elif msg_type == "subscribe":
                await self._handle_subscribe(connection, data)
            elif msg_type == "unsubscribe":
                await self._handle_unsubscribe(connection, data)
            else:
                await connection.send({
                    "type": "error",
                    "message": f"未知消息类型: {msg_type}",
                })

        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON 解析错误: {e}")
            await connection.send({
                "type": "error",
                "message": "无效的 JSON 格式",
            })
        except Exception as e:
            logger.error(f"❌ 处理消息错误: {e}")
            await connection.send({
                "type": "error",
                "message": f"处理消息时发生错误: {str(e)}",
            })

    async def _handle_ping(self, connection: Any, data: dict) -> None:
        """处理 ping 消息

        Args:
            connection: 连接对象
            data: 消息数据
        """
        await connection.send({
            "type": "pong",
            "timestamp": data.get("timestamp"),
        })

    async def _handle_agent_request(self, connection: Any, data: dict) -> None:
        """处理代理请求

        Args:
            connection: 连接对象
            data: 消息数据
        """
        # 这个方法将在后续集成 Agent Loop
        await connection.send({
            "type": "agent_response",
            "request_id": data.get("request_id"),
            "status": "pending",
            "message": "代理请求已接收，正在处理...",
        })

    async def _handle_subscribe(self, connection: Any, data: dict) -> None:
        """处理订阅请求

        Args:
            connection: 连接对象
            data: 消息数据
        """
        # 订阅事件类型
        event_types = data.get("event_types", [])

        await connection.send({
            "type": "subscribed",
            "event_types": event_types,
            "message": f"已订阅 {len(event_types)} 个事件类型",
        })

    async def _handle_unsubscribe(self, connection: Any, data: dict) -> None:
        """处理取消订阅请求

        Args:
            connection: 连接对象
            data: 消息数据
        """
        # 取消订阅事件类型
        event_types = data.get("event_types", [])

        await connection.send({
            "type": "unsubscribed",
            "event_types": event_types,
            "message": f"已取消订阅 {len(event_types)} 个事件类型",
        })


# ========================================
# FastAPI/Starlette 集成
# ========================================

try:
    from fastapi import WebSocket, WebSocketDisconnect

    class FastAPIWebSocketEndpoint:
        """FastAPI WebSocket 端点"""

        def __init__(self):
            """初始化 FastAPI WebSocket 端点"""
            self.endpoint = WebSocketEndpoint()
            self.connection_manager = get_global_connection_manager()

        async def websocket_endpoint(
            self,
            websocket: WebSocket,
            session_id: str | None = None,
            user_id: str | None = None,
        ):
            """FastAPI WebSocket 端点

            Args:
                websocket: WebSocket 对象
                session_id: 会话 ID（从查询参数获取）
                user_id: 用户 ID（从查询参数获取）
            """
            await websocket.accept()

            # 使用 aiohttpWebSocket 包装器
            class WebSocketWrapper:
                def __init__(self, ws: WebSocket):
                    self._ws = ws

                async def send(self, message: str):
                    await self._ws.send_text(message)

                async def close(self, code: int = 1000, reason: str = ""):
                    await self._ws.close(code=code, reason=reason)

                def __aiter__(self):
                    return self

                async def __anext__(self):
                    try:
                        return await self._ws.receive_text()
                    except:
                        raise StopAsyncIteration

            wrapper = WebSocketWrapper(websocket)

            # 处理连接
            await self.endpoint.handle_connection(
                websocket=wrapper,
                session_id=session_id,
                user_id=user_id,
            )

    FASTAPI_AVAILABLE = True

except ImportError:
    FASTAPI_AVAILABLE = False
    logger.warning("⚠️ FastAPI 未安装，FastAPI WebSocket 端点不可用")


# ========================================
# aiohttp 集成
# ========================================

try:
    from aiohttp import web

    class AioHTTPWebSocketEndpoint:
        """aiohttp WebSocket 端点"""

        def __init__(self):
            """初始化 aiohttp WebSocket 端点"""
            self.endpoint = WebSocketEndpoint()
            self.connection_manager = get_global_connection_manager()

        async def websocket_handler(self, request: web.Request) -> web.WebSocketResponse:
            """aiohttp WebSocket 处理器

            Args:
                request: HTTP 请求

            Returns:
                web.WebSocketResponse: WebSocket 响应
            """
            ws = web.WebSocketResponse()
            await ws.prepare(request)

            # 获取会话和用户 ID
            session_id = request.query.get("session_id")
            user_id = request.query.get("user_id")

            # 处理连接
            await self.endpoint.handle_connection(
                websocket=ws,
                session_id=session_id,
                user_id=user_id,
            )

            return ws

    AIOHTTP_AVAILABLE = True

except ImportError:
    AIOHTTP_AVAILABLE = False
    logger.warning("⚠️ aiohttp 未安装，aiohttp WebSocket 端点不可用")


__all__ = [
    "WebSocketEndpoint",
    "FASTAPI_AVAILABLE",
    "AIOHTTP_AVAILABLE",
]

if FASTAPI_AVAILABLE:
    __all__.append("FastAPIWebSocketEndpoint")

if AIOHTTP_AVAILABLE:
    __all__.append("AioHTTPWebSocketEndpoint")
