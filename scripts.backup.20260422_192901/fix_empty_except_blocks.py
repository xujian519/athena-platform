#!/usr/bin/env python3
"""
修复空except块脚本
Fix Empty Except Blocks Script

系统性地修复项目中的所有空except块，添加适当的错误处理和日志记录。
"""

import ast
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EmptyExceptFixer:
    """空except块修复器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.fixed_files: List[Path] = []
        self.error_files: List[Tuple[Path, str]] = []

        # 需要排除的目录
        self.exclude_dirs = {
            'venv', '__pycache__', '.git', 'node_modules',
            'backup', 'archive', '.pytest_cache', 'dist', 'build'
        }

        # 需要排除的文件模式
        self.exclude_patterns = {
            '*.pyc', '*.pyo', '*.pyd', '__init__.py'
        }

    def should_exclude(self, path: Path) -> bool:
        """检查是否应该排除该文件"""
        # 检查目录
        for part in path.parts:
            if part in self.exclude_dirs:
                return True

        # 检查文件模式
        for pattern in self.exclude_patterns:
            if path.match(pattern):
                return True

        return False

    def find_python_files(self) -> List[Path]:
        """查找所有Python文件"""
        python_files = []
        for root, dirs, files in os.walk(self.project_root):
            # 排除特定目录
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]

            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    if not self.should_exclude(file_path):
                        python_files.append(file_path)

        return python_files

    def check_empty_except(self, source_code: str) -> List[Dict]:
        """检查代码中的空except块"""
        issues = []

        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return issues

        class EmptyExceptVisitor(ast.NodeVisitor):
            def __init__(self):
                self.issues = []

            def visit_ExceptHandler(self, node):
                # 检查except块体是否为空或只有pass
                if node.body:
                    # 检查是否只有pass或...
                    is_empty = True
                    for stmt in node.body:
                        if isinstance(stmt, ast.Pass):
                            continue
                        elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
                            if stmt.value.value == ...:
                                continue
                        is_empty = False
                        break

                    if is_empty:
                        line = node.lineno
                        col = node.col_offset
                        exception_type = "Unknown"
                        if node.type:
                            if isinstance(node.type, ast.Name):
                                exception_type = node.type.id
                            elif isinstance(node.type, ast.Attribute):
                                exception_type = node.type.attr

                        self.issues.append({
                            'line': line,
                            'col': col,
                            'exception_type': exception_type,
                            'has_name': node.name is not None
                        })

                self.generic_visit(node)

        visitor = EmptyExceptVisitor()
        visitor.visit(tree)
        return visitor.issues

    def fix_file(self, file_path: Path) -> bool:
        """修复单个文件"""
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
                original_lines = source_code.splitlines(keepends=True)

            # 检查空except块
            issues = self.check_empty_except(source_code)
            if not issues:
                return False

            logger.info(f"发现空except块: {file_path} ({len(issues)}个)")

            # 获取模块logger名称
            logger_name = self._get_logger_name(file_path)

            # 构建修复后的代码
            fixed_lines = original_lines.copy()
            line_offset = 0

            for issue in sorted(issues, key=lambda x: x['line'], reverse=True):
                line_num = issue['line'] - 1  # 转换为0-index
                exception_type = issue['exception_type']

                # 找到except块的结束位置
                indent = len(original_lines[line_num]) - len(original_lines[line_num].lstrip())

                # 构建修复代码
                fix_code = self._generate_fix_code(
                    exception_type,
                    indent,
                    logger_name,
                    issue['has_name']
                )

                # 替换pass或...行
                if line_num + 1 < len(fixed_lines):
                    if 'pass' in fixed_lines[line_num + 1] or '...' in fixed_lines[line_num + 1]:
                        fixed_lines[line_num + 1] = fix_code
                    else:
                        # 如果下一行不是pass，插入新行
                        fixed_lines.insert(line_num + 1, fix_code)

            # 写回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(fixed_lines)

            self.fixed_files.append(file_path)
            return True

        except Exception as e:
            self.error_files.append((file_path, str(e)))
            logger.error(f"修复文件失败 {file_path}: {e}")
            return False

    def _get_logger_name(self, file_path: Path) -> str:
        """获取模块的logger名称"""
        rel_path = file_path.relative_to(self.project_root)
        parts = list(rel_path.parts[:-1]) + [rel_path.stem]
        return '.'.join(parts)

    def _generate_fix_code(
        self,
        exception_type: str,
        indent: int,
        logger_name: str,
        has_name: bool
    ) -> str:
        """生成修复代码"""

        indent_str = ' ' * (indent + 4)

        if exception_type == 'asyncio.CancelledError':
            # 对于CancelledError，通常只需要记录日志
            return f'{indent_str}# 任务被取消，正常退出\n'
        elif exception_type in ['ImportError', 'ModuleNotFoundError']:
            # 对于导入错误，提供降级方案
            return f'{indent_str}logger.warning(f"可选模块导入失败，使用降级方案: {{e}}")\n'
        else:
            # 通用错误处理
            if has_name:
                return f'{indent_str}logger.error(f"捕获异常: {{e}}", exc_info=True)\n'
            else:
                return f'{indent_str}logger.error(f"捕获{exception_type}异常", exc_info=True)\n'

    def fix_all(self) -> Dict:
        """修复所有文件"""
        logger.info(f"开始扫描项目: {self.project_root}")

        python_files = self.find_python_files()
        logger.info(f"找到 {len(python_files)} 个Python文件")

        fixed_count = 0
        for file_path in python_files:
            try:
                if self.fix_file(file_path):
                    fixed_count += 1
            except Exception as e:
                logger.error(f"处理文件失败 {file_path}: {e}")

        return {
            'total_files': len(python_files),
            'fixed_files': fixed_count,
            'error_files': len(self.error_files),
            'fixed_file_list': self.fixed_files,
            'error_file_list': self.error_files
        }

    def generate_report(self, results: Dict) -> str:
        """生成修复报告"""
        report = []
        report.append("=" * 80)
        report.append("空except块修复报告")
        report.append("=" * 80)
        report.append(f"扫描文件总数: {results['total_files']}")
        report.append(f"修复文件数量: {results['fixed_files']}")
        report.append(f"错误文件数量: {results['error_files']}")
        report.append("")

        if results['fixed_files'] > 0:
            report.append("已修复的文件:")
            for file_path in results['fixed_file_list']:
                rel_path = file_path.relative_to(self.project_root)
                report.append(f"  ✓ {rel_path}")
            report.append("")

        if results['error_files'] > 0:
            report.append("修复失败的文件:")
            for file_path, error in results['error_file_list']:
                rel_path = file_path.relative_to(self.project_root)
                report.append(f"  ✗ {rel_path}: {error}")
            report.append("")

        report.append("=" * 80)

        return "\n".join(report)


def main():
    """主函数"""
    # 获取项目根目录
    project_root = Path(__file__).parent.parent

    logger.info(f"项目根目录: {project_root}")

    # 创建修复器
    fixer = EmptyExceptFixer(project_root)

    # 执行修复
    results = fixer.fix_all()

    # 生成报告
    report = fixer.generate_report(results)
    print(report)

    # 保存报告
    report_path = project_root / 'fix_empty_except_blocks_report.txt'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    logger.info(f"报告已保存到: {report_path}")


if __name__ == '__main__':
    main()
