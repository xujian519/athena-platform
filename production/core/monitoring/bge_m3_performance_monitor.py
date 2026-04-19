#!/usr/bin/env python3
from __future__ import annotations
"""
BGE-M3性能监控系统
Performance Monitor for BGE-M3

监控BGE-M3模型的性能指标,包括吞吐量、延迟、资源使用等
"""

import threading
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import psutil

from core.logging_config import setup_logging

logger = setup_logging()


@dataclass
class PerformanceMetric:
    """性能指标"""

    timestamp: datetime
    operation: str  # encode, encode_batch, load_model, etc.
    duration: float  # 秒
    batch_size: int = 1
    text_length: int = 0
    token_count: int = 0
    success: bool = True
    error_message: str = ""


@dataclass
class PerformanceStats:
    """性能统计"""

    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    total_duration: float = 0.0
    avg_duration: float = 0.0
    min_duration: float = float("inf")
    max_duration: float = 0.0
    p50_duration: float = 0.0
    p95_duration: float = 0.0
    p99_duration: float = 0.0
    throughput_per_second: float = 0.0
    avg_texts_per_second: float = 0.0
    avg_tokens_per_second: float = 0.0


@dataclass
class ResourceUsage:
    """资源使用情况"""

    timestamp: datetime
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    gpu_memory_mb: float = 0.0


class BGE_M3_PerformanceMonitor:
    """BGE-M3性能监控器"""

    def __init__(
        self,
        max_history: int = 10000,
        monitoring_interval: int = 60,
        alert_thresholds: dict[str, float] | None = None,
    ):
        """初始化监控器

        Args:
            max_history: 最大历史记录数
            monitoring_interval: 资源监控间隔(秒)
            alert_thresholds: 告警阈值
        """
        self.max_history = max_history
        self.monitoring_interval = monitoring_interval

        # 告警阈值
        self.alert_thresholds = alert_thresholds or {
            "avg_duration": 5.0,  # 平均处理时间超过5秒
            "error_rate": 0.05,  # 错误率超过5%
            "memory_percent": 90,  # 内存使用超过90%
            "cpu_percent": 95,  # CPU使用超过95%
        }

        # 指标存储
        self.metrics: deque = deque(maxlen=max_history)
        self.resource_metrics: deque = deque(maxlen=1000)

        # 监控线程
        self.monitoring_thread: threading.Thread | None = None
        self.is_monitoring = False

        # 统计缓存
        self._stats_cache: PerformanceStats | None = None
        self._stats_cache_time: datetime | None = None
        self._cache_ttl = timedelta(seconds=10)

    def start_monitoring(self) -> Any:
        """启动资源监控"""
        if self.is_monitoring:
            logger.warning("⚠️  监控已在运行")
            return

        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(
            target=self._monitor_resources,
            daemon=True,
        )
        self.monitoring_thread.start()
        logger.info("✅ 性能监控已启动")

    def stop_monitoring(self) -> Any:
        """停止资源监控"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("⏸️  性能监控已停止")

    def _monitor_resources(self) -> Any:
        """资源监控线程"""
        while self.is_monitoring:
            try:
                # 获取CPU和内存使用
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()

                # 尝试获取GPU内存(如果有)
                gpu_memory_mb = 0.0
                try:
                    import torch

                    if torch.cuda.is_available():
                        gpu_memory_mb = torch.cuda.memory_allocated() / 1024 / 1024
                except Exception as e:
                    logger.debug(f"空except块已触发: {e}")
                    pass

                # 记录资源使用
                resource_usage = ResourceUsage(
                    timestamp=datetime.now(),
                    cpu_percent=cpu_percent,
                    memory_mb=memory.used / 1024 / 1024,
                    memory_percent=memory.percent,
                    gpu_memory_mb=gpu_memory_mb,
                )

                self.resource_metrics.append(resource_usage)

                # 检查告警
                self._check_resource_alerts(resource_usage)

            except Exception as e:
                logger.error(f"❌ 资源监控错误: {e}")

            # 等待下一次监控
            time.sleep(self.monitoring_interval)

    def _check_resource_alerts(self, usage: ResourceUsage) -> Any:
        """检查资源告警

        Args:
            usage: 资源使用情况
        """
        if usage.memory_percent > self.alert_thresholds["memory_percent"]:
            logger.warning(
                f"⚠️  内存使用过高: {usage.memory_percent:.1f}% "
                f">(阈值: {self.alert_thresholds['memory_percent']}%)"
            )

        if usage.cpu_percent > self.alert_thresholds["cpu_percent"]:
            logger.warning(
                f"⚠️  CPU使用过高: {usage.cpu_percent:.1f}% "
                f">(阈值: {self.alert_thresholds['cpu_percent']}%)"
            )

    def record_metric(self, metric: PerformanceMetric) -> Any:
        """记录性能指标

        Args:
            metric: 性能指标
        """
        self.metrics.append(metric)
        self._stats_cache = None  # 清除缓存

        # 检查告警
        if not metric.success:
            logger.error(f"❌ 操作失败: {metric.operation} - {metric.error_message}")

    def record_operation(
        self,
        operation: str,
        duration: float,
        batch_size: int = 1,
        text_length: int = 0,
        token_count: int = 0,
        success: bool = True,
        error_message: str = "",
    ):
        """记录操作的便捷函数

        Args:
            operation: 操作名称
            duration: 持续时间(秒)
            batch_size: 批次大小
            text_length: 文本长度
            token_count: token数量
            success: 是否成功
            error_message: 错误信息
        """
        metric = PerformanceMetric(
            timestamp=datetime.now(),
            operation=operation,
            duration=duration,
            batch_size=batch_size,
            text_length=text_length,
            token_count=token_count,
            success=success,
            error_message=error_message,
        )
        self.record_metric(metric)

    def calculate_stats(
        self,
        operation: str | None = None,
        time_window: timedelta | None = None,
    ) -> PerformanceStats:
        """计算性能统计

        Args:
            operation: 过滤操作类型(None表示所有)
            time_window: 时间窗口(None表示全部)

        Returns:
            性能统计
        """
        # 检查缓存
        if (
            self._stats_cache is not None
            and self._stats_cache_time is not None
            and datetime.now() - self._stats_cache_time < self._cache_ttl
            and operation is None
            and time_window is None
        ):
            return self._stats_cache

        # 过滤指标
        filtered_metrics = list(self.metrics)

        if operation:
            filtered_metrics = [m for m in filtered_metrics if m.operation == operation]

        if time_window:
            cutoff_time = datetime.now() - time_window
            filtered_metrics = [m for m in filtered_metrics if m.timestamp >= cutoff_time]

        if not filtered_metrics:
            return PerformanceStats()

        # 计算统计
        stats = PerformanceStats(
            total_operations=len(filtered_metrics),
            successful_operations=sum(1 for m in filtered_metrics if m.success),
            failed_operations=sum(1 for m in filtered_metrics if not m.success),
            total_duration=sum(m.duration for m in filtered_metrics),
        )

        durations = [m.duration for m in filtered_metrics]
        stats.min_duration = min(durations)
        stats.max_duration = max(durations)
        stats.avg_duration = stats.total_duration / stats.total_operations

        # 百分位数
        sorted_durations = sorted(durations)
        stats.p50_duration = np.percentile(sorted_durations, 50)
        stats.p95_duration = np.percentile(sorted_durations, 95)
        stats.p99_duration = np.percentile(sorted_durations, 99)

        # 吞吐量
        time_span = (filtered_metrics[-1].timestamp - filtered_metrics[0].timestamp).total_seconds()

        if time_span > 0:
            stats.throughput_per_second = stats.total_operations / time_span
            stats.avg_texts_per_second = sum(m.batch_size for m in filtered_metrics) / time_span
            stats.avg_tokens_per_second = sum(m.token_count for m in filtered_metrics) / time_span

        # 缓存结果
        if operation is None and time_window is None:
            self._stats_cache = stats
            self._stats_cache_time = datetime.now()

        return stats

    def get_recent_stats(
        self,
        minutes: int = 5,
        operation: str | None = None,
    ) -> PerformanceStats:
        """获取最近的性能统计

        Args:
            minutes: 时间窗口(分钟)
            operation: 操作类型

        Returns:
            性能统计
        """
        return self.calculate_stats(
            operation=operation,
            time_window=timedelta(minutes=minutes),
        )

    def get_resource_stats(
        self,
        minutes: int = 5,
    ) -> dict[str, Any]:
        """获取资源使用统计

        Args:
            minutes: 时间窗口(分钟)

        Returns:
            资源统计
        """
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_metrics = [m for m in self.resource_metrics if m.timestamp >= cutoff_time]

        if not recent_metrics:
            return {}

        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_mb for m in recent_metrics]
        memory_percent_values = [m.memory_percent for m in recent_metrics]
        gpu_values = [m.gpu_memory_mb for m in recent_metrics if m.gpu_memory_mb > 0]

        return {
            "cpu": {
                "avg": np.mean(cpu_values),
                "max": np.max(cpu_values),
                "min": np.min(cpu_values),
            },
            "memory_mb": {
                "avg": np.mean(memory_values),
                "max": np.max(memory_values),
                "min": np.min(memory_values),
            },
            "memory_percent": {
                "avg": np.mean(memory_percent_values),
                "max": np.max(memory_percent_values),
                "min": np.min(memory_percent_values),
            },
            "gpu_memory_mb": {
                "avg": np.mean(gpu_values) if gpu_values else 0,
                "max": np.max(gpu_values) if gpu_values else 0,
            },
            "sample_count": len(recent_metrics),
        }

    def print_report(
        self,
        time_window: timedelta | None = None,
        include_resources: bool = True,
    ):
        """打印性能报告

        Args:
            time_window: 时间窗口
            include_resources: 是否包含资源使用
        """
        stats = self.calculate_stats(time_window=time_window)

        logger.info("\n" + "=" * 70)
        logger.info("📊 BGE-M3 性能监控报告")
        logger.info("=" * 70)

        if time_window:
            logger.info(f"⏱️  时间窗口: {time_window}")
        logger.info(f"📅 统计时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        logger.info("\n🔄 操作统计:")
        logger.info(f"  总操作数: {stats.total_operations}")
        logger.info(f"  ✅ 成功: {stats.successful_operations}")
        logger.info(f"  ❌ 失败: {stats.failed_operations}")
        if stats.total_operations > 0:
            error_rate = stats.failed_operations / stats.total_operations
            logger.info(f"  📊 错误率: {error_rate:.2%}")

        logger.info("\n⏱️  延迟统计 (秒):")
        logger.info(f"  平均: {stats.avg_duration:.3f}s")
        logger.info(f"  最小: {stats.min_duration:.3f}s")
        logger.info(f"  最大: {stats.max_duration:.3f}s")
        logger.info(f"  P50: {stats.p50_duration:.3f}s")
        logger.info(f"  P95: {stats.p95_duration:.3f}s")
        logger.info(f"  P99: {stats.p99_duration:.3f}s")

        logger.info("\n⚡ 吞吐量统计:")
        logger.info(f"  操作/秒: {stats.throughput_per_second:.2f}")
        logger.info(f"  文本/秒: {stats.avg_texts_per_second:.2f}")
        logger.info(f"  tokens/秒: {stats.avg_tokens_per_second:.0f}")

        if include_resources:
            logger.info("\n💻 资源使用:")
            resource_stats = self.get_resource_stats(minutes=5)
            if resource_stats:
                logger.info(
                    f"  CPU: {resource_stats['cpu']['avg']:.1f}% "
                    f"(最大: {resource_stats['cpu']['max']:.1f}%)"
                )
                logger.info(
                    f"  内存: {resource_stats['memory_mb']['avg']:.0f}MB "
                    f"(最大: {resource_stats['memory_mb']['max']:.0f}MB)"
                )
                logger.info(
                    f"  内存使用率: {resource_stats['memory_percent']['avg']:.1f}% "
                    f"(最大: {resource_stats['memory_percent']['max']:.1f}%)"
                )
                if resource_stats["gpu_memory_mb"]["max"] > 0:
                    logger.info(
                        f"  GPU内存: {resource_stats['gpu_memory_mb']['avg']:.0f}MB "
                        f"(最大: {resource_stats['gpu_memory_mb']['max']:.0f}MB)"
                    )

        logger.info("=" * 70 + "\n")


# 全局监控器实例
_global_monitor: BGE_M3_PerformanceMonitor | None = None


def get_performance_monitor() -> BGE_M3_PerformanceMonitor:
    """获取全局性能监控器实例

    Returns:
        性能监控器实例
    """
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = BGE_M3_PerformanceMonitor()
    return _global_monitor


if __name__ == "__main__":
    # 测试监控器
    # setup_logging()  # 日志配置已移至模块导入

    monitor = get_performance_monitor()
    monitor.start_monitoring()

    # 模拟一些操作
    logger.info("🔄 模拟操作...")

    for _i in range(10):
        import random

        time.sleep(random.uniform(0.1, 0.5))
        monitor.record_operation(
            operation="encode",
            duration=random.uniform(0.1, 0.5),
            batch_size=random.randint(1, 10),
            token_count=random.randint(50, 500),
            success=random.random() > 0.1,  # 10%失败率
        )

    # 打印报告
    monitor.print_report()

    monitor.stop_monitoring()
