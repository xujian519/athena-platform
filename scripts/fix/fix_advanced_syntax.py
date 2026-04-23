#!/usr/bin/env python3
"""
高级Python语法修复 - 处理括号不匹配等复杂错误
Advanced Python Syntax Fixer
"""

import re
from pathlib import Path


def fix_bracket_mismatches(content: str) -> str:
    """修复括号不匹配问题"""

    # 模式1: Optional[dict[str, Any]) -> Optional[dict[str, Any] | dict[str, Any] | None
    content = re.sub(
        r'Optional\[([a-z]+\[str, Any\])\)\s*->\s*',
        r'\1 | None -> ',
        content
    )

    # 模式2: list[dict[str, Any], XXX: -> list[dict[str, Any], XXX:
    content = re.sub(
        r'list\[dict\[str, Any\],\s*([a-z_]+):',
        r'list[dict[str, Any], \1:',
        content
    )

    # 模式3: query: str] = Optional[None, -> query: str | None] = None,
    content = re.sub(
        r': str\] = Optional\[None,\s*',
        r': str | None = None, ',
        content
    )

    # 模式4: list[str | None = None -> list[str] | None = None
    content = re.sub(
        r'list\[str \| None = None',
        r'list[str] | None = None',
        content
    )

    # 模式5: Set[str | None = None -> Set[str] | None = None
    content = re.sub(
        r'Set\[str \| None = None',
        r'Set[str] | None = None',
        content
    )

    # 模式6: 修复 Optional[dict[str, Any] | None = None] -> dict[str, Any] | None = None
    content = re.sub(
        r'Optional\[dict\[str, Any\] \| None = None\]',
        r'dict[str, Any] | None = None',
        content
    )

    # 模式7: 修复 list[str | None = None, -> list[str] | None = None,
    content = re.sub(
        r'list\[str \| None = None,\s*\*',
        r'list[str] | None = None, *',
        content
    )

    # 模式8: 修复 list[str | None = None, **kwargs -> list[str] | None = None, **kwargs
    content = re.sub(
        r'list\[str \| None = None,\s+\*\*',
        r'list[str] | None = None, **',
        content
    )

    # 模式9: 修复 Optional[ServiceContainer | None] = None) -> ServiceContainer | None = None)
    content = re.sub(
        r'Optional\[([A-Z][a-zA-Z0-9_]*) \| None = None\)',
        r'\1 | None = None)',
        content
    )

    return content

def fix_specific_file_patterns(content: str, file_path: str) -> str:
    """修复特定文件的特定模式"""

    # exceptions.py 特殊处理
    if 'exceptions.py' in file_path:
        # query: str] = Optional[None, -> query: str | None] = None,
        content = re.sub(
            r'query: str\] = Optional\[None,\s*details:',
            r'query: str | None = None, details:',
            content
        )

    return content

def fix_file(file_path: Path) -> bool:
    """修复单个文件"""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content

        # 应用所有修复
        content = fix_bracket_mismatches(content)
        content = fix_specific_file_patterns(content, str(file_path))

        if content != original:
            file_path.write_text(content, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"⚠️ 处理文件失败 {file_path}: {e}")
        return False

def main():
    """主函数"""
    core_path = Path('/Users/xujian/Athena工作平台/core')

    print("=" * 60)
    print("🔧 高级语法修复")
    print("=" * 60)

    # 获取所有有语法错误的文件
    error_files = []
    for f in core_path.rglob('*.py'):
        try:
            compile(f.read_text(encoding='utf-8'), str(f), 'exec')
        except SyntaxError:
            error_files.append(f)

    print(f"\n📁 发现 {len(error_files)} 个有语法错误的文件")

    # 修复文件
    fixed_count = 0
    for f in error_files:
        if fix_file(f):
            fixed_count += 1
            print(f"✅ {f.relative_to(core_path.parent)}")

    # 统计剩余错误
    remaining_errors = 0
    for f in core_path.rglob('*.py'):
        try:
            compile(f.read_text(encoding='utf-8'), str(f), 'exec')
        except SyntaxError:
            remaining_errors += 1

    print("\n" + "=" * 60)
    print("✅ 修复完成:")
    print(f"   - 修复文件: {fixed_count} 个")
    print(f"   - 剩余错误: {remaining_errors} 个文件")
    print("=" * 60)

if __name__ == "__main__":
    main()
