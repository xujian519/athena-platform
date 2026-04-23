"""
简单的httpx测试
诊断502错误问题
"""

import asyncio

import httpx


async def test_httpx():
    """测试httpx连接"""

    print("测试1: 使用httpx.AsyncClient（默认配置）")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8009/health")
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.text}")
    except Exception as e:
        print(f"错误: {e}")

    print("\n测试2: 使用httpx.AsyncClient（禁用HTTP/2）")
    try:
        async with httpx.AsyncClient(http1=True) as client:
            response = await client.get("http://localhost:8009/health")
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.text}")
    except Exception as e:
        print(f"错误: {e}")

    print("\n测试3: 使用base_url参数")
    try:
        async with httpx.AsyncClient(base_url="http://localhost:8009", http1=True) as client:
            response = await client.get("/health")
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.text}")
    except Exception as e:
        print(f"错误: {e}")


if __name__ == "__main__":
    asyncio.run(test_httpx())
