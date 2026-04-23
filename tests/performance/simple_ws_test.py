#!/usr/bin/env python3
"""简单的WebSocket连接测试"""

import asyncio
import json

import websockets


async def test_websocket():
    """测试WebSocket连接"""
    uri = "ws://localhost:8005/ws"
    print(f"连接到 {uri}...")

    try:
        async with websockets.connect(uri) as ws:
            print("✅ WebSocket连接成功！")

            # 发送握手消息
            handshake = {
                "id": "msg_001",
                "type": "handshake",
                "timestamp": 1234567890000000000,
                "session_id": None,
                "data": {
                    "client_id": "test_client",
                    "auth_token": "demo_token",
                    "capabilities": ["task", "query"]
                }
            }

            await ws.send(json.dumps(handshake))
            print("✅ 握手消息已发送")

            # 等待响应
            response = await ws.recv()
            print(f"✅ 收到响应: {response}")

            # 解析响应
            data = json.loads(response)
            print(f"✅ 响应类型: {data.get('type')}")

            # 发送测试消息
            test_msg = {
                "id": "msg_002",
                "type": "ping",
                "timestamp": 1234567890000000000,
                "session_id": None,
                "data": {"test": "hello"}
            }

            await ws.send(json.dumps(test_msg))
            print("✅ 测试消息已发送")

            # 等待响应
            response2 = await asyncio.wait_for(ws.recv(), timeout=5.0)
            print(f"✅ 收到响应: {response2}")

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_websocket())
