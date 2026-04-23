#!/usr/bin/env python3
"""
手动修复批次1 - 全面修复最常见的102个括号不匹配错误
"""

import re
from pathlib import Path


def fix_bracket_mismatches(content: str) -> str:
    """修复所有类型的括号不匹配错误"""

    # ========================================
    # 类型1: set[str | None = None: → set[str] | None = None:
    # 最多见：102个错误中的大部分
    # ========================================
    content = re.sub(
        r'set\[str\s*\|\s*None\s*=\s*None:\s*$',
        r'set[str] | None = None:',
        content
    )

    content = re.sub(
        r'set\[str\s*\|\s*None\s*=\s*None,',
        r'set[str] | None = None,',
        content
    )

    content = re.sub(
        r'exclude_paths:\s*set\[str\s*\|\s*None\s*=\s*None,',
        r'exclude_paths: set[str] | None = None,',
        content
    )

    content = re.sub(
        r'include_paths:\s*set\[str\s*\|\s*None\s*=\s*None,',
        r'include_paths: set[str] | None = None,',
        content
    )

    # ========================================
    # 类型2: dict[str, list[str] = {} (未闭合的括号)
    # 44个错误
    # ========================================
    content = re.sub(
        r'self\.(\w+):\s*dict\[str,\s*list\[str\]\s*=\s*{}',
        r'self.\1: dict[str, list[str] = {}',
        content
    )

    content = re.sub(
        r'self\.(\w+):\s*dict\[str,\s*list\[str\]\s*=\s*defaultdict\(',
        r'self.\1: dict[str, list[str] = defaultdict(',
        content
    )

    content = re.sub(
        r'(\w+):\s*dict\[str,\s*list\[str\]\s*=\s*\{\}',
        r'\1: dict[str, list[str] = {}',
        content
    )

    # ========================================
    # 类型3: 参数类型中的 ]| None
    # 19个错误
    # ========================================
    content = re.sub(
        r':\s*([a-zA-Z0-9_]+)\])\s*\|\s*None\s*=\s*None',
        r': \1 | None = None',
        content
    )

    content = re.sub(
        r':\s*([a-zA-Z0-9_]+)\])\s*\|\s*None\s*=\s*None,',
        r': \1 | None = None,',
        content
    )

    content = re.sub(
        r':\s*list\[int\])\s*\|\s*None\s*=\s*None',
        r': list[int] | None = None',
        content
    )

    content = re.sub(
        r':\s*list\[str\]\]\s*\|\s*None\s*=\s*None',
        r': list[str] | None = None',
        content
    )

    # ========================================
    # 类型4: 双重None赋值
    # 6个错误
    # ========================================
    content = re.sub(
        r':\s*bool\s*=\s*False\s*\|\s*None\s*=\s*None,',
        r': bool | None = None,',
        content
    )

    content = re.sub(
        r'(\w+):\s*([a-zA-Z0-9_\[\],:\s]+?)\s*=\s*[a-zA-Z0-9_]+\s*\|\s*None\s*=\s*None',
        r'\1: \2 | None = None',
        content
    )

    content = re.sub(
        r':\s*dict\s*\|\s*None\s*=\s*None',
        r': dict | None = None',
        content
    )

    # ========================================
    # 类型5: 缺少闭合括号的返回类型
    # ========================================
    # ) -> list[list[str]: 添加缺失的括号
    content = re.sub(
        r'(\)\s*->\s*)(list\[list\[str\]\]):',
        r'\1\2]:',
        content
    )

    content = re.sub(
        r'(\)\s*->\s*)(dict\[str,\s*list\[dict\[str,\s*Any\]\]\]):',
        r'\1\2]:',
        content
    )

    # ========================================
    # 类型6: 参数列表中的未闭合括号
    # ========================================
    # param: dict[str, | None = None
    content = re.sub(
        r':\s*dict\[str,\s*\|\s*None\s*=\s*None',
        r': dict[str, Any] | None = None',
        content
    )

    content = re.sub(
        r':\s*list\[dict\[str,\s*Any\]\s*\|\s*None\s*=\s*None',
        r': list[dict[str, Any] | None = None',
        content
    )

    content = re.sub(
        r':\s*Optional\[Any\]\s*\n\s*def',
        r': Optional[Any] = None):\n        def',
        content
    )

    content = re.sub(
        r':\s*Optional\[str\]\s*\n\s*def',
        r': Optional[str] = None):\n        def',
        content
    )

    # ========================================
    # 类型7: 修复 except 块
    # ========================================
    lines = content.split('\n')
    fixed_lines = []

    for i, line in enumerate(lines):
        fixed_lines.append(line)

        # 如果是 except 行且下一行缩进不正确
        if re.match(r'^\s*except\s+', line):
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                # 如果下一行是空行或缩进太小，添加 pass
                if not next_line.strip() or (next_line.strip() and not next_line.startswith('#')):
                    current_indent = len(line) - len(line.lstrip())
                    next_indent = len(next_line) - len(next_line.lstrip()) if next_line.strip() else 0

                    if next_indent < current_indent and next_indent == 0:
                        # 添加 pass 语句
                        indent = ' ' * (current_indent + 4)
                        fixed_lines[-1] = line
                        fixed_lines.append(f'{indent}pass  # TODO: 实现异常处理')

    content = '\n'.join(fixed_lines)

    return content

def fix_file_safe(file_path: Path) -> bool:
    """安全地修复文件"""
    try:
        content = file_path.read_text(encoding='utf-8')

        # 只修复有错误的文件
        try:
            compile(content, str(file_path), 'exec')
            return False
        except SyntaxError:
            pass

        # 应用修复
        fixed = fix_bracket_mismatches(content)

        if fixed != content:
            # 验证修复
            try:
                compile(fixed, str(file_path), 'exec')
                file_path.write_text(fixed, encoding='utf-8')
                return True
            except SyntaxError:
                pass
        return False
    except Exception:
        return False

def main():
    core_path = Path('/Users/xujian/Athena工作平台/core')

    print("=" * 80)
    print("🔧 手动修复批次1 - 括号不匹配错误")
    print("=" * 80)

    # 多轮修复
    total_fixed = 0
    for round_num in range(1, 8):
        print(f"\n第{round_num}轮...")

        error_files = []
        for f in core_path.rglob('*.py'):
            try:
                compile(f.read_text(encoding='utf-8'), str(f), 'exec')
            except SyntaxError:
                error_files.append(f)

        if not error_files:
            print("✅ 所有文件语法正确!")
            break

        fixed_count = 0
        for f in error_files:
            if fix_file_safe(f):
                fixed_count += 1
                print(f"  ✅ {f.relative_to(core_path.parent)}")

        total_fixed += fixed_count
        print(f"   本轮修复: {fixed_count} 个")
        print(f"   剩余错误: {len(error_files) - fixed_count} 个")

        if fixed_count == 0:
            print("   自动修复达到极限")
            break

    # 最终统计
    all_files = list(core_path.rglob('*.py'))
    error_count = 0
    success_count = 0

    for f in all_files:
        try:
            compile(f.read_text(encoding='utf-8'), str(f), 'exec')
            success_count += 1
        except SyntaxError:
            error_count += 1

    print("\n" + "=" * 80)
    print(f"✅ 本批次修复: {total_fixed} 个文件")
    print(f"📊 当前状态: {success_count}/{len(all_files)} ({success_count*100//len(all_files)}%)")
    print(f"⚠️ 剩余错误: {error_count} 个文件")
    print("=" * 80)

    return success_count, error_count

if __name__ == "__main__":
    main()
