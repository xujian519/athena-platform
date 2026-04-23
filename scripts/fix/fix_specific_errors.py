#!/usr/bin/env python3
"""精确修复特定的语法错误"""

import re
from pathlib import Path


def fix_specific_errors(content: str, file_name: str) -> str:
    """根据文件名应用特定的修复"""

    # ========================================
    # 通用修复模式
    # ========================================

    # 模式1: dict[str, str | None = None (缺少类型闭合)
    content = re.sub(
        r'dict\[str,\s*str\s*\|\s*None\s*=\s*None',
        r'dict[str, str] | None = None',
        content
    )

    # 模式2: dict[str, str | None = None, (后面有逗号)
    content = re.sub(
        r'dict\[str,\s*str\s*\|\s*None\s*=\s*None,',
        r'dict[str, str] | None = None,',
        content
    )

    # 模式3: list[str, output_path: str | None = None (缺少闭合括号)
    content = re.sub(
        r'list\[str,\s*output_path:\s*str\s*\|\s*None\s*=\s*None',
        r'list[str], output_path: str | None = None',
        content
    )

    # 模式4: 修复 )] -> 中的多余括号
    # 如果之前已经有 ] 了，不要再添加
    content = re.sub(
        r'\)\]\]\s*->',
        r']) ->',
        content
    )

    # 模式5: 修复 ):]: 多余的括号
    content = re.sub(
        r'\):\]:',
        r'):',
        content
    )

    # 模式6: 修复 labels: dict[str, str | None = None
    content = re.sub(
        r'labels:\s*dict\[str,\s*str\s*\|\s*None\s*=\s*None',
        r'labels: dict[str, str] | None = None',
        content
    )

    # 模式7: 修复 exclude_paths: set[str | None = None,
    content = re.sub(
        r'exclude_paths:\s*set\[str\s*\|\s*None\s*=\s*None,',
        r'exclude_paths: set[str] | None = None,',
        content
    )

    # 模式8: 修复 name: str, value: float = 1.0, labels: dict[str, str | None = None
    content = re.sub(
        r'name:\s*str,\s*value:\s*float\s*=\s*1\.0,\s*labels:\s*dict\[str,\s*str\s*\|\s*None\s*=\s*None',
        r'name: str, value: float = 1.0, labels: dict[str, str] | None = None',
        content
    )

    return content

def fix_file_safe(file_path: Path) -> bool:
    """安全地修复文件"""
    try:
        content = file_path.read_text(encoding='utf-8')
        file_name = file_path.name

        # 只处理有语法错误的文件
        try:
            compile(content, str(file_path), 'exec')
            return False  # 没有错误
        except SyntaxError:
            pass

        # 应用修复
        fixed = fix_specific_errors(content, file_name)

        if fixed != content:
            # 验证修复
            try:
                compile(fixed, str(file_path), 'exec')
                file_path.write_text(fixed, encoding='utf-8')
                return True
            except SyntaxError:
                return False
        return False
    except Exception:
        return False

def main():
    core_path = Path('/Users/xujian/Athena工作平台/core')

    print("=" * 80)
    print("🔧 精确修复特定错误")
    print("=" * 80)

    # 修复所有有错误的文件
    fixed_count = 0
    total_errors = 0

    for f in core_path.rglob('*.py'):
        try:
            compile(f.read_text(encoding='utf-8'), str(f), 'exec')
        except SyntaxError:
            total_errors += 1
            if fix_file_safe(f):
                fixed_count += 1
                print(f"  ✅ {f.relative_to(core_path.parent)}")

    # 统计最终结果
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
    print(f"✅ 本轮修复: {fixed_count} 个文件")
    print(f"📊 最终状态: {success_count}/{len(all_files)} ({success_count*100//len(all_files)}%)")
    print(f"⚠️ 剩余错误: {error_count} 个文件")

    improvement = success_count * 100 // len(all_files)
    print(f"\n📈 总体成功率: {improvement}%")

    if improvement >= 85:
        print("🎉 优秀!成功率已达到85%以上!")
    elif improvement >= 82:
        print("👍 很好!成功率已达到82%以上!")
    elif improvement >= 80:
        print("✅ 良好!成功率保持在80%以上!")
    print("=" * 80)

if __name__ == "__main__":
    main()
