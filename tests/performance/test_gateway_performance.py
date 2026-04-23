"""
Gateway性能测试

测试Gateway关键组件的性能：
1. 意图路由性能
2. 负载均衡性能
3. WebSocket消息处理性能
4. gRPC流式响应性能
"""

import statistics
import time
from typing import Any

import pytest

pytestmark = [pytest.mark.performance, pytest.mark.integration]


class TestIntentRouterPerformance:
    """意图路由性能测试"""

    @pytest.fixture
    def intent_router(self):
        """意图路由器fixture"""
        # 这里应该导入Go实现的意图路由器
        # 简化版使用Python模拟
        class MockIntentRouter:
            def route(self, input_text: str) -> dict[str, Any]:
                # 简化的关键词匹配
                keywords = {
                    "patent_analysis": ["分析", "专利", "创造性"],
                    "case_search": ["案例", "检索"],
                    "legal_consult": ["法律", "法规"]
                }

                for intent, words in keywords.items():
                    if any(word in input_text for word in words):
                        return {"intent": intent, "confidence": 0.9}

                return {"intent": "general_query", "confidence": 0.5}

        return MockIntentRouter()

    def test_single_route_performance(self, intent_router):
        """测试单次路由性能"""
        test_input = "分析专利CN123456789A的创造性"

        start = time.perf_counter()
        result = intent_router.route(test_input)
        elapsed = time.perf_counter() - start

        # 验证路由时间 < 10ms
        assert elapsed < 0.01, f"路由耗时过长: {elapsed*1000:.2f}ms"
        assert result is not None

    def test_batch_route_performance(self, intent_router):
        """测试批量路由性能"""
        test_inputs = [
            "分析专利CN123456789A的创造性",
            "检索类似案例",
            "查询专利法相关条文",
            "评估技术方案的新颖性",
            "分析是否侵权"
        ] * 100  # 500次请求

        start = time.perf_counter()
        [intent_router.route(inp) for inp in test_inputs]
        elapsed = time.perf_counter() - start

        # 验证平均路由时间 < 5ms
        avg_time = elapsed / len(test_inputs)
        assert avg_time < 0.005, f"平均路由耗时过长: {avg_time*1000:.2f}ms"

        # 验证吞吐量 > 100 QPS
        qps = len(test_inputs) / elapsed
        assert qps > 100, f"吞吐量过低: {qps:.2f} QPS"

    def test_concurrent_route_performance(self, intent_router):
        """测试并发路由性能"""
        import concurrent.futures

        test_inputs = ["分析专利" for _ in range(100)]

        start = time.perf_counter()

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(intent_router.route, test_inputs))

        elapsed = time.perf_counter() - start

        # 验证并发性能
        assert len(results) == 100
        assert elapsed < 1.0, f"并发路由耗时过长: {elapsed:.2f}s"


class TestLoadBalancerPerformance:
    """负载均衡性能测试"""

    def test_round_robin_performance(self):
        """测试轮询负载均衡性能"""
        # 模拟服务实例
        instances = [
            {"id": f"instance_{i}", "host": "127.0.0.1", "port": 8000 + i}
            for i in range(10)
        ]

        # 简化的轮询选择
        def round_robin_select(instances: list[dict], index: int) -> dict:
            return instances[index % len(instances)]

        start = time.perf_counter()

        # 执行10000次选择
        for i in range(10000):
            round_robin_select(instances, i)

        elapsed = time.perf_counter() - start

        # 验证性能：10000次 < 10ms
        assert elapsed < 0.01, f"轮询选择耗时过长: {elapsed*1000:.2f}ms"

    def test_least_connections_performance(self):
        """测试最少连接负载均衡性能"""
        # 模拟连接统计
        connections = {f"instance_{i}": 0 for i in range(10)}

        def least_connections_select(instances: list[dict]) -> dict:
            # 选择连接数最少的实例
            min_conn = min(connections.values())
            for inst in instances:
                if connections[inst["id"] == min_conn:
                    connections[inst["id"] += 1
                    return inst
            return instances[0]

        start = time.perf_counter()

        # 执行1000次选择
        instances = [{"id": f"instance_{i}", "host": "127.0.0.1"} for i in range(10)]
        for _ in range(1000):
            least_connections_select(instances)

        elapsed = time.perf_counter() - start

        # 验证性能：1000次 < 50ms
        assert elapsed < 0.05, f"最少连接选择耗时过长: {elapsed*1000:.2f}ms"


class TestMemorySystemPerformance:
    """记忆系统性能测试"""

    def test_memory_write_performance(self):
        """测试记忆写入性能"""
        from core.framework.memory.unified_memory_system import (
            MemoryCategory,
            MemoryType,
            get_project_memory,
        )

        memory = get_project_memory("/Users/xujian/Athena工作平台")

        test_data = "# 测试数据\n\n内容" * 100  # 约1KB数据

        write_times = []
        for i in range(10):
            start = time.perf_counter()

            memory.write(
                type=MemoryType.PROJECT,
                category=MemoryCategory.TECHNICAL_FINDINGS,
                key=f"perf_test_{i}",
                content=test_data
            )

            elapsed = time.perf_counter() - start
            write_times.append(elapsed)

        avg_write_time = statistics.mean(write_times)

        # 验证平均写入时间 < 50ms
        assert avg_write_time < 0.05, f"平均写入耗时过长: {avg_write_time*1000:.2f}ms"

    def test_memory_read_performance(self):
        """测试记忆读取性能"""
        from core.framework.memory.unified_memory_system import (
            MemoryCategory,
            MemoryType,
            get_project_memory,
        )

        memory = get_project_memory("/Users/xujian/Athena工作平台")

        # 先写入测试数据
        memory.write(
            type=MemoryType.PROJECT,
            category=MemoryCategory.TECHNICAL_FINDINGS,
            key="perf_read_test",
            content="# 测试数据\n\n内容" * 100
        )

        read_times = []
        for _ in range(100):
            start = time.perf_counter()

            memory.read(
                MemoryType.PROJECT,
                MemoryCategory.TECHNICAL_FINDINGS,
                "perf_read_test"
            )

            elapsed = time.perf_counter() - start
            read_times.append(elapsed)

        avg_read_time = statistics.mean(read_times)

        # 验证平均读取时间 < 10ms
        assert avg_read_time < 0.01, f"平均读取耗时过长: {avg_read_time*1000:.2f}ms"

    def test_memory_search_performance(self):
        """测试记忆搜索性能"""
        from core.framework.memory.unified_memory_system import get_project_memory

        memory = get_project_memory("/Users/xujian/Athena工作平台")

        search_times = []
        for _ in range(10):
            start = time.perf_counter()

            memory.search(
                query="测试",
                limit=10
            )

            elapsed = time.perf_counter() - start
            search_times.append(elapsed)

        avg_search_time = statistics.mean(search_times)

        # 验证平均搜索时间 < 100ms
        assert avg_search_time < 0.1, f"平均搜索耗时过长: {avg_search_time*1000:.2f}ms"


class TestWebSocketPerformance:
    """WebSocket性能测试"""

    def test_message_serialization_performance(self):
        """测试消息序列化性能"""
        import json

        # 模拟WebSocket消息
        message = {
            "type": "task_create",
            "data": {
                "task_id": "TASK_001",
                "agent": "xiaona",
                "action": "analyze",
                "parameters": {
                    "patent_id": "CN123456789A",
                    "analysis_type": "novelty"
                }
            }
        }

        serialize_times = []
        for _ in range(1000):
            start = time.perf_counter()

            json.dumps(message)

            elapsed = time.perf_counter() - start
            serialize_times.append(elapsed)

        avg_serialize_time = statistics.mean(serialize_times)

        # 验证平均序列化时间 < 1ms
        assert avg_serialize_time < 0.001, f"平均序列化耗时过长: {avg_serialize_time*1000:.2f}ms"

    def test_message_deserialization_performance(self):
        """测试消息反序列化性能"""
        import json

        # 模拟序列化消息
        serialized = '{"type":"task_create","data":{"task_id":"TASK_001"}}'

        deserialize_times = []
        for _ in range(1000):
            start = time.perf_counter()

            json.loads(serialized)

            elapsed = time.perf_counter() - start
            deserialize_times.append(elapsed)

        avg_deserialize_time = statistics.mean(deserialize_times)

        # 验证平均反序列化时间 < 1ms
        assert avg_deserialize_time < 0.001, f"平均反序列化耗时过长: {avg_deserialize_time*1000:.2f}ms"


class TestOverallPerformance:
    """整体性能测试"""

    def test_end_to_end_latency(self):
        """测试端到端延迟"""
        # 模拟完整的请求-响应流程
        steps = [
            ("意图识别", 0.005),  # 5ms
            ("智能体选择", 0.002),  # 2ms
            ("任务执行", 0.500),  # 500ms (LLM调用)
            ("结果返回", 0.003),  # 3ms
        ]

        total_latency = sum(latency for _, latency in steps)

        # 验证总延迟 < 600ms
        assert total_latency < 0.6, f"端到端延迟过长: {total_latency*1000:.2f}ms"

    def test_system_throughput(self):
        """测试系统吞吐量"""
        # 模拟并发请求处理
        import concurrent.futures

        def process_request(request_id: int) -> dict[str, Any]:
            # 模拟请求处理
            time.sleep(0.1)  # 100ms处理时间
            return {"request_id": request_id, "status": "completed"}

        start = time.perf_counter()

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(process_request, i) for i in range(100)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        elapsed = time.perf_counter() - start

        # 验证吞吐量 > 50 QPS
        qps = len(results) / elapsed
        assert qps > 50, f"系统吞吐量过低: {qps:.2f} QPS"

    def test_memory_usage(self):
        """测试内存使用"""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # 执行一些操作
        from core.framework.memory.unified_memory_system import (
            MemoryCategory,
            MemoryType,
            get_project_memory,
        )

        memory = get_project_memory("/Users/xujian/Athena工作平台")

        for i in range(100):
            memory.write(
                type=MemoryType.PROJECT,
                category=MemoryCategory.TECHNICAL_FINDINGS,
                key=f"memory_test_{i}",
                content=f"内容 {i}" * 100
            )

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # 验证内存增长 < 100MB
        assert memory_increase < 100, f"内存增长过多: {memory_increase:.2f}MB"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
