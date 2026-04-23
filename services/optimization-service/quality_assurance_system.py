#!/usr/bin/env python3
"""
Athena平台质量保证体系
提供代码质量检测、性能测试、安全审计、自动化测试等功能
"""

import ast
import asyncio
import json
import pstats
import re
import subprocess
import sys
import time
import tracemalloc
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import bandit
import c_profile

# 代码质量检测
import flake8

# 性能测试
import psutil

# 安全审计
from coverage import Coverage

from core.logging_config import setup_logging

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

class QualityMetricType(Enum):
    """质量指标类型"""
    CODE_COMPLEXITY = 'code_complexity'
    CODE_COVERAGE = 'code_coverage'
    CODE_STYLE = 'code_style'
    SECURITY_VULNERABILITY = 'security_vulnerability'
    PERFORMANCE_METRIC = 'performance_metric'
    RELIABILITY_METRIC = 'reliability_metric'
    MAINTAINABILITY_INDEX = 'maintainability_index'
    TEST_COVERAGE = 'test_coverage'

class SeverityLevel(Enum):
    """严重程度"""
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'

class QualityStandard(Enum):
    """质量标准"""
    EXCELLENT = 'excellent'      # 90-100
    GOOD = 'good'               # 80-89
    ACCEPTABLE = 'acceptable'   # 70-79
    NEEDS_IMPROVEMENT = 'needs_improvement'  # 60-69
    POOR = 'poor'               # 0-59

@dataclass
class QualityIssue:
    """质量问题"""
    issue_id: str
    metric_type: QualityMetricType
    severity: SeverityLevel
    title: str
    description: str
    file_path: str
    line_number: int | None = None
    column_number: int | None = None
    rule_id: str | None = None
    suggestion: str | None = None
    auto_fixable: bool = False
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class QualityReport:
    """质量报告"""
    report_id: str
    project_path: str
    timestamp: datetime = field(default_factory=datetime.now)
    overall_score: float = 0.0
    quality_standard: QualityStandard = QualityStandard.POOR
    metrics: dict[str, Any] = field(default_factory=dict)
    issues: list[QualityIssue] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)

@dataclass
class TestResult:
    """测试结果"""
    test_id: str
    test_name: str
    test_type: str
    status: str  # passed, failed, skipped, error
    duration: float
    error_message: str | None = None
    assertions: int = 0
    coverage_data: dict[str, Any] = field(default_factory=dict)

class CodeQualityAnalyzer:
    """代码质量分析器"""

    def __init__(self):
        """初始化代码质量分析器"""
        self.supported_extensions = {'.py'}
        self.quality_rules = self._initialize_quality_rules()

    def _initialize_quality_rules(self) -> dict[str, dict]:
        """初始化质量规则"""
        return {
            'complexity': {
                'max_cyclomatic_complexity': 10,
                'max_cognitive_complexity': 15,
                'max_line_length': 88,
                'max_function_lines': 50
            },
            'style': {
                'indent_size': 4,
                'quote_style': 'double',
                'import_order': 'standard'
            },
            'security': {
                'disable_hardcoded_passwords': True,
                'disable_sql_injection': True,
                'disable_insecure_deserialization': True
            },
            'maintainability': {
                'min_maintainability_index': 70,
                'max_duplication': 3
            }
        }

    async def analyze_project(self, project_path: str) -> QualityReport:
        """分析项目代码质量"""
        logger.info(f"开始分析项目代码质量: {project_path}")

        report = QualityReport(
            report_id=str(uuid.uuid4()),
            project_path=project_path
        )

        try:
            # 1. 代码复杂度分析
            complexity_metrics = await self._analyze_complexity(project_path)
            report.metrics['complexity'] = complexity_metrics

            # 2. 代码风格检查
            style_metrics = await self._check_code_style(project_path)
            report.metrics['style'] = style_metrics

            # 3. 安全漏洞扫描
            security_metrics = await self._scan_security_vulnerabilities(project_path)
            report.metrics['security'] = security_metrics

            # 4. 代码覆盖率分析
            coverage_metrics = await self._analyze_code_coverage(project_path)
            report.metrics['coverage'] = coverage_metrics

            # 5. 可维护性分析
            maintainability_metrics = await self._analyze_maintainability(project_path)
            report.metrics['maintainability'] = maintainability_metrics

            # 6. 收集所有问题
            report.issues = await self._collect_all_issues(project_path)

            # 7. 计算总体评分
            report.overall_score, report.quality_standard = self._calculate_overall_score(report.metrics)

            # 8. 生成摘要和建议
            report.summary = self._generate_summary(report)
            report.recommendations = self._generate_recommendations(report)

            logger.info(f"代码质量分析完成，总体评分: {report.overall_score:.1f}")

        except Exception as e:
            logger.error(f"代码质量分析失败: {e}")
            report.issues.append(QualityIssue(
                issue_id=str(uuid.uuid4()),
                metric_type=QualityMetricType.CODE_QUALITY,
                severity=SeverityLevel.HIGH,
                title='分析错误',
                description=f"代码质量分析过程中出现错误: {str(e)}",
                file_path=project_path
            ))

        return report

    async def _analyze_complexity(self, project_path: str) -> dict[str, Any]:
        """分析代码复杂度"""
        complexity_data = {
            'files_analyzed': 0,
            'total_lines': 0,
            'total_functions': 0,
            'max_cyclomatic_complexity': 0,
            'avg_cyclomatic_complexity': 0,
            'complex_functions': [],
            'long_functions': []
        }

        try:
            python_files = self._get_python_files(project_path)
            complexity_data['files_analyzed'] = len(python_files)

            total_complexity = 0
            complexity_scores = []

            for file_path in python_files:
                try:
                    with open(file_path, encoding='utf-8') as f:
                        content = f.read()

                    # 计算行数
                    lines = content.split('\n')
                    complexity_data['total_lines'] += len(lines)

                    # 解析AST
                    try:
                        tree = ast.parse(content)

                        # 分析函数复杂度
                        for node in ast.walk(tree):
                            if isinstance(node, ast.FunctionDef):
                                complexity_data['total_functions'] += 1

                                # 计算圈复杂度（简化版）
                                cyclomatic_complexity = self._calculate_cyclomatic_complexity(node)
                                total_complexity += cyclomatic_complexity
                                complexity_scores.append(cyclomatic_complexity)

                                # 检查是否超过阈值
                                if cyclomatic_complexity > self.quality_rules['complexity']['max_cyclomatic_complexity']:
                                    complexity_data['complex_functions'].append({
                                        'file': str(file_path.relative_to(project_path)),
                                        'function': node.name,
                                        'line': node.lineno,
                                        'complexity': cyclomatic_complexity
                                    })

                                # 检查函数长度
                                function_lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else len(lines[node.lineno-1:])
                                if function_lines > self.quality_rules['complexity']['max_function_lines']:
                                    complexity_data['long_functions'].append({
                                        'file': str(file_path.relative_to(project_path)),
                                        'function': node.name,
                                        'line': node.lineno,
                                        'lines': function_lines
                                    })

                    except SyntaxError as e:
                        logger.warning(f"文件 {file_path} 语法错误，跳过分析: {e}")
                        continue

                except Exception as e:
                    logger.error(f"分析文件 {file_path} 失败: {e}")
                    continue

            # 计算平均复杂度
            if complexity_scores:
                complexity_data['avg_cyclomatic_complexity'] = sum(complexity_scores) / len(complexity_scores)
                complexity_data['max_cyclomatic_complexity'] = max(complexity_scores)

        except Exception as e:
            logger.error(f"复杂度分析失败: {e}")

        return complexity_data

    def _calculate_cyclomatic_complexity(self, node: ast.FunctionDef) -> int:
        """计算圈复杂度"""
        complexity = 1  # 基础复杂度

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.With, ast.AsyncWith):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        return complexity

    async def _check_code_style(self, project_path: str) -> dict[str, Any]:
        """检查代码风格"""
        style_data = {
            'files_checked': 0,
            'total_issues': 0,
            'issues_by_type': {},
            'violations': []
        }

        try:
            # 使用flake8检查代码风格
            python_files = self._get_python_files(project_path)
            style_data['files_checked'] = len(python_files)

            # 配置flake8
            style_guide = flake8.get_style_guide(
                max_line_length=self.quality_rules['style']['max_line_length'],
                ignore=['E501']  # 忽略行长度检查，我们自己处理
            )

            total_violations = 0
            violations_by_type = {}

            for file_path in python_files:
                try:
                    report = style_guide.input_file(str(file_path))

                    if report:
                        for error in report.get_statistics('E'):
                            error_code = error[0]
                            error_count = error[1]

                            total_violations += error_count
                            violations_by_type[error_code] = violations_by_type.get(error_code, 0) + error_count

                            # 添加具体违规信息
                            style_data['violations'].extend([
                                {
                                    'file': str(file_path.relative_to(project_path)),
                                    'code': error_code,
                                    'message': f"{error_code}: {error[2] if len(error) > 2 else 'Style violation'}",
                                    'line': violation[1] if len(violation) > 1 else 0
                                }
                                for violation in error[3] if isinstance(error[3], list)
                            ])

                except Exception as e:
                    logger.error(f"检查文件 {file_path} 代码风格失败: {e}")
                    continue

            style_data['total_issues'] = total_violations
            style_data['issues_by_type'] = violations_by_type

        except Exception as e:
            logger.error(f"代码风格检查失败: {e}")

        return style_data

    async def _scan_security_vulnerabilities(self, project_path: str) -> dict[str, Any]:
        """扫描安全漏洞"""
        security_data = {
            'files_scanned': 0,
            'total_vulnerabilities': 0,
            'vulnerabilities_by_severity': {
                'low': 0,
                'medium': 0,
                'high': 0,
                'critical': 0
            },
            'vulnerabilities': []
        }

        try:
            # 使用bandit进行安全扫描
            python_files = self._get_python_files(project_path)
            security_data['files_scanned'] = len(python_files)

            for file_path in python_files:
                try:
                    # 配置bandit
                    bandit_config = {
                        'exclude_dirs': ['tests', 'test'],
                        'severity_level': 'low'
                    }

                    # 运行bandit扫描
                    result = bandit.core.manager.Manager(bandit_config, str(file_path))
                    result.run_tests()

                    # 处理扫描结果
                    for issue in result.get_issues():
                        severity_map = {
                            'LOW': 'low',
                            'MEDIUM': 'medium',
                            'HIGH': 'high'
                        }

                        severity = severity_map.get(issue.severity, 'low')

                        security_data['vulnerabilities_by_severity'][severity] += 1
                        security_data['total_vulnerabilities'] += 1

                        security_data['vulnerabilities'].append({
                            'file': str(file_path.relative_to(project_path)),
                            'line': issue.lineno,
                            'test_id': issue.test_id,
                            'severity': severity,
                            'text': issue.text,
                            'confidence': issue.confidence
                        })

                except Exception as e:
                    logger.error(f"扫描文件 {file_path} 安全漏洞失败: {e}")
                    continue

        except Exception as e:
            logger.error(f"安全漏洞扫描失败: {e}")

        return security_data

    async def _analyze_code_coverage(self, project_path: str) -> dict[str, Any]:
        """分析代码覆盖率"""
        coverage_data = {
            'files_covered': 0,
            'total_lines': 0,
            'covered_lines': 0,
            'coverage_percentage': 0.0,
            'uncovered_files': []
        }

        try:
            # 查找测试文件
            test_files = self._get_test_files(project_path)

            if not test_files:
                logger.warning(f"在 {project_path} 中未找到测试文件")
                return coverage_data

            # 运行覆盖率测试
            cov = Coverage()
            cov.start()

            try:
                # 运行测试
                for test_file in test_files:
                    try:
                        # 使用subprocess运行测试
                        result = subprocess.run(
                            [sys.executable, str(test_file)],
                            capture_output=True,
                            text=True,
                            timeout=30
                        )

                        if result.returncode != 0:
                            logger.warning(f"测试文件 {test_file} 执行失败: {result.stderr}")

                    except subprocess.TimeoutExpired:
                        logger.warning(f"测试文件 {test_file} 执行超时")
                    except Exception as e:
                        logger.error(f"执行测试文件 {test_file} 失败: {e}")

            finally:
                cov.stop()
                cov.save()

            # 生成覆盖率报告
            coverage_data['files_covered'] = len(cov.get_data().measured_files())

            total_lines = 0
            covered_lines = 0

            # 获取所有被测量的Python文件
            python_files = cov.get_data().measured_files()
            for file_path in python_files:
                try:
                    analysis = cov._analyze(file_path)
                    file_total = analysis.statements
                    file_covered = analysis.numbers.covered

                    total_lines += file_total
                    covered_lines += file_covered

                    if file_total == 0:
                        coverage_data['uncovered_files'].append(str(file_path.relative_to(project_path)))

                except Exception:
                    coverage_data['uncovered_files'].append(str(file_path.relative_to(project_path)))

            coverage_data['total_lines'] = total_lines
            coverage_data['covered_lines'] = covered_lines

            if total_lines > 0:
                coverage_data['coverage_percentage'] = (covered_lines / total_lines) * 100

        except Exception as e:
            logger.error(f"代码覆盖率分析失败: {e}")

        return coverage_data

    async def _analyze_maintainability(self, project_path: str) -> dict[str, Any]:
        """分析可维护性"""
        maintainability_data = {
            'files_analyzed': 0,
            'avg_maintainability_index': 0.0,
            'maintainability_scores': [],
            'duplication_percentage': 0.0,
            'technical_debt': 0
        }

        try:
            python_files = self._get_python_files(project_path)
            maintainability_data['files_analyzed'] = len(python_files)

            maintainability_scores = []

            for file_path in python_files:
                try:
                    # 简化的可维护性指数计算
                    with open(file_path, encoding='utf-8') as f:
                        content = f.read()

                    # 基础指标
                    lines_count = len(content.split('\n'))
                    comment_lines = len([line for line in content.split('\n') if line.strip().startswith('#')])
                    code_lines = lines_count - comment_lines

                    # 函数数量
                    tree = ast.parse(content)
                    function_count = len([node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)])

                    # 计算简化版可维护性指数
                    if function_count > 0:
                        avg_function_size = code_lines / function_count
                        comment_ratio = comment_lines / lines_count if lines_count > 0 else 0

                        # 可维护性指数 (0-100)
                        maintainability_index = max(0, 100 - (avg_function_size * 2) - (20 * (1 - comment_ratio)))
                    else:
                        maintainability_index = 80  # 默认值

                    maintainability_scores.append(maintainability_index)

                    if maintainability_index < self.quality_rules['maintainability']['min_maintainability_index']:
                        maintainability_data['technical_debt'] += 1

                except Exception as e:
                    logger.error(f"分析文件 {file_path} 可维护性失败: {e}")
                    continue

            if maintainability_scores:
                maintainability_data['avg_maintainability_index'] = sum(maintainability_scores) / len(maintainability_scores)
                maintainability_data['maintainability_scores'] = maintainability_scores

        except Exception as e:
            logger.error(f"可维护性分析失败: {e}")

        return maintainability_data

    async def _collect_all_issues(self, project_path: str) -> list[QualityIssue]:
        """收集所有质量问题"""
        issues = []

        try:
            python_files = self._get_python_files(project_path)

            for file_path in python_files:
                try:
                    with open(file_path, encoding='utf-8') as f:
                        content = f.read()

                    # 检查硬编码密码
                    if self._check_hardcoded_passwords(content):
                        issues.append(QualityIssue(
                            issue_id=str(uuid.uuid4()),
                            metric_type=QualityMetricType.SECURITY_VULNERABILITY,
                            severity=SeverityLevel.HIGH,
                            title='硬编码密码',
                            description='代码中包含硬编码密码，存在安全风险',
                            file_path=str(file_path.relative_to(project_path)),
                            suggestion='使用环境变量或配置文件存储敏感信息',
                            auto_fixable=False
                        ))

                    # 检查SQL注入风险
                    if self._check_sql_injection_risk(content):
                        issues.append(QualityIssue(
                            issue_id=str(uuid.uuid4()),
                            metric_type=QualityMetricType.SECURITY_VULNERABILITY,
                            severity=SeverityLevel.CRITICAL,
                            title='SQL注入风险',
                            description='代码中存在SQL注入风险',
                            file_path=str(file_path.relative_to(project_path)),
                            suggestion='使用参数化查询或ORM框架',
                            auto_fixable=False
                        ))

                    # 检查长行
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if len(line) > self.quality_rules['complexity']['max_line_length']:
                            issues.append(QualityIssue(
                                issue_id=str(uuid.uuid4()),
                                metric_type=QualityMetricType.CODE_STYLE,
                                severity=SeverityLevel.LOW,
                                title='代码行过长',
                                description=f"第{i+1}行超过{self.quality_rules['complexity']['max_line_length']}个字符",
                                file_path=str(file_path.relative_to(project_path)),
                                line_number=i+1,
                                suggestion='将长行分解为多行或使用更短的变量名',
                                auto_fixable=True
                            ))

                except Exception as e:
                    logger.error(f"收集文件 {file_path} 问题失败: {e}")
                    continue

        except Exception as e:
            logger.error(f"收集质量问题失败: {e}")

        return issues

    def _check_hardcoded_passwords(self, content: str) -> bool:
        """检查硬编码密码"""
        password_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'passwd\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'key\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']'
        ]

        for pattern in password_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True

        return False

    def _check_sql_injection_risk(self, content: str) -> bool:
        """检查SQL注入风险"""
        sql_patterns = [
            r'execute\s*\(\s*["\'][^"\']*%[^"\']*["\']',
            r'execute\s*\(\s*["\'][^"\']*\+[^"\']*["\']',
            r'format\s*\(\s*["\'][^"\']*SELECT[^"\']*["\']',
            r'\.format\s*\([^)]*SELECT[^)]*\)',
        ]

        for pattern in sql_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True

        return False

    def _calculate_overall_score(self, metrics: dict[str, Any]) -> tuple[float, QualityStandard]:
        """计算总体评分"""
        score = 0.0
        weights = {
            'complexity': 0.25,
            'style': 0.15,
            'security': 0.30,
            'coverage': 0.15,
            'maintainability': 0.15
        }

        # 复杂度评分 (0-100)
        complexity_score = 100.0
        if metrics.get('complexity', {}).get('avg_cyclomatic_complexity', 0) > 10:
            complexity_score = max(0, 100 - (metrics['complexity']['avg_cyclomatic_complexity'] - 10) * 5)

        # 风格评分 (0-100)
        style_score = max(0, 100 - min(100, metrics.get('style', {}).get('total_issues', 0) * 2))

        # 安全评分 (0-100)
        security_score = 100.0
        total_vulns = metrics.get('security', {}).get('total_vulnerabilities', 0)
        if total_vulns > 0:
            critical_high = (metrics['security']['vulnerabilities_by_severity']['critical'] +
                           metrics['security']['vulnerabilities_by_severity']['high'])
            security_score = max(0, 100 - critical_high * 20 - (total_vulns - critical_high) * 10)

        # 覆盖率评分 (0-100)
        coverage_score = metrics.get('coverage', {}).get('coverage_percentage', 0)

        # 可维护性评分 (0-100)
        maintainability_score = metrics.get('maintainability', {}).get('avg_maintainability_index', 70)

        # 计算加权总分
        score = (
            complexity_score * weights['complexity'] +
            style_score * weights['style'] +
            security_score * weights['security'] +
            coverage_score * weights['coverage'] +
            maintainability_score * weights['maintainability']
        )

        # 确定质量标准
        if score >= 90:
            standard = QualityStandard.EXCELLENT
        elif score >= 80:
            standard = QualityStandard.GOOD
        elif score >= 70:
            standard = QualityStandard.ACCEPTABLE
        elif score >= 60:
            standard = QualityStandard.NEEDS_IMPROVEMENT
        else:
            standard = QualityStandard.POOR

        return score, standard

    def _generate_summary(self, report: QualityReport) -> dict[str, Any]:
        """生成质量摘要"""
        return {
            'files_analyzed': report.metrics.get('complexity', {}).get('files_analyzed', 0),
            'total_issues': len(report.issues),
            'issues_by_severity': self._count_issues_by_severity(report.issues),
            'critical_issues': len([i for i in report.issues if i.severity == SeverityLevel.CRITICAL]),
            'high_issues': len([i for i in report.issues if i.severity == SeverityLevel.HIGH]),
            'most_common_issues': self._get_most_common_issues(report.issues),
            'improvement_areas': self._identify_improvement_areas(report.metrics)
        }

    def _generate_recommendations(self, report: QualityReport) -> list[str]:
        """生成改进建议"""
        recommendations = []

        # 基于评分的建议
        if report.overall_score < 70:
            recommendations.append('整体代码质量需要改善，建议优先解决高严重性和关键性问题')

        # 基于指标的建议
        metrics = report.metrics

        if metrics.get('complexity', {}).get('avg_cyclomatic_complexity', 0) > 10:
            recommendations.append('代码复杂度过高，建议重构复杂函数，减少圈复杂度')

        if metrics.get('style', {}).get('total_issues', 0) > 50:
            recommendations.append('代码风格问题较多，建议使用自动化格式化工具（如black）')

        if metrics.get('security', {}).get('total_vulnerabilities', 0) > 0:
            recommendations.append('发现安全漏洞，建议立即修复关键和高严重性问题')

        if metrics.get('coverage', {}).get('coverage_percentage', 0) < 80:
            recommendations.append('测试覆盖率不足，建议增加单元测试和集成测试')

        if metrics.get('maintainability', {}).get('avg_maintainability_index', 0) < 70:
            recommendations.append('代码可维护性较低，建议改善代码结构和文档')

        return recommendations

    def _count_issues_by_severity(self, issues: list[QualityIssue]) -> dict[str, int]:
        """按严重程度统计问题"""
        counts = {
            'low': 0,
            'medium': 0,
            'high': 0,
            'critical': 0
        }

        for issue in issues:
            counts[issue.severity.value] += 1

        return counts

    def _get_most_common_issues(self, issues: list[QualityIssue]) -> list[dict[str, Any]:
        """获取最常见的问题"""
        issue_counts = {}

        for issue in issues:
            title = issue.title
            issue_counts[title] = issue_counts.get(title, 0) + 1

        # 按频率排序
        sorted_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)

        return [{'title': title, 'count': count} for title, count in sorted_issues[:5]

    def _identify_improvement_areas(self, metrics: dict[str, Any]) -> list[str]:
        """识别改进领域"""
        areas = []

        if metrics.get('complexity', {}).get('avg_cyclomatic_complexity', 0) > 10:
            areas.append('代码复杂度')

        if metrics.get('style', {}).get('total_issues', 0) > 20:
            areas.append('代码风格')

        if metrics.get('security', {}).get('total_vulnerabilities', 0) > 0:
            areas.append('安全性')

        if metrics.get('coverage', {}).get('coverage_percentage', 0) < 80:
            areas.append('测试覆盖率')

        if metrics.get('maintainability', {}).get('avg_maintainability_index', 0) < 70:
            areas.append('可维护性')

        return areas

    def _get_python_files(self, project_path: str) -> list[Path]:
        """获取Python文件列表"""
        python_files = []
        project_path = Path(project_path)

        for file_path in project_path.rglob('*.py'):
            # 跳过虚拟环境和缓存目录
            if any(part in str(file_path) for part in ['venv', '__pycache__', '.git', 'node_modules']):
                continue

            python_files.append(file_path)

        return python_files

    def _get_test_files(self, project_path: str) -> list[Path]:
        """获取测试文件列表"""
        test_files = []
        project_path = Path(project_path)

        test_patterns = ['test_*.py', '*_test.py', 'tests/*.py', 'test/*.py']

        for pattern in test_patterns:
            for file_path in project_path.glob(pattern):
                if file_path.is_file():
                    test_files.append(file_path)

        return test_files

class PerformanceTester:
    """性能测试器"""

    def __init__(self):
        """初始化性能测试器"""
        self.test_results = []

    async def run_performance_tests(self, project_path: str) -> dict[str, Any]:
        """运行性能测试"""
        logger.info(f"开始性能测试: {project_path}")

        test_results = {
            'memory_usage': await self._test_memory_usage(project_path),
            'cpu_performance': await self._test_cpu_performance(project_path),
            'response_time': await self._test_response_time(project_path),
            'load_testing': await self._test_load_performance(project_path),
            'profiling_data': await self._profile_code(project_path)
        }

        return test_results

    async def _test_memory_usage(self, project_path: str) -> dict[str, Any]:
        """测试内存使用"""
        # 启动内存追踪
        tracemalloc.start()

        try:
            # 模拟项目加载和执行
            python_files = list(Path(project_path).rglob('*.py'))

            initial_memory = tracemalloc.get_traced_memory()[0]

            # 加载和解析所有Python文件
            for file_path in python_files[:10]:  # 限制文件数量
                try:
                    with open(file_path, encoding='utf-8') as f:
                        content = f.read()

                    # 模拟代码执行
                    compile(content, str(file_path), 'exec')

                except Exception as e:
                    logger.warning(f"处理文件 {file_path} 时出错: {e}")

            current_memory, peak_memory = tracemalloc.get_traced_memory()

            memory_data = {
                'initial_memory_mb': initial_memory / 1024 / 1024,
                'current_memory_mb': current_memory / 1024 / 1024,
                'peak_memory_mb': peak_memory / 1024 / 1024,
                'memory_increase_mb': (current_memory - initial_memory) / 1024 / 1024,
                'files_processed': len(python_files[:10])
            }

        finally:
            tracemalloc.stop()

        return memory_data

    async def _test_cpu_performance(self, project_path: str) -> dict[str, Any]:
        """测试CPU性能"""
        import time

        # 记录开始时的CPU时间
        start_time = time.time()
        psutil.cpu_percent()

        try:
            # 模拟CPU密集型任务
            for i in range(100000):
                _ = i * i * i  # 计算密集型操作

            # 记录结束时的CPU时间
            end_time = time.time()
            end_cpu = psutil.cpu_percent()

            cpu_data = {
                'execution_time_seconds': end_time - start_time,
                'cpu_usage_percent': end_cpu,
                'operations_per_second': 100000 / (end_time - start_time)
            }

        except Exception as e:
            cpu_data = {'error': str(e)}

        return cpu_data

    async def _test_response_time(self, project_path: str) -> dict[str, Any]:
        """测试响应时间"""
        response_times = []

        try:
            # 测试文件读取响应时间
            python_files = list(Path(project_path).rglob('*.py'))

            for file_path in python_files[:20]:  # 测试前20个文件
                start_time = time.time()

                try:
                    with open(file_path, encoding='utf-8') as f:
                        f.read()

                    end_time = time.time()
                    response_time = (end_time - start_time) * 1000  # 转换为毫秒
                    response_times.append(response_time)

                except Exception as e:
                    logger.warning(f"读取文件 {file_path} 失败: {e}")

            if response_times:
                response_data = {
                    'avg_response_time_ms': sum(response_times) / len(response_times),
                    'min_response_time_ms': min(response_times),
                    'max_response_time_ms': max(response_times),
                    'files_tested': len(response_times),
                    'response_times': response_times
                }
            else:
                response_data = {'error': '无法测试响应时间'}

        except Exception as e:
            response_data = {'error': str(e)}

        return response_data

    async def _test_load_performance(self, project_path: str) -> dict[str, Any]:
        """测试负载性能"""
        import concurrent.futures

        def simulate_user_request():
            """模拟用户请求"""
            start_time = time.time()

            try:
                # 模拟文件操作
                python_files = list(Path(project_path).rglob('*.py'))

                if python_files:
                    file_path = python_files[0]
                    with open(file_path, encoding='utf-8') as f:
                        f.read()

                    # 模拟处理时间
                    time.sleep(0.01)

                end_time = time.time()
                return (end_time - start_time) * 1000  # 毫秒

            except Exception:
                return -1  # 错误标记

        try:
            # 模拟并发用户请求
            concurrent_users = 10
            requests_per_user = 5

            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
                futures = []

                for _ in range(concurrent_users):
                    for _ in range(requests_per_user):
                        future = executor.submit(simulate_user_request)
                        futures.append(future)

                # 等待所有请求完成
                results = [future.result() for future in concurrent.futures.as_completed(futures)]

                # 过滤掉错误结果
                valid_results = [r for r in results if r > 0]

                if valid_results:
                    load_data = {
                        'concurrent_users': concurrent_users,
                        'total_requests': len(futures),
                        'successful_requests': len(valid_results),
                        'avg_response_time_ms': sum(valid_results) / len(valid_results),
                        'min_response_time_ms': min(valid_results),
                        'max_response_time_ms': max(valid_results),
                        'requests_per_second': len(valid_results) / (sum(valid_results) / 1000)
                    }
                else:
                    load_data = {'error': '所有请求都失败了'}

        except Exception as e:
            load_data = {'error': str(e)}

        return load_data

    async def _profile_code(self, project_path: str) -> dict[str, Any]:
        """代码性能分析"""
        profiler = c_profile.Profile()

        try:
            python_files = list(Path(project_path).rglob('*.py'))

            if not python_files:
                return {'error': '没有找到Python文件'}

            # 选择一个中等大小的文件进行分析
            test_file = python_files[len(python_files) // 2]

            def profiled_function():
                """被分析的性能函数"""
                try:
                    with open(test_file, encoding='utf-8') as f:
                        content = f.read()

                    # 模拟一些处理
                    words = content.split()
                    word_count = {}

                    for word in words:
                        word_count[word] = word_count.get(word, 0) + 1

                    # 排序
                    sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)

                    return len(sorted_words)

                except Exception as e:
                    logger.error(f"分析文件 {test_file} 失败: {e}")
                    return 0

            # 运行性能分析
            profiler.enable()
            result = profiled_function()
            profiler.disable()

            # 获取统计信息
            stats = pstats.Stats(profiler)

            # 获取最重要的函数
            stats.sort_stats('cumulative')
            top_functions = []

            for func_info in stats.stats[:10]:
                func_name = func_info[0]
                if isinstance(func_name, tuple):
                    func_name = func_name[2]  # 获取函数名

                top_functions.append({
                    'function': func_name,
                    'calls': func_info[1],
                    'total_time': func_info[3],
                    'cumulative_time': func_info[4],
                    'per_call_time': func_info[3] / func_info[1] if func_info[1] > 0 else 0
                })

            profiling_data = {
                'file_analyzed': str(test_file.relative_to(project_path)),
                'total_functions': len(top_functions),
                'top_functions': top_functions,
                'execution_result': result
            }

        except Exception as e:
            profiling_data = {'error': str(e)}

        return profiling_data

class SecurityAuditor:
    """安全审计器"""

    def __init__(self):
        """初始化安全审计器"""
        self.security_checks = [
            'hardcoded_secrets',
            'insecure_dependencies',
            'weak_cryptography',
            'input_validation',
            'authentication_issues',
            'authorization_issues',
            'data_exposure',
            'insecure_communication'
        ]

    async def audit_security(self, project_path: str) -> dict[str, Any]:
        """执行安全审计"""
        logger.info(f"开始安全审计: {project_path}")

        audit_results = {
            'overall_security_score': 0.0,
            'security_issues': [],
            'vulnerabilities_by_category': {},
            'risk_assessment': {},
            'compliance_check': {},
            'recommendations': []
        }

        try:
            # 执行各项安全检查
            for check in self.security_checks:
                check_result = await self._run_security_check(check, project_path)
                audit_results['vulnerabilities_by_category'][check] = check_result

                if check_result.get('issues'):
                    audit_results['security_issues'].extend(check_result['issues'])

            # 计算安全评分
            audit_results['overall_security_score'] = self._calculate_security_score(audit_results['vulnerabilities_by_category'])

            # 风险评估
            audit_results['risk_assessment'] = self._assess_security_risk(audit_results['security_issues'])

            # 合规性检查
            audit_results['compliance_check'] = await self._check_compliance(project_path)

            # 生成安全建议
            audit_results['recommendations'] = self._generate_security_recommendations(audit_results)

        except Exception as e:
            logger.error(f"安全审计失败: {e}")
            audit_results['error'] = str(e)

        return audit_results

    async def _run_security_check(self, check_type: str, project_path: str) -> dict[str, Any]:
        """运行特定安全检查"""
        check_methods = {
            'hardcoded_secrets': self._check_hardcoded_secrets,
            'insecure_dependencies': self._check_insecure_dependencies,
            'weak_cryptography': self._check_weak_cryptography,
            'input_validation': self._check_input_validation,
            'authentication_issues': self._check_authentication_issues,
            'authorization_issues': self._check_authorization_issues,
            'data_exposure': self._check_data_exposure,
            'insecure_communication': self._check_insecure_communication
        }

        if check_type in check_methods:
            return await check_methods[check_type](project_path)
        else:
            return {'error': f"未知的安全检查类型: {check_type}"}

    async def _check_hardcoded_secrets(self, project_path: str) -> dict[str, Any]:
        """检查硬编码密钥"""
        secrets_patterns = [
            (r'password\s*=\s*["\'][^"\']{8,}["\']', "password"),
            (r'api[_-]?key\s*=\s*["\'][^"\']{16,}["\']', "api_key"),
            (r'secret[_-]?key\s*=\s*["\'][^"\']{16,}["\']', "secret_key"),
            (r'token\s*=\s*["\'][^"\']{20,}["\']', "token"),
            (r'private[_-]?key\s*=\s*["\'][-A-Za-z0-9+/]{32,}["\']', 'private_key'),
            (r'access[_-]?token\s*=\s*["\'][^"\']{20,}["\']', "access_token"),
            (r'auth[_-]?token\s*=\s*["\'][^"\']{20,}["\']', "auth_token")
        ]

        issues = []

        try:
            for file_path in Path(project_path).rglob('*.py'):
                try:
                    with open(file_path, encoding='utf-8') as f:
                        content = f.read()

                    line_number = 0
                    for line in content.split('\n'):
                        line_number += 1

                        for pattern, secret_type in secrets_patterns:
                            if re.search(pattern, line, re.IGNORECASE):
                                issues.append({
                                    'type': 'hardcoded_secret',
                                    'severity': 'high',
                                    'file': str(file_path.relative_to(project_path)),
                                    'line': line_number,
                                    'secret_type': secret_type,
                                    'description': f"发现硬编码的{secret_type}",
                                    'recommendation': '使用环境变量或配置文件存储敏感信息'
                                })

                except Exception as e:
                    logger.error(f"检查文件 {file_path} 硬编码密钥失败: {e}")

        except Exception as e:
            return {'error': str(e)}

        return {
            'issues_found': len(issues),
            'issues': issues
        }

    async def _check_insecure_dependencies(self, project_path: str) -> dict[str, Any]:
        """检查不安全的依赖"""
        issues = []

        try:
            # 检查requirements.txt
            requirements_file = Path(project_path) / 'requirements.txt'
            if requirements_file.exists():
                with open(requirements_file) as f:
                    requirements = f.read().split('\n')

                # 已知有安全问题的包
                vulnerable_packages = {
                    'pickle': '可能存在不安全反序列化',
                    'c_pickle': '可能存在不安全反序列化',
                    'subprocess': '可能存在命令注入',
                    'eval': '可能存在代码注入',
                    'exec': '可能存在代码注入'
                }

                for requirement in requirements:
                    requirement = requirement.strip()
                    if not requirement or requirement.startswith('#'):
                        package_name = requirement.split('==')[0].split('>=')[0].split('<=')[0].strip()

                        if package_name in vulnerable_packages:
                            issues.append({
                                'type': 'insecure_dependency',
                                'severity': 'medium',
                                'package': package_name,
                                'description': vulnerable_packages[package_name],
                                'recommendation': f"考虑使用{package_name}的安全替代方案"
                            })

            # 检查setup.py
            setup_file = Path(project_path) / 'setup.py'
            if setup_file.exists():
                with open(setup_file) as f:
                    setup_content = f.read()

                for package_name, description in vulnerable_packages.items():
                    if package_name in setup_content:
                        issues.append({
                            'type': 'insecure_dependency',
                            'severity': 'medium',
                            'package': package_name,
                            'file': 'setup.py',
                            'description': description,
                            'recommendation': f"考虑使用{package_name}的安全替代方案"
                        })

        except Exception as e:
            return {'error': str(e)}

        return {
            'issues_found': len(issues),
            'issues': issues
        }

    async def _check_weak_cryptography(self, project_path: str) -> dict[str, Any]:
        """检查弱加密"""
        issues = []

        weak_crypto_patterns = [
            (r'md5\(', 'MD5哈希算法已被认为不安全'),
            (r'sha1\(', 'SHA1哈希算法已被认为不安全'),
            (r'rsa\.generate_private_key\([^,)]+\s*,\s*1024', 'RSA密钥长度小于2048位不安全'),
            (r'AES\.new\([^,)]+\s*,\s*AES\.MODE_ECB', 'AES ECB模式不安全'),
            (r'des\(', 'DES加密算法已被破解'),
            (r'rc4\(', 'RC4流密码已被认为不安全')
        ]

        try:
            for file_path in Path(project_path).rglob('*.py'):
                try:
                    with open(file_path, encoding='utf-8') as f:
                        content = f.read()

                    line_number = 0
                    for line in content.split('\n'):
                        line_number += 1

                        for pattern, description in weak_crypto_patterns:
                            if re.search(pattern, line, re.IGNORECASE):
                                issues.append({
                                    'type': 'weak_cryptography',
                                    'severity': 'high',
                                    'file': str(file_path.relative_to(project_path)),
                                    'line': line_number,
                                    'description': description,
                                    'recommendation': '使用更强的加密算法（如SHA-256、AES-256-GCM等）'
                                })

                except Exception as e:
                    logger.error(f"检查文件 {file_path} 弱加密失败: {e}")

        except Exception as e:
            return {'error': str(e)}

        return {
            'issues_found': len(issues),
            'issues': issues
        }

    async def _check_input_validation(self, project_path: str) -> dict[str, Any]:
        """检查输入验证"""
        issues = []

        try:
            for file_path in Path(project_path).rglob('*.py'):
                try:
                    with open(file_path, encoding='utf-8') as f:
                        content = f.read()

                    # 检查是否有输入验证的缺失
                    flask_routes = re.findall(r'@app\.route\([^)]+\)', content)
                    re.findall(r'def\s+\w+\s*\([^)]*\)\s*->\s*HttpResponse', content)

                    # 检查这些路由/视图是否有输入验证
                    for _i, route in enumerate(flask_routes):
                        # 简化检查：如果路由后面没有验证逻辑，标记为潜在问题
                        route_start = content.find(route)
                        next_function = content.find('def ', route_start)

                        if next_function > route_start:
                            function_code = content[next_function:next_function+2000]  # 取函数的一部分

                            # 检查是否有验证
                            if not any(keyword in function_code.lower() for keyword in
                                      ['validate', 'verify', 'check', 'sanitize', 'escape']):
                                issues.append({
                                    'type': 'missing_input_validation',
                                    'severity': 'medium',
                                    'file': str(file_path.relative_to(project_path)),
                                    'route': route,
                                    'description': '缺少输入验证',
                                    'recommendation': '添加适当的输入验证和清理'
                                })

                except Exception as e:
                    logger.error(f"检查文件 {file_path} 输入验证失败: {e}")

        except Exception as e:
            return {'error': str(e)}

        return {
            'issues_found': len(issues),
            'issues': issues
        }

    async def _check_authentication_issues(self, project_path: str) -> dict[str, Any]:
        """检查认证问题"""
        issues = []

        auth_anti_patterns = [
            (r'password\s*==\s*["\'][^"\']+["\']', "硬编码密码比较"),
            (r'session\[.*\]\s*==\s*["\'][^"\']+["\']', "硬编码会话值比较"),
            (r'auth\.login\([^,)]+\s*,\s*["\'][^"\']+["\']', "硬编码认证凭据"),
            (r'cookie\[.*\]\s*==\s*["\'][^"\']+["\']', "硬编码Cookie值")
        ]

        try:
            for file_path in Path(project_path).rglob('*.py'):
                try:
                    with open(file_path, encoding='utf-8') as f:
                        content = f.read()

                    line_number = 0
                    for line in content.split('\n'):
                        line_number += 1

                        for pattern, description in auth_anti_patterns:
                            if re.search(pattern, line, re.IGNORECASE):
                                issues.append({
                                    'type': 'authentication_issue',
                                    'severity': 'high',
                                    'file': str(file_path.relative_to(project_path)),
                                    'line': line_number,
                                    'description': description,
                                    'recommendation': '使用安全的认证机制（如哈希比较、JWT等）'
                                })

                except Exception as e:
                    logger.error(f"检查文件 {file_path} 认证问题失败: {e}")

        except Exception as e:
            return {'error': str(e)}

        return {
            'issues_found': len(issues),
            'issues': issues
        }

    async def _check_authorization_issues(self, project_path: str) -> dict[str, Any]:
        """检查授权问题"""
        issues = []

        try:
            for file_path in Path(project_path).rglob('*.py'):
                try:
                    with open(file_path, encoding='utf-8') as f:
                        content = f.read()

                    # 检查是否有管理员权限直接判断
                    if 'if user.is_admin:' in content or 'if user.is_superuser:' in content:
                        issues.append({
                            'type': 'authorization_issue',
                            'severity': 'medium',
                            'file': str(file_path.relative_to(project_path)),
                            'description': '直接检查管理员权限',
                            'recommendation': '使用基于角色的访问控制（RBAC）'
                        })

                    # 检查是否有硬编码的权限检查
                    if re.search(r'user\.id\s*==\s*\d+', content):
                        issues.append({
                            'type': 'authorization_issue',
                            'severity': 'medium',
                            'file': str(file_path.relative_to(project_path)),
                            'description': '硬编码用户ID权限检查',
                            'recommendation': '使用动态权限管理系统'
                        })

                except Exception as e:
                    logger.error(f"检查文件 {file_path} 授权问题失败: {e}")

        except Exception as e:
            return {'error': str(e)}

        return {
            'issues_found': len(issues),
            'issues': issues
        }

    async def _check_data_exposure(self, project_path: str) -> dict[str, Any]:
        """检查数据暴露"""
        issues = []

        data_exposure_patterns = [
            (r'print\([^)]*password[^)]*\)', '密码信息可能被打印'),
            (r'print\([^)]*token[^)]*\)', '令牌信息可能被打印'),
            (r'print\([^)]*secret[^)]*\)', '密钥信息可能被打印'),
            (r'logging\.(debug|info)\([^)]*password[^)]*\)', '密码信息可能被记录'),
            (r'logging\.(debug|info)\([^)]*token[^)]*\)', '令牌信息可能被记录'),
            (r'logger\.(debug|info)\([^)]*password[^)]*\)', '密码信息可能被记录'),
            (r'logger\.(debug|info)\([^)]*token[^)]*\)', '令牌信息可能被记录'),
            (r'return.*password', '密码可能通过API返回'),
            (r'return.*token', '令牌可能通过API返回')
        ]

        try:
            for file_path in Path(project_path).rglob('*.py'):
                try:
                    with open(file_path, encoding='utf-8') as f:
                        content = f.read()

                    line_number = 0
                    for line in content.split('\n'):
                        line_number += 1

                        for pattern, description in data_exposure_patterns:
                            if re.search(pattern, line, re.IGNORECASE):
                                issues.append({
                                    'type': 'data_exposure',
                                    'severity': 'high',
                                    'file': str(file_path.relative_to(project_path)),
                                    'line': line_number,
                                    'description': description,
                                    'recommendation': '移除敏感信息的日志记录和返回'
                                })

                except Exception as e:
                    logger.error(f"检查文件 {file_path} 数据暴露失败: {e}")

        except Exception as e:
            return {'error': str(e)}

        return {
            'issues_found': len(issues),
            'issues': issues
        }

    async def _check_insecure_communication(self, project_path: str) -> dict[str, Any]:
        """检查不安全通信"""
        issues = []

        insecure_comm_patterns = [
            (r'http://[^"\'\s]+', "使用HTTP协议"),
            (r'verify\s*=\s*False', 'SSL证书验证被禁用'),
            (r'ssl\.verify\s*=\s*False', 'SSL证书验证被禁用'),
            (r'urllib\.request\.urlopen\([^)]*\)', '可能缺少SSL验证'),
            (r'requests\.get\([^)]*verify\s*=\s*False[^)]*\)', 'SSL验证被禁用'),
            (r'requests\.post\([^)]*verify\s*=\s*False[^)]*\)', 'SSL验证被禁用'),
            (r'socket\.socket\([^)]*\)', '使用原始socket（可能不安全）'),
            (r'telnetlib\.', '使用Telnet协议（不安全）'),
            (r'ftplib\.', '使用FTP协议（不安全）')
        ]

        try:
            for file_path in Path(project_path).rglob('*.py'):
                try:
                    with open(file_path, encoding='utf-8') as f:
                        content = f.read()

                    line_number = 0
                    for line in content.split('\n'):
                        line_number += 1

                        for pattern, description in insecure_comm_patterns:
                            if re.search(pattern, line, re.IGNORECASE):
                                issues.append({
                                    'type': 'insecure_communication',
                                    'severity': 'high',
                                    'file': str(file_path.relative_to(project_path)),
                                    'line': line_number,
                                    'description': description,
                                    'recommendation': '使用HTTPS协议并启用SSL证书验证'
                                })

                except Exception as e:
                    logger.error(f"检查文件 {file_path} 不安全通信失败: {e}")

        except Exception as e:
            return {'error': str(e)}

        return {
            'issues_found': len(issues),
            'issues': issues
        }

    def _calculate_security_score(self, vulnerabilities_by_category: dict[str, Any]) -> float:
        """计算安全评分"""
        total_issues = 0
        critical_issues = 0

        for _category, check_result in vulnerabilities_by_category.items():
            if isinstance(check_result, dict) and 'issues' in check_result:
                issues = check_result['issues']
                total_issues += len(issues)

                critical_issues += len([i for i in issues if i.get('severity') == 'critical' or i.get('severity') == 'high'])

        if total_issues == 0:
            return 100.0

        # 基础分数
        base_score = 100.0

        # 根据问题数量扣分
        base_score -= min(50, total_issues * 2)  # 每个问题扣2分，最多扣50分

        # 关键问题额外扣分
        base_score -= min(40, critical_issues * 10)  # 每个关键问题扣10分，最多扣40分

        return max(0, base_score)

    def _assess_security_risk(self, security_issues: list[dict[str, Any]) -> dict[str, Any]:
        """评估安全风险"""
        if not security_issues:
            return {
                'risk_level': 'low',
                'risk_score': 0.0,
                'critical_vulnerabilities': 0,
                'high_vulnerabilities': 0,
                'medium_vulnerabilities': 0,
                'low_vulnerabilities': 0
            }

        critical_count = len([i for i in security_issues if i.get('severity') == 'critical'])
        high_count = len([i for i in security_issues if i.get('severity') == 'high'])
        medium_count = len([i for i in security_issues if i.get('severity') == 'medium'])
        low_count = len([i for i in security_issues if i.get('severity') == 'low'])

        # 计算风险分数
        risk_score = (critical_count * 10 + high_count * 5 + medium_count * 2 + low_count * 1)

        # 确定风险等级
        if critical_count > 0 or high_count > 5:
            risk_level = 'critical'
        elif high_count > 0 or medium_count > 10:
            risk_level = 'high'
        elif medium_count > 0 or low_count > 20:
            risk_level = 'medium'
        else:
            risk_level = 'low'

        return {
            'risk_level': risk_level,
            'risk_score': risk_score,
            'critical_vulnerabilities': critical_count,
            'high_vulnerabilities': high_count,
            'medium_vulnerabilities': medium_count,
            'low_vulnerabilities': low_count
        }

    async def _check_compliance(self, project_path: str) -> dict[str, Any]:
        """检查合规性"""
        compliance_checks = {
            'has_license': False,
            'has_readme': False,
            'has_security_policy': False,
            'has_privacy_policy': False,
            'has_tests': False
        }

        try:
            project_root = Path(project_path)

            # 检查许可证文件
            license_files = ['LICENSE', 'LICENSE.txt', 'LICENSE.md', 'COPYING']
            for license_file in license_files:
                if (project_root / license_file).exists():
                    compliance_checks['has_license'] = True
                    break

            # 检查README
            readme_files = ['README.md', 'README.txt', 'README.rst']
            for readme_file in readme_files:
                if (project_root / readme_file).exists():
                    compliance_checks['has_readme'] = True
                    break

            # 检查安全政策
            security_files = ['SECURITY.md', 'SECURITY.txt', '.security']
            for security_file in security_files:
                if (project_root / security_file).exists():
                    compliance_checks['has_security_policy'] = True
                    break

            # 检查隐私政策
            privacy_files = ['PRIVACY.md', 'PRIVACY.txt', 'privacy-policy.md']
            for privacy_file in privacy_files:
                if (project_root / privacy_file).exists():
                    compliance_checks['has_privacy_policy'] = True
                    break

            # 检查测试
            test_dirs = ['tests', 'test', '__tests__']
            for test_dir in test_dirs:
                if (project_root / test_dir).exists():
                    compliance_checks['has_tests'] = True
                    break

            # 检查Python测试文件
            if not compliance_checks['has_tests']:
                test_files = list(project_root.rglob('test_*.py'))
                test_files.extend(project_root.rglob('*_test.py'))
                if test_files:
                    compliance_checks['has_tests'] = True

        except Exception as e:
            logger.error(f"合规性检查失败: {e}")

        return compliance_checks

    def _generate_security_recommendations(self, audit_results: dict[str, Any]) -> list[str]:
        """生成安全建议"""
        recommendations = []

        risk_level = audit_results.get('risk_assessment', {}).get('risk_level', 'unknown')

        if risk_level == 'critical':
            recommendations.append('发现关键安全漏洞，建议立即修复所有关键和高风险问题')

        if risk_level in ['critical', 'high']:
            recommendations.append('建立定期安全审计流程，及时发现和修复安全问题')
            recommendations.append('实施安全开发生命周期（SDLC）实践')

        # 基于具体问题的建议
        vulnerabilities = audit_results.get('security_issues', [])

        if any(i.get('type') == 'hardcoded_secret' for i in vulnerabilities):
            recommendations.append('使用环境变量或密钥管理系统存储敏感信息')

        if any(i.get('type') == 'insecure_communication' for i in vulnerabilities):
            recommendations.append('所有外部通信使用HTTPS协议并启用SSL证书验证')

        if any(i.get('type') == 'weak_cryptography' for i in vulnerabilities):
            recommendations.append('更新到强加密算法（如SHA-256、AES-256-GCM）')

        if any(i.get('type') == 'missing_input_validation' for i in vulnerabilities):
            recommendations.append('为所有用户输入添加适当的验证和清理')

        # 合规性建议
        compliance = audit_results.get('compliance_check', {})

        if not compliance.get('has_license'):
            recommendations.append('添加适当的许可证文件')

        if not compliance.get('has_security_policy'):
            recommendations.append('创建安全政策文档')

        if not compliance.get('has_tests'):
            recommendations.append('增加自动化测试覆盖率')

        return recommendations

class QualityAssuranceSystem:
    """质量保证系统主类"""

    def __init__(self):
        """初始化质量保证系统"""
        self.code_analyzer = CodeQualityAnalyzer()
        self.performance_tester = PerformanceTester()
        self.security_auditor = SecurityAuditor()
        self.test_results = {}

    async def run_comprehensive_qa(self, project_path: str) -> dict[str, Any]:
        """运行全面质量保证检查"""
        logger.info(f"开始全面质量保证检查: {project_path}")

        qa_results = {
            'project_path': project_path,
            'timestamp': datetime.now().isoformat(),
            'quality_report': None,
            'performance_tests': None,
            'security_audit': None,
            'overall_assessment': None,
            'recommendations': []
        }

        try:
            # 1. 代码质量分析
            logger.info('执行代码质量分析...')
            qa_results['quality_report'] = await self.code_analyzer.analyze_project(project_path)

            # 2. 性能测试
            logger.info('执行性能测试...')
            qa_results['performance_tests'] = await self.performance_tester.run_performance_tests(project_path)

            # 3. 安全审计
            logger.info('执行安全审计...')
            qa_results['security_audit'] = await self.security_auditor.audit_security(project_path)

            # 4. 综合评估
            qa_results['overall_assessment'] = self._generate_overall_assessment(qa_results)

            # 5. 生成建议
            qa_results['recommendations'] = self._generate_overall_recommendations(qa_results)

        except Exception as e:
            logger.error(f"质量保证检查失败: {e}")
            qa_results['error'] = str(e)

        return qa_results

    def _generate_overall_assessment(self, qa_results: dict[str, Any]) -> dict[str, Any]:
        """生成综合评估"""
        assessment = {
            'overall_score': 0.0,
            'quality_grade': 'F',
            'key_metrics': {},
            'strengths': [],
            'weaknesses': [],
            'improvement_priority': []
        }

        try:
            # 收集各项评分
            quality_score = qa_results.get('quality_report', {}).get('overall_score', 0)
            security_score = qa_results.get('security_audit', {}).get('overall_security_score', 0)

            # 性能评分（简化版）
            performance_score = 80  # 默认值，可以基于性能测试结果调整

            # 权重
            weights = {
                'quality': 0.4,
                'security': 0.4,
                'performance': 0.2
            }

            # 计算总体评分
            assessment['overall_score'] = (
                quality_score * weights['quality'] +
                security_score * weights['security'] +
                performance_score * weights['performance']
            )

            # 确定等级
            score = assessment['overall_score']
            if score >= 90:
                assessment['quality_grade'] = 'A'
            elif score >= 80:
                assessment['quality_grade'] = 'B'
            elif score >= 70:
                assessment['quality_grade'] = 'C'
            elif score >= 60:
                assessment['quality_grade'] = 'D'
            else:
                assessment['quality_grade'] = 'F'

            # 关键指标
            assessment['key_metrics'] = {
                'code_quality_score': quality_score,
                'security_score': security_score,
                'performance_score': performance_score,
                'total_issues': len(qa_results.get('quality_report', {}).get('issues', [])),
                'security_vulnerabilities': len(qa_results.get('security_audit', {}).get('security_issues', []))
            }

            # 优势和劣势
            if quality_score >= 80:
                assessment['strengths'].append('代码质量良好')
            if security_score >= 80:
                assessment['strengths'].append('安全性较强')
            if performance_score >= 80:
                assessment['strengths'].append('性能表现良好')

            if quality_score < 70:
                assessment['weaknesses'].append('代码质量需要改进')
            if security_score < 70:
                assessment['weaknesses'].append('存在安全风险')
            if performance_score < 70:
                assessment['weaknesses'].append('性能需要优化')

            # 改进优先级
            issues = qa_results.get('quality_report', {}).get('issues', [])
            vulnerabilities = qa_results.get('security_audit', {}).get('security_issues', [])

            # 按严重程度排序
            critical_issues = [i for i in issues + vulnerabilities if i.get('severity') in ['critical', 'high']
            medium_issues = [i for i in issues + vulnerabilities if i.get('severity') == 'medium']

            if critical_issues:
                assessment['improvement_priority'].append('立即修复关键和高严重性问题')
            if medium_issues:
                assessment['improvement_priority'].append('计划修复中等严重性问题')

            assessment['improvement_priority'].extend([
                '提升测试覆盖率',
                '改善代码文档',
                '优化性能瓶颈'
            ])

        except Exception as e:
            logger.error(f"生成综合评估失败: {e}")

        return assessment

    def _generate_overall_recommendations(self, qa_results: dict[str, Any]) -> list[str]:
        """生成总体建议"""
        recommendations = []

        # 代码质量建议
        quality_report = qa_results.get('quality_report')
        if quality_report:
            recommendations.extend(quality_report.get('recommendations', []))

        # 安全建议
        security_audit = qa_results.get('security_audit')
        if security_audit:
            recommendations.extend(security_audit.get('recommendations', []))

        # 性能建议
        performance_tests = qa_results.get('performance_tests')
        if performance_tests:
            # 基于性能测试结果生成建议
            memory_data = performance_tests.get('memory_usage', {})
            if memory_data.get('memory_increase_mb', 0) > 100:
                recommendations.append('内存使用增长过快，检查是否存在内存泄漏')

            cpu_data = performance_tests.get('cpu_performance', {})
            if cpu_data.get('operations_per_second', 0) < 1000:
                recommendations.append('CPU性能较低，考虑算法优化或并行处理')

        # 去重并排序建议
        unique_recommendations = list(set(recommendations))
        unique_recommendations.sort()

        return unique_recommendations

# 全局质量保证系统实例
_qa_system = None

def get_quality_assurance_system() -> QualityAssuranceSystem:
    """获取质量保证系统实例"""
    global _qa_system
    if _qa_system is None:
        _qa_system = QualityAssuranceSystem()
    return _qa_system

if __name__ == '__main__':
    async def test_quality_assurance_system():
        """测试质量保证系统"""
        qa_system = get_quality_assurance_system()

        # 测试项目路径
        project_path = '/Users/xujian/Athena工作平台'

        # 运行全面质量保证检查
        qa_results = await qa_system.run_comprehensive_qa(project_path)

        logger.info("质量保证检查结果:")
        logger.info(f"  总体评分: {qa_results.get('overall_assessment', {}).get('overall_score', 0):.1f}")
        logger.info(f"  质量等级: {qa_results.get('overall_assessment', {}).get('quality_grade', 'F')}")
        logger.info(f"  代码质量问题: {len(qa_results.get('quality_report', {}).get('issues', []))}")
        logger.info(f"  安全漏洞: {len(qa_results.get('security_audit', {}).get('security_issues', []))}")
        logger.info(f"  改进建议: {len(qa_results.get('recommendations', []))}")

        # 保存结果到文件
        with open('qa_results.json', 'w', encoding='utf-8') as f:
            json.dump(qa_results, f, ensure_ascii=False, indent=2, default=str)

        logger.info('详细结果已保存到 qa_results.json')

    asyncio.run(test_quality_assurance_system())
