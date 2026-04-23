#!/usr/bin/env python3
"""
端到端测试运行器

运行所有端到端测试并生成报告
"""

import argparse
import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# 添加项目根目录到sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.e2e.test_agent_workflow import (
    MockAnalyzerAgent,
    MockRetrieverAgent,
    MockWriterAgent,
    TestAgentIntegration,
    TestAgentPerformance,
    TestE2EWorkflow,
)


class E2ETestRunner:
    """端到端测试运行器"""

    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path("test_results/e2e")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results = []

    def create_test_report(self, test_name: str, start_time: float, end_time: float,
                          status: str, details: dict[str, Any] = None) -> dict[str, Any]:
        """创建测试报告"""
        duration = end_time - start_time

        report = {
            "test_name": test_name,
            "timestamp": datetime.now().isoformat(),
            "duration": duration,
            "status": status,
            "details": details or {}
        }

        return report

    async def run_workflow_tests(self) -> list[dict[str, Any]:
        """运行工作流测试"""
        print("🚀 开始运行工作流测试...")

        test = TestE2EWorkflow()
        mock_agents = {
            "retriever": MockRetrieverAgent(),
            "analyzer": MockAnalyzerAgent(),
            "writer": MockWriterAgent()
        }
        scenario_detector = MockScenarioDetector()

        results = []

        # 运行各个测试
        tests = [
            ("retriever_agent_workflow", test.test_retriever_agent_workflow),
            ("analyzer_agent_workflow", test.test_analyzer_agent_workflow),
            ("writer_agent_workflow", test.test_writer_agent_workflow),
            ("complete_workflow", test.test_complete_workflow),
            ("error_handling", test.test_error_handling)
        ]

        for test_name, test_func in tests:
            print(f"\n🧪 运行测试: {test_name}")
            start_time = time.time()

            try:
                if test_name == "complete_workflow":
                    # 完整工作流需要额外的参数
                    await test_func(mock_agents, scenario_detector)
                else:
                    await test_func(mock_agents)

                end_time = time.time()
                report = self.create_test_report(
                    test_name, start_time, end_time, "passed"
                )
                results.append(report)
                print(f"✅ 测试通过: {test_name}")

            except Exception as e:
                end_time = time.time()
                report = self.create_test_report(
                    test_name, start_time, end_time, "failed",
                    {"error": str(e)}
                )
                results.append(report)
                print(f"❌ 测试失败: {test_name} - {e}")

        return results

    async def run_performance_tests(self) -> list[dict[str, Any]:
        """运行性能测试"""
        print("\n🔥 开始运行性能测试...")

        test = TestAgentPerformance()
        results = []

        # 运行性能测试
        try:
            start_time = time.time()
            await test.test_workflow_performance()
            end_time = time.time()

            report = self.create_test_report(
                "workflow_performance", start_time, end_time, "passed"
            )
            results.append(report)
            print("✅ 性能测试通过")

        except Exception as e:
            end_time = time.time()
            report = self.create_test_report(
                "workflow_performance", start_time, end_time, "failed",
                {"error": str(e)}
            )
            results.append(report)
            print(f"❌ 性能测试失败: {e}")

        return results

    async def run_integration_tests(self) -> list[dict[str, Any]:
        """运行集成测试"""
        print("\n🔗 开始运行集成测试...")

        test = TestAgentIntegration()
        results = []

        # 运行集成测试
        try:
            start_time = time.time()
            await test.test_agent_registry_integration()
            end_time = time.time()

            report = self.create_test_report(
                "agent_registry_integration", start_time, end_time, "passed"
            )
            results.append(report)
            print("✅ 集成测试通过")

        except Exception as e:
            end_time = time.time()
            report = self.create_test_report(
                "agent_registry_integration", start_time, end_time, "failed",
                {"error": str(e)}
            )
            results.append(report)
            print(f"❌ 集成测试失败: {e}")

        return results

    def generate_summary_report(self, all_results: list[dict[str, Any]) -> dict[str, Any]:
        """生成汇总报告"""
        total_tests = len(all_results)
        passed_tests = sum(1 for r in all_results if r["status"] == "passed")
        failed_tests = total_tests - passed_tests

        total_duration = sum(r["duration"] for r in all_results)
        avg_duration = total_duration / total_tests if total_tests > 0 else 0

        # 按测试类型分组
        workflow_results = [r for r in all_results if "workflow" in r["test_name"]
        performance_results = [r for r in all_results if "performance" in r["test_name"]
        integration_results = [r for r in all_results if "integration" in r["test_name"]

        summary = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "pass_rate": passed_tests / total_tests if total_tests > 0 else 0,
            "total_duration": total_duration,
            "avg_duration": avg_duration,
            "test_groups": {
                "workflow": {
                    "count": len(workflow_results),
                    "passed": sum(1 for r in workflow_results if r["status"] == "passed"),
                    "failed": len(workflow_results) - sum(1 for r in workflow_results if r["status"] == "passed")
                },
                "performance": {
                    "count": len(performance_results),
                    "passed": sum(1 for r in performance_results if r["status"] == "passed"),
                    "failed": len(performance_results) - sum(1 for r in performance_results if r["status"] == "passed")
                },
                "integration": {
                    "count": len(integration_results),
                    "passed": sum(1 for r in integration_results if r["status"] == "passed"),
                    "failed": len(integration_results) - sum(1 for r in integration_results if r["status"] == "passed")
                }
            },
            "timestamp": datetime.now().isoformat(),
            "test_results": all_results
        }

        return summary

    def save_results(self, summary: dict[str, Any]) -> None:
        """保存测试结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 保存JSON报告
        json_file = self.output_dir / f"e2e_test_report_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        # 保存Markdown报告
        md_file = self.output_dir / f"e2e_test_report_{timestamp}.md"
        self.generate_markdown_report(summary, md_file)

        print("\n📊 测试报告已保存到:")
        print(f"   JSON: {json_file}")
        print(f"   Markdown: {md_file}")

    def generate_markdown_report(self, summary: dict[str, Any], output_file: Path) -> None:
        """生成Markdown报告"""
        md_content = f"""# 端到端测试报告

## 测试概览

- **测试时间**: {summary['timestamp']}
- **总测试数**: {summary['total_tests']}
- **通过测试**: {summary['passed_tests']}
- **失败测试**: {summary['failed_tests']}
- **通过率**: {summary['pass_rate']:.2%}
- **总耗时**: {summary['total_duration']:.2f}秒
- **平均耗时**: {summary['avg_duration']:.2f}秒

## 测试分组结果

### 工作流测试
- **数量**: {summary['test_groups']['workflow']['count']}
- **通过**: {summary['test_groups']['workflow']['passed']}
- **失败**: {summary['test_groups']['workflow']['failed']}

### 性能测试
- **数量**: {summary['test_groups']['performance']['count']}
- **通过**: {summary['test_groups']['performance']['passed']}
- **失败**: {summary['test_groups']['performance']['failed']}

### 集成测试
- **数量**: {summary['test_groups']['integration']['count']}
- **通过**: {summary['test_groups']['integration']['passed']}
- **失败**: {summary['test_groups']['integration']['failed']}

## 详细测试结果

"""

        for result in summary['test_results']:
            status_icon = "✅" if result['status'] == 'passed' else "❌"
            md_content += f"### {status_icon} {result['test_name']}\n"
            md_content += f"- **耗时**: {result['duration']:.2f}秒\n"
            md_content += f"- **状态**: {result['status']}\n"
            if result['details']:
                md_content += f"- **详情**: {json.dumps(result['details'], indent=2, ensure_ascii=False)}\n"
            md_content += "\n"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_content)

    async def run_all_tests(self) -> dict[str, Any]:
        """运行所有测试"""
        print("=" * 80)
        print("🚀 Athena平台端到端测试开始")
        print("=" * 80)

        all_results = []

        # 运行各类测试
        workflow_results = await self.run_workflow_tests()
        all_results.extend(workflow_results)

        performance_results = await self.run_performance_tests()
        all_results.extend(performance_results)

        integration_results = await self.run_integration_tests()
        all_results.extend(integration_results)

        # 生成汇总报告
        summary = self.generate_summary_report(all_results)

        # 保存结果
        self.save_results(summary)

        # 打印汇总
        print("\n" + "=" * 80)
        print("📊 测试汇总")
        print("=" * 80)
        print(f"总测试数: {summary['total_tests']}")
        print(f"通过: {summary['passed_tests']}")
        print(f"失败: {summary['failed_tests']}")
        print(f"通过率: {summary['pass_rate']:.2%}")
        print(f"总耗时: {summary['total_duration']:.2f}秒")

        if summary['failed_tests'] > 0:
            print("\n❌ 失败的测试:")
            for result in all_results:
                if result['status'] == 'failed':
                    print(f"   - {result['test_name']}: {result['details'].get('error', 'Unknown error')}")

        return summary


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='运行端到端测试')
    parser.add_argument('--output', '-o', type=str, help='输出目录')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')

    args = parser.parse_args()

    # 创建测试运行器
    output_dir = Path(args.output) if args.output else None
    runner = E2ETestRunner(output_dir)

    # 运行测试
    summary = await runner.run_all_tests()

    # 退出状态码
    sys.exit(0 if summary['failed_tests'] == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
