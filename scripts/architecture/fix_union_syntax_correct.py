#!/usr/bin/env python3
"""
正确修复Python 3.9类型注解 - | None语法
"""

import re
from pathlib import Path


def fix_file_union_syntax(file_path: Path) -> int:
    """修复单个文件的union语法"""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content

        # 修复各种 | None 模式 - 必须从最长匹配到最短匹配
        replacements = [
            # 带方括号的复杂类型（必须先匹配）
            (r': type\[([^\]+)\] \| None', r': Optional[type[\1]'),
            (r': list\[([^\]+)\] \| None', r': Optional[list[\1]'),
            (r': dict\[([^\]+)\] \| None', r': Optional[dict[\1]'),
            (r': set\[([^\]+)\] \| None', r': Optional[set[\1]'),
            (r': tuple\[([^\]+)\] \| None', r': Optional[tuple[\1]'),

            # 简单类型
            (r': str \| None', r': Optional[str]'),
            (r': int \| None', r': Optional[int]'),
            (r': float \| None', r': Optional[float]'),
            (r': bool \| None', r': Optional[bool]'),
            (r': list \| None', r': Optional[list]'),
            (r': dict \| None', r': Optional[dict]'),
            (r': set \| None', r': Optional[set]'),
            (r': tuple \| None', r': Optional[tuple]'),
            (r': Any \| None', r': Optional[Any]'),
        ]

        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content)

        if content != original:
            file_path.write_text(content, encoding='utf-8')
            return 1

        return 0

    except Exception as e:
        print(f"⚠️  修复失败 {file_path}: {e}")
        return 0


def main():
    """主函数"""
    target_dir = Path("/Users/xujian/Athena工作平台/core/framework/agents")

    print("🚀 正确修复Python 3.9类型注解")
    print("=" * 60)

    fixed_count = 0
    for file_path in target_dir.rglob('*.py'):
        if file_path.is_file():
            fixed = fix_file_union_syntax(file_path)
            if fixed:
                fixed_count += 1
                print(f"✅ {file_path.relative_to(target_dir)}")

    print("=" * 60)
    print(f"✅ 修复完成: {fixed_count}个文件")


if __name__ == "__main__":
    main()
