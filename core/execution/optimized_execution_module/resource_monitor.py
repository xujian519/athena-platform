#!/usr/bin/env python3
"""
优化版执行模块 - 资源监控器
Optimized Execution Module - Resource Monitor

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0
"""

import threading
import time
from collections import deque

import psutil

from core.logging_config import setup_logging

from .types import ResourceUsage

logger = setup_logging()


class ResourceMonitor:
    """资源监控器 - 实时监控系统资源使用情况"""

    def __init__(self):
        """初始化资源监控器"""
        self.cpu_usage_history = deque(maxlen=60)  # 保存60个历史数据点
        self.memory_usage_history = deque(maxlen=60)
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def _monitor_loop(self) -> None:
        """监控循环 - 后台线程持续采集资源使用数据"""
        while self.monitoring:
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()

                self.cpu_usage_history.append(cpu_percent / 100.0)
                self.memory_usage_history.append(memory.used / memory.total)

            except Exception as e:
                logger.error(f"资源监控异常: {e}")

            time.sleep(1)

    def get_current_usage(self) -> ResourceUsage:
        """获取当前资源使用情况

        Returns:
            当前资源使用情况对象
        """
        try:
            return ResourceUsage(
                cpu_cores=psutil.cpu_count()
                * (self.cpu_usage_history[-1] if self.cpu_usage_history else 0.1),
                memory_mb=psutil.virtual_memory().used / (1024 * 1024),
                disk_io_mb_s=(
                    psutil.disk_io_counters().read_bytes / (1024 * 1024)
                    if psutil.disk_io_counters()
                    else 0
                ),
                network_mbps=(
                    psutil.net_io_counters().bytes_recv / (1024 * 1024)
                    if psutil.net_io_counters()
                    else 0
                ),
            )
        except Exception:
            return ResourceUsage()

    def get_average_usage(self, minutes: int = 5) -> ResourceUsage:
        """获取平均资源使用情况

        Args:
            minutes: 计算平均值的时长(分钟)

        Returns:
            平均资源使用情况对象
        """
        points = min(minutes * 60, len(self.cpu_usage_history))
        if points == 0:
            return ResourceUsage()

        avg_cpu = sum(list(self.cpu_usage_history)[-points:]) / points
        avg_memory = sum(list(self.memory_usage_history)[-points:]) / points

        return ResourceUsage(
            cpu_cores=psutil.cpu_count() * avg_cpu,
            memory_mb=psutil.virtual_memory().total / (1024 * 1024) * avg_memory,
        )

    def stop(self) -> None:
        """停止监控"""
        self.monitoring = False
