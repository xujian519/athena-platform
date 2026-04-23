"""
性能测试脚本
测试批量处理的并发优化效果
"""

import asyncio
import time

from athena_cli.services.api_client import APIClient


async def test_concurrent_analyze():
    """测试并发批量分析性能"""

    print("\n" + "="*60)
    print("性能测试: 并发批量分析")
    print("="*60 + "\n")

    # 测试数据: 10个专利号
    patent_ids = [f"CN{1000+i}A" for i in range(10)]

    # 测试1: 小并发数 (max_concurrent=3)
    print("📊 测试1: 小并发数 (max_concurrent=3)")
    client1 = APIClient(max_concurrent=3, enable_cache=False)
    start_time = time.time()
    results1 = await client1.batch_analyze(patent_ids)
    elapsed_time1 = time.time() - start_time

    success_count1 = sum(1 for r in results1 if r.get("status") == "completed")

    print(f"  总耗时: {elapsed_time1:.2f}秒")
    print(f"  成功: {success_count1}/{len(patent_ids)}")
    print(f"  平均每个: {elapsed_time1/len(patent_ids):.2f}秒")
    await client1.close()

    # 测试2: 中并发数 (max_concurrent=10)
    print("\n📊 测试2: 中并发数 (max_concurrent=10)")
    client2 = APIClient(max_concurrent=10, enable_cache=False)
    start_time = time.time()
    results2 = await client2.batch_analyze(patent_ids)
    elapsed_time2 = time.time() - start_time

    success_count2 = sum(1 for r in results2 if r.get("status") == "completed")

    print(f"  总耗时: {elapsed_time2:.2f}秒")
    print(f"  成功: {success_count2}/{len(patent_ids)}")
    print(f"  平均每个: {elapsed_time2/len(patent_ids):.2f}秒")
    await client2.close()

    # 测试3: 大并发数 (max_concurrent=20)
    print("\n📊 测试3: 大并发数 (max_concurrent=20)")
    client3 = APIClient(max_concurrent=20, enable_cache=False)
    start_time = time.time()
    results3 = await client3.batch_analyze(patent_ids)
    elapsed_time3 = time.time() - start_time

    success_count3 = sum(1 for r in results3 if r.get("status") == "completed")

    print(f"  总耗时: {elapsed_time3:.2f}秒")
    print(f"  成功: {success_count3}/{len(patent_ids)}")
    print(f"  平均每个: {elapsed_time3/len(patent_ids):.2f}秒")
    await client3.close()

    # 性能对比
    print("\n⭐ 性能对比:")
    print(f"  小并发 → 中并发: {(elapsed_time1/elapsed_time2):.1f}x 提升")
    print(f"  小并发 → 大并发: {(elapsed_time1/elapsed_time3):.1f}x 提升")

    # 估算: 串行处理需要的时间 (2秒/个)
    serial_time = len(patent_ids) * 2.0
    print(f"\n  串行处理预估: {serial_time:.1f}秒")
    print(f"  并发处理实际: {elapsed_time3:.2f}秒")
    print(f"  效率提升: {(serial_time/elapsed_time3):.1f}x")

    return elapsed_time3


async def test_cache_performance():
    """测试缓存性能"""

    print("\n" + "="*60)
    print("性能测试: 缓存效果")
    print("="*60 + "\n")

    patent_id = "CN123456A"

    # 测试1: 无缓存
    print("📊 测试1: 无缓存 (3次重复查询)")
    client1 = APIClient(enable_cache=False)
    start_time = time.time()

    for i in range(3):
        await client1.analyze_patent(patent_id, use_cache=False)

    elapsed_time1 = time.time() - start_time
    print(f"  总耗时: {elapsed_time1:.2f}秒")
    print(f"  平均每次: {elapsed_time1/3:.2f}秒")
    await client1.close()

    # 测试2: 有缓存
    print("\n📊 测试2: 有缓存 (3次重复查询)")
    client2 = APIClient(enable_cache=True)
    start_time = time.time()

    for i in range(3):
        await client2.analyze_patent(patent_id, use_cache=True)

    elapsed_time2 = time.time() - start_time
    print(f"  总耗时: {elapsed_time2:.2f}秒")
    print(f"  平均每次: {elapsed_time2/3:.2f}秒")

    cache_stats = client2.get_cache_stats()
    print(f"  缓存大小: {cache_stats['size']}")

    await client2.close()

    # 性能对比
    print("\n⭐ 缓存效果:")
    print(f"  缓存加速: {(elapsed_time1/elapsed_time2):.1f}x")

    return elapsed_time2


async def test_large_batch():
    """测试大批量处理 (模拟济南力邦188个专利)"""

    print("\n" + "="*60)
    print("性能测试: 大批量处理 (济南力邦场景)")
    print("="*60 + "\n")

    # 模拟188个专利
    patent_ids = [f"CN{1000+i}A" for i in range(188)]

    print(f"📊 测试: {len(patent_ids)}个专利批量分析")
    print("  (使用max_concurrent=20)\n")

    client = APIClient(max_concurrent=20, enable_cache=True)
    start_time = time.time()

    results = await client.batch_analyze(patent_ids)

    elapsed_time = time.time() - start_time

    success_count = sum(1 for r in results if r.get("status") == "completed")

    print(f"  总耗时: {elapsed_time:.2f}秒 ({elapsed_time/60:.2f}分钟)")
    print(f"  成功: {success_count}/{len(patent_ids)}")
    print(f"  平均每个: {elapsed_time/len(patent_ids):.2f}秒")

    # 对比Web操作
    web_time = len(patent_ids) * 3 * 60  # Web: 3分钟/个
    print("\n⭐ 效率对比:")
    print(f"  Web操作: {web_time/60:.1f}分钟 ({web_time//3600}小时{(web_time%3600)//60}分钟)")
    print(f"  CLI实际: {elapsed_time/60:.2f}分钟")
    print(f"  效率提升: {(web_time/60)/(elapsed_time/60):.1f}x")

    cache_stats = client.get_cache_stats()
    print(f"\n  缓存统计: {cache_stats}")

    await client.close()

    return elapsed_time


async def main():
    """运行所有性能测试"""

    print("\n🚀 Athena CLI - 性能测试套件")
    print("   目标: 验证并发优化和缓存效果\n")

    try:
        # 测试1: 并发性能
        await test_concurrent_analyze()

        # 测试2: 缓存性能
        await test_cache_performance()

        # 测试3: 大批量处理
        await test_large_batch()

        print("\n" + "="*60)
        print("✅ 所有性能测试完成")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
