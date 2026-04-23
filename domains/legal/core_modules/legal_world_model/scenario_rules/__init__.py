"""
v4 提示词资产迁移后的场景规则定义。

这些规则由 `scripts/migrate_v4_prompts_to_rules.py` 从 prompts/ 目录的 Markdown 文件自动生成，
并可通过 `ScenarioRuleRetrieverOptimized` 写入 Neo4j 规则库。
"""

from .hitl_safety_block import HITL_SAFETY_BLOCK
from .patent_inventive_analysis import PATENT_INVENTIVE_ANALYSIS_RULE
from .patent_office_action_analysis import PATENT_OFFICE_ACTION_ANALYSIS_RULE

__all__ = [
    "HITL_SAFETY_BLOCK",
    "PATENT_INVENTIVE_ANALYSIS_RULE",
    "PATENT_OFFICE_ACTION_ANALYSIS_RULE",
]
