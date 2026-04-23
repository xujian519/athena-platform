#!/usr/bin/env python3
"""
精确修复类型注解中的方括号不匹配问题
只修复类型注解中的问题，不影响正常的列表/字典初始化
"""
import re
from pathlib import Path


def fix_typing_brackets(content: str) -> tuple[str, int]:
    """修复类型注解中的方括号不匹配

    主要模式：
    1. -> dict[str, Any]]: → -> dict[str, Any]:
    2. Optional[list[str] → Optional[list[str]]
    3. Optional[type[BaseAgent) → Optional[type[BaseAgent]]
    """
    fix_count = 0
    lines = content.split('\n')
    fixed_lines = []

    for line_num, line in enumerate(lines, 1):
        original_line = line
        fixed_line = line

        # 模式1: 修复返回类型中多余的 ]] (例如: -> dict[str, Any]]:)
        if re.search(r'\->[^[]*\]\]:', fixed_line):
            fixed_line = re.sub(r'\]\]:', ']:', fixed_line)
            if fixed_line != original_line:
                fix_count += 1
                print(f"  行{line_num}: 修复多余]]")
                print(f"    原始: {original_line.strip()}")
                print(f"    修复: {fixed_line.strip()}")

        # 模式2: 修复返回类型中多余的 ]] 后跟其他符号
        if re.search(r'\->[^[]*\]\],', fixed_line):
            fixed_line = re.sub(r'\]\],', '],', fixed_line)
            if fixed_line != original_line:
                fix_count += 1
                print(f"  行{line_num}: 修复多余]],")
                print(f"    原始: {original_line.strip()}")
                print(f"    修复: {fixed_line.strip()}")

        # 模式3: 修复类型注解中缺少的 ] (例如: Optional[list[str] = field()
        # 这种情况需要更仔细处理，只修复类型注解部分
        if re.search(r'Optional\[list\[str\]\s*=\s*field\(', fixed_line):
            fixed_line = re.sub(
                r'Optional\[list\[str\](\s*=\s*field\()',
                r'Optional[list[str]]\1',
                fixed_line
            )
            if fixed_line != original_line:
                fix_count += 1
                print(f"  行{line_num}: 修复缺少的]")
                print(f"    原始: {original_line.strip()}")
                print(f"    修复: {fixed_line.strip()}")

        # 模式4: 修复参数类型中缺少的 ] (例如: dict[str, Any) → dict[str, Any])
        # 只在函数参数的上下文中修复
        if re.search(r':\s*dict\[str,\s*Any\)[,)]', fixed_line):
            fixed_line = re.sub(
                r':\s*dict\[str,\s*Any\)([,)])',
                r': dict[str, Any]\1',
                fixed_line
            )
            if fixed_line != original_line:
                fix_count += 1
                print(f"  行{line_num}: 修复参数类型缺少]")
                print(f"    原始: {original_line.strip()}")
                print(f"    修复: {fixed_line.strip()}")

        # 模式5: 修复 Optional[type[X)] → Optional[type[X]]
        if re.search(r'Optional\[type\[[^\]]+\)[,\)]', fixed_line):
            fixed_line = re.sub(
                r'Optional\[type\[[^\]]+\)([,\)])',
                r'Optional[type[\1\1]',
                fixed_line
            )
            if fixed_line != original_line:
                fix_count += 1
                print(f"  行{line_num}: 修复Optional[type[...)]")
                print(f"    原始: {original_line.strip()}")
                print(f"    修复: {fixed_line.strip()}")

        # 模式6: 修复 -> dict[str, Any]]  (没有冒号的情况)
        if re.search(r'\->[^\[]*\]\](?!\s*[:,\n])', fixed_line):
            fixed_line = re.sub(r'\]\](?!\s*[:,\n])', ']', fixed_line, count=1)
            if fixed_line != original_line:
                fix_count += 1
                print(f"  行{line_num}: 修复]] → ]")
                print(f"    原始: {original_line.strip()}")
                print(f"    修复: {fixed_line.strip()}")

        # 模式7: 修复 dict[str, Any] = 后面缺少的情况
        if re.search(r'dict\[str,\s*Any\]\s*=\s*$', fixed_line):
            # 这种情况可能是多行定义，保持原样
            pass

        fixed_lines.append(fixed_line)

    return '\n'.join(fixed_lines), fix_count


def verify_syntax(content: str) -> bool:
    """验证Python语法"""
    try:
        import ast
        ast.parse(content)
        return True
    except SyntaxError as e:
        print(f"    语法错误: {e.msg} at line {e.lineno}")
        return False


def process_file(file_path: Path) -> tuple[bool, int]:
    """处理单个文件"""
    print(f"\n处理文件: {file_path.name}")

    try:
        # 读取文件
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 修复类型注解
        fixed_content, fix_count = fix_typing_brackets(content)

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
    print("=" * 60)

    # 统计
    total_files = 0
    successful_files = 0
    total_fixes = 0

    # 处理每个文件
    for file_path in sorted(python_files):
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
