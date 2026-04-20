"""
Agent WebSocket适配器基类

提供Agent与Gateway WebSocket通信的统一接口。
"""

import asyncio
import logging
from typing import Any, Dict, Optional
from abc import ABC, abstractmethod

from .client import WebSocketClient, MessageType, AgentType


logger = logging.getLogger(__name__)


class BaseAgentAdapter(ABC):
    """
    Agent WebSocket适配器基类

    所有Python Agent都应该继承此类，实现与Gateway的WebSocket通信。
    """

    def __init__(
        self,
        agent_type: AgentType,
        gateway_url: str = "ws://localhost:8005/ws",
        auth_token: str = "demo_token",
        **kwargs
    ):
        """
        初始化Agent适配器

        Args:
            agent_type: Agent类型
            gateway_url: Gateway WebSocket URL
            auth_token: 认证Token
            **kwargs: 其他参数传递给WebSocketClient
        """
        self.agent_type = agent_type
        self.gateway_url = gateway_url
        self.auth_token = auth_token

        # 创建WebSocket客户端
        self.client = WebSocketClient(
            gateway_url=gateway_url,
            auth_token=auth_token,
            **kwargs
        )

        # 注册消息处理器
        self._register_handlers()

        # Agent状态
        self._running = False
        self._tasks: Dict[str, asyncio.Task] = {}

        logger.info(f"{self.agent_type.value} Agent适配器已初始化")

    def _register_handlers(self) -> None:
        """注册消息处理器"""
        self.client.register_handler(MessageType.TASK, self._handle_task)
        self.client.register_handler(MessageType.QUERY, self._handle_query)
        self.client.register_handler(MessageType.CANCEL, self._handle_cancel)
        self.client.register_handler(MessageType.PING, self._handle_ping)

    async def _handle_task(self, message) -> None:
        """
        处理任务消息

        Args:
            message: 任务消息
        """
        task_type = message.data.get("task_type")
        parameters = message.data.get("parameters", {})
        priority = message.data.get("priority", 5)

        logger.info(f"收到任务: {task_type} (优先级: {priority})")

        # 在后台任务中处理
        task_id = message.id
        task = asyncio.create_task(self._process_task(task_id, task_type, parameters))
        self._tasks[task_id] = task

    async def _handle_query(self, message) -> None:
        """
        处理查询消息

        Args:
            message: 查询消息
        """
        query_type = message.data.get("type")
        parameters = message.data.get("parameters", {})

        logger.info(f"收到查询: {query_type}")

        try:
            # 调用子类实现的查询处理
            result = await self.handle_query(query_type, parameters)

            # 发送响应
            await self.client.send_response(
                success=True,
                result=result,
                metadata={"query_type": query_type}
            )

        except Exception as e:
            logger.error(f"查询处理失败: {e}")
            await self.client.send_error(
                error_code="QUERY_ERROR",
                error_msg=str(e),
                details=f"查询类型: {query_type}"
            )

    async def _handle_cancel(self, message) -> None:
        """
        处理取消消息

        Args:
            message: 取消消息
        """
        task_id = message.data.get("task_id") or message.id

        if task_id in self._tasks:
            task = self._tasks[task_id]
            task.cancel()
            del self._tasks[task_id]

            logger.info(f"任务已取消: {task_id}")

            await self.client.send_response(
                success=True,
                result={"cancelled": True, "task_id": task_id},
                metadata={"action": "cancel"}
            )
        else:
            logger.warning(f"任务不存在: {task_id}")

    async def _handle_ping(self, message) -> None:
        """处理心跳消息"""
        # Pong消息会由客户端自动处理
        pass

    async def _process_task(self, task_id: str, task_type: str, parameters: Dict[str, Any]) -> None:
        """
        处理任务（后台执行）

        Args:
            task_id: 任务ID
            task_type: 任务类型
            parameters: 任务参数
        """
        try:
            # 调用子类实现的任务处理
            result = await self.handle_task(task_type, parameters, self._progress_callback)

            # 发送完成响应
            await self.client.send_response(
                success=True,
                result=result,
                metadata={
                    "task_id": task_id,
                    "task_type": task_type,
                    "agent": self.agent_type.value
                }
            )

            logger.info(f"任务完成: {task_type}")

        except asyncio.CancelledError:
            logger.info(f"任务被取消: {task_id}")
            await self.client.send_error(
                error_code="TASK_CANCELLED",
                error_msg="任务已被取消",
                details=f"任务ID: {task_id}"
            )

        except Exception as e:
            logger.error(f"任务处理失败: {e}")
            await self.client.send_error(
                error_code="TASK_ERROR",
                error_msg=str(e),
                details=f"任务类型: {task_type}"
            )

        finally:
            # 清理任务
            if task_id in self._tasks:
                del self._tasks[task_id]

    async def _progress_callback(self, progress: int, status: str, current_step: str = "", total_steps: int = 0) -> None:
        """
        进度回调函数

        Args:
            progress: 进度百分比（0-100）
            status: 状态描述
            current_step: 当前步骤
            total_steps: 总步骤数
        """
        await self.client.send_progress(progress, status, current_step, total_steps)

    @abstractmethod
    async def handle_task(
        self,
        task_type: str,
        parameters: Dict[str, Any],
        progress_callback: callable
    ) -> Dict[str, Any]:
        """
        处理任务（子类必须实现）

        Args:
            task_type: 任务类型
            parameters: 任务参数
            progress_callback: 进度回调函数

        Returns:
            任务结果
        """
        raise NotImplementedError("子类必须实现handle_task方法")

    @abstractmethod
    async def handle_query(self, query_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理查询（子类必须实现）

        Args:
            query_type: 查询类型
            parameters: 查询参数

        Returns:
            查询结果
        """
        raise NotImplementedError("子类必须实现handle_query方法")

    async def start(self) -> None:
        """启动Agent"""
        logger.info(f"启动{self.agent_type.value} Agent...")

        # 连接到Gateway
        if not await self.client.connect():
            raise ConnectionError("无法连接到Gateway")

        self._running = True
        logger.info(f"{self.agent_type.value} Agent已启动")

    async def stop(self) -> None:
        """停止Agent"""
        logger.info(f"停止{self.agent_type.value} Agent...")

        self._running = False

        # 取消所有任务
        for task_id, task in self._tasks.items():
            task.cancel()

        # 断开连接
        await self.client.disconnect()

        logger.info(f"{self.agent_type.value} Agent已停止")

    async def run(self) -> None:
        """运行Agent（阻塞）"""
        await self.start()

        try:
            # 保持运行
            while self._running and self.client.is_connected:
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            logger.info("Agent运行被取消")

        finally:
            await self.stop()

    @property
    def is_running(self) -> bool:
        """Agent是否正在运行"""
        return self._running

    @property
    def is_connected(self) -> bool:
        """是否已连接到Gateway"""
        return self.client.is_connected

    @property
    def session_id(self) -> Optional[str]:
        """获取会话ID"""
        return self.client.session_id

    async def notify(self, level: str, title: str, body: str) -> None:
        """
        发送通知消息

        Args:
            level: 级别（info/warn/error）
            title: 标题
            body: 内容
        """
        from .client import Message

        notification = Message(
            id=self.client._generate_message_id(),
            type=MessageType.NOTIFY,
            timestamp=self.client._get_timestamp(),
            session_id=self.client.session_id,
            data={
                "level": level,
                "title": title,
                "body": body
            }
        )

        await self.client._send_message(notification)
