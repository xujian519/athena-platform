#!/usr/bin/env python3
"""
BGE增强的知识图谱
BGE Enhanced Knowledge Graph for Athena Platform

使用BGE Large ZH v1.5增强知识图谱的实体关系抽取和向量化表示

作者: 小诺·双鱼座
创建时间: 2025-12-16
"""
from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Any

import numpy as np

from ..embedding.unified_embedding_service import encode_for_knowledge_graph

logger = logging.getLogger(__name__)


@dataclass
class Entity:
    """实体"""

    id: str
    name: str
    type: str
    embedding: list[float] | None = None
    description: str | None = None
    aliases: list[str] | None = None


@dataclass
class Relation:
    """关系"""

    id: str
    source: str
    target: str
    type: str
    embedding: list[float] | None = None
    confidence: float = 1.0
    description: str | None = None


@dataclass
class KnowledgeTriplet:
    """知识三元组"""

    subject: Entity
    predicate: str
    object: Entity
    confidence: float = 1.0
    embedding: list[float] | None = None


class BGEKnowledgeGraph:
    """BGE增强的知识图谱"""

    def __init__(self):
        self.name = "BGE知识图谱"
        self.version = "1.0.0"
        self.logger = logging.getLogger(self.name)

        # 图结构
        self.entities: dict[str, Entity] = {}
        self.relations: dict[str, Relation] = {}
        self.triplets: list[KnowledgeTriplet] = []

        # 索引
        self.type_index: dict[str, set[str]] = {}
        self.embedding_index: dict[str, np.ndarray] | None | None = None

        # 统计
        self.stats = {
            "total_entities": 0,
            "total_relations": 0,
            "total_triplets": 0,
            "indexed_entities": 0,
        }

    async def add_entity(self, entity: Entity) -> bool:
        """
        添加实体并生成嵌入

        Args:
            entity: 实体对象

        Returns:
            是否成功
        """
        try:
            # 生成实体嵌入
            entity_text = f"{entity.name} 是一个 {entity.type}"
            if entity.description:
                entity_text += f"。{entity.description}"

            result = await encode_for_knowledge_graph(entity_text)
            entity.embedding = result["embeddings"]

            # 存储实体
            self.entities[entity.id] = entity

            # 更新类型索引
            if entity.type not in self.type_index:
                self.type_index[entity.type] = set()
            self.type_index[entity.type].add(entity.id)

            # 更新统计
            self.stats["total_entities"] += 1

            self.logger.debug(f"添加实体: {entity.name} ({entity.type})")
            return True

        except Exception as e:
            self.logger.error(f"添加实体失败: {e}")
            return False

    async def add_relation(self, relation: Relation) -> bool:
        """
        添加关系并生成嵌入

        Args:
            relation: 关系对象

        Returns:
            是否成功
        """
        try:
            # 验证实体存在
            if relation.source not in self.entities or relation.target not in self.entities:
                self.logger.warning(f"关系中的实体不存在: {relation.source} -> {relation.target}")
                return False

            # 生成关系嵌入
            source_entity = self.entities[relation.source]
            target_entity = self.entities[relation.target]
            relation_text = f"{source_entity.name} {relation.type} {target_entity.name}"

            result = await encode_for_knowledge_graph(relation_text)
            relation.embedding = result["embeddings"]

            # 存储关系
            self.relations[relation.id] = relation

            # 创建三元组
            triplet = KnowledgeTriplet(
                subject=source_entity,
                predicate=relation.type,
                object=target_entity,
                confidence=relation.confidence,
                embedding=relation.embedding,
            )
            self.triplets.append(triplet)

            # 更新统计
            self.stats["total_relations"] += 1
            self.stats["total_triplets"] += 1

            self.logger.debug(
                f"添加关系: {source_entity.name} -> {target_entity.name} ({relation.type})"
            )
            return True

        except Exception as e:
            self.logger.error(f"添加关系失败: {e}")
            return False

    async def add_knowledge_from_text(
        self, text: str, entity_types: list[str] | None = None
    ) -> list[KnowledgeTriplet]:
        """
        从文本中提取知识并添加到图谱

        Args:
            text: 输入文本
            entity_types: 指定的实体类型

        Returns:
            提取的三元组列表
        """
        # TODO: 集成NER和关系抽取模型
        # 这里使用简化的示例

        # 1. 生成文本嵌入
        text_result = await encode_for_knowledge_graph(text)
        text_result["embeddings"]

        # 2. 简单的实体抽取(示例)
        extracted_triplets = []

        # 模拟提取结果
        example_entities = [
            Entity("E1", "深度学习", "技术", description="人工智能的重要分支"),
            Entity("E2", "神经网络", "技术", description="深度学习的基础结构"),
            Entity("E3", "计算机视觉", "应用", description="AI的重要应用领域"),
        ]

        # 添加实体
        for entity in example_entities:
            await self.add_entity(entity)

        # 添加关系
        relations = [
            Relation("R1", "E1", "E2", "基于", 0.9, "深度学习基于神经网络"),
            Relation("R2", "E1", "E3", "应用于", 0.8, "深度学习应用于计算机视觉"),
        ]

        for relation in relations:
            if await self.add_relation(relation):
                # 添加到提取结果
                source_entity = self.entities[relation.source]
                target_entity = self.entities[relation.target]
                triplet = KnowledgeTriplet(
                    subject=source_entity,
                    predicate=relation.type,
                    object=target_entity,
                    confidence=relation.confidence,
                )
                extracted_triplets.append(triplet)

        self.logger.info(f"从文本中提取了 {len(extracted_triplets)} 个三元组")
        return extracted_triplets

    async def find_similar_entities(self, query: str, top_k: int = 5) -> list[tuple[Entity, float]]:
        """
        查找相似实体

        Args:
            query: 查询文本
            top_k: 返回数量

        Returns:
            相似实体列表及相似度
        """
        if not self.entities:
            return []

        try:
            # 生成查询嵌入
            query_result = await encode_for_knowledge_graph(query)
            query_embedding = np.array(query_result["embeddings"])

            # 计算相似度
            similarities = []
            for entity in self.entities.values():
                if entity.embedding:
                    entity_embedding = np.array(entity.embedding)
                    similarity = np.dot(query_embedding, entity_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(entity_embedding)
                    )
                    similarities.append((entity, similarity))

            # 排序并返回top-k
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:top_k]

        except Exception as e:
            self.logger.error(f"查找相似实体失败: {e}")
            return []

    async def find_related_entities(self, entity_id: str, max_depth: int = 2) -> dict[str, Any]:
        """
        查找相关实体

        Args:
            entity_id: 实体ID
            max_depth: 搜索深度

        Returns:
            相关实体网络
        """
        if entity_id not in self.entities:
            return {}

        related = {"center": self.entities[entity_id], "relations": [], "entities": set()}

        visited = set()
        queue = [(entity_id, 0)]

        while queue and queue[0][1] < max_depth:
            current_id, depth = queue.pop(0)

            if current_id in visited:
                continue
            visited.add(current_id)

            for relation in self.relations.values():
                related_entity = None
                relation_type = None

                if relation.source == current_id:
                    related_entity = self.entities[relation.target]
                    relation_type = "outgoing"
                elif relation.target == current_id:
                    related_entity = self.entities[relation.source]
                    relation_type = "incoming"

                if related_entity and related_entity.id not in visited:
                    related["relations"].append(
                        {
                            "relation": relation,
                            "entity": related_entity,
                            "direction": relation_type,
                            "depth": depth,
                        }
                    )
                    related["entities"].add(related_entity.id)
                    queue.append((related_entity.id, depth + 1))

        return related

    def get_statistics(self) -> dict[str, Any]:
        """获取知识图谱统计信息"""
        # 统计实体类型分布
        type_counts = {}
        for entity_type, entities in self.type_index.items():
            type_counts[entity_type] = len(entities)

        # 统计关系类型分布
        relation_counts = {}
        for relation in self.relations.values():
            relation_type = relation.type
            relation_counts[relation_type] = relation_counts.get(relation_type, 0) + 1

        return {
            "entities": {"total": self.stats["total_entities"], "by_type": type_counts},
            "relations": {"total": self.stats["total_relations"], "by_type": relation_counts},
            "triplets": self.stats["total_triplets"],
            "connected_components": self._count_connected_components(),
        }

    def _count_connected_components(self) -> int:
        """计算连通分量数"""
        if not self.entities:
            return 0

        # 构建邻接表
        graph = {entity_id: set() for entity_id in self.entities}
        for relation in self.relations.values():
            graph[relation.source].add(relation.target)
            graph[relation.target].add(relation.source)

        # DFS计算连通分量
        visited = set()
        components = 0

        def dfs(node) -> None:
            visited.add(node)
            for neighbor in graph[node]:
                if neighbor not in visited:
                    dfs(neighbor)

        for node in self.entities:
            if node not in visited:
                components += 1
                dfs(node)

        return components

    async def export_to_vector_db(self, vector_db_client):
        """
        导出到向量数据库

        Args:
            vector_db_client: 向量数据库客户端
        """
        try:
            # 导出实体向量
            for entity in self.entities.values():
                if entity.embedding:
                    await vector_db_client.insert(
                        id=entity.id,
                        vector=entity.embedding,
                        metadata={
                            "name": entity.name,
                            "type": entity.type,
                            "description": entity.description,
                            "kind": "entity",
                        },
                    )

            # 导出关系向量
            for relation in self.relations.values():
                if relation.embedding:
                    await vector_db_client.insert(
                        id=relation.id,
                        vector=relation.embedding,
                        metadata={
                            "source": relation.source,
                            "target": relation.target,
                            "type": relation.type,
                            "confidence": relation.confidence,
                            "kind": "relation",
                        },
                    )

            self.logger.info("知识图谱已导出到向量数据库")

        except Exception as e:
            self.logger.error(f"导出失败: {e}")


# 便捷函数
async def create_knowledge_graph_from_texts(texts: list[str]) -> BGEKnowledgeGraph:
    """
    从文本列表创建知识图谱

    Args:
        texts: 文本列表

    Returns:
        知识图谱实例
    """
    kg = BGEKnowledgeGraph()

    for text in texts:
        await kg.add_knowledge_from_text(text)

    return kg


# 导出
__all__ = [
    "BGEKnowledgeGraph",
    "Entity",
    "KnowledgeTriplet",
    "Relation",
    "create_knowledge_graph_from_texts",
]
