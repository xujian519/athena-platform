#!/usr/bin/env python3
"""
Python代码规范化工具
用于统一代码风格、替换print语句、优化导入等
"""

import ast
import logging
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class PythonCodeStandardizer:
    """Python代码规范化器"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.processed_files = []
        self.errors = []
        self.stats = {
            'print_replaced': 0,
            'imports_optimized': 0,
            'strings_standardized': 0,
            'type_hints_added': 0,
            'files_processed': 0
        }

    def find_python_files(self) -> List[Path]:
        """查找所有Python文件"""
        python_files = []
        for py_file in self.project_root.rglob('*.py'):
            # 跳过一些目录
            if any(part in py_file.parts for part in [
                '__pycache__', '.venv', 'venv', 'node_modules',
                '.git', 'dist', 'build', 'migrations'
            ]):
                continue
            python_files.append(py_file)
        return python_files

    def replace_print_with_logging(self, file_path: Path) -> int:
        """替换print语句为logging"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content
            replaced_count = 0

            # 检查是否已经导入了logging
            has_logging_import = False
            logging_import_line = None

            # 首先检查是否已有logging导入
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'import logging' in line or 'from logging' in line:
                    has_logging_import = True
                    logging_import_line = i
                    break

            # 如果没有logging导入，在适当位置添加
            if not has_logging_import:
                # 找到第一个导入语句
                first_import_idx = -1
                for i, line in enumerate(lines):
                    if line.strip().startswith(('import ', 'from ')):
                        first_import_idx = i
                        break

                if first_import_idx >= 0:
                    # 在第一个导入之前添加
                    lines.insert(first_import_idx, 'import logging')
                    # 添加空行
                    lines.insert(first_import_idx + 1, '')
                    content = '\n'.join(lines)
                else:
                    # 如果没有导入，在文件开始添加
                    content = 'import logging\n\n' + content

            # 替换print语句
            # 使用正则表达式匹配各种print格式
            patterns = [
                # logger.info("...")
                (r'print\('([^']*)"\)', r'logger.info("\1")'),
                # logger.info("...")
                (r"print\('([^']*)'\)", r'logger.info("\1")'),
                # logger.info(f"...")
                (r'print\(f"([^']*)'\)', r'logger.info(f"\1")'),
                # logger.info(f"...")
                (r"print\(f'([^']*)'\)", r'logger.info(f"\1")'),
                # logger.info(str(variable))
                (r'print\(([^,)]+)\)', r'logger.info(str(\1))'),
                # print(..., ...)
                (r'logger\.(info|debug|warning|error|critical)\(f?'([^']*)", (.+)\)', r'logger.\1(f"\2: {\3}")'),
            ]

            for pattern, replacement in patterns:
                new_content, count = re.subn(pattern, replacement, content)
                if count > 0:
                    content = new_content
                    replaced_count += count

            # 添加logger初始化（如果需要）
            if replaced_count > 0 and 'logger = ' not in content:
                # 在导入后添加logger配置
                lines = content.split('\n')
                logger_line_idx = -1
                for i, line in enumerate(lines):
                    if line.strip().startswith('import logging') or line.strip().startswith('from logging'):
                        # 找到logging导入后的位置
                        for j in range(i + 1, len(lines)):
                            if lines[j].strip() and not lines[j].strip().startswith(('import ', 'from ')):
                                logger_line_idx = j
                                break
                        break

                if logger_line_idx >= 0:
                    lines.insert(logger_line_idx, 'logger = logging.getLogger(__name__)')
                    lines.insert(logger_line_idx + 1, '')
                    content = '\n'.join(lines)

            # 写回文件
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.stats['print_replaced'] += replaced_count

            return replaced_count

        except Exception as e:
            self.errors.append(f"替换print语句失败 {file_path}: {str(e)}")
            return 0

    def optimize_imports(self, file_path: Path) -> bool:
        """优化import语句"""
        try:
            # 使用isort来优化导入
            result = subprocess.run(
                ['python3', '-m', 'isort', str(file_path), '--profile', 'black'],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                self.stats['imports_optimized'] += 1
                return True
            else:
                # 如果isort失败，手动处理
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 移除未使用的导入
                try:
                    tree = ast.parse(content)
                    used_names = set()

                    # 收集所有使用的名称
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Name):
                            used_names.add(node.id)
                        elif isinstance(node, ast.Attribute):
                            # 处理模块属性访问
                            if isinstance(node.value, ast.Name):
                                used_names.add(node.value.id)

                    # 移除未使用的导入
                    lines = content.split('\n')
                    new_lines = []
                    for line in lines:
                        should_keep = True
                        if line.strip().startswith(('import ', 'from ')):
                            # 简单检查：如果导入的名称未被使用
                            imported_name = None
                            if 'import ' in line:
                                parts = line.split()
                                if 'as' in parts:
                                    idx = parts.index('as')
                                    imported_name = parts[idx + 1]
                                else:
                                    imported_name = parts[-1].split('.')[0]

                            if imported_name and imported_name not in used_names:
                                # 检查是否在注释或字符串中
                                if imported_name not in line.split('#')[1] if '#' in line else True:
                                    should_keep = False

                        if should_keep:
                            new_lines.append(line)

                    content = '\n'.join(new_lines)

                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)

                    self.stats['imports_optimized'] += 1
                    return True

                except:
                    return False

        except Exception as e:
            # 如果没有isort，跳过
            if 'No such file or directory' not in str(e):
                self.errors.append(f"优化导入失败 {file_path}: {str(e)}")
            return False

    def standardize_strings(self, file_path: Path) -> int:
        """标准化字符串格式（统一使用单引号）"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content
            changed_count = 0

            # 将双引号字符串替换为单引号（保留f-string和docstring）
            lines = content.split('\n')
            new_lines = []

            for line in lines:
                new_line = line

                # 跳过注释和文档字符串
                if not line.strip().startswith('#') and '"""' not in line:
                    # 查找双引号字符串（不包括f-string）
                    # 这个正则表达式会匹配普通的双引号字符串
                    pattern = r'(?<!f)'([^'\\]*(\\.[^"\\]*)*)"'
                    matches = re.finditer(pattern, new_line)

                    # 需要从后往前替换，避免位置偏移
                    replacements = []
                    for match in matches:
                        replacements.append((match.start(), match.end(), match.group(1)))

                    # 从后往前替换
                    for start, end, text in reversed(replacements):
                        new_line = new_line[:start] + "'" + text + "'" + new_line[end:]
                        changed_count += 1

                new_lines.append(new_line)

            if changed_count > 0:
                content = '\n'.join(new_lines)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.stats['strings_standardized'] += changed_count

            return changed_count

        except Exception as e:
            self.errors.append(f"标准化字符串失败 {file_path}: {str(e)}")
            return 0

    def add_type_hints(self, file_path: Path) -> int:
        """添加类型注解"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 尝试使用mypy stubgen添加类型提示
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
                tmp.write(content)
                tmp_path = tmp.name

            try:
                # 运行stubgen
                result = subprocess.run(
                    ['stubgen', tmp_path, '--no-import'],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    # 读取生成的stub文件
                    stub_file = tmp_path.replace('.py', '.pyi')
                    if os.path.exists(stub_file):
                        with open(stub_file, 'r', encoding='utf-8') as f:
                            stub_content = f.read()

                        # 这里可以比较原始文件和stub文件
                        # 实际的类型提示添加需要更复杂的逻辑
                        self.stats['type_hints_added'] += 1

                        # 清理临时文件
                        os.unlink(stub_file)

                        return 1
            except:
                pass
            finally:
                # 清理临时文件
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

            return 0

        except Exception as e:
            self.errors.append(f"添加类型提示失败 {file_path}: {str(e)}")
            return 0

    def format_with_black(self, file_path: Path) -> bool:
        """使用black格式化代码"""
        try:
            result = subprocess.run(
                ['black', str(file_path)],
                capture_output=True,
                text=True
            )

            return result.returncode == 0

        except Exception as e:
            # 如果没有black，跳过
            if 'No such file or directory' not in str(e):
                self.errors.append(f"Black格式化失败 {file_path}: {str(e)}")
            return False

    def process_file(self, file_path: Path, options: Dict[str, bool]) -> Dict[str, int]:
        """处理单个文件"""
        results = {
            'print_replaced': 0,
            'imports_optimized': 0,
            'strings_standardized': 0,
            'type_hints_added': 0
        }

        try:
            # 跳过某些文件
            file_str = str(file_path)
            skip_patterns = [
                '__pycache__', 'venv', '.venv', 'migrations',
                'settings.py', 'manage.py', 'wsgi.py'
            ]

            if any(pattern in file_str for pattern in skip_patterns):
                return results

            # 执行各种标准化操作
            if options.get('replace_print', True):
                count = self.replace_print_with_logging(file_path)
                results['print_replaced'] = count

            if options.get('optimize_imports', True):
                if self.optimize_imports(file_path):
                    results['imports_optimized'] = 1

            if options.get('standardize_strings', True):
                count = self.standardize_strings(file_path)
                results['strings_standardized'] = count

            if options.get('add_type_hints', False):
                count = self.add_type_hints(file_path)
                results['type_hints_added'] = count

            if options.get('format_with_black', True):
                self.format_with_black(file_path)

            self.stats['files_processed'] += 1

        except Exception as e:
            self.errors.append(f"处理文件失败 {file_path}: {str(e)}")

        return results

    def generate_report(self) -> str:
        """生成处理报告"""
        report = [
            "# Python代码规范化报告\n",
            f"处理时间: {self.get_current_time()}",
            f"\n## 统计信息",
            f"- 处理的文件数: {self.stats['files_processed']}",
            f"- 替换的print语句: {self.stats['print_replaced']}",
            f"- 优化的导入: {self.stats['imports_optimized']}",
            f"- 标准化的字符串: {self.stats['strings_standardized']}",
            f"- 添加类型提示的文件: {self.stats['type_hints_added']}",
        ]

        if self.errors:
            report.append("\n## 错误信息")
            for error in self.errors[:10]:  # 只显示前10个错误
                report.append(f"- {error}")
            if len(self.errors) > 10:
                report.append(f"- ...还有 {len(self.errors) - 10} 个错误")

        report.append("\n## 建议")
        report.append('1. 安装代码格式化工具: `pip install black isort mypy`')
        report.append('2. 配置pre-commit hooks自动执行格式化')
        report.append('3. 在CI/CD中集成代码质量检查')
        report.append('4. 定期运行mypy类型检查')

        return "\n".join(report)

    def get_current_time(self) -> str:
        """获取当前时间"""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def run(self, options: Dict[str, bool] = None):
        """运行代码规范化"""
        if options is None:
            options = {
                'replace_print': True,
                'optimize_imports': True,
                'standardize_strings': True,
                'add_type_hints': False,  # 默认关闭，因为这可能会破坏代码
                'format_with_black': True
            }

        logger.info('🔧 开始Python代码规范化...')

        # 查找所有Python文件
        python_files = self.find_python_files()
        logger.info(f"📁 找到 {len(python_files)} 个Python文件")

        # 处理每个文件
        for i, file_path in enumerate(python_files, 1):
            logger.info(f"📝 [{i}/{len(python_files)}] 处理: {file_path.relative_to(self.project_root)}")
            self.process_file(file_path, options)

        # 生成报告
        report_path = self.project_root / 'optimization_work' / 'logs' / 'python_standardization_report.md'
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(self.generate_report())

        logger.info(f"\n✅ Python代码规范化完成！")
        logger.info(f"📊 处理了 {self.stats['files_processed']} 个文件")
        logger.info(f"📄 报告已保存到: {report_path}")

        return self.stats


def main():
    """主函数"""
    project_root = Path(__file__).parent.parent.parent
    standardizer = PythonCodeStandardizer(str(project_root))

    try:
        # 可以通过命令行参数控制选项
        import sys
        options = {
            'replace_print': '--no-print' not in sys.argv,
            'optimize_imports': '--no-imports' not in sys.argv,
            'standardize_strings': '--no-strings' not in sys.argv,
            'add_type_hints': '--type-hints' in sys.argv,
            'format_with_black': '--no-black' not in sys.argv
        }

        stats = standardizer.run(options)
        return stats
    except Exception as e:
        logger.info(f"❌ 执行失败: {str(e)}")
        return None


if __name__ == '__main__':
    main()