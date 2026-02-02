#!/usr/bin/env python3
"""
协作模式工厂
Collaboration Pattern Factory

作者: Athena平台团队
创建时间: 2026-01-20
重构时间: 2026-01-26
版本: 2.0.0

提供协作模式的创建、注册和发现功能。
"""

import logging
from typing import Any

from .base import CollaborationPattern
from .patterns.consensus import ConsensusCollaborationPattern
from .patterns.hierarchical import HierarchicalCollaborationPattern
from .patterns.parallel import ParallelCollaborationPattern
from .patterns.sequential import SequentialCollaborationPattern

# 导入 MultiAgentCollaborationFramework - 使用绝对导入避免相对层级问题
try:
    from core.collaboration.multi_agent_collaboration import MultiAgentCollaborationFramework
except ImportError:
    # 如果绝对导入失败，尝试相对导入
    try:
        from ...multi_agent_collaboration import MultiAgentCollaborationFramework
    except ImportError:
        # 如果都失败，设置为 None
        MultiAgentCollaborationFramework = None  # type: ignore

logger = logging.getLogger(__name__)


class CollaborationPatternFactory:
    """
    协作模式工厂

    支持创建不同的协作模式实例，并支持注册自定义模式。
    """

    _patterns = {
        "sequential": SequentialCollaborationPattern,
        "parallel": ParallelCollaborationPattern,
        "hierarchical": HierarchicalCollaborationPattern,
        "consensus": ConsensusCollaborationPattern,
    }

    @classmethod
    def create_pattern(
        cls, pattern_type: str, framework: MultiAgentCollaborationFramework
    ) -> CollaborationPattern | None:
        """
        创建协作模式实例

        Args:
            pattern_type: 协作模式类型 (sequential, parallel, hierarchical, consensus)
            framework: 多智能体协作框架实例

        Returns:
            协作模式实例，如果类型未知则返回None
        """
        pattern_class = cls._patterns.get(pattern_type.lower())
        if pattern_class:
            return pattern_class(framework)
        else:
            logger.error(f"未知的协作模式类型: {pattern_type}")
            return None

    @classmethod
    def get_available_patterns(cls) -> list[str]:
        """获取可用的协作模式列表"""
        return list(cls._patterns.keys())

    @classmethod
    def register_pattern(cls, pattern_type: str, pattern_class: type) -> Any:
        """
        注册新的协作模式

        Args:
            pattern_type: 模式类型名称
            pattern_class: 协作模式类 (必须继承CollaborationPattern)
        """
        cls._patterns[pattern_type.lower()] = pattern_class
        logger.info(f"协作模式 {pattern_type} 已注册")
