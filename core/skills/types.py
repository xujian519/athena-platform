#!/usr/bin/env python3
"""
技能数据类型定义

定义Skills系统的核心数据结构。

作者: Athena平台团队
创建时间: 2026-04-21
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class SkillCategory(Enum):
    """技能类别"""

    ANALYSIS = "analysis"  # 分析类技能
    WRITING = "writing"  # 写作类技能
    SEARCH = "search"  # 检索类技能
    COORDINATION = "coordination"  # 协调类技能
    AUTOMATION = "automation"  # 自动化技能


@dataclass
class SkillMetadata:
    """技能元数据"""

    author: str | None = None
    version: str = "1.0.0"
    tags: list[str] = field(default_factory=list)
    enabled: bool = True
    priority: int = 5  # 1-10, 10最高
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class SkillDefinition:
    """技能定义"""

    id: str  # 技能唯一标识
    name: str  # 技能名称
    category: SkillCategory  # 技能类别
    description: str  # 技能描述
    tools: list[str] = field(default_factory=list)  # 关联的工具列表
    metadata: SkillMetadata | None = None  # 元数据
    content: str = ""  # 技能内容（Markdown格式）
    source: str = "athena"  # 来源
    path: str | None = None  # 文件路径

    def __post_init__(self):
        """初始化后处理"""
        if self.metadata is None:
            self.metadata = SkillMetadata()

    def has_tool(self, tool_id: str) -> bool:
        """检查技能是否包含指定工具"""
        return tool_id in self.tools

    def is_enabled(self) -> bool:
        """检查技能是否启用"""
        return self.metadata.enabled if self.metadata else True


__all__ = [
    "SkillCategory",
    "SkillMetadata",
    "SkillDefinition",
]
