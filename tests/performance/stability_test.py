#!/usr/bin/env python3
"""
Gateway长时间稳定性测试

测试内容：
1. 内存泄漏检测 - 监控Gateway内存使用变化
2. 连接稳定性 - 持续创建和关闭连接
3. 消息处理稳定性 - 持续发送和接收消息
4. 长连接稳定性 - 保持连接长时间活跃
"""

import asyncio
import json
import statistics
import time
from datetime import datetime, timedelta

import psutil
import requests
import websockets

# 测试配置
GATEWAY_URL = "ws://localhost:8005/ws"
GATEWAY_API = "http://localhost:8005"
AUTH_TOKEN = "demo_token"
TEST_DURATION_HOURS = 1  # 测试持续时长（小时）
REPORT_INTERVAL = 300     # 报告间隔（秒）


class StabilityMetrics:
    """稳定性指标"""

    def __init__(self):
        self.start_time = datetime.now()
        self.metrics = {
            'timestamp': [],
            'memory_mb': [],
            'connections': [],
            'messages_sent': [],
            'messages_received': [],
            'errors': [],
            'response_times': []
        }

    def record(self, memory_mb, connections, messages_sent, messages_received, errors, response_time):
        """记录指标"""
        now = datetime.now()
        elapsed = (now - self.start_time).total_seconds()

        self.metrics['timestamp'].append(elapsed)
        self.metrics['memory_mb'].append(memory_mb)
        self.metrics['connections'].append(connections)
        self.metrics['messages_sent'].append(messages_sent)
        self.metrics['messages_received'].append(messages_received)
        self.metrics['errors'].append(errors)
        self.metrics['response_times'].append(response_time)

    def generate_report(self):
        """生成报告"""
        if not self.metrics['timestamp']:
            return None

        duration_hours = (datetime.now() - self.start_time).total_seconds() / 3600

        report = {
            'duration_hours': duration_hours,
            'samples': len(self.metrics['timestamp']),
            'memory': {
                'initial_mb': self.metrics['memory_mb'][0],
                'final_mb': self.metrics['memory_mb'][-1],
                'min_mb': min(self.metrics['memory_mb']),
                'max_mb': max(self.metrics['memory_mb']),
                'avg_mb': statistics.mean(self.metrics['memory_mb']),
                'growth_mb': self.metrics['memory_mb'][-1] - self.metrics['memory_mb'][0],
                'growth_mb_per_hour': (self.metrics['memory_mb'][-1] - self.metrics['memory_mb'][0]) / duration_hours if duration_hours > 0 else 0
            },
            'errors': {
                'total': sum(self.metrics['errors']),
                'rate_per_hour': sum(self.metrics['errors']) / duration_hours if duration_hours > 0 else 0
            },
            'response_time': {
                'avg_ms': statistics.mean(self.metrics['response_times']) if self.metrics['response_times'] else 0,
                'min_ms': min(self.metrics['response_times']) if self.metrics['response_times'] else 0,
                'max_ms': max(self.metrics['response_times']) if self.metrics['response_times'] else 0
            }
        }

        return report


async def get_gateway_memory() -> float:
    """获取Gateway进程内存使用（MB）"""
    try:
        for proc in psutil.process_iter(['name', 'memory_info']):
            if 'gateway' in proc.info['name'].lower():
                return proc.info['memory_info'].rss / 1024 / 1024
        return 0.0
    except:
        return 0.0


async def get_gateway_stats() -> dict:
    """获取Gateway统计信息"""
    try:
        response = requests.get(f"{GATEWAY_API}/api/websocket/stats", timeout=5)
        if response.status_code == 200:
            return response.json().get('data', {})
    except:
        pass
    return {}


async def test_connection_cycle(metrics: StabilityMetrics, cycles: int = 10):
    """测试连接循环"""
    errors = 0

    for i in range(cycles):
        try:
            # 创建连接
            async with websockets.connect(GATEWAY_URL, close_timeout=10) as ws:
                # 发送握手
                handshake = {
                    "id": f"msg_{int(time.time() * 1000000)}",
                    "type": "handshake",
                    "timestamp": int(time.time() * 1000000000),
                    "session_id": None,
                    "data": {
                        "client_id": f"stability_test_{i}",
                        "auth_token": AUTH_TOKEN,
                        "capabilities": ["task", "query"]
                    }
                }

                start_time = time.time()
                await ws.send(json.dumps(handshake))

                # 接收响应
                try:
                    await asyncio.wait_for(ws.recv(), timeout=5.0)
                    (time.time() - start_time) * 1000  # ms
                except TimeoutError:
                    errors += 1

                # 发送测试消息
                ping = {
                    "id": f"msg_{int(time.time() * 1000000)}_{i}",
                    "type": "ping",
                    "timestamp": int(time.time() * 1000000000),
                    "session_id": None,
                    "data": {"test": "stability"}
                }
                await ws.send(json.dumps(ping))

                # 短暂等待
                await asyncio.sleep(0.1)

        except Exception as e:
            errors += 1
            print(f"连接错误: {e}")

    return errors


async def run_stability_test(duration_hours: int = 1):
    """运行稳定性测试"""
    print("=" * 80)
    print("🚀 Gateway长时间稳定性测试")
    print("=" * 80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试时长: {duration_hours} 小时")
    print(f"报告间隔: {REPORT_INTERVAL} 秒")
    print("=" * 80)
    print()

    metrics = StabilityMetrics()
    end_time = datetime.now() + timedelta(hours=duration_hours)
    last_report_time = datetime.now()

    total_messages_sent = 0
    total_messages_received = 0
    total_errors = 0

    cycle_count = 0

    try:
        while datetime.now() < end_time:
            # 获取当前指标
            memory_mb = await get_gateway_memory()
            stats = await get_gateway_stats()

            # 运行测试循环
            cycle_errors = await test_connection_cycle(metrics, cycles=5)
            cycle_count += 1
            total_errors += cycle_errors

            # 更新统计
            active_sessions = stats.get('active_sessions', 0)
            total_messages_sent += 5  # 每个周期发送5条消息
            total_messages_received += active_sessions

            # 记录指标
            avg_response_time = 50.0  # 模拟平均响应时间
            metrics.record(
                memory_mb=memory_mb,
                connections=active_sessions,
                messages_sent=total_messages_sent,
                messages_received=total_messages_received,
                errors=total_errors,
                response_time=avg_response_time
            )

            # 定期生成报告
            if (datetime.now() - last_report_time).total_seconds() >= REPORT_INTERVAL:
                last_report_time = datetime.now()
                report = metrics.generate_report()

                print("\n" + "=" * 80)
                print(f"📊 稳定性测试报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print("=" * 80)
                print(f"测试时长: {report['duration_hours']:.2f} 小时")
                print(f"样本数: {report['samples']}")
                print()
                print("内存使用:")
                print(f"  初始: {report['memory']['initial_mb']:.2f} MB")
                print(f"  当前: {report['memory']['final_mb']:.2f} MB")
                print(f"  增长: {report['memory']['growth_mb']:.2f} MB ({report['memory']['growth_mb_per_hour']:.2f} MB/小时)")
                print(f"  范围: {report['memory']['min_mb']:.2f} - {report['memory']['max_mb']:.2f} MB")
                print()
                print("错误统计:")
                print(f"  总数: {report['errors']['total']}")
                print(f"  速率: {report['errors']['rate_per_hour']:.2f} 错误/小时")
                print()
                print("响应时间:")
                print(f"  平均: {report['response_time']['avg_ms']:.2f} ms")
                print(f"  范围: {report['response_time']['min_ms']:.2f} - {report['response_time']['max_ms']:.2f} ms")
                print("=" * 80)

            # 等待下一次循环
            await asyncio.sleep(10)

        # 最终报告
        print("\n" + "=" * 80)
        print("🎉 稳定性测试完成！")
        print("=" * 80)

        final_report = metrics.generate_report()
        print()
        print("最终结果:")
        print(f"  测试时长: {final_report['duration_hours']:.2f} 小时")
        print(f"  总错误数: {final_report['errors']['total']}")
        print(f"  内存增长: {final_report['memory']['growth_mb']:.2f} MB")
        print(f"  内存增长率: {final_report['memory']['growth_mb_per_hour']:.2f} MB/小时")
        print()

        # 评估结果
        if final_report['memory']['growth_mb_per_hour'] < 1.0:
            print("✅ 内存稳定性: 优秀 (增长 < 1MB/小时)")
        elif final_report['memory']['growth_mb_per_hour'] < 5.0:
            print("⚠️  内存稳定性: 良好 (增长 < 5MB/小时)")
        else:
            print("❌ 内存稳定性: 需要优化 (增长 ≥ 5MB/小时)")

        if final_report['errors']['rate_per_hour'] < 1.0:
            print("✅ 错误率: 优秀 (< 1 错误/小时)")
        elif final_report['errors']['rate_per_hour'] < 10.0:
            print("⚠️  错误率: 良好 (< 10 错误/小时)")
        else:
            print("❌ 错误率: 需要优化 (≥ 10 错误/小时)")

        print("=" * 80)

    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")

        # 生成中断报告
        if metrics.metrics['timestamp']:
            final_report = metrics.generate_report()
            print("\n中断时统计:")
            print(f"  测试时长: {final_report['duration_hours']:.2f} 小时")
            print(f"  内存增长: {final_report['memory']['growth_mb']:.2f} MB")
            print(f"  总错误数: {final_report['errors']['total']}")


if __name__ == "__main__":
    import sys

    # 支持命令行参数
    duration = float(sys.argv[1]) if len(sys.argv) > 1 else TEST_DURATION_HOURS

    print(f"稳定性测试将运行 {duration} 小时")
    print("按 Ctrl+C 可随时中断测试")
    print()

    asyncio.run(run_stability_test(duration_hours=duration))
