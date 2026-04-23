#!/usr/bin/env python3
"""
Hook链处理器

实现Hook链式执行和中间件模式。

Author: Athena平台团队
创建时间: 2026-04-20
版本: 2.0.0
"""
from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any

from ..base import HookContext, HookFunction, HookRegistry, HookType
from .types import HookResult, HookStatus

logger = logging.getLogger(__name__)


class HookMiddleware(ABC):
    """Hook中间件基类"""

    @abstractmethod
    async def before_hook(self, context: HookContext) -> HookContext:
        """Hook执行前处理

        Args:
            context: Hook上下文

        Returns:
            HookContext: 处理后的上下文
        """
        pass

    @abstractmethod
    async def after_hook(
        self, context: HookContext, result: HookResult
    ) -> HookResult:
        """Hook执行后处理

        Args:
            context: Hook上下文
            result: Hook执行结果

        Returns:
            HookResult: 处理后的结果
        """
        pass


class HookChain:
    """Hook链

    管理一组Hook的链式执行。
    """

    def __init__(
        self,
        hook_type: HookType,
        stop_on_error: bool = False,
        stop_on_failure: bool = False,
    ):
        """初始化Hook链

        Args:
            hook_type: Hook类型
            stop_on_error: 遇到错误时是否停止
            stop_on_failure: 遇到失败时是否停止
        """
        self.hook_type = hook_type
        self.hooks: list[HookFunction] = []
        self.middlewares: list[HookMiddleware] = []
        self.stop_on_error = stop_on_error
        self.stop_on_failure = stop_on_failure

    def add_hook(self, hook: HookFunction) -> None:
        """添加Hook到链

        Args:
            hook: Hook函数
        """
        self.hooks.append(hook)
        # 按优先级排序
        self.hooks.sort(key=lambda h: h.priority, reverse=True)

    def add_middleware(self, middleware: HookMiddleware) -> None:
        """添加中间件

        Args:
            middleware: 中间件
        """
        self.middlewares.append(middleware)

    async def execute(self, context: HookContext) -> HookResult:
        """执行Hook链

        Args:
            context: Hook上下文

        Returns:
            HookResult: 执行结果
        """
        results = []
        modified_context = False

        for hook in self.hooks:
            if not hook.enabled:
                continue

            try:
                # 执行中间件前置处理
                for middleware in self.middlewares:
                    context = await middleware.before_hook(context)

                # 执行Hook
                start_time = asyncio.get_event_loop().time()
                hook_result = await hook.execute(context)
                execution_time = asyncio.get_event_loop().time() - start_time

                # 构建结果
                result = HookResult(
                    success=True,
                    data=hook_result,
                    execution_time=execution_time,
                    status=HookStatus.COMPLETED,
                )

                # 检查上下文是否被修改
                if len(context.data) > 0:
                    result.modified_context = True

                # 执行中间件后置处理
                for middleware in self.middlewares:
                    result = await middleware.after_hook(context, result)

                results.append(result)
                modified_context = modified_context or result.modified_context

                # 检查是否需要停止
                if result.stopped:
                    logger.info(f"⏹️ Hook链被中断: {hook.name}")
                    break

            except Exception as e:
                logger.error(f"❌ Hook执行失败: {hook.name}, 错误: {e}")

                error_result = HookResult(
                    success=False,
                    error=str(e),
                    status=HookStatus.FAILED,
                )

                results.append(error_result)

                if self.stop_on_error:
                    error_result.stopped = True
                    break

        # 合并结果
        return self._merge_results(results, modified_context)

    def _merge_results(
        self, results: list[HookResult], modified_context: bool
    ) -> HookResult:
        """合并多个Hook的结果

        Args:
            results: Hook结果列表
            modified_context: 上下文是否被修改

        Returns:
            HookResult: 合并后的结果
        """
        if not results:
            return HookResult(success=True, status=HookStatus.COMPLETED)

        # 检查是否有失败
        failed = any(not r.success for r in results)

        # 检查是否被停止
        stopped = any(r.stopped for r in results)

        # 计算总时间
        total_time = sum(r.execution_time for r in results)

        # 收集所有数据
        data = [r.data for r in results if r.data is not None]

        return HookResult(
            success=not failed,
            data=data if len(data) > 1 else (data[0] if data else None),
            execution_time=total_time,
            modified_context=modified_context,
            stopped=stopped,
            status=HookStatus.COMPLETED if not failed else HookStatus.FAILED,
        )


class HookChainProcessor:
    """Hook链处理器

    管理所有Hook链的创建和执行。
    """

    def __init__(self, registry: HookRegistry | None = None):
        """初始化Hook链处理器

        Args:
            registry: Hook注册表
        """
        self._registry = registry or HookRegistry()
        self._chains: dict[HookType, HookChain] = {}
        self._middlewares: list[HookMiddleware] = []
        self._lock = asyncio.Lock()

        logger.info("🔗 HookChainProcessor初始化完成")

    def add_middleware(self, middleware: HookMiddleware) -> None:
        """添加全局中间件

        Args:
            middleware: 中间件
        """
        self._middlewares.append(middleware)
        logger.info(f"✅ 中间件已添加: {middleware.__class__.__name__}")

    def create_chain(
        self,
        hook_type: HookType,
        stop_on_error: bool = False,
        stop_on_failure: bool = False,
    ) -> HookChain:
        """创建Hook链

        Args:
            hook_type: Hook类型
            stop_on_error: 遇到错误时是否停止
            stop_on_failure: 遇到失败时是否停止

        Returns:
            HookChain: Hook链
        """
        chain = HookChain(
            hook_type=hook_type,
            stop_on_error=stop_on_error,
            stop_on_failure=stop_on_failure,
        )

        # 添加所有该类型的Hook
        hooks = self._registry.get_hooks(hook_type)
        for hook in hooks:
            chain.add_hook(hook)

        # 添加全局中间件
        for middleware in self._middlewares:
            chain.add_middleware(middleware)

        self._chains[hook_type] = chain
        return chain

    async def process(
        self,
        hook_type: HookType,
        context: HookContext,
        parallel: bool = False,
    ) -> HookResult:
        """处理Hook链

        Args:
            hook_type: Hook类型
            context: Hook上下文
            parallel: 是否并行执行

        Returns:
            HookResult: 执行结果
        """
        async with self._lock:
            # 获取或创建链
            if hook_type not in self._chains:
                self.create_chain(hook_type)

            chain = self._chains[hook_type]

            # 执行链
            if parallel:
                return await self._execute_parallel(chain, context)
            else:
                return await chain.execute(context)

    async def _execute_parallel(
        self, chain: HookChain, context: HookContext
    ) -> HookResult:
        """并行执行Hook链

        Args:
            chain: Hook链
            context: Hook上下文

        Returns:
            HookResult: 执行结果
        """
        tasks = []
        start_times = {}

        # 创建所有任务
        for hook in chain.hooks:
            if not hook.enabled:
                continue

            async def execute_hook(h: HookFunction) -> tuple[HookFunction, Any]:
                start = asyncio.get_event_loop().time()
                result = await h.execute(context)
                return h, (result, asyncio.get_event_loop().time() - start)

            tasks.append(execute_hook(hook))

        # 并行执行
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        hook_results = []
        total_time = 0.0

        for item in results:
            if isinstance(item, Exception):
                logger.error(f"❌ Hook执行异常: {item}")
                continue

            hook, (result, exec_time) = item
            total_time = max(total_time, exec_time)

            hook_results.append(
                HookResult(
                    success=True,
                    data=result,
                    execution_time=exec_time,
                )
            )

        return HookResult(
            success=all(r.success for r in hook_results) if hook_results else True,
            data=[r.data for r in hook_results],
            execution_time=total_time,
        )

    def get_chain(self, hook_type: HookType) -> HookChain | None:
        """获取Hook链

        Args:
            hook_type: Hook类型

        Returns:
            HookChain | None: Hook链
        """
        return self._chains.get(hook_type)

    def clear_chains(self) -> None:
        """清空所有链"""
        self._chains.clear()
        logger.info("🗑️ 所有Hook链已清空")


__all__ = [
    "HookMiddleware",
    "HookChain",
    "HookChainProcessor",
]
