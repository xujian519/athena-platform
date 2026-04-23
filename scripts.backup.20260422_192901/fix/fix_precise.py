#!/usr/bin/env python3
"""
逐文件精准修复语法错误
"""

import re
from pathlib import Path

def fix_file_errors(file_path: Path) -> tuple[bool, list[str]]:
    """修复单个文件的所有错误"""
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

            # 模式1: Optional[list | None = None]
            if re.search(r'Optional\[list\s*\|\s*None\s*=\s*None\]', line):
                line = re.sub(r'Optional\[list\s*\|\s*None\s*=\s*None\]', r'list | None', line)
                if line != original_line:
                    fixes.append(f'第{i+1}行: Optional[list | None]')

            # 模式2: Optional[dict | None = None]
            if re.search(r'Optional\[dict\s*\|\s*None\s*=\s*None\]', line):
                line = re.sub(r'Optional\[dict\s*\|\s*None\s*=\s*None\]', r'dict | None', line)
                if line != original_line:
                    fixes.append(f'第{i+1}行: Optional[dict | None]')

            # 模式3: Optional[list["key"] = None]
            if re.search(r'Optional\[list\["[^"]+"\]\s*=\s*None\]', line):
                line = re.sub(r'Optional\[list\["[^"]+"\]\s*=\s*None\]', r'list | None', line)
                if line != original_line:
                    fixes.append(f'第{i+1}行: Optional[list["key"]]')

            # 模式4: Optional[dict[str, Any] | None = None]
            if re.search(r'Optional\[dict\[str,\s*Any\]\s*\|\s*None\s*=\s*None\]', line):
                line = re.sub(r'Optional\[dict\[str,\s*Any\]\s*\|\s*None\s*=\s*None\]', r'dict[str, Any] | None', line)
                if line != original_line:
                    fixes.append(f'第{i+1}行: Optional[dict[str, Any]]')

            # 模式5: algorithms=[JWT_ALGORITHM]]
            if re.search(r'algorithms=\[JWT_ALGORITHM\]\]', line):
                line = re.sub(r'algorithms=\[JWT_ALGORITHM\]\]', r'algorithms=[JWT_ALGORITHM]]', line)
                if line != original_line:
                    fixes.append(f'第{i+1}行: algorithms 括号')

            # 模式6: dict[dict[str, str]] -> bool:
            if re.search(r'dict\[dict\[str,\s*str\]\]\s*->\s*bool:', line):
                line = re.sub(r'dict\[dict\[str,\s*str\]\]\s*->\s*bool:', r'dict[dict[str, str]] -> bool:', line)
                if line != original_line:
                    fixes.append(f'第{i+1}行: dict[dict[str, str]]')

            # 模式7: *args]
            if re.search(r'\*\s*(?:args|kwargs)\]', line):
                line = re.sub(r'\*\s*(args|kwargs)\]', r'*\1]', line)
                if line != original_line:
                    fixes.append(f'第{i+1}行: *args]')

            # 模式8: config[{config['port']
            if re.search(r'config\[\{config\[', line):
                line = re.sub(r'config\[\{config\[', r"config[{config['port']}", line)
                if line != original_line:
                    fixes.append(f'第{i+1}行: config 嵌套括号')

            # 模式9: dict[DecisionLayer, dict[str, Any] (dataclass 字段)
            if re.search(r'dict\[[^]]+, dict\[str,\s*Any\s*#', line):
                line = re.sub(r'(dict\[[^]]+, dict\[str,\s*Any)(\s*#)', r'\1]\2', line)
                if line != original_line:
                    fixes.append(f'第{i+1}行: dataclass 字段括号')

            # 模式10: f-string 错误 {[.2f}') for k]]}
            if re.search(r'{\[\.2f\'\)\s*for\s+k\]\]\}', line):
                line = re.sub(r'{\[\.2f\'\)\s*for\s+k\]\]\}', r'{key:.2f}', line)
                if line != original_line:
                    fixes.append(f'第{i+1}行: f-string 修复')

            # 模式11: dict[str, list[str]) -> str | None: (缺少闭合括号)
            if re.search(r'dict\[str,\s*list\[str\)\]\s*->\s*str\s*\|\s*None:', line):
                line = re.sub(r'dict\[str,\s*list\[str\)\]\s*->\s*str\s*\|\s*None:', r'dict[str, list[str]] -> str | None:', line)
                if line != original_line:
                    fixes.append(f'第{i+1}行: dict[str, list[str]]')

            # 模式12: list[list[float]: (缺少闭合括号)
            if re.search(r'list\[list\[float\]:\s*$', line):
                line = re.sub(r'list\[list\[float\]:\s*$', r'list[list[float]]:', line)
                if line != original_line:
                    fixes.append(f'第{i+1}行: list[list[float]]')

            # 模式13: 修复多余的 ] 符号
            if re.search(r'\]\]\s*\)', line):
                line = re.sub(r'\]\]\s*\)', r'])', line)
                if line != original_line:
                    fixes.append(f'第{i+1}行: 移除多余的 ]')

            # 模式14: 修复 ) -> 后面缺少内容
            if re.search(r'\)\s*->\s*None:\s*$', line) and 'def ' not in line:
                # 这可能是一个单独的 ) -> None: 行，需要检查上一行
                pass  # 跳过，这种需要上下文处理

            modified_lines.append(line)

        content = '\n'.join(modified_lines)

        # 检查是否有修改
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, fixes

        return False, []

    except Exception as e:
        return False, [f"错误: {str(e)}"]

def main():
    """主函数"""
    import subprocess
    import sys

    core_path = Path("core")

    print("=" * 80)
    print("开始逐文件精准修复语法错误")
    print("=" * 80)

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
            fixed, fixes = fix_file_errors(py_file)
            if fixed:
                fixed_count += 1
                total_fixes.extend(fixes)
                print(f"✓ 修复: {py_file.relative_to('core')} ({len(fixes)} 处)")
                for fix in fixes[:3]:
                    print(f"    - {fix}")

    print("\n" + "=" * 80)
    print(f"修复完成: {fixed_count} 个文件")
    print("=" * 80)

if __name__ == "__main__":
    main()
