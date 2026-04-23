#!/usr/bin/env python3
"""
事件发布器

集成 Agent Loop 与 EventBus，自动发布代理生命周期和工具执行事件。

作者: Athena平台团队
创建时间: 2026-04-20
"""
from __future__ import annotations

import logging
import time
from typing import Any

from core.events.event_bus import get_global_event_bus
from core.events.event_types import (
    AgentError,
    AgentStarted,
    AgentStopped,
    ToolExecutionCompleted as ToolExecutionCompletedEvent,
    ToolExecutionFailed,
    ToolExecutionStarted as ToolExecutionStartedEvent,
)

logger = logging.getLogger(__name__)


class AgentEventPublisher:
    """代理事件发布器

    自动发布代理相关事件到 EventBus。
    """

    def __init__(self, agent_id: str, agent_type: str, agent_name: Optional[str] = None):
        """初始化事件发布器

        Args:
            agent_id: 代理 ID
            agent_type: 代理类型
            agent_name: 代理名称
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.agent_name = agent_name
        self.event_bus = get_global_event_bus()

        # 统计
        self._stats = {
            "published_events": 0,
            "failed_events": 0,
        }

        logger.info(f"📡 事件发布器已初始化: {agent_id}")

    async def publish_agent_started(self, capabilities: Optional[list[str]] = None) -> None:
        """发布代理启动事件

        Args:
            capabilities: 能力列表
        """
        try:
            event = AgentStarted(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                agent_name=self.agent_name,
                startup_time=time.time(),
                capabilities=capabilities or [],
            )
            await self.event_bus.publish(event)
            self._stats["published_events"] += 1
            logger.info(f"✅ 已发布事件: AgentStarted - {self.agent_id}")

        except Exception as e:
            self._stats["failed_events"] += 1
            logger.error(f"❌ 发布 AgentStarted 事件失败: {e}")

    async def publish_agent_stopped(self, reason: Optional[str] = None) -> None:
        """发布代理停止事件

        Args:
            reason: 停止原因
        """
        try:
            event = AgentStopped(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                agent_name=self.agent_name,
                shutdown_time=time.time(),
                reason=reason,
            )
            await self.event_bus.publish(event)
            self._stats["published_events"] += 1
            logger.info(f"✅ 已发布事件: AgentStopped - {self.agent_id}")

        except Exception as e:
            self._stats["failed_events"] += 1
            logger.error(f"❌ 发布 AgentStopped 事件失败: {e}")

    async def publish_agent_error(
        self,
        error_type: Optional[str] = None,
        error_message: str = "",
        traceback: Optional[str] = None,
    ) -> None:
        """发布代理错误事件

        Args:
            error_type: 错误类型
            error_message: 错误消息
            traceback: 堆栈跟踪
        """
        try:
            event = AgentError(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                agent_name=self.agent_name,
                error_time=time.time(),
                error_type=error_type,
                error_message=error_message,
                traceback=traceback,
            )
            await self.event_bus.publish(event)
            self._stats["published_events"] += 1
            logger.info(f"✅ 已发布事件: AgentError - {self.agent_id}")

        except Exception as e:
            self._stats["failed_events"] += 1
            logger.error(f"❌ 发布 AgentError 事件失败: {e}")

    async def publish_tool_execution_started(
        self,
        tool_id: str,
        tool_name: str,
        tool_use_id: Optional[str] = None,
        parameters: Optional[dict[str, Any]] = None,
    ) -> None:
        """发布工具执行开始事件

        Args:
            tool_id: 工具 ID
            tool_name: 工具名称
            tool_use_id: 工具使用 ID
            parameters: 参数
        """
        try:
            event = ToolExecutionStartedEvent(
                tool_id=tool_id,
                tool_name=tool_name,
                agent_id=self.agent_id,
                tool_use_id=tool_use_id,
                parameters=parameters or {},
            )
            await self.event_bus.publish(event)
            self._stats["published_events"] += 1
            logger.debug(f"✅ 已发布事件: ToolExecutionStarted - {tool_name}")

        except Exception as e:
            self._stats["failed_events"] += 1
            logger.error(f"❌ 发布 ToolExecutionStarted 事件失败: {e}")

    async def publish_tool_execution_completed(
        self,
        tool_id: str,
        tool_name: str,
        tool_use_id: Optional[str] = None,
        parameters: Optional[dict[str, Any]] = None,
        result: Any = None,
        execution_time: float = 0.0,
    ) -> None:
        """发布工具执行完成事件

        Args:
            tool_id: 工具 ID
            tool_name: 工具名称
            tool_use_id: 工具使用 ID
            parameters: 参数
            result: 执行结果
            execution_time: 执行时间
        """
        try:
            event = ToolExecutionCompletedEvent(
                tool_id=tool_id,
                tool_name=tool_name,
                agent_id=self.agent_id,
                tool_use_id=tool_use_id,
                parameters=parameters or {},
                result=result,
                execution_time=execution_time,
            )
            await self.event_bus.publish(event)
            self._stats["published_events"] += 1
            logger.debug(f"✅ 已发布事件: ToolExecutionCompleted - {tool_name}")

        except Exception as e:
            self._stats["failed_events"] += 1
            logger.error(f"❌ 发布 ToolExecutionCompleted 事件失败: {e}")

    async def publish_tool_execution_failed(
        self,
        tool_id: str,
        tool_name: str,
        tool_use_id: Optional[str] = None,
        parameters: Optional[dict[str, Any]] = None,
        error_type: Optional[str] = None,
        error_message: str = "",
        execution_time: float = 0.0,
    ) -> None:
        """发布工具执行失败事件

        Args:
            tool_id: 工具 ID
            tool_name: 工具名称
            tool_use_id: 工具使用 ID
            parameters: 参数
            error_type: 错误类型
            error_message: 错误消息
            execution_time: 执行时间
        """
        try:
            event = ToolExecutionFailed(
                tool_id=tool_id,
                tool_name=tool_name,
                agent_id=self.agent_id,
                tool_use_id=tool_use_id,
                parameters=parameters or {},
                error_type=error_type,
                error_message=error_message,
                execution_time=execution_time,
            )
            await self.event_bus.publish(event)
            self._stats["published_events"] += 1
            logger.debug(f"✅ 已发布事件: ToolExecutionFailed - {tool_name}")

        except Exception as e:
            self._stats["failed_events"] += 1
            logger.error(f"❌ 发布 ToolExecutionFailed 事件失败: {e}")

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息

        Returns:
            dict: 统计信息
        """
        return self._stats.copy()


__all__ = [
    "AgentEventPublisher",
]
