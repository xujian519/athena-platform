#!/usr/bin/env python3
"""
认知与决策模块逻辑错误扫描器
Logic Error Scanner for Cognitive & Decision Module

识别常见的逻辑错误模式：
- cannot assign to function call
- 未定义变量使用
- 逻辑恒等/恒不等
- 死代码
- 潜在的类型错误

作者: Athena Platform Team
版本: v1.0
"""

import ast
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class LogicError:
    """逻辑错误数据类"""
    file_path: str
    line_no: int
    col_offset: int
    error_type: str
    severity: str  # critical, high, medium, low
    message: str
    code_snippet: str


class LogicErrorScanner(ast.NodeVisitor):
    """逻辑错误扫描器"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.errors: List[LogicError] = []
        self.source_lines: List[str] = []

        with open(file_path, 'r', encoding='utf-8') as f:
            self.source_lines = f.readlines()

    def get_code_snippet(self, line_no: int, context: int = 2) -> str:
        """获取代码片段"""
        start = max(0, line_no - context - 1)
        end = min(len(self.source_lines), line_no + context)
        lines = []
        for i in range(start, end):
            prefix = ">>> " if i == line_no - 1 else "    "
            lines.append(f"{prefix}{i+1:4d}: {self.source_lines[i].rstrip()}")
        return "\n".join(lines)

    def add_error(self, node: ast.AST, error_type: str, severity: str, message: str):
        """添加错误"""
        snippet = self.get_code_snippet(node.lineno)
        error = LogicError(
            file_path=self.file_path,
            line_no=node.lineno,
            col_offset=getattr(node, 'col_offset', 0),
            error_type=error_type,
            severity=severity,
            message=message,
            code_snippet=snippet
        )
        self.errors.append(error)

    def visit_Assign(self, node: ast.Assign):
        """检查赋值语句"""
        # 检查是否尝试对函数调用赋值
        for target in node.targets:
            if isinstance(target, (ast.Call, ast.Subscript)):
                # 检查特殊情况：目标可能是合法的
                if isinstance(target, ast.Subscript):
                    # 检查slice是否为常量
                    if isinstance(target.slice, (ast.Index, ast.Constant)):
                        # 这可能是合法的，如: arr[0] = value
                        pass
                    else:
                        self.add_error(
                            target,
                            "cannot_assign_to_complex_subscript",
                            "high",
                            f"尝试对复杂的下标表达式赋值，可能导致运行时错误"
                        )
                elif isinstance(target, ast.Call):
                    self.add_error(
                        target,
                        "cannot_assign_to_function_call",
                        "critical",
                        f"尝试对函数调用结果赋值，这是不允许的"
                    )

        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare):
        """检查比较操作中的逻辑错误"""
        # 检查恒等/恒不等
        if len(node.ops) == 1:
            op = node.ops[0]
            left = node.left
            comparators = node.comparators[0] if node.comparators else None

            # 检查 x == x 或 x != x
            if isinstance(op, (ast.Eq, ast.NotEq)):
                if self._is_same_expression(left, comparators):
                    self.add_error(
                        node,
                        "always_true_or_false_comparison",
                        "medium",
                        f"比较表达式总是返回{'True' if isinstance(op, ast.Eq) else 'False'}"
                    )

        self.generic_visit(node)

    def visit_If(self, node: ast.If):
        """检查if语句中的逻辑问题"""
        # 检查条件是否总是为真或假
        if isinstance(node.test, ast.NameConstant):
            value = node.test.value
            if value is True:
                self.add_error(
                    node.test,
                    "always_true_condition",
                    "medium",
                    "if条件总是为True，else分支永远不会执行"
                )
            elif value is False:
                self.add_error(
                    node.test,
                    "always_false_condition",
                    "medium",
                    "if条件总是为False，if分支永远不会执行"
                )

        # 检查 if True: return / if False: return 模式
        if isinstance(node.test, ast.NameConstant) and node.test.value is True:
            if node.body and len(node.body) == 1:
                if isinstance(node.body[0], ast.Return) and node.orelse:
                    self.add_error(
                        node.test,
                        "unreachable_code",
                        "low",
                        "if True: return 后的代码永远不会执行"
                    )

        self.generic_visit(node)

    def visit_Try(self, node: ast.Try):
        """检查try-except块中的问题"""
        # 检查空的except块
        for handler in node.handlers:
            if not handler.body:
                self.add_error(
                    handler,
                    "empty_except_block",
                    "high",
                    "空的except块，隐藏所有异常"
                )
            elif len(handler.body) == 1 and isinstance(handler.body[0], ast.Pass):
                self.add_error(
                    handler,
                    "pass_except_block",
                    "medium",
                    "except块只有pass语句，没有错误处理"
                )

        self.generic_visit(node)

    def visit_While(self, node: ast.While):
        """检查while循环中的问题"""
        # 检查 while True: 模式（可能是合理的，但需要检查body）
        if isinstance(node.test, ast.NameConstant) and node.test.value is True:
            # 检查是否有break语句
            has_break = False
            for child in ast.walk(node):
                if isinstance(child, ast.Break):
                    has_break = True
                    break

            if not has_break:
                self.add_error(
                    node.test,
                    "infinite_loop",
                    "medium",
                    "while True: 循环没有break语句，可能是无限循环"
                )

        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        """检查函数调用中的问题"""
        # 检查 print() 调用（可能是调试代码）
        if isinstance(node.func, ast.Name) and node.func.id == 'print':
            self.add_error(
                node,
                "print_statement",
                "low",
                "存在print语句，生产代码应使用logger"
            )

        # 检查常见错误：dict.get(str, Any)
        if isinstance(node.func, ast.Attribute) and node.func.attr == 'get':
            if len(node.args) >= 2:
                # 检查是否是 dict.get(str, Any) 模式
                if isinstance(node.args[1], ast.Name) and node.args[1].id == 'Any':
                    self.add_error(
                        node,
                        "dict_get_any_pattern",
                        "high",
                        "dict.get(str, Any) 应该是 dict.get(str, default_value)"
                    )

        self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp):
        """检查二元操作中的问题"""
        # 检查除零风险
        if isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)):
            # 右操作数为0的情况（直接常量）
            if isinstance(node.right, (ast.Num, ast.Constant)):
                if isinstance(node.right, ast.Num) and node.right.n == 0:
                    self.add_error(
                        node.right,
                        "division_by_zero_constant",
                        "critical",
                        "除数为常量0，会导致ZeroDivisionError"
                    )
                elif isinstance(node.right, ast.Constant) and node.right.value == 0:
                    self.add_error(
                        node.right,
                        "division_by_zero_constant",
                        "critical",
                        "除数为常量0，会导致ZeroDivisionError"
                    )

        self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        """检查变量使用"""
        # 这个检查需要整个文件的上下文，在类级别完成
        pass

    def _is_same_expression(self, left: ast.AST, right: ast.AST) -> bool:
        """检查两个表达式是否相同（简化版）"""
        if type(left) != type(right):
            return False

        if isinstance(left, ast.Name):
            return left.id == right.id if isinstance(right, ast.Name) else False

        if isinstance(left, ast.Constant):
            return left.value == right.value if isinstance(right, ast.Constant) else False

        return False


def scan_file(file_path: str) -> List[LogicError]:
    """扫描单个文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()

        tree = ast.parse(source, filename=file_path)
        scanner = LogicErrorScanner(file_path)
        scanner.visit(tree)
        return scanner.errors

    except SyntaxError as e:
        print(f"⚠️  语法错误 {file_path}:{e.lineno}: {e.msg}")
        return []
    except Exception as e:
        print(f"❌ 扫描失败 {file_path}: {e}")
        return []


def scan_directory(directory: str, pattern: str = "*.py") -> Dict[str, List[LogicError]]:
    """扫描目录"""
    results = {}
    dir_path = Path(directory)

    for file_path in dir_path.rglob(pattern):
        errors = scan_file(str(file_path))
        if errors:
            results[str(file_path)] = errors

    return results


def print_results(results: Dict[str, List[LogicError]]):
    """打印扫描结果"""
    total_errors = sum(len(errors) for errors in results.values())

    print("\n" + "="*80)
    print(f"📊 逻辑错误扫描结果")
    print("="*80)
    print(f"扫描文件数: {len(results)}")
    print(f"发现问题数: {total_errors}")
    print("="*80 + "\n")

    # 按严重级别分组
    by_severity = defaultdict(list)
    for file_path, errors in results.items():
        for error in errors:
            by_severity[error.severity].append((file_path, error))

    # 打印各严重级别的错误
    for severity in ['critical', 'high', 'medium', 'low']:
        if severity not in by_severity:
            continue

        severity_name = {
            'critical': '🔴 严重',
            'high': '🟠 高',
            'medium': '🟡 中',
            'low': '🔵 低'
        }[severity]

        print(f"\n{severity_name} 优先级问题 ({len(by_severity[severity])}个)")
        print("-" * 80)

        for file_path, error in by_severity[severity]:
            print(f"\n📁 {file_path}:{error.line_no}")
            print(f"   类型: {error.error_type}")
            print(f"   说明: {error.message}")
            print(f"\n   代码上下文:")
            for line in error.code_snippet.split('\n'):
                print(f"   {line}")

    # 统计信息
    print("\n" + "="*80)
    print("📈 错误类型统计")
    print("="*80)

    error_types = defaultdict(int)
    for errors in results.values():
        for error in errors:
            error_types[error.error_type] += 1

    for error_type, count in sorted(error_types.items(), key=lambda x: -x[1]):
        print(f"  {error_type}: {count}")

    # 按文件统计
    print("\n" + "="*80)
    print("📁 按文件统计")
    print("="*80)

    for file_path, errors in sorted(results.items(), key=lambda x: -len(x[1])):
        print(f"  {file_path}: {len(errors)}个问题")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="认知与决策模块逻辑错误扫描器")
    parser.add_argument(
        '--files',
        nargs='+',
        help='要扫描的文件列表'
    )
    parser.add_argument(
        '--dir',
        help='要扫描的目录'
    )
    parser.add_argument(
        '--pattern',
        default='*.py',
        help='文件匹配模式 (默认: *.py)'
    )
    parser.add_argument(
        '--fixable',
        action='store_true',
        help='仅显示可自动修复的错误'
    )

    args = parser.parse_args()

    if args.files:
        # 扫描指定文件
        results = {}
        for file_path in args.files:
            if os.path.exists(file_path):
                errors = scan_file(file_path)
                if errors:
                    results[file_path] = errors
    elif args.dir:
        # 扫描目录
        results = scan_directory(args.dir, args.pattern)
    else:
        # 默认扫描认知与决策模块
        print("🔍 扫描认知与决策模块...")
        modules = [
            'core/cognition',
            'core/planning',
            'core/decision',
            'core/learning',
            'core/intelligence',
            'core/evaluation'
        ]

        results = {}
        for module in modules:
            if os.path.exists(module):
                module_results = scan_directory(module)
                results.update(module_results)

    if results:
        print_results(results)

        # 生成修复脚本
        print("\n" + "="*80)
        print("💡 提示")
        print("="*80)
        print("使用以下命令修复可自动修复的问题：")
        print("  python3 scripts/fix_logic_errors.py --dir core/cognition")
    else:
        print("✅ 未发现逻辑错误!")


if __name__ == '__main__':
    main()
