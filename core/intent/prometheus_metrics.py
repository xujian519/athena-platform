from __future__ import annotations
"""
意图识别服务 - Prometheus监控集成

提供Prometheus指标采集和导出功能。

Author: Xiaonuo
Created: 2025-01-17
Version: 1.0.0
"""

import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any

try:
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        CollectorRegistry,
        Counter,
        Gauge,
        Histogram,
        Summary,
        generate_latest,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logging.warning("prometheus_client未安装,监控功能将不可用")


# ========================================================================
# 指标注册表
# ========================================================================

_registry = CollectorRegistry() if PROMETHEUS_AVAILABLE else None


def get_registry() -> CollectorRegistry | None:
    """
    获取指标注册表

    Returns:
        CollectorRegistry实例或None
    """
    return _registry


# ========================================================================
# 意图识别核心指标
# ========================================================================

if PROMETHEUS_AVAILABLE:
    # 请求计数器
    intent_requests_total = Counter(
        "intent_recognition_requests_total",
        "意图识别请求总数",
        ["engine_type", "intent_type", "status"],
        registry=_registry,
    )

    # 请求延迟直方图
    intent_latency_seconds = Histogram(
        "intent_recognition_latency_seconds",
        "意图识别请求延迟",
        ["engine_type"],
        buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
        registry=_registry,
    )

    # 批处理大小直方图
    batch_size_distribution = Histogram(
        "intent_batch_size_distribution",
        "批处理大小分布",
        buckets=(1, 2, 4, 8, 16, 32, 64, 128),
        registry=_registry,
    )

    # 批处理吞吐量
    batch_throughput = Gauge(
        "intent_batch_throughput_per_second",
        "批处理吞吐量(请求/秒)",
        ["strategy"],
        registry=_registry,
    )

    # 当前批大小
    current_batch_size = Gauge(
        "intent_current_batch_size", "当前批大小", ["processor_name"], registry=_registry
    )

    # 模型加载计数
    model_loads_total = Counter(
        "intent_model_loads_total", "模型加载次数", ["model_name", "status"], registry=_registry
    )

    # 模型加载时间
    model_load_duration_seconds = Histogram(
        "intent_model_load_duration_seconds",
        "模型加载耗时",
        ["model_name"],
        buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
        registry=_registry,
    )

    # 已加载模型数量
    loaded_models_count = Gauge("intent_loaded_models_count", "已加载模型数量", registry=_registry)

    # 模型内存使用
    model_memory_usage_bytes = Gauge(
        "intent_model_memory_usage_bytes",
        "模型内存使用量(字节)",
        ["model_name"],
        registry=_registry,
    )

    # 缓存命中率
    cache_hit_rate = Gauge(
        "intent_cache_hit_rate", "缓存命中率", ["cache_type"], registry=_registry
    )

    # 缓存大小
    cache_size = Gauge("intent_cache_size", "缓存大小", ["cache_type"], registry=_registry)

    # 队列长度
    queue_length = Gauge("intent_queue_length", "队列长度", ["queue_name"], registry=_registry)

    # 错误计数
    errors_total = Counter(
        "intent_errors_total", "错误总数", ["error_type", "component"], registry=_registry
    )

    # 系统资源使用
    system_resource_usage = Gauge(
        "intent_system_resource_usage",
        "系统资源使用率",
        ["resource_type"],  # cpu, memory, gpu
        registry=_registry,
    )

else:
    # 创建空对象以避免导入错误
    class MockMetric:
        def __init__(self, *args, **kwargs):
            pass

        def labels(self, *args, **kwargs) -> Any:
            return self

        def inc(self, *args, **kwargs) -> Any:
            pass

        def dec(self, *args, **kwargs) -> Any:
            pass

        def observe(self, *args, **kwargs) -> Any:
            pass

        def set(self, *args, **kwargs) -> Any:
            pass

        def time(self, *args, **kwargs) -> Any:
            def decorator(func) -> None:
                return func

            return decorator

    intent_requests_total = MockMetric()
    intent_latency_seconds = MockMetric()
    batch_size_distribution = MockMetric()
    batch_throughput = MockMetric()
    current_batch_size = MockMetric()
    model_loads_total = MockMetric()
    model_load_duration_seconds = MockMetric()
    loaded_models_count = MockMetric()
    model_memory_usage_bytes = MockMetric()
    cache_hit_rate = MockMetric()
    cache_size = MockMetric()
    queue_length = MockMetric()
    errors_total = MockMetric()
    system_resource_usage = MockMetric()


# ========================================================================
# 装饰器
# ========================================================================


def track_request(engine_type: str = "unknown") -> Any:
    """
    跟踪请求的装饰器

    Args:
        engine_type: 引擎类型

    Returns:
        装饰器函数
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.perf_counter()
            status = "success"

            try:
                result = func(*args, **kwargs)

                # 记录成功请求
                intent_type = result.intent.value if hasattr(result, "intent") else "unknown"

                intent_requests_total.labels(
                    engine_type=engine_type, intent_type=intent_type, status=status
                ).inc()

                return result

            except Exception as e:
                status = "error"
                error_type = type(e).__name__

                # 记录错误请求
                intent_requests_total.labels(
                    engine_type=engine_type, intent_type="unknown", status=status
                ).inc()

                # 记录错误
                errors_total.labels(error_type=error_type, component="intent_recognition").inc()

                raise

            finally:
                # 记录延迟
                duration = time.perf_counter() - start_time
                intent_latency_seconds.labels(engine_type=engine_type).observe(duration)

        return wrapper

    return decorator


def track_model_load(model_name: str) -> Any:
    """
    跟踪模型加载的装饰器

    Args:
        model_name: 模型名称

    Returns:
        装饰器函数
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.perf_counter()
            status = "success"

            try:
                result = func(*args, **kwargs)

                model_loads_total.labels(model_name=model_name, status=status).inc()

                # 更新已加载模型计数
                if hasattr(result, "model_instance") and result.model_instance is not None:
                    loaded_models_count.inc()

                return result

            except Exception as e:
                status = "error"
                error_type = type(e).__name__

                model_loads_total.labels(model_name=model_name, status=status).inc()

                errors_total.labels(error_type=error_type, component="model_loader").inc()

                raise

            finally:
                # 记录加载时间
                duration = time.perf_counter() - start_time
                model_load_duration_seconds.labels(model_name=model_name).observe(duration)

        return wrapper

    return decorator


# ========================================================================
# 指标管理器
# ========================================================================


class IntentMetricsManager:
    """
    意图识别指标管理器

    管理所有意图识别相关的Prometheus指标。
    """

    def __init__(self):
        """初始化指标管理器"""
        self.logger = logging.getLogger("intent.metrics")
        self._enabled = PROMETHEUS_AVAILABLE

    def record_request(
        self, engine_type: str, intent_type: str, status: str, duration: float
    ) -> None:
        """
        记录请求指标

        Args:
            engine_type: 引擎类型
            intent_type: 意图类型
            status: 请求状态
            duration: 请求耗时(秒)
        """
        if not self._enabled:
            return

        intent_requests_total.labels(
            engine_type=engine_type, intent_type=intent_type, status=status
        ).inc()

        intent_latency_seconds.labels(engine_type=engine_type).observe(duration)

    def record_batch(self, batch_size: int, throughput: float, strategy: str) -> None:
        """
        记录批处理指标

        Args:
            batch_size: 批大小
            throughput: 吞吐量(请求/秒)
            strategy: 批处理策略
        """
        if not self._enabled:
            return

        batch_size_distribution.observe(batch_size)
        batch_throughput.labels(strategy=strategy).set(throughput)

    def record_model_load(self, model_name: str, duration: float, status: str) -> None:
        """
        记录模型加载指标

        Args:
            model_name: 模型名称
            duration: 加载耗时(秒)
            status: 加载状态
        """
        if not self._enabled:
            return

        model_loads_total.labels(model_name=model_name, status=status).inc()

        model_load_duration_seconds.labels(model_name=model_name).observe(duration)

    def update_loaded_models_count(self, count: int) -> None:
        """
        更新已加载模型数量

        Args:
            count: 模型数量
        """
        if not self._enabled:
            return

        loaded_models_count.set(count)

    def update_cache_metrics(self, cache_type: str, hit_rate: float, size: int) -> None:
        """
        更新缓存指标

        Args:
            cache_type: 缓存类型
            hit_rate: 命中率
            size: 缓存大小
        """
        if not self._enabled:
            return

        cache_hit_rate.labels(cache_type=cache_type).set(hit_rate)
        cache_size.labels(cache_type=cache_type).set(size)

    def update_queue_length(self, queue_name: str, length: int) -> None:
        """
        更新队列长度

        Args:
            queue_name: 队列名称
            length: 队列长度
        """
        if not self._enabled:
            return

        queue_length.labels(queue_name=queue_name).set(length)

    def update_current_batch_size(self, processor_name: str, size: int) -> None:
        """
        更新当前批大小

        Args:
            processor_name: 处理器名称
            size: 批大小
        """
        if not self._enabled:
            return

        current_batch_size.labels(processor_name=processor_name).set(size)

    def record_error(self, error_type: str, component: str) -> None:
        """
        记录错误

        Args:
            error_type: 错误类型
            component: 组件名称
        """
        if not self._enabled:
            return

        errors_total.labels(error_type=error_type, component=component).inc()

    def update_system_resources(
        self, cpu_percent: float, memory_percent: float, gpu_utilization: float | None = None
    ) -> None:
        """
        更新系统资源指标

        Args:
            cpu_percent: CPU使用率(百分比)
            memory_percent: 内存使用率(百分比)
            gpu_utilization: GPU使用率(百分比,可选)
        """
        if not self._enabled:
            return

        system_resource_usage.labels(resource_type="cpu").set(cpu_percent)
        system_resource_usage.labels(resource_type="memory").set(memory_percent)

        if gpu_utilization is not None:
            system_resource_usage.labels(resource_type="gpu").set(gpu_utilization)

    def get_metrics_text(self) -> str:
        """
        获取Prometheus格式的指标文本

        Returns:
            Prometheus指标文本
        """
        if not self._enabled:
            return "# Prometheus metrics not available"

        try:
            return generate_latest(_registry).decode("utf-8")
        except Exception as e:
            self.logger.error(f"生成指标失败: {e}")
            return f"# Error generating metrics: {e}"

    def get_content_type(self) -> str:
        """
        获取指标内容类型

        Returns:
            Content-Type字符串
        """
        if not self._enabled:
            return "text/plain"

        return CONTENT_TYPE_LATEST

    def is_enabled(self) -> bool:
        """
        检查监控是否启用

        Returns:
            是否启用
        """
        return self._enabled


# ========================================================================
# 全局实例
# ========================================================================

_metrics_manager: IntentMetricsManager | None = None


def get_metrics_manager() -> IntentMetricsManager:
    """
    获取全局指标管理器实例

    Returns:
        指标管理器实例
    """
    global _metrics_manager
    if _metrics_manager is None:
        _metrics_manager = IntentMetricsManager()
    return _metrics_manager


# ========================================================================
# FastAPI集成
# ========================================================================


async def metrics_endpoint():
    """
    Prometheus指标端点

    用于FastAPI/Starlette的端点函数。

    Returns:
        Response对象
    """
    from fastapi import Response

    manager = get_metrics_manager()
    metrics_text = manager.get_metrics_text()
    content_type = manager.get_content_type()

    return Response(content=metrics_text, media_type=content_type)


# ========================================================================
# 导出
# ========================================================================

__all__ = [
    # 管理器
    "IntentMetricsManager",
    "batch_size_distribution",
    "batch_throughput",
    "cache_hit_rate",
    "cache_size",
    "current_batch_size",
    "errors_total",
    "get_metrics_manager",
    "get_registry",
    "intent_latency_seconds",
    # 指标
    "intent_requests_total",
    "loaded_models_count",
    # FastAPI
    "metrics_endpoint",
    "model_load_duration_seconds",
    "model_loads_total",
    "model_memory_usage_bytes",
    "queue_length",
    "system_resource_usage",
    "track_model_load",
    # 装饰器
    "track_request",
]
