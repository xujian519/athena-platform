#!/usr/bin/env python3
from __future__ import annotations
"""
工具分组管理系统基础模块

定义工具的数据模型、分组类型和注册中心。

Author: Athena平台团队
Created: 2026-01-20
Version: v1.0.0
"""

import functools
import logging
import math
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ToolCategory(Enum):
    """工具分类枚举"""

    # 数据检索类
    PATENT_SEARCH = "patent_search"  # 专利检索
    ACADEMIC_SEARCH = "academic_search"  # 学术搜索
    DOCUMENT_RETRIEVAL = "document_retrieval"  # 文档检索

    # 分析类
    PATENT_ANALYSIS = "patent_analysis"  # 专利分析
    LEGAL_ANALYSIS = "legal_analysis"  # 法律分析
    SEMANTIC_ANALYSIS = "semantic_analysis"  # 语义分析
    CODE_ANALYSIS = "code_analysis"  # 代码分析

    # 知识管理类
    KNOWLEDGE_GRAPH = "knowledge_graph"  # 知识图谱
    VECTOR_SEARCH = "vector_search"  # 向量搜索
    CACHE_MANAGEMENT = "cache_management"  # 缓存管理

    # 数据处理类
    DATA_EXTRACTION = "data_extraction"  # 数据提取
    DATA_TRANSFORMATION = "data_transformation"  # 数据转换
    DATA_VALIDATION = "data_validation"  # 数据验证

    # 外部服务类
    MCP_SERVICE = "mcp_service"  # MCP服务
    WEB_AUTOMATION = "web_automation"  # Web自动化
    API_INTEGRATION = "api_integration"  # API集成
    WEB_SEARCH = "web_search"  # 网络搜索
    CHAT_COMPLETION = "chat_completion"  # 聊天补全

    # 辅助类
    LOGGING = "logging"  # 日志记录
    MONITORING = "monitoring"  # 监控
    ERROR_HANDLING = "error_handling"  # 错误处理


class ToolPriority(Enum):
    """工具优先级"""

    CRITICAL = "critical"  # 关键工具,优先使用
    HIGH = "high"  # 高优先级
    MEDIUM = "medium"  # 中等优先级
    LOW = "low"  # 低优先级


@dataclass
class ToolCapability:
    """
    工具能力描述

    定义工具能处理什么类型的任务。
    """

    input_types: list[str]  # 支持的输入类型
    output_types: list[str]  # 输出的数据类型
    domains: list[str]  # 适用领域 (如: patent, legal, academic)
    task_types: list[str]  # 支持的任务类型
    features: dict[str, Any] = field(default_factory=dict)  # 额外功能特性


@dataclass
class ToolPerformance:
    """
    工具性能指标

    跟踪工具的执行性能。
    """

    total_calls: int = 0  # 总调用次数
    successful_calls: int = 0  # 成功调用次数
    failed_calls: int = 0  # 失败调用次数
    avg_execution_time: float = 0.0  # 平均执行时间(秒)
    min_execution_time: float = float("inf")
    max_execution_time: float = 0.0
    last_used: datetime | None = None
    success_rate: float = 1.0  # 成功率

    def update(self, execution_time: float, success: bool) -> Any:
        """
        更新性能指标(带参数验证)

        Args:
            execution_time: 执行时间(秒)
            success: 是否成功

        Raises:
            ValueError: 如果参数无效
        """
        # 🔒 参数验证
        if not isinstance(execution_time, (int, float)):
            raise ValueError(f"execution_time必须是数字类型,得到{type(execution_time)}")

        # 防止NaN和无穷大(必须在负数检查之前)
        if math.isnan(execution_time) or math.isinf(execution_time):
            raise ValueError(f"execution_time必须是有限数值,得到{execution_time}")

        if execution_time < 0:
            raise ValueError(f"execution_time必须非负,得到{execution_time}")

        if not isinstance(success, bool):
            raise ValueError(f"success必须是布尔类型,得到{type(success)}")

        self.total_calls += 1

        if success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1

        # 更新执行时间统计
        self.avg_execution_time = (
            self.avg_execution_time * (self.total_calls - 1) + execution_time
        ) / self.total_calls

        if execution_time < self.min_execution_time:
            self.min_execution_time = execution_time

        if execution_time > self.max_execution_time:
            self.max_execution_time = execution_time

        # 更新成功率
        self.success_rate = (
            self.successful_calls / self.total_calls if self.total_calls > 0 else 0.0
        )
        self.last_used = datetime.now()


@dataclass
class ToolDefinition:
    """
    工具定义

    完整描述一个工具的元数据、能力和性能。
    """

    tool_id: str  # 工具唯一标识
    name: str  # 工具名称
    description: str  # 工具描述
    category: ToolCategory  # 工具分类
    priority: ToolPriority = ToolPriority.MEDIUM

    # 能力描述
    capability: ToolCapability | None = None

    # 性能指标
    performance: ToolPerformance = field(default_factory=ToolPerformance)

    # 实现信息
    implementation_type: str = "function"  # function, mcp, api
    implementation_ref: str = ""  # 实现引用 (函数名/MCP名/API端点)

    # 配置
    config: dict[str, Any] = field(default_factory=dict)

    # 依赖关系
    dependencies: list[str] = field(default_factory=list)

    # 标签 (用于灵活查询)
    tags: set[str] = field(default_factory=set)

    # 执行相关 (用于ToolCallManager)
    required_params: list[str] = field(default_factory=list)  # 必需参数列表
    optional_params: list[str] = field(default_factory=list)  # 可选参数列表
    handler: Callable | None = None  # 处理函数
    timeout: float = 30.0  # 超时时间(秒)
    max_retries: int = 3  # 最大重试次数

    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    enabled: bool = True

    def get_success_rate(self) -> float:
        """获取成功率"""
        return self.performance.success_rate

    def is_available(self) -> bool:
        """检查工具是否可用"""
        return self.enabled

    def matches_domain(self, domain: str) -> bool:
        """检查工具是否支持指定领域"""
        if not self.capability:
            return False
        # "all"作为查询时匹配所有工具(通配符查询)
        if domain == "all":
            return True
        return domain in self.capability.domains or "all" in self.capability.domains

    def matches_task_type(self, task_type: str) -> bool:
        """检查工具是否支持指定任务类型"""
        if not self.capability:
            return False
        # "all"作为查询时匹配所有工具(通配符查询)
        if task_type == "all":
            return True
        return task_type in self.capability.task_types or "all" in self.capability.task_types


class ToolRegistry:
    """
    工具注册中心(线程安全版 + 缓存优化)

    管理所有工具的注册、查询、选择和性能跟踪。

    线程安全:使用RLock保证多线程环境下的安全访问。
    缓存优化:使用LRU缓存提升查询性能 (P2-1)
    """

    def __init__(self):
        """初始化工具注册中心"""
        self._tools: dict[str, ToolDefinition] = {}
        self._category_index: dict[ToolCategory, set[str]] = {}
        self._domain_index: dict[str, set[str]] = {}
        self._tag_index: dict[str, set[str]] = {}

        # 🔒 线程安全:添加可重入锁
        self._lock = threading.RLock()

        # 💾 缓存统计 (P2-1)
        self._cache_stats = {
            "find_by_category_hits": 0,
            "find_by_category_misses": 0,
            "find_by_domain_hits": 0,
            "find_by_domain_misses": 0,
            "search_tools_hits": 0,
            "search_tools_misses": 0,
        }

        logger.info("🔧 ToolRegistry初始化完成(线程安全版 + 缓存优化)")

    def register(self, tool: ToolDefinition) -> "ToolRegistry":
        """
        注册工具(线程安全 + 缓存失效, P2-1)

        Args:
            tool: ToolDefinition对象

        Returns:
            self (支持链式调用)
        """
        with self._lock:
            tool_id = tool.tool_id

            # 检查是否已存在
            if tool_id in self._tools:
                logger.warning(f"⚠️ 工具已存在,将更新: {tool_id}")

            self._tools[tool_id] = tool

            # 更新分类索引
            if tool.category not in self._category_index:
                self._category_index[tool.category] = set()
            self._category_index[tool.category].add(tool_id)

            # 更新领域索引
            if tool.capability:
                for domain in tool.capability.domains:
                    if domain not in self._domain_index:
                        self._domain_index[domain] = set()
                    self._domain_index[domain].add(tool_id)

            # 更新标签索引
            for tag in tool.tags:
                if tag not in self._tag_index:
                    self._tag_index[tag] = set()
                self._tag_index[tag].add(tool_id)

            # 💾 缓存失效 (P2-1) - 工具注册后清除相关缓存
            self.clear_cache()

            logger.info(
                f"✅ 工具已注册: {tool.name} "
                f"(分类: {tool.category.value}, 优先级: {tool.priority.value})"
            )

            return self

    def get_tool(self, tool_id: str) -> ToolDefinition | None:
        """
        获取工具定义

        Args:
            tool_id: 工具ID

        Returns:
            ToolDefinition对象,如果不存在返回None
        """
        return self._tools.get(tool_id)

    @functools.lru_cache(maxsize=128)
    def find_by_category(
        self, category: ToolCategory, enabled_only: bool = True
    ) -> tuple[ToolDefinition, ...]:
        """
        按分类查找工具 (带LRU缓存, P2-1)

        Args:
            category: 工具分类
            enabled_only: 是否只返回启用的工具

        Returns:
            工具列表 (元组，可哈希以支持缓存)
        """
        tool_ids = self._category_index.get(category, set())
        tools = tuple(self._tools[tid] for tid in tool_ids if tid in self._tools)

        if enabled_only:
            tools = tuple(t for t in tools if t.enabled)

        return tools

    def find_by_category_uncached(
        self, category: ToolCategory, enabled_only: bool = True
    ) -> list[ToolDefinition]:
        """
        按分类查找工具 (无缓存版本，用于更新缓存)

        Args:
            category: 工具分类
            enabled_only: 是否只返回启用的工具

        Returns:
            工具列表
        """
        # 清除缓存
        self.find_by_category.cache_clear()

        # 调用带缓存版本
        return list(self.find_by_category(category, enabled_only))

    @functools.lru_cache(maxsize=256)
    def find_by_domain(self, domain: str, enabled_only: bool = True) -> tuple[ToolDefinition, ...]:
        """
        按领域查找工具 (带LRU缓存, P2-1)

        Args:
            domain: 领域名称
            enabled_only: 是否只返回启用的工具

        Returns:
            工具列表 (元组，可哈希以支持缓存)
        """
        tool_ids = self._domain_index.get(domain, set())
        tools = tuple(self._tools[tid] for tid in tool_ids if tid in self._tools)

        if enabled_only:
            tools = tuple(t for t in tools if t.enabled)

        return tools

    def find_by_domain_uncached(
        self, domain: str, enabled_only: bool = True
    ) -> list[ToolDefinition]:
        """
        按领域查找工具 (无缓存版本，用于更新缓存)

        Args:
            domain: 领域名称
            enabled_only: 是否只返回启用的工具

        Returns:
            工具列表
        """
        # 清除缓存
        self.find_by_domain.cache_clear()

        # 调用带缓存版本
        return list(self.find_by_domain(domain, enabled_only))

    def find_by_tag(self, tag: str, enabled_only: bool = True) -> list[ToolDefinition]:
        """
        按标签查找工具

        Args:
            tag: 标签
            enabled_only: 是否只返回启用的工具

        Returns:
            工具列表
        """
        tool_ids = self._tag_index.get(tag, set())
        tools = [self._tools[tid] for tid in tool_ids if tid in self._tools]

        if enabled_only:
            tools = [t for t in tools if t.enabled]

        return tools

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
        # 使用工具ID集合进行过滤
        result_ids = set(self._tools.keys())

        # 按分类过滤
        if category:
            category_tools = self.find_by_category(category, enabled_only=False)
            category_ids = {t.tool_id for t in category_tools}
            result_ids = result_ids.intersection(category_ids)

        # 按领域过滤
        if domain:
            domain_tools = self.find_by_domain(domain, enabled_only=False)
            domain_ids = {t.tool_id for t in domain_tools}
            result_ids = result_ids.intersection(domain_ids)

        # 按标签过滤
        if tags:
            tag_result_ids = set()
            for tag in tags:
                tag_tools = self.find_by_tag(tag, enabled_only=False)
                tag_ids = {t.tool_id for t in tag_tools}
                tag_result_ids = tag_result_ids.union(tag_ids)
            result_ids = result_ids.intersection(tag_result_ids)

        # 转换为工具列表
        tools = [self._tools[tid] for tid in result_ids if tid in self._tools]

        # 按优先级过滤
        if min_priority:
            priority_order = {
                ToolPriority.CRITICAL: 4,
                ToolPriority.HIGH: 3,
                ToolPriority.MEDIUM: 2,
                ToolPriority.LOW: 1,
            }
            min_level = priority_order[min_priority]
            tools = [t for t in tools if priority_order.get(t.priority, 0) >= min_level]

        # 按优先级排序
        priority_order = {
            ToolPriority.CRITICAL: 4,
            ToolPriority.HIGH: 3,
            ToolPriority.MEDIUM: 2,
            ToolPriority.LOW: 1,
        }
        tools.sort(key=lambda t: (-priority_order.get(t.priority, 0), -t.performance.success_rate))

        # 过滤禁用的工具
        if enabled_only:
            tools = [t for t in tools if t.enabled]

        return tools

    def get_statistics(self) -> dict[str, Any]:
        """
        获取工具统计信息 (包含缓存统计, P2-1)

        Returns:
            统计信息字典
        """
        total_tools = len(self._tools)
        enabled_tools = sum(1 for t in self._tools.values() if t.enabled)

        category_counts = {
            cat.value: len(self._category_index.get(cat, set())) for cat in ToolCategory
        }

        total_calls = sum(t.performance.total_calls for t in self._tools.values())
        total_success = sum(t.performance.successful_calls for t in self._tools.values())
        overall_success_rate = total_success / total_calls if total_calls > 0 else 0.0

        # 💾 缓存统计 (P2-1)
        cache_stats = self._get_cache_statistics()

        return {
            "total_tools": total_tools,
            "enabled_tools": enabled_tools,
            "disabled_tools": total_tools - enabled_tools,
            "category_distribution": category_counts,
            "total_calls": total_calls,
            "total_success": total_success,
            "overall_success_rate": overall_success_rate,
            "cache_performance": cache_stats,  # 新增缓存性能统计
        }

    def _get_cache_statistics(self) -> dict[str, Any]:
        """
        获取缓存统计信息 (P2-1)

        Returns:
            缓存统计字典
        """
        # 获取各个方法的缓存信息
        find_by_category_info = self.find_by_category.cache_info()
        find_by_domain_info = self.find_by_domain.cache_info()

        return {
            "find_by_category": {
                "hits": find_by_category_info.hits,
                "misses": find_by_category_info.misses,
                "size": find_by_category_info.currsize,
                "hit_rate": find_by_category_info.hits
                / max(find_by_category_info.hits + find_by_category_info.misses, 1),
            },
            "find_by_domain": {
                "hits": find_by_domain_info.hits,
                "misses": find_by_domain_info.misses,
                "size": find_by_domain_info.currsize,
                "hit_rate": find_by_domain_info.hits
                / max(find_by_domain_info.hits + find_by_domain_info.misses, 1),
            },
        }

    def clear_cache(self):
        """
        清除所有缓存 (P2-1)

        在工具注册/更新后调用，以保持缓存一致性。
        """
        self.find_by_category.cache_clear()
        self.find_by_domain.cache_clear()
        logger.info("🧹 工具缓存已清除")

    def update_tool_performance(self, tool_id: str, execution_time: float, success: bool):
        """
        更新工具性能指标

        Args:
            tool_id: 工具ID
            execution_time: 执行时间(秒)
            success: 是否成功
        """
        tool = self._tools.get(tool_id)
        if not tool:
            logger.warning(f"⚠️ 工具不存在: {tool_id}")
            return

        tool.performance.update(execution_time, success)
        tool.updated_at = datetime.now()


# 全局工具注册中心实例
_global_registry = ToolRegistry()


def get_global_registry() -> ToolRegistry:
    """获取全局工具注册中心"""
    return _global_registry


__all__ = [
    "ToolCapability",
    "ToolCategory",
    "ToolDefinition",
    "ToolPerformance",
    "ToolPriority",
    "ToolRegistry",
    "get_global_registry",
]
