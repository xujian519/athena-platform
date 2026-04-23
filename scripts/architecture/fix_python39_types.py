#!/usr/bin/env python3
"""
批量修复Python 3.9类型注解兼容性问题
修复 str | None, int | None, dict | None 等为 Optional[str] 等格式
"""

import re
from pathlib import Path

# 定义需要修复的类型注解模式
TYPE_FIXES = [
    # 基础类型
    (r': str \| None', r': Optional[str]'),
    (r': int \| None', r': Optional[int]'),
    (r': float \| None', r': Optional[float]'),
    (r': bool \| None', r': Optional[bool]'),
    (r': list \| None', r': Optional[list]'),
    (r': dict \| None', r': Optional[dict]'),
    (r': set \| None', r': Optional[set]'),
    (r': tuple \| None', r': Optional[tuple]'),

    # 带类型的容器
    (r': list\[(.*?)\] \| None', r': Optional[list[\1]'),
    (r': dict\[(.*?)\] \| None', r': Optional[dict[\1]'),
    (r': set\[(.*?)\] \| None', r': Optional[set[\1]'),
    (r': tuple\[(.*?)\] \| None', r': Optional[tuple[\1]'),

    # Union类型
    (r': str \| type \| None', r': Optional[Union[str, type]'),
    (r': int \| tuple', r': Union[int, tuple]'),
    (r': type \| None', r': Optional[type]'),
    (r': dict\|list\|None', r': Optional[Union[dict, list]'),

    # Any组合
    (r': Any \| None', r': Optional[Any]'),
]

# 需要添加的导入
IMPORT_ADDITIONS = {
    'Optional': 'from typing import Optional',
    'Union': 'from typing import Union',
}

def fix_file_types(file_path: Path) -> int:
    """修复单个文件的类型注解"""
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content

        # 应用所有修复规则
        for pattern, replacement in TYPE_FIXES:
            content = re.sub(pattern, replacement, content)

        # 如果内容有变化，写回文件
        if content != original_content:
            # 检查是否需要添加导入
            needed_imports = set()
            if 'Optional[' in content and 'from typing import' in content:
                if 'Optional' not in content:
                    needed_imports.add('Optional')
            if 'Union[' in content and 'from typing import' in content:
                if 'Union' not in content:
                    needed_imports.add('Union')

            # 添加缺失的导入
            if needed_imports:
                for imp in needed_imports:
                    import_line = IMPORT_ADDITIONS[imp]
                    if import_line not in content:
                        # 在第一个from typing import后添加
                        content = re.sub(
                            r'(from typing import [^\n]+)',
                            rf'\1, {imp}',
                            content
                        )

            file_path.write_text(content, encoding='utf-8')
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

        # 检查文件是否包含需要修复的模式
        try:
            content = file_path.read_text(encoding='utf-8')
            has_issue = any(
                pattern in content
                for pattern in [' | None', ' | type', '| dict', '| list', '| tuple']
            )

            if has_issue:
                fixed = fix_file_types(file_path)
                if fixed:
                    results['fixed'] += 1
                    results['files'].append(str(file_path.relative_to(directory)))
                    print(f"✅ 修复: {file_path.relative_to(directory)}")

        except Exception as e:
            results['errors'] += 1
            print(f"❌ 错误: {file_path.relative_to(directory)} - {e}")

    return results

def main():
    """主函数"""
    project_root = Path("/Users/xujian/Athena工作平台")

    print("🚀 开始批量修复Python 3.9类型注解兼容性问题")
    print("=" * 60)

    # 扫描并修复core目录
    core_dir = project_root / "core"
    core_results = scan_and_fix(core_dir)

    # 扫描并修复config目录
    config_dir = project_root / "config"
    config_results = scan_and_fix(config_dir)

    # 汇总结果
    total_fixed = core_results['fixed'] + config_results['fixed']
    total_scanned = core_results['scanned'] + config_results['scanned']
    total_errors = core_results['errors'] + config_results['errors']

    print("\n" + "=" * 60)
    print("📊 修复结果:")
    print(f"  扫描文件: {total_scanned}")
    print(f"  修复文件: {total_fixed}")
    print(f"  错误数量: {total_errors}")
    print("=" * 60)

    if total_fixed > 0:
        print("\n✅ 类型注解兼容性修复完成！")
        print(f"   共修复 {total_fixed} 个文件")
    else:
        print("\nℹ️  未发现需要修复的类型注解问题")

    print("\n💡 建议:")
    print("   1. 运行测试验证修复效果")
    print("   2. 检查导入语句是否完整")
    print("   3. 提交更改前进行代码审查")

if __name__ == "__main__":
    main()
