"""
Athena Gateway WebSocket客户端库

用于Python Agent与Gateway之间的WebSocket通信。
"""

import asyncio
import json
import logging
import time
from typing import Any, Callable, Dict, Optional, List
from dataclasses import dataclass, field
from enum import Enum

try:
    import websockets
    from websockets.exceptions import ConnectionClosed, ConnectionClosedError, ConnectionClosedOK
except ImportError:
    raise ImportError("请安装websockets库: pip install websockets")


# 配置日志
logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """消息类型"""
    HANDSHAKE = "handshake"
    TASK = "task"
    QUERY = "query"
    CANCEL = "cancel"
    RESPONSE = "response"
    PROGRESS = "progress"
    ERROR = "error"
    NOTIFY = "notify"
    PING = "ping"
    PONG = "pong"
    CLOSE = "close"


class AgentType(str, Enum):
    """Agent类型"""
    XIAONA = "xiaona"  # 法律专家
    XIAONUO = "xiaonuo"  # 调度官
    YUNXI = "yunxi"  # IP管理
    UNKNOWN = "unknown"


@dataclass
class Message:
    """WebSocket消息"""
    id: str
    type: MessageType
    timestamp: int
    session_id: Optional[str]
    data: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
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
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """从字典创建消息"""
        return cls(
            id=data["id"],
            type=MessageType(data["type"]),
            timestamp=data["timestamp"],
            session_id=data.get("session_id"),
            data=data.get("data", {})
        )


@dataclass
class TaskRequest(Message):
    """任务请求"""
    task_type: str = ""
    target_agent: AgentType = AgentType.UNKNOWN
    priority: int = 5
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base = super().to_dict()
        base["data"] = {
            "task_type": self.task_type,
            "target_agent": self.target_agent.value,
            "priority": self.priority,
            "parameters": self.parameters
        }
        return base


@dataclass
class ProgressUpdate(Message):
    """进度更新"""
    progress: int = 0
    status: str = ""
    current_step: str = ""
    total_steps: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base = super().to_dict()
        base["data"] = {
            "progress": self.progress,
            "status": self.status,
            "current_step": self.current_step,
            "total_steps": self.total_steps
        }
        return base


@dataclass
class ErrorResponse(Message):
    """错误响应"""
    error_code: str = ""
    error_msg: str = ""
    details: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base = super().to_dict()
        base["data"] = {
            "error_code": self.error_code,
            "error_msg": self.error_msg,
            "details": self.details
        }
        return base


class WebSocketClient:
    """
    Athena Gateway WebSocket客户端

    用于Python Agent与Gateway的WebSocket通信。
    """

    def __init__(
        self,
        gateway_url: str = "ws://localhost:8005/ws",
        client_id: Optional[str] = None,
        auth_token: str = "demo_token",
        auto_reconnect: bool = True,
        reconnect_interval: float = 3.0,
        ping_interval: float = 30.0,
        capabilities: Optional[List[str]] = None
    ):
        """
        初始化WebSocket客户端

        Args:
            gateway_url: Gateway WebSocket URL
            client_id: 客户端ID（可选，默认自动生成）
            auth_token: 认证Token
            auto_reconnect: 是否自动重连
            reconnect_interval: 重连间隔（秒）
            ping_interval: 心跳间隔（秒）
            capabilities: 客户端能力列表
        """
        self.gateway_url = gateway_url
        self.client_id = client_id or self._generate_client_id()
        self.auth_token = auth_token
        self.auto_reconnect = auto_reconnect
        self.reconnect_interval = reconnect_interval
        self.ping_interval = ping_interval
        self.capabilities = capabilities or ["task", "query", "progress"]

        # 连接状态
        self._websocket: Optional[websockets.WebSocketClientProtocol] = None
        self._connected = False
        self._session_id: Optional[str] = None
        self._message_handlers: Dict[MessageType, List[Callable]] = {}
        self._stop_event = asyncio.Event()

        # 消息ID计数器
        self._message_counter = 0

        logger.info(f"WebSocket客户端已初始化: {self.client_id}")

    def _generate_client_id(self) -> str:
        """生成客户端ID"""
        return f"client_{int(time.time() * 1000)}_{id(self)}"

    def _generate_message_id(self) -> str:
        """生成消息ID"""
        self._message_counter += 1
        return f"msg_{int(time.time() * 1000000000)}_{self._message_counter}"

    def _get_timestamp(self) -> int:
        """获取当前时间戳（纳秒）"""
        return int(time.time() * 1000000000)

    async def connect(self) -> bool:
        """
        连接到Gateway

        Returns:
            是否连接成功
        """
        try:
            # 构建WebSocket URL
            url = f"{self.gateway_url}?client_id={self.client_id}"
            logger.info(f"连接到Gateway: {url}")

            # 建立连接
            self._websocket = await websockets.connect(url)
            self._connected = True

            logger.info("WebSocket连接已建立")

            # 发送握手消息
            await self._handshake()

            # 启动消息接收循环
            asyncio.create_task(self._receive_loop())

            # 启动心跳循环
            asyncio.create_task(self._ping_loop())

            return True

        except Exception as e:
            logger.error(f"连接失败: {e}")
            return False

    async def _handshake(self) -> None:
        """发送握手消息"""
        handshake = Message(
            id=self._generate_message_id(),
            type=MessageType.HANDSHAKE,
            timestamp=self._get_timestamp(),
            session_id=None,
            data={
                "client_id": self.client_id,
                "auth_token": self.auth_token,
                "capabilities": self.capabilities,
                "user_agent": f"PythonWebSocketClient/1.0"
            }
        )

        await self._send_message(handshake)
        logger.info("握手消息已发送")

    async def _receive_loop(self) -> None:
        """消息接收循环"""
        try:
            async for message in self._websocket:
                try:
                    # 解析消息
                    msg_dict = json.loads(message)
                    msg = Message.from_dict(msg_dict)

                    # 处理消息
                    await self._handle_message(msg)

                except json.JSONDecodeError as e:
                    logger.error(f"消息解析失败: {e}")
                except Exception as e:
                    logger.error(f"处理消息失败: {e}")

        except ConnectionClosed:
            logger.warning("WebSocket连接已关闭")
            self._connected = False

            # 自动重连
            if self.auto_reconnect and not self._stop_event.is_set():
                await self._reconnect()

    async def _handle_message(self, message: Message) -> None:
        """处理接收到的消息"""
        logger.debug(f"收到消息: {message.type.value}")

        # 特殊处理握手响应
        if message.type == MessageType.HANDSHAKE:
            self._session_id = message.data.get("session_id")
            logger.info(f"握手成功，Session ID: {self._session_id}")

        # 调用注册的处理器
        handlers = self._message_handlers.get(message.type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
            except Exception as e:
                logger.error(f"消息处理器执行失败: {e}")

    async def _ping_loop(self) -> None:
        """心跳循环"""
        while self._connected and not self._stop_event.is_set():
            try:
                await asyncio.sleep(self.ping_interval)

                if self._connected:
                    ping = Message(
                        id=self._generate_message_id(),
                        type=MessageType.PING,
                        timestamp=self._get_timestamp(),
                        session_id=self._session_id,
                        data={"ping_id": self._generate_message_id()}
                    )

                    await self._send_message(ping)
                    logger.debug("心跳消息已发送")

            except Exception as e:
                logger.error(f"心跳发送失败: {e}")
                break

    async def _send_message(self, message: Message) -> None:
        """发送消息"""
        if not self._connected or not self._websocket:
            raise ConnectionError("WebSocket未连接")

        message_str = message.to_json()
        await self._websocket.send(message_str)
        logger.debug(f"消息已发送: {message.type.value}")

    async def _reconnect(self) -> None:
        """重新连接"""
        while self.auto_reconnect and not self._stop_event.is_set():
            try:
                logger.info(f"尝试重新连接...（{self.reconnect_interval}秒后）")
                await asyncio.sleep(self.reconnect_interval)

                if await self.connect():
                    logger.info("重新连接成功")
                    break

            except Exception as e:
                logger.error(f"重新连接失败: {e}")

    def register_handler(self, message_type: MessageType, handler: Callable) -> None:
        """
        注册消息处理器

        Args:
            message_type: 消息类型
            handler: 处理器函数（支持同步和异步）
        """
        if message_type not in self._message_handlers:
            self._message_handlers[message_type] = []

        self._message_handlers[message_type].append(handler)
        logger.debug(f"已注册{message_type.value}处理器")

    async def send_task(
        self,
        task_type: str,
        target_agent: AgentType,
        parameters: Dict[str, Any],
        priority: int = 5
    ) -> str:
        """
        发送任务请求

        Args:
            task_type: 任务类型
            target_agent: 目标Agent
            parameters: 任务参数
            priority: 优先级（0-10）

        Returns:
            消息ID
        """
        task = TaskRequest(
            id=self._generate_message_id(),
            type=MessageType.TASK,
            timestamp=self._get_timestamp(),
            session_id=self._session_id,
            data={},  # 会被to_dict覆盖
            task_type=task_type,
            target_agent=target_agent,
            priority=priority,
            parameters=parameters
        )

        await self._send_message(task)
        return task.id

    async def send_query(
        self,
        query_type: str,
        parameters: Dict[str, Any]
    ) -> str:
        """
        发送查询请求

        Args:
            query_type: 查询类型
            parameters: 查询参数

        Returns:
            消息ID
        """
        query = Message(
            id=self._generate_message_id(),
            type=MessageType.QUERY,
            timestamp=self._get_timestamp(),
            session_id=self._session_id,
            data={
                "type": query_type,
                "parameters": parameters
            }
        )

        await self._send_message(query)
        return query.id

    async def send_progress(
        self,
        progress: int,
        status: str,
        current_step: str = "",
        total_steps: int = 0
    ) -> None:
        """
        发送进度更新

        Args:
            progress: 进度百分比（0-100）
            status: 状态描述
            current_step: 当前步骤
            total_steps: 总步骤数
        """
        progress_msg = ProgressUpdate(
            id=self._generate_message_id(),
            type=MessageType.PROGRESS,
            timestamp=self._get_timestamp(),
            session_id=self._session_id,
            data={},  # 会被to_dict覆盖
            progress=progress,
            status=status,
            current_step=current_step,
            total_steps=total_steps
        )

        await self._send_message(progress_msg)

    async def send_response(
        self,
        success: bool,
        result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        发送响应

        Args:
            success: 是否成功
            result: 结果数据
            metadata: 元数据
        """
        response = Message(
            id=self._generate_message_id(),
            type=MessageType.RESPONSE,
            timestamp=self._get_timestamp(),
            session_id=self._session_id,
            data={
                "success": success,
                "result": result,
                "metadata": metadata or {}
            }
        )

        await self._send_message(response)

    async def send_error(
        self,
        error_code: str,
        error_msg: str,
        details: str = ""
    ) -> None:
        """
        发送错误消息

        Args:
            error_code: 错误码
            error_msg: 错误消息
            details: 详细信息
        """
        error = ErrorResponse(
            id=self._generate_message_id(),
            type=MessageType.ERROR,
            timestamp=self._get_timestamp(),
            session_id=self._session_id,
            data={},  # 会被to_dict覆盖
            error_code=error_code,
            error_msg=error_msg,
            details=details
        )

        await self._send_message(error)

    async def disconnect(self) -> None:
        """断开连接"""
        logger.info("断开WebSocket连接")

        self._stop_event.set()
        self._connected = False

        if self._websocket:
            await self._websocket.close()

    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self._connected

    @property
    def session_id(self) -> Optional[str]:
        """获取会话ID"""
        return self._session_id

    @property
    def client_id(self) -> str:
        """获取客户端ID"""
        return self._client_id


# 便捷函数
async def create_client(
    gateway_url: str = "ws://localhost:8005/ws",
    **_kwargs  # noqa: ARG001
) -> WebSocketClient:
    """
    创建并连接WebSocket客户端

    Args:
        gateway_url: Gateway WebSocket URL
        **_kwargs  # noqa: ARG001: 其他参数传递给WebSocketClient

    Returns:
        已连接的WebSocket客户端
    """
    client = WebSocketClient(gateway_url=gateway_url, **_kwargs  # noqa: ARG001)
    await client.connect()
    return client
