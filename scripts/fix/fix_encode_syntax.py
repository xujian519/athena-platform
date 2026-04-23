#!/usr/bin/env python3
"""
修复MD5脚本引入的语法错误
将 .encode(, usedforsecurity=False 修复为 .encode(), usedforsecurity=False
"""

import re
from pathlib import Path


def fix_encode_syntax(file_path):
    """修复文件中的encode语法错误"""
    try:
        with open(file_path, encoding='utf-8') as f:
            content = f.read()

        fixes = 0

        # 修复 .encode(, usedforsecurity=False
        pattern = r'\.encode\(\s*,\s*usedforsecurity=False'
        matches = list(re.finditer(pattern, content))

        for match in reversed(matches):  # 从后向前替换，避免位置偏移
            fixes += 1
            start = match.start()
            end = match.end()
            # 替换为 .encode(), usedforsecurity=False
            content = content[:start] + '.encode(), usedforsecurity=False' + content[end:]

        if fixes > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return fixes

        return 0

    except Exception as e:
        print(f"❌ 修复文件失败 {file_path}: {e}")
        return 0


def main():
    import argparse

    parser = argparse.ArgumentParser(description='修复encode语法错误')
    parser.add_argument('--directory', default='core', help='扫描目录')
    parser.add_argument('--dry-run', action='store_true', help='预览模式')

    args = parser.parse_args()

    print("🔧 修复encode语法错误")
    print("=" * 80)
    print(f"扫描目录: {args.directory}")
    print()

    if args.dry_run:
        print("🔍 预览模式")
        print("=" * 80)

    # 扫描Python文件
    py_files = list(Path(args.directory).rglob("*.py"))

    # 查找包含错误的文件
    error_files = []
    for py_file in py_files:
        try:
            with open(py_file, encoding='utf-8') as f:
                content = f.read()
                if re.search(r'\.encode\(\s*,\s*usedforsecurity=False', content):
                    error_files.append(py_file)
        except Exception:
            pass

    print(f"找到 {len(error_files)} 个文件包含语法错误\n")

    if not error_files:
        print("✅ 未发现语法错误")
        return

    # 显示文件列表
    for i, file_path in enumerate(error_files, 1):
        print(f"{i}. {file_path}")

    if args.dry_run:
        print("\n💡 移除 --dry-run 参数进行实际修复")
        return

    # 实际修复
    print("\n" + "=" * 80)
    print("开始修复...")
    print("=" * 80 + "\n")

    fixed_files = 0
    total_fixes = 0

    for file_path in error_files:
        fixes = fix_encode_syntax(file_path)
        if fixes > 0:
            fixed_files += 1
            total_fixes += fixes
            print(f"✓ {file_path}: 修复 {fixes} 处")

    print("\n" + "=" * 80)
    print("修复总结")
    print("=" * 80)
    print(f"修复文件数: {fixed_files}")
    print(f"修复总数: {total_fixes}")
    print("=" * 80)


if __name__ == '__main__':
    main()
