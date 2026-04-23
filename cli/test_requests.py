"""
使用requests库测试
对比httpx和requests的差异
"""

import requests
import asyncio


def test_requests():
    """测试requests连接"""

    print("测试1: 使用requests（默认）")
    try:
        response = requests.get("http://localhost:8009/health")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
    except Exception as e:
        print(f"错误: {e}")

    print("\n测试2: 使用requests（设置headers）")
    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        }
        response = requests.get("http://localhost:8009/health", headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
    except Exception as e:
        print(f"错误: {e}")


if __name__ == "__main__":
    test_requests()
