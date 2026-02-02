#!/usr/bin/env python3
"""
系统管理器 - 主管理器类
System Manager - Main Manager

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0
"""

import asyncio
import importlib.util
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from .config_manager import ConfigurationManager
from .dependency_graph import DependencyGraph
from .module_loader import ModuleLoader
from .service_registry import ServiceRegistry
from .types import (
    DependencyType,
    HealthStatus,
    ModuleInstance,
    ModuleMetadata,
    ModuleState,
)

logger = logging.getLogger(__name__)


# 基础模块接口
class BaseModule:
    """基础模块接口"""

    def __init__(self, module_id: str, config: dict[str, Any] | None = None):
        """初始化模块

        Args:
            module_id: 模块ID
            config: 模块配置
        """
        self.module_id = module_id
        self.config = config or {}

    async def initialize(self) -> bool:
        """初始化模块

        Returns:
            是否初始化成功
        """
        return True

    async def start(self) -> bool:
        """启动模块

        Returns:
            是否启动成功
        """
        return True

    async def stop(self) -> bool:
        """停止模块

        Returns:
            是否停止成功
        """
        return True

    async def health_check(self) -> HealthStatus:
        """健康检查

        Returns:
            健康状态
        """
        return HealthStatus.HEALTHY


class SystemManager:
    """系统管理器

    负责模块的加载、初始化、启动、停止和卸载，
    支持热更新、依赖管理、服务注册和健康检查。
    """

    def __init__(self, config_path: str | Path | None = None):
        """初始化系统管理器

        Args:
            config_path: 配置文件路径
        """
        # 核心组件
        self.config_manager = ConfigurationManager(config_path)
        self.dependency_graph = DependencyGraph()
        self.service_registry = ServiceRegistry()
        self.module_loader = ModuleLoader()

        # 模块管理
        self.module_instances: dict[str, ModuleInstance] = {}
        self.module_loader.add_module_path(Path(__file__).parent.parent)

        # 系统状态
        self.system_state = {
            "loaded_modules": 0,
            "running_modules": 0,
            "failed_modules": 0,
            "total_services": 0,
        }

        # 统计信息
        self.statistics = {
            "module_loads": 0,
            "module_unloads": 0,
            "service_registrations": 0,
            "module_reloads": 0,
            "health_checks": 0,
            "auto_recoveries": 0,
        }

        # 后台任务
        self.background_tasks: list[asyncio.Task] = []
        self.shutdown_event = asyncio.Event()

        # 运行状态
        self.running = False
        self.logger = logging.getLogger(__name__)

        logger.info("系统管理器已创建")

    async def initialize(self):
        """初始化系统管理器"""
        if self.running:
            logger.warning("系统管理器已在运行")
            return

        logger.info("🚀 初始化系统管理器")

        # 加载配置
        if self.config_manager.config_path:
            self.config_manager.load_global_config()

        # 启动后台任务
        self.running = True
        self.background_tasks.append(
            asyncio.create_task(self._health_check_loop(), name="health_check_loop")
        )
        self.background_tasks.append(
            asyncio.create_task(self._auto_recovery_loop(), name="auto_recovery_loop")
        )

        logger.info("✅ 系统管理器初始化完成")

    async def load_module(
        self, module_path: str, config: dict[str, Any] | None = None
    ) -> bool:
        """加载模块

        Args:
            module_path: 模块文件路径
            config: 模块配置

        Returns:
            是否加载成功
        """
        try:
            # 扫描模块
            modules = self.module_loader.scan_modules(Path(module_path).parent)

            if not modules:
                logger.error(f"未找到模块: {module_path}")
                return False

            success = True
            for metadata in modules:
                if str(metadata.file_path) == module_path:
                    if await self._load_single_module(metadata, config):
                        self.statistics["module_loads"] += 1
                    else:
                        logger.error(f"❌ 模块加载失败: {metadata.module_id}")
                        success = False

            return success

        except Exception as e:
            logger.error(f"❌ 模块加载异常: {e}")
            return False

    async def _load_single_module(
        self, metadata: ModuleMetadata, config: dict[str, Any] | None = None
    ) -> bool:
        """加载单个模块"""
        try:
            # 检查依赖
            if not self._check_dependencies(metadata):
                logger.error(f"模块依赖检查失败: {metadata.module_id}")
                return False

            # 检查循环依赖
            if self.dependency_graph.check_circular_dependency(metadata.module_id):
                logger.error(f"检测到循环依赖: {metadata.module_id}")
                return False

            # 导入模块类
            spec = importlib.util.spec_from_file_location(
                metadata.module_id, metadata.file_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            module_class = getattr(module, metadata.class_name)

            # 创建模块实例
            instance = module_class(metadata.module_id, config or {})

            # 创建模块实例记录
            module_instance = ModuleInstance(
                metadata=metadata,
                module_class=module_class,
                instance=instance,
                state=ModuleState.LOADED,
                config=config or {},
            )

            # 添加到系统
            self.module_instances[metadata.module_id] = module_instance
            self.dependency_graph.add_module(metadata)

            # 更新系统状态
            self.system_state["loaded_modules"] += 1

            logger.debug(f"模块已加载: {metadata.module_id}")
            return True

        except Exception as e:
            logger.error(f"加载模块失败 {metadata.module_id}: {e}")
            return False

    def _check_dependencies(self, metadata: ModuleMetadata) -> bool:
        """检查模块依赖"""
        for dep_id, dep_type in metadata.dependencies.items():
            if dep_type == DependencyType.REQUIRED:
                if dep_id not in self.module_instances:
                    logger.error(f"缺少必需依赖: {dep_id}")
                    return False
                elif self.module_instances[dep_id].state not in [
                    ModuleState.READY,
                    ModuleState.RUNNING,
                ]:
                    logger.error(f"依赖未就绪: {dep_id}")
                    return False
            elif dep_type == DependencyType.CONFLICTS:
                if dep_id in self.module_instances:
                    logger.error(f"存在冲突依赖: {dep_id}")
                    return False

        return True

    async def initialize_module(self, module_id: str) -> bool:
        """初始化模块"""
        try:
            if module_id not in self.module_instances:
                logger.error(f"模块不存在: {module_id}")
                return False

            module_instance = self.module_instances[module_id]

            # 获取依赖顺序
            dependencies = self.dependency_graph.get_dependencies(module_id)
            load_order = self.dependency_graph.get_load_order(
                [module_id, *list(dependencies)]
            )

            # 按顺序初始化依赖
            for dep_id in load_order:
                if dep_id != module_id and dep_id in self.module_instances:
                    dep_instance = self.module_instances[dep_id]
                    if dep_instance.state == ModuleState.LOADED:
                        await self.initialize_module(dep_id)

            # 初始化目标模块
            module_instance.state = ModuleState.INITIALIZING
            success = await module_instance.instance.initialize()

            if success:
                module_instance.state = ModuleState.READY
                logger.info(f"✅ 模块初始化成功: {module_id}")
                return True
            else:
                module_instance.state = ModuleState.ERROR
                logger.error(f"❌ 模块初始化失败: {module_id}")
                return False

        except Exception as e:
            logger.error(f"初始化模块异常 {module_id}: {e}")
            if module_id in self.module_instances:
                self.module_instances[module_id].state = ModuleState.ERROR
            return False

    async def start_module(self, module_id: str) -> bool:
        """启动模块"""
        try:
            if module_id not in self.module_instances:
                logger.error(f"模块不存在: {module_id}")
                return False

            module_instance = self.module_instances[module_id]

            if module_instance.state != ModuleState.READY:
                logger.error(
                    f"模块状态不正确: {module_id} - {module_instance.state}"
                )
                return False

            # 启动模块
            module_instance.state = ModuleState.STARTING
            module_instance.start_time = datetime.now()

            success = await module_instance.instance.start()

            if success:
                module_instance.state = ModuleState.RUNNING
                module_instance.last_health_check = datetime.now()

                # 注册服务
                for service_name in module_instance.metadata.provides:
                    self.service_registry.register_service(
                        module_id, service_name, module_instance.instance
                    )
                    self.statistics["service_registrations"] += 1

                self.system_state["running_modules"] += 1
                self.system_state["total_services"] += len(
                    module_instance.metadata.provides
                )

                logger.info(f"✅ 模块启动成功: {module_id}")
                return True
            else:
                module_instance.state = ModuleState.ERROR
                self.system_state["failed_modules"] += 1
                logger.error(f"❌ 模块启动失败: {module_id}")
                return False

        except Exception as e:
            logger.error(f"启动模块异常 {module_id}: {e}")
            return False

    async def stop_module(self, module_id: str) -> bool:
        """停止模块"""
        try:
            if module_id not in self.module_instances:
                logger.error(f"模块不存在: {module_id}")
                return False

            module_instance = self.module_instances[module_id]

            if module_instance.state != ModuleState.RUNNING:
                logger.warning(f"模块未运行: {module_id}")
                return True

            # 停止模块
            module_instance.state = ModuleState.STOPPING
            success = await module_instance.instance.stop()

            if success:
                # 注销服务
                for service_name in module_instance.metadata.provides:
                    self.service_registry.unregister_service(service_name)

                module_instance.state = ModuleState.STOPPED
                self.system_state["running_modules"] -= 1

                logger.info(f"✅ 模块停止成功: {module_id}")
                return True
            else:
                module_instance.state = ModuleState.ERROR
                logger.error(f"❌ 模块停止失败: {module_id}")
                return False

        except Exception as e:
            logger.error(f"停止模块异常 {module_id}: {e}")
            return False

    async def unload_module(self, module_id: str) -> bool:
        """卸载模块"""
        try:
            if module_id not in self.module_instances:
                logger.error(f"模块不存在: {module_id}")
                return False

            module_instance = self.module_instances[module_id]

            # 先停止模块
            if module_instance.state == ModuleState.RUNNING:
                await self.stop_module(module_id)

            # 关闭模块
            if hasattr(module_instance.instance, "shutdown"):
                await module_instance.instance.shutdown()

            # 从系统中移除
            del self.module_instances[module_id]
            self.dependency_graph.remove_module(module_id)
            self.system_state["loaded_modules"] -= 1

            self.statistics["module_unloads"] += 1
            logger.info(f"✅ 模块卸载成功: {module_id}")
            return True

        except Exception as e:
            logger.error(f"卸载模块异常 {module_id}: {e}")
            return False

    async def reload_module(self, module_id: str) -> bool:
        """重新加载模块"""
        try:
            if module_id not in self.module_instances:
                logger.error(f"模块不存在: {module_id}")
                return False

            module_instance = self.module_instances[module_id]
            metadata = module_instance.metadata
            config = module_instance.config

            # 卸载模块
            await self.unload_module(module_id)

            # 重新加载模块文件
            if self.module_loader.check_file_changes(metadata.file_path):
                modules = self.module_loader.scan_modules(
                    Path(metadata.file_path).parent
                )
                for new_metadata in modules:
                    if new_metadata.module_id == module_id:
                        metadata = new_metadata
                        break

            # 重新加载模块
            if await self._load_single_module(metadata, config):
                await self.initialize_module(module_id)
                await self.start_module(module_id)
                logger.info(f"✅ 模块重新加载成功: {module_id}")
                return True
            else:
                logger.error(f"❌ 模块重新加载失败: {module_id}")
                return False

        except Exception as e:
            logger.error(f"重新加载模块异常 {module_id}: {e}")
            return False

    async def _health_check_loop(self):
        """健康检查循环"""
        logger.info("🔄 启动健康检查循环")

        while not self.shutdown_event.is_set():
            try:
                for module_id, module_instance in self.module_instances.items():
                    if module_instance.state == ModuleState.RUNNING:
                        await self._check_module_health(module_id)

                await asyncio.sleep(30)  # 30秒检查间隔

            except Exception as e:
                logger.error(f"健康检查循环异常: {e}")
                await asyncio.sleep(60)

    async def _check_module_health(self, module_id: str):
        """检查模块健康状态"""
        try:
            module_instance = self.module_instances[module_id]
            health_status = await module_instance.instance.health_check()

            module_instance.last_health_check = datetime.now()
            module_instance.health_status = health_status
            self.statistics["health_checks"] += 1

            if health_status != HealthStatus.HEALTHY:
                module_instance.error_count += 1
                logger.warning(
                    f"模块健康检查失败: {module_id} - {health_status}"
                )

                # 自动重启
                if (
                    module_instance.error_count
                    >= module_instance.metadata.max_retries
                    and module_instance.metadata.auto_restart
                ):
                    logger.info(f"尝试自动重启模块: {module_id}")
                    await self._restart_module(module_id)

        except Exception as e:
            logger.error(f"模块健康检查异常 {module_id}: {e}")

    async def _restart_module(self, module_id: str):
        """重启模块"""
        try:
            logger.info(f"重启模块: {module_id}")

            await self.stop_module(module_id)
            await self.start_module(module_id)

            # 重置错误计数
            if module_id in self.module_instances:
                self.module_instances[module_id].error_count = 0

        except Exception as e:
            logger.error(f"重启模块失败 {module_id}: {e}")

    async def _auto_recovery_loop(self):
        """自动恢复循环"""
        logger.info("🔄 启动自动恢复循环")

        while not self.shutdown_event.is_set():
            try:
                # 检查失败模块
                for module_id, module_instance in self.module_instances.items():
                    if module_instance.state == ModuleState.ERROR:
                        logger.info(f"尝试恢复错误模块: {module_id}")
                        await self._recover_module(module_id)

                await asyncio.sleep(60)  # 1分钟检查间隔

            except Exception as e:
                logger.error(f"自动恢复循环异常: {e}")
                await asyncio.sleep(120)

    async def _recover_module(self, module_id: str):
        """恢复错误模块"""
        try:
            module_instance = self.module_instances[module_id]

            # 重置状态
            module_instance.state = ModuleState.LOADED
            module_instance.error_count = 0
            module_instance.last_error = None

            # 重新初始化和启动
            if await self.initialize_module(module_id):
                await self.start_module(module_id)
                self.statistics["auto_recoveries"] += 1
                logger.info(f"✅ 模块恢复成功: {module_id}")
            else:
                logger.error(f"❌ 模块恢复失败: {module_id}")

        except Exception as e:
            logger.error(f"恢复模块异常 {module_id}: {e}")

    def get_service(self, service_name: str) -> BaseModule | None:
        """获取服务"""
        return self.service_registry.get_service(service_name)

    def get_module_status(self, module_id: str) -> dict[str, Any] | None:
        """获取模块状态"""
        if module_id not in self.module_instances:
            return None

        module_instance = self.module_instances[module_id]
        return {
            "module_id": module_id,
            "state": module_instance.state.value,
            "health_status": module_instance.health_status.value,
            "last_health_check": (
                module_instance.last_health_check.isoformat()
                if module_instance.last_health_check
                else None
            ),
            "error_count": module_instance.error_count,
            "last_error": module_instance.last_error,
            "start_time": (
                module_instance.start_time.isoformat()
                if module_instance.start_time
                else None
            ),
            "uptime": (
                (datetime.now() - module_instance.start_time).total_seconds()
                if module_instance.start_time
                else 0
            ),
        }

    def get_system_status(self) -> dict[str, Any]:
        """获取系统状态"""
        return {
            "system_state": self.system_state,
            "statistics": self.statistics,
            "modules": {
                module_id: self.get_module_status(module_id)
                for module_id in self.module_instances
            },
            "services": self.service_registry.list_services(),
            "dependencies": {
                module_id: list(self.dependency_graph.get_dependencies(module_id))
                for module_id in self.module_instances
            },
        }

    async def shutdown(self):
        """关闭系统管理器"""
        try:
            logger.info("🔚 关闭系统管理器")

            # 停止所有模块
            for module_id in list(self.module_instances.keys()):
                await self.stop_module(module_id)

            # 关闭后台任务
            self.shutdown_event.set()
            for task in self.background_tasks:
                task.cancel()

            # 保存配置
            self.config_manager.save_config()

            self.running = False
            logger.info("✅ 系统管理器关闭成功")

        except Exception as e:
            logger.error(f"关闭系统管理器失败: {e}")


__all__ = ["BaseModule", "SystemManager"]
