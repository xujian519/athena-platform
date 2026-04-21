"""
统一Prometheus指标收集器
Unified Prometheus Metrics Collector
"""
import time
import functools
from typing import Optional, Callable
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    CollectorRegistry,
    generate_latest,
)
import logging

logger = logging.getLogger(__name__)


class UnifiedMetricsCollector:
    """统一Prometheus指标收集器"""

    def __init__(self, service_name: str):
        """初始化指标收集器

        Args:
            service_name: 服务名称
        """
        self.service_name = service_name
        self.registry = CollectorRegistry()

        # 设置默认指标
        self._setup_default_metrics()

        logger.info(f"✅ {service_name} 统一指标收集器初始化完成")

    def _setup_default_metrics(self):
        """设置默认指标"""

        # 1. HTTP请求指标
        self.http_requests_total = Counter(
            'http_requests_total',
            'HTTP请求总数',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )

        self.http_request_duration_seconds = Histogram(
            'http_request_duration_seconds',
            'HTTP请求耗时（秒）',
            ['method', 'endpoint'],
            registry=self.registry
        )

        # 2. 服务任务指标
        self.service_tasks_total = Counter(
            'service_tasks_total',
            '服务任务总数',
            ['service', 'status'],
            registry=self.registry
        )

        self.service_task_duration_seconds = Histogram(
            'service_task_duration_seconds',
            '服务任务耗时（秒）',
            ['service', 'task_type'],
            registry=self.registry
        )

        # 3. 错误指标
        self.service_errors_total = Counter(
            'service_errors_total',
            '服务错误总数',
            ['service', 'error_type'],
            registry=self.registry
        )

        # 4. LLM调用指标
        self.llm_requests_total = Counter(
            'llm_requests_total',
            'LLM请求总数',
            ['provider', 'model'],
            registry=self.registry
        )

        self.llm_response_time_seconds = Histogram(
            'llm_response_time_seconds',
            'LLM响应时间（秒）',
            ['provider', 'model'],
            registry=self.registry
        )

        # 5. 缓存指标
        self.cache_hits_total = Counter(
            'cache_hits_total',
            '缓存命中总数',
            ['cache_type'],
            registry=self.registry
        )

        self.cache_misses_total = Counter(
            'cache_misses_total',
            '缓存未命中总数',
            ['cache_type'],
            registry=self.registry
        )

    def record_http_request(
        self,
        method: str,
        endpoint: str,
        status: int,
        duration: float
    ):
        """记录HTTP请求

        Args:
            method: HTTP方法
            endpoint: 端点路径
            status: HTTP状态码
            duration: 请求耗时（秒）
        """
        self.http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=status
        ).inc()

        self.http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)

    def record_service_task(
        self,
        task_type: str,
        status: str,
        duration: float
    ):
        """记录服务任务

        Args:
            task_type: 任务类型
            status: 任务状态（success/error）
            duration: 任务耗时（秒）
        """
        self.service_tasks_total.labels(
            service=self.service_name,
            status=status
        ).inc()

        self.service_task_duration_seconds.labels(
            service=self.service_name,
            task_type=task_type
        ).observe(duration)

    def record_error(self, error_type: str):
        """记录错误

        Args:
            error_type: 错误类型
        """
        self.service_errors_total.labels(
            service=self.service_name,
            error_type=error_type
        ).inc()

    def record_llm_request(
        self,
        provider: str,
        model: str,
        duration: float
    ):
        """记录LLM请求

        Args:
            provider: 提供商
            model: 模型名称
            duration: 响应时间（秒）
        """
        self.llm_requests_total.labels(
            provider=provider,
            model=model
        ).inc()

        self.llm_response_time_seconds.labels(
            provider=provider,
            model=model
        ).observe(duration)

    def record_cache_hit(self, cache_type: str):
        """记录缓存命中"""
        self.cache_hits_total.labels(cache_type=cache_type).inc()

    def record_cache_miss(self, cache_type: str):
        """记录缓存未命中"""
        self.cache_misses_total.labels(cache_type=cache_type).inc()

    def get_metrics(self) -> bytes:
        """获取Prometheus格式的指标"""
        return generate_latest(self.registry)


def monitor_performance(
    collector: UnifiedMetricsCollector,
    task_type: str = "default"
):
    """性能监控装饰器"""
    import asyncio

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                collector.record_error(f"{type(e).__name__}")
                raise
            finally:
                duration = time.time() - start_time
                collector.record_service_task(task_type, status, duration)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                collector.record_error(f"{type(e).__name__}")
                raise
            finally:
                duration = time.time() - start_time
                collector.record_service_task(task_type, status, duration)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# 单例实例
_collector_instances: dict = {}


def get_metrics_collector(service_name: str) -> UnifiedMetricsCollector:
    """获取指标收集器实例（单例模式）"""
    if service_name not in _collector_instances:
        _collector_instances[service_name] = UnifiedMetricsCollector(service_name)
    return _collector_instances[service_name]
