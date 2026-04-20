#!/usr/bin/env python3
"""
Skills系统Hook集成

将增强的Hook系统集成到Skills系统。

Author: Athena平台团队
创建时间: 2026-04-20
版本: 2.0.0
"""
from __future__ import annotations

import logging
from typing import Any

from core.hooks.base import HookContext, HookRegistry, HookType
from core.hooks.enhanced import HookLifecycleManager, HookResult
from core.skills.base import Skill, SkillMetadata, SkillResult

logger = logging.getLogger(__name__)


# 扩展HookType以支持Skills系统
class SkillHookType:
    """Skills系统专用Hook类型"""

    PRE_SKILL_LOAD = "pre_skill_load"
    POST_SKILL_LOAD = "post_skill_load"
    PRE_SKILL_EXECUTE = "pre_skill_execute"
    POST_SKILL_EXECUTE = "post_skill_execute"
    SKILL_ERROR = "skill_error"
    SKILL_VALIDATE = "skill_validate"


class SkillHookIntegration:
    """Skills系统Hook集成

    为Skills系统提供Hook支持。
    """

    def __init__(
        self,
        registry: HookRegistry | None = None,
        enable_lifecycle: bool = True,
    ):
        """初始化集成

        Args:
            registry: Hook注册表
            enable_lifecycle: 是否启用生命周期管理
        """
        self._registry = registry or HookRegistry()
        self._lifecycle = HookLifecycleManager(self._registry) if enable_lifecycle else None

        logger.info("🔗 Skills系统Hook集成已初始化")

    @property
    def registry(self) -> HookRegistry:
        """获取Hook注册表"""
        return self._registry

    @property
    def lifecycle(self) -> HookLifecycleManager | None:
        """获取生命周期管理器"""
        return self._lifecycle

    async def before_skill_load(
        self, skill_path: str, metadata: dict[str, Any] | None = None
    ) -> HookResult:
        """技能加载前Hook

        Args:
            skill_path: 技能路径
            metadata: 元数据

        Returns:
            HookResult: Hook执行结果
        """
        context = HookContext(
            hook_type=HookType.PRE_TASK_START,  # 使用现有类型
            data={
                "skill_path": skill_path,
                "metadata": metadata or {},
            },
        )

        results = await self._registry.trigger(HookType.PRE_TASK_START, context)

        return HookResult(
            success=True,
            data=results,
            execution_time=0.0,
        )

    async def after_skill_load(
        self, skill: Skill, success: bool = True, error: str | None = None
    ) -> HookResult:
        """技能加载后Hook

        Args:
            skill: 技能实例
            success: 是否成功
            error: 错误信息

        Returns:
            HookResult: Hook执行结果
        """
        context = HookContext(
            hook_type=HookType.POST_TASK_COMPLETE,
            data={
                "skill": skill,
                "skill_name": skill.metadata.name if skill else None,
                "success": success,
                "error": error,
            },
        )

        results = await self._registry.trigger(HookType.POST_TASK_COMPLETE, context)

        return HookResult(
            success=success,
            data=results,
            error=error,
        )

    async def before_skill_execute(
        self, skill: Skill, params: dict[str, Any]
    ) -> HookResult:
        """技能执行前Hook

        Args:
            skill: 技能实例
            params: 执行参数

        Returns:
            HookResult: Hook执行结果
        """
        context = HookContext(
            hook_type=HookType.PRE_TOOL_USE,  # 复用工具类型
            data={
                "skill": skill,
                "skill_name": skill.metadata.name,
                "params": params,
            },
        )

        results = await self._registry.trigger(HookType.PRE_TOOL_USE, context)

        return HookResult(
            success=True,
            data=results,
        )

    async def after_skill_execute(
        self, skill: Skill, result: SkillResult, execution_time: float
    ) -> HookResult:
        """技能执行后Hook

        Args:
            skill: 技能实例
            result: 执行结果
            execution_time: 执行时间

        Returns:
            HookResult: Hook执行结果
        """
        context = HookContext(
            hook_type=HookType.POST_TOOL_USE,
            data={
                "skill": skill,
                "skill_name": skill.metadata.name,
                "result": result.to_dict() if result else None,
                "execution_time": execution_time,
            },
        )

        results = await self._registry.trigger(HookType.POST_TOOL_USE, context)

        return HookResult(
            success=result.success if result else True,
            data=results,
            execution_time=execution_time,
        )

    async def on_skill_error(
        self, skill: Skill | None, error: Exception, context: dict[str, Any]
    ) -> HookResult:
        """技能错误Hook

        Args:
            skill: 技能实例
            error: 异常
            context: 上下文信息

        Returns:
            HookResult: Hook执行结果
        """
        hook_context = HookContext(
            hook_type=HookType.ON_ERROR,
            data={
                "skill": skill,
                "skill_name": skill.metadata.name if skill else None,
                "error": str(error),
                "error_type": type(error).__name__,
                "context": context,
            },
        )

        results = await self._registry.trigger(HookType.ON_ERROR, hook_context)

        return HookResult(
            success=False,
            data=results,
            error=str(error),
        )


class SkillExecutorWithHooks:
    """带Hook的技能执行器

    包装技能执行，自动触发Hook。
    """

    def __init__(self, skill: Skill, hook_integration: SkillHookIntegration):
        """初始化执行器

        Args:
            skill: 技能实例
            hook_integration: Hook集成
        """
        self._skill = skill
        self._hooks = hook_integration

    async def execute(self, **params) -> SkillResult:
        """执行技能（带Hook）

        Args:
            **params: 技能参数

        Returns:
            SkillResult: 执行结果
        """
        import time

        # 执行前Hook
        await self._hooks.before_skill_execute(self._skill, params)

        # 执行技能
        start_time = time.time()
        try:
            result = await self._skill.execute(**params)
            execution_time = time.time() - start_time

            # 执行后Hook
            await self._hooks.after_skill_execute(self._skill, result, execution_time)

            return result

        except Exception as e:
            execution_time = time.time() - start_time

            # 错误Hook
            await self._hooks.on_skill_error(
                self._skill, e, {"params": params, "execution_time": execution_time}
            )

            # 重新抛出异常
            raise


# 便捷函数


def create_skill_hook_integration(
    registry: HookRegistry | None = None,
    enable_lifecycle: bool = True,
) -> SkillHookIntegration:
    """创建Skills系统Hook集成

    Args:
        registry: Hook注册表
        enable_lifecycle: 是否启用生命周期管理

    Returns:
        SkillHookIntegration: Hook集成实例
    """
    return SkillHookIntegration(
        registry=registry,
        enable_lifecycle=enable_lifecycle,
    )


def wrap_skill_with_hooks(
    skill: Skill, hook_integration: SkillHookIntegration
) -> SkillExecutorWithHooks:
    """包装技能以支持Hook

    Args:
        skill: 技能实例
        hook_integration: Hook集成

    Returns:
        SkillExecutorWithHooks: 带Hook的执行器
    """
    return SkillExecutorWithHooks(skill, hook_integration)


__all__ = [
    "SkillHookType",
    "SkillHookIntegration",
    "SkillExecutorWithHooks",
    "create_skill_hook_integration",
    "wrap_skill_with_hooks",
]
