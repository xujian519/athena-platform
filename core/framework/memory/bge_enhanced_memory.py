#!/usr/bin/env python3

"""
BGE增强的记忆系统
BGE Enhanced Memory System for Athena Platform

使用BGE Large ZH v1.5增强记忆系统的向量化和检索能力

作者: 小诺·双鱼座
创建时间: 2025-12-16
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

import numpy as np

from ..embedding.unified_embedding_service import encode_for_memory

logger = logging.getLogger(__name__)

@dataclass
class MemoryItem:
    """记忆项"""
    id: str
    content: str
    embedding: list[str] = None
    memory_type: str = "episodic"  # episodic, semantic, procedural
    importance: float = 1.0
    tags: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    decay_rate: float = 0.1  # 遗忘速率
    related_memories: list[str] = field(default_factory=list)

@dataclass
class MemoryQuery:
    """记忆查询"""
    query: str
    memory_type: Optional[str] = None
    min_importance: float = 0.0
    time_range: Optional[tuple[datetime, datetime]] = None
    tags: list[str] = None
    top_k: int = 10

class BGEEnhancedMemorySystem:
    """BGE增强的记忆系统"""

    def __init__(self, max_memories: int = 10000):
        self.name = "BGE增强记忆系统"
        self.version = "1.0.0"
        self.logger = logging.getLogger(self.name)

        # 记忆存储
        self.memories: dict[str, MemoryItem] = {}
        self.max_memories = max_memories

        # 向量索引（用于快速检索）
        self.embedding_index: np.Optional[ndarray] = None
        self.memory_ids: list[str] = []

        # 记忆类型索引
        self.type_index: dict[str, list[str] = {
            "episodic": [],
            "semantic": [],
            "procedural": []
        }

        # 标签索引
        self.tag_index: dict[str, list[str] = {}

        # 统计信息
        self.stats = {
            "total_memories": 0,
            "total_retrievals": 0,
            "cache_hits": 0,
            "memory consolidations": 0
        }

    async def add_memory(self,
                        content: str,
                        memory_type: str = "episodic",
                        importance: float = 1.0,
                        tags: list[str] = None,
                        memory_id: Optional[Optional[str]] = None) -> str:
        """
        添加记忆项

        Args:
            content: 记忆内容
            memory_type: 记忆类型
            importance: 重要性
            tags: 标签列表
            memory_id: 记忆ID（可选）

        Returns:
            记忆ID
        """
        try:
            # 生成ID
            if not memory_id:
                import hashlib
                memory_id = hashlib.md5(
                    f"{content}_{datetime.now()}".encode(), usedforsecurity=False
                ).hexdigest()[:16]

            # 生成内容嵌入
            result = await encode_for_memory(content)
            embedding = result["embeddings"]

            # 创建记忆项
            memory = MemoryItem(
                id=memory_id,
                content=content,
                embedding=embedding,
                memory_type=memory_type,
                importance=importance,
                tags=tags or [],
                timestamp=datetime.now()
            )

            # 存储记忆
            self.memories[memory_id] = memory

            # 更新索引
            self._update_indices(memory_id, memory)

            # 检查是否需要清理
            if len(self.memories) > self.max_memories:
                await self._forget_memories()

            self.logger.debug(f"添加记忆: {memory_id} ({memory_type})")
            return memory_id

        except Exception as e:
            logger.error(f"操作失败: {e}", exc_info=True)
            raise

    def _update_indices(self, memory_id: str, memory: MemoryItem):
        """更新索引"""
        # 类型索引
        if memory.memory_type in self.type_index:
            self.type_index[memory.memory_type].append(memory_id)

        # 标签索引
        for tag in memory.tags:
            if tag not in self.tag_index:
                self.tag_index[tag]] = []
            self.tag_index[tag].append(memory_id)

        # 更新向量索引
        self._rebuild_embedding_index()

    def _rebuild_embedding_index(self):
        """重建向量索引"""
        embeddings = []
        ids = []

        for memory_id, memory in self.memories.items():
            if memory.embedding:
                embeddings.append(memory.embedding)
                ids.append(memory_id)

        if embeddings:
            self.embedding_index = np.array(embeddings)
            self.memory_ids = ids

    async def retrieve_memories(self, query: MemoryQuery) -> list[tuple[MemoryItem, float]]:
        """
        检索记忆

        Args:
            query: 记忆查询

        Returns:
            相关记忆列表及相似度
        """
        try:
            # 生成查询嵌入
            query_result = await encode_for_memory(query.query)
            query_embedding = np.array(query_result["embeddings"])

            # 向量相似度检索
            vector_results = []
            if self.embedding_index is not None and len(self.memory_ids) > 0:
                similarities = np.dot(self.embedding_index, query_embedding)

                # 获取top-k
                top_k_indices = np.argsort(similarities)[-query.top_k:][::-1]

                for idx in top_k_indices:
                    if similarities[idx] > 0.3:  # 相似度阈值
                        memory_id = self.memory_ids[idx]
                        memory = self.memories[memory_id]
                        vector_results.append((memory, float(similarities[idx])))

            # 根据查询条件过滤
            filtered_results = []
            for memory, similarity in vector_results:
                # 记忆类型过滤
                if query.memory_type and memory.memory_type != query.memory_type:
                    continue

                # 重要性过滤
                if memory.importance < query.min_importance:
                    continue

                # 时间范围过滤
                if query.time_range:
                    start_time, end_time = query.time_range
                    if not (start_time <= memory.timestamp <= end_time):
                        continue

                # 标签过滤
                if query.tags and not any(tag in memory.tags for tag in query.tags):
                    continue

                filtered_results.append((memory, similarity))

            # 更新访问统计
            for memory, _ in filtered_results[:5]:  # 只更新前5个
                memory.last_accessed = datetime.now()
                memory.access_count += 1

            self.stats["total_retrievals"] += 1

            return filtered_results

        except Exception as e:
            logger.error(f"操作失败: {e}", exc_info=True)
            return []

    async def find_related_memories(self, memory_id: str, top_k: int = 5) -> list[tuple[MemoryItem, float]]:
        """
        查找相关记忆

        Args:
            memory_id: 记忆ID
            top_k: 返回数量

        Returns:
            相关记忆列表
        """
        if memory_id not in self.memories:
            return []

        memory = self.memories[memory_id]

        # 使用记忆内容作为查询
        query = MemoryQuery(
            query=memory.content,
            top_k=top_k + 1,  # +1 因为会包含自己
            memory_type=memory.memory_type
        )

        results = await self.retrieve_memories(query)

        # 排除自己
        return [(m, s) for m, s in results if m.id != memory_id][:top_k]

    async def consolidate_memories(self):
        """
        记忆整合
        将相似的记忆合并，减少冗余
        """
        consolidation_threshold = 0.9
        consolidated_count = 0

        # 获取所有记忆对
        memory_ids = list(self.memories.keys())

        for i in range(len(memory_ids)):
            for j in range(i + 1, len(memory_ids)):
                id1, id2 = memory_ids[i], memory_ids[j]
                memory1, memory2 = self.memories[id1], self.memories[id2]

                # 只整合同类型的记忆
                if memory1.memory_type != memory2.memory_type:
                    continue

                # 计算相似度
                if memory1.embedding and memory2.embedding:
                    similarity = np.dot(
                        np.array(memory1.embedding),
                        np.array(memory2.embedding)
                    ) / (
                        np.linalg.norm(memory1.embedding) * np.linalg.norm(memory2.embedding)
                    )

                    # 如果相似度超过阈值，整合
                    if similarity > consolidation_threshold:
                        # 保留重要性更高的记忆
                        if memory1.importance >= memory2.importance:
                            # 更新记忆1
                            memory1.related_memories.append(id2)
                            memory1.importance = max(memory1.importance, memory2.importance)
                            # 删除记忆2
                            del self.memories[id2]
                        else:
                            # 更新记忆2
                            memory2.related_memories.append(id1)
                            memory2.importance = max(memory1.importance, memory2.importance)
                            # 删除记忆1
                            del self.memories[id1]

                        consolidated_count += 1

        # 重建索引
        self._rebuild_embedding_index()
        self._rebuild_secondary_indices()

        self.stats["memory consolidations"] += consolidated_count
        self.logger.info(f"记忆整合完成，合并了 {consolidated_count} 个记忆")

    def _rebuild_secondary_indices(self):
        """重建次要索引"""
        # 清空索引
        self.type_index = {t: [] for t in self.type_index}
        self.tag_index = {}

        # 重建索引
        for memory_id, memory in self.memories.items():
            # 类型索引
            if memory.memory_type in self.type_index:
                self.type_index[memory.memory_type].append(memory_id)

            # 标签索引
            for tag in memory.tags:
                if tag not in self.tag_index:
                    self.tag_index[tag]] = []
                self.tag_index[tag].append(memory_id)

    async def _forget_memories(self):
        """
        遗忘机制
        根据重要性、访问频率和遗忘速率删除记忆
        """
        # 计算每个记忆的得分
        memory_scores = []

        current_time = datetime.now()

        for memory_id, memory in self.memories.items():
            # 时间衰减
            time_diff = (current_time - memory.timestamp).total_seconds() / 3600  # 小时
            time_decay = np.exp(-memory.decay_rate * time_diff)

            # 访问频率加成
            access_bonus = np.log(1 + memory.access_count)

            # 最终得分
            score = memory.importance * time_decay * access_bonus
            memory_scores.append((memory_id, score))

        # 按得分排序，删除得分最低的
        memory_scores.sort(key=lambda x: x[1])
        to_forget = len(self.memories) - self.max_memories

        for i in range(to_forget):
            memory_id = memory_scores[i][0]
            del self.memories[memory_id]

        # 重建索引
        self._rebuild_embedding_index()
        self._rebuild_secondary_indices()

        self.logger.info(f"遗忘了 {to_forget} 个记忆")

    def get_memory_statistics(self) -> dict[str, Any]:
        """获取记忆系统统计"""
        # 计算平均重要性
        if self.memories:
            avg_importance = sum(m.importance for m in self.memories.values()) / len(self.memories)
        else:
            avg_importance = 0

        # 计算记忆年龄分布
        current_time = datetime.now()
        age_distribution = {"day": 0, "week": 0, "month": 0, "older": 0}

        for memory in self.memories.values():
            age = (current_time - memory.timestamp).days
            if age <= 1:
                age_distribution["day"] += 1
            elif age <= 7:
                age_distribution["week"] += 1
            elif age <= 30:
                age_distribution["month"] += 1
            else:
                age_distribution["older"] += 1

        return {
            "total_memories": len(self.memories),
            "by_type": {t: len(ids) for t, ids in self.type_index.items()},
            "by_tags": len(self.tag_index),
            "avg_importance": avg_importance,
            "age_distribution": age_distribution,
            "retrievals": self.stats["total_retrievals"],
            "consolidations": self.stats["memory consolidations"],
            "vector_index_size": len(self.memory_ids) if self.embedding_index is not None else 0
        }

    async def export_memories(self, filepath: str):
        """导出记忆到文件"""
        import json

        export_data = []
        for memory in self.memories.values():
            memory_data = {
                "id": memory.id,
                "content": memory.content,
                "memory_type": memory.memory_type,
                "importance": memory.importance,
                "tags": memory.tags,
                "timestamp": memory.timestamp.isoformat(),
                "access_count": memory.access_count
            }
            export_data.append(memory_data)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        self.logger.info(f"记忆已导出到: {filepath}")

# 便捷函数
async def create_episodic_memory(content: str, importance: float = 1.0) -> str:
    """创建情景记忆"""
    system = BGEEnhancedMemorySystem()
    return await system.add_memory(content, "episodic", importance)

async def create_semantic_memory(content: Optional[str] = None, tags: list[str] = None) -> str:
    """创建语义记忆"""
    system = BGEEnhancedMemorySystem()
    return await system.add_memory(content, "semantic", importance=2.0, tags=tags)

# 导出
__all__ = [
    'BGEEnhancedMemorySystem',
    'MemoryItem',
    'MemoryQuery',
    'create_episodic_memory',
    'create_semantic_memory'
]

