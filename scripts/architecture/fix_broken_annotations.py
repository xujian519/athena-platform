#!/usr/bin/env python3
"""
批量修复被破坏的类型注解
"""

import re
from pathlib import Path


def fix_broken_annotations(file_path: Path) -> bool:
    """修复单个文件的类型注解"""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content

        # 1. 修复双重闭合括号（但保留dict[str, Any]]等正确用法）
        # 只有当]]后面跟着] =时才说明有问题
        content = re.sub(r'\]\]\] = ', ']] = ', content)

        # 2. 修复field()中的缺失括号
        # 模式: Optional[xxx] = field( → Optional[xxx]] = field(
        # 但要小心，只修复确实有问题的
        content = re.sub(
            r'Optional\[([^\[\]]+?)\] = (field\()',
            r'Optional[\1]] = \2',
            content
        )

        # 3. 修复其他类似的模式
        # Optional[list[xxx] = field( → Optional[list[xxx]]] = field(
        content = re.sub(
            r'Optional\[list\[([^\]]+?)\] = (field\()',
            r'Optional[list[\1]]] = \2',
            content
        )

        # 4. 修复dict[str, Any模式
        # Optional[dict[str, Any] = field( → Optional[dict[str, Any]]] = field(
        content = re.sub(
            r'Optional\[dict\[([^\]]+?)\] = (field\()',
            r'Optional[dict[\1]]] = \2',
            content
        )

        if content != original:
            # 验证语法
            try:
                compile(content, str(file_path), 'exec')
                file_path.write_text(content, encoding='utf-8')
                return True
            except SyntaxError as e:
                print(f"⚠️  修复后仍有错误: {file_path.name}")
                return False

        return False

    except Exception as e:
        print(f"❌ {file_path.name}: {e}")
        return False


def main():
    """主函数"""
    target_dir = Path("/Users/xujian/Athena工作平台/core/framework/agents")

    print("🚀 批量修复类型注解")
    print("=" * 60)

    fixed_count = 0
    total_count = 0

    for file_path in target_dir.rglob('*.py'):
        if not file_path.is_file():
            continue

        total_count += 1

        # 检查是否有语法错误
        try:
            with open(file_path, 'r') as f:
                compile(f.read(), str(file_path), 'exec')
        except SyntaxError:
            # 有错误，尝试修复
            if fix_broken_annotations(file_path):
                fixed_count += 1
                print(f"✅ {file_path.relative_to(target_dir)}")

    print("=" * 60)
    print(f"📊 修复: {fixed_count}/{total_count} 个文件")


if __name__ == "__main__":
    main()
