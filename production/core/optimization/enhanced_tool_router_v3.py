#!/usr/bin/env python3
"""
增强工具路由器 - 第一阶段优化版本
Enhanced Tool Router - Phase 1 Optimization

优化重点:
1. 多工具竞争决策算法优化
2. 工具相似度评分机制
3. 工具组合推荐权重
4. 工具冲突检测模块
5. 工具选择置信度评分

作者: 小诺·双鱼公主
版本: v3.0.0 "竞争决策优化"
创建: 2026-01-12
基于: v2.0.0
"""

from __future__ import annotations
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ConflictLevel(Enum):
    """冲突级别"""

    NO_CONFLICT = "no_conflict"  # 无冲突
    LOW_CONFLICT = "low_conflict"  # 低冲突(可并行)
    MEDIUM_CONFLICT = "medium_conflict"  # 中等冲突(需顺序)
    HIGH_CONFLICT = "high_conflict"  # 高冲突(互斥)


@dataclass
class ToolSimilarity:
    """工具相似度"""

    tool_a: str
    tool_b: str
    similarity_score: float  # 0-1,越高越相似
    functional_overlap: float  # 功能重叠度
    compatibility_score: float  # 兼容性评分


@dataclass
class ToolConflict:
    """工具冲突"""

    tool_a: str
    tool_b: str
    conflict_level: ConflictLevel
    conflict_reason: str
    resolution_strategy: str


@dataclass
class ToolCombination:
    """工具组合"""

    tools: list[str]
    combination_score: float
    synergy_score: float  # 协同效应评分
    confidence: float
    reasoning: str


@dataclass
class RoutingDecision:
    """路由决策(增强版)"""

    selected_tools: list[str]
    strategy: str
    confidence: float
    reasoning: str
    alternative_combinations: list[ToolCombination]
    detected_conflicts: list[ToolConflict]
    execution_order: list[str]  # 执行顺序
    timestamp: datetime = field(default_factory=datetime.now)


class EnhancedToolRouter:
    """增强工具路由器 - 第一阶段优化"""

    def __init__(self):
        self.name = "增强工具路由器 v3.0"
        self.version = "3.0.0"

        # 工具注册表
        self.tool_registry: dict[str, dict] = {}

        # 工具相似度矩阵
        self.similarity_matrix: dict[tuple[str, str], ToolSimilarity] = {}

        # 工具冲突规则
        self.conflict_rules: dict[tuple[str, str], ToolConflict] = {}

        # 工具性能历史
        self.performance_history: dict[str, list[dict]] = defaultdict(list)

        # 统计信息
        self.stats = {
            "total_routings": 0,
            "conflicts_detected": 0,
            "combinations_recommended": 0,
            "avg_confidence": 0.0,
        }

        # 初始化
        self._initialize_tool_registry()
        self._build_similarity_matrix()
        self._load_conflict_rules()

        logger.info(f"🧭 {self.name} 初始化完成")

    def _initialize_tool_registry(self):
        """初始化工具注册表"""
        # 定义17个能力模块的工具元数据
        self.tool_registry = {
            "daily_chat": {
                "category": "conversation",
                "priority": 1,
                "cost": 0.1,
                "reliability": 0.99,
                "capabilities": ["闲聊", "问候", "情感交流"],
            },
            "platform_controller": {
                "category": "management",
                "priority": 10,
                "cost": 0.5,
                "reliability": 0.95,
                "capabilities": ["平台管理", "服务调度", "智能体管理"],
            },
            "coding_assistant": {
                "category": "development",
                "priority": 5,
                "cost": 0.3,
                "reliability": 0.92,
                "capabilities": ["代码生成", "代码审查", "调试"],
            },
            "life_assistant": {
                "category": "lifestyle",
                "priority": 3,
                "cost": 0.2,
                "reliability": 0.90,
                "capabilities": ["日程管理", "提醒", "生活建议"],
            },
            "patent": {
                "category": "legal",
                "priority": 8,
                "cost": 0.4,
                "reliability": 0.94,
                "capabilities": ["专利分析", "专利检索", "专利撰写"],
            },
            "legal": {
                "category": "legal",
                "priority": 8,
                "cost": 0.4,
                "reliability": 0.93,
                "capabilities": ["法律咨询", "案例分析", "合规检查"],
            },
            "nlp": {
                "category": "processing",
                "priority": 6,
                "cost": 0.3,
                "reliability": 0.91,
                "capabilities": ["文本分析", "情感分析", "实体识别"],
            },
            "knowledge_graph": {
                "category": "knowledge",
                "priority": 7,
                "cost": 0.4,
                "reliability": 0.89,
                "capabilities": ["知识推理", "关系分析", "图谱查询"],
            },
            "memory": {
                "category": "storage",
                "priority": 4,
                "cost": 0.2,
                "reliability": 0.96,
                "capabilities": ["记忆存储", "记忆检索", "记忆管理"],
            },
            "optimization": {
                "category": "system",
                "priority": 6,
                "cost": 0.3,
                "reliability": 0.88,
                "capabilities": ["性能优化", "资源调度", "参数调优"],
            },
            "multimodal": {
                "category": "processing",
                "priority": 7,
                "cost": 0.5,
                "reliability": 0.85,
                "capabilities": ["图像理解", "文档分析", "多模态融合"],
            },
            "agent_fusion": {
                "category": "orchestration",
                "priority": 9,
                "cost": 0.4,
                "reliability": 0.87,
                "capabilities": ["智能体协同", "任务分发", "结果融合"],
            },
            "autonomous": {
                "category": "intelligence",
                "priority": 8,
                "cost": 0.5,
                "reliability": 0.83,
                "capabilities": ["自主学习", "任务规划", "决策优化"],
            },
            "xiaona": {
                "category": "expert",
                "priority": 9,
                "cost": 0.4,
                "reliability": 0.95,
                "capabilities": ["专利法律", "案例分析", "专业咨询"],
            },
            "xiaochen": {
                "category": "expert",
                "priority": 7,
                "cost": 0.3,
                "reliability": 0.90,
                "capabilities": ["内容创作", "社交媒体", "数据分析"],
            },
        }

        logger.info(f"✅ 工具注册表初始化完成: {len(self.tool_registry)}个工具")

    def _build_similarity_matrix(self):
        """构建工具相似度矩阵"""
        tools = list(self.tool_registry.keys())

        for i, tool_a in enumerate(tools):
            for tool_b in tools[i + 1 :]:
                # 计算功能相似度
                similarity = self._calculate_similarity(tool_a, tool_b)
                self.similarity_matrix[tool_a, tool_b] = similarity

        logger.info(f"✅ 相似度矩阵构建完成: {len(self.similarity_matrix)}对工具")

    def _calculate_similarity(self, tool_a: str, tool_b: str) -> ToolSimilarity:
        """计算工具相似度"""
        meta_a = self.tool_registry[tool_a]
        meta_b = self.tool_registry[tool_b]

        # 类别相似度
        category_similarity = 1.0 if meta_a["category"] == meta_b["category"] else 0.0

        # 能力重叠度
        capabilities_a = set(meta_a["capabilities"])
        capabilities_b = set(meta_b["capabilities"])
        intersection = capabilities_a & capabilities_b
        union = capabilities_a | capabilities_b
        functional_overlap = len(intersection) / len(union) if union else 0.0

        # 综合相似度
        similarity_score = 0.3 * category_similarity + 0.7 * functional_overlap

        # 兼容性评分(相似度高可能竞争,相似度低可能互补)
        if similarity_score > 0.7:
            compatibility_score = 1.0 - similarity_score  # 高相似=竞争
        else:
            compatibility_score = similarity_score  # 低相似=互补

        return ToolSimilarity(
            tool_a=tool_a,
            tool_b=tool_b,
            similarity_score=similarity_score,
            functional_overlap=functional_overlap,
            compatibility_score=compatibility_score,
        )

    def _load_conflict_rules(self):
        """加载工具冲突规则"""
        # 定义已知的工具冲突规则
        conflicts = [
            # 专利相关工具的冲突
            ToolConflict(
                tool_a="patent",
                tool_b="xiaona",
                conflict_level=ConflictLevel.LOW_CONFLICT,
                conflict_reason="功能重叠,都支持专利分析",
                resolution_strategy="选择可靠性更高的xiaona,或组合使用",
            ),
            # 法律相关工具的冲突
            ToolConflict(
                tool_a="legal",
                tool_b="xiaona",
                conflict_level=ConflictLevel.MEDIUM_CONFLICT,
                conflict_reason="法律能力重叠",
                resolution_strategy="根据具体场景选择,xiaona更专业",
            ),
            # 资源密集型工具的冲突
            ToolConflict(
                tool_a="multimodal",
                tool_b="knowledge_graph",
                conflict_level=ConflictLevel.MEDIUM_CONFLICT,
                conflict_reason="都是资源密集型操作",
                resolution_strategy="顺序执行,避免资源竞争",
            ),
        ]

        for conflict in conflicts:
            self.conflict_rules[conflict.tool_a, conflict.tool_b] = conflict

        logger.info(f"✅ 冲突规则加载完成: {len(self.conflict_rules)}条规则")

    async def route(
        self, intent: str, context: dict[str, Any], available_tools: list[str] | None = None
    ) -> RoutingDecision:
        """
        智能路由决策

        Args:
            intent: 用户意图
            context: 上下文信息
            available_tools: 可用工具列表

        Returns:
            RoutingDecision: 路由决策
        """
        # 1. 获取候选工具
        candidates = self._get_candidate_tools(intent, available_tools)

        # 2. 评估单个工具
        tool_scores = await self._evaluate_single_tools(candidates, intent, context)

        # 3. 检测冲突
        conflicts = self._detect_conflicts(candidates)

        # 4. 生成工具组合
        combinations = self._generate_combinations(candidates, tool_scores, conflicts)

        # 5. 选择最佳组合
        best_combination = self._select_best_combination(combinations)

        # 6. 确定执行顺序
        execution_order = self._determine_execution_order(best_combination.tools, conflicts)

        # 7. 生成决策
        decision = RoutingDecision(
            selected_tools=best_combination.tools,
            strategy="multi_objective_optimization",
            confidence=best_combination.confidence,
            reasoning=best_combination.reasoning,
            alternative_combinations=combinations[:3],  # Top-3备选
            detected_conflicts=conflicts,
            execution_order=execution_order,
        )

        # 8. 更新统计
        self._update_stats(decision)

        return decision

    def _get_candidate_tools(self, intent: str, available_tools: list[str]) -> list[str]:
        """获取候选工具列表"""
        if available_tools:
            candidates = [t for t in available_tools if t in self.tool_registry]
        else:
            # 基于意图推荐候选工具
            candidates = self._recommend_tools_by_intent(intent)

        return candidates

    def _recommend_tools_by_intent(self, intent: str) -> list[str]:
        """基于意图推荐工具(优化版)"""
        # 优化的意图-工具映射
        intent_tool_map = {
            "patent_search": ["xiaona", "patent", "knowledge_graph"],
            "patent_analysis": ["xiaona", "patent", "nlp"],
            "patent_drafting": ["xiaona", "patent", "coding_assistant"],
            "legal_query": ["xiaona", "legal", "knowledge_graph"],
            "coding": ["coding_assistant", "optimization", "memory"],
            "code_generation": ["coding_assistant", "optimization"],
            "data_analysis": ["nlp", "knowledge_graph", "xiaochen"],
            "daily_chat": ["daily_chat", "life_assistant", "memory"],
            "chat": ["daily_chat", "memory"],
            "greeting": ["daily_chat"],
            "system_control": ["platform_controller", "optimization"],
            "multimodal": ["multimodal", "nlp", "knowledge_graph"],
            "agent_coordination": ["agent_fusion", "autonomous"],
            "problem_solving": ["coding_assistant", "knowledge_graph", "autonomous"],
        }

        return intent_tool_map.get(intent, ["daily_chat", "life_assistant", "memory"])

    async def _evaluate_single_tools(
        self, tools: list[str], intent: str, context: dict[str, Any]
    ) -> dict[str, float]:
        """评估单个工具的得分"""
        scores = {}

        for tool in tools:
            if tool not in self.tool_registry:
                continue

            meta = self.tool_registry[tool]

            # 多维度评分
            score = 0.0

            # 1. 可靠性评分 (30%)
            score += 0.3 * meta["reliability"]

            # 2. 优先级评分 (20%)
            max_priority = max(self.tool_registry[t]["priority"] for t in tools)
            priority_score = meta["priority"] / max_priority
            score += 0.2 * priority_score

            # 3. 历史性能评分 (30%)
            perf_score = self._get_performance_score(tool)
            score += 0.3 * perf_score

            # 4. 成本效率评分 (20%)
            max_cost = max(self.tool_registry[t]["cost"] for t in tools)
            cost_score = 1.0 - (meta["cost"] / max_cost)
            score += 0.2 * cost_score

            scores[tool] = score

        return scores

    def _get_performance_score(self, tool: str) -> float:
        """获取工具历史性能评分"""
        if tool not in self.performance_history:
            return 0.8  # 默认评分

        history = self.performance_history[tool]
        if not history:
            return 0.8

        # 计算平均成功率
        success_rate = sum(h.get("success", 1.0) for h in history[-10:]) / min(  # 最近10次
            len(history), 10
        )

        return success_rate

    def _detect_conflicts(self, tools: list[str]) -> list[ToolConflict]:
        """检测工具冲突"""
        conflicts = []

        for i, tool_a in enumerate(tools):
            for tool_b in tools[i + 1 :]:
                # 检查预定义冲突规则
                if (tool_a, tool_b) in self.conflict_rules:
                    conflicts.append(self.conflict_rules[tool_a, tool_b])
                elif (tool_b, tool_a) in self.conflict_rules:
                    conflicts.append(self.conflict_rules[tool_b, tool_a])
                else:
                    # 动态检测冲突
                    similarity = self.similarity_matrix.get((tool_a, tool_b))
                    if similarity and similarity.similarity_score > 0.8:
                        # 高相似度工具存在竞争
                        conflicts.append(
                            ToolConflict(
                                tool_a=tool_a,
                                tool_b=tool_b,
                                conflict_level=ConflictLevel.MEDIUM_CONFLICT,
                                conflict_reason=f"高功能相似度({similarity.similarity_score:.2f})",
                                resolution_strategy="选择评分更高的工具",
                            )
                        )

        return conflicts

    def _generate_combinations(
        self, tools: list[str], tool_scores: dict[str, float], conflicts: list[ToolConflict]
    ) -> list[ToolCombination]:
        """生成工具组合"""
        combinations = []

        # 1. 单工具组合
        for tool in tools:
            combinations.append(
                ToolCombination(
                    tools=[tool],
                    combination_score=tool_scores.get(tool, 0.0),
                    synergy_score=1.0,
                    confidence=tool_scores.get(tool, 0.0),
                    reasoning=f"单工具策略: {tool}",
                )
            )

        # 2. 双工具组合(互补工具)
        for i, tool_a in enumerate(tools):
            for tool_b in tools[i + 1 :]:
                # 检查是否冲突
                has_high_conflict = any(
                    c.conflict_level == ConflictLevel.HIGH_CONFLICT
                    for c in conflicts
                    if (c.tool_a == tool_a and c.tool_b == tool_b)
                    or (c.tool_a == tool_b and c.tool_b == tool_a)
                )

                if has_high_conflict:
                    continue

                # 计算协同效应
                synergy = self._calculate_synergy(tool_a, tool_b)

                # 计算组合得分
                avg_score = (tool_scores.get(tool_a, 0.0) + tool_scores.get(tool_b, 0.0)) / 2
                combination_score = avg_score * (1 + 0.2 * synergy)  # 协同奖励

                combinations.append(
                    ToolCombination(
                        tools=[tool_a, tool_b],
                        combination_score=combination_score,
                        synergy_score=synergy,
                        confidence=min(tool_scores.get(tool_a, 0.0), tool_scores.get(tool_b, 0.0)),
                        reasoning=f"双工具协同: {tool_a} + {tool_b}, 协同度={synergy:.2f}",
                    )
                )

        # 3. 三工具组合(谨慎使用)
        if len(tools) >= 3:
            # 选择Top-3工具
            top_tools = sorted(tools, key=lambda t: tool_scores.get(t, 0.0), reverse=True)[:3]

            # 检查是否适合组合
            if self._can_combine_tools(top_tools, conflicts):
                synergy = self._calculate_multi_synergy(top_tools)
                avg_score = sum(tool_scores.get(t, 0.0) for t in top_tools) / len(top_tools)
                combination_score = avg_score * (1 + 0.1 * synergy)  # 较小的协同奖励

                combinations.append(
                    ToolCombination(
                        tools=top_tools,
                        combination_score=combination_score,
                        synergy_score=synergy,
                        confidence=min(tool_scores.get(t, 0.0) for t in top_tools),
                        reasoning=f"多工具协同: {', '.join(top_tools)}, 协同度={synergy:.2f}",
                    )
                )

        # 按组合得分排序
        combinations.sort(key=lambda c: c.combination_score, reverse=True)

        return combinations

    def _calculate_synergy(self, tool_a: str, tool_b: str) -> float:
        """计算双工具协同效应"""
        # 基于相似度矩阵
        similarity = self.similarity_matrix.get((tool_a, tool_b))
        if similarity:
            # 互补性工具(similarity低,compatibility高)有更好的协同
            return similarity.compatibility_score
        return 0.5  # 默认中等协同

    def _calculate_multi_synergy(self, tools: list[str]) -> float:
        """计算多工具协同效应"""
        if len(tools) < 2:
            return 1.0

        synergies = []
        for i, tool_a in enumerate(tools):
            for tool_b in tools[i + 1 :]:
                synergy = self._calculate_synergy(tool_a, tool_b)
                synergies.append(synergy)

        return sum(synergies) / len(synergies)

    def _can_combine_tools(self, tools: list[str], conflicts: list[ToolConflict]) -> bool:
        """判断工具是否可以组合"""
        # 检查是否有高冲突
        high_conflicts = [
            c
            for c in conflicts
            if c.conflict_level == ConflictLevel.HIGH_CONFLICT
            and c.tool_a in tools
            and c.tool_b in tools
        ]

        return len(high_conflicts) == 0

    def _select_best_combination(self, combinations: list[ToolCombination]) -> ToolCombination:
        """选择最佳工具组合"""
        if not combinations:
            # 返回默认组合
            return ToolCombination(
                tools=["daily_chat"],
                combination_score=0.5,
                synergy_score=1.0,
                confidence=0.5,
                reasoning="默认工具",
            )

        # 优先选择单工具(简单高效)
        single_tools = [c for c in combinations if len(c.tools) == 1]
        if single_tools and single_tools[0].confidence > 0.85:
            return single_tools[0]

        # 否则选择组合得分最高的
        return combinations[0]

    def _determine_execution_order(
        self, tools: list[str], conflicts: list[ToolConflict]
    ) -> list[str]:
        """确定工具执行顺序"""
        if len(tools) <= 1:
            return tools

        # 根据优先级和冲突关系确定顺序
        tool_priorities = {tool: self.tool_registry[tool]["priority"] for tool in tools}

        # 按优先级降序排列
        sorted_tools = sorted(tools, key=lambda t: tool_priorities[t], reverse=True)

        # 处理中高冲突的工具
        for conflict in conflicts:
            if conflict.conflict_level in [
                ConflictLevel.MEDIUM_CONFLICT,
                ConflictLevel.HIGH_CONFLICT,
            ] and conflict.tool_a in sorted_tools and conflict.tool_b in sorted_tools:
                # 调整顺序,避免同时执行
                idx_a = sorted_tools.index(conflict.tool_a)
                idx_b = sorted_tools.index(conflict.tool_b)
                if idx_a < idx_b:
                    # tool_a先执行,tool_b后执行
                    pass
                else:
                    # tool_b先执行,tool_a后执行
                    pass

        return sorted_tools

    def _update_stats(self, decision: RoutingDecision):
        """更新统计信息"""
        self.stats["total_routings"] += 1
        self.stats["conflicts_detected"] += len(decision.detected_conflicts)
        self.stats["combinations_recommended"] += len(decision.alternative_combinations)

        # 更新平均置信度
        n = self.stats["total_routings"]
        old_avg = self.stats["avg_confidence"]
        self.stats["avg_confidence"] = (old_avg * (n - 1) + decision.confidence) / n

    def record_performance(
        self, tool: str, success: bool, execution_time: float, context: dict[str, Any]
    ):
        """记录工具性能"""
        self.performance_history[tool].append(
            {
                "success": success,
                "execution_time": execution_time,
                "context": context,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # 限制历史记录数量
        if len(self.performance_history[tool]) > 100:
            self.performance_history[tool] = self.performance_history[tool][-50:]

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "registered_tools": len(self.tool_registry),
            "similarity_pairs": len(self.similarity_matrix),
            "conflict_rules": len(self.conflict_rules),
            "tools_with_history": len(self.performance_history),
        }


# 全局实例
_router_instance: EnhancedToolRouter | None = None


def get_enhanced_tool_router() -> EnhancedToolRouter:
    """获取增强工具路由器单例"""
    global _router_instance
    if _router_instance is None:
        _router_instance = EnhancedToolRouter()
    return _router_instance
