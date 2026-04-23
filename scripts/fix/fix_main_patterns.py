#!/usr/bin/env python3
"""
针对主要错误模式的修复脚本
"""

import re
from pathlib import Path


def fix_main_patterns(content: str) -> tuple[str, list[str]:
    """修复主要的语法错误模式"""
    fixes = []
    lines = content.split('\n')
    result_lines = []

    for i, line in enumerate(lines):
        original_line = line

        # 模式1: dict[str, ...] | None = None (缺少右括号)
        # 匹配: param: dict[str, type | None = None
        # 应该是: param: dict[str, type] | None = None
        if re.search(r'\w+:\s*dict\[str,\s*[^|\]+\s*\|\s*None\s*=\s*None\s*[,)]', line):
            # 检查是否缺少闭合括号
            match = re.search(r'dict\[str,\s*([^|\]+?)\s*\|\s*None\s*=\s*None', line)
            if match:
                # 在 | None 之前添加 ]
                new_line = re.sub(
                    r'dict\[str,\s*([^|\]+?)\s*\|\s*None\s*=\s*None',
                    r'dict[str, \1] | None = None',
                    line
                )
                if new_line != line and ']' in new_line:
                    line = new_line
                    fixes.append(f"第{i+1}行: dict[str, ...]")

        # 模式2: Optional[错误]
        # 匹配: Optional[None, param: ... 或 Optional[True, ...
        if re.search(r'Optional\[(None|True|False),\s*\w+:', line):
            line = re.sub(
                r'Optional\[(None|True|False),\s*(\w+:)',
                r'\1, \2',
                line
            )
            if line != original_line:
                fixes.append(f"第{i+1}行: 移除错误的 Optional")

        # 模式3: Optional[list[Type | None = None)]
        if re.search(r'Optional\[list\[[^\]+\|\s*None\s*=\s*None\]', line):
            line = re.sub(
                r'Optional\[list\[([^\]+)\|\s*None\s*=\s*None\]',
                r'list[\1] | None',
                line
            )
            if line != original_line:
                fixes.append(f"第{i+1}行: Optional[list]")

        # 模式4: dict[Type, list[str] = {...} (缺少右括号)
        if re.search(r'dict\[[^]+,\s*list\[str\]\s*=\s*\{', line):
            line = re.sub(
                r'dict\[([^]+),\s*list\[str\]\s*=\s*\{',
                r'dict[\1, list[str] = {',
                line
            )
            if line != original_line:
                fixes.append(f"第{i+1}行: dict[Type, list[str]")

        # 模式5: param: type | None = None, param2: ... (缺少闭合)
        if re.search(r'\w+:\s*[^,]+,\s*\w+:', line):
            # 检查是否在函数定义中
            if re.match(r'\s*def\s+', lines[i-1] if i > 0 else ''):
                # 检查参数列表是否正确闭合
                if line.count('(') > line.count(')') and 'def ' not in line:
                    # 在行尾添加 )
                    line = line.rstrip() + ')'
                    if line != original_line:
                        fixes.append(f"第{i+1}行: 添加闭合括号")

        result_lines.append(line)

    return '\n'.join(result_lines), fixes

def fix_file(file_path: Path) -> tuple[bool, list[str]:
    """修复单个文件"""
    try:
        with open(file_path, encoding='utf-8') as f:
            content = f.read()

        new_content, fixes = fix_main_patterns(content)

        if new_content != content:
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

    print("开始主要模式修复...")

    fixed_count = 0
    total_fixes = []

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
                print(f"✓ 修复: {py_file.relative_to('core')}")
                for fix in fixes[:3]:
                    print(f"    {fix}")

    print("\n修复完成!")
    print(f"修复文件数: {fixed_count}")

if __name__ == "__main__":
    main()
