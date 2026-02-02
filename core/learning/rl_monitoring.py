#!/usr/bin/env python3
"""
强化学习监控和评估系统
RL Monitoring and Evaluation System

功能:
1. 实时监控RL学习进度
2. 性能评估和报告
3. 可视化学习曲线
4. 异常检测和告警

作者: Athena平台团队
版本: v1.0.0
创建: 2025-01-08
"""
import numpy as np

import asyncio
import contextlib
import logging
from datetime import datetime, timedelta
from typing import Any


from .production_rl_integration import ProductionRLSystem, get_production_rl_system

logger = logging.getLogger(__name__)


class RLMetricsCollector:
    """RL指标收集器"""

    def __init__(self, rl_system: ProductionRLSystem):
        self.rl_system = rl_system
        self.metrics_history: list[dict] = []
        self.alerts: list[dict] = []

        # 告警阈值
        self.thresholds = {
            "low_reward": -0.5,  # 平均奖励过低
            "high_reward_variance": 1.0,  # 奖励方差过大
            "low_engagement": 0.3,  # 完成率过低
            "high_error_rate": 0.2,  # 错误率过高
        }

    async def collect_metrics(self) -> dict[str, Any]:
        """收集当前指标"""
        interactions = self.rl_system.interaction_history

        if not interactions:
            return {"timestamp": datetime.now().isoformat(), "status": "no_data"}

        # 时间窗口
        recent_24h = [i for i in interactions if i.timestamp > datetime.now() - timedelta(hours=24)]
        recent_100 = list(interactions)[-100:]

        # 基础统计
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "total_interactions": len(interactions),
            "last_24h_interactions": len(recent_24h),
            "last_100_interactions": len(recent_100),
        }

        # 奖励统计
        if recent_100:
            rewards = [self.rl_system.calculate_reward(i) for i in recent_100]
            metrics.update(
                {
                    "recent_rewards": {
                        "mean": float(np.mean(rewards)),
                        "std": float(np.std(rewards)),
                        "min": float(np.min(rewards)),
                        "max": float(np.max(rewards)),
                        "median": float(np.median(rewards)),
                    }
                }
            )

        # 显式反馈统计
        with_feedback = [i for i in recent_100 if i.explicit_feedback is not None]
        if with_feedback:
            # 过滤掉None值并确保都是float
            feedback_scores = [
                float(i.explicit_feedback) for i in with_feedback if i.explicit_feedback is not None
            ]
            if feedback_scores:  # 确保有有效值
                metrics["explicit_feedback"] = {
                    "count": len(feedback_scores),
                    "mean_score": float(np.mean(feedback_scores)),
                    "distribution": {
                        "positive": sum(1 for s in feedback_scores if s > 0.6),
                        "neutral": sum(1 for s in feedback_scores if 0.4 <= s <= 0.6),
                        "negative": sum(1 for s in feedback_scores if s < 0.4),
                    },
                }

        # 质量指标
        if recent_100:
            error_count = sum(1 for i in recent_100 if i.error_occurred)
            corrected_count = sum(1 for i in recent_100 if i.user_corrected)
            completed_count = sum(1 for i in recent_100 if not i.error_occurred)

            metrics["quality_metrics"] = {
                "error_rate": error_count / len(recent_100),
                "correction_rate": corrected_count / len(recent_100),
                "completion_rate": completed_count / len(recent_100),
            }

        # RL智能体状态
        rl_report = await self.rl_system.rl_agent.get_agent_report()
        metrics["rl_agent"] = {
            "q_table_size": rl_report["q_table_size"],
            "epsilon": rl_report["epsilon"],
            "total_episodes": rl_report["total_episodes"],
        }

        # 能力使用分布
        if recent_100:
            capabilities = {}
            for i in recent_100:
                capabilities[i.capability_used] = capabilities.get(i.capability_used, 0) + 1
            metrics["capability_distribution"] = capabilities

        return metrics

    def check_alerts(self, metrics: dict[str, Any]) -> list[dict]:
        """检查告警条件"""
        new_alerts = []

        # 检查平均奖励
        if "recent_rewards" in metrics:
            avg_reward = metrics["recent_rewards"]["mean"]
            if avg_reward < self.thresholds["low_reward"]:
                new_alerts.append(
                    {
                        "type": "low_reward",
                        "severity": "warning",
                        "message": f"平均奖励过低: {avg_reward:.3f}",
                        "value": avg_reward,
                        "threshold": self.thresholds["low_reward"],
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        # 检查奖励方差
        if "recent_rewards" in metrics:
            reward_std = metrics["recent_rewards"]["std"]
            if reward_std > self.thresholds["high_reward_variance"]:
                new_alerts.append(
                    {
                        "type": "high_variance",
                        "severity": "warning",
                        "message": f"奖励波动过大: {reward_std:.3f}",
                        "value": reward_std,
                        "threshold": self.thresholds["high_reward_variance"],
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        # 检查错误率
        if "quality_metrics" in metrics:
            error_rate = metrics["quality_metrics"]["error_rate"]
            if error_rate > self.thresholds["high_error_rate"]:
                new_alerts.append(
                    {
                        "type": "high_error_rate",
                        "severity": "critical",
                        "message": f"错误率过高: {error_rate:.2%}",
                        "value": error_rate,
                        "threshold": self.thresholds["high_error_rate"],
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        # 检查完成率
        if "quality_metrics" in metrics:
            completion_rate = metrics["quality_metrics"]["completion_rate"]
            if completion_rate < self.thresholds["low_engagement"]:
                new_alerts.append(
                    {
                        "type": "low_completion_rate",
                        "severity": "warning",
                        "message": f"完成率过低: {completion_rate:.2%}",
                        "value": completion_rate,
                        "threshold": self.thresholds["low_engagement"],
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        # 更新告警历史
        self.alerts.extend(new_alerts)

        # 只保留最近100条告警
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]

        return new_alerts

    async def update_metrics(self):
        """更新指标记录"""
        metrics = await self.collect_metrics()
        alerts = self.check_alerts(metrics)

        metrics["alerts"] = alerts
        self.metrics_history.append(metrics)

        # 只保留最近1000条记录
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]

        return metrics, alerts


class RLEvaluationReport:
    """RL评估报告生成器"""

    def __init__(self, rl_system: ProductionRLSystem):
        self.rl_system = rl_system
        self.collector = RLMetricsCollector(rl_system)

    async def generate_daily_report(self) -> str:
        """生成日报"""
        metrics, alerts = await self.collector.update_metrics()

        report = f"""
{'='*60}
📊 强化学习系统日报
{'='*60}

🕐 报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📈 核心指标
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

        if metrics.get("status") == "no_data":
            report += "\n暂无数据,请等待系统收集更多交互记录。\n"
            return report

        # 总体统计
        report += f"""
总交互次数: {metrics['total_interactions']:,}
最近24小时: {metrics['last_24h_interactions']:,}
最近100次: {metrics['last_100_interactions']:,}
"""

        # 奖励统计
        if "recent_rewards" in metrics:
            rewards = metrics["recent_rewards"]
            report += f"""
🎯 奖励统计 (最近100次)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
平均值: {rewards['mean']:+.3f}
标准差: {rewards['std']:.3f}
中位数: {rewards['median']:+.3f}
范围: [{rewards['min']:+.3f}, {rewards['max']:+.3f}]

趋势: {'↗️ 上升' if rewards['mean'] > 0 else '↘️ 下降'}
"""

        # 显式反馈
        if "explicit_feedback" in metrics:
            feedback = metrics["explicit_feedback"]
            dist = feedback["distribution"]
            report += f"""
👍 显式反馈统计
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
反馈数量: {feedback['count']}
平均评分: {feedback['mean_score']:.2%}
正面: {dist['positive']} ({dist['positive']/feedback['count']*100:.1f}%)
中性: {dist['neutral']} ({dist['neutral']/feedback['count']*100:.1f}%)
负面: {dist['negative']} ({dist['negative']/feedback['count']*100:.1f}%)
"""

        # 质量指标
        if "quality_metrics" in metrics:
            quality = metrics["quality_metrics"]
            report += f"""
✨ 质量指标
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
错误率: {quality['error_rate']:.2%}
纠正率: {quality['correction_rate']:.2%}
完成率: {quality['completion_rate']:.2%}
"""

        # RL状态
        if "rl_agent" in metrics:
            rl = metrics["rl_agent"]
            report += f"""
🎮 RL智能体状态
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Q表大小: {rl['q_table_size']:,}
探索率 (ε): {rl['epsilon']:.3f}
学习进度: {'早期' if rl['epsilon'] > 0.05 else '中期' if rl['epsilon'] > 0.02 else '成熟'}
"""

        # 能力分布
        if "capability_distribution" in metrics:
            report += "\n📊 能力使用分布\n"
            report += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            for cap, count in sorted(
                metrics["capability_distribution"].items(), key=lambda x: x[1], reverse=True
            ):
                bar = "█" * (count * 20 // 100)
                report += f"{cap:20s} {bar} {count}\n"

        # 告警
        if alerts:
            report += f"""
⚠️ 告警信息 ({len(alerts)}条)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
            for alert in alerts:
                emoji = "🔴" if alert["severity"] == "critical" else "🟡"
                report += f"{emoji} {alert['message']}\n"

        report += f"""
{'='*60}
💡 提示: 系统正在持续学习中,感谢您的使用和反馈!
{'='*60}
"""

        return report

    async def save_report(self, report: str):
        """保存报告到文件"""
        try:
            reports_dir = self.rl_system.data_dir / "reports"
            reports_dir.mkdir(exist_ok=True)

            report_file = reports_dir / f"daily_report_{datetime.now().strftime('%Y%m%d')}.txt"
            with open(report_file, "w", encoding="utf-8") as f:
                f.write(report)

            logger.info(f"📄 报告已保存: {report_file}")
        except Exception as e:
            logger.error(f"❌ 保存报告失败: {e}")


class RLMonitoringService:
    """RL监控服务"""

    def __init__(self, rl_system: ProductionRLSystem | None = None):
        self.rl_system = rl_system or get_production_rl_system()
        self.collector = RLMetricsCollector(self.rl_system)
        self.report_generator = RLEvaluationReport(self.rl_system)

        self._monitoring_task = None
        self._is_running = False

    async def start_monitoring(self, interval_seconds: int = 3600):
        """启动监控任务"""
        if self._is_running:
            logger.warning("⚠️ 监控任务已在运行")
            return

        self._is_running = True

        async def monitor_loop():
            while self._is_running:
                try:
                    # 收集指标
                    _metrics, alerts = await self.collector.update_metrics()

                    # 保存指标
                    await self.rl_system.save_metrics()

                    # 如果有严重告警,记录日志
                    critical_alerts = [a for a in alerts if a["severity"] == "critical"]
                    if critical_alerts:
                        logger.warning(f"🚨 检测到 {len(critical_alerts)} 个严重告警")
                        for alert in critical_alerts:
                            logger.warning(f"  - {alert['message']}")

                    # 每天生成一次报告
                    if datetime.now().hour == 8:  # 早上8点
                        report = await self.report_generator.generate_daily_report()
                        await self.report_generator.save_report(report)
                        logger.info("📊 日报已生成")

                except Exception as e:
                    logger.error(f"❌ 监控任务错误: {e}", exc_info=True)

                await asyncio.sleep(interval_seconds)

        self._monitoring_task = asyncio.create_task(monitor_loop())
        logger.info(f"✅ 监控任务已启动 (间隔: {interval_seconds}秒)")

    async def stop_monitoring(self):
        """停止监控任务"""
        self._is_running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._monitoring_task
        logger.info("⏹️ 监控任务已停止")

    async def get_current_status(self) -> dict[str, Any]:
        """获取当前状态"""
        metrics, alerts = await self.collector.update_metrics()

        return {
            "metrics": metrics,
            "alerts": alerts,
            "monitoring_active": self._is_running,
            "summary": self.rl_system.get_learning_summary(),
        }


# 导出
_monitoring_service: RLMonitoringService | None = None


def get_monitoring_service() -> RLMonitoringService:
    """获取监控服务单例"""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = RLMonitoringService()
    return _monitoring_service
