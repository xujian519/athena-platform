#!/usr/bin/env python3
from __future__ import annotations
"""
恢复监控仪表板
Recovery Monitoring Dashboard

提供实时的错误恢复监控和统计

作者: Athena平台团队
创建时间: 2026-03-17
版本: v1.0.0
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


class RecoveryDashboard:
    """恢复监控仪表板"""

    def __init__(self, recovery_system):
        """
        初始化仪表板

        Args:
            recovery_system: EnhancedFallbackRecovery实例
        """
        self.recovery_system = recovery_system

    def get_real_time_stats(self) -> dict[str, Any]:
        """
        获取实时统计信息

        Returns:
            统计信息字典
        """
        stats = self.recovery_system.stats.copy()

        # 计算恢复率
        if stats['total_failures'] > 0:
            stats['recovery_rate'] = stats['recoveries'] / stats['total_failures']
        else:
            stats['recovery_rate'] = 1.0

        # 添加组件健康状态
        stats['component_health'] = self.recovery_system.component_health.copy()

        # 添加时间戳
        stats['timestamp'] = datetime.now().isoformat()

        return stats

    def get_strategy_breakdown(self) -> dict[str, int]:
        """
        获取策略使用分布

        Returns:
            策略使用次数字典
        """
        return self.recovery_system.stats['strategy_usage'].copy()

    def get_recent_failures(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        获取最近的失败记录

        Args:
            limit: 返回的最大记录数

        Returns:
            失败记录列表
        """
        failures = list(self.recovery_system.failure_history)[-limit:]

        return [
            {
                'component': f.component,
                'operation': f.operation,
                'error': f.error,
                'severity': f.severity.value,
                'timestamp': f.timestamp.isoformat(),
                'attempt': f.attempt,
            }
            for f in failures
        ]

    def get_component_health_summary(self) -> dict[str, str]:
        """
        获取组件健康状态摘要

        Returns:
            组件健康状态字典（人类可读）
        """
        summary = {}
        for component, health in self.recovery_system.component_health.items():
            if health >= 0.9:
                status = "健康 ✅"
            elif health >= 0.7:
                status = "良好 👍"
            elif health >= 0.5:
                status = "一般 ⚠️"
            else:
                status = "不佳 ❌"

            summary[component] = f"{status} ({health:.2%})"

        return summary

    def export_metrics(self, format: str = 'json') -> str:
        """
        导出监控指标

        Args:
            format: 导出格式（json/prometheus）

        Returns:
            格式化的监控数据
        """
        stats = self.get_real_time_stats()

        if format == 'json':
            return json.dumps(stats, indent=2, ensure_ascii=False, default=str)

        elif format == 'prometheus':
            # Prometheus格式
            lines = []
            lines.append("# HELP recovery_rate Error recovery rate")
            lines.append("# TYPE recovery_rate gauge")
            lines.append(f"recovery_rate {stats['recovery_rate']:.4f}")

            lines.append("# HELP total_failures Total number of failures")
            lines.append("# TYPE total_failures counter")
            lines.append(f"total_failures {stats['total_failures']}")

            lines.append("# HELP successful_recoveries Successful recoveries")
            lines.append("# TYPE successful_recoveries counter")
            lines.append(f"successful_recoveries {stats['recoveries']}")

            # 策略使用统计
            for strategy, count in stats['strategy_usage'].items():
                lines.append(f'strategy_usage{{strategy="{strategy}"}} {count}')

            return '\n'.join(lines)

        else:
            raise ValueError(f"不支持的格式: {format}")

    def generate_report(self, period_hours: int = 24) -> str:
        """
        生成恢复报告

        Args:
            period_hours: 报告周期（小时）

        Returns:
            报告文本
        """
        stats = self.get_real_time_stats()
        cutoff_time = datetime.now() - timedelta(hours=period_hours)

        # 过滤时间段内的失败
        recent_failures = [
            f for f in self.recovery_system.failure_history
            if f.timestamp >= cutoff_time
        ]

        report_lines = [
            "# 错误恢复系统报告",
            f"\n**报告周期**: 过去{period_hours}小时",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 总体统计",
            f"- 总失败数: {stats['total_failures']}",
            f"- 成功恢复数: {stats['recoveries']}",
            f"- 恢复成功率: {stats['recovery_rate']:.2%}",
            "",
            "## 策略使用分布",
        ]

        for strategy, count in sorted(stats['strategy_usage'].items(),
                                     key=lambda x: x[1], reverse=True):
            if count > 0:
                percentage = (count / sum(stats['strategy_usage'].values())) * 100
                report_lines.append(f"- {strategy}: {count}次 ({percentage:.1f}%)")

        report_lines.extend([
            "",
            "## 组件健康状态",
        ])

        health_summary = self.get_component_health_summary()
        for component, status in health_summary.items():
            report_lines.append(f"- {component}: {status}")

        if recent_failures:
            report_lines.extend([
                "",
                "## 最近失败记录",
            ])

            for f in recent_failures[-10:]:
                report_lines.append(
                    f"- [{f.severity.value}] {f.component}.{f.operation}: {f.error}"
                )

        return '\n'.join(report_lines)


# 导出
__all__ = ['RecoveryDashboard']
