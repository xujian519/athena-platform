#!/usr/bin/env python3
"""
工具分类统计报告
Tool Classification Statistics Report

分析Athena平台220个工具的分类情况和分布。

Author: Athena Team
Version: 1.0.0
Date: 2026-02-24
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


async def analyze_tools():
    """分析工具分类"""

    from core.governance.unified_tool_registry import ToolCategory, get_unified_registry

    # 初始化注册中心
    registry = get_unified_registry()
    await registry.initialize()

    # 获取所有工具
    all_tools = registry.get_all_tools()

    print("=" * 80)
    print("  Athena平台工具分类统计报告")
    print("=" * 80)
    print(f"\n📊 总工具数: {len(all_tools)}个")
    print()

    # 按类别统计
    category_stats = {}
    for tool in all_tools:
        category = tool.category.value
        if category not in category_stats:
            category_stats[category] = []
        category_stats[category].append(tool)

    print("┌" + "─" * 78 + "┐")
    print("│  按类别统计                                                        │")
    print("├" + "─" * 78 + "┤")

    # 按数量排序
    sorted_categories = sorted(category_stats.items(), key=lambda x: len(x[1]), reverse=True)

    for category, tools in sorted_categories:
        count = len(tools)
        percentage = (count / len(all_tools)) * 100
        print(f"│  {category:15} {count:4}个 ({percentage:5.1f}%)                           │")

    print("└" + "─" * 78 + "┘")
    print()

    # 详细展示各类别工具
    print("=" * 80)
    print("  各类别工具详情")
    print("=" * 80)

    for category, tools in sorted_categories:
        print(f"\n📁 {category.upper()} ({len(tools)}个工具)")
        print("-" * 80)

        # 显示前10个工具
        for i, tool in enumerate(tools[:10], 1):
            print(f"   {i:2}. {tool.tool_id}")
            print(f"      名称: {tool.name}")

        if len(tools) > 10:
            print(f"   ... 还有 {len(tools) - 10} 个工具")

    # 按子目录统计
    print("\n" + "=" * 80)
    print("  按子目录统计")
    print("=" * 80)

    dir_stats = {}
    for tool in all_tools:
        # 从tool_id提取目录
        parts = tool.tool_id.split(".")
        if len(parts) >= 2:
            subdir = parts[0]
            if subdir not in dir_stats:
                dir_stats[subdir] = 0
            dir_stats[subdir] += 1

    sorted_dirs = sorted(dir_stats.items(), key=lambda x: x[1], reverse=True)

    print(f"\n{'子目录':<20} {'工具数':<10} {'占比':<10}")
    print("-" * 80)

    for subdir, count in sorted_dirs:
        percentage = (count / len(all_tools)) * 100
        print(f"{subdir:<20} {count:<10} {percentage:>6.1f}%")

    # 专利相关工具
    print("\n" + "=" * 80)
    print("  专利相关工具")
    print("=" * 80)

    patent_tools = [t for t in all_tools if "patent" in t.tool_id.lower()]

    print(f"\n📋 专利相关工具: {len(patent_tools)}个")

    if patent_tools:
        print("\n示例工具:")
        for i, tool in enumerate(patent_tools[:15], 1):
            print(f"   {i:2}. {tool.tool_id}")
            print(f"      {tool.name[:50]}...")

    # 搜索工具
    print("\n" + "=" * 80)
    print("  搜索工具")
    print("=" * 80)

    search_tools = [t for t in all_tools if "search" in t.tool_id.lower() or t.category == ToolCategory.SEARCH]

    print(f"\n🔍 搜索工具: {len(search_tools)}个")

    if search_tools:
        print("\n示例工具:")
        for i, tool in enumerate(search_tools[:10], 1):
            print(f"   {i:2}. {tool.tool_id}")
            print(f"      {tool.name[:50]}...")

    # 文件处理工具
    print("\n" + "=" * 80)
    print("  文件处理工具")
    print("=" * 80)

    file_tools = [t for t in all_tools if any(kw in t.tool_id.lower() for kw in
                     ["parser", "importer", "exporter", "detector", "extractor"])]

    print(f"\n📄 文件处理工具: {len(file_tools)}个")

    if file_tools:
        print("\n示例工具:")
        for i, tool in enumerate(file_tools[:10], 1):
            print(f"   {i:2}. {tool.tool_id}")
            print(f"      {tool.name[:50]}...")

    # 系统工具
    print("\n" + "=" * 80)
    print("  系统工具")
    print("=" * 80)

    system_tools = [t for t in all_tools if any(kw in t.tool_id.lower() for kw in
                     ["fix", "check", "cleanup", "optimize", "diagnose"])]

    print(f"\n🛠️ 系统工具: {len(system_tools)}个")

    if system_tools:
        print("\n示例工具:")
        for i, tool in enumerate(system_tools[:10], 1):
            print(f"   {i:2}. {tool.tool_id}")
            print(f"      {tool.name[:50]}...")

    # 数据库工具
    print("\n" + "=" * 80)
    print("  数据库工具")
    print("=" * 80)

    db_tools = [t for t in all_tools if any(kw in t.tool_id.lower() for kw in
                  ["database", "db_", "sql", "postgres", "mongodb"])]

    print(f"\n💾 数据库工具: {len(db_tools)}个")

    if db_tools:
        print("\n示例工具:")
        for i, tool in enumerate(db_tools[:10], 1):
            print(f"   {i:2}. {tool.tool_id}")
            print(f"      {tool.name[:50]}...")

    print("\n" + "=" * 80)
    print("  ✅ 分析完成")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(analyze_tools())
