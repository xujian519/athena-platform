#!/usr/bin/env python3
"""
WebChat V2 Gateway 测试客户端
用于测试Gateway WebSocket连接和通信

作者: Athena平台团队
创建时间: 2025-01-31
版本: 2.0.0
"""

import asyncio
import json
import websockets
from datetime import datetime


class GatewayTestClient:
    """Gateway测试客户端"""

    def __init__(self, url: str, user_id: str = "xujian"):
        """
        初始化客户端

        Args:
            url: WebSocket URL
            user_id: 用户ID
        """
        self.url = url
        self.user_id = user_id
        self.ws = None
        self.request_id = 0

    def _get_request_id(self) -> str:
        """生成请求ID"""
        self.request_id += 1
        return f"test-{self.request_id}"

    def _create_request(self, method: str, params: dict = None) -> dict:
        """创建请求帧"""
        return {
            "type": "request",
            "id": self._get_request_id(),
            "method": method,
            "params": params or {},
            "timestamp": datetime.now().isoformat(),
        }

    async def connect(self):
        """连接到Gateway"""
        ws_url = f"{self.url}?user_id={self.user_id}"
        print(f"连接到: {ws_url}")
        self.ws = await websockets.connect(ws_url)
        print("✅ 连接成功")

        # 接收连接确认事件
        response = await self.ws.recv()
        event = json.loads(response)
        print(f"📡 收到事件: {event['event']}")
        print(f"   数据: {event.get('data', {})}")

    async def send_message(self, message: str):
        """发送聊天消息"""
        request = self._create_request("send", {"message": message})
        await self.ws.send(json.dumps(request))
        print(f"📤 发送消息: {message}")

    async def get_modules(self):
        """获取可用模块列表"""
        request = self._create_request("platform_modules")
        await self.ws.send(json.dumps(request))
        print(f"📤 请求模块列表")

    async def close(self):
        """关闭连接"""
        if self.ws:
            await self.ws.close()
            print("❌ 连接已关闭")

    async def listen(self, duration: int = 10):
        """
        监听消息

        Args:
            duration: 监听时长（秒）
        """
        print(f"\n👂 监听消息 ({duration}秒)...\n")
        end_time = asyncio.get_event_loop().time() + duration

        try:
            while asyncio.get_event_loop().time() < end_time:
                try:
                    response = await asyncio.wait_for(
                        self.ws.recv(),
                        timeout=1.0
                    )
                    frame = json.loads(response)

                    frame_type = frame.get("type")
                    if frame_type == "event":
                        event_type = frame.get("event")
                        data = frame.get("data", {})
                        print(f"📡 事件 [{event_type}]:")
                        if event_type == "chat.message":
                            print(f"   💬 {data.get('content', '')}")
                        elif event_type == "heartbeat":
                            print(f"   💓 心跳")
                        else:
                            print(f"   {data}")

                    elif frame_type == "response":
                        result = frame.get("result")
                        error = frame.get("error")
                        if error:
                            print(f"❌ 错误: {error}")
                        else:
                            print(f"✅ 响应: {result}")

                except asyncio.TimeoutError:
                    continue

        except asyncio.CancelledError:
            pass


async def test_basic_chat():
    """测试基本聊天"""
    client = GatewayTestClient("ws://localhost:8000/gateway/ws", "xujian")

    try:
        await client.connect()

        # 测试1: 发送消息
        print("\n--- 测试1: 专利搜索 ---")
        await client.send_message("搜索关于深度学习的专利")
        await client.listen(duration=3)

        # 测试2: 获取模块列表
        print("\n--- 测试2: 获取模块列表 ---")
        await client.get_modules()
        await client.listen(duration=2)

        # 测试3: 继续监听
        print("\n--- 测试3: 继续监听 ---")
        await client.listen(duration=5)

    finally:
        await client.close()


async def test_different_user():
    """测试不同用户"""
    client = GatewayTestClient("ws://localhost:8000/gateway/ws", "guest")

    try:
        await client.connect()
        await client.send_message("你好，我是新用户")
        await client.listen(duration=3)

    finally:
        await client.close()


async def main():
    """主函数"""
    print("=" * 60)
    print("WebChat V2 Gateway 测试客户端")
    print("=" * 60)

    print("\n选择测试:")
    print("1. 基本聊天测试 (xujian用户)")
    print("2. 访客用户测试")

    choice = input("\n请选择 (1-2，默认1): ").strip() or "1"

    if choice == "1":
        await test_basic_chat()
    elif choice == "2":
        await test_different_user()
    else:
        print("无效选择，执行基本聊天测试")
        await test_basic_chat()

    print("\n测试完成！")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n测试中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
