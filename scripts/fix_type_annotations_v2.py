#!/usr/bin/env python3
"""
批量修复core/framework/agents目录下的类型注解错误 v2

新增错误模式：
- dict[str, Any) → dict[str, Any])
"""

import re
from pathlib import Path


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

        # 模式1: Optional[type[X]]] → Optional[type[X]]
        line = re.sub(r'Optional\[type\[([^\]]+)\]\]\]', r'Optional[type[\1]]', line)

        # 模式2: -> dict[str, Any]]: → -> dict[str, Any]:
        line = re.sub(r'-> (dict|list)\[str, [^\]]+\]\]:', r'-> \1[str, Any]:', line)
        line = re.sub(r'-> (dict|list)\[[^\]]+\]\]:', r'-> \1[str, Any]:', line)

        # 模式3: Optional[list[str] = field( → Optional[list[str]] = field(
        line = re.sub(
            r'Optional\[list\[([^\]]+)\] = field\(',
            r'Optional[list[\1]] = field(',
            line
        )

        # 模式4: ) → SubagentConfig]]: → ) → SubagentConfig]:
        line = re.sub(r'\]\] ->', r'] ->', line)
        line = re.sub(r'\]\]:\s*$', r']:', line)

        # 模式5: 修复嵌套的方括号问题
        line = re.sub(r'(\w+)\]\]:\s*$', r'\1]:', line)

        # 模式6: messages: Optional[list[dict[str, str]] 缺少右括号
        if 'messages: Optional[list[dict[str, str]' in line and 'tools:' in line:
            line = line.replace(
                'messages: Optional[list[dict[str, str]]',
                'messages: Optional[list[dict[str, str]]]'
            )

        # 模式7: ) → dict[str, Any]]:
        line = re.sub(r'\) -> dict\[str, Any\]\]:', r') -> dict[str, Any]:', line)

        # 模式8: **_kwargs  # noqa: ARG001 → **_kwargs)
        line = re.sub(
            r'\*\*_kwargs\s+# noqa: ARG001\) ->',
            r'**_kwargs) ->  # noqa: ARG001',
            line
        )

        # 模式9: dict[str, Any) → dict[str, Any])
        line = re.sub(r'\[str, Any\)(\s*->|:|$)', r'[str, Any])\1', line)

        # 模式10: dict[str, str} → dict[str, str]
        line = re.sub(r'\[str, str\}', r'[str, str]', line)

        # 模式11: list[dict[str, Any] → list[dict[str, Any]]
        if re.search(r'list\[dict\[str, Any\][^\]]*(\)|:|$)', line):
            line = re.sub(
                r'list\[dict\[str, Any\]([^\]]*)(\)|:|$)',
                r'list[dict[str, Any]]\1\2',
                line
            )

        # 模式12: 检查下一行是否有tools，如果有则补全当前行的messages定义
        if 'messages: Optional[list[dict[str, str]' in line:
            # 检查是否缺少右括号
            if line.count('[') > line.count(']'):
                line = line.rstrip() + ']'

        if line != original_line:
            fixes += 1
            print(f"  行 {i+1}: {original_line.strip()[:60]}")
            print(f"       → {line.strip()[:60]}")

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
