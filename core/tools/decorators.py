#!/usr/bin/env python3
from __future__ import annotations
"""
工具装饰器模块
Tool Decorators

提供@tool装饰器，用于标记和注册工具函数。

核心功能:
1. 工具标记 - _is_tool属性
2. 元数据提取 - _tool_name, _tool_description, _tool_tags
3. 懒加载支持 - lazy参数
4. 自动注册 - 可选自动注册到统一注册表

Author: Athena平台团队
Created: 2026-04-19
Version: v2.0.0
"""

import functools
import logging
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass
class ToolMetadata:
    """
    工具元数据

    存储工具的描述性信息。
    """

    name: str  # 工具名称
    description: str  # 工具描述
    tags: list[str] = field(default_factory=list)  # 标签
    category: Optional[str] = None  # 分类
    version: str = "1.0.0"  # 版本
    author: str = "Athena Team"  # 作者
    lazy: bool = False  # 是否懒加载
    timeout: float = 30.0  # 超时时间(秒)
    max_retries: int = 3  # 最大重试次数


def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[list[str]] = None,
    category: Optional[str] = None,
    version: str = "1.0.0",
    author: str = "Athena Team",
    lazy: bool = False,
    timeout: float = 30.0,
    max_retries: int = 3,
    auto_register: bool = True,
):
    """
    工具装饰器

    标记函数为工具，并附加元数据。

    Args:
        name: 工具名称（默认使用函数名）
        description: 工具描述（默认使用函数文档字符串）
        tags: 工具标签列表
        category: 工具分类
        version: 工具版本
        author: 工具作者
        lazy: 是否懒加载
        timeout: 超时时间(秒)
        max_retries: 最大重试次数
        auto_register: 是否自动注册到统一注册表

    Returns:
        装饰器函数

    Examples:
        >>> @tool()
        >>> def my_function(param1: str) -> str:
        ...     '''我的工具函数'''
        ...     return param1

        >>> @tool(name="custom_name", description="自定义描述", tags=["search", "web"])
        >>> def search_tool(query: str) -> dict:
        ...     return {"results": []}
    """

    def decorator(func: Callable) -> Callable:
        # 提取元数据
        tool_name = name or func.__name__
        tool_description = description or func.__doc__ or ""
        tool_tags = tags or []

        # 创建元数据对象
        metadata = ToolMetadata(
            name=tool_name,
            description=tool_description,
            tags=tool_tags,
            category=category,
            version=version,
            author=author,
            lazy=lazy,
            timeout=timeout,
            max_retries=max_retries,
        )

        # 附加元数据到函数
        func._is_tool = True  # type: ignore
        func._tool_name = tool_name  # type: ignore
        func._tool_description = tool_description  # type: ignore
        func._tool_tags = tool_tags  # type: ignore
        func._tool_metadata = metadata  # type: ignore

        # 可选：自动注册到统一注册表
        if auto_register:
            try:
                # 延迟导入避免循环依赖
                from core.tools.unified_registry import get_unified_registry

                registry = get_unified_registry()

                # 构建工具ID
                tool_id = f"{func.__module__}.{func.__name__}"

                # 注册为懒加载工具
                registry.register_lazy(
                    tool_id=tool_id,
                    import_path=func.__module__,
                    function_name=func.__name__,
                    metadata={
                        "name": tool_name,
                        "description": tool_description,
                        "tags": tool_tags,
                        "category": category,
                        "version": version,
                        "author": author,
                    },
                )

                logger.debug(f"✅ 工具已自动注册: {tool_id}")

            except Exception as e:
                logger.warning(f"⚠️ 自动注册失败 {tool_name}: {e}")

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            """包装函数"""
            return func(*args, **kwargs)

        # 传递元数据到包装函数
        wrapper._is_tool = True  # type: ignore
        wrapper._tool_name = tool_name  # type: ignore
        wrapper._tool_description = tool_description  # type: ignore
        wrapper._tool_tags = tool_tags  # type: ignore
        wrapper._tool_metadata = metadata  # type: ignore
        wrapper._original_func = func  # type: ignore

        return wrapper

    return decorator


def is_tool(func: Any) -> bool:
    """
    检查函数是否是工具

    Args:
        func: 函数对象

    Returns:
        bool: 是否是工具
    """
    return getattr(func, "_is_tool", False)


def get_tool_metadata(func: Any) -> ToolMetadata | None:
    """
    获取工具元数据

    Args:
        func: 函数对象

    Returns:
        ToolMetadata对象，如果不是工具返回None
    """
    if not is_tool(func):
        return None

    return getattr(func, "_tool_metadata", None)


def get_tool_name(func: Any) -> Optional[str]:
    """
    获取工具名称

    Args:
        func: 函数对象

    Returns:
        str: 工具名称，如果不是工具返回None
    """
    if not is_tool(func):
        return None
    return getattr(func, "_tool_name", None)


def get_tool_description(func: Any) -> Optional[str]:
    """
    获取工具描述

    Args:
        func: 函数对象

    Returns:
        str: 工具描述，如果不是工具返回None
    """
    if not is_tool(func):
        return None
    return getattr(func, "_tool_description", None)


def get_tool_tags(func: Any) -> Optional[list[str]]:
    """
    获取工具标签

    Args:
        func: 函数对象

    Returns:
        list[str]: 工具标签，如果不是工具返回None
    """
    if not is_tool(func):
        return None
    return getattr(func, "_tool_tags", None)


__all__ = [
    "tool",
    "ToolMetadata",
    "is_tool",
    "get_tool_metadata",
    "get_tool_name",
    "get_tool_description",
    "get_tool_tags",
]
