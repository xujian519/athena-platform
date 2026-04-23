"""
详细诊断httpx vs curl的差异
"""

import httpx
import urllib.request
import json


def test_urllib_detailed():
    """详细测试urllib"""
    print("=" * 60)
    print("测试urllib详细诊断")
    print("=" * 60)

    url = "http://localhost:8009/health"

    # 尝试1: 简单请求
    print("\n尝试1: 简单GET请求")
    try:
        req = urllib.request.Request(url)
        print(f"  请求URL: {url}")
        print(f"  请求方法: {req.method}")
        print(f"  请求Headers:")
        for key, value in req.headers.items():
            print(f"    {key}: {value}")

        with urllib.request.urlopen(req, timeout=5) as response:
            print(f"  响应状态码: {response.status}")
            print(f"  响应Headers:")
            for key, value in response.headers.items():
                print(f"    {key}: {value}")
            data = response.read().decode('utf-8')
            print(f"  响应数据: {data[:100]}...")
    except Exception as e:
        print(f"  ❌ 错误: {e}")

    # 尝试2: 添加curl的User-Agent
    print("\n尝试2: 添加curl的User-Agent")
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "curl/8.7.1",
                "Accept": "*/*",
            }
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            print(f"  ✅ 成功！状态码: {response.status}")
            data = response.read().decode('utf-8')
            print(f"  响应数据: {data[:100]}...")
    except Exception as e:
        print(f"  ❌ 错误: {e}")


async def test_httpx_detailed():
    """详细测试httpx"""
    print("\n" + "=" * 60)
    print("测试httpx详细诊断")
    print("=" * 60)

    url = "http://localhost:8009/health"

    # 尝试1: 默认配置
    print("\n尝试1: httpx默认配置")
    try:
        async with httpx.AsyncClient() as client:
            print(f"  请求URL: {url}")
            print(f"  HTTP/2: {client.http2}")

            response = await client.get(url)
            print(f"  响应状态码: {response.status_code}")
            print(f"  响应Headers:")
            for key, value in response.headers.items():
                print(f"    {key}: {value}")

            if response.status_code == 502:
                print(f"  ❌ 502错误！响应体: {response.text[:200]}")
    except Exception as e:
        print(f"  ❌ 错误: {e}")

    # 尝试2: 强制HTTP/1.1
    print("\n尝试2: 强制HTTP/1.1 + curl的User-Agent")
    try:
        async with httpx.AsyncClient(
            http2=False,
            headers={
                "User-Agent": "curl/8.7.1",
                "Accept": "*/*",
            }
        ) as client:
            response = await client.get(url)
            print(f"  状态码: {response.status_code}")
            print(f"  响应头:")
            for key, value in response.headers.items():
                print(f"    {key}: {value}")
            print(f"  完整响应: {response.text}")
            if response.status_code == 200:
                print(f"  ✅ 成功！")
    except Exception as e:
        print(f"  ❌ 错误: {e}")

    # 尝试3: 使用基础URL
    print("\n尝试3: 使用base_url参数")
    try:
        async with httpx.AsyncClient(
            base_url="http://localhost:8009",
            http2=False,
        ) as client:
            response = await client.get("/health")
            print(f"  状态码: {response.status_code}")
            print(f"  响应头:")
            for key, value in response.headers.items():
                print(f"    {key}: {value}")
            print(f"  完整响应: {response.text}")
            if response.status_code == 200:
                print(f"  ✅ 成功！")
                # 解析JSON
                try:
                    data = response.json()
                    print(f"  解析后数据: {data}")
                except:
                    pass
    except Exception as e:
        print(f"  ❌ 错误: {e}")


if __name__ == "__main__":
    import asyncio

    test_urllib_detailed()
    asyncio.run(test_httpx_detailed())
