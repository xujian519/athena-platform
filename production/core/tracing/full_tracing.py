"""
全链路追踪系统

实现请求的完整处理链路追踪功能:
1. 请求ID生成和传递
2. 跨模块调用追踪
3. 性能耗时统计
4. 错误传播追踪
5. 分布式追踪支持
"""

from __future__ import annotations
import contextvars
import logging
import threading
import time
import uuid
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)

# 请求上下文变量
_request_context = contextvars.ContextVar("request_context", default=None)


class SpanStatus(Enum):
    """Span状态"""

    STARTED = "started"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class Span:
    """追踪Span(一个操作单元)"""

    span_id: str  # Span ID
    parent_id: str  # 父Span ID
    trace_id: str  # 追踪ID
    operation_name: str  # 操作名称
    start_time: float  # 开始时间
    end_time: float | None = None  # 结束时间
    duration_ms: float | None = None  # 耗时(毫秒)
    status: SpanStatus = SpanStatus.STARTED  # 状态
    tags: dict[str, Any] = field(default_factory=dict)  # 标签
    logs: list[dict[str, Any]] = field(default_factory=list)  # 日志
    metadata: dict[str, Any] = field(default_factory=dict)  # 元数据

    def finish(self, status: SpanStatus = SpanStatus.COMPLETED) -> Any:
        """完成Span"""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.status = status

    def add_tag(self, key: str, value: Any) -> None:
        """添加标签"""
        self.tags[key] = value

    def add_log(self, message: str, level: str = "info", **kwargs) -> None:
        """添加日志"""
        self.logs.append({"timestamp": time.time(), "message": message, "level": level, **kwargs})

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "span_id": self.span_id,
            "parent_id": self.parent_id,
            "trace_id": self.trace_id,
            "operation_name": self.operation_name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "status": self.status.value,
            "tags": self.tags,
            "logs": self.logs,
            "metadata": self.metadata,
        }


@dataclass
class TraceContext:
    """追踪上下文"""

    trace_id: str  # 追踪ID
    request_id: str  # 请求ID
    user_id: str | None = None  # 用户ID
    session_id: str | None = None  # 会话ID
    spans: list[Span] = field(default_factory=list)  # Span列表
    metadata: dict[str, Any] = field(default_factory=dict)  # 元数据
    start_time: float = field(default_factory=time.time)  # 开始时间

    def create_span(
        self,
        operation_name: str,
        parent_id: str | None = None,
        tags: dict[str, Any] | None = None,
    ) -> Span:
        """创建新Span"""
        span = Span(
            span_id=str(uuid.uuid4()),
            parent_id=parent_id,
            trace_id=self.trace_id,
            operation_name=operation_name,
            start_time=time.time(),
            tags=tags or {},
        )

        self.spans.append(span)
        return span

    def get_summary(self) -> dict[str, Any]:
        """获取追踪摘要"""
        total_duration = (time.time() - self.start_time) * 1000

        # 统计各操作耗时
        operations = defaultdict(list)
        for span in self.spans:
            if span.duration_ms is not None:
                operations[span.operation_name].append(span.duration_ms)

        operation_stats = {}
        for op, durations in operations.items():
            operation_stats[op] = {
                "count": len(durations),
                "total_ms": sum(durations),
                "avg_ms": sum(durations) / len(durations),
                "min_ms": min(durations),
                "max_ms": max(durations),
            }

        return {
            "trace_id": self.trace_id,
            "request_id": self.request_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "total_duration_ms": total_duration,
            "span_count": len(self.spans),
            "operation_stats": operation_stats,
            "metadata": self.metadata,
        }


class TracingManager:
    """
    追踪管理器

    管理所有追踪上下文和Span
    """

    def __init__(self):
        """初始化追踪管理器"""
        # 活跃的追踪上下文 {trace_id: TraceContext}
        self.active_traces: dict[str, TraceContext] = {}

        # 已完成的追踪
        self.completed_traces: list[TraceContext] = []

        # 最大保存的追踪数量
        self.max_completed_traces = 1000

        # 线程本地存储
        self._local = threading.local()

        logger.info("✅ 全链路追踪管理器初始化完成")

    def start_trace(
        self,
        request_id: str | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TraceContext:
        """
        开始新的追踪

        Args:
            request_id: 请求ID
            user_id: 用户ID
            session_id: 会话ID
            metadata: 元数据

        Returns:
            追踪上下文
        """
        trace_id = str(uuid.uuid4())
        if request_id is None:
            request_id = f"req_{trace_id[:8]}"

        context = TraceContext(
            trace_id=trace_id,
            request_id=request_id,
            user_id=user_id,
            session_id=session_id,
            metadata=metadata or {},
        )

        self.active_traces[trace_id] = context
        _request_context.set(context)

        logger.info(f"🔍 开始追踪: trace_id={trace_id}, request_id={request_id}")

        return context

    def end_trace(
        self, trace_id: str | None = None, status: str = "completed"
    ) -> dict[str, Any] | None:
        """
        结束追踪

        Args:
            trace_id: 追踪ID
            status: 状态

        Returns:
            追踪摘要
        """
        context = _request_context.get()

        if context:
            trace_id = trace_id or context.trace_id

            # 从活跃追踪中移除
            if trace_id in self.active_traces:
                del self.active_traces[trace_id]

            # 添加到已完成追踪
            self.completed_traces.append(context)

            # 清理旧追踪
            self._cleanup_old_traces()

            summary = context.get_summary()
            summary["status"] = status

            logger.info(
                f"✅ 结束追踪: trace_id={trace_id}, duration={summary['total_duration_ms']:.2f}ms"
            )

            # 清除上下文
            _request_context.set(None)

            return summary

        return None

    def get_current_context(self) -> TraceContext | None:
        """获取当前追踪上下文"""
        return _request_context.get()

    def create_span(
        self, operation_name: str, tags: dict[str, Any] | None = None
    ) -> Span | None:
        """
        创建新Span

        Args:
            operation_name: 操作名称
            tags: 标签

        Returns:
            Span或None
        """
        context = self.get_current_context()
        if not context:
            logger.warning("没有活跃的追踪上下文")
            return None

        # 获取父Span ID(最后一个未完成的Span)
        parent_id = None
        for span in reversed(context.spans):
            if span.status == SpanStatus.RUNNING:
                parent_id = span.span_id
                break

        span = context.create_span(operation_name=operation_name, parent_id=parent_id, tags=tags)

        span.status = SpanStatus.RUNNING
        return span

    def finish_span(self, span: Span, status: SpanStatus = SpanStatus.COMPLETED) -> Any:
        """完成Span"""
        span.finish(status)

    def get_trace(self, trace_id: str) -> dict[str, Any] | None:
        """获取追踪详情"""
        # 检查活跃追踪
        if trace_id in self.active_traces:
            context = self.active_traces[trace_id]
            return context.get_summary()

        # 检查已完成追踪
        for context in self.completed_traces:
            if context.trace_id == trace_id:
                return context.get_summary()

        return None

    def get_active_traces(self) -> list[dict[str, Any]]:
        """获取所有活跃追踪"""
        return [
            {
                "trace_id": ctx.trace_id,
                "request_id": ctx.request_id,
                "user_id": ctx.user_id,
                "duration_ms": (time.time() - ctx.start_time) * 1000,
                "span_count": len(ctx.spans),
            }
            for ctx in self.active_traces.values()
        ]

    def _cleanup_old_traces(self) -> Any:
        """清理旧追踪"""
        while len(self.completed_traces) > self.max_completed_traces:
            self.completed_traces.pop(0)


# 全局单例
_tracing_manager: TracingManager | None = None


def get_tracing_manager() -> TracingManager:
    """获取追踪管理器单例"""
    global _tracing_manager
    if _tracing_manager is None:
        _tracing_manager = TracingManager()
    return _tracing_manager


def traced(operation_name: str | None = None, tags: dict[str, Any] | None = None):
    """
    追踪装饰器

    Usage:
        @traced(operation_name="database_query")
        def query_user(user_id):
            return db.query(user_id)
    """

    def decorator(func) -> None:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            tracing = get_tracing_manager()
            span = tracing.create_span(operation_name or func.__name__, tags=tags)

            if not span:
                return func(*args, **kwargs)

            try:
                result = func(*args, **kwargs)
                tracing.finish_span(span, SpanStatus.COMPLETED)
                return result
            except Exception as e:
                tracing.finish_span(span, SpanStatus.ERROR)
                span.add_log(f"Error: {e!s}", level="error", exception_type=type(e).__name__)
                raise

        return wrapper

    return decorator


class TracingContextManager:
    """追踪上下文管理器(支持with语句)"""

    def __init__(self, operation_name: str, tags: dict[str, Any] | None = None):
        self.operation_name = operation_name
        self.tags = tags
        self.span = None

    def __enter__(self):
        tracing = get_tracing_manager()
        self.span = tracing.create_span(self.operation_name, self.tags)
        return self.span

    def __exit__(self, exc_type, exc_val, exc_tb):
        tracing = get_tracing_manager()
        if exc_type is not None:
            tracing.finish_span(self.span, SpanStatus.ERROR)
        else:
            tracing.finish_span(self.span, SpanStatus.COMPLETED)


# 便捷函数
def trace_operation(
    operation_name: str, func: Callable, tags: dict[str, Any] = None
) -> Any:
    """
    追踪操作执行

    Args:
        operation_name: 操作名称
        func: 要执行的函数
        tags: 标签

    Returns:
        函数执行结果
    """
    tracing = get_tracing_manager()
    span = tracing.create_span(operation_name, tags)

    if not span:
        return func()

    try:
        result = func()
        tracing.finish_span(span, SpanStatus.COMPLETED)
        return result
    except Exception as e:
        tracing.finish_span(span, SpanStatus.ERROR)
        span.add_log(f"Error: {e!s}", level="error")
        raise
