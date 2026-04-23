#!/usr/bin/env python3
"""
批量修复Python语法错误脚本 - 第四轮
"""

import re
from pathlib import Path


def fix_file(file_path: Path) -> tuple[bool, str]:
    """修复单个文件的语法错误"""
    try:
        with open(file_path, encoding='utf-8') as f:
            content = f.read()

        original_content = content
        fix_type = ""

        # 逐行处理
        lines = content.split('\n')

        for i in range(len(lines)):
            line = lines[i]
            original_line = line

            # 模式1: 双逗号 ,, 替换为 ,
            if ',,' in line:
                line = line.replace(',,', ',')
                if line != original_line:
                    fix_type = "双逗号"

            # 模式2: -> tuple[str, list[str]: (缺少右方括号)
            if re.search(r'->\s*tuple\[str,\s*list\[str\]:\s*$', line):
                line = re.sub(
                    r'tuple\[str,\s*list\[str\]:\s*$',
                    'tuple[str, list[str]:',
                    line
                )
                if line != original_line:
                    fix_type = "tuple[str, list[str]"

            # 模式3: list[dict[str, Any]): (缺少右方括号)
            if re.search(r'list\[dict\[str,\s*Any\]):\s*$', line):
                line = line.sub(
                    r'list\[dict\[str,\s*Any\]):\s*$',
                    'list[dict[str, Any]):',
                    line
                )
                if line != original_line:
                    fix_type = "list[dict[str, Any]"

            # 模式4: -> list[dict[str, Any]: (缺少左括号)
            if re.search(r'->\s*list\[dict\[str,\s*Any\]:\s*$', line):
                # 需要检查参数列表是否正确闭合
                line = re.sub(
                    r'\w+:\s*list\[dict\[str,\s*Any\]:\s*$',
                    lambda m: m.group(0).replace(']:', ']):'),
                    line
                )
                if line != original_line:
                    fix_type = "参数列表闭合"

            # 模式5: variable["key"] | None = None (错误的赋值语法)
            # 这可能是类型注解错误，应该是 variable: dict[str, str] | None = None
            if re.search(r'^\s*\w+\["[^"]+"\]\s*\|\s*None\s*=\s*None', line):
                # 提取变量名
                match = re.search(r'(\w+)\["([^"]+)"\]', line)
                if match:
                    var_name = match.group(1)
                    line = re.sub(
                        r'^\s*\w+\["[^"]+"\]\s*\|\s*None\s*=\s*None',
                        f'{var_name}: dict[str, str] | None = None',
                        line
                    )
                    if line != original_line:
                        fix_type = "错误的赋值语法"

            # 模式6: def func(self, ... param: type (缺少逗号)
            if re.search(r'def\s+\w+\([^)]*\w+\s*:\s*\w+\s*\)\s*:', line):
                line = re.sub(
                    r'(\w+\s*:\s*\w+)\s*\)\s*:',
                    r'\1,):',
                    line
                )
                if line != original_line:
                    fix_type = "缺少逗号"

            lines[i] = line

        content = '\n'.join(lines)

        # 如果有修改，写回文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, fix_type

        return False, ""

    except Exception as e:
        return False, f"错误: {e}"

def main():
    """主函数"""
    import subprocess
    import sys

    core_path = Path("core")

    print("开始批量修复语法错误 (第四轮)...")

    fixed_count = 0

    for py_file in sorted(core_path.rglob("*.py")):
        # 先检查是否有语法错误
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(py_file)],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            fixed, fix_type = fix_file(py_file)
            if fixed:
                fixed_count += 1
                print(f"✓ 修复: {py_file} ({fix_type})")

    print("\n修复完成!")
    print(f"修复文件数: {fixed_count}")

if __name__ == "__main__":
    main()
