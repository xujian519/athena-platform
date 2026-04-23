#!/usr/bin/env python3
"""
批量修复Python语法错误脚本 - 精准模式修复
"""

import re
from pathlib import Path


def fix_specific_patterns(content: str) -> tuple[str, list[str]:
    """修复特定的语法错误模式"""
    fixes = []

    # 逐行处理
    lines = content.split('\n')
    result_lines = []

    for i, line in enumerate(lines):
        original_line = line

        # 模式1: dict[str, list[str] = field(...) (缺少右方括号)
        if re.search(r'dict\[str,\s*list\[str\]\s*=\s*field', line):
            line = re.sub(
                r'dict\[str,\s*list\[str\]\s*=\s*field',
                'dict[str, list[str] = field',
                line
            )
            if line != original_line:
                fixes.append(f"第{i+1}行: dict[str, list[str]")

        # 模式2: hashlib.md5(..., usedforsecurity=False.isoformat()...)
        # 修复错误的参数顺序
        if 'hashlib.md5(' in line and 'usedforsecurity=False.isoformat()' in line:
            # 提取正确的模式: hashlib.md5(datetime.now().isoformat().encode(), usedforsecurity=False)
            line = re.sub(
                r'hashlib\.md5\(datetime\.now\(\),\s*usedforsecurity=False\.isoformat\(\)\.encode\(\),\s*usedforsecurity=False\)',
                r'hashlib.md5(datetime.now().isoformat().encode(), usedforsecurity=False)',
                line
            )
            if line != original_line:
                fixes.append(f"第{i+1}行: hashlib.md5 参数修复")

        # 模式3: param: type = value | None = None (错误的默认值)
        # 例如: use_redis: bool = False | None = None
        if re.search(r'\w+:\s*\w+\s*=\s*\w+\s*\|\s*None\s*=\s*None', line):
            line = re.sub(
                r'(\w+:\s*\w+\s*=\s*\w+)\s*\|\s*None\s*=\s*None',
                r'\1 | None = None',
                line
            )
            if line != original_line:
                fixes.append(f"第{i+1}行: 修复默认值语法")

        # 模式4: algorithms=[value) (缺少右方括号)
        if re.search(r'algorithms=\[([^\]+)\)', line):
            line = re.sub(r'algorithms=\[([^\]+)\)', r'algorithms=[\1]', line)
            if line != original_line:
                fixes.append(f"第{i+1}行: algorithms 括号修复")

        # 模式5: Optional[True, ... (错误的 Optional 使用)
        if re.search(r'Optional\[True,\s*(\w+:)', line):
            line = re.sub(r'Optional\[True,\s*(\w+:)', r'True, \1', line)
            if line != original_line:
                fixes.append(f"第{i+1}行: 移除错误的 Optional")

        # 模式6: list[str, (参数分隔错误)
        if re.search(r':\s*list\[str,\s*\w+', line):
            line = re.sub(r':\s*list\[str,\s*(\w+)', r': list[str], \1', line)
            if line != original_line:
                fixes.append(f"第{i+1}行: list[str] 参数分隔")

        # 模式7: return type: dict[str, Any]: (多余右方括号)
        if re.search(r'->\s*dict\[str,\s*Any\]\]:\s*$', line):
            line = re.sub(r'dict\[str,\s*Any\]\]:', 'dict[str, Any]:', line)
            if line != original_line:
                fixes.append(f"第{i+1}行: 移除多余括号")

        # 模式8: param: dict[AgentType, list[str] = {...} (缺少右方括号)
        if re.search(r'dict\[[\w:]+,\s*list\[str\]\s*=\s*\{', line):
            line = re.sub(
                r'dict\[([\w:]+),\s*list\[str\]\s*=\s*\{',
                r'dict[\1, list[str] = {',
                line
            )
            if line != original_line:
                fixes.append(f"第{i+1}行: dict[Type, list[str]")

        # 模式9: double None assignment: param: type | None = None | None = None
        if re.search(r'\w+:\s*[^=]+\|\s*None\s*=\s*None\s*\|\s*None\s*=\s*None', line):
            line = re.sub(
                r'(\w+:\s*[^=]+)\|\s*None\s*=\s*None\s*\|\s*None\s*=\s*None',
                r'\1 | None = None',
                line
            )
            if line != original_line:
                fixes.append(f"第{i+1}行: 移除重复的 None 赋值")

        # 模式10: def func(self, ... = Optional[None, param: ... (错误的语法)
        if re.search(r'= Optional\[None,\s*\w+:', line):
            line = re.sub(r'Optional\[None,\s*(\w+:)', r'None, \1', line)
            if line != original_line:
                fixes.append(f"第{i+1}行: 修复 Optional[None,")

        result_lines.append(line)

    return '\n'.join(result_lines), fixes

def fix_file(file_path: Path) -> tuple[bool, list[str]:
    """修复单个文件"""
    try:
        with open(file_path, encoding='utf-8') as f:
            content = f.read()

        new_content, fixes = fix_specific_patterns(content)

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

    print("开始精准模式修复...")

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
                for fix in fixes[:5]:  # 只显示前5个修复
                    print(f"    {fix}")

    print("\n修复完成!")
    print(f"修复文件数: {fixed_count}")

if __name__ == "__main__":
    main()
