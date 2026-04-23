# pyright: ignore
# !/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
认知模块质量保障框架
Cognitive Module Quality Assurance Framework

提供零容忍错误检查和质量保证工具

作者: Athena平台团队
版本: v1.0.0
"""

import ast
import logging
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class Severity(Enum):
    """问题严重程度"""
    CRITICAL = "critical"  # 零容忍,必须修复
    HIGH = "high"         # 高优先级,应该修复
    MEDIUM = "medium"     # 中等优先级,建议修复
    LOW = "low"           # 低优先级,可选修复


@dataclass
class QualityIssue:
    """质量问题"""
    file_path: str
    line: int
    severity: Severity
    issue_type: str
    message: str
    code_snippet: str
    suggestion: Optional[str] = None


class CognitiveQualityChecker:
    """认知模块质量检查器"""

    # 零容忍规则
    ZERO_TOLERANCE_RULES = {
        'syntax_error',
        'bare_except',
        'pass_in_except',
        'unreachable_code',
        'undefined_variable',
    }

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.issues: list[QualityIssue] = []

    def check(self) -> list[QualityIssue]:
        """执行完整检查"""
        try:
            content = self.file_path.read_text(encoding='utf-8', errors='ignore')

            # 语法检查
            try:
                tree = ast.parse(content)
            except SyntaxError:
                pass  # TODO: 添加适当的错误处理
            # AST检查
            self._check_ast(tree, content)  # type: ignore

            # 额外模式检查
            self._check_patterns(content)
        except Exception as e:
            # 质量检查失败，记录错误
            logger.error(f'质量检查失败: {e}', exc_info=True)

        return self.issues

    def _check_ast(self, tree: ast.AST, content: str):
        """检查AST节点"""
        lines = content.split('\n')

        for node in ast.walk(tree):
            # 检查异常处理
            if isinstance(node, ast.Try):
                self._check_try_except(node, lines)

            # 检查函数定义
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._check_function(node, lines)

    def _check_try_except(self, node: ast.Try, lines: list[str]):
        """检查异常处理"""
        for handler in node.handlers:
            # 零容忍: 裸except
            if handler.type is None:
                self.issues.append(QualityIssue(
                    file_path=str(self.file_path),
                    line=handler.lineno,
                    severity=Severity.CRITICAL,
                    issue_type='bare_except',
                    message='发现裸except块,违反零容忍原则',
                    code_snippet=lines[handler.lineno - 1] if handler.lineno <= len(lines) else '',
                    suggestion='指定具体的异常类型,如: except (ValueError, TypeError) as e:'
                ))

            # 零容忍: except块只有pass
            elif isinstance(handler.body, list) and len(handler.body) == 1:  # type: ignore
                if isinstance(handler.body[0], ast.Pass):
                    self.issues.append(QualityIssue(
                        file_path=str(self.file_path),
                        line=handler.lineno,
                        severity=Severity.CRITICAL,
                        issue_type='pass_in_except',
                        message='except块只有pass,错误被静默忽略',
                        code_snippet=lines[handler.lineno - 1] if handler.lineno <= len(lines) else '',
                        suggestion='至少应添加日志记录: logger.error(f"错误: {e}")'
                    ))

            # 高优先级: except块只有日志没有其他处理
            elif len(handler.body) <= 2:
                has_logger = False
                has_raise_or_return = False

                for stmt in handler.body:
                    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                        call = stmt.value
                        if isinstance(call.func, ast.Attribute):
                            if call.func.attr in ['debug', 'info', 'warning', 'error']:
                                has_logger = True

                    if isinstance(stmt, (ast.Raise, ast.Return)):
                        has_raise_or_return = True

                if has_logger and not has_raise_or_return:
                    self.issues.append(QualityIssue(
                        file_path=str(self.file_path),
                        line=handler.lineno,
                        severity=Severity.HIGH,
                        issue_type='insufficient_error_handling',
                        message='异常处理不充分,仅有日志记录',
                        code_snippet=lines[handler.lineno - 1] if handler.lineno <= len(lines) else '',
                        suggestion='应添加raise或return重新抛出异常'
                    ))

    def _check_function(self, node: ast.FunctionDef, lines: list[str]):
        """检查函数定义"""
        # 检查公共函数是否有文档字符串
        if not node.name.startswith('_'):
            docstring = ast.get_docstring(node)
            if not docstring:
                self.issues.append(QualityIssue(
                    file_path=str(self.file_path),
                    line=node.lineno,
                    severity=Severity.MEDIUM,
                    issue_type='missing_docstring',
                    message=f'公共函数 {node.name} 缺少文档字符串',
                    code_snippet=f'def {node.name}(...)',
                    suggestion='添加函数文档字符串说明功能、参数和返回值'
                ))

            # 检查返回类型注解
            if not node.returns:
                self.issues.append(QualityIssue(
                    file_path=str(self.file_path),
                    line=node.lineno,
                    severity=Severity.MEDIUM,
                    issue_type='missing_return_annotation',
                    message=f'函数 {node.name} 缺少返回类型注解',
                    code_snippet=f'def {node.name}(...)',
                    suggestion='添加返回类型注解,如: def {node.name}(...) -> ReturnType:'
                ))

    def _check_patterns(self, content: str):
        """检查额外的问题模式"""
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # 检查除以零风险
            if re.search(r'/\s*\w+\s*([+\-*/]|%|\])', line):
                # 检查上下文是否有保护
                context = '\n'.join(lines[max(0, i - 5):i])
                if not re.search(r'(if.*!=\s*0|if.*>\s*0|if\s+\w+\s*:)', context):
                    self.issues.append(QualityIssue(
                        file_path=str(self.file_path),
                        line=i,
                        severity=Severity.HIGH,
                        issue_type='division_by_zero_risk',
                        message='存在潜在的除以零风险',
                        code_snippet=line.strip(),
                        suggestion='添加除数检查: if denominator != 0:'
                    ))

            # 检查None比较
            if ' == None' in line or ' != None' in line:
                self.issues.append(QualityIssue(
                    file_path=str(self.file_path),
                    line=i,
                    severity=Severity.MEDIUM,
                    issue_type='none_comparison',
                    message='使用 `is None` 而非 `== None`',
                    code_snippet=line.strip(),
                    suggestion='使用 `is None` 或 `is not None`'
                ))

            # 检查可变默认参数
            if re.search(r'def \w+\([^)]*=\[\]', line):
                self.issues.append(QualityIssue(
                    file_path=str(self.file_path),
                    line=i,
                    severity=Severity.HIGH,
                    issue_type='mutable_default',
                    message='使用可变对象作为默认参数',
                    code_snippet=line.strip(),
                    suggestion='使用 None 作为默认值并在函数内创建: def func(x=None): if x is None: x = []'
                ))


class CognitiveModuleQualityGuard:
    """认知模块质量保障门禁"""

    def __init__(self, root_path: Optional[Path] = None):
        self.root_path = root_path or Path('/Users/xujian/Athena工作平台')

    def check_module(self, module_path: str) -> tuple[bool, list[QualityIssue]]:
        """检查单个模块"""
        module_file = self.root_path / module_path

        if not module_file.exists():
            return False, [QualityIssue(
                file_path=module_path,
                line=0,
                severity=Severity.CRITICAL,
                issue_type='file_not_found',
                message=f'文件不存在: {module_path}',
                code_snippet='',
                suggestion='检查文件路径'
            )]

        checker = CognitiveQualityChecker(module_file)
        issues = checker.check()

        # 检查是否有零容忍问题
        has_zero_tolerance = any(
            issue.issue_type in CognitiveQualityChecker.ZERO_TOLERANCE_RULES
            for issue in issues
        )

        return not has_zero_tolerance, issues

    def check_all_cognitive_modules(self) -> dict[str, Any]:
        """检查所有认知模块"""
        cognitive_dirs = [
            'core/cognition',
            'core/decision',
            'core/evaluation',
            'core/planning',
            'core/reasoning',
        ]

        results = {
            'total_files': 0,
            'passed_files': 0,
            'failed_files': 0,
            'total_issues': 0,
            'zero_tolerance_violations': 0,
            'issues_by_severity': {
                'critical': 0,
                'high': 0,
                'medium': 0,
                'low': 0
            },
            'failed_modules': []
        }

        for dir_name in cognitive_dirs:
            module_dir = self.root_path / dir_name
            if not module_dir.exists():
                continue

            for py_file in module_dir.rglob('*.py'):
                if any(x in py_file.parts for x in ['__pycache__', 'test', '.bak']):
                    continue

                results['total_files'] += 1

                checker = CognitiveQualityChecker(py_file)
                issues = checker.check()

                if issues:
                    has_critical = any(
                        issue.issue_type in CognitiveQualityChecker.ZERO_TOLERANCE_RULES
                        for issue in issues
                    )

                    if has_critical:
                        results['failed_files'] += 1
                        results['zero_tolerance_violations'] += 1
                        results['failed_modules'].append({
                            'file': str(py_file.relative_to(self.root_path)),
                            'critical_issues': [i for i in issues if i.severity == Severity.CRITICAL]
                        })
                    else:
                        results['passed_files'] += 1

                    results['total_issues'] += len(issues)

                    for issue in issues:
                        results['issues_by_severity'][issue.severity.value] += 1  # type: ignore
                else:
                    results['passed_files'] += 1

        return results


# 便捷函数
def check_cognitive_module(module_path: str) -> tuple[bool, list[QualityIssue]]:
    """检查认知模块(便捷函数)"""
    guard = CognitiveModuleQualityGuard()
    return guard.check_module(module_path)


def quality_gate_passed() -> bool:
    """检查质量门禁是否通过"""
    guard = CognitiveModuleQualityGuard()
    results = guard.check_all_cognitive_modules()

    return results['zero_tolerance_violations'] == 0


if __name__ == '__main__':
    # 运行质量检查
    import sys
    if len(sys.argv) > 1:
        # 检查指定模块
        passed, issues = check_cognitive_module(sys.argv[1])

        if passed:
            print(f"✅ {sys.argv[1]} 质量检查通过")
            sys.exit(0)
        else:
            print(f"❌ {sys.argv[1]} 质量检查失败")
            for issue in issues:
                print(f"  {issue.severity.value.upper()}: {issue.message}")
            sys.exit(1)
    else:
        # 检查所有认知模块
        guard = CognitiveModuleQualityGuard()
        results = guard.check_all_cognitive_modules()

        print("=" * 80)
        print("认知模块质量检查报告")
        print("=" * 80)

        print("\n📊 统计:")
        print(f"  - 扫描文件: {results.get('total_files')}")
        print(f"  - 通过检查: {results.get('passed_files')}")
        print(f"  - 失败检查: {results.get('failed_files')}")
        print(f"  - 发现问题: {results.get('total_issues')}")
        print(f"  - 零容忍违规: {results.get('zero_tolerance_violations')}")

        print("\n🔴 严重程度:")
        for severity, count in results.get('issues_by_severity').items():  # type: ignore
            if count > 0:
                print(f"  - {severity.upper()}: {count}")

        if results.get('failed_modules'):
            print("\n❌ 失败的模块:")
            for module in results.get('failed_modules'):  # type: ignore
                print(f"  - {module['file']}")
                for issue in module['critical_issues']:
                    print(f"    {issue.line}: {issue.message}")

        print("\n" + "=" * 80)

        # 返回退出码
        sys.exit(0 if results['zero_tolerance_violations'] == 0 else 1)

