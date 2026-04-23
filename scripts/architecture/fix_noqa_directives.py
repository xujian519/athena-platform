#!/usr/bin/env python3
"""
修复无效的# noqa指令
格式要求: # noqa: F401 (大写字母+数字)
"""

import re
from pathlib import Path


def fix_noqa_directives(file_path: Path) -> int:
    """修复单个文件的noqa指令"""
    try:
        content = file_path.read_text(encoding='utf-8')
        lines = content.split('\n')
        modified_lines = []
        fixes = 0

        for line in lines:
            # 匹配无效的noqa格式（如 # noqa, # noqa: unused）
            # 应该是 # noqa: F401 或 # noqa: F401,E501
            new_line = line

            # 修复 # noqa → # noqa: F401 (如果在包含unused import的行)
            if '# noqa' in line and '# noqa:' not in line:
                # 检查是否是F401相关的行
                if 'import' in line:
                    new_line = re.sub(r'# noqa\s*$', '# noqa: F401', line)
                    if new_line != line:
                        fixes += 1

            modified_lines.append(new_line)

        if fixes > 0:
            file_path.write_text('\n'.join(modified_lines), encoding='utf-8')

        return fixes

    except Exception as e:
        print(f"⚠️  修复失败 {file_path}: {e}")
        return 0


def scan_and_fix(directory: Path) -> dict:
    """扫描并修复所有文件"""
    results = {
        'scanned': 0,
        'fixed': 0,
        'total_fixes': 0,
        'files': []
    }

    print(f"🔍 扫描目录: {directory}")
    print("=" * 60)

    for file_path in directory.rglob('*.py'):
        if not file_path.is_file():
            continue

        # 跳过虚拟环境
        if any(part in file_path.parts for part in ('venv', '.venv', '__pycache__', '.git')):
            continue

        results['scanned'] += 1

        fixes = fix_noqa_directives(file_path)
        if fixes > 0:
            results['fixed'] += 1
            results['total_fixes'] += fixes
            results['files'].append(str(file_path.relative_to(directory)))
            print(f"✅ {file_path.relative_to(directory)}: {fixes}处修复")

    return results


def main():
    """主函数"""
    project_root = Path("/Users/xujian/Athena工作平台")

    print("🚀 开始修复无效的# noqa指令")
    print("=" * 60)

    # 修复core和tests目录
    core_results = scan_and_fix(project_root / "core")
    tests_results = scan_and_fix(project_root / "tests")

    total_fixes = core_results['total_fixes'] + tests_results['total_fixes']
    total_files = core_results['fixed'] + tests_results['fixed']

    print("\n" + "=" * 60)
    print("📊 修复结果:")
    print(f"  扫描文件: {core_results['scanned'] + tests_results['scanned']}")
    print(f"  修复文件: {total_files}")
    print(f"  修复指令: {total_fixes}")
    print("=" * 60)

    if total_fixes > 0:
        print("\n✅ 修复完成！")
    else:
        print("\nℹ️  未发现需要修复的noqa指令")


if __name__ == "__main__":
    main()
