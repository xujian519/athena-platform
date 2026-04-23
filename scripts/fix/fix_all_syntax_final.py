#!/usr/bin/env python3
"""
最终全面语法修复 - 处理所有已知错误模式
Final Comprehensive Syntax Fix
"""

import re
from pathlib import Path


def fix_all_patterns(content: str) -> str:
    """应用所有修复模式"""

    # ========================================
    # 模式1: 缺少右括号 ]
    # ========================================
    # list[dict[str, Any]) -> list[dict[str, Any]
    content = re.sub(
        r'list\[dict\[str, Any\]\)\s*->',
        r'list[dict[str, Any] ->',
        content
    )
    content = re.sub(
        r'list\[dict\[str, Any\]\)\s*,',
        r'list[dict[str, Any],',
        content
    )

    # tuple[list[QueryResult], dict[str, Any]) -> tuple[list[QueryResult], dict[str, Any]
    content = re.sub(
        r'tuple\[list\[QueryResult\], dict\[str, Any\]\)\s*->',
        r'tuple[list[QueryResult], dict[str, Any] ->',
        content
    )

    # list[str], domain: str]) -> list[str], domain: str]
    content = re.sub(
        r':\s*str\]),\s*domain:\s*str\]\)',
        r': str], domain: str])',
        content
    )

    # ========================================
    # 模式2: Optional使用错误
    # ========================================
    # Optional[dict[str, Any] | None = None) -> dict[str, Any] | None = None)
    content = re.sub(
        r'Optional\[dict\[str, Any\] \| None = None\)',
        r'dict[str, Any] | None = None)',
        content
    )

    # Optional[logging.Logger | None] = None) -> logging.Logger | None = None)
    content = re.sub(
        r'Optional\[logging\.Logger \| None = None\)',
        r'logging.Logger | None = None)',
        content
    )

    # Optional[str | None] = None) -> str | None = None)
    content = re.sub(
        r'Optional\[([a-z][a-zA-Z0-9_]*) \| None = None\)',
        r'\1 | None = None)',
        content
    )

    # Optional[dict[str | None = None, dict | None = None) -> dict[str, Any] | None, dict | None
    content = re.sub(
        r'Optional\[dict\[str \| None = None,\s*dict \| None = None\)',
        r'dict[str, Any] | None, dict | None',
        content
    )

    # ========================================
    # 模式3: 双重None赋值
    # ========================================
    # step_id: str | None = None | None = None -> step_id: str | None = None
    content = re.sub(
        r':\s*([a-zA-Z0-9_]+)\s*\|\s*None\s*=\s*None\s*\|\s*None\s*=\s*None',
        r': \1 | None = None',
        content
    )

    # ========================================
    # 模式4: 缺少 -> 前的括号
    # ========================================
    # context: dict[str, Any] | None -> -> context: dict[str, Any] | None = None) ->
    content = re.sub(
        r'context:\s*dict\[str, Any\] \| None\s*->\s*->',
        r'context: dict[str, Any] | None = None) ->',
        content
    )

    # ========================================
    # 模式5: set[str | None = None: -> set[str] | None = None:
    # ========================================
    content = re.sub(
        r'set\[str \| None = None:\s*\)',
        r'set[str] | None = None):',
        content
    )
    content = re.sub(
        r'set\[str \| None = None\):\s*->',
        r'set[str] | None = None) ->',
        content
    )

    # ========================================
    # 模式6: 修复tuple] | None -> tuple | None
    # ========================================
    content = re.sub(
        r':\s*tuple\] \| None\s*=',
        r': tuple | None =',
        content
    )

    # ========================================
    # 模式7: 修复 params: tuple] | None -> params: tuple | None
    # ========================================
    content = re.sub(
        r'params:\s*tuple\]\s*\|\s*None',
        r'params: tuple | None',
        content
    )

    # ========================================
    # 模式8: 修复 Optional[None ->  | None
    # ========================================
    content = re.sub(
        r'config=Optional\[None,',
        r'config=None,',
        content
    )

    # ========================================
    # 模式9: 修复 *Optional[args -> *args
    # ========================================
    content = re.sub(
        r'\*Optional\[args,\s*timeout:',
        r'*args, timeout:',
        content
    )

    # ========================================
    # 模式10: 修复 message_type: str | None = None | None = None
    # ========================================
    content = re.sub(
        r'([a-z_]+):\s*str\s*\|\s*None\s*=\s*None\s*\|\s*None\s*=\s*None',
        r'\1: str | None = None',
        content
    )

    # ========================================
    # 模式11: 修复 dict[str | None = None -> dict[str, Any] | None = None
    # ========================================
    content = re.sub(
        r'dict\[str \| None = None',
        r'dict[str, Any] | None = None',
        content
    )

    # ========================================
    # 模式12: 修复 dict | None = None -> dict[str, Any] | None = None
    # ========================================
    content = re.sub(
        r'metadata:\s*dict\s*\|\s*None\s*=\s*None',
        r'metadata: dict[str, Any] | None = None',
        content
    )

    return content

def fix_file(file_path: Path) -> bool:
    """修复单个文件"""
    try:
        content = file_path.read_text(encoding='utf-8')
        fixed = fix_all_patterns(content)

        if fixed != content:
            file_path.write_text(fixed, encoding='utf-8')
            return True
        return False
    except Exception:
        return False

def main():
    core_path = Path('/Users/xujian/Athena工作平台/core')

    print("=" * 70)
    print("🔧 最终全面语法修复")
    print("=" * 70)

    # 多轮修复
    for round_num in range(1, 6):
        print(f"\n第{round_num}轮修复...")

        # 获取有错误的文件
        error_files = []
        for f in core_path.rglob('*.py'):
            try:
                compile(f.read_text(encoding='utf-8'), str(f), 'exec')
            except SyntaxError:
                error_files.append(f)

        if not error_files:
            print("✅ 所有文件语法正确!")
            break

        # 修复文件
        fixed_count = 0
        for f in error_files:
            if fix_file(f):
                fixed_count += 1

        print(f"   修复: {fixed_count} 个文件, 剩余: {len(error_files)} 个有错误")

        if fixed_count == 0:
            print("   ⚠️ 无法自动修复更多错误")
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

    print("\n" + "=" * 70)
    print("📊 最终统计:")
    print(f"   总文件: {len(all_files)}")
    print(f"   成功: {success_count} ({success_count*100//len(all_files)}%)")
    print(f"   失败: {error_count} ({error_count*100//len(all_files)}%)")
    print("=" * 70)

    # 显示仍有错误的文件（最多10个）
    if error_count > 0:
        print(f"\n⚠️ 仍有{error_count}个文件存在语法错误（前10个）:")
        count = 0
        for f in all_files:
            try:
                compile(f.read_text(encoding='utf-8'), str(f), 'exec')
            except SyntaxError:
                if count < 10:
                    print(f"   - {f.relative_to(core_path.parent)}")
                    count += 1

if __name__ == "__main__":
    main()
