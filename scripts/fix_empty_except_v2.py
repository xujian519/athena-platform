#!/usr/bin/env python3
"""
批量修复空except块 - 改进版
使用正则表达式识别和修复空except块
"""

import os
import re
from pathlib import Path
from typing import List, Tuple, Dict


def find_empty_except_blocks(file_path: Path) -> List[Dict]:
    """
    查找文件中的空except块

    返回: [{'line': 行号, 'exception_type': 异常类型, 'full_except': 完整except语句}]
    """
    issues = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        i = 0
        while i < len(lines):
            line = lines[i]

            # 检查是否是except行
            except_match = re.match(r'^(\s*)except\s+([^:]+):', line)
            if except_match:
                # 检查下一行或几行是否是pass或...或注释
                j = i + 1
                is_empty = True

                # 跳过空行和注释
                while j < len(lines):
                    next_line = lines[j].strip()
                    if next_line == '':
                        j += 1
                        continue
                    elif next_line.startswith('#'):
                        # 如果只有注释，也算空except
                        j += 1
                        continue
                    elif next_line in ['pass', '...']:
                        # 找到空except
                        break
                    else:
                        # 有实际代码，不是空except
                        is_empty = False
                        break

                if is_empty and j < len(lines):
                    # 提取异常类型
                    exception_part = except_match.group(2).strip()

                    # 处理 "except Exception as e:" 的情况
                    exception_type = exception_part.split(' as ')[0].strip()

                    issues.append({
                        'line': i,  # 0-based
                        'exception_type': exception_type,
                        'full_except': line.strip(),
                        'indent': len(except_match.group(1))
                    })

            i += 1

    except Exception as e:
        print(f"读取文件失败 {file_path}: {e}")

    return issues


def generate_fix_code(exception_type: str, indent: int, has_logger: bool) -> str:
    """
    生成修复代码

    Args:
        exception_type: 异常类型
        indent: 缩进空格数
        has_logger: 是否已有logger

    Returns:
        修复代码行
    """
    indent_str = ' ' * (indent + 4)

    # 如果没有logger，使用print
    if not has_logger:
        if 'CancelledError' in exception_type or 'CancelError' in exception_type:
            return f'{indent_str}# 任务被取消，正常退出\n{indent_str}pass\n'
        elif 'ImportError' in exception_type or 'ModuleNotFoundError' in exception_type:
            return f'{indent_str}print(f"可选模块导入失败，使用降级方案: {{e}}")\n'
        else:
            return f'{indent_str}print(f"捕获{exception_type}异常: {{e}}")\n'
    else:
        # 有logger，使用logger
        if 'CancelledError' in exception_type or 'CancelError' in exception_type:
            return f'{indent_str}# 任务被取消，正常退出\n{indent_str}pass\n'
        elif 'ImportError' in exception_type or 'ModuleNotFoundError' in exception_type:
            return f'{indent_str}logger.warning(f"可选模块导入失败，使用降级方案: {{e}}")\n'
        elif 'ConnectionError' in exception_type or 'TimeoutError' in exception_type:
            return f'{indent_str}logger.warning(f"连接或超时错误: {{e}}")\n'
        elif exception_type in ['Exception', '']:
            return f'{indent_str}logger.error(f"捕获异常: {{e}}", exc_info=True)\n'
        else:
            return f'{indent_str}logger.error(f"捕获{exception_type}异常: {{e}}", exc_info=True)\n'


def check_has_logger(file_path: Path) -> bool:
    """检查文件是否已有logger"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return 'logger = ' in content or 'logging.getLogger' in content
    except:
        return False


def fix_file(file_path: Path) -> Tuple[bool, int]:
    """
    修复单个文件

    返回: (是否成功, 修复数量)
    """
    try:
        # 检查是否有logger
        has_logger = check_has_logger(file_path)

        # 如果没有logger，先添加
        if not has_logger:
            add_logger_to_file(file_path)
            has_logger = True

        # 读取文件
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # 查找空except块
        issues = find_empty_except_blocks(file_path)
        if not issues:
            return False, 0

        print(f"\n修复文件: {file_path.relative_to(file_path.parents[2])}")
        print(f"  发现 {len(issues)} 个空except块")

        # 从后往前修复（避免行号变化）
        for issue in sorted(issues, key=lambda x: x['line'], reverse=True):
            line_num = issue['line']
            exception_type = issue['exception_type']
            indent = issue['indent']

            print(f"  - 行 {line_num + 1}: {exception_type}")

            # 生成修复代码
            fix_code = generate_fix_code(exception_type, indent, has_logger)

            # 找到pass或...的位置
            j = line_num + 1
            while j < len(lines) and lines[j].strip() in ['', 'pass', '...']:
                j += 1

            # 替换pass行
            if j > line_num + 1:
                # 找到了pass或...
                for k in range(line_num + 1, j):
                    if lines[k].strip() in ['pass', '...']:
                        lines[k] = fix_code
                        break
            else:
                # 没找到，插入新行
                lines.insert(line_num + 1, fix_code)

        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"  ✓ 修复完成")
        return True, len(issues)

    except Exception as e:
        print(f"  ✗ 修复失败: {e}")
        import traceback
        traceback.print_exc()
        return False, 0


def add_logger_to_file(file_path: Path) -> bool:
    """向文件添加logger"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # 检查是否已有logging导入
        has_logging_import = any('import logging' in line for line in lines)

        # 找到导入部分的结束位置
        import_end = 0
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                import_end = i + 1
            elif import_end > 0 and not line.startswith('import ') and not line.startswith('from '):
                break

        if import_end > 0:
            # 添加logging导入（如果还没有）
            new_lines = []
            if not has_logging_import:
                # 获取最后一行import的缩进
                last_import_line = lines[import_end - 1]
                indent = len(last_import_line) - len(last_import_line.lstrip())
                indent_str = ' ' * indent if indent > 0 else ''
                new_lines.append(f'{indent_str}import logging\n')

            # 添加logger初始化
            last_import_line = lines[import_end - 1]
            indent = len(last_import_line) - len(last_import_line.lstrip())
            indent_str = ' ' * indent if indent > 0 else ''
            new_lines.append(f'{indent_str}logger = logging.getLogger(__name__)\n')

            # 插入到导入部分之后
            lines[import_end:import_end] = new_lines

            # 写回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)

            return True

    except Exception as e:
        print(f"    添加logger失败: {e}")

    return False


def main():
    """主函数"""
    # 项目根目录
    project_root = Path('/Users/xujian/Athena工作平台')

    # 只处理core目录
    target_dir = project_root / 'core'

    if not target_dir.exists():
        print(f"目录不存在: {target_dir}")
        return

    print("=" * 80)
    print("批量修复空except块 V2")
    print("=" * 80)
    print(f"目标目录: {target_dir}")
    print()

    # 查找所有Python文件
    python_files = list(target_dir.rglob('*.py'))

    # 排除一些目录
    exclude_dirs = {'__pycache__', '.pytest_cache', 'venv', '.tox'}
    python_files = [
        f for f in python_files
        if not any(exclude in f.parts for exclude in exclude_dirs)
    ]

    print(f"找到 {len(python_files)} 个Python文件")
    print()

    # 统计
    fixed_count = 0
    total_issues = 0
    failed_files = []

    # 修复每个文件
    for file_path in python_files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # 快速检查是否有空except
            if re.search(r'except\s+.*:\s*(pass|\.\.\.)', content):
                success, count = fix_file(file_path)
                if success:
                    fixed_count += 1
                    total_issues += count
                elif count > 0:
                    failed_files.append(file_path)
        except Exception as e:
            print(f"处理文件失败 {file_path}: {e}")

    # 输出总结
    print()
    print("=" * 80)
    print("修复总结")
    print("=" * 80)
    print(f"扫描文件: {len(python_files)}")
    print(f"修复文件: {fixed_count}")
    print(f"空except块总数: {total_issues}")
    if failed_files:
        print(f"失败文件: {len(failed_files)}")
        for f in failed_files:
            print(f"  - {f}")
    print("=" * 80)


if __name__ == '__main__':
    main()
