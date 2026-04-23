#!/usr/bin/env python3
"""
全面修复Python语法错误

处理：
1. 类型注解括号不匹配
2. 列表/字典语法错误
3. 函数定义参数错误
"""

import re
from pathlib import Path


def fix_common_syntax_errors(content: str) -> tuple[str, int]:
    """
    修复常见语法错误

    Returns:
        (修复后的内容, 修复数量)
    """
    fixes = 0
    lines = content.split('\n')
    i = 0
    fixed_lines = []

    while i < len(lines):
        line = lines[i]
        original_line = line

        # 修复1: _register_capabilities([] → _register_capabilities([
        if re.search(r'register_capabilities\(\[\]\s*$', line):
            next_line = lines[i + 1] if i + 1 < len(lines) else ''
            if next_line.strip() and not next_line.strip().startswith(']'):
                line = line.replace('[]', '[')
                fixes += 1

        # 修复2: Optional[list[dict[str, Any] → Optional[list[dict[str, Any]]]
        if re.search(r'Optional\[list\[dict\[str, Any\][^\]]*$', line):
            next_line = lines[i + 1] if i + 1 < len(lines) else ''
            if next_line.strip().startswith(')'):
                line = line.rstrip() + ']'
                fixes += 1

        # 修复3: def func(..., param: Type → def func(..., param: Type)
        if re.search(r'def \w+\(.*,\s*\w+:\s*\w+\s*$', line):
            next_line = lines[i + 1] if i + 1 < len(lines) else ''
            if next_line.strip().startswith(')'):
                # 检查是否缺少类型注解的闭合
                if '[' in line and line.count('[') > line.count(']'):
                    line = line.rstrip() + ']'
                    fixes += 1

        # 修复4: list[dict[str, Any]: → list[dict[str, Any]]:
        if re.search(r'list\[dict\[str, Any\][^\]]*\]:', line):
            line = re.sub(
                r'list\[dict\[str, Any\]([^\]]*)\]:',
                r'list[dict[str, Any]]\1]:',
                line
            )
            fixes += 1

        # 修复5: dict[str, Any] → dict[str, Any]]
        if re.search(r'dict\[str, Any\][^\]]*$', line):
            next_line = lines[i + 1] if i + 1 < len(lines) else ''
            if next_line.strip().startswith(']'):
                line = line.rstrip()
                fixes += 1

        # 修复6: 方括号计数修复
        open_count = line.count('[')
        close_count = line.count(']')
        if open_count > close_count and 'def ' in line:
            # 函数定义行，缺少 ]
            missing = open_count - close_count
            if ' -> ' in line:
                line = re.sub(r'(\s*->\s*)', ']' * missing + r'\1', line, count=1)
            elif line.rstrip().endswith(':'):
                line = line.rstrip()[:-1] + ']' * missing + ':'
            else:
                line = line.rstrip() + ']' * missing
            fixes += 1

        if line != original_line:
            print(f"  行 {i+1}: 修复")

        fixed_lines.append(line)
        i += 1

    return '\n'.join(fixed_lines), fixes


def process_file(file_path: Path) -> tuple[bool, int]:
    """处理单个文件"""
    try:
        content = file_path.read_text(encoding='utf-8')
        fixed_content, fixes = fix_common_syntax_errors(content)

        if fixes > 0:
            file_path.write_text(fixed_content, encoding='utf-8')
            return True, fixes

        return True, 0

    except Exception as e:
        print(f"❌ 处理文件失败 {file_path}: {e}")
        return False, 0


def main():
    """主函数"""
    base_dir = Path('core/framework/agents')
    py_files = list(base_dir.rglob('*.py'))

    print(f"📁 找到 {len(py_files)} 个Python文件\n")

    total_fixes = 0
    success_count = 0
    error_count = 0

    for file_path in py_files:
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
            else:
                error_count += 1

    print(f"\n📊 修复完成:")
    print(f"   - 成功处理: {success_count} 个文件")
    print(f"   - 修复错误: {total_fixes} 处")
    print(f"   - 失败: {error_count} 个文件")


if __name__ == '__main__':
    main()
