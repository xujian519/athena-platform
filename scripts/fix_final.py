#!/usr/bin/env python3
"""
最终版本：修复所有类型注解错误
"""

import re
from pathlib import Path


def count_brackets(s: str, char: str) -> int:
    """计算字符出现次数"""
    return s.count(char)


def balance_brackets_in_line(line: str) -> str:
    """平衡一行中的方括号"""
    open_count = count_brackets(line, '[')
    close_count = count_brackets(line, ']')

    if open_count == close_count:
        return line

    # 缺少右括号
    if open_count > close_count:
        missing = open_count - close_count

        # 在 -> 或 : 之前添加
        if ' -> ' in line:
            # 在 -> 之前添加 ]
            parts = line.split(' -> ', 1)
            line = parts[0] + ']' * missing + ' -> ' + parts[1]
        elif line.rstrip().endswith(':'):
            line = line.rstrip()[:-1] + ']' * missing + ':\n'
        else:
            line = line.rstrip() + ']' * missing

    return line


def fix_file(content: str) -> str:
    """修复文件内容"""
    lines = content.split('\n')
    fixed_lines = []

    for line in lines:
        # 修复模式1: register_capabilities([] → register_capabilities([
        line = re.sub(r'register_capabilities\(\[\]\s*$', 'register_capabilities([', line)

        # 修复模式2: messages: Optional[list[dict[str, str]] tools:
        if 'messages: Optional[list[dict[str, str]' in line and 'tools:' in line:
            line = line.replace(
                'messages: Optional[list[dict[str, str]]',
                'messages: Optional[list[dict[str, str]]]'
            )

        # 修复模式3: ) → dict[str, Any]:
        if ') -> dict[str, Any]:' in line:
            open_count = count_brackets(line, '[')
            close_count = count_brackets(line, ']')
            if open_count > close_count:
                line = line.replace(') -> dict[str, Any]:', '] -> dict[str, Any]:')

        # 平衡方括号
        line = balance_brackets_in_line(line)

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
            print(f"🔧 {file_path.relative_to(base_dir)}")
            try:
                content = file_path.read_text(encoding='utf-8')
                fixed_content = fix_file(content)
                file_path.write_text(fixed_content, encoding='utf-8')
                fixed_count += 1
            except Exception as e:
                print(f"   ❌ 错误: {e}")

    print(f"\n✅ 修复了 {fixed_count} 个文件")


if __name__ == '__main__':
    main()
