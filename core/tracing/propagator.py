"""
W3C Trace Context传播模块

实现W3C Trace Context标准的跨服务追踪上下文传播。
"""

from typing import Dict, Optional, Any
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.context import Context


class TracePropagator:
    """
    W3C Trace Context传播器

    用于在微服务间传播追踪上下文。
    使用W3C标准：traceparent和tracestate HTTP头。

    Example:
        >>> propagator = TracePropagator()
        >>>
        >>> # 服务端：注入到HTTP headers
        >>> headers = {}
        >>> propagator.inject(headers)
        >>> # headers = {'traceparent': '00-...-...-01'}
        >>>
        >>> # 客户端：从HTTP headers提取
        >>> context = propagator.extract(headers)
    """

    def __init__(self):
        self._propagator = TraceContextTextMapPropagator()

    def inject(self, carrier: Dict[str, str]) -> None:
        """
        将当前追踪上下文注入到载体

        Args:
            carrier: 载体字典，通常用于HTTP headers
        """
        self._propagator.inject(carrier)

    def extract(self, carrier: Dict[str, str]) -> Optional[Context]:
        """
        从载体提取追踪上下文

        Args:
            carrier: 载体字典，通常来自HTTP headers

        Returns:
            OpenTelemetry Context对象
        """
        if not carrier:
            return None
        return self._propagator.extract(carrier)

    def inject_to_headers(self) -> Dict[str, str]:
        """
        生成包含追踪信息的HTTP headers

        Returns:
            包含traceparent的headers字典
        """
        headers: Dict[str, str] = {}
        self.inject(headers)
        return headers

    @staticmethod
    def get_trace_parent_from_headers(headers: Dict[str, str]) -> Optional[str]:
        """
        从headers获取traceparent值

        Args:
            headers: HTTP headers字典

        Returns:
            traceparent字符串或None
        """
        return headers.get("traceparent")

    @staticmethod
    def parse_trace_parent(trace_parent: str) -> Optional[Dict[str, str]]:
        """
        解析traceparent字符串

        traceparent格式: version-trace_id-span_id-trace_flags

        Args:
            trace_parent: traceparent字符串

        Returns:
            包含各部分的字典，或None（解析失败时）
        """
        try:
            parts = trace_parent.split("-")
            if len(parts) != 4:
                return None

            return {
                "version": parts[0],
                "trace_id": parts[1],
                "span_id": parts[2],
                "trace_flags": parts[3]
            }
        except (ValueError, AttributeError):
            return None


# 全局传播器实例
_default_propagator: Optional[TracePropagator] = None


def get_propagator() -> TracePropagator:
    """获取默认传播器（单例）"""
    global _default_propagator
    if _default_propagator is None:
        _default_propagator = TracePropagator()
    return _default_propagator
