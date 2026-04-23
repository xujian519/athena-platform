#!/usr/bin/env python3
"""
MD5弱哈希算法修复工具
自动为非安全场景的MD5使用添加usedforsecurity=False参数
"""

import re
from pathlib import Path


def scan_md5_usage(directory):
    """扫描目录中的MD5使用"""
    md5_usage = []

    # 扫描Python文件
    for py_file in Path(directory).rglob("*.py"):
        try:
            with open(py_file, encoding='utf-8') as f:
                content = f.read()

            # 查找MD5使用模式
            patterns = [
                r'hashlib\.md5\([^)]+\)\.hexdigest\(\)',
                r'hashlib\.md5\([^)]+\)',
                r'md5\([^)]*\)',
            ]

            for pattern in patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    md5_usage.append({
                        'file': str(py_file),
                        'match': match.group(),
                        'line': content[:match.start()].count('\n') + 1
                    })

        except Exception as e:
            print(f"⚠️  扫描文件失败 {py_file}: {e}")

    return md5_usage

def fix_md5_usage(file_path, dry_run=True):
    """修复文件中的MD5使用"""
    try:
        with open(file_path, encoding='utf-8') as f:
            content = f.read()

        original_content = content
        fixes = 0

        # 修复模式1: hashlib.md5(content.encode('utf-8'), usedforsecurity=False).hexdigest()
        pattern1 = r'hashlib\.md5\(([^)]+)\)\.hexdigest\(\)'
        def replace1(match):
            nonlocal fixes
            fixes += 1
            args = match.group(1)
            # 检查是否已有usedforsecurity参数
            if 'usedforsecurity' in args:
                return match.group(0)
            # 添加usedforsecurity=False
            return f'hashlib.md5({args}, usedforsecurity=False).hexdigest()'

        content = re.sub(pattern1, replace1, content)

        # 修复模式2: hashlib.md5(data, usedforsecurity=False)
        pattern2 = r'hashlib\.md5\(([^)]+)\)(?!\.hexdigest\(\))'
        def replace2(match):
            nonlocal fixes
            fixes += 1
            args = match.group(1)
            if 'usedforsecurity' in args:
                return match.group(0)
            return f'hashlib.md5({args}, usedforsecurity=False)'

        content = re.sub(pattern2, replace2, content)

        if fixes > 0 and not dry_run:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

        return fixes, original_content != content

    except Exception as e:
        print(f"❌ 修复文件失败 {file_path}: {e}")
        return 0, False

def main():
    import argparse

    parser = argparse.ArgumentParser(description='扫描和修复MD5使用')
    parser.add_argument('--directory', default='.', help='扫描目录')
    parser.add_argument('--dry-run', action='store_true', help='预览模式，不实际修改')
    parser.add_argument('--actual', action='store_true', help='实际修复模式')
    parser.add_argument('--top', type=int, default=50, help='显示前N个结果')

    args = parser.parse_args()

    if args.actual:
        print("🔧 实际修复模式")
        print("=" * 80)
    else:
        print("🔍 预览模式")
        print("=" * 80)

    # 扫描MD5使用
    print(f"\n扫描目录: {args.directory}")
    print("\n正在扫描MD5使用...")
    md5_usage = scan_md5_usage(args.directory)

    print(f"\n找到 {len(md5_usage)} 处MD5使用")

    if not md5_usage:
        print("✅ 未发现需要修复的MD5使用")
        return

    # 显示结果
    print(f"\n显示前 {min(args.top, len(md5_usage))} 个结果:\n")

    for i, usage in enumerate(md5_usage[:args.top], 1):
        print(f"{i}. {usage['file']}:{usage['line']}")
        print(f"   {usage['match']}")
        print()

    if not args.actual:
        print("\n💡 使用 --actual 参数进行实际修复")
        return

    # 实际修复
    print("\n" + "=" * 80)
    print("开始修复...")
    print("=" * 80 + "\n")

    fixed_files = 0
    total_fixes = 0

    # 按文件分组
    files_to_fix = {}
    for usage in md5_usage:
        file_path = usage['file']
        if file_path not in files_to_fix:
            files_to_fix[file_path] = []
        files_to_fix[file_path].append(usage)

    for file_path, _usages in files_to_fix.items():
        fixes, changed = fix_md5_usage(file_path, dry_run=False)
        if changed:
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
