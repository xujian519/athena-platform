#!/usr/bin/env python3
"""
批量修复 core/framework/agents 目录下的类型注解错误
主要修复方括号不匹配的问题
"""
import re
import ast
from pathlib import Path
from typing import Tuple, List


def check_bracket_balance(line: str) -> Tuple[bool, int]:
    """检查一行代码中的方括号是否平衡

    Args:
        line: 代码行

    Returns:
        (是否平衡, 方括号数量)
    """
    open_brackets = line.count('[')
    close_brackets = line.count(']')
    return open_brackets == close_brackets, open_brackets - close_brackets


def fix_typing_annotations(content: str) -> Tuple[str, int]:
    """修复类型注解中的方括号不匹配问题

    Args:
        content: 文件内容

    Returns:
        (修复后的内容, 修复数量)
    """
    lines = content.split('\n')
    fixed_lines = []
    fix_count = 0

    for i, line in enumerate(lines):
        # 检查是否包含类型注解
        if '[' in line or ']' in line:
            is_balanced, bracket_diff = check_bracket_balance(line)

            if not is_balanced:
                # 需要修复
                original_line = line
                fixed_line = line

                # 模式1: 缺少闭合括号 - 例如: Optional[type[BaseAgent) → Optional[type[BaseAgent]]]
                if bracket_diff > 0:  # 缺少 ] 括号
                    # 在行尾添加缺少的括号
                    if line.rstrip().endswith(':'):
                        fixed_line = line.rstrip()[:-1] + ']' + ':'
                    elif line.rstrip().endswith(','):
                        fixed_line = line.rstrip()[:-1] + ']' + ','
                    elif line.rstrip().endswith('='):
                        fixed_line = line.rstrip()[:-1] + ']' + ' ='
                    else:
                        # 在最后一个非空格字符后添加 ]
                        fixed_line = line.rstrip() + ']'

                # 模式2: 多余的闭合括号 - 例如: -> dict[str, Any]]: → -> dict[str, Any]:
                elif bracket_diff < 0:  # 多余 ] 括号
                    # 移除多余的 ] 括号
                    # 在行尾查找连续的 ] 符号并移除多余的
                    stripped = line.rstrip()
                    extra_brackets = abs(bracket_diff)

                    # 处理不同行尾情况
                    if stripped.endswith(':'):
                        base = stripped[:-1]
                        # 从末尾移除多余的 ]
                        while extra_brackets > 0 and base.endswith(']'):
                            base = base[:-1]
                            extra_brackets -= 1
                        fixed_line = base + ':' + line[len(stripped):]
                    elif stripped.endswith(','):
                        base = stripped[:-1]
                        while extra_brackets > 0 and base.endswith(']'):
                            base = base[:-1]
                            extra_brackets -= 1
                        fixed_line = base + ',' + line[len(stripped):]
                    else:
                        base = stripped
                        while extra_brackets > 0 and base.endswith(']'):
                            base = base[:-1]
                            extra_brackets -= 1
                        fixed_line = base + line[len(stripped):]

                if fixed_line != original_line:
                    # 验证修复后的行是否平衡
                    is_fixed_balanced, _ = check_bracket_balance(fixed_line)
                    if is_fixed_balanced:
                        fixed_lines.append(fixed_line)
                        fix_count += 1
                        print(f"  行 {i+1}: 修复")
                        print(f"    原始: {original_line.strip()}")
                        print(f"    修复: {fixed_line.strip()}")
                    else:
                        # 修复后仍不平衡，保留原行
                        fixed_lines.append(original_line)
                        print(f"  行 {i+1}: ⚠️  修复后仍不平衡，保留原行")
                else:
                    fixed_lines.append(original_line)
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)

    return '\n'.join(fixed_lines), fix_count


def verify_syntax(content: str) -> bool:
    """验证 Python 代码语法是否正确

    Args:
        content: Python 代码内容

    Returns:
        语法是否正确
    """
    try:
        ast.parse(content)
        return True
    except SyntaxError as e:
        print(f"    语法错误: {e}")
        return False


def process_file(file_path: Path) -> Tuple[bool, int]:
    """处理单个文件

    Args:
        file_path: 文件路径

    Returns:
        (是否成功, 修复数量)
    """
    print(f"\n处理文件: {file_path.name}")

    try:
        # 读取文件
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()

        # 修复类型注解
        fixed_content, fix_count = fix_typing_annotations(original_content)

        if fix_count == 0:
            print("  ✓ 无需修复")
            return True, 0

        # 验证语法
        if not verify_syntax(fixed_content):
            print("  ✗ 修复后语法错误，跳过写入")
            return False, 0

        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)

        print(f"  ✓ 成功修复 {fix_count} 处")
        return True, fix_count

    except Exception as e:
        print(f"  ✗ 处理失败: {e}")
        return False, 0


def main():
    """主函数"""
    # 目标目录
    target_dir = Path("/Users/xujian/Athena工作平台/core/framework/agents")

    if not target_dir.exists():
        print(f"✗ 目录不存在: {target_dir}")
        return

    # 查找所有 Python 文件
    python_files = list(target_dir.rglob("*.py"))

    print(f"找到 {len(python_files)} 个 Python 文件")
    print("=" * 60)

    # 统计
    total_files = 0
    successful_files = 0
    total_fixes = 0

    # 处理每个文件
    for file_path in python_files:
        total_files += 1
        success, fixes = process_file(file_path)
        if success:
            successful_files += 1
            total_fixes += fixes

    # 输出统计
    print("\n" + "=" * 60)
    print(f"处理完成！")
    print(f"  总文件数: {total_files}")
    print(f"  成功处理: {successful_files}")
    print(f"  修复数量: {total_fixes} 处")


if __name__ == "__main__":
    main()
