from __future__ import annotations
from typing import Optional
"""
智能体技能集成

将技能系统集成到智能体中，允许智能体动态使用技能。
"""

import logging

from core.skills import (
    SkillExecutor,
    SkillManager,
    SkillRegistry,
    SkillResult,
)

logger = logging.getLogger(__name__)


class SkillMixin:
    """技能混入类

    为智能体添加技能使用能力。
    """

    def __init__(self, *args, skills_dir=None, **_kwargs  # noqa: ARG001):
        super().__init__(*args, **_kwargs  # noqa: ARG001)
        self._skill_manager: SkillManager | None = None
        self._skill_executor: SkillExecutor | None = None
        self._skills_dir = skills_dir

    async def setup_skills(self, skills_dir=None) -> None:
        """初始化技能系统

        Args:
            skills_dir: 技能目录路径，默认使用初始化时指定的目录
        """
        from pathlib import Path

        directory = Path(skills_dir or self._skills_dir or "skills")

        # 创建技能管理器和执行器
        registry = SkillRegistry(skills_dir=directory)
        self._skill_manager = SkillManager(registry=registry, skills_dir=directory)
        self._skill_executor = SkillExecutor(registry=registry)

        # 加载所有技能
        logger.info(f"Loading skills from {directory}...")
        count = await self._skill_manager.load_all()
        logger.info(f"Loaded {count} skills")

        # 输出可用技能
        available = self._skill_executor.registry.list_enabled()
        logger.info(f"Available skills: {', '.join(available)}")

    async def use_skill(
        self,
        skill_name: str,
        **parameters
    ) -> SkillResult:
        """使用技能

        Args:
            skill_name: 技能名称
            **parameters: 技能参数

        Returns:
            SkillResult: 执行结果
        """
        if self._skill_executor is None:
            await self.setup_skills()

        return await self._skill_executor.execute(skill_name, **parameters)

    async def use_skills_parallel(
        self,
        skill_names: list[str],
        parameters_list: list[dict] | None = None
    ) -> list[SkillResult]:
        """并行使用多个技能

        Args:
            skill_names: 技能名称列表
            parameters_list: 对应的参数列表

        Returns:
            List[SkillResult]: 所有执行结果
        """
        if self._skill_executor is None:
            await self.setup_skills()

        from core.skills import SkillComposer
        composer = SkillComposer(self._skill_executor)
        return await composer.parallel(skill_names, parameters_list)

    def list_available_skills(self) -> list[str]:
        """列出可用技能

        Returns:
            List[str]: 可用技能名称列表
        """
        if self._skill_executor is None:
            return []

        return self._skill_executor.registry.list_enabled()

    def get_skill_info(self, skill_name: str) -> dict | None:
        """获取技能信息

        Args:
            skill_name: 技能名称

        Returns:
            Optional[dict]: 技能元数据，不存在返回 None
        """
        if self._skill_executor is None:
            return None

        metadata = self._skill_executor.registry.get_metadata(skill_name)
        if metadata:
            return metadata.to_dict()
        return None

    async def shutdown_skills(self) -> None:
        """关闭技能系统"""
        # 清理资源
        if self._skill_executor:
            self._skill_executor.clear_history()
        logger.info("Skills system shutdown")


class SkillfulAgent(SkillMixin):
    """技能化智能体基类

    集成技能系统的智能体基类，可以方便地使用各种技能。
    """

    async def initialize(self, *args, **_kwargs  # noqa: ARG001):
        """初始化智能体"""
        await super().initialize(*args, **_kwargs  # noqa: ARG001)
        await self.setup_skills()

    async def process_with_skill(
        self,
        skill_name: str,
        user_input: str,
        **skill_parameters
    ) -> str:
        """使用技能处理用户输入

        Args:
            skill_name: 技能名称
            user_input: 用户输入
            **skill_parameters: 额外的技能参数

        Returns:
            str: 处理结果
        """
        # 执行技能
        result = await self.use_skill(skill_name, **skill_parameters)

        if result.success:
            # 格式化结果
            if isinstance(result.data, dict):
                return self._format_skill_result(result.data)
            return str(result.data)
        else:
            # 处理错误
            return f"技能执行失败: {result.error}"

    def _format_skill_result(self, data: dict) -> str:
        """格式化技能结果

        Args:
            data: 技能返回的数据

        Returns:
            str: 格式化后的结果字符串
        """
        # 简单的格式化逻辑
        if "message" in data:
            return data["message"]
        elif "result" in data:
            return str(data["result"])
        else:
            return str(data)
