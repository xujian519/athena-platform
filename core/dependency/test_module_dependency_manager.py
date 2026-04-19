#!/usr/bin/env python3
from __future__ import annotations
"""
模块依赖管理系统测试脚本
Test Module Dependency Manager

验证模块依赖管理功能
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

from core.dependency.module_dependency_manager import (
    CORE_MODULE_DEPENDENCIES,
    DependencyType,
    ModuleDependencyManager,
    ModuleInfo,
    ModulePriority,
)

# 导入增强模块用于测试
try:
    from core.cognition.enhanced_cognition_module import EnhancedCognitionModule
    from core.communication.enhanced_communication_module import (
        EnhancedCommunicationModule,
    )
    from core.evaluation.enhanced_evaluation_module import EnhancedEvaluationModule
    from core.execution.enhanced_execution_engine import EnhancedExecutionEngine
    from core.knowledge.enhanced_knowledge_tools_module import (
        EnhancedKnowledgeToolsModule,
    )
    from core.learning.enhanced_learning_engine import EnhancedLearningEngine
    from core.memory.enhanced_memory_module import EnhancedMemoryModule
    from core.perception.enhanced_perception_module import EnhancedPerceptionModule

    MODULES_AVAILABLE = True
except ImportError as e:
    logging.warning(f"无法导入增强模块: {e}")
    MODULES_AVAILABLE = False

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_module_dependency_manager():
    """测试模块依赖管理器"""
    logger.info("\n🔗 模块依赖管理系统测试")
    logger.info(str("=" * 60))

    try:
        # 1. 创建依赖管理器
        logger.info("\n1. 创建模块依赖管理器...")
        dependency_manager = ModuleDependencyManager(
            {"default_timeout": 10.0, "enable_parallel_startup": True, "health_check_interval": 2.0}
        )
        logger.info("✅ 依赖管理器创建成功")

        # 2. 注册核心模块
        logger.info("\n2. 注册核心模块...")
        if MODULES_AVAILABLE:
            core_modules = {
                "perception": (EnhancedPerceptionModule, ModulePriority.CRITICAL),
                "memory": (EnhancedMemoryModule, ModulePriority.CRITICAL),
                "cognition": (EnhancedCognitionModule, ModulePriority.CRITICAL),
                "execution": (EnhancedExecutionEngine, ModulePriority.HIGH),
                "learning": (EnhancedLearningEngine, ModulePriority.HIGH),
                "communication": (EnhancedCommunicationModule, ModulePriority.NORMAL),
                "evaluation": (EnhancedEvaluationModule, ModulePriority.NORMAL),
                "knowledge_tools": (EnhancedKnowledgeToolsModule, ModulePriority.LOW),
            }

            for module_id, (module_class, priority) in core_modules.items():
                module_info = ModuleInfo(
                    module_id=module_id,
                    module_name=f"Enhanced {module_id.title()} Module",
                    module_class=module_class,
                    priority=priority,
                    required=priority.value <= ModulePriority.HIGH.value,
                    startup_timeout=5.0,
                    config={"test_mode": True},
                )
                dependency_manager.register_module(module_info)

            logger.info(f"✅ 注册了 {len(core_modules)} 个核心模块")
        else:
            logger.info("⚠️ 跳过模块注册(模块不可用)")

        # 3. 注册依赖关系
        logger.info("\n3. 注册依赖关系...")
        for module_id, dependencies in CORE_MODULE_DEPENDENCIES.items():
            for dep in dependencies:
                dependency_manager.register_dependency(
                    module_id=module_id,
                    depends_on=dep,
                    dependency_type=DependencyType.REQUIRED,
                    description=f"{module_id} requires {dep}",
                )

        logger.info("✅ 依赖关系注册完成")

        # 4. 创建启动计划
        logger.info("\n4. 创建启动计划...")
        startup_plan = dependency_manager.create_startup_plan()
        logger.info("✅ 启动计划创建成功")
        logger.info(f"   - 启动顺序: {startup_plan.startup_order}")
        logger.info(f"   - 并行组数: {len(startup_plan.parallel_groups)}")
        logger.info(f"   - 预估时间: {startup_plan.total_estimated_time:.1f}s")
        logger.info(f"   - 关键路径: {startup_plan.critical_path}")

        # 5. 显示并行启动组
        logger.info("\n5. 并行启动组详情...")
        for i, group in enumerate(startup_plan.parallel_groups):
            logger.info(f"   组 {i+1}: {group} ({len(group)} 个模块)")

        # 6. 获取依赖图信息
        logger.info("\n6. 获取依赖图信息...")
        graph_info = dependency_manager.get_dependency_graph()
        logger.info("✅ 依赖图信息:")
        logger.info(f"   - 节点数: {graph_info['nodes']}")
        logger.info(f"   - 边数: {graph_info['edges']}")
        logger.info(f"   - 无环: {graph_info['is_acyclic']}")

        # 7. 执行启动计划(简化版)
        logger.info("\n7. 执行启动计划(模拟)...")
        if MODULES_AVAILABLE:
            try:
                # 使用较短的测试时间
                for module_id in startup_plan.startup_order[:2]:  # 只启动前两个模块
                    result = await dependency_manager.startup_module(module_id)
                    logger.info(f"   - {module_id}: {'✅ 成功' if result else '❌ 失败'}")

                logger.info("✅ 启动计划执行完成(模拟)")
            except Exception as e:
                logger.info(f"⚠️ 启动模拟失败: {e}")
        else:
            logger.info("⚠️ 跳过启动执行(模块不可用)")

        # 8. 获取模块状态
        logger.info("\n8. 获取模块状态...")
        status_info = dependency_manager.get_module_status()
        logger.info("✅ 模块状态获取完成")
        summary = status_info["summary"]
        logger.info(f"   - 未初始化: {summary.get('uninitialized', 0)}")
        logger.info(f"   - 初始化中: {summary.get('initializing', 0)}")
        logger.info(f"   - 就绪: {summary.get('ready', 0)}")
        logger.info(f"   - 运行中: {summary.get('running', 0)}")
        logger.info(f"   - 错误: {summary.get('error', 0)}")

        # 9. 关闭所有模块
        logger.info("\n9. 关闭所有模块...")
        if MODULES_AVAILABLE:
            try:
                shutdown_result = await dependency_manager.shutdown_all()
                logger.info("✅ 关闭完成:")
                logger.info(f"   - 成功关闭: {len(shutdown_result['shutdown_modules'])}")
                logger.info(f"   - 失败: {len(shutdown_result['failed_modules'])}")
            except Exception as e:
                logger.info(f"⚠️ 关闭失败: {e}")

        logger.info(str("\n" + "=" * 60))
        logger.info("🎉 模块依赖管理系统测试完成!")
        return True

    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e!s}")
        import traceback

        traceback.print_exc()
        return False


async def test_dependency_scenarios():
    """测试依赖管理场景"""
    logger.info("\n🔄 依赖管理场景测试")
    logger.info(str("=" * 60))

    try:
        # 场景1: 循环依赖检测
        logger.info("\n场景1: 循环依赖检测...")
        dep_manager = ModuleDependencyManager()

        # 创建有循环依赖的模块
        module_a = ModuleInfo(
            module_id="module_a",
            module_name="Module A",
            module_class=object,  # 使用虚拟类
            priority=ModulePriority.NORMAL,
        )
        module_b = ModuleInfo(
            module_id="module_b",
            module_name="Module B",
            module_class=object,
            priority=ModulePriority.NORMAL,
        )
        module_c = ModuleInfo(
            module_id="module_c",
            module_name="Module C",
            module_class=object,
            priority=ModulePriority.NORMAL,
        )

        dep_manager.register_module(module_a)
        dep_manager.register_module(module_b)
        dep_manager.register_module(module_c)

        # 添加循环依赖 A -> B -> C -> A
        dep_manager.register_dependency("module_b", "module_a")
        dep_manager.register_dependency("module_c", "module_b")
        dep_manager.register_dependency("module_a", "module_c")

        try:
            plan = dep_manager.create_startup_plan()
            logger.info("❌ 循环依赖检测失败")
            return False
        except ValueError as e:
            if "循环依赖" in str(e):
                logger.info("✅ 成功检测到循环依赖")
            else:
                logger.info(f"⚠️ 检测到其他错误: {e}")

        # 场景2: 复杂依赖关系
        logger.info("\n场景2: 复杂依赖关系...")
        dep_manager2 = ModuleDependencyManager()

        # 创建复杂依赖结构
        modules_config = {
            "base": (ModulePriority.CRITICAL, []),
            "service1": (ModulePriority.HIGH, ["base"]),
            "service2": (ModulePriority.HIGH, ["base"]),
            "app1": (ModulePriority.NORMAL, ["service1", "service2"]),
            "app2": (ModulePriority.NORMAL, ["service1"]),
            "monitor": (ModulePriority.LOW, ["app1", "app2"]),
        }

        for module_id, (priority, deps) in modules_config.items():
            module_info = ModuleInfo(
                module_id=module_id,
                module_name=f"Module {module_id.title()}",
                module_class=object,
                priority=priority,
            )
            dep_manager2.register_module(module_info)

            for dep in deps:
                dep_manager2.register_dependency(module_id, dep)

        plan = dep_manager2.create_startup_plan()
        logger.info("✅ 复杂依赖启动计划:")
        logger.info(f"   - 启动顺序: {plan.startup_order}")
        logger.info(f"   - 并行组: {len(plan.parallel_groups)}")

        # 场景3: 可选依赖处理
        logger.info("\n场景3: 可选依赖处理...")
        dep_manager3 = ModuleDependencyManager()

        main_module = ModuleInfo(
            module_id="main",
            module_name="Main Module",
            module_class=object,
            priority=ModulePriority.HIGH,
        )
        optional_module = ModuleInfo(
            module_id="optional",
            module_name="Optional Module",
            module_class=object,
            priority=ModulePriority.LOW,
            required=False,
            auto_start=True,
        )

        dep_manager3.register_module(main_module)
        dep_manager3.register_module(optional_module)
        dep_manager3.register_dependency("main", "optional", DependencyType.OPTIONAL)

        plan = dep_manager3.create_startup_plan()
        logger.info("✅ 可选依赖启动计划:")
        logger.info(f"   - 启动顺序: {plan.startup_order}")

        return True

    except Exception as e:
        logger.error(f"❌ 场景测试失败: {e!s}")
        return False


async def main():
    """主测试函数"""
    logger.info("🚀 模块依赖管理系统完整测试套件")
    logger.info(str("=" * 80))

    # 基础功能测试
    basic_test_passed = await test_module_dependency_manager()

    # 场景测试
    scenario_test_passed = await test_dependency_scenarios()

    # 测试总结
    logger.info(str("\n" + "=" * 80))
    logger.info("📊 测试总结")
    logger.info(str("=" * 80))
    logger.info(f"基础功能测试: {'✅ 通过' if basic_test_passed else '❌ 失败'}")
    logger.info(f"场景测试: {'✅ 通过' if scenario_test_passed else '❌ 失败'}")

    overall_success = basic_test_passed and scenario_test_passed
    logger.info(f"\n🎯 总体结果: {'✅ 全部测试通过' if overall_success else '❌ 存在失败测试'}")

    return overall_success


if __name__ == "__main__":
    asyncio.run(main())
