#!/usr/bin/env python3
"""
修复所有MD5相关的括号问题
"""

import re
from pathlib import Path


def fix_all_parentheses(file_path):
    """修复文件中的所有括号问题"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        fixes = 0

        # 模式1: hashlib.md5(..., usedforsecurity=False).hexdigest() -> hashlib.md5(..., usedforsecurity=False).hexdigest()
        pattern1 = r'hashlib\.md5\([^)]+\, usedforsecurity=False\)\)\.hexdigest\(\)'
        matches1 = list(re.finditer(pattern1, content))
        for match in reversed(matches1):
            fixes += 1
            old = match.group()
            new = old.replace('usedforsecurity=False)).hexdigest()', 'usedforsecurity=False).hexdigest()')
            content = content[:match.start()] + new + content[match.end():]

        # 模式2: hashlib.md5(..., usedforsecurity=False).hexdigest()[:8] -> hashlib.md5(..., usedforsecurity=False).hexdigest()[:8]
        pattern2 = r'hashlib\.md5\([^)]+\, usedforsecurity=False\)\)\.hexdigest\(\)\[:'
        matches2 = list(re.finditer(pattern2, content))
        for match in reversed(matches2):
            fixes += 1
            old = match.group()
            new = old.replace('usedforsecurity=False)).hexdigest()[:', 'usedforsecurity=False).hexdigest()[:')
            content = content[:match.start()] + new + content[match.end():]

        # 模式3: hash_obj = hashlib.md5(..., usedforsecurity=False) -> hash_obj = hashlib.md5(..., usedforsecurity=False)
        pattern3 = r'(hash(?:_obj|_object)?\s*=\s*hashlib\.md5\([^)]+\, usedforsecurity=False)\)\)'
        matches3 = list(re.finditer(pattern3, content))
        for match in reversed(matches3):
            fixes += 1
            old = match.group()
            # 只删除最后的 ))
            new = old[:-1]
            content = content[:match.start()] + new + content[match.end():]

        # 模式4: hashlib.md5(..., usedforsecurity=False)} -> hashlib.md5(..., usedforsecurity=False)}
        pattern4 = r'hashlib\.md5\([^)]+\, usedforsecurity=False\)\)\}'
        matches4 = list(re.finditer(pattern4, content))
        for match in reversed(matches4):
            fixes += 1
            old = match.group()
            new = old.replace('usedforsecurity=False))}', 'usedforsecurity=False)}')
            content = content[:match.start()] + new + content[match.end():]

        # 模式5: hashlib.md5(..., usedforsecurity=False), -> hashlib.md5(..., usedforsecurity=False),
        pattern5 = r'hashlib\.md5\([^)]+\, usedforsecurity=False\)\)\,'
        matches5 = list(re.finditer(pattern5, content))
        for match in reversed(matches5):
            fixes += 1
            old = match.group()
            new = old.replace('usedforsecurity=False)),', 'usedforsecurity=False),')
            content = content[:match.start()] + new + content[match.end():]

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

    parser = argparse.ArgumentParser(description='修复所有MD5括号问题')
    parser.add_argument('--directory', default='.', help='扫描目录')

    args = parser.parse_args()

    print("🔧 修复所有MD5括号问题")
    print("=" * 80)
    print(f"扫描目录: {args.directory}")
    print()

    # 扫描Python文件
    py_files = list(Path(args.directory).rglob("*.py"))

    # 查找包含错误的文件
    error_files = []
    error_pattern = re.compile(r'usedforsecurity=False\)\)')

    for py_file in py_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if error_pattern.search(content):
                    error_files.append(py_file)
        except Exception:
            pass

    print(f"找到 {len(error_files)} 个文件包含括号问题\n")

    if not error_files:
        print("✅ 未发现括号问题")
        return

    # 显示文件列表
    for i, file_path in enumerate(error_files[:20], 1):
        print(f"{i}. {file_path}")
    if len(error_files) > 20:
        print(f"... 还有 {len(error_files) - 20} 个文件")

    # 实际修复
    print("\n" + "=" * 80)
    print("开始修复...")
    print("=" * 80 + "\n")

    fixed_files = 0
    total_fixes = 0

    for file_path in error_files:
        fixes = fix_all_parentheses(file_path)
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
