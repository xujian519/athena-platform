#!/usr/bin/env python3
from __future__ import annotations
"""
统一工具注册表核心模块
Unified Tool Registry Core

整合所有工具注册表，提供统一的工具发现、访问和管理接口。

核心功能:
1. 单例模式 - 全局唯一实例
2. 懒加载机制 - 工具按需加载
3. 健康状态管理 - 工具健康检查
4. 自动发现机制 - 扫描@tool装饰器
5. 工具获取 - get/require接口

Author: Athena平台团队
Created: 2026-04-19
Version: v2.0.0
"""

import importlib
import logging
import threading
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

# 导入现有ToolRegistry作为基础
from core.tools.base import (
    ToolDefinition,
    ToolCategory,
    ToolPriority,
    get_global_registry,
)

logger = logging.getLogger(__name__)


class ToolHealthStatus(Enum):
    """工具健康状态"""

    HEALTHY = "healthy"  # 健康
    DEGRADED = "degraded"  # 降级
    UNHEALTHY = "unhealthy"  # 不健康
    UNKNOWN = "unknown"  # 未知


@dataclass
class LazyToolLoader:
    """
    懒加载工具配置

    工具在第一次使用时才加载，减少启动时间。
    """

    tool_id: str
    import_path: str  # 模块导入路径
    function_name: str  # 函数名
    metadata: dict[str, Any]  # 工具元数据
    _loaded: bool = False
    _instance: Any = None

    def load(self) -> Any:
        """加载工具"""
        if self._loaded:
            return self._instance

        try:
            # 动态导入模块
            module = importlib.import_module(self.import_path)

            # 获取函数
            func = getattr(module, self.function_name)

            # 缓存实例
            self._instance = func
            self._loaded = True

            logger.debug(f"✅ 懒加载工具: {self.tool_id}")
            return func

        except Exception as e:
            logger.error(f"❌ 加载工具失败 {self.tool_id}: {e}")
            raise


class UnifiedToolRegistry:
    """
    统一工具注册表

    整合所有工具注册表，提供统一的工具发现和访问接口。

    核心特性:
    - 单例模式：全局唯一实例
    - 懒加载：工具按需加载
    - 健康检查：工具状态监控
    - 自动发现：扫描@tool装饰器
    - 线程安全：使用RLock保证并发安全
    """

    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        """初始化统一工具注册表"""
        # 基础注册表（复用现有ToolRegistry）
        self._base_registry = get_global_registry()

        # 懒加载工具字典
        self._lazy_tools: dict[str, LazyToolLoader] = {}

        # 健康状态字典
        self._health_status: dict[str, ToolHealthStatus] = {}

        # 自动发现的工具列表
        self._discovered_tools: list[str] = []

        # 工具分组（支持ToolManager的group概念）
        self._tool_groups: dict[str, set[str]] = {}

        # 线程安全锁
        self._registry_lock = threading.RLock()

        # 初始化状态
        self._initialized = False

        logger.info("✅ 统一工具注册表已创建")

    @classmethod
    def get_instance(cls) -> "UnifiedToolRegistry":
        """
        获取单例实例

        Returns:
            UnifiedToolRegistry: 全局唯一实例
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    async def initialize(
        self,
        auto_discover: bool = True,
        scan_paths: list[str] | None = None,
    ) -> bool:
        """
        初始化统一工具注册表

        Args:
            auto_discover: 是否自动发现工具
            scan_paths: 扫描路径列表

        Returns:
            bool: 初始化是否成功
        """
        if self._initialized:
            logger.warning("⚠️ 统一工具注册表已初始化，跳过")
            return True

        logger.info("🚀 初始化统一工具注册表...")

        try:
            # 1. 加载现有工具（从base_registry）
            await self._load_existing_tools()

            # 2. 自动发现工具（如果启用）
            if auto_discover:
                await self._auto_discover_tools(scan_paths)

            # 3. 初始化健康状态
            self._initialize_health_status()

            self._initialized = True
            logger.info(f"✅ 统一工具注册表初始化完成，共注册 {self.get_total_count()} 个工具")
            return True

        except Exception as e:
            logger.error(f"❌ 初始化失败: {e}")
            import traceback

            traceback.print_exc()
            return False

    async def _load_existing_tools(self):
        """加载现有工具（从base_registry）"""
        logger.info("📦 加载现有工具...")

        # 基础注册表已经包含工具，无需额外操作
        # 这里只是为了日志记录
        stats = self._base_registry.get_statistics()
        logger.info(f"   已加载 {stats['total_tools']} 个工具")

    async def _auto_discover_tools(
        self, scan_paths: list[str] | None = None
    ):
        """
        自动发现工具

        扫描指定路径，查找@tool装饰器标记的函数。

        Args:
            scan_paths: 扫描路径列表
        """
        logger.info("🔍 自动发现工具...")

        # 默认扫描路径
        if scan_paths is None:
            scan_paths = [
                "core/tools",
                "core/search",
                "services",
                "tools",
            ]

        discovered_count = 0

        for scan_path in scan_paths:
            try:
                # 扫描Python文件
                path = Path(scan_path)
                if not path.exists():
                    continue

                for py_file in path.rglob("*.py"):
                    # 跳过__init__.py和测试文件
                    if (
                        py_file.name == "__init__.py"
                        or py_file.name.startswith("test_")
                        or "tests" in py_file.parts
                    ):
                        continue

                    # 扫描文件中的工具
                    discovered = await self._scan_file_for_tools(py_file)
                    discovered_count += discovered

            except Exception as e:
                logger.warning(f"⚠️ 扫描路径失败 {scan_path}: {e}")

        self._discovered_tools = list(self._lazy_tools.keys())
        logger.info(f"✅ 自动发现完成，共发现 {discovered_count} 个工具")

    async def _scan_file_for_tools(self, file_path: Path) -> int:
        """
        扫描文件查找工具

        查找@tool装饰器标记的函数。

        Args:
            file_path: 文件路径

        Returns:
            int: 发现的工具数量
        """
        try:
            # 读取文件内容
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # 解析AST
            import ast

            tree = ast.parse(content)

            discovered = 0

            # 遍历AST节点
            for node in ast.walk(tree):
                # 查找函数定义
                if isinstance(node, ast.FunctionDef):
                    # 检查是否有@tool装饰器
                    for decorator in node.decorator_list:
                        # 检查是否是tool装饰器
                        decorator_name = None

                        if isinstance(decorator, ast.Name):
                            decorator_name = decorator.id
                        elif isinstance(decorator, ast.Call):
                            if isinstance(decorator.func, ast.Name):
                                decorator_name = decorator.func.id

                        if decorator_name == "tool":
                            # 找到@tool装饰器
                            tool_id = f"{file_path.stem}.{node.name}"

                            # 获取文档字符串
                            docstring = ast.get_docstring(node) or ""

                            # 注册为懒加载工具
                            self.register_lazy(
                                tool_id=tool_id,
                                import_path=self._path_to_import(file_path),
                                function_name=node.name,
                                metadata={
                                    "description": docstring,
                                    "file": str(file_path),
                                    "line": node.lineno,
                                },
                            )

                            discovered += 1
                            break

            return discovered

        except Exception as e:
            logger.debug(f"扫描文件失败 {file_path}: {e}")
            return 0

    def _path_to_import(self, file_path: Path) -> str:
        """
        将文件路径转换为导入路径

        Args:
            file_path: 文件路径

        Returns:
            str: 导入路径
        """
        # 获取相对路径
        project_root = Path("/Users/xujian/Athena工作平台")
        try:
            rel_path = file_path.relative_to(project_root)
        except ValueError:
            # 文件不在项目根目录下
            rel_path = file_path

        # 转换为导入路径
        import_path = str(rel_path.with_suffix("")).replace("/", ".")

        return import_path

    def _initialize_health_status(self):
        """初始化健康状态"""
        logger.info("🏥 初始化健康状态...")

        # 所有工具初始状态为UNKNOWN
        for tool_id in self._base_registry._tools.keys():
            self._health_status[tool_id] = ToolHealthStatus.UNKNOWN

        # 懒加载工具也初始化为UNKNOWN
        for tool_id in self._lazy_tools.keys():
            self._health_status[tool_id] = ToolHealthStatus.UNKNOWN

    def register_lazy(
        self,
        tool_id: str,
        import_path: str,
        function_name: str,
        metadata: dict[str, Any],
    ) -> bool:
        """
        注册懒加载工具

        Args:
            tool_id: 工具ID
            import_path: 模块导入路径
            function_name: 函数名
            metadata: 工具元数据

        Returns:
            bool: 注册是否成功
        """
        with self._registry_lock:
            if tool_id in self._lazy_tools:
                logger.warning(f"⚠️ 懒加载工具已存在: {tool_id}")
                return False

            # 创建懒加载器
            loader = LazyToolLoader(
                tool_id=tool_id,
                import_path=import_path,
                function_name=function_name,
                metadata=metadata,
            )

            self._lazy_tools[tool_id] = loader
            self._health_status[tool_id] = ToolHealthStatus.UNKNOWN

            logger.debug(f"✅ 注册懒加载工具: {tool_id}")
            return True

    def register(
        self,
        tool: ToolDefinition,
    ) -> "UnifiedToolRegistry":
        """
        注册工具（同步接口，委托给base_registry）

        Args:
            tool: ToolDefinition对象

        Returns:
            self (支持链式调用)
        """
        with self._registry_lock:
            # 委托给base_registry
            self._base_registry.register(tool)

            # 初始化健康状态
            self._health_status[tool.tool_id] = ToolHealthStatus.UNKNOWN

            logger.debug(f"✅ 工具已注册: {tool.tool_id}")
            return self

    def get(self, tool_id: str) -> Any | None:
        """
        获取工具（支持懒加载）

        Args:
            tool_id: 工具ID

        Returns:
            工具实例，如果不存在返回None
        """
        with self._registry_lock:
            # 1. 检查懒加载工具
            if tool_id in self._lazy_tools:
                loader = self._lazy_tools[tool_id]
                try:
                    return loader.load()
                except Exception as e:
                    logger.error(f"❌ 加载懒加载工具失败 {tool_id}: {e}")
                    self._health_status[tool_id] = ToolHealthStatus.UNHEALTHY
                    return None

            # 2. 检查已注册工具
            tool = self._base_registry.get_tool(tool_id)
            if tool:
                return tool.handler if tool.handler else tool

            # 3. 工具不存在
            logger.warning(f"⚠️ 工具不存在: {tool_id}")
            return None

    def require(self, tool_id: str) -> Any:
        """
        获取工具（必须存在）

        Args:
            tool_id: 工具ID

        Returns:
            工具实例

        Raises:
            ValueError: 如果工具不存在
        """
        tool = self.get(tool_id)
        if tool is None:
            raise ValueError(f"工具不存在: {tool_id}")
        return tool

    def mark_unhealthy(self, tool_id: str, reason: str = ""):
        """
        标记工具为不健康

        Args:
            tool_id: 工具ID
            reason: 原因
        """
        with self._registry_lock:
            if tool_id in self._health_status:
                self._health_status[tool_id] = ToolHealthStatus.UNHEALTHY
                logger.warning(f"⚠️ 工具标记为不健康: {tool_id} ({reason})")

    def mark_healthy(self, tool_id: str):
        """
        标记工具为健康

        Args:
            tool_id: 工具ID
        """
        with self._registry_lock:
            if tool_id in self._health_status:
                self._health_status[tool_id] = ToolHealthStatus.HEALTHY
                logger.debug(f"✅ 工具标记为健康: {tool_id}")

    def get_health_status(self, tool_id: str) -> ToolHealthStatus:
        """
        获取工具健康状态

        Args:
            tool_id: 工具ID

        Returns:
            ToolHealthStatus: 健康状态
        """
        return self._health_status.get(tool_id, ToolHealthStatus.UNKNOWN)

    def is_healthy(self, tool_id: str) -> bool:
        """
        检查工具是否健康

        Args:
            tool_id: 工具ID

        Returns:
            bool: 是否健康
        """
        status = self.get_health_status(tool_id)
        return status in [ToolHealthStatus.HEALTHY, ToolHealthStatus.UNKNOWN]

    def find_by_category(
        self, category: ToolCategory, enabled_only: bool = True
    ) -> list[ToolDefinition]:
        """
        按分类查找工具

        Args:
            category: 工具分类
            enabled_only: 是否只返回启用的工具

        Returns:
            工具列表
        """
        return list(self._base_registry.find_by_category(category, enabled_only))

    def find_by_domain(self, domain: str, enabled_only: bool = True) -> list[ToolDefinition]:
        """
        按领域查找工具

        Args:
            domain: 领域名称
            enabled_only: 是否只返回启用的工具

        Returns:
            工具列表
        """
        return list(self._base_registry.find_by_domain(domain, enabled_only))

    def search_tools(
        self,
        category: ToolCategory | None = None,
        domain: str | None = None,
        tags: list[str] | None = None,
        min_priority: ToolPriority | None = None,
        enabled_only: bool = True,
    ) -> list[ToolDefinition]:
        """
        综合搜索工具

        Args:
            category: 工具分类 (可选)
            domain: 领域 (可选)
            tags: 标签列表 (可选)
            min_priority: 最低优先级 (可选)
            enabled_only: 是否只返回启用的工具

        Returns:
            匹配的工具列表
        """
        return self._base_registry.search_tools(
            category=category,
            domain=domain,
            tags=tags,
            min_priority=min_priority,
            enabled_only=enabled_only,
        )

    def get_total_count(self) -> int:
        """
        获取工具总数

        Returns:
            int: 工具总数
        """
        base_count = len(self._base_registry._tools)
        lazy_count = len(self._lazy_tools)
        return base_count + lazy_count

    def get_statistics(self) -> dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        base_stats = self._base_registry.get_statistics()

        return {
            "total_tools": self.get_total_count(),
            "base_tools": len(self._base_registry._tools),
            "lazy_tools": len(self._lazy_tools),
            "discovered_tools": len(self._discovered_tools),
            "health_distribution": self._get_health_distribution(),
            **base_stats,
        }

    def _get_health_distribution(self) -> dict[str, int]:
        """
        获取健康状态分布

        Returns:
            健康状态分布字典
        """
        distribution = {status.value: 0 for status in ToolHealthStatus}

        for status in self._health_status.values():
            distribution[status.value] += 1

        return distribution

    def get_health_report(self) -> dict[str, dict[str, Any]]:
        """
        获取健康报告

        Returns:
            健康报告字典
        """
        report = {}

        for tool_id, status in self._health_status.items():
            report[tool_id] = {
                "status": status.value,
                "healthy": status in [ToolHealthStatus.HEALTHY, ToolHealthStatus.UNKNOWN],
            }

        return report


# ================================
# 全局单例访问函数
# ================================


def get_unified_registry() -> UnifiedToolRegistry:
    """
    获取统一工具注册表单例

    Returns:
        UnifiedToolRegistry: 全局唯一实例
    """
    return UnifiedToolRegistry.get_instance()


async def initialize_unified_registry(
    auto_discover: bool = True,
    scan_paths: list[str] | None = None,
) -> UnifiedToolRegistry:
    """
    初始化统一工具注册表

    Args:
        auto_discover: 是否自动发现工具
        scan_paths: 扫描路径列表

    Returns:
        UnifiedToolRegistry: 初始化后的实例
    """
    registry = get_unified_registry()
    await registry.initialize(auto_discover=auto_discover, scan_paths=scan_paths)
    return registry


__all__ = [
    "UnifiedToolRegistry",
    "ToolHealthStatus",
    "LazyToolLoader",
    "get_unified_registry",
    "initialize_unified_registry",
]
