#!/usr/bin/env python3
"""
LLM 适配器

集成 UnifiedLLMManager，提供 Agent Loop 所需的 LLM 调用接口。

作者: Athena平台团队
创建时间: 2026-04-20
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Union

from core.llm.unified_llm_manager import UnifiedLLMManager

from .stream_events import (
    AssistantTextDelta,
    AssistantTurnComplete,
    ErrorEvent,
    StreamEvent,
    ToolExecutionStarted,
)

logger = logging.getLogger(__name__)


@dataclass
class LLMRequest:
    """LLM 请求"""

    messages: list[dict[str, str]]
    tools: list[dict[str, Any]] | None = None
    max_tokens: int = 4096
    temperature: float = 0.7
    stream: bool = True


@dataclass
class LLMResponse:
    """LLM 响应"""

    content: str = ""
    stop_reason: str | None = None
    tool_uses: list[dict] = field(default_factory=list)
    usage: dict[str, Any] = field(default_factory=dict)
    model: str = ""


class LLMAdapter:
    """LLM 适配器

    集成 UnifiedLLMManager，提供流式和非流式调用接口。
    """

    def __init__(
        self,
        llm_manager: UnifiedLLMManager | None = None,
        default_model: str = "claude-sonnet-4-6",
    ):
        """初始化 LLM 适配器

        Args:
            llm_manager: LLM 管理器
            default_model: 默认模型
        """
        self.llm_manager = llm_manager or UnifiedLLMManager()
        self.default_model = default_model
        self._stats = {
            "total_calls": 0,
            "total_tokens": 0,
            "total_time": 0.0,
        }
        logger.info(f"🤖 LLM 适配器已初始化 (模型: {default_model})")

    async def call_llm(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        """调用 LLM（非流式）

        Args:
            request: LLM 请求

        Returns:
            LLMResponse: LLM 响应
        """
        import time

        start_time = time.time()

        try:
            # 调用 UnifiedLLMManager
            response = await self.llm_manager.call_llm(
                messages=request.messages,
                tools=request.tools,
                model=self.default_model,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                stream=False,
            )

            # 解析响应
            result = self._parse_response(response)

            # 更新统计
            elapsed = time.time() - start_time
            self._stats["total_calls"] += 1
            self._stats["total_time"] += elapsed
            if "usage" in result:
                self._stats["total_tokens"] += result.usage.get("total_tokens", 0)

            logger.info(f"✅ LLM 调用完成: {elapsed:.2f}s, {result.usage}")
            return result

        except Exception as e:
            logger.error(f"❌ LLM 调用失败: {e}")
            # 返回错误响应
            return LLMResponse(
                content=f"抱歉，调用 LLM 时发生错误: {str(e)}",
                stop_reason="error",
            )

    async def call_llm_stream(
        self,
        request: LLMRequest,
    ) -> AsyncIterator[StreamEvent]:
        """调用 LLM（流式）

        Args:
            request: LLM 请求

        Yields:
            StreamEvent: 流式事件
        """
        import time

        start_time = time.time()
        content_buffer = ""
        tool_uses = []

        try:
            # 调用 UnifiedLLMManager (流式)
            async for chunk in self.llm_manager.call_llm(
                messages=request.messages,
                tools=request.tools,
                model=self.default_model,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                stream=True,
            ):
                # 解析 chunk
                if isinstance(chunk, dict):
                    if "delta" in chunk:
                        # 文本增量
                        delta = chunk["delta"]
                        if isinstance(delta, str):
                            content_buffer += delta
                            yield AssistantTextDelta(text=delta)

                    elif "tool_use" in chunk:
                        # 工具调用
                        tool_use = chunk["tool_use"]
                        tool_uses.append(tool_use)
                        yield ToolExecutionStarted(
                            tool_id=tool_use.get("name", ""),
                            tool_name=tool_use.get("name", ""),
                            tool_input=tool_use.get("input", {}),
                            tool_use_id=tool_use.get("id", ""),
                        )

                    elif "error" in chunk:
                        # 错误
                        yield ErrorEvent(
                            message=chunk["error"],
                            recoverable=True,
                        )

            # 完成
            elapsed = time.time() - start_time
            self._stats["total_calls"] += 1
            self._stats["total_time"] += elapsed

            yield AssistantTurnComplete(
                message=content_buffer,
                tool_calls=tool_uses,
                usage={"total_time": elapsed},
            )

            logger.info(f"✅ LLM 流式调用完成: {elapsed:.2f}s")

        except Exception as e:
            logger.error(f"❌ LLM 流式调用失败: {e}")
            yield ErrorEvent(
                message=f"调用 LLM 时发生错误: {str(e)}",
                recoverable=True,
                error_type=type(e).__name__,
            )

    def _parse_response(self, response: Any) -> LLMResponse:
        """解析 LLM 响应

        Args:
            response: 原始响应

        Returns:
            LLMResponse: 解析后的响应
        """
        # 处理不同类型的响应
        if isinstance(response, dict):
            content = response.get("content", "")
            tool_uses = response.get("tool_calls", [])
            usage = response.get("usage", {})
            stop_reason = response.get("stop_reason", "end_turn")

            return LLMResponse(
                content=content,
                stop_reason=stop_reason,
                tool_uses=tool_uses if isinstance(tool_uses, list) else [],
                usage=usage,
            )

        elif isinstance(response, str):
            return LLMResponse(content=response)

        else:
            return LLMResponse(content=str(response))

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息

        Returns:
            dict: 统计信息
        """
        return self._stats.copy()


__all__ = [
    "LLMRequest",
    "LLMResponse",
    "LLMAdapter",
]
