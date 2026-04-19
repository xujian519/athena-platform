#!/usr/bin/env python3
"""
测试法律世界模型API接口
"""

import asyncio
import sys
from pathlib import Path

import aiohttp

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))


async def test_legal_world_model():
    """测试法律世界模型API"""
    print("🧠 测试法律世界模型API接口...")

    gateway_url = "http://localhost:8080"

    async with aiohttp.ClientSession() as session:
        try:
            # 1. 测试健康检查
            print("\n🏥 测试健康检查接口...")
            async with session.get(f"{gateway_url}/api/v1/legal/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ 健康检查成功: {data.get('status', 'unknown')}")
                    print(f"📊 组件状态: {data.get('components', {})}")
                else:
                    print(f"❌ 健康检查失败: {response.status}")

            # 2. 测试动态提示词生成
            print("\n📝 测试动态提示词生成接口...")
            prompt_data = {
                "business_type": "专利审查意见答复",
                "domain": "patent_law",
                "keywords": ["新颖性", "创造性", "审查意见", "答复策略"],
                "user_query": "如何回复审查意见",
                "urgency_level": "high",
                "complexity_level": "high",
            }

            async with session.post(
                f"{gateway_url}/api/v1/legal/prompt/generate", json=prompt_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("success", False):
                        print(f"❌ 提示词生成失败: {data.get('detail', 'Unknown error')}")
                    else:
                        print("✅ 提示词生成成功")
                        prompt_result = data.get("data", {})
                        print(f"📝 提示词长度: {len(prompt_result.get('prompt', ''))}")
                        print(f"📊 置信度: {prompt_result.get('confidence_score', 0.0)}")
                else:
                    print(f"❌ 提示词生成请求失败: {response.status}")

            # 3. 测试场景规划器
            print("\n📋 测试场景规划器接口...")
            plan_data = {
                "goal": "制定专利审查意见答复策略",
                "domain": "patent_law",
                "complexity": "high",
                "available_agents": ["xiaona", "xiaonuo"],
            }

            async with session.post(
                f"{gateway_url}/api/v1/legal/planner/plan", json=plan_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("success", False):
                        print(f"❌ 计划生成失败: {data.get('detail', 'Unknown error')}")
                    else:
                        print("✅ 计划生成成功")
                        plan_result = data.get("data", {})
                        execution_plan = plan_result.get("execution_plan", {})
                        print(f"📋 规划步骤数: {len(execution_plan.get('steps', []))}")
                        print(f"🎯 目标: {plan_result.get('goal', '')}")
                else:
                    print(f"❌ 计划生成请求失败: {response.status}")

            print("\n🏆 法律世界模型API测试完成！")

        except Exception as e:
            print(f"❌ 测试失败: {e}")


if __name__ == "__main__":
    asyncio.run(test_legal_world_model())
