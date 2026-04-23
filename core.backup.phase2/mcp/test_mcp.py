#!/usr/bin/env python3
from __future__ import annotations
"""
MCP客户端测试脚本

测试MCP服务器的工具调用和资源读取功能

作者: 小诺·双鱼座
创建时间: 2025-01-05
"""

import asyncio
import json
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.mcp.athena_mcp_client import (
    get_mcp_client,
    get_mcp_invoker,
)


async def test_connect_to_server():
    """测试1: 连接到MCP服务器"""
    print("\n" + "=" * 60)
    print("🧪 测试1: 连接到MCP服务器")
    print("=" * 60)

    client = get_mcp_client()

    # 连接到Athena MCP服务器
    server_info = await client.connect_to_server(
        command="python", args=["-m", "core.mcp.athena_mcp_server"]
    )

    if server_info["status"] == "connected":
        print(f"✅ 成功连接到服务器: {server_info['server_name']}")
        print(f"   可用工具数: {len(server_info['tools'])}")
        print(f"   可用资源数: {len(server_info['resources'])}")

        # 列出工具
        print("\n📋 可用工具:")
        for tool in server_info["tools"]:
            print(f"   - {tool['name']}: {tool['description']}")

        return True
    else:
        print(f"❌ 连接失败: {server_info.get('error')}")
        return False


async def test_patent_search():
    """测试2: 专利检索工具"""
    print("\n" + "=" * 60)
    print("🧪 测试2: 专利检索工具")
    print("=" * 60)

    invoker = get_mcp_invoker()

    result = await invoker.search_patents(query="深度学习 图像识别", database="all", limit=10)

    print("\n🔍 专利检索结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if result.get("success", True):
        print(f"\n✅ 检索成功,找到 {result.get('total_found', 0)} 个相关专利")
    else:
        print(f"\n❌ 检索失败: {result.get('error')}")


async def test_patent_analysis():
    """测试3: 专利分析工具"""
    print("\n" + "=" * 60)
    print("🧪 测试3: 专利分析工具")
    print("=" * 60)

    invoker = get_mcp_invoker()

    result = await invoker.analyze_patent(patent_id="CN123456789A", analysis_type="comprehensive")

    print("\n📊 专利分析结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if result.get("confidence"):
        print(f"\n✅ 分析完成,置信度: {result['confidence']:.1%}")


async def test_vector_search():
    """测试4: 向量搜索工具"""
    print("\n" + "=" * 60)
    print("🧪 测试4: 向量搜索工具")
    print("=" * 60)

    invoker = get_mcp_invoker()

    result = await invoker.vector_search(query="计算机视觉 深度学习", top_k=5)

    print("\n🔍 向量搜索结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if result.get("results"):
        print(f"\n✅ 搜索完成,返回 {len(result['results'])} 个结果")


async def test_knowledge_graph():
    """测试5: 知识图谱查询工具"""
    print("\n" + "=" * 60)
    print("🧪 测试5: 知识图谱查询工具")
    print("=" * 60)

    invoker = get_mcp_invoker()

    result = await invoker.query_knowledge_graph(entity="某科技公司", depth=2)

    print("\n🕸️ 知识图谱查询结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if result.get("nodes_found"):
        print(
            f"\n✅ 查询完成,找到 {result['nodes_found']} 个节点,{result['relations_found']} 条关系"
        )


async def test_read_resource():
    """测试6: 读取资源"""
    print("\n" + "=" * 60)
    print("🧪 测试6: 读取资源")
    print("=" * 60)

    client = get_mcp_client()

    # 读取专利详情资源
    content = await client.read_resource("athena_mcp_server.py", "patent://CN123456789A")

    print("\n📄 专利详情资源:")
    print(content)

    if "专利详情" in content:
        print("\n✅ 资源读取成功")


async def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("🧪 MCP客户端测试套件")
    print("测试Anthropic MCP标准集成")
    print("=" * 60)

    try:
        # 测试1: 连接服务器
        connected = await test_connect_to_server()
        if not connected:
            print("\n❌ 无法连接到MCP服务器,终止测试")
            return

        # 稍等服务器初始化
        await asyncio.sleep(1)

        # 测试2-6: 工具调用和资源读取
        await test_patent_search()
        await test_patent_analysis()
        await test_vector_search()
        await test_knowledge_graph()
        await test_read_resource()

        print("\n" + "=" * 60)
        print("✅ 所有测试完成!")
        print("=" * 60)

        # 清理
        client = get_mcp_client()
        await client.close()

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
