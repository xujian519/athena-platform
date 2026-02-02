#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试混合多模态系统
Test Hybrid Multimodal System
"""

import asyncio
import aiohttp
import json
import time
from pathlib import Path

# API基础URL
BASE_URL = "http://localhost:8090"

async def test_health():
    """测试健康检查"""
    print("1. 测试健康检查...")

    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/health") as response:
            data = await response.json()
            print(f"   状态: {data['status']}")
            print(f"   服务: {json.dumps(data['services'], indent=2, ensure_ascii=False)}")

async def test_statistics():
    """测试统计信息"""
    print("\n2. 获取统计信息...")

    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/api/statistics") as response:
            data = await response.json()

            if 'total_requests' in data:
                print(f"   总请求数: {data['total_requests']}")
                print(f"   MCP使用率: {data.get('mcp_ratio', '0%')}")
                print(f"   本地使用率: {data.get('local_ratio', '0%')}")
                print(f"   成功率: {data.get('success_rate', '0%')}")
            else:
                print(f"   {data.get('message', '暂无统计')}")

async def test_intelligent_routing():
    """测试智能路由决策"""
    print("\n3. 测试智能路由决策...")

    from intelligent_router import get_intelligent_router, ProcessingRequest, ProcessingPriority, DataSensitivity

    router = get_intelligent_router()

    test_cases = [
        {
            "name": "🔒 机密音频文件",
            "request": ProcessingRequest(
                request_id="test_secret",
                file_path="/tmp/secret.amr",
                file_type="audio",
                sensitivity=DataSensitivity.SECRET
            )
        },
        {
            "name": "⚡ 紧急图片分析",
            "request": ProcessingRequest(
                request_id="test_urgent",
                file_path="/tmp/urgent.jpg",
                file_type="image",
                priority=ProcessingPriority.URGENT
            )
        },
        {
            "name": "📦 大批量文档",
            "request": ProcessingRequest(
                request_id="test_batch",
                file_path="/tmp/batch.pdf",
                file_type="document",
                batch_size=500
            )
        },
        {
            "name": "🎯 高质量要求",
            "request": ProcessingRequest(
                request_id="test_quality",
                file_path="/tmp/quality.png",
                file_type="image",
                require_high_quality=True
            )
        }
    ]

    for test in test_cases:
        method = router.choose_optimal_method(test['request'])
        print(f"   {test['name']} → {method.value}")

async def test_api_upload():
    """测试API上传功能（模拟）"""
    print("\n4. API使用示例...")

    print("   示例1: 智能处理图片")
    print("   curl -X POST http://localhost:8090/api/process \\")
    print("     -F \"file=@photo.jpg\" \\")
    print("     -F \"priority=high\" \\")
    print("     -F \"sensitivity=public\" \\")
    print("     -F \"high_quality=true\"")
    print("")

    print("   示例2: 批量处理")
    print("   curl -X POST http://localhost:8090/api/batch-process \\")
    print("     -F \"files=@doc1.pdf\" -F \"files=@doc2.jpg\" \\")
    print("     -F \"priority=normal\" \\")
    print("     -F \"max_concurrent=3\"")
    print("")

    print("   示例3: 机密音频处理（会自动选择本地）")
    print("   curl -X POST http://localhost:8090/api/process \\")
    print("     -F \"file=@meeting.amr\" \\")
    print("     -F \"sensitivity=secret\"")
    print("")

async def test_cost_analysis():
    """测试成本分析"""
    print("\n5. 成本分析...")

    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/api/cost-analysis") as response:
            data = await response.json()

            if 'total_requests' in data:
                print(f"   总请求数: {data['total_requests']}")
                print(f"   实际成本: ${data['actual_cost']:.4f}")
                print(f"   节省成本: ${data['savings']:.4f} ({data['savings_percentage']})")
                print(f"   平均成本: ${data['average_cost_per_request']:.4f}")
            else:
                print(f"   {data.get('message', '暂无数据')}")

async def main():
    """主测试函数"""
    print("🧪 Athena混合多模态系统测试")
    print("=" * 50)

    # 测试各个组件
    await test_health()
    await test_statistics()
    await test_intelligent_routing()
    await test_api_upload()
    await test_cost_analysis()

    print("\n✅ 测试完成！")
    print("\n💡 系统特性：")
    print("   1. 智能路由：根据场景自动选择最优方案")
    print("   2. 成本优化：批量处理使用本地，高质量使用MCP")
    print("   3. 数据安全：敏感数据本地处理")
    print("   4. 灵活配置：支持优先级和质量要求设置")

if __name__ == "__main__":
    asyncio.run(main())