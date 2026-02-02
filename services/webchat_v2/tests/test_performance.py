#!/usr/bin/env python3
"""
WebChat V2 Gateway 性能测试
测试并发连接、吞吐量和响应时间

作者: Athena平台团队
创建时间: 2025-01-31
版本: 2.0.0
"""

import asyncio
import json
import time
import websockets
from datetime import datetime, timezone
from typing import List, Dict, Any
import statistics


# 测试配置
WS_URL = "ws://localhost:8000/gateway/ws"
TEST_USER_PREFIX = "perf_test_user"


class PerformanceTestClient:
    """性能测试客户端"""

    def __init__(self, client_id: int):
        self.client_id = client_id
        self.user_id = f"{TEST_USER_PREFIX}_{client_id}"
        self.session_id = f"perf_session_{client_id}"
        self.ws_url = WS_URL
        self.websocket = None
        self.connected = False
        self.messages_sent = 0
        self.messages_received = 0
        self.errors = 0
        self.latencies = []

    async def connect(self) -> bool:
        """连接到服务器"""
        try:
            url = f"{self.ws_url}?user_id={self.user_id}&session_id={self.session_id}"
            self.websocket = await websockets.connect(url, close_timeout=10)
            self.connected = True

            # 等待connected事件
            await asyncio.sleep(0.1)
            return True
        except Exception as e:
            print(f"客户端 {self.client_id} 连接失败: {e}")
            return False

    async def disconnect(self):
        """断开连接"""
        if self.websocket:
            await self.websocket.close()
            self.connected = False

    async def send_request(self, method: str, params: dict) -> float:
        """
        发送请求并返回延迟（毫秒）

        Returns:
            延迟时间（毫秒），失败返回-1
        """
        if not self.connected:
            return -1

        request_id = f"req_{self.messages_sent}"
        request = {
            "type": "request",
            "id": request_id,
            "method": method,
            "params": params,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        try:
            start_time = time.time()
            await self.websocket.send(json.dumps(request))
            self.messages_sent += 1

            # 等待响应
            timeout = 10
            while True:
                try:
                    response_str = await asyncio.wait_for(self.websocket.recv(), timeout=timeout)
                    response = json.loads(response_str)

                    if response.get("type") == "response" and response.get("id") == request_id:
                        latency = (time.time() - start_time) * 1000  # 转换为毫秒
                        self.messages_received += 1
                        self.latencies.append(latency)
                        return latency
                    elif response.get("type") == "event":
                        continue  # 跳过事件消息

                except asyncio.TimeoutError:
                    self.errors += 1
                    return -1

        except Exception as e:
            self.errors += 1
            return -1


class PerformanceTestRunner:
    """性能测试运行器"""

    def __init__(self):
        self.results = {}

    async def test_concurrent_connections(
        self,
        num_clients: int,
        duration_seconds: int = 10
    ) -> Dict[str, Any]:
        """
        测试并发连接能力

        Args:
            num_clients: 并发连接数
            duration_seconds: 测试持续时间

        Returns:
            测试结果
        """
        print(f"\n{'='*60}")
        print(f"测试: 并发连接能力")
        print(f"参数: {num_clients}个客户端, {duration_seconds}秒")
        print(f"{'='*60}\n")

        clients: List[PerformanceTestClient] = []
        successful_connections = 0
        failed_connections = 0

        # 创建并连接所有客户端
        print("正在连接客户端...")
        start_time = time.time()

        for i in range(num_clients):
            client = PerformanceTestClient(i)
            clients.append(client)

            if await client.connect():
                successful_connections += 1
            else:
                failed_connections += 1

            # 每100个客户端输出一次进度
            if (i + 1) % 100 == 0:
                print(f"  已连接: {i + 1}/{num_clients}")

        connect_time = time.time() - start_time

        print(f"\n连接完成:")
        print(f"  成功: {successful_connections}/{num_clients}")
        print(f"  失败: {failed_connections}/{num_clients}")
        print(f"  耗时: {connect_time:.2f}秒")
        print(f"  平均连接速率: {num_clients/connect_time:.2f}个/秒")

        # 保持连接一段时间
        print(f"\n保持连接 {duration_seconds} 秒...")
        await asyncio.sleep(duration_seconds)

        # 断开所有连接
        print("\n正在断开连接...")
        for client in clients:
            await client.disconnect()

        return {
            "test": "concurrent_connections",
            "num_clients": num_clients,
            "successful_connections": successful_connections,
            "failed_connections": failed_connections,
            "connect_time": connect_time,
            "connect_rate": num_clients / connect_time if connect_time > 0 else 0,
            "duration": duration_seconds,
        }

    async def test_request_throughput(
        self,
        num_clients: int,
        requests_per_client: int
    ) -> Dict[str, Any]:
        """
        测试请求吞吐量

        Args:
            num_clients: 客户端数量
            requests_per_client: 每个客户端发送的请求数

        Returns:
            测试结果
        """
        print(f"\n{'='*60}")
        print(f"测试: 请求吞吐量")
        print(f"参数: {num_clients}个客户端, 每个客户端{requests_per_client}个请求")
        print(f"{'='*60}\n")

        clients: List[PerformanceTestClient] = []

        # 连接所有客户端
        print("正在连接客户端...")
        for i in range(num_clients):
            client = PerformanceTestClient(i)
            if await client.connect():
                clients.append(client)

        print(f"已连接: {len(clients)}/{num_clients}个客户端\n")

        # 并发发送请求
        print("正在发送请求...")
        start_time = time.time()

        tasks = []
        for client in clients:
            for _ in range(requests_per_client):
                tasks.append(client.send_request("platform_modules", {}))

        # 等待所有请求完成
        results = await asyncio.gather(*tasks, return_exceptions=True)

        total_time = time.time() - start_time

        # 统计结果
        successful_requests = sum(1 for r in results if r > 0)
        failed_requests = len(results) - successful_requests

        all_latencies = []
        for client in clients:
            all_latencies.extend(client.latencies)

        # 计算统计数据
        if all_latencies:
            avg_latency = statistics.mean(all_latencies)
            median_latency = statistics.median(all_latencies)
            p95_latency = statistics.quantiles(all_latencies, n=20)[18] if len(all_latencies) >= 20 else max(all_latencies)
            p99_latency = statistics.quantiles(all_latencies, n=100)[98] if len(all_latencies) >= 100 else max(all_latencies)
            min_latency = min(all_latencies)
            max_latency = max(all_latencies)
        else:
            avg_latency = median_latency = p95_latency = p99_latency = min_latency = max_latency = 0

        total_requests = num_clients * requests_per_client
        throughput = total_requests / total_time if total_time > 0 else 0

        print(f"\n测试结果:")
        print(f"  总请求数: {total_requests}")
        print(f"  成功: {successful_requests}")
        print(f"  失败: {failed_requests}")
        print(f"  总耗时: {total_time:.2f}秒")
        print(f"  吞吐量: {throughput:.2f}请求/秒")
        print(f"\n延迟统计 (毫秒):")
        print(f"  平均: {avg_latency:.2f}")
        print(f"  中位数: {median_latency:.2f}")
        print(f"  P95: {p95_latency:.2f}")
        print(f"  P99: {p99_latency:.2f}")
        print(f"  最小: {min_latency:.2f}")
        print(f"  最大: {max_latency:.2f}")

        # 断开所有连接
        for client in clients:
            await client.disconnect()

        return {
            "test": "request_throughput",
            "num_clients": num_clients,
            "requests_per_client": requests_per_client,
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "total_time": total_time,
            "throughput": throughput,
            "avg_latency": avg_latency,
            "median_latency": median_latency,
            "p95_latency": p95_latency,
            "p99_latency": p99_latency,
            "min_latency": min_latency,
            "max_latency": max_latency,
        }

    async def test_sustained_load(
        self,
        num_clients: int,
        duration_seconds: int,
        request_interval: float = 1.0
    ) -> Dict[str, Any]:
        """
        测试持续负载能力

        Args:
            num_clients: 客户端数量
            duration_seconds: 测试持续时间
            request_interval: 请求间隔（秒）

        Returns:
            测试结果
        """
        print(f"\n{'='*60}")
        print(f"测试: 持续负载能力")
        print(f"参数: {num_clients}个客户端, {duration_seconds}秒, 每{request_interval}秒发送一次请求")
        print(f"{'='*60}\n")

        clients: List[PerformanceTestClient] = []

        # 连接所有客户端
        print("正在连接客户端...")
        for i in range(num_clients):
            client = PerformanceTestClient(i)
            if await client.connect():
                clients.append(client)

        print(f"已连接: {len(clients)}/{num_clients}个客户端\n")

        # 持续发送请求
        print("正在发送持续负载...")
        start_time = time.time()
        end_time = start_time + duration_seconds

        # 每个客户端持续发送请求
        async def send_continuous_requests(client: PerformanceTestClient):
            while time.time() < end_time:
                await client.send_request("platform_modules", {})
                await asyncio.sleep(request_interval)

        # 启动所有客户端的持续请求
        tasks = [send_continuous_requests(client) for client in clients]
        await asyncio.gather(*tasks, return_exceptions=True)

        actual_duration = time.time() - start_time

        # 统计结果
        total_requests = sum(c.messages_sent for c in clients)
        total_received = sum(c.messages_received for c in clients)
        total_errors = sum(c.errors for c in clients)

        all_latencies = []
        for client in clients:
            all_latencies.extend(client.latencies)

        if all_latencies:
            avg_latency = statistics.mean(all_latencies)
            p95_latency = statistics.quantiles(all_latencies, n=20)[18] if len(all_latencies) >= 20 else max(all_latencies)
        else:
            avg_latency = p95_latency = 0

        throughput = total_requests / actual_duration if actual_duration > 0 else 0

        print(f"\n测试结果:")
        print(f"  实际持续时间: {actual_duration:.2f}秒")
        print(f"  总请求数: {total_requests}")
        print(f"  成功响应: {total_received}")
        print(f"  错误数: {total_errors}")
        print(f"  吞吐量: {throughput:.2f}请求/秒")
        print(f"  平均延迟: {avg_latency:.2f}毫秒")
        print(f"  P95延迟: {p95_latency:.2f}毫秒")

        # 断开所有连接
        for client in clients:
            await client.disconnect()

        return {
            "test": "sustained_load",
            "num_clients": num_clients,
            "duration": duration_seconds,
            "actual_duration": actual_duration,
            "total_requests": total_requests,
            "successful_responses": total_received,
            "errors": total_errors,
            "throughput": throughput,
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
        }

    def print_summary(self, results: List[Dict[str, Any]]):
        """打印测试结果汇总"""
        print(f"\n{'='*70}")
        print(f"{' '*20 + '性能测试结果汇总'}")
        print(f"{'='*70}\n")

        for result in results:
            test_name = result["test"].replace("_", " ").title()
            print(f"📊 {test_name}")
            print(f"{'-'*70}")

            if result["test"] == "concurrent_connections":
                print(f"  并发连接数: {result['num_clients']}")
                print(f"  成功率: {result['successful_connections']/result['num_clients']*100:.1f}%")
                print(f"  连接速率: {result['connect_rate']:.2f}个/秒")

            elif result["test"] == "request_throughput":
                print(f"  总请求数: {result['total_requests']}")
                print(f"  吞吐量: {result['throughput']:.2f}请求/秒")
                print(f"  成功率: {result['successful_requests']/result['total_requests']*100:.1f}%")
                print(f"  平均延迟: {result['avg_latency']:.2f}ms")
                print(f"  P95延迟: {result['p95_latency']:.2f}ms")

            elif result["test"] == "sustained_load":
                print(f"  持续时间: {result['actual_duration']:.2f}秒")
                print(f"  吞吐量: {result['throughput']:.2f}请求/秒")
                print(f"  错误率: {result['errors']/result['total_requests']*100:.1f}%")
                print(f"  平均延迟: {result['avg_latency']:.2f}ms")

            print()

        print(f"{'='*70}")


async def run_performance_tests():
    """运行所有性能测试"""
    print("\n" + "="*70)
    print(" "*15 + "WebChat V2 Gateway 性能测试套件")
    print("="*70)

    runner = PerformanceTestRunner()
    results = []

    # 测试1: 小规模并发连接
    try:
        result = await runner.test_concurrent_connections(
            num_clients=50,
            duration_seconds=5
        )
        results.append(result)
    except Exception as e:
        print(f"测试1失败: {e}")

    await asyncio.sleep(2)

    # 测试2: 请求吞吐量
    try:
        result = await runner.test_request_throughput(
            num_clients=10,
            requests_per_client=10
        )
        results.append(result)
    except Exception as e:
        print(f"测试2失败: {e}")

    await asyncio.sleep(2)

    # 测试3: 持续负载
    try:
        result = await runner.test_sustained_load(
            num_clients=10,
            duration_seconds=10,
            request_interval=0.5
        )
        results.append(result)
    except Exception as e:
        print(f"测试3失败: {e}")

    # 打印汇总
    runner.print_summary(results)

    return results


if __name__ == "__main__":
    results = asyncio.run(run_performance_tests())
