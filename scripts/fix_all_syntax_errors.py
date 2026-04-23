#!/usr/bin/env python3
"""
使用正则表达式批量修复类型注解语法错误
"""

import re
from pathlib import Path


def fix_optional_patterns(content: str) -> str:
    """修复所有Optional相关的模式"""

    # 模式1: Optional[Type] = None, (注意Type可能包含嵌套的[])
    content = re.sub(
        r':\s*Optional\[([^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*)\]\s*=\s*None,',
        r': Optional[\1] = None,',
        content
    )

    # 模式2: Optional[Type] = None)  # 函数参数结束
    content = re.sub(
        r':\s*Optional\[([^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*)\]\s*=\s*None\)',
        r': Optional[\1] = None)',
        content
    )

    # 模式3: Optional[Type] = field(...)
    content = re.sub(
        r':\s*Optional\[([^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*)\]\s*=\s*field\(',
        r': Optional[\1] = field(',
        content
    )

    # 模式4: Optional[Optional[Type]] -> Optional[Type]
    content = re.sub(r'Optional\[Optional\[([^\]]+)\]\]', r'Optional[\1]', content)

    # 模式5: 修复剩余的 ]] -> ]
    content = re.sub(r'\]\]', r']', content)

    return content


def process_file(file_path: Path) -> bool:
    """处理单个文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        fixed_content = fix_optional_patterns(content)

        if fixed_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            return True
        return False

    except Exception as e:
        print(f"❌ {file_path}: {e}")
        return False


def main():
    """主函数"""
    base_dir = Path("/Users/xujian/Athena工作平台/core/framework/agents")

    # 查找所有Python文件
    python_files = list(base_dir.rglob("*.py"))

    print(f"📁 处理 {len(python_files)} 个Python文件\n")

    fixed_count = 0
    for file_path in python_files:
        if process_file(file_path):
            fixed_count += 1
            print(f"✅ {file_path.relative_to(base_dir)}")

    print(f"\n📊 修复了 {fixed_count} 个文件")

    # 验证语法
    print("\n🔍 验证语法...")
    import ast
    error_count = 0

    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                ast.parse(f.read())
        except SyntaxError as e:
            error_count += 1
            print(f"❌ {file_path.relative_to(base_dir)}: {e}")

    if error_count == 0:
        print("✅ 所有文件语法正确！")
    else:
        print(f"⚠️  还有 {error_count} 个文件有语法错误")


if __name__ == "__main__":
    main()
