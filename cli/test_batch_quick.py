"""
快速测试批量分析功能
"""

import asyncio
import time
from athena_cli.services.api_client import SyncAPIClient


def test_batch_analyze():
    """测试批量分析"""

    # 读取专利号
    with open("patent_ids.txt", "r") as f:
        patent_ids = [line.strip() for line in f if line.strip()]

    print(f"\n🚀 批量分析测试")
    print(f"专利数量: {len(patent_ids)}\n")

    # 创建客户端
    client = SyncAPIClient(enable_cache=True, max_concurrent=10)

    # 测试连接
    print("测试API连接...")
    result = client.test_connection()
    print(f"状态: {result['status']}")
    print(f"响应时间: {result.get('response_time', 0):.3f}秒\n")

    # 批量分析
    print("开始批量分析...")
    start_time = time.time()

    results = client.batch_analyze(patent_ids)

    elapsed_time = time.time() - start_time

    # 统计
    success_count = sum(1 for r in results if r.get("status") == "completed")

    print(f"\n✅ 批量分析完成！")
    print(f"总耗时: {elapsed_time:.2f}秒 ({elapsed_time/60:.2f}分钟)")
    print(f"成功: {success_count}/{len(patent_ids)}")
    print(f"平均每个: {elapsed_time/len(patent_ids):.2f}秒")

    # 缓存统计
    cache_stats = client.get_cache_stats()
    print(f"\n缓存统计: {cache_stats}")

    # 效率对比
    web_time = len(patent_ids) * 3 * 60  # Web: 3分钟/个
    print(f"\n⭐ 效率对比:")
    print(f"  Web预估: {web_time/60:.1f}分钟")
    print(f"  CLI实际: {elapsed_time/60:.2f}分钟")
    print(f"  效率提升: {(web_time/60)/(elapsed_time/60):.1f}x")


if __name__ == "__main__":
    test_batch_analyze()
