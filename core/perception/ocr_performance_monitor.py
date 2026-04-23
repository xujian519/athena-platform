#!/usr/bin/env python3
from __future__ import annotations
"""
OCR性能监控模块
OCR Performance Monitoring Module

专门用于监控OCR优化引擎的性能

作者: 小诺·双鱼公主
创建时间: 2026-01-01
"""

import asyncio
import contextlib
import json
import logging
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import psutil

logger = logging.getLogger(__name__)


@dataclass
class OCRMetric:
    """OCR指标"""

    operation: str
    timestamp: datetime
    duration_ms: float
    success: bool
    text_length: int = 0
    chinese_chars: int = 0
    confidence: float = 0.0
    image_size: tuple = (0, 0)
    metadata: dict[str, Any] = field(default_factory=dict)


class OCRPerformanceMonitor:
    """
    OCR性能监控器

    专门监控OCR优化引擎的性能:
    1. 文本纠错性能
    2. 图像预处理性能
    3. 置信度计算性能
    4. 系统资源使用
    """

    def __init__(
        self,
        agent_id: str = "ocr_optimizer",
        log_dir: Optional[str] = None,
        enable_alerts: bool = True,
    ):
        self.agent_id = agent_id
        self.enable_alerts = enable_alerts

        # 日志目录
        if log_dir is None:
            log_dir = "/Users/xujian/Athena工作平台/logs/monitoring"
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 指标存储
        self.metrics: dict[str, deque[OCRMetric]] = defaultdict(lambda: deque(maxlen=10000))

        # 统计数据
        self.stats: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "count": 0,
                "total_time": 0.0,
                "min_time": float("inf"),
                "max_time": 0.0,
                "errors": 0,
                "success_rate": 1.0,
            }
        )

        # 告警规则
        self.alert_rules: dict[str, dict[str, Any]] = {
            "text_correction": {
                "max_duration_ms": 10.0,  # 10ms
                "error_threshold": 0.05,  # 5%
            },
            "image_preprocessing": {
                "max_duration_ms": 500.0,  # 500ms
                "error_threshold": 0.02,  # 2%
            },
            "confidence_scoring": {
                "max_duration_ms": 1.0,  # 1ms
                "error_threshold": 0.01,  # 1%
            },
        }

        # 告警回调
        self.alert_callbacks: list[Callable] = []

        # 系统监控
        self.process = psutil.Process()
        self.system_metrics: deque[dict[str, Any]] = deque(maxlen=1000)

        # 监控状态
        self.is_monitoring = False
        self.monitor_task: asyncio.Task | None = None

        logger.info(f"📊 OCR性能监控器初始化: {self.agent_id}")

    def record_metric(self, metric: OCRMetric) -> Any:
        """
        记录OCR指标

        Args:
            metric: OCR指标数据
        """
        # 存储指标
        self.metrics[metric.operation].append(metric)

        # 更新统计
        stats = self.stats[metric.operation]
        stats["count"] += 1
        stats["total_time"] += metric.duration_ms
        stats["min_time"] = min(stats["min_time"], metric.duration_ms)
        stats["max_time"] = max(stats["max_time"], metric.duration_ms)

        if not metric.success:
            stats["errors"] += 1

        stats["success_rate"] = (stats["count"] - stats["errors"]) / stats["count"]

        # 检查告警
        if self.enable_alerts:
            self._check_alerts(metric)

        # 定期保存日志
        if stats["count"] % 100 == 0:
            self._save_metrics_log(metric.operation)

    def _check_alerts(self, metric: OCRMetric) -> Any:
        """检查告警条件"""
        if metric.operation not in self.alert_rules:
            return

        rules = self.alert_rules[metric.operation]

        # 性能告警
        if metric.duration_ms > rules["max_duration_ms"]:
            self._trigger_alert(
                alert_type="performance_slow",
                operation=metric.operation,
                duration_ms=metric.duration_ms,
                threshold_ms=rules["max_duration_ms"],
                message=f"{metric.operation}性能下降: {metric.duration_ms:.2f}ms > {rules['max_duration_ms']:.2f}ms",
            )

        # 错误率告警
        stats = self.stats[metric.operation]
        if stats["count"] >= 20:
            error_rate = stats["errors"] / stats["count"]
            if error_rate > rules["error_threshold"]:
                self._trigger_alert(
                    alert_type="high_error_rate",
                    operation=metric.operation,
                    error_rate=error_rate,
                    threshold=rules["error_threshold"],
                    message=f"{metric.operation}错误率过高: {error_rate*100:.1f}%",
                )

    def _trigger_alert(self, **kwargs) -> Any:
        """触发告警"""
        alert = {"timestamp": datetime.now().isoformat(), "agent_id": self.agent_id, **kwargs}

        # 日志记录
        alert_type = kwargs.get("alert_type", "info")
        message = kwargs.get("message", "")

        if "slow" in alert_type or "high_error" in alert_type:
            logger.warning(f"🚨 告警: {message}")
        else:
            logger.info(f"📊 {message}")

        # 调用回调函数
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"告警回调失败: {e}")

    def get_stats(self, operation: str) -> dict[str, Any]:
        """获取操作统计"""
        stats = self.stats[operation].copy()

        if stats["count"] > 0:
            stats["avg_time"] = stats["total_time"] / stats["count"]
            stats["min_time"] = stats["min_time"] if stats["min_time"] != float("inf") else 0
            stats["throughput"] = 1000 / stats["avg_time"] if stats["avg_time"] > 0 else 0
        else:
            stats["avg_time"] = 0
            stats["min_time"] = 0
            stats["throughput"] = 0

        return stats

    def get_all_stats(self) -> dict[str, dict[str, Any]]:
        """获取所有统计"""
        return {op: self.get_stats(op) for op in self.stats}

    def get_performance_report(self) -> dict[str, Any]:
        """生成性能报告"""
        # 获取系统信息
        cpu_percent = self.process.cpu_percent()
        memory_info = self.process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024

        return {
            "timestamp": datetime.now().isoformat(),
            "agent_id": self.agent_id,
            "operations": self.get_all_stats(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_mb": memory_mb,
                "memory_gb": memory_mb / 1024,
            },
            "total_operations": sum(s["count"] for s in self.stats.values()),
        }

    def _save_metrics_log(self, operation: str) -> Any:
        """保存指标日志"""
        try:
            stats = self.get_stats(operation)
            log_file = self.log_dir / f"{operation}_metrics.jsonl"

            # 追加写入
            with open(log_file, "a") as f:
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "operation": operation,
                    "stats": stats,
                }
                f.write(json.dumps(log_entry) + "\n")

        except Exception as e:
            logger.error(f"保存指标日志失败: {e}")

    def save_report(self, filename: Optional[str] = None) -> None:
        """保存性能报告"""
        if filename is None:
            filename = f"ocr_performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        report_path = self.log_dir / filename

        try:
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(self.get_performance_report(), f, indent=2, ensure_ascii=False)

            logger.info(f"💾 性能报告已保存: {report_path}")
            return str(report_path)

        except Exception as e:
            logger.error(f"保存性能报告失败: {e}")
            return None

    async def start_monitoring(self, interval: float = 5.0):
        """启动后台监控"""
        if self.is_monitoring:
            logger.warning("监控已在运行")
            return

        self.is_monitoring = True
        self.monitor_task = asyncio.create_task(self._monitor_loop(interval))
        logger.info(f"✅ OCR性能监控已启动 (间隔: {interval}秒)")

    async def stop_monitoring(self):
        """停止监控"""
        if not self.is_monitoring:
            return

        self.is_monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.monitor_task

        # 保存最终报告
        self.save_report()

        logger.info("⏸️ OCR性能监控已停止")

    async def _monitor_loop(self, interval: float):
        """监控循环"""
        while self.is_monitoring:
            try:
                # 记录系统指标
                cpu_percent = self.process.cpu_percent()
                memory_info = self.process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024

                self.system_metrics.append(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "cpu_percent": cpu_percent,
                        "memory_mb": memory_mb,
                    }
                )

                # 检查系统资源告警
                if cpu_percent > 80:
                    self._trigger_alert(
                        alert_type="high_cpu",
                        cpu_percent=cpu_percent,
                        message=f"CPU使用率过高: {cpu_percent:.1f}%",
                    )

                if memory_mb > 1000:
                    self._trigger_alert(
                        alert_type="high_memory",
                        memory_mb=memory_mb,
                        message=f"内存使用过高: {memory_mb:.1f}MB",
                    )

            except Exception as e:
                logger.error(f"监控循环错误: {e}")

            await asyncio.sleep(interval)

    def add_alert_callback(self, callback: Callable) -> None:
        """添加告警回调"""
        self.alert_callbacks.append(callback)

    def clear_metrics(self) -> None:
        """清除所有指标"""
        self.metrics.clear()
        self.stats.clear()
        logger.info("🗑️ 已清除所有OCR性能指标")


class OCRTimer:
    """OCR操作计时器上下文管理器"""

    def __init__(self, monitor: OCRPerformanceMonitor, operation: str, **metadata):
        self.monitor = monitor
        self.operation = operation
        self.metadata = metadata
        self.start_time = None
        self.success = True

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000
        self.success = exc_type is None

        metric = OCRMetric(
            operation=self.operation,
            timestamp=datetime.now(),
            duration_ms=duration_ms,
            success=self.success,
            metadata=self.metadata,
        )

        self.monitor.record_metric(metric)


# 全局监控器实例
_global_monitor: OCRPerformanceMonitor | None = None


def get_ocr_monitor() -> OCRPerformanceMonitor:
    """获取全局OCR监控器"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = OCRPerformanceMonitor()
    return _global_monitor


# 导出
__all__ = ["OCRMetric", "OCRPerformanceMonitor", "OCRTimer", "get_ocr_monitor"]
