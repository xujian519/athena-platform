#!/usr/bin/env python3
"""
WebChat V2 Gateway WebSocket测试客户端
测试WebSocket连接、JWT认证和模块调用功能

作者: Athena平台团队
创建时间: 2025-01-31
版本: 2.0.0
"""

import asyncio
import json
import websockets
import jwt
from datetime import datetime, timezone
from typing import Optional


# JWT配置（与服务器保持一致）
JWT_SECRET = "wyFS8YpbrMunCmsMASeWEmtULWuwTE0TWnW1WcqkDIU"
JWT_ALGORITHM = "HS256"

# WebSocket服务器地址
WS_URL = "ws://localhost:8000/gateway/ws"
HTTP_URL = "http://localhost:8000"

# 测试用户配置
TEST_USER_ID = "test_user"
TEST_SESSION_ID = "test_session_001"


class GatewayTestClient:
    """Gateway测试客户端"""

    def __init__(self, user_id: str = TEST_USER_ID, session_id: str = TEST_SESSION_ID):
        self.user_id = user_id
        self.session_id = session_id
        self.ws_url = WS_URL
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.request_id = 0

    def generate_jwt_token(self) -> str:
        """生成JWT token"""
        now = datetime.now(timezone.utc)
        payload = {
            "user_id": self.user_id,
            "exp": now.timestamp() + 86400,  # 24小时过期
            "iat": now.timestamp(),
            "iss": "webchat-gateway",
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    async def connect(self, use_token: bool = False) -> bool:
        """连接到WebSocket服务器"""
        try:
            # 构建连接URL
            url = f"{self.ws_url}?user_id={self.user_id}&session_id={self.session_id}"
            if use_token:
                token = self.generate_jwt_token()
                url += f"&token={token}"

            print(f"\n{'='*60}")
            print(f"连接到: {self.ws_url}")
            print(f"用户ID: {self.user_id}")
            print(f"会话ID: {self.session_id}")
            print(f"JWT认证: {'是' if use_token else '否'}")
            print(f"{'='*60}\n")

            # 建立连接（使用close_timeout代替timeout）
            self.websocket = await websockets.connect(url, close_timeout=10)
            print("✅ WebSocket连接成功!")
            return True

        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False

    async def disconnect(self):
        """断开连接"""
        if self.websocket:
            await self.websocket.close()
            print("\n✅ 连接已关闭")

    def create_request(self, method: str, params: dict) -> dict:
        """创建请求帧"""
        self.request_id += 1
        return {
            "type": "request",
            "id": f"req_{self.request_id}",
            "method": method,
            "params": params,
            "timestamp": datetime.now().isoformat(),
        }

    async def send_request(self, method: str, params: dict) -> Optional[dict]:
        """发送请求并接收响应"""
        if not self.websocket:
            print("❌ 未连接到服务器")
            return None

        request = self.create_request(method, params)
        request_id = request["id"]
        print(f"\n📤 发送请求:")
        print(f"   ID: {request_id}")
        print(f"   方法: {method}")
        print(f"   参数: {json.dumps(params, ensure_ascii=False)}")

        try:
            await self.websocket.send(json.dumps(request))

            # 等待响应（跳过事件消息）
            while True:
                response_str = await asyncio.wait_for(self.websocket.recv(), timeout=10)
                response = json.loads(response_str)

                # 如果是响应类型且ID匹配，则返回
                if response.get("type") == "response" and response.get("id") == request_id:
                    print(f"\n📥 收到响应:")
                    print(f"   类型: {response.get('type')}")
                    print(f"   ID: {response.get('id')}")

                    if "result" in response:
                        result = response["result"]
                        # 美化打印结果
                        if isinstance(result, dict):
                            print(f"   结果: {json.dumps(result, ensure_ascii=False, indent=10)}")
                        else:
                            print(f"   结果: {result}")
                    if "error" in response:
                        print(f"   错误: {response['error']}")

                    return response
                # 如果是事件消息，打印并继续等待
                elif response.get("type") == "event":
                    print(f"   [跳过事件: {response.get('event')}]")
                    continue

        except asyncio.TimeoutError:
            print("❌ 请求超时")
            return None
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            return None

    async def listen_events(self, count: int = 3, timeout: int = 5):
        """监听服务器推送的事件"""
        print(f"\n🎧 监听事件 (最多{count}个, {timeout}秒超时)...")
        received = 0

        try:
            while received < count:
                try:
                    message_str = await asyncio.wait_for(self.websocket.recv(), timeout=timeout)
                    message = json.loads(message_str)

                    print(f"\n📨 收到消息 #{received + 1}:")
                    print(f"   类型: {message.get('type')}")

                    if message.get('type') == 'event':
                        print(f"   事件: {message.get('event')}")
                        data = message.get('data')
                        if data:
                            print(f"   数据: {json.dumps(data, ensure_ascii=False, indent=10)}")
                    else:
                        print(f"   内容: {json.dumps(message, ensure_ascii=False, indent=6)}")

                    received += 1

                except asyncio.TimeoutError:
                    print(f"⏱️  {timeout}秒内无新事件")
                    break

        except Exception as e:
            print(f"❌ 监听事件失败: {e}")


# 测试用例
async def test_basic_connection():
    """测试1: 基本WebSocket连接（无JWT）"""
    print("\n" + "="*60)
    print("测试1: 基本WebSocket连接（无JWT认证）")
    print("="*60)

    client = GatewayTestClient()
    if await client.connect(use_token=False):
        await client.listen_events(count=2, timeout=3)
        await client.disconnect()
        print("\n✅ 测试1通过")
        return True
    else:
        print("\n❌ 测试1失败")
        return False


async def test_jwt_authentication():
    """测试2: JWT认证连接"""
    print("\n" + "="*60)
    print("测试2: JWT认证连接")
    print("="*60)

    client = GatewayTestClient()
    if await client.connect(use_token=True):
        await client.listen_events(count=2, timeout=3)
        await client.disconnect()
        print("\n✅ 测试2通过")
        return True
    else:
        print("\n❌ 测试2失败")
        return False


async def test_platform_modules():
    """测试3: 获取平台模块列表"""
    print("\n" + "="*60)
    print("测试3: 获取平台模块列表")
    print("="*60)

    client = GatewayTestClient()
    if await client.connect(use_token=False):
        response = await client.send_request("platform_modules", {})
        await client.disconnect()

        if response and response.get("type") == "response" and "result" in response:
            modules = response["result"].get("modules", [])
            print(f"\n📊 模块总数: {len(modules)}")
            print("\n模块列表:")
            for m in modules:
                print(f"   - {m['display_name']} ({m['name']}): {m['description']}")
            print("\n✅ 测试3通过")
            return True
        else:
            print("\n❌ 测试3失败")
            return False
    else:
        print("\n❌ 测试3失败")
        return False


async def test_patent_search():
    """测试4: 专利搜索模块调用"""
    print("\n" + "="*60)
    print("测试4: 专利搜索模块调用")
    print("="*60)

    client = GatewayTestClient()
    if await client.connect(use_token=False):
        # 调用专利搜索
        response = await client.send_request("platform_invoke", {
            "module": "patent.search",
            "action": "search",
            "params": {
                "query": "人工智能",
                "limit": 3
            }
        })
        await client.disconnect()

        if response:
            print("\n✅ 测试4通过（调用成功）")
            return True
        else:
            print("\n❌ 测试4失败")
            return False
    else:
        print("\n❌ 测试4失败")
        return False


async def test_concurrent_requests():
    """测试5: 并发请求"""
    print("\n" + "="*60)
    print("测试5: 并发请求")
    print("="*60)

    client = GatewayTestClient()
    if await client.connect(use_token=False):
        # 同时发送多个请求
        tasks = [
            client.send_request("platform_modules", {}),
            client.send_request("platform_modules", {}),
            client.send_request("platform_modules", {}),
        ]

        responses = await asyncio.gather(*tasks, return_exceptions=True)
        await client.disconnect()

        success_count = sum(1 for r in responses if r and r.get("type") == "response")
        print(f"\n📊 并发请求结果: {success_count}/{len(tasks)} 成功")

        if success_count == len(tasks):
            print("\n✅ 测试5通过")
            return True
        else:
            print("\n⚠️  测试5部分通过")
            return False
    else:
        print("\n❌ 测试5失败")
        return False


async def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*70)
    print(" "*15 + "WebChat V2 Gateway 测试套件")
    print("="*70)

    tests = [
        ("基本WebSocket连接", test_basic_connection),
        ("JWT认证连接", test_jwt_authentication),
        ("获取平台模块列表", test_platform_modules),
        ("专利搜索模块调用", test_patent_search),
        ("并发请求", test_concurrent_requests),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ 测试异常: {e}")
            results.append((name, False))

        # 等待一段时间再进行下一个测试
        await asyncio.sleep(1)

    # 打印测试结果汇总
    print("\n" + "="*70)
    print(" "*25 + "测试结果汇总")
    print("="*70)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {status}   {name}")

    print("\n" + "-"*70)
    print(f"   测试通过率: {passed}/{total} ({passed*100//total}%)")
    print("="*70)

    return passed == total


if __name__ == "__main__":
    # 运行测试
    result = asyncio.run(run_all_tests())
    exit(0 if result else 1)
