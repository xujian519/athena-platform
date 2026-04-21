#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记忆系统性能监控器
Memory System Performance Monitor

提供全面的性能监控、指标收集和分析功能

作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import asyncio
import json
import logging
import os
import threading
import time
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import numpy as np
import psutil

from .memory_error_handler import get_logger, handle_memory_error, safe_execute

logger = get_logger(__name__)

@dataclass
class PerformanceMetric:
    """性能指标"""
    name: str
    value: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.now)
    component: str = 'unknown'
    tags: Dict[str, Any] = field(default_factory=dict)

@dataclass
class OperationMetrics:
    """操作指标"""
    operation_name: str
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    total_duration: float = 0.0
    min_duration: float = float('inf')
    max_duration: float = 0.0
    last_operation_time: datetime | None = None
    error_rate: float = 0.0
    average_duration: float = 0.0

    def update(self, duration: float, success: bool = True):
        """更新指标"""
        self.total_operations += 1
        self.total_duration += duration
        self.last_operation_time = datetime.now()

        if success:
            self.successful_operations += 1
        else:
            self.failed_operations += 1

        # 更新最小和最大时间
        self.min_duration = min(self.min_duration, duration)
        self.max_duration = max(self.max_duration, duration)

        # 计算平均值和错误率
        if self.total_operations > 0:
            self.average_duration = self.total_duration / self.total_operations
            self.error_rate = self.failed_operations / self.total_operations

@dataclass
class ResourceMetrics:
    """资源指标"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    network_bytes_sent: int
    network_bytes_recv: int
    timestamp: datetime = field(default_factory=datetime.now)

class MemoryPerformanceMonitor:
    """记忆系统性能监控器"""

    def __init__(self, monitoring_interval: int = 30, metrics_history_size: int = 1000):
        self.monitoring_interval = monitoring_interval
        self.metrics_history_size = metrics_history_size

        # 监控状态
        self.is_monitoring = False
        self.monitoring_task: asyncio.Task | None = None

        # 指标存储
        self.operation_metrics: Dict[str, OperationMetrics] = {}
        self.resource_metrics: deque = deque(maxlen=metrics_history_size)
        self.custom_metrics: deque = deque(maxlen=metrics_history_size)

        # 性能阈值
        self.thresholds = {
            'cpu_warning': 70.0,
            'cpu_critical': 90.0,
            'memory_warning': 75.0,
            'memory_critical': 90.0,
            'response_time_warning': 1.0,
            'response_time_critical': 5.0,
            'error_rate_warning': 0.05,
            'error_rate_critical': 0.1
        }

        # 回调函数
        self.alert_callbacks: List[Callable] = []

        # 统计信息
        self.start_time = datetime.now()
        self.peak_cpu = 0.0
        self.peak_memory = 0.0

        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix='perf_monitor')

        logger.log_performance('monitor_init', 1.0, 'instance', {
            'monitoring_interval': monitoring_interval,
            'history_size': metrics_history_size
        })

    @handle_memory_error
    async def start_monitoring(self):
        """开始性能监控"""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())

        logger.log_operation('性能监控启动')
        logger.info('🚀 性能监控已启动')

    @handle_memory_error
    async def stop_monitoring(self):
        """停止性能监控"""
        if not self.is_monitoring:
            return

        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass

        logger.log_operation('性能监控停止')
        logger.info('⏹️ 性能监控已停止')

    async def _monitoring_loop(self):
        """监控循环"""
        while self.is_monitoring:
            try:
                # 收集资源指标
                await self._collect_resource_metrics()

                # 检查性能阈值
                self._check_performance_thresholds()

                # 等待下次监控
                await asyncio.sleep(self.monitoring_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.logger.error(f"监控循环错误: {e}")
                await asyncio.sleep(5)

    async def _collect_resource_metrics(self):
        """收集资源指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)

            # 内存使用
            memory = psutil.virtual_memory()
            memory_used_mb = memory.used / (1024 * 1024)
            memory_available_mb = memory.available / (1024 * 1024)

            # 磁盘使用
            disk = psutil.disk_usage('/')
            disk_usage_percent = disk.percent

            # 网络使用
            network = psutil.net_io_counters()

            # 创建资源指标
            resource_metric = ResourceMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory_used_mb,
                memory_available_mb=memory_available_mb,
                disk_usage_percent=disk_usage_percent,
                network_bytes_sent=network.bytes_sent,
                network_bytes_recv=network.bytes_recv
            )

            self.resource_metrics.append(resource_metric)

            # 更新峰值
            self.peak_cpu = max(self.peak_cpu, cpu_percent)
            self.peak_memory = max(self.peak_memory, memory.percent)

        except Exception as e:
            logger.logger.error(f"收集资源指标失败: {e}")

    def _check_performance_thresholds(self):
        """检查性能阈值"""
        if not self.resource_metrics:
            return

        latest = self.resource_metrics[-1]

        # 检查CPU阈值
        if latest.cpu_percent >= self.thresholds['cpu_critical']:
            self._trigger_alert('cpu_critical', f"CPU使用率过高: {latest.cpu_percent:.1f}%")
        elif latest.cpu_percent >= self.thresholds['cpu_warning']:
            self._trigger_alert('cpu_warning', f"CPU使用率警告: {latest.cpu_percent:.1f}%")

        # 检查内存阈值
        if latest.memory_percent >= self.thresholds['memory_critical']:
            self._trigger_alert('memory_critical', f"内存使用率过高: {latest.memory_percent:.1f}%")
        elif latest.memory_percent >= self.thresholds['memory_warning']:
            self._trigger_alert('memory_warning', f"内存使用率警告: {latest.memory_percent:.1f}%")

        # 检查操作错误率
        for operation_name, metrics in self.operation_metrics.items():
            if metrics.error_rate >= self.thresholds['error_rate_critical']:
                self._trigger_alert('error_rate_critical',
                    f"操作 {operation_name} 错误率过高: {metrics.error_rate:.2%}")
            elif metrics.error_rate >= self.thresholds['error_rate_warning']:
                self._trigger_alert('error_rate_warning',
                    f"操作 {operation_name} 错误率警告: {metrics.error_rate:.2%}")

            if metrics.average_duration >= self.thresholds['response_time_critical']:
                self._trigger_alert('response_time_critical',
                    f"操作 {operation_name} 响应时间过长: {metrics.average_duration:.3f}s")
            elif metrics.average_duration >= self.thresholds['response_time_warning']:
                self._trigger_alert('response_time_warning',
                    f"操作 {operation_name} 响应时间警告: {metrics.average_duration:.3f}s")

    def _trigger_alert(self, alert_type: str, message: str):
        """触发告警"""
        alert_data = {
            'type': alert_type,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'metrics': self.get_current_metrics()
        }

        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    asyncio.create_task(callback(alert_data))
                else:
                    # 在线程池中执行同步回调
                    self.executor.submit(callback, alert_data)
            except Exception as e:
                logger.logger.error(f"执行告警回调失败: {e}")

        logger.logger.warning(f"⚠️ 性能告警: {message}")

    def record_operation(self, operation_name: str, duration: float,
                        success: bool = True, tags: Dict[str, Any] = None):
        """记录操作指标"""
        if operation_name not in self.operation_metrics:
            self.operation_metrics[operation_name] = OperationMetrics(operation_name)

        self.operation_metrics[operation_name].update(duration, success)

        # 记录自定义指标
        metric = PerformanceMetric(
            name=f"{operation_name}_duration",
            value=duration,
            unit='seconds',
            component=operation_name,
            tags=tags or {}
        )
        self.custom_metrics.append(metric)

    def record_metric(self, name: str, value: float, unit: str = '',
                     component: str = 'unknown', tags: Dict[str, Any] = None):
        """记录自定义指标"""
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            component=component,
            tags=tags or {}
        )
        self.custom_metrics.append(metric)

    def add_alert_callback(self, callback: Callable):
        """添加告警回调"""
        self.alert_callbacks.append(callback)

    def remove_alert_callback(self, callback: Callable):
        """移除告警回调"""
        if callback in self.alert_callbacks:
            self.alert_callbacks.remove(callback)

    def get_operation_metrics(self, operation_name: str = None) -> Dict[str, Any]:
        """获取操作指标"""
        if operation_name:
            if operation_name in self.operation_metrics:
                metrics = self.operation_metrics[operation_name]
                return asdict(metrics)
            else:
                return {}
        else:
            return {name: asdict(metrics) for name, metrics in self.operation_metrics.items()}

    def get_resource_metrics(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取资源指标"""
        metrics_list = list(self.resource_metrics)
        if limit:
            metrics_list = metrics_list[-limit:]

        return [asdict(metric) for metric in metrics_list]

    def get_custom_metrics(self, metric_name: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """获取自定义指标"""
        metrics_list = list(self.custom_metrics)

        if metric_name:
            metrics_list = [m for m in metrics_list if m.name == metric_name]

        if limit:
            metrics_list = metrics_list[-limit:]

        return [asdict(metric) for metric in metrics_list]

    def get_current_metrics(self) -> Dict[str, Any]:
        """获取当前性能指标"""
        current_time = datetime.now()
        uptime = (current_time - self.start_time).total_seconds()

        # 获取最新的资源指标
        latest_resource = self.resource_metrics[-1] if self.resource_metrics else None

        result = {
            'uptime_seconds': uptime,
            'peak_cpu': self.peak_cpu,
            'peak_memory': self.peak_memory,
            'monitoring_active': self.is_monitoring,
            'operations_count': len(self.operation_metrics),
            'resource_metrics': asdict(latest_resource) if latest_resource else None,
            'timestamp': current_time.isoformat()
        }

        # 添加操作统计
        total_operations = sum(m.total_operations for m in self.operation_metrics.values())
        total_errors = sum(m.failed_operations for m in self.operation_metrics.values())

        result['operations_summary'] = {
            'total_operations': total_operations,
            'total_errors': total_errors,
            'overall_error_rate': total_errors / max(total_operations, 1),
            'active_operations': len([m for m in self.operation_metrics.values()
                                     if m.last_operation_time and
                                     (current_time - m.last_operation_time).total_seconds() < 300])
        }

        return result

    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        if not self.resource_metrics:
            return {'status': 'no_data'}

        recent_metrics = list(self.resource_metrics)[-60:]  # 最近60个数据点

        # 计算平均值
        avg_cpu = np.mean([m.cpu_percent for m in recent_metrics])
        avg_memory = np.mean([m.memory_percent for m in recent_metrics])

        # 计算趋势
        if len(recent_metrics) >= 2:
            cpu_trend = recent_metrics[-1].cpu_percent - recent_metrics[0].cpu_percent
            memory_trend = recent_metrics[-1].memory_percent - recent_metrics[0].memory_percent
        else:
            cpu_trend = 0
            memory_trend = 0

        # 找出最慢的操作
        slowest_operations = []
        for name, metrics in self.operation_metrics.items():
            if metrics.total_operations > 0:
                slowest_operations.append({
                    'operation': name,
                    'avg_duration': metrics.average_duration,
                    'max_duration': metrics.max_duration,
                    'total_operations': metrics.total_operations,
                    'error_rate': metrics.error_rate
                })

        slowest_operations.sort(key=lambda x: x['avg_duration'], reverse=True)
        slowest_operations = slowest_operations[:5]

        return {
            'period': f"最近 {len(recent_metrics) * self.monitoring_interval} 秒",
            'average_cpu': avg_cpu,
            'average_memory': avg_memory,
            'cpu_trend': cpu_trend,
            'memory_trend': memory_trend,
            'slowest_operations': slowest_operations,
            'total_metrics_collected': len(self.custom_metrics),
            'monitoring_uptime': (datetime.now() - self.start_time).total_seconds()
        }

    def export_metrics(self, file_path: str, format: str = 'json'):
        """导出指标数据"""
        data = {
            'export_time': datetime.now().isoformat(),
            'performance_summary': self.get_performance_summary(),
            'current_metrics': self.get_current_metrics(),
            'operation_metrics': self.get_operation_metrics(),
            'resource_metrics': self.get_resource_metrics(),
            'custom_metrics': self.get_custom_metrics()
        }

        # 创建目录
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        try:
            if format.lower() == 'json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            else:
                # 简单的CSV导出
                import csv
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    if self.resource_metrics:
                        writer = csv.DictWriter(f, fieldnames=[
                            'timestamp', 'cpu_percent', 'memory_percent',
                            'memory_used_mb', 'disk_usage_percent'
                        ])
                        writer.writeheader()

                        for metric in self.resource_metrics:
                            writer.writerow({
                                'timestamp': metric.timestamp.isoformat(),
                                'cpu_percent': metric.cpu_percent,
                                'memory_percent': metric.memory_percent,
                                'memory_used_mb': metric.memory_used_mb,
                                'disk_usage_percent': metric.disk_usage_percent
                            })

            logger.log_operation(f"性能指标导出', details={'file': file_path, 'format": format})
            logger.info(f"📊 性能指标已导出到: {file_path}")

        except Exception as e:
            logger.logger.error(f"导出指标失败: {e}")
            raise

    def reset_metrics(self):
        """重置指标"""
        self.operation_metrics.clear()
        self.resource_metrics.clear()
        self.custom_metrics.clear()
        self.start_time = datetime.now()
        self.peak_cpu = 0.0
        self.peak_memory = 0.0

        logger.log_operation('性能指标重置')

    def set_threshold(self, metric_type: str, warning: float, critical: float):
        """设置性能阈值"""
        if f"{metric_type}_warning" in self.thresholds:
            self.thresholds[f"{metric_type}_warning"] = warning
            self.thresholds[f"{metric_type}_critical"] = critical
            logger.log_performance('threshold_update', 1.0, 'set', {
                'metric_type': metric_type,
                'warning': warning,
                'critical': critical
            })
        else:
            raise ValueError(f"未知的指标类型: {metric_type}")

# 全局性能监控器实例
_global_monitor: MemoryPerformanceMonitor | None = None

def get_performance_monitor(monitoring_interval: int = 30) -> MemoryPerformanceMonitor:
    """获取全局性能监控器实例"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = MemoryPerformanceMonitor(monitoring_interval)
    return _global_monitor

async def start_monitoring(monitoring_interval: int = 30):
    """启动全局性能监控"""
    monitor = get_performance_monitor(monitoring_interval)
    await monitor.start_monitoring()

async def stop_monitoring():
    """停止全局性能监控"""
    global _global_monitor
    if _global_monitor:
        await _global_monitor.stop_monitoring()

def record_operation(operation_name: str, duration: float, success: bool = True):
    """记录操作指标"""
    monitor = get_performance_monitor()
    monitor.record_operation(operation_name, duration, success)

def record_metric(name: str, value: float, unit: str = '', component: str = 'unknown'):
    """记录自定义指标"""
    monitor = get_performance_monitor()
    monitor.record_metric(name, value, unit, component)

# 性能监控装饰器
def monitor_performance(operation_name: str = None):
    """性能监控装饰器"""
    def decorator(func: Callable) -> Callable:
        op_name = operation_name or f"{func.__module__}.{func.__name__}"

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            success = True

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise
            finally:
                duration = time.time() - start_time
                record_operation(op_name, duration, success)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            success = True

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise
            finally:
                duration = time.time() - start_time
                record_operation(op_name, duration, success)

        # 判断是否是异步函数
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator

# 需要导入functools
import functools
