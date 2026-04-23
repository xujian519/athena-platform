#!/usr/bin/env python3
"""
精确修复剩余的Python类型注解语法错误
"""
import ast
import re
from pathlib import Path


def fix_advanced_brackets(content: str) -> str:
    """
    修复复杂的括号匹配问题

    主要模式:
    1. Optional[tuple[X, Y]]] -> Optional[tuple[X, Y]]
    2. Optional[list[dict[X, Y]]]] -> Optional[list[dict[X, Y]]]
    3. 三重或四重括号
    """
    original = content

    # 模式1: Optional[tuple[X, Y]]] -> Optional[tuple[X, Y]]
    # 只修复明确的三重括号情况
    content = re.sub(
        r'Optional\[tuple\[([^\[\]]+)\]\]\]',
        r'Optional[tuple[\1]]',
        content
    )

    # 模式2: Optional[list[dict[X, Y]]]] -> Optional[list[dict[X, Y]]]
    content = re.sub(
        r'Optional\[list\[dict\[([^\[\]]+)\]\]\]\]',
        r'Optional[list[dict[\1]]]',
        content
    )

    # 模式3: Optional[list[X]]] -> Optional[list[X]]
    content = re.sub(
        r'Optional\[list\[([^\[\]]+)\]\]\]',
        r'Optional[list[\1]]',
        content
    )

    # 模式4: Optional[dict[X, Y]]] -> Optional[dict[X, Y]]
    content = re.sub(
        r'Optional\[dict\[([^\[\]]+)\]\]\]',
        r'Optional[dict[\1]]',
        content
    )

    # 模式5: Optional[set[X]]] -> Optional[set[X]]
    content = re.sub(
        r'Optional\[set\[([^\[\]]+)\]\]\]',
        r'Optional[set[\1]]',
        content
    )

    return content


def fix_file(file_path: Path) -> dict:
    """修复单个文件"""
    try:
        content = file_path.read_text(encoding='utf-8')

        # 尝试修复
        fixed_content = fix_advanced_brackets(content)

        if fixed_content != content:
            # 验证修复后的语法
            try:
                ast.parse(fixed_content, filename=str(file_path))
                file_path.write_text(fixed_content, encoding='utf-8')
                return {
                    'file': str(file_path),
                    'status': 'fixed',
                    'changed': True
                }
            except SyntaxError as e:
                return {
                    'file': str(file_path),
                    'status': 'failed',
                    'error': str(e)
                }
        else:
            return {
                'file': str(file_path),
                'status': 'no_change',
                'changed': False
            }
    except Exception as e:
        return {
            'file': str(file_path),
            'status': 'error',
            'error': str(e)
        }


def main():
    """主函数"""
    target_dir = Path("/Users/xujian/Athena工作平台/core")

    print("🔧 精确修复剩余语法错误")
    print("=" * 60)

    # 先找到所有有错误的文件
    error_files = []
    for py_file in target_dir.rglob("*.py"):
        try:
            with open(py_file) as f:
                compile(f.read(), str(py_file), 'exec')
        except SyntaxError:
            error_files.append(py_file)

    print(f"📊 发现 {len(error_files)} 个有语法错误的文件")
    print()

    fixed_count = 0
    failed_count = 0

    for file_path in error_files[:50]:  # 先处理前50个
        result = fix_file(file_path)
        if result.get('status') == 'fixed':
            fixed_count += 1
            print(f"✅ {file_path.relative_to(target_dir)}")
        elif result.get('status') == 'failed':
            failed_count += 1
            print(f"❌ {file_path.relative_to(target_dir)}: {result.get('error')}")

    print()
    print("=" * 60)
    print(f"📊 修复统计:")
    print(f"  成功: {fixed_count}")
    print(f"  失败: {failed_count}")
    print(f"  剩余: {len(error_files) - 50}")

    # 验证整体改善
    print()
    print("📊 验证整体改善...")
    import subprocess
    result = subprocess.run(
        ['find', 'core', '-name', '*.py', '-exec', 'python3', '-m', 'py_compile', '{}', ';'],
        capture_output=True,
        text=True
    )
    remaining = result.stderr.count('SyntaxError')
    print(f"剩余语法错误: {remaining}")


if __name__ == '__main__':
    main()
