#!/usr/bin/env python3
"""
Agent Loop 核心引擎

实现统一的代理执行循环，参考 OpenHarness 设计。

作者: Athena平台团队
创建时间: 2026-04-20
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from core.llm.unified_llm_manager import UnifiedLLMManager
from core.tools.unified_registry import get_unified_registry
from core.tools.tool_call_manager import call_tool

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """LLM 响应"""

    content: str = ""
    stop_reason: Optional[str] = None
    tool_uses: list[dict] = field(default_factory=list)
    tool_results: list[dict] = field(default_factory=list)
    stream_delta: Optional[str] = None  # 流式增量


@dataclass
class ToolResult:
    """工具执行结果"""

    tool_id: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0


class BaseAgentLoop:
    """Agent Loop 基类

    实现标准的代理执行循环，简化代理逻辑。
    """

    def __init__(
        self,
        agent_name: str,
        agent_type: str,
        system_prompt: str,
        llm_manager: UnifiedLLMManager | None = None,
    ):
        """初始化 Agent Loop

        Args:
            agent_name: 代理名称
            agent_type: 代理类型
            system_prompt: 系统提示词
            llm_manager: LLM 管理器
        """
        self.agent_name = agent_name
        self.agent_type = agent_type
        self.system_prompt = system_prompt

        # LLM 管理器
        self.llm_manager = llm_manager or UnifiedLLMManager()

        # 工具注册表
        self.tool_registry = get_unified_registry()

        # 执行统计
        self.stats = {
            "total_calls": 0,
            "total_tool_executions": 0,
            "total_time": 0.0,
        }

        logger.info(f"🔄 Agent Loop 已创建: {agent_name} ({agent_type})")

    async def run(
        self,
        user_message: str,
        context: Optional[dict[str, Any]] = None,
    ) -> str:
        """执行 Agent Loop

        Args:
            user_message: 用户消息
            context: 上下文信息

        Returns:
            str: 代理的最终响应
        """
        start_time = time.time()

        # 构建消息历史
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_message},
        ]

        # 转换工具格式
        tools = self._get_tools_for_llm()

        # 执行循环
        iteration = 0
        max_iterations = 10  # 防止无限循环

        while iteration < max_iterations:
            iteration += 1
            logger.info(f"🔄 [迭代 {iteration}] 调用 LLM...")

            try:
                # 调用 LLM
                response = await self._call_llm(messages, tools)

                # 检查停止条件
                if response.stop_reason != "tool_use":
                    # 执行完成，返回最终响应
                    self.stats["total_calls"] += 1
                    self.stats["total_time"] += time.time() - start_time
                    logger.info(f"✅ Agent Loop 完成: {iteration} 次迭代, {time.time() - start_time:.2f}秒")
                    return response.content

                # 处理工具调用
                logger.info(f"🔧 [迭代 {iteration}] 处理 {len(response.tool_uses)} 个工具调用")

                for tool_use in response.tool_uses:
                    # 执行工具
                    tool_result = await self._execute_tool(tool_use)

                    # 添加工具结果到响应
                    response.tool_results.append({
                        "tool_use_id": tool_use.get("id", ""),
                        "role": "tool",
                        "content": str(tool_result.result),
                    })

                    # 更新统计
                    self.stats["total_tool_executions"] += 1

                    # 检查是否出错
                    if not tool_result.success:
                        logger.error(f"❌ 工具执行失败: {tool_result.error}")
                        # 将错误信息添加到消息中
                        messages.append({
                            "role": "tool",
                            "content": f"工具执行失败: {tool_result.error}",
                        })
                        break

                # 添加工具结果到消息历史
                messages.extend(response.tool_results)

            except Exception as e:
                logger.error(f"❌ Agent Loop 错误: {e}")
                return f"抱歉，处理过程中发生错误: {str(e)}"

        # 达到最大迭代次数
        logger.warning(f"⚠️ 达到最大迭代次数: {max_iterations}")
        return "抱歉，处理超时或遇到循环。"

    async def _call_llm(
        self,
        messages: list[dict],
        tools: list[dict],
    ) -> LLMResponse:
        """调用 LLM

        Args:
            messages: 消息历史
            tools: 工具列表

        Returns:
            LLMResponse: LLM 响应
        """
        # 这里简化处理，实际应该调用 self.llm_manager
        # 返回模拟响应
        return LLMResponse(
            content="这是一个模拟响应",
            stop_reason="tool_use",
            tool_uses=[{"id": "test", "name": "test_tool"}],
        )

    def _get_tools_for_llm(self) -> list[dict]:
        """获取 LLM 格式的工具列表

        Returns:
            list[dict]: LLM 工具列表
        """
        tools = []
        # 使用search_tools获取所有工具(不传过滤参数)
        for tool in self.tool_registry.search_tools():
            # 构建简单的工具描述（后续可扩展为完整的Claude/OpenAI格式）
            tool_info = {
                "name": tool.tool_id,
                "description": tool.description,
                "category": tool.category.value,
                "required_params": tool.required_params,
                "optional_params": tool.optional_params,
            }
            tools.append(tool_info)
        return tools

    async def _execute_tool(self, tool_use: dict) -> ToolResult:
        """执行工具

        Args:
            tool_use: 工具调用信息

        Returns:
            ToolResult: 工具执行结果
        """
        start_time = time.time()

        tool_id = tool_use.get("name", "")
        parameters = tool_use.get("input", {})

        logger.info(f"🔧 执行工具: {tool_id}")

        try:
            # 调用工具执行管理器
            call_result = await call_tool(tool_id, parameters)

            execution_time = time.time() - start_time

            if call_result.status == "success":
                return ToolResult(
                    tool_id=tool_id,
                    success=True,
                    result=call_result.result,
                    execution_time=execution_time,
                )
            else:
                return ToolResult(
                    tool_id=tool_id,
                    success=False,
                    error=call_result.error_message or "工具执行失败",
                    execution_time=execution_time,
                )

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ 工具执行失败: {tool_id} - {e}")

            return ToolResult(
                tool_id=tool_id,
                success=False,
                error=str(e),
                execution_time=execution_time,
            )

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息

        Returns:
            dict: 统计信息
        """
        return self.stats.copy()


# ========================================
# 工厂函数
# ========================================

def create_agent_loop(
    agent_name: str,
    agent_type: str,
    system_prompt: str,
) -> BaseAgentLoop:
    """创建 Agent Loop

    Args:
        agent_name: 代理名称
        agent_type: 代理类型
        system_prompt: 系统提示词

    Returns:
        BaseAgentLoop: Agent Loop 实例
    """
    return BaseAgentLoop(
        agent_name=agent_name,
        agent_type=agent_type,
        system_prompt=system_prompt,
    )


__all__ = [
    "LLMResponse",
    "ToolResult",
    "BaseAgentLoop",
    "create_agent_loop",
]
