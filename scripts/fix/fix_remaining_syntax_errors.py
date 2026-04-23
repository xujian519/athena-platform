#!/usr/bin/env python3
import re
from pathlib import Path


def fix_all_patterns(content: str) -> str:
    """修复所有已知的类型注解语法错误"""
    replacements = [
        # Set[str | None = None -> Set[str] | None = None
        (r'Set\[str \| None = None\]', 'Set[str] | None = None'),
        (r'List\[str \| None = None\]', 'List[str] | None = None'),
        (r'Dict\[str, Any\] \| None = None\]', 'Dict[str, Any] | None = None'),
        (r'Optional\[dict\[str, Any\] \| None\]', 'Optional[dict[str, Any] | None'),
        (r'Optional\[list\[str\] \| None\]', 'Optional[list[str] | None'),

        # 修复未闭合的括号模式
        (r'list\[str \| None = None\]', 'list[str] | None = None'),
        (r'dict\[str, Any\] \| None = None\]', 'dict[str, Any] | None = None'),
        (r'\[str \| None = None\]', '[str] | None = None'),
        (r'\[str, Any\] \| None = None\]', '[str, Any] | None = None'),

        # 其他常见模式
        (r'Optional\[set\[str\]\]', 'Optional[set[str]'),
        (r'set\[str \| None = None\]', 'set[str] | None = None'),
    ]

    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)

    return content

def main():
    core_path = Path('/Users/xujian/Athena工作平台/core')

    print("🔍 修复剩余语法错误...")
    fixed_count = 0

    for py_file in core_path.rglob('*.py'):
        try:
            content = py_file.read_text(encoding='utf-8')
            original = content

            content = fix_all_patterns(content)

            if content != original:
                py_file.write_text(content, encoding='utf-8')
                fixed_count += 1
                print(f"✅ {py_file.relative_to(core_path.parent)}")
        except Exception:
            pass

    print(f"\n📊 共修复 {fixed_count} 个文件")

if __name__ == "__main__":
    main()
