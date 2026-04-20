#!/usr/bin/env python3
"""
Skills系统Hook集成测试

测试Hook系统与Skills系统的集成。

Author: Athena平台团队
创建时间: 2026-04-20
"""
from __future__ import annotations

import asyncio
import pytest

from core.hooks.base import HookContext, HookFunction, HookRegistry, HookType
from core.hooks.enhanced import HookLifecycleManager
from core.hooks.integrations import (
    SkillHookIntegration,
    SkillExecutorWithHooks,
    create_skill_hook_integration,
    wrap_skill_with_hooks,
)
from core.skills.base import Skill, SkillMetadata, SkillResult


class MockSkill(Skill):
    """模拟技能"""

    def __init__(self):
        metadata = SkillMetadata(
            name="test_skill",
            display_name="测试技能",
            description="用于测试的模拟技能",
            version="1.0.0",
        )
        super().__init__(metadata)

        self.execute_count = 0
        self.last_params = {}

    async def execute(self, **kwargs) -> SkillResult:
        """执行技能"""
        self.execute_count += 1
        self.last_params = kwargs

        return SkillResult(
            success=True,
            data={"result": f"executed {self.execute_count} times"},
            execution_time=0.01,
        )


class TestSkillHookIntegration:
    """测试Skills Hook集成"""

    @pytest.fixture
    def integration(self):
        """创建Hook集成"""
        return create_skill_hook_integration()

    @pytest.fixture
    def skill(self):
        """创建模拟技能"""
        return MockSkill()

    @pytest.mark.asyncio
    async def test_before_skill_load(self, integration):
        """测试技能加载前Hook"""

        # 注册测试Hook
        executed = []

        async def test_hook(context: HookContext):
            executed.append("before_load")
            return "ok"

        integration.registry.register_function(
            "test_hook", HookType.PRE_TASK_START, test_hook
        )

        # 触发Hook
        result = await integration.before_skill_load("/path/to/skill")

        assert result.success is True
        assert len(executed) == 1

    @pytest.mark.asyncio
    async def test_after_skill_load(self, integration, skill):
        """测试技能加载后Hook"""

        executed = []

        async def test_hook(context: HookContext):
            executed.append("after_load")
            return "ok"

        integration.registry.register_function(
            "test_hook", HookType.POST_TASK_COMPLETE, test_hook
        )

        # 触发Hook
        result = await integration.after_skill_load(skill, success=True)

        assert result.success is True
        assert len(executed) == 1

    @pytest.mark.asyncio
    async def test_before_skill_execute(self, integration, skill):
        """测试技能执行前Hook"""

        executed = []

        async def test_hook(context: HookContext):
            executed.append("before_execute")
            return "ok"

        integration.registry.register_function(
            "test_hook", HookType.PRE_TOOL_USE, test_hook
        )

        # 触发Hook
        result = await integration.before_skill_execute(skill, {"param1": "value1"})

        assert result.success is True
        assert len(executed) == 1

    @pytest.mark.asyncio
    async def test_after_skill_execute(self, integration, skill):
        """测试技能执行后Hook"""

        executed = []

        async def test_hook(context: HookContext):
            executed.append("after_execute")
            return "ok"

        integration.registry.register_function(
            "test_hook", HookType.POST_TOOL_USE, test_hook
        )

        # 创建模拟结果
        skill_result = SkillResult(
            success=True,
            data={"result": "ok"},
            execution_time=0.1,
        )

        # 触发Hook
        result = await integration.after_skill_execute(skill, skill_result, 0.1)

        assert result.success is True
        assert len(executed) == 1

    @pytest.mark.asyncio
    async def test_on_skill_error(self, integration, skill):
        """测试技能错误Hook"""

        executed = []

        async def test_hook(context: HookContext):
            executed.append("error")
            return "ok"

        integration.registry.register_function("test_hook", HookType.ON_ERROR, test_hook)

        # 触发Hook
        result = await integration.on_skill_error(
            skill, ValueError("Test error"), {"context": "data"}
        )

        assert result.success is False
        assert result.error == "Test error"
        assert len(executed) == 1


class TestSkillExecutorWithHooks:
    """测试带Hook的技能执行器"""

    @pytest.fixture
    def integration(self):
        """创建Hook集成"""
        return create_skill_hook_integration()

    @pytest.fixture
    def skill(self):
        """创建模拟技能"""
        return MockSkill()

    @pytest.mark.asyncio
    async def test_execute_with_hooks(self, integration, skill):
        """测试带Hook的技能执行"""

        executed = []

        # 注册Hook
        async def before_hook(context: HookContext):
            executed.append("before")
            return "ok"

        async def after_hook(context: HookContext):
            executed.append("after")
            return "ok"

        integration.registry.register_function("before", HookType.PRE_TOOL_USE, before_hook)
        integration.registry.register_function("after", HookType.POST_TOOL_USE, after_hook)

        # 创建执行器
        executor = wrap_skill_with_hooks(skill, integration)

        # 执行技能
        result = await executor.execute(param1="value1")

        assert result.success is True
        assert skill.execute_count == 1
        assert skill.last_params == {"param1": "value1"}
        assert "before" in executed
        assert "after" in executed

    @pytest.mark.asyncio
    async def test_execute_with_error_hook(self, integration):
        """测试执行错误时的Hook"""

        class FailingSkill(Skill):
            def __init__(self):
                metadata = SkillMetadata(
                    name="failing_skill",
                    display_name="失败技能",
                    description="用于测试错误的技能",
                )
                super().__init__(metadata)

            async def execute(self, **kwargs):
                raise ValueError("Skill execution failed")

        executed = []

        # 注册错误Hook
        async def error_hook(context: HookContext):
            executed.append("error")
            return "ok"

        integration.registry.register_function("error", HookType.ON_ERROR, error_hook)

        # 创建执行器
        failing_skill = FailingSkill()
        executor = wrap_skill_with_hooks(failing_skill, integration)

        # 执行技能（应该抛出异常）
        with pytest.raises(ValueError, match="Skill execution failed"):
            await executor.execute()

        # 验证错误Hook被触发
        assert "error" in executed


class TestSkillHookLifecycle:
    """测试Skills Hook生命周期管理"""

    @pytest.mark.asyncio
    async def test_hook_lifecycle_with_skills(self):
        """测试Hook生命周期与Skills的集成"""

        # 创建带生命周期的集成
        integration = create_skill_hook_integration(enable_lifecycle=True)

        # 注册Hook
        async def test_hook(context: HookContext):
            return "ok"

        hook = HookFunction(
            name="skill_hook",
            hook_type=HookType.PRE_TOOL_USE,
            func=test_hook,
        )

        await integration.lifecycle.register(hook)

        # 验证状态
        assert integration.lifecycle.get_state("skill_hook") is not None

        # 停用Hook
        await integration.lifecycle.deactivate("skill_hook")

        # 验证状态
        from core.hooks.enhanced.types import HookState

        assert integration.lifecycle.get_state("skill_hook") == HookState.INACTIVE


__all__ = [
    "TestSkillHookIntegration",
    "TestSkillExecutorWithHooks",
    "TestSkillHookLifecycle",
]
