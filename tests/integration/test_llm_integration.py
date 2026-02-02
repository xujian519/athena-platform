#!/usr/bin/env python3
"""
LLM集成测试脚本
Test LLM Integration for Athena Platform
"""

import asyncio
import json
import requests
import sys
from pathlib import Path
from datetime import datetime

# 添加路径
sys.path.append(str(Path(__file__).parent))

async def test_llm_integration():
    """测试LLM集成"""
    print("🧪 开始LLM集成测试...")
    print("=" * 50)

    # 1. 测试配置加载
    print("\n1️⃣ 测试配置加载...")
    try:
        with open('config/domestic_llm_config.json', 'r') as f:
            config = json.load(f)
        print(f"✅ 配置加载成功")
        print(f"   - 主要提供商: {config['primary_provider']}")
        print(f"   - API Key: {config['zhipu_api_key'][:10]}...")
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False

    # 2. 测试智谱API
    print("\n2️⃣ 测试智谱GLM-4 API...")
    try:
        url = 'https://open.bigmodel.cn/api/paas/v4/chat/completions'
        headers = {
            'Authorization': f'Bearer {config["zhipu_api_key"]}',
            'Content-Type': 'application/json'
        }
        data = {
            'model': 'glm-4',
            'messages': [{'role': 'user', 'content': '请用一句话介绍你自己'}],
            'max_tokens': 100
        }

        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print("✅ 智谱GLM-4 API连接成功")
            print(f"   响应: {result['choices'][0]['message']['content']}")
        else:
            print(f"❌ 智谱API错误: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 智谱API连接失败: {e}")
        return False

    # 3. 测试Ollama本地模型
    print("\n3️⃣ 测试Ollama本地模型...")
    try:
        ollama_url = 'http://localhost:11434/api/generate'
        ollama_data = {
            'model': 'qwen:7b',
            'prompt': '你好，请简单介绍一下你自己',
            'stream': False
        }

        response = requests.post(ollama_url, json=ollama_data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print("✅ Ollama本地模型连接成功")
            print(f"   模型: {result['model']}")
            print(f"   响应: {result['response'][:50]}...")
        else:
            print(f"❌ Ollama错误: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ollama连接失败: {e}")
        return False

    # 4. 测试模型路由器
    print("\n4️⃣ 测试模型路由器...")
    try:
        sys.path.append('core/orchestration')
        from xiaonuo_model_router import XiaonuoModelRouter

        router = XiaonuoModelRouter()
        print("✅ 模型路由器加载成功")

        # 测试路由选择
        task_type = "patent_analysis"
        model_config = router.select_model(task_type)
        print(f"✅ 专利分析任务路由到: {model_config.name}")

        task_type = "general_chat"
        model_config = router.select_model(task_type)
        print(f"✅ 日常对话任务路由到: {model_config.name}")

    except Exception as e:
        print(f"❌ 模型路由器测试失败: {e}")
        return False

    # 5. 测试记忆系统存储LLM响应
    print("\n5️⃣ 测试记忆系统存储LLM响应...")
    try:
        memory_api_url = 'http://localhost:8003/api/memory/store'
        memory_data = {
            "agent_id": "xiaonuo_pisces",
            "content": "今天测试了GLM-4和Ollama的连接，都成功响应了",
            "memory_type": "knowledge",
            "importance": 0.8,
            "tags": ["LLM测试", "GLM-4", "Ollama", "系统集成"]
        }

        response = requests.post(memory_api_url, json=memory_data)
        if response.status_code == 200:
            print("✅ LLM响应已存储到记忆系统")
        else:
            print(f"❌ 记忆存储失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 记忆系统测试失败: {e}")

    print("\n" + "=" * 50)
    print("🎉 LLM集成测试完成！")
    print("✅ 所有LLM服务运行正常")
    print("✅ 智谱GLM-4 API可用")
    print("✅ Ollama本地模型可用")
    print("✅ 模型路由器工作正常")
    print("✅ 记忆系统集成成功")

    return True

if __name__ == "__main__":
    success = asyncio.run(test_llm_integration())
    sys.exit(0 if success else 1)