#!/usr/bin/env python3
"""
小诺调用链路监控系统
Xiaonuo Call Chain Monitoring System

实现端到端调用链路追踪和监控,包括:
1. 分布式追踪 - 请求链路完整追踪
2. 性能监控 - 实时性能指标收集
3. 异常检测 - 智能异常发现和告警
4. 可视化支持 - 调用链路图谱生成
5. 性能分析 - 瓶颈识别和优化建议

作者: 小诺AI团队
日期: 2025-12-18
"""

from __future__ import annotations
import json
import os
import queue
import threading
import time
import uuid
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

import numpy as np

from core.logging_config import setup_logging

if TYPE_CHECKING:
    from collections.abc import Callable

from core.monitoring.alerting_system import Alert

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


@dataclass
class SpanConfig:
    """追踪配置"""

    # 追踪配置
    service_name: str = "xiaonuo-nlp"
    service_version: str = "1.0.0"
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


@dataclass
class Span:
    """调用链路追踪信息"""

    trace_id: str  # 追踪ID
    span_id: str  # 当前span ID
    parent_span_id: str  # 父span ID
    operation_name: str  # 操作名称
    start_time: datetime  # 开始时间
    end_time: datetime | None = None  # 结束时间
    duration_ms: float | None = None  # 持续时间(毫秒)

    # 状态和结果
    status: str = "unknown"  # unknown, success, error, timeout
    error_message: str | None = None  # 错误信息
    result: Any | None = None  # 结果数据

    # 标签和注解
    tags: dict[str, str] = field(default_factory=dict)  # 标签
    annotations: dict[str, Any] = field(default_factory=dict)  # 注解
    metrics: dict[str, float] = field(default_factory=dict)  # 指标

    # 元数据
    service_name: str = "xiaonuo-nlp"
    resource: str = ""  # 资源标识
    component: str = ""  # 组件名称


@dataclass
class TraceContext:
    """追踪上下文"""

    trace_id: str
    spans: dict[str, Span] = field(default_factory=dict)
    root_span: str | None = None
    start_time: datetime = field(default_factory=datetime.now)

    # 性能统计
    total_duration_ms: float = 0.0
    span_count: int = 0
    success_count: int = 0
    error_count: int = 0

    # 采样信息
    sampled: bool = True
    sample_rate: float = 1.0


@dataclass
class AlertRule:
    """告警规则"""

    name: str
    condition: str  # 告警条件
    threshold: float  # 阈值
    severity: str = "warning"  # 严重级别: info, warning, error, critical
    cooldown_seconds: int = 60  # 冷却时间
    enabled: bool = True  # 是否启用
    last_triggered: datetime | None = None  # 上次触发时间


@dataclass
class PerformanceMetrics:
    """性能指标"""

    request_count: int = 0
    success_count: int = 0
    error_count: int = 0
    timeout_count: int = 0

    # 时间统计
    avg_duration_ms: float = 0.0
    max_duration_ms: float = 0.0
    min_duration_ms: float = float("inf")
    p95_duration_ms: float = 0.0
    p99_duration_ms: float = 0.0

    # 吞吐量
    requests_per_second: float = 0.0

    # 错误率
    error_rate: float = 0.0
    timeout_rate: float = 0.0


class CallChainMonitor:
    """调用链路监控器"""

    def __init__(self, config: SpanConfig = None):
        self.config = config or SpanConfig()

        # 追踪存储
        self.active_traces: dict[str, TraceContext] = {}
        self.completed_traces: deque = deque(maxlen=self.config.span_history_size)

        # 性能指标
        self.metrics = PerformanceMetrics()
        self.metrics_history: deque = deque(maxlen=1000)

        # 告警系统
        self.alert_rules: list[AlertRule] = []
        self.alerts: list[Alert] = []
        self.alert_queue = queue.Queue()

        # 追踪历史
        self.trace_history: deque = deque(maxlen=10000)

        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=4)

        # 链路追踪
        self._setup_default_alert_rules()

        # 线程安全
        self.lock = threading.RLock()

        logger.info("🔍 小诺调用链路监控系统初始化完成")
        logger.info(f"📊 服务名称: {self.config.service_name}")
        logger.info(f"⚡ 慢请求阈值: {self.config.slow_threshold_ms}ms")
        logger.info(f"🚨 错误率阈值: {self.config.error_threshold_percent}%")

    def _setup_default_alert_rules(self) -> Any:
        """设置默认告警规则"""
        default_rules = [
            AlertRule(
                name="高错误率",
                condition="error_rate > threshold",
                threshold=self.config.error_threshold_percent,
                severity="error",
            ),
            AlertRule(
                name="请求延迟过高",
                condition="p95_duration_ms > threshold",
                threshold=self.config.slow_threshold_ms,
                severity="warning",
            ),
            AlertRule(
                name="超时率过高",
                condition="timeout_rate > threshold",
                threshold=1.0,
                severity="error",
            ),
            AlertRule(
                name="吞吐量异常",
                condition="requests_per_second < threshold",
                threshold=0.1,
                severity="warning",
            ),
        ]

        self.alert_rules.extend(default_rules)
        logger.info(f"📋 已配置 {len(default_rules)} 个默认告警规则")

    def start_trace(
        self,
        operation_name: str,
        parent_span_id: str | None = None,
        tags: dict[str, str] | None = None,
    ) -> Span:
        """开始追踪"""
        with self.lock:
            # 生成trace_id和span_id
            trace_id = getattr(threading.current_thread(), "trace_id", None)
            if trace_id is None:
                trace_id = str(uuid.uuid4())
                threading.current_thread().trace_id = trace_id

            span_id = str(uuid.uuid4())

            # 创建span
            span = Span(
                trace_id=trace_id,
                span_id=span_id,
                parent_span_id=parent_span_id,
                operation_name=operation_name,
                start_time=datetime.now(),
                tags=tags or {},
                service_name=self.config.service_name,
                component=operation_name.split(".")[0] if "." in operation_name else operation_name,
            )

            # 获取或创建追踪上下文
            if trace_id not in self.active_traces:
                self.active_traces[trace_id] = TraceContext(
                    trace_id=trace_id,
                    sampled=(hash(trace_id) % 100) < int(self.config.sample_rate * 100),
                )
                self.active_traces[trace_id].root_span = span_id

            context = self.active_traces[trace_id]
            if context.sampled:
                context.spans[span_id] = span
                context.span_count += 1

                # 如果是根span,设置开始时间
                if parent_span_id is None:
                    context.start_time = span.start_time

        logger.debug(f"🔍 开始追踪: {operation_name} (span_id: {span_id[:8]})")
        return span

    def finish_span(
        self,
        span: Span,
        status: str = "success",
        error_message: str | None = None,
        result: Any = None,
    ) -> Span:
        """完成追踪"""
        with self.lock:
            # 更新span信息
            span.end_time = datetime.now()
            span.duration_ms = (span.end_time - span.start_time).total_seconds() * 1000
            span.status = status
            span.error_message = error_message
            span.result = result

            # 更新追踪上下文
            if span.trace_id in self.active_traces:
                context = self.active_traces[span.trace_id]
                context.total_duration_ms += span.duration_ms

                if status == "error" or status == "timeout":
                    context.error_count += 1
                elif status == "success":
                    context.success_count += 1

        # 更新全局指标
        self._update_metrics(span)

        logger.debug(
            f"✅ 完成追踪: {span.operation_name} "
            f"(耗时: {span.duration_ms:.2f}ms, 状态: {status})"
        )

        return span

    def record_function_call(self, operation_name: str, tags: dict[str, str] | None = None) -> Any:
        """记录函数调用的装饰器"""

        def decorator(func: Callable) -> Any:
            def wrapper(*args, **kwargs) -> Any:
                span = self.start_trace(operation_name, tags=tags)

                try:
                    start_time = time.time()
                    result = func(*args, **kwargs)
                    duration = (time.time() - start_time) * 1000

                    # 添加性能指标
                    span.metrics["duration_ms"] = duration
                    span.annotations["args_count"] = len(args)
                    span.annotations["kwargs_count"] = len(kwargs)

                    return self.finish_span(span, "success", result=result)

                except Exception as e:
                    error_message = f"{type(e).__name__}: {e!s}"
                    logger.error(f"❌ 函数调用失败: {operation_name} - {error_message}")
                    return self.finish_span(span, "error", error_message=error_message)

                except TimeoutError as e:
                    timeout_message = f"超时: {e!s}"
                    logger.error(f"⏰ 函数调用超时: {operation_name}")
                    return self.finish_span(span, "timeout", error_message=timeout_message)

            return wrapper

        return decorator

    def trace_pipeline_step(self, step_name: str, input_data: Any = None, output_data: Any = None):
        """追踪管道步骤的装饰器"""

        def decorator(func: Callable) -> Any:
            def wrapper(*args, **kwargs) -> Any:
                span = self.start_trace(f"pipeline.{step_name}")

                # 记录输入数据大小
                if input_data is not None:
                    span.annotations["input_size"] = len(str(input_data))

                try:
                    start_time = time.time()
                    result = func(*args, **kwargs)
                    duration = (time.time() - start_time) * 1000

                    # 记录输出数据大小
                    if output_data is not None:
                        span.annotations["output_size"] = len(str(output_data))

                    span.metrics["step_duration_ms"] = duration

                    return self.finish_span(span, "success", result=result)

                except Exception as e:
                    error_message = f"{type(e).__name__}: {e!s}"
                    logger.error(f"❌ 管道步骤失败: {step_name} - {error_message}")
                    return self.finish_span(span, "error", error_message=error_message)

            return wrapper

        return decorator

    def _update_metrics(self, span: Span) -> Any:
        """更新性能指标"""
        with self.lock:
            self.metrics.request_count += 1

            # 状态统计
            if span.status == "success":
                self.metrics.success_count += 1
            elif span.status == "error":
                self.metrics.error_count += 1
            elif span.status == "timeout":
                self.metrics.timeout_count += 1

            # 时间统计
            if span.duration_ms is not None:
                self.metrics.avg_duration_ms = (
                    self.metrics.avg_duration_ms * (self.metrics.request_count - 1)
                    + span.duration_ms
                ) / self.metrics.request_count
                self.metrics.max_duration_ms = max(self.metrics.max_duration_ms, span.duration_ms)
                self.metrics.min_duration_ms = min(self.metrics.min_duration_ms, span.duration_ms)

        # 定期计算百分位数和吞吐量
        if self.metrics.request_count % 100 == 0:
            self._calculate_percentiles()
            self._calculate_throughput()

            # 检查告警
            if self.config.enable_realtime_alerts:
                self._check_alerts()

    def _calculate_percentiles(self) -> Any:
        """计算延迟百分位数"""
        with self.lock:
            # 从历史数据中计算百分位数
            durations = []
            for context in list(self.active_traces.values()):
                for span in context.spans.values():
                    if span.duration_ms is not None:
                        durations.append(span.duration_ms)

            if durations:
                durations.sort()
                n = len(durations)
                self.metrics.p95_duration_ms = durations[int(n * 0.95)] if n > 0 else 0
                self.metrics.p99_duration_ms = durations[int(n * 0.99)] if n > 0 else 0

    def _calculate_throughput(self) -> Any:
        """计算吞吐量"""
        with self.lock:
            # 计算最近时间窗口内的请求速率
            now = datetime.now()
            window_start = now - timedelta(seconds=self.config.metrics_window_seconds)

            recent_requests = 0
            for context in list(self.active_traces.values()):
                for span in context.spans.values():
                    if span.start_time >= window_start:
                        recent_requests += 1

            self.metrics.requests_per_second = recent_requests / self.config.metrics_window_seconds

    def _check_alerts(self) -> Any:
        """检查告警条件"""
        now = datetime.now()

        for rule in self.alert_rules:
            if not rule.enabled:
                continue

            # 检查冷却时间
            if (
                rule.last_triggered
                and (now - rule.last_triggered).total_seconds() < rule.cooldown_seconds
            ):
                continue

            # 评估告警条件
            if self._evaluate_alert_condition(rule):
                rule.last_triggered = now
                self._trigger_alert(rule)

    def _evaluate_alert_condition(self, rule: AlertRule) -> bool:
        """评估告警条件"""
        try:
            # 这里可以扩展更复杂的条件评估逻辑
            if rule.condition == "error_rate > threshold":
                return self.metrics.error_rate > rule.threshold
            elif rule.condition == "p95_duration_ms > threshold":
                return self.metrics.p95_duration_ms > rule.threshold
            elif rule.condition == "timeout_rate > threshold":
                timeout_rate = (
                    self.metrics.timeout_count / max(1, self.metrics.request_count)
                ) * 100
                return timeout_rate > rule.threshold
            elif rule.condition == "requests_per_second < threshold":
                return self.metrics.requests_per_second < rule.threshold

        except Exception as e:
            logger.error(f"❌ 告警条件评估失败: {rule.name} - {e}")

        return False

    def _trigger_alert(self, rule: AlertRule) -> Any:
        """触发告警"""
        alert_data = {
            "rule_name": rule.name,
            "severity": rule.severity,
            "threshold": rule.threshold,
            "current_metrics": asdict(self.metrics),
            "timestamp": datetime.now().isoformat(),
            "trace_id": getattr(threading.current_thread(), "trace_id", "unknown"),
        }

        self.alert_queue.put(alert_data)
        logger.warning(f"🚨 触发告警: {rule.name} (严重程度: {rule.severity})")

        # 异步处理告警
        self.executor.submit(self._process_alert, alert_data)

    def _process_alert(self, alert_data: dict[str, Any]) -> Any:
        """处理告警"""
        try:
            # 这里可以扩展告警处理逻辑,如发送邮件、短信、Slack通知等
            logger.info(f"📧 处理告警: {alert_data['rule_name']}")

            # 示例:记录到文件
            alert_file = f"data/alerts/alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            os.makedirs(os.path.dirname(alert_file), exist_ok=True)

            with open(alert_file, "w", encoding="utf-8") as f:
                json.dump(alert_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"❌ 告警处理失败: {e}")

    def get_trace_summary(self, trace_id: str) -> dict[str, Any]:
        """获取追踪摘要"""
        with self.lock:
            if trace_id not in self.active_traces:
                return {"error": f"追踪ID {trace_id} 不存在"}

            context = self.active_traces[trace_id]
            spans = list(context.spans.values())

            # 统计信息
            spans_by_status = defaultdict(int)
            spans_by_operation = defaultdict(int)

            for span in spans:
                spans_by_status[span.status] += 1
                spans_by_operation[span.operation_name] += 1

            return {
                "trace_id": trace_id,
                "span_count": len(spans),
                "total_duration_ms": context.total_duration_ms,
                "error_count": context.error_count,
                "sampled": context.sampled,
                "sample_rate": context.sample_rate,
                "spans_by_status": dict(spans_by_status),
                "spans_by_operation": dict(spans_by_operation),
                "start_time": context.start_time.isoformat(),
                "root_span": context.root_span,
            }

    def get_performance_dashboard(self) -> dict[str, Any]:
        """获取性能仪表板数据"""
        with self.lock:
            # 计算错误率
            total_requests = self.metrics.request_count
            error_rate = (
                (self.metrics.error_count / total_requests * 100) if total_requests > 0 else 0
            )
            timeout_rate = (
                (self.metrics.timeout_count / total_requests * 100) if total_requests > 0 else 0
            )

            # 活跃追踪数量
            active_trace_count = len(self.active_traces)
            active_span_count = sum(len(ctx.spans) for ctx in self.active_traces.values())

            # 待处理告警数量
            pending_alerts = self.alert_queue.qsize()

            return {
                "performance_metrics": asdict(self.metrics),
                "calculated_metrics": {
                    "error_rate": error_rate,
                    "timeout_rate": timeout_rate,
                    "success_rate": (
                        (self.metrics.success_count / total_requests * 100)
                        if total_requests > 0
                        else 0
                    ),
                },
                "active_traces": {
                    "trace_count": active_trace_count,
                    "span_count": active_span_count,
                },
                "alerts": {
                    "pending_count": pending_alerts,
                    "rules_count": len(self.alert_rules),
                    "enabled_rules": sum(1 for rule in self.alert_rules if rule.enabled),
                },
                "system_info": {
                    "service_name": self.config.service_name,
                    "service_version": self.config.service_version,
                    "environment": self.config.environment,
                    "sample_rate": self.config.sample_rate,
                    "monitoring_time": datetime.now().isoformat(),
                },
            }

    def export_traces(self, filepath: str, filter_condition: dict[str, Any] | None = None) -> Any:
        """导出追踪数据"""
        try:
            all_traces = []

            # 导出活跃追踪
            with self.lock:
                for trace_id, context in self.active_traces.items():
                    trace_data = {
                        "trace_id": trace_id,
                        "context": asdict(context),
                        "spans": [asdict(span) for span in context.spans.values()],
                    }
                    all_traces.append(trace_data)

                # 导出已完成追踪
                for trace_data in self.completed_traces:
                    all_traces.append(trace_data)

            # 应用过滤条件
            if filter_condition:
                filtered_traces = []
                for trace in all_traces:
                    match = True
                    for key, value in filter_condition.items():
                        if key not in trace or trace[key] != value:
                            match = False
                            break
                    if match:
                        filtered_traces.append(trace)
                all_traces = filtered_traces

            # 保存到文件
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(all_traces, f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"💾 导出 {len(all_traces)} 个追踪到: {filepath}")

        except Exception as e:
            logger.error(f"❌ 导出追踪数据失败: {e}")

    def cleanup_old_traces(self, max_age_hours: int = 24) -> Any:
        """清理过期追踪数据"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

            with self.lock:
                # 清理过期的活跃追踪
                expired_trace_ids = [
                    trace_id
                    for trace_id, context in self.active_traces.items()
                    if context.start_time < cutoff_time
                ]

                for trace_id in expired_trace_ids:
                    # 移动到已完成追踪
                    if trace_id in self.active_traces:
                        context = self.active_traces[trace_id]
                        trace_data = {
                            "trace_id": trace_id,
                            "context": asdict(context),
                            "spans": [asdict(span) for span in context.spans.values()],
                            "completed_at": datetime.now().isoformat(),
                            "cleanup_reason": "expired",
                        }
                        self.completed_traces.append(trace_data)
                        del self.active_traces[trace_id]

                logger.info(f"🧹 清理了 {len(expired_trace_ids)} 个过期追踪")

        except Exception as e:
            logger.error(f"❌ 清理过期追踪失败: {e}")

    def add_custom_alert_rule(self, rule: AlertRule) -> None:
        """添加自定义告警规则"""
        self.alert_rules.append(rule)
        logger.info(f"📋 添加自定义告警规则: {rule.name}")

    def get_alert_rules(self) -> list[dict[str, Any]]:
        """获取告警规则列表"""
        return [asdict(rule) for rule in self.alert_rules]

    def get_active_alerts(self) -> list[dict[str, Any]]:
        """获取当前活跃的告警"""
        try:
            with self.lock:
                return [
                    {
                        "alert_id": alert.alert_id,
                        "alert_type": alert.alert_type,
                        "severity": alert.severity,
                        "message": alert.message,
                        "timestamp": alert.timestamp.isoformat(),
                        "resolved": alert.resolved,
                    }
                    for alert in self.alerts
                    if not alert.resolved
                ]
        except Exception as e:
            logger.error(f"获取活跃告警失败: {e}")
            return []

    def generate_tracing_report(self, time_range_minutes: int = 60) -> dict[str, Any]:
        """生成指定时间范围内的追踪报告"""
        try:
            cutoff_time = datetime.now() - timedelta(minutes=time_range_minutes)

            with self.lock:
                # 收集时间范围内的追踪数据
                recent_traces = []
                for trace_id, context in self.active_traces.items():
                    if context.start_time >= cutoff_time:
                        recent_traces.append(
                            {
                                "trace_id": trace_id,
                                "start_time": context.start_time.isoformat(),
                                "duration_ms": context.total_duration_ms,
                                "span_count": context.span_count,
                                "success_count": context.success_count,
                                "error_count": context.error_count,
                            }
                        )

                # 收集历史追踪数据
                historical_traces = []
                for trace_data in self.trace_history:
                    trace_time = datetime.fromisoformat(trace_data.get("start_time", ""))
                    if trace_time >= cutoff_time:
                        historical_traces.append(trace_data)

                return {
                    "time_range_minutes": time_range_minutes,
                    "cutoff_time": cutoff_time.isoformat(),
                    "active_traces_count": len(recent_traces),
                    "historical_traces_count": len(historical_traces),
                    "total_traces": len(recent_traces) + len(historical_traces),
                    "traces": recent_traces + historical_traces,
                    "performance_summary": {
                        "avg_duration_ms": (
                            np.mean([t["duration_ms"] for t in recent_traces])
                            if recent_traces
                            else 0
                        ),
                        "total_spans": sum(t["span_count"] for t in recent_traces),
                        "success_rate": (
                            sum(t["success_count"] for t in recent_traces)
                            / max(
                                1, sum(t["success_count"] + t["error_count"] for t in recent_traces)
                            )
                        )
                        * 100,
                    },
                }

        except Exception as e:
            logger.error(f"生成追踪报告失败: {e}")
            return {"time_range_minutes": time_range_minutes, "error": str(e), "traces": []}

    def cleanup(self) -> None:
        """清理监控器资源"""
        try:
            logger.info("🧹 正在清理调用链路监控器资源...")

            with self.lock:
                # 清理活跃追踪
                self.active_traces.clear()

                # 清理追踪历史
                self.trace_history.clear()

                # 清理告警
                self.alerts.clear()

                # 重置性能统计
                self.metrics = PerformanceMetrics()

            logger.info("✅ 调用链路监控器资源清理完成")

        except Exception as e:
            logger.error(f"❌ 调用链路监控器资源清理失败: {e}")


# 创建全局监控实例
_global_monitor = None


def get_call_chain_monitor() -> CallChainMonitor:
    """获取全局调用链监控实例"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = CallChainMonitor()
    return _global_monitor


# 便捷装饰器
def trace_operation(operation_name: str | None = None, tags: dict[str, str] | None = None) -> Any:
    """追踪操作的便捷装饰器"""
    monitor = get_call_chain_monitor()
    return monitor.record_function_call(operation_name, tags)


def trace_pipeline_step(step_name: str) -> Any:
    """追踪管道步骤的便捷装饰器"""
    monitor = get_call_chain_monitor()
    return monitor.trace_pipeline_step(step_name)


# 测试代码
def test_call_chain_monitor() -> Any:
    """测试调用链路监控系统"""
    print("🧪 开始测试调用链路监控系统...")

    # 创建监控器
    config = SpanConfig(
        service_name="test-service",
        slow_threshold_ms=500.0,
        enable_realtime_alerts=False,  # 测试时关闭实时告警
    )
    monitor = CallChainMonitor(config)

    # 测试函数调用追踪
    @trace_operation("test_function", {"component": "test"})
    def test_function() -> Any:
        time.sleep(0.1)
        return "test result"

    # 测试管道步骤追踪
    @trace_pipeline_step("preprocessing")
    def preprocessing_step(data) -> None:
        time.sleep(0.05)
        return data.upper()

    @trace_pipeline_step("processing")
    def processing_step(data) -> None:
        time.sleep(0.1)
        return f"processed: {data}"

    # 执行测试
    print("\n📝 测试1: 函数调用追踪")
    result = test_function()
    print(f"结果: {result}")

    print("\n📝 测试2: 管道步骤追踪")
    pipeline_data = "hello world"
    pipeline_data = preprocessing_step(pipeline_data)
    pipeline_data = processing_step(pipeline_data)
    print(f"管道结果: {pipeline_data}")

    # 测试手动追踪
    print("\n📝 测试3: 手动追踪")
    span1 = monitor.start_trace("manual_operation", tags={"type": "manual"})
    time.sleep(0.15)
    monitor.finish_span(span1, "success", result="manual result")

    # 获取性能仪表板
    print("\n📊 性能仪表板:")
    dashboard = monitor.get_performance_dashboard()
    print(json.dumps(dashboard, indent=2, ensure_ascii=False, default=str))

    # 测试追踪摘要
    print("\n🔍 追踪摘要:")
    if monitor.active_traces:
        trace_id = next(iter(monitor.active_traces.keys()))
        summary = monitor.get_trace_summary(trace_id)
        print(json.dumps(summary, indent=2, ensure_ascii=False))

    # 清理资源
    monitor.cleanup_old_traces(0)  # 清理所有追踪
    print("\n✅ 调用链路监控系统测试完成!")


if __name__ == "__main__":
    test_call_chain_monitor()
