#!/usr/bin/env python3
"""
Agent Loop 增强版引擎

集成流式响应、LLM 适配器和事件发布的完整 Agent Loop 实现。

作者: Athena平台团队
创建时间: 2026-04-20
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, AsyncIterator

from core.llm.unified_llm_manager import UnifiedLLMManager
from core.tools.unified_registry import get_unified_registry
from core.tools.tool_call_manager import call_tool

from .event_publisher import AgentEventPublisher
from .llm_adapter import LLMAdapter, LLMRequest, LLMResponse
from .stream_events import (
    AssistantTextDelta,
    AssistantTurnComplete,
    ErrorEvent,
    StreamEvent,
    StatusEvent,
    ToolExecutionCompleted,
    ToolExecutionStarted,
)
from .streaming_handler import StreamingHandler

logger = logging.getLogger(__name__)


@dataclass
class AgentLoopConfig:
    """Agent Loop 配置"""

    agent_name: str
    agent_type: str
    system_prompt: str
    max_iterations: int = 10
    enable_streaming: bool = True
    enable_events: bool = True
    default_model: str = "claude-sonnet-4-6"


@dataclass
class AgentResult:
    """代理执行结果"""

    content: str = ""
    success: bool = True
    iterations: int = 0
    total_time: float = 0.0
    tool_executions: int = 0
    error: Optional[str] = None


class EnhancedAgentLoop:
    """增强版 Agent Loop

    集成流式响应、LLM 适配器和事件发布。
    """

    def __init__(
        self,
        config: AgentLoopConfig,
        llm_manager: UnifiedLLMManager | None = None,
    ):
        """初始化增强版 Agent Loop

        Args:
            config: Agent Loop 配置
            llm_manager: LLM 管理器
        """
        self.config = config

        # LLM 适配器
        self.llm_adapter = LLMAdapter(
            llm_manager=llm_manager,
            default_model=config.default_model,
        )

        # 工具注册表
        self.tool_registry = get_unified_registry()

        # 事件发布器
        self.event_publisher: AgentEventPublisher | None = None
        if config.enable_events:
            self.event_publisher = AgentEventPublisher(
                agent_id=config.agent_name,
                agent_type=config.agent_type,
                agent_name=config.agent_name,
            )

        # 流式处理器
        self.streaming_handler: StreamingHandler | None = None
        if config.enable_streaming:
            from .streaming_handler import LoggingStreamingHandler

            self.streaming_handler = LoggingStreamingHandler()

        # 执行统计
        self.stats = {
            "total_calls": 0,
            "total_tool_executions": 0,
            "total_time": 0.0,
            "total_errors": 0,
        }

        logger.info(
            f"🔄 增强版 Agent Loop 已创建: {config.agent_name} "
            f"(流式: {config.enable_streaming}, 事件: {config.enable_events})"
        )

    async def initialize(self) -> None:
        """初始化 Agent Loop"""
        # 启动流式处理器
        if self.streaming_handler:
            await self.streaming_handler.start()

        # 发布启动事件
        if self.event_publisher:
            capabilities = [tool.tool_id for tool in self.tool_registry.search_tools()]
            await self.event_publisher.publish_agent_started(capabilities=capabilities)

        logger.info(f"✅ Agent Loop 已初始化: {self.config.agent_name}")

    async def shutdown(self) -> None:
        """关闭 Agent Loop"""
        # 停止流式处理器
        if self.streaming_handler:
            await self.streaming_handler.stop()

        # 发布停止事件
        if self.event_publisher:
            await self.event_publisher.publish_agent_stopped(reason="normal_shutdown")

        logger.info(f"🛑 Agent Loop 已关闭: {self.config.agent_name}")

    async def run(
        self,
        user_message: str,
        context: Optional[dict[str, Any]] = None,
    ) -> AgentResult:
        """执行 Agent Loop

        Args:
            user_message: 用户消息
            context: 上下文信息

        Returns:
            AgentResult: 执行结果
        """
        start_time = time.time()

        try:
            # 构建消息历史
            messages = [
                {"role": "system", "content": self.config.system_prompt},
                {"role": "user", "content": user_message},
            ]

            # 获取工具列表
            tools = self._get_tools_for_llm()

            # 执行循环
            iteration = 0
            tool_executions = 0
            final_content = ""

            while iteration < self.config.max_iterations:
                iteration += 1
                logger.info(f"🔄 [迭代 {iteration}] 调用 LLM...")

                # 发送状态事件
                await self._emit_status_event(f"迭代 {iteration}/{self.config.max_iterations}")

                # 调用 LLM（流式）
                llm_request = LLMRequest(
                    messages=messages,
                    tools=tools,
                    stream=self.config.enable_streaming,
                )

                if self.config.enable_streaming:
                    # 流式调用
                    response = await self._process_llm_stream(llm_request)
                else:
                    # 非流式调用
                    response = await self.llm_adapter.call_llm(llm_request)

                # 检查停止条件
                if response.stop_reason != "tool_use":
                    # 执行完成
                    final_content = response.content
                    break

                # 处理工具调用
                logger.info(f"🔧 [迭代 {iteration}] 处理 {len(response.tool_uses)} 个工具调用")

                for tool_use in response.tool_uses:
                    tool_result = await self._execute_tool(tool_use)
                    tool_executions += 1

                    # 添加工具结果到消息历史
                    messages.append({
                        "role": "tool",
                        "content": str(tool_result.result),
                        "tool_use_id": tool_use.get("id", ""),
                    })

                    # 检查是否出错
                    if not tool_result.success:
                        logger.error(f"❌ 工具执行失败: {tool_result.error}")
                        await self._emit_error_event(f"工具执行失败: {tool_result.error}")
                        break

            # 完成
            elapsed = time.time() - start_time
            self.stats["total_calls"] += 1
            self.stats["total_time"] += elapsed
            self.stats["total_tool_executions"] += tool_executions

            logger.info(
                f"✅ Agent Loop 完成: {iteration} 次迭代, {tool_executions} 次工具执行, {elapsed:.2f}秒"
            )

            return AgentResult(
                content=final_content or response.content,
                success=True,
                iterations=iteration,
                total_time=elapsed,
                tool_executions=tool_executions,
            )

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"❌ Agent Loop 错误: {e}")
            self.stats["total_errors"] += 1

            # 发布错误事件
            if self.event_publisher:
                await self.event_publisher.publish_agent_error(
                    error_type=type(e).__name__,
                    error_message=str(e),
                )

            return AgentResult(
                content="",
                success=False,
                iterations=iteration,
                total_time=elapsed,
                tool_executions=tool_executions,
                error=str(e),
            )

    async def run_stream(
        self,
        user_message: str,
        context: Optional[dict[str, Any]] = None,
    ) -> AsyncIterator[StreamEvent]:
        """流式执行 Agent Loop

        Args:
            user_message: 用户消息
            context: 上下文信息

        Yields:
            StreamEvent: 流式事件
        """
        start_time = time.time()

        try:
            # 构建消息历史
            messages = [
                {"role": "system", "content": self.config.system_prompt},
                {"role": "user", "content": user_message},
            ]

            # 获取工具列表
            tools = self._get_tools_for_llm()

            # 执行循环
            iteration = 0
            tool_executions = 0

            while iteration < self.config.max_iterations:
                iteration += 1

                # 发送状态事件
                yield StatusEvent(
                    message=f"迭代 {iteration}/{self.config.max_iterations}",
                    level="info",
                )

                # 调用 LLM（流式）
                llm_request = LLMRequest(
                    messages=messages,
                    tools=tools,
                    stream=True,
                )

                content_buffer = ""

                # 处理流式响应
                async for event in self.llm_adapter.call_llm_stream(llm_request):
                    # 转发事件
                    yield event

                    # 收集内容
                    if isinstance(event, AssistantTextDelta):
                        content_buffer += event.text
                    elif isinstance(event, AssistantTurnComplete):
                        # 检查停止条件
                        if event.tool_calls:
                            # 有工具调用，处理工具
                            for tool_use in event.tool_calls:
                                yield ToolExecutionStarted(
                                    tool_id=tool_use.get("name", ""),
                                    tool_name=tool_use.get("name", ""),
                                    tool_input=tool_use.get("input", {}),
                                    tool_use_id=tool_use.get("id", ""),
                                )

                                tool_result = await self._execute_tool(tool_use)
                                tool_executions += 1

                                yield ToolExecutionCompleted(
                                    tool_id=tool_use.get("name", ""),
                                    tool_name=tool_use.get("name", ""),
                                    output=str(tool_result.result),
                                    is_error=not tool_result.success,
                                    execution_time=tool_result.execution_time,
                                )

                                # 添加到消息历史
                                messages.append({
                                    "role": "tool",
                                    "content": str(tool_result.result),
                                    "tool_use_id": tool_use.get("id", ""),
                                })
                        else:
                            # 完成
                            elapsed = time.time() - start_time
                            self.stats["total_calls"] += 1
                            self.stats["total_time"] += elapsed
                            self.stats["total_tool_executions"] += tool_executions

                            logger.info(
                                f"✅ Agent Loop 流式执行完成: {iteration} 次迭代, {elapsed:.2f}秒"
                            )
                            return

            # 达到最大迭代次数
            yield ErrorEvent(
                message="达到最大迭代次数",
                recoverable=False,
            )

        except Exception as e:
            logger.error(f"❌ Agent Loop 流式执行错误: {e}")
            yield ErrorEvent(
                message=f"执行错误: {str(e)}",
                recoverable=True,
                error_type=type(e).__name__,
            )

    async def _process_llm_stream(self, request: LLMRequest) -> LLMResponse:
        """处理 LLM 流式响应

        Args:
            request: LLM 请求

        Returns:
            LLMResponse: LLM 响应
        """
        content_buffer = ""
        tool_uses = []

        async for event in self.llm_adapter.call_llm_stream(request):
            # 转发到流式处理器
            if self.streaming_handler:
                await self.streaming_handler.emit(event)

            # 收集内容
            if isinstance(event, AssistantTextDelta):
                content_buffer += event.text
            elif isinstance(event, AssistantTurnComplete):
                tool_uses = event.tool_calls

        return LLMResponse(
            content=content_buffer,
            stop_reason="tool_use" if tool_uses else "end_turn",
            tool_uses=tool_uses,
        )

    async def _execute_tool(self, tool_use: dict) -> Any:
        """执行工具

        Args:
            tool_use: 工具调用信息

        Returns:
            ToolResult: 工具执行结果
        """
        from .agent_loop import ToolResult

        start_time = time.time()

        tool_id = tool_use.get("name", "")
        parameters = tool_use.get("input", {})
        tool_use_id = tool_use.get("id", "")

        logger.info(f"🔧 执行工具: {tool_id}")

        # 发布工具执行开始事件
        if self.event_publisher:
            await self.event_publisher.publish_tool_execution_started(
                tool_id=tool_id,
                tool_name=tool_id,
                tool_use_id=tool_use_id,
                parameters=parameters,
            )

        try:
            # 调用工具
            call_result = await call_tool(tool_id, parameters)
            execution_time = time.time() - start_time

            if call_result.status == "success":
                result = ToolResult(
                    tool_id=tool_id,
                    success=True,
                    result=call_result.result,
                    execution_time=execution_time,
                )

                # 发布工具执行完成事件
                if self.event_publisher:
                    await self.event_publisher.publish_tool_execution_completed(
                        tool_id=tool_id,
                        tool_name=tool_id,
                        tool_use_id=tool_use_id,
                        parameters=parameters,
                        result=call_result.result,
                        execution_time=execution_time,
                    )

                return result
            else:
                result = ToolResult(
                    tool_id=tool_id,
                    success=False,
                    error=call_result.error_message or "工具执行失败",
                    execution_time=execution_time,
                )

                # 发布工具执行失败事件
                if self.event_publisher:
                    await self.event_publisher.publish_tool_execution_failed(
                        tool_id=tool_id,
                        tool_name=tool_id,
                        tool_use_id=tool_use_id,
                        parameters=parameters,
                        error_type="execution_error",
                        error_message=call_result.error_message or "工具执行失败",
                        execution_time=execution_time,
                    )

                return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ 工具执行失败: {tool_id} - {e}")

            result = ToolResult(
                tool_id=tool_id,
                success=False,
                error=str(e),
                execution_time=execution_time,
            )

            # 发布工具执行失败事件
            if self.event_publisher:
                await self.event_publisher.publish_tool_execution_failed(
                    tool_id=tool_id,
                    tool_name=tool_id,
                    tool_use_id=tool_use_id,
                    parameters=parameters,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    execution_time=execution_time,
                )

            return result

    async def _emit_status_event(self, message: str) -> None:
        """发送状态事件

        Args:
            message: 状态消息
        """
        if self.streaming_handler:
            from .stream_events import StatusEvent

            await self.streaming_handler.emit(
                StatusEvent(message=message, level="info")
            )

    async def _emit_error_event(self, message: str) -> None:
        """发送错误事件

        Args:
            message: 错误消息
        """
        if self.streaming_handler:
            await self.streaming_handler.emit(
                ErrorEvent(message=message, recoverable=True)
            )

    def _get_tools_for_llm(self) -> list[dict]:
        """获取 LLM 格式的工具列表

        Returns:
            list[dict]: LLM 工具列表
        """
        tools = []
        for tool in self.tool_registry.search_tools():
            tool_info = {
                "name": tool.tool_id,
                "description": tool.description,
                "category": tool.category.value,
                "required_params": tool.required_params,
                "optional_params": tool.optional_params,
            }
            tools.append(tool_info)
        return tools

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息

        Returns:
            dict: 统计信息
        """
        stats = self.stats.copy()
        if self.streaming_handler:
            stats["streaming"] = self.streaming_handler.get_stats()
        if self.event_publisher:
            stats["events"] = self.event_publisher.get_stats()
        return stats


# ========================================
# 工厂函数
# ========================================

def create_enhanced_agent_loop(
    agent_name: str,
    agent_type: str,
    system_prompt: str,
    **_kwargs  # noqa: ARG001,
) -> EnhancedAgentLoop:
    """创建增强版 Agent Loop

    Args:
        agent_name: 代理名称
        agent_type: 代理类型
        system_prompt: 系统提示词
        **_kwargs  # noqa: ARG001: 其他配置参数

    Returns:
        EnhancedAgentLoop: 增强版 Agent Loop 实例
    """
    config = AgentLoopConfig(
        agent_name=agent_name,
        agent_type=agent_type,
        system_prompt=system_prompt,
        **_kwargs  # noqa: ARG001,
    )
    return EnhancedAgentLoop(config)


__all__ = [
    "AgentLoopConfig",
    "AgentResult",
    "EnhancedAgentLoop",
    "create_enhanced_agent_loop",
]
