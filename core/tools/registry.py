#!/usr/bin/env python3
from __future__ import annotations
"""
统一工具注册系统 - 装饰器模式

基于 Hermes Agent 的设计理念，实现模块级工具自动注册。
支持装饰器模式注册、类型检查和 OpenAI function calling schema 生成。

核心特性:
1. 装饰器模式注册工具
2. 自动类型检查和验证
3. OpenAI function calling schema 生成
4. 支持工具分类、域和标签

作者: Athena平台团队
创建时间: 2026-03-19
版本: v1.0.0
"""

import functools
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from .base import ToolCategory, ToolDefinition, ToolRegistry, get_global_registry

logger = logging.getLogger(__name__)


class ParameterType(Enum):
    """参数类型枚举"""

    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


@dataclass
class ParameterSchema:
    """
    参数模式定义

    用于定义工具参数的类型和约束。
    """

    name: str
    param_type: ParameterType
    description: str
    required: bool = True
    default: Any = None
    enum: Optional[list[str]] = None  # 枚举值
    min_value: Optional[float] = None  # 最小值 (用于 number/integer)
    max_value: Optional[float] = None  # 最大值
    items_type: ParameterType | None = None  # 数组元素类型
    properties: dict[str, ParameterSchema] | None = None  # 对象属性

    def to_openai_schema(self) -> dict[str, Any]:
        """
        转换为 OpenAI 参数 schema

        Returns:
            dict: OpenAI 格式的参数定义
        """
        schema: dict[str, Any] = {
            "type": self.param_type.value,
            "description": self.description,
        }

        if self.enum:
            schema["enum"] = self.enum

        if self.param_type in (ParameterType.INTEGER, ParameterType.NUMBER):
            if self.min_value is not None:
                schema["minimum"] = self.min_value
            if self.max_value is not None:
                schema["maximum"] = self.max_value

        if self.param_type == ParameterType.ARRAY and self.items_type:
            schema["items"] = {"type": self.items_type.value}

        if self.param_type == ParameterType.OBJECT and self.properties:
            props = {}
            for name, param in self.properties.items():
                props[name] = param.to_openai_schema()
            schema["properties"] = props

        return schema


@dataclass
class RegisteredTool:
    """
    已注册工具的完整定义

    包含工具的所有元数据和执行函数。
    """

    tool_id: str
    name: str
    description: str
    category: ToolCategory
    parameters: list[ParameterSchema]
    handler: Callable[..., Any]
    domains: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    priority: int = 1
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)

    def to_tool_definition(self) -> ToolDefinition:
        """
        转换为 ToolDefinition

        Returns:
            ToolDefinition: 工具定义对象
        """
        required_params = [p.name for p in self.parameters if p.required]
        optional_params = [p.name for p in self.parameters if not p.required]

        return ToolDefinition(
            tool_id=self.tool_id,
            name=self.name,
            description=self.description,
            category=self.category,
            required_params=required_params,
            optional_params=optional_params,
            domains=self.domains,
            tags=self.tags,
            priority=self.priority,
            enabled=self.enabled,
        )

    def to_openai_schema(self) -> dict[str, Any]:
        """
        生成 OpenAI function calling schema

        Returns:
            dict: OpenAI 格式的 function calling schema
        """
        properties = {}
        required = []

        for param in self.parameters:
            properties[param.name] = param.to_openai_schema()
            if param.required:
                required.append(param.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }


class UnifiedToolRegistry:
    """
    统一工具注册中心

    使用装饰器模式注册工具，支持模块级自动注册。
    """

    def __init__(self, registry: ToolRegistry | None = None):
        """
        初始化统一工具注册中心

        Args:
            registry: 底层工具注册中心 (默认使用全局注册中心)
        """
        self.registry = registry or get_global_registry()
        self._registered_tools: dict[str, RegisteredTool] = {}

        logger.info("🔧 UnifiedToolRegistry 初始化完成")

    def tool(
        self,
        tool_id: str,
        name: str,
        description: str,
        category: ToolCategory,
        parameters: list[ParameterSchema],
        domains: Optional[list[str]] = None,
        tags: Optional[list[str]] = None,
        priority: int = 1,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """
        工具注册装饰器

        Args:
            tool_id: 工具唯一标识
            name: 工具名称
            description: 工具描述
            category: 工具分类
            parameters: 参数模式列表
            domains: 适用领域
            tags: 标签
            priority: 优先级

        Returns:
            装饰器函数

        Example:
            >>> registry = UnifiedToolRegistry()
            >>> @registry.tool(
            ...     tool_id="patent_search",
            ...     name="专利检索",
            ...     description="搜索专利数据库",
            ...     category=ToolCategory.PATENT_SEARCH,
            ...     parameters=[
            ...         ParameterSchema(
            ...             name="query",
            ...             param_type=ParameterType.STRING,
            ...             description="搜索关键词",
            ...             required=True
            ...         )
            ...     ]
            ... )
            ... async def search_patents(query: str) -> dict:
            ...     # 实现检索逻辑
            ...     pass
        """

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            # 创建已注册工具
            registered = RegisteredTool(
                tool_id=tool_id,
                name=name,
                description=description,
                category=category,
                parameters=parameters,
                handler=func,
                domains=domains or [],
                tags=tags or [],
                priority=priority,
            )

            # 存储到本地注册表
            self._registered_tools[tool_id] = registered

            # 同步到底层注册中心
            tool_def = registered.to_tool_definition()
            self.registry.register_tool(tool_def)

            logger.info(f"✅ 工具已注册: {name} (ID: {tool_id}, Category: {category.value})")

            @functools.wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                return await func(*args, **kwargs)

            # 附加元数据到函数
            wrapper._tool_metadata = registered  # type: ignore

            return wrapper

        return decorator

    def get_tool(self, tool_id: str) -> RegisteredTool | None:
        """
        获取已注册的工具

        Args:
            tool_id: 工具ID

        Returns:
            RegisteredTool | None: 工具定义
        """
        return self._registered_tools.get(tool_id)

    def get_all_tools(self) -> list[RegisteredTool]:
        """
        获取所有已注册的工具

        Returns:
            list[RegisteredTool]: 工具列表
        """
        return list(self._registered_tools.values())

    def get_tools_by_category(self, category: ToolCategory) -> list[RegisteredTool]:
        """
        按分类获取工具

        Args:
            category: 工具分类

        Returns:
            list[RegisteredTool]: 该分类下的工具列表
        """
        return [t for t in self._registered_tools.values() if t.category == category]

    def get_tools_by_domain(self, domain: str) -> list[RegisteredTool]:
        """
        按领域获取工具

        Args:
            domain: 领域名称

        Returns:
            list[RegisteredTool]: 该领域下的工具列表
        """
        return [t for t in self._registered_tools.values() if domain in t.domains]

    def to_openai_schemas(self, tool_ids: Optional[list[str]] = None) -> list[dict]:
        """
        生成 OpenAI function calling schemas

        Args:
            tool_ids: 要生成的工具ID列表 (None表示全部)

        Returns:
            list[dict]: OpenAI schemas 列表
        """
        if tool_ids:
            tools = [self._registered_tools.get(tid) for tid in tool_ids]
            tools = [t for t in tools if t is not None]
        else:
            tools = list(self._registered_tools.values())

        return [t.to_openai_schema() for t in tools if t.enabled]

    def validate_parameters(self, tool_id: str, params: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        验证工具参数

        Args:
            tool_id: 工具ID
            params: 参数字典

        Returns:
            tuple[bool, list[str]]: (是否有效, 错误消息列表)
        """
        tool = self._registered_tools.get(tool_id)
        if not tool:
            return False, [f"工具不存在: {tool_id}"]

        errors = []

        # 检查必需参数
        for param in tool.parameters:
            if param.required and param.name not in params:
                errors.append(f"缺少必需参数: {param.name}")
                continue

            if param.name not in params:
                continue

            value = params[param.name]

            # 类型检查
            type_valid = self._validate_type(value, param)
            if not type_valid:
                errors.append(
                    f"参数 {param.name} 类型错误: 期望 {param.param_type.value}, "
                    f"实际 {type(value).__name__}"
                )

            # 枚举检查
            if param.enum and value not in param.enum:
                errors.append(f"参数 {param.name} 值无效: {value}, 有效值: {param.enum}")

            # 范围检查
            if param.param_type in (ParameterType.INTEGER, ParameterType.NUMBER):
                if isinstance(value, int | float):
                    if param.min_value is not None and value < param.min_value:
                        errors.append(f"参数 {param.name} 值 {value} 小于最小值 {param.min_value}")
                    if param.max_value is not None and value > param.max_value:
                        errors.append(f"参数 {param.name} 值 {value} 大于最大值 {param.max_value}")

        return len(errors) == 0, errors

    def _validate_type(self, value: Any, param: ParameterSchema) -> bool:
        """
        验证参数类型

        Args:
            value: 参数值
            param: 参数模式

        Returns:
            bool: 类型是否匹配
        """
        type_mapping = {
            ParameterType.STRING: str,
            ParameterType.INTEGER: int,
            ParameterType.NUMBER: int | float,
            ParameterType.BOOLEAN: bool,
            ParameterType.ARRAY: list,
            ParameterType.OBJECT: dict,
        }

        expected_type = type_mapping.get(param.param_type)
        if expected_type is None:
            return True  # 未知类型，跳过检查

        return isinstance(value, expected_type)

    def get_statistics(self) -> dict[str, Any]:
        """
        获取注册统计信息

        Returns:
            dict: 统计信息
        """
        by_category: dict[str, int] = {}
        by_domain: dict[str, int] = {}

        for tool in self._registered_tools.values():
            # 按分类统计
            cat = tool.category.value
            by_category[cat] = by_category.get(cat, 0) + 1

            # 按领域统计
            for domain in tool.domains:
                by_domain[domain] = by_domain.get(domain, 0) + 1

        return {
            "total_tools": len(self._registered_tools),
            "enabled_tools": sum(1 for t in self._registered_tools.values() if t.enabled),
            "by_category": by_category,
            "by_domain": by_domain,
            "tools": [
                {
                    "id": t.tool_id,
                    "name": t.name,
                    "category": t.category.value,
                    "domains": t.domains,
                    "enabled": t.enabled,
                }
                for t in self._registered_tools.values()
            ],
        }


# ========================================
# 全局统一注册中心实例
# ========================================
_global_unified_registry: UnifiedToolRegistry | None = None


def get_unified_registry() -> UnifiedToolRegistry:
    """获取全局统一工具注册中心"""
    global _global_unified_registry
    if _global_unified_registry is None:
        _global_unified_registry = UnifiedToolRegistry()
    return _global_unified_registry


# ========================================
# 便捷装饰器
# ========================================


def register_tool(
    tool_id: str,
    name: str,
    description: str,
    category: ToolCategory,
    parameters: list[ParameterSchema],
    domains: Optional[list[str]] = None,
    tags: Optional[list[str]] = None,
    priority: int = 1,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    便捷工具注册装饰器

    直接使用全局注册中心注册工具

    Args:
        tool_id: 工具唯一标识
        name: 工具名称
        description: 工具描述
        category: 工具分类
        parameters: 参数模式列表
        domains: 适用领域
        tags: 标签
        priority: 优先级

    Returns:
        装饰器函数
    """
    registry = get_unified_registry()
    return registry.tool(
        tool_id=tool_id,
        name=name,
        description=description,
        category=category,
        parameters=parameters,
        domains=domains,
        tags=tags,
        priority=priority,
    )


__all__ = [
    "ParameterSchema",
    "ParameterType",
    "RegisteredTool",
    "UnifiedToolRegistry",
    "get_unified_registry",
    "register_tool",
]
