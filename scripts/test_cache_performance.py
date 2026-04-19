#!/usr/bin/env python3
"""
缓存性能测试脚本
Cache Performance Test Script

测试缓存系统的性能指标：
- 命中率
- 响应时间
- 吞吐量
"""

import asyncio
import sys
import time
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.cache.unified_cache import UnifiedCache


class CachePerformanceTester:
    """缓存性能测试器"""

    def __init__(self):
        self.cache = UnifiedCache()

    async def test_hit_rate(self, iterations: int = 1000) -> dict:
        """
        测试缓存命中率

        Args:
            iterations: 测试迭代次数

        Returns:
            测试结果
        """
        print(f"\n📊 测试缓存命中率 (iterations={iterations})...")

        # 预填充一些数据
        for i in range(100):
            await self.cache.set(f"key_{i}", f"value_{i}")

        hits = 0
        misses = 0

        start_time = time.time()

        for i in range(iterations):
            # 80%的请求访问已存在的键，20%访问不存在的键
            key = f"key_{i % 120}"

            result = await self.cache.get(key)
            if result is not None:
                hits += 1
            else:
                misses += 1

        end_time = time.time()
        total_time = end_time - start_time

        hit_rate = (hits / iterations) * 100
        avg_response_time = (total_time / iterations) * 1000  # 毫秒

        print(f"  ✅ 命中率: {hit_rate:.2f}%")
        print(f"  ✅ 平均响应时间: {avg_response_time:.2f}ms")
        print(f"  ✅ 总耗时: {total_time:.2f}s")
        print(f"  ✅ 吞吐量: {iterations/total_time:.2f} ops/s")

        return {
            "hit_rate": hit_rate,
            "hits": hits,
            "misses": misses,
            "avg_response_time_ms": avg_response_time,
            "throughput_ops": iterations / total_time,
        }

    async def test_write_performance(self, iterations: int = 1000) -> dict:
        """
        测试写入性能

        Args:
            iterations: 测试迭代次数

        Returns:
            测试结果
        """
        print(f"\n📝 测试写入性能 (iterations={iterations})...")

        start_time = time.time()

        for i in range(iterations):
            await self.cache.set(f"write_test_{i}", {"data": f"value_{i}"})

        end_time = time.time()
        total_time = end_time - start_time

        avg_write_time = (total_time / iterations) * 1000  # 毫秒
        write_throughput = iterations / total_time

        print(f"  ✅ 平均写入时间: {avg_write_time:.2f}ms")
        print(f"  ✅ 写入吞吐量: {write_throughput:.2f} ops/s")

        return {
            "avg_write_time_ms": avg_write_time,
            "write_throughput_ops": write_throughput,
        }

    async def test_batch_operations(self, batch_size: int = 100) -> dict:
        """
        测试批量操作性能

        Args:
            batch_size: 批量大小

        Returns:
            测试结果
        """
        print(f"\n📦 测试批量操作 (batch_size={batch_size})...")

        # 批量写入
        items = {f"batch_key_{i}": f"batch_value_{i}" for i in range(batch_size)}

        start_time = time.time()
        await self.cache.set_multi(items)
        batch_write_time = time.time() - start_time

        # 批量读取
        keys = list(items.keys())
        start_time = time.time()
        results = await self.cache.get_multi(keys)
        batch_read_time = time.time() - start_time

        print(f"  ✅ 批量写入时间: {batch_write_time*1000:.2f}ms")
        print(f"  ✅ 批量读取时间: {batch_read_time*1000:.2f}ms")
        print(f"  ✅ 读取命中率: {len(results)}/{batch_size}")

        return {
            "batch_write_time_ms": batch_write_time * 1000,
            "batch_read_time_ms": batch_read_time * 1000,
            "batch_size": batch_size,
        }

    async def test_concurrent_access(self, concurrent_users: int = 10, requests_per_user: int = 100) -> dict:
        """
        测试并发访问性能

        Args:
            concurrent_users: 并发用户数
            requests_per_user: 每个用户的请求数

        Returns:
            测试结果
        """
        print(f"\n👥 测试并发访问 (users={concurrent_users}, requests={requests_per_user})...")

        async def user_simulation(user_id: int):
            """模拟单个用户"""
            for i in range(requests_per_user):
                key = f"user_{user_id}_key_{i}"
                await self.cache.set(key, f"value_{i}")
                await self.cache.get(key)

        start_time = time.time()

        # 启动并发用户
        tasks = [user_simulation(i) for i in range(concurrent_users)]
        await asyncio.gather(*tasks)

        end_time = time.time()
        total_time = end_time - start_time

        total_requests = concurrent_users * requests_per_user * 2  # 每个用户读写各一次
        throughput = total_requests / total_time

        print(f"  ✅ 总请求数: {total_requests}")
        print(f"  ✅ 总耗时: {total_time:.2f}s")
        print(f"  ✅ 并发吞吐量: {throughput:.2f} ops/s")

        return {
            "concurrent_users": concurrent_users,
            "total_requests": total_requests,
            "throughput_ops": throughput,
        }

    async def run_all_tests(self):
        """运行所有性能测试"""
        print("=" * 60)
        print("🚀 缓存性能测试套件")
        print("=" * 60)

        results = {}

        # 1. 命中率测试
        results["hit_rate"] = await self.test_hit_rate(iterations=1000)

        # 2. 写入性能测试
        results["write_performance"] = await self.test_write_performance(iterations=1000)

        # 3. 批量操作测试
        results["batch_operations"] = await self.test_batch_operations(batch_size=100)

        # 4. 并发访问测试
        results["concurrent_access"] = await self.test_concurrent_access(
            concurrent_users=10, requests_per_user=100
        )

        # 5. 获取Redis统计信息
        print("\n📊 Redis统计信息:")
        stats = await self.cache.get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")

        print("\n" + "=" * 60)
        print("✅ 性能测试完成")
        print("=" * 60)

        return results


async def main():
    """主函数"""
    tester = CachePerformanceTester()
    results = await tester.run_all_tests()

    # 保存结果
    import json

    result_file = project_root / "test_results" / "cache_performance.json"
    result_file.parent.mkdir(exist_ok=True)

    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n💾 测试结果已保存到: {result_file}")


if __name__ == "__main__":
    asyncio.run(main())
