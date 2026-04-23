#!/usr/bin/env python3
"""第二轮修复 - 处理剩余的特定错误模式"""

import re
from pathlib import Path


def fix_round2_patterns(content: str) -> str:
    """第二轮特定错误修复"""

    # ========================================
    # 模式1: 缺少闭合括号 (return type annotations)
    # ========================================
    # ) -> dict[str, Any]: → )] -> dict[str, Any]:
    # 但要小心不要过度修复

    # 检查是否缺少闭合括号: 在 -> 和 : 之间需要匹配的括号
    def fix_return_type_annotation(match):
        prefix = match.group(1)
        return_type = match.group(2)
        # 检查是否有未闭合的 [
        open_brackets = return_type.count('[')
        close_brackets = return_type.count(']')
        if open_brackets > close_brackets:
            # 需要添加闭合括号
            return f'{prefix}{return_type}{"}" * (open_brackets - close_brackets)}:'
        return match.group(0)

    # 修复 ) -> dict[str, Any]: 模式
    content = re.sub(
        r'(\)\s*->\s*)(dict\[str, Any\]):',
        lambda m: m.group(1) + m.group(2) + ']:' if m.group(2).count('[') > m.group(2).count(']') else m.group(0),
        content
    )

    # 修复 ) -> list[dict[str, Any]: 已经是正确的

    # 修复 ) -> list[dict[str, Any]:
    content = re.sub(
        r'(\)\s*->\s*)(list\[dict\[str, Any\]):',
        lambda m: m.group(1) + m.group(2) + ']:' if m.group(2).count('[') > m.group(2).count(']') else m.group(0),
        content
    )

    # 修复 ) -> Any:
    content = re.sub(
        r'(\)\s*->\s*)(Any):',
        lambda m: m.group(1) + m.group(2) + ']:' if m.group(2).count('[') > m.group(2).count(']') else m.group(0),
        content
    )

    # 修复 ) -> list[str]:
    content = re.sub(
        r'(\)\s*->\s*)(list\[str\]):',
        lambda m: m.group(1) + m.group(2) + ']:' if m.group(2).count('[') > m.group(2).count(']') else m.group(0),
        content
    )

    # 修复 ) -> str:
    content = re.sub(
        r'(\)\s*->\s*)(str):',
        lambda m: m.group(1) + m.group(2) + ']:' if m.group(2).count('[') > m.group(2).count(']') else m.group(0),
        content
    )

    # 修复 ) -> None:
    content = re.sub(
        r'(\)\s*->\s*)(None):',
        lambda m: m.group(1) + m.group(2) + ']:' if m.group(2).count('[') > m.group(2).count(']') else m.group(0),
        content
    )

    # 修复 ) -> bool:
    content = re.sub(
        r'(\)\s*->\s*)(bool):',
        lambda m: m.group(1) + m.group(2) + ']:' if m.group(2).count('[') > m.group(2).count(']') else m.group(0),
        content
    )

    # 修复 ) -> dict[str, list[dict[str, Any]]:
    content = re.sub(
        r'(\)\s*->\s*)(dict\[str,\s*list\[dict\[str,\s*Any\]\]\]):',
        lambda m: m.group(1) + m.group(2) + ']:' if m.group(2).count('[') > m.group(2).count(']') else m.group(0),
        content
    )

    # ========================================
    # 模式2: 未闭合的列表/字典注解
    # ========================================
    # conversation_log: list[dict[str, Any]  # 专家对话记录
    # → conversation_log: list[dict[str, Any]  # 专家对话记录
    content = re.sub(
        r':\s*list\[dict\[str,\s*Any\]\s*#',
        r': list[dict[str, Any]  #',
        content
    )

    content = re.sub(
        r':\s*dict\[str,\s*list\[str\]\s*#',
        r': dict[str, list[str]  #',
        content
    )

    # ========================================
    # 模式3: hashlib.md5 参数修复
    # ========================================
    # .encode("utf-8", usedforsecurity=False
    # → .encode("utf-8"), usedforsecurity=False
    content = re.sub(
        r'\.encode\("utf-8",\s*usedforsecurity=False',
        r'.encode("utf-8"), usedforsecurity=False',
        content
    )

    content = re.sub(
        r'\.encode\(\),\s*usedforsecurity=False',
        r'.encode(), usedforsecurity=False',
        content
    )

    # ========================================
    # 模式4: 修复被截断的类型注解
    # ========================================
    # patent_list: list[PatentInfo] | Non
    # → patent_list: list[PatentInfo] | None = None
    content = re.sub(
        r'patent_list:\s*list\[\w+\]\]\]\s*\|\s*Non',
        r'patent_list: list[PatentInfo] | None = None',
        content
    )

    content = re.sub(
        r'tool_schema:\s*dict\[str,\s*ParameterType\]\]',
        r'tool_schema: dict[str, ParameterType]',
        content
    )

    # ========================================
    # 模式5: async def 导入 -> 不完整
    # ========================================
    # async def _import_nodes(self, nodes: list[dict[str, Any]) ->
    # → async def _import_nodes(self, nodes: list[dict[str, Any]):
    content = re.sub(
        r'async def\s+\w+\(self,\s*nodes:\s*list\[dict\[str,\s*Any\]\)\s*->\s*$',
        lambda m: m.group(0).rstrip() + ']:',
        content,
        flags=re.MULTILINE
    )

    # ========================================
    # 模式6: Optional[ 被截断
    # ========================================
    # details: Optional[
    # 应该查看下一行是什么
    content = re.sub(
        r'details:\s*Optional\[\s*$',
        r'details: dict[str, Any] | None =',
        content,
        flags=re.MULTILINE
    )

    return content

def fix_file(file_path: Path) -> bool:
    """修复单个文件"""
    try:
        content = file_path.read_text(encoding='utf-8')
        fixed = fix_round2_patterns(content)

        if fixed != content:
            file_path.write_text(fixed, encoding='utf-8')
            return True
        return False
    except Exception:
        return False

def main():
    core_path = Path('/Users/xujian/Athena工作平台/core')

    print("=" * 80)
    print("🔧 第二轮特定错误修复")
    print("=" * 80)

    # 获取有错误的文件
    error_files = []
    for f in core_path.rglob('*.py'):
        try:
            compile(f.read_text(encoding='utf-8'), str(f), 'exec')
        except SyntaxError:
            error_files.append(f)

    print(f"\n待修复文件: {len(error_files)} 个")

    # 修复文件
    fixed_count = 0
    for f in error_files:
        if fix_file(f):
            fixed_count += 1
            print(f"  ✅ {f.relative_to(core_path.parent)}")

    # 统计结果
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
    print(f"📊 当前状态: {success_count}/{len(all_files)} ({success_count*100//len(all_files)}%)")
    print(f"⚠️ 剩余错误: {error_count} 个文件")
    print("=" * 80)

if __name__ == "__main__":
    main()
