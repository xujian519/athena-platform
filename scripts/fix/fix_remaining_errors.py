#!/usr/bin/env python3
"""
高效批量修复剩余的语法错误
"""

import re
from pathlib import Path


def fix_remaining_errors(file_path: Path) -> tuple[bool, list[str]:
    """修复剩余的语法错误"""
    try:
        with open(file_path, encoding='utf-8') as f:
            content = f.read()

        original_content = content
        fixes = []

        # 模式1: 修复各种 Optional[...] 错误
        patterns_to_fix = [
            # Optional[list[...] | None = None] -> list[...] | None
            (r'Optional\[list\[([^\]+)\]\s*\|\s*None\s*=\s*None\]', r'list[\1] | None', 'Optional[list[...]'),
            # Optional[dict | None = None] -> dict | None
            (r'Optional\[dict\s*\|\s*None\s*=\s*None\]', r'dict | None', 'Optional[dict]'),
            # Optional[...] 错误
            (r'Optional\[list\s*\|\s*None\s*=\s*None\]', r'list | None', 'Optional[list]'),
            (r'Optional\[tuple\s*\|\s*None\s*=\s*None\]', r'tuple | None', 'Optional[tuple]'),
            (r'Optional\[int\s*\|\s*None\s*=\s*None\]', r'int | None', 'Optional[int]'),
            (r'Optional\[str\s*\|\s*None\s*=\s*None\]', r'str | None', 'Optional[str]'),
            (r'Optional\[bool\s*\|\s*None\s*=\s*None\]', r'bool | None', 'Optional[bool]'),
            (r'Optional\[float\s*\|\s*None\s*=\s*None\]', r'float | None', 'Optional[float]'),
        ]

        for pattern, replacement, fix_name in patterns_to_fix:
            if re.search(pattern, content):
                new_content = re.sub(pattern, replacement, content)
                if new_content != content:
                    content = new_content
                    fixes.append(fix_name)

        # 模式2: 修复括号不匹配
        lines = content.split('\n')
        modified_lines = []

        for i, line in enumerate(lines):
            original_line = line

            # 修复 [1:4] -> [1:4]
            if re.search(r'\[\d+:\d+\][^]\s*$', line) and line.count('[') > line.count(']'):
                if not line.rstrip().endswith(']'):
                    line = line.rstrip() + ']'
                elif line.count('[') > line.count(']'):
                    line = line + ']'
                if line != original_line:
                    fixes.append(f"第{i+1}行: 添加闭合括号")

            # 修复 algorithms=[value]
            if re.search(r'algorithms=\[[^\]+\]\]', line):
                line = re.sub(r'algorithms=\[([^\]+)\]\]', r'algorithms=[\1]', line)
                if line != original_line:
                    fixes.append(f"第{i+1}行: 移除多余的 ]")

            # 修复 type] | None
            if re.search(r'\w+\]\]\s*\|\s*None', line):
                line = re.sub(r'(\w+)\]\]\s*\|\s*None', r'\1] | None', line)
                if line != original_line:
                    fixes.append(f"第{i+1}行: 移除多余的 ]")

            # 修复 dict[str, tuple[...] (缺少闭合括号)
            if re.search(r'dict\[str,\s*tuple\[.*?\]\s*=', line):
                match = re.search(r'(dict\[str,\s*tuple\[.*?\])\s*=', line)
                if match:
                    if match.group(1).count('[') > match.group(1).count(']'):
                        line = re.sub(
                            r'(dict\[str,\s*tuple\[.*?)(\s*=)',
                            r'\1]\2',
                            line
                        )
                        if line != original_line:
                            fixes.append(f"第{i+1}行: 闭合 tuple")

            # 修复 list[str | Optional[dict[...],
            if re.search(r'list\[str\s*\|\s*Optional\[dict\[str,\s*Any\],\s*$', line):
                line = re.sub(
                    r'list\[str\s*\|\s*Optional\[dict\[str,\s*Any\],',
                    'list[str] | Optional[dict[str, Any],',
                    line
                )
                if line != original_line:
                    fixes.append(f"第{i+1}行: 修复 list | Optional")

            # 修复 dict[int | None = None, *args]
            if re.search(r'dict\[int\s*\|\s*None\s*=\s*None,\s*\*args\]', line):
                line = re.sub(
                    r'dict\[int\s*\|\s*None\s*=\s*None,\s*\*args\]',
                    'dict[int, Any] | None, *args',
                    line
                )
                if line != original_line:
                    fixes.append(f"第{i+1}行: 修复 dict[int | None]")

            modified_lines.append(line)

        content = '\n'.join(modified_lines)

        # 如果有修改，写回文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, fixes

        return False, []

    except Exception as e:
        return False, [f"错误: {e}"]

def main():
    """主函数"""
    import subprocess
    import sys

    core_path = Path("core")

    print("开始高效批量修复剩余错误...")

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
            fixed, fixes = fix_remaining_errors(py_file)
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
