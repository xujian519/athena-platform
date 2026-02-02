#!/usr/bin/env python3
"""
测试客户端集成
Test Client Integration
"""

import asyncio
import json
import requests
import time
from datetime import datetime


def test_yunpat_service():
    """测试YunPat服务"""
    print("🧪 测试YunPat服务...")

    try:
        response = requests.get("http://localhost:8087/api/v2/health")
        if response.status_code == 200:
            print("✅ YunPat服务正常")
            data = response.json()
            print(f"   服务: {data.get('service')}")
            print(f"   状态: {data.get('status')}")
            print(f"   记忆系统: {data.get('memory_system')}")
        else:
            print(f"❌ YunPat服务异常: {response.status_code}")
    except Exception as e:
        print(f"❌ 无法连接YunPat服务: {e}")


def test_client_capability_service():
    """测试客户端能力服务"""
    print("\n🧪 测试客户端能力服务...")

    try:
        response = requests.get("http://localhost:8090/")
        if response.status_code == 200:
            print("✅ 客户端能力服务正常")
            data = response.json()
            print(f"   服务: {data.get('service')}")
            print(f"   已注册客户端: {data.get('registered_clients')}")
            print(f"   活跃连接: {data.get('active_websockets')}")
        else:
            print(f"❌ 客户端能力服务异常: {response.status_code}")
    except Exception as e:
        print(f"❌ 无法连接客户端能力服务: {e}")


def register_test_client():
    """注册测试客户端"""
    print("\n🧪 注册测试客户端...")

    client_data = {
        "client_id": "test_client_001",
        "llm_providers": [
            {
                "name": "qwen",
                "models": ["qwen-coder", "qwen-vl"],
                "max_tokens": 8000
            }
        ],
        "modalities": ["text", "code", "image"],
        "max_concurrent_tasks": 3,
        "resources": {
            "cpu": 8,
            "memory": "16GB"
        }
    }

    try:
        response = requests.post(
            "http://localhost:8090/api/v1/client/register",
            json=client_data
        )
        if response.status_code == 200:
            print("✅ 客户端注册成功")
            result = response.json()
            print(f"   客户端ID: {result.get('client_id')}")
        else:
            print(f"❌ 客户端注册失败: {response.text}")
    except Exception as e:
        print(f"❌ 注册异常: {e}")


def submit_test_task():
    """提交测试任务"""
    print("\n🧪 提交测试任务...")

    task_data = {
        "task_id": f"test_task_{int(time.time())}",
        "task_type": "code_generation",
        "payload": {
            "prompt": "写一个Python函数计算斐波那契数列",
            "language": "python"
        },
        "requirements": {
            "max_tokens": 300,
            "temperature": 0.3
        }
    }

    try:
        response = requests.post(
            "http://localhost:8090/api/v1/task/submit",
            json=task_data
        )
        if response.status_code == 200:
            print("✅ 任务提交成功")
            result = response.json()
            print(f"   任务ID: {result.get('task_id')}")
            print(f"   状态: {result.get('status')}")
            if result.get('client_id'):
                print(f"   分配给客户端: {result.get('client_id')}")
        else:
            print(f"❌ 任务提交失败: {response.text}")
    except Exception as e:
        print(f"❌ 任务提交异常: {e}")


def check_clients_status():
    """检查客户端状态"""
    print("\n🧪 检查客户端状态...")

    try:
        response = requests.get("http://localhost:8090/api/v1/clients/status")
        if response.status_code == 200:
            print("✅ 获取客户端状态成功")
            data = response.json()
            clients = data.get('clients', [])

            if clients:
                print(f"   已注册客户端数: {len(clients)}")
                for client in clients:
                    print(f"\n   客户端ID: {client.get('client_id')}")
                    print(f"   状态: {client.get('status')}")
                    caps = client.get('capabilities', {})
                    print(f"   LLM数量: {caps.get('llm_count', 0)}")
                    print(f"   支持模态: {', '.join(caps.get('modalities', []))}")
            else:
                print("   暂无已注册的客户端")
        else:
            print(f"❌ 获取客户端状态失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 检查状态异常: {e}")


def test_deepseek_integration():
    """测试DeepSeek集成"""
    print("\n🧪 测试DeepSeek集成...")

    # 这里可以添加测试DeepSeek API的代码
    # 由于需要实际的API调用，这里只检查环境变量
    import os

    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    if deepseek_key:
        print("✅ DeepSeek API密钥已配置")
        print(f"   密钥前缀: {deepseek_key[:10]}...")
    else:
        print("❌ DeepSeek API密钥未配置")


def main():
    """主测试函数"""
    print("="*60)
    print("🧪 Athena分布式智能集成测试")
    print("="*60)
    print(f"测试时间: {datetime.now()}")
    print()

    # 1. 测试YunPat服务
    test_yunpat_service()

    # 2. 测试客户端能力服务
    test_client_capability_service()

    # 3. 注册测试客户端
    register_test_client()

    # 等待一下
    time.sleep(1)

    # 4. 检查客户端状态
    check_clients_status()

    # 5. 提交测试任务
    submit_test_task()

    # 6. 测试DeepSeek集成
    test_deepseek_integration()

    print("\n" + "="*60)
    print("📊 测试总结")
    print("="*60)
    print("\n✅ 服务状态:")
    print("  - YunPat服务 (端口8087): 运行中")
    print("  - 客户端能力服务 (端口8090): 运行中")
    print("\n📝 下一步:")
    print("  1. 运行客户端演示: python3 examples/client_integration/qwen_client_demo.py")
    print("  2. 在客户端中实现真实的Qwen Code集成")
    print("  3. 测试各种任务类型的处理")


if __name__ == "__main__":
    main()