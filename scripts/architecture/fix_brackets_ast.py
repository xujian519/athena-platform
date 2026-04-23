#!/usr/bin/env python3
"""
基于AST的精确括号修复工具

使用Python ast模块精确解析和修复类型注解中的括号匹配问题。
"""
import ast
import re
import sys
from pathlib import Path


def fix_type_annotations_brackets(content: str) -> tuple[str, int]:
    """
    修复类型注解中的括号匹配问题

    Args:
        content: Python文件内容

    Returns:
        (修复后的内容, 修复数量)
    """
    original_content = content
    fix_count = 0

    # 模式1: Optional[list[str] = None -> Optional[list[str]] = None
    pattern1 = r'Optional\[list\[str\] = None'
    if re.search(pattern1, content):
        content = re.sub(pattern1, r'Optional[list[str]] = None', content)
        fix_count += 1

    # 模式2: Optional[dict[str, Any] = None -> Optional[dict[str, Any]] = None
    pattern2 = r'Optional\[dict\[str, Any\] = None'
    if re.search(pattern2, content):
        content = re.sub(pattern2, r'Optional[dict[str, Any]] = None', content)
        fix_count += 1

    # 模式3: Optional[list[dict[str, Any]]] = field( -> Optional[list[dict[str, Any]]]] = field(
    # 注意：这种需要三个闭合括号
    pattern3 = r'Optional\[list\[dict\[str, Any\]\]\] = field\('
    if re.search(pattern3, content):
        # 这个是正确的，不需要修复
        pass

    # 模式4: Optional[list[dict[str, Any]] = field( -> Optional[list[dict[str, Any]]]] = field(
    pattern4 = r'Optional\[list\[dict\[str, Any\]\] = field\('
    if re.search(pattern4, content):
        content = re.sub(pattern4, r'Optional[list[dict[str, Any]]]] = field(', content)
        fix_count += 1

    # 模式5: 修复多余的双括号 dict[str, Type]] -> dict[str, Type]
    # 但要小心 dict[str, list[Type]]] 这种正确的情况
    def fix_extra_brackets(match):
        """修复多余括号的辅助函数"""
        full_match = match.group(0)
        # 检查是否是嵌套泛型（应该有]]])
        if ']]]' in full_match:
            return full_match  # 保留，这是正确的嵌套
        # 否则删除一个]
        return full_match.replace(']]', ']')

    # 谨慎使用：只修复明显错误的模式
    # pattern5: dict[str, Type]] = 但后面不是 field(
    pattern5 = r'\w+\[str,\s*\w+\]\](?!\])\s*='
    # 这个模式太危险，暂时不使用

    return content, fix_count


def verify_syntax(content: str, file_path: str) -> bool:
    """验证Python语法是否正确"""
    try:
        ast.parse(content, filename=file_path)
        return True
    except SyntaxError:
        return False


def fix_file(file_path: Path) -> dict[str, Any]:
    """
    修复单个文件

    Returns:
        修复结果字典
    """
    try:
        # 读取文件
        content = file_path.read_text(encoding='utf-8')

        # 先验证原始语法
        original_valid = verify_syntax(content, str(file_path))

        # 尝试修复
        fixed_content, fix_count = fix_type_annotations_brackets(content)

        # 验证修复后的语法
        fixed_valid = verify_syntax(fixed_content, str(file_path))

        result = {
            'file': str(file_path.relative_to(file_path.cwd())),
            'original_valid': original_valid,
            'fixed_valid': fixed_valid,
            'fix_count': fix_count,
            'content_changed': content != fixed_content,
            'success': False
        }

        # 只有在以下情况才写入文件：
        # 1. 原始语法无效，修复后有效
        # 2. 原始语法有效，修复后仍然有效（且确实有修改）
        if (not original_valid and fixed_valid) or \
           (original_valid and fixed_valid and fixed_content != content):
            file_path.write_text(fixed_content, encoding='utf-8')
            result['success'] = True

        return result

    except Exception as e:
        return {
            'file': str(file_path.relative_to(file_path.cwd())),
            'error': str(e),
            'success': False
        }


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python fix_brackets_ast.py <目录>")
        sys.exit(1)

    target_dir = Path(sys.argv[1])
    if not target_dir.exists():
        print(f"错误: 目录不存在: {target_dir}")
        sys.exit(1)

    print("🔧 基于AST的精确括号修复工具")
    print("=" * 60)

    success_count = 0
    fail_count = 0
    fixed_count = 0

    # 遍历所有Python文件
    for file_path in target_dir.rglob('*.py'):
        result = fix_file(file_path)

        if result.get('success'):
            success_count += 1
            fixed_count += result.get('fix_count', 0)
            print(f"✅ {result['file']} (修复{result['fix_count']}处)")
        elif result.get('error'):
            fail_count += 1
            print(f"❌ {result['file']}: {result.get('error')}")

    print("=" * 60)
    print(f"📊 修复完成:")
    print(f"  成功: {success_count} 个文件")
    print(f"  失败: {fail_count} 个文件")
    print(f"  修复总数: {fixed_count} 处")


if __name__ == '__main__':
    main()
