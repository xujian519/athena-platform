#!/usr/bin/env python3
"""
批量修复Python语法错误脚本 - 第三轮
"""

import re
from pathlib import Path

def fix_file(file_path: Path) -> tuple[bool, list[str]]:
    """修复单个文件的语法错误"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        fixes = []

        # 逐行处理
        lines = content.split('\n')
        modified_lines = []

        for i, line in enumerate(lines):
            modified_line = line
            original_line = line

            # 模式1: dict[str, list[str] | None = None (缺少右方括号)
            if re.search(r'dict\[str,\s*list\[\w+\]\s*\|\s*None\s*=\s*None\s*[,)]', modified_line):
                modified_line = re.sub(
                    r'dict\[str,\s*list\[(\w+)\]\s*\|\s*None\s*=\s*None',
                    r'dict[str, list[\1]] | None = None',
                    modified_line
                )
                if modified_line != original_line:
                    fixes.append("dict[str, list[X] | None")

            # 模式2: dict[str, str | None = None (缺少右方括号)
            if 'dict[str, str | None = None' in modified_line:
                modified_line = modified_line.replace(
                    'dict[str, str | None = None',
                    'dict[str, str] | None = None'
                )
                if modified_line != original_line:
                    fixes.append("dict[str, str] | None")

            # 模式3: list[dict[str, Any]) -> (缺少右方括号)
            if re.search(r'list\[dict\[str,\s*Any\])\s*->', modified_line):
                modified_line = re.sub(
                    r'list\[dict\[str,\s*Any\])\s*->',
                    r'list[dict[str, Any]]) ->',
                    modified_line
                )
                if modified_line != original_line:
                    fixes.append("list[dict[str, Any]]")

            # 模式4: tuple[int, ...]] | None (多余右方括号)
            if 'tuple[int, ...]]' in modified_line:
                modified_line = modified_line.replace('tuple[int, ...]]', 'tuple[int, ...]]')
                if modified_line != original_line:
                    fixes.append("tuple[int, ...]")

            # 模式5: dict[str, Any | None = None (缺少右方括号)
            if 'dict[str, Any | None = None' in modified_line:
                modified_line = modified_line.replace(
                    'dict[str, Any | None = None',
                    'dict[str, Any] | None = None'
                )
                if modified_line != original_line:
                    fixes.append("dict[str, Any] | None")

            # 模式6: Callable[..., Any | None = None] (混乱的类型)
            if re.search(r'Callable\[\.\.\.,\s*Any\s*\|\s*None\s*=\s*None\]', modified_line):
                modified_line = re.sub(
                    r'Callable\[\.\.\.,\s*Any\s*\|\s*None\s*=\s*None\]',
                    'Callable[..., Any] | None',
                    modified_line
                )
                if modified_line != original_line:
                    fixes.append("Callable[..., Any] | None")

            # 模式7: list[str, (缺少右方括号和逗号)
            if re.search(r':\s*list\[str,\s*\w+', modified_line):
                modified_line = re.sub(
                    r':\s*list\[str,\s*(\w+)',
                    r': list[str], \1',
                    modified_line
                )
                if modified_line != original_line:
                    fixes.append("list[str],")

            # 模式8: def func(self, text: (参数类型缺失)
            if re.search(r'def\s+\w+\([^)]*:\s*text:', modified_line):
                modified_line = re.sub(
                    r'(:\s*)text:',
                    r'\1text: str,',
                    modified_line
                )
                if modified_line != original_line:
                    fixes.append("添加 str 类型")

            # 模式9: 多余的逗号 ,, 替换为 ,
            modified_line = modified_line.replace(',,', ',')

            # 模式10: def func(self, ... = Optional[None, (参数错误)
            if re.search(r'= Optional\[None,\s*\w+', modified_line):
                modified_line = re.sub(
                    r'Optional\[None,\s*(\w+)',
                    r'None, \1',
                    modified_line
                )
                if modified_line != original_line:
                    fixes.append("修复 Optional[None,")

            modified_lines.append(modified_line)

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

    print("开始批量修复语法错误 (第三轮)...")

    fixed_count = 0
    total_fixes = []

    for py_file in sorted(core_path.rglob("*.py")):
        # 先检查是否有语法错误
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
                print(f"✓ 修复: {py_file}")
                for fix in fixes:
                    print(f"    - {fix}")

    print(f"\n修复完成!")
    print(f"修复文件数: {fixed_count}")

    if total_fixes:
        print(f"\n应用的修复:")
        fix_counts = {}
        for fix in total_fixes:
            fix_counts[fix] = fix_counts.get(fix, 0) + 1
        for fix, count in sorted(fix_counts.items()):
            print(f"  - {fix}: {count}次")

if __name__ == "__main__":
    main()
