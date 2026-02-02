#!/usr/bin/env python3

# Athena AI平台 - 完整自动化测试套件
# 生成时间: 2025-12-11
# 功能: 单元测试、集成测试、端到端测试、性能测试、安全测试

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_execution.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TestRunner:
    """测试运行器主类"""

    def __init__(self, test_type: str = 'all', coverage: bool = True, parallel: bool = True):
        self.test_type = test_type
        self.coverage = coverage
        self.parallel = parallel
        self.start_time = datetime.now()
        self.results = {
            'unit_tests': {},
            'integration_tests': {},
            'e2e_tests': {},
            'performance_tests': {},
            'security_tests': {},
            'summary': {}
        }
        self.report_dir = PROJECT_ROOT / 'test_reports' / f"test_report_{self.start_time.strftime('%Y%m%d_%H%M%S')}"
        self.report_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"初始化测试运行器 - 类型: {test_type}, 覆盖率: {coverage}, 并行: {parallel}")

    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        logger.info('🚀 开始运行Athena AI平台完整测试套件')

        try:
            # 环境检查
            self._check_environment()

            # 运行不同类型的测试
            if self.test_type in ['all', 'unit']:
                self._run_unit_tests()

            if self.test_type in ['all', 'integration']:
                self._run_integration_tests()

            if self.test_type in ['all', 'e2e']:
                self._run_e2e_tests()

            if self.test_type in ['all', 'performance']:
                self._run_performance_tests()

            if self.test_type in ['all', 'security']:
                self._run_security_tests()

            # 生成综合报告
            self._generate_comprehensive_report()

            logger.info('✅ 所有测试执行完成')
            return self.results

        except Exception as e:
            logger.error(f"❌ 测试执行失败: {str(e)}")
            raise

    def _check_environment(self) -> None:
        """检查测试环境"""
        logger.info('🔍 检查测试环境...')

        # 检查Python版本
        python_version = sys.version_info
        if python_version < (3, 8):
            raise RuntimeError(f"Python版本过低: {python_version}，需要Python 3.8+")

        # 检查必要的依赖
        required_packages = [
            'pytest', 'pytest-cov', 'pytest-asyncio', 'pytest-mock',
            'requests', 'httpx', 'beautifulsoup4', 'selenium'
        ]

        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
            except ImportError:
                logger.error(f"缺少依赖包: {package}")
                raise

        # 检查Docker（如果需要）
        if self.test_type in ['integration', 'e2e']:
            try:
                subprocess.run(['docker', '--version'], check=True, capture_output=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.warning('Docker未安装，部分集成测试可能无法运行')

        logger.info('✅ 环境检查通过')

    def _run_unit_tests(self) -> None:
        """运行单元测试"""
        logger.info('🧪 运行单元测试...')

        start_time = time.time()

        # 构建pytest命令
        cmd = [
            'python', '-m', 'pytest',
            'tests/unit/',
            '-v',
            '--tb=short',
            '--durations=10'
        ]

        if self.coverage:
            cmd.extend([
                '--cov=src',
                '--cov-report=term-missing',
                '--cov-report=html:' + str(self.report_dir / 'htmlcov'),
                '--cov-report=xml:' + str(self.report_dir / 'coverage.xml'),
                '--cov-fail-under=85'
            ])

        if self.parallel:
            cmd.extend(['-n', 'auto'])

        # 运行测试
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT)

        execution_time = time.time() - start_time

        # 解析结果
        self.results['unit_tests'] = {
            'status': 'passed' if result.returncode == 0 else 'failed',
            'execution_time': execution_time,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'return_code': result.returncode
        }

        # 提取测试统计
        if result.returncode == 0:
            logger.info(f"✅ 单元测试通过 - 耗时: {execution_time:.2f}秒")
        else:
            logger.error(f"❌ 单元测试失败 - 耗时: {execution_time:.2f}秒")
            logger.error(result.stderr)

    def _run_integration_tests(self) -> None:
        """运行集成测试"""
        logger.info('🔗 运行集成测试...')

        start_time = time.time()

        # 构建pytest命令
        cmd = [
            'python', '-m', 'pytest',
            'tests/integration/',
            '-v',
            '--tb=short',
            '--durations=10'
        ]

        # 集成测试通常需要并行运行
        if self.parallel:
            cmd.extend(['-n', 'auto'])

        # 运行测试
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT)

        execution_time = time.time() - start_time

        # 解析结果
        self.results['integration_tests'] = {
            'status': 'passed' if result.returncode == 0 else 'failed',
            'execution_time': execution_time,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'return_code': result.returncode
        }

        if result.returncode == 0:
            logger.info(f"✅ 集成测试通过 - 耗时: {execution_time:.2f}秒")
        else:
            logger.error(f"❌ 集成测试失败 - 耗时: {execution_time:.2f}秒")
            logger.error(result.stderr)

    def _run_e2e_tests(self) -> None:
        """运行端到端测试"""
        logger.info('🌐 运行端到端测试...')

        start_time = time.time()

        # 构建pytest命令
        cmd = [
            'python', '-m', 'pytest',
            'tests/e2e/',
            '-v',
            '--tb=short',
            '--durations=10',
            '--maxfail=3'  # 最多允许3个失败
        ]

        # 运行测试
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT)

        execution_time = time.time() - start_time

        # 解析结果
        self.results['e2e_tests'] = {
            'status': 'passed' if result.returncode == 0 else 'failed',
            'execution_time': execution_time,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'return_code': result.returncode
        }

        if result.returncode == 0:
            logger.info(f"✅ 端到端测试通过 - 耗时: {execution_time:.2f}秒")
        else:
            logger.error(f"❌ 端到端测试失败 - 耗时: {execution_time:.2f}秒")
            logger.error(result.stderr)

    def _run_performance_tests(self) -> None:
        """运行性能测试"""
        logger.info('⚡ 运行性能测试...')

        start_time = time.time()

        # 构建pytest命令
        cmd = [
            'python', '-m', 'pytest',
            'tests/performance/',
            '-v',
            '--tb=short',
            '--benchmark-only',
            '--benchmark-json=' + str(self.report_dir / 'benchmark.json')
        ]

        # 运行测试
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT)

        execution_time = time.time() - start_time

        # 解析结果
        self.results['performance_tests'] = {
            'status': 'passed' if result.returncode == 0 else 'failed',
            'execution_time': execution_time,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'return_code': result.returncode
        }

        # 如果有基准测试结果，进行分析
        benchmark_file = self.report_dir / 'benchmark.json'
        if benchmark_file.exists():
            try:
                with open(benchmark_file, 'r') as f:
                    benchmark_data = json.load(f)
                self._analyze_performance_results(benchmark_data)
            except Exception as e:
                logger.warning(f"无法分析性能测试结果: {e}")

        if result.returncode == 0:
            logger.info(f"✅ 性能测试通过 - 耗时: {execution_time:.2f}秒")
        else:
            logger.error(f"❌ 性能测试失败 - 耗时: {execution_time:.2f}秒")
            logger.error(result.stderr)

    def _analyze_performance_results(self, benchmark_data: Dict) -> None:
        """分析性能测试结果"""
        logger.info('📊 分析性能测试结果...')

        benchmarks = benchmark_data.get('benchmarks', [])

        if not benchmarks:
            logger.warning('未找到性能基准测试数据')
            return

        # 性能统计分析
        for benchmark in benchmarks:
            name = benchmark.get('name', 'unknown')
            stats = benchmark.get('stats', {})

            min_time = stats.get('min', 0)
            max_time = stats.get('max', 0)
            mean_time = stats.get('mean', 0)
            std_dev = stats.get('stddev', 0)

            logger.info(f"性能基准 {name}:")
            logger.info(f"  平均时间: {mean_time:.4f}s ± {std_dev:.4f}s")
            logger.info(f"  范围: {min_time:.4f}s - {max_time:.4f}s")

        # 保存性能分析报告
        analysis_file = self.report_dir / 'performance_analysis.json'
        with open(analysis_file, 'w') as f:
            json.dump({
                'analysis_time': datetime.now().isoformat(),
                'benchmarks': benchmarks
            }, f, indent=2)

    def _run_security_tests(self) -> None:
        """运行安全测试"""
        logger.info('🔒 运行安全测试...')

        start_time = time.time()

        # 构建pytest命令
        cmd = [
            'python', '-m', 'pytest',
            'tests/security/',
            '-v',
            '--tb=short'
        ]

        # 运行测试
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT)

        execution_time = time.time() - start_time

        # 解析结果
        self.results['security_tests'] = {
            'status': 'passed' if result.returncode == 0 else 'failed',
            'execution_time': execution_time,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'return_code': result.returncode
        }

        if result.returncode == 0:
            logger.info(f"✅ 安全测试通过 - 耗时: {execution_time:.2f}秒")
        else:
            logger.error(f"❌ 安全测试失败 - 耗时: {execution_time:.2f}秒")
            logger.error(result.stderr)

    def _generate_comprehensive_report(self) -> None:
        """生成综合测试报告"""
        logger.info('📋 生成综合测试报告...')

        total_time = time.time() - time.mktime(self.start_time.timetuple())

        # 统计结果
        total_tests = 0
        passed_tests = 0
        failed_tests = 0

        for test_type, result in self.results.items():
            if test_type == 'summary':
                continue

            if result.get('status') == 'passed':
                passed_tests += 1
            else:
                failed_tests += 1
            total_tests += 1

        # 生成摘要
        self.results['summary'] = {
            'total_execution_time': total_time,
            'total_test_suites': total_tests,
            'passed_suites': passed_tests,
            'failed_suites': failed_tests,
            'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            'report_directory': str(self.report_dir),
            'generated_at': datetime.now().isoformat()
        }

        # 保存JSON报告
        json_report = self.report_dir / 'test_report.json'
        with open(json_report, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        # 生成HTML报告
        self._generate_html_report()

        # 生成Markdown报告
        self._generate_markdown_report()

        logger.info(f"📊 测试报告生成完成: {self.report_dir}")

        # 打印摘要
        self._print_summary()

    def _generate_html_report(self) -> None:
        """生成HTML格式的测试报告"""
        html_file = self.report_dir / 'test_report.html'

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Athena AI平台测试报告</title>
    <meta charset='utf-8'>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ margin: 20px 0; padding: 15px; background-color: #e8f4f8; border-radius: 5px; }}
        .test-section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .passed {{ color: green; }}
        .failed {{ color: red; }}
        .pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 3px; overflow-x: auto; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class='header'>
        <h1>🚀 Athena AI平台测试报告</h1>
        <p>生成时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>测试类型: {self.test_type}</p>
    </div>

    <div class='summary'>
        <h2>📊 测试摘要</h2>
        <table>
            <tr><th>项目</th><th>数值</th></tr>
            <tr><td>总执行时间</td><td>{self.results['summary']['total_execution_time']:.2f}秒</td></tr>
            <tr><td>测试套件总数</td><td>{self.results['summary']['total_test_suites']}</td></tr>
            <tr><td>通过套件数</td><td class='passed'>{self.results['summary']['passed_suites']}</td></tr>
            <tr><td>失败套件数</td><td class='failed'>{self.results['summary']['failed_suites']}</td></tr>
            <tr><td>成功率</td><td>{self.results['summary']['success_rate']:.1f}%</td></tr>
        </table>
    </div>
"""

        # 添加各测试类型的结果
        for test_type, result in self.results.items():
            if test_type == 'summary':
                continue

            status_class = 'passed' if result.get('status') == 'passed' else 'failed'

            html_content += f"""
    <div class='test-section'>
        <h3 class='{status_class}'>🧪 {test_type.replace('_', ' ').title()}</h3>
        <p><strong>状态:</strong> <span class='{status_class}'>{result.get('status', 'unknown')}</span></p>
        <p><strong>执行时间:</strong> {result.get('execution_time', 0):.2f}秒</p>
        <p><strong>返回码:</strong> {result.get('return_code', 'N/A')}</p>

        {f'<pre class='pre'>{result.get('stdout', '')}</pre>' if result.get('stdout') else ''}
        {f'<pre class='pre' style='color: red;'>{result.get('stderr', '')}</pre>' if result.get('stderr') else ''}
    </div>
"""

        html_content += """
</body>
</html>
"""

        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

    def _generate_markdown_report(self) -> None:
        """生成Markdown格式的测试报告"""
        md_file = self.report_dir / 'test_report.md'

        md_content = f"""# 🚀 Athena AI平台测试报告

**生成时间**: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}
**测试类型**: {self.test_type}

## 📊 测试摘要

| 项目 | 数值 |
|------|------|
| 总执行时间 | {self.results['summary']['total_execution_time']:.2f}秒 |
| 测试套件总数 | {self.results['summary']['total_test_suites']} |
| 通过套件数 | {self.results['summary']['passed_suites']} |
| 失败套件数 | {self.results['summary']['failed_suites']} |
| 成功率 | {self.results['summary']['success_rate']:.1f}% |

## 🧪 详细测试结果

"""

        # 添加各测试类型的结果
        for test_type, result in self.results.items():
            if test_type == 'summary':
                continue

            status_emoji = '✅' if result.get('status') == 'passed' else '❌'

            md_content += f"""
### {status_emoji} {test_type.replace('_', ' ').title()}

- **状态**: {result.get('status', 'unknown')}
- **执行时间**: {result.get('execution_time', 0):.2f}秒
- **返回码**: {result.get('return_code', 'N/A')}

"""

            if result.get('stdout'):
                md_content += f"""
**输出**:
```
{result.get('stdout', '')}
```

"""

            if result.get('stderr'):
                md_content += f"""
**错误**:
```
{result.get('stderr', '')}
```

"""

        md_content += f"""
## 📁 报告文件

- JSON报告: `test_report.json`
- HTML报告: `test_report.html`
- 覆盖率报告: `htmlcov/` (如果启用)
- 性能基准: `benchmark.json` (如果运行性能测试)

## 🔗 访问链接

- [HTML报告](test_report.html)
- [覆盖率报告](htmlcov/index.html) (如果启用)
"""

        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md_content)

    def _print_summary(self) -> None:
        """打印测试摘要"""
        summary = self.results['summary']

        logger.info(str("\n" + '='*60))
        logger.info('🎉 Athena AI平台测试执行完成')
        logger.info(str('='*60))
        logger.info(f"📊 测试摘要:")
        logger.info(f"   总执行时间: {summary['total_execution_time']:.2f}秒")
        logger.info(f"   测试套件总数: {summary['total_test_suites']}")
        logger.info(f"   通过套件数: {summary['passed_suites']} ✅")
        logger.info(f"   失败套件数: {summary['failed_suites']} ❌")
        logger.info(f"   成功率: {summary['success_rate']:.1f}%")
        logger.info(f"📁 报告目录: {summary['report_directory']}")
        logger.info(str('='*60))

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Athena AI平台自动化测试套件')
    parser.add_argument(
        '--type',
        choices=['all', 'unit', 'integration', 'e2e', 'performance', 'security'],
        default='all',
        help='测试类型 (默认: all)'
    )
    parser.add_argument(
        '--no-coverage',
        action='store_true',
        help='禁用代码覆盖率检查'
    )
    parser.add_argument(
        '--no-parallel',
        action='store_true',
        help='禁用并行测试'
    )

    args = parser.parse_args()

    # 创建测试运行器
    test_runner = TestRunner(
        test_type=args.type,
        coverage=not args.no_coverage,
        parallel=not args.no_parallel
    )

    try:
        # 运行测试
        results = test_runner.run_all_tests()

        # 根据结果设置退出码
        failed_suites = results['summary']['failed_suites']
        sys.exit(1 if failed_suites > 0 else 0)

    except KeyboardInterrupt:
        logger.warning('测试被用户中断')
        sys.exit(130)
    except Exception as e:
        logger.error(f"测试执行异常: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()