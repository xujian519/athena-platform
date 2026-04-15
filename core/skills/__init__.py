from __future__ import annotations
"""
Athena 技能系统

模块化的能力扩展系统，允许智能体动态加载和执行技能。

参考：DeerFlow 技能系统设计
"""

from .base import (
    FunctionSkill,
    Skill,
    SkillCategory,
    SkillException,
    SkillMetadata,
    SkillResult,
    SkillStatus,
    skill_function,
)
from .executor import SkillComposer, SkillExecutor
from .manager import SkillManager
from .registry import SkillRegistry

__all__ = [
    # 基础组件
    "Skill",
    "SkillMetadata",
    "SkillResult",
    "SkillException",
    "SkillCategory",
    "SkillStatus",
    "FunctionSkill",
    "skill_function",

    # 注册和管理
    "SkillRegistry",
    "SkillManager",

    # 执行
    "SkillExecutor",
    "SkillComposer",
]
