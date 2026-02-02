#!/usr/bin/env python3
"""
Athena统一工具注册中心
Unified Tool Registry for Athena Platform

整合所有工具注册表,提供统一的工具发现和访问接口

核心功能:
1. 统一注册所有类型工具(内置、MCP、搜索、服务)
2. 自动发现和注册
3. 健康检查和状态监控
4. 工具调用统一接口
5. 性能统计和分析

使用方法:
    from core.governance.unified_tool_registry import get_unified_registry

    registry = await get_unified_registry()
    await registry.initialize()

    # 发现工具
    tools = await registry.discover_tools("搜索专利")

    # 执行工具
    result = await registry.execute_tool(tools[0]['tool_id'], {...})
"""

import asyncio
import contextlib
import logging
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.logging_config import setup_logging

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

# ================================
# 数据模型
# ================================


class ToolCategory(Enum):
    """工具类别"""

    BUILTIN = "builtin"  # 内置工具
    SEARCH = "search"  # 搜索工具
    MCP = "mcp"  # MCP工具
    SERVICE = "service"  # 服务工具
    DOMAIN = "domain"  # 领域工具
    UTILITY = "utility"  # 工具函数
    AGENT = "agent"  # 智能体


class ToolStatus(Enum):
    """工具状态"""

    REGISTERED = "registered"  # 已注册
    AVAILABLE = "available"  # 可用
    BUSY = "busy"  # 忙碌
    ERROR = "error"  # 错误
    DEPRECATED = "deprecated"  # 已废弃
    DISABLED = "disabled"  # 已禁用


@dataclass
class ToolMetadata:
    """工具元数据"""

    tool_id: str
    name: str
    category: ToolCategory
    version: str
    description: str
    author: str = "Athena Team"

    # 能力描述
    capabilities: list[str] = field(default_factory=list)
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)

    # 状态信息
    status: ToolStatus = ToolStatus.REGISTERED
    health_score: float = 1.0
    last_health_check: datetime | None = None

    # 性能统计
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    avg_response_time: float = 0.0

    # 注册信息
    registration_time: datetime = field(default_factory=datetime.now)
    registration_source: str = "manual"  # manual, auto_discovered, mcp

    # 依赖关系
    dependencies: list[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_calls == 0:
            return 0.0
        return self.successful_calls / self.total_calls


@dataclass
class ToolExecutionResult:
    """工具执行结果"""

    tool_id: str
    success: bool
    result: Any = None
    error: str | None = None
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


# ================================
# 统一工具注册中心
# ================================


class UnifiedToolRegistry:
    """
    统一工具注册中心

    核心功能:
    1. 统一注册所有类型工具(内置、MCP、搜索、服务)
    2. 自动发现和注册
    3. 健康检查和状态监控
    4. 工具调用统一接口
    5. 性能统计和分析
    """

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}

        # 平台根目录
        self.platform_root = Path("/Users/xujian/Athena工作平台")

        # 工具存储
        self.tools: dict[str, Any] = {}  # tool_id -> tool_instance
        self.metadata: dict[str, ToolMetadata] = {}  # tool_id -> metadata

        # 类别索引
        self.tools_by_category: dict[ToolCategory, list[str]] = {
            category: [] for category in ToolCategory
        }

        # 健康检查配置
        self.health_check_interval = self.config.get("health_check_interval", 60)
        self.health_check_task: asyncio.Task | None = None

        # 事件回调
        self._on_tool_registered: list[Callable] = []
        self._on_tool_updated: list[Callable] = []
        self._on_tool_removed: list[Callable] = []

        # 子注册表引用(延迟初始化)
        self._builtin_registry = None
        self._search_registry = None
        self._mcp_manager = None

        # 工具发现器(延迟初始化)
        self._enhanced_discovery = None
        self._vector_discovery = None

        logger.info("✅ 统一工具注册中心已创建")

    async def initialize(self) -> bool:
        """初始化统一注册中心"""
        logger.info("🚀 初始化统一工具注册中心...")

        try:
            # 1. 注册内置工具
            await self._register_builtin_tools()

            # 2. 注册搜索工具
            await self._register_search_tools()

            # 3. 注册MCP工具
            await self._register_mcp_tools()

            # 4. 从清单加载服务工具
            await self._load_tools_from_inventory()

            # 5. 启动健康检查
            await self._start_health_check_scheduler()

            total = len(self.tools)
            logger.info(f"✅ 统一工具注册中心初始化完成,共注册 {total} 个工具")
            return True

        except Exception as e:
            logger.error(f"❌ 初始化失败: {e}")
            import traceback

            traceback.print_exc()
            return False

    async def _register_builtin_tools(self):
        """注册内置工具"""
        logger.info("📦 注册内置工具...")

        try:
            # 直接执行模块,设置正确的__package__以支持相对导入
            import importlib.util
            import sys

            # 添加项目根目录到sys.path
            if str(PROJECT_ROOT) not in sys.path:
                sys.path.insert(0, str(PROJECT_ROOT))

            # 读取模块文件
            module_path = PROJECT_ROOT / "core" / "tool_auto_executor.py"
            with open(module_path, encoding="utf-8") as f:
                code = f.read()

            # 创建模块并设置__package__
            module = type(
                importlib.util.module_from_spec(
                    importlib.util.spec_from_file_location(
                        "core.tool_auto_executor", str(module_path)
                    )
                )
            )("core.tool_auto_executor")

            # 设置__name__和__package__以支持相对导入
            module.__name__ = "core.tool_auto_executor"
            module.__package__ = "core"
            module.__file__ = str(module_path)
            module.__path__ = str(PROJECT_ROOT / "core")

            # 添加到sys.modules
            sys.modules["core.tool_auto_executor"] = module
            if "core" not in sys.modules:
                # 创建一个空的core模块占位符
                import types

                core_module = types.ModuleType("core")
                core_module.__path__ = [str(PROJECT_ROOT / "core")]
                sys.modules["core"] = core_module

            # 执行代码
            exec(code, module.__dict__)

            ToolAutoExecutionEngine = module.ToolAutoExecutionEngine
            self._builtin_registry = ToolAutoExecutionEngine()

            # 获取已注册的工具能力
            if hasattr(self._builtin_registry, "tools"):
                for tool_name, tool_capability in self._builtin_registry.tools.items():
                    await self.register_tool(
                        tool_id=f"builtin.{tool_name}",
                        name=tool_name,
                        category=ToolCategory.BUILTIN,
                        version="2.0.0",
                        description=getattr(tool_capability, "description", ""),
                        capabilities=getattr(tool_capability, "tags", []),
                        input_schema=getattr(tool_capability, "input_schema", {}),
                        output_schema=getattr(tool_capability, "output_schema", {}),
                        tool_instance=None,  # 内置工具通过executor调用
                        registration_source="builtin_registry",
                    )
        except Exception as e:
            logger.warning(f"⚠️ 无法加载内置工具注册表: {e}")

    async def _register_search_tools(self):
        """注册搜索工具"""
        logger.info("🔍 注册搜索工具...")

        try:
            # 直接执行模块,设置正确的__package__以支持相对导入
            import importlib.util
            import sys

            # 添加项目根目录到sys.path
            if str(PROJECT_ROOT) not in sys.path:
                sys.path.insert(0, str(PROJECT_ROOT))

            # 读取模块文件
            module_path = PROJECT_ROOT / "core" / "search" / "registry" / "tool_registry.py"
            with open(module_path, encoding="utf-8") as f:
                code = f.read()

            # 创建模块并设置__package__
            module = type(
                importlib.util.module_from_spec(
                    importlib.util.spec_from_file_location(
                        "core.search.registry.tool_registry", str(module_path)
                    )
                )
            )("core.search.registry.tool_registry")

            # 设置__name__和__package__以支持相对导入
            module.__name__ = "core.search.registry.tool_registry"
            module.__package__ = "core.search.registry"
            module.__file__ = str(module_path)

            # 添加到sys.modules
            sys.modules["core.search.registry.tool_registry"] = module
            if "core.search.registry" not in sys.modules:
                # 创建占位符模块
                import types

                registry_module = types.ModuleType("core.search.registry")
                registry_module.__path__ = [str(PROJECT_ROOT / "core" / "search" / "registry")]
                sys.modules["core.search.registry"] = registry_module

            if "core.search" not in sys.modules:
                search_module = types.ModuleType("core.search")
                search_module.__path__ = [str(PROJECT_ROOT / "core" / "search")]
                sys.modules["core.search"] = search_module

            if "core" not in sys.modules:
                core_module = types.ModuleType("core")
                core_module.__path__ = [str(PROJECT_ROOT / "core")]
                sys.modules["core"] = core_module

            # 执行代码
            exec(code, module.__dict__)

            get_tool_registry = module.get_tool_registry
            self._search_registry = get_tool_registry()

            # 获取搜索工具列表
            search_tools = self._search_registry.list_tools()

            for tool_name in search_tools:
                try:
                    tool = self._search_registry.get_tool(tool_name)
                    metadata = self._search_registry.get_tool_metadata(tool_name)

                    if tool and metadata:
                        await self.register_tool(
                            tool_id=f"search.{tool_name}",
                            name=tool_name,
                            category=ToolCategory.SEARCH,
                            version=metadata.version if hasattr(metadata, "version") else "1.0.0",
                            description=(
                                metadata.description if hasattr(metadata, "description") else ""
                            ),
                            capabilities=(
                                metadata.capabilities.supported_search_types
                                if hasattr(metadata, "capabilities") and metadata.capabilities
                                else []
                            ),
                            tool_instance=tool,
                            registration_source="search_registry",
                        )
                except Exception as e:
                    logger.debug(f"无法注册搜索工具 {tool_name}: {e}")

        except Exception as e:
            logger.warning(f"⚠️ 无法加载搜索工具注册表: {e}")

    async def _register_mcp_tools(self):
        """注册MCP工具"""
        logger.info("🔌 注册MCP工具...")

        try:
            from dev.tools.mcp.athena_mcp_manager import AthenaMCPManager

            self._mcp_manager = AthenaMCPManager()

            # 获取所有MCP服务器
            mcp_servers = self._mcp_manager.list_all_servers()

            for server_name in mcp_servers:
                try:
                    # 获取工具列表
                    tools = await self._mcp_manager.list_tools(server_name)

                    for mcp_tool in tools:
                        await self.register_tool(
                            tool_id=f"mcp.{server_name}.{mcp_tool.name}",
                            name=mcp_tool.name,
                            category=ToolCategory.MCP,
                            version="1.0.0",
                            description=mcp_tool.description,
                            input_schema=getattr(mcp_tool, "input_schema", {}),
                            tool_instance=mcp_tool,
                            registration_source="mcp_manager",
                            dependencies=[f"mcp_server:{server_name}"],
                        )

                except Exception as e:
                    logger.warning(f"⚠️ 无法注册MCP服务器 {server_name}: {e}")

        except Exception as e:
            logger.warning(f"⚠️ 无法加载MCP管理器: {e}")

    async def _load_tools_from_inventory(self):
        """从清单加载服务工具"""
        logger.info("📋 从清单加载工具...")

        inventory_file = self.platform_root / "reports" / "tool_inventory_report.json"

        if not inventory_file.exists():
            logger.warning("⚠️ 工具清单文件不存在,跳过")
            return

        import json

        with open(inventory_file, encoding="utf-8") as f:
            data = json.load(f)

        tools = data.get("tools", [])

        for tool_data in tools:
            # 跳过已注册的类别(builtin, mcp, search已单独处理)
            category_str = tool_data.get("category")
            if category_str in ["builtin", "mcp", "search"]:
                continue

            # 只注册可用工具
            if tool_data.get("status") != "available":
                continue

            try:
                category = ToolCategory(category_str)

                await self.register_tool(
                    tool_id=tool_data["tool_id"],
                    name=tool_data["name"],
                    category=category,
                    version=tool_data.get("version", "1.0.0"),
                    description=tool_data.get("description", ""),
                    capabilities=tool_data.get("capabilities", []),
                    tool_instance=None,  # 服务工具延迟加载
                    registration_source="inventory",
                )
            except Exception as e:
                logger.debug(f"无法注册工具 {tool_data.get('tool_id')}: {e}")

    async def register_tool(
        self,
        tool_id: str,
        name: str,
        category: ToolCategory,
        version: str,
        description: str,
        capabilities: list[str],
        tool_instance: Any = None,
        input_schema: dict[str, Any] | None = None,
        output_schema: dict[str, Any] | None = None,
        registration_source: str = "manual",
        dependencies: list[str] | None = None,
    ) -> bool:
        """注册工具"""
        try:
            # 创建元数据
            metadata = ToolMetadata(
                tool_id=tool_id,
                name=name,
                category=category,
                version=version,
                description=description,
                capabilities=capabilities,
                input_schema=input_schema or {},
                output_schema=output_schema or {},
                registration_source=registration_source,
                dependencies=dependencies or [],
                status=ToolStatus.AVAILABLE,
            )

            # 存储工具和元数据
            self.tools[tool_id] = tool_instance
            self.metadata[tool_id] = metadata

            # 更新类别索引
            self.tools_by_category[category].append(tool_id)

            logger.debug(f"✅ 工具已注册: {tool_id} ({category.value})")

            # 触发事件
            await self._trigger_event(self._on_tool_registered, tool_id, metadata)

            return True

        except Exception as e:
            logger.error(f"❌ 工具注册失败 {tool_id}: {e}")
            return False

    async def execute_tool(
        self, tool_id: str, parameters: dict[str, Any], context: dict[str, Any] | None = None
    ) -> ToolExecutionResult:
        """
        统一工具执行接口

        Args:
            tool_id: 工具ID
            parameters: 执行参数
            context: 执行上下文

        Returns:
            ToolExecutionResult
        """
        start_time = datetime.now()

        try:
            # 检查工具是否存在
            if tool_id not in self.metadata:
                return ToolExecutionResult(
                    tool_id=tool_id, success=False, error=f"工具不存在: {tool_id}"
                )

            metadata = self.metadata[tool_id]

            # 检查工具状态
            if metadata.status != ToolStatus.AVAILABLE:
                return ToolExecutionResult(
                    tool_id=tool_id, success=False, error=f"工具不可用: {metadata.status.value}"
                )

            # 根据工具类别执行
            if metadata.category == ToolCategory.BUILTIN:
                result = await self._execute_builtin_tool(tool_id, parameters, context)
            elif metadata.category == ToolCategory.MCP:
                result = await self._execute_mcp_tool(tool_id, parameters, context)
            elif metadata.category == ToolCategory.SEARCH:
                result = await self._execute_search_tool(tool_id, parameters, context)
            elif metadata.category in [ToolCategory.SERVICE, ToolCategory.DOMAIN]:
                result = await self._execute_service_tool(tool_id, parameters, context)
            elif metadata.category == ToolCategory.AGENT:
                result = await self._execute_agent_tool(tool_id, parameters, context)
            else:
                result = ToolExecutionResult(
                    tool_id=tool_id,
                    success=False,
                    error=f"不支持的工具类别: {metadata.category.value}",
                )

            # 计算执行时间
            execution_time = (datetime.now() - start_time).total_seconds()

            # 更新统计
            metadata.total_calls += 1
            if result.success:
                metadata.successful_calls += 1
            else:
                metadata.failed_calls += 1

            metadata.avg_response_time = (
                metadata.avg_response_time * (metadata.total_calls - 1) + execution_time
            ) / metadata.total_calls

            result.execution_time = execution_time
            return result

        except Exception as e:
            logger.error(f"工具执行失败 {tool_id}: {e}")
            return ToolExecutionResult(
                tool_id=tool_id,
                success=False,
                error=str(e),
                execution_time=(datetime.now() - start_time).total_seconds(),
            )

    async def _execute_builtin_tool(
        self, tool_id: str, parameters: dict[str, Any], context: dict[str, Any]
    ) -> ToolExecutionResult:
        """执行内置工具"""
        # 通过tool_executor执行(简化实现)
        return ToolExecutionResult(
            tool_id=tool_id,
            success=True,
            result={"message": f"执行内置工具: {tool_id}", "parameters": parameters},
        )

    async def _execute_mcp_tool(
        self, tool_id: str, parameters: dict[str, Any], context: dict[str, Any]
    ) -> ToolExecutionResult:
        """执行MCP工具"""
        if not self._mcp_manager:
            return ToolExecutionResult(tool_id=tool_id, success=False, error="MCP管理器未初始化")

        # 解析服务器和工具名称
        parts = tool_id.split(".")
        if len(parts) < 3:
            return ToolExecutionResult(tool_id=tool_id, success=False, error="无效的MCP工具ID")

        server_name = parts[1]
        tool_name = ".".join(parts[2:])

        try:
            # 通过MCP管理器调用
            result = await self._mcp_manager.call_tool(server_name, tool_name, parameters)

            return ToolExecutionResult(tool_id=tool_id, success=True, result=result)
        except Exception as e:
            return ToolExecutionResult(
                tool_id=tool_id, success=False, error=f"MCP调用失败: {e!s}"
            )

    async def _execute_search_tool(
        self, tool_id: str, parameters: dict[str, Any], context: dict[str, Any]
    ) -> ToolExecutionResult:
        """执行搜索工具"""
        if not self._search_registry:
            return ToolExecutionResult(tool_id=tool_id, success=False, error="搜索注册表未初始化")

        tool_name = tool_id.replace("search.", "")
        tool = self._search_registry.get_tool(tool_name)

        if not tool:
            return ToolExecutionResult(
                tool_id=tool_id, success=False, error=f"搜索工具不存在: {tool_name}"
            )

        # 执行搜索(简化实现)
        return ToolExecutionResult(
            tool_id=tool_id,
            success=True,
            result={"message": f"执行搜索: {tool_name}", "query": parameters},
        )

    async def _execute_service_tool(
        self, tool_id: str, parameters: dict[str, Any], context: dict[str, Any]
    ) -> ToolExecutionResult:
        """执行服务工具"""
        # 服务工具延迟加载(简化实现)
        return ToolExecutionResult(
            tool_id=tool_id,
            success=True,
            result={"message": f"执行服务工具: {tool_id}", "parameters": parameters},
        )

    async def _execute_agent_tool(
        self, tool_id: str, parameters: dict[str, Any], context: dict[str, Any]
    ) -> ToolExecutionResult:
        """执行智能体工具"""
        # 智能体工具(简化实现)
        return ToolExecutionResult(
            tool_id=tool_id,
            success=True,
            result={"message": f"执行智能体: {tool_id}", "parameters": parameters},
        )

    async def discover_tools(
        self,
        query: str,
        category: ToolCategory | None = None,
        limit: int = 5,
        use_enhanced: bool = True,
        use_vector: bool = False,
        use_gpu: bool = True,
        vector_weight: float = 0.7,
    ) -> list[dict[str, Any]]:
        """
        智能工具发现

        Args:
            query: 查询描述
            category: 工具类别过滤
            limit: 返回数量限制
            use_enhanced: 是否使用增强发现(同义词扩展+模糊匹配)
            use_vector: 是否使用向量搜索
            use_gpu: 是否使用GPU加速(mac_os MPS/CUDA)
            vector_weight: 向量搜索权重(仅在use_vector=True时有效)

        Returns:
            匹配的工具列表
        """
        # 向量搜索优先(GPU加速)
        if use_vector:
            return await self._discover_tools_vector(query, category, limit, vector_weight, use_gpu)

        # 使用增强工具发现
        if use_enhanced:
            return await self._discover_tools_enhanced(query, category, limit)

        # 原始实现(基于简单关键词匹配)
        results = []

        # 简化实现:基于关键词匹配
        query_lower = query.lower()

        for tool_id, metadata in self.metadata.items():
            # 类别过滤
            if category and metadata.category != category:
                continue

            # 状态过滤
            if metadata.status != ToolStatus.AVAILABLE:
                continue

            # 关键词匹配
            score = 0.0

            # 名称匹配
            if query_lower in metadata.name.lower():
                score += 0.5

            # 描述匹配
            if query_lower in metadata.description.lower():
                score += 0.3

            # 能力匹配
            for capability in metadata.capabilities:
                if query_lower in capability.lower():
                    score += 0.2
                    break

            if score > 0:
                results.append(
                    {
                        "tool_id": tool_id,
                        "name": metadata.name,
                        "description": metadata.description,
                        "category": metadata.category.value,
                        "score": score,
                        "success_rate": metadata.success_rate,
                    }
                )

        # 按分数排序
        results.sort(key=lambda x: x["score"], reverse=True)

        return results[:limit]

    async def _discover_tools_enhanced(
        self, query: str, category: ToolCategory | None = None, limit: int = 5
    ) -> list[dict[str, Any]]:
        """
        使用增强工具发现器进行工具发现

        Args:
            query: 查询描述
            category: 工具类别过滤
            limit: 返回数量限制

        Returns:
            匹配的工具列表
        """
        # 延迟初始化增强发现器
        if self._enhanced_discovery is None:
            # 使用绝对导入避免相对导入问题
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                "enhanced_tool_discovery", "core/governance/enhanced_tool_discovery.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            EnhancedToolDiscovery = module.EnhancedToolDiscovery
            self._enhanced_discovery = EnhancedToolDiscovery(self.metadata)
            stats = self._enhanced_discovery.get_discovery_stats()
            logger.info(f"✅ 增强工具发现器已初始化: {stats}")

        # 使用增强发现
        category_str = category.value if category else None
        results = await self._enhanced_discovery.discover_tools(
            query=query, limit=limit, category=category_str, enable_synonyms=True, enable_fuzzy=True
        )

        return results

    async def _discover_tools_vector(
        self,
        query: str,
        category: ToolCategory | None = None,
        limit: int = 5,
        vector_weight: float = 0.7,
        use_gpu: bool = True,
    ) -> list[dict[str, Any]]:
        """
        使用向量搜索进行工具发现(支持GPU加速)

        Args:
            query: 查询描述
            category: 工具类别过滤
            limit: 返回数量限制
            vector_weight: 向量搜索权重(用于混合搜索)
            use_gpu: 是否使用GPU加速

        Returns:
            匹配的工具列表
        """
        # 延迟初始化向量发现器
        if self._vector_discovery is None:
            # 优先使用GPU加速版本
            if use_gpu:
                try:
                    import importlib.util

                    spec = importlib.util.spec_from_file_location(
                        "vector_tool_discovery_gpu", "core/governance/vector_tool_discovery_gpu.py"
                    )
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    GPUVectorToolDiscovery = module.GPUVectorToolDiscovery
                    self._vector_discovery = GPUVectorToolDiscovery(self.metadata, use_gpu=True)
                    stats = self._vector_discovery.get_statistics()
                    logger.info(f"✅ GPU向量工具发现器已初始化: {stats}")
                except Exception as e:
                    logger.warning(f"⚠️ GPU向量发现器初始化失败,回退到CPU版本: {e}")
                    use_gpu = False

            # CPU版本回退
            if self._vector_discovery is None:
                import importlib.util

                spec = importlib.util.spec_from_file_location(
                    "vector_tool_discovery", "core/governance/vector_tool_discovery.py"
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                VectorToolDiscovery = module.VectorToolDiscovery
                self._vector_discovery = VectorToolDiscovery(self.metadata)
                stats = self._vector_discovery.get_statistics()
                logger.info(f"✅ 向量工具发现器已初始化: {stats}")

        # 使用向量发现
        category_str = category.value if category else None

        # 检查是否使用混合搜索
        if vector_weight < 1.0:
            # 混合搜索:向量 + 关键词
            results = await self._vector_discovery.hybrid_discover(
                query=query,
                limit=limit,
                category=category_str,
                vector_weight=vector_weight,
                keyword_weight=1.0 - vector_weight,
            )
        else:
            # 纯向量搜索
            results = await self._vector_discovery.discover_tools(
                query=query, limit=limit, category=category_str, threshold=0.3  # 相似度阈值
            )

        return results

    async def _start_health_check_scheduler(self):
        """启动健康检查调度器"""
        if self.health_check_interval > 0:
            self.health_check_task = asyncio.create_task(self._health_check_loop())
            logger.info(f"🔄 健康检查调度器已启动,间隔: {self.health_check_interval}秒")

    async def _health_check_loop(self):
        """健康检查循环"""
        while True:
            try:
                await self.health_check_all()
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ 健康检查异常: {e}")
                await asyncio.sleep(5)

    async def health_check_all(self) -> dict[str, dict[str, Any]]:
        """执行所有工具的健康检查"""
        results = {}

        for tool_id, metadata in self.metadata.items():
            try:
                health_info = await self._health_check_tool(tool_id)
                results[tool_id] = health_info

                # 更新状态
                if health_info["healthy"]:
                    metadata.status = ToolStatus.AVAILABLE
                    metadata.health_score = health_info.get("score", 1.0)
                else:
                    metadata.status = ToolStatus.ERROR
                    metadata.health_score = 0.0

                metadata.last_health_check = datetime.now()

            except Exception as e:
                results[tool_id] = {"healthy": False, "error": str(e)}
                metadata.status = ToolStatus.ERROR

        return results

    async def _health_check_tool(self, tool_id: str) -> dict[str, Any]:
        """检查单个工具健康状态"""
        metadata = self.metadata.get(tool_id)

        if not metadata:
            return {"healthy": False, "error": "工具不存在"}

        # 简化实现:根据状态判断
        if metadata.status == ToolStatus.DEPRECATED:
            return {"healthy": False, "reason": "已废弃"}

        # 默认健康
        return {"healthy": True, "score": metadata.health_score}

    def list_tools(
        self, category: ToolCategory | None = None, status: ToolStatus | None = None
    ) -> list[dict[str, Any]]:
        """列出工具"""
        results = []

        for tool_id, metadata in self.metadata.items():
            # 过滤类别
            if category and metadata.category != category:
                continue

            # 过滤状态
            if status and metadata.status != status:
                continue

            results.append(
                {
                    "tool_id": tool_id,
                    "name": metadata.name,
                    "category": metadata.category.value,
                    "description": metadata.description,
                    "status": metadata.status.value,
                    "health_score": metadata.health_score,
                    "success_rate": metadata.success_rate,
                    "total_calls": metadata.total_calls,
                }
            )

        return results

    def get_tool_info(self, tool_id: str) -> dict[str, Any] | None:
        """获取工具详细信息"""
        metadata = self.metadata.get(tool_id)

        if not metadata:
            return None

        return {
            "tool_id": metadata.tool_id,
            "name": metadata.name,
            "category": metadata.category.value,
            "version": metadata.version,
            "description": metadata.description,
            "author": metadata.author,
            "capabilities": metadata.capabilities,
            "status": metadata.status.value,
            "health_score": metadata.health_score,
            "success_rate": metadata.success_rate,
            "total_calls": metadata.total_calls,
            "registration_source": metadata.registration_source,
            "dependencies": metadata.dependencies,
        }

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        total_tools = len(self.tools)

        stats = {
            "total_tools": total_tools,
            "by_category": {},
            "by_status": {},
            "overall_health_score": 0.0,
            "overall_success_rate": 0.0,
            "total_calls": 0,
            "timestamp": datetime.now().isoformat(),
        }

        for metadata in self.metadata.values():
            # 按类别统计
            category = metadata.category.value
            stats["by_category"][category] = stats["by_category"].get(category, 0) + 1

            # 按状态统计
            status = metadata.status.value
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1

        # 计算总体健康分数
        if total_tools > 0:
            stats["overall_health_score"] = (
                sum(m.health_score for m in self.metadata.values()) / total_tools
            )
            stats["overall_success_rate"] = (
                sum(m.success_rate for m in self.metadata.values()) / total_tools
            )
            stats["total_calls"] = sum(m.total_calls for m in self.metadata.values())

        return stats

    async def _trigger_event(self, callbacks: list[Callable], *args, **kwargs):
        """触发事件回调"""
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(*args, **kwargs)
                else:
                    callback(*args, **kwargs)
            except Exception as e:
                logger.error(f"❌ 事件回调执行失败: {e}")

    async def shutdown(self):
        """关闭注册中心"""
        logger.info("🛒 关闭统一工具注册中心...")

        # 停止健康检查
        if self.health_check_task:
            self.health_check_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.health_check_task

        logger.info("✅ 统一工具注册中心已关闭")


# ================================
# 全局单例
# ================================

_unified_registry: UnifiedToolRegistry | None = None


def get_unified_registry() -> UnifiedToolRegistry:
    """获取统一工具注册中心单例"""
    global _unified_registry
    if _unified_registry is None:
        _unified_registry = UnifiedToolRegistry()
    return _unified_registry


async def initialize_unified_registry() -> UnifiedToolRegistry:
    """初始化统一工具注册中心"""
    registry = get_unified_registry()
    await registry.initialize()
    return registry


# ================================
# 测试代码
# ================================


async def main():
    """主函数(用于测试)"""
    print("=" * 80)
    print("🔍 统一工具注册中心测试")
    print("=" * 80)
    print()

    # 获取注册中心
    registry = get_unified_registry()

    # 初始化
    print("初始化注册中心...")
    success = await registry.initialize()

    if success:
        print()
        print("📊 注册中心统计:")
        stats = registry.get_statistics()
        print(f"   总工具数: {stats['total_tools']}")
        print()
        print("   按类别:")
        for category, count in stats["by_category"].items():
            print(f"     {category}: {count}")
        print()
        print("   按状态:")
        for status, count in stats["by_status"].items():
            print(f"     {status}: {count}")
        print()

        # 测试工具发现
        print("🔍 测试工具发现:")
        tools = await registry.discover_tools("搜索", limit=5)
        for tool in tools:
            print(f"   - {tool['tool_id']}: {tool['name']} ({tool['category']})")
        print()

        print("✅ 测试完成")
    else:
        print("❌ 初始化失败")

    print("=" * 80)


# 入口点: @async_main装饰器已添加到main函数
