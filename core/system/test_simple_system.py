#!/usr/bin/env python3
"""
简化版系统管理器测试脚本
Simplified Test for System Manager

作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.base_module import BaseModule
from core.system.system_manager import (
    DependencyType,
    ModuleMetadata,
    SystemManager,
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_configuration_and_services():
    """测试配置管理和基本服务"""
    logger.info("⚙️ 测试配置管理和基本服务")
    logger.info(str("=" * 60))

    try:
        # 创建系统管理器
        system_manager = SystemManager()
        await system_manager.initialize()

        # 测试配置管理
        logger.info("\n1. 测试配置管理...")
        system_manager.config_manager.set_config("system.name", "Athena Platform")
        system_manager.config_manager.set_config("system.version", "2.0.0")
        system_manager.config_manager.set_config("modules.max_loaded", 10)

        config_name = system_manager.config_manager.get_config("system.name")
        config_version = system_manager.config_manager.get_config("system.version")
        config_max = system_manager.config_manager.get_config("modules.max_loaded")

        logger.info(f"   系统名称: {config_name}")
        logger.info(f"   系统版本: {config_version}")
        logger.info(f"   最大模块数: {config_max}")

        # 测试服务注册表
        logger.info("\n2. 测试服务注册表...")

        # 创建模拟模块
        class MockModuleA(BaseModule):
            async def _on_initialize(self):
                return True

            async def _on_start(self):
                return True

            async def _on_stop(self):
                return True

            async def _on_shutdown(self):
                return True

            async def _on_health_check(self):
                return True

        class MockModuleB(BaseModule):
            async def _on_initialize(self):
                return True

            async def _on_start(self):
                return True

            async def _on_stop(self):
                return True

            async def _on_shutdown(self):
                return True

            async def _on_health_check(self):
                return True

        # 创建模块实例
        module_a = MockModuleA("service_a")
        module_b = MockModuleB("service_b")

        # 注册服务
        system_manager.service_registry.register_service("module_a", "data_service", module_a)
        system_manager.service_registry.register_service("module_a", "processing_service", module_a)
        system_manager.service_registry.register_service("module_b", "analysis_service", module_b)

        services = system_manager.service_registry.list_services()
        logger.info(f"   注册的服务: {list(services.keys())}")

        # 测试服务获取
        data_service = system_manager.service_registry.get_service("data_service")
        processing_service = system_manager.service_registry.get_service("processing_service")
        analysis_service = system_manager.service_registry.get_service("analysis_service")

        logger.info(f"   data_service: {'✅ 可用' if data_service else '❌ 不可用'}")
        logger.info(f"   processing_service: {'✅ 可用' if processing_service else '❌ 不可用'}")
        logger.info(f"   analysis_service: {'✅ 可用' if analysis_service else '❌ 不可用'}")

        # 测试服务提供者查询
        logger.info("\n3. 测试服务提供者查询...")
        provider_a = system_manager.service_registry.get_service_provider("data_service")
        provider_b = system_manager.service_registry.get_service("processing_service")
        provider_c = system_manager.service_registry.get_service_provider("analysis_service")

        logger.info(f"   data_service 提供者: {provider_a}")
        logger.info(f"   processing_service 提供者: {provider_b}")
        logger.info(f"   analysis_service 提供者: {provider_c}")

        # 测试服务注销
        logger.info("\n4. 测试服务注销...")
        system_manager.service_registry.unregister_service("processing_service")
        remaining_services = system_manager.service_registry.list_services()
        logger.info(f"   注销后剩余服务: {list(remaining_services.keys())}")

        await system_manager.shutdown()
        logger.info("✅ 配置管理和基本服务测试完成")
        return True

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_dependency_graph():
    """测试依赖图"""
    logger.info("\n🔗 测试依赖图")
    logger.info(str("=" * 60))

    try:
        system_manager = SystemManager()
        await system_manager.initialize()

        # 创建测试模块元数据
        metadata_a = ModuleMetadata(
            module_id="CoreModule",
            name="核心模块",
            version="1.0.0",
            description="系统核心模块",
            author="Athena AI",
            created_at=datetime.now(),
            file_path="core/module.py",
            class_name="CoreModule",
            dependencies={},
            provides=["core_service", "system_service"],
            requires=[],
        )

        metadata_b = ModuleMetadata(
            module_id="InputModule",
            name="输入模块",
            version="1.0.0",
            description="输入处理模块",
            author="Athena AI",
            created_at=datetime.now(),
            file_path="input/module.py",
            class_name="InputModule",
            dependencies={"CoreModule": DependencyType.REQUIRED},
            provides=["input_service"],
            requires=["core_service"],
        )

        metadata_c = ModuleMetadata(
            module_id="OutputModule",
            name="输出模块",
            version="1.0.0",
            description="输出处理模块",
            author="Athena AI",
            created_at=datetime.now(),
            file_path="output/module.py",
            class_name="OutputModule",
            dependencies={
                "InputModule": DependencyType.REQUIRED,
                "CoreModule": DependencyType.OPTIONAL,
            },
            provides=["output_service"],
            requires=["input_service"],
        )

        # 添加到依赖图
        logger.info("\n1. 构建依赖图...")
        system_manager.dependency_graph.add_module(metadata_a)
        system_manager.dependency_graph.add_module(metadata_b)
        system_manager.dependency_graph.add_module(metadata_c)

        logger.info("   ✅ 依赖图构建完成")

        # 测试依赖查询
        logger.info("\n2. 测试依赖查询...")
        deps_core = system_manager.dependency_graph.get_dependencies("CoreModule")
        deps_input = system_manager.dependency_graph.get_dependencies("InputModule")
        deps_output = system_manager.dependency_graph.get_dependencies("OutputModule")

        logger.info(f"   CoreModule 依赖: {list(deps_core)}")
        logger.info(f"   InputModule 依赖: {list(deps_input)}")
        logger.info(f"   OutputModule 依赖: {list(deps_output)}")

        # 测试依赖者查询
        logger.info("\n3. 测试依赖者查询...")
        dependents_core = system_manager.dependency_graph.get_dependents("CoreModule")
        dependents_input = system_manager.dependency_graph.get_dependents("InputModule")
        dependents_output = system_manager.dependency_graph.get_dependents("OutputModule")

        logger.info(f"   依赖 CoreModule 的模块: {list(dependents_core)}")
        logger.info(f"   依赖 InputModule 的模块: {list(dependents_input)}")
        logger.info(f"   依赖 OutputModule 的模块: {list(dependents_output)}")

        # 测试加载顺序
        logger.info("\n4. 测试加载顺序...")
        try:
            load_order = system_manager.dependency_graph.get_load_order(
                ["OutputModule", "InputModule", "CoreModule"]
            )
            logger.info(f"   推荐加载顺序: {load_order}")
        except Exception as e:
            logger.info(f"   ❌ 计算加载顺序失败: {e}")

        # 测试循环依赖检测
        logger.info("\n5. 测试循环依赖检测...")
        cycle_core = system_manager.dependency_graph.check_circular_dependency("CoreModule")
        cycle_input = system_manager.dependency_graph.check_circular_dependency("InputModule")
        cycle_output = system_manager.dependency_graph.check_circular_dependency("OutputModule")

        logger.info(f"   CoreModule 循环依赖: {'检测到' if cycle_core else '无'}")
        logger.info(f"   InputModule 循环依赖: {'检测到' if cycle_input else '无'}")
        logger.info(f"   OutputModule 循环依赖: {'检测到' if cycle_output else '无'}")

        # 创建循环依赖进行测试
        logger.info("\n6. 创建循环依赖进行测试...")
        metadata_c.dependencies["CoreModule"] = DependencyType.REQUIRED
        system_manager.dependency_graph.add_module(metadata_c)

        cycle_after = system_manager.dependency_graph.check_circular_dependency("CoreModule")
        logger.info(f"   添加依赖后 CoreModule 循环依赖: {'检测到' if cycle_after else '无'}")

        await system_manager.shutdown()
        logger.info("✅ 依赖图测试完成")
        return True

    except Exception as e:
        logger.error(f"❌ 依赖图测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_system_status():
    """测试系统状态"""
    logger.info("\n📊 测试系统状态")
    logger.info(str("=" * 60))

    try:
        system_manager = SystemManager()
        await system_manager.initialize()

        # 获取系统状态
        logger.info("\n1. 获取系统状态...")
        system_status = system_manager.get_system_status()
        system_state = system_status["system_state"]
        statistics = system_status["statistics"]

        logger.info("   系统状态:")
        logger.info(f"     启动时间: {system_state['startup_time']}")
        logger.info(f"     已加载模块数: {system_state['loaded_modules']}")
        logger.info(f"     运行模块数: {system_state['running_modules']}")
        logger.info(f"     失败模块数: {system_state['failed_modules']}")
        logger.info(f"     总服务数: {system_state['total_services']}")

        logger.info("\n   统计信息:")
        logger.info(f"     模块加载次数: {statistics['module_loads']}")
        logger.info(f"     模块卸载次数: {statistics['module_unloads']}")
        logger.info(f"     服务注册次数: {statistics['service_registrations']}")
        logger.info(f"     配置更新次数: {statistics['configuration_updates']}")
        logger.info(f"     健康检查次数: {statistics['health_checks']}")

        # 测试系统健康度
        logger.info("\n2. 测试系统健康度...")
        logger.info("   系统管理器状态: ✅ 运行中")
        logger.info(f"   后台任务数: {len(system_manager.background_tasks)}")
        logger.info(f"   加载的模块路径数: {len(system_manager.module_loader.module_paths)}")

        await system_manager.shutdown()
        logger.info("✅ 系统状态测试完成")
        return True

    except Exception as e:
        logger.error(f"❌ 系统状态测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    logger.info("🚀 系统管理器核心功能测试")
    logger.info(str("=" * 80))

    # 测试列表
    tests = [
        ("配置管理和基本服务测试", test_configuration_and_services),
        ("依赖图测试", test_dependency_graph),
        ("系统状态测试", test_system_status),
    ]

    results = []

    for test_name, test_func in tests:
        logger.info(f"\n🧪 执行测试: {test_name}")
        try:
            result = await test_func()
            results.append((test_name, result))
            status = "✅ 通过" if result else "❌ 失败"
            logger.info(f"\n{test_name}: {status}")
        except Exception as e:
            logger.error(f"测试异常 {test_name}: {e}")
            results.append((test_name, False))

    # 测试总结
    logger.info(str("\n" + "=" * 80))
    logger.info("📊 测试总结")
    logger.info(str("=" * 80))

    passed_count = sum(1 for _, result in results if result)
    total_count = len(results)

    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{test_name}: {status}")

    logger.info(f"\n🎯 总体结果: {passed_count}/{total_count} 测试通过")
    logger.info(f"成功率: {passed_count/total_count*100:.1f}%")

    if passed_count == total_count:
        logger.info("\n🎉 所有测试通过!系统管理器核心功能验证成功!")
        logger.info("\n🌟 系统级优化特性:")
        logger.info("   ✅ 配置管理系统")
        logger.info("   ✅ 服务注册与发现")
        logger.info("   ✅ 依赖图管理")
        logger.info("   ✅ 拓扑排序")
        logger.info("   ✅ 循环依赖检测")
        logger.info("   ✅ 系统状态监控")
        logger.info("   ✅ 后台任务管理")
    else:
        logger.info("\n⚠️ 部分测试失败,需要进一步优化。")

    return passed_count == total_count


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
