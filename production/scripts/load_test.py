#!/usr/bin/env python3
"""
专利检索API负载测试
Patent Retrieval API Load Test

测试生产环境的性能和稳定性
"""

from __future__ import annotations
import argparse
import asyncio
import logging
import statistics
import time
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

import aiohttp


class LoadTestResult:
    """负载测试结果"""
    def __init__(self):
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.response_times = []
        self.errors = []
        self.start_time = None
        self.end_time = None

    def add_success(self, response_time: float) -> None:
        """添加成功请求"""
        self.successful_requests += 1
        self.total_requests += 1
        self.response_times.append(response_time)

    def add_failure(self, error: str) -> None:
        """添加失败请求"""
        self.failed_requests += 1
        self.total_requests += 1
        self.errors.append(error)

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        if not self.response_times:
            return {
                "total_requests": self.total_requests,
                "success_rate": 0,
                "avg_response_time": 0,
                "min_response_time": 0,
                "max_response_time": 0,
                "p95_response_time": 0,
                "p99_response_time": 0,
                "throughput": 0
            }

        duration = (self.end_time - self.start_time) if self.end_time and self.start_time else 1

        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": (self.successful_requests / self.total_requests) * 100,
            "avg_response_time": statistics.mean(self.response_times),
            "min_response_time": min(self.response_times),
            "max_response_time": max(self.response_times),
            "p95_response_time": statistics.quantiles(self.response_times, n=20)[18] if len(self.response_times) >= 20 else max(self.response_times),
            "p99_response_time": statistics.quantiles(self.response_times, n=100)[98] if len(self.response_times) >= 100 else max(self.response_times),
            "throughput": self.total_requests / duration
        }

class PatentAPILoadTester:
    """专利API负载测试器"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None

        # 测试用例
        self.test_queries = [
            "发明专利的创造性判断标准",
            "专利无效宣告程序有哪些",
            "外观设计专利的保护范围",
            "专利侵权赔偿如何计算",
            "实用新型专利的审查要求",
            "专利优先权的确定条件",
            "药品专利的例外规定",
            "专利复审委员会的决定程序"
        ]

    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60),
            connector=aiohttp.TCPConnector(limit=100)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                return response.status == 200
        except Exception as e:
            logger.debug(f"空except块已触发: {e}")
            return False

    async def single_request(self, endpoint: str, data: dict[str, Any]) -> dict[str, Any]:
        """单次请求测试"""
        try:
            start_time = time.time()

            async with self.session.post(
                f"{self.base_url}{endpoint}",
                json=data,
                headers={"Content-Type": "application/json"}
            ) as response:
                response_time = time.time() - start_time

                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "response_time": response_time,
                        "status_code": response.status,
                        "result_count": result.get("total_results", 0)
                    }
                else:
                    return {
                        "success": False,
                        "response_time": response_time,
                        "status_code": response.status,
                        "error": f"HTTP {response.status}"
                    }

        except Exception as e:
            return {
                "success": False,
                "response_time": 0,
                "error": str(e)
            }

    async def test_patent_search(self, concurrent_users: int = 10, requests_per_user: int = 5) -> LoadTestResult:
        """测试专利搜索接口"""
        print(f"🔍 测试专利搜索接口 ({concurrent_users} 并发用户, 每用户 {requests_per_user} 请求)")

        result = LoadTestResult()
        result.start_time = time.time()

        # 创建并发任务
        tasks = []
        for user_id in range(concurrent_users):
            for request_id in range(requests_per_user):
                task = self._user_search_task(user_id, request_id, result)
                tasks.append(task)

        # 执行所有任务
        await asyncio.gather(*tasks, return_exceptions=True)

        result.end_time = time.time()
        return result

    async def _user_search_task(self, user_id: int, request_id: int, result: LoadTestResult):
        """用户搜索任务"""
        # 随机选择查询
        import random
        query = random.choice(self.test_queries)

        search_data = {
            "query": query,
            "top_k": 10,
            "search_type": "hybrid"
        }

        request_result = await self.single_request("/api/v1/search", search_data)

        if request_result["success"]:
            result.add_success(request_result["response_time"])
        else:
            result.add_failure(request_result.get("error", "Unknown error"))

    async def test_semantic_analysis(self, concurrent_users: int = 5, requests_per_user: int = 3) -> LoadTestResult:
        """测试语义分析接口"""
        print(f"🧠 测试语义分析接口 ({concurrent_users} 并发用户, 每用户 {requests_per_user} 请求)")

        result = LoadTestResult()
        result.start_time = time.time()

        # 创建并发任务
        tasks = []
        for user_id in range(concurrent_users):
            for request_id in range(requests_per_user):
                task = self._user_analysis_task(user_id, request_id, result)
                tasks.append(task)

        # 执行所有任务
        await asyncio.gather(*tasks, return_exceptions=True)

        result.end_time = time.time()
        return result

    async def _user_analysis_task(self, user_id: int, request_id: int, result: LoadTestResult):
        """用户分析任务"""
        analysis_data = {
            "text": "本发明涉及一种新型数据存储方法，具有很高的创新性和实用性。",
            "analysis_type": "comprehensive"
        }

        request_result = await self.single_request("/api/v1/semantic-analysis", analysis_data)

        if request_result["success"]:
            result.add_success(request_result["response_time"])
        else:
            result.add_failure(request_result.get("error", "Unknown error"))

    async def test_case_recommendation(self, concurrent_users: int = 3, requests_per_user: int = 2) -> LoadTestResult:
        """测试案例推荐接口"""
        print(f"🎯 测试案例推荐接口 ({concurrent_users} 并发用户, 每用户 {requests_per_user} 请求)")

        result = LoadTestResult()
        result.start_time = time.time()

        # 创建并发任务
        tasks = []
        for user_id in range(concurrent_users):
            for request_id in range(requests_per_user):
                task = self._user_recommendation_task(user_id, request_id, result)
                tasks.append(task)

        # 执行所有任务
        await asyncio.gather(*tasks, return_exceptions=True)

        result.end_time = time.time()
        return result

    async def _user_recommendation_task(self, user_id: int, request_id: int, result: LoadTestResult):
        """用户推荐任务"""
        recommendation_data = {
            "case_description": "涉及通信技术的专利侵权纠纷，需要查找类似案例",
            "similarity_threshold": 0.7,
            "max_recommendations": 5
        }

        request_result = await self.single_request("/api/v1/case-recommendation", recommendation_data)

        if request_result["success"]:
            result.add_success(request_result["response_time"])
        else:
            result.add_failure(request_result.get("error", "Unknown error"))

    def print_results(self, test_name: str, result: LoadTestResult) -> Any:
        """打印测试结果"""
        stats = result.get_stats()

        print(f"\n📊 {test_name} 测试结果:")
        print(f"   总请求数: {stats['total_requests']}")
        print(f"   成功请求: {stats['successful_requests']}")
        print(f"   失败请求: {stats['failed_requests']}")
        print(f"   成功率: {stats['success_rate']:.2f}%")
        print(f"   平均响应时间: {stats['avg_response_time']:.3f}秒")
        print(f"   最小响应时间: {stats['min_response_time']:.3f}秒")
        print(f"   最大响应时间: {stats['max_response_time']:.3f}秒")
        print(f"   P95响应时间: {stats['p95_response_time']:.3f}秒")
        print(f"   P99响应时间: {stats['p99_response_time']:.3f}秒")
        print(f"   吞吐量: {stats['throughput']:.2f} 请求/秒")

        if result.errors:
            print("   错误样本:")
            for i, error in enumerate(result.errors[:3]):
                print(f"     {i+1}. {error}")

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="专利检索API负载测试")
    parser.add_argument("--url", default="http://localhost:8000", help="API服务地址")
    parser.add_argument("--search-users", type=int, default=10, help="搜索测试并发用户数")
    parser.add_argument("--search-requests", type=int, default=5, help="搜索测试每用户请求数")
    parser.add_argument("--analysis-users", type=int, default=5, help="分析测试并发用户数")
    parser.add_argument("--analysis-requests", type=int, default=3, help="分析测试每用户请求数")
    parser.add_argument("--recommendation-users", type=int, default=3, help="推荐测试并发用户数")
    parser.add_argument("--recommendation-requests", type=int, default=2, help="推荐测试每用户请求数")

    args = parser.parse_args()

    print("🚀 开始专利检索API负载测试")
    print("=" * 60)
    print(f"测试目标: {args.url}")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    async with PatentAPILoadTester(args.url) as tester:
        # 健康检查
        print("🔍 执行健康检查...")
        if not await tester.health_check():
            print("❌ 健康检查失败，API服务不可用")
            return
        print("✅ 健康检查通过")

        # 测试专利搜索
        search_result = await tester.test_patent_search(
            args.search_users, args.search_requests
        )
        tester.print_results("专利搜索", search_result)

        # 测试语义分析
        analysis_result = await tester.test_semantic_analysis(
            args.analysis_users, args.analysis_requests
        )
        tester.print_results("语义分析", analysis_result)

        # 测试案例推荐
        recommendation_result = await tester.test_case_recommendation(
            args.recommendation_users, args.recommendation_requests
        )
        tester.print_results("案例推荐", recommendation_result)

        # 总体评估
        print("\n" + "=" * 60)
        print("📈 总体性能评估:")

        total_requests = search_result.total_requests + analysis_result.total_requests + recommendation_result.total_requests
        total_success = search_result.successful_requests + analysis_result.successful_requests + recommendation_result.successful_requests
        total_time = (search_result.end_time - search_result.start_time)

        overall_success_rate = (total_success / total_requests) * 100 if total_requests > 0 else 0
        overall_throughput = total_requests / total_time if total_time > 0 else 0

        print(f"   总请求数: {total_requests}")
        print(f"   总成功数: {total_success}")
        print(f"   总成功率: {overall_success_rate:.2f}%")
        print(f"   总吞吐量: {overall_throughput:.2f} 请求/秒")
        print(f"   测试时长: {total_time:.2f}秒")

        # 性能评级
        if overall_success_rate >= 99 and overall_throughput >= 20:
            grade = "A+ (优秀)"
        elif overall_success_rate >= 95 and overall_throughput >= 15:
            grade = "A (良好)"
        elif overall_success_rate >= 90 and overall_throughput >= 10:
            grade = "B (一般)"
        elif overall_success_rate >= 80:
            grade = "C (较差)"
        else:
            grade = "D (不合格)"

        print(f"   性能评级: {grade}")

        print("=" * 60)
        print("🎉 负载测试完成!")

if __name__ == "__main__":
    asyncio.run(main())
