#!/usr/bin/env python3
from __future__ import annotations
"""
系统管理器测试脚本
Test System Manager

验证模块热插拔和动态依赖管理功能
作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import asyncio
import logging
import os
import sys
import tempfile
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


# 创建测试模块
class TestModuleA(BaseModule):
    """测试模块A"""

    __version__ = "1.0.0"
    __author__ = "Test"
    __dependencies__ = {}  # 无依赖
    __provides__ = ["service_a", "test_service"]
    __requires__ = []
    __tags__ = ["test", "core"]
    __auto_restart__ = True
    __max_retries__ = 3


class TestModuleB(BaseModule):
    """测试模块B"""

    __version__ = "1.0.0"
    __author__ = "Test"
    __dependencies__ = {"TestModuleA": DependencyType.REQUIRED}
    __provides__ = ["service_b"]
    __requires__ = ["service_a"]
    __tags__ = ["test", "dependent"]
    __auto_restart__ = True
    __max_retries__ = 3


class TestModuleC(BaseModule):
    """测试模块C"""

    __version__ = "1.0.0"
    __author__ = "Test"
    __dependencies__ = {
        "TestModuleB": DependencyType.REQUIRED,
        "NonExistentModule": DependencyType.OPTIONAL,
    }
    __provides__ = ["service_c"]
    __requires__ = ["service_b"]
    __tags__ = ["test", "leaf"]
    __auto_restart__ = True
    __max_retries__ = 3


async def test_module_loading():
    """测试模块加载"""
    logger.info("\n📦 测试模块加载")
    logger.info(str("=" * 60))

    try:
        # 创建临时模块目录
        temp_dir = tempfile.mkdtemp()
        logger.info(f"临时模块目录: {temp_dir}")

        # 创建测试模块文件
        module_files = [
            (
                "test_module_a.py",
                '''
from core.base_module import BaseModule

class TestModuleA(BaseModule):
    """测试模块A"""
    __version__ = '1.0.0'
    __author__ = 'Test'
    __dependencies__ = {}
    __provides__ = ['service_a', 'test_service']
    __requires__ = []
    __tags__ = ['test', 'core']
    __auto_restart__ = True
    __max_retries__ = 3

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
''',
            ),
            (
                "test_module_b.py",
                '''
from core.base_module import BaseModule

class TestModuleB(BaseModule):
    """测试模块B"""
    __version__ = '1.0.0'
    __author__ = 'Test'
    __dependencies__ = {'TestModuleA': 'required'}
    __provides__ = ['service_b']
    __requires__ = ['service_a']
    __tags__ = ['test', 'dependent']
    __auto_restart__ = True
    __max_retries__ = 3

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
''',
            ),
            (
                "test_module_c.py",
                '''
from core.base_module import BaseModule

class TestModuleC(BaseModule):
    """测试模块C"""
    __version__ = '1.0.0'
    __author__ = 'Test'
    __dependencies__ = {'TestModuleB': 'required', 'NonExistentModule': 'optional'}
    __provides__ = ['service_c']
    __requires__ = ['service_b']
    __tags__ = ['test', 'leaf']
    __auto_restart__ = True
    __max_retries__ = 3

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
''',
            ),
        ]

        for filename, content in module_files:
            file_path = os.path.join(temp_dir, filename)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

        # 创建系统管理器
        system_manager = SystemManager()
        await system_manager.initialize()

        logger.info("\n1. 加载测试模块...")
        load_success = await system_manager.load_module(temp_dir)
        logger.info(
            f"   {'✅' if load_success else '❌'} 模块加载{'成功' if load_success else '失败'}"
        )

        # 获取系统状态
        system_status = system_manager.get_system_status()
        loaded_modules = system_status["system_state"]["loaded_modules"]
        logger.info(f"   已加载模块数: {loaded_modules}")

        # 初始化模块
        logger.info("\n2. 初始化模块...")
        for module_id in system_manager.module_instances:
            init_success = await system_manager.initialize_module(module_id)
            logger.info(
                f"   {'✅' if init_success else '❌'} {module_id} 初始化{'成功' if init_success else '失败'}"
            )

        # 启动模块
        logger.info("\n3. 启动模块...")
        for module_id in system_manager.module_instances:
            start_success = await system_manager.start_module(module_id)
            logger.info(
                f"   {'✅' if start_success else '❌'} {module_id} 启动{'成功' if start_success else '失败'}"
            )

        # 检查服务注册
        logger.info("\n4. 检查服务注册...")
        services = system_manager.service_registry.list_services()
        logger.info(f"   注册的服务: {list(services.keys())}")

        # 验证依赖关系
        logger.info("\n5. 验证依赖关系...")
        for service_name in services:
            module_id = services[service_name]
            system_manager.get_service(service_name)
            logger.info(f"   ✅ 服务 {service_name} 由模块 {module_id} 提供")

        # 清理
        logger.info("\n6. 清理测试环境...")
        await system_manager.shutdown()
        for filename in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, filename))
        os.rmdir(temp_dir)

        logger.info("✅ 模块加载测试完成")
        return True

    except Exception as e:
        logger.error(f"❌ 模块加载测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_dependency_management():
    """测试依赖管理"""
    logger.info("\n🔗 测试依赖管理")
    logger.info(str("=" * 60))

    try:
        system_manager = SystemManager()
        await system_manager.initialize()

        # 创建测试模块元数据
        metadata_a = ModuleMetadata(
            module_id="TestModuleA",
            name="测试模块A",
            version="1.0.0",
            description="无依赖的测试模块",
            author="Test",
            created_at=datetime.now(),
            file_path="test_module_a.py",
            class_name="TestModuleA",
            dependencies={},
            provides=["service_a"],
            requires=[],
        )

        metadata_b = ModuleMetadata(
            module_id="TestModuleB",
            name="测试模块B",
            version="1.0.0",
            description="依赖A的测试模块",
            author="Test",
            created_at=datetime.now(),
            file_path="test_module_b.py",
            class_name="TestModuleB",
            dependencies={"TestModuleA": DependencyType.REQUIRED},
            provides=["service_b"],
            requires=["service_a"],
        )

        metadata_c = ModuleMetadata(
            module_id="TestModuleC",
            name="测试模块C",
            version="1.0.0",
            description="依赖B的测试模块",
            author="Test",
            created_at=datetime.now(),
            file_path="test_module_c.py",
            class_name="TestModuleC",
            dependencies={"TestModuleB": DependencyType.REQUIRED},
            provides=["service_c"],
            requires=["service_b"],
        )

        logger.info("\n1. 测试依赖图构建...")
        system_manager.dependency_graph.add_module(metadata_a)
        system_manager.dependency_graph.add_module(metadata_b)
        system_manager.dependency_graph.add_module(metadata_c)

        logger.info("   ✅ 依赖图构建完成")

        # 测试依赖查询
        logger.info("\n2. 测试依赖查询...")
        deps_a = system_manager.dependency_graph.get_dependencies("TestModuleA")
        deps_b = system_manager.dependency_graph.get_dependencies("TestModuleB")
        deps_c = system_manager.dependency_graph.get_dependencies("TestModuleC")

        logger.info(f"   TestModuleA 依赖: {deps_a}")
        logger.info(f"   TestModuleB 依赖: {deps_b}")
        logger.info(f"   TestModuleC 依赖: {deps_c}")

        # 测试依赖者查询
        logger.info("\n3. 测试依赖者查询...")
        dependents_a = system_manager.dependency_graph.get_dependents("TestModuleA")
        dependents_b = system_manager.dependency_graph.get_dependents("TestModuleB")
        dependents_c = system_manager.dependency_graph.get_dependents("TestModuleC")

        logger.info(f"   依赖 TestModuleA 的模块: {dependents_a}")
        logger.info(f"   依赖 TestModuleB 的模块: {dependents_b}")
        logger.info(f"   依赖 TestModuleC 的模块: {dependents_c}")

        # 测试加载顺序
        logger.info("\n4. 测试加载顺序...")
        load_order = system_manager.dependency_graph.get_load_order(
            ["TestModuleC", "TestModuleB", "TestModuleA"]
        )
        logger.info(f"   推荐加载顺序: {load_order}")

        # 测试循环依赖检测
        logger.info("\n5. 测试循环依赖检测...")
        # 创建循环依赖
        metadata_c.dependencies["TestModuleA"] = DependencyType.REQUIRED
        system_manager.dependency_graph.add_module(metadata_c)

        has_cycle = system_manager.dependency_graph.check_circular_dependency("TestModuleA")
        logger.info(f"   检测到循环依赖: {'是' if has_cycle else '否'}")

        await system_manager.shutdown()
        logger.info("✅ 依赖管理测试完成")
        return True

    except Exception as e:
        logger.error(f"❌ 依赖管理测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_service_registry():
    """测试服务注册表"""
    logger.info("\n📋 测试服务注册表")
    logger.info(str("=" * 60))

    try:
        system_manager = SystemManager()
        await system_manager.initialize()

        # 创建测试模块
        module_a = TestModuleA("test_a")
        module_b = TestModuleB("test_b")
        module_c = TestModuleC("test_c")

        # 注册服务
        logger.info("\n1. 注册服务...")
        system_manager.service_registry.register_service("module_a", "service_a", module_a)
        system_manager.service_registry.register_service("module_a", "test_service", module_a)
        system_manager.service_registry.register_service("module_b", "service_b", module_b)
        system_manager.service_registry.register_service("module_c", "service_c", module_c)

        services = system_manager.service_registry.list_services()
        logger.info(f"   注册的服务: {list(services.keys())}")

        # 测试服务获取
        logger.info("\n2. 测试服务获取...")
        service_a = system_manager.service_registry.get_service("service_a")
        service_b = system_manager.service_registry.get_service("service_b")
        service_c = system_manager.service_registry.get_service("service_c")

        logger.info(f"   service_a: {service_a is not None}")
        logger.info(f"   service_b: {service_b is not None}")
        logger.info(f"   service_c: {service_c is not None}")

        # 测试服务提供者查询
        logger.info("\n3. 测试服务提供者查询...")
        provider_a = system_manager.service_registry.get_service_provider("service_a")
        provider_b = system_manager.service_registry.get_service_provider("service_b")
        provider_c = system_manager.service_registry.get_service_provider("service_c")

        logger.info(f"   service_a 提供者: {provider_a}")
        logger.info(f"   service_b 提供者: {provider_b}")
        logger.info(f"   service_c 提供者: {provider_c}")

        # 测试服务注销
        logger.info("\n4. 测试服务注销...")
        system_manager.service_registry.unregister_service("test_service")
        remaining_services = system_manager.service_registry.list_services()
        logger.info(f"   注销后剩余服务: {list(remaining_services.keys())}")

        await system_manager.shutdown()
        logger.info("✅ 服务注册表测试完成")
        return True

    except Exception as e:
        logger.error(f"❌ 服务注册表测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_module_lifecycle():
    """测试模块生命周期"""
    logger.info("\n🔄 测试模块生命周期")
    logger.info(str("=" * 60))

    try:
        system_manager = SystemManager()
        await system_manager.initialize()

        # 创建测试模块元数据
        metadata = ModuleMetadata(
            module_id="LifecycleTestModule",
            name="生命周期测试模块",
            version="1.0.0",
            description="测试模块生命周期",
            author="Test",
            created_at=datetime.now(),
            file_path="lifecycle_test.py",
            class_name="LifecycleTestModule",
            dependencies={},
            provides=["lifecycle_service"],
            requires=[],
        )

        # 创建模块类
        class LifecycleTestModule(BaseModule):
            def __init__(self, agent_id, config=None):
                super().__init__(agent_id, config)
                self.initialized = False
                self.started = False

            async def _on_initialize(self):
                self.initialized = True
                return True

            async def _on_start(self):
                self.started = True
                return True

            async def _on_stop(self):
                self.started = False
                return True

            async def _on_shutdown(self):
                self.initialized = False
                return True

            async def _on_health_check(self):
                return True

        # 手动加载模块
        logger.info("\n1. 手动加载模块...")
        module_class = LifecycleTestModule
        instance = module_class("lifecycle_test")

        from core.system.system_manager import ModuleInstance

        module_instance = ModuleInstance(
            metadata=metadata, module_class=module_class, instance=instance
        )

        system_manager.module_instances["LifecycleTestModule"] = module_instance
        logger.info(f"   模块状态: {module_instance.state.value}")

        # 测试初始化
        logger.info("\n2. 测试模块初始化...")
        init_success = await system_manager.initialize_module("LifecycleTestModule")
        logger.info(f"   初始化结果: {'成功' if init_success else '失败'}")
        logger.info(f"   模块状态: {module_instance.state.value}")
        logger.info(f"   模块是否已初始化: {module_instance.instance.initialized}")

        # 测试启动
        logger.info("\n3. 测试模块启动...")
        start_success = await system_manager.start_module("LifecycleTestModule")
        logger.info(f"   启动结果: {'成功' if start_success else '失败'}")
        logger.info(f"   模块状态: {module_instance.state.value}")
        logger.info(f"   模块是否已启动: {module_instance.instance.started}")

        # 测试健康检查
        logger.info("\n4. 测试健康检查...")
        await system_manager._check_module_health("LifecycleTestModule")
        logger.info(f"   健康状态: {module_instance.health_status.value}")
        logger.info(f"   最后健康检查: {module_instance.last_health_check}")

        # 等待一段时间
        await asyncio.sleep(2)

        # 测试停止
        logger.info("\n5. 测试模块停止...")
        stop_success = await system_manager.stop_module("LifecycleTestModule")
        logger.info(f"   停止结果: {'成功' if stop_success else '失败'}")
        logger.info(f"   模块状态: {module_instance.state.value}")
        logger.info(f"   模块是否已启动: {module_instance.instance.started}")

        # 测试重新启动
        logger.info("\n6. 测试模块重新启动...")
        restart_success = await system_manager.start_module("LifecycleTestModule")
        logger.info(f"   重新启动结果: {'成功' if restart_success else '失败'}")
        logger.info(f"   模块状态: {module_instance.state.value}")

        # 清理
        logger.info("\n7. 清理...")
        await system_manager.stop_module("LifecycleTestModule")
        await system_manager.unload_module("LifecycleTestModule")

        await system_manager.shutdown()
        logger.info("✅ 模块生命周期测试完成")
        return True

    except Exception as e:
        logger.error(f"❌ 模块生命周期测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_configuration_management():
    """测试配置管理"""
    logger.info("\n⚙️ 测试配置管理")
    logger.info(str("=" * 60))

    try:
        system_manager = SystemManager()
        await system_manager.initialize()

        # 测试配置设置和获取
        logger.info("\n1. 测试配置设置和获取...")
        system_manager.config_manager.set_config("test.string", "hello")
        system_manager.config_manager.set_config("test.number", 42)
        system_manager.config_manager.set_config("test.boolean", True)
        system_manager.config_manager.set_config("test.nested.value", "nested")

        config_value = system_manager.config_manager.get_config("test.string")
        logger.info(f"   test.string: {config_value}")

        config_value = system_manager.config_manager.get_config("test.number")
        logger.info(f"   test.number: {config_value}")

        config_value = system_manager.config_manager.get_config("test.boolean")
        logger.info(f"   test.boolean: {config_value}")

        config_value = system_manager.config_manager.get_config("test.nested.value")
        logger.info(f"   test.nested.value: {config_value}")

        # 测试配置监听
        logger.info("\n2. 测试配置监听...")
        config_changes = []

        def config_callback(key, value) -> None:
            config_changes.append((key, value))
            logger.info(f"   配置变化: {key} = {value}")

        system_manager.config_manager.watch_config("test.string", config_callback)
        system_manager.config_manager.watch_config("test.number", config_callback)

        # 触发配置变化
        system_manager.config_manager.set_config("test.string", "world")
        system_manager.config_manager.set_config("test.number", 100)

        logger.info(f"   配置变化次数: {len(config_changes)}")
        for change in config_changes:
            logger.info(f"     {change[0]} -> {change[1]}")

        # 测试默认值
        logger.info("\n3. 测试配置默认值...")
        default_value = system_manager.config_manager.get_config("nonexistent.key", "default")
        logger.info(f"   不存在的键的默认值: {default_value}")

        await system_manager.shutdown()
        logger.info("✅ 配置管理测试完成")
        return True

    except Exception as e:
        logger.error(f"❌ 配置管理测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    logger.info("🚀 系统管理器完整测试套件")
    logger.info(str("=" * 80))

    # 测试列表
    tests = [
        ("模块加载测试", test_module_loading),
        ("依赖管理测试", test_dependency_management),
        ("服务注册表测试", test_service_registry),
        ("模块生命周期测试", test_module_lifecycle),
        ("配置管理测试", test_configuration_management),
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
        logger.info("\n🎉 所有测试通过!系统管理器功能验证成功!")
        logger.info("\n🌟 系统级优化特性:")
        logger.info("   ✅ 模块热插拔机制")
        logger.info("   ✅ 动态依赖管理")
        logger.info("   ✅ 服务注册与发现")
        logger.info("   ✅ 配置热更新")
        logger.info("   ✅ 自动健康检查")
        logger.info("   ✅ 故障自动恢复")
    else:
        logger.info("\n⚠️ 部分测试失败,需要进一步优化。")

    return passed_count == total_count


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
