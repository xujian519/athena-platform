#!/usr/bin/env python3
"""
批量修复Python语法错误脚本 - 综合修复
"""

import re
from pathlib import Path


def fix_comprehensive(content: str) -> tuple[str, list[str]:
    """全面修复语法错误"""
    fixes = []

    lines = content.split('\n')
    result_lines = []

    for i, line in enumerate(lines):
        original_line = line

        # 模式1: param: type = value | None = None (错误的默认值)
        if re.search(r'\w+:\s*\w+\s*=\s*\w+\s*\|\s*None\s*=\s*None', line):
            line = re.sub(
                r'(\w+:\s*\w+\s*=\s*\w+)\s*\|\s*None\s*=\s*None',
                r'\1 | None = None',
                line
            )
            if line != original_line:
                fixes.append(f"第{i+1}行: 默认值语法")

        # 模式2: Optional[list[Type | None = None)] (括号错误)
        if re.search(r'Optional\[list\[[^\]+\|\s*None\s*=\s*None\]', line):
            line = re.sub(
                r'Optional\[list\[([^\]+)\|\s*None\s*=\s*None\]',
                r'list[\1] | None',
                line
            )
            if line != original_line:
                fixes.append(f"第{i+1}行: Optional[list] 修复")

        # 模式3: dict[str, int | None = None (缺少右方括号)
        if re.search(r'dict\[str,\s*int\s*\|\s*None\s*=\s*None\s*[,)]', line):
            line = re.sub(
                r'dict\[str,\s*int\s*\|\s*None\s*=\s*None',
                'dict[str, int] | None = None',
                line
            )
            if line != original_line:
                fixes.append(f"第{i+1}行: dict[str, int]")

        # 模式4: list[start: end,] (切片语法错误)
        if re.search(r'\[(\d+):\s*(\d+),\s*\]', line):
            line = re.sub(r'\[(\d+):\s*(\d+),\s*\]', r'[\1:\2]', line)
            if line != original_line:
                fixes.append(f"第{i+1}行: 切片语法")

        # 模式5: param: dict[str, Any | None = None (类型注解错误)
        if re.search(r'\w+:\s*dict\[str,\s*Any\s*\|\s*None\s*=\s*None\s*[,)]', line):
            line = re.sub(
                r'dict\[str,\s*Any\s*\|\s*None\s*=\s*None',
                'dict[str, Any] | None = None',
                line
            )
            if line != original_line:
                fixes.append(f"第{i+1}行: dict[str, Any]")

        # 模式6: -> type: (在函数定义末尾)
        # 检查是否缺少参数列表的闭合括号
        if re.search(r'def\s+\w+\([^)]*\)\s*->\s*[^:]+:\s*$', line):
            # 检查括号是否匹配
            if line.count('(') > line.count(')'):
                # 在 : 之前添加 )
                line = re.sub(r'(:\s*)$', r')\1', line)
                if line != original_line:
                    fixes.append(f"第{i+1}行: 添加闭合括号")

        # 模式7: def func(..., param: type, param2: type (缺少闭合括号)
        if re.search(r'def\s+\w+\([^)]*:\s*\w+\s*:\s*$', line):
            line = line.rstrip() + '):'
            if line != original_line:
                fixes.append(f"第{i+1}行: 闭合参数列表")

        result_lines.append(line)

    return '\n'.join(result_lines), fixes

def fix_file(file_path: Path) -> tuple[bool, list[str]:
    """修复单个文件"""
    try:
        with open(file_path, encoding='utf-8') as f:
            content = f.read()

        new_content, fixes = fix_comprehensive(content)

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

    print("开始综合模式修复...")

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
