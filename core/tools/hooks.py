#!/usr/bin/env python3
"""
Athena工具调用Hook系统
Tool Call Hook System

提供工具调用生命周期中的拦截、监控和增强功能。

核心功能:
1. Hook事件定义 (PRE_TOOL_USE, POST_TOOL_USE, TOOL_FAILURE, SESSION_START)
2. Hook上下文和结果数据结构
3. Hook注册和执行管理
4. 内置Hook实现 (日志、限流、监控、验证)

Author: Athena平台团队
Created: 2026-04-19
Version: v1.0.0
"""

from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from core.logging_config import setup_logging

# 配置日志
logger = setup_logging()


class HookEvent(Enum):
    """Hook事件类型"""

    PRE_TOOL_USE = "pre_tool_use"  # 工具调用前
    POST_TOOL_USE = "post_tool_use"  # 工具调用后
    TOOL_FAILURE = "tool_failure"  # 工具调用失败
    SESSION_START = "session_start"  # 会话开始
    SESSION_END = "session_end"  # 会话结束


@dataclass
class HookContext:
    """Hook上下文信息

    包含工具调用的完整上下文信息，供Hook处理器使用。
    """

    tool_name: str  # 工具名称
    parameters: dict[str, Any]  # 调用参数
    context: dict[str, Any]  # 额外上下文
    request_id: str  # 请求ID
    timestamp: datetime  # 调用时间戳
    metadata: dict[str, Any]  # 元数据

    def __init__(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        context: dict[str, Any] | None = None,
        request_id: str | None = None,
        timestamp: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        self.tool_name = tool_name
        self.parameters = parameters
        self.context = context or {}
        self.request_id = request_id or ""
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}


@dataclass
class HookResult:
    """Hook执行结果

    Hook处理器可以修改工具调用行为或添加元数据。
    """

    should_proceed: bool = True  # 是否继续执行（False则阻止调用）
    modified_parameters: dict[str, Any] | None = None  # 修改后的参数
    metadata: dict[str, Any] = field(default_factory=dict)  # 添加的元数据
    error_message: str | None = None  # 错误信息（如果阻止调用）

    def __init__(
        self,
        should_proceed: bool = True,
        modified_parameters: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        error_message: str | None = None,
    ):
        self.should_proceed = should_proceed
        self.modified_parameters = modified_parameters
        self.metadata = metadata or {}
        self.error_message = error_message


class BaseHook(ABC):
    """Hook基类

    所有Hook处理器必须继承此类并实现process方法。
    """

    def __init__(self, hook_id: str, priority: int = 10, enabled: bool = True):
        """
        初始化Hook

        Args:
            hook_id: Hook唯一标识符
            priority: 优先级（数字越小优先级越高）
            enabled: 是否启用
        """
        self.hook_id = hook_id
        self.priority = priority
        self.enabled = enabled

    @abstractmethod
    async def process(
        self, event: HookEvent, hook_context: HookContext
    ) -> HookResult:
        """
        处理Hook事件

        Args:
            event: Hook事件类型
            hook_context: Hook上下文

        Returns:
            HookResult: Hook执行结果
        """
        pass

    def __repr__(self) -> str:
        return f"BaseHook(id={self.hook_id}, priority={self.priority}, enabled={self.enabled})"


class HookRegistry:
    """Hook注册表

    管理所有Hook的注册、执行和生命周期。
    """

    def __init__(self):
        """初始化Hook注册表"""
        # 按事件类型分组的Hook: {HookEvent: [BaseHook]}
        self._hooks: dict[HookEvent, list[BaseHook]] = {
            event: [] for event in HookEvent
        }

        # Hook统计
        self._stats = {
            "total_hooks": 0,
            "executed_hooks": 0,
            "blocked_calls": 0,
            "hook_errors": 0,
        }

        logger.info("🔧 Hook注册表初始化完成")

    def register(self, hook: BaseHook, events: list[HookEvent]) -> None:
        """
        注册Hook到指定事件

        Args:
            hook: Hook实例
            events: 要监听的事件列表
        """
        for event in events:
            self._hooks[event].append(hook)

        # 按优先级排序
        for event in events:
            self._hooks[event].sort(key=lambda h: h.priority)

        self._stats["total_hooks"] += len(events)
        logger.info(f"✅ Hook已注册: {hook.hook_id} -> {[e.value for e in events]}")

    def unregister(self, hook_id: str) -> bool:
        """
        注销指定Hook

        Args:
            hook_id: Hook ID

        Returns:
            bool: 是否成功注销
        """
        removed = False
        for event in self._hooks:
            original_length = len(self._hooks[event])
            self._hooks[event] = [
                h for h in self._hooks[event] if h.hook_id != hook_id
            ]
            # 如果删除后长度减少，说明确实删除了Hook
            if len(self._hooks[event]) < original_length:
                removed = True

        if removed:
            logger.info(f"🗑️ Hook已注销: {hook_id}")

        return removed

    def get_hooks(self, event: HookEvent) -> list[BaseHook]:
        """
        获取指定事件的所有Hook

        Args:
            event: Hook事件

        Returns:
            list[BaseHook]: Hook列表（按优先级排序）
        """
        return [h for h in self._hooks[event] if h.enabled]

    async def execute_hooks(
        self, event: HookEvent, hook_context: HookContext
    ) -> HookResult:
        """
        执行指定事件的所有Hook

        Args:
            event: Hook事件
            hook_context: Hook上下文

        Returns:
            HookResult: 合并后的Hook结果
        """
        hooks = self.get_hooks(event)

        if not hooks:
            return HookResult(should_proceed=True)

        result = HookResult(should_proceed=True)

        for hook in hooks:
            if not hook.enabled:
                continue

            try:
                self._stats["executed_hooks"] += 1
                hook_result = await hook.process(event, hook_context)

                # 如果Hook阻止调用，立即返回
                if not hook_result.should_proceed:
                    self._stats["blocked_calls"] += 1
                    logger.warning(
                        f"🚫 Hook阻止调用: {hook.hook_id} - {hook_result.error_message}"
                    )
                    return hook_result

                # 合并修改的参数
                if hook_result.modified_parameters:
                    if result.modified_parameters is None:
                        result.modified_parameters = {}
                    result.modified_parameters.update(hook_result.modified_parameters)

                # 合并元数据
                result.metadata.update(hook_result.metadata)

            except Exception as e:
                self._stats["hook_errors"] += 1
                logger.error(f"❌ Hook执行失败: {hook.hook_id} - {e}")

                # Hook错误不应阻止主流程
                continue

        return result

    def get_stats(self) -> dict[str, Any]:
        """获取Hook统计信息"""
        return {
            **self._stats,
            "hooks_by_event": {
                event.value: len(hooks) for event, hooks in self._hooks.items()
            },
        }

    def clear(self) -> None:
        """清除所有Hook"""
        for event in self._hooks:
            self._hooks[event].clear()

        self._stats = {
            "total_hooks": 0,
            "executed_hooks": 0,
            "blocked_calls": 0,
            "hook_errors": 0,
        }

        logger.info("🗑️ Hook注册表已清空")


# ==================== 内置Hook实现 ====================


class LoggingHook(BaseHook):
    """日志Hook

    记录所有工具调用的详细信息。
    """

    def __init__(self, enabled: bool = True):
        super().__init__(hook_id="logging_hook", priority=100, enabled=enabled)

    async def process(
        self, event: HookEvent, hook_context: HookContext
    ) -> HookResult:
        """记录工具调用日志"""
        if event == HookEvent.PRE_TOOL_USE:
            logger.info(
                f"🔧 工具调用开始: {hook_context.tool_name} "
                f"(request_id={hook_context.request_id})"
            )
            logger.debug(f"  参数: {hook_context.parameters}")

        elif event == HookEvent.POST_TOOL_USE:
            logger.info(
                f"✅ 工具调用完成: {hook_context.tool_name} "
                f"(request_id={hook_context.request_id})"
            )

        elif event == HookEvent.TOOL_FAILURE:
            logger.error(
                f"❌ 工具调用失败: {hook_context.tool_name} "
                f"(request_id={hook_context.request_id})"
            )

        return HookResult(should_proceed=True)


class MetricsHook(BaseHook):
    """监控指标Hook

    收集工具调用的性能指标。
    """

    def __init__(self, enabled: bool = True):
        super().__init__(hook_id="metrics_hook", priority=90, enabled=enabled)
        self._call_counts: dict[str, int] = {}
        self._call_times: dict[str, list[float]] = {}

    async def process(
        self, event: HookEvent, hook_context: HookContext
    ) -> HookResult:
        """收集性能指标"""
        tool_name = hook_context.tool_name

        if event == HookEvent.PRE_TOOL_USE:
            # 记录调用开始时间
            hook_context.metadata["_hook_start_time"] = time.time()

            # 统计调用次数
            self._call_counts[tool_name] = self._call_counts.get(tool_name, 0) + 1

        elif event == HookEvent.POST_TOOL_USE:
            # 计算执行时间
            start_time = hook_context.metadata.get("_hook_start_time")
            if start_time:
                execution_time = time.time() - start_time

                if tool_name not in self._call_times:
                    self._call_times[tool_name] = []

                self._call_times[tool_name].append(execution_time)

                # 保留最近100次记录
                if len(self._call_times[tool_name]) > 100:
                    self._call_times[tool_name].pop(0)

        return HookResult(should_proceed=True)

    def get_metrics(self, tool_name: str | None = None) -> dict[str, Any]:
        """
        获取性能指标

        Args:
            tool_name: 工具名称（None则返回所有）

        Returns:
            性能指标字典
        """
        if tool_name:
            call_times = self._call_times.get(tool_name, [])
            avg_time = sum(call_times) / len(call_times) if call_times else 0.0

            return {
                "call_count": self._call_counts.get(tool_name, 0),
                "avg_execution_time": avg_time,
                "last_calls": call_times[-10:],  # 最近10次
            }

        # 返回所有工具的指标
        return {
            name: self.get_metrics(name) for name in self._call_counts.keys()
        }


class ValidationHook(BaseHook):
    """验证Hook

    验证工具调用的参数和权限。
    """

    def __init__(self, enabled: bool = True):
        super().__init__(hook_id="validation_hook", priority=10, enabled=enabled)

    async def process(
        self, event: HookEvent, hook_context: HookContext
    ) -> HookResult:
        """验证工具调用"""
        if event != HookEvent.PRE_TOOL_USE:
            return HookResult(should_proceed=True)

        # 验证参数
        if not hook_context.parameters:
            return HookResult(
                should_proceed=False,
                error_message="参数不能为空",
            )

        # 验证工具名称
        if not hook_context.tool_name or not isinstance(hook_context.tool_name, str):
            return HookResult(
                should_proceed=False,
                error_message="工具名称无效",
            )

        # 验证请求ID
        if not hook_context.request_id:
            return HookResult(
                should_proceed=False,
                error_message="请求ID不能为空",
            )

        return HookResult(should_proceed=True)


class RateLimitHook(BaseHook):
    """速率限制Hook

    基于滑动窗口限制工具调用频率。
    """

    def __init__(
        self,
        max_calls: int = 100,
        window_seconds: int = 60,
        enabled: bool = True,
    ):
        """
        初始化速率限制Hook

        Args:
            max_calls: 时间窗口内最大调用次数
            window_seconds: 时间窗口（秒）
            enabled: 是否启用
        """
        super().__init__(hook_id="rate_limit_hook", priority=5, enabled=enabled)
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self._call_history: dict[str, list[float]] = {}

    async def process(
        self, event: HookEvent, hook_context: HookContext
    ) -> HookResult:
        """执行速率限制检查"""
        if event != HookEvent.PRE_TOOL_USE:
            return HookResult(should_proceed=True)

        tool_name = hook_context.tool_name
        current_time = time.time()

        # 初始化工具调用历史
        if tool_name not in self._call_history:
            self._call_history[tool_name] = []

        # 清理过期记录
        cutoff_time = current_time - self.window_seconds
        self._call_history[tool_name] = [
            t for t in self._call_history[tool_name] if t > cutoff_time
        ]

        # 检查是否超过限制
        if len(self._call_history[tool_name]) >= self.max_calls:
            return HookResult(
                should_proceed=False,
                error_message=(
                    f"速率限制: {tool_name} 超过限制 "
                    f"({self.max_calls}次/{self.window_seconds}秒)"
                ),
            )

        # 记录本次调用
        self._call_history[tool_name].append(current_time)

        return HookResult(should_proceed=True)

    def reset(self, tool_name: str | None = None) -> None:
        """
        重置速率限制计数

        Args:
            tool_name: 工具名称（None则重置所有）
        """
        if tool_name:
            self._call_history.pop(tool_name, None)
        else:
            self._call_history.clear()


# ==================== 便捷函数 ====================


def create_default_hooks() -> list[BaseHook]:
    """
    创建默认Hook集合

    Returns:
        默认Hook列表
    """
    return [
        ValidationHook(),
        RateLimitHook(max_calls=100, window_seconds=60),
        MetricsHook(),
        LoggingHook(),
    ]


def register_default_hooks(registry: HookRegistry) -> None:
    """
    注册默认Hook到注册表

    Args:
        registry: Hook注册表
    """
    hooks = create_default_hooks()

    for hook in hooks:
        # 注册到所有相关事件
        events = [
            HookEvent.PRE_TOOL_USE,
            HookEvent.POST_TOOL_USE,
            HookEvent.TOOL_FAILURE,
        ]
        registry.register(hook, events)

    logger.info(f"✅ 已注册 {len(hooks)} 个默认Hook")
