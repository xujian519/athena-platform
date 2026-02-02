#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Athena工作平台统一追踪器
Unified Tracer for Athena Platform

基于OpenTelemetry的分布式追踪实现
提供装饰器和上下文管理器两种使用方式

Created by Athena AI系统
Date: 2025-12-14
Version: 1.0.0
"""

import asyncio
import logging
import functools
import time
from typing import Any, Callable, Dict, Optional, TypeVar
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass

# OpenTelemetry导入
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.trace import Status, StatusCode, Span
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.context import Context

# 配置
from shared.observability.tracing.config import OPENTELEMETRY_CONFIG

logger = logging.getLogger(__name__)

T = TypeVar('T')


# =============================================================================
# 全局TracerProvider初始化
# =============================================================================

_global_tracer_provider: Optional[TracerProvider] = None
_global_tracer: Optional[trace.Tracer] = None


def _initialize_tracer_provider(service_name: str) -> TracerProvider:
    """
    初始化TracerProvider

    Args:
        service_name: 服务名称

    Returns:
        TracerProvider实例
    """
    global _global_tracer_provider

    if _global_tracer_provider is None:
        # 创建资源
        resource = Resource(attributes={
            SERVICE_NAME: service_name,
            "environment": OPENTELEMETRY_CONFIG.get("environment", "development"),
            "service.version": "1.0.0"
        })

        # 创建TracerProvider
        _global_tracer_provider = TracerProvider(resource=resource)

        # 配置导出器
        exporter_type = OPENTELEMETRY_CONFIG.get("exporter", "console")

        if exporter_type == "console":
            # 控制台导出器（开发环境）
            exporter = ConsoleSpanExporter()
            logger.info("✅ 使用Console Span Exporter")

        elif exporter_type == "jaeger":
            # Jaeger导出器
            try:
                from opentelemetry.exporter.jaeger.thrift import JaegerExporter
                jaeger_endpoint = OPENTELEMETRY_CONFIG.get("jaeger_endpoint")
                exporter = JaegerExporter(
                    agent_host_name=jaeger_endpoint.split(":")[1].replace("//", ""),
                    agent_port=int(jaeger_endpoint.split(":")[-1].split("/")[0])
                )
                logger.info(f"✅ 使用Jaeger Exporter: {jaeger_endpoint}")
            except ImportError:
                logger.warning("⚠️ Jaeger exporter未安装，回退到Console")
                exporter = ConsoleSpanExporter()

        elif exporter_type == "otlp":
            # OTLP导出器
            try:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
                otlp_endpoint = OPENTELEMETRY_CONFIG.get("otlp_endpoint", "localhost:4317")
                exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
                logger.info(f"✅ 使用OTLP Exporter: {otlp_endpoint}")
            except ImportError:
                logger.warning("⚠️ OTLP exporter未安装，回退到Console")
                exporter = ConsoleSpanExporter()
        else:
            exporter = ConsoleSpanExporter()

        # 添加Span处理器
        if OPENTELEMETRY_CONFIG.get("enable_batch_export", True):
            batch_processor = BatchSpanProcessor(
                exporter,
                schedule_delay_millis=OPENTELEMETRY_CONFIG.get("batch_export_schedule_delay", 5000),
                max_queue_size=OPENTELEMETRY_CONFIG.get("batch_export_max_queue_size", 2048)
            )
            _global_tracer_provider.add_span_processor(batch_processor)
        else:
            _global_tracer_provider.add_span_processor(exporter)

        # 设置全局TracerProvider
        trace.set_tracer_provider(_global_tracer_provider)
        logger.info(f"✅ TracerProvider初始化完成: {service_name}")

    return _global_tracer_provider


def get_tracer(service_name: str, instrumenting_module: str = __name__) -> 'AthenaTracer':
    """
    获取统一追踪器（单例模式）

    Args:
        service_name: 服务名称（如：patent-service, crawler-service）
        instrumenting_module: 模块名称

    Returns:
        AthenaTracer实例
    """
    global _global_tracer

    if _global_tracer is None or _global_tracer.service_name != service_name:
        # 初始化TracerProvider
        _initialize_tracer_provider(service_name)

        # 创建Tracer
        otel_tracer = trace.get_tracer(instrumenting_module)
        _global_tracer = AthenaTracer(service_name, otel_tracer)
        logger.info(f"✅ AthenaTracer创建成功: {service_name}")

    return _global_tracer


# =============================================================================
# AthenaTracer统一追踪器
# =============================================================================

class AthenaTracer:
    """
    Athena统一追踪器

    提供装饰器和上下文管理器两种使用方式

    使用示例：
        # 方式1：装饰器
        @tracer.trace("analyze_patent")
        async def analyze_patent(patent_id):
            pass

        # 方式2：上下文管理器
        async with tracer.start_span("analyze_patent"):
            pass
    """

    def __init__(self, service_name: str, otel_tracer: trace.Tracer):
        """
        初始化追踪器

        Args:
            service_name: 服务名称
            otel_tracer: OpenTelemetry Tracer实例
        """
        self.service_name = service_name
        self.tracer = otel_tracer
        self.logger = logging.getLogger(f"{__name__}.{service_name}")

    def trace(self, operation_name: str,
              attributes: Optional[Dict[str, Any]] = None):
        """
        装饰器：自动追踪函数/方法

        Args:
            operation_name: 操作名称（如：analyze_patent, llm_call）
            attributes: 预设的Span属性

        Returns:
            装饰器函数

        使用示例：
            @tracer.trace("analyze_patent")
            async def analyze_patent(patent_id: str):
                # Span名称: service-name.analyze_patent
                # 自动添加属性: {"patent_id": patent_id}
                return await process(patent_id)
        """
        def decorator(func: Callable) -> Callable:
            # 判断是否是异步函数
            if asyncio.iscoroutinefunction(func):
                @functools.wraps(func)
                async def async_wrapper(*args, **kwargs):
                    span_name = f"{self.service_name}.{operation_name}"

                    with self.tracer.start_as_current_span(span_name) as span:
                        # 添加预设属性
                        if attributes:
                            for key, value in attributes.items():
                                span.set_attribute(key, str(value))

                        # 自动从函数参数提取属性
                        self._extract_params_to_span(span, func, args, kwargs)

                        # 记录开始时间
                        start_time = time.time()
                        span.add_event("operation_started", {"timestamp": start_time})

                        try:
                            result = await func(*args, **kwargs)

                            # 记录成功
                            duration = time.time() - start_time
                            span.set_attribute("success", True)
                            span.set_attribute("duration_seconds", duration)
                            span.add_event("operation_completed", {"duration": duration})

                            return result

                        except Exception as e:
                            # 记录异常
                            duration = time.time() - start_time
                            span.set_attribute("success", False)
                            span.set_attribute("error", str(e))
                            span.set_attribute("duration_seconds", duration)
                            span.record_exception(e)
                            span.set_status(Status(StatusCode.ERROR, str(e)))
                            raise

                return async_wrapper

            else:
                # 同步函数
                @functools.wraps(func)
                def sync_wrapper(*args, **kwargs):
                    span_name = f"{self.service_name}.{operation_name}"

                    with self.tracer.start_as_current_span(span_name) as span:
                        # 添加预设属性
                        if attributes:
                            for key, value in attributes.items():
                                span.set_attribute(key, str(value))

                        # 自动从函数参数提取属性
                        self._extract_params_to_span(span, func, args, kwargs)

                        # 记录开始时间
                        start_time = time.time()
                        span.add_event("operation_started", {"timestamp": start_time})

                        try:
                            result = func(*args, **kwargs)

                            # 记录成功
                            duration = time.time() - start_time
                            span.set_attribute("success", True)
                            span.set_attribute("duration_seconds", duration)
                            span.add_event("operation_completed", {"duration": duration})

                            return result

                        except Exception as e:
                            # 记录异常
                            duration = time.time() - start_time
                            span.set_attribute("success", False)
                            span.set_attribute("error", str(e))
                            span.set_attribute("duration_seconds", duration)
                            span.record_exception(e)
                            span.set_status(Status(StatusCode.ERROR, str(e)))
                            raise

                return sync_wrapper

        return decorator

    @asynccontextmanager
    async def start_async_span(self, operation_name: str,
                               attributes: Optional[Dict[str, Any]] = None):
        """
        异步上下文管理器：手动创建Span

        Args:
            operation_name: 操作名称
            attributes: Span属性

        使用示例：
            async with tracer.start_async_span("custom_operation"):
                # 业务逻辑
                pass
        """
        span_name = f"{self.service_name}.{operation_name}"
        with self.tracer.start_as_current_span(span_name) as span:
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, str(value))

            span.add_event("span_started", {"timestamp": time.time()})

            try:
                yield span
                span.set_attribute("success", True)
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise

    @contextmanager
    def start_span(self, operation_name: str,
                   attributes: Optional[Dict[str, Any]] = None):
        """
        同步上下文管理器：手动创建Span

        Args:
            operation_name: 操作名称
            attributes: Span属性

        使用示例：
            with tracer.start_span("custom_operation"):
                # 业务逻辑
                pass
        """
        span_name = f"{self.service_name}.{operation_name}"
        with self.tracer.start_as_current_span(span_name) as span:
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, str(value))

            span.add_event("span_started", {"timestamp": time.time()})

            try:
                yield span
                span.set_attribute("success", True)
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise

    def get_current_span(self) -> Span:
        """
        获取当前活动的Span

        Returns:
            当前Span实例
        """
        return trace.get_current_span()

    def _extract_params_to_span(self, span: Span, func: Callable,
                                args: tuple, kwargs: dict):
        """
        自动从函数参数提取并添加到Span属性

        Args:
            span: Span实例
            func: 函数对象
            args: 位置参数
            kwargs: 关键字参数
        """
        import inspect

        try:
            # 获取函数签名
            sig = inspect.signature(func)
            parameters = sig.parameters

            # 绑定参数
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # 提取常见参数
            for param_name, param_value in bound_args.arguments.items():
                # 跳过self和cls
                if param_name in ['self', 'cls']:
                    continue

                # 只记录简单类型
                if isinstance(param_value, (str, int, float, bool)):
                    attr_name = f"param.{param_name}"
                    span.set_attribute(attr_name, str(param_value))

        except Exception as e:
            self.logger.debug(f"参数提取失败（不影响业务）: {e}")


# =============================================================================
# 上下文传播
# =============================================================================

class TraceContext:
    """
    追踪上下文传播器

    用于跨进程/跨服务传播追踪上下文
    """

    def __init__(self):
        self.propagator = TraceContextTextMapPropagator()

    def inject(self, headers: Dict[str, str]) -> Dict[str, str]:
        """
        注入追踪上下文到HTTP头

        Args:
            headers: 原始HTTP头

        Returns:
            包含追踪上下文的HTTP头
        """
        ctx = trace.get_current()
        self.propagator.inject(headers, context=ctx)
        return headers

    def extract(self, headers: Dict[str, str]) -> Context:
        """
        从HTTP头提取追踪上下文

        Args:
            headers: HTTP头

        Returns:
            追踪上下文
        """
        ctx = self.propagator.extract(headers)
        return ctx


# =============================================================================
# 辅助函数
# =============================================================================

def add_span_attributes(**attributes):
    """
    辅助装饰器：添加额外的Span属性

    使用示例：
        @add_span_attributes(custom_attr="value")
        @tracer.trace("operation")
        async def operation():
            pass
    """
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            current_span = trace.get_current_span()
            for key, value in attributes.items():
                current_span.set_attribute(key, str(value))
            return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            current_span = trace.get_current_span()
            for key, value in attributes.items():
                current_span.set_attribute(key, str(value))
            return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# =============================================================================
# 测试代码
# =============================================================================

async def test_tracer():
    """测试追踪器"""
    import random

    # 创建追踪器
    tracer = get_tracer("test-service")

    # 测试装饰器
    @tracer.trace("test_operation")
    async def test_function(user_id: str, action: str):
        await asyncio.sleep(0.1)
        if random.random() < 0.3:
            raise ValueError("随机错误")
        return f"操作成功: {action}"

    # 执行测试
    try:
        result = await test_function("user123", "login")
        logger.info(f"✅ {result}")
    except Exception as e:
        logger.error(f"❌ 错误已记录到Span: {e}")


if __name__ == '__main__':
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 运行测试
    asyncio.run(test_tracer())
