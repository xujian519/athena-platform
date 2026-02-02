#!/usr/bin/env python3
"""
智能工具发现引擎
Intelligent Tool Discovery Engine

智能发现和匹配最合适的工具:
1. 工具语义嵌入
2. 任务-工具匹配
3. 工具能力索引
4. 智能推荐
5. 工具使用学习
6. 工具性能追踪

作者: Athena平台团队
创建时间: 2025-12-26
版本: v1.0.0 "智能发现"
"""

import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


logger = logging.getLogger(__name__)


class ToolCategory(Enum):
    """工具类别"""

    SEARCH = "search"  # 搜索类
    ANALYSIS = "analysis"  # 分析类
    GENERATION = "generation"  # 生成类
    AUTOMATION = "automation"  # 自动化类
    COMMUNICATION = "communication"  # 通信类
    DATABASE = "database"  # 数据库类
    API = "api"  # API类
    UTILITY = "utility"  # 实用工具类


@dataclass
class Tool:
    """工具定义"""

    tool_id: str
    name: str
    category: ToolCategory
    description: str

    # 能力
    capabilities: list[str] = field(default_factory=list)

    # 输入输出
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)

    # 性能指标
    avg_response_time: float = 0.0
    success_rate: float = 1.0
    usage_count: int = 0

    # 语义嵌入(用于匹配)
    embedding: np.ndarray | None = None

    # 元数据
    tags: list[str] = field(default_factory=list)
    author: str = "system"
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.now)

    # 状态
    available: bool = True
    deprecated: bool = False


@dataclass
class ToolMatch:
    """工具匹配结果"""

    tool: Tool
    similarity_score: float  # 0-1
    confidence: float  # 0-1
    reasoning: str  # 匹配理由


class IntelligentToolDiscovery:
    """
    智能工具发现引擎

    核心功能:
    1. 工具注册和索引
    2. 语义匹配
    3. 智能推荐
    4. 性能追踪
    5. 使用学习
    6. 工具发现
    """

    def __init__(self):
        # 工具注册表
        self.tools: dict[str, Tool] = {}

        # 类别索引
        self.by_category: dict[ToolCategory, list[str]] = defaultdict(list)

        # 能力索引
        self.by_capability: dict[str, list[str]] = defaultdict(list)

        # 使用历史
        self.usage_history: deque = deque(maxlen=1000)

        # 性能统计
        self.performance_metrics: dict[str, dict[str, float]] = defaultdict(
            lambda: {"avg_score": 0.8, "usage_count": 0, "success_count": 0, "avg_time": 0.0}
        )

        logger.info("🔍 智能工具发现引擎初始化完成")

    async def register_tool(self, tool: Tool) -> bool:
        """注册工具"""
        self.tools[tool.tool_id] = tool

        # 更新索引
        self.by_category[tool.category].append(tool.tool_id)
        for capability in tool.capabilities:
            self.by_capability[capability].append(tool.tool_id)

        logger.info(f"✅ 工具已注册: {tool.name} ({tool.category.value})")

        return True

    async def discover_tools(
        self,
        task_description: str,
        required_capabilities: list[str] | None = None,
        category_filter: ToolCategory | None = None,
        top_k: int = 5,
    ) -> list[ToolMatch]:
        """智能发现工具"""

        # 收集候选工具
        candidates = list(self.tools.values())

        # 过滤
        if category_filter:
            candidates = [t for t in candidates if t.category == category_filter]

        if required_capabilities:
            candidates = [
                t for t in candidates if any(cap in t.capabilities for cap in required_capabilities)
            ]

        # 评分和排序
        scored_tools = []
        for tool in candidates:
            if not tool.available or tool.deprecated:
                continue

            # 计算匹配分数
            similarity = await self._calculate_similarity(task_description, tool)
            confidence = await self._calculate_confidence(tool)
            reasoning = await self._generate_reasoning(task_description, tool)

            # 综合分数
            similarity * 0.6 + confidence * 0.4

            scored_tools.append(
                ToolMatch(
                    tool=tool,
                    similarity_score=similarity,
                    confidence=confidence,
                    reasoning=reasoning,
                )
            )

        # 排序
        scored_tools.sort(key=lambda m: m.similarity_score, reverse=True)

        return scored_tools[:top_k]

    async def _calculate_similarity(self, task_description: str, tool: Tool) -> float:
        """计算相似度"""
        # 简化实现:基于关键词匹配
        task_lower = task_description.lower()
        tool_desc_lower = tool.description.lower()

        # 关键词重叠
        task_words = set(task_lower.split())
        tool_words = set(tool_desc_lower.split()) | set(tool.tags)

        if not tool_words:
            return 0.0

        overlap = len(task_words & tool_words)
        similarity = overlap / len(task_words)

        # 考虑类别匹配
        # 这里简化,实际应该使用嵌入向量

        return min(1.0, similarity * 2)  # 放大信号

    async def _calculate_confidence(self, tool: Tool) -> float:
        """计算置信度"""
        metrics = self.performance_metrics[tool.tool_id]

        # 基于使用统计
        usage_factor = min(1.0, metrics["usage_count"] / 100)

        # 基于成功率
        success_factor = metrics["avg_score"]

        # 基于可用性
        availability_factor = 1.0 if tool.available else 0.0

        # 综合置信度
        confidence = usage_factor * 0.3 + success_factor * 0.5 + availability_factor * 0.2

        return confidence

    async def _generate_reasoning(self, task_description: str, tool: Tool) -> str:
        """生成匹配理由"""
        reasons = []

        # 类别匹配
        reasons.append(f"工具类别: {tool.category.value}")

        # 能力匹配
        if tool.capabilities:
            reasons.append(f"核心能力: {', '.join(tool.capabilities[:3])}")

        # 性能指标
        if tool.usage_count > 0:
            reasons.append(f"使用次数: {tool.usage_count}, 成功率: {tool.success_rate:.1%}")

        # 语义相似
        task_words = set(task_description.lower().split())
        tool_words = set(tool.description.lower().split()) | set(tool.tags)
        overlap = task_words & tool_words
        if overlap:
            reasons.append(f"关键词匹配: {', '.join(list(overlap)[:3])}")

        return "; ".join(reasons)

    async def record_tool_usage(self, tool_id: str, success: bool, response_time: float):
        """记录工具使用"""
        tool = self.tools.get(tool_id)
        if not tool:
            return

        # 更新工具统计
        tool.usage_count += 1
        tool.avg_response_time = tool.avg_response_time * 0.9 + response_time * 0.1

        # 更新性能指标
        metrics = self.performance_metrics[tool_id]
        metrics["usage_count"] += 1

        if success:
            metrics["success_count"] += 1

        metrics["avg_score"] = metrics["avg_score"] * 0.9 + (1.0 if success else 0.0) * 0.1
        metrics["avg_time"] = metrics["avg_time"] * 0.9 + response_time * 0.1

        # 记录历史
        self.usage_history.append(
            {
                "tool_id": tool_id,
                "timestamp": datetime.now(),
                "success": success,
                "response_time": response_time,
            }
        )

        logger.debug(f"📊 工具使用已记录: {tool_id}")

    async def recommend_tools(
        self, context: dict[str, Any], exclude: list[str] | None = None
    ) -> list[Tool]:
        """基于上下文推荐工具"""
        task = context.get("task", "")
        context.get("previous_tools", [])

        # 发现工具
        matches = await self.discover_tools(task)

        # 过滤已使用的工具
        exclude = exclude or []
        recommendations = [match.tool for match in matches if match.tool.tool_id not in exclude]

        return recommendations[:3]

    async def get_tool_analytics(self) -> dict[str, Any]:
        """获取工具分析"""
        return {
            "total_tools": len(self.tools),
            "by_category": {
                category.value: len(tool_ids) for category, tool_ids in self.by_category.items()
            },
            "most_used": sorted(
                [(tid, tool.usage_count) for tid, tool in self.tools.items()],
                key=lambda x: x[1],
                reverse=True,
            )[:10],
            "highest_success_rate": sorted(
                [(tid, tool.success_rate) for tid, tool in self.tools.items()],
                key=lambda x: x[1],
                reverse=True,
            )[:10],
            "recent_usage": len(self.usage_history),
            "avg_performance": (
                np.mean([m["avg_score"] for m in self.performance_metrics.values()])
                if self.performance_metrics
                else 0
            ),
        }


# 导出便捷函数
_tool_discovery: IntelligentToolDiscovery | None = None


def get_tool_discovery() -> IntelligentToolDiscovery:
    """获取工具发现引擎单例"""
    global _tool_discovery
    if _tool_discovery is None:
        _tool_discovery = IntelligentToolDiscovery()
    return _tool_discovery
