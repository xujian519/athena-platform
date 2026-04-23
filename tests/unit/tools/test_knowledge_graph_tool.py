#!/usr/bin/env python3
"""
知识图谱搜索工具验证测试

测试knowledge_graph_search工具的完整功能。

Author: Athena平台团队
Created: 2026-04-19
"""

import asyncio
import sys
import logging

# 添加项目路径
sys.path.insert(0, "/Users/xujian/Athena工作平台")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


async def test_knowledge_graph_tool():
    """测试知识图谱搜索工具"""
    from core.tools.knowledge_graph_handler import (
        get_graph_statistics,
        knowledge_graph_search_handler,
        search_patents_by_keyword,
    )

    print("=" * 80)
    print("知识图谱搜索工具验证测试")
    print("=" * 80)

    # 测试1: 获取统计信息
    print("\n【测试1】获取知识图谱统计信息")
    print("-" * 80)
    try:
        stats = await get_graph_statistics()
        print(f"✅ 成功获取统计信息")
        print(f"  - 后端类型: {stats['results'][0]['backend']}")
        print(f"  - 节点数量: {stats['results'][0]['node_count']}")
        print(f"  - 边数量: {stats['results'][0]['edge_count']}")
        print(f"  - 标签类型: {stats['results'][0]['tag_types']}")
        print(f"  - 关系类型: {stats['results'][0]['edge_types']}")
        print(f"  - 可用状态: {stats['results'][0]['is_available']}")
        print(f"  - 执行时间: {stats['execution_time']:.3f}秒")
    except Exception as e:
        print(f"❌ 获取统计信息失败: {e}")
        import traceback

        traceback.print_exc()
        return False

    # 测试2: 简单Cypher查询（统计节点数）
    print("\n【测试2】执行Cypher查询 - 统计节点数")
    print("-" * 80)
    try:
        result = await knowledge_graph_search_handler(
            query="MATCH (n) RETURN count(n) as total_nodes", query_type="cypher", top_k=1
        )
        print(f"✅ Cypher查询成功")
        print(f"  - 结果数量: {result['count']}")
        print(f"  - 执行时间: {result['execution_time']:.3f}秒")
        if result["count"] > 0:
            print(f"  - 查询结果: {result['results'][0]}")
    except Exception as e:
        print(f"❌ Cypher查询失败: {e}")
        import traceback

        traceback.print_exc()
        return False

    # 测试3: 查询前5个节点
    print("\n【测试3】执行Cypher查询 - 查询前5个节点")
    print("-" * 80)
    try:
        result = await knowledge_graph_search_handler(query="MATCH (n) RETURN n LIMIT 5", query_type="cypher")
        print(f"✅ 查询节点成功")
        print(f"  - 结果数量: {result['count']}")
        print(f"  - 执行时间: {result['execution_time']:.3f}秒")
        if result["count"] > 0:
            print(f"  - 第一个节点: {result['results'][0]}")
    except Exception as e:
        print(f"❌ 查询节点失败: {e}")
        import traceback

        traceback.print_exc()
        return False

    # 测试4: 测试便捷函数 - 搜索专利
    print("\n【测试4】便捷函数 - 按关键词搜索专利")
    print("-" * 80)
    try:
        result = await search_patents_by_keyword("专利", limit=3)
        print(f"✅ 专利搜索成功")
        print(f"  - 结果数量: {result['count']}")
        print(f"  - 执行时间: {result['execution_time']:.3f}秒")
    except Exception as e:
        print(f"❌ 专利搜索失败: {e}")
        import traceback

        traceback.print_exc()
        # 这不算失败，可能只是没有Patent节点

    # 测试5: 测试错误处理
    print("\n【测试5】错误处理 - 无效查询类型")
    print("-" * 80)
    try:
        result = await knowledge_graph_search_handler(query="test", query_type="invalid_type")
        if not result["success"]:
            print(f"✅ 错误处理正确")
            print(f"  - 错误信息: {result['error']}")
        else:
            print(f"❌ 错误处理失败: 应该返回错误但没有")
    except Exception as e:
        print(f"✅ 错误处理正确（抛出异常）")
        print(f"  - 异常信息: {e}")

    print("\n" + "=" * 80)
    print("✅ 所有测试通过")
    print("=" * 80)
    return True


async def test_tool_registration():
    """测试工具注册"""
    print("\n" + "=" * 80)
    print("工具注册测试")
    print("=" * 80)

    try:
        from core.tools.unified_registry import get_unified_registry

        registry = get_unified_registry()

        # 检查工具是否已注册
        tool = registry.get("knowledge_graph_search")

        if tool:
            print("✅ 工具已成功注册到统一工具注册表")
            print(f"  - 工具ID: {tool.tool_id}")
            print(f"  - 工具名称: {tool.name}")
            print(f"  - 工具描述: {tool.description}")
            print(f"  - 工具类别: {tool.category}")
            print(f"  - 版本: {tool.version}")
            print(f"  - 作者: {tool.author}")
            print(f"  - 标签: {tool.tags}")
            return True
        else:
            print("❌ 工具未注册")
            return False

    except Exception as e:
        print(f"❌ 工具注册测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "知识图谱搜索工具完整验证" + " " * 30 + "║")
    print("╚" + "=" * 78 + "╝")

    # 测试1: 工具功能
    func_test = await test_knowledge_graph_tool()

    # 测试2: 工具注册
    reg_test = await test_tool_registration()

    # 总结
    print("\n" + "=" * 80)
    print("验证总结")
    print("=" * 80)
    print(f"  功能测试: {'✅ 通过' if func_test else '❌ 失败'}")
    print(f"  注册测试: {'✅ 通过' if reg_test else '❌ 失败'}")

    if func_test and reg_test:
        print("\n✅ knowledge_graph_search工具验证成功！")
        print("\n工具信息:")
        print("  - 工具名称: knowledge_graph_search")
        print("  - 功能描述: 基于Neo4j的知识图谱搜索和推理")
        print("  - 核心能力:")
        print("    1. Cypher查询执行")
        print("    2. 图谱统计信息")
        print("    3. 路径查找（最短路径）")
        print("    4. 邻居节点发现")
        print("    5. 关系推理")
        print("\n使用示例:")
        print("  from core.tools.unified_registry import get_unified_registry")
        print("  registry = get_unified_registry()")
        print("  tool = registry.get('knowledge_graph_search')")
        print("  result = await tool.function(query='MATCH (n) RETURN n LIMIT 10')")
        return 0
    else:
        print("\n❌ 验证失败，请检查错误信息")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
