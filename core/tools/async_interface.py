#!/usr/bin/env python3
"""
Athena工具系统 - 统一异步执行接口
Unified Async Execution Interface

为所有工具提供统一的异步执行接口，支持同步/异步工具混合使用。

核心功能:
1. BaseTool抽象类 - 统一工具接口
2. 异步上下文管理器
3. 向后兼容层 - 同步工具包装器
4. 类型提示和验证

作者: Athena平台团队
创建时间: 2026-04-19
版本: v1.0.0
"""

import asyncio
import functools
import inspect
import logging
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Optional, TypeVar, Union

from .feature_gates import feature

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class ToolContext:
    """
    工具执行上下文

    包含工具执行时的上下文信息。
    """

    session_id: Optional[str] = None  # 会话ID
    user_id: Optional[str] = None  # 用户ID
    request_id: Optional[str] = None  # 请求ID
    metadata: Optional[Dict[str, Any]] = None  # 元数据

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "request_id": self.request_id,
            "metadata": self.metadata or {},
        }


class BaseTool(ABC):
    """
    基础工具抽象类

    所有工具都应继承此类，实现统一的异步接口。
    """

    def __init__(self, name: str, description: str = ""):
        """
        初始化工具

        Args:
            name: 工具名称
            description: 工具描述
        """
        self.name = name
        self.description = description

    @abstractmethod
    async def call(
        self, parameters: Dict[str, Any], context: Optional[ToolContext] = None
    ) -> Any:
        """
        调用工具（异步接口）

        Args:
            parameters: 参数字典
            context: 工具上下文

        Returns:
            Any: 执行结果
        """
        pass

    async def __call__(
        self, parameters: Dict[str, Any], context: Optional[ToolContext] = None
    ) -> Any:
        """
        可调用对象接口

        Args:
            parameters: 参数字典
            context: 工具上下文

        Returns:
            Any: 执行结果
        """
        return await self.call(parameters, context)

    def validate_parameters(self, parameters: Dict[str, Any]) -> tuple[bool, list[str]]:
        """
        验证参数（子类可重写）

        Args:
            parameters: 参数字典

        Returns:
            tuple[bool, list[str]]: (是否有效, 错误消息列表)
        """
        return True, []


class SyncToolWrapper(BaseTool):
    """
    同步工具包装器

    将同步函数包装为异步工具，实现向后兼容。
    """

    def __init__(
        self,
        name: str,
        sync_handler: Callable[[Dict[str, Any]], Any],
        description: str = "",
    ):
        """
        初始化同步工具包装器

        Args:
            name: 工具名称
            sync_handler: 同步处理函数
            description: 工具描述
        """
        super().__init__(name, description)
        self.sync_handler = sync_handler

    async def call(
        self, parameters: Dict[str, Any], context: Optional[ToolContext] = None
    ) -> Any:
        """
        调用同步工具（在线程池中执行）

        Args:
            parameters: 参数字典
            context: 工具上下文（同步工具忽略）

        Returns:
            Any: 执行结果
        """
        # 在线程池中执行同步函数
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.sync_handler, parameters)


class AsyncToolWrapper(BaseTool):
    """
    异步工具包装器

    将异步函数包装为标准工具。
    """

    def __init__(
        self,
        name: str,
        async_handler: Callable[[Dict[str, Any]], Awaitable[Any]],
        description: str = "",
    ):
        """
        初始化异步工具包装器

        Args:
            name: 工具名称
            async_handler: 异步处理函数
            description: 工具描述
        """
        super().__init__(name, description)
        self.async_handler = async_handler

    async def call(
        self, parameters: Dict[str, Any], context: Optional[ToolContext] = None
    ) -> Any:
        """
        调用异步工具

        Args:
            parameters: 参数字典
            context: 工具上下文（异步工具忽略）

        Returns:
            Any: 执行结果
        """
        return await self.async_handler(parameters)


def to_async_tool(
    name: str,
    description: str = "",
) -> Callable[[Union[Callable[[Dict[str, Any]], Any], Callable[[Dict[str, Any]], Awaitable[Any]]]], BaseTool]:
    """
    装饰器：将函数转换为异步工具

    自动检测同步/异步函数并选择合适的包装器。

    Args:
        name: 工具名称
        description: 工具描述

    Returns:
        装饰器函数

    Example:
        >>> @to_async_tool("my_tool", "我的工具")
        ... async def my_handler(params: dict) -> Any:
        ...     return {"result": "success"}
    """
    def decorator(
        func: Union[Callable[[Dict[str, Any]], Any], Callable[[Dict[str, Any]], Awaitable[Any]]]
    ) -> BaseTool:
        # 检测是否为异步函数
        if asyncio.iscoroutinefunction(func):
            return AsyncToolWrapper(
                name=name,
                async_handler=func,  # type: ignore
                description=description,
            )
        else:
            return SyncToolWrapper(
                name=name,
                sync_handler=func,  # type: ignore
                description=description,
            )

    return decorator


@asynccontextmanager
async def tool_context(
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    request_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    """
    工具执行上下文管理器

    Args:
        session_id: 会话ID
        user_id: 用户ID
        request_id: 请求ID
        metadata: 元数据

    Yields:
        ToolContext: 工具上下文对象
    """
    context = ToolContext(
        session_id=session_id,
        user_id=user_id,
        request_id=request_id,
        metadata=metadata,
    )

    try:
        logger.debug(f"🔧 工具上下文已创建: {request_id}")
        yield context
    finally:
        logger.debug(f"🔧 工具上下文已销毁: {request_id}")


class ToolExecutor:
    """
    工具执行器

    统一执行同步/异步工具，提供错误处理和重试机制。
    """

    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: float = 30.0,
    ):
        """
        初始化工具执行器

        Args:
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            timeout: 超时时间（秒）
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout

    async def execute(
        self,
        tool: BaseTool,
        parameters: Dict[str, Any],
        context: Optional[ToolContext] = None,
    ) -> Any:
        """
        执行工具（带重试和超时）

        Args:
            tool: 工具对象
            parameters: 参数字典
            context: 工具上下文

        Returns:
            Any: 执行结果

        Raises:
            Exception: 执行失败（重试耗尽后）
        """
        # 参数验证
        is_valid, errors = tool.validate_parameters(parameters)
        if not is_valid:
            error_msg = f"参数验证失败: {', '.join(errors)}"
            logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)

        # 执行（带重试）
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                # 带超时的异步执行
                result = await asyncio.wait_for(
                    tool.call(parameters, context),
                    timeout=self.timeout,
                )

                logger.info(f"✅ 工具执行成功: {tool.name} (尝试 {attempt + 1}/{self.max_retries})")
                return result

            except asyncio.TimeoutError:
                last_exception = TimeoutError(f"工具执行超时: {tool.name}")
                logger.warning(f"⏰ {last_exception} (尝试 {attempt + 1}/{self.max_retries})")

            except Exception as e:
                last_exception = e
                logger.warning(
                    f"❌ 工具执行失败: {tool.name} - {e} (尝试 {attempt + 1}/{self.max_retries})"
                )

            # 重试延迟
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay)

        # 重试耗尽
        logger.error(f"❌ 工具执行失败（重试耗尽）: {tool.name}")
        raise last_exception or Exception("工具执行失败")


# ========================================
# 便捷函数
# ========================================


async def call_tool(
    tool: BaseTool,
    parameters: Dict[str, Any],
    context: Optional[ToolContext] = None,
    executor: Optional[ToolExecutor] = None,
) -> Any:
    """
    调用工具（便捷函数）

    Args:
        tool: 工具对象
        parameters: 参数字典
        context: 工具上下文
        executor: 工具执行器（默认创建新的）

    Returns:
        Any: 执行结果
    """
    if executor is None:
        executor = ToolExecutor()

    return await executor.execute(tool, parameters, context)


__all__ = [
    "BaseTool",
    "SyncToolWrapper",
    "AsyncToolWrapper",
    "ToolContext",
    "ToolExecutor",
    "to_async_tool",
    "tool_context",
    "call_tool",
]
