#!/usr/bin/env python3
"""
增强语义工具发现引擎
Enhanced Semantic Tool Discovery Engine

提升工具选择的语义理解深度:
1. 基于向量嵌入的深度语义匹配
2. 多阶段匹配策略(粗匹配→精匹配→重排序)
3. 上下文感知的工具推荐
4. 工具使用模式学习
5. 实时反馈优化

作者: Athena平台团队
创建时间: 2025-12-27
版本: v2.0.0 "深度语义理解"
"""

import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


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
    compatibility: dict[str, float] = field(default_factory=dict)  # 工具兼容性


@dataclass
class SemanticMatch:
    """语义匹配结果"""

    tool_id: str
    score: float
    stage: MatchStage
    reasoning: str
    confidence_factors: dict[str, float] = field(default_factory=dict)
    alternative_tools: list[str] = field(default_factory=list)


class EnhancedSemanticToolDiscovery:
    """
    增强语义工具发现引擎

    核心改进:
    1. 向量嵌入语义匹配(替代关键词匹配)
    2. 多阶段匹配策略(提高准确率)
    3. 上下文感知推荐(考虑使用历史)
    4. 模式学习(从历史中学习)
    5. 实时反馈优化
    """

    def __init__(self, embedding_model=None):
        # 工具注册表
        self.tools: dict[str, Any] = {}

        # 向量嵌入缓存
        self.tool_embeddings: dict[str, np.ndarray] = {}

        # 工具上下文
        self.tool_contexts: dict[str, ToolContext] = defaultdict(ToolContext)

        # 语义匹配阈值
        self.coarse_threshold = 0.3  # 粗匹配阈值
        self.fine_threshold = 0.6  # 精匹配阈值

        # 匹配权重(可动态调整)
        self.semantic_weight = 0.5  # 语义相似度权重
        self.context_weight = 0.3  # 上下文权重
        self.performance_weight = 0.2  # 性能权重

        # 使用模式学习
        self.pattern_learning = True
        self.learning_rate = 0.1

        # 嵌入模型
        self.embedding_model = embedding_model

        logger.info("🧠 增强语义工具发现引擎初始化完成")

    async def register_tool(self, tool: Any) -> bool:
        """注册工具并计算嵌入向量"""
        tool_id = tool.tool_id
        self.tools[tool_id] = tool

        # 计算语义嵌入
        embedding = await self._compute_tool_embedding(tool)
        self.tool_embeddings[tool_id] = embedding

        # 初始化工具上下文
        self.tool_contexts[tool_id] = ToolContext()

        logger.info(f"✅ 工具已注册: {tool.name} (嵌入维度: {len(embedding)})")
        return True

    async def discover_tools(
        self,
        task_description: str,
        context: dict[str, Any] | None = None,
        top_k: int = 5,
        enable_reranking: bool = True,
    ) -> list[SemanticMatch]:
        """
        多阶段智能工具发现

        Args:
            task_description: 任务描述
            context: 上下文信息
            top_k: 返回前K个结果
            enable_reranking: 是否启用重排序

        Returns:
            匹配的工具列表
        """
        # 阶段1: 粗匹配(快速过滤)
        coarse_matches = await self._coarse_match(task_description, context)
        logger.debug(f"🔍 粗匹配: {len(coarse_matches)} 个候选工具")

        if not coarse_matches:
            return []

        # 阶段2: 精匹配(语义计算)
        fine_matches = await self._fine_match(task_description, coarse_matches, context)
        logger.debug(f"🎯 精匹配: {len(fine_matches)} 个候选工具")

        # 阶段3: 重排序(上下文优化)
        if enable_reranking:
            final_matches = await self._rerank(task_description, fine_matches, context)
        else:
            final_matches = fine_matches

        return final_matches[:top_k]

    async def _coarse_match(
        self, task_description: str, context: dict[str, Any]
    ) -> list[str]:
        """
        粗匹配阶段:快速过滤明显不相关的工具

        策略:
        1. 类别快速匹配
        2. 关键词粗过滤
        3. 可用性检查
        """
        candidates = []

        task_lower = task_description.lower()
        task_words = set(task_lower.split())

        for tool_id, tool in self.tools.items():
            # 可用性检查
            if not tool.available or tool.deprecated:
                continue

            # 类别快速匹配
            category_match = self._quick_category_match(task_lower, tool.category)

            # 能力粗匹配
            capability_match = any(cap.lower() in task_lower for cap in tool.capabilities)

            # 关键词粗匹配
            keyword_overlap = len(task_words & set(tool.tags)) > 0

            # 任一条件满足即可进入候选
            if category_match or capability_match or keyword_overlap:
                candidates.append(tool_id)

        return candidates

    async def _fine_match(
        self, task_description: str, candidate_ids: list[str], context: dict[str, Any]
    ) -> list[SemanticMatch]:
        """
        精匹配阶段:计算语义相似度

        策略:
        1. 计算任务嵌入向量
        2. 计算余弦相似度
        3. 综合多个因素评分
        """
        # 计算任务嵌入
        task_embedding = await self._compute_task_embedding(task_description)

        matches = []

        for tool_id in candidate_ids:
            tool = self.tools[tool_id]
            tool_embedding = self.tool_embeddings[tool_id]

            # 计算语义相似度
            semantic_similarity = self._cosine_similarity(task_embedding, tool_embedding)

            # 过滤低相似度
            if semantic_similarity < self.fine_threshold:
                continue

            # 计算置信度因素
            confidence_factors = await self._compute_confidence_factors(
                tool_id, task_description, context
            )

            # 综合评分
            score = (
                semantic_similarity * self.semantic_weight
                + confidence_factors.get("context_score", 0.5) * self.context_weight
                + confidence_factors.get("performance_score", 0.5) * self.performance_weight
            )

            # 生成匹配理由
            reasoning = await self._generate_match_reasoning(
                tool, semantic_similarity, confidence_factors
            )

            matches.append(
                SemanticMatch(
                    tool_id=tool_id,
                    score=score,
                    stage=MatchStage.FINE,
                    reasoning=reasoning,
                    confidence_factors=confidence_factors,
                )
            )

        # 排序
        matches.sort(key=lambda m: m.score, reverse=True)
        return matches

    async def _rerank(
        self, task_description: str, matches: list[SemanticMatch], context: dict[str, Any]
    ) -> list[SemanticMatch]:
        """
        重排序阶段:基于上下文和模式学习优化

        考虑因素:
        1. 最近使用历史
        2. 工具兼容性
        3. 成功/失败模式
        4. 上下文连贯性
        """
        if not context:
            return matches

        reranked_matches = []

        for match in matches:
            tool_id = match.tool_id
            self.tool_contexts[tool_id]

            # 上下文连贯性评分
            context_score = await self._compute_context_coherence(tool_id, context)

            # 模式学习评分
            pattern_score = await self._compute_pattern_score(tool_id, task_description)

            # 兼容性评分
            compatibility_score = await self._compute_compatibility(
                tool_id, context.get("previous_tools", [])
            )

            # 调整分数
            adjusted_score = (
                match.score * 0.7
                + context_score * 0.15
                + pattern_score * 0.1
                + compatibility_score * 0.05
            )

            # 创建新的匹配结果
            reranked_match = SemanticMatch(
                tool_id=match.tool_id,
                score=adjusted_score,
                stage=MatchStage.RERANK,
                reasoning=f"{match.reasoning}; 重排序: +{adjusted_score - match.score:.3f}",
                confidence_factors={
                    **match.confidence_factors,
                    "context_score": context_score,
                    "pattern_score": pattern_score,
                    "compatibility_score": compatibility_score,
                },
            )

            reranked_matches.append(reranked_match)

        # 重新排序
        reranked_matches.sort(key=lambda m: m.score, reverse=True)
        return reranked_matches

    async def _compute_tool_embedding(self, tool: Any) -> np.ndarray:
        """
        计算工具的语义嵌入向量

        组合多个文本信息:
        1. 工具名称
        2. 工具描述
        3. 能力列表
        4. 标签
        """
        # 组合文本
        text_parts = [tool.name, tool.description, " ".join(tool.capabilities), " ".join(tool.tags)]

        combined_text = " ".join(text_parts)

        # 使用嵌入模型(这里简化,实际应该使用BERT等)
        if self.embedding_model:
            embedding = await self.embedding_model.encode(combined_text)
        else:
            # 简化实现:字符编码的hash映射
            embedding = self._simple_embedding(combined_text, dim=384)

        # 归一化
        embedding = embedding / (np.linalg.norm(embedding) + 1e-8)

        return embedding

    async def _compute_task_embedding(self, task_description: str) -> np.ndarray:
        """计算任务的语义嵌入向量"""
        if self.embedding_model:
            embedding = await self.embedding_model.encode(task_description)
        else:
            embedding = self._simple_embedding(task_description, dim=384)

        # 归一化
        embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
        return embedding

    def _simple_embedding(self, text: str, dim: int = 384) -> np.ndarray:
        """
        简化的嵌入实现(用于演示)

        实际应该使用:
        - sentence-transformers
        - BERT
        - 或其他预训练模型
        """
        # 简化实现:基于字符的hash嵌入
        text_bytes = text.encode("utf-8")
        embedding = np.zeros(dim)

        for i, byte_val in enumerate(text_bytes):
            embedding[i % dim] += byte_val / 255.0

        # 添加一些随机性模拟语义
        np.random.seed(hash(text) % (2**32))
        embedding += np.random.randn(dim) * 0.1

        return embedding

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2) + 1e-8)

    def _quick_category_match(self, task: str, category) -> bool:
        """快速类别匹配"""
        category_keywords = {
            "search": ["搜索", "查找", "检索", "search", "find"],
            "analysis": ["分析", "解析", "analysis", "analyze"],
            "generation": ["生成", "创建", "generate", "create"],
            "automation": ["自动化", "自动", "automation", "auto"],
            "database": ["数据库", "存储", "database", "store"],
        }

        keywords = category_keywords.get(category.value, [])
        return any(kw in task for kw in keywords)

    async def _compute_confidence_factors(
        self, tool_id: str, task_description: str, context: dict[str, Any]
    ) -> dict[str, float]:
        """计算置信度因素"""
        tool = self.tools[tool_id]
        self.tool_contexts[tool_id]

        # 性能评分
        performance_score = tool.success_rate

        # 使用频率评分
        usage_score = min(1.0, tool.usage_count / 100)

        # 上下文评分
        context_score = 0.5
        if context:
            recent_tools = context.get("previous_tools", [])
            if tool_id in recent_tools:
                # 最近使用过,降低优先级(避免重复)
                context_score = 0.3
            else:
                context_score = 0.7

        return {
            "performance_score": performance_score,
            "usage_score": usage_score,
            "context_score": context_score,
        }

    async def _compute_context_coherence(self, tool_id: str, context: dict[str, Any]) -> float:
        """计算上下文连贯性"""
        tool_context = self.tool_contexts[tool_id]

        # 检查与最近使用的工具的兼容性
        recent_tools = context.get("previous_tools", [])
        if not recent_tools:
            return 0.5

        compatibility_scores = [
            tool_context.compatibility.get(rt, 0.5) for rt in recent_tools if rt != tool_id
        ]

        return np.mean(compatibility_scores) if compatibility_scores else 0.5

    async def _compute_pattern_score(self, tool_id: str, task_description: str) -> float:
        """基于历史模式计算评分"""
        tool_context = self.tool_contexts[tool_id]

        # 检查成功模式
        set(task_description.lower().split())

        pattern_score = 0.5
        for pattern, score in tool_context.success_patterns.items():
            if pattern in task_description.lower():
                pattern_score = max(pattern_score, score)

        # 检查失败模式(降低分数)
        for pattern, score in tool_context.failure_patterns.items():
            if pattern in task_description.lower():
                pattern_score = min(pattern_score, 1.0 - score)

        return pattern_score

    async def _compute_compatibility(self, tool_id: str, previous_tools: list[str]) -> float:
        """计算工具兼容性"""
        if not previous_tools:
            return 0.5

        tool_context = self.tool_contexts[tool_id]
        compatibility_scores = []

        for prev_tool in previous_tools:
            if prev_tool == tool_id:
                continue

            # 获取或计算兼容性
            compat = tool_context.compatibility.get(prev_tool, 0.5)
            compatibility_scores.append(compat)

        return np.mean(compatibility_scores) if compatibility_scores else 0.5

    async def _generate_match_reasoning(
        self, tool: Any, semantic_similarity: float, confidence_factors: dict[str, float]
    ) -> str:
        """生成匹配理由"""
        reasons = [
            f"语义相似度: {semantic_similarity:.2%}",
            f"成功率: {confidence_factors.get('performance_score', 0):.1%}",
            f"类别: {tool.category.value}",
        ]

        if tool.capabilities:
            reasons.append(f"能力: {', '.join(tool.capabilities[:2])}")

        return "; ".join(reasons)

    async def record_usage(
        self, tool_id: str, success: bool, context: dict[str, Any] | None = None
    ):
        """记录工具使用并学习模式"""
        tool_context = self.tool_contexts[tool_id]

        # 更新最近使用
        if context:
            task = context.get("task", "")
            tool_context.recent_usage.append(
                {"timestamp": datetime.now(), "task": task, "success": success}
            )

            # 学习成功/失败模式
            if self.pattern_learning:
                await self._learn_patterns(tool_id, task, success, context)

    async def _learn_patterns(
        self, tool_id: str, task: str, success: bool, context: dict[str, Any]
    ):
        """从使用中学习模式"""
        tool_context = self.tool_contexts[tool_id]

        # 提取关键短语
        task_words = task.lower().split()

        # 更新成功/失败模式
        for word in task_words:
            if len(word) < 3:  # 忽略太短的词
                continue

            if success:
                # 成功模式:增加正面关联
                current = tool_context.success_patterns.get(word, 0.5)
                tool_context.success_patterns[word] = (
                    current * (1 - self.learning_rate) + 1.0 * self.learning_rate
                )
            else:
                # 失败模式:增加负面关联
                current = tool_context.failure_patterns.get(word, 0.0)
                tool_context.failure_patterns[word] = (
                    current * (1 - self.learning_rate) + 1.0 * self.learning_rate
                )

        # 更新工具兼容性
        previous_tools = context.get("previous_tools", [])
        for prev_tool in previous_tools:
            if prev_tool == tool_id:
                continue

            current_compat = tool_context.compatibility.get(prev_tool, 0.5)
            new_compat = (
                current_compat * (1 - self.learning_rate)
                + (1.0 if success else 0.0) * self.learning_rate
            )

            tool_context.compatibility[prev_tool] = new_compat

    async def get_analytics(self) -> dict[str, Any]:
        """获取分析数据"""
        return {
            "total_tools": len(self.tools),
            "avg_embedding_dim": (
                np.mean([len(emb) for emb in self.tool_embeddings.values()])
                if self.tool_embeddings
                else 0
            ),
            "tools_with_patterns": sum(
                1
                for ctx in self.tool_contexts.values()
                if ctx.success_patterns or ctx.failure_patterns
            ),
            "pattern_learning_enabled": self.pattern_learning,
        }


# 导出便捷函数
_enhanced_discovery: EnhancedSemanticToolDiscovery | None = None


def get_enhanced_tool_discovery() -> EnhancedSemanticToolDiscovery:
    """获取增强工具发现引擎单例"""
    global _enhanced_discovery
    if _enhanced_discovery is None:
        _enhanced_discovery = EnhancedSemanticToolDiscovery()
    return _enhanced_discovery
