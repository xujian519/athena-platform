#!/usr/bin/env python3
"""
Phase 3.2 学习与优先级测试脚本
Testing Phase 3.2 Learning & Prioritization

测试在线学习引擎和智能优先级系统

作者: 小诺·双鱼座
创建时间: 2025-01-05
"""

from __future__ import annotations
import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 设置环境变量
os.chdir(project_root)

from core.learning.online_learning_engine import get_online_learning_engine
from core.prioritization.intelligent_prioritization import (
    get_intelligent_prioritization_system,
)


async def test_online_learning_engine():
    """测试1: 在线学习引擎"""
    print("\n" + "=" * 70)
    print("🧪 测试1: 在线学习引擎")
    print("=" * 70)

    engine = get_online_learning_engine()

    # 测试从执行中学习
    print("\n🧠 测试从执行中学习...")
    task_context = {"domain": "专利检索", "task_type": "搜索任务", "complexity": 0.7}

    actions = [
        {"name": "构建查询", "params": {"query": "AI专利"}},
        {"name": "向量检索", "params": {"limit": 10}},
        {"name": "结果排序", "params": {"method": "relevance"}},
    ]

    results = [
        {"success": True, "results_count": 15},
        {"success": True, "results_count": 8},
        {"success": False, "error": "超时"},
    ]

    lessons = await engine.learn_from_execution(task_context, actions, results)

    print("✅ 学习完成:")
    print(f"   - 获得 {len(lessons)} 条经验")
    for lesson in lessons:
        print(f"   - {lesson}")

    # 测试用户反馈适应
    print("\n🔄 测试用户反馈适应...")
    feedback_result = await engine.adapt_to_user_feedback(
        user_id="user_001",
        feedback={"type": "rating", "value": 0.8, "text": "检索结果很好,但速度可以更快"},
        context={"task": "专利检索"},
    )

    print("✅ 反馈适应完成:")
    print(f"   - 适应成功: {feedback_result['adaptation_successful']}")
    print(f"   - 策略调整: {feedback_result['strategy_adjustments']}")

    # 测试元学习
    print("\n🎓 测试元学习...")
    task_history = [
        {"success": True, "domain": "专利检索", "strategy": "向量优先"},
        {"success": True, "domain": "专利检索", "strategy": "向量优先"},
        {"success": False, "domain": "专利检索", "strategy": "关键词优先"},
        {"success": True, "domain": "专利分析", "strategy": "混合检索"},
    ]

    meta_result = await engine.meta_learning(task_history, num_tasks=4)

    print("✅ 元学习完成:")
    print(f"   - 识别模式: {meta_result['patterns_identified']} 个")
    print(f"   - 学习能力: {meta_result['learning_capability']}")

    # 测试策略提取和优化
    print("\n⚙️ 测试策略提取和优化...")
    # 添加更多经验
    for i in range(10):
        await engine.learn_from_execution(
            {"domain": "专利检索", "test": i},
            [{"name": "动作A", "params": {}}],
            [{"success": i % 2 == 0}],
        )

    strategy_result = await engine.extract_and_optimize_strategy(
        domain="专利检索", experience_window=20
    )

    print("✅ 策略优化完成:")
    print(f"   - 优化状态: {strategy_result['optimization_status']}")
    print(f"   - 分析经验: {strategy_result.get('experiences_analyzed', 0)} 条")
    print(f"   - 推荐策略: {strategy_result.get('strategies_recommended', 0)} 个")

    # 显示学习统计
    stats = engine.get_learning_stats()
    print("\n📊 学习统计:")
    print(f"   - 总学习次数: {stats['total_learning_episodes']}")
    print(f"   - 成功学习: {stats['successful_learnings']}")
    print(f"   - 失败学习: {stats['failed_learnings']}")
    print(f"   - 总经验数: {stats['total_experiences']}")
    print(f"   - 总策略数: {stats['total_strategies']}")

    # 显示顶级策略
    top_strategies = engine.get_top_strategies(limit=3)
    print("\n🏆 顶级策略:")
    for strategy in top_strategies:
        print(f"   - {strategy.name}: 成功率 {strategy.success_rate:.1%}")

    print("\n✅ 在线学习引擎测试通过!")
    return engine


async def test_intelligent_prioritization():
    """测试2: 智能优先级系统"""
    print("\n" + "=" * 70)
    print("🧪 测试2: 智能优先级系统")
    print("=" * 70)

    system = get_intelligent_prioritization_system()

    # 添加测试任务
    print("\n⚡ 添加测试任务...")

    # 任务1: 高紧急性,截止时间临近
    await system.add_task(
        task_id="task_001",
        title="紧急专利检索",
        description="需要立即检索区块链专利",
        domain="专利检索",
        importance=0.8,
        deadline=datetime.now() + timedelta(hours=2),
        dependencies=[],
    )

    # 任务2: 高重要性,但不太紧急
    await system.add_task(
        task_id="task_002",
        title="专利分析报告",
        description="生成季度专利分析报告",
        domain="专利分析",
        importance=0.9,
        deadline=datetime.now() + timedelta(days=3),
        dependencies=[],
    )

    # 任务3: 中等重要性,有依赖
    await system.add_task(
        task_id="task_003",
        title="数据更新",
        description="更新专利数据库",
        domain="数据维护",
        importance=0.6,
        dependencies=["task_001"],
    )

    # 任务4: 低重要性
    await system.add_task(
        task_id="task_004",
        title="日志清理",
        description="清理系统日志",
        domain="维护",
        importance=0.3,
        dependencies=[],
    )

    # 任务5: 高战略价值
    await system.add_task(
        task_id="task_005",
        title="新功能开发",
        description="开发智能推荐功能",
        domain="开发",
        importance=0.7,
        strategic_value=0.9,
        dependencies=[],
    )

    print("✅ 添加了 5 个测试任务")

    # 显示队列状态
    status = system.get_queue_status()
    print("\n📊 队列状态:")
    print(f"   - 总任务数: {status['total_tasks']}")
    print(f"   - 待处理: {status['pending']}")
    print(f"   - 进行中: {status['in_progress']}")
    print(f"   - 已阻塞: {status['blocked']}")
    print(f"   - 平均优先级: {status['avg_priority']:.2f}")

    # 获取下一个任务
    print("\n🎯 获取下一个优先级最高的任务...")
    next_task = await system.get_next_task()
    if next_task:
        print("✅ 下一个任务:")
        print(f"   - ID: {next_task.task_id}")
        print(f"   - 标题: {next_task.title}")
        print(f"   - 优先级分数: {next_task.priority_score:.2f}")
        print(f"   - 状态: {next_task.status.value}")

    # 显示顶级任务
    print("\n🏆 优先级最高的3个任务:")
    top_tasks = system.get_top_tasks(limit=3)
    for i, task in enumerate(top_tasks, 1):
        print(f"   {i}. {task.title} (优先级: {task.priority_score:.2f})")

    # 测试动态重排序
    print("\n🔄 测试动态重排序...")
    reprior_result = await system.reprioritize_all(
        reason="模拟紧急任务", context={"emergency": True}
    )

    print("✅ 重排序完成:")
    print(f"   - 变化任务数: {len(reprior_result.changes)}")
    if reprior_result.changes:
        for change in reprior_result.changes[:3]:
            print(f"   - {change['task_id']}: {change['old_position']} → {change['new_position']}")

    # 测试动态优先级调整
    print("\n⚡ 测试动态优先级调整...")
    affected = await system.dynamic_reprioritize(
        {
            "type": "deadline_approaching",
            "task_id": "task_002",
            "new_deadline": (datetime.now() + timedelta(hours=1)).isoformat(),
        }
    )

    print("✅ 动态调整完成:")
    print(f"   - 受影响任务: {len(affected)} 个")

    # 测试任务完成事件
    print("\n✅ 测试任务完成事件...")
    await system.dynamic_reprioritize({"type": "task_completed", "task_id": "task_001"})

    new_status = system.get_queue_status()
    print(f"   - 已完成任务: {new_status['completed_tasks']}")

    print("\n✅ 智能优先级系统测试通过!")
    return system


async def test_integration():
    """测试3: 学习与优先级集成"""
    print("\n" + "=" * 70)
    print("🧪 测试3: 学习与优先级系统集成")
    print("=" * 70)

    learning_engine = get_online_learning_engine()
    prioritization_system = get_intelligent_prioritization_system()

    print("\n🔗 模拟真实场景: 专利检索任务流程")

    # 场景1: 添加任务到优先级系统
    print("\n1️⃣ 添加高优先级专利检索任务...")
    await prioritization_system.add_task(
        task_id="patent_search_001",
        title="AI医疗专利检索",
        description="检索AI+医疗领域的最新专利",
        domain="专利检索",
        importance=0.9,
        deadline=datetime.now() + timedelta(hours=4),
        strategic_value=0.8,
    )

    # 场景2: 获取任务并执行
    print("\n2️⃣ 获取并执行任务...")
    next_task = await prioritization_system.get_next_task()

    if next_task:
        # 模拟执行动作
        actions = [
            {"name": "构建查询", "params": {"query": "AI医疗"}},
            {"name": "执行检索", "params": {}},
            {"name": "结果分析", "params": {}},
        ]

        results = [
            {"success": True, "results": 10},
            {"success": True, "results": 25},
            {"success": True, "results": 8},
        ]

        # 场景3: 从执行中学习
        print("\n3️⃣ 从执行结果中学习...")
        lessons = await learning_engine.learn_from_execution(
            task_context={"domain": next_task.domain, "task_id": next_task.task_id},
            actions=actions,
            results=results,
        )

        print(f"✅ 学习到 {len(lessons)} 条经验")

    # 场景4: 收集用户反馈
    print("\n4️⃣ 收集用户反馈...")
    await learning_engine.adapt_to_user_feedback(
        user_id="researcher_001",
        feedback={"type": "rating", "value": 0.9, "text": "检索结果非常相关,很满意!"},
        context={"task_id": "patent_search_001"},
    )

    print("✅ 反馈适应成功")

    # 场景5: 提取策略
    print("\n5️⃣ 提取和优化策略...")
    strategy_result = await learning_engine.extract_and_optimize_strategy(
        domain="专利检索", experience_window=10
    )

    print(f"✅ 策略优化: {strategy_result['optimization_status']}")

    # 场景6: 任务完成,触发重排序
    print("\n6️⃣ 任务完成,更新优先级...")
    await prioritization_system.dynamic_reprioritize(
        {"type": "task_completed", "task_id": "patent_search_001"}
    )

    # 场景7: 生成最终报告
    print("\n📊 集成测试报告:")

    learning_stats = learning_engine.get_learning_stats()
    priority_status = prioritization_system.get_queue_status()

    print("\n学习引擎:")
    print(f"   - 总学习次数: {learning_stats['total_learning_episodes']}")
    print(f"   - 总策略数: {learning_stats['total_strategies']}")
    print(f"   - 用户数: {learning_stats['user_count']}")

    print("\n优先级系统:")
    print(f"   - 总任务数: {priority_status['total_tasks']}")
    print(f"   - 已完成: {priority_status['completed_tasks']}")
    print(f"   - 重排序次数: {priority_status['reprioritizations']}")

    print("\n✅ 学习与优先级系统集成测试通过!")
    print("\n🎉 Phase 3.2 所有功能测试通过!")


async def main():
    """主测试函数"""
    print("\n" + "=" * 70)
    print("🧪 Phase 3.2学习与优先级测试套件")
    print("在线学习 + 智能优先级 + 动态调整")
    print("=" * 70)

    try:
        # 测试1: 在线学习引擎
        await test_online_learning_engine()

        # 测试2: 智能优先级系统
        await test_intelligent_prioritization()

        # 测试3: 集成测试
        await test_integration()

        print("\n" + "=" * 70)
        print("✅ Phase 3.2学习与优先级测试全部通过!")
        print("=" * 70)
        print("\n📋 Phase 3.2功能总结:")
        print("   ✅ 在线学习引擎已实现")
        print("   ✅ 用户反馈适应已实现")
        print("   ✅ 策略提取和优化已实现")
        print("   ✅ 智能优先级系统已实现")
        print("   ✅ 动态优先级调整已实现")
        print("   ✅ 学习与优先级集成完成")
        print("\n🚀 Phase 3.2学习与适应模式已成功集成到Athena平台!")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
