#!/usr/bin/env python3
"""
批量修复Python 3.12类型注解兼容性问题 v2

修复内容:
1. 修复错误的类型注解格式: `Type] = None` -> `Optional[Type] = None`
2. 确保所有使用Optional的文件都正确导入了Optional
"""

import re
import sys
from pathlib import Path

# 需要跳过的目录
SKIP_DIRS = {
    'venv', 'athena_env', '__pycache__', '.git', 'node_modules',
    'site-packages', '.bak', 'dist', 'build', '.pytest_cache',
    '.tox', '.eggs', '*.egg-info', '.mypy_cache', '.venv'
}

# 错误的模式1: Optional[Type] = None)  (带括号)
ERROR_PATTERN1 = re.compile(r':\s*([A-Z][a-zA-Z0-9_.]*)\]\s*=\s*None\)')

# 错误的模式2: Optional[Type] = None  (不带括号)
ERROR_PATTERN2 = re.compile(r':\s*([A-Z][a-zA-Z0-9_.]*)\]\s*=\sNone(?!\))')

# Optional使用模式(不包括已经有Optional的)
OPTIONAL_WITHOUT_WRAPPER = re.compile(r':\s*(?!Optional\[)([A-Z][a-zA-Z0-9_.\[\] ,]*)\s*=\s*None\)')

# Optional导入模式
OPTIONAL_PATTERN = re.compile(r':\s*Optional\[')
OPTIONAL_IMPORT_PATTERN = re.compile(r'from\s+typing\s+import.*\bOptional\b')


def should_skip_dir(path: Path) -> bool:
    """判断是否应该跳过该目录"""
    # 检查目录名
    if path.name in SKIP_DIRS:
        return True

    # 检查路径中的任何部分
    for part in path.parts:
        if part in SKIP_DIRS or part.startswith('.'):
            return True

    return False


def fix_typing_in_file(file_path: Path) -> tuple[bool, int, str]:
    """修复单个文件的类型注解问题

    返回: (是否修改, 修复数量, 详情)
    """
    try:
        with open(file_path, encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return False, 0, f"读取失败: {e}"

    original_content = content
    fixes = []
    fix_count = 0

    # 1. 修复错误的类型注解格式: Optional[Type] = None) -> Optional[Type] = None)
    def fix_error_pattern1(match):
        nonlocal fix_count
        error_text = match.group(0)
        type_name = match.group(1)
        # 避免修复已经是Optional的情况
        if 'Optional' in error_text:
            return error_text
        fixed_text = f': Optional[{type_name}] = None)'
        fix_count += 1
        fixes.append(f"修复: {error_text[:50]}... -> Optional[{type_name}] = None)")
        return fixed_text

    content = ERROR_PATTERN1.sub(fix_error_pattern1, content)

    # 2. 修复错误的类型注解格式: Optional[Type] = None -> Optional[Type] = None
    def fix_error_pattern2(match):
        nonlocal fix_count
        error_text = match.group(0)
        type_name = match.group(1)
        # 避免修复已经是Optional的情况
        if 'Optional' in error_text:
            return error_text
        fixed_text = f': Optional[{type_name}] = None'
        fix_count += 1
        fixes.append(f"修复: {error_text[:50]}... -> Optional[{type_name}] = None")
        return fixed_text

    content = ERROR_PATTERN2.sub(fix_error_pattern2, content)

    # 3. 检查是否需要添加Optional导入
    uses_optional = OPTIONAL_PATTERN.search(content) is not None
    has_optional_import = OPTIONAL_IMPORT_PATTERN.search(content) is not None

    if uses_optional and not has_optional_import:
        # 查找typing导入行
        typing_imports = []

        # 查找所有from typing import行
        for match in re.finditer(r'^from\s+typing\s+import\s+[^\n]+', content, re.MULTILINE):
            typing_imports.append(match)

        if typing_imports:
            # 在现有的typing导入中添加Optional
            last_import = typing_imports[-1]
            import_line = last_import.group(0)

            # 检查是否已经有Optional
            if 'Optional' not in import_line:
                # 在导入列表末尾添加Optional
                new_import_line = import_line.rstrip()
                if new_import_line.endswith(','):
                    new_import_line = f"{new_import_line} Optional"
                elif not new_import_line.endswith(')'):
                    new_import_line = f"{new_import_line}, Optional"
                else:
                    # 处理多行导入的情况
                    new_import_line = new_import_line[:-1] + ", Optional)"

                content = content[:last_import.start()] + new_import_line + '\n' + content[last_import.end():]
                fixes.append("添加Optional到现有导入")
        else:
            # 在文件开头添加新的typing导入
            # 查找第一个import语句或docstring结束
            lines = content.split('\n')
            insert_pos = 0

            # 跳过shebang和编码声明
            i = 0
            while i < len(lines):
                if lines[i].startswith('#!') or lines[i].startswith('# -*-') or lines[i].startswith('# coding:'):
                    i += 1
                    insert_pos = i + 1
                elif lines[i].startswith('"""') or lines[i].startswith("'''"):
                    # 跳过docstring
                    quote = lines[i][:3]
                    i += 1
                    while i < len(lines) and quote not in lines[i]:
                        i += 1
                    i += 1
                    insert_pos = i
                    break
                else:
                    break

            # 在insert_pos处插入
            lines.insert(insert_pos, "from typing import Optional")
            content = '\n'.join(lines)
            fixes.append("添加新的Optional导入")

    # 如果有修改,写回文件
    if content != original_content:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            detail = "; ".join(fixes) if fixes else "无修复"
            return True, fix_count, detail
        except Exception as e:
            return False, 0, f"写入失败: {e}"

    return False, 0, "无需修复"


def scan_and_fix(root_dir: Path, dry_run: bool = False) -> dict:
    """扫描并修复所有Python文件

    Args:
        root_dir: 根目录
        dry_run: 是否只扫描不修复

    Returns:
        统计信息字典
    """
    stats = {
        'total_files': 0,
        'fixed_files': 0,
        'skipped_files': 0,
        'error_files': 0,
        'total_fixes': 0,
        'fixed_files_list': [],
        'error_files_list': []
    }

    # 遍历所有Python文件
    for py_file in root_dir.rglob('*.py'):
        # 跳过特定目录
        if should_skip_dir(py_file.parent):
            continue

        stats['total_files'] += 1

        if not dry_run:
            modified, fix_count, detail = fix_typing_in_file(py_file)

            if modified:
                stats['fixed_files'] += 1
                stats['total_fixes'] += fix_count
                stats['fixed_files_list'].append({
                    'file': str(py_file.relative_to(root_dir)),
                    'fixes': fix_count,
                    'detail': detail
                })
                print(f"✅ 修复: {py_file.relative_to(root_dir)} ({fix_count}处)")
            elif '失败' in detail:
                stats['error_files'] += 1
                stats['error_files_list'].append({
                    'file': str(py_file.relative_to(root_dir)),
                    'error': detail
                })
                print(f"❌ 错误: {py_file.relative_to(root_dir)} - {detail}")
            else:
                stats['skipped_files'] += 1

    return stats


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='批量修复Python 3.12类型注解兼容性问题')
    parser.add_argument('--dry-run', action='store_true', help='只扫描不修复')
    parser.add_argument('--path', type=str, default='.', help='要扫描的目录路径')
    parser.add_argument('--verbose', '-v', action='store_true', help='显示详细信息')

    args = parser.parse_args()

    root_path = Path(args.path).resolve()

    if not root_path.exists():
        print(f"❌ 错误: 路径不存在: {root_path}")
        sys.exit(1)

    print(f"🔍 开始扫描: {root_path}")
    print(f"📋 模式: {'扫描模式 (不修改文件)' if args.dry_run else '修复模式 (将修改文件)'}")
    print("=" * 80)

    stats = scan_and_fix(root_path, dry_run=args.dry_run)

    print("=" * 80)
    print("📊 统计信息:")
    print(f"  - 总文件数: {stats['total_files']}")
    print(f"  - 修复文件: {stats['fixed_files']}")
    print(f"  - 跳过文件: {stats['skipped_files']}")
    print(f"  - 错误文件: {stats['error_files']}")
    print(f"  - 总修复数: {stats['total_fixes']}")

    if stats['fixed_files_list'] and args.verbose:
        print("\n📝 修复详情:")
        for item in stats['fixed_files_list'][:20]:  # 只显示前20个
            print(f"  {item['file']}: {item['detail']}")

        if len(stats['fixed_files_list']) > 20:
            print(f"  ... 还有 {len(stats['fixed_files_list']) - 20} 个文件")

    if stats['error_files_list']:
        print("\n❌ 错误详情:")
        for item in stats['error_files_list']:
            print(f"  {item['file']}: {item['error']}")

    print("\n✅ 完成!")


if __name__ == '__main__':
    main()
