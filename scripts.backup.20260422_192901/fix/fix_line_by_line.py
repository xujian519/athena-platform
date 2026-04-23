#!/usr/bin/env python3
"""
逐行精准修复Python语法错误
"""

import re
from pathlib import Path

def fix_line_by_line(content: str) -> tuple[str, list[str]]:
    """逐行精准修复"""
    fixes = []
    lines = content.split('\n')
    result_lines = []

    for i, line in enumerate(lines):
        original_line = line

        # 模式1: 双逗号 (, ,)
        if ', ,' in line or ',  ,' in line:
            line = re.sub(r',\s*,', ',', line)
            if line != original_line:
                fixes.append(f"第{i+1}行: 移除双逗号")

        # 模式2: [1:4] 缺少闭合括号
        if re.search(r'\[\d+:\d+\][^]]', line) and line.count('[') > line.count(']'):
            if line.endswith(']'):
                # 如果行以 ] 结尾但括号不匹配
                line = line + ']'
            else:
                # 在行尾添加 ]
                line = line + ']'
            if line != original_line:
                fixes.append(f"第{i+1}行: 添加闭合括号")

        # 模式3: time.time(, usedforsecurity=False) (参数顺序错误)
        if 'time.time(, usedforsecurity=False)' in line:
            line = line.replace('time.time(, usedforsecurity=False)', 'time.time()')
            if line != original_line:
                fixes.append(f"第{i+1}行: 修复 time.time")

        # 模式4: [start: end,.strip() (错误的切片语法)
        if re.search(r'\[.+:\s*.+,.+\)', line):
            line = re.sub(r'\[.+:\s*(.+),.+\)', r'[\1]', line)
            if line != original_line:
                fixes.append(f"第{i+1}行: 修复切片语法")

        # 模式5: Optional[list | None = None] (错误的Optional)
        if re.search(r'Optional\[list\s*\|\s*None\s*=\s*None\]', line):
            line = re.sub(r'Optional\[list\s*\|\s*None\s*=\s*None\]', 'list | None', line)
            if line != original_line:
                fixes.append(f"第{i+1}行: 修复 Optional[list]")

        # 模式6: algorithms=[value]] (多余的右方括号)
        if re.search(r'algorithms=\[[^\]]+\]\]', line):
            line = re.sub(r'algorithms=\[([^\]]+)\]\]', r'algorithms=[\1]', line)
            if line != original_line:
                fixes.append(f"第{i+1}行: 移除多余的 ]")

        # 模式7: type]] | None (多余的右方括号)
        if re.search(r'\w+\]\]\s*\|\s*None', line):
            line = re.sub(r'\w+\]\]\s*\|\s*None', r'\1] | None', line)
            if line != original_line:
                fixes.append(f"第{i+1}行: 移除多余的 ]")

        # 模式8: dict[str, tuple[float, dict[str, Any]] (缺少闭合括号)
        if re.search(r'dict\[str,\s*tuple\[float,\s*dict\[str,\s*Any\]\]\s*=', line):
            line = re.sub(
                r'(dict\[str,\s*tuple\[float,\s*dict\[str,\s*Any\])\]\s*=',
                r'\1] =',
                line
            )
            if line != original_line:
                fixes.append(f"第{i+1}行: 添加闭合括号")

        # 模式9: tuple[bool, list[str]: (缺少闭合括号)
        if re.search(r'tuple\[bool,\s*list\[str\]:\s*$', line):
            line = line.replace('tuple[bool, list[str]:', 'tuple[bool, list[str]]:')
            if line != original_line:
                fixes.append(f"第{i+1}行: 闭合 tuple")

        # 模式10: Optional[dict | None = None] (错误的Optional)
        if re.search(r'Optional\[dict\s*\|\s*None\s*=\s*None\]', line):
            line = re.sub(r'Optional\[dict\s*\|\s*None\s*=\s*None\]', 'dict | None', line)
            if line != original_line:
                fixes.append(f"第{i+1}行: 修复 Optional[dict]")

        # 模式11: list[str | Optional[dict[str, Any], (缺少闭合)
        if re.search(r'list\[str\s*\|\s*Optional\[dict\[str,\s*Any\],\s*$', line):
            line = re.sub(
                r'list\[str\s*\|\s*Optional\[dict\[str,\s*Any\],',
                'list[str] | Optional[dict[str, Any]],',
                line
            )
            if line != original_line:
                fixes.append(f"第{i+1}行: 修复 list | Optional")

        # 模式12: list[dict[str, Any] | None = None (缺少闭合括号)
        if re.search(r'list\[dict\[str,\s*Any\]\s*\|\s*None\s*=\s*None\s*[,)]', line):
            line = re.sub(
                r'(list\[dict\[str,\s*Any\])\s*\|\s*None\s*=\s*None',
                r'\1] | None = None',
                line
            )
            if line != original_line:
                fixes.append(f"第{i+1}行: list[dict] | None")

        # 模式13: Optional[list[Type] | None = None] (错误的Optional)
        if re.search(r'Optional\[list\[[^\]]+\]\s*\|\s*None\s*=\s*None\]', line):
            line = re.sub(
                r'Optional\[list\[([^\]]+)\]\s*\|\s*None\s*=\s*None\]',
                r'list[\1] | None',
                line
            )
            if line != original_line:
                fixes.append(f"第{i+1}行: 修复 Optional[list[Type]]")

        result_lines.append(line)

    return '\n'.join(result_lines), fixes

def fix_file(file_path: Path) -> tuple[bool, list[str]]:
    """修复单个文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        new_content, fixes = fix_line_by_line(content)

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

    print("开始逐行精准修复...")

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

    print(f"\n修复完成!")
    print(f"修复文件数: {fixed_count}")

if __name__ == "__main__":
    main()
