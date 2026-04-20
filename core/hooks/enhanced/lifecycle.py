#!/usr/bin/env python3
"""
Hook生命周期管理器

管理Hook的完整生命周期：注册、激活、停用、卸载。

Author: Athena平台团队
创建时间: 2026-04-20
版本: 2.0.0
"""
from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Any

from ..base import HookFunction, HookRegistry, HookType
from .types import HookDependency, HookResult, HookState

logger = logging.getLogger(__name__)


class HookLifecycleManager:
    """Hook生命周期管理器

    管理Hook的注册、激活、停用、卸载等生命周期操作。
    """

    def __init__(self, registry: HookRegistry | None = None):
        """初始化生命周期管理器

        Args:
            registry: Hook注册表，默认使用全局注册表
        """
        self._registry = registry or HookRegistry()
        self._states: dict[str, HookState] = {}
        self._dependencies: dict[str, HookDependency] = {}
        self._lock = asyncio.Lock()

        logger.info("🔗 HookLifecycleManager初始化完成")

    @property
    def registry(self) -> HookRegistry:
        """获取Hook注册表"""
        return self._registry

    async def register(
        self,
        hook: HookFunction,
        dependencies: list[str] | None = None,
        auto_activate: bool = True,
    ) -> bool:
        """注册Hook

        Args:
            hook: Hook函数
            dependencies: 依赖的Hook ID列表
            auto_activate: 是否自动激活

        Returns:
            bool: 是否注册成功
        """
        async with self._lock:
            try:
                # 检查是否已注册
                if hook.name in self._states:
                    logger.warning(f"⚠️ Hook已存在: {hook.name}")
                    return False

                # 注册到注册表
                self._registry.register(hook)

                # 设置状态
                self._states[hook.name] = HookState.REGISTERED

                # 记录依赖
                if dependencies:
                    self._dependencies[hook.name] = HookDependency(
                        hook_id=hook.name,
                        depends_on=dependencies,
                        required=True,
                    )

                logger.info(f"✅ Hook已注册: {hook.name}")

                # 自动激活
                if auto_activate:
                    await self.activate(hook.name)

                return True

            except Exception as e:
                logger.error(f"❌ 注册Hook失败: {hook.name}, 错误: {e}")
                self._states[hook.name] = HookState.ERROR
                return False

    async def activate(self, hook_id: str) -> bool:
        """激活Hook

        Args:
            hook_id: Hook ID

        Returns:
            bool: 是否激活成功
        """
        async with self._lock:
            # 检查依赖
            if hook_id in self._dependencies:
                dep = self._dependencies[hook_id]
                if not await self._check_dependencies(dep):
                    logger.warning(f"⚠️ Hook依赖未满足: {hook_id}")
                    return False

            try:
                # 设置状态为激活中
                self._states[hook_id] = HookState.ACTIVATING

                # 启用Hook
                self._registry.enable_hook(hook_id)

                # 设置状态为活跃
                self._states[hook_id] = HookState.ACTIVE

                logger.info(f"🟢 Hook已激活: {hook_id}")
                return True

            except Exception as e:
                logger.error(f"❌ 激活Hook失败: {hook_id}, 错误: {e}")
                self._states[hook_id] = HookState.ERROR
                return False

    async def deactivate(self, hook_id: str) -> bool:
        """停用Hook

        Args:
            hook_id: Hook ID

        Returns:
            bool: 是否停用成功
        """
        async with self._lock:
            try:
                # 设置状态为停用中
                self._states[hook_id] = HookState.DEACTIVATING

                # 禁用Hook
                self._registry.disable_hook(hook_id)

                # 设置状态为未激活
                self._states[hook_id] = HookState.INACTIVE

                logger.info(f"⚪ Hook已停用: {hook_id}")
                return True

            except Exception as e:
                logger.error(f"❌ 停用Hook失败: {hook_id}, 错误: {e}")
                self._states[hook_id] = HookState.ERROR
                return False

    async def unregister(self, hook_id: str) -> bool:
        """卸载Hook

        Args:
            hook_id: Hook ID

        Returns:
            bool: 是否卸载成功
        """
        # 不在锁内调用deactivate，避免死锁
        try:
            # 先停用（如果已激活）
            current_state = self._states.get(hook_id)
            if current_state == HookState.ACTIVE:
                await self.deactivate(hook_id)

            async with self._lock:
                # 设置状态为卸载中
                self._states[hook_id] = HookState.UNREGISTERING

                # 从注册表移除
                self._registry.remove_hook(hook_id)

                # 清理状态和依赖
                self._states.pop(hook_id, None)
                self._dependencies.pop(hook_id, None)

            logger.info(f"🗑️ Hook已卸载: {hook_id}")
            return True

        except Exception as e:
            logger.error(f"❌ 卸载Hook失败: {hook_id}, 错误: {e}")
            async with self._lock:
                self._states[hook_id] = HookState.ERROR
            return False

    def get_state(self, hook_id: str) -> HookState | None:
        """获取Hook状态

        Args:
            hook_id: Hook ID

        Returns:
            HookState | None: Hook状态
        """
        return self._states.get(hook_id)

    def get_all_states(self) -> dict[str, HookState]:
        """获取所有Hook状态

        Returns:
            dict[str, HookState]: Hook ID到状态的映射
        """
        return self._states.copy()

    async def resolve_dependencies(self) -> list[str]:
        """解析Hook依赖关系

        按依赖顺序返回Hook ID列表。

        Returns:
            list[str]: 按依赖顺序排列的Hook ID列表
        """
        # 使用拓扑排序
        sorted_hooks: list[str] = []
        visited: set[str] = set()
        visiting: set[str] = set()

        def visit(hook_id: str) -> None:
            if hook_id in visited:
                return
            if hook_id in visiting:
                raise ValueError(f"检测到循环依赖: {hook_id}")

            visiting.add(hook_id)

            # 先访问依赖
            if hook_id in self._dependencies:
                for dep_id in self._dependencies[hook_id].depends_on:
                    visit(dep_id)

            visiting.remove(hook_id)
            visited.add(hook_id)
            sorted_hooks.append(hook_id)

        # 访问所有Hook
        for hook_id in self._states:
            visit(hook_id)

        return sorted_hooks

    async def _check_dependencies(self, dependency: HookDependency) -> bool:
        """检查依赖是否满足

        Args:
            dependency: Hook依赖关系

        Returns:
            bool: 依赖是否满足
        """
        for dep_id in dependency.depends_on:
            state = self._states.get(dep_id)
            if state != HookState.ACTIVE:
                if dependency.required:
                    return False
        return True

    async def activate_all(self) -> dict[str, bool]:
        """激活所有Hook

        Returns:
            dict[str, bool]: Hook ID到激活结果的映射
        """
        results = {}

        # 按依赖顺序激活
        for hook_id in await self.resolve_dependencies():
            results[hook_id] = await self.activate(hook_id)

        return results

    async def deactivate_all(self) -> dict[str, bool]:
        """停用所有Hook

        Returns:
            dict[str, bool]: Hook ID到停用结果的映射
        """
        results = {}

        # 按反向依赖顺序停用
        for hook_id in reversed(await self.resolve_dependencies()):
            results[hook_id] = await self.deactivate(hook_id)

        return results

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息

        Returns:
            dict: 统计信息
        """
        state_counts: dict[HookState, int] = defaultdict(int)
        for state in self._states.values():
            state_counts[state] += 1

        return {
            "total_hooks": len(self._states),
            "state_counts": {state.value: count for state, count in state_counts.items()},
            "dependencies": len(self._dependencies),
        }


__all__ = [
    "HookLifecycleManager",
]
