"""
使用urllib适配器的真实API测试
"""

import time

from athena_cli.services.urllib_api_adapter import UrllibAPIAdapter


def test_real_api_with_urllib():
    """使用urllib测试真实API"""

    print("\n" + "="*60)
    print("真实API测试（使用urllib适配器）")
    print("="*60 + "\n")

    # 创建urllib适配器
    adapter = UrllibAPIAdapter(base_url="http://localhost:8009")

    # 测试1: API连接
    print("🔍 测试1: API连接")
    print("-" * 40)

    result = adapter.test_connection()

    if result['status'] == 'ok':
        print("✅ 连接成功！")
        print(f"  服务: {result.get('service', 'unknown')}")
        print(f"  智能体: {result.get('agent_name', 'unknown')}")
        print(f"  已初始化: {result.get('initialized', False)}")
        print(f"  可用智能体: {result.get('available_agents', [])}")
        print()
    else:
        print(f"❌ 连接失败: {result.get('error', 'unknown')}")
        return

    # 测试2: 专利搜索
    print("🔍 测试2: 专利搜索")
    print("-" * 40)

    query = "人工智能专利"
    print(f"查询: {query}\n")

    start_time = time.time()
    search_result = adapter.search_patents(query, limit=3)
    elapsed_time = time.time() - start_time

    print(f"✅ 搜索完成，耗时: {elapsed_time:.2f}秒")
    print(f"  总数: {search_result['total']}")
    print(f"  数据源: {search_result.get('source', 'unknown')}")

    if search_result['results']:
        print("\n  搜索结果:")
        for i, item in enumerate(search_result['results'][:3], 1):
            print(f"    {i}. {item.get('id', 'N/A')} - {item.get('title', 'N/A')}")
    print()

    # 测试3: 专利分析
    print("🔬 测试3: 专利分析")
    print("-" * 40)

    patent_id = "201921401279.9"
    print(f"专利号: {patent_id}\n")

    start_time = time.time()
    analyze_result = adapter.analyze_patent(patent_id, "creativity")
    elapsed_time = time.time() - start_time

    print(f"✅ 分析完成，耗时: {elapsed_time:.2f}秒")
    print(f"  创造性高度: {analyze_result.get('creativity_level', 'N/A')}")
    print(f"  技术效果: {analyze_result.get('technical_effect', 'N/A')}")
    print(f"  授权前景: {analyze_result.get('authorization_prospects', 'N/A')}")
    print(f"  置信度: {analyze_result.get('confidence', 0):.0%}")
    print(f"  数据源: {analyze_result.get('source', 'unknown')}")

    if analyze_result.get('key_features'):
        print("\n  关键特征:")
        for feature in analyze_result['key_features']:
            print(f"    - {feature}")
    print()

    # 测试4: 批量分析（济南力邦小规模测试）
    print("🚀 测试4: 批量分析（济南力邦场景 - 10个专利）")
    print("-" * 40)

    patent_ids = [
        "201921401279.9",
        "CN202010123456A",
        "CN202020123456A",
        "CN1000A",
        "CN1001A",
        "CN1002A",
        "CN1003A",
        "CN1004A",
        "CN1005A",
        "CN1006A",
    ]

    print(f"专利数量: {len(patent_ids)}\n")
    print("开始批量分析...")

    start_time = time.time()
    results = []
    for i, patent_id in enumerate(patent_ids, 1):
        print(f"  [{i}/{len(patent_ids)}] {patent_id}...", end=" ")
        result = adapter.analyze_patent(patent_id, "creativity")
        results.append({
            "patent_id": patent_id,
            "status": "completed",
            "result": result,
        })
        source = result.get('source', 'unknown')
        print(f"✓ ({source})")

    elapsed_time = time.time() - start_time

    print("\n✅ 批量分析完成！")
    print(f"  总耗时: {elapsed_time:.2f}秒 ({elapsed_time/60:.2f}分钟)")
    print(f"  成功: {len(results)}/{len(patent_ids)}")
    print(f"  平均每个: {elapsed_time/len(patent_ids):.2f}秒")

    # 数据源统计
    sources = {}
    for r in results:
        source = r.get("result", {}).get("source", "unknown")
        sources[source] = sources.get(source, 0) + 1

    print("\n  数据源统计:")
    for source, count in sources.items():
        print(f"    {source}: {count}个")

    # 效率对比
    web_time = len(patent_ids) * 30  # Web: 30秒/个
    print("\n⭐ 效率对比（估算）:")
    print(f"  Web预估: {web_time/60:.1f}分钟")
    print(f"  CLI实际: {elapsed_time/60:.2f}分钟")
    print(f"  效率提升: {(web_time/60)/(elapsed_time/60):.1f}x")

    print("\n" + "="*60)
    print("✅ 所有测试完成！")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_real_api_with_urllib()
