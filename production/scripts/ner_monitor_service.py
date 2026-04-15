#!/usr/bin/env python3
"""
NER性能监控服务
NER Performance Monitoring Service

实时监控NER系统的性能指标，提供：
1. 实时性能监控
2. 异常检测和告警
3. 性能趋势分析
4. 自动化报告生成

作者: 小诺AI团队
创建时间: 2025-12-28
版本: v1.0.0
"""

from __future__ import annotations
import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from production.core.ner_production_service import get_ner_service

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NERPerformanceMonitorService:
    """NER性能监控服务"""

    def __init__(
        self,
        check_interval: int = 60,
        slow_threshold_ms: float = 100,
        error_threshold: float = 5.0,
    ):
        """
        初始化监控服务

        Args:
            check_interval: 检查间隔（秒）
            slow_threshold_ms: 慢查询阈值（毫秒）
            error_threshold: 错误率阈值（百分比）
        """
        self.check_interval = check_interval
        self.slow_threshold_ms = slow_threshold_ms
        self.error_threshold = error_threshold

        self.running = False
        self.start_time = None
        self.alerts_sent = []

        # 报告存储路径
        self.reports_dir = Path(project_root) / ".claude" / "reports" / "ner_monitoring"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    async def start(self):
        """启动监控服务"""
        self.running = True
        self.start_time = datetime.now()

        logger.info("🚀 NER性能监控服务启动")
        logger.info(f"📊 检查间隔: {self.check_interval}秒")
        logger.info(f"⚠️  慢查询阈值: {self.slow_threshold_ms}ms")
        logger.info(f"🚨 错误率阈值: {self.error_threshold}%")

        while self.running:
            try:
                await self.monitoring_cycle()
                await asyncio.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"❌ 监控周期失败: {e}")
                await asyncio.sleep(10)

    async def stop(self):
        """停止监控服务"""
        self.running = False
        logger.info("⏹️  NER性能监控服务停止")

    async def monitoring_cycle(self):
        """执行一次监控周期"""
        try:
            # 获取服务实例
            ner_service = get_ner_service()

            # 获取性能报告
            report = ner_service.get_performance_report()

            # 检查告警条件
            await self.check_alerts(report)

            # 记录指标
            await self.record_metrics(report)

            # 定期生成报告（每小时）
            if datetime.now().minute == 0:
                await self.generate_report(report)

        except Exception as e:
            logger.error(f"❌ 监控周期错误: {e}")

    async def check_alerts(self, report: dict[str, Any]):
        """检查告警条件"""
        alerts = []

        # 检查错误率
        success_rate = report['summary']['success_rate']
        if success_rate < (100 - self.error_threshold):
            alert = {
                "type": "high_error_rate",
                "severity": "critical",
                "message": f"错误率过高: {100 - success_rate:.2f}%",
                "threshold": f"{self.error_threshold}%",
                "timestamp": datetime.now().isoformat(),
            }
            alerts.append(alert)

        # 检查慢查询
        p95_latency = report['performance']['p95_inference_ms']
        if p95_latency > self.slow_threshold_ms:
            alert = {
                "type": "slow_query",
                "severity": "warning",
                "message": f"P95延迟过高: {p95_latency:.2f}ms",
                "threshold": f"{self.slow_threshold_ms}ms",
                "timestamp": datetime.now().isoformat(),
            }
            alerts.append(alert)

        # 检查平均延迟
        avg_latency = report['performance']['avg_inference_ms']
        if avg_latency > self.slow_threshold_ms * 0.7:
            alert = {
                "type": "high_avg_latency",
                "severity": "warning",
                "message": f"平均延迟过高: {avg_latency:.2f}ms",
                "threshold": f"{self.slow_threshold_ms * 0.7:.0f}ms",
                "timestamp": datetime.now().isoformat(),
            }
            alerts.append(alert)

        # 发送告警
        for alert in alerts:
            await self.send_alert(alert)

    async def send_alert(self, alert: dict[str, Any]):
        """发送告警"""
        # 避免重复告警（5分钟内相同类型不重复发送）
        alert_key = f"{alert['type']}_{alert['severity']}"
        now = time.time()

        if alert_key in self.alerts_sent:
            last_sent = self.alerts_sent[alert_key]
            if now - last_sent < 300:  # 5分钟
                return

        self.alerts_sent[alert_key] = now

        # 记录告警
        severity_emoji = {
            "critical": "🚨",
            "warning": "⚠️",
            "info": "ℹ️",
        }

        emoji = severity_emoji.get(alert['severity'], "⚡")
        logger.warning(f"{emoji} 告警: {alert['message']}")

        # 保存告警到文件
        alert_file = self.reports_dir / f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(alert_file, 'w', encoding='utf-8') as f:
            json.dump(alert, f, indent=2, ensure_ascii=False)

    async def record_metrics(self, report: dict[str, Any]):
        """记录指标到文件"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        metrics_file = self.reports_dir / f"metrics_{timestamp}.json"

        with open(metrics_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

    async def generate_report(self, report: dict[str, Any]):
        """生成性能报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.reports_dir / f"performance_report_{timestamp}.md"

        # 生成Markdown报告
        content = f"""# NER性能监控报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📊 总体统计

| 指标 | 数值 |
|------|------|
| 总请求数 | {report['summary']['total_requests']:,} |
| 成功率 | {report['summary']['success_rate']:.2f}% |
| 平均实体数/请求 | {report['summary']['avg_entities_per_request']:.2f} |

---

## ⚡ 性能指标

| 指标 | 数值 |
|------|------|
| 平均延迟 | {report['performance']['avg_inference_ms']:.2f}ms |
| 最小延迟 | {report['performance']['min_inference_ms']:.2f}ms |
| 最大延迟 | {report['performance']['max_inference_ms']:.2f}ms |
| P50延迟 | {report['performance']['p50_inference_ms']:.2f}ms |
| P95延迟 | {report['performance']['p95_inference_ms']:.2f}ms |
| P99延迟 | {report['performance']['p99_inference_ms']:.2f}ms |

---

## 🏷️ 实体分布

"""

        # 实体类型分布
        entity_counts = report.get('entity_distribution', {})
        if entity_counts:
            sorted_entities = sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)
            content += "| 实体类型 | 数量 | 占比 |\n"
            content += "|---------|------|------|\n"

            total = sum(entity_counts.values())
            for entity_type, count in sorted_entities:
                percentage = (count / total) * 100
                content += f"| {entity_type} | {count:,} | {percentage:.1f}% |\n"
        else:
            content += "\n暂无实体分布数据\n"

        content += """

---

## 📈 性能评级

"""

        # 性能评级
        p95_latency = report['performance']['p95_inference_ms']
        if p95_latency < 50:
            grade = "🚀 优秀"
            comment = "性能极佳，延迟极低"
        elif p95_latency < 100:
            grade = "✅ 良好"
            comment = "性能良好，满足预期"
        elif p95_latency < 200:
            grade = "⚠️  一般"
            comment = "性能一般，需要关注"
        else:
            grade = "❌ 需优化"
            comment = "性能较差，建议优化"

        content += f"""**评级**: {grade}

**说明**: {comment}

---

*报告由NER性能监控服务自动生成*
"""

        # 写入文件
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"📄 性能报告已生成: {report_file.name}")

    async def get_metrics_summary(self) -> dict[str, Any]:
        """获取指标摘要"""
        ner_service = get_ner_service()
        health = ner_service.get_health_status()
        report = ner_service.get_performance_report()

        return {
            "health": health,
            "performance": report,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
        }


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="NER性能监控服务")
    parser.add_argument("--daemon", action="store_true", help="以守护进程模式运行")
    parser.add_argument("--once", action="store_true", help="运行一次监控检查")
    parser.add_argument("--report", action="store_true", help="生成当前性能报告")
    parser.add_argument("--interval", type=int, default=60, help="检查间隔（秒）")

    args = parser.parse_args()

    monitor = NERPerformanceMonitorService(check_interval=args.interval)

    if args.report:
        # 生成报告
        ner_service = get_ner_service()
        report = ner_service.get_performance_report()
        await monitor.generate_report(report)
        print("✅ 性能报告已生成")

    elif args.once:
        # 运行一次检查
        await monitor.monitoring_cycle()
        print("✅ 监控检查完成")

    elif args.daemon:
        # 守护进程模式
        try:
            await monitor.start()
        except KeyboardInterrupt:
            await monitor.stop()
            print("\n⏹️  监控服务已停止")

    else:
        # 显示帮助
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
