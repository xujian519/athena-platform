#!/usr/bin/env python3
"""
批量修复 core/framework/agents 目录下的类型注解错误
使用模式匹配和手动修复规则
"""
import re
import ast
from pathlib import Path
from typing import List, Tuple


def find_typing_errors(content: str) -> List[Tuple[int, str, str]]:
    """查找文件中的类型注解错误

    Returns:
        List of (line_number, error_type, matched_text)
    """
    errors = []
    lines = content.split('\n')

    for i, line in enumerate(lines, 1):
        # 模式1: 多余的 ]] (例如: -> dict[str, Any]]:)
        if re.search(r'\->[^[]*\]\]:', line):
            match = re.search(r'\->[^[]*\]\]:', line)
            errors.append((i, "extra_brackets", match.group()))

        # 模式2: 参数类型缺少 ] (例如: dict[str, Any) 后面是 , 或 ))
        if re.search(r':\s*dict\[str,\s*Any\)(?=\s*[,)])', line):
            match = re.search(r':\s*dict\[str,\s*Any\)(?=\s*[,)])', line)
            errors.append((i, "missing_bracket_param", match.group()))

        # 模式3: Optional[type[...)] 缺少 ]
        if re.search(r'Optional\[type\[[^\]]+\)(?=\s*[,)])', line):
            match = re.search(r'Optional\[type\[[^\]]+\)(?=\s*[,)])', line)
            errors.append((i, "missing_bracket_optional_type", match.group()))

        # 模式4: list[str] = field( 缺少 ]
        if re.search(r'Optional\[list\[str\]\s*=\s*field\(', line):
            match = re.search(r'Optional\[list\[str\]\s*=\s*field\(', line)
            errors.append((i, "missing_bracket_field", match.group()))

        # 模式5: Optional[dict[str, Any]]] 三个括号
        if re.search(r'Optional\[dict\[str,\s*Any\]\]\]', line):
            match = re.search(r'Optional\[dict\[str,\s*Any\]\]\]', line)
            errors.append((i, "triple_brackets", match.group()))

        # 模式6: -> dict[str, Any]] 后面跟逗号
        if re.search(r'\->[^\[]*\]\](?=\s*,)', line):
            match = re.search(r'\->[^\[]*\]\](?=\s*,)', line)
            errors.append((i, "extra_brackets_return_comma", match.group()))

        # 模式7: session_id=data.get("session_id", "")]]  多余括号
        if re.search(r'=\s*[^[\]]*\]\]\]', line):
            match = re.search(r'=\s*[^[\]]*\]\]\]', line)
            errors.append((i, "extra_brackets_get", match.group()))

        # 模式8: Optional[Agent] = 后面多余空格和括号
        if re.search(r'Optional\[[^\]]+\]\s*\]\s*=', line):
            match = re.search(r'Optional\[[^\]]+\]\s*\]\s*=', line)
            errors.append((i, "extra_bracket_assignment", match.group()))

        # 模式9: self._handlers[message_type]]] 多余括号
        if re.search(r'\[[^\]]+\]\]\]', line):
            match = re.search(r'\[[^\]]+\]\]\]', line)
            errors.append((i, "extra_brackets_subscript", match.group()))

    return errors


def apply_fixes(content: str, errors: List[Tuple[int, str, str]]) -> Tuple[str, int]:
    """应用修复

    Returns:
        (fixed_content, fix_count)
    """
    lines = content.split('\n')
    fix_count = 0

    for line_num, error_type, _ in errors:
        if line_num - 1 >= len(lines):
            continue

        line = lines[line_num - 1]
        original_line = line
        fixed_line = line

        if error_type == "extra_brackets":
            # -> dict[str, Any]]: → -> dict[str, Any]:
            fixed_line = re.sub(r'\]\]:', ']:', fixed_line)

        elif error_type == "extra_brackets_return_comma":
            # -> dict[str, Any]], → -> dict[str, Any],
            fixed_line = re.sub(r'\]\](?=\s*,)', ']', fixed_line)

        elif error_type == "missing_bracket_param":
            # : dict[str, Any) → : dict[str, Any])
            fixed_line = re.sub(
                r':\s*(dict\[str,\s*Any\))(?=\s*[,)])',
                r': \1]',
                fixed_line
            )

        elif error_type == "missing_bracket_optional_type":
            # Optional[type[X)] → Optional[type[X]]
            fixed_line = re.sub(
                r'Optional\[type\[([^\]]+)\)(?=\s*[,)])',
                r'Optional[type[\1]]',
                fixed_line
            )

        elif error_type == "missing_bracket_field":
            # Optional[list[str] = field( → Optional[list[str]] = field(
            fixed_line = re.sub(
                r'Optional\[list\[str\](\s*=\s*field\()',
                r'Optional[list[str]]\1',
                fixed_line
            )

        elif error_type == "triple_brackets":
            # Optional[dict[str, Any]]] → Optional[dict[str, Any]]
            fixed_line = re.sub(r'Optional\[dict\[str,\s*Any\]\]\]', 'Optional[dict[str, Any]]', fixed_line)

        elif error_type == "extra_brackets_get":
            # = ...")]] → = ...")
            fixed_line = re.sub(r'\]\]\]', '"]', fixed_line)

        elif error_type == "extra_bracket_assignment":
            # Optional[Agent] ] = → Optional[Agent] =
            fixed_line = re.sub(r'(\s*])\s*=\s*$', r' =', fixed_line)

        elif error_type == "extra_brackets_subscript":
            # handlers[key]]] → handlers[key]
            fixed_line = re.sub(r'\]\]\]', ']]', fixed_line)

        if fixed_line != original_line:
            lines[line_num - 1] = fixed_line
            fix_count += 1
            print(f"  行{line_num} ({error_type}): 已修复")

    return '\n'.join(lines), fix_count


def process_file(file_path: Path) -> Tuple[bool, int]:
    """处理单个文件"""
    print(f"\n{'='*60}")
    print(f"处理文件: {file_path.name}")
    print(f"{'='*60}")

    try:
        # 读取文件
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 查找错误
        errors = find_typing_errors(content)

        if not errors:
            print("✓ 未发现类型注解错误")
            return True, 0

        print(f"发现 {len(errors)} 处错误:")
        for line_num, error_type, matched_text in errors:
            print(f"  行{line_num} [{error_type}]: {matched_text.strip()[:60]}")

        # 应用修复
        fixed_content, fix_count = apply_fixes(content, errors)

        if fix_count == 0:
            print("⚠️  未应用任何修复")
            return True, 0

        # 验证语法
        try:
            ast.parse(fixed_content)
        except SyntaxError as e:
            print(f"✗ 修复后语法错误: {e.msg} at line {e.lineno}")
            return False, 0

        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)

        print(f"✓ 成功修复 {fix_count} 处")
        return True, fix_count

    except Exception as e:
        print(f"✗ 处理失败: {e}")
        import traceback
        traceback.print_exc()
        return False, 0


def main():
    """主函数"""
    target_dir = Path("/Users/xujian/Athena工作平台/core/framework/agents")

    if not target_dir.exists():
        print(f"✗ 目录不存在: {target_dir}")
        return

    # 查找所有Python文件
    python_files = list(target_dir.rglob("*.py"))
    print(f"找到 {len(python_files)} 个Python文件")

    # 统计
    total_files = 0
    successful_files = 0
    total_fixes = 0
    files_with_errors = 0

    # 处理每个文件
    for file_path in sorted(python_files):
        total_files += 1
        success, fixes = process_file(file_path)
        if success:
            successful_files += 1
            if fixes > 0:
                files_with_errors += 1
                total_fixes += fixes

    # 输出统计
    print(f"\n{'='*60}")
    print(f"处理完成！")
    print(f"{'='*60}")
    print(f"  总文件数: {total_files}")
    print(f"  成功处理: {successful_files}")
    print(f"  有错误的文件: {files_with_errors}")
    print(f"  修复总数: {total_fixes} 处")


if __name__ == "__main__":
    main()
