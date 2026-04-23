#!/usr/bin/env python3
"""
使用AST精确修复类型注解问题
"""

import ast
import re
from pathlib import Path
from typing import List, Tuple


def fix_type_annotations(content: str) -> Tuple[str, int]:
    """
    修复类型注解中的语法错误

    主要修复：
    1. Optional[xxx] = value → Optional[xxx]] = value
    2. Optional[Optional[xxx]] → Optional[xxx]
    """
    original = content
    fixes = 0

    # 1. 修复field()调用中的类型注解
    # 模式: Optional[xxx] = field(...) → Optional[xxx]] = field(...)
    lines = content.split('\n')
    fixed_lines = []

    for line in lines:
        fixed_line = line

        # 检测是否包含field()且Optional未闭合
        if 'field(' in line and 'Optional[' in line:
            # 找到Optional[... = field(的模式
            match = re.search(r'(Optional\[([^\[\]]+))\] = (\(field\()', line)
            if match:
                # 这种情况下，需要在]后添加一个]
                fixed_line = line.replace(
                    f'{match.group(1)}] = {match.group(3)}',
                    f'{match.group(1)}]] = {match.group(3)}'
                )
                fixes += 1

        # 2. 修复嵌套Optional
        if 'Optional[Optional[' in fixed_line:
            fixed_line = re.sub(r'Optional\[Optional\[([^\]]+)\]\]', r'Optional[\1]', fixed_line)
            fixes += 1

        # 3. 修复缺失的闭合括号（简单情况）
        # 检测: Optional[something] = None（缺少一个]）
        if re.search(r'Optional\[([^\[\]]+)\] = ', fixed_line):
            # 检查是否真的缺少括号
            optional_match = re.search(r'Optional\[([^\[\]]+)\]', fixed_line)
            if optional_match:
                inner = optional_match.group(1)
                # 如果内部不包含]，说明缺少闭合括号
                if ']' not in inner and '[' not in inner:
                    fixed_line = fixed_line.replace(
                        f'Optional[{inner}] = ',
                        f'Optional[{inner}]] = '
                    )
                    fixes += 1

        fixed_lines.append(fixed_line)

    content = '\n'.join(fixed_lines)

    # 4. 修复函数定义中的参数类型注解
    # 使用AST来解析和修复
    try:
        tree = ast.parse(content)
        # 如果解析成功，说明语法正确
        return content, fixes
    except SyntaxError:
        # AST解析失败，尝试更深入的修复
        pass

    # 5. 使用正则进行更深层的修复（谨慎使用）
    # 修复函数参数中的类型注解
    # 模式: def method(self, name: Optional[type = None)
    # 应该是: def method(self, name: Optional[type]] = None)

    # 查找所有函数定义行
    lines = content.split('\n')
    fixed_lines = []

    for i, line in enumerate(lines):
        fixed_line = line

        # 检查是否是函数定义行且包含Optional
        if re.match(r'\s*def\s+', line) and 'Optional[' in line:
            # 计算方括号平衡
            open_brackets = line.count('[')
            close_brackets = line.count(']')

            if open_brackets > close_brackets:
                # 缺少闭合括号，在行尾添加
                # 但要小心不要在注释中添加
                if '#' in line:
                    # 有注释，在注释前添加
                    code_part, comment_part = line.split('#', 1)
                    missing = open_brackets - close_brackets
                    fixed_line = code_part + ']' * missing + '  #' + comment_part
                else:
                    # 没有注释，直接添加
                    missing = open_brackets - close_brackets
                    fixed_line = line + ']' * missing

                fixes += 1

        fixed_lines.append(fixed_line)

    content = '\n'.join(fixed_lines)

    return content, fixes


def fix_file(file_path: Path) -> bool:
    """修复单个文件"""
    try:
        content = file_path.read_text(encoding='utf-8')
        fixed_content, fixes = fix_type_annotations(content)

        if fixes > 0:
            # 验证修复后的内容语法正确
            try:
                compile(fixed_content, str(file_path), 'exec')
                file_path.write_text(fixed_content, encoding='utf-8')
                return True
            except SyntaxError as e:
                print(f"⚠️  修复后仍有语法错误: {file_path.name} - {e.msg}")
                return False

        return False

    except Exception as e:
        print(f"❌ 处理失败 {file_path}: {e}")
        return False


def main():
    """主函数"""
    target_dir = Path("/Users/xujian/Athena工作平台/core/framework/agents")

    print("🚀 使用AST精确修复类型注解")
    print("=" * 60)

    fixed_count = 0
    error_count = 0

    for file_path in target_dir.rglob('*.py'):
        if not file_path.is_file():
            continue

        # 先检查是否有语法错误
        try:
            with open(file_path, 'r') as f:
                compile(f.read(), str(file_path), 'exec')
            continue  # 没有错误，跳过
        except SyntaxError:
            pass  # 有错误，需要修复

        if fix_file(file_path):
            fixed_count += 1
            print(f"✅ {file_path.relative_to(target_dir)}")
        else:
            error_count += 1
            print(f"❌ {file_path.relative_to(target_dir)}: 无法自动修复")

    print("=" * 60)
    print(f"📊 修复结果:")
    print(f"  成功修复: {fixed_count}")
    print(f"  修复失败: {error_count}")


if __name__ == "__main__":
    main()
