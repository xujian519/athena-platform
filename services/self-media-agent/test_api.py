#!/usr/bin/env python3
"""
测试小宸智能体API功能
"""

import requests
from typing import Any, Dict, List, Optional, Tuple, Callable, Union
import json

# API基础URL
BASE_URL = "http://localhost:8030"

def test_content_creation() -> Any:
    """测试内容创作API"""
    print("\n=== 测试内容创作功能 ===")

    # 准备测试数据
    data = {
        "type": "article",
        "topic": "专利申请的基础知识",
        "platform": "小红书",
        "style": "casual"
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/content/create",
            json=data,
            headers={"Content-Type": "application/json"}
        )

        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"✅ 内容创作成功！")
            print(f"内容标题: {result['content']['title']}")
            print(f"内容长度: {len(result['content']['body'])} 字")
            print(f"标签: {', '.join(result['content']['tags'])}")
        else:
            print(f"❌ 请求失败: {response.text}")

    except Exception as e:
        print(f"❌ 请求异常: {str(e)}")

def test_chat() -> Any:
    """测试智能对话API"""
    print("\n=== 测试智能对话功能 ===")

    data = {
        "message": "你好，小宸！请介绍一下专利申请的流程",
        "context": "ip_tech"
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/chat",
            json=data,
            headers={"Content-Type": "application/json"}
        )

        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"✅ 对话成功！")
            print(f"小宸回复: {result['response'][:200]}...")
        else:
            print(f"❌ 请求失败: {response.text}")

    except Exception as e:
        print(f"❌ 请求异常: {str(e)}")

def test_analytics() -> Any:
    """测试数据分析API"""
    print("\n=== 测试数据分析功能 ===")

    try:
        response = requests.get(f"{BASE_URL}/api/v1/analytics/overview")

        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"✅ 数据分析成功！")
            print(f"总发布数: {result['total_posts']}")
            print(f"总互动数: {result['total_engagement']}")
            print(f"热门话题: {', '.join(result['trending_topics'])}")
        else:
            print(f"❌ 请求失败: {response.text}")

    except Exception as e:
        print(f"❌ 请求异常: {str(e)}")

if __name__ == "__main__":
    print("🚀 开始测试小宸智能体API...")

    # 测试基础服务
    print("\n=== 测试基础服务 ===")
    response = requests.get(f"{BASE_URL}/")
    if response.status_code == 200:
        print("✅ 基础服务正常运行")
    else:
        print("❌ 基础服务异常")

    # 测试健康检查
    print("\n=== 测试健康检查 ===")
    response = requests.get(f"{BASE_URL}/api/v1/health")
    if response.status_code == 200:
        print("✅ 健康检查通过")
    else:
        print("❌ 健康检查失败")

    # 测试各项功能
    test_content_creation()
    test_chat()
    test_analytics()

    print("\n🎉 测试完成！")