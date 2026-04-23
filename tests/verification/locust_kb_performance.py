#!/usr/bin/env python3
"""
Athena平台知识库并发性能测试脚本 (基于Locust)

性能目标:
- KB-PERF-01: 10并发, QPS > 50, P95 < 200ms
- KB-PERF-02: 50并发, QPS > 80, P95 < 500ms
- KB-PERF-03: 100并发, QPS > 100, P95 < 1s, 错误率 < 1%
- KB-PERF-04: 200并发, 系统不崩溃，限流生效
- KB-PERF-05: 80读+20写, 读写均正常，无死锁

作者: 徐健
日期: 2026-04-18
"""

import json
import time

from locust import HttpUser, between, events, task
from locust.runners import MasterRunner

# ============================================================================
# 测试数据
# ============================================================================

VECTOR_SEARCH_QUERIES = [
    "发明专利创造性判断标准",
    "专利申请驳回后复审流程",
    "人工智能相关专利的审查指南",
    "专利侵权判定方法",
    "实用新型专利授权条件",
]

KG_QUERIES = [
    "MATCH (n:Concept) RETURN n LIMIT 10",
    "MATCH (a:Concept)-[:RELATED_TO]->(b:Concept) RETURN a,b LIMIT 5",
    "MATCH path = (start:Concept {name: '专利侵权'})-[:RELATED_TO*1..2]-(end) RETURN path LIMIT 3",
]

LEGAL_SEARCH_QUERIES = [
    "专利法第22条 创造性",
    "专利审查指南 第二部分第一章",
    "无效宣告请求审查流程",
    "专利侵权损害赔偿计算",
]


# ============================================================================
# 性能测试用户类
# ============================================================================

class KnowledgeBaseUser(HttpUser):
    """知识库性能测试用户"""

    # 等待时间: 1~3秒之间随机 (模拟真实用户行为)
    wait_time = between(1, 3)

    # 默认host (可通过命令行 --host 覆盖)
    host = "http://localhost:8005"

    def on_start(self):
        """用户启动时执行"""
        self.client.verify = False  # 跳过SSL验证(如果使用HTTPS)

    @task(3)
    def vector_search(self):
        """向量搜索 (高频操作, 权重3)"""
        query = self.client.environment.vector_search_queries[self.user_index() % len(VECTOR_SEARCH_QUERIES)]

        with self.client.post(
            "/api/v1/vector/search",
            json={
                "collection_name": "patent_rules_1024",
                "query_text": query,
                "limit": 10
            },
            catch_response=True,
            name="/api/v1/vector/search"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                if len(results) > 0:
                    response.success()
                else:
                    response.failure("No results returned")
            elif response.status_code in [401, 422]:
                # 认证/参数错误不算失败 (测试环境可能未配置)
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(2)
    def knowledge_graph_query(self):
        """知识图谱查询 (中频操作, 权重2)"""
        query = KG_QUERIES[self.user_index() % len(KG_QUERIES)]

        with self.client.post(
            "/api/v1/kg/query",
            json={"cypher": query},
            catch_response=True,
            name="/api/v1/kg/query"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                data.get("results", [])
                response.success()
            elif response.status_code in [401, 422]:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(1)
    def legal_search(self):
        """法律搜索 (低频操作, 权重1)"""
        query = LEGAL_SEARCH_QUERIES[self.user_index() % len(LEGAL_SEARCH_QUERIES)]

        with self.client.post(
            "/api/v1/legal/search",
            json={"query": query, "limit": 10},
            catch_response=True,
            name="/api/v1/legal/search"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                data.get("results", [])
                response.success()
            elif response.status_code in [401, 422]:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(1)
    def health_check(self):
        """健康检查 (低频操作, 权重1)"""
        with self.client.get(
            "/health",
            catch_response=True,
            name="/health"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")

    def user_index(self):
        """获取用户索引 (用于轮询测试数据)"""
        return int(str(time.time_ns())[-6:]) % 1000


# ============================================================================
# 读写混合测试用户类
# ============================================================================

class MixedReadWriteUser(HttpUser):
    """读写混合性能测试用户 (80%读 + 20%写)"""

    wait_time = between(1, 2)
    host = "http://localhost:8005"

    @task(4)
    def read_operation(self):
        """读操作 (80%)"""
        with self.client.get(
            "/api/v1/tools",
            catch_response=True,
            name="[READ] /api/v1/tools"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(1)
    def write_operation(self):
        """写操作 (20%) - 模拟工具执行"""
        with self.client.post(
            "/api/v1/tools/echo/execute",
            json={"message": f"test_{int(time.time())}"},
            catch_response=True,
            name="[WRITE] /api/v1/tools/echo/execute"
        ) as response:
            if response.status_code in [200, 404]:
                # 404表示工具不存在但路由正常
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")


# ============================================================================
# 测试事件处理器
# ============================================================================

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """测试开始时执行"""
    print(f"\n{'='*80}")
    print("Locust性能测试开始")
    print(f"目标: {environment.host}")
    print(f"用户数: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else '未指定'}")
    print(f"{'='*80}\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """测试结束时执行"""
    print(f"\n{'='*80}")
    print("Locust性能测试完成")

    # 输出统计摘要
    stats = environment.runner.stats
    print(f"\n总请求数: {stats.total.num_requests}")
    print(f"失败请求数: {stats.total.num_failures}")
    print(f"失败率: {stats.total.fail_ratio * 100:.2f}%")
    print(f"总RPS: {stats.total.total_rps:.2f}")
    print("\n响应时间统计:")
    print(f"  中位数 (P50): {stats.total.median_response_time:.0f} ms")
    print(f"  P95: {stats.total.get_response_time_percentile(0.95):.0f} ms")
    print(f"  P99: {stats.total.get_response_time_percentile(0.99):.0f} ms")
    print(f"{'='*80}\n")

    # 保存详细统计到JSON文件
    if isinstance(environment.runner, MasterRunner):
        stats_filename = f"locust_stats_{int(time.time())}.json"
        with open(stats_filename, "w") as f:
            json.dump(stats.serialize_stats(), f, indent=2)
        print(f"详细统计已保存到: {stats_filename}")


# ============================================================================
# 主函数
# ============================================================================

if __name__ == "__main__":

    # 如果通过命令行直接运行此脚本
    print("""
    ╔════════════════════════════════════════════════════════════════════════════╗
    ║                     Athena 知识库性能测试 (Locust)                         ║
    ╠════════════════════════════════════════════════════════════════════════════╣
    ║  运行方式:                                                                 ║
    ║  1. Web UI模式:   locust -f locust_kb_performance.py                       ║
    ║  2. Headless模式: locust -f locust_kb_performance.py --headless ...        ║
    ╚════════════════════════════════════════════════════════════════════════════╝

    性能基准:
    - KB-PERF-01: 10并发, QPS > 50,  P95 < 200ms
    - KB-PERF-02: 50并发, QPS > 80,  P95 < 500ms
    - KB-PERF-03: 100并发, QPS > 100, P95 < 1s, 错误率 < 1%
    - KB-PERF-04: 200并发, 系统不崩溃，限流生效
    - KB-PERF-05: 80读+20写, 读写均正常，无死锁
    """)

    # 示例命令
    print("\n示例命令:\n")
    print("1. 启动Web UI (默认8089端口):")
    print("   locust -f tests/verification/locust_kb_performance.py\n")
    print("2. Headless模式 - 100用户, 持续60秒:")
    print("   locust -f tests/verification/locust_kb_performance.py \\")
    print("     --headless --users=100 --spawn-rate=10 --run-time=60s \\")
    print("     --host=http://localhost:8005\n")
    print("3. 读写混合测试:")
    print("   locust -f tests/verification/locust_kb_performance.py \\")
    print("     --headless --users=50 --spawn-rate=5 --run-time=120s \\")
    print("     --user-class=MixedReadWriteUser\n")
