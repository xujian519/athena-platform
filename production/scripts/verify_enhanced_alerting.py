#!/usr/bin/env python3
"""
Athena增强监控告警系统验证脚本
验证多渠道告警、告警聚合、规则引擎等功能

作者: Athena平台团队
创建时间: 2025-12-29
版本: v1.0.0
"""

from __future__ import annotations
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# 添加项目路径
PROJECT_ROOT = Path("/Users/xujian/Athena工作平台")
sys.path.insert(0, str(PROJECT_ROOT))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'


def print_success(msg: str) -> Any:
    print(f"{Colors.GREEN}[✓]{Colors.NC} {msg}")


def print_error(msg: str) -> Any:
    print(f"{Colors.RED}[✗]{Colors.NC} {msg}")


def print_warning(msg: str) -> Any:
    print(f"{Colors.YELLOW}[⚠]{Colors.NC} {msg}")


def print_info(msg: str) -> Any:
    print(f"{Colors.BLUE}[i]{Colors.NC} {msg}")


def print_section(title: str) -> Any:
    print(f"\n{Colors.CYAN}{'='*60}{Colors.NC}")
    print(f"{Colors.CYAN}{title}{Colors.NC}")
    print(f"{Colors.CYAN}{'='*60}{Colors.NC}")


class EnhancedAlertingVerifier:
    """增强告警系统验证器"""

    def __init__(self):
        self.results = {
            "timestamp": time.time(),
            "tests": {},
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0
            }
        }

    def add_result(
        self,
        test_name: str,
        status: str,
        details: str = "",
        execution_time: float = 0.0,
        data: Any = None
    ):
        """添加测试结果"""
        self.results["tests"][test_name] = {
            "status": status,
            "details": details,
            "execution_time": execution_time,
            "data": data
        }

        self.results["summary"]["total"] += 1
        if status == "passed":
            self.results["summary"]["passed"] += 1
        elif status == "failed":
            self.results["summary"]["failed"] += 1
        else:
            self.results["summary"]["warnings"] += 1

    def test_alert_rules(self) -> bool:
        """测试告警规则"""
        print_section("测试1: 告警规则")

        try:
            from core.monitoring.enhanced_alerting_system import (
                EnhancedAlertingSystem,
                create_default_rules,
            )

            start_time = time.time()

            # 创建告警系统
            alerting = EnhancedAlertingSystem()

            # 添加默认规则
            default_rules = create_default_rules()
            for rule in default_rules:
                alerting.add_rule(rule)

            print_info(f"添加了 {len(default_rules)} 条默认规则")

            # 测试规则触发
            test_metrics = {
                "error_rate": 10.0,  # 超过5%阈值
                "p95_latency_ms": 1500,  # 超过1000ms阈值
                "system.memory_usage_percent": 90,  # 超过85%阈值
                "system.cpu_usage_percent": 85,  # 超过80%阈值
                "cache_hit_rate": 60,  # 低于70%阈值
                "queue_size": 1500,  # 超过1000阈值
                "throughput": 5  # 低于10阈值
            }

            print_info("评估告警规则...")
            alerting.evaluate_rules(test_metrics)

            # 检查活跃告警
            active_alerts = alerting.get_active_alerts()
            print_success(f"✓ 触发了 {len(active_alerts)} 个告警")

            # 显示告警详情
            for alert in active_alerts[:3]:  # 只显示前3个
                print_info(f"  - [{alert['severity']}] {alert['name']}: {alert['message']}")

            if len(active_alerts) < 5:
                print_warning(f"⚠️ 预期触发更多告警，实际: {len(active_alerts)}")

            execution_time = time.time() - start_time

            self.add_result(
                "alert_rules",
                "passed",
                f"告警规则正常，触发{len(active_alerts)}个告警",
                execution_time,
                {"active_alerts": len(active_alerts)}
            )
            return True

        except Exception as e:
            print_error(f"✗ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            self.add_result("alert_rules", "failed", str(e))
            return False

    def test_notification_channels(self) -> bool:
        """测试通知渠道"""
        print_section("测试2: 通知渠道")

        try:
            from core.monitoring.enhanced_alerting_system import (
                Alert,
                AlertSeverity,
                EnhancedAlertingSystem,
                LogNotificationChannel,
            )

            start_time = time.time()

            # 创建告警系统
            alerting = EnhancedAlertingSystem()

            # 添加日志通知渠道
            log_channel = LogNotificationChannel(enabled=True)
            alerting.add_notification_channel(log_channel)
            print_success("✓ 添加日志通知渠道")

            # 创建测试告警
            test_alert = Alert(
                alert_id="test_001",
                name="测试告警",
                severity=AlertSeverity.P2_MEDIUM,
                message="这是一条测试告警消息",
                details={"test_key": "test_value"}
            )

            print_info("发送测试通知...")
            # 直接调用通知渠道
            sent = log_channel.send(test_alert)

            if sent:
                print_success("✓ 日志通知发送成功")
            else:
                print_error("✗ 日志通知发送失败")
                self.add_result("notification_channels", "failed", "通知发送失败")
                return False

            execution_time = time.time() - start_time

            self.add_result(
                "notification_channels",
                "passed",
                "通知渠道工作正常",
                execution_time,
                {"channels": len(alerting.notification_channels)}
            )
            return True

        except Exception as e:
            print_error(f"✗ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            self.add_result("notification_channels", "failed", str(e))
            return False

    def test_alert_aggregation(self) -> bool:
        """测试告警聚合"""
        print_section("测试3: 告警聚合")

        try:
            from core.monitoring.enhanced_alerting_system import (
                Alert,
                AlertAggregator,
                AlertSeverity,
            )

            start_time = time.time()

            # 创建告警聚合器
            aggregator = AlertAggregator(
                aggregation_window_seconds=10,
                max_alerts_per_window=5
            )

            print_info("测试告警聚合...")

            # 连续触发15个相同告警
            sent_count = 0
            for i in range(15):
                alert = Alert(
                    alert_id=f"test_{i}",
                    name="重复测试告警",
                    severity=AlertSeverity.P3_LOW,
                    message=f"测试消息 {i}"
                )

                if aggregator.should_send(alert):
                    sent_count += 1

            print_info(f"触发了15个告警，实际发送: {sent_count}个")

            # 应该只发送前5个（超过max_alerts_per_window的会被聚合）
            if sent_count == 5:
                print_success("✓ 告警聚合正常工作 (5/15)")
            else:
                print_warning(f"⚠️ 聚合效果不符合预期: {sent_count}/15")

            execution_time = time.time() - start_time

            self.add_result(
                "alert_aggregation",
                "passed" if sent_count == 5 else "warning",
                f"告警聚合测试: {sent_count}/15",
                execution_time,
                {"sent_count": sent_count, "total_count": 15}
            )
            return sent_count == 5

        except Exception as e:
            print_error(f"✗ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            self.add_result("alert_aggregation", "failed", str(e))
            return False

    def test_alert_lifecycle(self) -> bool:
        """测试告警生命周期"""
        print_section("测试4: 告警生命周期")

        try:
            from core.monitoring.enhanced_alerting_system import (
                AlertRule,
                AlertSeverity,
                EnhancedAlertingSystem,
            )

            start_time = time.time()

            # 创建告警系统
            alerting = EnhancedAlertingSystem()

            # 添加简单规则
            simple_rule = AlertRule(
                rule_id="test_rule",
                name="测试规则",
                severity=AlertSeverity.P2_MEDIUM,
                condition=lambda m: m.get("test_value", 0) > 100,
                message_template="测试值过高: {test_value}",
                cooldown_seconds=0  # 禁用冷却
            )
            alerting.add_rule(simple_rule)

            # 触发告警
            alerting.evaluate_rules({"test_value": 150})
            active_alerts = alerting.get_active_alerts()

            if len(active_alerts) != 1:
                print_error(f"✗ 预期1个活跃告警，实际: {len(active_alerts)}")
                self.add_result("alert_lifecycle", "failed", "告警数量不正确")
                return False

            alert_id = active_alerts[0]["alert_id"]
            print_success(f"✓ 告警已创建: {alert_id}")

            # 确认告警
            alerting.acknowledge_alert(alert_id, "test_user")
            active_alerts = alerting.get_active_alerts()
            if active_alerts[0]["status"] != "acknowledged":
                print_error("✗ 告警确认失败")
                self.add_result("alert_lifecycle", "failed", "告警确认失败")
                return False
            print_success("✓ 告警已确认")

            # 静默告警
            alerting.silence_alert(alert_id, 10)  # 静默10秒
            active_alerts = alerting.get_active_alerts()
            if active_alerts[0]["status"] != "silenced":
                print_error("✗ 告警静默失败")
                self.add_result("alert_lifecycle", "failed", "告警静默失败")
                return False
            print_success("✓ 告警已静默")

            # 解决告警
            alerting.resolve_alert(alert_id)
            active_alerts = alerting.get_active_alerts()
            if len(active_alerts) != 0:
                print_error(f"✗ 告警解决失败，仍有{len(active_alerts)}个活跃告警")
                self.add_result("alert_lifecycle", "failed", "告警解决失败")
                return False
            print_success("✓ 告警已解决")

            # 检查历史记录
            history = alerting.get_alert_history(limit=10)
            if len(history) != 1:
                print_warning(f"⚠️ 历史记录数量: {len(history)}")
            else:
                print_success("✓ 告警已归档到历史")

            execution_time = time.time() - start_time

            self.add_result(
                "alert_lifecycle",
                "passed",
                "告警生命周期管理正常",
                execution_time,
                {"history_count": len(history)}
            )
            return True

        except Exception as e:
            print_error(f"✗ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            self.add_result("alert_lifecycle", "failed", str(e))
            return False

    def test_alert_statistics(self) -> bool:
        """测试告警统计"""
        print_section("测试5: 告警统计")

        try:
            from core.monitoring.enhanced_alerting_system import (
                EnhancedAlertingSystem,
                create_default_rules,
            )

            start_time = time.time()

            # 创建告警系统并添加规则
            alerting = EnhancedAlertingSystem()

            for rule in create_default_rules():
                alerting.add_rule(rule)

            # 触发多个告警
            metrics_high = {
                "error_rate": 10.0,
                "p95_latency_ms": 1500,
                "system.memory_usage_percent": 90
            }

            alerting.evaluate_rules(metrics_high)

            # 获取统计信息
            stats = alerting.get_statistics()
            print_info("告警统计:")
            print_info(f"  - 活跃告警: {stats['active_alerts']}")
            print_info(f"  - 总告警数: {stats['total_alerts']}")
            print_info(f"  - 启用规则: {stats['enabled_rules']}/{stats['total_rules']}")
            print_info(f"  - 状态分布: {stats['status_distribution']}")
            print_info(f"  - 严重程度分布: {stats['severity_distribution']}")

            # 解决所有告警
            for alert in alerting.get_active_alerts():
                alerting.resolve_alert(alert["alert_id"])

            # 再次获取统计
            stats_after = alerting.get_statistics()
            print_success(f"✓ 解决告警后: {stats_after['active_alerts']}个活跃告警")

            execution_time = time.time() - start_time

            self.add_result(
                "alert_statistics",
                "passed",
                "告警统计功能正常",
                execution_time,
                stats
            )
            return True

        except Exception as e:
            print_error(f"✗ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            self.add_result("alert_statistics", "failed", str(e))
            return False

    def test_alert_report_export(self) -> bool:
        """测试告警报告导出"""
        print_section("测试6: 告警报告导出")

        try:
            import json
            import tempfile

            from core.monitoring.enhanced_alerting_system import (
                EnhancedAlertingSystem,
                create_default_rules,
            )

            start_time = time.time()

            # 创建告警系统
            alerting = EnhancedAlertingSystem()

            # 添加规则并触发告警
            for rule in create_default_rules():
                alerting.add_rule(rule)

            alerting.evaluate_rules({
                "error_rate": 8.0,
                "throughput": 5
            })

            # 导出报告
            temp_dir = tempfile.mkdtemp(prefix="athena_alert_report_")
            temp_path = Path(temp_dir) / "test_report.json"

            alerting.export_report(temp_path)

            if not temp_path.exists():
                print_error("✗ 报告文件未生成")
                self.add_result("alert_report_export", "failed", "报告文件未生成")
                return False

            # 读取并验证报告
            with open(temp_path, encoding='utf-8') as f:
                report = json.load(f)

            print_info("报告内容:")
            print_info(f"  - 生成时间: {report['generated_at']}")
            print_info(f"  - 活跃告警: {len(report['active_alerts'])}")
            print_info(f"  - 历史告警: {len(report['recent_history'])}")
            print_info(f"  - 统计信息: {list(report['statistics'].keys())}")

            print_success("✓ 报告导出成功")

            # 清理
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

            execution_time = time.time() - start_time

            self.add_result(
                "alert_report_export",
                "passed",
                "告警报告导出正常",
                execution_time,
                {"report_path": str(temp_path)}
            )
            return True

        except Exception as e:
            print_error(f"✗ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            self.add_result("alert_report_export", "failed", str(e))
            return False

    def run_all_verifications(self) -> Any:
        """运行所有验证测试"""
        print_section("Athena增强监控告警系统验证")
        print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

        # 执行测试
        tests = [
            ("告警规则引擎", self.test_alert_rules),
            ("通知渠道", self.test_notification_channels),
            ("告警聚合", self.test_alert_aggregation),
            ("告警生命周期", self.test_alert_lifecycle),
            ("告警统计", self.test_alert_statistics),
            ("告警报告导出", self.test_alert_report_export),
        ]

        passed = 0
        failed = 0
        warnings = 0
        skipped = 0

        for test_name, test_func in tests:
            try:
                result = test_func()
                if result:
                    passed += 1
                elif result is None:
                    skipped += 1
                else:
                    failed += 1
            except Exception as e:
                print_error(f"测试执行异常: {test_name} - {e}")
                failed += 1

        # 打印摘要
        self.print_summary()

        return failed == 0

    def print_summary(self) -> Any:
        """打印验证摘要"""
        print_section("验证摘要")

        summary = self.results["summary"]
        total = summary["total"]
        passed = summary["passed"]
        failed = summary["failed"]
        warnings = summary["warnings"]

        print(f"总测试数: {total}")
        print_success(f"通过: {passed}")
        if failed > 0:
            print_error(f"失败: {failed}")
        if warnings > 0:
            print_warning(f"警告: {warnings}")

        success_rate = (passed / total * 100) if total > 0 else 0
        print(f"\n通过率: {success_rate:.1f}%")

        if success_rate >= 90:
            print_success("\n🎉 增强监控告警系统验证通过!")
        elif success_rate >= 70:
            print_warning("\n⚠ 系统基本可用，建议优化部分功能")
        else:
            print_error("\n❌ 系统存在较多问题，需要修复")

    def save_report(self) -> None:
        """保存验证报告"""
        import json

        report_dir = Path("logs/monitoring")
        report_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"enhanced_alerting_verification_{timestamp}.json"

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

        print_info(f"\n报告已保存: {report_file}")


def main() -> None:
    """主函数"""
    verifier = EnhancedAlertingVerifier()
    success = verifier.run_all_verifications()

    # 保存报告
    verifier.save_report()

    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
