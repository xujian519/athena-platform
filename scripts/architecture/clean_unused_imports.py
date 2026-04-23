#!/usr/bin/env python3
"""
智能清理unused-import问题

策略：
1. 识别条件导入（try-except、if TYPE_CHECKING）→ 添加# noqa: F401
2. 识别真正未使用的导入 → 删除
3. 识别用于类型注解的导入 → 移到TYPE_CHECKING块
"""

import ast
import re
from pathlib import Path
from typing import Set, Dict, List, Tuple


def analyze_import_usage(file_path: Path) -> Dict:
    """分析文件中导入的使用情况"""
    try:
        content = file_path.read_text(encoding='utf-8')

        # 解析AST
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return {"error": "syntax_error"}

        # 收集所有导入
        imports = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imports[name] = {
                        'module': alias.name,
                        'alias': alias.asname,
                        'lineno': node.lineno,
                        'type': 'import',
                        'in_type_checking': False,
                        'in_try_except': False,
                    }
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imports[name] = {
                        'module': module,
                        'alias': alias.asname,
                        'lineno': node.lineno,
                        'type': 'from_import',
                        'in_type_checking': False,
                        'in_try_except': False,
                    }

        # 检查是否在TYPE_CHECKING或try-except块中
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            # 检查TYPE_CHECKING
            if 'TYPE_CHECKING' in line or 'typing' in line:
                for name, info in imports.items():
                    if info['lineno'] == i:
                        imports[name]['in_type_checking'] = True

            # 检查try-except
            if 'try:' in line or 'except' in line:
                for name, info in imports.items():
                    if info['lineno'] == i:
                        imports[name]['in_try_except'] = True

        # 检查实际使用
        used_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                # 获取属性访问的根名称
                if isinstance(node.value, ast.Name):
                    used_names.add(node.value.id)

        # 分类导入
        unused = []
        used_in_annotations = []
        conditional = []

        for name, info in imports.items():
            if name not in used_names:
                if info['in_type_checking'] or info['in_try_except']:
                    conditional.append((name, info))
                else:
                    # 检查是否可能用于类型注解
                    unused.append((name, info))

        return {
            'total': len(imports),
            'unused': unused,
            'conditional': conditional,
            'used_count': len(used_names),
        }

    except Exception as e:
        return {"error": str(e)}


def fix_file_unused_imports(file_path: Path) -> Tuple[int, List[str]:
    """修复单个文件的unused-import"""
    try:
        analysis = analyze_import_usage(file_path)

        if 'error' in analysis:
            return 0, []

        if not analysis['unused']:
            return 0, []

        content = file_path.read_text(encoding='utf-8')
        lines = content.split('\n')
        modified_lines = lines.copy()
        removed_count = 0
        changes = []

        # 从后往前删除，避免行号偏移
        for name, info in reversed(analysis['unused']):
            lineno = info['lineno'] - 1  # 转为0索引
            line = modified_lines[lineno]

            # 检查是否是from导入的一部分
            if info['type'] == 'from_import':
                # 尝试删除这一项
                pattern = rf'(from\s+\S+\s+import\s+.*?)\b{re.escape(name)}\b(.*,?|.*\))'
                new_line = re.sub(pattern, r'\1\2', line)

                # 清理可能的尾部逗号或括号
                new_line = re.sub(r',\s*,', ',', new_line)
                new_line = re.sub(r'\(\s*,', '(', new_line)
                new_line = re.sub(r',\s*\)', ')', new_line)

                if new_line != line:
                    # 检查是否还有剩余导入
                    if re.search(r'import\s+\w+', new_line):
                        modified_lines[lineno] = new_line
                        removed_count += 1
                        changes.append(f"删除未使用导入: {name} (行{lineno+1})")
                    else:
                        # 如果没有剩余导入，删除整行
                        modified_lines.pop(lineno)
                        # 同时删除前一个空行（如果有）
                        if lineno > 0 and not modified_lines[lineno-1].strip():
                            modified_lines.pop(lineno-1)
                            removed_count += 1
                        removed_count += 1
                        changes.append(f"删除导入行: {name} (行{lineno+1})")
            else:
                # import语句，尝试删除
                pattern = rf'import\s+{re.escape(name)}\s*(?:,.*)?'
                if re.match(pattern, line):
                    modified_lines.pop(lineno)
                    removed_count += 1
                    changes.append(f"删除导入行: import {name} (行{lineno+1})")

        if removed_count > 0:
            file_path.write_text('\n'.join(modified_lines) + '\n', encoding='utf-8')

        return removed_count, changes

    except Exception as e:
        print(f"⚠️  处理失败 {file_path}: {e}")
        return 0, []


def scan_and_fix(directory: Path, extensions: tuple = ('.py',)) -> Dict:
    """扫描目录并修复所有Python文件"""
    results = {
        'scanned': 0,
        'fixed': 0,
        'removed': 0,
        'errors': 0,
        'files': []
    }

    print(f"🔍 扫描目录: {directory}")
    print("=" * 60)

    for file_path in directory.rglob('*'):
        if not file_path.is_file() or file_path.suffix not in extensions:
            continue

        # 跳过虚拟环境和缓存目录
        if any(part in file_path.parts for part in ('venv', '.venv', '__pycache__', '.git', 'node_modules', 'build', 'dist', '.pytest_cache')):
            continue

        results['scanned'] += 1

        removed, changes = fix_file_unused_imports(file_path)

        if removed > 0:
            results['fixed'] += 1
            results['removed'] += removed
            results['files'].append({
                'path': str(file_path.relative_to(directory)),
                'removed': removed,
                'changes': changes
            })
            print(f"✅ {file_path.relative_to(directory)}: 删除{removed}个未使用导入")

    return results


def main():
    """主函数"""
    project_root = Path("/Users/xujian/Athena工作平台")

    print("🚀 开始智能清理unused-import")
    print("=" * 60)

    # 清理core目录
    core_dir = project_root / "core"
    core_results = scan_and_fix(core_dir)

    # 清理tests目录（排除deprecated）
    tests_dir = project_root / "tests"
    tests_results = scan_and_fix(tests_dir)

    # 汇总结果
    total_removed = core_results['removed'] + tests_results['removed']
    total_fixed = core_results['fixed'] + tests_results['fixed']

    print("\n" + "=" * 60)
    print("📊 清理结果:")
    print(f"  扫描文件: {core_results['scanned'] + tests_results['scanned']}")
    print(f"  修复文件: {total_fixed}")
    print(f"  删除导入: {total_removed}")
    print("=" * 60)

    if total_removed > 0:
        print("\n✅ 清理完成！")
        print(f"   共删除 {total_removed} 个未使用的导入")

        # 显示详细变更
        print("\n📝 详细变更（前20个文件）:")
        for file_info in (core_results['files'] + tests_results['files'])[:20]:
            print(f"\n  📄 {file_info['path']}")
            for change in file_info['changes'][:3]:
                print(f"     - {change}")

        print("\n💡 建议:")
        print("   1. 运行测试验证功能正常")
        print("   2. 提交前检查代码差异")
        print("   3. 对剩余的F401添加# noqa: F401（如果是条件导入）")
    else:
        print("\nℹ️  未发现可自动清理的unused-import")

    # 验证剩余问题
    print("\n🔍 验证剩余F401问题...")
    import subprocess
    result = subprocess.run(
        ["ruff", "check", ".", "--select", "F401"],
        capture_output=True,
        text=True,
        cwd=project_root
    )

    remaining = len([line for line in result.stdout.split('\n') if 'F401' in line])
    print(f"   剩余F401问题: {remaining}个")
    print(f"   清理率: {(total_removed / (total_removed + remaining) * 100):.1f}%")


if __name__ == "__main__":
    main()
