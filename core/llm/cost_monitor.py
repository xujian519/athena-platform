"""
统一LLM层 - 成本监控和告警系统
实时追踪API调用成本,设置预算和告警

作者: Claude Code
日期: 2026-01-23
"""

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """告警级别"""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class CostRecord:
    """成本记录"""

    timestamp: datetime
    model_id: str
    task_type: str
    tokens_used: int
    cost: float
    processing_time: float


@dataclass
class CostAlert:
    """成本告警"""

    level: AlertLevel
    message: str
    current_cost: float
    threshold: float
    timestamp: datetime
    recommendations: list[str] = field(default_factory=list)


class CostMonitor:
    """
    成本监控器

    功能:
    1. 实时追踪API调用成本
    2. 按模型/任务/时间统计
    3. 预算控制和告警
    4. 成本报告生成
    """

    def __init__(
        self,
        daily_budget: float = 10.0,
        alert_threshold: float = 5.0,
        max_cost_per_request: float = 0.5,
        max_records: int = 10000,
        max_alerts: int = 1000,
    ):
        """
        初始化成本监控器

        Args:
            daily_budget: 每日预算限制(元)
            alert_threshold: 成本告警阈值(元)
            max_cost_per_request: 单次请求最大成本(元)
            max_records: 最大成本记录数(防止内存泄漏)
            max_alerts: 最大告警记录数(防止内存泄漏)
        """
        self.daily_budget = daily_budget
        self.alert_threshold = alert_threshold
        self.max_cost_per_request = max_cost_per_request
        self.max_records = max_records
        self.max_alerts = max_alerts

        # 成本记录
        self.records: list[CostRecord] = []

        # 告警历史
        self.alerts: list[CostAlert] = []

        # 统计缓存
        self._stats_cache: dict[str, Any] = {}
        self._cache_timestamp: datetime | None = None

        logger.info(
            f"✅ 成本监控器初始化完成 "
            f"(预算: ¥{daily_budget}/天, "
            f"最大记录: {max_records}, "
            f"最大告警: {max_alerts})"
        )

    def record_cost(
        self, model_id: str, task_type: str, tokens_used: int, cost: float, processing_time: float
    ) -> None:
        """
        记录成本

        Args:
            model_id: 模型ID
            task_type: 任务类型
            tokens_used: 使用tokens数
            cost: 成本(元)
            processing_time: 处理时间(秒)
        """
        # 检查单次请求成本
        if cost > self.max_cost_per_request:
            alert = CostAlert(
                level=AlertLevel.WARNING,
                message="单次请求成本超过限制",
                current_cost=cost,
                threshold=self.max_cost_per_request,
                timestamp=datetime.now(),
                recommendations=[
                    "考虑使用成本更低的模型",
                    "减少max_tokens设置",
                    "使用本地模型替代云端模型",
                ],
            )
            self._add_alert(alert)

        # 记录成本
        record = CostRecord(
            timestamp=datetime.now(),
            model_id=model_id,
            task_type=task_type,
            tokens_used=tokens_used,
            cost=cost,
            processing_time=processing_time,
        )
        self.records.append(record)

        # 滚动清理:删除最旧的记录(FIFO)
        if len(self.records) > self.max_records:
            removed_count = len(self.records) - self.max_records
            self.records = self.records[-self.max_records :]
            logger.debug(
                f"🗑️ 成本记录滚动清理: 删除了 {removed_count} 条最旧记录 "
                f"(当前: {len(self.records)}/{self.max_records})"
            )

        # 清理缓存
        self._stats_cache = {}
        self._cache_timestamp = None

        # 检查是否超过预算
        self._check_budget()

    def _check_budget(self) -> None:
        """检查预算并生成告警"""
        stats = self.get_stats()
        today_cost = stats["today_cost"]

        # 检查告警阈值
        if today_cost >= self.alert_threshold and today_cost < self.daily_budget:
            # 警告级别
            alert = CostAlert(
                level=AlertLevel.WARNING,
                message="今日成本已超过告警阈值",
                current_cost=today_cost,
                threshold=self.alert_threshold,
                timestamp=datetime.now(),
                recommendations=[
                    f"距离预算上限还有 ¥{self.daily_budget - today_cost:.2f}",
                    "建议切换到成本优化策略",
                    "考虑使用本地模型减少成本",
                ],
            )
            self._add_alert(alert)

        # 检查预算上限
        if today_cost >= self.daily_budget:
            # 严重级别
            alert = CostAlert(
                level=AlertLevel.CRITICAL,
                message="今日成本已超过预算上限",
                current_cost=today_cost,
                threshold=self.daily_budget,
                timestamp=datetime.now(),
                recommendations=[
                    "立即停止非必要的云端模型调用",
                    "仅使用本地免费模型",
                    "等待预算重置(每日00:00)",
                ],
            )
            self._add_alert(alert)

    def _add_alert(self, alert: CostAlert) -> None:
        """
        添加告警

        Args:
            alert: 告警对象
        """
        # 避免重复告警(1分钟内)
        recent_alerts = [
            a
            for a in self.alerts
            if (datetime.now() - a.timestamp).total_seconds() < 60 and a.message == alert.message
        ]
        if not recent_alerts:
            self.alerts.append(alert)

            # 滚动清理:删除最旧的告警(FIFO)
            if len(self.alerts) > self.max_alerts:
                removed_count = len(self.alerts) - self.max_alerts
                self.alerts = self.alerts[-self.max_alerts :]
                logger.debug(
                    f"🗑️ 告警记录滚动清理: 删除了 {removed_count} 条最旧告警 "
                    f"(当前: {len(self.alerts)}/{self.max_alerts})"
                )

            # 记录日志
            log_func = logger.warning if alert.level == AlertLevel.WARNING else logger.error
            log_func(
                f"💰 成本告警: {alert.message} "
                f"(当前: ¥{alert.current_cost:.2f}, 阈值: ¥{alert.threshold:.2f})"
            )

            # 打印建议
            for rec in alert.recommendations:
                logger.info(f"   建议: {rec}")

    def get_stats(self, time_window: str = "today") -> dict[str, Any]:
        """
        获取统计信息

        Args:
            time_window: 时间窗口 (today, week, month, all)

        Returns:
            Dict: 统计信息
        """
        # 检查缓存
        if self._cache_timestamp and (datetime.now() - self._cache_timestamp).total_seconds() < 10:
            return self._stats_cache

        # 过滤记录
        now = datetime.now()
        if time_window == "today":
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_window == "week":
            start_time = now - timedelta(days=7)
        elif time_window == "month":
            start_time = now - timedelta(days=30)
        else:  # all
            start_time = datetime.min

        filtered_records = [r for r in self.records if r.timestamp >= start_time]

        if not filtered_records:
            return {
                "total_requests": 0,
                "total_cost": 0.0,
                "total_tokens": 0,
                "today_cost": 0.0,
                "avg_cost_per_request": 0.0,
                "model_costs": {},
                "task_costs": {},
            }

        # 计算统计
        total_requests = len(filtered_records)
        total_cost = sum(r.cost for r in filtered_records)
        total_tokens = sum(r.tokens_used for r in filtered_records)
        today_cost = sum(r.cost for r in self.records if r.timestamp.date() == now.date())

        # 按模型统计
        model_costs: dict[str, dict[str, Any]] = {}
        for r in filtered_records:
            if r.model_id not in model_costs:
                model_costs[r.model_id] = {"cost": 0.0, "requests": 0, "tokens": 0}
            model_costs[r.model_id]["cost"] += r.cost
            model_costs[r.model_id]["requests"] += 1
            model_costs[r.model_id]["tokens"] += r.tokens_used

        # 按任务类型统计
        task_costs: dict[str, dict[str, Any]] = {}
        for r in filtered_records:
            if r.task_type not in task_costs:
                task_costs[r.task_type] = {"cost": 0.0, "requests": 0, "tokens": 0}
            task_costs[r.task_type]["cost"] += r.cost
            task_costs[r.task_type]["requests"] += 1
            task_costs[r.task_type]["tokens"] += r.tokens_used

        stats = {
            "total_requests": total_requests,
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "today_cost": today_cost,
            "avg_cost_per_request": total_cost / total_requests if total_requests > 0 else 0.0,
            "model_costs": model_costs,
            "task_costs": task_costs,
            "budget_utilization": (
                (today_cost / self.daily_budget) * 100 if self.daily_budget > 0 else 0
            ),
            "alert_threshold_utilization": (
                (today_cost / self.alert_threshold) * 100 if self.alert_threshold > 0 else 0
            ),
        }

        # 更新缓存
        self._stats_cache = stats
        self._cache_timestamp = datetime.now()

        return stats

    def get_recent_alerts(self, limit: int = 10) -> list[CostAlert]:
        """
        获取最近的告警

        Args:
            limit: 最大返回数量

        Returns:
            list[CostAlert]: 告警列表
        """
        return sorted(self.alerts, key=lambda x: x.timestamp, reverse=True)[:limit]

    def check_budget_status(self) -> dict[str, Any]:
        """
        检查预算状态

        Returns:
            Dict: 预算状态信息
        """
        stats = self.get_stats()
        today_cost = stats["today_cost"]

        return {
            "daily_budget": self.daily_budget,
            "today_cost": today_cost,
            "remaining_budget": max(0, self.daily_budget - today_cost),
            "budget_utilization": (
                (today_cost / self.daily_budget) * 100 if self.daily_budget > 0 else 0
            ),
            "alert_threshold": self.alert_threshold,
            "threshold_exceeded": today_cost >= self.alert_threshold,
            "budget_exceeded": today_cost >= self.daily_budget,
            "recommendations": self._get_budget_recommendations(today_cost),
        }

    def _get_budget_recommendations(self, current_cost: float) -> list[str]:
        """
        获取预算建议

        Args:
            current_cost: 当前成本

        Returns:
            list[str]: 建议列表
        """
        recommendations = []

        if current_cost < self.alert_threshold * 0.5:
            recommendations.append("当前成本良好,可继续正常使用")
        elif current_cost < self.alert_threshold:
            recommendations.append(f"接近告警阈值 (¥{self.alert_threshold:.2f}),建议关注成本")
        elif current_cost < self.daily_budget * 0.8:
            recommendations.append("已超过告警阈值,建议切换到成本优化策略")
        else:
            recommendations.append("接近预算上限,建议仅使用本地模型")

        return recommendations

    def generate_report(self, time_window: str = "today") -> str:
        """
        生成成本报告

        Args:
            time_window: 时间窗口

        Returns:
            str: 格式化的成本报告
        """
        stats = self.get_stats(time_window)
        budget_status = self.check_budget_status()

        lines = [
            "=" * 80,
            f"成本报告 - {time_window.upper()}",
            "=" * 80,
            "",
            "[概览]",
            f"  总请求数: {stats['total_requests']}",
            f"  总成本: ¥{stats['total_cost']:.4f}",
            f"  总Tokens: {stats['total_tokens']:,}",
            f"  平均成本/请求: ¥{stats['avg_cost_per_request']:.4f}",
            "",
            "[今日预算]",
            f"  日预算: ¥{budget_status['daily_budget']:.2f}",
            f"  今日成本: ¥{budget_status['today_cost']:.4f}",
            f"  剩余预算: ¥{budget_status['remaining_budget']:.2f}",
            f"  预算使用率: {budget_status['budget_utilization']:.1f}%",
            "",
            "[模型成本分布]",
        ]

        # 按成本排序
        sorted_models = sorted(
            stats["model_costs"].items(), key=lambda x: x[1]["cost"], reverse=True
        )

        for model_id, model_stat in sorted_models:
            percentage = (
                (model_stat["cost"] / stats["total_cost"]) * 100 if stats["total_cost"] > 0 else 0
            )
            lines.append(
                f"  {model_id}: "
                f"¥{model_stat['cost']:.4f} "
                f"({percentage:.1f}%) "
                f"- {model_stat['requests']}请求 "
                f"- {model_stat['tokens']:,}tokens"
            )

        lines.extend(["", "[任务类型成本分布]"])

        # 按成本排序
        sorted_tasks = sorted(stats["task_costs"].items(), key=lambda x: x[1]["cost"], reverse=True)

        for task_type, task_stat in sorted_tasks:
            percentage = (
                (task_stat["cost"] / stats["total_cost"]) * 100 if stats["total_cost"] > 0 else 0
            )
            lines.append(
                f"  {task_type}: "
                f"¥{task_stat['cost']:.4f} "
                f"({percentage:.1f}%) "
                f"- {task_stat['requests']}请求"
            )

        # 最近告警
        recent_alerts = self.get_recent_alerts(limit=5)
        if recent_alerts:
            lines.extend(["", "[最近告警]"])
            for alert in recent_alerts:
                lines.append(
                    f"  [{alert.level.value.upper()}] {alert.message} "
                    f"(¥{alert.current_cost:.2f}/¥{alert.threshold:.2f})"
                )

        lines.extend(["", "=" * 80])

        return "\n".join(lines)

    def reset_daily_records(self) -> None:
        """重置今日记录"""
        now = datetime.now()
        today = now.date()

        # 只保留今天的记录
        self.records = [r for r in self.records if r.timestamp.date() == today]

        logger.info("✅ 已重置成本监控记录")


# 单例
_cost_monitor: CostMonitor | None = None
_cost_monitor_lock = threading.Lock()


def get_cost_monitor() -> CostMonitor:
    """
    获取成本监控器单例(线程安全)

    Returns:
        CostMonitor: 成本监控器实例
    """
    global _cost_monitor
    if _cost_monitor is None:
        with _cost_monitor_lock:
            # 双重检查锁定
            if _cost_monitor is None:
                _cost_monitor = CostMonitor()
    return _cost_monitor


def reset_cost_monitor():
    """重置单例(用于测试,线程安全)"""
    global _cost_monitor
    with _cost_monitor_lock:
        _cost_monitor = None
