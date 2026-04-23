#!/usr/bin/env python3
"""
批量修复Python语法错误脚本 - 括号修复专用
"""

import re
from pathlib import Path


def fix_bracket_errors(content: str) -> tuple[str, list[str]:
    """修复括号相关的语法错误"""
    fixes = []

    # 逐行处理
    lines = content.split('\n')
    result_lines = []

    for i, line in enumerate(lines):
        original_line = line
        fix_desc = ""

        # 模式1: list[dict[str, Any] 缺少右括号
        # 匹配: def func(self, param: list[dict[str, Any]) -> 返回类型:
        if re.search(r'\w+:\s*list\[dict\[str,\s*Any\]\]\s*\)\s*->', line):
            # 检查是否缺少一个 ]
            if line.count('[') > line.count(']'):
                # 在 ) 之前添加 ]
                line = re.sub(
                    r'(list\[dict\[str,\s*Any\])\s*\)\s*(->)',
                    r'\1]) \2',
                    line
                )
                if line != original_line:
                    fix_desc = "添加缺失的 ]"

        # 模式2: tuple[str, list[str] 缺少右括号
        if re.search(r'->\s*tuple\[str,\s*list\[str\]:\s*$', line):
            line = line.replace('tuple[str, list[str]:', 'tuple[str, list[str]:')
            if line != original_line:
                fix_desc = "tuple[str, list[str]"

        # 模式3: dict[str, Any] | None = None (类型注解错误)
        # 匹配: param: dict[str, Any | None = None
        if re.search(r'\w+:\s*dict\[str,\s*Any\s*\|\s*None\s*=\s*None\s*[,)]', line):
            line = re.sub(
                r'dict\[str,\s*Any\s*\|\s*None\s*=\s*None',
                'dict[str, Any] | None = None',
                line
            )
            if line != original_line:
                fix_desc = "dict[str, Any] | None"

        # 模式4: list[str, ... 缺少右括号和分隔符
        if re.search(r':\s*list\[str,\s*\w+', line):
            line = re.sub(r':\s*list\[str,\s*(\w+)', r': list[str], \1', line)
            if line != original_line:
                fix_desc = "list[str], param"

        # 模式5: variable["key"] = value | None = None (错误的赋值)
        # 应该是: variable["key"] = value
        if re.search(r'\["[^"]+"\]\s*=\s*\w+\s*\|\s*None\s*=\s*None', line):
            line = re.sub(
                r'(\["[^"]+"\]\s*=\s*\w+)\s*\|\s*None\s*=\s*None',
                r'\1',
                line
            )
            if line != original_line:
                fix_desc = "移除冗余的 | None = None"

        # 模式6: def func(...) -> type (缺少冒号)
        # 匹配: def func(...) -> type (没有冒号)
        if re.search(r'def\s+\w+\([^)]*\)\s*(?:->\s*[^:]+)?\s*$', line):
            # 检查下一行是否有冒号或缩进的代码块
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if not next_line.endswith(':') and not next_line.startswith('#'):
                    # 如果下一行是缩进的代码块，可能需要添加冒号
                    if next_line and not next_line[0].isalpha():
                        # 检查是否已经有返回类型注解
                        if '->' in line and not line.rstrip().endswith(':'):
                            line = line.rstrip() + ':'
                            if line != original_line:
                                fix_desc = "添加缺失的冒号"

        # 模式7: 修复双逗号
        if ',,' in line:
            line = line.replace(',,', ',')
            if line != original_line:
                fix_desc = "双逗号"

        result_lines.append(line)
        if fix_desc:
            fixes.append(f"第{i+1}行: {fix_desc}")

    return '\n'.join(result_lines), fixes

def fix_file(file_path: Path) -> tuple[bool, list[str]:
    """修复单个文件"""
    try:
        with open(file_path, encoding='utf-8') as f:
            content = f.read()

        new_content, fixes = fix_bracket_errors(content)

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

    print("开始批量修复括号语法错误...")

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
                for fix in fixes[:3]:  # 只显示前3个修复
                    print(f"    {fix}")

    print("\n修复完成!")
    print(f"修复文件数: {fixed_count}")

if __name__ == "__main__":
    main()
