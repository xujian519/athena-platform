#!/usr/bin/env python3
"""
深度服务分析器
Deep Service Analyzer
极兔提升服务标准化率的分析工具
"""

import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, asdict
import subprocess

@dataclass
class ServiceMetrics:
    """服务度量指标"""
    name: str
    has_main: bool = False
    has_requirements: bool = False
    has_readme: bool = False
    has_docker: bool = False
    has_config: bool = False
    has_tests: bool = False
    has_env_example: bool = False
    has_health_check: bool = False
    has_logging: bool = False
    has_error_handling: bool = False
    has_metrics: bool = False
    has_documentation: bool = False
    is_microservice: bool = False
    uses_fastapi: bool = False
    has_async: bool = False
    has_type_hints: bool = False
    code_quality_score: float = 0.0
    overall_score: float = 0.0

class DeepServiceAnalyzer:
    """深度服务分析器"""

    def __init__(self, services_path: str = "/Users/xujian/Athena工作平台/services"):
        self.services_path = Path(services_path)
        self.results: Dict[str, ServiceMetrics] = {}
        self.optimization_plan: Dict[str, List[str]] = {}

    async def analyze_service(self, service_name: str) -> ServiceMetrics:
        """深度分析单个服务"""
        service_path = self.services_path / service_name
        metrics = ServiceMetrics(name=service_name)

        # 检查基础文件
        metrics.has_main = self._check_main_file(service_path)
        metrics.has_requirements = self._check_requirements_file(service_path)
        metrics.has_readme = self._check_readme_file(service_path)
        metrics.has_docker = self._check_docker_file(service_path)
        metrics.has_config = self._check_config_files(service_path)
        metrics.has_tests = self._check_test_files(service_path)
        metrics.has_env_example = self._check_env_example(service_path)

        # 深度代码分析
        if metrics.has_main:
            code_analysis = await self._analyze_code(service_path)
            metrics.has_health_check = code_analysis.get('health_check', False)
            metrics.has_logging = code_analysis.get('logging', False)
            metrics.has_error_handling = code_analysis.get('error_handling', False)
            metrics.has_metrics = code_analysis.get('metrics', False)
            metrics.is_microservice = code_analysis.get('microservice', False)
            metrics.uses_fastapi = code_analysis.get('fastapi', False)
            metrics.has_async = code_analysis.get('async', False)
            metrics.has_type_hints = code_analysis.get('type_hints', False)
            metrics.has_documentation = code_analysis.get('documentation', False)

            # 代码质量评分
            metrics.code_quality_score = self._calculate_code_quality(service_path)

        # 计算总体评分
        metrics.overall_score = self._calculate_overall_score(metrics)

        return metrics

    def _check_main_file(self, service_path: Path) -> bool:
        """检查主入口文件"""
        main_files = ['main.py', 'app.py', 'server.py', 'index.js', 'app.js']
        for file in main_files:
            if (service_path / file).exists():
                return True
        return False

    def _check_requirements_file(self, service_path: Path) -> bool:
        """检查依赖文件"""
        req_files = ['requirements.txt', 'package.json', 'Pipfile', 'pyproject.toml']
        for file in req_files:
            if (service_path / file).exists():
                return True
        return False

    def _check_readme_file(self, service_path: Path) -> bool:
        """检查文档文件"""
        readme_files = ['README.md', 'README.rst', 'README.txt', 'DOCS.md']
        for file in readme_files:
            if (service_path / file).exists():
                return True
        return False

    def _check_docker_file(self, service_path: Path) -> bool:
        """检查Docker支持"""
        docker_files = ['Dockerfile', 'docker-compose.yml', 'Dockerfile.dev', '.dockerignore']
        for file in docker_files:
            if (service_path / file).exists():
                return True
        return False

    def _check_config_files(self, service_path: Path) -> bool:
        """检查配置文件"""
        config_patterns = [
            '.env*', 'config/', 'settings/', '*.yaml', '*.yml',
            '*.toml', '*.ini', '*.conf'
        ]

        for pattern in config_patterns:
            if list(service_path.glob(pattern)):
                return True

        # 检查代码中的配置类
        py_files = list(service_path.glob('**/*.py'))
        for py_file in py_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'class Config' in content or 'Settings' in content:
                        return True
            except:
                pass
        return False

    def _check_test_files(self, service_path: Path) -> bool:
        """检查测试文件"""
        test_patterns = [
            'test_*.py', '*_test.py', 'tests/', 'test/',
            'conftest.py', 'pytest.ini', 'tox.ini'
        ]

        for pattern in test_patterns:
            if list(service_path.glob(pattern)):
                return True
        return False

    def _check_env_example(self, service_path: Path) -> bool:
        """检查环境变量示例"""
        env_files = ['.env.example', '.env.sample', '.env.template', 'env.example']
        for file in env_files:
            if (service_path / file).exists():
                return True
        return False

    async def _analyze_code(self, service_path: Path) -> Dict[str, bool]:
        """深度代码分析"""
        analysis = {
            'health_check': False,
            'logging': False,
            'error_handling': False,
            'metrics': False,
            'microservice': False,
            'fastapi': False,
            'async': False,
            'type_hints': False,
            'documentation': False
        }

        # 获取所有Python文件
        py_files = list(service_path.glob('**/*.py'))

        for py_file in py_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                    # FastAPI检查
                    if 'from fastapi' in content or 'import fastapi' in content:
                        analysis['fastapi'] = True
                        analysis['microservice'] = True

                    # 健康检查
                    if '/health' in content or 'health_check' in content:
                        analysis['health_check'] = True

                    # 日志系统
                    if 'import logging' in content or 'logger.' in content:
                        analysis['logging'] = True

                    # 错误处理
                    if 'try:' in content and 'except' in content:
                        analysis['error_handling'] = True

                    # 指标收集
                    if 'prometheus' in content or 'metrics' in content:
                        analysis['metrics'] = True

                    # 异步编程
                    if 'async def' in content or 'await' in content:
                        analysis['async'] = True

                    # 类型提示
                    if ':' in content and 'def ' in content:
                        analysis['type_hints'] = True

                    # 文档字符串
                    if '"""' in content or "'''" in content:
                        analysis['documentation'] = True

            except Exception as e:
                print(f"Error analyzing {py_file}: {e}")

        return analysis

    def _calculate_code_quality(self, service_path: Path) -> float:
        """计算代码质量评分"""
        score = 0.0
        max_score = 10.0

        # 使用Python质量检查工具
        try:
            # flake8检查
            result = subprocess.run(
                ['flake8', '--format=json', str(service_path)],
                capture_output=True,
                text=True
            )
            # 基于错误数量评分
            errors = len(result.stdout.split('\n')) if result.stdout else 0
            score += max(0, 3 - errors * 0.1)

            # mypy类型检查
            result = subprocess.run(
                ['mypy', str(service_path)],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                score += 2

            # pytest测试覆盖率
            if (service_path / 'tests').exists():
                score += 2

            # 代码复杂度
            # 这里可以集成radon或mccabe
            score += 1

            # 文档覆盖率
            score += 1

            # 安全性
            # 这里可以集成bandit
            score += 1

        except Exception as e:
            print(f"Code quality check error: {e}")
            score = 5.0  # 默认中等分数

        return min(score, max_score)

    def _calculate_overall_score(self, metrics: ServiceMetrics) -> float:
        """计算总体标准化评分"""
        weights = {
            'has_main': 15,           # 主入口文件
            'has_requirements': 10,    # 依赖管理
            'has_readme': 10,         # 文档
            'has_docker': 10,         # 容器化
            'has_config': 8,          # 配置管理
            'has_tests': 10,          # 测试
            'has_env_example': 5,     # 环境变量
            'has_health_check': 8,    # 健康检查
            'has_logging': 5,         # 日志系统
            'has_error_handling': 5,  # 错误处理
            'has_metrics': 5,         # 指标收集
            'code_quality_score': 9   # 代码质量
        }

        total_score = 0.0
        total_weight = 0

        for attr, weight in weights.items():
            value = getattr(metrics, attr)
            if isinstance(value, bool):
                total_score += weight if value else 0
            elif isinstance(value, float):
                total_score += value * weight
            total_weight += weight

        return (total_score / total_weight * 100) if total_weight > 0 else 0

    async def analyze_all_services(self) -> Dict[str, ServiceMetrics]:
        """分析所有服务"""
        services = [d for d in self.services_path.iterdir()
                   if d.is_dir() and not d.name.startswith('.')
                   and d.name not in ['archives', 'config', 'docs', 'scripts']]

        tasks = [self.analyze_service(service.name) for service in services]
        results = await asyncio.gather(*tasks)

        for result in results:
            self.results[result.name] = result

        return self.results

    def generate_optimization_plan(self):
        """生成优化计划"""
        for name, metrics in self.results.items():
            improvements = []

            if not metrics.has_main:
                improvements.append("创建主入口文件 (main.py)")
            if not metrics.has_requirements:
                improvements.append("创建依赖管理文件 (requirements.txt)")
            if not metrics.has_readme:
                improvements.append("创建服务文档 (README.md)")
            if not metrics.has_docker:
                improvements.append("添加Docker支持 (Dockerfile)")
            if not metrics.has_config:
                improvements.append("实现配置管理系统")
            if not metrics.has_tests:
                improvements.append("添加单元测试")
            if not metrics.has_env_example:
                improvements.append("创建环境变量示例 (.env.example)")
            if not metrics.has_health_check:
                improvements.append("实现健康检查端点")
            if not metrics.has_logging:
                improvements.append("集成日志系统")
            if not metrics.has_error_handling:
                improvements.append("完善错误处理机制")
            if not metrics.has_metrics:
                improvements.append("添加监控指标")
            if not metrics.uses_fastapi and metrics.has_main:
                improvements.append("迁移到FastAPI框架")
            if not metrics.has_async and metrics.uses_fastapi:
                improvements.append("实现异步编程")
            if not metrics.has_type_hints:
                improvements.append("添加类型提示")
            if metrics.code_quality_score < 7:
                improvements.append("提升代码质量")

            self.optimization_plan[name] = improvements

    def generate_report(self) -> str:
        """生成分析报告"""
        report = []
        report.append("# Athena平台深度服务分析报告\n")
        report.append(f"**分析时间**: {datetime.now().isoformat()}\n")

        # 总体统计
        total_services = len(self.results)
        high_quality = sum(1 for m in self.results.values() if m.overall_score >= 90)
        medium_quality = sum(1 for m in self.results.values() if 70 <= m.overall_score < 90)
        low_quality = sum(1 for m in self.results.values() if m.overall_score < 70)

        report.append("## 📊 总体统计\n")
        report.append(f"- **服务总数**: {total_services}")
        report.append(f"- **高质量服务 (≥90分)**: {high_quality} ({high_quality/total_services*100:.1f}%)")
        report.append(f"- **中等质量服务 (70-89分)**: {medium_quality} ({medium_quality/total_services*100:.1f}%)")
        report.append(f"- **低质量服务 (<70分)**: {low_quality} ({low_quality/total_services*100:.1f}%)")
        report.append(f"- **平均标准化率**: {sum(m.overall_score for m in self.results.values())/total_services:.1f}%\n")

        # 服务详情
        report.append("## 📋 服务详情\n")
        report.append("| 服务名称 | 评分 | 主入口 | 依赖 | 文档 | Docker | 测试 | 健康检查 |")
        report.append("|---------|------|--------|------|------|--------|------|----------|")

        sorted_services = sorted(self.results.items(), key=lambda x: x[1].overall_score, reverse=True)

        for name, metrics in sorted_services:
            report.append(f"| {name} | {metrics.overall_score:.1f}% | "
                         f"{'✅' if metrics.has_main else '❌'} | "
                         f"{'✅' if metrics.has_requirements else '❌'} | "
                         f"{'✅' if metrics.has_readme else '❌'} | "
                         f"{'✅' if metrics.has_docker else '❌'} | "
                         f"{'✅' if metrics.has_tests else '❌'} | "
                         f"{'✅' if metrics.has_health_check else '❌'} |")

        # 优化计划
        report.append("\n## 🚀 优化计划\n")

        # 按优先级分组
        urgent_services = [(n, m) for n, m in self.results.items() if m.overall_score < 60]
        important_services = [(n, m) for n, m in self.results.items() if 60 <= m.overall_score < 80]

        if urgent_services:
            report.append("\n### 🔴 紧急优化 (评分 < 60)")
            for name, metrics in urgent_services:
                report.append(f"\n#### {name} (当前评分: {metrics.overall_score:.1f}%)")
                for improvement in self.optimization_plan.get(name, []):
                    report.append(f"- [ ] {improvement}")

        if important_services:
            report.append("\n### 🟡 重要优化 (评分 60-80)")
            for name, metrics in important_services:
                report.append(f"\n#### {name} (当前评分: {metrics.overall_score:.1f}%)")
                for improvement in self.optimization_plan.get(name, []):
                    report.append(f"- [ ] {improvement}")

        # 提升策略
        report.append("\n## 📈 极兔提升策略\n")
        report.append("\n### 1. 快速提升 (1周内)")
        report.append("- 为所有服务创建主入口文件和基础文档")
        report.append("- 添加环境变量示例和基础配置")
        report.append("- 实现统一的健康检查端点")
        report.append("- 添加基础日志系统\n")

        report.append("### 2. 深度优化 (2周内)")
        report.append("- 完善测试覆盖率到80%以上")
        report.append("- 实现Docker容器化")
        report.append("- 添加监控和指标收集")
        report.append("- 统一错误处理机制\n")

        report.append("### 3. 极致优化 (1个月内)")
        report.append("- 实现异步编程和性能优化")
        report.append("- 完善文档和API规范")
        report.append("- 实现服务间通信标准")
        report.append("- 建立配置中心和统一管理\n")

        return '\n'.join(report)

async def main():
    """主函数"""
    analyzer = DeepServiceAnalyzer()

    print("🔍 开始深度分析所有服务...")
    await analyzer.analyze_all_services()

    print("📋 生成优化计划...")
    analyzer.generate_optimization_plan()

    print("📊 生成分析报告...")
    report = analyzer.generate_report()

    # 保存报告
    report_path = Path("/Users/xujian/Athena工作平台/services/DEEP_ANALYSIS_REPORT.md")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"✅ 分析完成！报告已保存到: {report_path}")

    # 输出关键信息
    total_services = len(analyzer.results)
    avg_score = sum(m.overall_score for m in analyzer.results.values()) / total_services
    print(f"\n📈 当前平均标准化率: {avg_score:.1f}%")
    print(f"🎯 目标标准化率: 95%+")
    print(f"📊 需要优化的服务: {sum(1 for m in analyzer.results.values() if m.overall_score < 90)}")

if __name__ == "__main__":
    asyncio.run(main())