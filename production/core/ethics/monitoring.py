"""
伦理监控系统 - 实时监控AI系统的伦理合规性
Ethics Monitoring System - Real-time Ethics Compliance Monitoring

核心功能:
1. 实时监控伦理评估结果
2. 生成合规性指标和报告
3. 检测异常模式并触发告警
4. 提供可视化仪表板数据
5. 敏感信息过滤保护
"""

from __future__ import annotations
import logging
import os
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

from .evaluator import ActionSeverity, ComplianceStatus, EthicsEvaluator, EvaluationResult
from .sensitive_data_filter import filter_log

logger = setup_logging()


class AlertLevel(Enum):
    """告警级别"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class EthicsMetrics:
    """伦理指标"""

    total_evaluations: int = 0
    compliant_count: int = 0
    partial_count: int = 0
    non_compliant_count: int = 0
    critical_violations: int = 0
    high_violations: int = 0

    # 按原则统计
    principle_violations: dict[str, int] = field(default_factory=dict)

    # 按智能体统计
    agent_stats: dict[str, dict[str, int]] = field(default_factory=dict)

    # 时间序列数据
    timestamps: list[datetime] = field(default_factory=list)
    compliance_scores: list[float] = field(default_factory=list)

    @property
    def compliance_rate(self) -> float:
        """合规率"""
        if self.total_evaluations == 0:
            return 1.0
        return self.compliant_count / self.total_evaluations

    @property
    def violation_rate(self) -> float:
        """违规率"""
        if self.total_evaluations == 0:
            return 0.0
        return (self.partial_count + self.non_compliant_count) / self.total_evaluations


@dataclass
class Alert:
    """告警"""

    alert_id: str
    level: AlertLevel
    message: str
    agent_id: str
    principle_id: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class EthicsMonitor:
    """伦理监控器

    实时监控AI系统的伦理合规性
    """

    def __init__(
        self,
        evaluator: EthicsEvaluator | None = None,
        alert_threshold_violation_rate: float = 0.1,
        alert_threshold_critical: int = 3,
    ):
        self.evaluator = evaluator
        self.alert_threshold_violation_rate = alert_threshold_violation_rate
        self.alert_threshold_critical = alert_threshold_critical

        self.metrics = EthicsMetrics()
        self.alerts: list[Alert] = []
        self.alert_handlers: list[Callable[[Alert], None]] = []

        # 滑动窗口数据(最近N次评估)
        self.window_size = 100
        self.recent_evaluations: list[EvaluationResult] = []

    def record_evaluation(self, result: EvaluationResult) -> Any:
        """记录评估结果"""
        # 更新指标
        self.metrics.total_evaluations += 1

        if result.status == ComplianceStatus.COMPLIANT:
            self.metrics.compliant_count += 1
        elif result.status == ComplianceStatus.PARTIAL:
            self.metrics.partial_count += 1
        else:
            self.metrics.non_compliant_count += 1

        # 统计违规
        for violation in result.violations:
            principle_id = violation.principle_id
            self.metrics.principle_violations[principle_id] = (
                self.metrics.principle_violations.get(principle_id, 0) + 1
            )

        # 按智能体统计
        agent_id = result.agent_id
        if agent_id not in self.metrics.agent_stats:
            self.metrics.agent_stats[agent_id] = {
                "total": 0,
                "compliant": 0,
                "partial": 0,
                "non_compliant": 0,
            }

        self.metrics.agent_stats[agent_id]["total"] += 1
        if result.status == ComplianceStatus.COMPLIANT:
            self.metrics.agent_stats[agent_id]["compliant"] += 1
        elif result.status == ComplianceStatus.PARTIAL:
            self.metrics.agent_stats[agent_id]["partial"] += 1
        else:
            self.metrics.agent_stats[agent_id]["non_compliant"] += 1

        # 记录时间序列
        self.metrics.timestamps.append(result.evaluated_at)
        self.metrics.compliance_scores.append(result.overall_score)

        # 保持滑动窗口
        self.recent_evaluations.append(result)
        if len(self.recent_evaluations) > self.window_size:
            self.recent_evaluations.pop(0)

        # 检查告警条件
        self._check_alerts(result)

    def _check_alerts(self, result: EvaluationResult) -> Any:
        """检查是否需要告警"""

        # 关键违规告警
        critical_violations = [v for v in result.violations if v.principle_priority >= 10]

        if critical_violations:
            self.metrics.critical_violations += 1

            if self.metrics.critical_violations >= self.alert_threshold_critical:
                self._create_alert(
                    level=AlertLevel.CRITICAL,
                    message=f"关键违规次数达到阈值:{self.metrics.critical_violations}",
                    agent_id=result.agent_id,
                    principle_id=critical_violations[0].principle_id,
                )

        # 高严重度告警
        if result.severity == ActionSeverity.CRITICAL:
            self.metrics.high_violations += 1
            self._create_alert(
                level=AlertLevel.ERROR,
                message=f"检测到高严重度违规:{result.action}",
                agent_id=result.agent_id,
            )

        # 违规率告警
        if self.metrics.total_evaluations >= 10:
            violation_rate = self.metrics.violation_rate
            if violation_rate > self.alert_threshold_violation_rate:
                self._create_alert(
                    level=AlertLevel.WARNING,
                    message=f"违规率超过阈值:{violation_rate:.1%} > {self.alert_threshold_violation_rate:.1%}",
                    agent_id=result.agent_id,
                )

    def _create_alert(
        self, level: AlertLevel, message: str, agent_id: str, principle_id: str | None = None
    ):
        """创建告警"""
        alert = Alert(
            alert_id=f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            level=level,
            message=message,
            agent_id=agent_id,
            principle_id=principle_id,
        )

        self.alerts.append(alert)

        # 触发告警处理器
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"告警处理器执行失败: {e}")

        # 记录日志(使用敏感信息过滤器)
        log_levels = {
            AlertLevel.INFO: logging.INFO,
            AlertLevel.WARNING: logging.WARNING,
            AlertLevel.ERROR: logging.ERROR,
            AlertLevel.CRITICAL: logging.CRITICAL,
        }

        # 使用敏感信息过滤器过滤日志消息
        filtered_message = filter_log(
            message, context={"agent_id": agent_id, "principle_id": principle_id}
        )
        log_message = f"[{level.value.upper()}] {filtered_message}"

        logger.log(log_levels[level], log_message)

    def add_alert_handler(self, handler: Callable[[Alert], None]) -> None:
        """添加告警处理器"""
        self.alert_handlers.append(handler)

    def get_current_metrics(self) -> EthicsMetrics:
        """获取当前指标"""
        return self.metrics

    def get_compliance_trend(self, window_minutes: int = 60) -> list[dict[str, Any]]:
        """获取合规趋势"""
        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)

        trend_data = []
        for i, ts in enumerate(self.metrics.timestamps):
            if ts >= cutoff_time:
                trend_data.append(
                    {"timestamp": ts.isoformat(), "score": self.metrics.compliance_scores[i]}
                )

        return trend_data

    def get_agent_report(self, agent_id: str) -> dict[str, Any]:
        """获取智能体报告"""
        stats = self.metrics.agent_stats.get(agent_id, {})

        if not stats:
            return {"error": f"智能体 {agent_id} 没有记录"}

        total = stats["total"]
        compliant = stats["compliant"]

        return {
            "agent_id": agent_id,
            "total_evaluations": total,
            "compliant": compliant,
            "partial": stats["partial"],
            "non_compliant": stats["non_compliant"],
            "compliance_rate": compliant / total if total > 0 else 0.0,
            "violation_rate": (
                (stats["partial"] + stats["non_compliant"]) / total if total > 0 else 0.0
            ),
        }

    def get_top_violations(self, limit: int = 10) -> list[dict[str, Any]]:
        """获取最常违规的原则"""
        sorted_violations = sorted(
            self.metrics.principle_violations.items(), key=lambda x: x[1], reverse=True
        )

        return [
            {
                "principle_id": principle_id,
                "violation_count": count,
                "violation_rate": (
                    count / self.metrics.total_evaluations
                    if self.metrics.total_evaluations > 0
                    else 0.0
                ),
            }
            for principle_id, count in sorted_violations[:limit]
        ]

    def get_recent_alerts(self, limit: int = 20) -> list[Alert]:
        """获取最近的告警"""
        return sorted(self.alerts, key=lambda a: a.timestamp, reverse=True)[:limit]

    def generate_dashboard_data(self) -> dict[str, Any]:
        """生成仪表板数据"""
        return {
            "summary": {
                "total_evaluations": self.metrics.total_evaluations,
                "compliance_rate": self.metrics.compliance_rate,
                "violation_rate": self.metrics.violation_rate,
                "critical_violations": self.metrics.critical_violations,
                "active_alerts": len([a for a in self.alerts if not a.resolved]),
            },
            "metrics": {
                "compliant": self.metrics.compliant_count,
                "partial": self.metrics.partial_count,
                "non_compliant": self.metrics.non_compliant_count,
            },
            "top_violations": self.get_top_violations(5),
            "recent_alerts": [
                {"level": a.level.value, "message": a.message, "timestamp": a.timestamp.isoformat()}
                for a in self.get_recent_alerts(5)
            ],
            "agent_stats": [
                {
                    "agent_id": agent_id,
                    "compliance_rate": (
                        stats["compliant"] / stats["total"] if stats["total"] > 0 else 0.0
                    ),
                }
                for agent_id, stats in self.metrics.agent_stats.items()
            ],
            "compliance_trend": self.get_compliance_trend(),
        }

    def reset_metrics(self) -> Any:
        """重置指标"""
        self.metrics = EthicsMetrics()
        self.recent_evaluations.clear()
        logger.info("伦理监控指标已重置")


# 便捷函数
def create_ethics_monitor(evaluator: EthicsEvaluator = None) -> EthicsMonitor:
    """创建伦理监控器"""
    return EthicsMonitor(evaluator)


# 默认日志目录配置
DEFAULT_LOG_DIR = Path(
    os.getenv("ATHENA_LOGS_DIR", os.path.join(os.path.expanduser("~"), "athena", "logs"))
)


def setup_logging_alert_handler(monitor: EthicsMonitor, log_file: str | Path | None = None):
    """设置日志告警处理器

    Args:
        monitor: 伦理监控器实例
        log_file: 日志文件路径,如果为None则使用默认路径
    """
    # 使用默认路径如果未指定
    log_path = DEFAULT_LOG_DIR / "ethics_alerts.log" if log_file is None else Path(log_file)

    # 确保日志目录存在
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # 配置日志处理器
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(str(log_path)), logging.StreamHandler()],
    )

    # 添加告警处理器
    def log_alert_handler(alert: Alert) -> Any:
        logger.warning(f"告警: [{alert.level.value}] {alert.message}")

    monitor.add_alert_handler(log_alert_handler)

    return monitor
