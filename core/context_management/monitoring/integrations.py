#!/usr/bin/env python3
"""
监控集成工具 - 装饰器和辅助函数
Monitoring Integration Tools - Decorators and Helpers

提供便捷的监控集成方式：
- 装饰器：自动监控函数调用
- 上下文管理器：手动跟踪操作
- 辅助函数：直接记录指标

作者: Athena平台团队
创建时间: 2026-04-24
版本: v1.0.0
"""

import functools
import logging
from contextlib import asynccontextmanager
from typing import Any, Callable, Optional, TypeVar

from .metrics import get_metrics

logger = logging.getLogger(__name__)

T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])


def monitor_context_operation(
    operation: Optional[str] = None,
    context_type: str = "task",
):
    """
    监控上下文操作的装饰器

    自动记录操作计数、延迟和错误。

    Args:
        operation: 操作类型，默认使用函数名
        context_type: 上下文类型

    Example:
        ```python
        @monitor_context_operation("create", "task")
        async def create_context(task_id: str) -> TaskContext:
            ...
        ```
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            metrics = get_metrics()
            if not metrics.enabled:
                return await func(*args, **kwargs)

            op_name = operation or func.__name__

            with metrics.track_operation(op_name, context_type):
                return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            metrics = get_metrics()
            if not metrics.enabled:
                return func(*args, **kwargs)

            op_name = operation or func.__name__

            with metrics.track_operation(op_name, context_type):
                return func(*args, **kwargs)

        # 根据函数类型返回合适的包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore

    return decorator


@asynccontextmanager
async def track_operation_latency(
    operation: str,
    context_type: str = "task",
):
    """
    跟踪操作耗时的异步上下文管理器

    Args:
        operation: 操作类型
        context_type: 上下文类型

    Example:
        ```python
        async with track_operation_latency("create", "task"):
            context = await manager.create(...)
        ```
    """
    metrics = get_metrics()
    if not metrics.enabled:
        yield
        return

    with metrics.track_operation(operation, context_type):
        yield


def increment_operation_counter(
    operation: str,
    context_type: str = "task",
    status: str = "success",
) -> None:
    """
    增加操作计数

    Args:
        operation: 操作类型
        context_type: 上下文类型
        status: 操作状态
    """
    metrics = get_metrics()
    if metrics.enabled:
        metrics.record_operation(operation, context_type, status)


def record_error(
    error_type: str,
    operation: str,
) -> None:
    """
    记录错误

    Args:
        error_type: 错误类型
        operation: 发生错误的操作
    """
    metrics = get_metrics()
    if metrics.enabled:
        metrics.record_error(error_type, operation)


def record_cache_hit(cache_type: str = "memory") -> None:
    """
    记录缓存命中

    Args:
        cache_type: 缓存类型
    """
    metrics = get_metrics()
    if metrics.enabled:
        metrics.record_cache_operation("hit", cache_type)


def record_cache_miss(cache_type: str = "memory") -> None:
    """
    记录缓存未命中

    Args:
        cache_type: 缓存类型
    """
    metrics = get_metrics()
    if metrics.enabled:
        metrics.record_cache_operation("miss", cache_type)


def update_active_contexts(count: int, context_type: str = "task") -> None:
    """
    更新活跃上下文数量

    Args:
        count: 活跃数量
        context_type: 上下文类型
    """
    metrics = get_metrics()
    if metrics.enabled:
        metrics.update_active_contexts(count, context_type)


def update_pool_size(size: int, pool_type: str = "current") -> None:
    """
    更新对象池大小

    Args:
        size: 池大小
        pool_type: 池类型
    """
    metrics = get_metrics()
    if metrics.enabled:
        metrics.update_pool_size(size, pool_type)


def update_cache_hit_rate(rate: float, cache_type: str = "memory") -> None:
    """
    更新缓存命中率

    Args:
        rate: 命中率（0-1）
        cache_type: 缓存类型
    """
    metrics = get_metrics()
    if metrics.enabled:
        metrics.update_cache_hit_rate(rate, cache_type)


class MetricsContextManager:
    """
    上下文管理器的监控包装器

    自动包装上下文管理器的所有操作。

    Example:
        ```python
        # 包装现有的管理器
        manager = TaskContextManager()
        monitored_manager = MetricsContextManager(manager, "task")

        # 所有操作自动被监控
        await monitored_manager.create_context(...)
        ```
    """

    def __init__(
        self,
        manager: Any,
        context_type: str = "task",
    ):
        """
        初始化监控包装器

        Args:
            manager: 原始上下文管理器
            context_type: 上下文类型
        """
        self._manager = manager
        self._context_type = context_type
        self._metrics = get_metrics()

    async def create_context(self, *args: Any, **kwargs: Any) -> Any:
        """创建上下文（带监控）"""
        with self._metrics.track_operation("create", self._context_type):
            return await self._manager.create_context(*args, **kwargs)

    async def get_context(self, *args: Any, **kwargs: Any) -> Any:
        """获取上下文（带监控）"""
        with self._metrics.track_operation("read", self._context_type):
            return await self._manager.get(*args, **kwargs)

    async def update_context(self, *args: Any, **kwargs: Any) -> bool:
        """更新上下文（带监控）"""
        with self._metrics.track_operation("update", self._context_type):
            return await self._manager.update(*args, **kwargs)

    async def delete_context(self, *args: Any, **kwargs: Any) -> bool:
        """删除上下文（带监控）"""
        with self._metrics.track_operation("delete", self._context_type):
            return await self._manager.delete(*args, **kwargs)

    async def list_contexts(self, *args: Any, **kwargs: Any) -> list[Any]:
        """列出上下文（带监控）"""
        with self._metrics.track_operation("list", self._context_type):
            return await self._manager.list(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        """转发其他属性访问到原始管理器"""
        return getattr(self._manager, name)


def monitor_context_manager(
    manager: Any,
    context_type: str = "task",
) -> Any:
    """
    包装上下文管理器以添加监控

    Args:
        manager: 原始上下文管理器
        context_type: 上下文类型

    Returns:
        监控包装后的管理器
    """
    return MetricsContextManager(manager, context_type)


# 导入asyncio用于检查协程函数
import asyncio


__all__ = [
    # 装饰器
    "monitor_context_operation",
    # 上下文管理器
    "track_operation_latency",
    # 辅助函数
    "increment_operation_counter",
    "record_error",
    "record_cache_hit",
    "record_cache_miss",
    "update_active_contexts",
    "update_pool_size",
    "update_cache_hit_rate",
    # 包装器
    "MetricsContextManager",
    "monitor_context_manager",
]
