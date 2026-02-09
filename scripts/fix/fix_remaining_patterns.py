#!/usr/bin/env python3
"""
针对性修复剩余的语法错误模式
"""

import re
from pathlib import Path

def fix_specific_file_errors(file_path: Path) -> tuple[bool, list[str]]:
    """修复特定文件的语法错误"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        fixes = []

        # 模式1: Optional[list | None = None] -> list | None
        if 'Optional[list | None = None]' in content:
            content = content.replace('Optional[list | None = None]', 'list | None')
            fixes.append("修复 Optional[list | None]")

        # 模式2: Optional[dict | None = None] -> dict | None
        if 'Optional[dict | None = None]' in content:
            content = content.replace('Optional[dict | None = None]', 'dict | None')

        # 模式3: algorithms=[JWT_ALGORITHM]] -> algorithms=[JWT_ALGORITHM]]
        if re.search(r'algorithms=\[JWT_ALGORITHM\]\]', content):
            content = re.sub(r'algorithms=\[JWT_ALGORITHM\]\]', r'algorithms=[JWT_ALGORITHM]]', content)
            fixes.append("修复 algorithms 括号")

        # 模式4: Optional[list["key"] = None] -> list | None
        if re.search(r'Optional\[list\["[^"]+"\]\s*=\s*None\]', content):
            content = re.sub(r'Optional\[list\["[^"]+"\]\s*=\s*None\]', r'list | None', content)
            fixes.append("修复 Optional[list['key']]")

        # 模式5: dict[str, list[str]: -> dict[str, list[str]]:
        if re.search(r'dict\[str,\s*list\[str\]:\s*$', content):
            content = re.sub(r'dict\[str,\s*list\[str\]:\s*$', r'dict[str, list[str]]:', content)
            fixes.append("修复 dict[str, list[str]]")

        # 模式6: dict[dict[str] -> bool: -> dict[dict[str, str]] -> bool:
        if re.search(r'dict\[dict\[str\]\s*->\s*bool:', content):
            content = re.sub(r'dict\[dict\[str\]\s*->\s*bool:', r'dict[dict[str, str]] -> bool:', content)
            fixes.append("修复 dict[dict[str]]")

        # 模式7: Optional[asyncio.Task[None]) | None -> Optional[asyncio.Task[None]] | None
        if re.search(r'Optional\[asyncio\.Task\[None\)\]\s*\|\s*None', content):
            content = re.sub(r'Optional\[asyncio\.Task\[None\)\]\s*\|\s*None', r'Optional[asyncio.Task[None]] | None', content)
            fixes.append("修复 Optional[asyncio.Task]")

        # 模式8: list[Any) | None -> list[Any] | None
        if re.search(r'list\[Any\)\s*\|\s*None', content):
            content = re.sub(r'list\[Any\)\s*\|\s*None', r'list[Any] | None', content)
            fixes.append("修复 list[Any])")

        # 模式9: dict[str, Any]) | None -> dict[str, Any] | None
        if re.search(r'dict\[str,\s*Any\)\]\s*\|\s*None', content):
            content = re.sub(r'dict\[str,\s*Any\)\]\s*\|\s*None', r'dict[str, Any] | None', content)
            fixes.append("修复 dict[str, Any])")

        # 模式10: *args[]] -> *args]
        if re.search(r'\*args\[\]\]', content):
            content = re.sub(r'\*args\[\]\]', r'*args]', content)
            fixes.append("修复 *args[]")

        # 模式11: list[str]]) | None -> list[str] | None
        if re.search(r'list\[str\]\]\]\s*\|\s*None', content):
            content = re.sub(r'list\[str\]\]\]\s*\|\s*None', r'list[str] | None', content)
            fixes.append("修复 list[str]]")

        # 模式12: dict[str, int | None = None -> dict[str, int] | None = None
        if re.search(r'dict\[str,\s*int\s*\|\s*None\s*=\s*None\s*[,)]', content):
            content = re.sub(r'dict\[str,\s*int\s*\|\s*None\s*=\s*None', r'dict[str, int] | None = None', content)
            fixes.append("修复 dict[str, int]")

        # 模式13: def func( ... ) 缺少闭合括号
        # 检查是否有未闭合的函数定义
        lines = content.split('\n')
        modified_lines = []
        for i, line in enumerate(lines):
            # 检查是否是未闭合的函数定义
            if re.search(r'def\s+\w+\([^)]*:\s*\w+\s*=\s*[^,)]+\s*$', line):
                # 检查下一行是否是缩进的代码块
                if i + 1 < len(lines) and lines[i + 1].strip().startswith('#'):
                    # 在行尾添加 ):
                    line = line.rstrip() + '):'
                    fixes.append(f"第{i+1}行: 闭合参数列表")
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

    print("开始针对性修复剩余错误...")

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
            fixed, fixes = fix_specific_file_errors(py_file)
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
