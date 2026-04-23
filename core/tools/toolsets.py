#!/usr/bin/env python3
from __future__ import annotations
"""
Toolsets 工具集系统 - 场景化工具分组

基于 Hermes Agent 的设计理念，实现场景化的工具分组管理。
支持按专利法律场景自动选择工具集，并转换为 OpenAI function calling schema。

核心特性:
1. 场景化工具分组 - 按专利法律场景预定义工具集
2. 智能场景匹配 - 基于关键词和场景描述自动选择工具集
3. OpenAI Schema 生成 - 自动转换为 function calling 格式
4. 工具集组合 - 支持工具集之间的组合和继承

作者: Athena平台团队
创建时间: 2026-03-19
版本: v1.0.0
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .base import ToolDefinition, ToolRegistry, get_global_registry

logger = logging.getLogger(__name__)


@dataclass
class ScenarioMatchResult:
    """场景匹配结果"""

    toolset_name: str
    score: float  # 匹配分数 (0.0-1.0)
    matched_keywords: list[str]  # 匹配的关键词
    matched_scenarios: list[str]  # 匹配的场景


@dataclass
class Toolset:
    """
    工具集定义

    场景化的工具分组，支持按任务描述自动匹配。
    """

    # 基础信息
    name: str  # 工具集唯一标识
    display_name: str  # 显示名称
    description: str  # 描述

    # 场景定义
    scenarios: list[str] = field(default_factory=list)  # 适用场景列表
    domains: list[str] = field(default_factory=list)  # 适用领域 (patent, legal, academic)
    task_types: list[str] = field(default_factory=list)  # 支持的任务类型

    # 工具列表
    tools: list[str] = field(default_factory=list)  # 工具ID列表

    # 激活关键词
    activation_keywords: list[str] = field(default_factory=list)
    critical_keywords: list[str] = field(default_factory=list)  # 高权重关键词

    # 配置
    priority: int = 1  # 优先级 (数字越大越优先)
    enabled: bool = True  # 是否启用

    # 组合支持
    includes: list[str] = field(default_factory=list)  # 包含的其他工具集
    excludes: list[str] = field(default_factory=list)  # 排除的工具

    # 元数据
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"

    # 运行时状态 (不持久化)
    _resolved_tools: list[ToolDefinition] = field(default_factory=list, repr=False)

    def matches_scenario(self, task_description: str) -> ScenarioMatchResult:
        """
        计算场景匹配度

        Args:
            task_description: 任务描述

        Returns:
            ScenarioMatchResult 匹配结果
        """
        score = 0.0
        matched_keywords = []
        matched_scenarios = []

        desc_lower = task_description.lower()

        # 1. 关键词匹配 (权重 0.4)
        keyword_score = 0.0
        for kw in self.activation_keywords:
            if kw.lower() in desc_lower:
                keyword_score += 0.1
                matched_keywords.append(kw)

        # 高权重关键词 (每个 0.15)
        for kw in self.critical_keywords:
            if kw.lower() in desc_lower:
                keyword_score += 0.15
                matched_keywords.append(kw)

        keyword_score = min(0.4, keyword_score)
        score += keyword_score

        # 2. 场景匹配 (权重 0.35)
        scenario_score = 0.0
        for scenario in self.scenarios:
            # 精确匹配场景描述
            if scenario.lower() in desc_lower:
                scenario_score += 0.2
                matched_scenarios.append(scenario)
            # 部分匹配
            else:
                scenario_words = scenario.lower().split()
                matches = sum(1 for w in scenario_words if w in desc_lower)
                if matches >= len(scenario_words) * 0.5:
                    scenario_score += 0.1
                    matched_scenarios.append(scenario)

        scenario_score = min(0.35, scenario_score)
        score += scenario_score

        # 3. 领域匹配 (权重 0.15)
        domain_keywords = {
            "patent": ["专利", "patent", "发明", "实用新型", "外观设计"],
            "legal": ["法律", "legal", "诉讼", "合同", "法规", "条文"],
            "academic": ["学术", "academic", "论文", "paper", "研究", "research"],
        }

        domain_score = 0.0
        for domain in self.domains:
            if domain in domain_keywords:
                for kw in domain_keywords[domain]:
                    if kw in desc_lower:
                        domain_score += 0.05
                        break

        domain_score = min(0.15, domain_score)
        score += domain_score

        # 4. 任务类型匹配 (权重 0.1)
        task_type_score = 0.0
        for task_type in self.task_types:
            if task_type.lower() in desc_lower:
                task_type_score += 0.1

        task_type_score = min(0.1, task_type_score)
        score += task_type_score

        return ScenarioMatchResult(
            toolset_name=self.name,
            score=min(1.0, score),
            matched_keywords=list(set(matched_keywords)),
            matched_scenarios=list(set(matched_scenarios)),
        )

    def resolve_tools(self, registry: ToolRegistry) -> list[ToolDefinition]:
        """
        解析工具列表

        Args:
            registry: 工具注册中心

        Returns:
            解析后的工具定义列表
        """
        if self._resolved_tools:
            return self._resolved_tools

        resolved = []

        # 1. 添加直接包含的工具
        for tool_id in self.tools:
            if tool_id in self.excludes:
                continue
            tool = registry.get_tool(tool_id)
            if tool and tool.enabled:
                resolved.append(tool)

        # 2. 添加从包含的工具集中解析的工具 (由 ToolsetManager 处理)

        self._resolved_tools = resolved
        return resolved

    def to_openai_schema(self, registry: ToolRegistry) -> list[dict]:
        """
        转换为 OpenAI function calling schema

        Args:
            registry: 工具注册中心

        Returns:
            OpenAI function calling schema 列表
        """
        tools = self.resolve_tools(registry)
        schemas = []

        for tool in tools:
            schema = self._tool_to_openai_schema(tool)
            if schema:
                schemas.append(schema)

        return schemas

    def _tool_to_openai_schema(self, tool: ToolDefinition) -> dict | None:
        """
        将单个工具转换为 OpenAI schema

        Args:
            tool: 工具定义

        Returns:
            OpenAI function schema
        """
        # 构建参数属性
        properties = {}

        # 添加必需参数
        for param in tool.required_params:
            properties[param] = {
                "type": "string",
                "description": f"{param}参数",
            }

        # 添加可选参数
        for param in tool.optional_params:
            properties[param] = {
                "type": "string",
                "description": f"{param}参数(可选)",
            }

        # 如果有 capability，从中提取更多参数信息
        if tool.capability:
            for input_type in tool.capability.input_types:
                if input_type not in properties:
                    properties[input_type] = {
                        "type": "string",
                        "description": f"{input_type}输入",
                    }

        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": tool.required_params,
                },
            },
        }

    def get_tool_count(self) -> int:
        """获取工具数量"""
        return len(self.tools)

    def is_available(self) -> bool:
        """检查工具集是否可用"""
        return self.enabled and len(self.tools) > 0


class ToolsetManager:
    """
    工具集管理器

    管理所有工具集的注册、查询和智能选择。
    """

    def __init__(self, registry: ToolRegistry | None = None):
        """
        初始化工具集管理器

        Args:
            registry: 工具注册中心 (默认使用全局注册中心)
        """
        self.registry = registry or get_global_registry()
        self.toolsets: dict[str, Toolset] = {}
        self._scenario_cache: dict[str, str] = {}  # 场景缓存

        # 初始化默认工具集
        self._initialize_default_toolsets()

        logger.info(f"🔧 ToolsetManager 初始化完成 (已加载 {len(self.toolsets)} 个工具集)")

    def register_toolset(self, toolset: Toolset) -> None:
        """
        注册工具集

        Args:
            toolset: 工具集定义
        """
        if toolset.name in self.toolsets:
            logger.warning(f"⚠️ 工具集已存在，将更新: {toolset.name}")

        self.toolsets[toolset.name] = toolset
        logger.info(
            f"✅ 工具集已注册: {toolset.display_name} "
            f"(场景: {len(toolset.scenarios)}, 工具: {len(toolset.tools)})"
        )

    def get_toolset(self, name: str) -> Toolset | None:
        """
        获取工具集

        Args:
            name: 工具集名称

        Returns:
            工具集定义，如果不存在返回 None
        """
        return self.toolsets.get(name)

    def list_toolsets(self, enabled_only: bool = True) -> list[Toolset]:
        """
        列出所有工具集

        Args:
            enabled_only: 是否只返回启用的工具集

        Returns:
            工具集列表
        """
        toolsets = list(self.toolsets.values())
        if enabled_only:
            toolsets = [t for t in toolsets if t.enabled]
        return sorted(toolsets, key=lambda t: -t.priority)

    async def auto_select_toolset(
        self,
        task_description: str,
        min_score: float = 0.3,
    ) -> Toolset | None:
        """
        自动选择最适合的工具集

        Args:
            task_description: 任务描述
            min_score: 最低匹配分数阈值

        Returns:
            匹配度最高的工具集，如果没有匹配返回 None
        """
        # 检查缓存
        cache_key = task_description[:100]  # 截断以节省内存
        if cache_key in self._scenario_cache:
            cached_name = self._scenario_cache[cache_key]
            return self.toolsets.get(cached_name)

        # 评估所有工具集
        scored_toolsets: list[tuple[Toolset, ScenarioMatchResult]] = []

        for toolset in self.toolsets.values():
            if not toolset.enabled:
                continue

            result = toolset.matches_scenario(task_description)
            if result.score >= min_score:
                scored_toolsets.append((toolset, result))

        # 按分数和优先级排序
        scored_toolsets.sort(key=lambda x: (x[1].score, x[0].priority), reverse=True)

        if scored_toolsets:
            best_toolset, best_result = scored_toolsets[0]

            logger.info(
                f"🎯 自动选择工具集: {best_toolset.display_name} "
                f"(分数: {best_result.score:.2f}, 关键词: {best_result.matched_keywords})"
            )

            # 更新缓存
            self._scenario_cache[cache_key] = best_toolset.name

            return best_toolset

        return None

    def get_toolset_schemas(
        self,
        toolset_names: Optional[list[str]] = None,
    ) -> list[dict]:
        """
        获取工具集的 OpenAI schema

        Args:
            toolset_names: 工具集名称列表 (None 表示所有启用的)

        Returns:
            OpenAI function calling schema 列表
        """
        if toolset_names:
            toolsets = [self.toolsets.get(name) for name in toolset_names]
            toolsets = [t for t in toolsets if t and t.enabled]
        else:
            toolsets = self.list_toolsets(enabled_only=True)

        schemas = []
        seen_tools: set[str] = set()  # 避免重复

        for toolset in toolsets:
            for tool in toolset.resolve_tools(self.registry):
                if tool.tool_id not in seen_tools:
                    schema = toolset._tool_to_openai_schema(tool)
                    if schema:
                        schemas.append(schema)
                        seen_tools.add(tool.tool_id)

        return schemas

    def get_statistics(self) -> dict[str, Any]:
        """
        获取工具集统计信息

        Returns:
            统计信息字典
        """
        total = len(self.toolsets)
        enabled = sum(1 for t in self.toolsets.values() if t.enabled)

        return {
            "total_toolsets": total,
            "enabled_toolsets": enabled,
            "toolsets": [
                {
                    "name": t.name,
                    "display_name": t.display_name,
                    "tool_count": t.get_tool_count(),
                    "scenarios": t.scenarios,
                    "enabled": t.enabled,
                }
                for t in self.list_toolsets(enabled_only=False)
            ],
        }

    def _initialize_default_toolsets(self) -> None:
        """初始化专利法律场景的默认工具集"""

        # ========================================
        # 1. 专利检索工具集
        # ========================================
        self.register_toolset(
            Toolset(
                name="patent_search",
                display_name="专利检索",
                description="专利检索场景工具集，支持多数据源检索、检索式构建和结果分析",
                scenarios=[
                    "专利检索",
                    "现有技术调研",
                    "技术背景分析",
                    "专利搜索",
                    "专利查询",
                ],
                domains=["patent"],
                task_types=["search", "retrieval", "analysis"],
                tools=[
                    # 这些工具ID需要在实际注册时匹配
                    "enhanced_patent_search",
                    "web_search",
                    "pdf_patent_parser",
                ],
                activation_keywords=[
                    "检索",
                    "搜索",
                    "查询",
                    "查找",
                    "现有技术",
                    "技术背景",
                    "对比文件",
                ],
                critical_keywords=[
                    "专利检索",
                    "专利搜索",
                    "CNIPA",
                    "USPTO",
                    "EPO",
                    "WIPO",
                    "检索式",
                ],
                priority=10,
            )
        )

        # ========================================
        # 2. 新颖性分析工具集
        # ========================================
        self.register_toolset(
            Toolset(
                name="novelty_analysis",
                display_name="新颖性分析",
                description="新颖性分析场景工具集，支持三步法推理、技术特征对比和创造性评估",
                scenarios=[
                    "新颖性分析",
                    "创造性分析",
                    "三步法推理",
                    "技术特征对比",
                    "区别特征分析",
                ],
                domains=["patent", "legal"],
                task_types=["analysis", "reasoning", "comparison"],
                tools=[
                    "novelty_analyzer",
                    "claim_comparator",
                    "technical_feature_extractor",
                    "legal_reasoning_engine",
                ],
                activation_keywords=[
                    "新颖性",
                    "创造性",
                    "三步法",
                    "区别特征",
                    "技术启示",
                    "显而易见",
                    "技术方案",
                    "对比分析",
                ],
                critical_keywords=[
                    "新颖性分析",
                    "创造性分析",
                    "三步法推理",
                    "区别技术特征",
                    "技术启示判断",
                ],
                priority=9,
            )
        )

        # ========================================
        # 3. 审查意见答复工具集
        # ========================================
        self.register_toolset(
            Toolset(
                name="oa_response",
                display_name="审查意见答复",
                description="审查意见答复场景工具集，支持意见陈述、权利要求修改和答复策略生成",
                scenarios=[
                    "审查意见答复",
                    "意见陈述",
                    "权利要求修改",
                    "OA答复",
                    "审查意见分析",
                ],
                domains=["patent", "legal"],
                task_types=["writing", "analysis", "modification"],
                tools=[
                    "oa_analyzer",
                    "claim_amender",
                    "response_generator",
                    "legal_template_manager",
                ],
                activation_keywords=[
                    "审查意见",
                    "答复",
                    "意见陈述",
                    "修改",
                    "权利要求",
                    "OA",
                ],
                critical_keywords=[
                    "审查意见答复",
                    "意见陈述书",
                    "权利要求书修改",
                    "OA Response",
                    "Office Action",
                ],
                priority=9,
            )
        )

        # ========================================
        # 4. 侵权分析工具集
        # ========================================
        self.register_toolset(
            Toolset(
                name="infringement_analysis",
                display_name="侵权分析",
                description="侵权分析场景工具集，支持权利要求对比、等同原则判断和侵权风险评估",
                scenarios=[
                    "侵权分析",
                    "权利要求对比",
                    "等同原则判断",
                    "侵权风险评估",
                    "FTO分析",
                ],
                domains=["patent", "legal"],
                task_types=["analysis", "comparison", "risk_assessment"],
                tools=[
                    "infringement_analyzer",
                    "claim_coverage_checker",
                    "equivalence_judge",
                    "legal_case_search",
                ],
                activation_keywords=[
                    "侵权",
                    "比对",
                    "等同",
                    "特征覆盖",
                    "FTO",
                    "自由实施",
                ],
                critical_keywords=[
                    "侵权分析",
                    "等同原则",
                    "全面覆盖原则",
                    "FTO分析",
                    "侵权风险评估",
                ],
                priority=9,
            )
        )

        # ========================================
        # 5. 法律文书生成工具集
        # ========================================
        self.register_toolset(
            Toolset(
                name="legal_document",
                display_name="法律文书生成",
                description="法律文书生成场景工具集，支持专利申请书、答复意见、法律意见书等文书生成",
                scenarios=[
                    "法律文书生成",
                    "专利撰写",
                    "申请文件",
                    "法律意见书",
                ],
                domains=["patent", "legal"],
                task_types=["writing", "generation"],
                tools=[
                    "document_generator",
                    "template_manager",
                    "legal_formatter",
                    "content_validator",
                ],
                activation_keywords=[
                    "撰写",
                    "生成",
                    "起草",
                    "申请文件",
                    "法律文书",
                    "文档",
                ],
                critical_keywords=[
                    "专利撰写",
                    "法律意见书",
                    "申请文件",
                    "权利要求书",
                    "说明书",
                ],
                priority=8,
            )
        )

        # ========================================
        # 6. 学术研究工具集
        # ========================================
        self.register_toolset(
            Toolset(
                name="academic_research",
                display_name="学术研究",
                description="学术研究场景工具集，支持论文检索、文献综述和技术趋势分析",
                scenarios=[
                    "学术研究",
                    "论文检索",
                    "文献综述",
                    "技术趋势分析",
                ],
                domains=["academic"],
                task_types=["research", "analysis"],
                tools=[
                    "web_search",  # 使用本地搜索
                    "academic-search",  # MCP学术搜索
                    "paper_summarizer",
                    "citation_analyzer",
                ],
                activation_keywords=[
                    "论文",
                    "学术",
                    "研究",
                    "文献",
                    "引用",
                    "综述",
                ],
                critical_keywords=[
                    "学术论文",
                    "文献检索",
                    "引用分析",
                    "技术综述",
                    "研究前沿",
                ],
                priority=7,
            )
        )


# ========================================
# 全局工具集管理器实例
# ========================================
_global_toolset_manager: ToolsetManager | None = None


def get_toolset_manager() -> ToolsetManager:
    """获取全局工具集管理器"""
    global _global_toolset_manager
    if _global_toolset_manager is None:
        _global_toolset_manager = ToolsetManager()
    return _global_toolset_manager


def auto_select_toolset(task_description: str) -> Toolset | None:
    """
    便捷函数：自动选择工具集

    Args:
        task_description: 任务描述

    Returns:
        匹配的工具集
    """
    import asyncio

    manager = get_toolset_manager()
    return asyncio.get_event_loop().run_until_complete(
        manager.auto_select_toolset(task_description)
    )


__all__ = [
    "Toolset",
    "ToolsetManager",
    "ScenarioMatchResult",
    "get_toolset_manager",
    "auto_select_toolset",
]
