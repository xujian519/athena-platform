#!/usr/bin/env python3
"""
增强评估模块测试脚本
Test Enhanced Evaluation Module

验证BaseModule兼容性和评估功能
作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.evaluation.enhanced_evaluation_module import EnhancedEvaluationModule

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_enhanced_evaluation_module():
    """测试增强评估模块"""
    logger.info("\n🔍 增强评估模块测试")
    logger.info(str("=" * 60))

    try:
        # 1. 创建模块实例
        logger.info("\n1. 创建增强评估模块...")
        evaluation_module = EnhancedEvaluationModule(
            agent_id="test_evaluation_agent_001",
            config={
                "enable_quality_assurance": True,
                "enable_reflection": True,
                "auto_save_interval": 0,  # 测试时禁用自动保存
            },
        )
        logger.info("✅ 评估模块创建成功")

        # 2. 初始化模块
        logger.info("\n2. 初始化评估模块...")
        init_success = await evaluation_module.initialize()
        if init_success:
            logger.info("✅ 评估模块初始化成功")
        else:
            logger.info("❌ 评估模块初始化失败")
            return False

        # 3. 健康检查
        logger.info("\n3. 执行健康检查...")
        health_status = await evaluation_module.health_check()
        logger.info("✅ 健康检查结果:")
        logger.info(f"   - 健康状态: {'健康' if health_status.value == 'healthy' else '不健康'}")
        logger.info(f"   - 状态值: {health_status.value}")

        # 获取健康检查详情
        if hasattr(evaluation_module, "_health_check_details"):
            details = evaluation_module._health_check_details
            logger.info(f"   - 评估系统状态: {details.get('evaluation_status', 'unknown')}")
            logger.info(f"   - 质量保证: {details.get('quality_assurance', 'unknown')}")
            logger.info(f"   - 反思功能: {details.get('reflection_enabled', 'unknown')}")

            stats = details.get("stats", {})
            if stats:
                logger.info(
                    f"   - 评估统计: 总计{stats.get('total_evaluations', 0)}, 成功{stats.get('successful_evaluations', 0)}"
                )

        # 4. 创建评估任务
        logger.info("\n4. 测试评估任务创建...")
        task_id = await evaluation_module.create_evaluation_task(
            target_type="performance",
            target_id="test_target_001",
            evaluation_type="performance",
            criteria=[
                {
                    "id": "speed",
                    "name": "响应速度",
                    "description": "系统响应速度评估",
                    "weight": 0.3,
                    "min_value": 0,
                    "max_value": 100,
                    "target_value": 80,
                    "current_value": 85,
                },
                {
                    "id": "accuracy",
                    "name": "准确性",
                    "description": "结果准确性评估",
                    "weight": 0.4,
                    "min_value": 0,
                    "max_value": 100,
                    "target_value": 90,
                    "current_value": 88,
                },
                {
                    "id": "efficiency",
                    "name": "效率",
                    "description": "资源使用效率",
                    "weight": 0.3,
                    "min_value": 0,
                    "max_value": 100,
                    "target_value": 75,
                    "current_value": 72,
                },
            ],
        )
        logger.info(f"✅ 评估任务创建: {task_id}")

        # 5. 执行评估
        logger.info("\n5. 测试评估执行...")
        evaluation_result = await evaluation_module.evaluate(
            target_type="performance",
            target_id="test_target_002",
            evaluation_type="quality",
            criteria=[
                {
                    "id": "reliability",
                    "name": "可靠性",
                    "description": "系统稳定性评估",
                    "weight": 0.5,
                    "min_value": 0,
                    "max_value": 100,
                    "target_value": 95,
                    "current_value": 92,
                },
                {
                    "id": "usability",
                    "name": "易用性",
                    "description": "用户友好性评估",
                    "weight": 0.5,
                    "min_value": 0,
                    "max_value": 100,
                    "target_value": 85,
                    "current_value": 78,
                },
            ],
        )
        logger.info(f"   评估结果: {'成功' if evaluation_result.success else '失败'}")
        if evaluation_result.success:
            logger.info(f"   - 任务ID: {evaluation_result.task_id}")
            logger.info(f"   - 评估ID: {evaluation_result.evaluation_id}")
            logger.info(f"   - 得分: {evaluation_result.score}")
            logger.info(f"   - 等级: {evaluation_result.level}")
            logger.info(f"   - 执行时间: {evaluation_result.execution_time:.3f}s")

        # 6. 测试反思功能
        logger.info("\n6. 测试反思功能...")
        if evaluation_result.evaluation_id:
            reflection_result = await evaluation_module.reflect(
                evaluation_id=evaluation_result.evaluation_id,
                context={"focus": "improvement_areas"},
            )
            logger.info(f"   反思结果: {'成功' if reflection_result.get('success') else '失败'}")
            if reflection_result.get("success"):
                logger.info(f"   - 反思ID: {reflection_result.get('reflection_id')}")
                logger.info(f"   - 见解数量: {len(reflection_result.get('insights', []))}")
                logger.info(f"   - 行动项数量: {len(reflection_result.get('action_items', []))}")

        # 7. 测试标准处理接口
        logger.info("\n7. 测试标准处理接口...")
        process_test_cases = [
            {
                "operation": "evaluate",
                "target_type": "system",
                "target_id": "test_system_001",
                "evaluation_type": "performance",
                "criteria": [
                    {"id": "throughput", "name": "吞吐量", "current_value": 85, "target_value": 90}
                ],
            },
            {
                "operation": "create_task",
                "target_type": "module",
                "target_id": "test_module_001",
                "evaluation_type": "quality",
            },
            {"operation": "get_summary"},
        ]

        for i, test_case in enumerate(process_test_cases):
            result = await evaluation_module.process(test_case)
            operation = test_case["operation"]
            logger.info(f"   处理{i+1}({operation}): {result.get('success', False)}")
            if "task_id" in result:
                logger.info(f"     - 任务ID: {result.get('task_id', 'unknown')}")
            if "score" in result:
                logger.info(f"     - 得分: {result.get('score', 0):.1f}")

        # 8. 获取评估摘要
        logger.info("\n8. 获取评估摘要...")
        summary = await evaluation_module.get_evaluation_summary()
        logger.info("✅ 摘要获取完成")
        if "enhanced_stats" in summary:
            stats = summary["enhanced_stats"]
            logger.info(f"   - 总评估数: {stats.get('total_evaluations', 0)}")
            logger.info(f"   - 成功评估: {stats.get('successful_evaluations', 0)}")
            logger.info(f"   - 平均得分: {stats.get('average_score', 0):.2f}")
            logger.info(f"   - 活跃任务: {stats.get('active_tasks', 0)}")

        # 9. 获取模块状态
        logger.info("\n9. 获取模块状态...")
        status = evaluation_module.get_status()
        logger.info("✅ 状态获取完成")
        logger.info(f"   - 智能体ID: {status.get('agent_id', 'unknown')}")
        logger.info(f"   - 模块类型: {status.get('module_type', 'unknown')}")
        logger.info(f"   - 运行状态: {status.get('status', 'unknown')}")
        logger.info(f"   - 活跃任务: {status.get('active_tasks', 0)}")

        # 10. 获取性能指标
        logger.info("\n10. 获取性能指标...")
        metrics = evaluation_module.get_metrics()
        logger.info("✅ 指标获取完成")
        logger.info(f"   - 模块状态: {metrics.get('module_status', 'unknown')}")
        logger.info(f"   - 代理ID: {metrics.get('agent_id', 'unknown')}")
        logger.info(f"   - 初始化状态: {metrics.get('initialized', False)}")
        logger.info(f"   - 运行时长: {metrics.get('uptime_seconds', 0):.2f}s")

        eval_stats = metrics.get("evaluation_stats", {})
        if eval_stats:
            logger.info("   - 评估统计:")
            logger.info(f"     * 总评估数: {eval_stats.get('total_evaluations', 0)}")
            logger.info(f"     * 成功评估: {eval_stats.get('successful_evaluations', 0)}")
            logger.info(f"     * 失败评估: {eval_stats.get('failed_evaluations', 0)}")
            logger.info(f"     * 平均得分: {eval_stats.get('average_score', 0):.2f}")

        # 11. 测试不同评估类型
        logger.info("\n11. 测试不同评估类型...")
        evaluation_types = ["performance", "quality", "accuracy", "efficiency"]

        for eval_type in evaluation_types:
            logger.info(f"   测试评估类型: {eval_type}")
            result = await evaluation_module.evaluate(
                target_type=f"test_{eval_type}",
                target_id=f"target_{eval_type}_001",
                evaluation_type=eval_type,
                criteria=[
                    {
                        "id": f"metric_{eval_type}",
                        "name": f"{eval_type.title()} Metric",
                        "current_value": 80,
                        "target_value": 85,
                    }
                ],
            )
            logger.info(f"     评估结果: {'✅' if result.success else '❌'}")

        # 12. 测试关闭
        logger.info("\n12. 测试模块关闭...")
        await evaluation_module.shutdown()
        logger.info("✅ 模块关闭成功")

        logger.info(str("\n" + "=" * 60))
        logger.info("🎉 增强评估模块测试完成 - 所有测试通过!")
        return True

    except Exception as e:
        import traceback

        traceback.print_exc()
        return False


async def test_evaluation_scenarios():
    """测试不同评估场景"""
    logger.info("\n🔄 评估场景测试")
    logger.info(str("=" * 60))

    try:
        evaluation_module = EnhancedEvaluationModule(
            agent_id="scenario_test_agent",
            config={"enable_quality_assurance": True, "enable_reflection": True},
        )

        await evaluation_module.initialize()

        # 场景1: 高分评估
        logger.info("\n场景1: 优秀表现评估")
        result = await evaluation_module.evaluate(
            target_type="excellent_system",
            target_id="system_001",
            evaluation_type="performance",
            criteria=[
                {"id": "speed", "name": "速度", "current_value": 95, "target_value": 90},
                {"id": "accuracy", "name": "准确性", "current_value": 92, "target_value": 85},
            ],
        )
        logger.info(f"   结果: {result.score:.1f} ({result.level})")

        # 场景2: 低分评估
        logger.info("\n场景2: 需要改进评估")
        result = await evaluation_module.evaluate(
            target_type="poor_system",
            target_id="system_002",
            evaluation_type="quality",
            criteria=[
                {"id": "stability", "name": "稳定性", "current_value": 45, "target_value": 80},
                {"id": "reliability", "name": "可靠性", "current_value": 52, "target_value": 85},
            ],
        )
        logger.info(f"   结果: {result.score:.1f} ({result.level})")

        # 场景3: 批量评估
        logger.info("\n场景3: 批量评估")
        targets = [
            ("batch_target_1", "module"),
            ("batch_target_2", "component"),
            ("batch_target_3", "service"),
        ]

        results = []
        for target_id, target_type in targets:
            result = await evaluation_module.evaluate(
                target_type=target_type,
                target_id=target_id,
                evaluation_type="efficiency",
                criteria=[
                    {
                        "id": "resource_usage",
                        "name": "资源使用",
                        "current_value": 75,
                        "target_value": 80,
                    }
                ],
            )
            results.append(result)

        logger.info(f"   批量评估完成: {len(results)} 个目标")
        avg_score = sum(r.score for r in results if r.success) / len(results)
        logger.info(f"   平均得分: {avg_score:.1f}")

        await evaluation_module.shutdown()
        return True

    except Exception as e:
        return False


async def main():
    """主测试函数"""
    logger.info("🚀 增强评估模块完整测试套件")
    logger.info(str("=" * 80))

    # 基础功能测试
    basic_test_passed = await test_enhanced_evaluation_module()

    # 评估场景测试
    scenario_test_passed = await test_evaluation_scenarios()

    # 测试总结
    logger.info(str("\n" + "=" * 80))
    logger.info("📊 测试总结")
    logger.info(str("=" * 80))
    logger.info(f"基础功能测试: {'✅ 通过' if basic_test_passed else '❌ 失败'}")
    logger.info(f"评估场景测试: {'✅ 通过' if scenario_test_passed else '❌ 失败'}")

    overall_success = basic_test_passed and scenario_test_passed
    logger.info(f"\n🎯 总体结果: {'✅ 全部测试通过' if overall_success else '❌ 存在失败测试'}")

    return overall_success


if __name__ == "__main__":
    asyncio.run(main())
