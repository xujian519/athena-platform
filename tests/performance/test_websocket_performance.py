#!/usr/bin/env python3
"""
WebSocket性能测试脚本

测试Gateway的WebSocket性能：
1. 并发连接测试
2. 消息吞吐量测试
3. 延迟测试
4. 资源占用测试
"""

import asyncio
import json
import statistics
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import psutil
import websockets

# 测试配置
GATEWAY_URL = "ws://localhost:8005/ws"
AUTH_TOKEN = "demo_token"
MAX_CONNECTIONS = 1000  # 最大并发连接数
MESSAGES_PER_CLIENT = 100  # 每个客户端发送的消息数


@dataclass
class PerformanceMetrics:
    """性能指标"""
    name: str
    value: float
    unit: str
    timestamp: datetime


class PerformanceTestResult:
    """性能测试结果"""

    def __init__(self):
        self.metrics: list[PerformanceMetrics] = []
        self.start_time = datetime.now()
        self.end_time: datetime = None

    def add_metric(self, name: str, value: float, unit: str):
        """添加指标"""
        metric = PerformanceMetrics(
            name=name,
            value=value,
            unit=unit,
            timestamp=datetime.now()
        )
        self.metrics.append(metric)

    def finish(self):
        """结束测试"""
        self.end_time = datetime.now()

    def get_duration(self) -> float:
        """获取测试时长（秒）"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()

    def print_report(self):
        """打印测试报告"""
        print("\n" + "="*80)
        print(f"性能测试报告 - {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)

        # 按类别分组
        categories = {}
        for metric in self.metrics:
            category = metric.name.split('_')[0]
            if category not in categories:
                categories[category] = []
            categories[category].append(metric)

        # 打印指标
        for category, metrics in categories.items():
            print(f"\n【{category}】")
            for metric in metrics:
                print(f"  {metric.name}: {metric.value:.2f} {metric.unit}")

        print(f"\n测试时长: {self.get_duration():.2f} 秒")
        print("="*80)


class WebSocketClient:
    """WebSocket测试客户端"""

    def __init__(self, client_id: int):
        self.client_id = f"perf_test_{client_id}"
        self.ws = None
        self.connected = False
        self.messages_sent = 0
        self.messages_received = 0
        self.errors = 0

    async def connect(self, url: str) -> bool:
        """连接到Gateway"""
        try:
            self.ws = await websockets.connect(url)

            # 发送握手消息
            handshake = {
                "id": f"msg_{int(time.time() * 1000000)}",
                "type": "handshake",
                "timestamp": int(time.time() * 1000000000),
                "session_id": None,
                "data": {
                    "client_id": self.client_id,
                    "auth_token": AUTH_TOKEN,
                    "capabilities": ["task", "query"],
                    "user_agent": "PerformanceTestClient/1.0"
                }
            }

            await self.ws.send(json.dumps(handshake))

            # 等待握手响应
            response = await self.ws.recv()
            response_data = json.loads(response)

            if response_data.get("type") == "handshake":
                self.connected = True
                return True

            return False

        except Exception as e:
            print(f"客户端 {self.client_id} 连接失败: {e}")
            return False

    async def send_message(self, msg_type: str, data: dict[str, Any]) -> bool:
        """发送消息"""
        if not self.connected:
            return False

        try:
            message = {
                "id": f"msg_{int(time.time() * 1000000)}_{self.messages_sent}",
                "type": msg_type,
                "timestamp": int(time.time() * 1000000000),
                "session_id": None,
                "data": data
            }

            await self.ws.send(json.dumps(message))
            self.messages_sent += 1
            return True

        except Exception:
            self.errors += 1
            return False

    async def close(self):
        """关闭连接"""
        if self.ws:
            await self.ws.close()
        self.connected = False


async def test_concurrent_connections(result: PerformanceTestResult):
    """测试并发连接数"""
    print("\n🔗 测试1: 并发连接测试")
    print("-" * 60)

    num_clients = 100  # 测试100个并发连接
    clients = []

    # 创建并连接客户端
    start_time = time.time()

    for i in range(num_clients):
        client = WebSocketClient(i)
        success = await client.connect(GATEWAY_URL)

        if success:
            clients.append(client)
            print(f"✅ 客户端 {i+1}/{num_clients} 已连接")
        else:
            print(f"❌ 客户端 {i+1}/{num_clients} 连接失败")

        # 每连接10个客户端后暂停一下
        if (i + 1) % 10 == 0:
            await asyncio.sleep(0.5)

    connection_time = time.time() - start_time

    # 记录指标
    result.add_metric("connections_total", len(clients), "个")
    result.add_metric("connections_success_rate", len(clients) / num_clients * 100, "%")
    result.add_metric("connections_avg_time", connection_time / num_clients, "秒/连接")

    print(f"\n✅ 成功连接: {len(clients)}/{num_clients}")
    print(f"   连接成功率: {len(clients) / num_clients * 100:.1f}%")
    print(f"   平均连接时间: {connection_time / num_clients:.3f} 秒/连接")

    # 保持连接一段时间
    print("\n⏳ 保持连接10秒...")
    await asyncio.sleep(10)

    # 关闭所有连接
    print("\n🔌 关闭所有连接...")
    for client in clients:
        await client.close()

    print("✅ 并发连接测试完成")


async def test_message_throughput(result: PerformanceTestResult):
    """测试消息吞吐量"""
    print("\n📊 测试2: 消息吞吐量测试")
    print("-" * 60)

    num_clients = 10
    messages_per_client = 100
    num_clients * messages_per_client

    clients = []

    # 连接客户端
    print(f"连接 {num_clients} 个客户端...")
    for i in range(num_clients):
        client = WebSocketClient(i)
        if await client.connect(GATEWAY_URL):
            clients.append(client)
    print(f"✅ 已连接 {len(clients)} 个客户端")

    # 发送消息
    print(f"\n每个客户端发送 {messages_per_client} 条消息...")
    start_time = time.time()

    tasks = []
    for client in clients:
        for msg_num in range(messages_per_client):
            task = asyncio.create_task(client.send_message("ping", {
                "test_data": f"message_{msg_num}",
                "timestamp": time.time()
            }))
            tasks.append(task)

    # 等待所有消息发送完成
    await asyncio.gather(*tasks)

    end_time = time.time()
    duration = end_time - start_time

    # 计算指标
    total_sent = sum(client.messages_sent for client in clients)
    throughput = total_sent / duration

    result.add_metric("throughput_total_messages", total_sent, "条")
    result.add_metric("throughput_per_second", throughput, "条/秒")
    result.add_metric("throughput_per_client", total_sent / len(clients), "条/客户端")
    result.add_metric("throughput_duration", duration, "秒")

    print(f"\n✅ 总消息数: {total_sent} 条")
    print(f"   总耗时: {duration:.2f} 秒")
    print(f"   吞吐量: {throughput:.2f} 条/秒")
    print(f"   平均每客户端: {total_sent / len(clients):.1f} 条")

    # 关闭连接
    for client in clients:
        await client.close()

    print("✅ 消息吞吐量测试完成")


async def test_message_latency(result: PerformanceTestResult):
    """测试消息延迟"""
    print("\n⏱️ 测试3: 消息延迟测试")
    print("-" * 60)

    num_tests = 100
    latencies = []

    # 连接单个客户端
    print("连接测试客户端...")
    client = WebSocketClient(0)
    if not await client.connect(GATEWAY_URL):
        print("❌ 无法连接到Gateway")
        return

    print("✅ 已连接")

    # 测试延迟
    print(f"\n发送 {num_tests} 条测试消息...")

    for i in range(num_tests):
        start_time = time.time()

        await client.send_message("ping", {"test": i})

        # 等待响应（可选）
        # response = await client.ws.recv()

        end_time = time.time()
        latency = (end_time - start_time) * 1000  # 转换为毫秒
        latencies.append(latency)

        if (i + 1) % 20 == 0:
            print(f"进度: {i+1}/{num_tests}")

    # 计算统计数据
    avg_latency = statistics.mean(latencies)
    p50_latency = statistics.median(latencies)
    p95_latency = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
    p99_latency = statistics.quantiles(latencies, n=100)[98]  # 99th percentile
    min_latency = min(latencies)
    max_latency = max(latencies)

    result.add_metric("latency_avg", avg_latency, "ms")
    result.add_metric("latency_p50", p50_latency, "ms")
    result.add_metric("latency_p95", p95_latency, "ms")
    result.add_metric("latency_p99", p99_latency, "ms")
    result.add_metric("latency_min", min_latency, "ms")
    result.add_metric("latency_max", max_latency, "ms")

    print(f"\n✅ 延迟统计（{num_tests}条消息）:")
    print(f"   平均延迟: {avg_latency:.2f} ms")
    print(f"   中位数(P50): {p50_latency:.2f} ms")
    print(f"   P95延迟: {p95_latency:.2f} ms")
    print(f"   P99延迟: {p99_latency:.2f} ms")
    print(f"   最小延迟: {min_latency:.2f} ms")
    print(f"   最大延迟: {max_latency:.2f} ms")

    await client.close()
    print("✅ 消息延迟测试完成")


async def test_resource_usage(result: PerformanceTestResult):
    """测试资源占用"""
    print("\n💾 测试4: 资源占用测试")
    print("-" * 60)

    # 获取当前进程资源使用
    process = psutil.Process()

    # 记录初始资源使用
    initial_cpu = process.cpu_percent(interval=1)
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    print("初始资源使用:")
    print(f"  CPU: {initial_cpu}%")
    print(f"  内存: {initial_memory:.2f} MB")

    # 运行负载测试
    print("\n运行负载测试（50个客户端，每客户端50条消息）...")

    num_clients = 50
    messages_per_client = 50
    clients = []

    # 连接客户端
    for i in range(num_clients):
        client = WebSocketClient(i)
        if await client.connect(GATEWAY_URL):
            clients.append(client)

    # 发送消息并监控资源
    cpu_samples = []
    memory_samples = []

    start_time = time.time()

    for client in clients:
        for _ in range(messages_per_client):
            await client.send_message("ping", {"load_test": True})

            # 每发送100条消息记录一次资源使用
            if client.messages_sent % 100 == 0:
                cpu = process.cpu_percent()
                memory = process.memory_info().rss / 1024 / 1024
                cpu_samples.append(cpu)
                memory_samples.append(memory)

    duration = time.time() - start_time

    # 计算资源使用
    avg_cpu = statistics.mean(cpu_samples) if cpu_samples else 0
    max_cpu = max(cpu_samples) if cpu_samples else 0
    avg_memory = statistics.mean(memory_samples) if memory_samples else 0
    max_memory = max(memory_samples) if memory_samples else 0

    result.add_metric("resource_cpu_avg", avg_cpu, "%")
    result.add_metric("resource_cpu_max", max_cpu, "%")
    result.add_metric("resource_memory_avg", avg_memory, "MB")
    result.add_metric("resource_memory_max", max_memory, "MB")
    result.add_metric("resource_test_duration", duration, "秒")

    print("\n✅ 资源使用统计:")
    print(f"   平均CPU: {avg_cpu:.1f}%")
    print(f"   峰值CPU: {max_cpu:.1f}%")
    print(f"   平均内存: {avg_memory:.2f} MB")
    print(f"   峰值内存: {max_memory:.2f} MB")
    print(f"   测试时长: {duration:.2f} 秒")

    # 关闭连接
    for client in clients:
        await client.close()

    print("✅ 资源占用测试完成")


async def main():
    """主测试函数"""
    print("="*80)
    print("🚀 Athena Gateway WebSocket性能测试")
    print("="*80)
    print(f"Gateway URL: {GATEWAY_URL}")
    print(f"最大并发连接: {MAX_CONNECTIONS}")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    result = PerformanceTestResult()

    try:
        # 运行测试
        await test_concurrent_connections(result)
        await test_message_throughput(result)
        await test_message_latency(result)
        await test_resource_usage(result)

        # 完成测试
        result.finish()

        # 打印报告
        result.print_report()

        # 性能评估
        print("\n📊 性能评估:")
        print("-" * 60)

        # 根据指标给出评估
        avg_latency = next((m.value for m in result.metrics if m.name == "latency_avg"), 0)
        throughput = next((m.value for m in result.metrics if m.name == "throughput_per_second"), 0)

        # 延迟评估
        if avg_latency < 50:
            print(f"✅ 延迟: 优秀 ({avg_latency:.2f}ms < 50ms)")
        elif avg_latency < 100:
            print(f"⚠️  延迟: 良好 ({avg_latency:.2f}ms < 100ms)")
        else:
            print(f"❌ 延迟: 需要优化 ({avg_latency:.2f}ms > 100ms)")

        # 吞吐量评估
        if throughput > 10000:
            print(f"✅ 吞吐量: 优秀 ({throughput:.2f} 条/秒 > 10,000)")
        elif throughput > 1000:
            print(f"⚠️  吞吐量: 良好 ({throughput:.2f} 条/秒 > 1,000)")
        else:
            print(f"❌ 吞吐量: 需要优化 ({throughput:.2f} 条/秒 < 1,000)")

        print("\n✅ 所有性能测试完成！")

    except KeyboardInterrupt:
        print("\n\n⚠️  测试被中断")

    except Exception as e:
        print(f"\n\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
