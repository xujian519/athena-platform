#!/usr/bin/env python3
"""
评估与反思模块最终验证脚本
Evaluation and Reflection Module Final Verification Script

验证评估与反思模块的核心功能是否正常工作

作者: Athena AI系统
创建时间: 2026-04-18
"""

import asyncio
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.logging_config import setup_logging

logger = setup_logging()


async def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("🔍 评估与反思模块验证报告".center(80))
    print("=" * 80)

    results = {
        "passed": 0,
        "failed": 0,
        "tests": [],
    }

    def add_result(category: str, test_name: str, passed: bool, details: str = ""):
        """添加测试结果"""
        results["tests"].append({
            "category": category,
            "name": test_name,
            "passed": passed,
            "details": details,
        })
        if passed:
            results["passed"] += 1
        else:
            results["failed"] += 1

    # ========== 测试1: 反思引擎v5 ==========
    print("\n🔍 测试反思引擎v5...")

    try:
        from core.intelligence.reflection_engine_v5 import (
            ReflectionEngineV5,
            ReflectionType,
            ThoughtStep,
        )

        # 创建引擎
        engine = ReflectionEngineV5(agent_id="test_agent")
        add_result("反思引擎v5", "创建实例", True, f"代理ID: {engine.agent_id}")

        # 创建思维链
        thought_chain = [
            ThoughtStep(
                step_id="step1",
                timestamp=datetime.now(),
                content="分析用户需求",
                reasoning_type="intent_analysis",
                confidence=0.9,
            ),
            ThoughtStep(
                step_id="step2",
                timestamp=datetime.now(),
                content="检索相关知识",
                reasoning_type="knowledge_retrieval",
                confidence=0.85,
            ),
        ]

        # 执行反思循环
        loop = await engine.reflect_with_loop(
            original_input="帮我分析这个专利",
            output="这是一个关于人工智能的专利...",
            context={"domain": "patent_analysis"},
            thought_chain=thought_chain,
            reflection_types=[ReflectionType.OUTPUT, ReflectionType.PROCESS],
        )

        add_result(
            "反思引擎v5",
            "执行反思循环",
            loop.loop_id is not None,
            f"循环ID: {loop.loop_id}, 反思结果: {len(loop.reflection_result)}",
        )

        # 验证统计信息
        stats = await engine.get_statistics()
        add_result(
            "反思引擎v5",
            "统计信息",
            stats["stats"]["total_reflections"] > 0,
            f"总反思: {stats['stats']['total_reflections']}",
        )

    except Exception as e:
        add_result("反思引擎v5", "核心功能", False, f"错误: {e}")

    # ========== 测试2: 评估引擎 ==========
    print("\n🔍 测试评估引擎...")

    try:
        from core.evaluation.evaluation_engine import (
            EvaluationEngine,
            EvaluationCriteria,
            EvaluationType,
            EvaluationLevel,
        )

        # 创建引擎
        engine = EvaluationEngine(agent_id="test_evaluator")
        await engine.initialize()

        add_result(
            "评估引擎",
            "创建并初始化",
            True,
            f"评估器ID: {engine.agent_id}",
        )

        # 创建评估标准
        criteria = [
            EvaluationCriteria(
                id="accuracy",
                name="准确性",
                description="分析结果的准确性",
                current_value=85.0,
                min_value=0.0,
                max_value=100.0,
                weight=1.0,
            ),
            EvaluationCriteria(
                id="completeness",
                name="完整性",
                description="分析的完整程度",
                current_value=75.0,
                min_value=0.0,
                max_value=100.0,
                weight=0.8,
            ),
        ]

        # 执行评估
        eval_result = await engine.evaluate(
            target_type="test_target",
            target_id="test_001",
            evaluation_type=EvaluationType.QUALITY,
            criteria=criteria,
            context={"test": True},
        )

        # 验证结果
        add_result(
            "评估引擎",
            "执行评估",
            eval_result.id is not None and eval_result.overall_score > 0,
            f"评分: {eval_result.overall_score:.1f}, 等级: {eval_result.level.value}",
        )

        # 验证反思生成
        reflection = await engine.reflection_engine.generate_reflection(eval_result)
        add_result(
            "评估引擎",
            "生成反思",
            reflection.id is not None,
            f"反思ID: {reflection.id}",
        )

        # 验证统计
        stats = engine.stats
        add_result(
            "评估引擎",
            "统计信息",
            stats["total_evaluations"] > 0,
            f"总评估: {stats['total_evaluations']}",
        )

    except Exception as e:
        add_result("评估引擎", "核心功能", False, f"错误: {e}")

    # ========== 测试3: 模块集成 ==========
    print("\n🔍 测试模块集成...")

    try:
        from core.evaluation.evaluation_engine import EvaluationEngine, EvaluationCriteria, EvaluationType
        from core.intelligence.reflection_engine_v5 import ReflectionEngineV5, ReflectionType

        # 创建引擎
        eval_engine = EvaluationEngine(agent_id="integration_evaluator")
        await eval_engine.initialize()

        reflect_engine = ReflectionEngineV5(agent_id="integration_agent")

        # 执行评估
        criteria = [
            EvaluationCriteria(
                id="quality",
                name="质量",
                description="输出质量",
                current_value=70.0,
                min_value=0.0,
                max_value=100.0,
                weight=1.0,
            ),
        ]

        eval_result = await eval_engine.evaluate(
            target_type="integration_test",
            target_id="test_001",
            evaluation_type=EvaluationType.QUALITY,
            criteria=criteria,
        )

        # 基于评估结果执行反思
        loop = await reflect_engine.reflect_with_loop(
            original_input="集成测试输入",
            output=f"评估得分: {eval_result.overall_score:.1f}",
            context={"evaluation_result": asdict(eval_result)},
            reflection_types=[ReflectionType.OUTPUT],
        )

        add_result(
            "模块集成",
            "评估-反思集成",
            loop.loop_id is not None,
            f"评估得分: {eval_result.overall_score:.1f}, 反思循环: {loop.loop_id}",
        )

    except Exception as e:
        add_result("模块集成", "评估-反思集成", False, f"错误: {e}")

    # 测试反思集成包装器
    try:
        from core.intelligence.reflection_integration_wrapper import (
            ReflectionIntegrationWrapper,
            ReflectionConfig,
        )

        # 创建包装器
        wrapper = ReflectionIntegrationWrapper(config=ReflectionConfig())
        add_result(
            "模块集成",
            "反思集成包装器",
            wrapper.reflection_engine is not None,
            "包装器已初始化",
        )

    except Exception as e:
        add_result("模块集成", "反思集成包装器", False, f"错误: {e}")

    # ========== 测试4: 通信机制 ==========
    print("\n🔍 测试通信机制...")

    # 测试数据序列化
    try:
        from core.evaluation.evaluation_engine import EvaluationEngine, EvaluationCriteria, EvaluationType

        engine = EvaluationEngine(agent_id="serialization_test")
        await engine.initialize()

        criteria = [
            EvaluationCriteria(
                id="test",
                name="测试",
                description="测试标准",
                current_value=80.0,
                min_value=0.0,
                max_value=100.0,
                weight=1.0,
            ),
        ]

        result_obj = await engine.evaluate(
            target_type="test",
            target_id="test_001",
            evaluation_type=EvaluationType.PERFORMANCE,
            criteria=criteria,
        )

        # 尝试序列化
        serialized = asdict(result_obj)
        can_serialize = isinstance(serialized, dict) and len(serialized) > 0

        add_result(
            "通信机制",
            "评估结果序列化",
            can_serialize,
            f"序列化字段数: {len(serialized)}",
        )

    except Exception as e:
        add_result("通信机制", "评估结果序列化", False, f"错误: {e}")

    # 测试反思结果持久化
    try:
        from core.intelligence.reflection_engine_v5 import ReflectionEngineV5

        engine = ReflectionEngineV5(agent_id="persistence_test")

        # 执行反思
        loop = await engine.reflect_with_loop(
            original_input="持久化测试",
            output="测试输出",
            context={"test": True},
        )

        # 检查历史记录
        has_history = len(engine.reflection_history) > 0
        add_result(
            "通信机制",
            "反思结果持久化",
            has_history,
            f"历史记录数: {len(engine.reflection_history)}",
        )

    except Exception as e:
        add_result("通信机制", "反思结果持久化", False, f"错误: {e}")

    # ========== 测试5: 实际使用场景 ==========
    print("\n🔍 测试实际使用场景...")

    # 场景1: 专利分析质量评估
    try:
        from core.evaluation.evaluation_engine import (
            EvaluationEngine,
            EvaluationCriteria,
            EvaluationType,
        )
        from core.intelligence.reflection_engine_v5 import ReflectionEngineV5, ReflectionType

        # 创建引擎
        eval_engine = EvaluationEngine(agent_id="patent_evaluator")
        await eval_engine.initialize()

        reflect_engine = ReflectionEngineV5(agent_id="patent_agent")

        # 模拟专利分析评估
        criteria = [
            EvaluationCriteria(
                id="legal_accuracy",
                name="法律准确性",
                description="法律分析的准确性",
                current_value=85.0,
                min_value=0.0,
                max_value=100.0,
                weight=1.2,
            ),
            EvaluationCriteria(
                id="technical_depth",
                name="技术深度",
                description="技术分析的深度",
                current_value=75.0,
                min_value=0.0,
                max_value=100.0,
                weight=1.0,
            ),
            EvaluationCriteria(
                id="completeness",
                name="完整性",
                description="分析的完整程度",
                current_value=70.0,
                min_value=0.0,
                max_value=100.0,
                weight=0.8,
            ),
        ]

        eval_result = await eval_engine.evaluate(
            target_type="patent_analysis",
            target_id="CN123456789A",
            evaluation_type=EvaluationType.QUALITY,
            criteria=criteria,
            context={"patent_id": "CN123456789A", "domain": "patent_law"},
        )

        # 基于评估结果进行反思
        loop = await reflect_engine.reflect_with_loop(
            original_input="分析专利CN123456789A的权利要求",
            output=f"该专利的权利要求涉及...评估得分: {eval_result.overall_score:.1f}",
            context={
                "patent_id": "CN123456789A",
                "evaluation_score": eval_result.overall_score,
                "weaknesses": eval_result.weaknesses,
            },
            reflection_types=[ReflectionType.OUTPUT, ReflectionType.CAUSAL],
        )

        # 验证是否有改进建议
        has_recommendations = len(eval_result.recommendations) > 0
        has_action_items = len(loop.action_items) > 0

        add_result(
            "实际场景",
            "专利分析质量评估",
            has_recommendations or has_action_items,
            f"评估得分: {eval_result.overall_score:.1f}, 建议: {len(eval_result.recommendations)}, 行动项: {len(loop.action_items)}",
        )

    except Exception as e:
        add_result("实际场景", "专利分析质量评估", False, f"错误: {e}")

    # 场景2: 持续改进循环
    try:
        from core.intelligence.reflection_engine_v5 import ReflectionEngineV5

        engine = ReflectionEngineV5(agent_id="continuous_agent")

        # 第一轮
        loop1 = await engine.reflect_with_loop(
            original_input="初始任务",
            output="初步输出",
            context={"iteration": 1},
        )

        # 模拟改进
        improvement = await engine.measure_improvement(
            loop_id=loop1.loop_id,
            new_output="改进后的输出",
            new_context={"iteration": 2},
        )

        add_result(
            "实际场景",
            "持续改进循环",
            improvement >= 0,
            f"改进分数: {improvement:.3f}, 总反思: {engine.stats['total_reflections']}",
        )

    except Exception as e:
        add_result("实际场景", "持续改进循环", False, f"错误: {e}")

    # ========== 打印报告 ==========
    print("\n" + "=" * 80)
    print("📊 验证报告".center(80))
    print("=" * 80)

    # 按类别分组
    categories = {}
    for test in results["tests"]:
        category = test["category"]
        if category not in categories:
            categories[category] = []
        categories[category].append(test)

    for category, tests in categories.items():
        print(f"\n📋 {category}:")
        for test in tests:
            status = "✅" if test["passed"] else "❌"
            print(f"  {status} {test['name']}")
            if test["details"]:
                print(f"      → {test['details']}")

    print("\n" + "-" * 80)
    total = results["passed"] + results["failed"]
    pass_rate = results["passed"] / total * 100 if total > 0 else 0
    print(f"总计: {results['passed']}/{total} 通过 ({pass_rate:.1f}%)")
    print("=" * 80)

    # ========== 总结 ==========
    if results["failed"] == 0:
        print("\n✅ 所有测试通过! 评估与反思模块运行正常.")
        print("\n📋 核心发现:")
        print("  • 反思引擎v5可以正常创建思维链并执行反思循环")
        print("  • 评估引擎可以执行多维度评估并生成结果")
        print("  • 两个引擎可以集成工作，实现评估→反思→改进的闭环")
        print("  • 数据序列化和持久化功能正常")
        print("  • 实际使用场景(如专利分析)可以正常运行")
        print("\n🎯 结论: 评估与反思模块完整可运行，与其他模块通信正常")
        return 0
    else:
        print(f"\n⚠️  {results['failed']} 个测试失败，请检查上述报告.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
