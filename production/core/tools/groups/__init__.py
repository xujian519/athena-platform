#!/usr/bin/env python3
"""
工具组定义模块
Tool Group Definitions

定义各领域的工具组,用于自动工具供给。

作者: Athena平台团队
创建时间: 2026-01-20
版本: v1.0.0 "Phase 1"
"""

from __future__ import annotations
from ..base import ToolCategory
from ..tool_group import ActivationRule, GroupActivationRule, ToolGroupDef

# ============================================================================
# 专利分析工具组
# ============================================================================
PATENT_ANALYSIS_GROUP = ToolGroupDef(
    name="patent_analysis",
    display_name="专利分析工具组",
    description="用于专利检索、分析、审查的工具集",
    categories=[
        ToolCategory.PATENT_SEARCH,
        ToolCategory.PATENT_ANALYSIS,
        ToolCategory.SEMANTIC_ANALYSIS,
    ],
    activation_rules=[
        ActivationRule(
            rule_type=GroupActivationRule.KEYWORD,
            keywords=[
                "专利",
                "patent",
                "发明",
                "实用新型",
                "外观设计",
                "审查",
                "新颖性",
                "创造性",
                "实用性",
                "权利要求",
                "claim",
                "现有技术",
                "prior art",
            ],
            priority=10,
        ),
        ActivationRule(
            rule_type=GroupActivationRule.TASK_TYPE,
            task_types=[
                "patent_analysis",
                "patent_search",
                "novelty_assessment",
                "inventive_step_analysis",
                "claim_analysis",
            ],
            priority=10,
        ),
        ActivationRule(
            rule_type=GroupActivationRule.DOMAIN,
            domains=["patent", "知识产权", "intellectual_property"],
            priority=9,
        ),
    ],
)

# ============================================================================
# 法律研究工具组
# ============================================================================
LEGAL_RESEARCH_GROUP = ToolGroupDef(
    name="legal_research",
    display_name="法律研究工具组",
    description="用于法律案例检索、法规查询、合同审查的工具集",
    categories=[
        ToolCategory.DOCUMENT_RETRIEVAL,
        ToolCategory.LEGAL_ANALYSIS,
        ToolCategory.ACADEMIC_SEARCH,
    ],
    activation_rules=[
        ActivationRule(
            rule_type=GroupActivationRule.KEYWORD,
            keywords=[
                "法律",
                "legal",
                "诉讼",
                "litigation",
                "合同",
                "contract",
                "法条",
                "法规",
                "regulation",
                "案例",
                "case",
                "判决",
                "judgment",
                "合规",
                "compliance",
                "审查",
                "review",
            ],
            priority=10,
        ),
        ActivationRule(
            rule_type=GroupActivationRule.TASK_TYPE,
            task_types=["legal_research", "contract_review", "case_analysis", "compliance_check"],
            priority=10,
        ),
        ActivationRule(rule_type=GroupActivationRule.DOMAIN, domains=["legal", "law"], priority=9),
    ],
)

# ============================================================================
# 浏览器自动化工具组
# ============================================================================
BROWSER_AUTOMATION_GROUP = ToolGroupDef(
    name="browser_automation",
    display_name="浏览器自动化工具组",
    description="用于Web自动化、爬虫、数据采集的工具集",
    categories=[
        ToolCategory.WEB_AUTOMATION,
        ToolCategory.DATA_EXTRACTION,
        ToolCategory.API_INTEGRATION,
    ],
    activation_rules=[
        ActivationRule(
            rule_type=GroupActivationRule.KEYWORD,
            keywords=[
                "爬虫",
                "crawler",
                "抓取",
                "scrape",
                "网页",
                "web",
                "浏览器",
                "browser",
                "自动化",
                "automation",
                "下载",
                "download",
                "采集",
                "collect",
            ],
            priority=10,
        ),
        ActivationRule(
            rule_type=GroupActivationRule.TASK_TYPE,
            task_types=["web_scraping", "data_collection", "browser_automation", "web_crawling"],
            priority=10,
        ),
    ],
)

# ============================================================================
# 学术搜索工具组
# ============================================================================
ACADEMIC_SEARCH_GROUP = ToolGroupDef(
    name="academic_search",
    display_name="学术搜索工具组",
    description="用于学术论文检索、文献调研的工具集",
    categories=[
        ToolCategory.ACADEMIC_SEARCH,
        ToolCategory.DOCUMENT_RETRIEVAL,
        ToolCategory.SEMANTIC_ANALYSIS,
    ],
    activation_rules=[
        ActivationRule(
            rule_type=GroupActivationRule.KEYWORD,
            keywords=[
                "论文",
                "paper",
                "学术",
                "academic",
                "文献",
                "literature",
                "期刊",
                "journal",
                "研究",
                "research",
                "引用",
                "citation",
                "scholar",
                "arxiv",
                "pubmed",
            ],
            priority=10,
        ),
        ActivationRule(
            rule_type=GroupActivationRule.TASK_TYPE,
            task_types=[
                "academic_search",
                "literature_review",
                "paper_analysis",
                "citation_analysis",
            ],
            priority=10,
        ),
        ActivationRule(
            rule_type=GroupActivationRule.DOMAIN,
            domains=["academic", "research", "science"],
            priority=9,
        ),
    ],
)

# ============================================================================
# 知识图谱工具组
# ============================================================================
KNOWLEDGE_GRAPH_GROUP = ToolGroupDef(
    name="knowledge_graph",
    display_name="知识图谱工具组",
    description="用于知识图谱构建、查询、分析的工具集",
    categories=[
        ToolCategory.KNOWLEDGE_GRAPH,
        ToolCategory.VECTOR_SEARCH,
        ToolCategory.SEMANTIC_ANALYSIS,
    ],
    activation_rules=[
        ActivationRule(
            rule_type=GroupActivationRule.KEYWORD,
            keywords=[
                "知识图谱",
                "knowledge graph",
                "图谱",
                "graph",
                "实体",
                "entity",
                "关系",
                "relation",
                "推理",
                "inference",
                "nebula",
                "neo4j",
                "图数据库",
            ],
            priority=10,
        ),
        ActivationRule(
            rule_type=GroupActivationRule.TASK_TYPE,
            task_types=[
                "knowledge_graph_query",
                "entity_extraction",
                "relation_analysis",
                "graph_reasoning",
            ],
            priority=10,
        ),
    ],
)

# ============================================================================
# 通用工具组
# ============================================================================
GENERAL_GROUP = ToolGroupDef(
    name="general",
    display_name="通用工具组",
    description="通用工具集,适用于各种常见任务",
    categories=[
        ToolCategory.LOGGING,
        ToolCategory.MONITORING,
        ToolCategory.ERROR_HANDLING,
        ToolCategory.DATA_VALIDATION,
        ToolCategory.DATA_TRANSFORMATION,
    ],
    activation_rules=[
        ActivationRule(
            rule_type=GroupActivationRule.ADAPTIVE, priority=1  # 最低优先级,作为默认选项
        )
    ],
)

# ============================================================================
# 导出所有工具组定义
# ============================================================================
ALL_TOOL_GROUPS = [
    PATENT_ANALYSIS_GROUP,
    LEGAL_RESEARCH_GROUP,
    BROWSER_AUTOMATION_GROUP,
    ACADEMIC_SEARCH_GROUP,
    KNOWLEDGE_GRAPH_GROUP,
    GENERAL_GROUP,
]

__all__ = [
    "ACADEMIC_SEARCH_GROUP",
    "ALL_TOOL_GROUPS",
    "BROWSER_AUTOMATION_GROUP",
    "GENERAL_GROUP",
    "KNOWLEDGE_GRAPH_GROUP",
    "LEGAL_RESEARCH_GROUP",
    "PATENT_ANALYSIS_GROUP",
]
