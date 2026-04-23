#!/usr/bin/env python3
import asyncio
import json
import time

import websockets


async def test_handshake():
    uri = "ws://localhost:8005/ws"
    print(f"连接到 {uri}...", flush=True)

    try:
        async with websockets.connect(uri, close_timeout=10) as ws:
            print("✅ WebSocket连接成功！", flush=True)

            # 发送握手消息
            handshake = {
                "id": f"msg_{int(time.time() * 1000000)}",
                "type": "handshake",
                "timestamp": int(time.time() * 1000000000),
                "session_id": None,
                "data": {
                    "client_id": "test_client",
                    "auth_token": "demo_token",
                    "capabilities": ["task", "query"]
                }
            }

            print("发送握手消息...", flush=True)
            await ws.send(json.dumps(handshake))
            print("✅ 握手消息已发送", flush=True)

            # 等待响应（设置超时）
            print("等待响应...", flush=True)
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                print(f"✅ 收到响应: {response[:200]}", flush=True)

                data = json.loads(response)
                print(f"✅ 响应类型: {data.get('type')}", flush=True)

                # 发送ping测试
                ping = {
                    "id": f"msg_{int(time.time() * 1000000)}",
                    "type": "ping",
                    "timestamp": int(time.time() * 1000000000),
                    "session_id": None,
                    "data": {"test": "hello"}
                }

                print("发送ping消息...", flush=True)
                await ws.send(json.dumps(ping))
                print("✅ Ping已发送", flush=True)

                return True

            except TimeoutError:
                print("⚠️  等待响应超时", flush=True)
                return False

    except Exception as e:
        print(f"❌ 错误: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_handshake())
    print(f"\n测试结果: {'成功' if result else '失败'}", flush=True)
