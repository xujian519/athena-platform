"""
Span处理器模块

提供自定义Span处理器，用于在Span导出前进行额外处理。
"""

from typing import Optional
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanProcessor
from opentelemetry import trace


class AgentAttributeEnricher(SpanProcessor):
    """
    Agent属性增强处理器

    自动为Span添加Agent相关的通用属性。
    """

    def __init__(
        self,
        agent_name: Optional[str] = None,
        service_version: Optional[str] = None
    ):
        self.agent_name = agent_name
        self.service_version = service_version

    def on_start(
        self,
        span: trace.Span,
        parent_context: Optional[trace.Context] = None
    ) -> None:
        """Span开始时调用"""
        # 可以在这里添加通用属性
        if self.agent_name:
            span.set_attribute("agent.name", self.agent_name)
        if self.service_version:
            span.set_attribute("service.version", self.service_version)

    def on_end(self, span: ReadableSpan) -> None:
        """Span结束时调用"""
        # 可以在这里添加后处理逻辑
        pass

    def shutdown(self) -> None:
        """关闭处理器"""
        pass

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        """强制刷新"""
        return True


class ErrorFilterProcessor(SpanProcessor):
    """
    错误过滤处理器

    可以过滤掉某些不需要记录的错误。
    """

    def __init__(self, filtered_error_types: Optional[list[str]] = None):
        """
        Args:
            filtered_error_types: 要过滤的错误类型列表
        """
        self.filtered_error_types = filtered_error_types or []

    def on_start(
        self,
        span: trace.Span,
        parent_context: Optional[trace.Context] = None
    ) -> None:
        pass

    def on_end(self, span: ReadableSpan) -> None:
        """过滤掉指定类型的错误"""
        if not span.status:
            return

        error_type = span.attributes.get("error.type")
        if error_type in self.filtered_error_types:
            # 清除错误状态
            # 注意：ReadableSpan是只读的，这里需要在on_start时处理
            pass

    def shutdown(self) -> None:
        pass

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True


class SpanDurationProcessor(SpanProcessor):
    """
    Span持续时间统计处理器

    记录Span持续时间统计信息。
    """

    def __init__(self):
        self.span_durations: dict[str, list[int]] = {}

    def on_start(
        self,
        span: trace.Span,
        parent_context: Optional[trace.Context] = None
    ) -> None:
        pass

    def on_end(self, span: ReadableSpan) -> None:
        """记录Span持续时间"""
        if span.name not in self.span_durations:
            self.span_durations[span.name] = []

        if span.start_time and span.end_time:
            duration_ns = span.end_time - span.start_time
            duration_ms = duration_ns / 1_000_000
            self.span_durations[span.name].append(duration_ms)

    def get_statistics(self, span_name: str) -> Optional[dict]:
        """
        获取指定Span的统计信息

        Returns:
            包含min, max, avg, count的字典
        """
        if span_name not in self.span_durations:
            return None

        durations = self.span_durations[span_name]
        if not durations:
            return None

        return {
            "count": len(durations),
            "min_ms": min(durations),
            "max_ms": max(durations),
            "avg_ms": sum(durations) / len(durations)
        }

    def shutdown(self) -> None:
        pass

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True
