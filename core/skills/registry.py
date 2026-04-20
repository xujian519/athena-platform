#!/usr/bin/env python3
"""
技能注册表

管理所有技能的注册和查询。

作者: Athena平台团队
创建时间: 2026-04-21
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

from .types import SkillDefinition, SkillCategory

logger = logging.getLogger(__name__)


class SkillRegistry:
    """技能注册表
    
    存储和管理所有技能。
    """

    def __init__(self):
        """初始化注册表"""
        self._skills: Dict[str, SkillDefinition] = {}
        logger.info("📚 技能注册表已初始化")

    def register(self, skill: SkillDefinition) -> None:
        """注册技能
        
        Args:
            skill: 技能定义
            
        Raises:
            ValueError: 技能ID已存在
        """
        if skill.id in self._skills:
            raise ValueError(f"Skill {skill.id} already registered")
        
        self._skills[skill.id] = skill
        logger.info(f"✅ 技能已注册: {skill.id} - {skill.name}")

    def get_skill(self, skill_id: str) -> Optional[SkillDefinition]:
        """获取技能
        
        Args:
            skill_id: 技能ID
            
        Returns:
            SkillDefinition | None: 技能定义，不存在返回None
        """
        return self._skills.get(skill_id)

    def unregister(self, skill_id: str) -> bool:
        """注销技能
        
        Args:
            skill_id: 技能ID
            
        Returns:
            bool: 是否成功注销
        """
        if skill_id in self._skills:
            del self._skills[skill_id]
            logger.info(f"🗑️ 技能已注销: {skill_id}")
            return True
        return False

    def list_skills(
        self,
        category: Optional[SkillCategory] = None,
        enabled_only: bool = False,
    ) -> List[SkillDefinition]:
        """列出技能
        
        Args:
            category: 技能类别（None表示所有）
            enabled_only: 是否只返回启用的技能
            
        Returns:
            list[SkillDefinition]: 技能列表
        """
        skills = list(self._skills.values())
        
        # 按类别过滤
        if category:
            skills = [s for s in skills if s.category == category]
        
        # 按启用状态过滤
        if enabled_only:
            skills = [s for s in skills if s.is_enabled()]
        
        # 按名称排序
        skills.sort(key=lambda s: s.name)
        
        return skills

    def find_skills(
        self,
        name_pattern: str = "*",
        category: Optional[SkillCategory] = None,
    ) -> List[SkillDefinition]:
        """按模式查找技能

        Args:
            name_pattern: 名称模式（支持通配符*）
            category: 技能类别

        Returns:
            list[SkillDefinition]: 匹配的技能列表
        """
        import fnmatch

        skills = self.list_skills(category=category)

        # 按名称模式过滤
        if name_pattern != "*":
            pattern = name_pattern.lower().replace("*", "")
            skills = [s for s in skills if pattern in s.name.lower()]

        return skills

    def get_skills_by_tool(self, tool_id: str) -> List[SkillDefinition]:
        """获取使用指定工具的所有技能
        
        Args:
            tool_id: 工具ID
            
        Returns:
            list[SkillDefinition]: 技能列表
        """
        return [s for s in self._skills.values() if s.has_tool(tool_id)]

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息

        Returns:
            dict: 统计信息
        """
        # 按类别统计
        by_category: Dict[str, int] = {}
        for skill in self._skills.values():
            cat = skill.category.value
            by_category[cat] = by_category.get(cat, 0) + 1

        return {
            "total_skills": len(self._skills),
            "by_category": by_category,
        }


__all__ = [
    "SkillRegistry",
]
