#!/usr/bin/env python3
"""
最终全面修复脚本 - 处理所有剩余的语法错误
"""

import re
from pathlib import Path


def fix_all_remaining_errors(file_path: Path) -> tuple[bool, list[str]:
    """修复所有剩余的语法错误"""
    try:
        with open(file_path, encoding='utf-8') as f:
            content = f.read()

        original_content = content
        fixes = []

        # ============================================================
        # 1. 修复 Optional[dict | None = None] 类型错误
        # ============================================================
        if re.search(r'Optional\[dict\s*\|\s*None\s*=\s*None\]', content):
            content = re.sub(r'Optional\[dict\s*\|\s*None\s*=\s*None\]', r'dict | None', content)
            fixes.append('Optional[dict | None]')

        # ============================================================
        # 2. 修复 Optional[dict[str, Any] | None = None] 类型错误
        # ============================================================
        if re.search(r'Optional\[dict\[str,\s*Any\]\s*\|\s*None\s*=\s*None\]', content):
            content = re.sub(r'Optional\[dict\[str,\s*Any\]\s*\|\s*None\s*=\s*None\]', r'dict[str, Any] | None', content)
            fixes.append('Optional[dict[str, Any]')

        # ============================================================
        # 3. 修复 Optional[list | None = None] 类型错误
        # ============================================================
        if re.search(r'Optional\[list\s*\|\s*None\s*=\s*None\]', content):
            content = re.sub(r'Optional\[list\s*\|\s*None\s*=\s*None\]', r'list | None', content)
            fixes.append('Optional[list | None]')

        # ============================================================
        # 4. 修复 Optional[list["key"] = None] 类型错误
        # ============================================================
        if re.search(r'Optional\[list\["[^"]+"\]\s*=\s*None\]', content):
            content = re.sub(r'Optional\[list\["[^"]+"\]\s*=\s*None\]', r'list | None', content)
            fixes.append('Optional[list["key"]')

        # ============================================================
        # 5. 修复 Optional[list[CacheLevel] | None = None] 类型错误
        # ============================================================
        if re.search(r'Optional\[list\[CacheLevel\]\s*\|\s*None\s*=\s*None\]', content):
            content = re.sub(r'Optional\[list\[CacheLevel\]\s*\|\s*None\s*=\s*None\]', r'list[CacheLevel] | None', content)
            fixes.append('Optional[list[CacheLevel]')

        # ============================================================
        # 6. 修复 algorithms=[JWT_ALGORITHM] 括号错误
        # ============================================================
        if re.search(r'algorithms=\[JWT_ALGORITHM\]\]', content):
            content = re.sub(r'algorithms=\[JWT_ALGORITHM\]\]', r'algorithms=[JWT_ALGORITHM]', content)
            fixes.append('algorithms 括号')

        # ============================================================
        # 7. 修复函数定义中的括号不匹配
        # ============================================================
        lines = content.split('\n')
        modified_lines = []

        for i, line in enumerate(lines):
            original_line = line

            # 修复 dict[dict[str, str] -> bool:
            if re.search(r'dict\[dict\[str,\s*str\]\]\s*->\s*bool:', line):
                line = re.sub(r'dict\[dict\[str,\s*str\]\]\s*->\s*bool:', r'dict[dict[str, str] -> bool:', line)
                if line != original_line:
                    fixes.append(f'第{i+1}行: dict[dict[str, str]')

            # 修复 list[str]: (函数参数缺少闭合)
            if re.search(r':\s*list\[str\]:\s*$', line):
                # 检查是否在函数定义中
                if i > 0 and 'def ' in lines[i-1]:
                    line = re.sub(r':\s*list\[str\]:\s*$', r': list[str]:', line)
                    if line != original_line:
                        fixes.append(f'第{i+1}行: list[str] 参数')

            # 修复 cases: list[str]: (函数参数缺少闭合)
            if re.search(r'cases:\s*list\[str\]:\s*$', line):
                line = re.sub(r'cases:\s*list\[str\]:\s*$', r'cases: list[str]:', line)
                if line != original_line:
                    fixes.append(f'第{i+1}行: list[str] 参数')

            # 修复 vectors: list[list[dict[str] -> list[int]: (嵌套类型注解)
            if re.search(r'vectors:\s*list\[list\[dict\[str\]\s*->\s*list\[int\]:\s*$', line):
                line = re.sub(r'vectors:\s*list\[list\[dict\[str\]\s*->\s*list\[int\]:\s*$',
                          r'vectors: list[list[dict[str]] -> list[int]:', line)
                if line != original_line:
                    fixes.append(f'第{i+1}行: 嵌套list类型')

            # 修复 *args] (缺少左方括号)
            if re.search(r'\*\s*(?:args|kwargs)\]', line):
                line = re.sub(r'\*\s*(args|kwargs)\]', r'*\1]', line)
                if line != original_line:
                    fixes.append(f'第{i+1}行: *args]')

            # 修复 f-string 错误
            if re.search(r'{\[\.2f\'\)\s*for\s+k\]\]\}', line):
                line = re.sub(r'{\[\.2f\'\)\s*for\s+k\]\]\}', r'{key:.2f}', line)
                if line != original_line:
                    fixes.append(f'第{i+1}行: f-string')

            # 修复 domains: Optional[list["key"] = None]
            if re.search(r'domains:\s*Optional\[list\["[^"]+"\]\s*=\s*None\]', line):
                line = re.sub(r'domains:\s*Optional\[list\["[^"]+"\]\s*=\s*None\]', r'domains: list | None', line)
                if line != original_line:
                    fixes.append(f'第{i+1}行: Optional[list["key"]')

            # 修复 config: Optional[dict[str, Any] | None = None
            if re.search(r'config:\s*Optional\[dict\[str,\s*Any\]\s*\|\s*None\s*=\s*None\s*[,)]', line):
                line = re.sub(r'config:\s*Optional\[dict\[str,\s*Any\]\s*\|\s*None\s*=\s*None',
                          r'config: dict[str, Any] | None', line)
                if line != original_line:
                    fixes.append(f'第{i+1}行: Optional[dict[str, Any]')

            modified_lines.append(line)

        content = '\n'.join(modified_lines)

        # ============================================================
        # 8. 修复 __all__ 列表未闭合
        # ============================================================
        lines = content.split('\n')
        modified_lines = []

        for i, line in enumerate(lines):
            original_line = line

            # 检查 __all__ = [ 后面是否跟 for 循环
            if re.search(r'__all__\s*=\s*\[[^\]*\s*$', line):
                # 检查下一行
                if i + 1 < len(lines) and re.search(r'\s+for\s+', lines[i + 1]):
                    line = line.rstrip() + ']'
                    if line != original_line:
                        fixes.append(f'第{i+1}行: 闭合 __all__ 列表')

            # 检查其他未闭合的列表
            if re.search(r'\w+\s*=\s*\[[^\]*\s*$', line):
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line.startswith('for ') or next_line.startswith('if '):
                        # 这是列表推导式或条件列表，需要闭合
                        line = line.rstrip() + ']'
                        if line != original_line:
                            fixes.append(f'第{i+1}行: 闭合列表')

            modified_lines.append(line)

        content = '\n'.join(modified_lines)

        # ============================================================
        # 9. 检查并修复 content[start: end,.strip() 错误
        # ============================================================
        if re.search(r'\[.+:\s*.+,.+\)\.strip\(\)', content):
            content = re.sub(r'\[(.+):\s*(.+),.+\)\.strip\(\)', r'[\1:\2].strip()', content)
            fixes.append('修复切片语法错误')

        # 如果有修改，写回文件
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
    print("开始最终全面修复")
    print("=" * 80)

    fixed_count = 0
    total_fixes = []

    # 第一轮：修复所有能自动修复的错误
    for py_file in sorted(core_path.rglob("*.py")):
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(py_file)],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            fixed, fixes = fix_all_remaining_errors(py_file)
            if fixed:
                fixed_count += 1
                total_fixes.extend(fixes)
                print(f"✓ 修复: {py_file.relative_to('core')} ({len(fixes)} 处)")
                for fix in fixes[:2]:
                    print(f"    - {fix}")

    print("\n" + "=" * 80)
    print(f"第一轮修复完成: {fixed_count} 个文件")
    print("=" * 80)

    # 第二轮：检查剩余错误
    remaining_errors = []
    for py_file in sorted(core_path.rglob("*.py")):
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(py_file)],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            remaining_errors.append(str(py_file))

    print(f"\n剩余错误文件: {len(remaining_errors)}")

    if remaining_errors:
        print("\n需要手动处理的文件 (前10个):")
        for err in remaining_errors[:10]:
            print(f"  - {err}")

if __name__ == "__main__":
    main()
