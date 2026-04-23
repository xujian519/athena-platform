#!/usr/bin/env python3
"""
最终的语法修复脚本 - 使用tokenize来精确定位问题
"""

import tokenize
import token
from pathlib import Path


def has_unmatched_brackets(file_path):
    """检查文件是否有不匹配的括号"""
    try:
        with open(file_path, 'rb') as f:
            tokens = list(tokenize.tokenize(f.readline))

        bracket_stack = []
        for tok in tokens:
            if tok.type == token.OP:
                if tok.string in ['[', '(', '{']:
                    bracket_stack.append((tok.string, tok.start))
                elif tok.string in [']', ')', '}']:
                    if not bracket_stack:
                        return True, tok.start[0], f"Unexpected closing '{tok.string}'"
                    last, pos = bracket_stack.pop()
                    if (last == '[' and tok.string != ']') or \
                       (last == '(' and tok.string != ')') or \
                       (last == '{' and tok.string != '}'):
                        return True, tok.start[0], f"Mismatched brackets: '{last}' vs '{tok.string}'"

        if bracket_stack:
            last, pos = bracket_stack[-1]
            return True, pos[0], f"Unclosed '{last}'"

        return False, None, None
    except Exception as e:
        return True, None, str(e)


def fix_common_issues(content):
    """修复常见的类型注解问题"""
    lines = content.split('\n')
    fixed_lines = []

    for i, line in enumerate(lines, 1):
        # 模式1: var: Type[...] = value  (缺少闭合括号)
        # 检测是否包含类型注解但缺少闭合括号
        if ': Optional[' in line or ': list[' in line or ': dict[' in line:
            # 计算括号
            open_brackets = line.count('[')
            close_brackets = line.count(']')

            if open_brackets > close_brackets:
                # 缺少闭合括号，在 = 前添加
                line = line.replace(' = ', '] = ', line.count(' = ') - 1)

        fixed_lines.append(line)

    return '\n'.join(fixed_lines)


def process_file(file_path):
    """处理单个文件"""
    has_error, line_num, msg = has_unmatched_brackets(file_path)

    if not has_error:
        return False

    print(f"🔧 {file_path.relative_to(file_path.parent.parent)}: Line {line_num or '?'} - {msg}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        fixed_content = fix_common_issues(content)

        if fixed_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)

            # 验证修复
            has_error_after, _, _ = has_unmatched_brackets(file_path)
            if not has_error_after:
                print(f"   ✅ 修复成功")
                return True
            else:
                print(f"   ⚠️  仍有问题")
                return False
    except Exception as e:
        print(f"   ❌ {e}")
        return False


def main():
    base = Path('/Users/xujian/Athena工作平台/core/framework/agents')

    print("🔍 扫描文件...")
    py_files = list(base.rglob('*.py'))

    fixed_count = 0
    for py_file in py_files:
        if process_file(py_file):
            fixed_count += 1

    print(f"\n📊 修复了 {fixed_count} 个文件")

    # 最终验证
    print("\n🔍 最终验证...")
    import ast
    error_files = []

    for py_file in py_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                ast.parse(f.read())
        except SyntaxError as e:
            error_files.append((py_file, e.lineno, str(e)))

    if error_files:
        print(f"⚠️  还有 {len(error_files)} 个文件有错误:")
        for f, line, err in error_files[:10]:
            print(f"   ❌ {f.relative_to(base)}:{line} - {err}")
        if len(error_files) > 10:
            print(f"   ... 还有 {len(error_files) - 10} 个")
    else:
        print("✅ 所有文件语法正确！")


if __name__ == "__main__":
    main()
