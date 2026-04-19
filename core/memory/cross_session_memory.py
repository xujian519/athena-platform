#!/usr/bin/env python3
from __future__ import annotations
"""
跨会话记忆管理器 - 第二阶段
Cross-Session Memory Manager - Phase 2

核心功能:
1. 跨会话信息检索
2. 长期记忆管理
3. 记忆关联分析
4. 记忆重要性评分

作者: 小诺·双鱼公主
版本: v1.0.0 "跨会话记忆"
创建: 2026-01-12
"""

import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """记忆类型"""

    USER_PREFERENCE = "user_preference"  # 用户偏好
    TASK_CONTEXT = "task_context"  # 任务上下文
    DOMAIN_KNOWLEDGE = "domain_knowledge"  # 领域知识
    CONVERSATION_PATTERN = "conversation_pattern"  # 对话模式
    ERROR_PATTERN = "error_pattern"  # 错误模式


class MemoryImportance(Enum):
    """记忆重要性"""

    CRITICAL = "critical"  # 关键记忆
    HIGH = "high"  # 高重要性
    MEDIUM = "medium"  # 中等重要性
    LOW = "low"  # 低重要性


@dataclass
class MemoryFragment:
    """记忆片段"""

    memory_id: str
    memory_type: MemoryType
    importance: MemoryImportance
    content: str
    keywords: list[str]
    entities: list[str]

    # 关联信息
    session_id: str
    user_id: str
    timestamp: datetime = field(default_factory=datetime.now)

    # 访问统计
    access_count: int = 0
    last_accessed: datetime | None = None

    # 关联记忆
    related_memories: list[str] = field(default_factory=list)

    # 元数据
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryQuery:
    """记忆查询"""

    query_id: str
    query_text: str
    query_type: str  # keyword, semantic, entity, temporal
    filters: dict[str, Any]
    max_results: int
    min_importance: MemoryImportance | None = None


@dataclass
class MemoryRetrievalResult:
    """记忆检索结果"""

    query: MemoryQuery
    fragments: list[MemoryFragment]
    total_found: int
    retrieval_time: float
    relevance_scores: list[float]
    reasoning: str


class CrossSessionMemoryManager:
    """跨会话记忆管理器"""

    def __init__(self):
        self.name = "跨会话记忆管理器 v1.0"
        self.version = "1.0.0"

        # 记忆存储
        self.memories: dict[str, MemoryFragment] = {}

        # 索引
        self.keyword_index: dict[str, set[str]] = defaultdict(set)  # keyword -> memory_ids
        self.entity_index: dict[str, set[str]] = defaultdict(set)  # entity -> memory_ids
        self.user_index: dict[str, set[str]] = defaultdict(set)  # user_id -> memory_ids
        self.session_index: dict[str, set[str]] = defaultdict(set)  # session_id -> memory_ids

        # 记忆关联图
        self.memory_graph: dict[str, set[str]] = defaultdict(set)  # memory_id -> related_ids

        # 统计信息
        self.stats = {
            "total_memories": 0,
            "total_queries": 0,
            "avg_retrieval_time": 0.0,
            "cache_hit_rate": 0.0,
            "memory_types": defaultdict(int),
        }

        logger.info(f"🧠 {self.name} 初始化完成")

    def store_memory(
        self,
        content: str,
        memory_type: MemoryType,
        session_id: str,
        user_id: str,
        importance: MemoryImportance = MemoryImportance.MEDIUM,
        keywords: list[str] | None = None,
        entities: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        存储记忆片段

        Args:
            content: 记忆内容
            memory_type: 记忆类型
            session_id: 会话ID
            user_id: 用户ID
            importance: 重要性
            keywords: 关键词
            entities: 实体
            metadata: 元数据

        Returns:
            str: 记忆ID
        """
        import time

        memory_id = f"mem_{user_id}_{int(time.time() * 1000)}"

        # 提取关键词(如果未提供)
        if keywords is None:
            keywords = self._extract_keywords(content)

        # 提取实体(如果未提供)
        if entities is None:
            entities = self._extract_entities(content)

        # 创建记忆片段
        memory = MemoryFragment(
            memory_id=memory_id,
            memory_type=memory_type,
            importance=importance,
            content=content,
            keywords=keywords,
            entities=entities,
            session_id=session_id,
            user_id=user_id,
            metadata=metadata or {},
        )

        # 存储记忆
        self.memories[memory_id] = memory

        # 更新索引
        self._update_indexes(memory)

        # 更新关联
        self._update_memory_relations(memory)

        # 更新统计
        self.stats["total_memories"] += 1
        self.stats["memory_types"][memory_type.value] += 1

        logger.info(f"💾 记忆已存储: {memory_id} ({memory_type.value})")
        return memory_id

    def retrieve_memories(self, query: MemoryQuery) -> MemoryRetrievalResult:
        """
        检索记忆

        Args:
            query: 记忆查询

        Returns:
            MemoryRetrievalResult: 检索结果
        """
        import time

        start_time = time.time()

        self.stats["total_queries"] += 1

        # 1. 根据查询类型检索
        if query.query_type == "keyword":
            candidates = self._keyword_retrieval(query)
        elif query.query_type == "entity":
            candidates = self._entity_retrieval(query)
        elif query.query_type == "temporal":
            candidates = self._temporal_retrieval(query)
        else:
            # 默认: 混合检索
            candidates = self._hybrid_retrieval(query)

        # 2. 过滤和排序
        filtered_candidates = self._filter_and_rank(candidates, query)

        # 3. 应用限制
        result_fragments = filtered_candidates[: query.max_results]

        # 4. 计算相关性得分
        relevance_scores = [
            self._calculate_relevance(mem, query.query_text) for mem in result_fragments
        ]

        # 5. 更新访问统计
        for mem in result_fragments:
            mem.access_count += 1
            mem.last_accessed = datetime.now()

        # 6. 计算检索时间
        retrieval_time = time.time() - start_time

        # 7. 更新统计
        self._update_retrieval_stats(retrieval_time)

        return MemoryRetrievalResult(
            query=query,
            fragments=result_fragments,
            total_found=len(candidates),
            retrieval_time=retrieval_time,
            relevance_scores=relevance_scores,
            reasoning=f"检索到{len(result_fragments)}个相关记忆",
        )

    def _extract_keywords(self, text: str) -> list[str]:
        """提取关键词"""
        # 简化的关键词提取
        # 移除标点符号
        text = re.sub(r"[^\w\s]", " ", text)

        # 分词
        words = text.split()

        # 过滤停用词和短词
        stopwords = {"的", "了", "是", "在", "和", "有", "我", "你", "他", "她", "它", "这", "那"}
        keywords = [w for w in words if len(w) > 1 and w not in stopwords]

        # 返回前10个关键词
        return keywords[:10]

    def _extract_entities(self, text: str) -> list[str]:
        """提取实体"""
        entities = []

        # 简化的实体提取规则
        # 专利号
        patent_pattern = r"[A-Z]{0,2}\d{9,13}"
        patents = re.findall(patent_pattern, text)
        entities.extend(patents)

        # 数字(可能是ID、数量等)
        number_pattern = r"\d{4,}"
        numbers = re.findall(number_pattern, text)
        entities.extend(numbers[:3])

        return list(set(entities))

    def _update_indexes(self, memory: MemoryFragment) -> Any:
        """更新索引"""
        # 关键词索引
        for keyword in memory.keywords:
            self.keyword_index[keyword].add(memory.memory_id)

        # 实体索引
        for entity in memory.entities:
            self.entity_index[entity].add(memory.memory_id)

        # 用户索引
        self.user_index[memory.user_id].add(memory.memory_id)

        # 会话索引
        self.session_index[memory.session_id].add(memory.memory_id)

    def _update_memory_relations(self, memory: MemoryFragment) -> Any:
        """更新记忆关联"""
        # 基于共同关键词/实体建立关联
        related_ids = set()

        # 查找有共同关键词的记忆
        for keyword in memory.keywords:
            related_ids.update(self.keyword_index[keyword])

        # 查找有共同实体的记忆
        for entity in memory.entities:
            related_ids.update(self.entity_index[entity])

        # 移除自己
        related_ids.discard(memory.memory_id)

        # 更新关联图
        if related_ids:
            self.memory_graph[memory.memory_id].update(related_ids)
            for related_id in related_ids:
                self.memory_graph[related_id].add(memory.memory_id)

    def _keyword_retrieval(self, query: MemoryQuery) -> list[MemoryFragment]:
        """关键词检索"""
        query_keywords = self._extract_keywords(query.query_text)

        # 收集候选记忆ID
        candidate_ids = set()
        for keyword in query_keywords:
            candidate_ids.update(self.keyword_index.get(keyword, set()))

        # 转换为记忆对象
        candidates = [self.memories[mid] for mid in candidate_ids if mid in self.memories]
        return candidates

    def _entity_retrieval(self, query: MemoryQuery) -> list[MemoryFragment]:
        """实体检索"""
        query_entities = self._extract_entities(query.query_text)

        # 收集候选记忆ID
        candidate_ids = set()
        for entity in query_entities:
            candidate_ids.update(self.entity_index.get(entity, set()))

        # 转换为记忆对象
        candidates = [self.memories[mid] for mid in candidate_ids if mid in self.memories]
        return candidates

    def _temporal_retrieval(self, query: MemoryQuery) -> list[MemoryFragment]:
        """时间检索"""
        # 获取时间范围
        time_range = query.filters.get("time_range", "30d")  # 默认30天

        if time_range == "7d":
            cutoff = datetime.now() - timedelta(days=7)
        elif time_range == "30d":
            cutoff = datetime.now() - timedelta(days=30)
        elif time_range == "90d":
            cutoff = datetime.now() - timedelta(days=90)
        else:
            cutoff = datetime.now() - timedelta(days=30)

        # 过滤时间范围内的记忆
        candidates = [mem for mem in self.memories.values() if mem.timestamp >= cutoff]

        return candidates

    def _hybrid_retrieval(self, query: MemoryQuery) -> list[MemoryFragment]:
        """混合检索"""
        # 结合多种检索方式
        keyword_results = self._keyword_retrieval(query)
        entity_results = self._entity_retrieval(query)

        # 合并结果
        all_candidates = {mem.memory_id: mem for mem in keyword_results + entity_results}
        return list(all_candidates.values())

    def _filter_and_rank(
        self, candidates: list[MemoryFragment], query: MemoryQuery
    ) -> list[MemoryFragment]:
        """过滤和排序"""
        # 1. 应用重要性过滤
        if query.min_importance:
            importance_order = {
                MemoryImportance.LOW: 1,
                MemoryImportance.MEDIUM: 2,
                MemoryImportance.HIGH: 3,
                MemoryImportance.CRITICAL: 4,
            }
            min_level = importance_order[query.min_importance]
            candidates = [
                mem for mem in candidates if importance_order.get(mem.importance, 0) >= min_level
            ]

        # 2. 应用其他过滤器
        if "user_id" in query.filters:
            candidates = [mem for mem in candidates if mem.user_id == query.filters["user_id"]]

        if "session_id" in query.filters:
            candidates = [
                mem for mem in candidates if mem.session_id == query.filters["session_id"]
            ]

        if "memory_type" in query.filters:
            candidates = [
                mem for mem in candidates if mem.memory_type.value == query.filters["memory_type"]
            ]

        # 3. 排序
        def score_memory(mem: MemoryFragment) -> float:
            # 综合得分 = 相关性(50%) + 重要性(30%) + 访问频率(20%)
            relevance = self._calculate_relevance(mem, query.query_text)

            importance_score = {
                MemoryImportance.CRITICAL: 1.0,
                MemoryImportance.HIGH: 0.8,
                MemoryImportance.MEDIUM: 0.6,
                MemoryImportance.LOW: 0.4,
            }.get(mem.importance, 0.5)

            access_score = min(1.0, mem.access_count / 10.0)

            return 0.5 * relevance + 0.3 * importance_score + 0.2 * access_score

        ranked = sorted(candidates, key=score_memory, reverse=True)
        return ranked

    def _calculate_relevance(self, memory: MemoryFragment, query_text: str) -> float:
        """计算相关性"""
        # 简化的相关性计算
        query_keywords = set(self._extract_keywords(query_text))
        memory_keywords = set(memory.keywords)

        if not query_keywords:
            return 0.5

        # 关键词重叠率
        overlap = len(query_keywords & memory_keywords)
        total = len(query_keywords | memory_keywords)

        jaccard = overlap / total if total > 0 else 0.0

        # 内容匹配度
        content_match = 0.0
        for kw in query_keywords:
            if kw in memory.content:
                content_match += 1.0

        content_score = min(1.0, content_match / len(query_keywords)) if query_keywords else 0.0

        # 综合相关性
        relevance = 0.6 * jaccard + 0.4 * content_score

        return relevance

    def _update_retrieval_stats(self, retrieval_time: float) -> Any:
        """更新检索统计"""
        # 更新平均检索时间
        n = self.stats["total_queries"]
        old_avg = self.stats["avg_retrieval_time"]
        self.stats["avg_retrieval_time"] = (old_avg * (n - 1) + retrieval_time) / n

    def get_memory_by_id(self, memory_id: str) -> MemoryFragment | None:
        """通过ID获取记忆"""
        return self.memories.get(memory_id)

    def get_user_memories(
        self, user_id: str, memory_type: MemoryType | None = None, limit: int = 50
    ) -> list[MemoryFragment]:
        """获取用户的所有记忆"""
        memory_ids = self.user_index.get(user_id, set())

        memories = [self.memories[mid] for mid in memory_ids if mid in self.memories]

        # 过滤类型
        if memory_type:
            memories = [mem for mem in memories if mem.memory_type == memory_type]

        # 排序(按时间)
        memories.sort(key=lambda m: m.timestamp, reverse=True)

        return memories[:limit]

    def cleanup_old_memories(
        self, days: int = 90, min_importance: MemoryImportance = MemoryImportance.MEDIUM
    ) -> Any:
        """清理旧记忆"""
        cutoff = datetime.now() - timedelta(days=days)
        importance_order = {
            MemoryImportance.LOW: 1,
            MemoryImportance.MEDIUM: 2,
            MemoryImportance.HIGH: 3,
            MemoryImportance.CRITICAL: 4,
        }
        min_level = importance_order[min_importance]

        to_remove = []
        for memory_id, memory in self.memories.items():
            if memory.timestamp < cutoff and importance_order.get(memory.importance, 0) < min_level:
                to_remove.append(memory_id)

        # 删除记忆
        for memory_id in to_remove:
            self._delete_memory(memory_id)

        logger.info(f"🗑️ 清理了{len(to_remove)}个旧记忆")
        return len(to_remove)

    def _delete_memory(self, memory_id: str) -> Any:
        """删除记忆"""
        if memory_id not in self.memories:
            return

        memory = self.memories[memory_id]

        # 从索引中移除
        for keyword in memory.keywords:
            self.keyword_index[keyword].discard(memory_id)

        for entity in memory.entities:
            self.entity_index[entity].discard(memory_id)

        self.user_index[memory.user_id].discard(memory_id)
        self.session_index[memory.session_id].discard(memory_id)

        # 从关联图中移除
        if memory_id in self.memory_graph:
            del self.memory_graph[memory_id]

        for related_id in self.memory_graph:
            self.memory_graph[related_id].discard(memory_id)

        # 删除记忆
        del self.memories[memory_id]

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "memory_graph_size": sum(len(v) for v in self.memory_graph.values()),
            "index_sizes": {
                "keywords": len(self.keyword_index),
                "entities": len(self.entity_index),
                "users": len(self.user_index),
                "sessions": len(self.session_index),
            },
        }


# 全局实例
_manager_instance: CrossSessionMemoryManager | None = None


def get_cross_session_memory_manager() -> CrossSessionMemoryManager:
    """获取跨会话记忆管理器单例"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = CrossSessionMemoryManager()
    return _manager_instance
