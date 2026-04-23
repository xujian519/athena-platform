#!/usr/bin/env python3
"""
认知与决策模块逻辑错误修复工具
Logic Error Fixer for Cognitive & Decision Module

自动修复常见的逻辑错误：
- cannot assign to function call
- except语句后缺少缩进块
- dict.get(str, Any) 模式错误

作者: Athena Platform Team
版本: v1.0
"""

import os
import re
import ast
from pathlib import Path
from typing import List, Tuple


def fix_cannot_assign_to_function_call(file_path: str) -> int:
    """
    修复 "cannot assign to function call" 错误

    常见错误模式：
    - func().attr = value  →  temp = func(); temp.attr = value
    - func()[index] = value →  temp = func(); temp[index] = value
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original = content
        fixed_count = 0

        # 模式1: 修复 dict.get(str, Any) = value
        # 这种模式应该是: dict.get(str, default_value)
        pattern1 = r'\.get\(([^,]+),\s*Any\)\s*='
        matches1 = list(re.finditer(pattern1, content))

        for match in reversed(matches1):
            # 提取字典名和键
            dict_call = content[max(0, match.start()-50):match.end()]
            # 简单修复：将 Any 替换为 None
            fixed = content[:match.start()] + re.sub(r',\s*Any\)', ', None)', content[match.start():match.end()]) + content[match.end():]
            content = fixed
            fixed_count += 1

        # 模式2: 修复 obj.method() = value
        # 这种需要检查是否是对属性赋值
        lines = content.split('\n')
        new_lines = []

        for i, line in enumerate(lines):
            # 检测赋值语句
            if '=' in line and '(' in line and ')' in line:
                # 简单检查：左边有函数调用模式
                left_side = line.split('=')[0].strip()

                # 检测: something().something =
                if re.search(r'\w+\(\)\.\w+\s*$', left_side):
                    # 需要重写
                    func_call = re.match(r'(\w+)\(\)', left_side.split('.')[0])
                    if func_call:
                        func_name = func_call.group(1)
                        rest = left_side[len(func_name)+3:]  # 跳过 '().'
                        right_side = line.split('=', 1)[1].strip()

                        # 生成新代码
                        indent = len(line) - len(line.lstrip())
                        new_lines.append(' ' * indent + f'__temp_{i} = {func_name}()')
                        new_lines.append(' ' * indent + f'__temp_{i}.{rest} = {right_side}')
                        fixed_count += 1
                        continue

            new_lines.append(line)

        if content != original:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines) if new_lines else content)

        return fixed_count

    except Exception as e:
        print(f"❌ 修复 {file_path} 失败: {e}")
        return 0


def fix_empty_except_blocks(file_path: str) -> int:
    """修复空的except块"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        fixed_count = 0
        new_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]
            new_lines.append(line)

            # 检测except行
            if 'except' in line and ('Exception' in line or 'Error' in line or ':' in line):
                # 检查下一行
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    # 如果下一行是空的或只有注释，且缩进正确
                    if next_line.strip() == '' or (next_line.strip().startswith('#') and 'pass' not in next_line):
                        # 添加pass语句
                        indent = len(line) - len(line.lstrip())
                        if indent > 0:
                            pass_line = ' ' * (indent + 4) + 'pass  # TODO: 添加适当的错误处理\n'
                            new_lines.append(pass_line)
                            fixed_count += 1

            i += 1

        if fixed_count > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)

        return fixed_count

    except Exception as e:
        print(f"❌ 修复 {file_path} except块失败: {e}")
        return 0


def fix_dict_get_any_pattern(file_path: str) -> int:
    """修复 dict.get(str, Any) 模式"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original = content
        fixed_count = 0

        # 模式: .get(key, Any)
        # 修复为: .get(key, None)
        pattern = r'\.get\(([^,]+),\s*Any\)'
        matches = list(re.finditer(pattern, content))

        # 从后往前替换，保持位置正确
        for match in reversed(matches):
            replacement = f".get({match.group(1)}, None)"
            content = content[:match.start()] + replacement + content[match.end():]
            fixed_count += 1

        if content != original:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

        return fixed_count

    except Exception as e:
        print(f"❌ 修复 {file_path} dict.get模式失败: {e}")
        return 0


def fix_return_in_try_block(file_path: str) -> int:
    """
    修复 try-except 块中的 return 语句位置

    常见问题:
    try:
        return something
    except Exception as e:
        return something_else
    # 后续代码永远不会执行
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # 简单检测：try块有return，except块也有return
        # 这种模式本身可能是有意的，不强制修改
        # 只记录潜在问题
        return 0

    except Exception as e:
        return 0


def scan_and_fix_specific_files() -> Tuple[int, int]:
    """扫描并修复已知的特定问题文件"""
    fixed_total = 0
    files_fixed = 0

    # 已知有问题的文件列表
    problem_files = [
        'core/evaluation/evaluation_engine.py',
        'core/evaluation/patent_retrieval_metrics.py',
        'core/evaluation/async_file_ops.py',
        'core/evaluation/test_enhanced_evaluation.py',
        'core/evaluation/xiaonuo_feedback_system.py',
        'core/evaluation/enhanced_evaluation_module.py',
        'core/evaluation/lightweight_evaluation_engine.py',
    ]

    for file_path in problem_files:
        full_path = Path(file_path)
        if not full_path.exists():
            print(f"⚠️  文件不存在: {file_path}")
            continue

        print(f"\n📝 检查: {file_path}")

        fixes = 0
        fixes += fix_empty_except_blocks(str(full_path))
        fixes += fix_dict_get_any_pattern(str(full_path))
        fixes += fix_cannot_assign_to_function_call(str(full_path))

        if fixes > 0:
            print(f"   ✅ 修复了 {fixes} 个问题")
            fixed_total += fixes
            files_fixed += 1
        else:
            print(f"   ℹ️  无需修复")

    return files_fixed, fixed_total


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="认知与决策模块逻辑错误修复工具")
    parser.add_argument('--files', nargs='+', help='要修复的文件列表')
    parser.add_argument('--dir', help='要修复的目录')
    parser.add_argument('--all', action='store_true', help='修复所有已知问题')
    parser.add_argument('--scan', action='store_true', help='仅扫描不修复')

    args = parser.parse_args()

    if args.all:
        print("🔧 开始修复认知与决策模块的逻辑错误...")
        files_fixed, total_fixes = scan_and_fix_specific_files()
        print(f"\n✅ 修复完成!")
        print(f"   修复文件数: {files_fixed}")
        print(f"   修复问题数: {total_fixes}")
    elif args.files:
        for file_path in args.files:
            if not os.path.exists(file_path):
                print(f"⚠️  文件不存在: {file_path}")
                continue

            print(f"📝 修复: {file_path}")
            fixes = 0
            fixes += fix_empty_except_blocks(file_path)
            fixes += fix_dict_get_any_pattern(file_path)
            fixes += fix_cannot_assign_to_function_call(file_path)

            if fixes > 0:
                print(f"   ✅ 修复了 {fixes} 个问题")
    else:
        print("💡 使用 --all 修复所有已知问题")
        print("💡 使用 --files 指定要修复的文件")
        print("💡 使用 --scan 仅扫描问题")


if __name__ == '__main__':
    main()
