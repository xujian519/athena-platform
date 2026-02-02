"""
Co-STORM 与 Athena 平台深度集成

这个模块将 STORM/Co-STORM 深度集成到 Athena 平台,
提供专利领域的多视角研究、模拟专家对话、人机协作能力。

核心模块:
- patent_perspectives: 专利视角发现器
- patent_agents: 专利领域专家 Agent
- patent_curator: 专利信息策展器
- discourse_manager: 协作话语管理器
- mind_map_builder: 思维导图构建器
- cap_integration: 小娜 CAP 能力集成

作者: Athena 平台团队
创建时间: 2025-01-02
"""

from core.storm_integration.patent_agents import (
    PatentAttorneyAgent,
    PatentExaminerAgent,
    TechnicalExpertAgent,
)

__all__ = [
    "PatentAttorneyAgent",
    "PatentExaminerAgent",
    "PatentPerspectiveDiscoverer",
    "TechnicalExpertAgent",
]

__version__ = "0.1.0"
