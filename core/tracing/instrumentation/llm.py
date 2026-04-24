"""
LLM自动埋点模块

提供LLM调用的自动追踪装饰器和上下文管理器。
支持响应追踪、成本记录、token统计等功能。
"""

from functools import wraps
from typing import Any, Callable, Optional, Dict
from contextlib import contextmanager
from opentelemetry import trace, Status, StatusCode

from ..tracer import AthenaTracer
from ..attributes import LLMAttributes


class LLMTracer:
    """
    LLM调用追踪器（增强版）

    提供完整的LLM调用追踪，包括：
    - 请求/响应追踪
    - Token统计
    - 成本记录
    - 异常捕获

    Example:
        >>> tracer = LLMTracer()
        >>> with tracer.trace_llm_call("claude", "claude-3-opus", prompt):
        ...     response = await call_claude()
        ...     tracer.add_response(
        ...         response_length=len(response.content),
        ...         prompt_tokens=response.usage.prompt_tokens,
        ...         completion_tokens=response.usage.completion_tokens,
        ...         total_tokens=response.usage.total_tokens,
        ...         cost=calculate_cost(...)
        ...     )
    """

    def __init__(self, service_name: str = "llm-service"):
        """
        初始化LLM追踪器

        Args:
            service_name: 服务名称
        """
        self.service_name = service_name
        self._tracer = trace.get_tracer(service_name)
        self._current_span: Optional[trace.Span] = None

    @contextmanager
    def trace_llm_call(
        self,
        provider: str,
        model: str,
        prompt: str,
        request_type: str = "chat",
        **kwargs
    ):
        """
        LLM调用追踪上下文管理器

        Args:
            provider: LLM提供商（claude, gpt, deepseek等）
            model: 模型名称
            prompt: 提示词
            request_type: 请求类型
            **kwargs: 额外属性

        Yields:
            LLMSpanContext对象，用于添加响应信息

        Example:
            >>> with tracer.trace_llm_call("claude", "claude-3-opus", prompt) as ctx:
            ...     response = await call_llm()
            ...     ctx.add_response(
            ...         response_length=len(response.content),
            ...         prompt_tokens=response.usage.prompt_tokens,
            ...         completion_tokens=response.usage.completion_tokens
            ...     )
        """
        attributes = {
            "llm.provider": provider,
            "llm.model": model,
            "llm.request.type": request_type,
            "llm.prompt.length": len(prompt),
            **kwargs
        }

        with self._tracer.start_as_current_span(
            name=f"llm.{provider}",
            kind=trace.SpanKind.CLIENT,
            attributes=attributes
        ) as span:
            self._current_span = span
            ctx = LLMSpanContext(span)
            try:
                yield ctx
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                ctx.record_error(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise
            finally:
                self._current_span = None

    def get_current_span(self) -> Optional[trace.Span]:
        """获取当前活跃的LLM Span"""
        return self._current_span


class LLMSpanContext:
    """
    LLM Span上下文管理器

    提供便捷的方法来添加LLM响应相关属性。
    """

    def __init__(self, span: trace.Span):
        """
        初始化Span上下文

        Args:
            span: OpenTelemetry Span对象
        """
        self.span = span

    def add_response(
        self,
        response_length: int,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        finish_reason: Optional[str] = None,
        cost: float = 0.0,
        latency_ms: float = 0.0,
        **kwargs
    ):
        """
        添加LLM响应属性到Span

        Args:
            response_length: 响应内容长度
            prompt_tokens: 提示词token数
            completion_tokens: 完成token数
            total_tokens: 总token数
            finish_reason: 完成原因
            cost: 成本（美元）
            latency_ms: 延迟（毫秒）
            **kwargs: 其他自定义属性
        """
        attributes = {
            "llm.response.length": response_length,
            "llm.tokens.prompt": prompt_tokens,
            "llm.tokens.completion": completion_tokens,
            "llm.tokens.total": total_tokens,
            "llm.cost": cost,
            "llm.latency.ms": latency_ms,
            **kwargs
        }

        if finish_reason:
            attributes["llm.finish_reason"] = finish_reason

        for key, value in attributes.items():
            if value is not None:
                self.span.set_attribute(key, value)

    def record_error(self, error: Exception):
        """
        记录错误到Span

        Args:
            error: 异常对象
        """
        self.span.record_exception(error)
        self.span.set_attribute("llm.error.type", type(error).__name__)
        self.span.set_attribute("llm.error.message", str(error))

    def add_model_info(
        self,
        provider: str,
        model: str,
        version: Optional[str] = None
    ):
        """
        添加模型信息

        Args:
            provider: 提供商
            model: 模型名称
            version: 模型版本
        """
        self.span.set_attribute("llm.provider", provider)
        self.span.set_attribute("llm.model", model)
        if version:
            self.span.set_attribute("llm.model.version", version)

    def add_timing(self, latency_ms: float, ttft_ms: Optional[float] = None):
        """
        添加时间信息

        Args:
            latency_ms: 总延迟
            ttft_ms: 首字延迟（Time To First Token）
        """
        self.span.set_attribute("llm.latency.ms", latency_ms)
        if ttft_ms is not None:
            self.span.set_attribute("llm.ttft.ms", ttft_ms)


@contextmanager
def trace_llm_call(
    tracer: AthenaTracer,
    provider: str,
    model: str,
    request_type: str = "chat",
    **kwargs
):
    """
    LLM调用追踪上下文管理器

    Args:
        tracer: 追踪器实例
        provider: LLM提供商
        model: 模型名称
        request_type: 请求类型
        **kwargs: 额外属性

    Yields:
        包含Span和回调函数的元组

    Example:
        >>> with trace_llm_call(tracer, "claude", "claude-3-opus") as (span, add_response):
        ...     response = await call_claude()
        ...     add_response(
        ...         prompt_tokens=response.usage.prompt_tokens,
        ...         completion_tokens=response.usage.completion_tokens,
        ...         total_tokens=response.usage.total_tokens
        ...     )
    """
    with tracer.start_llm_span(
        provider=provider,
        model=model,
        request_type=request_type,
        **kwargs
    ) as span:
        # 定义响应添加函数
        def add_response(
            prompt_tokens: int,
            completion_tokens: int,
            total_tokens: int,
            finish_reason: Optional[str] = None
        ):
            """添加LLM响应属性到Span"""
            attributes = LLMAttributes.add_response(
                {},
                prompt_tokens=prompt_tokens,
  completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                finish_reason=finish_reason
            )
            for key, value in attributes.items():
                span.set_attribute(key, value)

        yield span, add_response


def trace_llm_method(
    provider: str = None,
    model: str = None
):
    """
    LLM方法装饰器

    自动为LLM调用方法添加追踪。

    Args:
        provider: LLM提供商（可从方法参数获取）
        model: 模型名称（可从方法参数获取）

    Example:
        >>> @trace_llm_method(provider="claude", model="claude-3-opus")
        ... async def call_llm(self, prompt: str):
        ...     return await self.client.messages.create(...)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            # 尝试获取追踪器
            tracer = getattr(self, '_tracer', None) or getattr(self, 'tracer', None)
            if tracer is None:
                # 如果没有追踪器，直接调用原方法
                return await func(self, *args, **kwargs)

            # 尝试从kwargs获取provider和model
            actual_provider = provider or kwargs.get('provider', 'unknown')
            actual_model = model or kwargs.get('model', 'unknown')

            with trace_llm_call(tracer, actual_provider, actual_model) as (span, add_response):
                try:
                    result = await func(self, *args, **kwargs)

                    # 尝试从响应中提取token信息
                    if hasattr(result, 'usage'):
                        usage = result.usage
                        add_response(
                            prompt_tokens=getattr(usage, 'prompt_tokens', 0),
                            completion_tokens=getattr(usage, 'completion_tokens', 0),
                            total_tokens=getattr(usage, 'total_tokens', 0),
                            finish_reason=getattr(usage, 'finish_reason', None)
                        )

                    return result

                except Exception as e:
                    tracer.record_exception(e, span)
                    raise

        @wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            tracer = getattr(self, '_tracer', None) or getattr(self, 'tracer', None)
            if tracer is None:
                return func(self, *args, **kwargs)

            actual_provider = provider or kwargs.get('provider', 'unknown')
            actual_model = model or kwargs.get('model', 'unknown')

            with trace_llm_call(tracer, actual_provider, actual_model) as (span, add_response):
                try:
                    result = func(self, *args, **kwargs)

                    if hasattr(result, 'usage'):
                        usage = result.usage
                        add_response(
                            prompt_tokens=getattr(usage, 'prompt_tokens', 0),
                            completion_tokens=getattr(usage, 'completion_tokens', 0),
                            total_tokens=getattr(usage, 'total_tokens', 0),
                            finish_reason=getattr(usage, 'finish_reason', None)
                        )

                    return result

                except Exception as e:
                    tracer.record_exception(e, span)
                    raise

        # 检测是否为协程函数
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class LLMTracerMixin:
    """
    LLM追踪混入类

    为LLM客户端类提供追踪功能。

    Example:
        >>> class MyLLMClient(LLMTracerMixin):
        ...     def __init__(self):
        ...         super().__init__()
        ...         self.setup_llm_tracer()
    """

    _llm_tracer: Optional[AthenaTracer] = None
    _llm_provider: str = "unknown"
    _llm_model: str = "unknown"

    def setup_llm_tracer(
        self,
        provider: str,
        model: str,
        tracer: Optional[AthenaTracer] = None
    ) -> None:
        """
        设置LLM追踪器

        Args:
            provider: LLM提供商
            model: 模型名称
            tracer: 自定义追踪器
        """
        self._llm_provider = provider
        self._llm_model = model
        self._llm_tracer = tracer or AthenaTracer(f"llm.{provider}")

    @contextmanager
    def trace_llm(self, **kwargs):
        """
        LLM调用追踪上下文管理器

        Yields:
            (span, add_response) 元组
        """
        if self._llm_tracer:
            with trace_llm_call(
                self._llm_tracer,
                self._llm_provider,
                self._llm_model,
                **kwargs
            ) as result:
                yield result
        else:
            # 返回空上下文管理器
            from contextlib import nullcontext
            yield nullcontext()


# LLM提供商常量
class LLMProvider:
    """LLM提供商常量"""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    ZHIPU = "zhipu"
    QWEN = "qwen"
    OLLAMA = "ollama"


# 常用模型常量
class LLMModel:
    """常用LLM模型常量"""

    # Anthropic Claude
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"
    CLAUDE_3_5_SONNET = "claude-3-5-sonnet-20240620"

    # OpenAI GPT
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_3_5_TURBO = "gpt-3.5-turbo"

    # DeepSeek
    DEEPSEEK_CHAT = "deepseek-chat"

    # 智谱GLM
    GLM_4 = "glm-4"
    GLM_3_TURBO = "glm-3-turbo"

    # 通义千问
    QWEN_TURBO = "qwen-turbo"
    QWEN_PLUS = "qwen-plus"
    QWEN_MAX = "qwen-max"
