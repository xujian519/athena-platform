#!/usr/bin/env python3
"""
Prometheus监控指标定义
Prometheus Metrics Definition for Context Management

指标类型:
- Counter: 计数器（只增不减）
- Histogram: 直方图（分布统计）
- Gauge: 仪表（可增可减）

作者: Athena平台团队
创建时间: 2026-04-24
版本: v1.0.0
"""

import logging
import threading
import time
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Union

# Prometheus client
try:
    from prometheus_client import (
        Counter,
        Gauge,
        Histogram,
        CollectorRegistry,
        start_http_server,
        disable_created_metrics,
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # 创建空类用于类型提示
    Counter = Histogram = Gauge = CollectorRegistry = object  # type: ignore

logger = logging.getLogger(__name__)

# 指标命名空间
METRIC_NAMESPACE = "athena_context"
METRIC_SUBSYSTEM = "management"


class ContextMetrics:
    """
    上下文管理监控指标

    提供完整的Prometheus指标收集和导出功能。

    使用示例:
        ```python
        from core.context_management.monitoring import ContextMetrics

        metrics = ContextMetrics()

        # 记录操作
        metrics.context_operations.labels(
            operation="create",
            context_type="task"
        ).inc()

        # 记录延迟
        with metrics.operation_latency.labels(
            operation="create",
            context_type="task"
        ).time():
            # 执行操作
            pass
        ```
    """

    def __init__(self, registry: Optional["CollectorRegistry"] = None):
        """
        初始化监控指标

        Args:
            registry: Prometheus指标注册表，默认使用全局注册表
        """
        if not PROMETHEUS_AVAILABLE:
            logger.warning("⚠️ prometheus_client未安装，监控功能将被禁用")
            self._enabled = False
            return

        self._enabled = True
        self._registry = registry or CollectorRegistry()
        self._lock = threading.Lock()

        # 初始化所有指标
        self._init_counters()
        self._init_histograms()
        self._init_gauges()

        logger.info("✅ Prometheus监控指标初始化完成")

    def _init_counters(self) -> None:
        """初始化计数器指标"""
        # 上下文操作计数器
        self.context_operations = Counter(
            f"{METRIC_NAMESPACE}_{METRIC_SUBSYSTEM}_operations_total",
            "上下文操作总数",
            ["operation", "context_type", "status"],  # operation: create/read/update/delete
            registry=self._registry,
        )

        # 缓存操作计数器
        self.cache_operations = Counter(
            f"{METRIC_NAMESPACE}_{METRIC_SUBSYSTEM}_cache_operations_total",
            "缓存操作总数",
            ["operation", "cache_type"],  # operation: hit/miss
            registry=self._registry,
        )

        # 错误计数器
        self.errors_total = Counter(
            f"{METRIC_NAMESPACE}_{METRIC_SUBSYSTEM}_errors_total",
            "错误总数",
            ["error_type", "operation"],
            registry=self._registry,
        )

    def _init_histograms(self) -> None:
        """初始化直方图指标"""
        # 操作延迟直方图（单位：秒）
        self.operation_latency = Histogram(
            f"{METRIC_NAMESPACE}_{METRIC_SUBSYSTEM}_operation_duration_seconds",
            "操作耗时分布",
            ["operation", "context_type"],
            buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
            registry=self._registry,
        )

        # 对象池操作延迟
        self.pool_latency = Histogram(
            f"{METRIC_NAMESPACE}_{METRIC_SUBSYSTEM}_pool_duration_seconds",
            "对象池操作耗时",
            ["operation"],  # operation: acquire/release
            buckets=(0.0001, 0.0005, 0.001, 0.005, 0.01, 0.05, 0.1),
            registry=self._registry,
        )

    def _init_gauges(self) -> None:
        """初始化仪表指标"""
        # 活跃上下文数量
        self.active_contexts = Gauge(
            f"{METRIC_NAMESPACE}_{METRIC_SUBSYSTEM}_active_contexts",
            "当前活跃的上下文数量",
            ["context_type"],
            registry=self._registry,
        )

        # 对象池状态
        self.pool_size = Gauge(
            f"{METRIC_NAMESPACE}_{METRIC_SUBSYSTEM}_pool_size",
            "对象池大小",
            ["pool_type"],  # pool_type: current/max
            registry=self._registry,
        )

        # 缓存命中率
        self.cache_hit_rate = Gauge(
            f"{METRIC_NAMESPACE}_{METRIC_SUBSYSTEM}_cache_hit_rate",
            "缓存命中率",
            ["cache_type"],
            registry=self._registry,
        )

    @property
    def enabled(self) -> bool:
        """检查监控是否启用"""
        return self._enabled

    @property
    def registry(self) -> Optional["CollectorRegistry"]:
        """获取指标注册表"""
        return self._registry if self._enabled else None

    def record_operation(
        self,
        operation: str,
        context_type: str,
        status: str = "success",
    ) -> None:
        """
        记录上下文操作

        Args:
            operation: 操作类型（create/read/update/delete）
            context_type: 上下文类型（task/async/pool等）
            status: 操作状态（success/error）
        """
        if not self._enabled:
            return

        self.context_operations.labels(
            operation=operation,
            context_type=context_type,
            status=status,
        ).inc()

    def record_cache_operation(
        self,
        operation: str,
        cache_type: str,
    ) -> None:
        """
        记录缓存操作

        Args:
            operation: 操作类型（hit/miss）
            cache_type: 缓存类型（memory/redis/file）
        """
        if not self._enabled:
            return

        self.cache_operations.labels(
            operation=operation,
            cache_type=cache_type,
        ).inc()

    def record_error(
        self,
        error_type: str,
        operation: str,
    ) -> None:
        """
        记录错误

        Args:
            error_type: 错误类型（validation/timeout/io等）
            operation: 发生错误的操作
        """
        if not self._enabled:
            return

        self.errors_total.labels(
            error_type=error_type,
            operation=operation,
        ).inc()

    def update_active_contexts(
        self,
        count: int,
        context_type: str = "task",
    ) -> None:
        """
        更新活跃上下文数量

        Args:
            count: 当前活跃数量
            context_type: 上下文类型
        """
        if not self._enabled:
            return

        self.active_contexts.labels(
            context_type=context_type,
        ).set(count)

    def update_pool_size(
        self,
        size: int,
        pool_type: str = "current",
    ) -> None:
        """
        更新对象池大小

        Args:
            size: 池大小
            pool_type: 池类型（current/max）
        """
        if not self._enabled:
            return

        self.pool_size.labels(
            pool_type=pool_type,
        ).set(size)

    def update_cache_hit_rate(
        self,
        rate: float,
        cache_type: str = "memory",
    ) -> None:
        """
        更新缓存命中率

        Args:
            rate: 命中率（0-1之间）
            cache_type: 缓存类型
        """
        if not self._enabled:
            return

        self.cache_hit_rate.labels(
            cache_type=cache_type,
        ).set(rate)

    @contextmanager
    def track_operation(
        self,
        operation: str,
        context_type: str = "task",
    ):
        """
        跟踪操作耗时

        Args:
            operation: 操作类型
            context_type: 上下文类型

        Yields:
            None

        Example:
            ```python
            with metrics.track_operation("create", "task"):
                context = await manager.create_context(...)
            ```
        """
        if not self._enabled:
            yield
            return

        start_time = time.time()
        try:
            yield
            # 记录成功操作
            self.record_operation(operation, context_type, "success")
        except Exception as e:
            # 记录失败操作
            self.record_operation(operation, context_type, "error")
            self.record_error(type(e).__name__, operation)
            raise
        finally:
            # 记录延迟
            duration = time.time() - start_time
            self.operation_latency.labels(
                operation=operation,
                context_type=context_type,
            ).observe(duration)

    @contextmanager
    def track_pool_operation(self, operation: str):
        """
        跟踪对象池操作耗时

        Args:
            operation: 操作类型（acquire/release）

        Yields:
            None
        """
        if not self._enabled:
            yield
            return

        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.pool_latency.labels(
                operation=operation,
            ).observe(duration)

    def get_metrics_summary(self) -> dict[str, Any]:
        """
        获取指标摘要（用于调试）

        Returns:
            Dict: 指标摘要
        """
        if not self._enabled:
            return {"enabled": False}

        # 注意：这里只返回简化的摘要，完整数据需要通过Prometheus查询
        return {
            "enabled": True,
            "registry_size": len(self._registry.describe()),
        }

    def reset(self) -> None:
        """重置所有指标（仅用于测试）"""
        if not self._enabled:
            return

        logger.warning("⚠️ 重置所有监控指标")
        # Prometheus指标不支持重置，需要重新创建实例
        self._init_counters()
        self._init_histograms()
        self._init_gauges()


# 全局指标实例
_global_metrics: Optional[ContextMetrics] = None
_metrics_lock = threading.Lock()


def get_metrics(registry: Optional["CollectorRegistry"] = None) -> ContextMetrics:
    """
    获取全局指标实例

    Args:
        registry: 可选的自定义注册表

    Returns:
        ContextMetrics: 全局指标实例
    """
    global _global_metrics

    with _metrics_lock:
        if _global_metrics is None:
            _global_metrics = ContextMetrics(registry=registry)
            logger.info("✅ 全局监控指标实例已创建")

        return _global_metrics


def get_metrics_registry() -> Optional["CollectorRegistry"]:
    """
    获取指标注册表

    Returns:
        CollectorRegistry: Prometheus注册表，如果未启用则返回None
    """
    metrics = get_metrics()
    return metrics.registry if metrics.enabled else None


# Metrics服务器
_metrics_server_thread: Optional[Any] = None
_metrics_server_port: int = 0


def start_metrics_server(port: int = 8000, addr: str = "0.0.0.0") -> bool:
    """
    启动Prometheus metrics HTTP服务器

    Args:
        port: 监听端口，默认8000
        addr: 绑定地址，默认0.0.0.0

    Returns:
        bool: 启动成功返回True
    """
    global _metrics_server_thread, _metrics_server_port

    if not PROMETHEUS_AVAILABLE:
        logger.error("❌ prometheus_client未安装，无法启动metrics服务器")
        return False

    try:
        # 禁用_created指标以减少标签基数
        disable_created_metrics()

        _metrics_server_thread = start_http_server(port, addr)
        _metrics_server_port = port

        logger.info(f"✅ Prometheus metrics服务器已启动: http://{addr}:{port}/metrics")
        return True

    except Exception as e:
        logger.error(f"❌ 启动metrics服务器失败: {e}")
        return False


def stop_metrics_server() -> None:
    """停止Prometheus metrics服务器"""
    global _metrics_server_thread, _metrics_server_port

    if _metrics_server_thread is not None:
        # Prometheus客户端的HTTP服务器没有提供优雅关闭方法
        # 这里只是重置引用
        _metrics_server_thread = None
        _metrics_server_port = 0
        logger.info("⚠️ Metrics服务器引用已清除（注意：线程可能仍在运行）")


__all__ = [
    "ContextMetrics",
    "get_metrics",
    "get_metrics_registry",
    "start_metrics_server",
    "stop_metrics_server",
]
