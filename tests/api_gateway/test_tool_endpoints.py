#!/usr/bin/env python3
"""
测试Gateway工具API端点
Test Gateway Tool API Endpoints

验证:
- GET /api/v1/tools - 列出工具
- GET /api/v1/tools/{tool_id} - 获取工具信息
- POST /api/v1/tools/discover - 发现工具
- POST /api/v1/tools/{tool_id}/execute - 执行工具
- GET /api/v1/tools/stats - 获取统计信息

Author: Athena Team
Date: 2026-02-24
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


async def test_tool_endpoints():
    """测试工具API端点"""

    print("=" * 80)
    print("🧪 Gateway 工具API端点测试")
    print("=" * 80)
    print()

    # 初始化工具注册中心
    from core.governance.unified_tool_registry import get_unified_registry

    registry = get_unified_registry()
    await registry.initialize()

    print(f"✅ 工具注册中心已初始化,共 {len(registry.tools)} 个工具")
    print()

    # 测试1: 列出工具
    print("📋 测试1: 列出工具 (GET /api/v1/tools)")
    tools = registry.list_tools()
    print(f"   总工具数: {len(tools)}")

    # 按类别统计
    from collections import Counter
    category_count = Counter(t["category"] for t in tools)
    print(f"   按类别: {dict(category_count.most_common(5))}")
    print()

    # 测试2: 获取工具详情
    if tools:
        print("📖 测试2: 获取工具详情 (GET /api/v1/tools/{{tool_id}})")
        tool_id = tools[0]["tool_id"]
        info = registry.get_tool_info(tool_id)
        if info:
            print(f"   工具ID: {info['tool_id']}")
            print(f"   名称: {info['name']}")
            print(f"   描述: {info['description'][:60]}...")
        print()

    # 测试3: 发现工具
    print("🔍 测试3: 发现工具 (POST /api/v1/tools/discover)")
    discovered = await registry.discover_tools("专利", limit=3)
    print(f"   查询 '专利': 找到 {len(discovered)} 个工具")
    for tool in discovered[:2]:
        print(f"   - {tool['name']}: {tool['description'][:50]}...")
    print()

    # 测试4: 工具统计
    print("📊 测试4: 工具统计 (GET /api/v1/tools/stats)")
    stats = registry.get_statistics()
    print(f"   总工具数: {stats['total_tools']}")
    print(f"   按类别: {stats['by_category']}")
    print()

    # 测试5: 工具执行(模拟)
    print("⚙️ 测试5: 工具执行 (POST /api/v1/tools/{{tool_id}}/execute)")
    if tools:
        tool_id = tools[0]["tool_id"]
        result = await registry.execute_tool(tool_id, {}, {})
        print(f"   工具: {tool_id}")
        print(f"   结果: {result.success}")
        if result.error:
            print(f"   错误: {result.error[:100]}...")
    print()

    print("=" * 80)
    print("✅ 测试完成")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_tool_endpoints())
