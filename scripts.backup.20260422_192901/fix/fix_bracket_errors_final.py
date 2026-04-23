#!/usr/bin/env python3
"""
专门针对括号不匹配和未闭合括号的修复脚本
"""

import re
from pathlib import Path

def fix_bracket_errors(file_path: Path) -> tuple[bool, list[str]]:
    """修复括号相关的语法错误"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        fixes = []

        # 逐行处理
        lines = content.split('\n')
        modified_lines = []

        for i, line in enumerate(lines):
            original_line = line

            # 模式1: 修复列表推导式缺少闭合括号
            # 例如: [intent for intent, _ in sorted_intents[1:4]
            if re.search(r'\[.*for\s+\w+.*in\s+.*\[\d+:\d+\]?\s*$', line):
                if line.count('[') > line.count(']'):
                    # 检查是否缺少闭合括号
                    if not line.rstrip().endswith(']'):
                        line = line.rstrip() + ']'
                        if line != original_line:
                            fixes.append(f"第{i+1}行: 添加列表推导式闭合括号")

            # 模式2: 修复 algorithms=[value] 缺少闭合括号
            if re.search(r'algorithms=\[[^\]]*\]\s*$', line):
                if line.count('[') > line.count(']'):
                    line = line + ']'
                    if line != original_line:
                        fixes.append(f"第{i+1}行: 添加 algorithms 闭合括号")

            # 模式3: 修复 type] | None (缺少括号)
            # 例如: list[dict[str, Any]] | None
            if re.search(r'[\w\]]+\]\s*\|\s*None\s*[,)=]', line):
                # 检查是否有多余的 ]]
                if re.search(r'\w+\]\]\s*\|\s*None', line):
                    line = re.sub(r'(\w+)\]\]\s*\|\s*None', r'\1] | None', line)
                    if line != original_line:
                        fixes.append(f"第{i+1}行: 移除多余的 ]")

            # 模式4: 修复 Optional[list[...]] 错误
            if re.search(r'Optional\[list\[([^\]]+)\]\]', line):
                line = re.sub(r'Optional\[list\[([^\]]+)\]\]', r'list[\1]', line)
                if line != original_line:
                    fixes.append(f"第{i+1}行: 修复 Optional[list]]")

            # 模式5: 修复 dict[str, tuple[...]] 缺少闭合括号
            if re.search(r'dict\[str,\s*tuple\[.*?\]\s*=', line):
                match = re.search(r'(dict\[str,\s*tuple\[.*?\])\s*=', line)
                if match:
                    group = match.group(1)
                    if group.count('[') > group.count(']'):
                        # 添加缺失的 ]
                        line = re.sub(
                            r'(dict\[str,\s*tuple\[.*?)(\s*=)',
                            lambda m: m.group(1) + ']' * (m.group(1).count('[') - m.group(1).count(']')) + m.group(2),
                            line
                        )
                        if line != original_line:
                            fixes.append(f"第{i+1}行: 修复 dict[str, tuple[...]]")

            # 模式6: 修复 list[dict[str, Any] | None = None 缺少闭合括号
            if re.search(r'list\[dict\[str,\s*Any\]\s*\|\s*None\s*=\s*None\s*[,)]', line):
                line = re.sub(
                    r'(list\[dict\[str,\s*Any\])\s*\|\s*None\s*=\s*None',
                    r'\1] | None = None',
                    line
                )
                if line != original_line:
                    fixes.append(f"第{i+1}行: 修复 list[dict] | None")

            # 模式7: 修复 tuple[bool, list[str]: 缺少闭合括号
            if re.search(r'tuple\[bool,\s*list\[str\]:\s*$', line):
                line = line.replace('tuple[bool, list[str]:', 'tuple[bool, list[str]]:')
                if line != original_line:
                    fixes.append(f"第{i+1}行: 修复 tuple[bool, list[str]]")

            # 模式8: 修复 def func(...) -> type: 缺少闭合括号
            if re.search(r'def\s+\w+\([^)]*\)\s*->\s*[^:]+:\s*$', line):
                # 检查括号是否匹配
                if line.count('(') > line.count(')'):
                    # 在 : 之前添加 )
                    line = re.sub(r'(:\s*)$', r')\1', line)
                    if line != original_line:
                        fixes.append(f"第{i+1}行: 添加参数列表闭合括号")

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

    print("开始修复括号错误...")

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
            fixed, fixes = fix_bracket_errors(py_file)
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
