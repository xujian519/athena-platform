#!/usr/bin/env python3
"""
高级括号修复脚本
"""

import re
from pathlib import Path


def fix_bracket_errors_advanced(content: str) -> tuple[str, list[str]:
    """高级括号修复"""
    fixes = []
    lines = content.split('\n')
    result_lines = []

    for i, line in enumerate(lines):
        original_line = line

        # 模式1: list[dict[str, Any] 缺少闭合括号
        # 匹配: def func(self, param: list[dict[str, Any] -> 返回类型:
        if 'def ' in line and 'list[dict[str, Any]' in line:
            # 计算括号数量
            open_brackets = line.count('[')
            close_brackets = line.count(']')
            if open_brackets > close_brackets:
                # 在 -> 之前添加缺失的 ]
                missing = open_brackets - close_brackets
                line = line.replace('list[dict[str, Any]', 'list[dict[str, Any]' + ']' * missing)
                if line != original_line:
                    fixes.append(f"第{i+1}行: 添加缺失的 ]")

        # 模式2: dict[str, type] | None = None (类型注解)
        if re.search(r'dict\[str,\s*[\w|\s]+\]\s*\|\s*None\s*=\s*None\s*[,)]', line):
            # 检查是否缺少闭合括号
            if line.count('[') > line.count(']'):
                # 找到 dict[ 的位置并添加闭合括号
                line = re.sub(
                    r'(dict\[str,\s*[^|\]+\|?\s*None\s*=\s*None)',
                    lambda m: m.group(1).replace('None = None', '] | None = None') if ']' not in m.group(1).split('None')[0] else m.group(0),
                    line
                )
                if line != original_line:
                    fixes.append(f"第{i+1}行: dict 闭合括号")

        # 模式3: list[str, ... 缺少分隔符
        if re.search(r':\s*list\[str,\s*\w+', line):
            line = re.sub(r':\s*list\[str,\s*(\w+)', r': list[str], \1', line)
            if line != original_line:
                fixes.append(f"第{i+1}行: list[str] 分隔")

        # 模式4: tuple[type, ...] 缺少闭合括号
        if re.search(r'tuple\[[^\]+:\s*$', line):
            line = re.sub(r'tuple\[([^\]+):\s*$', r'tuple[\1]:', line)
            if line != original_line:
                fixes.append(f"第{i+1}行: tuple 闭合括号")

        # 模式5: -> type] (多余的右方括号)
        if re.search(r'->\s*[^]+\]:\s*$', line):
            # 检查括号是否平衡
            if line.count('[') < line.count(']'):
                # 移除多余的 ]
                line = re.sub(r'->\s*([^]+)\]:\s*$', r'-> \1:', line)
                if line != original_line:
                    fixes.append(f"第{i+1}行: 移除多余的 ]")

        # 模式6: algorithms=[value) 缺少闭合方括号
        if re.search(r'algorithms=\[([^\]+)\)', line):
            line = re.sub(r'algorithms=\[([^\]+)\)', r'algorithms=[\1]', line)
            if line != original_line:
                fixes.append(f"第{i+1}行: algorithms 闭合括号")

        # 模式7: list[dict[str, Any] -> (缺少括号)
        if re.search(r'list\[dict\[str,\s*Any\]\s*->', line):
            line = re.sub(r'list\[dict\[str,\s*Any\]\s*->', r'list[dict[str, Any]) ->', line)
            if line != original_line:
                fixes.append(f"第{i+1}行: 参数列表闭合")

        result_lines.append(line)

    return '\n'.join(result_lines), fixes

def fix_file(file_path: Path) -> tuple[bool, list[str]:
    """修复单个文件"""
    try:
        with open(file_path, encoding='utf-8') as f:
            content = f.read()

        new_content, fixes = fix_bracket_errors_advanced(content)

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

    print("开始高级括号修复...")

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
