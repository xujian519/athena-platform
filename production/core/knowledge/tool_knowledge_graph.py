#!/usr/bin/env python3
from __future__ import annotations
"""
工具知识图谱
Tool Knowledge Graph

构建和管理工具的知识图谱:
1. 工具节点定义
2. 工具关系建立
3. 能力语义描述
4. 兼容性推理
5. 智能推荐
6. 图谱可视化

作者: Athena平台团队
创建时间: 2025-12-26
版本: v1.0.0 "工具图谱"
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ToolRelationshipType(Enum):
    """工具关系类型"""

    SIMILAR = "similar"  # 相似功能
    COMPLEMENTARY = "complementary"  # 互补功能
    DEPENDENT = "dependent"  # 依赖关系
    EXCLUSIVE = "exclusive"  # 互斥关系
    SEQUENCE = "sequence"  # 顺序关系
    ALTERNATIVE = "alternative"  # 替代关系


class CapabilityType(Enum):
    """能力类型"""

    DATA_INPUT = "data_input"  # 数据输入
    DATA_OUTPUT = "data_output"  # 数据输出
    PROCESSING = "processing"  # 处理能力
    ANALYSIS = "analysis"  # 分析能力
    GENERATION = "generation"  # 生成能力
    TRANSFORMATION = "transformation"  # 转换能力
    VALIDATION = "validation"  # 验证能力
    STORAGE = "storage"  # 存储能力
    SEARCH = "search"  # 搜索能力


@dataclass
class ToolNode:
    """工具节点"""

    tool_id: str
    name: str
    category: str

    # 能力描述
    capabilities: dict[CapabilityType, list[str]] = field(default_factory=dict)

    # 输入输出
    input_types: list[str] = field(default_factory=list)
    output_types: list[str] = field(default_factory=list)

    # 性能指标
    avg_response_time: float = 0.0
    success_rate: float = 1.0
    usage_count: int = 0

    # 元数据
    tags: list[str] = field(default_factory=list)
    author: str = "system"
    version: str = "1.0.0"


@dataclass
class ToolRelationship:
    """工具关系"""

    source_tool: str
    target_tool: str
    relationship_type: ToolRelationshipType
    strength: float = 1.0  # 0-1,关系强度
    metadata: dict[str, Any] = field(default_factory=dict)


class ToolKnowledgeGraph:
    """
    工具知识图谱

    核心功能:
    1. 工具节点管理
    2. 关系建立
    3. 能力匹配
    4. 兼容性推理
    5. 推荐排序
    6. 图谱分析
    """

    def __init__(self):
        # 工具节点
        self.tools: dict[str, ToolNode] = {}

        # 关系图谱
        self.relationships: dict[str, list[ToolRelationship]] = defaultdict(list)

        # 能力索引
        self.capability_index: dict[CapabilityType, dict[str, set[str]]] = defaultdict(
            lambda: defaultdict(set)
        )

        # 标签索引
        self.tag_index: dict[str, set[str]] = defaultdict(set)

        logger.info("🔗 工具知识图谱初始化完成")

    def add_tool(self, tool: ToolNode) -> None:
        """添加工具节点"""
        self.tools[tool.tool_id] = tool

        # 更新能力索引
        for cap_type, capabilities in tool.capabilities.items():
            for cap in capabilities:
                self.capability_index[cap_type][cap].add(tool.tool_id)

        # 更新标签索引
        for tag in tool.tags:
            self.tag_index[tag].add(tool.tool_id)

        logger.info(f"🔧 工具已添加: {tool.name}")

    def add_relationship(self, relationship: ToolRelationship) -> None:
        """添加工具关系"""
        key = f"{relationship.source_tool}->{relationship.target_tool}"
        self.relationships[key].append(relationship)

        logger.debug(f"🔗 关系已添加: {key} ({relationship.relationship_type.value})")

    async def find_tools_by_capability(
        self, capability_type: CapabilityType, capability: str
    ) -> list[str]:
        """根据能力查找工具"""
        return list(self.capability_index[capability_type][capability])

    async def find_similar_tools(self, tool_id: str, top_k: int = 5) -> list[tuple[str, float]]:
        """查找相似工具"""
        if tool_id not in self.tools:
            return []

        tool = self.tools[tool_id]
        similarities = []

        for other_id, other_tool in self.tools.items():
            if other_id == tool_id:
                continue

            # 计算相似度
            similarity = await self._calculate_similarity(tool, other_tool)
            similarities.append((other_id, similarity))

        # 排序返回Top-K
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    async def _calculate_similarity(self, tool1: ToolNode, tool2: ToolNode) -> float:
        """计算工具相似度"""
        similarity = 0.0

        # 1. 类别相似度
        if tool1.category == tool2.category:
            similarity += 0.3

        # 2. 能力相似度
        common_capabilities = 0
        total_capabilities = 0

        for cap_type in CapabilityType:
            caps1 = set(tool1.capabilities.get(cap_type, []))
            caps2 = set(tool2.capabilities.get(cap_type, []))

            common_capabilities += len(caps1 & caps2)
            total_capabilities += len(caps1 | caps2)

        if total_capabilities > 0:
            similarity += (common_capabilities / total_capabilities) * 0.4

        # 3. 标签相似度
        tags1 = set(tool1.tags)
        tags2 = set(tool2.tags)
        if tags1 or tags2:
            tag_similarity = len(tags1 & tags2) / len(tags1 | tags2)
            similarity += tag_similarity * 0.2

        # 4. 输入输出类型相似度
        io_similarity = (
            len(set(tool1.input_types) & set(tool2.input_types))
            + len(set(tool1.output_types) & set(tool2.output_types))
        ) / max(
            len(set(tool1.input_types) | set(tool2.input_types))
            + len(set(tool1.output_types) | set(tool2.output_types)),
            1,
        )
        similarity += io_similarity * 0.1

        return min(similarity, 1.0)

    async def check_compatibility(self, tool1_id: str, tool2_id: str) -> float:
        """
        检查工具兼容性

        Returns:
            float: 兼容性分数 0-1
        """
        if tool1_id not in self.tools or tool2_id not in self.tools:
            return 0.0

        tool1 = self.tools[tool1_id]
        tool2 = self.tools[tool2_id]

        compatibility = 0.0

        # 1. 检查输入输出匹配
        output_matches_input = any(output in tool2.input_types for output in tool1.output_types)
        if output_matches_input:
            compatibility += 0.5

        # 2. 检查关系
        key = f"{tool1_id}->{tool2_id}"
        if key in self.relationships:
            for rel in self.relationships[key]:
                if rel.relationship_type == ToolRelationshipType.COMPLEMENTARY:
                    compatibility += 0.3 * rel.strength
                elif rel.relationship_type == ToolRelationshipType.SEQUENCE:
                    compatibility += 0.4 * rel.strength
                elif rel.relationship_type == ToolRelationshipType.EXCLUSIVE:
                    compatibility -= 0.8 * rel.strength

        # 3. 检查类别兼容性
        if tool1.category == tool2.category:
            compatibility += 0.1

        return max(0.0, min(compatibility, 1.0))

    async def recommend_tool_combination(
        self,
        task_description: str,
        required_capabilities: list[tuple[CapabilityType, str]],
        exclude: list[str] | None = None,
        top_k: int = 5,
    ) -> list[tuple[str, float]]:
        """
        推荐工具组合

        Args:
            task_description: 任务描述
            required_capabilities: 需要的能力列表
            exclude: 排除的工具
            top_k: 返回Top-K

        Returns:
            list[tuple[tool_id, score]]: 推荐的工具及其分数
        """
        exclude = exclude or []

        # 收集候选工具
        candidate_scores: dict[str, float] = defaultdict(float)

        # 根据能力匹配评分
        for cap_type, capability in required_capabilities:
            tools = await self.find_tools_by_capability(cap_type, capability)
            for tool_id in tools:
                if tool_id not in exclude:
                    candidate_scores[tool_id] += 1.0

        # 根据任务描述的关键词评分
        task_words = set(task_description.lower().split())
        for tool_id, tool in self.tools.items():
            if tool_id in exclude:
                continue

            # 匹配工具名称
            if any(word in tool.name.lower() for word in task_words):
                candidate_scores[tool_id] += 0.5

            # 匹配标签
            for tag in tool.tags:
                if tag.lower() in task_description.lower():
                    candidate_scores[tool_id] += 0.3

            # 匹配能力描述
            for capabilities in tool.capabilities.values():
                for cap in capabilities:
                    if cap.lower() in task_description.lower():
                        candidate_scores[tool_id] += 0.2

        # 考虑成功率
        for tool_id in candidate_scores:
            if tool_id in self.tools:
                candidate_scores[tool_id] *= self.tools[tool_id].success_rate

        # 排序返回
        sorted_tools = sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True)

        return sorted_tools[:top_k]

    async def get_tool_path(self, start_tool: str, end_tool: str) -> list[str | None]:
        """
        获取工具路径(BFS)

        Returns:
            Optional[list[str]]: 从start到end的工具路径
        """
        if start_tool not in self.tools or end_tool not in self.tools:
            return None

        # BFS搜索
        from collections import deque

        queue = deque([[start_tool]])
        visited = {start_tool}

        while queue:
            path = queue.popleft()
            current = path[-1]

            if current == end_tool:
                return path

            # 获取相邻工具
            neighbors = await self._get_neighbors(current)
            for neighbor in neighbors:
                if neighbor not in visited:
                    visited.add(neighbor)
                    new_path = [*path, neighbor]
                    queue.append(new_path)

        return None

    async def _get_neighbors(self, tool_id: str) -> set[str]:
        """获取相邻工具"""
        neighbors = set()

        # 查找所有关系
        for key, relationships in self.relationships.items():
            if key.startswith(f"{tool_id}->"):
                for rel in relationships:
                    neighbors.add(rel.target_tool)

        return neighbors

    async def get_graph_statistics(self) -> dict[str, Any]:
        """获取图谱统计"""
        # 计算连通性
        total_pairs = len(self.tools) * (len(self.tools) - 1) / 2
        connected_pairs = len(self.relationships)

        # 最常用工具
        top_tools = sorted(
            [(tid, tool.usage_count) for tid, tool in self.tools.items()],
            key=lambda x: x[1],
            reverse=True,
        )[:10]

        # 能力分布
        capability_distribution = {}
        for cap_type, capabilities in self.capability_index.items():
            capability_distribution[cap_type.value] = {
                cap: len(tools) for cap, tools in capabilities.items()
            }

        return {
            "tools": {"total": len(self.tools), "by_category": self._count_by_category()},
            "relationships": {
                "total": connected_pairs,
                "connectivity": connected_pairs / max(total_pairs, 1),
                "by_type": self._count_by_relationship_type(),
            },
            "capabilities": {
                "total_types": len(CapabilityType),
                "distribution": capability_distribution,
            },
            "top_tools": top_tools,
        }

    def _count_by_category(self) -> dict[str, int]:
        """按类别统计工具"""
        category_count = defaultdict(int)
        for tool in self.tools.values():
            category_count[tool.category] += 1
        return dict(category_count)

    def _count_by_relationship_type(self) -> dict[str, int]:
        """按关系类型统计"""
        type_count = defaultdict(int)
        for relationships in self.relationships.values():
            for rel in relationships:
                type_count[rel.relationship_type.value] += 1
        return dict(type_count)


# 导出便捷函数
_tool_kg: ToolKnowledgeGraph | None = None


def get_tool_knowledge_graph() -> ToolKnowledgeGraph:
    """获取工具知识图谱单例"""
    global _tool_kg
    if _tool_kg is None:
        _tool_kg = ToolKnowledgeGraph()
    return _tool_kg


# 预定义一些常用工具
async def initialize_default_tools(kg: ToolKnowledgeGraph):
    """初始化默认工具"""

    # 专利检索工具
    patent_search = ToolNode(
        tool_id="patent_search",
        name="专利检索",
        category="patent",
        capabilities={
            CapabilityType.DATA_INPUT: ["专利号", "关键词", "申请人"],
            CapabilityType.SEARCH: ["全文检索", "字段检索"],
            CapabilityType.DATA_OUTPUT: ["专利文献", "检索结果"],
        },
        input_types=["query", "keywords"],
        output_types=["patent_document", "search_results"],
        tags=["专利", "检索", "搜索"],
        success_rate=0.95,
    )

    # 专利分析工具
    patent_analysis = ToolNode(
        tool_id="patent_analysis",
        name="专利分析",
        category="patent",
        capabilities={
            CapabilityType.PROCESSING: ["文献分析", "技术提取"],
            CapabilityType.ANALYSIS: ["新颖性分析", "创造性分析"],
        },
        input_types=["patent_document"],
        output_types=["analysis_report"],
        tags=["专利", "分析", "评估"],
        success_rate=0.92,
    )

    # 代码生成工具
    code_generation = ToolNode(
        tool_id="code_generation",
        name="代码生成",
        category="development",
        capabilities={
            CapabilityType.GENERATION: ["代码生成", "函数生成"],
            CapabilityType.PROCESSING: ["代码优化", "代码注释"],
        },
        input_types=["requirement", "specification"],
        output_types=["code", "function"],
        tags=["代码", "开发", "编程"],
        success_rate=0.88,
    )

    # 添加工具
    kg.add_tool(patent_search)
    kg.add_tool(patent_analysis)
    kg.add_tool(code_generation)

    # 添加关系
    kg.add_relationship(
        ToolRelationship(
            source_tool="patent_search",
            target_tool="patent_analysis",
            relationship_type=ToolRelationshipType.SEQUENCE,
            strength=0.9,
        )
    )

    kg.add_relationship(
        ToolRelationship(
            source_tool="patent_search",
            target_tool="patent_analysis",
            relationship_type=ToolRelationshipType.COMPLEMENTARY,
            strength=0.8,
        )
    )

    logger.info("✅ 默认工具已初始化")
