#!/usr/bin/env python3
from __future__ import annotations
"""
性能监控系统
实时监控Athena优化系统的性能指标

功能:
- CPU和内存使用监控
- 任务执行统计
- 组件性能分析
- 系统健康状态检查
- 性能报告生成
"""

import asyncio
import contextlib
import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import psutil

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """性能指标"""

    name: str
    value: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.now)
    category: str = "general"


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self, monitoring_interval: float = 30.0):
        self.monitoring_interval = monitoring_interval
        self.monitoring_active = False
        self.monitoring_task = None

        # 性能数据存储
        self.system_metrics = []
        self.component_metrics = {}
        self.task_metrics = {}
        self.custom_metrics = []

        # 性能阈值
        self.thresholds = {
            "cpu_warning": 70.0,
            "cpu_critical": 90.0,
            "memory_warning": 70.0,
            "memory_critical": 85.0,
            "response_time_warning": 2.0,
            "response_time_critical": 5.0,
        }

        # 统计信息
        self.start_time = datetime.now()
        self.total_alerts = 0
        self.performance_issues = []

    async def start_monitoring(self):
        """开始性能监控"""
        if self.monitoring_active:
            logger.warning("性能监控已经在运行中")
            return

        self.monitoring_active = True
        self.start_time = datetime.now()

        logger.info("🔍 性能监控已启动")
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())

    async def stop_monitoring(self):
        """停止性能监控"""
        self.monitoring_active = False

        if self.monitoring_task:
            self.monitoring_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.monitoring_task

        logger.info("⏹️ 性能监控已停止")

    async def _monitoring_loop(self):
        """监控主循环"""
        while self.monitoring_active:
            try:
                # 收集系统指标
                system_stats = await self._collect_system_stats()
                self.system_metrics.append(system_stats)

                # 检查性能阈值
                await self._check_thresholds(system_stats)

                # 等待下次监控
                await asyncio.sleep(self.monitoring_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"性能监控错误: {e}")
                await asyncio.sleep(5)

    async def _collect_system_stats(self):
        """收集系统统计信息"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)

            # 内存使用情况
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / (1024 * 1024)

            # 活跃线程数
            active_threads = threading.active_count()

            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "memory_used_mb": memory_used_mb,
                "active_threads": active_threads,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"收集系统统计信息失败: {e}")
            return None

    async def _check_thresholds(self, stats):
        """检查性能阈值"""
        if not stats:
            return

        alerts = []

        # CPU检查
        if stats["cpu_percent"] >= self.thresholds["cpu_critical"]:
            alerts.append(f"🚨 CPU使用率严重过高: {stats['cpu_percent']:.1f}%")
        elif stats["cpu_percent"] >= self.thresholds["cpu_warning"]:
            alerts.append(f"⚠️ CPU使用率过高: {stats['cpu_percent']:.1f}%")

        # 内存检查
        if stats["memory_percent"] >= self.thresholds["memory_critical"]:
            alerts.append(f"🚨 内存使用率严重过高: {stats['memory_percent']:.1f}%")
        elif stats["memory_percent"] >= self.thresholds["memory_warning"]:
            alerts.append(f"⚠️ 内存使用率过高: {stats['memory_percent']:.1f}%")

        # 发送警报
        for alert in alerts:
            await self._send_alert(alert)

    async def _send_alert(self, message: str):
        """发送性能警报"""
        self.total_alerts += 1
        self.performance_issues.append(
            {"timestamp": datetime.now().isoformat(), "message": message}
        )

        logger.warning(f"性能警报: {message}")

    def get_current_stats(self) -> Any | None:
        """获取当前统计信息"""
        current_time = datetime.now()
        uptime_seconds = (current_time - self.start_time).total_seconds()

        # 最新系统指标
        latest_system = self.system_metrics[-1] if self.system_metrics else None

        return {
            "uptime_seconds": uptime_seconds,
            "monitoring_active": self.monitoring_active,
            "total_alerts": self.total_alerts,
            "registered_components": len(self.component_metrics),
            "task_types": len(self.task_metrics),
            "current_system": latest_system,
        }

    def get_performance_summary(self) -> Any | None:
        """获取性能摘要"""
        if not self.system_metrics:
            return {"status": "no_data"}

        # 计算平均值
        recent_metrics = (
            self.system_metrics[-10:] if len(self.system_metrics) >= 10 else self.system_metrics
        )

        avg_cpu = sum(stats["cpu_percent"] for stats in recent_metrics if stats) / len(
            recent_metrics
        )
        avg_memory = sum(stats["memory_percent"] for stats in recent_metrics if stats) / len(
            recent_metrics
        )

        # 系统健康状态
        health_score = 100
        health_issues = []

        if avg_cpu > self.thresholds["cpu_warning"]:
            health_score -= min(30, (avg_cpu - self.thresholds["cpu_warning"]) * 2)
            health_issues.append("CPU使用率过高")

        if avg_memory > self.thresholds["memory_warning"]:
            health_score -= min(30, (avg_memory - self.thresholds["memory_warning"]) * 2)
            health_issues.append("内存使用率过高")

        # 总体状态
        overall_status = "excellent"
        if health_score < 70:
            overall_status = "poor"
        elif health_score < 85:
            overall_status = "fair"
        elif health_score < 95:
            overall_status = "good"

        return {
            "overall_status": overall_status,
            "health_score": round(health_score, 1),
            "health_issues": health_issues,
            "performance_averages": {
                "cpu_percent": round(avg_cpu, 1),
                "memory_percent": round(avg_memory, 1),
                "uptime_hours": round((datetime.now() - self.start_time).total_seconds() / 3600, 1),
            },
            "recent_alerts": self.performance_issues[-5:],  # 最近5个警报
        }


if __name__ == "__main__":
    print("性能监控模块已加载")
