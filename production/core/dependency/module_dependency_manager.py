#!/usr/bin/env python3
"""
模块依赖管理系统
Module Dependency Management System

管理Athena系统中各个模块的启动依赖关系,确保正确的启动顺序
作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

from __future__ import annotations
import asyncio
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import networkx as nx

from core.logging_config import setup_logging

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.base_module import BaseModule, HealthStatus, ModuleStatus

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

class ModulePriority(Enum):
    """模块优先级"""
    CRITICAL = 1      # 核心基础模块(如感知、认知)
    HIGH = 2         # 重要功能模块(如执行、学习)
    NORMAL = 3       # 一般功能模块(如通信、评估)
    LOW = 4          # 辅助功能模块(如知识库、工具)

class DependencyType(Enum):
    """依赖类型"""
    REQUIRED = 'required'       # 必需依赖
    OPTIONAL = 'optional'       # 可选依赖
    CONFLICT = 'conflict'       # 冲突依赖

@dataclass
class ModuleDependency:
    """模块依赖关系"""
    module_id: str
    depends_on: str
    dependency_type: DependencyType
    description: str = ''

@dataclass
class ModuleInfo:
    """模块信息"""
    module_id: str
    module_name: str
    module_class: type
    priority: ModulePriority
    required: bool = True
    config: dict[str, Any] | None = None
    auto_start: bool = True
    startup_timeout: float = 30.0
    dependencies: list[ModuleDependency] = field(default_factory=list)
    instance: BaseModule | None = None
    status: ModuleStatus = ModuleStatus.UNINITIALIZED
    initialized_at: datetime | None = None
    startup_time: float = 0.0

@dataclass
class StartupPlan:
    """启动计划"""
    startup_order: list[str]
    parallel_groups: list[list[str]]
    total_estimated_time: float
    critical_path: list[str]

class ModuleDependencyManager:
    """模块依赖管理器"""

    def __init__(self, config: dict[str, Any] | None = None):
        """
        初始化依赖管理器

        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.modules: dict[str, ModuleInfo] = {}
        self.dependency_graph = nx.DiGraph()
        self.startup_history: list[dict[str, Any]] = []

        # 配置参数
        self.default_timeout = self.config.get('default_timeout', 30.0)
        self.enable_parallel_startup = self.config.get('enable_parallel_startup', True)
        self.health_check_interval = self.config.get('health_check_interval', 5.0)

        logger.info('🔗 模块依赖管理器初始化完成')

    def register_module(self, module_info: ModuleInfo) -> Any:
        """
        注册模块

        Args:
            module_info: 模块信息
        """
        self.modules[module_info.module_id] = module_info
        self.dependency_graph.add_node(module_info.module_id, module_info=module_info)

        # 添加依赖关系到图
        for dep in module_info.dependencies:
            if dep.dependency_type == DependencyType.REQUIRED:
                self.dependency_graph.add_edge(dep.depends_on, module_info.module_id, dependency=dep)

        logger.info(f"📝 注册模块: {module_info.module_id} ({module_info.module_name})")

    def register_dependency(self, module_id: str, depends_on: str,
                           dependency_type: DependencyType = DependencyType.REQUIRED,
                           description: str = ''):
        """
        注册模块依赖关系

        Args:
            module_id: 模块ID
            depends_on: 依赖的模块ID
            dependency_type: 依赖类型
            description: 依赖描述
        """
        if module_id not in self.modules:
            raise ValueError(f"模块未注册: {module_id}")

        dependency = ModuleDependency(
            module_id=module_id,
            depends_on=depends_on,
            dependency_type=dependency_type,
            description=description
        )

        self.modules[module_id].dependencies.append(dependency)

        if dependency_type == DependencyType.REQUIRED:
            self.dependency_graph.add_edge(depends_on, module_id, dependency=dependency)

        logger.info(f"🔗 注册依赖: {module_id} -> {depends_on} ({dependency_type.value})")

    def create_startup_plan(self) -> StartupPlan:
        """
        创建启动计划

        Returns:
            启动计划
        """
        try:
            # 检查循环依赖
            if not nx.is_directed_acyclic_graph(self.dependency_graph):
                cycles = list(nx.simple_cycles(self.dependency_graph))
                raise ValueError(f"检测到循环依赖: {cycles}")

            # 按优先级分组
            priority_groups = {}
            for module_id, module_info in self.modules.items():
                if module_info.auto_start:
                    priority = module_info.priority.value
                    if priority not in priority_groups:
                        priority_groups[priority] = []
                    priority_groups[priority].append(module_id)

            # 获取拓扑排序
            startup_order = list(nx.topological_sort(self.dependency_graph))

            # 过滤出需要自动启动的模块
            startup_order = [mid for mid in startup_order
                           if mid in self.modules and self.modules[mid].auto_start]

            # 创建并行启动组
            parallel_groups = self._create_parallel_groups(startup_order)

            # 计算预估时间
            total_time = sum(
                self.modules[mid].startup_timeout
                for mid in startup_order if mid in self.modules
            )

            # 获取关键路径
            critical_path = self._get_critical_path()

            plan = StartupPlan(
                startup_order=startup_order,
                parallel_groups=parallel_groups,
                total_estimated_time=total_time,
                critical_path=critical_path
            )

            logger.info("📋 启动计划创建完成:")
            logger.info(f"   - 启动顺序: {len(startup_order)} 个模块")
            logger.info(f"   - 并行组数: {len(parallel_groups)}")
            logger.info(f"   - 预估时间: {total_time:.1f}s")

            return plan

        except Exception as e:
            logger.error(f"❌ 创建启动计划失败: {e}")
            raise

    async def execute_startup_plan(self, plan: StartupPlan) -> dict[str, Any]:
        """
        执行启动计划

        Args:
            plan: 启动计划

        Returns:
            启动结果
        """
        startup_results = {
            'success': True,
            'started_modules': [],
            'failed_modules': [],
            'skipped_modules': [],
            'total_time': 0.0,
            'details': {}
        }

        start_time = datetime.now()

        try:
            logger.info('🚀 开始执行启动计划...')

            if self.enable_parallel_startup:
                # 并行启动
                for group in plan.parallel_groups:
                    group_result = await self._startup_group_parallel(group)
                    startup_results['started_modules'].extend(group_result['started'])
                    startup_results['failed_modules'].extend(group_result['failed'])

                    # 如果关键模块失败,停止启动
                    critical_failed = self._check_critical_failures(group_result['failed'])
                    if critical_failed:
                        startup_results['success'] = False
                        break
            else:
                # 顺序启动
                for module_id in plan.startup_order:
                    if module_id in self.modules:
                        result = await self._startup_single_module(module_id)
                        if result['success']:
                            startup_results['started_modules'].append(module_id)
                        else:
                            startup_results['failed_modules'].append(module_id)

                            # 如果是必需模块,停止启动
                            if self.modules[module_id].required:
                                startup_results['success'] = False
                                break

            # 计算总时间
            startup_results['total_time'] = (datetime.now() - start_time).total_seconds()

            # 记录启动历史
            self._record_startup_history(startup_results)

            logger.info("✅ 启动计划执行完成:")
            logger.info(f"   - 成功: {len(startup_results['started_modules'])}")
            logger.info(f"   - 失败: {len(startup_results['failed_modules'])}")
            logger.info(f"   - 总时间: {startup_results['total_time']:.1f}s")

            return startup_results

        except Exception as e:
            logger.error(f"❌ 执行启动计划失败: {e}")
            startup_results['success'] = False
            startup_results['error'] = str(e)
            return startup_results

    async def startup_module(self, module_id: str, config: dict[str, Any] | None = None) -> bool:
        """
        启动单个模块

        Args:
            module_id: 模块ID
            config: 模块配置

        Returns:
            启动是否成功
        """
        if module_id not in self.modules:
            logger.error(f"模块未注册: {module_id}")
            return False

        self.modules[module_id]
        result = await self._startup_single_module(module_id, config)

        return result['success']

    async def shutdown_all(self) -> dict[str, Any]:
        """
        关闭所有模块

        Returns:
            关闭结果
        """
        shutdown_results = {
            'success': True,
            'shutdown_modules': [],
            'failed_modules': [],
            'total_time': 0.0
        }

        start_time = datetime.now()

        try:
            logger.info('🔄 开始关闭所有模块...')

            # 按启动顺序的逆序关闭
            shutdown_order = list(reversed(self._get_loaded_modules()))

            for module_id in shutdown_order:
                if module_id in self.modules and self.modules[module_id].instance:
                    try:
                        await self.modules[module_id].instance.shutdown()
                        shutdown_results['shutdown_modules'].append(module_id)
                        logger.info(f"✅ 模块已关闭: {module_id}")
                    except Exception as e:
                        logger.error(f"❌ 模块关闭失败 {module_id}: {e}")
                        shutdown_results['failed_modules'].append(module_id)

            shutdown_results['total_time'] = (datetime.now() - start_time).total_seconds()

            logger.info("✅ 所有模块关闭完成")
            return shutdown_results

        except Exception as e:
            logger.error(f"❌ 关闭模块失败: {e}")
            shutdown_results['success'] = False
            return shutdown_results

    def get_dependency_graph(self) -> dict[str, Any]:
        """
        获取依赖图信息

        Returns:
            依赖图信息
        """
        return {
            'nodes': len(self.dependency_graph.nodes),
            'edges': len(self.dependency_graph.edges),
            'is_acyclic': nx.is_directed_acyclic_graph(self.dependency_graph),
            'modules': {
                module_id: {
                    'name': info.module_name,
                    'priority': info.priority.value,
                    'required': info.required,
                    'dependencies': len(info.dependencies),
                    'status': info.status.value
                }
                for module_id, info in self.modules.items()
            }
        }

    def get_module_status(self) -> dict[str, Any]:
        """
        获取所有模块状态

        Returns:
            模块状态信息
        """
        status_summary = {
            'uninitialized': 0,
            'initializing': 0,
            'ready': 0,
            'running': 0,
            'paused': 0,
            'error': 0,
            'stopping': 0,
            'stopped': 0
        }

        module_statuses = {}
        for module_id, module_info in self.modules.items():
            status = module_info.status.value
            status_summary[status] += 1

            module_statuses[module_id] = {
                'name': module_info.module_name,
                'status': status,
                'initialized_at': module_info.initialized_at.isoformat() if module_info.initialized_at else None,
                'startup_time': module_info.startup_time,
                'instance_created': module_info.instance is not None
            }

        return {
            'summary': status_summary,
            'modules': module_statuses
        }

    # 私有方法
    def _create_parallel_groups(self, startup_order: list[str]) -> list[list[str]]:
        """创建并行启动组"""
        groups = []
        current_group = []
        current_level = 0

        # 计算每个模块的依赖层级
        levels = {}
        for module_id in startup_order:
            if module_id not in self.dependency_graph:
                continue

            # 计算到根节点的最长路径
            try:
                level = len(list(nx.all_simple_paths(
                    self.dependency_graph,
                    self._get_root_node(),
                    module_id
                ))) - 1
                levels[module_id] = level
            except nx.NetworkXNoPath:
                levels[module_id] = 0

        # 按层级分组
        for module_id in startup_order:
            if module_id not in levels:
                continue

            level = levels[module_id]
            if level > current_level:
                if current_group:
                    groups.append(current_group)
                current_group = [module_id]
                current_level = level
            else:
                current_group.append(module_id)

        if current_group:
            groups.append(current_group)

        return groups

    def _get_root_node(self) -> str | None:
        """获取根节点(没有依赖的模块)"""
        for node in self.dependency_graph.nodes:
            if self.dependency_graph.in_degree(node) == 0:
                return node
        return None

    def _get_critical_path(self) -> list[str]:
        """获取关键路径"""
        try:
            # 计算最长路径
            longest_path = nx.dag_longest_path(self.dependency_graph)
            return longest_path if longest_path else []
        except Exception:  # TODO
            return []

    async def _startup_group_parallel(self, module_ids: list[str]) -> dict[str, Any]:
        """并行启动一组模块"""
        group_result = {
            'started': [],
            'failed': []
        }

        # 创建启动任务
        tasks = []
        for module_id in module_ids:
            if module_id in self.modules:
                task = self._startup_single_module(module_id)
                tasks.append((module_id, task))

        # 并行执行
        if tasks:
            results = await asyncio.gather(
                *[task for _, task in tasks],
                return_exceptions=True
            )

            for i, (module_id, _) in enumerate(tasks):
                result = results[i]
                if isinstance(result, Exception):
                    logger.error(f"❌ 模块启动异常 {module_id}: {result}")
                    group_result['failed'].append(module_id)
                elif result['success']:
                    group_result['started'].append(module_id)
                else:
                    group_result['failed'].append(module_id)

        return group_result

    async def _startup_single_module(self, module_id: str,
                                   config: dict[str, Any] | None = None) -> dict[str, Any]:
        """启动单个模块"""
        module_info = self.modules[module_id]

        if module_info.instance:
            logger.info(f"⚠️ 模块已存在: {module_id}")
            return {'success': True, 'already_exists': True}

        try:
            logger.info(f"🔧 启动模块: {module_id}")
            module_info.status = ModuleStatus.INITIALIZING
            start_time = datetime.now()

            # 创建模块实例
            module_config = config or module_info.config or {}
            instance = module_info.module_class(
                agent_id=f"agent_{module_id}",
                config=module_config
            )

            # 初始化模块
            init_success = await instance.initialize()
            if not init_success:
                raise Exception('模块初始化失败')

            # 启动模块
            if hasattr(instance, 'start'):
                start_success = await instance.start()
                if not start_success:
                    raise Exception('模块启动失败')

            # 健康检查
            health_status = await instance.health_check()
            if health_status == HealthStatus.UNHEALTHY:
                logger.warning(f"⚠️ 模块健康检查失败: {module_id}")

            # 更新状态
            module_info.instance = instance
            module_info.status = ModuleStatus.READY
            module_info.initialized_at = datetime.now()
            module_info.startup_time = (datetime.now() - start_time).total_seconds()

            logger.info(f"✅ 模块启动成功: {module_id} ({module_info.startup_time:.2f}s)")
            return {'success': True, 'startup_time': module_info.startup_time}

        except Exception as e:
            logger.error(f"❌ 模块启动失败 {module_id}: {e}")
            module_info.status = ModuleStatus.ERROR
            return {'success': False, 'error': str(e)}

    def _check_critical_failures(self, failed_modules: list[str]) -> bool:
        """检查是否有关键模块失败"""
        for module_id in failed_modules:
            if module_id in self.modules and self.modules[module_id].required:
                return True
        return False

    def _get_loaded_modules(self) -> list[str]:
        """获取已加载的模块列表"""
        loaded = []
        for module_id, module_info in self.modules.items():
            if module_info.instance is not None:
                loaded.append(module_id)
        return loaded

    def _record_startup_history(self, results: dict[str, Any]) -> Any:
        """记录启动历史"""
        history_entry = {
            'timestamp': datetime.now().isoformat(),
            'success': results['success'],
            'started_modules': results['started_modules'],
            'failed_modules': results['failed_modules'],
            'total_time': results['total_time']
        }

        self.startup_history.append(history_entry)

        # 限制历史记录数量
        if len(self.startup_history) > 100:
            self.startup_history = self.startup_history[-100:]

# 预定义的核心模块依赖关系
CORE_MODULE_DEPENDENCIES = {
    'perception': [],  # 感知模块无依赖
    'memory': ['perception'],  # 记忆依赖感知
    'cognition': ['perception', 'memory'],  # 认知依赖感知和记忆
    'execution': ['cognition', 'memory'],  # 执行依赖认知和记忆
    'learning': ['cognition', 'memory', 'execution'],  # 学习依赖认知、记忆、执行
    'communication': ['cognition'],  # 通信依赖认知
    'evaluation': ['cognition', 'execution'],  # 评估依赖认知和执行
    'knowledge_tools': ['cognition', 'memory']  # 知识工具依赖认知和记忆
}

# 导出
__all__ = [
    'ModuleDependencyManager',
    'ModuleInfo',
    'ModuleDependency',
    'StartupPlan',
    'ModulePriority',
    'DependencyType',
    'CORE_MODULE_DEPENDENCIES'
]
