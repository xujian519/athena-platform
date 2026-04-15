#!/usr/bin/env python3
"""
Athena全链路监控系统验证脚本
Full-Link Monitoring System Verification Script

验证全链路监控系统的所有功能：
1. 链路追踪功能
2. 性能指标收集
3. 异常告警机制
4. 结果验证功能
5. 监控仪表板

作者: Athena平台团队
创建时间: 2025-12-29
版本: v1.0.0
"""

from __future__ import annotations
import asyncio
import json
import logging
import sys
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


class FullLinkMonitoringVerifier:
    """全链路监控验证器"""

    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0
            }
        }

        self.test_data = {}

    def add_result(self, test_name: str, status: str, details: str = "",
                   execution_time: float = 0.0, data: Any = None):
        """添加测试结果"""
        self.results["tests"][test_name] = {
            "status": status,  # passed, failed, warning
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

    async def test_link_tracing(self, monitoring_system) -> bool:
        """测试链路追踪功能"""
        print_section("测试1: 链路追踪功能")

        try:
            import time

            # 测试基本追踪
            print_info("测试基本链路追踪")
            start_time = time.time()

            trace_id = monitoring_system.start_trace(
                operation="test_operation",
                input_data={"test": "data"},
                tags={"test": "true"}
            )

            time.sleep(0.1)

            monitoring_system.finish_trace(
                trace_id=trace_id,
                output_data={"result": "success"},
                status="success"
            )

            execution_time = time.time() - start_time

            # 验证追踪数据
            trace = monitoring_system.get_trace(trace_id)
            if trace and trace["status"] == "success":
                print_success(f"  ✓ 链路追踪成功 ({execution_time:.3f}秒)")
                self.add_result("link_tracing", "passed", "链路追踪成功",
                               execution_time, trace)
                return True
            else:
                print_error("  ✗ 链路追踪数据不完整")
                self.add_result("link_tracing", "failed", "追踪数据不完整",
                               execution_time)
                return False

        except Exception as e:
            print_error(f"  ✗ 链路追踪测试异常: {e}")
            self.add_result("link_tracing", "failed", str(e))
            return False

    async def test_performance_metrics(self, monitoring_system) -> bool:
        """测试性能指标收集"""
        print_section("测试2: 性能指标收集")

        try:
            import time

            print_info("测试指标记录")
            start_time = time.time()

            # 添加测试指标
            from core.monitoring.full_link_monitoring_system import MetricPoint, MetricType

            monitoring_system.add_metric(
                MetricPoint(
                    name="test.metric.counter",
                    type=MetricType.COUNTER,
                    value=42.0,
                    labels={"test": "true"}
                )
            )

            monitoring_system.add_metric(
                MetricPoint(
                    name="test.metric.gauge",
                    type=MetricType.GAUGE,
                    value=99.9,
                    labels={"test": "true"}
                )
            )

            execution_time = time.time() - start_time

            # 验证指标
            metrics_summary = monitoring_system.get_metrics_summary()
            if metrics_summary["total_metrics"] >= 2:
                print_success(f"  ✓ 指标收集成功 ({metrics_summary['total_metrics']}个指标, {execution_time:.3f}秒)")
                self.add_result("performance_metrics", "passed",
                              f"收集了{metrics_summary['total_metrics']}个指标",
                               execution_time, metrics_summary)
                return True
            else:
                print_warning(f"  ⚠ 指标数量不足: {metrics_summary['total_metrics']}")
                self.add_result("performance_metrics", "warning",
                              f"指标数量: {metrics_summary['total_metrics']}",
                               execution_time)
                return False

        except Exception as e:
            print_error(f"  ✗ 指标收集测试异常: {e}")
            self.add_result("performance_metrics", "failed", str(e))
            return False

    async def test_result_validation(self, monitoring_system) -> bool:
        """测试结果验证功能"""
        print_section("测试3: 结果验证功能")

        try:
            import time

            print_info("测试有效结果验证")
            start_time = time.time()

            # 有效结果
            valid_result = {
                "analysis": "代码分析完成",
                "complexity": "低",
                "lines": 10
            }
            validation_result, error = monitoring_system.validate_result(
                "code_analyzer",
                valid_result
            )

            execution_time = time.time() - start_time

            if validation_result.value == "valid":
                print_success(f"  ✓ 有效结果验证通过 ({execution_time:.3f}秒)")
            else:
                print_warning(f"  ⚠ 有效结果验证失败: {error}")

            # 测试无效结果
            print_info("测试无效结果检测")

            invalid_result = {
                "analysis": "代码分析完成"
                # 缺少必填字段
            }
            validation_result, error = monitoring_system.validate_result(
                "code_analyzer",
                invalid_result
            )

            if validation_result.value != "valid":
                print_success(f"  ✓ 无效结果正确检测: {validation_result.value}")
                self.add_result("result_validation", "passed",
                              "成功检测有效和无效结果", execution_time)
                return True
            else:
                print_error("  ✗ 未能检测无效结果")
                self.add_result("result_validation", "failed",
                              "未能检测无效结果")
                return False

        except Exception as e:
            print_error(f"  ✗ 结果验证测试异常: {e}")
            self.add_result("result_validation", "failed", str(e))
            return False

    async def test_alert_system(self, monitoring_system) -> bool:
        """测试告警系统"""
        print_section("测试4: 异常告警系统")

        try:
            import time

            print_info("测试告警触发")
            start_time = time.time()

            # 获取当前告警
            dashboard = monitoring_system.get_dashboard_data()
            initial_alerts = dashboard.get("active_alerts", [])

            print_info(f"当前活跃告警: {len(initial_alerts)}个")

            execution_time = time.time() - start_time

            print_success(f"  ✓ 告警系统正常运行 ({execution_time:.3f}秒)")
            self.add_result("alert_system", "passed",
                          f"告警系统正常, 当前{len(initial_alerts)}个活跃告警",
                           execution_time, {"alert_count": len(initial_alerts)})
            return True

        except Exception as e:
            print_error(f"  ✗ 告警系统测试异常: {e}")
            self.add_result("alert_system", "failed", str(e))
            return False

    async def test_monitoring_dashboard(self, monitoring_system) -> bool:
        """测试监控仪表板"""
        print_section("测试5: 监控仪表板")

        try:
            import time

            print_info("生成监控仪表板数据")
            start_time = time.time()

            dashboard = monitoring_system.get_dashboard_data()

            execution_time = time.time() - start_time

            # 验证仪表板数据
            required_sections = ["timestamp", "current_metrics", "recent_traces",
                               "active_alerts", "performance_stats", "summary"]
            missing_sections = [s for s in required_sections if s not in dashboard]

            if missing_sections:
                print_warning(f"  ⚠ 仪表板缺少部分数据: {missing_sections}")
                self.add_result("monitoring_dashboard", "warning",
                              f"缺少部分数据: {missing_sections}",
                               execution_time, dashboard)
                return False
            else:
                print_success(f"  ✓ 监控仪表板数据完整 ({execution_time:.3f}秒)")

                # 显示仪表板摘要
                print_info("仪表板摘要:")
                print(f"  - 活跃追踪: {dashboard['summary']['active_traces']}")
                print(f"  - 已完成追踪: {dashboard['summary']['completed_traces']}")
                print(f"  - 总指标数: {dashboard['summary']['total_metrics']}")
                print(f"  - 活跃告警: {dashboard['summary']['unresolved_alerts']}")

                self.add_result("monitoring_dashboard", "passed",
                              "仪表板数据完整", execution_time, dashboard)
                return True

        except Exception as e:
            print_error(f"  ✗ 监控仪表板测试异常: {e}")
            self.add_result("monitoring_dashboard", "failed", str(e))
            return False

    async def test_integration_with_tool_manager(self, monitoring_system) -> bool:
        """测试与工具调用管理器的集成"""
        print_section("测试6: 工具调用管理器集成")

        try:
            import time

            from core.tools.monitored_tool_call_manager import get_monitored_tool_manager

            print_info("获取增强工具调用管理器")
            manager = get_monitored_tool_manager()

            print_info(f"已注册工具: {len(manager.tools)}个")

            print_info("测试工具调用（带监控）")
            start_time = time.time()

            result = await manager.call_tool(
                tool_name="emotional_support",
                parameters={"emotion": "焦虑", "intensity": 7},
                enable_monitoring=True,
                enable_validation=True
            )

            execution_time = time.time() - start_time

            if result.status.value == "success":
                print_success(f"  ✓ 工具调用成功 ({execution_time:.3f}秒)")
                print_info(f"  - 追踪ID: {result.trace_id[:8] if result.trace_id else 'N/A'}...")
                print_info(f"  - 验证结果: {result.validation_result.value if result.validation_result else 'N/A'}")
                print_info(f"  - 执行时间: {result.execution_time:.3f}秒")

                self.add_result("tool_manager_integration", "passed",
                              f"工具调用成功，验证: {result.validation_result.value if result.validation_result else 'N/A'}",
                               execution_time, {
                                   "trace_id": result.trace_id,
                                   "validation": result.validation_result.value if result.validation_result else None
                               })
                return True
            else:
                print_error(f"  ✗ 工具调用失败: {result.error}")
                self.add_result("tool_manager_integration", "failed",
                              result.error, execution_time)
                return False

        except Exception as e:
            print_error(f"  ✗ 工具管理器集成测试异常: {e}")
            self.add_result("tool_manager_integration", "failed", str(e))
            return False

    async def run_all_verifications(self):
        """运行所有验证测试"""
        print_section("Athena全链路监控系统验证")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 导入必要模块
        from core.monitoring.full_link_monitoring_system import get_monitoring_system

        # 获取监控系统
        monitoring_system = get_monitoring_system()

        # 执行测试
        tests = [
            ("链路追踪功能", self.test_link_tracing),
            ("性能指标收集", self.test_performance_metrics),
            ("结果验证功能", self.test_result_validation),
            ("异常告警系统", self.test_alert_system),
            ("监控仪表板", self.test_monitoring_dashboard),
            ("工具管理器集成", self.test_integration_with_tool_manager)
        ]

        passed = 0
        failed = 0
        warnings = 0

        for test_name, test_func in tests:
            try:
                result = await test_func(monitoring_system)
                if result:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print_error(f"测试执行异常: {test_name} - {e}")
                failed += 1

        # 打印摘要
        self.print_summary()

        # 保存报告
        self.save_report()

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
            print_success("\n🎉 全链路监控系统验证通过!")
        elif success_rate >= 70:
            print_warning("\n⚠ 系统基本可用，建议优化部分功能")
        else:
            print_error("\n❌ 系统存在较多问题，需要修复")

    def save_report(self) -> None:
        """保存验证报告"""
        report_dir = Path("logs/monitoring")
        report_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"full_link_monitoring_verification_{timestamp}.json"

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

        print_info(f"\n报告已保存: {report_file}")


async def main():
    """主函数"""
    verifier = FullLinkMonitoringVerifier()
    success = await verifier.run_all_verifications()

    # 返回退出码
    if success:
        return 0
    else:
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
