#!/usr/bin/env python3
"""
AgentProxy基类和代理实现
提供Python智能体与Gateway WebSocket通信的代理框架

核心功能:
1. gRPC/WebSocket客户端通信 - 与Gateway双向通信
2. 任务接收和执行 - 接收任务并分派给具体Agent
3. 流式结果返回 - 支持流式返回执行结果
4. 生命周期管理 - 启动、停止、健康检查

作者: Athena平台团队
创建时间: 2026-04-21
版本: v1.0.0
"""

from __future__ import annotations

import asyncio
import json
import logging
import signal
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, AsyncGenerator, Callable, Optional

# Gateway客户端导入
try:
    from core.agents.gateway_client import (
        GatewayClient,
        GatewayClientConfig,
        AgentType as GatewayAgentType,
        Message,
        MessageType,
        TaskRequest,
        Response
    )
    GATEWAY_AVAILABLE = True
except ImportError:
    GATEWAY_AVAILABLE = False
    GatewayClient = None  # type: ignore
    GatewayClientConfig = None  # type: ignore
    GatewayAgentType = None  # type: ignore
    Message = None  # type: ignore
    MessageType = None  # type: ignore
    TaskRequest = None  # type: ignore
    Response = None  # type: ignore

logger = logging.getLogger(__name__)


# ==================== 枚举定义 ====================

class ProxyStatus(str, Enum):
    """代理状态"""
    STARTING = "starting"     # 启动中
    READY = "ready"           # 就绪
    BUSY = "busy"             # 忙碌（执行任务中）
    STOPPING = "stopping"     # 停止中
    STOPPED = "stopped"       # 已停止
    ERROR = "error"           # 错误状态


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"       # 待处理
    RUNNING = "running"       # 执行中
    COMPLETED = "completed"   # 已完成
    FAILED = "failed"         # 失败
    CANCELLED = "cancelled"   # 已取消


# ==================== 数据结构 ====================

@dataclass
class ProxyConfig:
    """代理配置"""
    # Gateway连接配置
    gateway_url: str = "ws://localhost:8005/ws"
    agent_type: GatewayAgentType = GatewayAgentType.UNKNOWN
    agent_id: str = ""

    # 通信配置
    heartbeat_interval: int = 30       # 心跳间隔（秒）
    reconnect_interval: int = 5        # 重连间隔（秒）
    max_reconnect_attempts: int = 10   # 最大重连次数
    message_timeout: int = 120         # 消息超时（秒）

    # 执行配置
    max_concurrent_tasks: int = 3      # 最大并发任务数
    task_timeout: int = 300            # 任务超时（秒）
    enable_streaming: bool = True      # 启用流式返回

    # 日志配置
    log_level: str = "INFO"
    log_file: Optional[str] = None


@dataclass
class TaskContext:
    """任务上下文"""
    task_id: str
    task_type: str
    parameters: dict[str, Any]
    session_id: str
    created_at: datetime = field(default_factory=datetime.now)
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    progress: int = 0


@dataclass
class ProgressUpdate:
    """进度更新"""
    task_id: str
    progress: int              # 进度百分比 (0-100)
    message: str               # 状态消息
    current_step: str = ""     # 当前步骤
    total_steps: int = 0       # 总步骤数
    details: dict[str, Any] = field(default_factory=dict)


# ==================== AgentProxy基类 ====================

class AgentProxy(ABC):
    """
    Agent代理基类

    功能:
    1. 与Gateway WebSocket建立连接
    2. 接收任务请求
    3. 分派任务给具体Agent执行
    4. 流式返回执行结果
    5. 管理代理生命周期
    """

    def __init__(self, config: ProxyConfig):
        """
        初始化代理

        Args:
            config: 代理配置
        """
        self.config = config
        self.status = ProxyStatus.STARTING

        # Gateway客户端
        self._gateway_client: Optional[GatewayClient] = None
        self._gateway_config = GatewayClientConfig(
            gateway_url=config.gateway_url,
            agent_type=config.agent_type,
            agent_id=config.agent_id,
            heartbeat_interval=config.heartbeat_interval,
            reconnect_interval=config.reconnect_interval,
            max_reconnect_attempts=config.max_reconnect_attempts,
            message_timeout=config.message_timeout
        )

        # 任务管理
        self._tasks: dict[str, TaskContext] = {}
        self._task_semaphore = asyncio.Semaphore(config.max_concurrent_tasks)

        # 控制标志
        self._running = False
        self._shutdown_event = asyncio.Event()

        # 设置日志
        self._setup_logging()

        logger.info(f"🔧 AgentProxy初始化: {config.agent_type.value} @ {config.gateway_url}")

    def _setup_logging(self) -> None:
        """设置日志"""
        log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=self._get_log_handlers()
        )

    def _get_log_handlers(self) -> list[logging.Handler]:
        """获取日志处理器"""
        handlers = [logging.StreamHandler(sys.stdout)]

        if self.config.log_file:
            handlers.append(logging.FileHandler(self.config.log_file))

        return handlers

    async def start(self) -> None:
        """启动代理"""
        logger.info("🚀 启动AgentProxy...")

        try:
            # 检查Gateway可用性
            if not GATEWAY_AVAILABLE:
                raise RuntimeError("Gateway客户端不可用，请检查安装")

            # 连接到Gateway
            self._gateway_client = GatewayClient(self._gateway_config)
            if not await self._gateway_client.connect():
                raise RuntimeError("无法连接到Gateway")

            # 注册消息处理器
            self._register_handlers()

            # 标记为就绪
            self.status = ProxyStatus.READY
            self._running = True

            logger.info(f"✅ AgentProxy已启动: {self.config.agent_type.value}")
            logger.info(f"📋 Agent ID: {self._gateway_client.config.agent_id}")
            logger.info(f"🔗 Session ID: {self._gateway_client.session_id}")

        except Exception as e:
            logger.error(f"❌ 启动失败: {e}")
            self.status = ProxyStatus.ERROR
            raise

    async def stop(self) -> None:
        """停止代理"""
        logger.info("🛑 停止AgentProxy...")

        self.status = ProxyStatus.STOPPING
        self._running = False
        self._shutdown_event.set()

        # 断开Gateway连接
        if self._gateway_client:
            await self._gateway_client.disconnect()

        # 等待所有任务完成
        await self._wait_for_tasks_completion()

        self.status = ProxyStatus.STOPPED
        logger.info("✅ AgentProxy已停止")

    async def run(self) -> None:
        """运行代理（阻塞直到停止）"""
        await self.start()

        try:
            # 等待停止信号
            await self._shutdown_event.wait()
        except KeyboardInterrupt:
            logger.info("⌨️ 收到键盘中断")
        finally:
            await self.stop()

    def _register_handlers(self) -> None:
        """注册消息处理器"""
        if not self._gateway_client:
            return

        # 注册任务处理器
        self._gateway_client.register_handler(
            MessageType.TASK,
            self._handle_task_message
        )

        # 注册查询处理器
        self._gateway_client.register_handler(
            MessageType.QUERY,
            self._handle_query_message
        )

        # 注册取消处理器
        self._gateway_client.register_handler(
            MessageType.CANCEL,
            self._handle_cancel_message
        )

        logger.debug("📝 消息处理器已注册")

    async def _handle_task_message(self, message: Message) -> None:
        """处理任务消息"""
        try:
            # 解析任务
            task_data = message.data
            task_id = task_data.get("task_id") or message.id
            task_type = task_data.get("task_type", "unknown")
            parameters = task_data.get("parameters", {})

            logger.info(f"📋 收到任务: {task_id} ({task_type})")

            # 创建任务上下文
            context = TaskContext(
                task_id=task_id,
                task_type=task_type,
                parameters=parameters,
                session_id=message.session_id
            )
            self._tasks[task_id] = context

            # 异步执行任务
            asyncio.create_task(self._execute_task(context))

        except Exception as e:
            logger.error(f"❌ 处理任务消息失败: {e}")

    async def _handle_query_message(self, message: Message) -> None:
        """处理查询消息"""
        try:
            query_type = message.data.get("query_type", "status")

            if query_type == "status":
                await self._send_status_response(message.session_id)
            elif query_type == "health":
                await self._send_health_response(message.session_id)
            else:
                logger.warning(f"⚠️ 未知查询类型: {query_type}")

        except Exception as e:
            logger.error(f"❌ 处理查询消息失败: {e}")

    async def _handle_cancel_message(self, message: Message) -> None:
        """处理取消消息"""
        try:
            task_id = message.data.get("task_id")
            if task_id and task_id in self._tasks:
                context = self._tasks[task_id]
                context.status = TaskStatus.CANCELLED
                logger.info(f"🚫 任务已取消: {task_id}")

        except Exception as e:
            logger.error(f"❌ 处理取消消息失败: {e}")

    async def _execute_task(self, context: TaskContext) -> None:
        """执行任务"""
        async with self._task_semaphore:
            try:
                context.status = TaskStatus.RUNNING
                self.status = ProxyStatus.BUSY

                logger.info(f"⚙️ 执行任务: {context.task_id}")

                # 执行任务（支持流式返回）
                if self.config.enable_streaming:
                    await self._execute_task_streaming(context)
                else:
                    await self._execute_task_simple(context)

                # 发送完成消息
                if context.status != TaskStatus.CANCELLED:
                    await self._send_completion_message(context)

            except asyncio.CancelledError:
                context.status = TaskStatus.CANCELLED
                logger.info(f"🚫 任务已取消: {context.task_id}")

            except Exception as e:
                context.status = TaskStatus.FAILED
                context.error = str(e)
                logger.error(f"❌ 任务执行失败: {context.task_id} - {e}")

                await self._send_error_message(context, str(e))

            finally:
                self.status = ProxyStatus.READY

    async def _execute_task_streaming(self, context: TaskContext) -> None:
        """执行任务（流式返回）"""
        try:
            async for progress in self.execute_task_streaming(context):
                # 发送进度更新
                await self._send_progress_update(context.task_id, progress)

                # 更新上下文
                context.progress = progress.progress

        except Exception as e:
            logger.error(f"❌ 流式执行失败: {e}")
            raise

    async def _execute_task_simple(self, context: TaskContext) -> None:
        """执行任务（简单模式）"""
        result = await self.execute_task(context)
        context.result = result
        context.status = TaskStatus.COMPLETED

    async def _send_progress_update(self, task_id: str, progress: ProgressUpdate) -> None:
        """发送进度更新"""
        if not self._gateway_client:
            return

        message = Message(
            type=MessageType.PROGRESS,
            session_id=self._gateway_client.session_id,
            data={
                "task_id": task_id,
                "progress": progress.progress,
                "message": progress.message,
                "current_step": progress.current_step,
                "total_steps": progress.total_steps,
                "details": progress.details
            }
        )

        try:
            await self._gateway_client._send_message(message)
            logger.debug(f"📊 进度更新: {task_id} - {progress.progress}%")
        except Exception as e:
            logger.error(f"❌ 发送进度更新失败: {e}")

    async def _send_completion_message(self, context: TaskContext) -> None:
        """发送完成消息"""
        if not self._gateway_client:
            return

        message = Message(
            type=MessageType.RESPONSE,
            session_id=self._gateway_client.session_id,
            data={
                "task_id": context.task_id,
                "success": context.status == TaskStatus.COMPLETED,
                "result": context.result or {},
                "status": context.status.value
            }
        )

        try:
            await self._gateway_client._send_message(message)
            logger.info(f"✅ 任务完成: {context.task_id}")
        except Exception as e:
            logger.error(f"❌ 发送完成消息失败: {e}")

    async def _send_error_message(self, context: TaskContext, error: str) -> None:
        """发送错误消息"""
        if not self._gateway_client:
            return

        message = Message(
            type=MessageType.ERROR,
            session_id=self._gateway_client.session_id,
            data={
                "task_id": context.task_id,
                "error": error,
                "code": "TASK_EXECUTION_ERROR"
            }
        )

        try:
            await self._gateway_client._send_message(message)
        except Exception as e:
            logger.error(f"❌ 发送错误消息失败: {e}")

    async def _send_status_response(self, session_id: str) -> None:
        """发送状态响应"""
        if not self._gateway_client:
            return

        status_data = {
            "status": self.status.value,
            "active_tasks": len([t for t in self._tasks.values() if t.status == TaskStatus.RUNNING]),
            "total_tasks": len(self._tasks),
            "agent_type": self.config.agent_type.value
        }

        message = Message(
            type=MessageType.RESPONSE,
            session_id=session_id,
            data={"query_type": "status", "result": status_data}
        )

        await self._gateway_client._send_message(message)

    async def _send_health_response(self, session_id: str) -> None:
        """发送健康检查响应"""
        if not self._gateway_client:
            return

        health_data = {
            "healthy": self.status in (ProxyStatus.READY, ProxyStatus.BUSY),
            "status": self.status.value,
            "connected": self._gateway_client.is_connected if self._gateway_client else False
        }

        message = Message(
            type=MessageType.RESPONSE,
            session_id=session_id,
            data={"query_type": "health", "result": health_data}
        )

        await self._gateway_client._send_message(message)

    async def _wait_for_tasks_completion(self) -> None:
        """等待所有任务完成"""
        timeout = 10
        start_time = asyncio.get_event_loop().time()

        while self._tasks:
            active_tasks = [t for t in self._tasks.values() if t.status == TaskStatus.RUNNING]
            if not active_tasks:
                break

            if asyncio.get_event_loop().time() - start_time > timeout:
                logger.warning(f"⚠️ 等待任务完成超时，剩余 {len(active_tasks)} 个任务")
                break

            await asyncio.sleep(0.5)

    # ==================== 抽象方法（子类实现） ====================

    @abstractmethod
    async def execute_task(self, context: TaskContext) -> dict[str, Any]:
        """
        执行任务（简单模式）

        Args:
            context: 任务上下文

        Returns:
            dict[str, Any]: 任务结果
        """
        raise NotImplementedError

    async def execute_task_streaming(
        self,
        context: TaskContext
    ) -> AsyncGenerator[ProgressUpdate, None]:
        """
        执行任务（流式模式）

        Args:
            context: 任务上下文

        Yields:
            ProgressUpdate: 进度更新
        """
        # 默认实现：简单执行后返回完成进度
        result = await self.execute_task(context)
        yield ProgressUpdate(
            task_id=context.task_id,
            progress=100,
            message="已完成",
            details={"result": result}
        )

    # ==================== 工具方法 ====================

    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._running

    @property
    def agent_id(self) -> str:
        """获取Agent ID"""
        return self._gateway_config.agent_id if self._gateway_client else ""


# ==================== 便捷函数 ====================

async def run_proxy(proxy: AgentProxy) -> None:
    """
    运行代理（处理信号）

    Args:
        proxy: 代理实例
    """
    # 设置信号处理
    loop = asyncio.get_event_loop()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(proxy.stop()))

    # 运行代理
    await proxy.run()


def create_proxy_config(
    agent_type: str,
    gateway_url: str = "ws://localhost:8005/ws",
    **kwargs
) -> ProxyConfig:
    """
    创建代理配置

    Args:
        agent_type: Agent类型（xiaona/xiaonuo/yunxi）
        gateway_url: Gateway URL
        **kwargs: 其他配置

    Returns:
        ProxyConfig: 代理配置
    """
    agent_type_map = {
        "xiaona": GatewayAgentType.XIAONA,
        "xiaonuo": GatewayAgentType.XIAONUO,
        "yunxi": GatewayAgentType.YUNXI,
    }

    return ProxyConfig(
        gateway_url=gateway_url,
        agent_type=agent_type_map.get(agent_type.lower(), GatewayAgentType.UNKNOWN),
        **kwargs
    )
