#!/usr/bin/env python3
"""
流式响应处理器

处理 Agent Loop 的流式事件输出。

作者: Athena平台团队
创建时间: 2026-04-20
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Awaitable, Callable, Union

from .stream_events import StreamEvent, stream_event_to_json

logger = logging.getLogger(__name__)


# 流式事件处理器类型（Python 3.9 兼容）
StreamEventHandler = Callable[[StreamEvent], Union[Awaitable[None], None]]


class StreamingHandler:
    """流式响应处理器

    管理 Agent Loop 的流式事件输出。
    """

    def __init__(self):
        """初始化流式处理器"""
        self._handlers: list[StreamEventHandler] = []
        self._event_queue: asyncio.Queue[StreamEvent] = asyncio.Queue()
        self._running = False
        self._task: asyncio.Task | None = None

    def on_event(self, handler: StreamEventHandler) -> None:
        """注册事件处理器

        Args:
            handler: 事件处理函数
        """
        if handler not in self._handlers:
            self._handlers.append(handler)
            logger.debug(f"✅ 注册流式事件处理器: {handler.__name__}")

    def off_event(self, handler: StreamEventHandler) -> None:
        """取消注册事件处理器

        Args:
            handler: 事件处理函数
        """
        if handler in self._handlers:
            self._handlers.remove(handler)
            logger.debug(f"❌ 取消注册流式事件处理器: {handler.__name__}")

    async def emit(self, event: StreamEvent) -> None:
        """发送流式事件

        Args:
            event: 流式事件
        """
        await self._event_queue.put(event)

    def emit_sync(self, event: StreamEvent) -> None:
        """同步发送流式事件（用于非异步上下文）

        Args:
            event: 流式事件
        """
        try:
            self._event_queue.put_nowait(event)
        except asyncio.QueueFull:
            logger.warning("⚠️ 流式事件队列已满，丢弃事件")

    async def start(self) -> None:
        """启动流式处理器"""
        if self._running:
            logger.warning("⚠️ 流式处理器已在运行")
            return

        self._running = True
        self._task = asyncio.create_task(self._process_events())
        logger.info("🚀 流式处理器已启动")

    async def stop(self) -> None:
        """停止流式处理器"""
        if not self._running:
            return

        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("🛑 流式处理器已停止")

    async def _process_events(self) -> None:
        """处理流式事件"""
        while self._running:
            try:
                # 等待事件，超时1秒以检查 _running 标志
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)

                # 调用所有处理器
                for handler in self._handlers:
                    try:
                        result = handler(event)
                        if asyncio.iscoroutine(result):
                            await result
                    except Exception as e:
                        logger.error(f"❌ 流式事件处理器错误 ({handler.__name__}): {e}")

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"❌ 流式事件处理错误: {e}")

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息

        Returns:
            dict: 统计信息
        """
        return {
            "running": self._running,
            "handlers": len(self._handlers),
            "queue_size": self._event_queue.qsize(),
        }


class SSEStreamingHandler(StreamingHandler):
    """SSE (Server-Sent Events) 流式处理器

    将流式事件转换为 SSE 格式输出。
    """

    def __init__(self, output_callback: Callable[[str], Awaitable[None]] or None]):
        """初始化 SSE 处理器

        Args:
            output_callback: 输出回调函数
        """
        super().__init__()
        self._output_callback = output_callback

    async def start(self) -> None:
        """启动 SSE 处理器"""
        # 注册默认的 SSE 输出处理器
        self.on_event(self._sse_output_handler)
        await super().start()
        logger.info("🚀 SSE 流式处理器已启动")

    async def _sse_output_handler(self, event: StreamEvent) -> None:
        """SSE 输出处理器

        Args:
            event: 流式事件
        """
        # 转换为 JSON
        event_json = stream_event_to_json(event)

        # SSE 格式: "data: {json}\n\n"
        sse_message = f"data: {event_json}\n\n"

        # 调用输出回调
        result = self._output_callback(sse_message)
        if asyncio.iscoroutine(result):
            await result


class LoggingStreamingHandler(StreamingHandler):
    """日志流式处理器（用于调试）"""

    def __init__(self):
        """初始化日志处理器"""
        super().__init__()

    async def start(self) -> None:
        """启动日志处理器"""
        # 注册日志处理器
        self.on_event(self._log_handler)
        await super().start()
        logger.info("🚀 日志流式处理器已启动")

    async def _log_handler(self, event: StreamEvent) -> None:
        """日志处理器

        Args:
            event: 流式事件
        """
        event_type = event.__class__.__name__
        logger.debug(f"📡 流式事件: {event_type} - {event}")


__all__ = [
    "StreamEventHandler",
    "StreamingHandler",
    "SSEStreamingHandler",
    "LoggingStreamingHandler",
]
