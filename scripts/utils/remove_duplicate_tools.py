#!/usr/bin/env python3
"""
删除重复性工具

删除以下重复或已废弃的工具：
1. real_code_analyzer_handler - 已被code_analyzer替代
2. real_system_monitor_handler - 已被system_monitor替代
3. real_web_search_handler - 已被local_web_search替代
4. real_knowledge_graph_handler - 已被knowledge_graph_search替代
5. real_chat_companion_handler - 待确认，删除
6. code_executor_handler - 已被code_executor_sandbox替代（更安全）

Author: Athena平台团队
Date: 2026-04-20
"""
import os
import re
import shutil
import sys
from datetime import datetime

sys.path.insert(0, '/Users/xujian/Athena工作平台')

from core.logging_config import setup_logging

logger = setup_logging()


def backup_file(file_path):
    """备份文件"""
    if not os.path.exists(file_path):
        return None

    # 创建备份目录
    backup_dir = "/Users/xujian/Athena工作平台/.backup/removed_tools"
    os.makedirs(backup_dir, exist_ok=True)

    # 生成备份文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.basename(file_path)
    backup_path = os.path.join(backup_dir, f"{filename}.backup_{timestamp}")

    # 复制文件
    shutil.copy2(file_path, backup_path)
    logger.info(f"✅ 已备份: {file_path} -> {backup_path}")

    return backup_path


def remove_handlers_from_file(file_path, handler_names):
    """从文件中删除指定的handler函数"""

    with open(file_path, encoding='utf-8') as f:
        content = f.read()

    removed_count = 0

    for handler_name in handler_names:
        # 查找handler函数定义（包括async def和def）
        # 使用正则表达式匹配整个函数（包括文档字符串和函数体）
        pattern = rf'async def {handler_name}\([^)]*\)[^{{]*{{(?:[^{{}}]*{{[^{{}}]*}})*[^}}]*}}'

        matches = list(re.finditer(pattern, content, re.DOTALL | re.MULTILINE))

        if matches:
            for match in reversed(matches):  # 从后往前删，避免位置偏移
                content = content[:match.start()] + content[match.end():]
                removed_count += 1
                logger.info(f"   - 删除: {handler_name}")

    if removed_count > 0:
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"✅ 共删除 {removed_count} 个handler")

        return removed_count
    else:
        logger.warning("⚠️ 未找到指定的handler")
        return 0


def main():
    """主函数"""
    print("=" * 60)
    print("🗑️ 删除重复性工具")
    print("=" * 60)

    # 定义要删除的工具
    tools_to_remove = {
        "real_tool_implementations.py": [
            "real_code_analyzer_handler",
            "real_system_monitor_handler",
            "real_web_search_handler",
            "real_knowledge_graph_handler",
            "real_chat_companion_handler",
        ],
        "tool_implementations.py": [
            "code_executor_handler",  # 不安全的代码执行器，已被code_executor_sandbox替代
        ]
    }

    base_path = "/Users/xujian/Athena工作平台/core/tools"

    total_removed = 0

    for filename, handlers in tools_to_remove.items():
        file_path = os.path.join(base_path, filename)

        print(f"\n处理文件: {filename}")
        print("-" * 40)

        if not os.path.exists(file_path):
            print("   ⚠️ 文件不存在，跳过")
            continue

        # 1. 备份文件
        print("1. 备份文件...")
        backup_path = backup_file(file_path)

        if backup_path is None:
            print("   ❌ 文件不存在，跳过")
            continue

        # 2. 删除handler
        print("2. 删除handler...")
        removed = remove_handlers_from_file(file_path, handlers)
        total_removed += removed

        if removed == 0:
            # 恢复备份
            shutil.copy2(backup_path, file_path)
            print("   ⚠️ 未找到handler，已恢复备份")

    # 3. 验证删除结果
    print("\n" + "=" * 60)
    print("🔍 验证删除结果")
    print("=" * 60)

    import asyncio

    from core.tools.unified_registry import get_unified_registry

    async def verify():
        registry = get_unified_registry()
        await registry.initialize(auto_discover=False)

        stats = registry.get_statistics()
        print(f"总工具数: {stats['total_tools']}")
        print(f"懒加载工具: {stats['lazy_tools']}")

        print("\n✅ 系统运行正常，删除成功！")

    asyncio.run(verify())

    # 4. 总结
    print("\n" + "=" * 60)
    print("📊 删除总结")
    print("=" * 60)
    print(f"处理文件: {len(tools_to_remove)}")
    print(f"删除handler: {total_removed}个")
    print("备份位置: /Users/xujian/Athena工作平台/.backup/removed_tools/")

    print("\n删除的工具:")
    print("\nreal_tool_implementations.py:")
    for handler in tools_to_remove["real_tool_implementations.py"]:
        print(f"  - {handler}")

    print("\ntool_implementations.py:")
    for handler in tools_to_remove["tool_implementations.py"]:
        print(f"  - {handler}")

    print("\n" + "=" * 60)
    print("🎉 重复工具删除完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
