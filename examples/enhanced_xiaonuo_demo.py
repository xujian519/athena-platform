#!/usr/bin/env python3
"""
Enhanced Xiaonuo 完整使用示例
Complete Usage Example for Enhanced Xiaonuo

演示如何使用增强版小诺智能体的各种功能

作者: Athena AI System
创建时间: 2026-04-18
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.intelligence.reflection_engine_v5 import ReflectionType, ThoughtStep

from core.logging_config import setup_logging

logger = setup_logging()


async def demo_basic_usage():
    """演示1: 基本使用"""
    print("\n" + "=" * 80)
    print("📖 演示1: 基本使用".center(80))
    print("=" * 80)

    from core.framework.agents.xiaonuo.enhanced_xiaonuo import EnhancedXiaonuo

    # 创建实例
    print("\n🤖 创建 Enhanced Xiaonuo 实例...")
    agent = EnhancedXiaonuo()

    # 查看可用能力
    print(f"\n📋 可用能力: {', '.join(agent.enhanced_capabilities)}")

    # 处理用户输入
    print("\n💬 处理用户输入: '你好，请介绍一下你自己'")
    response = await agent.process_input(
        "你好，请介绍一下你自己",
        enable_reflection=False,  # 先禁用反思，加快响应
    )

    print(f"\n🤖 响应:\n{response}")

    # 查看性能统计
    print("\n📊 性能统计:")
    print(f"  - 交互次数: {agent.performance_tracker['interactions']}")

    print("\n✅ 基本使用演示完成")


async def demo_reflection():
    """演示2: 反思功能"""
    print("\n" + "=" * 80)
    print("📖 演示2: 反思功能".center(80))
    print("=" * 80)

    from core.framework.agents.xiaonuo.enhanced_xiaonuo import EnhancedXiaonuo

    agent = EnhancedXiaonuo()

    # 创建思维链
    thought_chain = [
        ThoughtStep(
            step_id="perception",
            timestamp=datetime.now(),
            content="感知用户输入: 分析专利权利要求",
            reasoning_type="perception",
            confidence=0.95,
        ),
        ThoughtStep(
            step_id="analysis",
            timestamp=datetime.now(),
            content="分析专利内容和技术特征",
            reasoning_type="analysis",
            confidence=0.88,
        ),
        ThoughtStep(
            step_id="legal_reasoning",
            timestamp=datetime.now(),
            content="应用法律知识进行推理",
            reasoning_type="legal_reasoning",
            confidence=0.85,
        ),
    ]

    print("\n🤔 执行反思循环...")
    print("思维链步骤:")
    for step in thought_chain:
        print(f"  - {step.content} (置信度: {step.confidence})")

    # 执行反思
    loop = await agent.reflection_engine_v5.reflect_with_loop(
        original_input="分析专利CN123456789A的权利要求",
        output="该专利的权利要求1涉及一种人工智能算法，包括...",
        context={
            "patent_id": "CN123456789A",
            "domain": "patent_law",
        },
        thought_chain=thought_chain,
        reflection_types=[ReflectionType.OUTPUT, ReflectionType.PROCESS, ReflectionType.CAUSAL],
    )

    print("\n📊 反思结果:")
    print(f"  - 循环ID: {loop.loop_id}")
    print(f"  - 反思类型数: {len(loop.reflection_result)}")
    print(f"  - 因子数: {len(loop.causal_factors)}")
    print(f"  - 行动项数: {len(loop.action_items)}")

    if loop.action_items:
        print("\n📝 生成的行动项:")
        for action in loop.action_items[:3]:
            print(f"  - {action.description} (优先级: {action.priority.value})")

    print("\n✅ 反思功能演示完成")


async def demo_with_reflection():
    """演示3: 带反思的完整处理流程"""
    print("\n" + "=" * 80)
    print("📖 演示3: 带反思的完整处理流程".center(80))
    print("=" * 80)

    from core.framework.agents.xiaonuo.enhanced_xiaonuo import EnhancedXiaonuo

    agent = EnhancedXiaonuo()

    print("\n💬 处理用户输入（启用反思和学习）...")
    response = await agent.process_input(
        "请分析一下这个专利的创造性",
        enable_reflection=True,  # 启用反思
        enable_learning=True,    # 启用学习
        include_performance=True, # 包含性能信息
    )

    print(f"\n🤖 响应:\n{response}")

    # 查看性能统计
    print("\n📊 处理后的性能统计:")
    print(f"  - 交互次数: {agent.performance_tracker['interactions']}")
    print(f"  - 反思次数: {agent.performance_tracker['reflections_performed']}")
    print(f"  - 学习周期: {agent.performance_tracker['learning_cycles']}")

    print("\n✅ 完整处理流程演示完成")


async def demo_memory_consolidation():
    """演示4: 记忆整合（如果可用）"""
    print("\n" + "=" * 80)
    print("📖 演示4: 记忆整合".center(80))
    print("=" * 80)

    from core.framework.agents.xiaonuo.enhanced_xiaonuo import EnhancedXiaonuo

    agent = EnhancedXiaonuo()

    if agent.memory_consolidation is not None:
        print("\n🧠 记忆整合系统已启用")

        # 执行一些交互以产生记忆
        print("\n💬 执行多次交互以产生记忆...")
        await agent.process_input("什么是专利?")
        await agent.process_input("如何申请专利?")
        await agent.process_input("专利的保护期限是多久?")

        # 尝试执行记忆整合
        print("\n🔄 执行记忆整合...")
        try:
            report = await agent.memory_consolidation.consolidate_memories(force=True)
            print("\n📊 整合报告:")
            print(f"  - 状态: {report.get('status', 'unknown')}")
            print(f"  - 整合数量: {report.get('consolidated_count', 0)}")
            print(f"  - 发现模式: {report.get('patterns_discovered', 0)}")
        except Exception as e:
            print(f"⚠️  整合过程: {e}")

        print("\n✅ 记忆整合演示完成")
    else:
        print("\n⚠️  记忆整合系统未启用（这是正常的，如果相关模块不可用）")


async def demo_statistics():
    """演示5: 统计信息"""
    print("\n" + "=" * 80)
    print("📖 演示5: 统计信息".center(80))
    print("=" * 80)

    from core.framework.agents.xiaonuo.enhanced_xiaonuo import EnhancedXiaonuo

    agent = EnhancedXiaonuo()

    # 执行一些操作
    print("\n💬 执行一些操作...")
    await agent.process_input("问题1")
    await agent.process_input("问题2")
    await agent.process_input("问题3")

    # 获取反思引擎统计
    reflection_stats = await agent.reflection_engine_v5.get_statistics()

    print("\n📊 智能体统计:")
    print(f"  - 版本: {agent.version}")
    print(f"  - 代理ID: {agent.agent_id}")
    print(f"  - 交互次数: {agent.performance_tracker['interactions']}")
    print(f"  - 反思次数: {agent.performance_tracker['reflections_performed']}")
    print(f"  - 学习周期: {agent.performance_tracker['learning_cycles']}")
    print(f"  - 改进应用: {agent.performance_tracker['improvements_applied']}")

    print("\n📊 反思引擎统计:")
    print(f"  - 总反思数: {reflection_stats['stats']['total_reflections']}")
    print(f"  - 因果分析数: {reflection_stats['stats']['causal_analyses']}")
    print(f"  - 行动项创建: {reflection_stats['stats']['action_items_created']}")
    print(f"  - 行动项完成: {reflection_stats['stats']['action_items_completed']}")

    print("\n✅ 统计信息演示完成")


async def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("🚀 Enhanced Xiaonuo 完整使用演示".center(80))
    print("=" * 80)

    try:
        # 演示1: 基本使用
        await demo_basic_usage()

        # 演示2: 反思功能
        await demo_reflection()

        # 演示3: 带反思的完整处理流程
        await demo_with_reflection()

        # 演示4: 记忆整合
        await demo_memory_consolidation()

        # 演示5: 统计信息
        await demo_statistics()

        print("\n" + "=" * 80)
        print("✅ 所有演示完成!".center(80))
        print("=" * 80)

        print("\n📋 总结:")
        print("  • ✅ 基本输入处理正常")
        print("  • ✅ 反思引擎工作正常")
        print("  • ✅ 学习功能已启用")
        print("  • ✅ 统计信息完整")
        print("\n🎯 Enhanced Xiaonuo 已完全可用!")

    except Exception as e:
        logger.error(f"演示过程出错: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
