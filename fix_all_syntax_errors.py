#!/usr/bin/env python3
"""
批量修复Python类型注解语法错误
Fix Python Type Annotation Syntax Errors

修复常见的类型注解语法错误模式
"""

import re
from pathlib import Path

def fix_syntax_errors(file_path: Path) -> int:
    """修复单个文件的语法错误，返回修复数量"""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content

        # 常见语法错误模式修复
        replacements = [
            # Optional[dict | None = None] -> Optional[dict] | None = None
            (r'Optional\[dict \| None = None\]', 'Optional[dict] | None = None'),
            (r'Optional\[list\[str\] \| None\]', 'Optional[list[str]] | None'),

            # dict[str, Any] | None = None] -> dict[str, Any] | None = None
            (r'dict\[str, Any\] \| None = None\]', 'dict[str, Any] | None = None'),

            # list[str | None = None] -> list[str] | None = None
            (r'list\[str \| None = None\]', 'list[str] | None = None'),

            # bool = True | None = None -> bool | None = None
            (r'bool = True \| None = None', 'bool | None = None'),

            # Any | None = None] -> Any | None = None
            (r'Any \| None = None\]', 'Any | None = None'),

            # 修复多余的右括号
            (r'Manager\] \| None', 'Manager | None'),
            (r'str\] \| None', 'str | None'),
            (r'int\] \| None', 'int | None'),
            (r'bool\] \| None', 'bool | None'),
        ]

        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content)

        if content != original:
            file_path.write_text(content, encoding='utf-8')
            return 1

        return 0

    except Exception as e:
        print(f"⚠️ 处理文件失败 {file_path}: {e}")
        return 0


def main():
    """主函数"""
    core_path = Path('/Users/xujian/Athena工作平台/core')

    print("🔍 开始扫描并修复语法错误...")
    print("=" * 60)

    fixed_count = 0
    checked_count = 0

    for py_file in core_path.rglob('*.py'):
        checked_count += 1
        fixed = fix_syntax_errors(py_file)
        if fixed:
            fixed_count += 1
            print(f"✅ 已修复: {py_file.relative_to(core_path.parent)}")

    print("=" * 60)
    print(f"📊 扫描完成:")
    print(f"   - 检查文件: {checked_count}")
    print(f"   - 修复文件: {fixed_count}")

    if fixed_count > 0:
        print("\n💡 提示: 某些复杂错误可能需要手动修复")


if __name__ == "__main__":
    main()
