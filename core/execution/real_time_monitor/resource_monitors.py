#!/usr/bin/env python3
"""
实时执行监控系统 - 资源监控器
Real-time Execution Monitoring System - Resource Monitors

作者: Athena AI系统
创建时间: 2025-12-04
重构时间: 2026-01-27
版本: 2.0.0
"""

import time

import psutil

from .types import ResourceStatus


class ResourceMonitor:
    """资源监控器基类"""

    def __init__(self, name: str):
        """初始化资源监控器

        Args:
            name: 监控器名称
        """
        self.name = name
        self.history = []  # 保留最近1000个数据点
        self.max_history = 1000
        self.last_check = time.time()

    async def check(self) -> float:
        """检查资源使用率

        Returns:
            资源使用率值
        """
        raise NotImplementedError

    def get_status(
        self, threshold_warning: float = 0.8, threshold_critical: float = 0.95
    ) -> ResourceStatus:
        """获取资源状态

        Args:
            threshold_warning: 警告阈值
            threshold_critical: 严重阈值

        Returns:
            资源状态
        """
        if not self.history:
            return ResourceStatus.UNKNOWN

        latest_value = self.history[-1]

        if latest_value >= threshold_critical:
            return ResourceStatus.CRITICAL
        elif latest_value >= threshold_warning:
            return ResourceStatus.WARNING
        else:
            return ResourceStatus.HEALTHY


class CPUMonitor(ResourceMonitor):
    """CPU监控器"""

    def __init__(self):
        """初始化CPU监控器"""
        super().__init__("cpu")

    async def check(self) -> float:
        """检查CPU使用率

        Returns:
            CPU使用率百分比
        """
        cpu_percent = psutil.cpu_percent(interval=0.1)
        self._add_to_history(cpu_percent)
        return cpu_percent

    def _add_to_history(self, value: float):
        """添加值到历史记录"""
        self.history.append(value)
        if len(self.history) > self.max_history:
            self.history.pop(0)


class MemoryMonitor(ResourceMonitor):
    """内存监控器"""

    def __init__(self):
        """初始化内存监控器"""
        super().__init__("memory")

    async def check(self) -> float:
        """检查内存使用率

        Returns:
            内存使用率百分比
        """
        memory = psutil.virtual_memory()
        self._add_to_history(memory.percent)
        return memory.percent

    def _add_to_history(self, value: float):
        """添加值到历史记录"""
        self.history.append(value)
        if len(self.history) > self.max_history:
            self.history.pop(0)


class DiskMonitor(ResourceMonitor):
    """磁盘监控器"""

    def __init__(self):
        """初始化磁盘监控器"""
        super().__init__("disk")

    async def check(self) -> float:
        """检查磁盘使用率

        Returns:
            磁盘使用率百分比
        """
        disk = psutil.disk_usage("/")
        usage_percent = (disk.used / disk.total) * 100
        self._add_to_history(usage_percent)
        return usage_percent

    def _add_to_history(self, value: float):
        """添加值到历史记录"""
        self.history.append(value)
        if len(self.history) > self.max_history:
            self.history.pop(0)


class NetworkMonitor(ResourceMonitor):
    """网络监控器"""

    def __init__(self):
        """初始化网络监控器"""
        super().__init__("network")
        self.last_io = None

    async def check(self) -> float:
        """检查网络IO

        Returns:
            网络IO字节数
        """
        current_io = psutil.net_io_counters()

        if self.last_io:
            bytes_sent = current_io.bytes_sent - self.last_io.bytes_sent
            bytes_recv = current_io.bytes_recv - self.last_io.bytes_recv
            total_bytes = bytes_sent + bytes_recv
            self._add_to_history(total_bytes)
        else:
            total_bytes = 0

        self.last_io = current_io
        return self.history[-1] if self.history else 0

    def _add_to_history(self, value: float):
        """添加值到历史记录"""
        self.history.append(value)
        if len(self.history) > self.max_history:
            self.history.pop(0)
