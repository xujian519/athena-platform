#!/usr/bin/env python3
"""
自动化修复Python类型注解语法错误
常见错误模式：
1. Optional[dict[str, Any] = None → Optional[dict[str, Any]] = None
2. list[dict[str, str] = None → list[dict[str, str]] = None
3. ]] → ]
"""

import os
import re
import sys
from pathlib import Path


def fix_type_annotations(content: str) -> tuple[str, int]:
    """
    修复类型注解语法错误

    返回: (修复后的内容, 修复数量)
    """
    fixes = 0
    lines = content.split('\n')
    fixed_lines = []

    # 需要添加的导入
    needed_imports = set()

    for line in lines:
        original_line = line
        fixed_line = line

        # 模式1: Optional[dict[str, Any] = None
        fixed_line = re.sub(
            r'Optional\[dict\[str, Any\] = None\]',
            r'Optional[dict[str, Any]] = None',
            fixed_line
        )

        # 模式2: Optional[list[str] = None
        fixed_line = re.sub(
            r'Optional\[list\[str\] = None\]',
            r'Optional[list[str]] = None',
            fixed_line
        )

        # 模式3: Optional[dict[str, Any]] = None（已经是正确的，但需要检测）
        if 'Optional[' in fixed_line and '= None' in fixed_line:
            needed_imports.add('Optional')

        # 模式4: list[dict[str, str] = None
        fixed_line = re.sub(
            r'list\[dict\[str, str\] = None\]',
            r'list[dict[str, str]] = None',
            fixed_line
        )

        # 模式5: dict[str, Any] = None（在Optional外）
        fixed_line = re.sub(
            r'(?<!Optional\[)dict\[str, Any\] = None\)',
            r'dict[str, Any] | None)',
            fixed_line
        )

        # 模式6: 修复 ]] → ]（但在类型注解中保留，如 list[str]]）
        # 只修复赋值语句中的 ]]
        fixed_line = re.sub(
            r"(\[['\"]\w+['\"]\])\] = ",
            r"\1 = ",
            fixed_line
        )

        if fixed_line != original_line:
            fixes += 1

        fixed_lines.append(fixed_line)

    # 添加缺失的导入
    if needed_imports:
        fixed_content = '\n'.join(fixed_lines)
        import_line = "from typing import " + ", ".join(sorted(needed_imports))

        # 检查是否已有 typing 导入
        if 'from typing import' in fixed_content:
            # 扩展现有导入
            fixed_content = re.sub(
                r'from typing import ([^\n]+)',
                lambda m: f'from typing import {m.group(1)}, {", ".join(sorted(needed_imports))}' if all(
                    imp not in m.group(1) for imp in needed_imports
                ) else m.group(0),
                fixed_content,
                count=1
            )
        else:
            # 在第一个导入后添加
            lines = fixed_content.split('\n')
            insert_pos = 0
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    insert_pos = i + 1
                elif insert_pos > 0 and not line.startswith('import ') and not line.startswith('from '):
                    break

            if insert_pos > 0:
                lines.insert(insert_pos, import_line)
                fixed_content = '\n'.join(lines)

        return fixed_content, fixes
    else:
        return '\n'.join(fixed_lines), fixes


def fix_file(filepath: str) -> bool:
    """修复单个文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        fixed_content, fixes = fix_type_annotations(content)

        if fixes > 0:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            return True
        return False
    except Exception as e:
        print(f"❌ 修复 {filepath} 失败: {e}", file=sys.stderr)
        return False


def main():
    """主函数"""
    if len(sys.argv) > 1:
        # 修复指定文件
        files = sys.argv[1:]
    else:
        # 修复所有Python文件
        files = []
        for root, dirs, filenames in os.walk('core'):
            for filename in filenames:
                if filename.endswith('.py'):
                    files.append(os.path.join(root, filename))

    print(f"🔧 开始修复 {len(files)} 个文件...")

    fixed_count = 0
    for filepath in files:
        if fix_file(filepath):
            fixed_count += 1
            print(f"  ✅ {filepath}")

    print(f"\n✨ 完成！共修复 {fixed_count} 个文件")


if __name__ == '__main__':
    main()
