"""
伦理框架性能监控模块
Ethics Framework Performance Monitoring

提供性能指标收集、分析和报告功能
"""

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict, Optional

from .evaluator import EthicsEvaluator, EvaluationResult


@dataclass
class PerformanceMetrics:
    """性能指标"""

    operation_name: str
    total_calls: int = 0
    total_time: float = 0.0
    min_time: float = float("inf")
    max_time: float = 0.0
    avg_time: float = 0.0
    p50_time: float = 0.0
    p95_time: float = 0.0
    p99_time: float = 0.0
    error_count: int = 0
    last_reset: datetime = field(default_factory=datetime.now)

    def add_measurement(self, duration: float, success: bool = True) -> None:
        """添加测量点"""
        self.total_calls += 1
        self.total_time += duration

        if duration < self.min_time:
            self.min_time = duration
        if duration > self.max_time:
            self.max_time = duration

        self.avg_time = self.total_time / self.total_calls

        if not success:
            self.error_count += 1


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self):
        self.metrics: dict[str, PerformanceMetrics] = {}
        self._lock = threading.Lock()
        self._measurement_history: dict[str, list] = {}

    def track(self, operation_name: str) -> Any:
        """装饰器:跟踪函数性能"""

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    self.record(operation_name, duration, success=True)
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    self.record(operation_name, duration, success=False)
                    raise e

            return wrapper

        return decorator

    def record(self, operation_name: str, duration: float, success: bool = True) -> Any:
        """记录性能数据"""
        with self._lock:
            if operation_name not in self.metrics:
                self.metrics[operation_name] = PerformanceMetrics(operation_name)

            self.metrics[operation_name].add_measurement(duration, success)

            # 记录历史用于百分位计算
            if operation_name not in self._measurement_history:
                self._measurement_history[operation_name] = []
            self._measurement_history[operation_name].append(duration)

            # 限制历史大小
            if len(self._measurement_history[operation_name]) > 1000:
                self._measurement_history[operation_name] = self._measurement_history[
                    operation_name
                ][-1000:]

            # 更新百分位数
            self._update_percentiles(operation_name)

    def _update_percentiles(self, operation_name: str) -> Any:
        """更新百分位数"""
        if operation_name not in self._measurement_history:
            return

        history = self._measurement_history[operation_name]
        if not history:
            return

        sorted_times = sorted(history)
        n = len(sorted_times)

        self.metrics[operation_name].p50_time = sorted_times[int(n * 0.5)]
        self.metrics[operation_name].p95_time = sorted_times[int(n * 0.95)]
        self.metrics[operation_name].p99_time = sorted_times[int(n * 0.99)]

    def get_metrics(self, operation_name: str) -> PerformanceMetrics | None:
        """获取特定操作的指标"""
        return self.metrics.get(operation_name)

    def get_all_metrics(self) -> dict[str, PerformanceMetrics]:
        """获取所有指标"""
        return self.metrics.copy()

    def get_summary(self) -> dict[str, Any]:
        """获取摘要"""
        summary = {"total_operations": len(self.metrics), "operations": {}}

        for name, metrics in self.metrics.items():
            summary["operations"][name] = {
                "total_calls": metrics.total_calls,
                "avg_time_ms": metrics.avg_time * 1000,
                "min_time_ms": metrics.min_time * 1000 if metrics.min_time != float("inf") else 0,
                "max_time_ms": metrics.max_time * 1000,
                "p95_time_ms": metrics.p95_time * 1000,
                "p99_time_ms": metrics.p99_time * 1000,
                "error_rate": (
                    metrics.error_count / metrics.total_calls if metrics.total_calls > 0 else 0
                ),
            }

        return summary

    def reset(self, operation_name: str | None = None) -> Any:
        """重置指标"""
        with self._lock:
            if operation_name:
                if operation_name in self.metrics:
                    del self.metrics[operation_name]
                if operation_name in self._measurement_history:
                    del self._measurement_history[operation_name]
            else:
                self.metrics.clear()
                self._measurement_history.clear()


# 全局性能监控器实例
_global_monitor = None


def get_performance_monitor() -> PerformanceMonitor:
    """获取全局性能监控器"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
    return _global_monitor


def monitor_performance(operation_name: str) -> Any:
    """便捷的性能监控装饰器"""
    return get_performance_monitor().track(operation_name)


class EthicsEvaluatorWithMonitoring(EthicsEvaluator):
    """带性能监控的伦理评估器"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.performance_monitor = get_performance_monitor()

    def evaluate_action(self, agent_id: str, action: str, context=None) -> EvaluationResult:
        """评估行动(带性能监控)"""
        operation_name = f"evaluate_action.{agent_id}"

        start_time = time.time()
        try:
            result = super().evaluate_action(agent_id, action, context)
            duration = time.time() - start_time
            self.performance_monitor.record(operation_name, duration, success=True)
            return result
        except Exception as e:
            duration = time.time() - start_time
            self.performance_monitor.record(operation_name, duration, success=False)
            raise e

    def get_performance_report(self) -> dict[str, Any]:
        """获取性能报告"""
        return self.performance_monitor.get_summary()
