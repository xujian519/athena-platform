#!/usr/bin/env python3
from __future__ import annotations
"""
MPS性能监控器 - 阶段5优化
实时监控GPU利用率、内存使用、温度和功耗

作者: 小诺·双鱼公主 🌊✨
创建时间: 2025-12-27
版本: v1.0.0
"""

import asyncio
import contextlib
import json
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import psutil
import torch

from core.logging_config import setup_logging

logger = setup_logging()


@dataclass
class GPUMetrics:
    """GPU指标"""

    timestamp: float
    gpu_utilization_percent: float  # GPU利用率
    memory_used_mb: float
    memory_total_mb: float
    memory_percent: float
    temperature_celsius: float | None = None
    power_watts: float | None = None


@dataclass
class SystemMetrics:
    """系统指标"""

    timestamp: float
    cpu_percent: float
    memory_used_gb: float
    memory_total_gb: float
    memory_percent: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_sent_mb: float
    network_recv_mb: float


@dataclass
class MonitorConfig:
    """监控配置"""

    # 采样间隔
    sample_interval_seconds: float = 5.0

    # 数据保留
    retention_minutes: int = 60  # 保留60分钟数据

    # 告警阈值
    gpu_memory_warning_percent: float = 0.90
    gpu_memory_critical_percent: float = 0.95
    system_memory_warning_percent: float = 0.85
    system_memory_critical_percent: float = 0.95

    # 告警配置
    enable_alerts: bool = True
    alert_cooldown_seconds: float = 60.0  # 告警冷却时间

    # 日志配置
    log_dir: str = "/Users/xujian/Athena工作平台/logs/monitoring"


class MPSPerformanceMonitor:
    """MPS性能监控器"""

    def __init__(self, config: MonitorConfig = None):
        self.config = config or MonitorConfig()
        self.device = self._select_device()

        # 数据存储
        self.gpu_metrics: deque = deque()
        self.system_metrics: deque = deque()

        # 告警状态
        self.last_alert_time: dict[str, float] = {}
        self.alert_callbacks: list[Callable] = []

        # 监控状态
        self.is_monitoring = False
        self.monitor_task: asyncio.Task | None = None

        # 初始IO计数
        self.last_io_counters = psutil.disk_io_counters()
        self.last_net_counters = psutil.net_io_counters()

        # 创建日志目录
        Path(self.config.log_dir).mkdir(parents=True, exist_ok=True)

        logger.info("📊 MPS性能监控器初始化完成")
        logger.info(f"⏱️ 采样间隔: {self.config.sample_interval_seconds}秒")
        logger.info(f"🔔 告警: {'启用' if self.config.enable_alerts else '禁用'}")

    def _select_device(self) -> torch.device:
        """选择最优设备"""
        if torch.backends.mps.is_available():
            return torch.device("mps")
        elif torch.cuda.is_available():
            return torch.device("cuda")
        else:
            return torch.device("cpu")

    async def start_monitoring(self):
        """启动监控"""
        if self.is_monitoring:
            logger.warning("⚠️ 监控已在运行")
            return

        self.is_monitoring = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())

        logger.info("✅ 性能监控已启动")

    async def stop_monitoring(self):
        """停止监控"""
        if not self.is_monitoring:
            return

        self.is_monitoring = False

        if self.monitor_task:
            self.monitor_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.monitor_task

        logger.info("🛑 性能监控已停止")

    async def _monitor_loop(self):
        """监控循环"""
        try:
            while self.is_monitoring:
                # 收集指标
                gpu_metrics = self._collect_gpu_metrics()
                system_metrics = self._collect_system_metrics()

                # 存储指标
                self.gpu_metrics.append(gpu_metrics)
                self.system_metrics.append(system_metrics)

                # 清理过期数据
                self._cleanup_old_metrics()

                # 检查告警
                if self.config.enable_alerts:
                    await self._check_alerts(gpu_metrics, system_metrics)

                # 等待下一次采样
                await asyncio.sleep(self.config.sample_interval_seconds)

        except asyncio.CancelledError:
            logger.info("📊 监控循环已取消")
        except Exception as e:
            logger.error(f"❌ 监控循环错误: {e}")

    def _collect_gpu_metrics(self) -> GPUMetrics:
        """收集GPU指标"""
        timestamp = time.time()

        if self.device.type == "mps":
            # MPS内存
            if hasattr(torch.mps, "current_allocated_memory"):
                memory_used_mb = torch.mps.current_allocated_memory() / (1024 * 1024)
            else:
                memory_used_mb = 0.0

            memory_total_mb = 48 * 1024  # M4 Pro 48GB

            # GPU利用率(估算)
            gpu_utilization = self._estimate_gpu_utilization()

            # 温度和功耗(MPS暂不支持,返回None)
            temperature = None
            power = None

        elif self.device.type == "cuda":
            # CUDA指标
            if torch.cuda.is_available():
                memory_used_mb = torch.cuda.memory_allocated() / (1024 * 1024)
                memory_total_mb = torch.cuda.get_device_properties(0).total_memory / (1024 * 1024)

                # GPU利用率(需要nvidia-ml-py)
                gpu_utilization = self._get_cuda_utilization()

                # 温度和功耗
                temperature = self._get_cuda_temperature()
                power = self._get_cuda_power()
            else:
                memory_used_mb = 0.0
                memory_total_mb = 1.0
                gpu_utilization = 0.0
                temperature = None
                power = None

        else:
            # CPU设备
            memory_used_mb = 0.0
            memory_total_mb = 1.0
            gpu_utilization = 0.0
            temperature = None
            power = None

        memory_percent = memory_used_mb / memory_total_mb

        return GPUMetrics(
            timestamp=timestamp,
            gpu_utilization_percent=gpu_utilization * 100,
            memory_used_mb=memory_used_mb,
            memory_total_mb=memory_total_mb,
            memory_percent=memory_percent * 100,
            temperature_celsius=temperature,
            power_watts=power,
        )

    def _collect_system_metrics(self) -> SystemMetrics:
        """收集系统指标"""
        timestamp = time.time()

        # CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)

        # 内存
        memory = psutil.virtual_memory()
        memory_used_gb = memory.used / (1024**3)
        memory_total_gb = memory.total / (1024**3)
        memory_percent = memory.percent

        # 磁盘IO
        io_counters = psutil.disk_io_counters()
        if self.last_io_counters:
            disk_read_mb = (io_counters.read_bytes - self.last_io_counters.read_bytes) / (1024**2)
            disk_write_mb = (io_counters.write_bytes - self.last_io_counters.write_bytes) / (
                1024**2
            )
        else:
            disk_read_mb = 0.0
            disk_write_mb = 0.0
        self.last_io_counters = io_counters

        # 网络IO
        net_counters = psutil.net_io_counters()
        if self.last_net_counters:
            net_sent_mb = (net_counters.bytes_sent - self.last_net_counters.bytes_sent) / (1024**2)
            net_recv_mb = (net_counters.bytes_recv - self.last_net_counters.bytes_recv) / (1024**2)
        else:
            net_sent_mb = 0.0
            net_recv_mb = 0.0
        self.last_net_counters = net_counters

        return SystemMetrics(
            timestamp=timestamp,
            cpu_percent=cpu_percent,
            memory_used_gb=memory_used_gb,
            memory_total_gb=memory_total_gb,
            memory_percent=memory_percent,
            disk_io_read_mb=disk_read_mb,
            disk_io_write_mb=disk_write_mb,
            network_sent_mb=net_sent_mb,
            network_recv_mb=net_recv_mb,
        )

    def _estimate_gpu_utilization(self) -> float:
        """估算GPU利用率(基于内存活动)"""
        try:
            if self.device.type == "mps" and hasattr(torch.mps, "driver_allocated_memory"):
                allocated = torch.mps.current_allocated_memory()
                cached = torch.mps.driver_allocated_memory()
                if cached > 0:
                    return allocated / cached
        except (TypeError, ZeroDivisionError) as e:
            logger.warning(f"计算时发生错误: {e}")
        except Exception as e:
            logger.error(f"未预期的错误: {e}")
        return 0.0

    def _get_cuda_utilization(self) -> float:
        """获取CUDA GPU利用率"""
        try:
            import pynvml

            pynvml.nvml_init()
            handle = pynvml.nvml_device_get_handle_by_index(0)
            utilization = pynvml.nvml_device_get_utilization_rates(handle)
            return utilization.gpu / 100.0
        except Exception:
            return 0.0

    def _get_cuda_temperature(self) -> float | None:
        """获取CUDA GPU温度"""
        try:
            import pynvml

            pynvml.nvml_init()
            handle = pynvml.nvml_device_get_handle_by_index(0)
            return pynvml.nvml_device_get_temperature(handle, pynvml.NVML_TEMPERATURE_GPU)
        except (ImportError, AttributeError):
            # pynvml不可用或GPU未初始化
            return None

    def _get_cuda_power(self) -> float | None:
        """获取CUDA GPU功耗"""
        try:
            import pynvml

            pynvml.nvml_init()
            handle = pynvml.nvml_device_get_handle_by_index(0)
            return pynvml.nvml_device_get_power_usage(handle) / 1000.0  # W
        except (ImportError, AttributeError):
            # pynvml不可用或GPU未初始化
            return None

    def _cleanup_old_metrics(self) -> Any:
        """清理过期指标"""
        cutoff_time = time.time() - (self.config.retention_minutes * 60)

        # 清理GPU指标
        while self.gpu_metrics and self.gpu_metrics[0].timestamp < cutoff_time:
            self.gpu_metrics.popleft()

        # 清理系统指标
        while self.system_metrics and self.system_metrics[0].timestamp < cutoff_time:
            self.system_metrics.popleft()

    async def _check_alerts(self, gpu_metrics: GPUMetrics, system_metrics: SystemMetrics):
        """检查告警条件"""
        time.time()

        # GPU内存告警
        if gpu_metrics.memory_percent > self.config.gpu_memory_critical_percent * 100:
            await self._trigger_alert(
                "critical",
                f"GPU内存严重不足: {gpu_metrics.memory_percent:.1f}% ({gpu_metrics.memory_used_mb:.0f}MB / {gpu_metrics.memory_total_mb:.0f}MB)",
            )
        elif gpu_metrics.memory_percent > self.config.gpu_memory_warning_percent * 100:
            await self._trigger_alert(
                "warning",
                f"GPU内存警告: {gpu_metrics.memory_percent:.1f}% ({gpu_metrics.memory_used_mb:.0f}MB / {gpu_metrics.memory_total_mb:.0f}MB)",
            )

        # 系统内存告警
        if system_metrics.memory_percent > self.config.system_memory_critical_percent * 100:
            await self._trigger_alert(
                "critical",
                f"系统内存严重不足: {system_metrics.memory_percent:.1f}% ({system_metrics.memory_used_gb:.1f}GB / {system_metrics.memory_total_gb:.1f}GB)",
            )
        elif system_metrics.memory_percent > self.config.system_memory_warning_percent * 100:
            await self._trigger_alert(
                "warning",
                f"系统内存警告: {system_metrics.memory_percent:.1f}% ({system_metrics.memory_used_gb:.1f}GB / {system_metrics.memory_total_gb:.1f}GB)",
            )

    async def _trigger_alert(self, level: str, message: str):
        """触发告警"""
        current_time = time.time()
        alert_key = f"{level}:{message}"

        # 检查冷却时间
        if alert_key in self.last_alert_time:
            if current_time - self.last_alert_time[alert_key] < self.config.alert_cooldown_seconds:
                return

        # 记录告警
        logger.warning(f"🚨 [{level.upper()}] {message}")
        self.last_alert_time[alert_key] = current_time

        # 调用回调
        for callback in self.alert_callbacks:
            try:
                await callback(level, message)
            except Exception as e:
                logger.error(f"告警回调错误: {e}")

    def add_alert_callback(self, callback: Callable) -> None:
        """添加告警回调"""
        self.alert_callbacks.append(callback)

    def get_current_metrics(self) -> dict[str, Any]:
        """获取当前指标"""
        if not self.gpu_metrics or not self.system_metrics:
            return {}

        gpu = self.gpu_metrics[-1]
        sys = self.system_metrics[-1]

        return {
            "timestamp": datetime.fromtimestamp(gpu.timestamp).isoformat(),
            "gpu": {
                "utilization_percent": gpu.gpu_utilization_percent,
                "memory_used_mb": gpu.memory_used_mb,
                "memory_total_mb": gpu.memory_total_mb,
                "memory_percent": gpu.memory_percent,
                "temperature_celsius": gpu.temperature_celsius,
                "power_watts": gpu.power_watts,
            },
            "system": {
                "cpu_percent": sys.cpu_percent,
                "memory_used_gb": sys.memory_used_gb,
                "memory_total_gb": sys.memory_total_gb,
                "memory_percent": sys.memory_percent,
                "disk_io_read_mb": sys.disk_io_read_mb,
                "disk_io_write_mb": sys.disk_io_write_mb,
                "network_sent_mb": sys.network_sent_mb,
                "network_recv_mb": sys.network_recv_mb,
            },
        }

    def get_metrics_history(self, minutes: int = 10) -> dict[str, Any]:
        """获取历史指标"""
        cutoff_time = time.time() - (minutes * 60)

        gpu_history = [
            {
                "timestamp": m.timestamp,
                "utilization_percent": m.gpu_utilization_percent,
                "memory_percent": m.memory_percent,
            }
            for m in self.gpu_metrics
            if m.timestamp >= cutoff_time
        ]

        system_history = [
            {
                "timestamp": m.timestamp,
                "cpu_percent": m.cpu_percent,
                "memory_percent": m.memory_percent,
            }
            for m in self.system_metrics
            if m.timestamp >= cutoff_time
        ]

        return {
            "gpu_metrics": gpu_history,
            "system_metrics": system_history,
            "count": len(gpu_history),
        }

    def save_metrics(self, filename: str | None = None) -> None:
        """保存指标到文件"""
        if filename is None:
            filename = f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        filepath = Path(self.config.log_dir) / filename

        data = {
            "current_metrics": self.get_current_metrics(),
            "history": self.get_metrics_history(minutes=self.config.retention_minutes),
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"💾 指标已保存: {filepath}")

    def generate_report(self) -> str:
        """生成监控报告"""
        if not self.gpu_metrics or not self.system_metrics:
            return "暂无监控数据"

        gpu = self.gpu_metrics[-1]
        sys = self.system_metrics[-1]

        report = [
            "=" * 60,
            "📊 MPS性能监控报告",
            "=" * 60,
            f"时间: {datetime.fromtimestamp(gpu.timestamp).strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "🖥️ GPU指标:",
            f"  利用率: {gpu.gpu_utilization_percent:.1f}%",
            f"  内存: {gpu.memory_used_mb:.0f}MB / {gpu.memory_total_mb:.0f}MB ({gpu.memory_percent:.1f}%)",
            (
                f"  温度: {gpu.temperature_celsius:.1f}°C"
                if gpu.temperature_celsius
                else "  温度: N/A"
            ),
            f"  功耗: {gpu.power_watts:.1f}W" if gpu.power_watts else "  功耗: N/A",
            "",
            "💻 系统指标:",
            f"  CPU: {sys.cpu_percent:.1f}%",
            f"  内存: {sys.memory_used_gb:.1f}GB / {sys.memory_total_gb:.1f}GB ({sys.memory_percent:.1f}%)",
            f"  磁盘读: {sys.disk_io_read_mb:.2f}MB/s",
            f"  磁盘写: {sys.disk_io_write_mb:.2f}MB/s",
            f"  网络收: {sys.network_recv_mb:.2f}MB/s",
            f"  网络发: {sys.network_sent_mb:.2f}MB/s",
            "=" * 60,
        ]

        return "\n".join(report)


# 全局单例
_monitor: MPSPerformanceMonitor | None = None


def get_performance_monitor() -> MPSPerformanceMonitor:
    """获取全局性能监控器实例"""
    global _monitor
    if _monitor is None:
        _monitor = MPSPerformanceMonitor()
    return _monitor


async def main():
    """测试监控器"""
    # setup_logging()  # 日志配置已移至模块导入

    monitor = MPSPerformanceMonitor()

    # 启动监控
    await monitor.start_monitoring()

    print("✅ 监控已启动,按Ctrl+C停止...")

    try:
        # 定期打印报告
        while True:
            await asyncio.sleep(10)
            print("\n" + monitor.generate_report())
    except KeyboardInterrupt:
        print("\n🛑 停止监控...")
        await monitor.stop_monitoring()

        # 保存最终指标
        monitor.save_metrics()
        print("💾 指标已保存")


# 入口点: @async_main装饰器已添加到main函数
