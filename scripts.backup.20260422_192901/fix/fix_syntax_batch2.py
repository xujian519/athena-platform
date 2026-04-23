#!/usr/bin/env python3
"""
批量修复Python语法错误脚本 - 第二轮
"""

import re
from pathlib import Path

def fix_file(file_path: Path) -> bool:
    """修复单个文件的语法错误"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        fixes = []

        # 模式1: list[dict[str, Any]) -> 类型 (缺少右方括号)
        pattern1 = r'(\w+\s*:\s*list\[dict\[str,\s*Any\])\)\s*->'
        if re.search(pattern1, content):
            content = re.sub(pattern1, r'\1]) ->', content)
            fixes.append("修复 list[dict[...]] 缺少括号")

        # 模式2: dict[str, str | None = None (缺少右方括号)
        pattern2 = r'(\w+\s*:\s*dict\[str,\s*str\s*\|\s*None\s*=)\s*$'
        def replace_pattern2(match):
            # 检查是否在同一行
            line_start = content.rfind('\n', 0, match.start()) + 1
            line_end = content.find('\n', match.end())
            if line_end == -1:
                line_end = len(content)
            line_content = content[line_start:line_end]

            # 如果行尾有 ) 但缺少 ]
            if ') ->' in line_content or ') ->' in content[match.end():match.end()+20]:
                return match.group(1).replace('dict[str, str | None = None', 'dict[str, str] | None = None')
            return match.group(0)

        # 逐行处理
        lines = content.split('\n')
        modified_lines = []
        for line in lines:
            # 模式2修复
            if 'dict[str, str | None = None' in line and not 'dict[str, str] | None' in line:
                if ') ->' in line or '])' in line:
                    line = line.replace('dict[str, str | None = None', 'dict[str, str] | None = None')
            modified_lines.append(line)
        content = '\n'.join(modified_lines)

        # 模式3: tuple[int, ...]] | None (多余右方括号)
        content = re.sub(r'tuple\[int,\s*\.\.\.]\]\s*\|\s*None', 'tuple[int, ...] | None', content)

        # 模式4: Optional[tuple[int | None = None, ... | None = None)]
        pattern4 = r'Optional\[tuple\[int\s*\|\s*None\s*=\s*None,\s*\.\.\.\s*\|\s*None\s*=\s*None\)\]'
        if re.search(pattern4, content):
            content = re.sub(pattern4, 'tuple[int, ...] | None', content)
            fixes.append("修复 Optional[tuple[...]] 混乱类型")

        # 模式5: RoutingResult] -> RoutingResult,
        content = re.sub(r'(\w+)\s*:\s*(\w+)\]', r'\1: \2,', content)

        # 模式6: dict[AgentType, list[str] = {...}] (缺少右方括号)
        pattern6 = r'dict\[(\w+),\s*list\[str\]\s*=\s*\{'
        if re.search(pattern6, content):
            content = re.sub(pattern6, r'dict[\1, list[str]] = {', content)
            fixes.append("修复 dict[Type, list[str]] 缺少括号")

        # 模式7: Callable[... | None = None, Any | None = None]
        pattern7 = r'Callable\[\.\.\.\s*\|\s*None\s*=\s*None,\s*Any\s*\|\s*None\s*=\s*None\]'
        if re.search(pattern7, content):
            content = re.sub(pattern7, 'Callable[..., Any] | None', content)
            fixes.append("修复 Callable[...] 混乱类型")

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

    print("开始批量修复语法错误...")

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

                # 验证修复
                result2 = subprocess.run(
                    [sys.executable, "-m", "py_compile", str(py_file)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result2.returncode != 0:
                    print(f"  ⚠️  仍有错误: {result2.stderr[:100]}")
            elif fixes:
                print(f"✗ 尝试修复失败: {py_file}")
                for fix in fixes:
                    print(f"    {fix}")

    print(f"\n修复完成!")
    print(f"修复文件数: {fixed_count}")

    if total_fixes:
        print(f"\n应用的修复模式:")
        for fix in set(total_fixes):
            print(f"  - {fix}")

if __name__ == "__main__":
    main()
