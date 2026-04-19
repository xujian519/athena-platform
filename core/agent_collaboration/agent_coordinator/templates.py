#!/usr/bin/env python3
from __future__ import annotations
"""
Agent协调器 - 工作流模板
Agent Coordinator - Workflow Templates

作者: Athena AI系统
创建时间: 2025-12-04
重构时间: 2026-01-26
版本: 2.0.0
"""

from typing import Any


def initialize_workflow_templates() -> dict[str, dict[str, Any]]:
    """
    初始化工作流模板

    Returns:
        工作流模板字典
    """
    return {
        "patent_research": {
            "name": "专利研究工作流",
            "description": "完整的专利研究流程",
            "steps": [
                {"type": "patent_search", "agent": "search_agent"},
                {"type": "patent_analysis", "agent": "analysis_agent"},
                {"type": "innovation_generation", "agent": "creative_agent"},
            ],
            "workflow_type": "sequential",
        },
        "competitive_analysis": {
            "name": "竞争分析工作流",
            "description": "竞争对手专利分析",
            "steps": [
                {"type": "multi_source_search", "agent": "search_agent"},
                {"type": "competitive_analysis", "agent": "analysis_agent"},
                {"type": "technology_trend_analysis", "agent": "analysis_agent"},
            ],
            "workflow_type": "parallel",
        },
        "innovation_scouting": {
            "name": "创新机会发现",
            "description": "发现技术创新机会",
            "steps": [
                {"type": "semantic_search", "agent": "search_agent"},
                {"type": "white_space_analysis", "agent": "analysis_agent"},
                {"type": "creative_solutions", "agent": "creative_agent"},
            ],
            "workflow_type": "collaborative",
        },
    }
