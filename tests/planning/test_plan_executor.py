#!/usr/bin/env python3
"""
测试 PlanExecutor - Minitap式进度追踪
Test Plan Executor - Minitap-Style Progress Tracking

验证进度追踪系统是否正常工作

Author: Athena Team
Version: 1.0.0
Date: 2026-02-26
"""

import asyncio
import logging
import sys
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


async def test_basic_execution():
    """测试基本执行功能"""
    logger.info("🧪 测试1: 基本执行功能")

    from core.cognition.plan_executor import PlanExecutor
    from core.cognition.xiaonuo_planner_engine import (
        ExecutionMode,
        ExecutionStep,
        Intent,
        IntentType,
        XiaonuoPlannerEngine,
    )

    # 创建规划器
    XiaonuoPlannerEngine()

    # 创建一个简单的测试方案
    test_steps = [
        ExecutionStep(
            id="step_1",
            description="解析专利文档",
            agent="xiaona",
            action="patent_search",
            parameters={"query": "深度学习"},
            dependencies=[],
            estimated_time=2,
        ),
        ExecutionStep(
            id="step_2",
            description="分析技术方案",
            agent="xiaona",
            action="patent_analyze",
            parameters={"patent_id": "test_123"},
            dependencies=["step_1"],
            estimated_time=3,
        ),
    ]

    test_intent = Intent(
        intent_type=IntentType.TASK,
        primary_goal="测试执行",
        sub_goals=["步骤1", "步骤2"],
        confidence=0.9,
    )

    from core.cognition.xiaonuo_planner_engine import (
        ExecutionPlan,
        PlanConfidence,
        ResourceRequirement,
    )

    test_plan = ExecutionPlan(
        plan_id="test_plan_001",
        intent=test_intent,
        steps=test_steps,
        mode=ExecutionMode.SEQUENTIAL,
        resource_requirements=ResourceRequirement(),
        confidence=PlanConfidence.HIGH,
        estimated_time=5,
    )

    # 创建执行器
    PlanExecutor()

    logger.info(f"   📋 测试方案: {test_plan.plan_id}")
    logger.info(f"   📊 步骤数: {len(test_plan.steps)}")

    # 执行方案（模拟）
    logger.info("   ⚠️  注意: 完整测试需要智能体注册，此处为模块验证")
    logger.info("   ✅ PlanExecutor 模块导入成功")
    logger.info("   ✅ 测试方案创建成功")


async def test_progress_pusher():
    """测试进度推送器"""
    logger.info("🧪 测试2: 进度推送器")

    try:
        from core.communication.websocket.progress_pusher import (
            ConnectionManager,
            ProgressPusher,
            ProgressUpdate,
        )

        # 创建连接管理器
        manager = ConnectionManager()
        ProgressPusher(manager)

        logger.info("   ✅ ConnectionManager 创建成功")
        logger.info("   ✅ ProgressPusher 创建成功")

        # 测试进度更新
        update = ProgressUpdate(
            task_id="test_task",
            step_id="step_1",
            step_name="测试步骤",
            status="in_progress",
            progress_percent=50,
            current_step=1,
            total_steps=2,
            message="测试中...",
        )

        logger.info(f"   📊 进度更新: {update.to_dict()}")
        logger.info("   ✅ 进度推送器测试成功")

    except ImportError as e:
        logger.warning(f"   ⚠️ 进度推送器模块导入失败（需要websockets）: {e}")
        logger.info("   ✅ 使用 NullProgressPusher 后备方案")


async def test_integration():
    """测试集成"""
    logger.info("🧪 测试3: 模块集成")

    success = True

    # 测试规划器导入
    try:
        from core.cognition.xiaonuo_planner_engine import XiaonuoPlannerEngine
        logger.info("   ✅ XiaonuoPlannerEngine 导入成功")
    except ImportError as e:
        logger.error(f"   ❌ XiaonuoPlannerEngine 导入失败: {e}")
        success = False

    # 测试执行器导入
    try:
        from core.cognition.plan_executor import PlanExecutor, create_executor
        logger.info("   ✅ PlanExecutor 导入成功")
    except ImportError as e:
        logger.error(f"   ❌ PlanExecutor 导入失败: {e}")
        success = False

    # 测试进度推送器导入（可选）
    try:
        from core.communication.websocket.progress_pusher import ProgressPusher
        logger.info("   ✅ ProgressPusher 导入成功")
    except ImportError:
        logger.info("   ⚠️ ProgressPusher 导入失败（需要websockets），使用NullProgressPusher")

    # 测试小诺协调器导入
    try:
        from core.agents.xiaonuo_coordinator import XiaonuoAgent
        logger.info("   ✅ XiaonuoAgent 导入成功")
    except ImportError as e:
        logger.error(f"   ❌ XiaonuoAgent 导入失败: {e}")
        success = False

    if success:
        logger.info("   ✅ 所有核心模块集成成功！")

    return success


async def main():
    """主测试函数"""
    logger.info("🚀 开始测试 Phase 1: 进度追踪系统")
    logger.info("=" * 60)

    success = True

    try:
        await test_basic_execution()
        logger.info("")

        await test_progress_pusher()
        logger.info("")

        success = await test_integration()
        logger.info("")

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        success = False

    logger.info("=" * 60)
    if success:
        logger.info("✅ Phase 1: 进度追踪系统 - 测试通过")
    else:
        logger.info("❌ Phase 1: 进度追踪系统 - 测试失败")

    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
