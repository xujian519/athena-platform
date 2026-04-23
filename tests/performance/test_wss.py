#!/usr/bin/env python3
"""
WSS (WebSocket Secure) 连接测试
测试Gateway的TLS/SSL功能
"""

import asyncio
import json
import ssl

import websockets


async def test_wss_connection():
    """测试WSS连接"""
    # WSS URL（使用自签名证书，需要禁用SSL验证）
    wss_url = "wss://localhost:8005/ws"  # Gateway运行在8005端口

    print("=" * 80)
    print("🔒 Gateway WSS (WebSocket Secure) 连接测试")
    print("=" * 80)
    print(f"WSS URL: {wss_url}")
    print()

    # 注意：自签名证书需要禁用SSL验证
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    try:
        print("正在连接到Gateway (WSS)...")
        async with websockets.connect(wss_url, ssl=ssl_context, close_timeout=10) as ws:
            print("✅ WSS连接成功！")

            # 发送握手消息
            handshake = {
                "id": "msg_wss_test",
                "type": "handshake",
                "timestamp": 1234567890000000000,
                "session_id": None,
                "data": {
                    "client_id": "wss_test_client",
                    "auth_token": "demo_token",
                    "capabilities": ["task", "query"],
                    "user_agent": "WSS Test Client/1.0"
                }
            }

            await ws.send(json.dumps(handshake))
            print("✅ 握手消息已发送")

            # 等待响应
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                print(f"✅ 收到响应: {response[:100]}")

                data = json.loads(response)
                print(f"✅ 响应类型: {data.get('type')}")

                print()
                print("=" * 80)
                print("🎉 WSS连接测试成功！TLS/SSL加密通信正常工作！")
                print("=" * 80)

                return True

            except TimeoutError:
                print("⚠️  等待响应超时")
                return False

    except Exception as e:
        print(f"❌ WSS连接失败: {e}")
        print()
        print("可能的原因：")
        print("  1. Gateway未启用TLS（检查config.yaml中tls.enabled）")
        print("  2. WSS端口配置不正确（通常为8443或其他）")
        print("   3. Gateway未运行")
        print()
        print("建议：")
        print("  - 先测试HTTP连接: curl http://localhost:8005/health")
        print("  - 检查Gateway日志")

        return False

if __name__ == "__main__":
    print("WSS (WebSocket Secure) 测试")
    print("注意：此测试需要Gateway启用TLS并监听WSS端口")
    print()

    result = asyncio.run(test_wss_connection())

    if result:
        print("\n✅ TLS/SSL配置正常！")
    else:
        print("\n⚠️  TLS/SSL需要配置")
