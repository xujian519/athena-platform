#!/usr/bin/env python3
"""
全面修复所有语法错误 - 基于详细错误分析的最终版本
"""

import re
from pathlib import Path

def fix_all_errors(content: str) -> tuple[str, list[str]]:
    """全面修复所有语法错误"""
    fixes = []

    # ============================================================
    # 1. 修复 Optional[...] 错误 (括号不匹配: [ ... ))
    # ============================================================
    optional_patterns = [
        (r'Optional\[list\s*\|\s*None\s*=\s*None\]', 'list | None', 'Optional[list | None]'),
        (r'Optional\[dict\s*\|\s*None\s*=\s*None\]', 'dict | None', 'Optional[dict | None]'),
        (r'Optional\[tuple\s*\|\s*None\s*=\s*None\]', 'tuple | None', 'Optional[tuple | None]'),
        (r'Optional\[int\s*\|\s*None\s*=\s*None\]', 'int | None', 'Optional[int | None]'),
        (r'Optional\[str\s*\|\s*None\s*=\s*None\]', 'str | None', 'Optional[str | None]'),
        (r'Optional\[bool\s*\|\s*None\s*=\s*None\]', 'bool | None', 'Optional[bool | None]'),
        (r'Optional\[float\s*\|\s*None\s*=\s*None\]', 'float | None', 'Optional[float | None]'),
        (r'Optional\[list\["[^"]+"\]\s*=\s*None\]', 'list | None', 'Optional[list["key"]]'),
        (r'Optional\[list\[CacheLevel\]\s*\|\s*None\s*=\s*None\]', 'list[CacheLevel] | None', 'Optional[list[CacheLevel]]'),
    ]

    for pattern, replacement, name in optional_patterns:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            fixes.append(name)

    # ============================================================
    # 2. 修复多余右方括号 (括号不匹配: ( ... ])
    # ============================================================
    bracket_patterns = [
        (r'algorithms=\[JWT_ALGORITHM\]\]', r'algorithms=[JWT_ALGORITHM]]', 'algorithms 括号'),
        (r'(\w+)\]\]\s*\|\s*None', r'\1] | None', '多余 ]]'),
        (r'list\[str\]\]\]\s*\|\s*None', r'list[str] | None', 'list[str]]]'),
        (r'list\[dict\[str,\s*Any\]\]\]\s*\|\s*None', r'list[dict[str, Any]] | None', 'list[dict]]]'),
        (r'dict\[str,\s*Any\)\]\s*\|\s*None', r'dict[str, Any] | None', 'dict[str, Any])]'),
        (r'dict\[str,\s*str\)\]\s*\|\s*None', r'dict[str, str] | None', 'dict[str, str])]'),
        (r'tuple\[float,\s*dict\[str,\s*Any\]\]\]\s*=', r'tuple[float, dict[str, Any]]] =', 'tuple 缺少括号'),
        (r'tuple\[bool,\s*list\[str\]\]\]\s*=', r'tuple[bool, list[str]]] =', 'tuple[bool, list[str]]]'),
    ]

    for pattern, replacement, name in bracket_patterns:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            fixes.append(name)

    # ============================================================
    # 3. 修复缺少右方括号 (括号未闭合: [)
    # ============================================================
    unclosed_patterns = [
        (r'dict\[str,\s*list\[list\[float\]:\s*$', r'dict[str, list[list[float]]]:', 'dict[str, list[list[float]]]'),
        (r'dict\[ModuleType,\s*list\[str\]\]\s*\)\s*->\s*dict\[ModuleType,\s*list\[list\[float\]:\s*$', r'dict[ModuleType, list[str]]) -> dict[ModuleType, list[list[float]]]:', '函数返回类型'),
        (r'dict\[DecisionLayer,\s*dict\[str,\s*Any\s*#', r'dict[DecisionLayer, dict[str, Any]]  #', 'dataclass 字段'),
        (r'list\[str\]:\s*$', r'list[str]]:', 'list[str]:'),
        (r'Optional\[int\]\s*$', r'Optional[int]]:', 'Optional[int] 参数'),
    ]

    for pattern, replacement, name in unclosed_patterns:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            fixes.append(name)

    # ============================================================
    # 4. 修复 f-string 错误
    # ============================================================
    if re.search(r'f"[^"]*{\[\.2f\'\)\s*for\s+k\]\]\}', content):
        content = re.sub(r'{\[\.2f\'\)\s*for\s+k\]\]\}', '{key:.2f}', content)
        fixes.append('f-string 语法错误')

    # ============================================================
    # 5. 修复 dict[key] = value (缺少括号)
    # ============================================================
    if re.search(r'\w+\[\w+\s*=\s*\w+', content):
        content = re.sub(r'(\w+)\[(\w+)\s*=\s*(\w+)', r'\1[\2] = \3', content)
        fixes.append('dict[key] = value 语法')

    # ============================================================
    # 6. 修复 *args] (缺少左方括号)
    # ============================================================
    if re.search(r'\*\s*(?:args|kwargs)\]', content):
        content = re.sub(r'\*\s*(args|kwargs)\]', r'*\1]', content)
        fixes.append('*args] 语法')

    # ============================================================
    # 7. 修复 __all__ 和列表推导式未闭合
    # ============================================================
    # __all__ = [ 后面缺少闭合 ]
    lines = content.split('\n')
    modified_lines = []

    for i, line in enumerate(lines):
        original_line = line

        # 修复 __all__ = [ 未闭合
        if re.search(r'__all__\s*=\s*\[[^\]]*\s*$', line):
            # 检查下一行是否是 for 循环
            if i + 1 < len(lines) and ' for ' in lines[i + 1]:
                line = line.rstrip() + ']'
                if line != original_line:
                    fixes.append(f'第{i+1}行: 闭合 __all__ 列表')

        # 修复 matched_tools = [ 后面跟 for 循环
        if re.search(r'\w+\s*=\s*\[[^\]]*\s*$', line):
            if i + 1 < len(lines) and re.search(r'\s+for\s+', lines[i + 1]):
                line = line.rstrip() + ']'
                if line != original_line:
                    fixes.append(f'第{i+1}行: 闭合列表推导式')

        modified_lines.append(line)

    content = '\n'.join(modified_lines)

    # ============================================================
    # 8. 修复函数定义中的类型注解错误
    # ============================================================
    lines = content.split('\n')
    modified_lines = []

    for i, line in enumerate(lines):
        original_line = line

        # 修复 def func(...) -> type: 缺少闭合括号
        if re.search(r'def\s+\w+\([^)]*:\s*\w+\s*->\s*[^:]+:\s*$', line):
            # 检查括号是否匹配
            if line.count('(') > line.count(')'):
                # 在 : 之前添加 )
                line = re.sub(r'(:\s*)$', r')\1', line)
                if line != original_line:
                    fixes.append(f'第{i+1}行: 闭合参数列表')

        # 修复 def func(, param: ... (多余的逗号)
        if re.search(r'def\s+\w+\([^)]*,\s*\w+:', line):
            line = re.sub(r',(\s*\w+:)', r',\1', line)
            if line != original_line:
                fixes.append(f'第{i+1}行: 移除多余逗号')

        # 修复 dict[dict[str, str]] -> bool: (缺少括号)
        if re.search(r'dict\[dict\[str,\s*str\]\]\s*->\s*bool:\s*$', line):
            line = re.sub(r'dict\[dict\[str,\s*str\]\]\s*->\s*bool:\s*$', r'dict[dict[str, str]] -> bool:', line)
            if line != original_line:
                fixes.append(f'第{i+1}行: dict[dict[str, str]]')

        modified_lines.append(line)

    content = '\n'.join(modified_lines)

    # ============================================================
    # 9. 修复 except 子句缺少冒号
    # ============================================================
    if re.search(r'except\s+\w+\s*as\s+\w+\s*$', content):
        content = re.sub(r'(except\s+\w+\s+as\s+\w+)\s*$', r'\1:', content)
        fixes.append('except 子句添加冒号')

    return content, fixes

def fix_file(file_path: Path) -> tuple[bool, list[str]]:
    """修复单个文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        new_content, fixes = fix_all_errors(content)

        if new_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True, fixes

        return False, []

    except Exception as e:
        return False, [f"错误: {e}"]

def main():
    """主函数"""
    import subprocess
    import sys

    core_path = Path("core")

    print("=" * 80)
    print("开始全面修复所有语法错误")
    print("=" * 80)

    fixed_count = 0
    total_fixes = []

    # 第一轮：修复所有能自动修复的错误
    for py_file in sorted(core_path.rglob("*.py")):
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(py_file)],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            fixed, fixes = fix_file(py_file)
            if fixed:
                fixed_count += 1
                total_fixes.extend(fixes)
                print(f"✓ 修复: {py_file.relative_to('core')} ({len(fixes)} 处)")
                for fix in fixes[:2]:
                    print(f"    - {fix}")

    print("\n" + "=" * 80)
    print(f"第一轮修复完成: {fixed_count} 个文件")
    print("=" * 80)

    # 第二轮：检查剩余错误并手动处理特殊情况
    remaining_errors = []
    for py_file in sorted(core_path.rglob("*.py")):
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(py_file)],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            remaining_errors.append(str(py_file))

    print(f"\n剩余错误文件: {len(remaining_errors)}")
    if remaining_errors:
        print("\n需要手动检查的文件:")
        for err in remaining_errors[:10]:
            print(f"  - {err}")
        if len(remaining_errors) > 10:
            print(f"  ... 还有 {len(remaining_errors) - 10} 个文件")

if __name__ == "__main__":
    main()
