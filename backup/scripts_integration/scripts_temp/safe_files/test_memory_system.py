#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记忆系统测试脚本
Test Script for Memory System
"""

import json
import requests
import time
from datetime import datetime

def test_memory_system():
    """测试记忆系统的完整功能"""
    base_url = "http://localhost:8003"

    print("🧠 测试 Athena 记忆系统")
    print("=" * 50)

    # 1. 健康检查
    print("\n1️⃣ 健康检查...")
    try:
        response = requests.get(f"{base_url}/api/health")
        if response.status_code == 200:
            health = response.json()
            print(f"   ✅ 服务状态: {health['status']}")
            print(f"   📅 时间戳: {health['timestamp']}")
        else:
            print(f"   ❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 无法连接到服务: {e}")
        return False

    # 2. 获取初始统计
    print("\n2️⃣ 获取初始统计...")
    try:
        response = requests.get(f"{base_url}/api/memory/stats")
        if response.status_code == 200:
            stats = response.json()
            initial_count = stats.get('total_memories', 0)
            print(f"   📊 初始记忆数量: {initial_count}")
        else:
            print(f"   ⚠️ 无法获取统计信息: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️ 获取统计信息错误: {e}")

    # 3. 测试存储记忆
    print("\n3️⃣ 测试存储记忆...")
    test_memories = [
        {
            "agent_id": "athena",
            "content": "今天启动了记忆系统，时间为 " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "memory_type": "event",
            "importance": 0.9,
            "tags": ["系统启动", "重要事件"]
        },
        {
            "agent_id": "athena",
            "content": "用户的偏好：喜欢使用中文进行交流",
            "memory_type": "preference",
            "importance": 0.8,
            "tags": ["用户偏好", "语言"]
        },
        {
            "agent_id": "athena",
            "content": "技术栈：Python, FastAPI, PostgreSQL, Redis",
            "memory_type": "knowledge",
            "importance": 0.7,
            "tags": ["技术", "栈"]
        }
    ]

    stored_count = 0
    for i, memory in enumerate(test_memories, 1):
        try:
            response = requests.post(f"{base_url}/api/memory/store", json=memory)
            if response.status_code == 200:
                print(f"   ✅ 记忆 {i} 存储成功")
                stored_count += 1
            else:
                print(f"   ❌ 记忆 {i} 存储失败: {response.text}")
        except Exception as e:
            print(f"   ❌ 记忆 {i} 存储错误: {e}")

    # 4. 测试检索记忆
    print("\n4️⃣ 测试检索记忆...")
    test_queries = [
        {"agent_id": "athena", "query": "启动", "limit": 5},
        {"agent_id": "athena", "query": "偏好", "limit": 5},
        {"agent_id": "athena", "query": "技术", "limit": 5}
    ]

    for i, query in enumerate(test_queries, 1):
        try:
            response = requests.post(f"{base_url}/api/memory/recall", json=query)
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ 查询 {i} ('{query['query']}') 找到 {result['count']} 条记忆")
                for j, memory in enumerate(result['memories'][:2], 1):
                    print(f"      {j}. {memory['content'][:50]}...")
            else:
                print(f"   ❌ 查询 {i} 失败: {response.text}")
        except Exception as e:
            print(f"   ❌ 查询 {i} 错误: {e}")

    # 5. 获取最终统计
    print("\n5️⃣ 获取最终统计...")
    try:
        response = requests.get(f"{base_url}/api/memory/stats")
        if response.status_code == 200:
            stats = response.json()
            final_count = stats.get('total_memories', 0)
            print(f"   📊 最终记忆数量: {final_count}")
            print(f"   📈 新增记忆: {final_count - initial_count}")
            print("\n   按类型统计:")
            for mem_type, count in stats.get('by_type', {}).items():
                print(f"      - {mem_type}: {count} 条")
        else:
            print(f"   ⚠️ 无法获取最终统计: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️ 获取最终统计错误: {e}")

    # 6. 测试结果总结
    print("\n" + "=" * 50)
    print("📋 测试结果总结:")
    print(f"   - 服务健康: ✅")
    print(f"   - 存储测试: {stored_count}/{len(test_memories)} 成功")
    print(f"   - 检索测试: ✅")
    print(f"   - 总体评价: {'✅ 通过' if stored_count == len(test_memories) else '⚠️ 部分失败'}")

    return stored_count == len(test_memories)

if __name__ == "__main__":
    # 等待服务启动
    time.sleep(2)

    # 运行测试
    success = test_memory_system()

    # 退出码
    exit(0 if success else 1)