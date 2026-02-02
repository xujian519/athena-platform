#!/usr/bin/env python3
"""
Hook系统基础模块

定义Hook的基础类型、接口和注册中心。

Author: Athena平台团队
Created: 2026-01-20
Version: v1.0.0
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class HookType(Enum):
    """Hook类型枚举"""

    # 任务生命周期
    PRE_TASK_START = "pre_task_start"
    POST_TASK_COMPLETE = "post_task_complete"

    # 工具调用
    PRE_TOOL_USE = "pre_tool_use"
    POST_TOOL_USE = "post_tool_use"

    # 错误处理
    ON_ERROR = "on_error"

    # 检查点
    ON_CHECKPOINT = "on_checkpoint"

    # 状态变化
    ON_STATE_CHANGE = "on_state_change"

    # 推理过程
    PRE_REASONING = "pre_reasoning"
    POST_REASONING = "post_reasoning"


@dataclass
class HookContext:
    """
    Hook上下文

    包含Hook执行时需要的所有上下文信息。
    """

    hook_type: HookType
    agent: Any = None
    task: Any = None
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def get(self, key: str, default: Any = None) -> Any:
        """获取上下文数据"""
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> Any:
        """设置上下文数据"""
        self.data[key] = value

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "hook_type": self.hook_type.value,
            "agent": str(self.agent) if self.agent else None,
            "task": str(self.task) if self.task else None,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
        }


class HookFunction:
    """
    Hook函数包装器

    封装一个可被Hook执行的函数。
    """

    def __init__(
        self,
        name: str,
        hook_type: HookType,
        func: Callable,
        priority: int = 0,
        async_mode: bool = True,
        enabled: bool = True,
    ):
        """
        初始化Hook函数

        Args:
            name: Hook名称
            hook_type: Hook类型
            func: 要执行的函数
            priority: 优先级 (数字越大优先级越高)
            async_mode: 是否异步执行
            enabled: 是否启用
        """
        self.name = name
        self.hook_type = hook_type
        self.func = func
        self.priority = priority
        self.async_mode = async_mode
        self.enabled = enabled

    async def execute(self, context: HookContext):
        """
        执行Hook

        Args:
            context: Hook上下文
        """
        if not self.enabled:
            logger.debug(f"⏭️ Hook已跳过: {self.name}")
            return

        logger.debug(f"🔗 执行Hook: {self.name} ({self.hook_type.value})")

        start_time = datetime.now()

        try:
            if self.async_mode:
                result = await self.func(context)
            else:
                result = self.func(context)

            execution_time = (datetime.now() - start_time).total_seconds()

            logger.debug(f"✅ Hook执行成功: {self.name} " f"(耗时: {execution_time*1000:.2f}ms)")

            return result

        except Exception as e:
            logger.error(f"❌ Hook执行失败: {self.name}, 错误: {e}")
            # 不抛出异常,避免影响主流程
            return None

    def __repr__(self) -> str:
        return f"HookFunction({self.name}, type={self.hook_type.value}, priority={self.priority})"


class HookRegistry:
    """
    Hook注册中心

    管理所有Hook的注册、触发和生命周期。
    """

    def __init__(self):
        """初始化Hook注册中心"""
        self._hooks: dict[HookType, list[HookFunction]] = {}
        self._global_hooks: list[HookFunction] = []

        logger.info("🔗 HookRegistry初始化完成")

    def register(self, hook: HookFunction) -> "HookRegistry":
        """
        注册Hook

        Args:
            hook: HookFunction对象

        Returns:
            self (支持链式调用)
        """
        hook_type = hook.hook_type

        if hook_type not in self._hooks:
            self._hooks[hook_type] = []

        self._hooks[hook_type].append(hook)

        # 按优先级排序 (数字越大优先级越高)
        self._hooks[hook_type].sort(key=lambda h: h.priority, reverse=True)

        logger.info(
            f"✅ Hook已注册: {hook.name} " f"(类型: {hook_type.value}, 优先级: {hook.priority})"
        )

        return self

    def register_function(
        self,
        name: str,
        hook_type: HookType,
        func: Callable,
        priority: int = 0,
        async_mode: bool = True,
    ) -> HookFunction:
        """
        便捷方法: 直接注册一个函数为Hook

        Args:
            name: Hook名称
            hook_type: Hook类型
            func: 要注册的函数
            priority: 优先级
            async_mode: 是否异步

        Returns:
            创建的HookFunction对象
        """
        hook = HookFunction(
            name=name, hook_type=hook_type, func=func, priority=priority, async_mode=async_mode
        )

        self.register(hook)

        return hook

    async def trigger(self, hook_type: HookType, context: HookContext) -> list[Any]:
        """
        触发指定类型的所有Hook

        Args:
            hook_type: Hook类型
            context: Hook上下文

        Returns:
            所有Hook的执行结果列表
        """
        if hook_type not in self._hooks:
            logger.debug(f"📭 没有注册的Hook: {hook_type.value}")
            return []

        results = []

        for hook in self._hooks[hook_type]:
            try:
                result = await hook.execute(context)
                results.append(result)
            except Exception as e:
                logger.error(f"❌ Hook执行异常: {hook.name}, 错误: {e}")

        return results

    async def trigger_parallel(self, hook_type: HookType, context: HookContext) -> list[Any]:
        """
        并行触发指定类型的所有Hook

        Args:
            hook_type: Hook类型
            context: Hook上下文

        Returns:
            所有Hook的执行结果列表
        """
        if hook_type not in self._hooks:
            return []

        # 并行执行所有Hook
        tasks = [hook.execute(context) for hook in self._hooks[hook_type] if hook.enabled]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 过滤异常结果
        return [r for r in results if not isinstance(r, Exception)]

    def get_hooks(self, hook_type: HookType) -> list[HookFunction]:
        """
        获取指定类型的所有Hook

        Args:
            hook_type: Hook类型

        Returns:
            Hook列表
        """
        return self._hooks.get(hook_type, [])

    def remove_hook(self, hook_name: str) -> bool:
        """
        移除指定的Hook

        Args:
            hook_name: Hook名称

        Returns:
            是否移除成功
        """
        removed = False

        for hook_type, hooks in self._hooks.items():
            self._hooks[hook_type] = [h for h in hooks if h.name != hook_name]

            if len(self._hooks[hook_type]) < len(hooks):
                removed = True

        if removed:
            logger.info(f"🗑️ Hook已移除: {hook_name}")

        return removed

    def enable_hook(self, hook_name: str) -> Any:
        """启用Hook"""
        for hooks in self._hooks.values():
            for hook in hooks:
                if hook.name == hook_name:
                    hook.enabled = True
                    logger.info(f"✅ Hook已启用: {hook_name}")

    def disable_hook(self, hook_name: str) -> Any:
        """禁用Hook"""
        for hooks in self._hooks.values():
            for hook in hooks:
                if hook.name == hook_name:
                    hook.enabled = False
                    logger.info(f"⏸️ Hook已禁用: {hook_name}")

    def clear(self) -> Any:
        """清空所有Hook"""
        self._hooks.clear()
        logger.info("🗑️ 所有Hook已清空")


# 全局Hook注册中心实例
_global_registry = HookRegistry()


def get_global_registry() -> HookRegistry:
    """获取全局Hook注册中心"""
    return _global_registry


def register_hook(hook_type: HookType | None = None, name: str | None = None, priority: int = 0):
    """
    装饰器: 快速注册Hook

    Args:
        hook_type: Hook类型
        name: Hook名称 (可选,默认使用函数名)
        priority: 优先级

    Returns:
        装饰器函数

    Example:
        ```python
        @register_hook(HookType.POST_TASK_COMPLETE, priority=100)
        async def on_task_complete(context: HookContext):
            print(f"任务完成: {context.task}")
        ```
    """

    def decorator(func: Callable) -> Callable:
        hook_name = name or func.__name__

        _global_registry.register_function(
            name=hook_name,
            hook_type=hook_type,
            func=func,
            priority=priority,
            async_mode=asyncio.iscoroutinefunction(func),
        )

        return func

    return decorator


__all__ = [
    "HookContext",
    "HookFunction",
    "HookRegistry",
    "HookType",
    "get_global_registry",
    "register_hook",
]
