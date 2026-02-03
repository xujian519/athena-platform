#!/usr/bin/env python3
"""
WebSocket服务器实现
WebSocket Server Implementation

完整的WebSocket服务器，支持：
- 异步连接处理
- 消息广播和点对点发送
- 心跳检测
- 自动重连
- 认证集成

作者: Athena平台团队
版本: 1.0.0
创建时间: 2026-01-28
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Callable, Dict, Set

from websockets.server import WebSocketServerProtocol, serve

from core.communication.websocket.connection_manager import ConnectionManager
from core.communication.websocket.message_protocol import (
    MessageProtocol,
    WebSocketMessageType,
    WebSocketMessage,
)
from core.communication.websocket_auth import (
    WebSocketAuthConfig,
    WebSocketAuthenticator,
    WebSocketAuthResult,
)

logger = logging.getLogger(__name__)


class WebSocketServer:
    """
    WebSocket服务器

    提供完整的WebSocket服务器功能。
    """

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8765,
        auth_config: WebSocketAuthConfig | None = None,
        ping_interval: float = 20.0,
        ping_timeout: float = 20.0,
        max_connections: int = 1000,
    ):
        """
        初始化WebSocket服务器

        Args:
            host: 监听地址
            port: 监听端口
            auth_config: 认证配置
            ping_interval: 心跳间隔（秒）
            ping_timeout: 心跳超时（秒）
            max_connections: 最大连接数
        """
        self.host = host
        self.port = port
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        self.max_connections = max_connections

        # 组件
        self.connection_manager = ConnectionManager(max_connections)
        self.authenticator = WebSocketAuthenticator(auth_config)
        self.protocol = MessageProtocol()

        # 事件处理器
        self._message_handlers: Dict[WebSocketMessageType, list[Callable]] = {}
        self._connection_handlers: list[Callable] = []
        self._disconnection_handlers: list[Callable] = []

        # 状态
        self._server = None
        self._running = False
        self._shutdown_event = asyncio.Event()

        logger.info(f"WebSocket服务器配置: {host}:{port}")

    async def start(self) -> None:
        """启动WebSocket服务器"""
        if self._running:
            logger.warning("WebSocket服务器已在运行")
            return

        logger.info(f"🚀 启动WebSocket服务器: {self.host}:{self.port}")

        self._server = await serve(
            self._handle_connection,
            self.host,
            self.port,
            ping_interval=self.ping_interval,
            ping_timeout=self.ping_timeout,
            max_size=2**20,  # 1MB max message size
            compression=None,  # 禁用压缩以提高性能
        )

        self._running = True
        self._shutdown_event.clear()

        logger.info(f"✅ WebSocket服务器已启动: ws://{self.host}:{self.port}")

    async def stop(self) -> None:
        """停止WebSocket服务器"""
        if not self._running:
            return

        logger.info("🛑 停止WebSocket服务器...")

        self._running = False
        self._shutdown_event.set()

        # 关闭所有连接
        await self.connection_manager.disconnect_all()

        # 关闭服务器
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

        logger.info("✅ WebSocket服务器已停止")

    async def _handle_connection(
        self, websocket: WebSocketServerProtocol, path: str
    ) -> None:
        """
        处理新连接

        Args:
            websocket: WebSocket连接
            path: 请求路径
        """
        connection_id = self._generate_connection_id()

        logger.info(f"📥 新连接请求: {connection_id} from {path}")

        try:
            # 1. 认证
            auth_result = await self._authenticate_connection(websocket, connection_id)
            if not auth_result.success:
                await websocket.close(4003, auth_result.error or "认证失败")
                logger.warning(f"❌ 连接认证失败: {connection_id}")
                return

            # 2. 注册连接
            await self.connection_manager.add_connection(
                connection_id, websocket, auth_result
            )

            logger.info(
                f"✅ 连接已建立: {connection_id} "
                f"(用户: {auth_result.username}, 角色: {auth_result.role})"
            )

            # 3. 触发连接事件
            await self._trigger_connection_handlers(connection_id, auth_result)

            # 4. 发送欢迎消息
            logger.info(f"发送欢迎消息: {connection_id}")
            try:
                await self._send_welcome_message(websocket, connection_id)
                logger.info(f"欢迎消息已发送: {connection_id}")
            except Exception as e:
                logger.error(f"欢迎消息发送失败: {connection_id}, 错误: {e}")

            # 5. 处理消息循环
            logger.info(f"进入消息循环: {connection_id}")
            await self._message_loop(websocket, connection_id)

        except Exception as e:
            logger.error(f"❌ 连接处理错误: {connection_id}, 错误: {e}")

        finally:
            # 清理连接
            await self._cleanup_connection(connection_id)

    async def _authenticate_connection(
        self, websocket: WebSocketServerProtocol, connection_id: str
    ) -> WebSocketAuthResult:
        """
        认证WebSocket连接

        Args:
            websocket: WebSocket连接
            connection_id: 连接ID

        Returns:
            认证结果
        """
        # 获取路径和查询参数
        try:
            path = websocket.request.path if hasattr(websocket, 'request') else '/'
        except AttributeError:
            path = '/'

        query_params = self._parse_query_params(path)
        token = query_params.get("token", [None])[0]

        # 构建认证消息JSON (authenticate_message 期望JSON格式的认证消息)
        auth_message_json = json.dumps({
            "type": "auth",
            "token": token or "",
            "client_type": "websocket",
            "ai_name": None
        })

        # 验证令牌
        return self.authenticator.authenticate_message(
            auth_message_json, connection_id
        )

    async def _message_loop(
        self, websocket: WebSocketServerProtocol, connection_id: str
    ) -> None:
        """
        消息处理循环

        Args:
            websocket: WebSocket连接
            connection_id: 连接ID
        """
        try:
            async for raw_message in websocket:
                try:
                    # 解析消息
                    message = await self.protocol.parse_message(raw_message)

                    # 处理消息
                    await self._handle_message(connection_id, message)

                except json.JSONDecodeError:
                    logger.warning(f"⚠️ 无效的JSON消息: {connection_id}")
                    await self._send_error(
                        websocket, "invalid_format", "消息格式错误"
                    )

                except Exception as e:
                    logger.error(f"❌ 消息处理错误: {connection_id}, 错误: {e}")
                    await self._send_error(websocket, "processing_error", str(e))

        except Exception as e:
            logger.error(f"❌ 消息循环错误: {connection_id}, 错误: {e}")

    async def _handle_message(
        self, connection_id: str, message: WebSocketMessage
    ) -> None:
        """
        处理收到的消息

        Args:
            connection_id: 连接ID
            message: WebSocket消息
        """
        # 更新最后活跃时间
        await self.connection_manager.update_last_activity(connection_id)

        # 特殊消息类型处理
        if message.type == WebSocketMessageType.PING:
            await self._handle_ping(connection_id)
            return

        if message.type == WebSocketMessageType.PONG:
            # Pong消息由websockets库自动处理
            return

        if message.type == WebSocketMessageType.SUBSCRIBE:
            await self._handle_subscribe(connection_id, message)
            return

        if message.type == WebSocketMessageType.UNSUBSCRIBE:
            await self._handle_unsubscribe(connection_id, message)
            return

        # 触发消息处理器
        handlers = self._message_handlers.get(message.type, [])
        for handler in handlers:
            try:
                await handler(connection_id, message)
            except Exception as e:
                logger.error(
                    f"❌ 消息处理器错误: {connection_id}, "
                    f"类型: {message.type}, 错误: {e}"
                )

    async def _handle_ping(self, connection_id: str) -> None:
        """处理PING消息"""
        websocket = await self.connection_manager.get_connection(connection_id)
        if websocket:
            pong_message = self.protocol.create_pong_message()
            await websocket.send(pong_message)

    async def _handle_subscribe(
        self, connection_id: str, message: WebSocketMessage
    ) -> None:
        """处理订阅消息"""
        channel = message.data.get("channel")
        if channel:
            await self.connection_manager.subscribe(connection_id, channel)
            logger.debug(f"🔔 订阅频道: {connection_id} -> {channel}")

    async def _handle_unsubscribe(
        self, connection_id: str, message: WebSocketMessage
    ) -> None:
        """处理取消订阅消息"""
        channel = message.data.get("channel")
        if channel:
            await self.connection_manager.unsubscribe(connection_id, channel)
            logger.debug(f"🔕 取消订阅: {connection_id} -> {channel}")

    async def _cleanup_connection(self, connection_id: str) -> None:
        """
        清理断开的连接

        Args:
            connection_id: 连接ID
        """
        # 从管理器移除
        await self.connection_manager.remove_connection(connection_id)

        # 触发断开事件
        await self._trigger_disconnection_handlers(connection_id)

        logger.info(f"📤 连接已清理: {connection_id}")

    async def _send_welcome_message(
        self, websocket: WebSocketServerProtocol, connection_id: str
    ) -> None:
        """发送欢迎消息"""
        welcome_msg = self.protocol.create_message(
            WebSocketMessageType.SYSTEM,
            {
                "type": "welcome",
                "connection_id": connection_id,
                "server_time": datetime.now().isoformat(),
                "features": [
                    "broadcast",
                    "direct_message",
                    "subscribe",
                    "heartbeat",
                ],
            },
        )
        await websocket.send(welcome_msg)

    async def _send_error(
        self, websocket: WebSocketServerProtocol, code: str, message: str
    ) -> None:
        """发送错误消息"""
        error_msg = self.protocol.create_message(
            WebSocketMessageType.ERROR,
            {"code": code, "message": message},
        )
        await websocket.send(error_msg)

    def _parse_query_params(self, path: str) -> Dict[str, list[str]]:
        """解析查询参数"""
        if "?" not in path:
            return {}

        query_string = path.split("?")[1]
        params = {}
        for pair in query_string.split("&"):
            if "=" in pair:
                key, value = pair.split("=", 1)
                params.setdefault(key, []).append(value)
        return params

    def _generate_connection_id(self) -> str:
        """生成连接ID"""
        import uuid

        return f"ws_{datetime.now().timestamp()}_{uuid.uuid4().hex[:8]}"

    # 事件处理

    def on_message(
        self, message_type: WebSocketMessageType
    ) -> Callable:
        """
        注册消息处理器装饰器

        Args:
            message_type: 消息类型

        Returns:
            装饰器函数
        """

        def decorator(handler: Callable) -> Callable:
            self._message_handlers.setdefault(message_type, []).append(handler)
            return handler

        return decorator

    def on_connection(self, handler: Callable) -> Callable:
        """
        注册连接处理器装饰器

        Args:
            handler: 处理器函数

        Returns:
            处理器函数
        """
        self._connection_handlers.append(handler)
        return handler

    def on_disconnection(self, handler: Callable) -> Callable:
        """
        注册断开连接处理器装饰器

        Args:
            handler: 处理器函数

        Returns:
            处理器函数
        """
        self._disconnection_handlers.append(handler)
        return handler

    async def _trigger_connection_handlers(
        self, connection_id: str, auth_result: WebSocketAuthResult
    ) -> None:
        """触发连接处理器"""
        for handler in self._connection_handlers:
            try:
                await handler(connection_id, auth_result)
            except Exception as e:
                logger.error(f"❌ 连接处理器错误: {e}")

    async def _trigger_disconnection_handlers(self, connection_id: str) -> None:
        """触发断开连接处理器"""
        for handler in self._disconnection_handlers:
            try:
                await handler(connection_id)
            except Exception as e:
                logger.error(f"❌ 断开连接处理器错误: {e}")

    # 公共API

    async def broadcast(
        self, message: WebSocketMessage, exclude: Set[str] | None = None
    ) -> int:
        """
        广播消息到所有连接

        Args:
            message: 要广播的消息
            exclude: 要排除的连接ID集合

        Returns:
            发送成功的连接数
        """
        message_data = self.protocol.serialize(message)
        return await self.connection_manager.broadcast(message_data, exclude)

    async def send_to(
        self, connection_id: str, message: WebSocketMessage
    ) -> bool:
        """
        发送消息到指定连接

        Args:
            connection_id: 目标连接ID
            message: 要发送的消息

        Returns:
            是否发送成功
        """
        message_data = self.protocol.serialize(message)
        websocket = await self.connection_manager.get_connection(connection_id)

        if websocket:
            try:
                await websocket.send(message_data)
                return True
            except Exception as e:
                logger.error(f"❌ 发送消息失败: {connection_id}, 错误: {e}")
                return False

        return False

    async def send_to_channel(
        self, channel: str, message: WebSocketMessage
    ) -> int:
        """
        发送消息到订阅频道的所有连接

        Args:
            channel: 频道名称
            message: 要发送的消息

        Returns:
            发送成功的连接数
        """
        subscribers = await self.connection_manager.get_channel_subscribers(channel)
        message_data = self.protocol.serialize(message)

        count = 0
        for connection_id in subscribers:
            if await self.send_to(connection_id, message):
                count += 1

        return count

    async def get_stats(self) -> Dict[str, Any]:
        """
        获取服务器统计信息

        Returns:
            统计信息字典
        """
        return {
            "running": self._running,
            "connections": await self.connection_manager.get_connection_count(),
            "max_connections": self.max_connections,
            "host": self.host,
            "port": self.port,
            "uptime": (
                datetime.now().isoformat()
                if self._running
                else None
            ),
        }


# =============================================================================
# === 便捷函数 ===
# =============================================================================

# 全局WebSocket服务器实例
_global_websocket_server: WebSocketServer | None = None


def get_websocket_server(
    host: str = "0.0.0.0",
    port: int = 8765,
    auth_config: WebSocketAuthConfig | None = None,
) -> WebSocketServer:
    """
    获取或创建WebSocket服务器实例

    Args:
        host: 监听地址
        port: 监听端口
        auth_config: 认证配置

    Returns:
        WebSocketServer实例
    """
    global _global_websocket_server

    if _global_websocket_server is None:
        _global_websocket_server = WebSocketServer(
            host=host,
            port=port,
            auth_config=auth_config,
        )

    return _global_websocket_server


async def start_websocket_server(
    host: str = "0.0.0.0",
    port: int = 8765,
    auth_config: WebSocketAuthConfig | None = None,
) -> WebSocketServer:
    """
    启动WebSocket服务器

    Args:
        host: 监听地址
        port: 监听端口
        auth_config: 认证配置

    Returns:
        WebSocketServer实例
    """
    server = get_websocket_server(host, port, auth_config)
    await server.start()
    return server


__all__ = ["WebSocketServer", "get_websocket_server", "start_websocket_server"]
