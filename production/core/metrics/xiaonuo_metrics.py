#!/usr/bin/env python3
"""
小诺·双鱼公主性能指标收集器
Xiaonuo Pisces Princess Metrics Collector

收集和管理小诺·双鱼公主的性能指标

作者: Athena平台团队
创建时间: 2025-12-18
版本: v1.0.0
"""

from __future__ import annotations
import asyncio
import json
import logging
import threading
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available, system metrics will be limited")


@dataclass
class MetricPoint:
    """指标数据点"""

    timestamp: datetime
    value: float
    labels: dict[str, str] | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class MetricSummary:
    """指标摘要"""

    name: str
    count: int
    sum: float
    min: float
    max: float
    avg: float
    last_value: float
    last_timestamp: datetime


class MetricType:
    """指标类型"""

    COUNTER = "counter"  # 计数器(只增不减)
    GAUGE = "gauge"  # 仪表盘(可增可减)
    HISTOGRAM = "histogram"  # 直方图
    SUMMARY = "summary"  # 摘要


class MetricsCollector:
    """性能指标收集器"""

    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics: dict[str, list[MetricPoint]] = defaultdict(list)
        self.metric_types: dict[str, str] = {}
        self.metric_descriptions: dict[str, str] = {}
        self.counters: dict[str, float] = defaultdict(float)
        self.gauges: dict[str, float] = defaultdict(float)
        self.histograms: dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.lock = threading.RLock()

        # 启动后台收集任务
        self._background_tasks = []
        self._running = False

    def register_metric(self, name: str, metric_type: str, description: str = "") -> Any:
        """注册指标"""
        with self.lock:
            self.metric_types[name] = metric_type
            self.metric_descriptions[name] = description

            if metric_type == MetricType.COUNTER:
                self.counters[name] = 0.0
            elif metric_type == MetricType.GAUGE:
                self.gauges[name] = 0.0

            logger.debug(f"注册指标: {name} ({metric_type})")

    def increment_counter(
        self, name: str, value: float = 1.0, labels: dict[str, str] | None = None
    ) -> Any:
        """递增计数器"""
        if name not in self.metric_types or self.metric_types[name] != MetricType.COUNTER:
            self.register_metric(name, MetricType.COUNTER)

        with self.lock:
            self.counters[name] += value
            self._add_metric_point(name, self.counters[name], labels)

    def set_gauge(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        """设置仪表盘值"""
        if name not in self.metric_types or self.metric_types[name] != MetricType.GAUGE:
            self.register_metric(name, MetricType.GAUGE)

        with self.lock:
            self.gauges[name] = value
            self._add_metric_point(name, value, labels)

    def observe_histogram(
        self, name: str, value: float, labels: dict[str, str] | None = None
    ) -> Any:
        """观察直方图值"""
        if name not in self.metric_types:
            self.register_metric(name, MetricType.HISTOGRAM)

        with self.lock:
            self.histograms[name].append(value)
            self._add_metric_point(name, value, labels)

    def record_timing(
        self, name: str, duration: float, labels: dict[str, str] | None = None
    ) -> Any:
        """记录时间指标"""
        self.observe_histogram(f"{name}_duration", duration, labels)
        self.increment_counter(f"{name}_total", 1.0, labels)

    def _add_metric_point(
        self, name: str, value: float, labels: dict[str, str] | None = None
    ) -> Any:
        """添加指标数据点"""
        point = MetricPoint(timestamp=datetime.now(), value=value, labels=labels)

        self.metrics[name].append(point)

        # 限制历史记录数量
        if len(self.metrics[name]) > self.max_history:
            self.metrics[name] = self.metrics[name][-self.max_history :]

    def get_metric(self, name: str, since: datetime | None = None) -> list[MetricPoint]:
        """获取指标数据"""
        with self.lock:
            points = self.metrics[name].copy()

        if since:
            points = [p for p in points if p.timestamp >= since]

        return points

    def get_metric_summary(self, name: str, since: datetime | None = None) -> MetricSummary | None:
        """获取指标摘要"""
        points = self.get_metric(name, since)

        if not points:
            return None

        values = [p.value for p in points]
        last_point = points[-1]

        return MetricSummary(
            name=name,
            count=len(values),
            sum=sum(values),
            min=min(values),
            max=max(values),
            avg=sum(values) / len(values),
            last_value=last_point.value,
            last_timestamp=last_point.timestamp,
        )

    def get_all_metrics(self) -> dict[str, Any]:
        """获取所有指标"""
        result = {"timestamp": datetime.now().isoformat(), "metrics": {}}

        for name in self.metrics:
            summary = self.get_metric_summary(name)
            if summary:
                result["metrics"][name] = asdict(summary)
                result["metrics"][name]["type"] = self.metric_types.get(name, "unknown")
                result["metrics"][name]["description"] = self.metric_descriptions.get(name, "")

        return result

    def reset_metric(self, name: str) -> Any:
        """重置指标"""
        with self.lock:
            if name in self.metrics:
                self.metrics[name].clear()

            if name in self.counters:
                self.counters[name] = 0.0

            if name in self.gauges:
                self.gauges[name] = 0.0

            if name in self.histograms:
                self.histograms[name].clear()

    def reset_all_metrics(self) -> Any:
        """重置所有指标"""
        with self.lock:
            self.metrics.clear()
            self.counters.clear()
            self.gauges.clear()
            self.histograms.clear()


class SystemMetricsCollector:
    """系统指标收集器"""

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.running = False

        if PSUTIL_AVAILABLE:
            self.process = psutil.Process()

    def start_collection(self, interval: int = 30) -> Any:
        """开始收集系统指标"""
        if not PSUTIL_AVAILABLE:
            logger.warning("psutil not available, system metrics collection disabled")
            return

        self.running = True

        def collect_loop() -> Any:
            while self.running:
                try:
                    self._collect_system_metrics()
                    time.sleep(interval)
                except Exception as e:
                    logger.error(f"系统指标收集错误: {e}")
                    time.sleep(interval)

        thread = threading.Thread(target=collect_loop, daemon=True)
        thread.start()
        logger.info(f"系统指标收集已启动,间隔: {interval}秒")

    def stop_collection(self) -> Any:
        """停止收集系统指标"""
        self.running = False

    def _collect_system_metrics(self) -> Any:
        """收集系统指标"""
        if not PSUTIL_AVAILABLE:
            return

        try:
            # CPU指标
            cpu_percent = self.process.cpu_percent()
            self.metrics_collector.set_gauge("process_cpu_percent", cpu_percent)

            # 内存指标
            memory_info = self.process.memory_info()
            self.metrics_collector.set_gauge("process_memory_rss_bytes", memory_info.rss)
            self.metrics_collector.set_gauge("process_memory_vms_bytes", memory_info.vms)
            self.metrics_collector.set_gauge(
                "process_memory_percent", self.process.memory_percent()
            )

            # 系统内存
            system_memory = psutil.virtual_memory()
            self.metrics_collector.set_gauge("system_memory_total_bytes", system_memory.total)
            self.metrics_collector.set_gauge(
                "system_memory_available_bytes", system_memory.available
            )
            self.metrics_collector.set_gauge("system_memory_percent", system_memory.percent)

            # 磁盘指标
            disk_usage = psutil.disk_usage("/")
            self.metrics_collector.set_gauge("disk_total_bytes", disk_usage.total)
            self.metrics_collector.set_gauge("disk_free_bytes", disk_usage.free)
            self.metrics_collector.set_gauge(
                "disk_percent", (disk_usage.total - disk_usage.free) / disk_usage.total * 100
            )

            # 文件描述符
            try:
                num_fds = self.process.num_fds()
                self.metrics_collector.set_gauge("process_open_fds", num_fds)
            except (AttributeError, psutil.AccessDenied):
                pass

            # 线程数
            self.metrics_collector.set_gauge("process_threads", self.process.num_threads())

            # 网络连接数
            try:
                connections = len(self.process.connections())
                self.metrics_collector.set_gauge("process_connections", connections)
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass

        except Exception as e:
            logger.error(f"收集系统指标时出错: {e}")


class XiaonuoMetricsCollector:
    """小诺·双鱼公主专用指标收集器"""

    def __init__(self):
        self.base_collector = MetricsCollector(max_history=2000)
        self.system_collector = SystemMetricsCollector(self.base_collector)
        self._register_default_metrics()

    def _register_default_metrics(self) -> Any:
        """注册默认指标"""
        # 智能体指标
        self.base_collector.register_metric(
            "agent_initializations", MetricType.COUNTER, "智能体初始化次数"
        )
        self.base_collector.register_metric(
            "agent_requests_total", MetricType.COUNTER, "智能体请求总数"
        )
        self.base_collector.register_metric("agent_active_sessions", MetricType.GAUGE, "活跃会话数")

        # 超级能力指标
        self.base_collector.register_metric(
            "prompt_generations_total", MetricType.COUNTER, "提示词生成总数"
        )
        self.base_collector.register_metric(
            "coordination_tasks_total", MetricType.COUNTER, "协调任务总数"
        )
        self.base_collector.register_metric(
            "reflection_operations_total", MetricType.COUNTER, "反思操作总数"
        )

        # 性能指标
        self.base_collector.register_metric(
            "prompt_generation_duration", MetricType.HISTOGRAM, "提示词生成耗时"
        )
        self.base_collector.register_metric(
            "coordination_duration", MetricType.HISTOGRAM, "协调任务耗时"
        )
        self.base_collector.register_metric(
            "reflection_duration", MetricType.HISTOGRAM, "反思操作耗时"
        )

        # 家庭互动指标
        self.base_collector.register_metric(
            "family_interactions_total", MetricType.COUNTER, "家庭互动总数"
        )
        self.base_collector.register_metric(
            "love_expressions_total", MetricType.COUNTER, "表达爱意次数"
        )
        self.base_collector.register_metric(
            "thanks_expressions_total", MetricType.COUNTER, "表达感谢次数"
        )

        # 错误指标
        self.base_collector.register_metric("errors_total", MetricType.COUNTER, "错误总数")
        self.base_collector.register_metric("exceptions_total", MetricType.COUNTER, "异常总数")

        # 启动系统指标收集
        self.system_collector.start_collection(interval=30)

    def record_agent_initialization(self, agent_name: str) -> Any:
        """记录智能体初始化"""
        self.base_collector.increment_counter("agent_initializations", labels={"agent": agent_name})

    def record_prompt_generation(self, duration: float, task_type: str = "unknown") -> Any:
        """记录提示词生成"""
        self.base_collector.record_timing(
            "prompt_generation", duration, labels={"task_type": task_type}
        )

    def record_coordination_task(self, duration: float, agents_count: int) -> Any:
        """记录协调任务"""
        self.base_collector.record_timing(
            "coordination", duration, labels={"agents_count": str(agents_count)}
        )

    def record_reflection_operation(self, duration: float, experience_type: str = "unknown") -> Any:
        """记录反思操作"""
        self.base_collector.record_timing(
            "reflection", duration, labels={"experience_type": experience_type}
        )

    def record_family_interaction(self, emotion_type: str, success: bool = True) -> Any:
        """记录家庭互动"""
        self.base_collector.increment_counter(
            "family_interactions", labels={"emotion": emotion_type, "success": str(success)}
        )

        if emotion_type == "love":
            self.base_collector.increment_counter("love_expressions")
        elif emotion_type == "thanks":
            self.base_collector.increment_counter("thanks_expressions")

    def record_error(self, error_type: str, component: str = "unknown") -> Any:
        """记录错误"""
        self.base_collector.increment_counter(
            "errors_total", labels={"error_type": error_type, "component": component}
        )

    def record_exception(self, exception_type: str, component: str = "unknown") -> Any:
        """记录异常"""
        self.base_collector.increment_counter(
            "exceptions_total", labels={"exception_type": exception_type, "component": component}
        )

    def set_active_sessions(self, count: int) -> None:
        """设置活跃会话数"""
        self.base_collector.set_gauge("agent_active_sessions", count)

    def get_prometheus_metrics(self) -> str:
        """获取Prometheus格式的指标"""
        metrics = []
        all_metrics = self.base_collector.get_all_metrics()

        for name, data in all_metrics["metrics"].items():
            metric_type = data.get("type", "unknown")
            last_value = data.get("last_value", 0)
            description = data.get("description", "")

            # 添加描述
            if description:
                metrics.append(f"# HELP {name} {description}")

            # 添加类型
            type_mapping = {
                "counter": "counter",
                "gauge": "gauge",
                "histogram": "histogram",
                "summary": "summary",
            }
            prometheus_type = type_mapping.get(metric_type, "untyped")
            metrics.append(f"# TYPE {name} {prometheus_type}")

            # 添加指标值
            metrics.append(f"{name} {last_value}")

        return "\n".join(metrics)

    def export_metrics_to_file(self, file_path: Path) -> Any:
        """导出指标到文件"""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)

            metrics_data = self.base_collector.get_all_metrics()

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(metrics_data, f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"指标已导出到: {file_path}")

        except Exception as e:
            logger.error(f"导出指标失败: {e}")

    def get_metrics_summary(self) -> dict[str, Any]:
        """获取指标摘要"""
        return {
            "timestamp": datetime.now().isoformat(),
            "metrics_count": len(self.base_collector.metrics),
            "registered_metrics": list(self.base_collector.metric_types.keys()),
            "system_metrics_enabled": PSUTIL_AVAILABLE,
            "collection_status": "running" if self.system_collector.running else "stopped",
        }

    def shutdown(self) -> Any:
        """关闭指标收集器"""
        self.system_collector.stop_collection()
        logger.info("指标收集器已关闭")


# 全局指标收集器实例
_global_metrics_collector: XiaonuoMetricsCollector | None = None


def get_metrics_collector() -> XiaonuoMetricsCollector:
    """获取全局指标收集器实例"""
    global _global_metrics_collector
    if _global_metrics_collector is None:
        _global_metrics_collector = XiaonuoMetricsCollector()
    return _global_metrics_collector


def record_agent_performance(operation: str, duration: float, **kwargs) -> Any:
    """装饰器:自动记录智能体操作性能"""

    def decorator(func) -> None:
        def sync_wrapper(*args, **kwargs_inner) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs_inner)
                duration = time.time() - start_time
                get_metrics_collector().record_timing(operation, duration, **kwargs)
                return result
            except Exception as e:
                duration = time.time() - start_time
                get_metrics_collector().record_exception(type(e).__name__, operation)
                raise

        async def async_wrapper(*args, **kwargs_inner):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs_inner)
                duration = time.time() - start_time
                get_metrics_collector().record_timing(operation, duration, **kwargs)
                return result
            except Exception as e:
                duration = time.time() - start_time
                get_metrics_collector().record_exception(type(e).__name__, operation)
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


if __name__ == "__main__":
    # 测试指标收集器
    collector = get_metrics_collector()

    print("🧪 测试小诺·双鱼公主指标收集器")
    print("=" * 60)

    # 模拟一些指标
    collector.record_agent_initialization("xiaonuo_princess")
    collector.record_prompt_generation(0.123, "专业分析")
    collector.record_coordination_task(0.456, 3)
    collector.record_reflection_operation(0.234, "学习经验")
    collector.record_family_interaction("love", True)

    # 等待一些系统指标收集
    import time

    time.sleep(2)

    # 显示指标摘要
    summary = collector.get_metrics_summary()
    print("\n📊 指标摘要:")
    import json

    print(json.dumps(summary, indent=2, ensure_ascii=False))

    # 显示所有指标
    all_metrics = collector.base_collector.get_all_metrics()
    print(f"\n📈 所有指标数量: {len(all_metrics['metrics'])}")

    # 显示Prometheus格式
    prometheus_metrics = collector.get_prometheus_metrics()
    print("\n📋 Prometheus格式指标 (前200字符):")
    print(prometheus_metrics[:200] + "...")

    # 清理
    collector.shutdown()
