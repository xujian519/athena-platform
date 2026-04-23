#!/usr/bin/env python3
"""
Gateway WebSocket客户端
Gateway WebSocket Client for Python Agents

提供Python Agent与Gateway WebSocket通信的客户端功能:
1. WebSocket连接管理 - 自动连接、断线重连
2. 消息编解码 - 兼容Go协议格式
3. 异步消息处理 - 异步收发消息
4. 心跳机制 - 保持连接活跃
5. 错误处理 - 完善的异常处理

作者: Athena平台团队
创建时间: 2026-04-20
版本: v1.0.0
"""

import asyncio
import json
import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import websockets.client as ws_client
from websockets.exceptions import ConnectionClosed

logger = logging.getLogger(__name__)


# ==================== 消息类型定义（兼容Go协议） ====================

class MessageType(str, Enum):
    """消息类型（与Go protocol/message.go保持一致）"""
    # 客户端请求类型
    HANDSHAKE = "handshake"
    TASK = "task"
    QUERY = "query"
    CANCEL = "cancel"

    # 服务器响应类型
    RESPONSE = "response"
    PROGRESS = "progress"
    ERROR = "error"
    NOTIFY = "notify"

    # 系统消息类型
    PING = "ping"
    PONG = "pong"
    CLOSE = "close"


class AgentType(str, Enum):
    """Agent类型（与Go protocol/message.go保持一致）"""
    XIAONA = "xiaona"   # 法律专家
    XIAONUO = "xiaonuo" # 调度官
    YUNXI = "yunxi"     # IP管理
    UNKNOWN = "unknown" # 未知


# ==================== 消息数据结构 ====================

@dataclass
class Message:
    """WebSocket消息基础结构（兼容Go protocol）"""
    id: str = field(default_factory=lambda: f"msg_{datetime.now().timestamp()}_{uuid.uuid4().hex[:8]}")
    type: MessageType = MessageType.TASK
    timestamp: int = field(default_factory=lambda: int(datetime.now().timestamp() * 1e9))
    session_id: str = ""
    data: Optional[[dict[str, Any]]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典（用于JSON序列化）"""
        return {
            "id": self.id,
            "type": self.type.value,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "data": self.data
        }

    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Optional[[dict[str, Any]]]) -> "Message":
        """从字典创建"""
        return cls(
            id=data.get("id", ""),
            type=MessageType(data.get("type", MessageType.TASK)),
            timestamp=data.get("timestamp", 0),
            session_id=data.get("session_id", ""),
            data=data.get("data", {})
        )

    @classmethod
    def from_json(cls, json_str: str) -> str:
        """从JSON字符串创建"""
        data = json.loads(json_str)
        return cls.from_dict(data)


@dataclass
class TaskRequest:
    """任务请求"""
    message: Message
    task_type: str
    target_agent: AgentType
    priority: int = 5
    parameters: Optional[[dict[str, Any]]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        result = self.message.to_dict()
        result.update({
            "task_type": self.task_type,
            "target_agent": self.target_agent.value,
            "priority": self.priority,
            "parameters": self.parameters
        })
        return result

    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def create(
        cls,
        session_id: str,
        task_type: str,
        target_agent: AgentType,
        parameters: Optional[[dict[str, Any]]],
        priority: int = 5
    ) -> str:
        """创建任务请求"""
        return cls(
            message=Message(type=MessageType.TASK, session_id=session_id),
            task_type=task_type,
            target_agent=target_agent,
            priority=priority,
            parameters=parameters or {}
        )


@dataclass
class Response:
    """响应消息"""
    message: Message
    success: bool
    result: Optional[[dict[str, Any]]] = field(default_factory=dict)
    metadata: Optional[[dict[str, Any]]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        result = self.message.to_dict()
        result.update({
            "success": self.success,
            "result": self.result,
            "metadata": self.metadata
        })
        return result

    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)


# ==================== Gateway客户端 ====================

class GatewayClientConfig:
    """Gateway客户端配置"""
    def __init__(
        self,
        gateway_url: str = "ws://localhost:8005/ws",
        agent_type: AgentType = AgentType.UNKNOWN,
        agent_id: str = "",
        heartbeat_interval: int = 30,
        reconnect_interval: int = 5,
        max_reconnect_attempts: int = 10,
        message_timeout: int = 30
    ):
        self.gateway_url = gateway_url
        self.agent_type = agent_type
        self.agent_id = agent_id or f"agent_{agent_type.value}_{uuid.uuid4().hex[:8]}"
        self.heartbeat_interval = heartbeat_interval
        self.reconnect_interval = reconnect_interval
        self.max_reconnect_attempts = max_reconnect_attempts
        self.message_timeout = message_timeout


class GatewayClient:
    """
    Gateway WebSocket客户端

    功能:
    1. 自动连接和重连
    2. 异步消息收发
    3. 心跳保持
    4. 消息处理器注册
    5. 请求-响应匹配
    """

    def __init__(self, config: GatewayClientConfig):
        self.config = config
        self._websocket: Optional[ws_client.WebSocketClientProtocol ] = None
        self._connected = False
        self._session_id = ""
        self._message_handlers: Optional[[dict[MessageType, list[Callable]]]] = {}
        self._pending_requests: Optional[[dict[str, asyncio.Future]]] = {}
        self._receive_task: Optional[asyncio.Task ] = None
        self._heartbeat_task: Optional[asyncio.Task ] = None
        self._reconnect_task: Optional[asyncio.Task ] = None
        self._shutdown = False

        logger.info(f"🔌 Gateway客户端初始化: {config.agent_id} @ {config.gateway_url}")

    async def connect(self) -> str:
        """
        连接到Gateway

        Returns:
            bool: 连接是否成功
        """
        try:
            logger.info(f"🔗 连接到Gateway: {self.config.gateway_url}")

            # 建立WebSocket连接
            self._websocket = await ws_client.connect(
                self.config.gateway_url,
                close_timeout=1
            )
            self._connected = True

            # 发送握手消息
            await self._handshake()

            # 启动接收任务
            self._receive_task = asyncio.create_task(self._receive_loop())

            # 启动心跳任务
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

            logger.info(f"✅ Gateway连接成功: {self._session_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Gateway连接失败: {e}")
            self._connected = False
            return False

    async def _handshake(self) -> str:
        """发送握手消息"""
        handshake_msg = Message(
            type=MessageType.HANDSHAKE,
            data={
                "client_id": self.config.agent_id,
                "agent_type": self.config.agent_type.value,
                "capabilities": ["task", "query", "broadcast"]
            }
        )

        await self._send_message(handshake_msg)

        # 等待握手响应
        response = await self._wait_for_response(handshake_msg.id, timeout=5)
        if response and response.data.get("session_id"):
            self._session_id = response.data["session_id"]
            logger.info(f"🤝 握手成功: session={self._session_id}")
        else:
            logger.warning("⚠️ 握手响应无效，继续使用临时会话")
            self._session_id = f"session_{uuid.uuid4().hex}"

    async def disconnect(self) -> str:
        """断开连接"""
        logger.info("🔌 断开Gateway连接")

        self._shutdown = True

        # 取消所有任务
        if self._receive_task:
            self._receive_task.cancel()
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._reconnect_task:
            self._reconnect_task.cancel()

        # 关闭WebSocket
        if self._websocket:
            await self._websocket.close()

        self._connected = False
        logger.info("✅ Gateway连接已关闭")

    async def send_task(
        self,
        task_type: str,
        target_agent: AgentType,
        parameters: Optional[[dict[str, Any]]],
        priority: int = 5
    ) -> Response:
        """
        发送任务请求

        Args:
            task_type: 任务类型
            target_agent: 目标Agent
            parameters: 任务参数
            priority: 优先级（0-10）

        Returns:
            Response: 响应消息
        """
        if not self._connected:
            logger.error("❌ 未连接到Gateway")
            return None

        task = TaskRequest.create(
            session_id=self._session_id,
            task_type=task_type,
            target_agent=target_agent,
            parameters=parameters,
            priority=priority
        )

        await self._send_message_raw(task.to_json())
        logger.debug(f"📤 任务已发送: {task_type} -> {target_agent.value}")

        # 等待响应
        response = await self._wait_for_response(task.message.id, timeout=self.config.message_timeout)
        return response

    async def broadcast(self, data: Optional[[dict[str, Any]]]) -> bool:
        """
        广播消息

        Args:
            data: 广播数据

        Returns:
            bool: 是否成功
        """
        if not self._connected:
            logger.error("❌ 未连接到Gateway")
            return False

        message = Message(
            type=MessageType.NOTIFY,
            session_id=self._session_id,
            data=data
        )

        await self._send_message(message)
        logger.debug(f"📢 广播消息: {data}")
        return True

    def register_handler(self, message_type: MessageType, handler: Callable) -> str:
        """
        注册消息处理器

        Args:
            message_type: 消息类型
            handler: 处理器函数
        """
        if message_type not in self._message_handlers:
            self._message_handlers[message_type] = []
        self._message_handlers[message_type].append(handler)
        logger.debug(f"📝 消息处理器已注册: {message_type.value}")

    async def _send_message(self, message: Message) -> str:
        """发送消息"""
        await self._send_message_raw(message.to_json())

    async def _send_message_raw(self, data: str) -> str:
        """发送原始消息"""
        if self._websocket:
            await self._websocket.send(data)

    async def _wait_for_response(
        self,
        request_id: str,
        timeout: int = 30
    ) -> Response:
        """
        等待响应

        Args:
            request_id: 请求ID
            timeout: 超时时间（秒）

        Returns:
            Response: 响应消息
        """
        future: Optional[asyncio.Future[Response]] = asyncio.Future()
        self._pending_requests[request_id] = future

        try:
            response = await asyncio.wait_for(future, timeout=timeout)
            return response
        except TimeoutError:
            logger.warning(f"⏰ 响应超时: {request_id}")
            return None
        finally:
            self._pending_requests.pop(request_id, None)

    async def _receive_loop(self) -> str:
        """接收消息循环"""
        logger.debug("📥 接收循环已启动")

        while not self._shutdown and self._connected:
            try:
                if not self._websocket:
                    await asyncio.sleep(0.1)
                    continue

                # 接收消息
                raw_message = await asyncio.wait_for(
                    self._websocket.recv(),
                    timeout=1.0
                )

                # 解析消息
                message = Message.from_json(raw_message)
                await self._handle_message(message)

            except TimeoutError:
                continue
            except ConnectionClosed:
                logger.warning("⚠️ WebSocket连接已关闭")
                break
            except Exception as e:
                logger.error(f"❌ 接收消息失败: {e}")
                break

        # 触发重连
        if not self._shutdown:
            asyncio.create_task(self._reconnect())

    async def _handle_message(self, message: Message) -> str:
        """
        处理接收到的消息

        Args:
            message: 消息对象
        """
        logger.debug(f"📨 收到消息: {message.type.value} ({message.id})")

        # 检查是否是响应消息
        if message.type == MessageType.RESPONSE:
            # 查找对应的请求
            correlation_id = message.data.get("correlation_id") or message.data.get("request_id")
            if correlation_id and correlation_id in self._pending_requests:
                future = self._pending_requests[correlation_id]
                if not future.done():
                    response = Response(
                        message=message,
                        success=message.data.get("success", False),
                        result=message.data.get("result", {}),
                        metadata=message.data.get("metadata", {})
                    )
                    future.set_result(response)
                return

        # 调用注册的处理器
        handlers = self._message_handlers.get(message.type, [])
        for handler in handlers:
            try:
                result = handler(message)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"❌ 消息处理器失败: {e}")

    async def _heartbeat_loop(self) -> str:
        """心跳循环"""
        logger.debug("💓 心跳循环已启动")

        while not self._shutdown and self._connected:
            try:
                await asyncio.sleep(self.config.heartbeat_interval)

                ping_message = Message(
                    type=MessageType.PING,
                    session_id=self._session_id,
                    data={"timestamp": int(datetime.now().timestamp() * 1e9)}
                )

                await self._send_message(ping_message)
                logger.debug("💓 心跳已发送")

            except Exception as e:
                logger.error(f"❌ 心跳失败: {e}")
                break

    async def _reconnect(self) -> str:
        """重连"""
        if self._reconnect_task and not self._reconnect_task.done():
            return

        self._reconnect_task = asyncio.create_task(self._reconnect_loop())

    async def _reconnect_loop(self) -> str:
        """重连循环"""
        logger.info("🔄 开始重连...")

        for attempt in range(self.config.max_reconnect_attempts):
            if self._shutdown:
                break

            await asyncio.sleep(self.config.reconnect_interval)

            logger.info(f"🔄 重连尝试 {attempt + 1}/{self.config.max_reconnect_attempts}")

            if await self.connect():
                logger.info("✅ 重连成功")
                return

        logger.error("❌ 重连失败，已达最大尝试次数")

    @property
    def is_connected(self) -> str:
        """是否已连接"""
        return self._connected

    @property
    def session_id(self) -> str:
        """会话ID"""
        return self._session_id


# ==================== 便捷函数 ====================

_client: Optional[GatewayClient] = None


async def get_gateway_client(config: Optional[GatewayClientConfig] = None) -> GatewayClient:
    """
    获取Gateway客户端单例

    Args:
        config: 客户端配置

    Returns:
        GatewayClient: 客户端实例
    """
    global _client

    if _client is None:
        if config is None:
            config = GatewayClientConfig()
        _client = GatewayClient(config)

    if not _client.is_connected:
        await _client.connect()

    return _client


def set_gateway_client(client: GatewayClient) -> None:
    """设置Gateway客户端"""
    global _client
    _client = client

