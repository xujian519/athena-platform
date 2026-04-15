#!/usr/bin/env python3
"""
增强工具路由器 (Enhanced Tool Router)
基于多因素评分和竞争决策的智能工具选择

作者: 小诺·双鱼公主
版本: v2.0.0
优化目标: 工具选择准确率 89% → 94%
"""

from __future__ import annotations
import heapq
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ToolPriority(str, Enum):
    """工具优先级"""

    CRITICAL = "critical"  # 关键,必须执行
    HIGH = "high"  # 高,优先执行
    MEDIUM = "medium"  # 中等,正常执行
    LOW = "low"  # 低,可以延后


@dataclass
class ToolCandidate:
    """工具候选"""

    tool_id: str
    tool_name: str
    capability_score: float  # 能力匹配度 (0-1)
    confidence: float  # 置信度 (0-1)
    estimated_latency: float  # 预估延迟 (ms)
    cost: float  # 执行成本 (0-1)
    priority: ToolPriority = ToolPriority.MEDIUM
    metadata: dict[str, Any] = field(default_factory=dict)

    def __lt__(self, other):
        """用于堆排序"""
        return self.score() > other.score()

    def score(self) -> float:
        """计算综合得分"""
        # 加权得分公式
        weights = {"capability": 0.40, "confidence": 0.25, "speed": 0.20, "cost": 0.15}

        # 速度得分(延迟越低越好)
        speed_score = max(0, 1 - self.estimated_latency / 1000)

        # 成本得分(成本越低越好)
        cost_score = 1 - self.cost

        total = (
            weights["capability"] * self.capability_score
            + weights["confidence"] * self.confidence
            + weights["speed"] * speed_score
            + weights["cost"] * cost_score
        )

        return total


@dataclass
class RoutingDecision:
    """路由决策"""

    decision_id: str
    query: str
    selected_tools: list[str]
    rejected_tools: list[str]
    confidence: float
    reasoning: str
    execution_order: list[int]  # 工具执行顺序
    estimated_total_latency: float


class EnhancedToolRouter:
    """
    增强工具路由器

    功能:
    1. 多工具竞争决策
    2. 工具相似度评分
    3. 工具组合推荐
    4. 冲突检测
    5. 置信度评分
    """

    def __init__(self):
        self.name = "增强工具路由器"
        self.version = "2.0.0"
        self.routing_history: list[RoutingDecision] = []
        self.tool_registry: dict[str, dict[str, Any]] = {}

        # 性能统计
        self.stats = {
            "total_routings": 0,
            "successful_routings": 0,
            "avg_confidence": 0.0,
            "avg_latency_reduction": 0.0,
        }

        logger.info(f"✅ {self.name} 初始化完成")

    def register_tool(
        self,
        tool_id: str,
        tool_name: str,
        capabilities: list[str],
        metadata: dict[str, Any] | None = None,
    ):
        """注册工具"""
        self.tool_registry[tool_id] = {
            "tool_id": tool_id,
            "tool_name": tool_name,
            "capabilities": capabilities,
            "metadata": metadata or {},
            "usage_count": 0,
            "success_rate": 1.0,
        }
        logger.debug(f"📝 注册工具: {tool_name} ({tool_id})")

    async def select_tools(
        self,
        query: str,
        intent: str | None = None,
        context: dict[str, Any] | None = None,
        max_tools: int = 3,
    ) -> RoutingDecision:
        """
        选择最佳工具组合

        Args:
            query: 用户查询
            intent: 意图类型
            context: 上下文信息
            max_tools: 最大工具数量

        Returns:
            路由决策
        """
        decision_id = f"route_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.stats["total_routings"] += 1

        # 1. 获取候选工具
        candidates = await self._get_tool_candidates(query, intent, context)

        if not candidates:
            return RoutingDecision(
                decision_id=decision_id,
                query=query,
                selected_tools=[],
                rejected_tools=[],
                confidence=0.0,
                reasoning="没有找到合适的工具",
                execution_order=[],
                estimated_total_latency=0,
            )

        # 2. 计算工具相似度并检测冲突
        similarity_matrix = self._compute_tool_similarity(candidates)
        conflicts = self._detect_conflicts(candidates, similarity_matrix)

        # 3. 过滤冲突工具
        valid_candidates = self._filter_conflicts(candidates, conflicts)

        # 4. 计算综合得分
        for candidate in valid_candidates:
            # 调整得分基于相似度(避免选择过于相似的工具)
            similarity_penalty = self._compute_similarity_penalty(
                candidate, valid_candidates, similarity_matrix
            )
            candidate.capability_score *= 1 - similarity_penalty * 0.2

        # 5. 选择Top-K工具
        selected = heapq.nsmallest(max_tools, valid_candidates)

        # 6. 确定执行顺序
        execution_order = self._determine_execution_order(selected)

        # 7. 计算置信度
        confidence = self._compute_selection_confidence(selected)

        # 8. 生成决策解释
        reasoning = self._generate_reasoning(
            selected, rejected=[c.tool_id for c in candidates if c not in selected]
        )

        # 9. 估算总延迟
        total_latency = sum(c.estimated_latency for c in selected)

        decision = RoutingDecision(
            decision_id=decision_id,
            query=query,
            selected_tools=[c.tool_id for c in selected],
            rejected_tools=[c.tool_id for c in candidates if c not in selected],
            confidence=confidence,
            reasoning=reasoning,
            execution_order=execution_order,
            estimated_total_latency=total_latency,
        )

        self.routing_history.append(decision)

        # 更新统计
        self.stats["successful_routings"] += 1
        self.stats["avg_confidence"] = (
            self.stats["avg_confidence"] * (self.stats["successful_routings"] - 1) + confidence
        ) / self.stats["successful_routings"]

        return decision

    async def _get_tool_candidates(
        self, query: str, intent: str, context: dict[str, Any]
    ) -> list[ToolCandidate]:
        """获取工具候选列表"""
        candidates = []

        # 基于意图筛选工具
        for tool_id, tool_info in self.tool_registry.items():
            # 简化版:假设所有工具都有一定匹配度
            # 实际应该基于能力匹配、历史表现等

            capability_score = self._compute_capability_match(query, tool_info, intent)

            if capability_score > 0.3:  # 阈值
                candidates.append(
                    ToolCandidate(
                        tool_id=tool_id,
                        tool_name=tool_info["tool_name"],
                        capability_score=capability_score,
                        confidence=tool_info.get("success_rate", 1.0),
                        estimated_latency=self._estimate_tool_latency(tool_id, context),
                        cost=self._compute_tool_cost(tool_id, context),
                    )
                )

        return candidates

    def _compute_capability_match(
        self, query: str, tool_info: dict[str, Any], intent: str,
    ) -> float:
        """计算能力匹配度"""
        # 简化版实现
        capabilities = tool_info.get("capabilities", [])

        if intent:
            # 基于意图匹配
            if intent in capabilities:
                return 0.9
            elif any(intent in cap for cap in capabilities):
                return 0.7

        # 基于关键词匹配
        query_lower = query.lower()
        matches = sum(1 for cap in capabilities if cap.lower() in query_lower)

        return min(1.0, matches * 0.3 + 0.4)

    def _compute_tool_similarity(
        self, candidates: list[ToolCandidate]
    ) -> dict[tuple[str, str], float]:
        """计算工具相似度矩阵"""
        similarity = {}

        for i, c1 in enumerate(candidates):
            for j, c2 in enumerate(candidates):
                if i >= j:
                    continue

                # 简化版:基于工具名称和能力计算相似度
                name_sim = self._string_similarity(c1.tool_name, c2.tool_name)

                # 这里可以加入更多相似度计算维度
                similarity[c1.tool_id, c2.tool_id] = name_sim
                similarity[c2.tool_id, c1.tool_id] = name_sim

        return similarity

    def _string_similarity(self, s1: str, s2: str) -> float:
        """计算字符串相似度(简化版Jaccard)"""
        set1 = set(s1.lower().split())
        set2 = set(s2.lower().split())

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0

    def _detect_conflicts(
        self, candidates: list[ToolCandidate], similarity_matrix: dict[tuple[str, str], float]
    ) -> list[tuple[str, str]]:
        """检测工具冲突"""
        conflicts = []

        # 相似度过高的工具视为冲突
        SIMILARITY_THRESHOLD = 0.8

        for (tool1, tool2), similarity in similarity_matrix.items():
            if similarity > SIMILARITY_THRESHOLD:
                conflicts.append((tool1, tool2))

        return conflicts

    def _filter_conflicts(
        self, candidates: list[ToolCandidate], conflicts: list[tuple[str, str]]
    ) -> list[ToolCandidate]:
        """过滤冲突工具,保留得分更高的"""
        if not conflicts:
            return candidates

        # 标记要移除的工具
        to_remove = set()
        for tool1, tool2 in conflicts:
            # 比较得分,移除较低的
            c1 = next((c for c in candidates if c.tool_id == tool1), None)
            c2 = next((c for c in candidates if c.tool_id == tool2), None)

            if c1 and c2:
                if c1.score() < c2.score():
                    to_remove.add(tool1)
                else:
                    to_remove.add(tool2)

        return [c for c in candidates if c.tool_id not in to_remove]

    def _compute_similarity_penalty(
        self,
        candidate: ToolCandidate,
        all_candidates: list[ToolCandidate],
        similarity_matrix: dict[tuple[str, str], float],
    ) -> float:
        """计算相似度惩罚"""
        total_similarity = 0
        count = 0

        for other in all_candidates:
            if other.tool_id == candidate.tool_id:
                continue

            sim = similarity_matrix.get((candidate.tool_id, other.tool_id), 0)
            total_similarity += sim
            count += 1

        return total_similarity / count if count > 0 else 0

    def _determine_execution_order(self, selected: list[ToolCandidate]) -> list[int]:
        """确定工具执行顺序"""
        # 简化版:按优先级和延迟排序
        indexed = list(enumerate(selected))

        # 排序:高优先级、低延迟在前
        indexed.sort(
            key=lambda x: (
                -x[1].priority.value.count("critical"),  # 降序
                -x[1].priority.value.count("high"),
                x[1].estimated_latency,  # 升序
            )
        )

        return [i for i, _ in indexed]

    def _compute_selection_confidence(self, selected: list[ToolCandidate]) -> float:
        """计算选择置信度"""
        if not selected:
            return 0.0

        # 基于工具的能力和置信度计算
        avg_capability = sum(c.capability_score for c in selected) / len(selected)
        avg_confidence = sum(c.confidence for c in selected) / len(selected)

        return (avg_capability + avg_confidence) / 2

    def _generate_reasoning(self, selected: list[ToolCandidate], rejected: list[str]) -> str:
        """生成决策解释"""
        parts = []

        if selected:
            parts.append("选择的工具:")
            for i, tool in enumerate(selected, 1):
                parts.append(
                    f"  {i}. {tool.tool_name} (得分: {tool.score():.2f}, "
                    f"能力: {tool.capability_score:.2f}, 置信度: {tool.confidence:.2f})"
                )

        if rejected:
            parts.append(f"\n未选择的工具: {', '.join(rejected)}")

        return "\n".join(parts)

    def _estimate_tool_latency(self, tool_id: str, context: dict[str, Any]) -> float:
        """估算工具延迟"""
        # 简化版:基于历史数据或默认值
        tool_info = self.tool_registry.get(tool_id, {})
        return tool_info.get("avg_latency_ms", 100)

    def _compute_tool_cost(self, tool_id: str, context: dict[str, Any]) -> float:
        """计算工具执行成本"""
        # 简化版:基于资源消耗
        tool_info = self.tool_registry.get(tool_id, {})
        return tool_info.get("cost", 0.5)

    def get_status(self) -> dict[str, Any]:
        """获取路由器状态"""
        return {
            "name": self.name,
            "version": self.version,
            "registered_tools": len(self.tool_registry),
            "routing_stats": self.stats,
            "recent_decisions": [
                {
                    "decision_id": d.decision_id,
                    "selected_count": len(d.selected_tools),
                    "confidence": d.confidence,
                    "latency": d.estimated_total_latency,
                }
                for d in self.routing_history[-10:]
            ],
        }


# 全局单例
_router_instance: EnhancedToolRouter | None = None


def get_enhanced_tool_router() -> EnhancedToolRouter:
    """获取增强工具路由器实例"""
    global _router_instance
    if _router_instance is None:
        _router_instance = EnhancedToolRouter()
        # 注册默认工具
        _register_default_tools(_router_instance)
    return _router_instance


def _register_default_tools(router: EnhancedToolRouter):
    """注册默认工具集"""
    default_tools = [
        ("patent_search", "专利搜索", ["patent", "search", "retrieval"]),
        ("patent_analysis", "专利分析", ["patent", "analysis", "nlp"]),
        ("legal_qa", "法律问答", ["legal", "qa", "knowledge"]),
        ("web_search", "网络搜索", ["web", "search", "browser"]),
        ("code_generation", "代码生成", ["code", "generation", "programming"]),
        ("data_analysis", "数据分析", ["data", "analysis", "statistics"]),
    ]

    for tool_id, name, capabilities in default_tools:
        router.register_tool(tool_id, name, capabilities)
