#!/usr/bin/env python3
"""
批量修复core/framework/agents目录下的类型注解错误 v3

使用括号计数法精确匹配和修复
"""

import re
from pathlib import Path


def count_brackets(s: str, open_bracket: str, close_bracket: str) -> tuple[int, int]:
    """计算括号数量"""
    return s.count(open_bracket), s.count(close_bracket)


def fix_line_with_bracket_count(line: str) -> str:
    """使用括号计数法修复一行"""
    # 检查方括号是否平衡
    open_count, close_count = count_brackets(line, '[', ']')

    # 如果方括号不平衡，尝试修复
    if open_count > close_count:
        # 缺少右括号，在行尾添加
        missing = open_count - close_count
        # 在行尾的 -> 或 : 之前添加
        if ' -> ' in line:
            line = re.sub(r'(\s*->\s*)', ']' * missing + r'\1', line, count=1)
        elif line.rstrip().endswith(':'):
            line = line.rstrip()[:-1] + ']' * missing + ':\n'
        else:
            line = line.rstrip() + ']' * missing + '\n'

    elif close_count > open_count:
        # 多余的右括号，删除
        extra = close_count - open_count
        # 从后向前删除多余的 ]
        for _ in range(extra):
            pos = line.rfind(']')
            if pos != -1:
                line = line[:pos] + line[pos+1:]

    # 检查圆括号是否平衡（针对 dict[str, Any) 的情况）
    open_round, close_round = count_brackets(line, '(', ')')
    if close_round > open_round:
        # 检查是否是 dict[str, Any) 这种情况
        if '[str, Any)' in line:
            line = line.replace('[str, Any)', '[str, Any])')

    return line


def fix_type_annotations(content: str) -> tuple[str, int]:
    """
    修复类型注解错误

    Returns:
        (修复后的内容, 修复数量)
    """
    fixes = 0
    lines = content.split('\n')
    fixed_lines = []

    for i, line in enumerate(lines):
        original_line = line

        # 先应用括号计数法
        line = fix_line_with_bracket_count(line)

        # 再应用其他修复规则

        # 修复 Optional[list[dict[str, Any] 这种跨行情况
        if 'Optional[list[dict[str, Any]' in line and not line.strip().endswith(']'):
            # 检查下一行是否是 )
            if i + 1 < len(lines) and lines[i + 1].strip().startswith(')'):
                line = line.rstrip() + ']'

        # 修复 list[dict[str, Any]: 这种情况
        if re.search(r'list\[dict\[str, Any\][^\]]*\]:', line):
            line = re.sub(
                r'list\[dict\[str, Any\]([^\]]*)\]:',
                r'list[dict[str, Any]]\1]:',
                line
            )

        # 修复 -> dict[str, Any]: 但前面是 ) 的情况
        if ') -> dict[str, Any]:' in line and '[' in line:
            # 检查括号是否平衡
            open_count, close_count = count_brackets(line, '[', ']')
            if open_count > close_count:
                # 在 -> 之前添加 ]
                line = line.replace(' -> dict[str, Any]:', '] -> dict[str, Any]:')

        if line != original_line:
            fixes += 1

        fixed_lines.append(line)

    return '\n'.join(fixed_lines), fixes


def process_file(file_path: Path) -> tuple[bool, int]:
    """
    处理单个文件

    Returns:
        (是否成功, 修复数量)
    """
    try:
        # 读取文件
        content = file_path.read_text(encoding='utf-8')

        # 修复类型注解
        fixed_content, fixes = fix_type_annotations(content)

        if fixes > 0:
            # 写回文件
            file_path.write_text(fixed_content, encoding='utf-8')
            return True, fixes

        return True, 0

    except Exception as e:
        print(f"❌ 处理文件失败 {file_path}: {e}")
        return False, 0


def main():
    """主函数"""
    base_dir = Path('core/framework/agents')

    # 查找所有Python文件
    py_files = list(base_dir.rglob('*.py'))

    print(f"📁 找到 {len(py_files)} 个Python文件")
    print()

    total_fixes = 0
    success_count = 0
    error_count = 0

    for file_path in py_files:
        # 先检查是否有语法错误
        import subprocess
        result = subprocess.run(
            ['python3', '-m', 'py_compile', str(file_path)],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"🔧 修复: {file_path.relative_to(base_dir)}")
            success, fixes = process_file(file_path)
            if success:
                success_count += 1
                total_fixes += fixes
                if fixes > 0:
                    print(f"   修复了 {fixes} 处")
            else:
                error_count += 1
            print()

    print()
    print(f"📊 修复完成:")
    print(f"   - 成功处理: {success_count} 个文件")
    print(f"   - 修复错误: {total_fixes} 处")
    print(f"   - 失败: {error_count} 个文件")


if __name__ == '__main__':
    main()
