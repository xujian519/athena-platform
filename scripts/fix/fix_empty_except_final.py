#!/usr/bin/env python3
"""
最终版：批量修复所有空except块
处理各种特殊情况
"""

import re
from pathlib import Path


def fix_file_smart(file_path: Path) -> tuple[bool, int]:
    """
    智能修复单个文件中的所有空except块

    返回: (是否成功, 修复数量)
    """
    try:
        with open(file_path, encoding='utf-8') as f:
            content = f.read()

        # 检查是否有空except块
        if not re.search(r'except\s+.*:\s*(pass|\.\.\.)\s*(#.*)?$', content, re.MULTILINE):
            return False, 0

        # 检查是否有logger
        has_logger = 'logger = ' in content or 'logging.getLogger' in content

        # 如果没有logger，添加
        if not has_logger:
            content = add_logger_to_content(content)

        # 逐行处理
        lines = content.splitlines(keepends=True)
        fixed_count = 0
        i = 0

        while i < len(lines):
            line = lines[i]

            # 检查是否是except行
            if re.match(r'^\s*except\s+', line):
                # 检查下一行是否是pass或...
                if i + 1 < len(lines):
                    next_line = lines[i + 1]

                    # 检查是否是空的except块
                    if re.match(r'^\s*(pass|\.\.\.)\s*(#.*)?$', next_line):
                        # 提取异常类型
                        except_match = re.search(r'except\s+([\w.\s(),]+):', line)
                        if except_match:
                            exception_type = except_match.group(1).strip()
                            # 处理 "Exception as e" 的情况
                            exception_type = exception_type.split(' as ')[0].strip()

                            # 获取缩进
                            indent = len(line) - len(line.lstrip())
                            indent_str = ' ' * (indent + 4)

                            # 生成修复代码
                            fix_code = generate_smart_fix(exception_type, indent_str, has_logger)

                            # 替换pass行
                            lines[i + 1] = fix_code
                            fixed_count += 1

            i += 1

        if fixed_count > 0:
            # 写回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            return True, fixed_count

        return False, 0

    except Exception as e:
        print(f"  ✗ 修复失败: {e}")
        return False, 0


def add_logger_to_content(content: str) -> str:
    """向内容添加logger"""
    lines = content.splitlines(keepends=True)

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
        new_lines = []

        # 添加logging导入（如果还没有）
        if not has_logging_import:
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

        return ''.join(lines)

    return content


def generate_smart_fix(exception_type: str, indent: str, has_logger: bool) -> str:
    """生成智能修复代码"""

    # 如果没有logger，使用print
    if not has_logger:
        if 'CancelledError' in exception_type or 'CancelError' in exception_type:
            return f'{indent}# 任务被取消，正常退出\n{indent}pass\n'
        elif 'ImportError' in exception_type or 'ModuleNotFoundError' in exception_type:
            return f'{indent}print(f"可选模块导入失败，使用降级方案: {{e}}")\n'
        else:
            return f'{indent}print(f"捕获{exception_type}异常: {{e}}")\n'
    else:
        # 有logger，使用logger
        if 'CancelledError' in exception_type or 'CancelError' in exception_type:
            return f'{indent}# 任务被取消，正常退出\n{indent}pass\n'
        elif 'ImportError' in exception_type or 'ModuleNotFoundError' in exception_type:
            return f'{indent}logger.warning(f"可选模块导入失败，使用降级方案: {{e}}")\n'
        elif 'ConnectionError' in exception_type or 'TimeoutError' in exception_type:
            return f'{indent}logger.warning(f"连接或超时错误: {{e}}")\n'
        elif exception_type in ['Exception', '']:
            return f'{indent}logger.error(f"捕获异常: {{e}}", exc_info=True)\n'
        else:
            return f'{indent}logger.error(f"捕获{exception_type}异常: {{e}}", exc_info=True)\n'


def main():
    """主函数"""
    project_root = Path('/Users/xujian/Athena工作平台')
    target_dir = project_root / 'core'

    if not target_dir.exists():
        print(f"目录不存在: {target_dir}")
        return

    print("=" * 80)
    print("最终版：批量修复空except块")
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

    # 修复每个文件
    for file_path in python_files:
        try:
            success, count = fix_file_smart(file_path)
            if success:
                print(f"✓ {file_path.relative_to(project_root)}: 修复 {count} 个空except块")
                fixed_count += 1
                total_issues += count
        except Exception as e:
            print(f"✗ {file_path.relative_to(project_root)}: {e}")

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
