#!/usr/bin/env python3
"""
三阶段优化系统生产监控指标采集
Production Metrics Collector for Three-Phase Optimization System

功能:
1. 关键性能指标(KPI)采集
2. Prometheus集成
3. 健康检查
4. 性能基线对比
5. 告警触发

作者: 小诺·双鱼公主
版本: v1.0.0
"""

from __future__ import annotations
import asyncio
import contextlib
import logging
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any

import psutil

# 导入Prometheus客户端库
try:
    from prometheus_client import (
        CollectorRegistry,
        Counter,
        Gauge,
        Histogram,
        Info,
        Summary,
        generate_latest,
        start_http_server,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logging.warning("prometheus_client 未安装,Prometheus指标将被禁用")

logger = logging.getLogger(__name__)


class MetricCategory(str, Enum):
    """指标类别"""

    PHASE3 = "phase3"  # Phase 3 高级优化
    ENHANCED = "enhanced"  # Enhanced 增强优化
    UTILS = "utils"  # Utils 工具函数
    SYSTEM = "system"  # 系统指标
    BUSINESS = "business"  # 业务指标


class HealthStatus(str, Enum):
    """健康状态"""

    HEALTHY = "healthy"  # 健康
    DEGRADED = "degraded"  # 降级
    UNHEALTHY = "unhealthy"  # 不健康
    CRITICAL = "critical"  # 严重


@dataclass
class MetricData:
    """指标数据"""

    name: str
    value: float
    category: MetricCategory
    tags: dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_prometheus_metric(self) -> str:
        """转换为Prometheus格式"""
        label_str = ",".join([f'{k}="{v}"' for k, v in self.tags.items()])
        return f"{self.name}{{{label_str}}} {self.value} {int(self.timestamp * 1000)}"


@dataclass
class PerformanceBaseline:
    """性能基线"""

    metric_name: str
    baseline_value: float
    warning_threshold: float  # 警告阈值(相对基线的百分比)
    critical_threshold: float  # 严重阈值
    created_at: datetime = field(default_factory=datetime.now)

    def check_threshold(self, current_value: float) -> HealthStatus:
        """检查阈值"""
        diff_pct = abs(current_value - self.baseline_value) / self.baseline_value * 100

        if diff_pct >= self.critical_threshold:
            return HealthStatus.CRITICAL
        elif diff_pct >= self.warning_threshold:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY


class ProductionMetricsCollector:
    """
    生产环境指标采集器

    功能:
    1. Phase 3 模块指标采集
    2. Enhanced 模块指标采集
    3. 系统资源监控
    4. 性能基线对比
    5. 自动告警
    """

    def __init__(
        self,
        enable_prometheus: bool = True,
        prometheus_port: int = 9091,
        collect_interval_seconds: int = 30,
    ):
        self.enable_prometheus = enable_prometheus and PROMETHEUS_AVAILABLE
        self.prometheus_port = prometheus_port
        self.collect_interval = collect_interval_seconds

        # Prometheus 注册表
        if self.enable_prometheus:
            self.registry = CollectorRegistry()
            self._setup_prometheus_metrics()
        else:
            self.registry = None

        # 内存中的指标存储
        self._metrics_buffer: dict[str, deque] = {}
        self._max_buffer_size = 1000

        # 性能基线
        self._baselines: dict[str, PerformanceBaseline] = {}

        # 健康状态
        self._health_status = HealthStatus.HEALTHY
        self._health_checks: dict[str, Callable] = {}

        # 统计信息
        self._start_time = time.time()
        self._total_metrics_collected = 0

        # 后台任务
        self._collection_task: asyncio.Task | None = None
        self._is_running = False

        # 注册默认健康检查
        self._register_default_health_checks()

        logger.info(f"✅ 生产指标采集器初始化完成 (Prometheus: {self.enable_prometheus})")

    def _setup_prometheus_metrics(self) -> Any:
        """设置Prometheus指标"""

        # Phase 3 指标
        self.phase3_meta_learning_latency = Histogram(
            "phase3_meta_learning_latency_seconds",
            "元学习引擎延迟",
            ["operation"],
            registry=self.registry,
        )

        self.phase3_distillation_compression_ratio = Gauge(
            "phase3_distillation_compression_ratio",
            "模型蒸馏压缩比",
            ["model_id"],
            registry=self.registry,
        )

        self.phase3_nas_accuracy_improvement = Gauge(
            "phase3_nas_accuracy_improvement_pct", "神经架构搜索准确率提升", registry=self.registry
        )

        # Enhanced 指标
        self.enhanced_ensemble_accuracy = Gauge(
            "enhanced_ensemble_accuracy", "多模型集成准确率", ["method"], registry=self.registry
        )

        self.enhanced_online_learning_samples = Counter(
            "enhanced_online_learning_samples_total", "在线学习样本总数", registry=self.registry
        )

        self.enhanced_p99_latency = Gauge(
            "enhanced_p99_latency_ms", "P99延迟", ["service"], registry=self.registry
        )

        self.enhanced_recovery_rate = Gauge(
            "enhanced_recovery_rate_pct", "错误恢复率", ["error_category"], registry=self.registry
        )

        # Utils 指标
        self.utils_operation_latency = Histogram(
            "utils_operation_latency_seconds",
            "工具函数操作延迟",
            ["function_name"],
            registry=self.registry,
        )

        # 系统指标
        self.system_memory_usage = Gauge(
            "system_memory_usage_bytes", "系统内存使用", ["service", "type"], registry=self.registry
        )

        self.system_cpu_usage = Gauge(
            "system_cpu_usage_pct", "系统CPU使用率", ["service"], registry=self.registry
        )

        self.system_request_rate = Counter(
            "system_requests_total", "系统请求总数", ["service", "status"], registry=self.registry
        )

        # 业务指标
        self.business_optimization_success_rate = Gauge(
            "business_optimization_success_rate", "优化成功率", registry=self.registry
        )

        # 健康状态
        self.health_status_info = Info(
            "optimization_health_status", "优化系统健康状态", registry=self.registry
        )

        logger.info("📊 Prometheus指标设置完成")

    def _register_default_health_checks(self) -> Any:
        """注册默认健康检查"""
        self.register_health_check("phase3_meta_learning", self._check_phase3_meta_learning)
        self.register_health_check("enhanced_latency", self._check_enhanced_latency)
        self.register_health_check("system_resources", self._check_system_resources)

    def register_health_check(self, name: str, check_func: Callable[[], HealthStatus]) -> Any:
        """注册健康检查"""
        self._health_checks[name] = check_func
        logger.debug(f"注册健康检查: {name}")

    def set_baseline(
        self,
        metric_name: str,
        baseline_value: float,
        warning_threshold: float = 20.0,
        critical_threshold: float = 50.0,
    ):
        """
        设置性能基线

        Args:
            metric_name: 指标名称
            baseline_value: 基线值
            warning_threshold: 警告阈值(百分比)
            critical_threshold: 严重阈值(百分比)
        """
        baseline = PerformanceBaseline(
            metric_name=metric_name,
            baseline_value=baseline_value,
            warning_threshold=warning_threshold,
            critical_threshold=critical_threshold,
        )
        self._baselines[metric_name] = baseline
        logger.info(f"📊 设置基线: {metric_name} = {baseline_value}")

    def record_phase3_metric(self, metric_name: str, value: float, operation: str = "unknown"):
        """记录Phase 3指标"""
        self._add_to_buffer(
            MetricData(
                name=f"phase3_{metric_name}",
                value=value,
                category=MetricCategory.PHASE3,
                tags={"operation": operation},
            )
        )

        if self.enable_prometheus:
            if metric_name == "meta_learning_latency":
                self.phase3_meta_learning_latency.labels(operation=operation).observe(value)
            elif metric_name == "distillation_compression_ratio":
                # 需要model_id标签,这里使用默认值
                self.phase3_distillation_compression_ratio.labels(model_id="default").set(value)
            elif metric_name == "nas_accuracy_improvement":
                self.phase3_nas_accuracy_improvement.set(value)

        self._total_metrics_collected += 1

    def record_enhanced_metric(
        self, metric_name: str, value: float, tags: dict[str, str] | None = None
    ):
        """记录Enhanced指标"""
        tags = tags or {}
        self._add_to_buffer(
            MetricData(
                name=f"enhanced_{metric_name}",
                value=value,
                category=MetricCategory.ENHANCED,
                tags=tags,
            )
        )

        if self.enable_prometheus:
            if metric_name == "ensemble_accuracy":
                method = tags.get("method", "weighted_voting")
                self.enhanced_ensemble_accuracy.labels(method=method).set(value)
            elif metric_name == "online_learning_samples":
                self.enhanced_online_learning_samples.inc(int(value))
            elif metric_name == "p99_latency":
                service = tags.get("service", "optimization")
                self.enhanced_p99_latency.labels(service=service).set(value)
            elif metric_name == "recovery_rate":
                category = tags.get("error_category", "unknown")
                self.enhanced_recovery_rate.labels(error_category=category).set(value)

        self._total_metrics_collected += 1

    def record_system_metric(self, metric_name: str, value: float, service: str = "optimization"):
        """记录系统指标"""
        self._add_to_buffer(
            MetricData(
                name=f"system_{metric_name}",
                value=value,
                category=MetricCategory.SYSTEM,
                tags={"service": service},
            )
        )

        if self.enable_prometheus:
            if metric_name == "memory_usage":
                self.system_memory_usage.labels(service=service, type="rss").set(value)
            elif metric_name == "cpu_usage":
                self.system_cpu_usage.labels(service=service).set(value)
            elif metric_name == "request_count":
                # Counter需要inc()而不是set()
                pass

        self._total_metrics_collected += 1

    def _add_to_buffer(self, metric: MetricData) -> Any:
        """添加到缓冲区"""
        if metric.name not in self._metrics_buffer:
            self._metrics_buffer[metric.name] = deque(maxlen=self._max_buffer_size)
        self._metrics_buffer[metric.name].append(metric)

    async def start_collection(self):
        """启动指标采集"""
        if self._is_running:
            logger.warning("指标采集已在运行")
            return

        self._is_running = True

        # 启动Prometheus服务器
        if self.enable_prometheus:
            try:
                start_http_server(self.prometheus_port)
                logger.info(f"🌐 Prometheus HTTP服务器启动在端口 {self.prometheus_port}")
            except Exception as e:
                logger.error(f"Prometheus服务器启动失败: {e}")

        # 启动采集任务
        self._collection_task = asyncio.create_task(self._collection_loop())
        logger.info("🔄 指标采集任务已启动")

    async def stop_collection(self):
        """停止指标采集"""
        self._is_running = False

        if self._collection_task:
            self._collection_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._collection_task

        logger.info("🛑 指标采集已停止")

    async def _collection_loop(self):
        """采集循环"""
        process = psutil.Process()

        while self._is_running:
            try:
                # 采集系统指标
                memory_info = process.memory_info()
                cpu_percent = process.cpu_percent()

                self.record_system_metric("memory_usage", memory_info.rss)
                self.record_system_metric("cpu_usage", cpu_percent)

                # 更新健康状态
                await self._update_health_status()

                # 等待下次采集
                await asyncio.sleep(self.collect_interval)

            except Exception as e:
                logger.error(f"指标采集错误: {e}")
                await asyncio.sleep(self.collect_interval)

    async def _update_health_status(self):
        """更新健康状态"""
        overall_status = HealthStatus.HEALTHY

        for name, check_func in self._health_checks.items():
            try:
                status = check_func()
                if status.value > overall_status.value:
                    overall_status = status
            except Exception as e:
                logger.error(f"健康检查失败 {name}: {e}")
                overall_status = HealthStatus.UNHEALTHY

        self._health_status = overall_status

        # 更新Prometheus Info
        if self.enable_prometheus:
            uptime = time.time() - self._start_time
            self.health_status_info.info(
                {
                    "status": overall_status.value,
                    "uptime_seconds": str(int(uptime)),
                    "total_metrics": str(self._total_metrics_collected),
                    "timestamp": datetime.now().isoformat(),
                }
            )

    def _check_phase3_meta_learning(self) -> HealthStatus:
        """检查Phase 3元学习状态"""
        # 获取最近的延迟数据
        metrics = self._metrics_buffer.get("phase3_meta_learning_latency", deque())

        if not metrics:
            return HealthStatus.HEALTHY

        # 计算平均延迟
        recent = list(metrics)[-10:]  # 最近10个数据点
        avg_latency = sum(m.value for m in recent) / len(recent)

        # 检查基线
        baseline = self._baselines.get("phase3_meta_learning_latency")
        if baseline:
            return baseline.check_threshold(avg_latency)

        # 默认阈值
        if avg_latency > 1.0:  # 1秒
            return HealthStatus.DEGRADED
        elif avg_latency > 2.0:  # 2秒
            return HealthStatus.CRITICAL

        return HealthStatus.HEALTHY

    def _check_enhanced_latency(self) -> HealthStatus:
        """检查Enhanced延迟状态"""
        # 获取P99延迟数据
        metrics = self._metrics_buffer.get("enhanced_p99_latency", deque())

        if not metrics:
            return HealthStatus.HEALTHY

        recent = list(metrics)[-10:]
        avg_p99 = sum(m.value for m in recent) / len(recent)

        # 检查基线
        baseline = self._baselines.get("enhanced_p99_latency")
        if baseline:
            return baseline.check_threshold(avg_p99)

        # 默认阈值
        if avg_p99 > 200:  # 200ms
            return HealthStatus.DEGRADED
        elif avg_p99 > 300:  # 300ms
            return HealthStatus.CRITICAL

        return HealthStatus.HEALTHY

    def _check_system_resources(self) -> HealthStatus:
        """检查系统资源状态"""
        process = psutil.Process()

        # 检查内存使用
        memory_percent = process.memory_info().rss / psutil.virtual_memory().total * 100
        if memory_percent > 80:
            return HealthStatus.CRITICAL
        elif memory_percent > 60:
            return HealthStatus.DEGRADED

        # 检查CPU使用
        cpu_percent = process.cpu_percent(interval=1)
        if cpu_percent > 90:
            return HealthStatus.CRITICAL
        elif cpu_percent > 70:
            return HealthStatus.DEGRADED

        return HealthStatus.HEALTHY

    def get_health_status(self) -> dict[str, Any]:
        """获取健康状态"""
        uptime = time.time() - self._start_time

        return {
            "status": self._health_status.value,
            "uptime_seconds": int(uptime),
            "uptime_hours": round(uptime / 3600, 2),
            "total_metrics_collected": self._total_metrics_collected,
            "metrics_in_buffer": sum(len(buf) for buf in self._metrics_buffer.values()),
            "baselines_configured": len(self._baselines),
            "health_checks": len(self._health_checks),
            "prometheus_enabled": self.enable_prometheus,
            "is_running": self._is_running,
        }

    def get_metrics_summary(self) -> dict[str, Any]:
        """获取指标摘要"""
        summary = {"timestamp": datetime.now().isoformat(), "categories": {}}

        for category in MetricCategory:
            category_metrics = {}
            for name, buffer in self._metrics_buffer.items():
                if name.startswith(category.value):
                    recent = list(buffer)[-10:]
                    if recent:
                        values = [m.value for m in recent]
                        category_metrics[name] = {
                            "count": len(recent),
                            "avg": sum(values) / len(values),
                            "min": min(values),
                            "max": max(values),
                            "latest": values[-1],
                        }

            if category_metrics:
                summary["categories"][category.value] = category_metrics

        return summary

    def export_prometheus_metrics(self) -> str:
        """导出Prometheus格式的指标"""
        if not self.enable_prometheus:
            return "# Prometheus metrics disabled\n"

        return generate_latest(self.registry).decode("utf-8")

    def record_request(self, service: str, status: str, duration: float | None = None):
        """记录请求指标"""
        if self.enable_prometheus:
            self.system_request_rate.labels(service=service, status=status).inc()

        # 计算成功率
        if duration:
            self.record_system_metric("response_time", duration, service)

    def record_optimization_result(self, success: bool, module: str, duration: float):
        """记录优化结果"""
        status = "success" if success else "failure"
        self.record_request(module, status, duration)

        # 更新成功率指标
        if self.enable_prometheus:
            # 这里可以添加更复杂的成功率计算
            pass


# 装饰器
def track_phase3_metric(operation: str = "unknown") -> Any:
    """Phase 3指标跟踪装饰器"""

    def decorator(func) -> None:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start

                # 记录成功的指标
                collector = get_production_metrics_collector()
                collector.record_phase3_metric(f"{operation}_latency", duration, operation)

                return result
            except Exception as e:
                duration = time.time() - start
                logger.error(f"Phase 3 操作失败: {operation}, 错误: {e}")
                raise

        return wrapper

    return decorator


def track_enhanced_metric(metric_name: str, **default_tags) -> Any:
    """Enhanced指标跟踪装饰器"""

    def decorator(func) -> None:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start

                # 记录成功的指标
                collector = get_production_metrics_collector()

                # 尝试从返回值中提取指标
                if isinstance(result, dict) and "metrics" in result:
                    for key, value in result["metrics"].items():
                        collector.record_enhanced_metric(
                            f"{metric_name}_{key}", value, default_tags
                        )
                else:
                    collector.record_enhanced_metric(
                        f"{metric_name}_duration", duration, default_tags
                    )

                return result
            except Exception as e:
                duration = time.time() - start
                logger.error(f"Enhanced 操作失败: {metric_name}, 错误: {e}")
                raise

        return wrapper

    return decorator


# 全局单例
_collector_instance: ProductionMetricsCollector | None = None


def get_production_metrics_collector(
    enable_prometheus: bool = True, prometheus_port: int = 9091
) -> ProductionMetricsCollector:
    """
    获取生产指标采集器单例

    Args:
        enable_prometheus: 是否启用Prometheus
        prometheus_port: Prometheus端口

    Returns:
        生产指标采集器实例
    """
    global _collector_instance

    if _collector_instance is None:
        _collector_instance = ProductionMetricsCollector(
            enable_prometheus=enable_prometheus, prometheus_port=prometheus_port
        )

        # 设置默认性能基线
        _collector_instance.set_baseline("phase3_meta_learning_latency", 0.1, 50.0, 100.0)
        _collector_instance.set_baseline("enhanced_p99_latency", 150.0, 33.0, 100.0)

    return _collector_instance
