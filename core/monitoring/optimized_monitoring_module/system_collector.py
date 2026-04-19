#!/usr/bin/env python3
from __future__ import annotations
"""
优化版监控告警模块 - 系统指标收集器
Optimized Monitoring and Alerting Module - System Metrics Collector

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0
"""

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import psutil

from .collector import MetricsCollector

logger = logging.getLogger(__name__)


class SystemMetricsCollector:
    """系统指标收集器

    定期收集系统级别的指标(CPU、内存、磁盘、网络等)。
    """

    def __init__(self, metrics_collector: MetricsCollector):
        """初始化系统指标收集器

        Args:
            metrics_collector: 指标收集器实例
        """
        self.metrics_collector = metrics_collector
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def start(self):
        """启动系统指标收集"""
        self.running = True

        # 在线程池中运行
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, self._collect_system_metrics)

    async def stop(self):
        """停止系统指标收集"""
        self.running = False
        self.executor.shutdown(wait=True)

    def _collect_system_metrics(self) -> Any:
        """收集系统指标(在线程池中运行)"""
        while self.running:
            try:
                # CPU指标
                cpu_percent = psutil.cpu_percent(interval=1)
                self.metrics_collector.set_gauge("system_cpu_usage", cpu_percent)

                # 内存指标
                memory = psutil.virtual_memory()
                self.metrics_collector.set_gauge("system_memory_usage", memory.percent)
                self.metrics_collector.set_gauge("system_memory_used", memory.used)
                self.metrics_collector.set_gauge("system_memory_available", memory.available)

                # 磁盘指标
                disk = psutil.disk_usage("/")
                self.metrics_collector.set_gauge("system_disk_usage", disk.percent)
                self.metrics_collector.set_gauge("system_disk_used", disk.used)
                self.metrics_collector.set_gauge("system_disk_free", disk.free)

                # 网络指标
                network = psutil.net_io_counters()
                self.metrics_collector.record_counter(
                    "system_network_bytes_sent", network.bytes_sent
                )
                self.metrics_collector.record_counter(
                    "system_network_bytes_recv", network.bytes_recv
                )

                # 进程指标
                process_count = len(psutil.pids())
                self.metrics_collector.set_gauge("system_process_count", process_count)

                time.sleep(10)  # 每10秒收集一次

            except Exception as e:
                logger.error(f"收集系统指标失败: {e}")
                time.sleep(10)
