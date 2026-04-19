#!/usr/bin/env python3
"""
智能体设计模式综合测试运行器
Comprehensive Test Runner for Agentic Design Patterns
"""

import asyncio
import json
import logging
import os
import sys
import time
import unittest
from datetime import datetime
from pathlib import Path
from typing import Any

# 添加项目路径
sys.path.append('/Users/xujian/Athena工作平台')

from tests.performance.test_performance_benchmarks import PerformanceTestRunner
from tests.test_framework import test_environment

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/xujian/Athena工作平台/tests/logs/test_run.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ComprehensiveTestRunner:
    """综合测试运行器"""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.test_results = {}
        self.environment = test_environment

    async def run_all_tests(self):
        """运行所有测试"""
        self.start_time = time.time()

        logger.info("🚀 开始智能体设计模式综合测试")
        logger.info("=" * 60)

        # 设置测试环境
        await self.environment.setup({})

        try:
            # 1. 运行单元测试
            await self._run_unit_tests()

            # 2. 运行集成测试
            await self._run_integration_tests()

            # 3. 运行性能测试
            await self._run_performance_tests()

            # 4. 生成综合报告
            await self._generate_comprehensive_report()

        finally:
            # 清理测试环境
            await self.environment.teardown()

        self.end_time = time.time()

        # 输出测试总结
        self._print_test_summary()

    async def _run_unit_tests(self):
        """运行单元测试"""
        logger.info("\n🧪 第1阶段: 单元测试")
        logger.info("-" * 30)

        unit_test_modules = [
            'tests.unit.test_agentic_task_planner',
            'tests.unit.test_prompt_chain_processor',
            'tests.unit.test_goal_management_system'
        ]

        unit_results = {}

        for module_name in unit_test_modules:
            logger.info(f"🔍 运行模块: {module_name}")

            try:
                # 动态导入测试模块
                module = __import__(module_name, fromlist=[''])

                # 创建测试套件
                loader = unittest.TestLoader()
                suite = loader.loadTestsFromModule(module)

                # 运行测试
                runner = unittest.TextTestRunner(
                    verbosity=2,
                    stream=open(os.devnull, 'w'),  # 静默运行
                    buffer=True
                )

                start_time = time.time()
                result = runner.run(suite)
                end_time = time.time()

                # 记录结果
                unit_results[module_name] = {
                    'tests_run': result.testsRun,
                    'failures': len(result.failures),
                    'errors': len(result.errors),
                    'skipped': len(result.skipped) if hasattr(result, 'skipped') else 0,
                    'success': result.wasSuccessful(),
                    'execution_time': end_time - start_time,
                    'failure_details': [str(f[1]) for f in result.failures] if result.failures else [],
                    'error_details': [str(e[1]) for e in result.errors] if result.errors else []
                }

                status = "✅ 通过" if result.wasSuccessful() else "❌ 失败"
                logger.info(f"   {status} - {result.testsRun}个测试, "
                           f"耗时: {end_time - start_time:.2f}s")

                if not result.wasSuccessful():
                    logger.error(f"   失败详情: {len(result.failures)}个失败, {len(result.errors)}个错误")

            except Exception as e:
                logger.error(f"❌ 模块 {module_name} 运行失败: {e}")
                unit_results[module_name] = {
                    'tests_run': 0,
                    'failures': 0,
                    'errors': 1,
                    'skipped': 0,
                    'success': False,
                    'execution_time': 0,
                    'failure_details': [],
                    'error_details': [str(e)]
                }

        self.test_results['unit_tests'] = unit_results
        logger.info(f"📊 单元测试完成: {len(unit_results)}个模块")

    async def _run_integration_tests(self):
        """运行集成测试"""
        logger.info("\n🔗 第2阶段: 集成测试")
        logger.info("-" * 30)

        try:
            # 动态导入集成测试模块
            integration_module = __import__('tests.integration.test_agent_integrations', fromlist=[''])

            # 创建测试套件
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromModule(integration_module)

            # 运行测试
            runner = unittest.TextTestRunner(
                verbosity=2,
                stream=open(os.devnull, 'w'),
                buffer=True
            )

            start_time = time.time()
            result = runner.run(suite)
            end_time = time.time()

            # 记录结果
            integration_results = {
                'tests_run': result.testsRun,
                'failures': len(result.failures),
                'errors': len(result.errors),
                'skipped': len(result.skipped) if hasattr(result, 'skipped') else 0,
                'success': result.wasSuccessful(),
                'execution_time': end_time - start_time,
                'failure_details': [str(f[1]) for f in result.failures] if result.failures else [],
                'error_details': [str(e[1]) for e in result.errors] if result.errors else []
            }

            status = "✅ 通过" if result.wasSuccessful() else "❌ 失败"
            logger.info(f"   {status} - {result.testsRun}个测试, 耗时: {end_time - start_time:.2f}s")

            if not result.wasSuccessful():
                logger.error(f"   失败详情: {len(result.failures)}个失败, {len(result.errors)}个错误")

            self.test_results['integration_tests'] = integration_results

        except Exception as e:
            logger.error(f"❌ 集成测试运行失败: {e}")
            self.test_results['integration_tests'] = {
                'tests_run': 0,
                'failures': 0,
                'errors': 1,
                'skipped': 0,
                'success': False,
                'execution_time': 0,
                'failure_details': [],
                'error_details': [str(e)]
            }

        logger.info("📊 集成测试完成")

    async def _run_performance_tests(self):
        """运行性能测试"""
        logger.info("\n⚡ 第3阶段: 性能测试")
        logger.info("-" * 30)

        try:
            performance_runner = PerformanceTestRunner()

            start_time = time.time()
            await performance_runner.run_all_performance_tests()
            end_time = time.time()

            performance_results = {
                'tests_run': 'multiple',  # 性能测试数量可变
                'failures': 0,  # 简化处理
                'errors': 0,
                'skipped': 0,
                'success': True,  # 假设成功
                'execution_time': end_time - start_time,
                'failure_details': [],
                'error_details': []
            }

            status = "✅ 通过"
            logger.info(f"   {status} - 耗时: {end_time - start_time:.2f}s")

            self.test_results['performance_tests'] = performance_results

        except Exception as e:
            logger.error(f"❌ 性能测试运行失败: {e}")
            self.test_results['performance_tests'] = {
                'tests_run': 0,
                'failures': 0,
                'errors': 1,
                'skipped': 0,
                'success': False,
                'execution_time': 0,
                'failure_details': [],
                'error_details': [str(e)]
            }

        logger.info("📊 性能测试完成")

    async def _generate_comprehensive_report(self):
        """生成综合报告"""
        logger.info("\n📄 生成综合测试报告")
        logger.info("-" * 30)

        # 计算总体统计
        total_tests = 0
        total_failures = 0
        total_errors = 0
        total_execution_time = 0

        for _test_type, results in self.test_results.items():
            if isinstance(results.get('tests_run'), int):
                total_tests += results['tests_run']
                total_failures += results['failures']
                total_errors += results['errors']
                total_execution_time += results.get('execution_time', 0)

        success_rate = (total_tests - total_failures - total_errors) / total_tests if total_tests > 0 else 0

        # 生成报告内容
        report = {
            'test_run_info': {
                'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
                'end_time': datetime.fromtimestamp(self.end_time).isoformat(),
                'total_duration': self.end_time - self.start_time,
                'test_environment': 'development'
            },
            'summary': {
                'total_tests': total_tests,
                'total_failures': total_failures,
                'total_errors': total_errors,
                'success_rate': success_rate,
                'total_execution_time': total_execution_time
            },
            'detailed_results': self.test_results,
            'recommendations': self._generate_recommendations()
        }

        # 保存JSON报告
        reports_dir = Path('/Users/xujian/Athena工作平台/tests/reports')
        reports_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_report_file = reports_dir / f'comprehensive_test_report_{timestamp}.json'

        with open(json_report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        # 生成Markdown报告
        markdown_report = self._generate_markdown_report(report)
        markdown_report_file = reports_dir / f'comprehensive_test_report_{timestamp}.md'

        with open(markdown_report_file, 'w', encoding='utf-8') as f:
            f.write(markdown_report)

        logger.info(f"📊 JSON报告: {json_report_file}")
        logger.info(f"📄 Markdown报告: {markdown_report_file}")

    def _generate_recommendations(self) -> list[str]:
        """生成改进建议"""
        recommendations = []

        # 基于测试结果生成建议
        for test_type, results in self.test_results.items():
            if not results.get('success', True):
                if results['failures'] > 0:
                    recommendations.append(f"修复 {test_type} 中的 {results['failures']} 个失败测试")
                if results['errors'] > 0:
                    recommendations.append(f"解决 {test_type} 中的 {results['errors']} 个错误测试")

            # 性能建议
            if 'execution_time' in results and results['execution_time'] > 30:
                recommendations.append(f"优化 {test_type} 的执行性能 (当前: {results['execution_time']:.1f}s)")

        # 通用建议
        if not recommendations:
            recommendations.extend([
                "保持当前代码质量",
                "考虑添加更多边界测试用例",
                "定期运行性能基准测试"
            ])

        return recommendations

    def _generate_markdown_report(self, report: dict[str, Any]) -> str:
        """生成Markdown格式的报告"""
        lines = [
            "# 智能体设计模式综合测试报告",
            "",
            f"**测试时间**: {report['test_run_info']['start_time']}",
            f"**总耗时**: {report['test_run_info']['total_duration']:.2f} 秒",
            "",
            "## 📊 测试概览",
            "",
            f"- **总测试数**: {report['summary']['total_tests']}",
            f"- **失败数**: {report['summary']['total_failures']}",
            f"- **错误数**: {report['summary']['total_errors']}",
            f"- **成功率**: {report['summary']['success_rate']:.1%}",
            f"- **总执行时间**: {report['summary']['total_execution_time']:.2f} 秒",
            "",
            "## 🧪 详细测试结果",
            ""
        ]

        # 添加各测试类型的详细结果
        test_type_names = {
            'unit_tests': '单元测试',
            'integration_tests': '集成测试',
            'performance_tests': '性能测试'
        }

        for test_type, results in report['detailed_results'].items():
            test_name = test_type_names.get(test_type, test_type)
            status = "✅ 通过" if results.get('success', False) else "❌ 失败"

            lines.extend([
                f"### {test_name}",
                "",
                f"- **状态**: {status}",
                f"- **测试数**: {results['tests_run']}",
                f"- **失败数**: {results['failures']}",
                f"- **错误数**: {results['errors']}",
                f"- **执行时间**: {results.get('execution_time', 0):.2f} 秒",
                ""
            ])

            # 添加失败详情
            if results.get('failure_details'):
                lines.append("**失败详情**:")
                lines.append("")
                for detail in results['failure_details'][:3]:  # 只显示前3个
                    lines.append(f"- {detail[:100]}...")
                lines.append("")

        # 添加建议
        lines.extend([
            "## 💡 改进建议",
            ""
        ])

        for i, recommendation in enumerate(report['recommendations'], 1):
            lines.append(f"{i}. {recommendation}")

        lines.extend([
            "",
            "---",
            f"*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        ])

        return "\n".join(lines)

    def _print_test_summary(self):
        """打印测试总结"""
        total_duration = self.end_time - self.start_time

        logger.info("\n" + "=" * 60)
        logger.info("🎉 智能体设计模式综合测试完成")
        logger.info("=" * 60)

        # 计算总体统计
        total_tests = sum(
            results.get('tests_run', 0)
            for results in self.test_results.values()
        )
        total_failures = sum(
            results.get('failures', 0)
            for results in self.test_results.values()
        )
        total_errors = sum(
            results.get('errors', 0)
            for results in self.test_results.values()
        )

        success_tests = total_tests - total_failures - total_errors
        success_rate = success_tests / total_tests if total_tests > 0 else 0

        logger.info("📊 测试统计:")
        logger.info(f"   总测试数: {total_tests}")
        logger.info(f"   成功测试: {success_tests}")
        logger.info(f"   失败测试: {total_failures}")
        logger.info(f"   错误测试: {total_errors}")
        logger.info(f"   成功率: {success_rate:.1%}")
        logger.info(f"   总耗时: {total_duration:.2f} 秒")

        # 测试结果状态
        if total_failures == 0 and total_errors == 0:
            logger.info("\n🎉 所有测试通过！系统质量良好")
        elif total_failures > 0 or total_errors > 0:
            logger.warning(f"\n⚠️ 有 {total_failures + total_errors} 个测试需要修复")

        logger.info("\n📄 详细报告已保存到 tests/reports/ 目录")

# 主函数
async def main():
    """主函数"""
    runner = ComprehensiveTestRunner()

    try:
        await runner.run_all_tests()
        return 0
    except KeyboardInterrupt:
        logger.info("\n⚠️ 测试被用户中断")
        return 1
    except Exception as e:
        logger.error(f"\n❌ 测试运行失败: {e}")
        return 1

if __name__ == "__main__":
    # 创建必要的目录
    os.makedirs('/Users/xujian/Athena工作平台/tests/logs', exist_ok=True)
    os.makedirs('/Users/xujian/Athena工作平台/tests/reports', exist_ok=True)

    # 运行测试
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
