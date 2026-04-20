#!/usr/bin/env python3
"""
技能-工具映射器

管理技能与工具之间的映射关系。

作者: Athena平台团队
创建时间: 2026-04-21
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

from .registry import SkillRegistry
from .types import SkillDefinition

logger = logging.getLogger(__name__)


class SkillToolMapper:
    """技能-工具映射器

    维护技能与工具之间的双向映射关系。
    """

    def __init__(self, registry: SkillRegistry):
        """初始化映射器

        Args:
            registry: 技能注册表
        """
        self.registry = registry
        self._tool_to_skills_cache: Optional[Dict[str, List[str]]] = None
        logger.info("🔗 技能-工具映射器已初始化")

    def map_tools_to_skills(self) -> Dict[str, List[str]]:
        """映射工具到技能

        Returns:
            dict: {tool_id: [skill_id1, skill_id2, ...]}
        """
        if self._tool_to_skills_cache is None:
            self._tool_to_skills_cache = {}
            self._build_mapping()
        return self._tool_to_skills_cache

    def get_tools_for_skill(self, skill_id: str) -> List[str]:
        """获取技能所需的工具

        Args:
            skill_id: 技能ID

        Returns:
            list[str]: 工具ID列表
        """
        skill = self.registry.get_skill(skill_id)
        if skill is None:
            return []
        return skill.tools

    def get_skills_for_tool(self, tool_id: str) -> List[SkillDefinition]:
        """获取使用某工具的所有技能

        Args:
            tool_id: 工具ID

        Returns:
            list[SkillDefinition]: 技能列表
        """
        # 提取基础工具ID（去除版本后缀）
        base_tool_id = self._extract_base_tool_id(tool_id)

        # 查找使用该工具的技能
        skills = []
        for skill in self.registry.list_skills():
            for tool in skill.tools:
                skill_tool_id = self._extract_base_tool_id(tool)
                if skill_tool_id == base_tool_id:
                    skills.append(skill)
                    break

        return skills

    def detect_tool_conflicts(self) -> List[Dict[str, str]]:
        """检测工具冲突

        检测不同技能是否使用同一工具的不同版本。

        Returns:
            list[dict]: 冲突列表 [{tool: str, skills: [skill_id1, skill_id2], versions: [v1, v2]}]
        """
        conflicts = []
        mapping = self.map_tools_to_skills()

        for tool_id, skill_ids in mapping.items():
            # 收集所有版本
            versions = {}
            for skill_id in skill_ids:
                skill = self.registry.get_skill(skill_id)
                if skill:
                    for tool in skill.tools:
                        base_id = self._extract_base_tool_id(tool)
                        if base_id == tool_id:
                            version = self._extract_tool_version(tool)
                            if skill_id not in versions:
                                versions[skill_id] = version

            # 检查是否有版本冲突
            unique_versions = set(versions.values())
            if len(unique_versions) > 1:
                conflicts.append({
                    "tool": tool_id,
                    "skills": skill_ids,
                    "versions": list(unique_versions),
                })

        return conflicts

    def detect_tool_dependencies(self) -> Dict[str, List[str]]:
        """检测工具依赖

        检测技能之间的工具依赖关系。
        如果技能A使用了技能B的工具，则认为A依赖B。

        Returns:
            dict: {skill_id: [dependent_skill_id1, dependent_skill_id2, ...]}
        """
        dependencies = {}

        # 获取所有技能的工具集合
        skill_tools = {}
        for skill in self.registry.list_skills():
            skill_tools[skill.id] = set(self._extract_base_tool_id(t) for t in skill.tools)

        # 检测依赖关系
        for skill_id, tools in skill_tools.items():
            deps = []
            for other_skill_id, other_tools in skill_tools.items():
                if skill_id == other_skill_id:
                    continue
                # 如果当前技能使用了其他技能的工具（有交集），则存在依赖
                if tools & other_tools:  # 集合交集
                    deps.append(other_skill_id)

            if deps:
                dependencies[skill_id] = deps

        return dependencies

    def get_tool_usage_stats(self) -> Dict[str, Dict[str, any]]:
        """获取工具使用统计

        Returns:
            dict: {tool_id: {count: int, skill_ids: [skill_id1, ...]}}
        """
        mapping = self.map_tools_to_skills()
        stats = {}

        for tool_id, skill_ids in mapping.items():
            stats[tool_id] = {
                "count": len(skill_ids),
                "skill_ids": skill_ids,
            }

        return stats

    def find_unused_tools(self, all_tools: List[str]) -> List[str]:
        """查找未使用的工具

        Args:
            all_tools: 所有可用工具ID列表

        Returns:
            list[str]: 未使用的工具ID列表
        """
        # 获取所有被使用的工具
        used_tools = set()
        for skill in self.registry.list_skills():
            for tool in skill.tools:
                base_tool = self._extract_base_tool_id(tool)
                used_tools.add(base_tool)

        # 找出未使用的工具
        unused = []
        for tool in all_tools:
            base_tool = self._extract_base_tool_id(tool)
            if base_tool not in used_tools:
                unused.append(tool)

        return unused

    def invalidate_cache(self) -> None:
        """清除缓存"""
        self._tool_to_skills_cache = None
        logger.debug("🗑️ 工具映射缓存已清除")

    def _build_mapping(self) -> None:
        """构建工具到技能的映射"""
        self._tool_to_skills_cache = {}

        for skill in self.registry.list_skills():
            for tool in skill.tools:
                # 提取基础工具ID（去除版本）
                base_tool_id = self._extract_base_tool_id(tool)

                if base_tool_id not in self._tool_to_skills_cache:
                    self._tool_to_skills_cache[base_tool_id] = []

                if skill.id not in self._tool_to_skills_cache[base_tool_id]:
                    self._tool_to_skills_cache[base_tool_id].append(skill.id)

    def _extract_base_tool_id(self, tool_id: str) -> str:
        """提取基础工具ID（去除版本后缀）

        Args:
            tool_id: 工具ID（可能包含版本，如 tool1@v1）

        Returns:
            str: 基础工具ID
        """
        if "@" in tool_id:
            return tool_id.split("@")[0]
        return tool_id

    def _extract_tool_version(self, tool_id: str) -> str:
        """提取工具版本

        Args:
            tool_id: 工具ID（可能包含版本，如 tool1@v1）

        Returns:
            str: 版本号，无版本返回"default"
        """
        if "@" in tool_id:
            return tool_id.split("@")[1]
        return "default"


__all__ = [
    "SkillToolMapper",
]
