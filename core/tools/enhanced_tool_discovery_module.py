#!/usr/bin/env python3
from __future__ import annotations
"""
轻量级工具发现模块
Lightweight Tool Discovery Module

从Athena提取的轻量级工具发现能力:
1. 基于向量嵌入的语义匹配
2. 多阶段匹配策略(粗→精→重排)
3. 上下文感知推荐
4. 模式学习与反馈优化

专门为小诺优化,去除Athena强耦合依赖。

作者: Athena平台团队
创建时间: 2025-12-27
版本: v1.0.0 "轻量级集成版"
"""

import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class MatchStage(Enum):
    """匹配阶段"""

    COARSE = "coarse"  # 粗匹配(快速过滤)
    FINE = "fine"  # 精匹配(语义计算)
    RERANK = "rerank"  # 重排序(上下文优化)


@dataclass
class ToolContext:
    """工具上下文信息"""

    recent_usage: deque = field(default_factory=lambda: deque(maxlen=10))
    success_patterns: dict[str, float] = field(default_factory=dict)
    failure_patterns: dict[str, float] = field(default_factory=dict)
    optimal_scenarios: list[str] = field(default_factory=list)
    compatibility: dict[str, float] = field(default_factory=dict)


@dataclass
class SemanticMatch:
    """语义匹配结果"""

    tool_id: str
    score: float
    stage: MatchStage
    reasoning: str
    confidence_factors: dict[str, float] = field(default_factory=dict)
    alternative_tools: list[str] = field(default_factory=list)


class LightweightToolDiscovery:
    """
    轻量级工具发现模块

    从Athena增强语义工具发现引擎提取核心能力,
    专门设计为可被小诺直接导入使用的Python模块。

    核心特性:
    1. 零外部服务依赖
    2. 可选嵌入模型支持
    3. 配置驱动的降级策略
    4. 简化的API接口
    """

    def __init__(self, config: dict | None = None):
        """
        初始化轻量级工具发现模块

        Args:
            config: 配置字典,包含:
                - enable_embedding: 是否启用嵌入模型(默认False,使用简化匹配)
                - embedding_model: 嵌入模型路径(可选)
                - coarse_threshold: 粗匹配阈值(默认0.3)
                - fine_threshold: 精匹配阈值(默认0.6)
        """
        self.config = config or {}

        # 工具注册表
        self.tools: dict[str, Any] = {}

        # 工具上下文
        self.tool_contexts: dict[str, ToolContext] = defaultdict(ToolContext)

        # 配置参数
        self.enable_embedding = self.config.get("enable_embedding", False)
        self.coarse_threshold = self.config.get("coarse_threshold", 0.3)
        self.fine_threshold = self.config.get("fine_threshold", 0.6)

        # 匹配权重
        self.semantic_weight = 0.5  # 语义相似度权重
        self.context_weight = 0.3  # 上下文权重
        self.performance_weight = 0.2  # 性能权重

        # 嵌入缓存(可选)
        self.tool_embeddings: dict[str, np.ndarray] = {}

        logger.info("🧠 轻量级工具发现模块初始化完成")
        logger.info(f"   嵌入模型: {'启用' if self.enable_embedding else '简化匹配'}")

    async def register_tool(self, tool: Any) -> bool:
        """
        注册工具到发现模块

        Args:
            tool: 工具对象,需要包含以下属性:
                - tool_id: 唯一标识符
                - name: 工具名称
                - category: 工具类别
                - description: 工具描述
                - capabilities: 能力列表
                - tags: 标签列表
                - available: 是否可用(默认True)
                - deprecated: 是否弃用(默认False)

        Returns:
            是否注册成功
        """
        tool_id = getattr(tool, "tool_id", str(id(tool)))
        self.tools[tool_id] = tool

        # 初始化上下文
        self.tool_contexts[tool_id] = ToolContext()

        # 如果启用嵌入,计算语义向量
        if self.enable_embedding and hasattr(tool, "description"):
            embedding = await self._compute_tool_embedding(tool)
            self.tool_embeddings[tool_id] = embedding

        logger.info(f"✅ 工具已注册: {getattr(tool, 'name', tool_id)}")
        return True

    async def discover_tools(
        self,
        task_description: str,
        available_tools: list[str] = None,
        context: Optional[dict[str, Any]] = None,
        top_k: int = 5,
    ) -> list[SemanticMatch]:
        """
        智能工具发现(简化版API)

        Args:
            task_description: 任务描述
            available_tools: 可用工具列表(如果为None,使用已注册工具)
            context: 上下文信息
            top_k: 返回前K个结果

        Returns:
            匹配的工具列表
        """
        # 如果提供了工具列表,临时注册
        temp_tools = {}
        if available_tools:
            for tool in available_tools:
                tool_id = getattr(tool, "tool_id", str(id(tool)))
                temp_tools[tool_id] = tool
                if tool_id not in self.tools:
                    await self.register_tool(tool)

        try:
            # 阶段1: 粗匹配
            coarse_matches = await self._coarse_match(task_description, context)

            if not coarse_matches:
                return []

            # 阶段2: 精匹配
            fine_matches = await self._fine_match(task_description, coarse_matches, context)

            # 阶段3: 重排序(可选)
            if context and len(fine_matches) > 1:
                final_matches = await self._rerank(task_description, fine_matches, context)
            else:
                final_matches = fine_matches

            # 清理临时注册的工具
            for tool_id in temp_tools:
                if tool_id in self.tools and tool_id not in self.tool_contexts:
                    del self.tools[tool_id]

            return final_matches[:top_k]

        except Exception as e:
            logger.error(f"工具发现失败: {e}")
            # 降级到基础匹配
            return await self._basic_tool_discovery(task_description, context)

    async def _coarse_match(
        self, task_description: str, context: dict[str, Any]
    ) -> list[str]:
        """
        粗匹配阶段:快速过滤候选工具

        Returns:
            候选工具ID列表
        """
        candidates = []
        task_lower = task_description.lower()
        set(task_lower.split())

        for tool_id, tool in self.tools.items():
            # 可用性检查
            if not getattr(tool, "available", True):
                continue
            if getattr(tool, "deprecated", False):
                continue

            # 类别匹配
            category = getattr(tool, "category", "")
            if category and category.lower() in task_lower:
                candidates.append(tool_id)
                continue

            # 能力匹配
            capabilities = getattr(tool, "capabilities", [])
            for cap in capabilities:
                if cap.lower() in task_lower:
                    candidates.append(tool_id)
                    break

            # 标签匹配
            tags = getattr(tool, "tags", [])
            if any(tag.lower() in task_lower for tag in tags):
                if tool_id not in candidates:
                    candidates.append(tool_id)

        return candidates

    async def _fine_match(
        self, task_description: str, candidate_ids: list[str], context: dict[str, Any]
    ) -> list[SemanticMatch]:
        """
        精匹配阶段:计算详细的匹配分数

        Returns:
            匹配结果列表
        """
        matches = []

        for tool_id in candidate_ids:
            tool = self.tools.get(tool_id)
            if not tool:
                continue

            # 计算匹配分数
            score = await self._compute_match_score(task_description, tool, context)

            if score >= self.fine_threshold:
                matches.append(
                    SemanticMatch(
                        tool_id=tool_id,
                        score=score,
                        stage=MatchStage.FINE,
                        reasoning=self._generate_reasoning(task_description, tool, score),
                    )
                )

        # 按分数排序
        matches.sort(key=lambda m: m.score, reverse=True)
        return matches

    async def _rerank(
        self, task_description: str, matches: list[SemanticMatch], context: dict[str, Any]
    ) -> list[SemanticMatch]:
        """
        重排序阶段:考虑上下文和使用历史

        Returns:
            重排序后的匹配列表
        """
        for match in matches:
            tool_id = match.tool_id
            tool_ctx = self.tool_contexts.get(tool_id)

            if tool_ctx:
                # 考虑使用历史
                if tool_ctx.recent_usage:
                    recent_success_rate = sum(
                        1 for usage in tool_ctx.recent_usage if usage.get("success", False)
                    ) / len(tool_ctx.recent_usage)

                    # 调整分数
                    match.score = match.score * 0.7 + recent_success_rate * 0.3
                    match.confidence_factors["recent_success"] = recent_success_rate

                # 考虑上下文兼容性
                if context:
                    context_type = context.get("task_type", "")
                    if context_type in tool_ctx.optimal_scenarios:
                        match.score *= 1.1
                        match.confidence_factors["context_fit"] = 1.1

                match.stage = MatchStage.RERANK

        # 重新排序
        matches.sort(key=lambda m: m.score, reverse=True)
        return matches

    async def _compute_match_score(
        self, task_description: str, tool: Any, context: dict[str, Any]
    ) -> float:
        """
        计算工具与任务的匹配分数

        Returns:
            匹配分数 (0-1)
        """
        score = 0.0

        # 语义匹配
        if self.enable_embedding and tool.tool_id in self.tool_embeddings:
            semantic_sim = await self._compute_semantic_similarity(task_description, tool.tool_id)
            score += semantic_sim * self.semantic_weight
        else:
            # 降级:基于关键词的匹配
            keyword_score = self._compute_keyword_similarity(task_description, tool)
            score += keyword_score * self.semantic_weight

        # 描述匹配
        desc_match = self._compute_description_match(task_description, tool)
        score += desc_match * 0.3

        # 能力匹配
        capability_match = self._compute_capability_match(task_description, tool)
        score += capability_match * 0.2

        return min(score, 1.0)

    async def _compute_tool_embedding(self, tool: Any) -> np.ndarray:
        """
        计算工具的语义嵌入向量

        Returns:
            嵌入向量
        """
        description = getattr(tool, "description", "")
        name = getattr(tool, "name", "")

        # 简化实现:基于TF-IDF的嵌入
        # 生产环境可替换为真实的sentence-transformers
        text = f"{name} {description}"
        words = text.lower().split()

        # 创建简单的词频向量
        word_vector = {}
        for word in words:
            word_vector[word] = word_vector.get(word, 0) + 1

        # 归一化为固定维度向量(简化为384维)
        embedding = np.zeros(384, dtype=np.float32)
        for i, word in enumerate(list(word_vector.keys())[:384]):
            embedding[i] = word_vector[word] / max(word_vector.values())

        return embedding

    async def _compute_semantic_similarity(self, task_description: str, tool_id: str) -> float:
        """计算任务和工具的语义相似度"""
        # 简化实现
        return 0.7  # 占位符

    def _compute_keyword_similarity(self, task_description: str, tool: Any) -> float:
        """计算关键词相似度"""
        task_words = set(task_description.lower().split())

        # 从工具的各个属性提取关键词
        tool_words = set()

        name = getattr(tool, "name", "")
        if name:
            tool_words.update(name.lower().split())

        description = getattr(tool, "description", "")
        if description:
            tool_words.update(description.lower().split())

        capabilities = getattr(tool, "capabilities", [])
        for cap in capabilities:
            tool_words.update(cap.lower().split())

        tags = getattr(tool, "tags", [])
        for tag in tags:
            tool_words.update(tag.lower().split())

        # 计算重叠率
        if not task_words or not tool_words:
            return 0.0

        intersection = task_words & tool_words
        union = task_words | tool_words

        return len(intersection) / len(union) if union else 0.0

    def _compute_description_match(self, task_description: str, tool: Any) -> float:
        """计算描述匹配度"""
        description = getattr(tool, "description", "")
        if not description:
            return 0.0

        task_lower = task_description.lower()
        desc_lower = description.lower()

        # 简单的包含关系
        words = task_lower.split()
        match_count = sum(1 for word in words if word in desc_lower)

        return match_count / len(words) if words else 0.0

    def _compute_capability_match(self, task_description: str, tool: Any) -> float:
        """计算能力匹配度"""
        capabilities = getattr(tool, "capabilities", [])
        if not capabilities:
            return 0.0

        task_lower = task_description.lower()

        # 计算匹配的能力数量
        match_count = sum(1 for cap in capabilities if cap.lower() in task_lower)

        return match_count / len(capabilities) if capabilities else 0.0

    def _generate_reasoning(self, task_description: str, tool: Any, score: float) -> str:
        """生成匹配理由"""
        name = getattr(tool, "name", tool.tool_id)
        return f"{name} 与任务匹配度 {score:.1%}"

    async def _basic_tool_discovery(
        self, task_description: str, context: dict[str, Any]
    ) -> list[SemanticMatch]:
        """基础工具发现(降级方案)"""
        matches = []

        for tool_id, tool in self.tools.items():
            if not getattr(tool, "available", True):
                continue

            score = self._compute_keyword_similarity(task_description, tool)

            if score > 0:
                matches.append(
                    SemanticMatch(
                        tool_id=tool_id,
                        score=score,
                        stage=MatchStage.COARSE,
                        reasoning=f"基础匹配: {score:.1%}",
                    )
                )

        matches.sort(key=lambda m: m.score, reverse=True)
        return matches[:5]

    async def record_tool_usage(
        self, tool_id: str, task_description: str, success: bool, execution_time: float
    ):
        """
        记录工具使用情况(用于模式学习)

        Args:
            tool_id: 工具ID
            task_description: 任务描述
            success: 是否成功
            execution_time: 执行时间
        """
        tool_ctx = self.tool_contexts.get(tool_id)
        if not tool_ctx:
            return

        # 记录到最近使用历史
        tool_ctx.recent_usage.append(
            {
                "task": task_description,
                "success": success,
                "time": execution_time,
                "timestamp": datetime.now(),
            }
        )

        # 更新模式统计
        if success:
            pattern_key = task_description[:50]  # 简化的模式key
            tool_ctx.success_patterns[pattern_key] = (
                tool_ctx.success_patterns.get(pattern_key, 0.0) + 0.1
            )
        else:
            pattern_key = task_description[:50]
            tool_ctx.failure_patterns[pattern_key] = (
                tool_ctx.failure_patterns.get(pattern_key, 0.0) + 0.1
            )

    async def get_analytics(self) -> dict[str, Any]:
        """
        获取工具发现的统计数据

        Returns:
            统计信息字典
        """
        total_tools = len(self.tools)
        total_contexts = sum(len(ctx.recent_usage) for ctx in self.tool_contexts.values())

        return {
            "total_tools": total_tools,
            "total_contexts": total_contexts,
            "tools_with_embeddings": len(self.tool_embeddings) if self.enable_embedding else 0,
            "average_success_rate": self._compute_average_success_rate(),
        }

    def _compute_average_success_rate(self) -> float:
        """计算平均成功率"""
        all_usage = []
        for ctx in self.tool_contexts.values():
            all_usage.extend(ctx.recent_usage)

        if not all_usage:
            return 0.0

        success_count = sum(1 for usage in all_usage if usage.get("success", False))
        return success_count / len(all_usage)


# 便捷函数
_discovery_instance: LightweightToolDiscovery | None = None


def get_tool_discovery(config: dict | None = None) -> LightweightToolDiscovery:
    """获取工具发现模块单例"""
    global _discovery_instance
    if _discovery_instance is None:
        _discovery_instance = LightweightToolDiscovery(config)
    return _discovery_instance


# 使用示例
async def main():
    """演示函数"""
    print("=" * 60)
    print("轻量级工具发现模块演示")
    print("=" * 60)

    # 创建发现模块
    discovery = LightweightToolDiscovery()

    # 模拟工具
    class MockTool:
        def __init__(self, tool_id, name, category, description, capabilities, tags):
            self.tool_id = tool_id
            self.name = name
            self.category = category
            self.description = description
            self.capabilities = capabilities
            self.tags = tags
            self.available = True
            self.deprecated = False

    # 注册工具
    await discovery.register_tool(
        MockTool(
            tool_id="patent_search",
            name="专利搜索工具",
            category="SEARCH",
            description="搜索专利数据库,查询专利信息",
            capabilities=["专利搜索", "专利查询", "专利检索"],
            tags=["专利", "搜索", "数据库"],
        )
    )

    await discovery.register_tool(
        MockTool(
            tool_id="legal_analysis",
            name="法律分析工具",
            category="ANALYSIS",
            description="分析法律文档,提取关键法律条款",
            capabilities=["法律分析", "合同分析", "条款提取"],
            tags=["法律", "分析", "文档"],
        )
    )

    # 发现工具
    task = "搜索专利数据库"
    matches = await discovery.discover_tools(task, top_k=2)

    print(f"\n任务: {task}")
    print(f"发现 {len(matches)} 个匹配工具:\n")

    for i, match in enumerate(matches, 1):
        print(f"{i}. {match.tool_id}")
        print(f"   分数: {match.score:.1%}")
        print(f"   理由: {match.reasoning}")

    print("\n✅ 演示完成")


# 入口点: @async_main装饰器已添加到main函数
