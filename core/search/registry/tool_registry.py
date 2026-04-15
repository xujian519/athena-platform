#!/usr/bin/env python3
from __future__ import annotations
"""
分散式智能搜索架构 - 工具注册中心
Decentralized Intelligent Search Architecture - Tool Registry

作者: Athena AI系统
创建时间: 2025-12-05
版本: 1.0.0

核心功能:
1. 工具注册和发现 - 管理所有搜索工具
2. 健康检查 - 定期检查工具状态
3. 性能监控 - 收集和分析工具性能
4. 轻量协调 - 配置同步和指标收集
"""

import asyncio
import contextlib
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from ..standards.base_search_tool import (
    BaseSearchTool,
    SearchCapabilities,
    SearchQuery,
    SearchType,
)

logger = logging.getLogger(__name__)


class ToolStatus(Enum):
    """工具状态枚举"""

    ACTIVE = "active"  # 活跃状态
    INACTIVE = "inactive"  # 非活跃状态
    ERROR = "error"  # 错误状态
    MAINTENANCE = "maintenance"  # 维护状态
    DISABLED = "disabled"  # 已禁用


class RegistrationResult(Enum):
    """注册结果"""

    SUCCESS = "success"
    ALREADY_EXISTS = "already_exists"
    INVALID_TOOL = "invalid_tool"
    INITIALIZATION_FAILED = "initialization_failed"


@dataclass
class ToolMetadata:
    """工具元数据"""

    name: str
    category: str
    version: str
    description: str

    # 注册信息
    registration_time: datetime = field(default_factory=datetime.now)
    last_heartbeat: datetime = field(default_factory=datetime.now)
    registration_source: str = "manual"

    # 状态信息
    status: ToolStatus = ToolStatus.INACTIVE
    health_score: float = 1.0

    # 性能统计
    total_requests: int = 0
    successful_requests: int = 0
    avg_response_time: float = 0.0
    last_request_time: datetime | None = None

    # 配置信息
    config: dict[str, Any] = field(default_factory=dict)
    capabilities: SearchCapabilities | None = None

    # 依赖关系
    dependencies: list[str] = field(default_factory=list)
    dependents: list[str] = field(default_factory=list)

    def get_success_rate(self) -> float:
        """获取成功率"""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests

    def update_health_score(self, success_rate: float, response_time: float) -> None:
        """更新健康评分"""
        # 基于成功率和响应时间计算健康评分
        success_factor = success_rate
        response_factor = max(0, 1 - (response_time / 10.0))  # 10秒为基准

        self.health_score = (success_factor + response_factor) / 2


@dataclass
class RegistryStats:
    """注册中心统计信息"""

    total_tools: int = 0
    active_tools: int = 0
    tools_by_category: dict[str, int] = field(default_factory=dict)
    tools_by_status: dict[ToolStatus, int] = field(default_factory=dict)

    total_requests: int = 0
    total_successes: int = 0
    avg_response_time: float = 0.0

    last_health_check: datetime | None = None
    registry_uptime: float = 0.0


class ToolRegistry:
    """
    工具注册中心

    设计原则:
    1. 轻量级管理 - 不干预工具运行,只做注册和监控
    2. 健康检查 - 定期检查工具状态
    3. 性能监控 - 收集性能数据
    4. 智能推荐 - 基于历史性能推荐最佳工具
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """
        初始化工具注册中心

        Args:
            config: 注册中心配置
        """
        self.config = config or {}
        self.tools: dict[str, BaseSearchTool] = {}
        self.metadata: dict[str, ToolMetadata] = {}

        # 健康检查配置
        self.health_check_interval = self.config.get("health_check_interval", 60)  # 秒
        self.health_check_timeout = self.config.get("health_check_timeout", 10)  # 秒
        self.max_health_check_failures = self.config.get("max_health_check_failures", 3)

        # 注册中心状态
        self.initialized = False
        self._start_time = time.time()
        self._health_check_task: asyncio.Task[Any] | None | None = None

        # 统计信息
        self.stats = RegistryStats()

        # 事件回调
        self._on_tool_registered: list[Callable[..., Any]] = []
        self._on_tool_unregistered: list[Callable[..., Any]] = []
        self._on_health_check_completed: list[Callable[..., Any]] = []

    async def initialize(self) -> bool:
        """
        初始化注册中心

        Returns:
            bool: 初始化是否成功
        """
        try:
            logger.info("🚀 初始化工具注册中心...")

            # 加载已有配置
            await self._load_existing_tools()

            # 启动健康检查任务
            await self._start_health_check_scheduler()

            self.initialized = True
            logger.info(f"✅ 工具注册中心初始化完成,已注册 {len(self.tools)} 个工具")

            return True

        except Exception as e:
            logger.error(f"❌ 工具注册中心初始化失败: {e}")
            return False

    async def register_tool(
        self, tool: BaseSearchTool, auto_initialize: bool = True, replace_existing: bool = False
    ) -> RegistrationResult:
        """
        注册搜索工具

        Args:
            tool: 搜索工具实例
            auto_initialize: 是否自动初始化工具
            replace_existing: 是否替换已存在的工具

        Returns:
            RegistrationResult: 注册结果
        """
        try:
            tool_name = tool.name

            # 检查工具是否已存在
            if tool_name in self.tools and not replace_existing:
                logger.warning(f"⚠️ 工具 {tool_name} 已存在")
                return RegistrationResult.ALREADY_EXISTS

            # 验证工具
            if not isinstance(tool, BaseSearchTool):
                logger.error(f"❌ 无效的工具类型: {type(tool)}")
                return RegistrationResult.INVALID_TOOL

            # 初始化工具
            if auto_initialize and not tool.initialized:
                init_success = await tool.initialize()
                if not init_success:
                    logger.error(f"❌ 工具 {tool_name} 初始化失败")
                    return RegistrationResult.INITIALIZATION_FAILED

            # 获取工具能力
            capabilities = tool.get_capabilities()

            # 创建元数据
            metadata = ToolMetadata(
                name=tool_name,
                category=capabilities.category,
                version=capabilities.version,
                description=capabilities.description,
                capabilities=capabilities,
                config=tool.config,
                status=ToolStatus.ACTIVE,
            )

            # 注册工具
            self.tools[tool_name] = tool
            self.metadata[tool_name] = metadata

            logger.info(f"✅ 工具 {tool_name} 注册成功")

            # 更新统计
            self._update_stats()

            # 触发注册事件
            await self._trigger_event(self._on_tool_registered, tool_name, metadata)

            return RegistrationResult.SUCCESS

        except Exception as e:
            logger.error(f"❌ 工具注册失败: {e}")
            return RegistrationResult.INVALID_TOOL

    async def unregister_tool(self, tool_name: str, force: bool = False) -> bool:
        """
        注销工具

        Args:
            tool_name: 工具名称
            force: 是否强制注销

        Returns:
            bool: 注销是否成功
        """
        try:
            if tool_name not in self.tools:
                logger.warning(f"⚠️ 工具 {tool_name} 不存在")
                return False

            # 检查依赖关系
            if not force:
                dependencies = self.get_tool_dependencies(tool_name)
                if dependencies:
                    logger.warning(f"⚠️ 工具 {tool_name} 有依赖关系,无法注销: {dependencies}")
                    return False

            # 移除工具
            del self.tools[tool_name]
            del self.metadata[tool_name]

            logger.info(f"✅ 工具 {tool_name} 注销成功")

            # 更新统计
            self._update_stats()

            # 触发注销事件
            await self._trigger_event(self._on_tool_unregistered, tool_name)

            return True

        except Exception as e:
            logger.error(f"❌ 工具注销失败: {e}")
            return False

    def get_tool(self, tool_name: str) -> BaseSearchTool | None:
        """
        获取工具实例

        Args:
            tool_name: 工具名称

        Returns:
            BaseSearchTool: 工具实例或None
        """
        return self.tools.get(tool_name)

    def get_tool_metadata(self, tool_name: str) -> ToolMetadata | None:
        """
        获取工具元数据

        Args:
            tool_name: 工具名称

        Returns:
            ToolMetadata: 工具元数据或None
        """
        return self.metadata.get(tool_name)

    def list_tools(
        self,
        status_filter: ToolStatus | None = None,
        category_filter: str | None = None,
        search_type_filter: SearchType | None = None,
    ) -> list[str]:
        """
        列出工具

        Args:
            status_filter: 状态过滤器
            category_filter: 类别过滤器
            search_type_filter: 搜索类型过滤器

        Returns:
            list[str]: 工具名称列表
        """
        tool_names = []

        for tool_name, metadata in self.metadata.items():
            # 状态过滤
            if status_filter and metadata.status != status_filter:
                continue

            # 类别过滤
            if category_filter and metadata.category != category_filter:
                continue

            # 搜索类型过滤
            if search_type_filter:
                capabilities = metadata.capabilities
                if (
                    not capabilities
                    or search_type_filter not in capabilities.supported_search_types
                ):
                    continue

            tool_names.append(tool_name)

        return tool_names

    async def recommend_tools(
        self, query: SearchQuery, max_tools: int = 3, exclude_tools: list[str] | None = None
    ) -> list[str]:
        """
        推荐最佳工具

        Args:
            query: 搜索查询
            max_tools: 最大推荐数量
            exclude_tools: 排除的工具列表

        Returns:
            list[str]: 推荐的工具名称列表
        """
        try:
            exclude_tools = exclude_tools or []
            candidates = []

            for tool_name, metadata in self.metadata.items():
                # 排除指定工具
                if tool_name in exclude_tools:
                    continue

                # 检查工具状态
                if metadata.status != ToolStatus.ACTIVE:
                    continue

                # 检查工具能力匹配
                capabilities = metadata.capabilities
                if not capabilities:
                    continue

                # 计算匹配分数
                score = await self._calculate_tool_match_score(tool_name, query, capabilities)
                if score > 0:
                    candidates.append((tool_name, score))

            # 按分数排序
            candidates.sort(key=lambda x: x[1], reverse=True)  # type: ignore[arg-type]

            # 返回前N个工具
            return [tool_name for tool_name, _ in candidates[:max_tools]]

        except Exception as e:
            logger.error(f"❌ 工具推荐失败: {e}")
            return []

    async def _calculate_tool_match_score(
        self, tool_name: str, query: SearchQuery, capabilities: SearchCapabilities
    ) -> float:
        """计算工具匹配分数"""
        score = 0.0

        # 搜索类型匹配
        if query.search_type in capabilities.supported_search_types:
            score += 0.3

        # 领域专业度匹配
        query_text = query.text.lower()
        for domain in capabilities.domain_expertise:
            if domain.lower() in query_text:
                score += 0.2

        # 性能评分
        metadata = self.metadata[tool_name]
        score += metadata.health_score * 0.2

        # 历史成功率
        success_rate = metadata.get_success_rate()
        score += success_rate * 0.2

        # 响应时间评分 (响应越快分数越高)
        response_score = max(0, 1 - (metadata.avg_response_time / 5.0))
        score += response_score * 0.1

        return min(score, 1.0)

    async def health_check_all(self) -> dict[str, dict[str, Any]]:
        """
        执行所有工具的健康检查

        Returns:
            Dict: 所有工具的健康状态
        """
        results = {}

        for tool_name, tool in self.tools.items():
            try:
                health_info = await tool.health_check()
                results[tool_name] = health_info

                # 更新元数据
                if tool_name in self.metadata:
                    metadata = self.metadata[tool_name]

                    # 更新状态
                    if health_info["status"] == "healthy":
                        metadata.status = ToolStatus.ACTIVE
                    else:
                        metadata.status = ToolStatus.ERROR

                    # 更新健康评分
                    stats = health_info.get("stats", {})
                    success_rate = stats.get("success_rate", 0.0)
                    response_time = health_info.get("response_time", 5.0)
                    metadata.update_health_score(success_rate, response_time)

                    # 更新心跳时间
                    metadata.last_heartbeat = datetime.now()

            except Exception as e:
                logger.error(f"❌ 工具 {tool_name} 健康检查失败: {e}")
                results[tool_name] = {"status": "error", "error": str(e)}

        # 更新统计
        self.stats.last_health_check = datetime.now()
        self._update_stats()

        # 触发健康检查完成事件
        await self._trigger_event(self._on_health_check_completed, results)

        return results

    async def _start_health_check_scheduler(self):
        """启动健康检查调度器"""
        if self.health_check_interval > 0:
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            logger.info(f"🔄 健康检查调度器已启动,间隔: {self.health_check_interval}秒")

    async def _health_check_loop(self):
        """健康检查循环"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self.health_check_all()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ 健康检查循环异常: {e}")

    def get_tool_dependencies(self, tool_name: str) -> list[str]:
        """获取工具依赖关系"""
        metadata = self.metadata.get(tool_name)
        return metadata.dependencies if metadata else []

    def get_tool_dependents(self, tool_name: str) -> list[str]:
        """获取工具被依赖关系"""
        metadata = self.metadata.get(tool_name)
        return metadata.dependents if metadata else []

    def _update_stats(self) -> Any:
        """更新统计信息"""
        self.stats.total_tools = len(self.tools)
        self.stats.active_tools = len(
            [m for m in self.metadata.values() if m.status == ToolStatus.ACTIVE]
        )

        # 按类别统计
        self.stats.tools_by_category.clear()
        for metadata in self.metadata.values():
            category = metadata.category
            self.stats.tools_by_category[category] = (
                self.stats.tools_by_category.get(category, 0) + 1
            )

        # 按状态统计
        self.stats.tools_by_status.clear()
        for metadata in self.metadata.values():
            status = metadata.status
            self.stats.tools_by_status[status] = self.stats.tools_by_status.get(status, 0) + 1

        # 总体性能统计
        total_requests = sum(m.total_requests for m in self.metadata.values())
        total_successes = sum(m.successful_requests for m in self.metadata.values())
        avg_response_time = sum(m.avg_response_time for m in self.metadata.values()) / max(
            1, len(self.metadata)
        )

        self.stats.total_requests = total_requests
        self.stats.total_successes = total_successes
        self.stats.avg_response_time = avg_response_time
        self.stats.registry_uptime = time.time() - self._start_time

    async def _load_existing_tools(self):
        """加载已有工具配置"""
        # 这里可以从配置文件或数据库加载已有工具
        logger.info("📂 加载已有工具配置...")

    async def _trigger_event(
        self, callbacks: list[Callable[..., Any]], *args: Any, **kwargs: Any
    ) -> None:
        """触发事件回调"""
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(*args, **kwargs)
                else:
                    callback(*args, **kwargs)
            except Exception as e:
                logger.error(f"❌ 事件回调执行失败: {e}")

    # 事件监听器
    def on_tool_registered(self, callback: Callable[..., Any]) -> Any:
        """工具注册事件监听器"""
        self._on_tool_registered.append(callback)

    def on_tool_unregistered(self, callback: Callable[..., Any]) -> Any:
        """工具注销事件监听器"""
        self._on_tool_unregistered.append(callback)

    def on_health_check_completed(self, callback: Callable[..., Any]) -> Any:
        """健康检查完成事件监听器"""
        self._on_health_check_completed.append(callback)

    def get_stats(self) -> RegistryStats:
        """获取注册中心统计信息"""
        self._update_stats()
        return self.stats

    async def shutdown(self):
        """关闭注册中心"""
        try:
            logger.info("🔄 关闭工具注册中心...")

            # 停止健康检查任务
            if self._health_check_task:
                self._health_check_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self._health_check_task

            # 关闭所有工具
            for tool_name, tool in self.tools.items():
                try:
                    if hasattr(tool, "shutdown"):
                        await tool.shutdown()  # type: ignore[attr-defined]
                except Exception as e:
                    logger.error(f"❌ 关闭工具 {tool_name} 失败: {e}")

            self.initialized = False
            logger.info("✅ 工具注册中心已关闭")

        except Exception as e:
            logger.error(f"❌ 工具注册中心关闭失败: {e}")


# 全局注册中心实例
_tool_registry: ToolRegistry | None = None


def get_tool_registry() -> ToolRegistry:
    """获取全局工具注册中心实例"""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry


async def initialize_tool_registry(config: dict[str, Any] | None = None) -> ToolRegistry:
    """初始化全局工具注册中心"""
    registry = get_tool_registry()
    await registry.initialize()
    return registry


# 便捷装饰器
def register_to_registry(category: str = "general", auto_init: bool = True) -> Any:
    """
    自动注册到注册中心的装饰器

    Args:
        category: 工具类别
        auto_init: 是否自动初始化
    """

    def decorator(cls) -> Any:
        original_init = cls.__init__

        def __init__(self: Any, *args: Any, **kwargs: Any) -> None:
            original_init(self, *args, **kwargs)
            # 异步注册到注册中心
            asyncio.create_task(_async_register_tool(self, category, auto_init))

        cls.__init__ = __init__
        return cls

    return decorator


async def _async_register_tool(tool: BaseSearchTool, category: str, auto_init: bool):
    """异步注册工具"""
    registry = get_tool_registry()
    await registry.register_tool(tool, auto_initialize=auto_init)


if __name__ == "__main__":
    # 示例用法
    logger.info("🔧 工具注册中心")
    logger.info("   注册和发现搜索工具")
    logger.info("   健康检查和性能监控")
    logger.info("   智能工具推荐")
    print()
    logger.info("💡 使用方法:")
    logger.info("   registry = ToolRegistry()")
    logger.info("   await registry.initialize()")
    logger.info("   await registry.register_tool(my_tool)")
    logger.info("   tools = await registry.recommend_tools(query)")
