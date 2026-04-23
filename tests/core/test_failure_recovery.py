#!/usr/bin/env python3
"""
测试失败恢复系统 - Phase 3
Test Failure Recovery System - Phase 3

验证检查点和失败恢复功能是否正常工作

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


async def test_checkpoint_manager():
    """测试检查点管理器"""
    logger.info("🧪 测试1: 检查点管理器")

    try:
        from core.cognition.checkpoint import (
            CheckpointManager,
            StepCheckpoint,
        )

        # 使用临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CheckpointManager(temp_dir)

            # 创建测试检查点
            step_states = {
                "step_1": StepCheckpoint(
                    step_id="step_1",
                    status="completed",
                    output={"result": "test"},
                ),
                "step_2": StepCheckpoint(
                    step_id="step_2",
                    status="in_progress",
                ),
            }

            checkpoint = manager.create_checkpoint(
                task_id="test_task",
                plan_id="test_plan",
                completed_steps=["step_1"],
                current_step="step_2",
                step_states=step_states,
            )

            logger.info(f"   ✅ 创建检查点: {checkpoint.checkpoint_id}")

            # 加载检查点
            loaded = manager.load_checkpoint(checkpoint.checkpoint_id)
            if loaded:
                logger.info(f"   ✅ 加载检查点成功: {loaded.checkpoint_id}")
                logger.info(f"   📊 状态: {loaded.status.value}")
            else:
                logger.error("   ❌ 加载检查点失败")
                return False

        logger.info("   ✅ 检查点管理器测试成功")
        return True

    except Exception as e:
        logger.error(f"   ❌ 测试失败: {e}", exc_info=True)
        return False


async def test_failure_analyzer():
    """测试失败分析器"""
    logger.info("🧪 测试2: 失败分析器")

    try:
        from core.cognition.failure_recovery import (
            FailureAnalyzer,
        )
        from core.cognition.xiaonuo_planner_engine import ExecutionStep

        analyzer = FailureAnalyzer()

        # 创建测试步骤
        test_step = ExecutionStep(
            id="test_step",
            description="测试步骤",
            agent="xiaona",
            action="patent_search",
            parameters={"query": "test"},
        )

        # 测试网络错误分析
        network_error = Exception("ConnectionError: timeout")

        analysis = await analyzer.analyze_failure(
            test_step,
            network_error,
            retry_count=0,
        )

        logger.info("   📊 失败分析结果:")
        logger.info(f"      错误类型: {analysis.error_type}")
        logger.info(f"      建议策略: {analysis.suggested_strategy}")
        logger.info(f"      可跳过: {analysis.can_skip}")

        logger.info("   ✅ 失败分析器测试成功")
        return True

    except Exception as e:
        logger.error(f"   ❌ 测试失败: {e}", exc_info=True)
        return False


async def test_recovery_handler():
    """测试失败恢复处理器"""
    logger.info("🧪 测试3: 失败恢复处理器")

    try:
        from core.cognition.checkpoint import get_checkpoint_manager
        from core.cognition.failure_recovery import (
            FailureRecoveryHandler,
        )
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
        test_steps = [
            ExecutionStep(
                id="step_1",
                description="步骤1",
                agent="xiaona",
                action="patent_search",
                parameters={"query": "test"},
                dependencies=[],
            ),
            ExecutionStep(
                id="step_2",
                description="步骤2",
                agent="xiaona",
                action="patent_analyze",
                parameters={"patent_id": "test"},
                dependencies=["step_1"],
            ),
        ]

        test_plan = ExecutionPlan(
            plan_id="test_plan_001",
            intent=Intent(
                intent_type=IntentType.TASK,
                primary_goal="测试",
                confidence=0.9,
            ),
            steps=test_steps,
            mode=ExecutionMode.SEQUENTIAL,
            resource_requirements=ResourceRequirement(),
            confidence=PlanConfidence.HIGH,
        )

        # 创建恢复处理器
        handler = FailureRecoveryHandler(
            checkpoint_manager=get_checkpoint_manager(),
        )

        # 测试处理重试
        test_error = Exception("ConnectionError: timeout")

        result = await handler.handle_failure(
            step=test_steps[0],
            error=test_error,
            execution_plan=test_plan,
            task_id="test_task",
            completed_steps=[],
            retry_count=0,
        )

        logger.info(f"   📊 处理结果: {result['action']}")
        logger.info(f"   📝 消息: {result.get('message', '')}")

        logger.info("   ✅ 失败恢复处理器测试成功")
        return True

    except Exception as e:
        logger.error(f"   ❌ 测试失败: {e}", exc_info=True)
        return False


async def main():
    """主测试函数"""
    logger.info("🚀 开始测试 Phase 3: 失败恢复系统")
    logger.info("=" * 60)

    success = True

    try:
        if not await test_checkpoint_manager():
            success = False
        logger.info("")

        if not await test_failure_analyzer():
            success = False
        logger.info("")

        if not await test_recovery_handler():
            success = False
        logger.info("")

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        success = False

    logger.info("=" * 60)
    if success:
        logger.info("✅ Phase 3: 失败恢复系统 - 测试通过")
    else:
        logger.info("❌ Phase 3: 失败恢复系统 - 测试失败")

    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
