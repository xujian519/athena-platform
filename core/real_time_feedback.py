#!/usr/bin/env python3
from __future__ import annotations
"""
即时反馈系统
Real-time Feedback System - 实时展示智能体思考和执行过程

作者: Athena平台团队
创建时间: 2026-01-20
版本: v1.0.0 "Phase 1"
"""

import asyncio
import inspect
import json
import logging
from collections import deque
from collections.abc import AsyncIterator, Callable
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """反馈类型"""

    THINKING = "thinking"  # 思考中
    PLANNING = "planning"  # 计划中
    EXECUTING = "executing"  # 执行中
    WAITING = "waiting"  # 等待中
    ERROR = "error"  # 错误
    SUCCESS = "success"  # 成功
    INFO = "info"  # 信息


class FeedbackLevel(Enum):
    """反馈级别"""

    MINIMAL = "minimal"  # 最小:仅关键步骤
    NORMAL = "normal"  # 正常:标准输出
    VERBOSE = "verbose"  # 详细:包含思考细节
    DEBUG = "debug"  # 调试:所有内部状态


@dataclass
class FeedbackMessage:
    """反馈消息"""

    type: FeedbackType
    level: FeedbackLevel
    timestamp: str
    content: str
    metadata: Optional[dict[str, Any]] = None
    step_id: Optional[str] = None
    progress: Optional[float] = None  # 0.0 - 1.0

    def to_dict(self) -> dict:
        """转换为字典"""
        data = asdict(self)
        data["type"] = self.type.value
        data["level"] = self.level.value
        return data

    def to_json(self) -> str:
        """转换为JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False)


class RealTimeFeedback:
    """即时反馈管理器"""

    def __init__(self, task_id: str, level: FeedbackLevel = FeedbackLevel.NORMAL):
        """
        初始化反馈管理器

        Args:
            task_id: 任务ID
            level: 反馈级别
        """
        self.task_id = task_id
        self.level = level
        self.messages: deque[FeedbackMessage] = deque(maxlen=1000)
        self.subscribers: list[Callable] = []
        self.start_time = datetime.now()
        self._current_step = 0
        self._total_steps = 0

        logger.info(f"📡 即时反馈系统初始化: {task_id}")

    async def thinking(self, content: str, metadata: dict | None = None) -> None:
        """
        发送思考反馈

        Args:
            content: 思考内容
            metadata: 额外元数据
        """
        if self.level in [FeedbackLevel.VERBOSE, FeedbackLevel.DEBUG]:
            await self._send(FeedbackType.THINKING, content, metadata)

    async def planning(
        self, content: str, step: int = 0, total: int = 0, metadata: dict | None = None
    ) -> None:
        """
        发送计划反馈

        Args:
            content: 计划内容
            step: 当前步骤
            total: 总步骤数
            metadata: 额外元数据
        """
        self._current_step = step
        self._total_steps = total
        progress = step / total if total > 0 else 0.0

        if self.level != FeedbackLevel.MINIMAL:
            await self._send(
                FeedbackType.PLANNING,
                content,
                {**(metadata or {}), "step": step, "total": total},
                progress=progress,
            )

    async def executing(
        self, content: str, step_id: Optional[str] = None, metadata: dict | None = None
    ) -> None:
        """
        发送执行反馈

        Args:
            content: 执行内容
            step_id: 步骤ID
            metadata: 额外元数据
        """
        if self.level != FeedbackLevel.MINIMAL:
            await self._send(FeedbackType.EXECUTING, content, metadata, step_id=step_id)

    async def success(self, content: str, metadata: dict | None = None) -> None:
        """
        发送成功反馈

        Args:
            content: 成功内容
            metadata: 额外元数据
        """
        await self._send(FeedbackType.SUCCESS, content, metadata, progress=1.0)

    async def error(self, content: str, metadata: dict | None = None) -> None:
        """
        发送错误反馈

        Args:
            content: 错误内容
            metadata: 额外元数据
        """
        await self._send(FeedbackType.ERROR, content, metadata)

    async def info(self, content: str, metadata: dict | None = None) -> None:
        """
        发送信息反馈

        Args:
            content: 信息内容
            metadata: 额外元数据
        """
        if self.level in [FeedbackLevel.NORMAL, FeedbackLevel.VERBOSE, FeedbackLevel.DEBUG]:
            await self._send(FeedbackType.INFO, content, metadata)

    async def _send(
        self,
        type: FeedbackType,
        content: str,
        metadata: dict | None = None,
        step_id: Optional[str] = None,
        progress: Optional[float] = None,
    ) -> None:
        """发送反馈消息"""
        message = FeedbackMessage(
            type=type,
            level=self.level,
            timestamp=datetime.now().isoformat(),
            content=content,
            metadata=metadata,
            step_id=step_id,
            progress=progress,
        )

        # 存储消息
        self.messages.append(message)

        # 通知订阅者
        await self._notify_subscribers(message)

    async def _notify_subscribers(self, message: FeedbackMessage) -> None:
        """通知所有订阅者"""
        for callback in self.subscribers:
            try:
                if inspect.iscoroutinefunction(callback):
                    await callback(message)
                else:
                    callback(message)
            except Exception as e:
                logger.error(f"❌ 通知订阅者失败: {e}")

    def subscribe(self, callback: Callable) -> None:
        """
        订阅反馈消息

        Args:
            callback: 回调函数
        """
        self.subscribers.append(callback)
        logger.info(
            f"📥 新订阅者加入: {callback.__name__ if hasattr(callback, '__name__') else 'unknown'}"
        )

    def unsubscribe(self, callback: Callable) -> None:
        """
        取消订阅

        Args:
            callback: 回调函数
        """
        if callback in self.subscribers:
            self.subscribers.remove(callback)
            logger.info(
                f"📤 订阅者退出: {callback.__name__ if hasattr(callback, '__name__') else 'unknown'}"
            )

    def get_history(self, limit: int = 100) -> list[FeedbackMessage]:
        """
        获取历史消息

        Args:
            limit: 返回数量限制

        Returns:
            list[FeedbackMessage]: 消息列表
        """
        messages = list(self.messages)
        if limit > 0:
            return messages[-limit:]
        return messages

    def get_progress(self) -> dict[str, Any]:
        """
        获取当前进度

        Returns:
            Dict: 进度信息
        """
        elapsed = (datetime.now() - self.start_time).total_seconds()

        return {
            "task_id": self.task_id,
            "current_step": self._current_step,
            "total_steps": self._total_steps,
            "progress": self._current_step / self._total_steps if self._total_steps > 0 else 0.0,
            "elapsed_seconds": elapsed,
            "message_count": len(self.messages),
        }

    def clear(self) -> None:
        """清空消息历史"""
        self.messages.clear()
        logger.info(f"🗑️ 已清空反馈历史: {self.task_id}")


class FeedbackStream:
    """反馈流 - 用于生成器模式的实时反馈"""

    def __init__(self, feedback: RealTimeFeedback):
        """
        初始化反馈流

        Args:
            feedback: 反馈管理器实例
        """
        self.feedback = feedback
        self._queue: asyncio.Queue[FeedbackMessage] | None = asyncio.Queue()
        self._done = False

        # 订阅反馈消息
        self.feedback.subscribe(self._add_to_queue)

    def _add_to_queue(self, message: FeedbackMessage) -> None:
        """添加消息到队列"""
        try:
            self._queue.put_nowait(message)
        except asyncio.QueueFull:
            logger.warning("⚠️ 反馈队列已满")

    async def stream(self) -> AsyncIterator:
        """
        流式输出反馈消息

        Yields:
            FeedbackMessage: 反馈消息
        """
        try:
            while not self._done or not self._queue.empty():
                message = await self._queue.get()
                if message is None:  # 结束信号
                    break
                yield message
        finally:
            self.feedback.unsubscribe(self._add_to_queue)

    async def close(self) -> None:
        """关闭流"""
        self._done = True
        await self._queue.put(None)


# 便捷函数
async def create_feedback_stream(
    task_id: str, level: FeedbackLevel = FeedbackLevel.NORMAL
) -> AsyncIterator:
    """
    创建反馈流

    Args:
        task_id: 任务ID
        level: 反馈级别

    Yields:
        FeedbackMessage: 反馈消息

    Example:
        >>> async for message in create_feedback_stream("task_123"):
        ...     print(f"[{message.type}] {message.content}")
    """
    feedback = RealTimeFeedback(task_id, level)
    stream = FeedbackStream(feedback)

    try:
        async for message in stream.stream():
            yield message
    finally:
        await stream.close()


# 装饰器:自动为函数添加反馈
def with_feedback(task_id: str, level: FeedbackLevel = FeedbackLevel.NORMAL) -> Any:
    """
    反馈装饰器 - 自动为函数添加即时反馈

    Args:
        task_id: 任务ID
        level: 反馈级别

    Example:
        >>> @with_feedback("task_123")
        ... async def my_task():
        ...     await asyncio.sleep(1)
        ...     return "done"
    """

    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            feedback = RealTimeFeedback(task_id, level)
            func_name = func.__name__

            try:
                await feedback.thinking(f"准备执行: {func_name}")

                # 执行原函数
                if inspect.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                await feedback.success(f"完成: {func_name}")
                return result
            except Exception as e:
                await feedback.error(f"执行失败: {func_name} - {e!s}")
                raise

        return wrapper

    return decorator


__all__ = [
    "FeedbackLevel",
    "FeedbackMessage",
    "FeedbackStream",
    "FeedbackType",
    "RealTimeFeedback",
    "create_feedback_stream",
    "with_feedback",
]
