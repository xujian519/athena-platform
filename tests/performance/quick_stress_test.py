#!/usr/bin/env python3
"""
Gateway快速压力测试（5分钟版本）

快速验证Gateway的基本稳定性和性能
"""

import asyncio
import json
import time
from datetime import datetime

import websockets

GATEWAY_URL = "ws://localhost:8005/ws"
AUTH_TOKEN = "demo_token"
TEST_DURATION = 300  # 5分钟


async def quick_stress_test():
    """快速压力测试"""
    print("=" * 80)
    print("🚀 Gateway快速压力测试（5分钟）")
    print("=" * 80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    start_time = time.time()
    end_time = start_time + TEST_DURATION

    total_connections = 0
    total_messages = 0
    total_errors = 0

    cycle = 0

    try:
        while time.time() < end_time:
            cycle += 1
            cycle_start = time.time()

            # 每个周期创建10个并发连接
            tasks = []
            for i in range(10):
                tasks.append(test_connection(i))

            # 等待所有连接完成
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 统计结果
            for result in results:
                if isinstance(result, Exception):
                    total_errors += 1
                else:
                    total_connections += result.get('connections', 0)
                    total_messages += result.get('messages', 0)

            # 计算耗时
            cycle_time = time.time() - cycle_start
            time.time() - start_time
            remaining = end_time - time.time()

            # 每30秒报告一次
            if cycle % 6 == 0:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                      f"周期{cycle} | "
                      f"连接: {total_connections} | "
                      f"消息: {total_messages} | "
                      f"错误: {total_errors} | "
                      f"耗时: {cycle_time:.2f}s | "
                      f"剩余: {int(remaining)}s")

            # 短暂休息
            await asyncio.sleep(5)

        # 最终报告
        elapsed_total = time.time() - start_time

        print("\n" + "=" * 80)
        print("🎉 快速压力测试完成！")
        print("=" * 80)
        print(f"测试时长: {elapsed_total:.0f} 秒 ({elapsed_total/60:.1f} 分钟)")
        print(f"总连接数: {total_connections}")
        print(f"总消息数: {total_messages}")
        print(f"总错误数: {total_errors}")
        print(f"连接速率: {total_connections/elapsed_total:.2f} 连接/秒")
        print(f"消息速率: {total_messages/elapsed_total:.2f} 消息/秒")
        print(f"错误率: {total_errors/(total_connections+total_messages)*100 if total_connections+total_messages > 0 else 0:.4f}%")
        print("=" * 80)

        # 评估
        if total_errors == 0:
            print("✅ 测试结果: 优秀 - 无错误")
        elif total_errors < 10:
            print("⚠️  测试结果: 良好 - 少量错误")
        else:
            print("❌ 测试结果: 需要优化 - 错误较多")

    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        elapsed_total = time.time() - start_time
        print(f"已运行: {elapsed_total:.0f} 秒")
        print(f"连接: {total_connections}, 消息: {total_messages}, 错误: {total_errors}")


async def test_connection(client_id: int) -> dict:
    """测试单个连接"""
    connections = 0
    messages = 0

    try:
        async with websockets.connect(GATEWAY_URL, close_timeout=10) as ws:
            connections += 1

            # 发送握手
            handshake = {
                "id": f"msg_{int(time.time() * 1000000)}_{client_id}",
                "type": "handshake",
                "timestamp": int(time.time() * 1000000000),
                "session_id": None,
                "data": {
                    "client_id": f"stress_test_{client_id}",
                    "auth_token": AUTH_TOKEN,
                    "capabilities": ["task", "query"]
                }
            }

            await ws.send(json.dumps(handshake))
            messages += 1

            # 接收握手响应（可选）
            try:
                await asyncio.wait_for(ws.recv(), timeout=2.0)
            except:
                pass

            # 发送5条测试消息
            for i in range(5):
                ping = {
                    "id": f"msg_{int(time.time() * 1000000)}_{client_id}_{i}",
                    "type": "ping",
                    "timestamp": int(time.time() * 1000000000),
                    "session_id": None,
                    "data": {"test": f"message_{i}"}
                }
                await ws.send(json.dumps(ping))
                messages += 1
                await asyncio.sleep(0.1)

    except Exception as e:
        # 返回错误信息
        raise e

    return {
        'connections': connections,
        'messages': messages
    }


if __name__ == "__main__":
    print("快速压力测试（5分钟）")
    print("按 Ctrl+C 可随时中断")
    print()

    asyncio.run(quick_stress_test())
