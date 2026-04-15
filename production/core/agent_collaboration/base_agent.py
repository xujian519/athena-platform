#!/usr/bin/env python3
"""
Agent基类
Base Agent Class

所有专业化Agent的基类,定义通用接口和行为
"""

from __future__ import annotations
import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import Any

from .agent_registry import (
    AgentInfo,
    AgentRegistry,
    AgentStatus,
    AgentType,
    get_agent_registry,
)
from .communication import MessageBus, ResponseMessage, TaskMessage, TaskPriority, get_message_bus

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Agent基类"""

    def __init__(
        self,
        agent_id: str,
        name: str,
        agent_type: AgentType,
        description: str = "",
        config: dict[str, Any] | None = None,
    ):
        self.agent_id = agent_id
        self.name = name
        self.agent_type = agent_type
        self.description = description
        self.config = config or {}

        # 状态管理
        self.status = AgentStatus.IDLE
        self.current_task_id: str | None = None

        # 性能统计
        self.task_count = 0
        self.success_count = 0
        self.error_count = 0
        self.total_execution_time = 0.0

        # 服务引用
        self.message_bus: MessageBus | None = None
        self.agent_registry: AgentRegistry | None = None

        # 初始化标志
        self.initialized = False

    async def initialize(self):
        """初始化Agent"""
        try:
            # 获取全局服务
            self.message_bus = get_message_bus()
            self.agent_registry = get_agent_registry()

            # 创建Agent信息
            agent_info = AgentInfo(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                name=self.name,
                description=self.description,
                capabilities=self.get_capabilities(),
                status=self.status,
                config=self.config,
            )

            # 注册到Agent注册中心
            await self.agent_registry.register_agent(agent_info)

            # 订阅消息总线
            self.message_bus.subscribe(self.agent_id, self.handle_message)

            # 启动心跳任务
            asyncio.create_task(self._heartbeat_loop())

            self.initialized = True
            logger.info(f"✅ Agent {self.name} 初始化成功")

        except Exception as e:
            logger.error(f"❌ Agent {self.name} 初始化失败: {e}")
            raise

    @abstractmethod
    async def process_task(self, task_message: TaskMessage) -> ResponseMessage:
        """
        处理任务的抽象方法

        Args:
            task_message: 任务消息

        Returns:
            ResponseMessage: 响应消息
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> list[str]:
        """
        获取Agent能力列表

        Returns:
            list[str]: 能力列表
        """
        pass

    async def handle_message(self, message: Any) -> None:
        """处理收到的消息"""
        try:
            if isinstance(message, TaskMessage):
                await self._handle_task_message(message)
            elif isinstance(message, ResponseMessage):
                await self._handle_response_message(message)
            else:
                logger.warning(f"⚠️ Agent {self.name} 收到未知消息类型: {type(message)}")

        except Exception as e:
            logger.error(f"❌ Agent {self.name} 消息处理失败: {e}")

    async def _handle_task_message(self, task_message: TaskMessage):
        """处理任务消息"""
        try:
            # 更新状态为忙碌
            await self._set_busy(task_message.task_id)

            start_time = time.time()

            logger.info(f"🔧 Agent {self.name} 开始处理任务: {task_message.task_type}")

            # 处理任务
            response = await self.process_task(task_message)

            # 计算执行时间
            execution_time = time.time() - start_time
            response.execution_time = execution_time

            # 更新性能统计
            self._update_performance_metrics(response.success, execution_time)

            # 发送响应
            if self.message_bus:
                await self.message_bus.send_response(response)  # type: ignore[attr-defined]

            # 更新状态为空闲
            await self._set_idle()

            logger.info(
                f"✅ Agent {self.name} 任务完成: {response.success}, 耗时: {execution_time:.2f}s"
            )

        except Exception as e:
            logger.error(f"❌ Agent {self.name} 任务处理失败: {e}")

            # 发送错误响应
            error_response = ResponseMessage(
                task_id=task_message.task_id,
                sender_id=self.agent_id,
                recipient_id=task_message.sender_id,
                success=False,
                error_message=str(e),
                execution_time=0.0,
            )

            if self.message_bus:
                await self.message_bus.send_response(error_response)  # type: ignore[attr-defined]
            await self._set_idle()

    async def _handle_response_message(self, response_message: ResponseMessage):
        """处理响应消息"""
        # 基类不处理响应消息,子类可以重写
        pass

    async def _set_busy(self, task_id: str):
        """设置状态为忙碌"""
        self.status = AgentStatus.BUSY
        self.current_task_id = task_id
        if self.agent_registry:
            await self.agent_registry.update_agent_status(self.agent_id, self.status, task_id)  # type: ignore[attr-defined]

    async def _set_idle(self):
        """设置状态为空闲"""
        self.status = AgentStatus.IDLE
        self.current_task_id = None
        if self.agent_registry:
            await self.agent_registry.update_agent_status(self.agent_id, self.status)  # type: ignore[attr-defined]

    def _update_performance_metrics(self, success: bool, execution_time: float) -> Any:
        """更新性能指标"""
        self.task_count += 1
        self.total_execution_time += execution_time

        if success:
            self.success_count += 1
        else:
            self.error_count += 1

        # 计算成功率
        success_rate = self.success_count / self.task_count if self.task_count > 0 else 0.0

        # 计算平均执行时间
        avg_execution_time = (
            self.total_execution_time / self.task_count if self.task_count > 0 else 0.0
        )

        # 更新到注册中心
        metrics = {
            "task_count": self.task_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": success_rate,
            "avg_execution_time": avg_execution_time,
            "last_execution_time": execution_time,
        }

        if self.agent_registry:
            asyncio.create_task(self.agent_registry.update_performance_metrics(self.agent_id, metrics))  # type: ignore[attr-defined]

    async def _heartbeat_loop(self):
        """心跳循环"""
        while True:
            try:
                if self.agent_registry:
                    await self.agent_registry.update_heartbeat(self.agent_id)

                await asyncio.sleep(30)  # 30秒心跳间隔

            except Exception as e:
                logger.error(f"❌ Agent {self.name} 心跳失败: {e}")
                await asyncio.sleep(5)

    async def send_message(
        self, recipient_id: str, task_type: str, content: dict[str, Any], priority: int = 2
    ):
        """
        发送消息给其他Agent

        Args:
            recipient_id: 接收者ID
            task_type: 任务类型
            content: 消息内容
            priority: 优先级
        """
        if not self.message_bus:
            logger.error(f"❌ Agent {self.name} 消息总线未初始化")
            return

        message = TaskMessage(
            sender_id=self.agent_id,
            recipient_id=recipient_id,
            task_type=task_type,
            content=content,
            priority=TaskPriority(priority),  # type: ignore[call-arg]
        )

        await self.message_bus.send_message(message)

    def get_status(self) -> dict[str, Any]:
        """获取Agent状态信息"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "type": self.agent_type.value,
            "status": self.status.value,
            "current_task_id": self.current_task_id,
            "initialized": self.initialized,
            "task_count": self.task_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": self.success_count / self.task_count if self.task_count > 0 else 0.0,
            "avg_execution_time": (
                self.total_execution_time / self.task_count if self.task_count > 0 else 0.0
            ),
        }

    async def shutdown(self):
        """关闭Agent"""
        try:
            # 注销Agent
            if self.agent_registry:
                await self.agent_registry.unregister_agent(self.agent_id)

            # 取消订阅
            if self.message_bus:
                self.message_bus.unsubscribe(self.agent_id)

            self.initialized = False
            logger.info(f"✅ Agent {self.name} 已关闭")

        except Exception as e:
            logger.error(f"❌ Agent {self.name} 关闭失败: {e}")
