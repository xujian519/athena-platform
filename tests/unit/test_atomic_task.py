#!/usr/bin/env python3
"""
测试原子化任务分解系统 - Phase 4
Test Atomic Task Decomposition System - Phase 4

验证原子任务的创建、分解和执行功能

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


async def test_input_contract():
    """测试输入契约验证"""
    logger.info("🧪 测试1: 输入契约验证")

    try:
        from core.cognition.atomic_task import InputContract

        # 创建契约
        contract = InputContract(
            required_parameters={"query", "limit"},
            parameter_types={"query": "str", "limit": "int"},
        )

        # 测试有效输入
        valid_params = {"query": "test", "limit": 10}
        is_valid, errors = contract.validate(valid_params)
        if is_valid:
            logger.info("   ✅ 有效参数验证通过")
        else:
            logger.error(f"   ❌ 有效参数验证失败: {errors}")
            return False

        # 测试无效输入（缺少必需参数）
        invalid_params = {"query": "test"}
        is_valid, errors = contract.validate(invalid_params)
        if not is_valid:
            logger.info(f"   ✅ 无效参数正确拒绝: {errors}")
        else:
            logger.error("   ❌ 无效参数未被拒绝")
            return False

        # 测试类型错误
        type_error_params = {"query": "test", "limit": "not_int"}
        is_valid, errors = contract.validate(type_error_params)
        if not is_valid:
            logger.info(f"   ✅ 类型错误正确检测: {errors}")
        else:
            logger.error("   ❌ 类型错误未被检测")
            return False

        logger.info("   ✅ 输入契约验证测试成功")
        return True

    except Exception as e:
        logger.error(f"   ❌ 测试失败: {e}", exc_info=True)
        return False


async def test_output_contract():
    """测试输出契约验证"""
    logger.info("🧪 测试2: 输出契约验证")

    try:
        from core.cognition.atomic_task import OutputContract

        # 创建契约
        contract = OutputContract(
            required_fields={"results", "total_count"},
            field_types={"results": "list", "total_count": "int"},
        )

        # 测试有效输出
        valid_output = {"results": [1, 2, 3], "total_count": 3}
        is_valid, errors = contract.validate(valid_output)
        if is_valid:
            logger.info("   ✅ 有效输出验证通过")
        else:
            logger.error(f"   ❌ 有效输出验证失败: {errors}")
            return False

        # 测试无效输出（缺少必需字段）
        invalid_output = {"results": [1, 2, 3]}
        is_valid, errors = contract.validate(invalid_output)
        if not is_valid:
            logger.info(f"   ✅ 无效输出正确拒绝: {errors}")
        else:
            logger.error("   ❌ 无效输出未被拒绝")
            return False

        logger.info("   ✅ 输出契约验证测试成功")
        return True

    except Exception as e:
        logger.error(f"   ❌ 测试失败: {e}", exc_info=True)
        return False


async def test_atomic_task_decomposer():
    """测试原子任务分解器"""
    logger.info("🧪 测试3: 原子任务分解器")

    try:
        from core.cognition.atomic_task import AtomicTaskDecomposer
        from core.cognition.xiaonuo_planner_engine import ExecutionStep

        decomposer = AtomicTaskDecomposer()

        # 创建测试步骤
        step = ExecutionStep(
            id="step_1",
            description="专利检索",
            agent="xiaona",
            action="patent_search",
            parameters={"query": "深度学习", "limit": 10},
        )

        # 分解步骤
        atomic_tasks = decomposer.decompose_step(step)

        logger.info(f"   📊 分解结果: {len(atomic_tasks)} 个原子任务")

        if atomic_tasks:
            task = atomic_tasks[0]
            logger.info(f"      任务ID: {task.id}")
            logger.info(f"      操作: {task.action}")
            logger.info(f"      智能体: {task.agent}")

            # 验证输入契约
            is_valid, errors = task.validate_input()
            if is_valid:
                logger.info("      ✅ 输入契约验证通过")
            else:
                logger.error(f"      ❌ 输入契约验证失败: {errors}")
                return False

        logger.info("   ✅ 原子任务分解器测试成功")
        return True

    except Exception as e:
        logger.error(f"   ❌ 测试失败: {e}", exc_info=True)
        return False


async def test_complex_step_decomposition():
    """测试复杂步骤分解"""
    logger.info("🧪 测试4: 复杂步骤分解")

    try:
        from core.cognition.atomic_task import AtomicTaskDecomposer
        from core.cognition.xiaonuo_planner_engine import ExecutionStep

        decomposer = AtomicTaskDecomposer()

        # 创建复合操作步骤
        step = ExecutionStep(
            id="step_complex",
            description="专利检索并分析",
            agent="xiaona",
            action="patent_search_and_analyze",
            parameters={"query": "深度学习"},
        )

        # 分解复杂步骤
        atomic_tasks = decomposer.decompose_complex_step(step)

        logger.info(f"   📊 分解结果: {len(atomic_tasks)} 个原子任务")

        for i, task in enumerate(atomic_tasks, 1):
            logger.info(f"      任务 {i}: {task.id} - {task.action}")
            logger.info(f"         依赖: {task.dependencies}")

        # 验证依赖关系
        if len(atomic_tasks) == 2:
            if atomic_tasks[1].dependencies == [atomic_tasks[0].id]:
                logger.info("      ✅ 依赖关系正确")
            else:
                logger.error(f"      ❌ 依赖关系错误: {atomic_tasks[1].dependencies}")
                return False

        logger.info("   ✅ 复杂步骤分解测试成功")
        return True

    except Exception as e:
        logger.error(f"   ❌ 测试失败: {e}", exc_info=True)
        return False


async def test_atomic_task():
    """测试原子任务模型"""
    logger.info("🧪 测试5: 原子任务模型")

    try:
        from core.cognition.atomic_task import (
            AtomicTask,
            InputContract,
            OutputContract,
        )

        # 创建原子任务
        task = AtomicTask(
            id="task_001",
            action="patent_search",
            agent="xiaona",
            description="测试任务",
            input_contract=InputContract(
                required_parameters={"query"},
            ),
            output_contract=OutputContract(
                required_fields={"results"},
            ),
            parameters={"query": "test"},
        )

        logger.info(f"   📊 任务ID: {task.id}")
        logger.info(f"   📊 状态: {task.status.value}")

        # 测试准备状态检查
        if task.is_ready(set()):
            logger.info("   ✅ 准备状态检查通过（无依赖）")
        else:
            logger.error("   ❌ 准备状态检查失败")
            return False

        # 测试有依赖的情况
        task_with_dep = AtomicTask(
            id="task_002",
            action="patent_analyze",
            agent="xiaona",
            description="依赖任务",
            input_contract=InputContract(),
            output_contract=OutputContract(),
            dependencies=["task_001"],
        )

        if not task_with_dep.is_ready(set()):
            logger.info("   ✅ 依赖检查通过（依赖未满足）")
        else:
            logger.error("   ❌ 依赖检查失败")
            return False

        if task_with_dep.is_ready({"task_001"}):
            logger.info("   ✅ 依赖检查通过（依赖已满足）")
        else:
            logger.error("   ❌ 依赖检查失败")
            return False

        logger.info("   ✅ 原子任务模型测试成功")
        return True

    except Exception as e:
        logger.error(f"   ❌ 测试失败: {e}", exc_info=True)
        return False


async def main():
    """主测试函数"""
    logger.info("🚀 开始测试 Phase 4: 原子化任务分解系统")
    logger.info("=" * 60)

    success = True

    try:
        if not await test_input_contract():
            success = False
        logger.info("")

        if not await test_output_contract():
            success = False
        logger.info("")

        if not await test_atomic_task():
            success = False
        logger.info("")

        if not await test_atomic_task_decomposer():
            success = False
        logger.info("")

        if not await test_complex_step_decomposition():
            success = False
        logger.info("")

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        success = False

    logger.info("=" * 60)
    if success:
        logger.info("✅ Phase 4: 原子化任务分解系统 - 测试通过")
    else:
        logger.info("❌ Phase 4: 原子化任务分解系统 - 测试失败")

    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
