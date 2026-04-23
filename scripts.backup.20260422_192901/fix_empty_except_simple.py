#!/usr/bin/env python3
"""
批量修复空except块
使用正则表达式识别和修复空except块
"""

import os
import re
from pathlib import Path
from typing import List, Tuple


def find_empty_except_blocks(file_path: Path) -> List[Tuple[int, str, str]]:
    """
    查找文件中的空except块

    返回: [(行号, except语句, 上下文)]
    """
    issues = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        i = 0
        while i < len(lines):
            line = lines[i]

            # 检查是否是except行
            if re.match(r'^\s*except\s+', line):
                # 检查下一行或几行是否是pass或...或注释
                j = i + 1
                is_empty = True
                empty_content = ""

                # 跳过空行
                while j < len(lines) and lines[j].strip() == '':
                    j += 1

                if j < len(lines):
                    next_line = lines[j].strip()
                    if next_line in ['pass', '...', '']:
                        is_empty = True
                        empty_content = next_line
                    elif next_line.startswith('#'):
                        # 如果只有注释，也算空except
                        is_empty = True
                        empty_content = next_line
                    else:
                        is_empty = False

                if is_empty:
                    # 获取上下文（前几行）
                    context_start = max(0, i - 2)
                    context = ''.join(lines[context_start:i+1])

                    issues.append((
                        i + 1,  # 行号（1-based）
                        line.strip(),
                        context
                    ))

            i += 1

    except Exception as e:
        print(f"读取文件失败 {file_path}: {e}")

    return issues


def fix_empty_except_block(
    lines: List[str],
    line_num: int,
    exception_type: str
) -> List[str]:
    """
    修复单个空except块

    Args:
        lines: 文件所有行
        line_num: except行号（0-based）
        exception_type: 异常类型

    Returns:
        修复后的行列表
    """
    # 找到except行的缩进
    except_line = lines[line_num]
    indent = len(except_line) - len(except_line.lstrip())
    indent_str = ' ' * (indent + 4)

    # 生成修复代码
    fix_code = generate_fix_code(except_type, indent_str)

    # 找到pass或...的位置
    j = line_num + 1
    while j < len(lines) and lines[j].strip() in ['', 'pass', '...', '# 只记录日志']:
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

    return lines


def generate_fix_code(exception_type: str, indent: str) -> str:
    """
    生成修复代码

    Args:
        exception_type: 异常类型
        indent: 缩进字符串

    Returns:
        修复代码行
    """
    # 根据异常类型生成不同的修复代码
    if 'CancelledError' in exception_type or 'CancelError' in exception_type:
        return f"{indent}# 任务被取消，正常退出\n"
    elif 'ImportError' in exception_type or 'ModuleNotFoundError' in exception_type:
        return f"{indent}logger.warning(f\"可选模块导入失败，使用降级方案: {{e}}\")\n"
    elif 'ConnectionError' in exception_type or 'TimeoutError' in exception_type:
        return f"{indent}logger.warning(f\"连接或超时错误: {{e}}\")\n"
    elif exception_type == 'Exception' or exception_type == '':
        return f"{indent}logger.error(f\"捕获异常: {{e}}\", exc_info=True)\n"
    else:
        return f"{indent}logger.error(f\"捕获{exception_type}异常: {{e}}\", exc_info=True)\n"


def fix_file(file_path: Path) -> bool:
    """修复单个文件"""
    try:
        # 检查是否已经有logger导入
        needs_logger = True
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'logger = ' in content or 'logging.getLogger' in content:
                needs_logger = False

        # 读取文件
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # 查找空except块
        issues = find_empty_except_blocks(file_path)
        if not issues:
            return False

        print(f"\n修复文件: {file_path.relative_to(file_path.parents[2])}")
        print(f"  发现 {len(issues)} 个空except块")

        # 如果需要logger，在导入部分添加
        if needs_logger:
            # 找到导入部分
            import_end = 0
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    import_end = i + 1
                elif import_end > 0 and not line.startswith('import ') and not line.startswith('from '):
                    break

            # 添加logging导入
            if import_end > 0 and 'import logging' not in ''.join(lines[:import_end]):
                indent = len(lines[import_end - 1]) - len(lines[import_end - 1].lstrip())
                indent_str = ' ' * indent if indent > 0 else ''
                lines.insert(import_end, f'{indent_str}import logging\n')

                # 添加logger初始化
                module_name = file_path.stem
                logger_line = f'{indent_str}logger = logging.getLogger(__name__)\n'
                lines.insert(import_end + 1, logger_line)

        # 从后往前修复（避免行号变化）
        for line_num, except_line, context in sorted(issues, key=lambda x: x[0], reverse=True):
            # 提取异常类型
            match = re.search(r'except\s+(\w+(?:\s+as\s+\w+)?)', except_line)
            if match:
                exception_type = match.group(1).split(' as ')[0]
                print(f"  - 行 {line_num + 1}: {exception_type}")

                lines = fix_empty_except_block(lines, line_num, exception_type)

        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"  ✓ 修复完成")
        return True

    except Exception as e:
        print(f"  ✗ 修复失败: {e}")
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
    print("批量修复空except块")
    print("=" * 80)
    print(f"目标目录: {target_dir}")
    print()

    # 查找所有Python文件
    python_files = list(target_dir.rglob('*.py'))

    # 排除一些目录
    exclude_dirs = {'__pycache__', '.pytest_cache', 'venv'}
    python_files = [
        f for f in python_files
        if not any(exclude in f.parts for exclude in exclude_dirs)
    ]

    print(f"找到 {len(python_files)} 个Python文件")
    print()

    # 统计
    fixed_count = 0
    total_issues = 0

    # 修复每个文件
    for file_path in python_files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # 快速检查是否有空except
            if re.search(r'except\s+.*:\s*(pass|\.\.\.)', content):
                issues = find_empty_except_blocks(file_path)
                if issues:
                    total_issues += len(issues)
                    if fix_file(file_path):
                        fixed_count += 1
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
    print("=" * 80)


if __name__ == '__main__':
    main()
