"""
使用httpx完全模拟curl的行为
"""

import asyncio

import httpx


async def test_httpx_as_curl():
    """使用httpx模拟curl"""

    print("测试: httpx模拟curl行为")
    print("=" * 60)

    # curl的headers
    curl_headers = {
        "User-Agent": "curl/8.7.1",
        "Accept": "*/*",
    }

    # 测试1: 直接URL
    print("\n测试1: 使用完整URL")
    try:
        async with httpx.AsyncClient(
            headers=curl_headers,
            http2=False,
            follow_redirects=True,
            timeout=30.0,
        ) as client:
            response = await client.get("http://localhost:8009/health")
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.text}")
            if response.status_code == 200:
                print("✅ 成功！")
    except Exception as e:
        print(f"❌ 错误: {e}")

    # 测试2: 使用base_url
    print("\n测试2: 使用base_url")
    try:
        async with httpx.AsyncClient(
            base_url="http://localhost:8009",
            headers=curl_headers,
            http2=False,
            follow_redirects=True,
            timeout=30.0,
        ) as client:
            response = await client.get("/health")
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.text}")
            if response.status_code == 200:
                print("✅ 成功！")
    except Exception as e:
        print(f"❌ 错误: {e}")

    # 测试3: 禁用HTTP/2，明确使用HTTP/1.1
    print("\n测试3: 明确使用HTTP/1.1")
    try:
        limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
        async with httpx.AsyncClient(
            base_url="http://localhost:8009",
            headers=curl_headers,
            http2=False,
            verify=False,
            follow_redirects=True,
            timeout=30.0,
            limits=limits,
        ) as client:
            # 打印请求详情
            print("客户端配置:")
            print(f"  base_url: {client.base_url}")
            print(f"  timeout: {client.timeout}")
            print(f"  http2: {getattr(client, 'http2', 'unknown')}")

            response = await client.get("/health")
            print("\n响应:")
            print(f"  状态码: {response.status_code}")
            print(f"  响应: {response.text}")
            if response.status_code == 200:
                print("✅ 成功！")
                data = response.json()
                print(f"  解析: {data}")
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_httpx_as_curl())
