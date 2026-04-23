"""
真实API测试脚本
测试通过小诺协调API调用小娜进行专利分析
"""

import asyncio
import time

from athena_cli.services.api_client import APIClient


async def test_real_api_connection():
    """测试真实API连接"""

    print("\n" + "="*60)
    print("真实API连接测试")
    print("="*60 + "\n")

    # 创建客户端（使用真实API）
    client = APIClient(use_real_api=True, real_api_url="http://localhost:8009")

    # 测试连接
    print("🔍 测试API连接...")
    result = await client.test_connection()

    print(f"状态: {result['status']}")
    print(f"API类型: {result.get('api_type', 'unknown')}")
    print(f"API端点: {result.get('api_endpoint', 'unknown')}")

    if result['status'] == 'ok':
        print(f"服务: {result.get('service', 'unknown')}")
        print(f"智能体: {result.get('agent_name', 'unknown')}")
        print(f"已初始化: {result.get('initialized', False)}")
        print(f"可用智能体: {result.get('available_agents', [])}")
        print(f"响应时间: {result.get('response_time', 0):.3f}秒")

        if 'cache' in result:
            print(f"缓存统计: {result['cache']}")

        print("\n✅ 真实API连接成功！")
        return True
    else:
        print(f"\n❌ 真实API连接失败: {result.get('error', 'unknown')}")
        return False

    await client.close()


async def test_real_search():
    """测试真实搜索功能"""

    print("\n" + "="*60)
    print("真实搜索功能测试")
    print("="*60 + "\n")

    # 创建客户端（使用真实API）
    client = APIClient(use_real_api=True, real_api_url="http://localhost:8009", enable_cache=True)

    query = "人工智能专利"
    limit = 3

    print(f"🔍 搜索专利: {query}")
    print(f"结果数量: {limit}\n")

    start_time = time.time()
    result = await client.search_patents(query, limit)
    elapsed_time = time.time() - start_time

    print(f"✅ 搜索完成，耗时: {elapsed_time:.2f}秒")
    print(f"查询: {result['query']}")
    print(f"总数: {result['total']}")
    print(f"数据源: {result.get('source', 'unknown')}")

    if result['results']:
        print("\n搜索结果:")
        for i, item in enumerate(result['results'][:3], 1):
            print(f"  {i}. {item.get('id', 'N/A')} - {item.get('title', 'N/A')}")
            print(f"     申请人: {item.get('applicant', 'N/A')}")
            print(f"     日期: {item.get('date', 'N/A')}")
            print(f"     评分: {item.get('score', 0):.2f}")

    await client.close()


async def test_real_analyze():
    """测试真实分析功能"""

    print("\n" + "="*60)
    print("真实分析功能测试")
    print("="*60 + "\n")

    # 创建客户端（使用真实API）
    client = APIClient(use_real_api=True, real_api_url="http://localhost:8009", enable_cache=True)

    patent_id = "201921401279.9"  # 济南力邦案件专利号
    analysis_type = "creativity"

    print(f"🔬 分析专利: {patent_id}")
    print(f"分析类型: {analysis_type}\n")

    start_time = time.time()
    result = await client.analyze_patent(patent_id, analysis_type)
    elapsed_time = time.time() - start_time

    print(f"✅ 分析完成，耗时: {elapsed_time:.2f}秒")
    print(f"专利号: {result['patent_id']}")
    print(f"分析类型: {result['analysis_type']}")
    print(f"创造性高度: {result.get('creativity_level', 'N/A')}")
    print(f"技术效果: {result.get('technical_effect', 'N/A')}")
    print(f"授权前景: {result.get('authorization_prospects', 'N/A')}")
    print(f"置信度: {result.get('confidence', 0):.0%}")
    print(f"数据源: {result.get('source', 'unknown')}")

    if result.get('key_features'):
        print("\n关键特征:")
        for feature in result['key_features']:
            print(f"  - {feature}")

    await client.close()


async def test_jinan_libang_scenario():
    """测试济南力邦场景（小规模）"""

    print("\n" + "="*60)
    print("济南力邦场景测试（小规模 - 10个专利）")
    print("="*60 + "\n")

    # 创建客户端（使用真实API）
    client = APIClient(
        use_real_api=True,
        real_api_url="http://localhost:8009",
        enable_cache=True,
        max_concurrent=5,  # 降低并发数，避免过载
    )

    # 测试数据：10个专利号（模拟济南力邦场景）
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

    print("🚀 批量分析测试")
    print(f"专利数量: {len(patent_ids)}")
    print("并发数: 5\n")

    # 测试连接
    print("测试API连接...")
    conn_result = await client.test_connection()
    if conn_result['status'] != 'ok':
        print("❌ API连接失败，退出测试")
        await client.close()
        return

    print("✅ API连接正常\n")

    # 批量分析
    print("开始批量分析...")
    start_time = time.time()

    results = await client.batch_analyze(patent_ids, "creativity")

    elapsed_time = time.time() - start_time

    # 统计
    total = len(results)
    completed = sum(1 for r in results if r.get("status") == "completed")
    failed = sum(1 for r in results if r.get("status") == "failed")

    print("\n✅ 批量分析完成！")
    print(f"总耗时: {elapsed_time:.2f}秒 ({elapsed_time/60:.2f}分钟)")
    print(f"总计: {total}")
    print(f"成功: {completed}")
    print(f"失败: {failed}")

    if completed > 0:
        success_rate = (completed / total) * 100
        print(f"成功率: {success_rate:.1f}%")
        print(f"平均每个: {elapsed_time/total:.2f}秒")

    # 缓存统计
    cache_stats = client.get_cache_stats()
    print(f"\n缓存统计: {cache_stats}")

    # 效率对比（基于真实API）
    web_time = total * 30  # 假设Web需要30秒/个
    print("\n⭐ 效率对比（估算）:")
    print(f"  Web预估: {web_time/60:.1f}分钟 ({web_time//60}分钟{web_time%60:.0f}秒)")
    print(f"  CLI实际: {elapsed_time/60:.2f}分钟")
    print(f"  效率提升: {(web_time/60)/(elapsed_time/60):.1f}x")

    # 数据源统计
    sources = {}
    for r in results:
        if r.get("status") == "completed":
            source = r.get("result", {}).get("source", "unknown")
            sources[source] = sources.get(source, 0) + 1

    print("\n数据源统计:")
    for source, count in sources.items():
        print(f"  {source}: {count}个")

    await client.close()


async def main():
    """运行所有真实API测试"""

    print("\n🚀 Athena CLI - 真实API测试套件")
    print("   目标: 验证真实API调用和数据质量\n")

    try:
        # 测试1: API连接
        connection_ok = await test_real_api_connection()

        if not connection_ok:
            print("\n⚠️  真实API不可用，使用降级模式（模拟数据）")
            print("    请确保小诺协调服务运行在 http://localhost:8009")
            return

        # 测试2: 搜索功能
        await test_real_search()

        # 测试3: 分析功能
        await test_real_analyze()

        # 测试4: 济南力邦场景（小规模）
        await test_jinan_libang_scenario()

        print("\n" + "="*60)
        print("✅ 所有真实API测试完成")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
