"""
Agent自动埋点模块

提供Agent类的自动追踪装饰器。
"""

from functools import wraps
from typing import Callable, Optional, Any
from ..tracer import AthenaTracer
from ..attributes import AgentAttributes


def trace_agent(cls: type, tracer_name: str = "agent") -> type:
    """
    类装饰器：为Agent类添加自动追踪

    自动包装process方法并添加追踪Span。

    Args:
        cls: Agent类
        tracer_name: 追踪器名称前缀

    Returns:
        装饰后的类

    Example:
        >>> @trace_agent
        ... class MyAgent:
        ...     def process(self, request):
        ...         return "result"
    """
    # 检查是否有process方法
    if hasattr(cls, 'process'):
        original_process = cls.process

        @wraps(original_process)
        async def traced_process(self, *args, **kwargs):
            tracer = getattr(self, '_tracer', None)
            if tracer is None:
                tracer = AthenaTracer(f"{tracer_name}.{self.__class__.__name__}")

            agent_name = getattr(self, 'name', self.__class__.__name__)
            task_type = kwargs.get('task_type', 'process')

            with tracer.start_agent_span(
                agent_name=agent_name,
                task_type=task_type
            ):
                return await original_process(self, *args, **kwargs)

        cls.process = traced_process

    # 检查是否有initialize方法
    if hasattr(cls, 'initialize'):
        original_initialize = cls.initialize

        @wraps(original_initialize)
        async def traced_initialize(self, *args, **kwargs):
            tracer = getattr(self, '_tracer', None)
            if tracer is None:
                tracer = AthenaTracer(f"{tracer_name}.{self.__class__.__name__}")

            agent_name = getattr(self, 'name', self.__class__.__name__)

            with tracer.start_agent_span(
                agent_name=agent_name,
                task_type="initialize"
            ):
                return await original_initialize(self, *args, **kwargs)

        cls.initialize = traced_initialize

    return cls


def trace_agent_method(
    task_type: Optional[str] = None,
    agent_name: Optional[str] = None
):
    """
    方法装饰器：为Agent方法添加追踪

    Args:
        task_type: 任务类型
        agent_name: Agent名称

    Example:
        >>> @trace_agent_method(task_type="analysis", agent_name="xiaona")
        ... async def analyze_patent(self, patent_id: str):
        ...     return analysis
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            tracer = getattr(self, '_tracer', None)
            if tracer is None:
                tracer = AthenaTracer("agent.method")

            name = agent_name or getattr(self, 'name', self.__class__.__name__)
            task = task_type or func.__name__

            with tracer.start_agent_span(
                agent_name=name,
                task_type=task
            ):
                return await func(self, *args, **kwargs)

        @wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            tracer = getattr(self, '_tracer', None)
            if tracer is None:
                tracer = AthenaTracer("agent.method")

            name = agent_name or getattr(self, 'name', self.__class__.__name__)
            task = task_type or func.__name__

            with tracer.start_agent_span(
                agent_name=name,
                task_type=task
            ):
                return func(self, *args, **kwargs)

        # 检测是否为协程函数
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class AgentTracerMixin:
    """
    Agent追踪混入类

    为Agent类提供追踪功能。

    Example:
        >>> class MyAgent(AgentTracerMixin):
        ...     def __init__(self, name: str):
        ...         super().__init__()
        ...         self.setup_tracer(name)
    """

    _tracer: Optional[AthenaTracer] = None

    def setup_tracer(self, agent_name: str) -> None:
        """
        设置追踪器

        Args:
            agent_name: Agent名称
        """
        self._tracer = AthenaTracer(f"agent.{agent_name}")

    def get_tracer(self) -> Optional[AthenaTracer]:
        """获取追踪器"""
        return self._tracer

    def trace_method(
        self,
        task_type: str,
        **attributes
    ):
        """
        方法追踪上下文管理器

        Args:
            task_type: 任务类型
            **attributes: 额外属性

        Returns:
            上下文管理器
        """
        if self._tracer:
            return self._tracer.start_agent_span(
                agent_name=getattr(self, 'name', 'unknown'),
                task_type=task_type,
                **attributes
            )
        else:
            # 返回空上下文管理器
            from contextlib import nullcontext
            return nullcontext()
