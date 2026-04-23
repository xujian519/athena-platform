#!/usr/bin/env python3
"""
修复被破坏的Optional类型注解
修复模式：
- Optional[Optional[str] → Optional[str]
- Optional[dict[str, Any] → Optional[dict[str, Any]
"""

import re
from pathlib import Path


def fix_optional_nesting(file_path: Path) -> bool:
    """修复Optional嵌套问题"""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content

        # 修复嵌套的Optional
        content = re.sub(r'Optional\[Optional\[([^\]+)\]\]', r'Optional[\1]', content)

        # 修复缺失的闭合括号 - 检测 Optional[xxx] 缺少 ]
        # 这种模式: Optional[something] = value
        content = re.sub(
            r'(:\s*Optional\[)([^\[\]+)(\] =)',
            r'\1\2]\3',
            content
        )

        # 修复 field() 中的问题
        # Optional[dict[str, Any] = field( → Optional[dict[str, Any] = field(
        content = re.sub(
            r'Optional\[([^=\]+?) = (field\()',
            r'Optional[\1] = \2',
            content
        )

        if content != original:
            file_path.write_text(content, encoding='utf-8')
            return True

        return False

    except Exception as e:
        print(f"⚠️  修复失败 {file_path}: {e}")
        return False


def main():
    """主函数"""
    target_dir = Path("/Users/xujian/Athena工作平台/core/framework/agents")

    print("🚀 开始修复Optional类型注解")
    print("=" * 60)

    fixed_count = 0
    error_count = 0

    for file_path in target_dir.rglob('*.py'):
        if not file_path.is_file():
            continue

        try:
            # 先验证语法
            with open(file_path, 'r') as f:
                compile(f.read(), str(file_path), 'exec')
        except SyntaxError:
            # 有语法错误，尝试修复
            if fix_optional_nesting(file_path):
                fixed_count += 1
                print(f"✅ {file_path.relative_to(target_dir)}")

                # 验证修复后是否正确
                try:
                    with open(file_path, 'r') as f:
                        compile(f.read(), str(file_path), 'exec')
                except SyntaxError as e:
                    error_count += 1
                    print(f"❌ {file_path.relative_to(target_dir)}: 仍有错误 - {e.msg}")
            else:
                error_count += 1
                print(f"⚠️  {file_path.relative_to(target_dir)}: 无法自动修复")

    print("=" * 60)
    print(f"📊 修复结果:")
    print(f"  修复文件: {fixed_count}")
    print(f"  失败文件: {error_count}")
    print(f"  总数: {fixed_count + error_count}")


if __name__ == "__main__":
    main()
