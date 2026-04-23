#!/usr/bin/env python3
"""
批量修复core/framework/agents下所有文件的类型注解错误
"""

import re
from pathlib import Path


def fix_type_annotations(content: str) -> str:
    """修复类型注解"""
    lines = content.split('\n')
    fixed_lines = []

    for line in lines:
        original_line = line

        # 修复1: register_capabilities([] → register_capabilities([
        line = re.sub(r'register_capabilities\(\[\]\s*$', 'register_capabilities([', line)

        # 修复2: Optional[list[dict[str, Any]]) → Optional[list[dict[str, Any]]]
        line = re.sub(
            r'Optional\[list\[dict\[str, Any\]\]\)\s*(->|:)',
            r'Optional[list[dict[str, Any]]]] \1',
            line
        )

        # 修复3: Optional[dict[str, Any]]) → Optional[dict[str, Any]]
        line = re.sub(
            r'Optional\[dict\[str, Any\]\)\s*(->|:)',
            r'Optional[dict[str, Any]]] \1',
            line
        )

        # 修复4: 方括号平衡
        open_count = line.count('[')
        close_count = line.count(']')
        if open_count > close_count and 'def ' in line:
            missing = open_count - close_count
            if ' -> ' in line:
                # 在 -> 之前添加 ]
                line = re.sub(r'(\s*->\s*)', ']' * missing + r'\1', line, count=1)
            elif line.rstrip().endswith(':'):
                line = line.rstrip()[:-1] + ']' * missing + ':'

        # 修复5: 列表结尾 ) → ])
        if re.search(r'\w+\)$', line) and open_count > close_count:
            # 检查是否是 _register_capabilities 的列表
            if '_register_capabilities' in ''.join(lines[max(0, fixed_lines.__len__()-10):]):
                line = re.sub(r'(\w+)\)$', r'\1])', line)

        if line != original_line:
            pass  # 可以打印调试信息

        fixed_lines.append(line)

    return '\n'.join(fixed_lines)


def main():
    base_dir = Path('core/framework/agents')
    py_files = list(base_dir.rglob('*.py'))

    print(f"📁 处理 {len(py_files)} 个文件\n")

    fixed_count = 0
    for file_path in py_files:
        # 检查是否有语法错误
        import subprocess
        result = subprocess.run(
            ['python3', '-m', 'py_compile', str(file_path)],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            try:
                content = file_path.read_text(encoding='utf-8')
                fixed_content = fix_type_annotations(content)
                file_path.write_text(fixed_content, encoding='utf-8')
                fixed_count += 1
                print(f"✅ {file_path.relative_to(base_dir)}")
            except Exception as e:
                print(f"❌ {file_path.relative_to(base_dir)}: {e}")

    print(f"\n✅ 修复了 {fixed_count} 个文件")


if __name__ == '__main__':
    main()
