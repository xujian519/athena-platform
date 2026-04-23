#!/usr/bin/env python3
"""
智能语法修复工具
修复Python 3.9+类型注解的常见语法错误
"""
import os
import re
import sys
from pathlib import Path


def fix_type_annotations(content: str) -> tuple[str, int]:
    """
    修复类型注解中的括号匹配问题

    Returns:
        (修复后的内容, 修复数量)
    """
    original_content = content
    fix_count = 0

    # 修复1: Optional[list[str] = None -> Optional[list[str]] = None
    # 匹配缺少第二个]的情况
    pattern1 = r'Optional\[list\[str\](?=\s*=\s*None)'
    matches1 = re.findall(pattern1, content)
    if matches1:
        content = re.sub(pattern1, r'Optional[list[str]]', content)
        fix_count += len(matches1)

    # 修复2: Optional[dict[str, Any] = None -> Optional[dict[str, Any]] = None
    pattern2 = r'Optional\[dict\[str,\s*Any\](?=\s*=\s*None)'
    matches2 = re.findall(pattern2, content)
    if matches2:
        content = re.sub(pattern2, r'Optional[dict[str, Any]]', content)
        fix_count += len(matches2)

    # 修复3: list[dict[str, Any] -> list[dict[str, Any]]
    pattern3 = r'\blist\[dict\[str,\s*Any\](?=\])'
    matches3 = re.findall(pattern3, content)
    if matches3:
        content = re.sub(pattern3, r'list[dict[str, Any]]', content)
        fix_count += len(matches3)

    # 修复4: 处理其他类似的模式
    # dict[str, Any] = None -> dict[str, Any] = None (应该已经有两个括号)
    # list[str] = None -> list[str] = None (应该已经有括号)
    # 修复: ]]] -> ]] (多余的三重括号)
    content = re.sub(r'\]\]\]', r']]', content)

    # 修复: ]]] -> ]] (双重括号在某些上下文中)
    # 但要小心不要破坏正确的]]（例如在字符串中）
    # 只在类型注解行中修复
    lines = content.split('\n')
    fixed_lines = []
    for line in lines:
        # 跳过注释和空行
        if line.strip().startswith('#') or not line.strip():
            fixed_lines.append(line)
            continue

        # 在类型注解中，如果有]]在=号之前，可能是多余的
        # 但要确保不会破坏合法的嵌套
        if '=' in line and ']]' in line:
            # 检查是否在类型注解部分（=之前）
            parts = line.split('=', 1)
            type_part = parts[0]

            # 如果类型部分有]]，可能是多余的
            # 例如: dict[str, Task]] =  -> dict[str, Task] =
            if type_part.count(']') > type_part.count('[') + 1:
                # 有多余的右括号
                line = re.sub(r'\]+(\s*=\s*)', lambda m: ']' * (type_part.count('[') - 1) + m.group(1), line, count=1)

        fixed_lines.append(line)

    content = '\n'.join(fixed_lines)

    # 修复4: 谨慎修复多余的]]（只在类型注解上下文中）
    # 避免]]在字符串、注释中的误修复
    lines = content.split('\n')
    fixed_lines = []
    for line in lines:
        # 跳过注释和字符串
        stripped = line.strip()
        if stripped.startswith('#') or '"""' in line or "'''" in line:
            fixed_lines.append(line)
            continue

        # 修复类型注解中的多余]]
        # 匹配模式: ]表达式]]  -> ]表达式]
        # 例如: dict[str, int]]] -> dict[str, int]]
        if ']]' in line and not line.strip().startswith('#'):
            # 使用更精确的正则，只在类型注解中修复
            # 匹配: <类型>]] = <值>
            line = re.sub(r'(\])\]+(\s*=\s*)', r'\1\2', line)
            fix_count += 1

        fixed_lines.append(line)

    content = '\n'.join(fixed_lines)

    return content, fix_count


def validate_syntax(file_path: Path) -> bool:
    """验证Python文件语法"""
    import py_compile
    try:
        py_compile.compile(str(file_path), doraise=True)
        return True
    except py_compile.PyCompileError as e:
        return False


def fix_file(file_path: Path, dry_run: bool = False) -> dict:
    """修复单个文件"""
    result = {
        'file': str(file_path),
        'fixed': False,
        'fix_count': 0,
        'error': None
    }

    try:
        # 读取文件
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 修复类型注解
        fixed_content, fix_count = fix_type_annotations(content)

        if fix_count > 0:
            result['fix_count'] = fix_count

            if not dry_run:
                # 写入修复后的内容
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)

                # 验证语法
                if validate_syntax(file_path):
                    result['fixed'] = True
                else:
                    result['error'] = '语法验证失败'
                    # 恢复原内容
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    result['fixed'] = False
            else:
                result['fixed'] = True  # dry run模式假设成功

    except Exception as e:
        result['error'] = str(e)

    return result


def main():
    import argparse

    parser = argparse.ArgumentParser(description='修复Python类型注解语法错误')
    parser.add_argument('path', nargs='?', default='.', help='文件或目录路径')
    parser.add_argument('--dry-run', action='store_true', help='仅显示将要修复的文件')
    parser.add_argument('--verbose', '-v', action='store_true', help='显示详细信息')

    args = parser.parse_args()

    path = Path(args.path)
    dry_run = args.dry_run

    # 查找所有Python文件
    if path.is_file() and path.suffix == '.py':
        python_files = [path]
    elif path.is_dir():
        python_files = list(path.rglob('*.py'))
    else:
        print(f"错误: 无效的路径 {args.path}", file=sys.stderr)
        sys.exit(1)

    print(f"找到 {len(python_files)} 个Python文件")
    print(f"模式: {'DRY RUN' if dry_run else '修复模式'}")
    print("-" * 50)

    # 修复文件
    results = []
    fixed_count = 0
    total_fixes = 0

    for file_path in python_files:
        result = fix_file(file_path, dry_run)
        results.append(result)

        if result['fixed']:
            fixed_count += 1
            total_fixes += result['fix_count']
            if args.verbose or result['fix_count'] > 0:
                print(f"✅ {result['file']}: {result['fix_count']}处修复")
        elif result['error']:
            print(f"❌ {result['file']}: {result['error']}")

    # 总结
    print("-" * 50)
    print(f"修复文件数: {fixed_count}/{len(python_files)}")
    print(f"总修复数: {total_fixes}")

    if dry_run:
        print("\n⚠️  DRY RUN模式 - 未实际修改文件")
        print("使用不带--dry-run的命令执行实际修复")

    return 0


if __name__ == '__main__':
    sys.exit(main())
