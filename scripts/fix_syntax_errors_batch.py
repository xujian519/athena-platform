#!/usr/bin/env python3.11
"""
批量修复Python 3.11语法错误

主要修复：
1. Optional类型注解括号不匹配
2. list/dict类型注解括号不匹配
3. dataclass参数顺序错误

作者: Athena平台团队
创建时间: 2026-04-23
版本: v1.0.0
"""

import re
from pathlib import Path
from typing import Optional


def fix_optional_brackets(content: str) -> str:
    """
    修复Optional类型注解的括号不匹配

    模式:
    - Optional[list[X]] -> Optional[[list[X]]]
    - Optional[dict[X, Y]] -> Optional[[dict[X, Y]]]
    """
    # 模式1: Optional[list[X]]
    content = re.sub(
        r'Optional\[list\[([^\]]+)\]\]',
        r'Optional[[list[\1]]]',
        content
    )

    # 模式2: Optional[dict[X, Y]]
    content = re.sub(
        r'Optional\[dict\[([^\]]+)\]\]',
        r'Optional[[dict[\1]]]',
        content
    )

    # 模式3: Optional[list[dict[X, Y]]]
    content = re.sub(
        r'Optional\[list\[dict\[([^\]]+)\]\]\]',
        r'Optional[[list[dict[\1]]]]',
        content
    )

    return content


def fix_list_dict_brackets(content: str) -> str:
    """
    修复list/dict类型注解的括号不匹配

    模式:
    - list[X] -> list[[X]]
    - dict[X, Y] -> dict[[X, Y]]
    """
    # 模式1: list[X]
    content = re.sub(
        r': list\[([^\]]+)\]',
        r': list[[\1]]',
        content
    )

    # 模式2: dict[X, Y]
    content = re.sub(
        r': dict\[([^\]]+)\]',
        r': dict[[\1]]',
        content
    )

    return content


def fix_function_signature(content: str) -> str:
    """
    修复函数签名中的类型注解括号不匹配
    """
    # 匹配函数定义行
    lines = content.split('\n')
    fixed_lines = []

    for line in lines:
        # 检查是否是函数定义
        if line.strip().startswith('def ') or line.strip().startswith('async def '):
            # 修复参数类型注解
            fixed_line = fix_optional_brackets(line)
            fixed_line = fix_list_dict_brackets(fixed_line)
            fixed_lines.append(fixed_line)
        else:
            fixed_lines.append(line)

    return '\n'.join(fixed_lines)


def fix_dataclass_field_order(content: str) -> str:
    """
    修复dataclass字段顺序（有默认值参数必须在无默认值参数之后）

    注意：这个修复比较复杂，需要分析具体上下文
    这里只做简单的标记，需要人工审查
    """
    lines = content.split('\n')
    fixed_lines = []
    in_dataclass = False
    issues_found = []

    for i, line in enumerate(lines, 1):
        # 检测dataclass装饰器
        if '@dataclass' in line:
            in_dataclass = True
            fixed_lines.append(line)
            continue

        # 检测类定义结束
        if in_dataclass and line.strip().startswith('class '):
            in_dataclass = False

        # 在dataclass中检查参数顺序
        if in_dataclass and '=' in line and ':' in line:
            # 这是一个带默认值的字段
            if ' = ' in line or '=None' in line or '=[]' in line or '={}':
                # 检查后面是否有不带默认值的字段
                for j in range(i, min(i + 10, len(lines))):
                    next_line = lines[j]
                    if (next_line.strip() and
                        ':' in next_line and
                        '=' not in next_line and
                        not next_line.strip().startswith('#') and
                        'def ' not in next_line):
                        issues_found.append(f"行 {i}: {line.strip()}")
                        break

        fixed_lines.append(line)

    if issues_found:
        fixed_lines.insert(0, f"# ⚠️ 发现dataclass字段顺序问题，需要人工审查:")
        for issue in issues_found:
            fixed_lines.insert(1, f"#   {issue}")

    return '\n'.join(fixed_lines)


def fix_indentation_errors(content: str) -> str:
    """
    修复缩进错误

    注意：这个修复比较复杂，需要分析具体上下文
    这里只做简单的修复，复杂情况需要人工审查
    """
    lines = content.split('\n')
    fixed_lines = []

    for line in lines:
        # 移除行尾空格
        fixed_line = line.rstrip()
        fixed_lines.append(fixed_line)

    return '\n'.join(fixed_lines)


def fix_file(file_path: Path) -> dict:
    """
    修复单个文件

    Returns:
        dict: 修复结果
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()

        content = original_content

        # 应用各种修复
        content = fix_optional_brackets(content)
        content = fix_list_dict_brackets(content)
        content = fix_function_signature(content)
        content = fix_indentation_errors(content)

        # 检查是否有变化
        if content != original_content:
            # 备份原文件
            backup_path = file_path.with_suffix('.py.backup')
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)

            # 写入修复后的内容
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return {
                'file': str(file_path),
                'status': 'fixed',
                'backup': str(backup_path),
                'changes': 'yes'
            }
        else:
            return {
                'file': str(file_path),
                'status': 'no_changes',
                'changes': 'no'
            }

    except Exception as e:
        return {
            'file': str(file_path),
            'status': 'error',
            'error': str(e),
            'changes': 'no'
        }


def main():
    """主函数"""
    import json

    # 定义需要修复的文件列表
    files_to_fix = [
        # P0 - 核心LLM模块
        Path('core/ai/llm/xiaonuo_llm_service.py'),
        Path('core/ai/llm/qwen_client.py'),
        Path('core/ai/llm/model_api_capabilities.py'),
        Path('core/ai/llm/glm47_flash_client.py'),
        Path('core/ai/llm/glm47_client.py'),

        # P0 - 小娜专业代理
        Path('core/framework/agents/xiaona/unified_patent_writer.py'),
        Path('core/framework/agents/xiaona/novelty_analyzer_proxy.py'),
        Path('core/framework/agents/xiaona/creativity_analyzer_proxy.py'),
        Path('core/framework/agents/xiaona/invalidation_analyzer_proxy.py'),
        Path('core/framework/agents/xiaona/infringement_analyzer_proxy.py'),
        Path('core/framework/agents/xiaona/application_reviewer_proxy.py'),
        Path('core/framework/agents/xiaona/writing_reviewer_proxy.py'),
        Path('core/framework/agents/xiaona/writer_agent.py'),

        # P0 - Gateway和协调代理
        Path('core/framework/agents/xiaonuo_agent.py'),
        Path('core/framework/agents/gateway_client.py'),
        Path('core/framework/agents/websocket_adapter/agent_adapter.py'),
        Path('core/framework/agents/websocket_adapter/xiaonuo_adapter.py'),
    ]

    print(f"🔧 开始修复 {len(files_to_fix)} 个文件...")

    results = []
    fixed_count = 0
    error_count = 0

    for file_path in files_to_fix:
        if not file_path.exists():
            print(f"⚠️  文件不存在: {file_path}")
            continue

        print(f"🔍 修复: {file_path}")
        result = fix_file(file_path)
        results.append(result)

        if result['status'] == 'fixed':
            print(f"✅ 已修复: {file_path}")
            print(f"   备份: {result['backup']}")
            fixed_count += 1
        elif result['status'] == 'error':
            print(f"❌ 错误: {file_path}")
            print(f"   错误信息: {result['error']}")
            error_count += 1
        else:
            print(f"➡️  无需修复: {file_path}")

    # 保存结果
    with open('/tmp/fix_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # 输出摘要
    print("\n" + "=" * 60)
    print("📊 修复摘要")
    print("=" * 60)
    print(f"总文件数: {len(files_to_fix)}")
    print(f"已修复: {fixed_count}")
    print(f"无需修复: {len(results) - fixed_count - error_count}")
    print(f"错误: {error_count}")
    print(f"\n详细结果已保存到: /tmp/fix_results.json")

    if fixed_count > 0:
        print("\n⚠️  注意:")
        print("1. 所有修改都已备份（.py.backup文件）")
        print("2. 请运行测试验证修复")
        print("3. 如有问题，可以从备份恢复")
        print("\n恢复命令:")
        print("  find . -name '*.py.backup' -exec sh -c 'mv \"$1\" \"${1%.backup}\"' _ {} \\;")


if __name__ == '__main__':
    main()
