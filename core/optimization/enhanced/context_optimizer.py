#!/usr/bin/env python3
from __future__ import annotations
"""
上下文优化器 (Context Optimizer)
智能上下文管理和压缩,最大化上下文利用率

作者: 小诺·双鱼公主
版本: v2.0.0
优化目标: 上下文利用率 78% → 88%
"""

import logging
import re
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ContextType(str, Enum):
    """上下文类型"""

    CONVERSATION = "conversation"  # 对话历史
    KNOWLEDGE = "knowledge"  # 知识库
    MEMORY = "memory"  # 记忆
    STATE = "state"  # 状态
    METADATA = "metadata"  # 元数据


class ContextPriority(str, Enum):
    """上下文优先级"""

    CRITICAL = "critical"  # 关键上下文
    HIGH = "high"  # 高优先级
    MEDIUM = "medium"  # 中等优先级
    LOW = "low"  # 低优先级


@dataclass
class ContextItem:
    """上下文项"""

    item_id: str
    content: Any
    context_type: ContextType
    priority: ContextPriority
    tokens: int
    relevance_score: float  # 相关性得分 (0-1)
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __lt__(self, other):
        """用于排序(优先级高、相关性高在前)"""
        priority_order = {
            ContextPriority.CRITICAL: 4,
            ContextPriority.HIGH: 3,
            ContextPriority.MEDIUM: 2,
            ContextPriority.LOW: 1,
        }
        return (priority_order.get(self.priority, 0) * 1000 + self.relevance_score * 100) > (
            priority_order.get(other.priority, 0) * 1000 + other.relevance_score * 100
        )


@dataclass
class ContextCompression:
    """上下文压缩"""

    original_tokens: int
    compressed_tokens: int
    compression_ratio: float
    preserved_items: list[str]
    removed_items: list[str]
    technique: str


class ContextOptimizer:
    """
    上下文优化器

    功能:
    1. 智能上下文选择
    2. 上下文压缩
    3. 相关性评估
    4. 访问模式分析
    5. 动态优先级调整
    """

    def __init__(self, max_tokens: int = 8000):
        self.name = "上下文优化器"
        self.version = "2.0.0"
        self.max_tokens = max_tokens

        # 上下文存储
        self.context_items: dict[str, ContextItem] = {}

        # 上下文历史(按类型分组)
        self.context_by_type: dict[ContextType, list[str]] = {
            ctx_type: [] for ctx_type in ContextType
        }

        # 访问历史
        self.access_history: deque = deque(maxlen=1000)

        # 统计信息
        self.stats = {
            "total_items": 0,
            "total_tokens": 0,
            "utilization_rate": 0.0,
            "avg_relevance": 0.0,
            "compression_count": 0,
            "avg_compression_ratio": 0.0,
        }

        logger.info(f"✅ {self.name} 初始化完成 (最大Token: {max_tokens})")

    async def add_context(
        self,
        item_id: str,
        content: Any,
        context_type: ContextType,
        priority: ContextPriority = ContextPriority.MEDIUM,
        metadata: dict[str, Any] | None = None,
    ):
        """
        添加上下文项

        Args:
            item_id: 项ID
            content: 内容
            context_type: 类型
            priority: 优先级
            metadata: 元数据
        """
        # 估算Token数量
        tokens = self._estimate_tokens(content)

        # 计算相关性(简化版)
        relevance_score = self._compute_relevance(content, context_type)

        item = ContextItem(
            item_id=item_id,
            content=content,
            context_type=context_type,
            priority=priority,
            tokens=tokens,
            relevance_score=relevance_score,
            metadata=metadata or {},
        )

        self.context_items[item_id] = item
        self.context_by_type[context_type].append(item_id)

        self.stats["total_items"] += 1
        self.stats["total_tokens"] += tokens

        logger.debug(f"📝 添加上下文: {item_id} ({tokens} tokens)")

        # 检查是否需要压缩
        await self._check_and_compress()

    def _estimate_tokens(self, content: Any) -> int:
        """估算Token数量"""
        if isinstance(content, str):
            # 简化版:按字符数估算(中文约2字符=1token)
            return len(content) // 2
        elif isinstance(content, dict):
            # 估算字典的Token数
            text = str(content)
            return len(text) // 2
        elif isinstance(content, list):
            return sum(self._estimate_tokens(item) for item in content)
        else:
            return len(str(content)) // 2

    def _compute_relevance(self, content: Any, context_type: ContextType) -> float:
        """计算相关性得分"""
        # 简化版:基于类型和内容长度
        base_score = {
            ContextType.CONVERSATION: 0.9,
            ContextType.KNOWLEDGE: 0.7,
            ContextType.MEMORY: 0.8,
            ContextType.STATE: 0.6,
            ContextType.METADATA: 0.4,
        }.get(context_type, 0.5)

        # 根据内容长度调整
        content_len = len(str(content))
        length_factor = min(1.0, content_len / 1000)

        return base_score * (0.7 + 0.3 * length_factor)

    async def _check_and_compress(self):
        """检查并压缩上下文"""
        total_tokens = sum(item.tokens for item in self.context_items.values())

        if total_tokens > self.max_tokens:
            await self.compress_context()

    async def compress_context(self, target_tokens: int | None = None) -> ContextCompression:
        """
        压缩上下文

        Args:
            target_tokens: 目标Token数

        Returns:
            压缩结果
        """
        target_tokens = target_tokens or int(self.max_tokens * 0.8)

        original_tokens = sum(item.tokens for item in self.context_items.values())

        # 1. 按优先级和相关性排序
        sorted_items = sorted(
            self.context_items.values(),
            key=lambda x: (-_priority_value(x.priority), -x.relevance_score, -x.access_count),
        )

        # 2. 选择要保留的项
        preserved_items = []
        removed_items = []
        current_tokens = 0

        for item in sorted_items:
            if current_tokens + item.tokens <= target_tokens:
                preserved_items.append(item.item_id)
                current_tokens += item.tokens
            else:
                removed_items.append(item.item_id)

        # 3. 移除低优先级项
        for item_id in removed_items:
            await self._remove_context(item_id)

        compressed_tokens = sum(self.context_items[item_id].tokens for item_id in preserved_items)

        compression_ratio = 1 - (compressed_tokens / original_tokens) if original_tokens > 0 else 0

        result = ContextCompression(
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            compression_ratio=compression_ratio,
            preserved_items=preserved_items,
            removed_items=removed_items,
            technique="priority_based_selection",
        )

        # 更新统计
        self.stats["compression_count"] += 1
        self.stats["avg_compression_ratio"] = (
            self.stats["avg_compression_ratio"] * (self.stats["compression_count"] - 1)
            + compression_ratio
        ) / self.stats["compression_count"]

        logger.info(
            f"🗜️ 上下文已压缩: {original_tokens} → {compressed_tokens} tokens "
            f"({compression_ratio:.1%} 压缩率)"
        )

        return result

    async def _remove_context(self, item_id: str):
        """移除上下文项"""
        if item_id in self.context_items:
            item = self.context_items[item_id]
            del self.context_items[item_id]

            # 从类型列表中移除
            if item_id in self.context_by_type[item.context_type]:
                self.context_by_type[item.context_type].remove(item_id)

            # 更新统计
            self.stats["total_items"] -= 1
            self.stats["total_tokens"] -= item.tokens

    async def get_optimal_context(
        self, query: str, max_tokens: int | None = None
    ) -> list[ContextItem]:
        """
        获取最优上下文

        Args:
            query: 查询
            max_tokens: 最大Token数

        Returns:
            上下文项列表
        """
        max_tokens = max_tokens or self.max_tokens

        # 1. 计算与查询的相关性
        query_relevance = self._compute_query_relevance(query)

        # 2. 更新相关性得分
        for item_id, relevance in query_relevance.items():
            if item_id in self.context_items:
                item = self.context_items[item_id]
                # 混合原有相关性和查询相关性
                item.relevance_score = item.relevance_score * 0.6 + relevance * 0.4

        # 3. 按综合得分排序
        scored_items = [
            (item_id, self._compute_comprehensive_score(item))
            for item_id, item in self.context_items.items()
        ]

        scored_items.sort(key=lambda x: x[1], reverse=True)

        # 4. 选择Top-K直到达到Token限制
        selected_items = []
        total_tokens = 0

        for item_id, score in scored_items:
            item = self.context_items[item_id]
            if total_tokens + item.tokens <= max_tokens:
                selected_items.append(item)
                total_tokens += item.tokens

                # 更新访问统计
                item.access_count += 1
                item.last_accessed = datetime.now()

                # 记录访问历史
                self.access_history.append(
                    {"item_id": item_id, "timestamp": datetime.now(), "score": score}
                )
            else:
                break

        # 更新利用率
        self.stats["utilization_rate"] = total_tokens / max_tokens if max_tokens > 0 else 0
        self.stats["avg_relevance"] = (
            sum(item.relevance_score for item in selected_items) / len(selected_items)
            if selected_items
            else 0
        )

        logger.debug(
            f"🎯 选择 {len(selected_items)} 个上下文项 "
            f"({total_tokens}/{max_tokens} tokens, 利用率: {self.stats['utilization_rate']:.1%})"
        )

        return selected_items

    def _compute_query_relevance(self, query: str) -> dict[str, float]:
        """计算查询相关性"""
        relevance = {}
        query_lower = query.lower()
        query_words = set(re.findall(r"\w+", query_lower))

        for item_id, item in self.context_items.items():
            content_str = str(item.content).lower()
            content_words = set(re.findall(r"\w+", content_str))

            # 计算词重叠度
            overlap = len(query_words & content_words)
            union = len(query_words | content_words)

            # Jaccard相似度
            similarity = overlap / union if union > 0 else 0

            # 优先级加成
            priority_bonus = {
                ContextPriority.CRITICAL: 0.3,
                ContextPriority.HIGH: 0.2,
                ContextPriority.MEDIUM: 0.1,
                ContextPriority.LOW: 0.0,
            }.get(item.priority, 0.0)

            relevance[item_id] = min(1.0, similarity + priority_bonus)

        return relevance

    def _compute_comprehensive_score(self, item: ContextItem) -> float:
        """计算综合得分"""
        # 综合考虑多个因素
        priority_factor = _priority_value(item.priority) / 4
        relevance_factor = item.relevance_score
        access_factor = min(1.0, item.access_count / 100)

        # 时间衰减(最近访问的得分更高)
        time_factor = 1.0
        if item.last_accessed:
            days_since_access = (datetime.now() - item.last_accessed).days
            time_factor = max(0.1, 1 - days_since_access / 30)

        comprehensive_score = (
            priority_factor * 0.3
            + relevance_factor * 0.4
            + access_factor * 0.15
            + time_factor * 0.15
        )

        return comprehensive_score

    async def optimize_for_conversation(
        self, conversation_history: list[dict[str, Any]], max_turns: int = 10
    ) -> list[dict[str, Any]]:
        """
        优化对话上下文

        Args:
            conversation_history: 对话历史
            max_turns: 最大轮数

        Returns:
            优化后的对话历史
        """
        if len(conversation_history) <= max_turns:
            return conversation_history

        # 保留最近的轮数
        recent_turns = conversation_history[-max_turns:]

        # 从早期轮次中选择重要的
        early_turns = conversation_history[:-max_turns]
        important_turns = []

        for turn in early_turns:
            # 简化版:基于关键词和长度判断重要性
            content = str(turn.get("content", ""))
            if len(content) > 100 or any(
                keyword in content.lower() for keyword in ["重要", "关键", "必须", "记住"]
            ):
                important_turns.append(turn)

        # 合并
        optimized = important_turns + recent_turns

        logger.info(f"💬 对话上下文优化: {len(conversation_history)} → {len(optimized)} 轮")

        return optimized

    def get_utilization_report(self) -> dict[str, Any]:
        """获取利用率报告"""
        # 按类型统计
        type_stats = {}
        for ctx_type, item_ids in self.context_by_type.items():
            items = [self.context_items[iid] for iid in item_ids if iid in self.context_items]
            type_stats[ctx_type.value] = {
                "count": len(items),
                "tokens": sum(item.tokens for item in items),
                "avg_relevance": (
                    sum(item.relevance_score for item in items) / len(items) if items else 0
                ),
            }

        return {
            "name": self.name,
            "version": self.version,
            "utilization": {
                "current_tokens": self.stats["total_tokens"],
                "max_tokens": self.max_tokens,
                "utilization_rate": self.stats["utilization_rate"],
                "avg_relevance": self.stats["avg_relevance"],
            },
            "type_breakdown": type_stats,
            "compression": {
                "count": self.stats["compression_count"],
                "avg_ratio": self.stats["avg_compression_ratio"],
            },
            "statistics": self.stats,
        }


def _priority_value(priority: ContextPriority) -> int:
    """获取优先级数值"""
    return {
        ContextPriority.CRITICAL: 4,
        ContextPriority.HIGH: 3,
        ContextPriority.MEDIUM: 2,
        ContextPriority.LOW: 1,
    }.get(priority, 0)


# 全局单例
_context_optimizer_instance: ContextOptimizer | None = None


def get_context_optimizer() -> ContextOptimizer:
    """获取上下文优化器实例"""
    global _context_optimizer_instance
    if _context_optimizer_instance is None:
        _context_optimizer_instance = ContextOptimizer()
    return _context_optimizer_instance
