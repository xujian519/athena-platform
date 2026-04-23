#!/usr/bin/env python3
"""
修复MD5修复脚本引入的多余右括号
将 usedforsecurity=False)).hexdigest() 修复为 usedforsecurity=False).hexdigest()
"""

import re
from pathlib import Path


def fix_extra_parentheses(file_path):
    """修复文件中的多余右括号"""
    try:
        with open(file_path, encoding='utf-8') as f:
            content = f.read()

        fixes = 0

        # 修复模式1: usedforsecurity=False)).hexdigest() -> usedforsecurity=False).hexdigest()
        pattern1 = r'usedforsecurity=False\)\)\.hexdigest\(\)'
        matches1 = list(re.finditer(pattern1, content))

        # 修复模式2: usedforsecurity=False)).hexdigest()[:8] -> usedforsecurity=False).hexdigest()[:8]
        pattern2 = r'usedforsecurity=False\)\)\.hexdigest\(\)\[:'
        matches2 = list(re.finditer(pattern2, content))

        # 修复模式3: usedforsecurity=False))} -> usedforsecurity=False)}
        pattern3 = r'usedforsecurity=False\)\)\}'
        matches3 = list(re.finditer(pattern3, content))

        # 修复模式4: usedforsecurity=False)), -> usedforsecurity=False),
        pattern4 = r'usedforsecurity=False\)\)\,'
        matches4 = list(re.finditer(pattern4, content))

        all_matches = [(m, 1) for m in matches1] + [(m, 2) for m in matches2] + [(m, 3) for m in matches3] + [(m, 4) for m in matches4]

        for match, pattern_type in sorted(all_matches, key=lambda x: x[0].start(), reverse=True):
            fixes += 1
            start = match.start()
            end = match.end()

            # 找到 usedforsecurity=False)) 的结束位置
            if pattern_type in [1, 2]:
                # usedforsecurity=False)).hexdigest() -> usedforsecurity=False).hexdigest()
                content = content[:start] + 'usedforsecurity=False).hexdigest()' + content[end:]
            elif pattern_type == 3:
                # usedforsecurity=False))} -> usedforsecurity=False)}
                content = content[:start] + 'usedforsecurity=False)}' + content[end:]
            elif pattern_type == 4:
                # usedforsecurity=False)), -> usedforsecurity=False),
                content = content[:start] + 'usedforsecurity=False),' + content[end:]

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

    parser = argparse.ArgumentParser(description='修复多余右括号')
    parser.add_argument('--directory', default='.', help='扫描目录')

    args = parser.parse_args()

    print("🔧 修复MD5多余右括号")
    print("=" * 80)
    print(f"扫描目录: {args.directory}")
    print()

    # 扫描Python文件
    py_files = list(Path(args.directory).rglob("*.py"))

    # 查找包含错误的文件
    error_files = []
    for py_file in py_files:
        try:
            with open(py_file, encoding='utf-8') as f:
                content = f.read()
                if re.search(r'usedforsecurity=False\)\)', content):
                    error_files.append(py_file)
        except Exception:
            pass

    print(f"找到 {len(error_files)} 个文件包含多余右括号\n")

    if not error_files:
        print("✅ 未发现多余右括号")
        return

    # 显示文件列表
    for i, file_path in enumerate(error_files, 1):
        print(f"{i}. {file_path}")

    # 实际修复
    print("\n" + "=" * 80)
    print("开始修复...")
    print("=" * 80 + "\n")

    fixed_files = 0
    total_fixes = 0

    for file_path in error_files:
        fixes = fix_extra_parentheses(file_path)
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
