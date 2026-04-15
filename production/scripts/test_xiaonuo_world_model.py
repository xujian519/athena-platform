#!/usr/bin/env python3
"""
小诺世界模型集成测试脚本
Test script for Xiaonuo World Model integration

测试小诺智能体的世界模型查询功能
"""

from __future__ import annotations
import asyncio
import logging
import os

# 使用当前工作目录作为项目根目录
import sys

PROJECT_ROOT = os.getcwd()
sys.path.insert(0, PROJECT_ROOT)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_xiaonuo_world_model():
    """测试小诺的世界模型功能"""
    print("=" * 70)
    print("🧪 测试小诺智能体 - 世界模型集成")
    print("=" * 70)

    try:
        # 导入小诺智能体
        from core.agent.xiaonuo_agent import XiaonuoAgent

        # 创建配置,启用世界模型
        config = {
            "name": "小诺",
            "world_model_enabled": True,
            "world_model_config": {
                "enabled": True,
                "access_level": "read",
                "allowed_graph_types": ["legal_rules", "patent_guideline"],
                "cache_enabled": True,
                "fallback_to_local": True,
            }
        }

        # 创建小诺智能体
        xiaonuo = XiaonuoAgent(config)
        print("\n📦 创建小诺智能体成功")

        # 初始化智能体
        print("\n🚀 初始化小诺智能体...")
        await xiaonuo.initialize()
        print("✅ 小诺初始化完成")

        # 测试1: 处理普通消息
        print("\n" + "=" * 70)
        print("📝 测试1: 处理普通消息")
        print("=" * 70)
        result1 = await xiaonuo.process_input("爸爸你好!")
        print(f"结果: {result1.get('xiaonuo_emotional_response', {})}")

        # 测试2: 法条查询
        print("\n" + "=" * 70)
        print("📝 测试2: 法条查询 (世界模型)")
        print("=" * 70)
        result2 = await xiaonuo.process_input("请查询专利法第22条第1款")
        if "world_model_enhancement" in result2:
            print("✅ 世界模型增强已触发")
            print(f"类型: {result2['world_model_enhancement'].get('type')}")
            print(f"来源: {result2['world_model_enhancement'].get('source')}")
        else:
            print("⚠️ 世界模型未触发 (可能服务未启动)")

        # 测试3: 语义搜索
        print("\n" + "=" * 70)
        print("📝 测试3: 语义搜索 (世界模型)")
        print("=" * 70)
        result3 = await xiaonuo.process_input("搜索关于外观设计相同的案例")
        if "world_model_enhancement" in result3:
            print("✅ 世界模型增强已触发")
            print(f"类型: {result3['world_model_enhancement'].get('type')}")
        else:
            print("⚠️ 世界模型未触发 (可能服务未启动)")

        # 测试4: 直接查询法条
        print("\n" + "=" * 70)
        print("📝 测试4: 直接调用世界模型API")
        print("=" * 70)
        legal_result = await xiaonuo.query_legal_article("专利法第23条")
        print(f"查询结果: success={legal_result.get('success')}")
        if legal_result.get('success'):
            print(f"数据: {legal_result.get('data')}")
            print(f"来源: {legal_result.get('source')}")
            print(f"缓存: {legal_result.get('cached')}")
            print(f"延迟: {legal_result.get('latency_ms')}ms")

        # 获取世界模型统计信息
        if xiaonuo.knowledge_adapter:
            stats = xiaonuo.knowledge_adapter.get_statistics()
            print("\n" + "=" * 70)
            print("📊 世界模型统计信息")
            print("=" * 70)
            print(f"智能体: {stats['agent_name']}")
            print(f"启用状态: {stats['enabled']}")
            print(f"总查询数: {stats['statistics']['total_queries']}")
            print(f"缓存命中: {stats['statistics']['cache_hits']}")
            print(f"缓存命中率: {stats['statistics']['cache_hit_rate']}")

        print("\n✅ 测试完成!")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 清理资源
        print("\n🧹 清理资源...")
        if 'xiaonuo' in locals():
            await xiaonuo.shutdown()
        print("✅ 清理完成")


if __name__ == "__main__":
    asyncio.run(test_xiaonuo_world_model())
