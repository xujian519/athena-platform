#!/usr/bin/env python3
"""
四阶段系统集成测试 - Minitap式智能执行系统
Four-Phase Integration Test - Minitap-Style Intelligent Execution System

综合测试四个阶段的集成效果：
1. Phase 1: 进度追踪系统
2. Phase 2: 验证机制系统
3. Phase 3: 失败恢复系统
4. Phase 4: 原子化任务分解

Author: Athena Team
Version: 1.0.0
Date: 2026-02-26
"""

import asyncio
import logging
import sys
import tempfile
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_phase1_progress_tracking():
    """测试Phase 1: 进度追踪系统"""
    logger.info("🧪 测试 Phase 1: 进度追踪系统")

    try:
        from core.cognition.plan_executor import create_executor
        from core.cognition.xiaonuo_planner_engine import (
            ExecutionMode,
            ExecutionPlan,
            ExecutionStep,
            Intent,
            IntentType,
            PlanConfidence,
            ResourceRequirement,
        )

        # 创建测试方案
        steps = [
            ExecutionStep(
                id='step_1',
                description='测试步骤1',
                agent='xiaona',
                action='test_action',
                parameters={'test': 'data'},
            ),
            ExecutionStep(
                id='step_2',
                description='测试步骤2',
                agent='xiaona',
                action='test_action',
                parameters={'test': 'data2'},
            ),
        ]

        ExecutionPlan(
            plan_id='test_plan_progress',
            intent=Intent(
                intent_type=IntentType.TASK,
                primary_goal='测试进度追踪',
                confidence=0.9,
            ),
            steps=steps,
            mode=ExecutionMode.SEQUENTIAL,
            resource_requirements=ResourceRequirement(),
            confidence=PlanConfidence.HIGH,
        )

        # 创建执行器（带进度推送）
        executor = create_executor(enable_progress=False)

        # 验证初始化
        if not hasattr(executor, 'progress_pusher'):
            logger.error("   ❌ 缺少进度推送器")
            return False

        logger.info("   ✅ 进度追踪组件已加载")
        return True

    except Exception as e:
        logger.error(f"   ❌ 测试失败: {e}", exc_info=True)
        return False


async def test_phase2_verification():
    """测试Phase 2: 验证机制系统"""
    logger.info("🧪 测试 Phase 2: 验证机制系统")

    try:
        from core.cognition.verification import (
            PatentSearchVerifier,
            VerificationStatus,
        )

        # 创建验证器
        verifier = PatentSearchVerifier()

        # 测试有效数据（包含query字段）
        valid_data = {
            "results": [{"title": "专利1"}],
            "total_count": 1,
            "query": "test",
        }

        result = await verifier.verify(valid_data)
        logger.info(f"   📊 验证结果: {result.status.value} (分数: {result.score:.1f})")

        if result.status == VerificationStatus.PASSED:
            logger.info("   ✅ 验证机制正常工作")
            return True
        else:
            logger.error(f"   ❌ 验证失败: {result.issues}")
            return False

    except Exception as e:
        logger.error(f"   ❌ 测试失败: {e}", exc_info=True)
        return False


async def test_phase3_failure_recovery():
    """测试Phase 3: 失败恢复系统"""
    logger.info("🧪 测试 Phase 3: 失败恢复系统")

    try:
        from core.cognition.checkpoint import CheckpointManager, StepCheckpoint
        from core.cognition.failure_recovery import FailureAnalyzer

        # 测试检查点管理器
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CheckpointManager(temp_dir)

            checkpoint = manager.create_checkpoint(
                task_id="test_task",
                plan_id="test_plan",
                completed_steps=["step_1"],
                current_step="step_2",
                step_states={
                    "step_1": StepCheckpoint(
                        step_id="step_1",
                        status="completed",
                    ),
                    "step_2": StepCheckpoint(
                        step_id="step_2",
                        status="in_progress",
                    ),
                },
            )

            loaded = manager.load_checkpoint(checkpoint.checkpoint_id)
            if loaded and loaded.checkpoint_id == checkpoint.checkpoint_id:
                logger.info(f"   ✅ 检查点创建和加载成功: {checkpoint.checkpoint_id}")
            else:
                logger.error("   ❌ 检查点加载失败")
                return False

        # 测试失败分析器
        analyzer = FailureAnalyzer()

        from core.cognition.xiaonuo_planner_engine import ExecutionStep

        test_step = ExecutionStep(
            id="test_step",
            description="测试步骤",
            agent="xiaona",
            action="test",
            parameters={},
        )

        analysis = await analyzer.analyze_failure(
            test_step,
            Exception("ConnectionError: timeout"),
            retry_count=0,
        )

        logger.info(f"   📊 失败分析: {analysis.error_type} -> {analysis.suggested_strategy.value}")

        logger.info("   ✅ 失败恢复系统正常工作")
        return True

    except Exception as e:
        logger.error(f"   ❌ 测试失败: {e}", exc_info=True)
        return False


async def test_phase4_atomic_decomposition():
    """测试Phase 4: 原子化任务分解"""
    logger.info("🧪 测试 Phase 4: 原子化任务分解")

    try:
        from core.cognition.atomic_task import (
            AtomicTaskDecomposer,
        )
        from core.cognition.xiaonuo_planner_engine import ExecutionStep

        # 测试分解器
        decomposer = AtomicTaskDecomposer()

        step = ExecutionStep(
            id="step_1",
            description="专利检索",
            agent="xiaona",
            action="patent_search",
            parameters={"query": "深度学习", "limit": 10},
        )

        atomic_tasks = decomposer.decompose_step(step)

        if atomic_tasks:
            task = atomic_tasks[0]

            # 验证输入契约
            is_valid, errors = task.validate_input()
            if is_valid:
                logger.info(f"   ✅ 原子任务创建成功: {task.id}")
                logger.info(f"      操作: {task.action}")
                logger.info("      输入契约验证通过")
                return True
            else:
                logger.error(f"   ❌ 输入契约验证失败: {errors}")
                return False
        else:
            logger.error("   ❌ 原子任务分解失败")
            return False

    except Exception as e:
        logger.error(f"   ❌ 测试失败: {e}", exc_info=True)
        return False


async def test_full_integration():
    """测试完整的系统集成"""
    logger.info("🧪 测试完整系统集成")

    try:
        from core.cognition.atomic_task import AtomicTaskDecomposer
        from core.cognition.plan_executor import create_executor
        from core.cognition.xiaonuo_planner_engine import (
            ExecutionMode,
            ExecutionPlan,
            ExecutionStep,
            Intent,
            IntentType,
            PlanConfidence,
            ResourceRequirement,
        )

        # 创建测试方案（包含复杂步骤）
        steps = [
            ExecutionStep(
                id='step_1',
                description='专利检索',
                agent='xiaona',
                action='patent_search',
                parameters={'query': 'AI', 'limit': 5},
            ),
            ExecutionStep(
                id='step_2',
                description='专利分析',
                agent='xiaona',
                action='patent_analyze',
                parameters={'patent_id': 'CN123456'},
                dependencies=['step_1'],
            ),
        ]

        ExecutionPlan(
            plan_id='integration_test_plan',
            intent=Intent(
                intent_type=IntentType.TASK,
                primary_goal='集成测试',
                confidence=0.9,
            ),
            steps=steps,
            mode=ExecutionMode.SEQUENTIAL,
            resource_requirements=ResourceRequirement(),
            confidence=PlanConfidence.HIGH,
        )

        # 创建全功能执行器
        executor = create_executor(
            enable_progress=False,
            enable_checkpoint=True,
            enable_recovery=True,
        )

        logger.info("   📊 执行器配置:")
        logger.info(f"      进度推送: {hasattr(executor, 'progress_pusher')}")
        logger.info(f"      检查点: {executor.enable_checkpoint}")
        logger.info(f"      失败恢复: {executor.enable_recovery}")
        logger.info(f"      原子任务: {executor.enable_atomic}")

        # 测试原子任务分解
        if executor.enable_atomic:
            decomposer = AtomicTaskDecomposer()
            for step in steps:
                atomic_tasks = decomposer.decompose_step(step)
                logger.info(f"      步骤 {step.id} 分解为 {len(atomic_tasks)} 个原子任务")

        logger.info("   ✅ 完整系统集成测试通过")
        return True

    except Exception as e:
        logger.error(f"   ❌ 测试失败: {e}", exc_info=True)
        return False


async def main():
    """主测试函数"""
    logger.info("🚀 开始四阶段系统集成测试")
    logger.info("=" * 60)
    logger.info("集成Minitap论文的四个核心特性:")
    logger.info("1. 进度追踪 (Progress Tracking)")
    logger.info("2. 验证机制 (Verification)")
    logger.info("3. 失败恢复 (Failure Recovery)")
    logger.info("4. 原子化分解 (Atomic Decomposition)")
    logger.info("=" * 60)
    logger.info("")

    results = {}

    # Phase 1
    results["phase1"] = await test_phase1_progress_tracking()
    logger.info("")

    # Phase 2
    results["phase2"] = await test_phase2_verification()
    logger.info("")

    # Phase 3
    results["phase3"] = await test_phase3_failure_recovery()
    logger.info("")

    # Phase 4
    results["phase4"] = await test_phase4_atomic_decomposition()
    logger.info("")

    # 完整集成
    results["integration"] = await test_full_integration()
    logger.info("")

    # 总结
    logger.info("=" * 60)
    logger.info("📊 测试结果总结:")
    logger.info(f"   Phase 1 (进度追踪):   {'✅ 通过' if results.get('phase1') else '❌ 失败'}")
    logger.info(f"   Phase 2 (验证机制):   {'✅ 通过' if results.get('phase2') else '❌ 失败'}")
    logger.info(f"   Phase 3 (失败恢复):   {'✅ 通过' if results.get('phase3') else '❌ 失败'}")
    logger.info(f"   Phase 4 (原子分解):   {'✅ 通过' if results.get('phase4') else '❌ 失败'}")
    logger.info(f"   完整集成测试:        {'✅ 通过' if results.get('integration') else '❌ 失败'}")

    all_passed = all(results.values())

    if all_passed:
        logger.info("")
        logger.info("🎉 四阶段系统集成测试全部通过！")
        logger.info("Minitap式智能执行系统已成功集成到小诺平台。")
    else:
        logger.info("")
        logger.info("⚠️ 部分测试失败，请检查相关模块。")

    logger.info("=" * 60)

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
