from __future__ import annotations
"""
技能执行器

负责执行技能并管理执行上下文。
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from .base import SkillException, SkillNotFoundException, SkillResult
from .registry import SkillRegistry

logger = logging.getLogger(__name__)


@dataclass
class ExecutionContext:
    """技能执行上下文

    存储执行过程中的共享数据。
    """
    skill_name: str
    parameters: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    session_id: Optional[str] = None

    def get(self, key: str, default: Any = None) -> Any:
        """获取上下文数据"""
        return self.metadata.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """设置上下文数据"""
        self.metadata[key] = value


class SkillExecutor:
    """技能执行器

    负责执行技能并处理执行结果。
    """

    def __init__(self, registry: SkillRegistry | None = None):
        self._registry = registry
        self._execution_history: list[dict[str, Any]] = []
        self._max_history = 1000

    @property
    def registry(self) -> SkillRegistry | None:
        """获取技能注册中心"""
        return self._registry

    def set_registry(self, registry: SkillRegistry) -> None:
        """设置技能注册中心"""
        self._registry = registry

    async def execute(
        self,
        skill_name: str,
        **parameters
    ) -> SkillResult:
        """执行技能

        Args:
            skill_name: 技能名称
            **parameters: 技能参数

        Returns:
            SkillResult: 执行结果

        Raises:
            SkillNotFoundException: 技能不存在
            SkillException: 执行失败
        """
        if self._registry is None:
            raise SkillException("Skill registry not configured")

        # 获取技能
        skill = self._registry.get(skill_name)
        if skill is None:
            raise SkillNotFoundException(f"Skill '{skill_name}' not found")

        # 检查技能是否启用
        if not skill.metadata.enabled:
            return SkillResult(
                success=False,
                error=f"Skill '{skill_name}' is disabled",
            )

        # 创建执行上下文
        ctx = ExecutionContext(
            skill_name=skill_name,
            parameters=parameters,
        )

        # 执行技能
        start_time = time.time()
        try:
            result = await skill.execute(**parameters)

            # 记录执行历史
            self._record_execution(ctx, result)

            return result

        except Exception as e:
            logger.error(f"Error executing skill '{skill_name}': {e}", exc_info=True)

            result = SkillResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time,
            )

            self._record_execution(ctx, result)
            return result

    async def execute_batch(
        self,
        executions: list[dict[str, Any]]
    ) -> list[SkillResult]:
        """批量执行技能

        Args:
            executions: 执行列表，每个元素包含 skill_name 和 parameters

        Returns:
            list[SkillResult]: 执行结果列表
        """
        tasks = []
        for exec_item in executions:
            skill_name = exec_item.get("skill_name")
            parameters = exec_item.get("parameters", {})
            if skill_name:
                tasks.append(self.execute(skill_name, **parameters))

        return await asyncio.gather(*tasks, return_exceptions=True)

    async def execute_chain(
        self,
        chain: list[dict[str, Any]],
        pass_result: bool = True
    ) -> list[SkillResult]:
        """链式执行技能

        前一个技能的输出作为后一个技能的输入。

        Args:
            chain: 技能链，每个元素包含 skill_name 和 parameters
            pass_result: 是否将前一个技能的结果传递给下一个

        Returns:
            list[SkillResult]: 所有技能的执行结果
        """
        results = []
        previous_result = None

        for item in chain:
            skill_name = item.get("skill_name")
            parameters = item.get("parameters", {}).copy()

            # 将前一个结果传递给当前技能
            if pass_result and previous_result and previous_result.success:
                parameters["previous_result"] = previous_result.data

            result = await self.execute(skill_name, **parameters)
            results.append(result)
            previous_result = result

            # 如果失败且要求严格模式，停止执行
            if not result.success and item.get("strict", False):
                logger.warning(f"Chain stopped at '{skill_name}' due to failure")
                break

        return results

    def _record_execution(
        self,
        ctx: ExecutionContext,
        result: SkillResult
    ) -> None:
        """记录执行历史

        Args:
            ctx: 执行上下文
            result: 执行结果
        """
        record = {
            "skill_name": ctx.skill_name,
            "parameters": ctx.parameters,
            "success": result.success,
            "execution_time": result.execution_time,
            "error": result.error,
            "timestamp": time.time(),
        }

        self._execution_history.append(record)

        # 限制历史记录大小
        if len(self._execution_history) > self._max_history:
            self._execution_history = self._execution_history[-self._max_history:]

    def get_execution_history(
        self,
        skill_name: Optional[str] = None,
        limit: int = 100
    ) -> list[dict[str, Any]]:
        """获取执行历史

        Args:
            skill_name: 筛选特定技能的历史
            limit: 返回记录数量限制

        Returns:
            list[dict[str, Any]]: 执行历史记录
        """
        history = self._execution_history

        if skill_name:
            history = [h for h in history if h["skill_name"] == skill_name]

        return history[-limit:]

    def get_statistics(self) -> dict[str, Any]:
        """获取执行统计

        Returns:
            dict[str, Any]: 统计信息
        """
        if not self._execution_history:
            return {
                "total_executions": 0,
                "success_rate": 0.0,
                "avg_execution_time": 0.0,
            }

        total = len(self._execution_history)
        successful = sum(1 for h in self._execution_history if h["success"])
        total_time = sum(h["execution_time"] for h in self._execution_history)

        return {
            "total_executions": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": successful / total if total > 0 else 0.0,
            "avg_execution_time": total_time / total if total > 0 else 0.0,
        }

    def clear_history(self) -> None:
        """清空执行历史"""
        self._execution_history.clear()


class SkillComposer:
    """技能组合器

    将多个技能组合成复杂的工作流。
    """

    def __init__(self, executor: SkillExecutor):
        self._executor = executor

    async def parallel(
        self,
        skill_names: list[str],
        parameters_list: Optional[list[dict[str, Any]] = None
    ) -> list[SkillResult]:
        """并行执行多个技能

        Args:
            skill_names: 技能名称列表
            parameters_list: 对应的参数列表

        Returns:
            list[SkillResult]: 执行结果列表
        """
        if parameters_list is None:
            parameters_list = [{}] * len(skill_names)

        executions = [
            {"skill_name": name, "parameters": params}
            for name, params in zip(skill_names, parameters_list, strict=False)
        ]

        return await self._executor.execute_batch(executions)

    async def conditional(
        self,
        condition: str,
        skill_if_true: str,
        skill_if_false: Optional[str] = None,
        **parameters
    ) -> SkillResult:
        """条件执行

        使用安全的表达式求值，避免代码注入风险。

        Args:
            condition: 条件表达式
            skill_if_true: 条件为真时执行的技能
            skill_if_false: 条件为假时执行的技能（可选）
            **parameters: 传递给技能的参数

        Returns:
            SkillResult: 执行结果

        Raises:
            ValueError: 条件表达式不安全或无效
        """
        # 使用安全的条件评估
        from core.utils import safe_eval

        try:
            result = safe_eval(condition, parameters)
        except ValueError as e:
            return SkillResult(
                success=True,
                data={"condition_result": None, "executed": False, "error": str(e)},
            )

        if result:
            return await self._executor.execute(skill_if_true, **parameters)
        elif skill_if_false:
            return await self._executor.execute(skill_if_false, **parameters)
        else:
            return SkillResult(
                success=True,
                data={"condition_result": result, "executed": False},
            )

    async def loop(
        self,
        skill_name: str,
        items: list[any],
        parameter_name: str = "item",
        **fixed_parameters
    ) -> list[SkillResult]:
        """循环执行技能

        对列表中的每个项目执行一次技能。

        Args:
            skill_name: 要执行的技能
            items: 项目列表
            parameter_name: 参数名称
            **fixed_parameters: 固定参数

        Returns:
            list[SkillResult]: 所有执行结果
        """
        executions = [
            {
                "skill_name": skill_name,
                "parameters": {**fixed_parameters, parameter_name: item}
            }
            for item in items
        ]

        return await self._executor.execute_batch(executions)
