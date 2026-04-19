#!/usr/bin/env python3
from __future__ import annotations
"""
Athena全链路监控系统
Full-Link Monitoring System

实现端到端的全链路监控,包括:
1. 调用链路追踪 - 完整的请求链路追踪
2. 性能指标收集 - 实时性能指标监控
3. 异常告警机制 - 智能异常检测和告警
4. 监控仪表板 - 可视化监控数据展示
5. 结果验证 - 调用结果自动验证

作者: Athena平台团队
创建时间: 2025-12-29
版本: v2.0.0
"""

import asyncio
import json
import threading
import time
import uuid
from collections import defaultdict, deque
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import psutil

from core.logging_config import setup_logging

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


@dataclass
class SpanConfig:
    """追踪配置"""

    # 追踪配置
    service_name: str = "athena-nlp"
    service_version: str = "2.0.0"
    environment: str = "development"

    # 性能配置
    slow_threshold_ms: float = 1000.0  # 慢请求阈值
    error_threshold_percent: float = 5.0  # 错误率阈值

    # 采样配置
    sample_rate: float = 1.0  # 采样率
    max_spans_per_request: int = 100

    # 存储配置
    span_history_size: int = 10000
    metrics_window_seconds: int = 300  # 5分钟窗口

    # 告警配置
    enable_realtime_alerts: bool = True
    alert_cooldown_seconds: int = 60


class MetricType(Enum):
    """指标类型"""

    COUNTER = "counter"  # 计数器
    GAUGE = "gauge"  # 仪表
    HISTOGRAM = "histogram"  # 直方图
    SUMMARY = "summary"  # 摘要


class AlertSeverity(Enum):
    """告警严重程度"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationResult(Enum):
    """验证结果"""

    VALID = "valid"
    INVALID_FORMAT = "invalid_format"
    INCOMPLETE = "incomplete"
    UNREASONABLE = "unreasonable"
    INCONSISTENT = "inconsistent"


@dataclass
class MetricPoint:
    """指标数据点"""

    name: str
    type: MetricType
    value: float
    labels: dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type.value,
            "value": self.value,
            "labels": self.labels,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class Alert:
    """告警"""

    alert_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    rule_name: str = ""
    severity: AlertSeverity = AlertSeverity.WARNING
    message: str = ""
    metrics: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolved_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "rule_name": self.rule_name,
            "severity": self.severity.value,
            "message": self.message,
            "metrics": self.metrics,
            "timestamp": self.timestamp.isoformat(),
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


@dataclass
class LinkTrace:
    """链路追踪"""

    trace_id: str
    parent_trace_id: str | None = None
    operation: str = ""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None
    duration_ms: float = 0.0

    # 状态
    status: str = "running"  # running, success, failed, timeout
    error: str | None = None

    # 数据流
    input_data: dict[str, Any] | None = None
    output_data: dict[str, Any] | None = None

    # 性能指标
    metrics: dict[str, Any] = field(default_factory=dict)

    # 上下文
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: dict[str, str] = field(default_factory=dict)

    # 子链路
    children: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "parent_trace_id": self.parent_trace_id,
            "operation": self.operation,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "error": self.error,
            "input_size": len(str(self.input_data)) if self.input_data else 0,
            "output_size": len(str(self.output_data)) if self.output_data else 0,
            "metrics": self.metrics,
            "metadata": self.metadata,
            "tags": self.tags,
            "children_count": len(self.children),
        }


class ResultValidator:
    """结果验证器"""

    def __init__(self):
        self.validation_rules = {}
        self._setup_default_rules()

    def _setup_default_rules(self) -> Any:
        """设置默认验证规则"""
        # 工具特定的验证规则
        self.validation_rules = {
            "code_analyzer": {
                "required_fields": ["analysis", "complexity"],
                "type_checks": {"lines": int},
                "range_checks": {"complexity": ["低", "中", "高", "中等"]},
            },
            "emotional_support": {
                "required_fields": ["detected_emotion", "strategies"],
                "type_checks": {"intensity": int},
                "range_checks": {"intensity": (1, 10)},
            },
            "decision_engine": {
                "required_fields": ["best_option", "ranking"],
                "type_checks": {"ranking": list},
                "min_length_checks": {"ranking": 1},
            },
        }

    def validate(
        self, tool_name: str, result: Any, context: dict[str, Any] | None = None
    ) -> tuple[ValidationResult, str | None]:
        """
        验证工具调用结果

        Args:
            tool_name: 工具名称
            result: 调用结果
            context: 上下文信息

        Returns:
            (验证结果, 错误消息)
        """
        if result is None:
            return ValidationResult.INCOMPLETE, "结果为空"

        # 检查是否是字典
        if not isinstance(result, dict):
            return ValidationResult.INVALID_FORMAT, "结果不是字典类型"

        # 获取工具特定的验证规则
        rules = self.validation_rules.get(tool_name, {})

        # 1. 必填字段检查
        if "required_fields" in rules:
            for field in rules["required_fields"]:
                if field not in result:
                    return ValidationResult.INCOMPLETE, f"缺少必填字段: {field}"

        # 2. 类型检查
        if "type_checks" in rules:
            for field, expected_type in rules["type_checks"].items():
                if field in result and not isinstance(result[field], expected_type):
                    return ValidationResult.INVALID_FORMAT, f"字段 {field} 类型错误"

        # 3. 范围检查
        if "range_checks" in rules:
            for field, valid_range in rules["range_checks"].items():
                if field in result:
                    if isinstance(valid_range, list) and result[field] not in valid_range:
                        return ValidationResult.UNREASONABLE, f"字段 {field} 值不在有效范围"
                    elif isinstance(valid_range, tuple) and len(valid_range) == 2:
                        min_val, max_val = valid_range
                        if not (min_val <= result[field] <= max_val):
                            return ValidationResult.UNREASONABLE, f"字段 {field} 值超出范围"

        # 4. 最小长度检查
        if "min_length_checks" in rules:
            for field, min_length in rules["min_length_checks"].items():
                if field in result and (
                    isinstance(result[field], (list, dict, str))
                    and len(result[field]) < min_length
                ):
                    return ValidationResult.INCONSISTENT, f"字段 {field} 长度不足"

        # 5. 通用合理性检查
        if not self._check_reasonable(tool_name, result):
            return ValidationResult.UNREASONABLE, "结果值不合理"

        return ValidationResult.VALID, None

    def _check_reasonable(self, tool_name: str, result: dict[str, Any]) -> bool:
        """检查结果是否合理"""
        # 检查空字符串
        for key, value in result.items():
            if isinstance(value, str) and len(value.strip()) == 0:
                logger.warning(f"工具 {tool_name} 的字段 {key} 为空字符串")
                return False

        # 检查负数(特定字段)
        if "execution_time" in result and result["execution_time"] < 0:
            return False

        return not ("duration_ms" in result and result["duration_ms"] < 0)


class FullLinkMonitoringSystem:
    """
    全链路监控系统

    核心功能:
    1. 链路追踪 - 完整的调用链路追踪
    2. 性能监控 - 实时性能指标收集
    3. 异常告警 - 智能异常检测和告警
    4. 结果验证 - 自动验证调用结果
    5. 系统监控 - 系统资源使用监控
    """

    def __init__(self, config: SpanConfig | None = None):
        # 配置
        self.config = config or SpanConfig()

        # 链路存储
        self.active_traces: dict[str, LinkTrace] = {}
        self.completed_traces: deque = deque(maxlen=10000)
        self.trace_index: dict[str, str] = {}  # operation -> trace_id

        # 指标存储
        self.metrics: deque = deque(maxlen=100000)
        self.metric_aggregates: dict[str, dict[str, float]] = defaultdict(
            lambda: {"count": 0, "sum": 0.0, "min": float("inf"), "max": float("-inf"), "avg": 0.0}
        )

        # 告警
        self.alerts: list[Alert] = []
        self.alert_rules: list[dict[str, Any]] = []
        self._setup_default_alert_rules()

        # 验证器
        self.validator = ResultValidator()

        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=4)

        # 存储路径
        self.data_dir = Path("logs/monitoring")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 线程安全
        self.lock = threading.RLock()

        # 启动后台任务
        self._running = True
        self._start_background_tasks()

        logger.info("🔍 Athena全链路监控系统初始化完成")
        logger.info(f"📊 数据目录: {self.data_dir}")
        logger.info(f"⚡ 慢请求阈值: {self.config.slow_threshold_ms}ms")
        logger.info(f"🚨 错误率阈值: {self.config.error_threshold_percent}%")

    def _setup_default_alert_rules(self) -> Any:
        """设置默认告警规则"""
        self.alert_rules = [
            {
                "name": "工具调用失败率过高",
                "condition": lambda metrics: metrics.get("error_rate", 0) > 5.0,
                "severity": AlertSeverity.ERROR,
                "cooldown_seconds": 60,
            },
            {
                "name": "工具响应时间过长",
                "condition": lambda metrics: metrics.get("p95_latency_ms", 0) > 1000,
                "severity": AlertSeverity.WARNING,
                "cooldown_seconds": 30,
            },
            {
                "name": "内存使用率过高",
                "condition": lambda metrics: metrics.get("memory_percent", 0) > 80,
                "severity": AlertSeverity.WARNING,
                "cooldown_seconds": 120,
            },
            {
                "name": "CPU使用率过高",
                "condition": lambda metrics: metrics.get("cpu_percent", 0) > 90,
                "severity": AlertSeverity.ERROR,
                "cooldown_seconds": 60,
            },
            {
                "name": "结果验证失败率过高",
                "condition": lambda metrics: metrics.get("validation_failure_rate", 0) > 10,
                "severity": AlertSeverity.ERROR,
                "cooldown_seconds": 120,
            },
        ]

    def _start_background_tasks(self) -> Any:
        """启动后台任务"""
        # 定期聚合指标
        threading.Thread(target=self._aggregate_metrics_loop, daemon=True).start()

        # 定期检查告警
        threading.Thread(target=self._check_alerts_loop, daemon=True).start()

        # 定期保存数据
        threading.Thread(target=self._persist_data_loop, daemon=True).start()

    def _aggregate_metrics_loop(self) -> Any:
        """定期聚合指标"""
        while self._running:
            try:
                time.sleep(60)  # 每分钟聚合一次
                self._aggregate_metrics()
            except Exception as e:
                logger.error(f"❌ 指标聚合失败: {e}")

    def _check_alerts_loop(self) -> Any:
        """定期检查告警"""
        while self._running:
            try:
                time.sleep(30)  # 每30秒检查一次
                self._check_alerts()
            except Exception as e:
                logger.error(f"❌ 告警检查失败: {e}")

    def _persist_data_loop(self) -> Any:
        """定期保存数据"""
        while self._running:
            try:
                time.sleep(300)  # 每5分钟保存一次
                self._persist_data()
            except Exception as e:
                logger.error(f"❌ 数据持久化失败: {e}")

    def start_trace(
        self,
        operation: str,
        parent_trace_id: str | None = None,
        input_data: dict[str, Any] | None = None,
        tags: dict[str, str] | None = None,
    ) -> str:
        """
        开始链路追踪

        Args:
            operation: 操作名称
            parent_trace_id: 父追踪ID
            input_data: 输入数据
            tags: 标签

        Returns:
            追踪ID
        """
        trace_id = str(uuid.uuid4())

        trace = LinkTrace(
            trace_id=trace_id,
            parent_trace_id=parent_trace_id,
            operation=operation,
            input_data=input_data,
            tags=tags or {},
        )

        with self.lock:
            self.active_traces[trace_id] = trace
            self.trace_index[operation] = trace_id

            # 如果有父追踪,添加到父追踪的子列表
            if parent_trace_id and parent_trace_id in self.active_traces:
                self.active_traces[parent_trace_id].children.append(trace_id)

        logger.debug(f"🔍 开始追踪: {operation} (trace_id: {trace_id[:8]})")
        return trace_id

    def finish_trace(
        self,
        trace_id: str,
        output_data: dict[str, Any] | None = None,
        status: str = "success",
        error: str | None = None,
    ) -> LinkTrace:
        """
        完成链路追踪

        Args:
            trace_id: 追踪ID
            output_data: 输出数据
            status: 状态
            error: 错误信息

        Returns:
            完成的追踪对象
        """
        with self.lock:
            if trace_id not in self.active_traces:
                logger.warning(f"⚠️ 追踪ID不存在: {trace_id}")
                return None

            trace = self.active_traces[trace_id]
            trace.end_time = datetime.now()
            trace.output_data = output_data
            trace.status = status
            trace.error = error
            trace.duration_ms = (trace.end_time - trace.start_time).total_seconds() * 1000

            # 添加性能指标
            trace.metrics["duration_ms"] = trace.duration_ms

            # 移动到已完成追踪
            self.completed_traces.append(trace.to_dict())
            del self.active_traces[trace_id]

            if trace.operation in self.trace_index:
                del self.trace_index[trace.operation]

        # 记录指标
        self._record_metrics(trace)

        logger.debug(
            f"✅ 完成追踪: {trace.operation} " f"(耗时: {trace.duration_ms:.2f}ms, 状态: {status})"
        )

        return trace

    def _record_metrics(self, trace: LinkTrace) -> Any:
        """记录指标"""
        # 响应时间指标
        self.add_metric(
            MetricPoint(
                name=f"{trace.operation}.duration_ms",
                type=MetricType.HISTOGRAM,
                value=trace.duration_ms,
                labels={"operation": trace.operation, "status": trace.status},
            )
        )

        # 状态计数
        self.add_metric(
            MetricPoint(
                name=f"{trace.operation}.count",
                type=MetricType.COUNTER,
                value=1,
                labels={"operation": trace.operation, "status": trace.status},
            )
        )

        # 系统资源指标
        self._record_system_metrics()

    def _record_system_metrics(self) -> Any:
        """记录系统资源指标"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.add_metric(
                MetricPoint(name="system.cpu.percent", type=MetricType.GAUGE, value=cpu_percent)
            )

            # 内存
            memory = psutil.virtual_memory()
            self.add_metric(
                MetricPoint(
                    name="system.memory.percent", type=MetricType.GAUGE, value=memory.percent
                )
            )
            self.add_metric(
                MetricPoint(
                    name="system.memory.available_gb",
                    type=MetricType.GAUGE,
                    value=memory.available / (1024**3),
                )
            )

            # 磁盘
            disk = psutil.disk_usage("/")
            self.add_metric(
                MetricPoint(name="system.disk.percent", type=MetricType.GAUGE, value=disk.percent)
            )

        except Exception as e:
            logger.error(f"❌ 系统指标记录失败: {e}")

    def add_metric(self, metric: MetricPoint) -> None:
        """添加指标"""
        with self.lock:
            self.metrics.append(metric)

            # 更新聚合
            key = f"{metric.name}_{hash(str(metric.labels))}"
            agg = self.metric_aggregates[key]
            agg["count"] += 1
            agg["sum"] += metric.value
            agg["min"] = min(agg["min"], metric.value)
            agg["max"] = max(agg["max"], metric.value)
            agg["avg"] = agg["sum"] / agg["count"]

    def _aggregate_metrics(self) -> Any:
        """聚合指标"""
        with self.lock:
            # 计算百分位数
            for operation in {m.name.split(".")[0] for m in self.metrics}:
                operation_metrics = [
                    m for m in self.metrics if m.name.startswith(f"{operation}.duration_ms")
                ]
                if operation_metrics:
                    values = sorted([m.value for m in operation_metrics])
                    n = len(values)
                    if n > 0:
                        p50 = values[int(n * 0.5)]
                        p95 = values[int(n * 0.95)]
                        p99 = values[int(n * 0.99)]

                        self.add_metric(
                            MetricPoint(
                                name=f"{operation}.latency.p50",
                                type=MetricType.GAUGE,
                                value=p50,
                                labels={"operation": operation},
                            )
                        )
                        self.add_metric(
                            MetricPoint(
                                name=f"{operation}.latency.p95",
                                type=MetricType.GAUGE,
                                value=p95,
                                labels={"operation": operation},
                            )
                        )
                        self.add_metric(
                            MetricPoint(
                                name=f"{operation}.latency.p99",
                                type=MetricType.GAUGE,
                                value=p99,
                                labels={"operation": operation},
                            )
                        )

    def _check_alerts(self) -> Any:
        """检查告警"""
        current_metrics = self.get_current_metrics()

        for rule in self.alert_rules:
            try:
                if rule["condition"](current_metrics):
                    # 检查冷却时间
                    last_alert = next(
                        (a for a in self.alerts if a.rule_name == rule["name"] and not a.resolved),
                        None,
                    )
                    if last_alert:
                        time_since_last = (datetime.now() - last_alert.timestamp).total_seconds()
                        if time_since_last < rule["cooldown_seconds"]:
                            continue

                    # 创建告警
                    alert = Alert(
                        rule_name=rule["name"],
                        severity=rule["severity"],
                        message=f"{rule['name']}: {current_metrics}",
                        metrics=current_metrics,
                    )
                    self.alerts.append(alert)

                    logger.warning(
                        f"🚨 触发告警: {rule['name']} " f"(严重程度: {rule['severity'].value})"
                    )

            except Exception as e:
                logger.error(f"❌ 告警检查失败: {rule['name']} - {e}")

    def get_current_metrics(self) -> dict[str, Any]:
        """获取当前指标"""
        with self.lock:
            metrics = {}

            # 从最近的指标中聚合
            recent_metrics = list(self.metrics)[-1000:]

            # 计算错误率
            error_count = sum(
                1
                for m in recent_metrics
                if m.name.endswith(".count") and m.labels.get("status") in ["failed", "error"]
            )
            total_count = sum(1 for m in recent_metrics if m.name.endswith(".count"))
            metrics["error_rate"] = (error_count / total_count * 100) if total_count > 0 else 0

            # 计算P95延迟
            latency_metrics = [m.value for m in recent_metrics if m.name.endswith(".duration_ms")]
            if latency_metrics:
                latency_metrics.sort()
                n = len(latency_metrics)
                metrics["p95_latency_ms"] = latency_metrics[int(n * 0.95)] if n > 0 else 0
                metrics["avg_latency_ms"] = sum(latency_metrics) / n if n > 0 else 0

            # 系统指标
            system_metrics = [m for m in recent_metrics if m.name.startswith("system.")]
            for m in system_metrics:
                metrics[m.name] = m.value

            return metrics

    def validate_result(
        self, tool_name: str, result: Any, trace_id: str | None = None
    ) -> tuple[ValidationResult, str | None]:
        """
        验证工具调用结果

        Args:
            tool_name: 工具名称
            result: 调用结果
            trace_id: 追踪ID

        Returns:
            (验证结果, 错误消息)
        """
        validation_result, error_msg = self.validator.validate(tool_name, result)

        # 记录验证指标
        self.add_metric(
            MetricPoint(
                name=f"{tool_name}.validation",
                type=MetricType.COUNTER,
                value=1,
                labels={"tool": tool_name, "result": validation_result.value},
            )
        )

        # 如果验证失败且有关联的追踪,更新追踪
        if trace_id and validation_result != ValidationResult.VALID:
            with self.lock:
                if trace_id in self.active_traces:
                    self.active_traces[trace_id].metadata[
                        "validation_result"
                    ] = validation_result.value
                    self.active_traces[trace_id].metadata["validation_error"] = error_msg

        if validation_result != ValidationResult.VALID:
            logger.warning(f"⚠️ 结果验证失败: {tool_name} - {validation_result.value}: {error_msg}")

        return validation_result, error_msg

    def get_trace(self, trace_id: str) -> dict[str, Any] | None:
        """获取追踪信息"""
        with self.lock:
            if trace_id in self.active_traces:
                return self.active_traces[trace_id].to_dict()

            # 在已完成追踪中查找
            for trace in self.completed_traces:
                if trace["trace_id"] == trace_id:
                    return trace

        return None

    def get_traces_by_operation(self, operation: str, limit: int = 10) -> list[dict[str, Any]]:
        """根据操作获取追踪"""
        with self.lock:
            traces = [t.to_dict() for t in self.active_traces.values() if t.operation == operation]
            traces.extend([t for t in self.completed_traces if t["operation"] == operation])
            return traces[-limit:]

    def get_metrics_summary(self) -> dict[str, Any]:
        """获取指标摘要"""
        with self.lock:
            summary = {
                "total_metrics": len(self.metrics),
                "active_traces": len(self.active_traces),
                "completed_traces": len(self.completed_traces),
                "total_alerts": len(self.alerts),
                "unresolved_alerts": sum(1 for a in self.alerts if not a.resolved),
                "metric_aggregates": dict(self.metric_aggregates),
            }
            return summary

    def get_dashboard_data(self) -> dict[str, Any]:
        """获取监控仪表板数据"""
        current_metrics = self.get_current_metrics()

        # 最近的追踪
        recent_traces = list(self.completed_traces)[-20:]

        # 活跃告警
        active_alerts = [a.to_dict() for a in self.alerts if not a.resolved][-10:]

        # 性能统计
        performance_stats = self._calculate_performance_stats()

        return {
            "timestamp": datetime.now().isoformat(),
            "current_metrics": current_metrics,
            "recent_traces": recent_traces,
            "active_alerts": active_alerts,
            "performance_stats": performance_stats,
            "summary": self.get_metrics_summary(),
        }

    def _calculate_performance_stats(self) -> dict[str, Any]:
        """计算性能统计"""
        with self.lock:
            stats = {
                "operations": {},
                "total_requests": 0,
                "total_errors": 0,
                "overall_success_rate": 0.0,
            }

            # 按操作聚合统计
            operation_stats = defaultdict(lambda: {"count": 0, "errors": 0, "durations": []})

            for trace in self.completed_traces:
                op = trace["operation"]
                operation_stats[op]["count"] += 1
                if trace["status"] in ["failed", "error", "timeout"]:
                    operation_stats[op]["errors"] += 1
                if "duration_ms" in trace["metrics"]:
                    operation_stats[op]["durations"].append(trace["metrics"]["duration_ms"])

            # 计算每个操作的统计
            for op, op_stat in operation_stats.items():
                durations = op_stat["durations"]
                stats["operations"][op] = {
                    "count": op_stat["count"],
                    "errors": op_stat["errors"],
                    "error_rate": (
                        (op_stat["errors"] / op_stat["count"] * 100) if op_stat["count"] > 0 else 0
                    ),
                    "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
                    "p95_duration_ms": (
                        sorted(durations)[int(len(durations) * 0.95)] if len(durations) > 0 else 0
                    ),
                }
                stats["total_requests"] += op_stat["count"]
                stats["total_errors"] += op_stat["errors"]

            # 整体成功率
            if stats["total_requests"] > 0:
                stats["overall_success_rate"] = (
                    (stats["total_requests"] - stats["total_errors"])
                    / stats["total_requests"]
                    * 100
                )

            return stats

    def _persist_data(self) -> Any:
        """持久化数据"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # 保存追踪数据
            traces_file = self.data_dir / f"traces_{timestamp}.json"
            with open(traces_file, "w", encoding="utf-8") as f:
                json.dump(list(self.completed_traces), f, ensure_ascii=False, indent=2)

            # 保存指标数据
            metrics_file = self.data_dir / f"metrics_{timestamp}.json"
            with open(metrics_file, "w", encoding="utf-8") as f:
                json.dump([m.to_dict() for m in self.metrics], f, ensure_ascii=False, indent=2)

            # 保存告警数据
            alerts_file = self.data_dir / f"alerts_{timestamp}.json"
            with open(alerts_file, "w", encoding="utf-8") as f:
                json.dump([a.to_dict() for a in self.alerts], f, ensure_ascii=False, indent=2)

            logger.info(
                f"💾 数据已保存: {traces_file.name}, {metrics_file.name}, {alerts_file.name}"
            )

        except Exception as e:
            logger.error(f"❌ 数据持久化失败: {e}")

    def cleanup(self) -> Any:
        """清理资源"""
        logger.info("🧹 正在清理监控系统...")
        self._running = False
        self._persist_data()
        logger.info("✅ 监控系统清理完成")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()


# 全局单例
_monitoring_system: FullLinkMonitoringSystem | None = None


def get_monitoring_system() -> FullLinkMonitoringSystem:
    """获取全链路监控系统单例"""
    global _monitoring_system
    if _monitoring_system is None:
        _monitoring_system = FullLinkMonitoringSystem()
    return _monitoring_system


# 便捷装饰器
def trace_operation(operation: str | None = None, tags: dict[str, str] | None | None = None) -> Any:
    """追踪操作的装饰器"""
    monitor = get_monitoring_system()

    def decorator(func: Callable) -> Any:
        def sync_wrapper(*args, **kwargs) -> Any:
            trace_id = monitor.start_trace(operation, tags=tags)
            try:
                result = func(*args, **kwargs)
                monitor.finish_trace(trace_id, status="success")
                return result
            except Exception as e:
                monitor.finish_trace(trace_id, status="failed", error=str(e))
                raise

        async def async_wrapper(*args, **kwargs):
            trace_id = monitor.start_trace(operation, tags=tags)
            try:
                result = await func(*args, **kwargs)
                monitor.finish_trace(trace_id, status="success")
                return result
            except Exception as e:
                monitor.finish_trace(trace_id, status="failed", error=str(e))
                raise

        # 判断是否是协程函数
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# 测试
async def test_full_link_monitoring():
    """测试全链路监控系统"""
    print("🧪 测试Athena全链路监控系统")
    print("=" * 60)

    monitor = get_monitoring_system()

    # 测试链路追踪
    print("\n📝 测试链路追踪")
    trace_id = monitor.start_trace("test_operation", input_data={"test": "data"})
    time.sleep(0.1)
    monitor.finish_trace(trace_id, output_data={"result": "success"})

    # 测试指标记录
    print("\n📊 测试指标记录")
    monitor.add_metric(MetricPoint(name="test.metric", type=MetricType.GAUGE, value=42.0))

    # 测试结果验证
    print("\n✅ 测试结果验证")
    result = {"analysis": "test", "complexity": "低", "lines": 10}
    validation_result, _error = monitor.validate_result("code_analyzer", result)
    print(f"验证结果: {validation_result.value}")

    # 获取仪表板数据
    print("\n📈 监控仪表板")
    dashboard = monitor.get_dashboard_data()
    print(json.dumps(dashboard, indent=2, ensure_ascii=False))

    print("\n✅ 测试完成!")


if __name__ == "__main__":
    asyncio.run(test_full_link_monitoring())
