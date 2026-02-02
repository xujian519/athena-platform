#!/usr/bin/env python3
"""
内存监控工具
Memory Monitor

用于检测和预防内存泄漏，提供实时内存监控和告警

作者: Athena AI Team
创建时间: 2026-01-26
版本: 1.0.0
"""

import asyncio
import gc
import logging
import os
import psutil
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class MemorySnapshot:
    """内存快照"""

    timestamp: float
    rss_mb: float  # 常驻内存大小 (MB)
    vms_mb: float  # 虚拟内存大小 (MB)
    percent: float  # 内存使用百分比
    gc_objects: int  # GC跟踪的对象数量
    gc_collected: int  # GC回收的对象数量

    @property
    def timestamp_str(self) -> str:
        """格式化的时间戳"""
        return datetime.fromtimestamp(self.timestamp).strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "timestamp": self.timestamp_str,
            "rss_mb": round(self.rss_mb, 2),
            "vms_mb": round(self.vms_mb, 2),
            "percent": round(self.percent, 2),
            "gc_objects": self.gc_objects,
            "gc_collected": self.gc_collected,
        }


@dataclass
class MemoryAlert:
    """内存告警"""

    alert_type: str  # 类型: leak, high_usage, gc_increasing
    severity: str  # 严重程度: info, warning, critical
    message: str
    timestamp: float
    current_snapshot: MemorySnapshot
    baseline_snapshot: MemorySnapshot | None = None
    recommendations: List[str] = field(default_factory=list)

    @property
    def timestamp_str(self) -> str:
        """格式化的时间戳"""
        return datetime.fromtimestamp(self.timestamp).strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "alert_type": self.alert_type,
            "severity": self.severity,
            "message": self.message,
            "timestamp": self.timestamp_str,
            "current_memory": self.current_snapshot.to_dict(),
            "baseline_memory": self.baseline_snapshot.to_dict() if self.baseline_snapshot else None,
            "recommendations": self.recommendations,
        }


class MemoryMonitor:
    """
    内存监控器

    功能:
    - 实时监控内存使用
    - 检测潜在内存泄漏
    - GC对象数量跟踪
    - 内存增长趋势分析
    - 自动告警
    """

    def __init__(
        self,
        check_interval: int = 60,  # 检查间隔(秒)
        memory_threshold_mb: float = 1000,  # 内存告警阈值(MB)
        growth_threshold_percent: float = 20,  # 增长告警阈值(%)
        gc_objects_threshold: int = 100000,  # GC对象告警阈值
        snapshot_history_size: int = 100,  # 快照历史大小
        auto_gc: bool = True,  # 自动垃圾回收
        alert_callback: Optional[Callable[[MemoryAlert], None] | None = None,
    ):
        """
        初始化内存监控器

        Args:
            check_interval: 检查间隔(秒)
            memory_threshold_mb: 内存使用告警阈值(MB)
            growth_threshold_percent: 内存增长告警阈值(%)
            gc_objects_threshold: GC对象数量告警阈值
            snapshot_history_size: 快照历史记录大小
            auto_gc: 是否自动垃圾回收
            alert_callback: 告警回调函数
        """
        self.check_interval = check_interval
        self.memory_threshold_mb = memory_threshold_mb
        self.growth_threshold_percent = growth_threshold_percent
        self.gc_objects_threshold = gc_objects_threshold
        self.snapshot_history_size = snapshot_history_size
        self.auto_gc = auto_gc
        self.alert_callback = alert_callback

        # 快照历史
        self.snapshots: List[MemorySnapshot] = []

        # 告警历史
        self.alerts: List[MemoryAlert] = []

        # 监控状态
        self._monitoring = False
        self._monitor_task: asyncio.Task | None = None
        self._monitor_thread: threading.Thread | None = None

        # 基线快照
        self.baseline_snapshot: MemorySnapshot | None = None

        logger.info(f"✅ 内存监控器初始化完成 (阈值: {memory_threshold_mb}MB)")

    def get_current_snapshot(self) -> MemorySnapshot:
        """获取当前内存快照"""
        process = psutil.Process(os.getpid())

        # 执行垃圾回收获取准确的对象数量
        if self.auto_gc:
            collected = gc.collect()
        else:
            collected = 0

        snapshot = MemorySnapshot(
            timestamp=time.time(),
            rss_mb=process.memory_info().rss / 1024 / 1024,  # 转换为MB
            vms_mb=process.memory_info().vms / 1024 / 1024,  # 转换为MB
            percent=process.memory_percent(),
            gc_objects=len(gc.get_objects()),
            gc_collected=collected,
        )

        return snapshot

    def take_snapshot(self) -> MemorySnapshot:
        """拍摄内存快照并保存"""
        snapshot = self.get_current_snapshot()

        # 保存到历史
        self.snapshots.append(snapshot)

        # 限制历史大小
        if len(self.snapshots) > self.snapshot_history_size:
            self.snapshots.pop(0)

        # 如果是第一个快照，设置为基线
        if self.baseline_snapshot is None:
            self.baseline_snapshot = snapshot
            logger.info(f"📊 设置内存基线: {snapshot.to_dict()}")

        return snapshot

    def analyze_memory_growth(self, current: MemorySnapshot, baseline: MemorySnapshot) -> dict[str, Any]:
        """分析内存增长"""
        time_elapsed = current.timestamp - baseline.timestamp
        rss_growth = current.rss_mb - baseline.rss_mb
        rss_growth_percent = (rss_growth / baseline.rss_mb * 100) if baseline.rss_mb > 0 else 0
        gc_objects_growth = current.gc_objects - baseline.gc_objects
        gc_objects_growth_percent = (
            gc_objects_growth / baseline.gc_objects * 100 if baseline.gc_objects > 0 else 0
        )

        return {
            "time_elapsed_seconds": time_elapsed,
            "rss_growth_mb": rss_growth,
            "rss_growth_percent": rss_growth_percent,
            "gc_objects_growth": gc_objects_growth,
            "gc_objects_growth_percent": gc_objects_growth_percent,
        }

    def check_memory_leak(self) -> List[MemoryAlert]:
        """检查内存泄漏"""
        alerts = []

        if len(self.snapshots) < 2:
            return alerts

        current = self.snapshots[-1]
        baseline = self.baseline_snapshot or self.snapshots[0]

        # 分析内存增长
        growth = self.analyze_memory_growth(current, baseline)

        # 检查1: 内存使用超过阈值
        if current.rss_mb > self.memory_threshold_mb:
            severity = "critical" if current.rss_mb > self.memory_threshold_mb * 1.5 else "warning"
            alert = MemoryAlert(
                alert_type="high_usage",
                severity=severity,
                message=f"内存使用超过阈值: {current.rss_mb:.2f}MB > {self.memory_threshold_mb}MB",
                timestamp=time.time(),
                current_snapshot=current,
                baseline_snapshot=baseline,
                recommendations=[
                    "检查是否有缓存未设置过期时间",
                    "检查是否有全局变量持续增长",
                    "检查是否有文件/数据库连接未关闭",
                    "考虑增加内存限制或重启服务",
                ],
            )
            alerts.append(alert)

        # 检查2: 内存持续增长
        if (
            growth["rss_growth_percent"] > self.growth_threshold_percent
            and growth["time_elapsed_seconds"] > 300  # 至少5分钟
        ):
            severity = "critical" if growth["rss_growth_percent"] > 50 else "warning"
            alert = MemoryAlert(
                alert_type="memory_growth",
                severity=severity,
                message=f"内存持续增长: {growth['rss_growth_percent']:.1f}% (时长: {growth['time_elapsed_seconds']:.0f}秒)",
                timestamp=time.time(),
                current_snapshot=current,
                baseline_snapshot=baseline,
                recommendations=[
                    "检查是否有循环引用",
                    "检查是否有大对象未释放",
                    "使用内存分析工具(如memory_profiler)定位问题",
                    "考虑使用weakref打破循环引用",
                ],
            )
            alerts.append(alert)

        # 检查3: GC对象数量持续增长
        if (
            growth["gc_objects_growth_percent"] > self.growth_threshold_percent
            and growth["time_elapsed_seconds"] > 300
        ):
            severity = "warning"
            alert = MemoryAlert(
                alert_type="gc_increasing",
                severity=severity,
                message=f"GC对象数量持续增长: {growth['gc_objects_growth']:,} ({growth['gc_objects_growth_percent']:.1f}%)",
                timestamp=time.time(),
                current_snapshot=current,
                baseline_snapshot=baseline,
                recommendations=[
                    "检查是否有对象创建后未释放",
                    "检查是否有缓存未设置淘汰策略",
                    "检查是否有事件监听器未取消",
                    "考虑使用objgraph分析对象引用",
                ],
            )
            alerts.append(alert)

        # 检查4: GC对象数量超过阈值
        if current.gc_objects > self.gc_objects_threshold:
            severity = "warning" if current.gc_objects < self.gc_objects_threshold * 2 else "critical"
            alert = MemoryAlert(
                alert_type="gc_high",
                severity=severity,
                message=f"GC对象数量过多: {current.gc_objects:,} > {self.gc_objects_threshold:,}",
                timestamp=time.time(),
                current_snapshot=current,
                baseline_snapshot=baseline,
                recommendations=[
                    "执行垃圾回收: gc.collect()",
                    "检查对象引用链",
                    "优化缓存策略",
                ],
            )
            alerts.append(alert)

        return alerts

    def emit_alert(self, alert: MemoryAlert):
        """发送告警"""
        self.alerts.append(alert)

        # 限制告警历史
        if len(self.alerts) > 100:
            self.alerts.pop(0)

        # 记录日志
        log_func = logger.warning if alert.severity == "warning" else logger.error
        log_func(f"🚨 内存告警: {alert.message}")

        # 调用回调
        if self.alert_callback:
            try:
                self.alert_callback(alert)
            except Exception as e:
                logger.error(f"告警回调失败: {e}")

    async def _monitoring_loop(self):
        """监控循环"""
        logger.info("🔍 开始内存监控循环")

        try:
            while self._monitoring:
                try:
                    # 拍摄快照
                    snapshot = self.take_snapshot()

                    # 检查内存泄漏
                    alerts = self.check_memory_leak()

                    # 发送告警
                    for alert in alerts:
                        self.emit_alert(alert)

                    # 如果没有告警，定期记录状态
                    if not alerts and len(self.snapshots) % 10 == 0:
                        logger.debug(f"📊 内存状态: {snapshot.to_dict()}")

                except Exception as e:
                    logger.error(f"❌ 内存监控异常: {e}")

                # 等待下一次检查
                await asyncio.sleep(self.check_interval)

        except asyncio.CancelledError:
            logger.info("📋 内存监控循环已收到取消信号，正在退出...")
            raise

    async def start(self):
        """启动监控"""
        if self._monitoring:
            logger.warning("⚠️ 内存监控已在运行")
            return

        self._monitoring = True

        # 拍摄初始快照
        self.take_snapshot()

        # 启动监控任务
        self._monitor_task = asyncio.create_task(self._monitoring_loop())

        logger.info(f"✅ 内存监控已启动 (检查间隔: {self.check_interval}秒)")

    async def stop(self):
        """停止监控"""
        if not self._monitoring:
            return

        logger.info("🛑 停止内存监控...")

        self._monitoring = False

        # 取消监控任务
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        logger.info("✅ 内存监控已停止")

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        if not self.snapshots:
            return {"status": "no_data"}

        current = self.snapshots[-1]

        stats = {
            "monitoring": self._monitoring,
            "check_interval": self.check_interval,
            "current_memory": current.to_dict(),
            "snapshot_count": len(self.snapshots),
            "alert_count": len(self.alerts),
        }

        # 如果有基线，添加增长分析
        if self.baseline_snapshot:
            stats["growth_since_baseline"] = self.analyze_memory_growth(
                current, self.baseline_snapshot
            )

        return stats

    def get_recent_alerts(self, limit: int = 10) -> List[dict[str, Any]:
        """获取最近的告警"""
        return [alert.to_dict() for alert in self.alerts[-limit:]]

    def clear_history(self):
        """清空历史"""
        self.snapshots.clear()
        self.alerts.clear()
        self.baseline_snapshot = None
        logger.info("🧹 内存监控历史已清空")


# =============================================================================
# 全局内存监控器实例
# =============================================================================

_global_memory_monitor: MemoryMonitor | None = None


def get_memory_monitor(**kwargs) -> MemoryMonitor:
    """获取全局内存监控器实例"""
    global _global_memory_monitor

    if _global_memory_monitor is None:
        _global_memory_monitor = MemoryMonitor(**kwargs)

    return _global_memory_monitor


# =============================================================================
# 便捷函数
# =============================================================================

def check_memory_now() -> dict[str, Any]:
    """立即检查内存使用"""
    monitor = get_memory_monitor()
    snapshot = monitor.take_snapshot()
    return snapshot.to_dict()


def analyze_memory_leaks() -> List[dict[str, Any]:
    """分析内存泄漏"""
    monitor = get_memory_monitor()

    # 确保有足够的快照
    if len(monitor.snapshots) < 2:
        monitor.take_snapshot()
        asyncio.run(asyncio.sleep(1))  # 等待1秒
        monitor.take_snapshot()

    alerts = monitor.check_memory_leak()
    return [alert.to_dict() for alert in alerts]


def print_memory_summary():
    """打印内存摘要"""
    monitor = get_memory_monitor()
    stats = monitor.get_stats()

    print()
    print("=" * 60)
    print("📊 内存监控摘要")
    print("=" * 60)
    print(f"监控状态: {'运行中' if stats['monitoring'] else '未运行'}")
    print(f"当前内存: {stats['current_memory']['rss_mb']:.2f} MB")
    print(f"GC对象数: {stats['current_memory']['gc_objects']:,}")
    print(f"快照数量: {stats['snapshot_count']}")
    print(f"告警数量: {stats['alert_count']}")

    if "growth_since_baseline" in stats:
        growth = stats["growth_since_baseline"]
        print()
        print("自基线以来的增长:")
        print(f"  RSS增长: {growth['rss_growth_mb']:.2f} MB ({growth['rss_growth_percent']:.1f}%)")
        print(f"  GC对象增长: {growth['gc_objects_growth']:,} ({growth['gc_objects_growth_percent']:.1f}%)")

    print()
    print("=" * 60)
    print()


# =============================================================================
# 使用示例
# =============================================================================

async def main():
    """主函数示例"""
    print("🔍 内存监控器演示")
    print()

    # 创建监控器
    monitor = MemoryMonitor(
        check_interval=5,  # 5秒检查一次
        memory_threshold_mb=500,  # 500MB阈值
        growth_threshold_percent=10,  # 10%增长告警
    )

    # 启动监控
    await monitor.start()

    # 模拟运行一段时间
    print("监控运行中，按 Ctrl+C 停止...")
    try:
        await asyncio.sleep(30)
    except KeyboardInterrupt:
        pass

    # 停止监控
    await monitor.stop()

    # 打印统计
    print_memory_summary()


if __name__ == "__main__":
    asyncio.run(main())
