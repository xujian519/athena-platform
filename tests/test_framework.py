#!/usr/bin/env python3
"""
智能体设计模式测试框架
Agentic Design Patterns Test Framework

提供统一的测试基础设施和工具类
"""

import asyncio
import json
import logging

# 添加项目路径
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

sys.path.append('/Users/xujian/Athena工作平台')

logger = logging.getLogger(__name__)

@dataclass
class TestCase:
    """测试用例定义"""
    name: str
    description: str
    test_function: Callable
    expected_result: Any
    timeout: int = 30
    setup_data: dict[str, Any] = field(default_factory=dict)
    cleanup_data: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)

@dataclass
class TestResult:
    """测试结果"""
    test_name: str
    success: bool
    execution_time: float
    error_message: str | None = None
    actual_result: Any = None
    expected_result: Any = None
    performance_metrics: dict[str, float] = field(default_factory=dict)

@dataclass
class TestSuite:
    """测试套件"""
    name: str
    description: str
    test_cases: list[TestCase] = field(default_factory=list)
    setup_function: Callable | None = None
    teardown_function: Callable | None = None
    environment_config: dict[str, Any] = field(default_factory=dict)

class TestEnvironment:
    """测试环境管理器"""

    def __init__(self):
        self.temp_data = {}
        self.mock_services = {}
        self.performance_baseline = {}

    async def setup(self, config: dict[str, Any]):
        """设置测试环境"""
        self.config = config

        # 创建临时数据目录
        self.temp_dir = Path('/tmp/athena_test_data')
        self.temp_dir.mkdir(exist_ok=True)

        # 初始化模拟服务
        await self._init_mock_services()

        # 加载性能基准
        await self._load_performance_baseline()

        logger.info("✅ 测试环境设置完成")

    async def teardown(self):
        """清理测试环境"""
        # 清理临时数据
        if hasattr(self, 'temp_dir') and self.temp_dir.exists():
            import shutil
            shutil.rmtree(self.temp_dir)

        # 清理模拟服务
        self.mock_services.clear()
        self.temp_data.clear()

        logger.info("🧹 测试环境清理完成")

    async def _init_mock_services(self):
        """初始化模拟服务"""
        # 模拟认知引擎
        mock_cognitive_engine = AsyncMock()
        mock_cognitive_engine.initialize.return_value = None
        mock_cognitive_engine.process.return_value = {
            'cognition': 'mock_result',
            'agent_id': 'test_agent',
            'processing_type': 'test'
        }
        self.mock_services['cognitive_engine'] = mock_cognitive_engine

        # 模拟专利服务
        mock_patent_service = AsyncMock()
        mock_patent_service.initialize.return_value = None
        mock_patent_service.search_patents.return_value = {
            'count': 10,
            'patents': ['mock_patent_1', 'mock_patent_2']
        }
        self.mock_services['patent_service'] = mock_patent_service

    async def _load_performance_baseline(self):
        """加载性能基准"""
        baseline_file = Path('/Users/xujian/Athena工作平台/tests/data/performance_baseline.json')
        if baseline_file.exists():
            with open(baseline_file, encoding='utf-8') as f:
                self.performance_baseline = json.load(f)
        else:
            # 默认性能基准
            self.performance_baseline = {
                'task_planning': {'max_time': 2.0, 'min_success_rate': 0.95},
                'prompt_chaining': {'max_time': 3.0, 'min_success_rate': 0.90},
                'goal_management': {'max_time': 1.5, 'min_success_rate': 0.95},
                'agent_integration': {'max_time': 1.0, 'min_success_rate': 0.90}
            }

class TestRunner:
    """测试运行器"""

    def __init__(self, environment: TestEnvironment):
        self.environment = environment
        self.results: list[TestResult] = []
        self.start_time = None
        self.end_time = None

    async def run_test_suite(self, test_suite: TestSuite) -> list[TestResult]:
        """运行测试套件"""
        logger.info(f"🚀 开始运行测试套件: {test_suite.name}")
        suite_start_time = time.time()

        # 执行套件设置
        if test_suite.setup_function:
            await test_suite.setup_function(self.environment)

        suite_results = []

        # 运行每个测试用例
        for test_case in test_suite.test_cases:
            result = await self._run_single_test(test_case)
            suite_results.append(result)

        # 执行套件清理
        if test_suite.teardown_function:
            await test_suite.teardown_function(self.environment)

        suite_end_time = time.time()
        suite_duration = suite_end_time - suite_start_time

        logger.info(f"✅ 测试套件完成: {test_suite.name} (耗时: {suite_duration:.2f}秒)")

        return suite_results

    async def _run_single_test(self, test_case: TestCase) -> TestResult:
        """运行单个测试用例"""
        logger.info(f"🔍 运行测试: {test_case.name}")

        start_time = time.time()
        success = False
        error_message = None
        actual_result = None
        performance_metrics = {}

        try:
            # 设置超时
            test_future = test_case.test_function(self.environment, test_case.setup_data)

            # 执行测试
            actual_result = await asyncio.wait_for(test_future, timeout=test_case.timeout)

            # 验证结果
            if self._validate_result(actual_result, test_case.expected_result):
                success = True
                logger.info(f"✅ 测试通过: {test_case.name}")
            else:
                error_message = f"结果不匹配: 期望 {test_case.expected_result}, 实际 {actual_result}"
                logger.error(f"❌ 测试失败: {test_case.name} - {error_message}")

        except asyncio.TimeoutError:
            error_message = f"测试超时 (>{test_case.timeout}秒)"
            logger.error(f"⏰ 测试超时: {test_case.name}")

        except Exception as e:
            error_message = str(e)
            logger.error(f"💥 测试异常: {test_case.name} - {error_message}")

        finally:
            end_time = time.time()
            execution_time = end_time - start_time
            performance_metrics['execution_time'] = execution_time

            # 记录性能指标
            await self._record_performance_metrics(test_case.name, performance_metrics)

        return TestResult(
            test_name=test_case.name,
            success=success,
            execution_time=execution_time,
            error_message=error_message,
            actual_result=actual_result,
            expected_result=test_case.expected_result,
            performance_metrics=performance_metrics
        )

    def _validate_result(self, actual: Any, expected: Any) -> bool:
        """验证测试结果"""
        if isinstance(expected, dict) and isinstance(actual, dict):
            # 对于字典，检查关键字段
            for key, value in expected.items():
                if key not in actual or actual[key] != value:
                    return False
            return True
        else:
            # 简单值比较
            return actual == expected

    async def _record_performance_metrics(self, test_name: str, metrics: dict[str, float]):
        """记录性能指标"""
        # 这里可以记录到数据库或文件
        performance_file = Path('/Users/xujian/Athena工作平台/tests/reports/performance_metrics.json')

        # 读取现有数据
        if performance_file.exists():
            with open(performance_file, encoding='utf-8') as f:
                existing_data = json.load(f)
        else:
            existing_data = {}

        # 添加新数据
        timestamp = datetime.now().isoformat()
        if test_name not in existing_data:
            existing_data[test_name] = []

        existing_data[test_name].append({
            'timestamp': timestamp,
            'metrics': metrics
        })

        # 保持最新100条记录
        if len(existing_data[test_name]) > 100:
            existing_data[test_name] = existing_data[test_name][-100:]

        # 写入文件
        with open(performance_file, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)

class TestReporter:
    """测试报告生成器"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)

    def generate_report(self, test_results: list[TestResult], suite_name: str) -> str:
        """生成测试报告"""
        report_data = {
            'suite_name': suite_name,
            'timestamp': datetime.now().isoformat(),
            'summary': self._generate_summary(test_results),
            'results': self._format_results(test_results),
            'performance_analysis': self._analyze_performance(test_results)
        }

        # 生成HTML报告
        html_report = self._generate_html_report(report_data)

        # 生成JSON报告
        json_report = json.dumps(report_data, indent=2, ensure_ascii=False, default=str)

        # 保存报告
        html_file = self.output_dir / f'{suite_name}_report.html'
        json_file = self.output_dir / f'{suite_name}_report.json'

        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_report)

        with open(json_file, 'w', encoding='utf-8') as f:
            f.write(json_report)

        logger.info(f"📊 测试报告已生成: {html_file}")

        return str(html_file)

    def _generate_summary(self, results: list[TestResult]) -> dict[str, Any]:
        """生成测试摘要"""
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.success)
        failed_tests = total_tests - passed_tests
        total_time = sum(r.execution_time for r in results)
        avg_time = total_time / total_tests if total_tests > 0 else 0

        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': passed_tests / total_tests if total_tests > 0 else 0,
            'total_execution_time': total_time,
            'average_execution_time': avg_time
        }

    def _format_results(self, results: list[TestResult]) -> list[dict[str, Any]]:
        """格式化测试结果"""
        formatted_results = []

        for result in results:
            formatted_result = {
                'test_name': result.test_name,
                'success': result.success,
                'execution_time': result.execution_time,
                'error_message': result.error_message,
                'performance_metrics': result.performance_metrics
            }

            # 添加结果信息（简化处理）
            if result.success:
                formatted_result['status'] = 'PASSED'
            else:
                formatted_result['status'] = 'FAILED'

            formatted_results.append(formatted_result)

        return formatted_results

    def _analyze_performance(self, results: list[TestResult]) -> dict[str, Any]:
        """分析性能数据"""
        performance_data = []

        for result in results:
            performance_data.append({
                'test_name': result.test_name,
                'execution_time': result.execution_time
            })

        # 计算性能统计
        execution_times = [r.execution_time for r in results]

        return {
            'fastest_test': min(performance_data, key=lambda x: x['execution_time']),
            'slowest_test': max(performance_data, key=lambda x: x['execution_time']),
            'average_time': sum(execution_times) / len(execution_times) if execution_times else 0,
            'performance_distribution': {
                'under_1s': len([t for t in execution_times if t < 1.0]),
                'between_1s_3s': len([t for t in execution_times if 1.0 <= t < 3.0]),
                'over_3s': len([t for t in execution_times if t >= 3.0])
            }
        }

    def _generate_html_report(self, report_data: dict[str, Any]) -> str:
        """生成HTML格式的报告"""
        html_template = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>智能体设计模式测试报告 - {suite_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .summary-card {{ background: #f8f9fa; padding: 20px; border-radius: 6px; text-align: center; }}
        .summary-card h3 {{ margin: 0 0 10px 0; color: #333; }}
        .summary-card .value {{ font-size: 2em; font-weight: bold; color: #007bff; }}
        .results-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        .results-table th, .results-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        .results-table th {{ background-color: #f8f9fa; font-weight: bold; }}
        .status-passed {{ color: #28a745; font-weight: bold; }}
        .status-failed {{ color: #dc3545; font-weight: bold; }}
        .performance-section {{ margin-top: 30px; }}
        .performance-chart {{ background: #f8f9fa; padding: 20px; border-radius: 6px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 智能体设计模式测试报告</h1>
            <h2>{suite_name}</h2>
            <p>生成时间: {timestamp}</p>
        </div>

        <div class="summary">
            <div class="summary-card">
                <h3>总测试数</h3>
                <div class="value">{total_tests}</div>
            </div>
            <div class="summary-card">
                <h3>通过测试</h3>
                <div class="value status-passed">{passed_tests}</div>
            </div>
            <div class="summary-card">
                <h3>失败测试</h3>
                <div class="value status-failed">{failed_tests}</div>
            </div>
            <div class="summary-card">
                <h3>成功率</h3>
                <div class="value">{success_rate:.1%}</div>
            </div>
            <div class="summary-card">
                <h3>总耗时</h3>
                <div class="value">{total_execution_time:.2f}s</div>
            </div>
            <div class="summary-card">
                <h3>平均耗时</h3>
                <div class="value">{average_execution_time:.2f}s</div>
            </div>
        </div>

        <h3>📋 详细测试结果</h3>
        <table class="results-table">
            <thead>
                <tr>
                    <th>测试名称</th>
                    <th>状态</th>
                    <th>执行时间 (秒)</th>
                    <th>错误信息</th>
                </tr>
            </thead>
            <tbody>
                {results_rows}
            </tbody>
        </table>

        <div class="performance-section">
            <h3>⚡ 性能分析</h3>
            <div class="performance-chart">
                <p><strong>最快测试:</strong> {fastest_test_name} ({fastest_test_time:.3f}s)</p>
                <p><strong>最慢测试:</strong> {slowest_test_name} ({slowest_test_time:.3f}s)</p>
                <p><strong>性能分布:</strong> &lt;1s: {under_1s} | 1-3s: {between_1s_3s} | &gt;3s: {over_3s}</p>
            </div>
        </div>
    </div>
</body>
</html>
        """

        # 准备模板变量
        summary = report_data['summary']
        performance = report_data['performance_analysis']

        # 生成结果表格行
        results_rows = ""
        for result in report_data['results']:
            status_class = "status-passed" if result['success'] else "status-failed"
            error_msg = result.get('error_message', 'N/A') if not result['success'] else 'N/A'

            results_rows += f"""
                <tr>
                    <td>{result['test_name']}</td>
                    <td class="{status_class}">{result['status']}</td>
                    <td>{result['execution_time']:.3f}</td>
                    <td>{error_msg}</td>
                </tr>
            """

        return html_template.format(
            suite_name=report_data['suite_name'],
            timestamp=report_data['timestamp'],
            total_tests=summary['total_tests'],
            passed_tests=summary['passed_tests'],
            failed_tests=summary['failed_tests'],
            success_rate=summary['success_rate'],
            total_execution_time=summary['total_execution_time'],
            average_execution_time=summary['average_execution_time'],
            results_rows=results_rows,
            fastest_test_name=performance['fastest_test']['test_name'],
            fastest_test_time=performance['fastest_test']['execution_time'],
            slowest_test_name=performance['slowest_test']['test_name'],
            slowest_test_time=performance['slowest_test']['execution_time'],
            under_1s=performance['performance_distribution']['under_1s'],
            between_1s_3s=performance['performance_distribution']['between_1s_3s'],
            over_3s=performance['performance_distribution']['over_3s']
        )

class TestDataGenerator:
    """测试数据生成器"""

    @staticmethod
    def generate_planning_test_data() -> dict[str, Any]:
        """生成规划测试数据"""
        return {
            'simple_task': {
                'goal': '分析系统性能',
                'context': {'priority': 'medium', 'deadline': '1 day'},
                'expected_steps': 3
            },
            'complex_task': {
                'goal': '设计和实现新的存储架构',
                'context': {'priority': 'high', 'deadline': '2 weeks'},
                'expected_steps': 8
            },
            'technical_task': {
                'goal': '优化数据库查询性能',
                'context': {'domain': 'database', 'metrics': ['response_time', 'throughput']},
                'expected_steps': 5
            }
        }

    @staticmethod
    def generate_chain_test_data() -> dict[str, Any]:
        """生成提示链测试数据"""
        return {
            'patent_analysis': {
                'query': '分析人工智能领域的专利技术趋势',
                'expected_steps': 6,
                'expected_output_fields': ['trends', 'innovations', 'legal_analysis']
            },
            'technical_evaluation': {
                'query': '评估区块链技术的商业应用潜力',
                'expected_steps': 4,
                'expected_output_fields': ['technical_feasibility', 'market_potential']
            }
        }

    @staticmethod
    def generate_goal_test_data() -> dict[str, Any]:
        """生成目标管理测试数据"""
        return {
            'learning_goal': {
                'title': '学习Python编程',
                'description': '在3个月内掌握Python基础和高级特性',
                'expected_subgoals': 4,
                'expected_metrics': 3
            },
            'business_goal': {
                'title': '提升系统性能30%',
                'description': '通过优化架构和算法实现性能提升',
                'expected_subgoals': 6,
                'expected_metrics': 4
            }
        }

    @staticmethod
    def generate_collaboration_test_data() -> dict[str, Any]:
        """生成协作测试数据"""
        return {
            'multi_agent_project': {
                'goal': '开发智能专利分析系统',
                'participants': ['xiaonuo', 'xiaona', 'yunxi', 'xiaochen'],
                'expected_tasks': 5,
                'expected_collaboration_mode': 'hierarchical'
            },
            'analysis_collaboration': {
                'goal': '完成技术专利综合分析报告',
                'participants': ['xiaona', 'yunxi'],
                'expected_tasks': 3,
                'expected_collaboration_mode': 'parallel'
            }
        }

# 创建全局测试实例
test_environment = TestEnvironment()
test_runner = TestRunner(test_environment)
test_reporter = TestReporter(Path('/Users/xujian/Athena工作平台/tests/reports'))
test_data_generator = TestDataGenerator()
