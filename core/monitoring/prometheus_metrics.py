from __future__ import annotations
"""
Prometheus监控指标
提供全面的性能和业务指标收集
"""

import asyncio
import logging
import time
from datetime import datetime
from functools import wraps
from typing import Any

from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    Info,
    generate_latest,
    start_http_server,
)

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class PrometheusMetrics:
    """Prometheus指标收集器"""

    def __init__(self, registry: CollectorRegistry | None = None):
        self.registry = registry or CollectorRegistry()
        self._setup_metrics()

    def _setup_metrics(self) -> Any:
        """设置监控指标"""

        # 请求指标
        self.request_count = Counter(
            "http_requests_total",
            "Total number of HTTP requests",
            ["method", "endpoint", "status_code"],
            registry=self.registry,
        )

        self.request_duration = Histogram(
            "http_request_duration_seconds",
            "HTTP request duration in seconds",
            ["method", "endpoint"],
            registry=self.registry,
        )

        self.request_size = Histogram(
            "http_request_size_bytes",
            "HTTP request size in bytes",
            ["method", "endpoint"],
            registry=self.registry,
        )

        self.response_size = Histogram(
            "http_response_size_bytes",
            "HTTP response size in bytes",
            ["method", "endpoint"],
            registry=self.registry,
        )

        # 系统指标
        self.active_connections = Gauge(
            "active_connections_total",
            "Number of active connections",
            ["service"],
            registry=self.registry,
        )

        self.memory_usage = Gauge(
            "memory_usage_bytes",
            "Memory usage in bytes",
            ["service", "type"],
            registry=self.registry,
        )

        self.cpu_usage = Gauge(
            "cpu_usage_percent", "CPU usage percentage", ["service"], registry=self.registry
        )

        # 业务指标
        self.ai_tasks_total = Counter(
            "ai_tasks_total",
            "Total number of AI tasks",
            ["ai_name", "task_type", "status"],
            registry=self.registry,
        )

        self.task_duration = Histogram(
            "ai_task_duration_seconds",
            "AI task execution duration in seconds",
            ["ai_name", "task_type"],
            registry=self.registry,
        )

        self.collaboration_efficiency = Gauge(
            "collaboration_efficiency_score",
            "Collaboration efficiency score",
            ["participants"],
            registry=self.registry,
        )

        self.cache_hits = Counter(
            "cache_hits_total",
            "Total number of cache hits",
            ["cache_type", "cache_level"],
            registry=self.registry,
        )

        self.cache_misses = Counter(
            "cache_misses_total",
            "Total number of cache misses",
            ["cache_type", "cache_level"],
            registry=self.registry,
        )

        # 错误指标
        self.error_count = Counter(
            "errors_total",
            "Total number of errors",
            ["service", "error_type", "severity"],
            registry=self.registry,
        )

        self.circuit_breaker_state = Gauge(
            "circuit_breaker_state",
            "Circuit breaker state (1=open, 0=closed)",
            ["service"],
            registry=self.registry,
        )

        # AI特定指标
        self.ai_confidence_score = Histogram(
            "ai_confidence_score",
            "AI response confidence score",
            ["ai_name", "task_type"],
            registry=self.registry,
        )

        self.ai_response_time = Histogram(
            "ai_response_time_seconds",
            "AI response time in seconds",
            ["ai_name", "model"],
            registry=self.registry,
        )

        # 服务信息
        self.service_info = Info("service_info", "Service information", registry=self.registry)

        # 消息队列指标
        self.message_queue_size = Gauge(
            "message_queue_size",
            "Current message queue size",
            ["queue_name"],
            registry=self.registry,
        )

        self.message_processing_time = Histogram(
            "message_processing_time_seconds",
            "Message processing time in seconds",
            ["queue_name"],
            registry=self.registry,
        )

    def record_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration: float,
        request_size: int = 0,
        response_size: int = 0,
    ):
        """记录HTTP请求指标"""
        self.request_count.labels(
            method=method, endpoint=endpoint, status_code=str(status_code)
        ).inc()

        self.request_duration.labels(method=method, endpoint=endpoint).observe(duration)

        if request_size > 0:
            self.request_size.labels(method=method, endpoint=endpoint).observe(request_size)

        if response_size > 0:
            self.response_size.labels(method=method, endpoint=endpoint).observe(response_size)

    def record_ai_task(
        self,
        ai_name: str,
        task_type: str,
        status: str,
        duration: Optional[float] = None,
        confidence: Optional[float] = None,
    ):
        """记录AI任务指标"""
        self.ai_tasks_total.labels(ai_name=ai_name, task_type=task_type, status=status).inc()

        if duration:
            self.task_duration.labels(ai_name=ai_name, task_type=task_type).observe(duration)

        if confidence:
            self.ai_confidence_score.labels(ai_name=ai_name, task_type=task_type).observe(
                confidence
            )

    def record_cache_operation(self, cache_type: str, cache_level: str, hit: bool) -> Any:
        """记录缓存操作"""
        if hit:
            self.cache_hits.labels(cache_type=cache_type, cache_level=cache_level).inc()
        else:
            self.cache_misses.labels(cache_type=cache_type, cache_level=cache_level).inc()

    def record_error(self, service: str, error_type: str, severity: str) -> Any:
        """记录错误"""
        self.error_count.labels(service=service, error_type=error_type, severity=severity).inc()

    def update_circuit_breaker(self, service: str, is_open: bool) -> None:
        """更新熔断器状态"""
        self.circuit_breaker_state.labels(service=service).set(1 if is_open else 0)

    def update_active_connections(self, service: str, count: int) -> None:
        """更新活跃连接数"""
        self.active_connections.labels(service=service).set(count)

    def update_memory_usage(self, service: str, usage_type: str, bytes_used: int) -> None:
        """更新内存使用"""
        self.memory_usage.labels(service=service, type=usage_type).set(bytes_used)

    def update_cpu_usage(self, service: str, percent: float) -> None:
        """更新CPU使用率"""
        self.cpu_usage.labels(service=service).set(percent)

    def update_collaboration_efficiency(self, participants: str, efficiency: float) -> None:
        """更新协作效率"""
        self.collaboration_efficiency.labels(participants=participants).set(efficiency)

    def update_service_info(self, service_name: str, version: str, **kwargs) -> None:
        """更新服务信息"""
        info = {
            "service_name": service_name,
            "version": version,
            "timestamp": datetime.now().isoformat(),
        }
        info.update(kwargs)
        self.service_info.info(info)

    def update_message_queue(self, queue_name: str, size: int) -> None:
        """更新消息队列大小"""
        self.message_queue_size.labels(queue_name=queue_name).set(size)

    def record_message_processing(self, queue_name: str, duration: float) -> Any:
        """记录消息处理时间"""
        self.message_processing_time.labels(queue_name=queue_name).observe(duration)

    def get_metrics(self) -> str:
        """获取Prometheus格式的指标"""
        return generate_latest(self.registry).decode("utf-8")


# 全局指标收集器
metrics = PrometheusMetrics()


# 装饰器
def track_requests(func) -> None:
    """请求跟踪装饰器"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        method = getattr(kwargs.get("request"), "method", "UNKNOWN")
        endpoint = getattr(kwargs.get("request"), "url", {}).path or func.__name__
        status_code = 200

        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            status_code = 500
            metrics.record_error(
                service=func.__module__, error_type=type(e).__name__, severity="high"
            )
            raise
        finally:
            duration = time.time() - start_time
            metrics.record_request(method, endpoint, status_code, duration)

    return wrapper


def track_ai_task(ai_name: str, task_type: str) -> Any:
    """AI任务跟踪装饰器"""

    def decorator(func) -> None:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            confidence = None

            try:
                result = await func(*args, **kwargs)
                # 提取置信度(如果存在)
                if isinstance(result, dict) and "confidence" in result:
                    confidence = result["confidence"]
                return result
            except Exception as e:
                status = "failed"
                metrics.record_error(
                    service=f"ai_{ai_name}", error_type=type(e).__name__, severity="medium"
                )
                raise
            finally:
                duration = time.time() - start_time
                metrics.record_ai_task(ai_name, task_type, status, duration, confidence)

        return wrapper

    return decorator


# 监控任务
async def start_metrics_collection(interval: int = 30):
    """启动指标收集任务"""
    import os

    import psutil

    logger.info("启动Prometheus指标收集")

    process = psutil.Process(os.getpid())
    service_name = "fusion_platform"

    while True:
        try:
            # 收集系统指标
            memory_info = process.memory_info()
            cpu_percent = process.cpu_percent()

            metrics.update_memory_usage(
                service=service_name, usage_type="rss", bytes_used=memory_info.rss
            )

            metrics.update_memory_usage(
                service=service_name, usage_type="vms", bytes_used=memory_info.vms
            )

            metrics.update_cpu_usage(service=service_name, percent=cpu_percent)

            await asyncio.sleep(interval)

        except Exception as e:
            logger.error(f"指标收集错误: {e}")
            await asyncio.sleep(interval)


# 启动Prometheus HTTP服务器
def start_prometheus_server(port: int = 8000) -> Any:
    """启动Prometheus HTTP服务器"""
    try:
        start_http_server(port)
        logger.info(f"Prometheus服务器启动在端口 {port}")
    except Exception as e:
        logger.error(f"Prometheus服务器启动失败: {e}")


# 监控仪表板配置
DASHBOARD_CONFIG = {
    "panels": [
        {
            "title": "HTTP请求率",
            "type": "graph",
            "targets": [
                {
                    "expr": "rate(http_requests_total[5m])",
                    "legend_format": "{{method}} {{endpoint}}",
                }
            ],
        },
        {
            "title": "请求延迟",
            "type": "graph",
            "targets": [
                {
                    "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
                    "legend_format": "95th percentile",
                },
                {
                    "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
                    "legend_format": "50th percentile",
                },
            ],
        },
        {
            "title": "AI任务执行",
            "type": "graph",
            "targets": [
                {
                    "expr": "rate(ai_tasks_total[5m])",
                    "legend_format": "{{ai_name}} {{task_type}} {{status}}",
                }
            ],
        },
        {
            "title": "缓存命中率",
            "type": "singlestat",
            "targets": [
                {
                    "expr": "cache_hits_total / (cache_hits_total + cache_misses_total) * 100",
                    "legend_format": "Hit Rate %",
                }
            ],
        },
        {
            "title": "内存使用",
            "type": "graph",
            "targets": [
                {
                    "expr": "memory_usage_bytes / 1024 / 1024",
                    "legend_format": "{{service}} {{type}} (MB)",
                }
            ],
        },
        {
            "title": "错误率",
            "type": "graph",
            "targets": [
                {"expr": "rate(errors_total[5m])", "legend_format": "{{service}} {{error_type}}"}
            ],
        },
    ]
}

# 告警规则配置
ALERT_RULES = """
groups:
- name: fusion_platform_alerts
  rules:
  - alert: HighErrorRate
    expr: rate(errors_total[5m]) > 0.1
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: 'High error rate detected'
      description: 'Error rate is above 10% for 2 minutes'

  - alert: HighMemoryUsage
    expr: memory_usage_bytes / (1024*1024*1024) > 2
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: 'High memory usage'
      description: 'Memory usage is above 2GB'

  - alert: CircuitBreakerOpen
    expr: circuit_breaker_state == 1
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: 'Circuit breaker is open'
      description: 'Circuit breaker for {{ $labels.service }} is open'

  - alert: ServiceDown
    expr: up == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: 'Service is down'
      description: 'Service {{ $labels.instance }} is down'
"""


# 便捷函数
def get_metrics_summary() -> dict[str, Any]:
    """获取指标摘要"""
    # 这里可以实现指标摘要逻辑
    return {"timestamp": datetime.now().isoformat(), "metrics_available": True}
