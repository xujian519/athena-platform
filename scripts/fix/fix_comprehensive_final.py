#!/usr/bin/env python3
"""
全面批量修复剩余的语法错误
"""

import re
from pathlib import Path

def fix_comprehensive_errors(content: str) -> tuple[str, list[str]]:
    """全面修复语法错误"""
    fixes = []

    # 模式1: 修复 Optional[list["key"] = None] 类型错误
    if re.search(r'Optional\[list\["[^"]+"\]\s*=\s*None\]', content):
        content = re.sub(r'Optional\[list\["[^"]+"\]\s*=\s*None\]', r'list | None', content)
        fixes.append("修复 Optional[list['key']]")

    # 模式2: 修复 dict[dict[str, str]] -> bool: (缺少闭合括号)
    if re.search(r'dict\[dict\[str,\s*str\]\]\s*->\s*bool:\s*$', content):
        content = re.sub(r'dict\[dict\[str,\s*str\]\]\s*->\s*bool:\s*$', r'dict[dict[str, str]] -> bool:', content)
        fixes.append("修复 dict[dict[str, str]]")

    # 模式3: 修复 _context_managers[key = value (缺少右方括号)
    if re.search(r'\w+\[\w+\s*=\s*\w+', content):
        content = re.sub(r'(\w+)\[(\w+)\s*=\s*(\w+)', r'\1[\2] = \3', content)
        fixes.append("修复 dict[key] = value")

    # 模式4: 修复 list[str]]) | None (多余的右方括号)
    if re.search(r'list\[str\]\]\]\s*\|\s*None', content):
        content = re.sub(r'list\[str\]\]\]\s*\|\s*None', r'list[str] | None', content)
        fixes.append("修复 list[str]]")

    # 模式5: 修复 *args] (缺少左方括号)
    if re.search(r'\*\s*(?:args|kwargs)\]', content):
        content = re.sub(r'\*\s*(args|kwargs)\]', r'*\1]', content)
        fixes.append("修复 *args]")

    # 模式6: 修复 dict[str, Any]]) | None (多余的右方括号)
    if re.search(r'dict\[str,\s*Any\]\]\]\s*\|\s*None', content):
        content = re.sub(r'dict\[str,\s*Any\]\]\]\s*\|\s*None', r'dict[str, Any] | None', content)
        fixes.append("修复 dict[str, Any]]")

    # 模式7: 修复 f-string 错误 {[.2f}') for k]]}
    if re.search(r'f"[^"]*{\[\.2f\'\)\s*for\s+k\]\]\}', content):
        content = re.sub(r'{\[\.2f\'\)\s*for\s+k\]\]\}', '{k:.2f}', content)
        fixes.append("修复 f-string 语法")

    # 模式8: 修复 algorithms=[JWT_ALGORITHM]] (多余的右方括号)
    if re.search(r'algorithms=\[JWT_ALGORITHM\]\]', content):
        content = re.sub(r'algorithms=\[JWT_ALGORITHM\]\]', r'algorithms=[JWT_ALGORITHM]]', content)
        fixes.append("修复 algorithms 括号")

    # 模式9: 修复 Optional[list | None = None]
    if 'Optional[list | None = None]' in content:
        content = content.replace('Optional[list | None = None]', 'list | None')
        fixes.append("修复 Optional[list | None]")

    # 模式10: 修复 Optional[dict | None = None]
    if 'Optional[dict | None = None]' in content:
        content = content.replace('Optional[dict | None = None]', 'dict | None')
        fixes.append("修复 Optional[dict | None]")

    return content, fixes

def fix_file(file_path: Path) -> tuple[bool, list[str]]:
    """修复单个文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        new_content, fixes = fix_comprehensive_errors(content)

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

    print("开始全面批量修复...")

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
