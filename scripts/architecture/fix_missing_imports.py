#!/usr/bin/env python3
"""
添加缺失的typing导入（Optional, Union）
"""

import re
from pathlib import Path

def fix_typing_imports(file_path: Path) -> int:
    """修复单个文件的typing导入"""
    try:
        content = file_path.read_text(encoding='utf-8')

        # 检查是否使用了Optional/Union但没有导入
        uses_optional = 'Optional[' in content
        uses_union = 'Union[' in content
        has_typing_import = 'from typing import' in content

        if not (uses_optional or uses_union) or not has_typing_import:
            return 0

        # 检查是否已导入
        has_optional = 'Optional' in content.split('from typing import')[1].split('\n')[0] if 'from typing import' in content else False
        has_union = 'Union' in content.split('from typing import')[1].split('\n')[0] if 'from typing import' in content else False

        modified = False
        lines = content.split('\n')

        # 找到from typing import那一行
        for i, line in enumerate(lines):
            if 'from typing import' in line and not line.strip().startswith('#'):
                imports = line.split('import')[1].strip()

                # 添加Optional
                if uses_optional and 'Optional' not in imports:
                    imports += ', Optional'
                    modified = True

                # 添加Union
                if uses_union and 'Union' not in imports:
                    imports += ', Union'
                    modified = True

                if modified:
                    lines[i] = f"from typing import {imports}"
                    break

        if modified:
            file_path.write_text('\n'.join(lines), encoding='utf-8')
            return 1

        return 0

    except Exception as e:
        print(f"⚠️  修复失败 {file_path}: {e}")
        return 0

def scan_and_fix(directory: Path, extensions: tuple = ('.py',)) -> dict:
    """扫描目录并修复所有Python文件"""
    results = {
        'scanned': 0,
        'fixed': 0,
        'errors': 0,
        'files': []
    }

    print(f"🔍 扫描目录: {directory}")
    print("=" * 60)

    for file_path in directory.rglob('*'):
        if not file_path.is_file() or file_path.suffix not in extensions:
            continue

        # 跳过虚拟环境和缓存目录
        if any(part in file_path.parts for part in ('venv', '.venv', '__pycache__', '.git', 'node_modules', 'build', 'dist')):
            continue

        results['scanned'] += 1

        fixed = fix_typing_imports(file_path)
        if fixed:
            results['fixed'] += 1
            results['files'].append(str(file_path.relative_to(directory)))
            print(f"✅ 修复: {file_path.relative_to(directory)}")

    return results

def main():
    """主函数"""
    project_root = Path("/Users/xujian/Athena工作平台")

    print("🚀 开始添加缺失的typing导入")
    print("=" * 60)

    # 修复core目录
    core_dir = project_root / "core"
    core_results = scan_and_fix(core_dir)

    # 修复tests目录
    tests_dir = project_root / "tests"
    tests_results = scan_and_fix(tests_dir)

    # 汇总结果
    total_fixed = core_results['fixed'] + tests_results['fixed']
    total_scanned = core_results['scanned'] + tests_results['scanned']

    print("\n" + "=" * 60)
    print("📊 修复结果:")
    print(f"  扫描文件: {total_scanned}")
    print(f"  修复文件: {total_fixed}")
    print("=" * 60)

    if total_fixed > 0:
        print("\n✅ typing导入修复完成！")
        print(f"   共修复 {total_fixed} 个文件")
    else:
        print("\nℹ️  所有typing导入都正确")

if __name__ == "__main__":
    main()
