"""
测试oMLX API适配器
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import json

from athena_cli.services.omlox_api_adapter import OmloxAPIAdapter


def test_omlox_adapter():
    """测试oMLX适配器"""

    print("\n" + "="*60)
    print("测试oMLX API适配器")
    print("=" * 60 + "\n")

    # 创建oMLX适配器
    adapter = OmloxAPIAdapter(base_url="http://localhost:8009")

    # 测试1: API连接
    print("🔍 测试1: API连接")
    print("-" * 40)

    result = adapter.test_connection()

    print(f"状态: {result['status']}")
    print(f"适配器: {result.get('adapter', 'unknown')}")

    if result['status'] == 'ok':
        print("✅ 连接成功！")
        print(f"  服务: {result.get('service', 'unknown')}")
        print(f"  智能体: {result.get('agent_name', 'unknown')}")
        print(f"  已初始化: {result.get('initialized', False)}")

        # 打印详细信息
        if 'details' in result:
            print("\n  详细信息:")
            details = result['details']
            print(f"    default_model: {details.get('default_model', 'N/A')}")
            engine_pool = details.get('engine_pool', {})
            print(f"    model_count: {engine_pool.get('model_count', 'N/A')}")
            print(f"    loaded_count: {engine_pool.get('loaded_count', 'N/A')}")
    else:
        print(f"❌ 连接失败: {result.get('error', 'unknown')}")
        return

    # 测试2: 查看可用的MCP工具
    print("\n🔍 测试2: 查看可用的MCP工具")
    print("-" * 40)

    try:
        # 直接调用curl获取MCP工具列表
        import subprocess
        result = subprocess.run(
            ["curl", "-s", "http://localhost:8009/v1/mcp/tools"],
            capture_output=True,
            text=True,
        )
        tools = json.loads(result.stdout)
        print("✅ 成功获取MCP工具列表")
        print(f"  工具数量: {len(tools)}")

        if tools:
            print("\n  前5个工具:")
            for i, tool in enumerate(tools[:5], 1):
                print(f"    {i}. {tool.get('name', 'N/A')} - {tool.get('description', 'N/A')}")

        # 检查是否有专利相关的工具
        patent_tools = [t for t in tools if 'patent' in t.get('name', '').lower()]
        if patent_tools:
            print("\n  专利相关工具:")
            for tool in patent_tools:
                print(f"    - {tool.get('name')}: {tool.get('description')}")
        else:
            print("\n  ⚠️  未找到专利相关的MCP工具")
            print(f"  可用工具类型: {set(t.get('name', '').split('_')[0] for t in tools)}")

    except Exception as e:
        print(f"❌ 获取MCP工具失败: {e}")

    # 测试3: 专利搜索（使用MCP工具）
    print("\n🔍 测试3: 专利搜索（MCP工具）")
    print("-" * 40)

    query = "人工智能专利"
    print(f"查询: {query}")

    try:
        search_result = adapter.search_patents(query, limit=3)
        print("\n✅ 搜索完成")
        print(f"  总数: {search_result['total']}")
        print(f"  数据源: {search_result.get('source', 'unknown')}")

        if search_result['results']:
            print("\n  搜索结果:")
            for i, item in enumerate(search_result['results'][:3], 1):
                print(f"    {i}. {item.get('id', 'N/A')} - {item.get('title', 'N/A')}")
    except Exception as e:
        print(f"❌ 搜索失败: {e}")

    # 测试4: 专利分析（使用LLM）
    print("\n🔬 测试4: 专利分析（LLM推理）")
    print("-" * 40)

    patent_id = "201921401279.9"
    print(f"专利号: {patent_id}")

    try:
        analyze_result = adapter.analyze_patent(patent_id, "creativity")
        print("\n✅ 分析完成")
        print(f"  创造性高度: {analyze_result.get('creativity_level', 'N/A')}")
        print(f"  技术效果: {analyze_result.get('technical_effect', 'N/A')[:100]}...")
        print(f"  授权前景: {analyze_result.get('authorization_prospects', 'N/A')}")
        print(f"  置信度: {analyze_result.get('confidence', 0):.0%}")
        print(f"  数据源: {analyze_result.get('source', 'unknown')}")

        if analyze_result.get('key_features'):
            print("\n  关键特征:")
            for feature in analyze_result['key_features']:
                print(f"    - {feature}")
    except Exception as e:
        print(f"❌ 分析失败: {e}")

    print("\n" + "="*60)
    print("✅ 所有测试完成！")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_omlox_adapter()
