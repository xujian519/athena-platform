#!/usr/bin/env python3
from __future__ import annotations
"""
Athena工作平台Prometheus指标导出器
Prometheus Metrics Exporter for Athena Platform

提供统一的指标收集和导出功能

Created by Athena AI系统
Date: 2025-12-14
Version: 1.0.0
"""

import logging
import time
from functools import wraps

# Prometheus客户端
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    Summary,
    generate_latest,
)

# 配置

logger = logging.getLogger(__name__)


# =============================================================================
# 全局指标注册表
# =============================================================================

_global_registry: CollectorRegistry | None = None


def get_registry() -> CollectorRegistry:
    """
    获取全局指标注册表（单例）

    Returns:
        CollectorRegistry实例
    """
    global _global_registry

    if _global_registry is None:
        _global_registry = CollectorRegistry(auto_describe=True)
        logger.info("✅ Prometheus指标注册表初始化完成")

    return _global_registry


# =============================================================================
# Prometheus指标封装类
# =============================================================================

class PrometheusCounter:
    """
    Prometheus计数器封装

    只能递增，不能递减
    适用于：请求总数、错误总数等单调递增的指标
    """

    def __init__(self,
                 name: str,
                 description: str,
                 labelnames: tuple = (),
                 registry: CollectorRegistry | None = None):
        """
        初始化计数器

        Args:
            name: 指标名称（如：http_requests_total）
            description: 指标描述
            labelnames: 标签名称（如：('method', 'endpoint')）
            registry: 指标注册表
        """
        self.registry = registry or get_registry()
        self.counter = Counter(
            name=name,
            documentation=description,
            labelnames=labelnames,
            registry=self.registry
        )
        self.logger = logging.getLogger(f"{__name__}.Counter.{name}")

    def inc(self, amount: float = 1, **labels):
        """
        增加计数

        Args:
            amount: 增加量（默认1）
            **labels: 标签键值对
        """
        try:
            if labels:
                self.counter.labels(**labels).inc(amount)
            else:
                self.counter.inc(amount)
        except Exception as e:
            self.logger.error(f"计数器增加失败: {e}")

    def labels(self, **label_values):
        """
        获取带标签的计数器

        Args:
            **label_values: 标签值

        Returns:
            带标签的计数器实例
        """
        return self.counter.labels(**label_values)


class PrometheusHistogram:
    """
    Prometheus直方图封装

    用于观察数值，自动计算分布统计
    适用于：延迟、请求大小等需要分布的指标
    """

    def __init__(self,
                 name: str,
                 description: str,
                 labelnames: tuple = (),
                 buckets: tuple = (),
                 registry: CollectorRegistry | None = None):
        """
        初始化直方图

        Args:
            name: 指标名称（如：http_response_time_seconds）
            description: 指标描述
            labelnames: 标签名称
            buckets: 分桶（默认：.005, .01, .025, .05, .075, .1, .25, .5, .75, 1.0, 2.5, 5.0, 7.5, 10.0, INF）
            registry: 指标注册表
        """
        self.registry = registry or get_registry()
        self.histogram = Histogram(
            name=name,
            documentation=description,
            labelnames=labelnames,
            buckets=buckets if buckets else Histogram.DEFAULT_BUCKETS,
            registry=self.registry
        )
        self.logger = logging.getLogger(f"{__name__}.Histogram.{name}")

    def observe(self, amount: float, **labels):
        """
        观察值

        Args:
            amount: 观察值
            **labels: 标签键值对
        """
        try:
            if labels:
                self.histogram.labels(**labels).observe(amount)
            else:
                self.histogram.observe(amount)
        except Exception as e:
            self.logger.error(f"直方图观察失败: {e}")

    def labels(self, **label_values):
        """
        获取带标签的直方图

        Args:
            **label_values: 标签值

        Returns:
            带标签的直方图实例
        """
        return self.histogram.labels(**label_values)

    def time(self, **labels):
        """
        上下文管理器：计时

        Args:
            **labels: 标签键值对

        Returns:
            计时上下文管理器

        使用示例：
            with histogram.time(method="GET", endpoint="/api/patents"):
                # 业务逻辑
                pass
        """
        if labels:
            return self.histogram.labels(**labels).time()
        else:
            return self.histogram.time()


class PrometheusGauge:
    """
    Prometheus仪表封装

    可以增减，表示瞬时值
    适用于：连接数、队列大小、内存使用等
    """

    def __init__(self,
                 name: str,
                 description: str,
                 labelnames: tuple = (),
                 registry: CollectorRegistry | None = None):
        """
        初始化仪表

        Args:
            name: 指标名称（如：active_connections）
            description: 指标描述
            labelnames: 标签名称
            registry: 指标注册表
        """
        self.registry = registry or get_registry()
        self.gauge = Gauge(
            name=name,
            documentation=description,
            labelnames=labelnames,
            registry=self.registry
        )
        self.logger = logging.getLogger(f"{__name__}.Gauge.{name}")

    def set(self, value: float, **labels):
        """
        设置值

        Args:
            value: 设置的值
            **labels: 标签键值对
        """
        try:
            if labels:
                self.gauge.labels(**labels).set(value)
            else:
                self.gauge.set(value)
        except Exception as e:
            self.logger.error(f"仪表设置失败: {e}")

    def inc(self, amount: float = 1, **labels):
        """
        增加值

        Args:
            amount: 增加量（默认1）
            **labels: 标签键值对
        """
        try:
            if labels:
                self.gauge.labels(**labels).inc(amount)
            else:
                self.gauge.inc(amount)
        except Exception as e:
            self.logger.error(f"仪表增加失败: {e}")

    def dec(self, amount: float = 1, **labels):
        """
        减少值

        Args:
            amount: 减少量（默认1）
            **labels: 标签键值对
        """
        try:
            if labels:
                self.gauge.labels(**labels).dec(amount)
            else:
                self.gauge.dec(amount)
        except Exception as e:
            self.logger.error(f"仪表减少失败: {e}")

    def labels(self, **label_values):
        """
        获取带标签的仪表

        Args:
            **label_values: 标签值

        Returns:
            带标签的仪表实例
        """
        return self.gauge.labels(**label_values)


class PrometheusSummary:
    """
    Prometheus摘要封装

    类似直方图，但在客户端计算可配置的百分位数
    适用于：延迟分布等
    """

    def __init__(self,
                 name: str,
                 description: str,
                 labelnames: tuple = (),
                 registry: CollectorRegistry | None = None):
        """
        初始化摘要

        Args:
            name: 指标名称
            description: 指标描述
            labelnames: 标签名称
            registry: 指标注册表
        """
        self.registry = registry or get_registry()
        self.summary = Summary(
            name=name,
            documentation=description,
            labelnames=labelnames,
            registry=self.registry
        )
        self.logger = logging.getLogger(f"{__name__}.Summary.{name}")

    def observe(self, amount: float, **labels):
        """
        观察值

        Args:
            amount: 观察值
            **labels: 标签键值对
        """
        try:
            if labels:
                self.summary.labels(**labels).observe(amount)
            else:
                self.summary.observe(amount)
        except Exception as e:
            self.logger.error(f"摘要观察失败: {e}")

    def labels(self, **label_values):
        """
        获取带标签的摘要

        Args:
            **label_values: 标签值

        Returns:
            带标签的摘要实例
        """
        return self.summary.labels(**label_values)

    def time(self, **labels):
        """
        上下文管理器：计时

        Args:
            **labels: 标签键值对

        Returns:
            计时上下文管理器
        """
        if labels:
            return self.summary.labels(**labels).time()
        else:
            return self.summary.time()


# =============================================================================
# 装饰器：自动计时
# =============================================================================

def track_time(histogram: PrometheusHistogram, **labels):
    """
    装饰器：自动追踪函数执行时间

    Args:
        histogram: 直方图实例
        **labels: 预设标签

    使用示例：
        @track_time(response_time_histogram, endpoint="/api/patents")
        async def get_patents():
            pass
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                histogram.observe(duration, **labels)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                histogram.observe(duration, **labels)

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def track_count(counter: PrometheusCounter, **labels):
    """
    装饰器：自动计数函数调用

    Args:
        counter: 计数器实例
        **labels: 预设标签

    使用示例：
        @track_count(request_counter, method="GET")
        async def get_patents():
            pass
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            counter.inc(**labels)
            return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            counter.inc(**labels)
            return func(*args, **kwargs)

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# =============================================================================
# FastAPI集成
# =============================================================================

class PrometheusMiddleware:
    """
    Prometheus中间件（用于FastAPI）

    自动收集HTTP指标
    """

    def __init__(self, app=None):
        """
        初始化中间件

        Args:
            app: FastAPI应用实例
        """
        self.app = app

        # 创建指标
        self.request_count = PrometheusCounter(
            "http_requests_total",
            "Total HTTP requests",
            labelnames=("method", "endpoint", "status")
        )

        self.request_duration = PrometheusHistogram(
            "http_request_duration_seconds",
            "HTTP request duration",
            labelnames=("method", "endpoint"),
            buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
        )

        self.request_size = PrometheusSummary(
            "http_request_size_bytes",
            "HTTP request size"
        )

        self.response_size = PrometheusSummary(
            "http_response_size_bytes",
            "HTTP response size"
        )

    async def __call__(self, scope, receive, send):
        """
        中间件调用

        Args:
            scope: ASGI scope
            receive: ASGI receive
            send: ASGI send
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # 提取请求信息
        method = scope["method"]
        path = scope["path"]

        # 记录开始时间
        start_time = time.time()

        # 包装send函数以捕获响应
        status_code = None

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        # 处理请求
        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            # 记录指标
            duration = time.time() - start_time
            endpoint = path if path != "/metrics" else "/metrics"

            self.request_count.inc(
                method=method,
                endpoint=endpoint,
                status=status_code or 500
            )

            self.request_duration.observe(
                duration,
                method=method,
                endpoint=endpoint
            )


# =============================================================================
# 指标导出
# =============================================================================

def generate_metrics() -> bytes:
    """
    生成Prometheus格式的指标

    Returns:
        指标数据（bytes）
    """
    return generate_latest(get_registry())


def get_content_type() -> str:
    """
    获取指标内容类型

    Returns:
        内容类型字符串
    """
    return CONTENT_TYPE_LATEST


# =============================================================================
# 测试代码
# =============================================================================

async def test_metrics():
    """测试指标"""
    # 创建指标
    counter = PrometheusCounter("test_requests_total", "Test requests")
    histogram = PrometheusHistogram("test_duration_seconds", "Test duration")
    gauge = PrometheusGauge("test_gauge", "Test gauge")

    # 使用指标
    counter.inc()
    counter.inc(method="GET", endpoint="/api/test")

    histogram.observe(0.5)
    histogram.observe(1.2, method="POST")

    gauge.set(10)
    gauge.inc()
    gauge.dec()

    # 生成指标
    metrics = generate_metrics()
    logger.info(f"✅ 指标生成成功，长度: {len(metrics)} bytes")

    # 打印指标
    print("\n" + "="*60)
    print("Prometheus指标:")
    print("="*60)
    print(metrics.decode('utf-8'))
    print("="*60)


if __name__ == '__main__':
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 运行测试
    import asyncio
    asyncio.run(test_metrics())
