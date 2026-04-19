"""
知识图谱增强模块 - Knowledge Graph Enhancement

集成现有知识图谱系统,提供:
1. 图谱检索API
2. 实体关系查询
3. 概念推理
4. 意图增强

注意:此模块是对现有知识图谱系统的集成层
"""

from __future__ import annotations
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class EntityType(Enum):
    """实体类型"""

    PATENT = "patent"  # 专利
    CONCEPT = "concept"  # 技术概念
    COMPANY = "company"  # 公司/申请人
    INVENTOR = "inventor"  # 发明人
    CATEGORY = "category"  # 分类号
    KEYWORD = "keyword"  # 关键词
    LEGAL = "legal"  # 法律概念
    TECH_FIELD = "tech_field"  # 技术领域


class RelationType(Enum):
    """关系类型"""

    CONTAINS = "contains"  # 包含
    BELONGS_TO = "belongs_to"  # 属于
    CITES = "cites"  # 引用
    SIMILAR_TO = "similar_to"  # 相似
    RELATED_TO = "related_to"  # 相关
    INVENTED_BY = "invented_by"  # 发明者
    ASSIGNED_TO = "assigned_to"  # 受让人
    SUB_CLASS_OF = "sub_class_of"  # 子类
    PART_OF = "part_of"  # 部分
    APPLIES_TO = "applies_to"  # 应用于
    DERIVED_FROM = "derived_from"  # 源于


@dataclass
class Entity:
    """实体"""

    id: str  # 实体ID
    type: EntityType  # 实体类型
    name: str  # 实体名称
    properties: dict[str, Any] = field(default_factory=dict)  # 属性
    embedding: list[float] | None = None  # 向量嵌入
    created_at: float = field(default_factory=time.time)  # 创建时间

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "type": self.type.value,
            "name": self.name,
            "properties": self.properties,
            "embedding": self.embedding[:10] if self.embedding else None,  # 只显示前10维
        }


@dataclass
class Relation:
    """关系"""

    id: str  # 关系ID
    from_entity: str  # 起始实体ID
    to_entity: str  # 目标实体ID
    type: RelationType  # 关系类型
    properties: dict[str, Any] = field(default_factory=dict)  # 属性
    weight: float = 1.0  # 关系权重
    created_at: float = field(default_factory=time.time)  # 创建时间

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "from_entity": self.from_entity,
            "to_entity": self.to_entity,
            "type": self.type.value,
            "weight": self.weight,
            "properties": self.properties,
        }


@dataclass
class GraphPath:
    """图路径"""

    entities: list[Entity]  # 实体列表
    relations: list[Relation]  # 关系列表
    score: float = 0.0  # 路径得分

    def length(self) -> int:
        """路径长度(关系数量)"""
        return len(self.relations)


class KnowledgeGraphClient(ABC):
    """知识图谱客户端抽象接口"""

    @abstractmethod
    async def search_entities(
        self, query: str, entity_type: EntityType | None = None, limit: int = 10
    ) -> list[Entity]:
        """搜索实体"""
        pass

    @abstractmethod
    async def get_entity(self, entity_id: str) -> Entity | None:
        """获取实体详情"""
        pass

    @abstractmethod
    async def get_relations(
        self,
        entity_id: str,
        relation_type: RelationType | None = None,
        direction: str = "out",  # "out", "in", "both"
    ) -> list[Relation]:
        """获取实体的关系"""
        pass

    @abstractmethod
    async def find_paths(
        self, from_entity: str, to_entity: str, max_depth: int = 3, max_paths: int = 10
    ) -> list[GraphPath]:
        """查找两个实体之间的路径"""
        pass

    @abstractmethod
    async def get_neighbors(
        self, entity_id: str, depth: int = 1, relation_types: list[RelationType] | None = None
    ) -> dict[str, list[Entity]]:
        """获取邻居实体"""
        pass

    @abstractmethod
    async def expand_concept(
        self, concept: str, expand_type: str = "hierarchy"  # "hierarchy", "related", "both"
    ) -> list[Entity]:
        """扩展概念(获取父概念、子概念、相关概念)"""
        pass


class MockKnowledgeGraphClient(KnowledgeGraphClient):
    """
    模拟知识图谱客户端

    用于测试和演示,实际使用时应该替换为真实的知识图谱客户端
    """

    def __init__(self):
        """初始化模拟客户端"""
        # 构建模拟图谱
        self._entities: dict[str, Entity] = {}
        self._relations: dict[str, Relation] = {}
        self._build_mock_graph()

    def _build_mock_graph(self) -> None:
        """构建模拟图谱数据"""
        # 技术领域层级
        ai = Entity(
            id="tech_ai",
            type=EntityType.TECH_FIELD,
            name="人工智能",
            properties={"level": 0, "description": "模拟智能的技术"},
        )
        ml = Entity(
            id="tech_ml",
            type=EntityType.TECH_FIELD,
            name="机器学习",
            properties={"level": 1, "parent": "tech_ai"},
        )
        dl = Entity(
            id="tech_dl",
            type=EntityType.TECH_FIELD,
            name="深度学习",
            properties={"level": 2, "parent": "tech_ml"},
        )
        nlp = Entity(
            id="tech_nlp",
            type=EntityType.TECH_FIELD,
            name="自然语言处理",
            properties={"level": 2, "parent": "tech_ml"},
        )
        cnn = Entity(
            id="tech_cnn",
            type=EntityType.CONCEPT,
            name="卷积神经网络",
            properties={"level": 3, "parent": "tech_dl"},
        )
        rnn = Entity(
            id="tech_rnn",
            type=EntityType.CONCEPT,
            name="循环神经网络",
            properties={"level": 3, "parent": "tech_dl"},
        )
        transformer = Entity(
            id="tech_transformer",
            type=EntityType.CONCEPT,
            name="Transformer",
            properties={"level": 3, "parent": "tech_nlp"},
        )
        bert = Entity(
            id="tech_bert",
            type=EntityType.CONCEPT,
            name="BERT",
            properties={"level": 4, "parent": "tech_transformer"},
        )
        gpt = Entity(
            id="tech_gpt",
            type=EntityType.CONCEPT,
            name="GPT",
            properties={"level": 4, "parent": "tech_transformer"},
        )

        # 添加实体
        for entity in [ai, ml, dl, nlp, cnn, rnn, transformer, bert, gpt]:
            self._entities[entity.id] = entity

        # 添加关系(层级关系)
        relations = [
            Relation(
                id="rel_1",
                from_entity="tech_ml",
                to_entity="tech_ai",
                type=RelationType.SUB_CLASS_OF,
                weight=1.0,
            ),
            Relation(
                id="rel_2",
                from_entity="tech_dl",
                to_entity="tech_ml",
                type=RelationType.SUB_CLASS_OF,
                weight=1.0,
            ),
            Relation(
                id="rel_3",
                from_entity="tech_nlp",
                to_entity="tech_ml",
                type=RelationType.SUB_CLASS_OF,
                weight=1.0,
            ),
            Relation(
                id="rel_4",
                from_entity="tech_cnn",
                to_entity="tech_dl",
                type=RelationType.SUB_CLASS_OF,
                weight=1.0,
            ),
            Relation(
                id="rel_5",
                from_entity="tech_rnn",
                to_entity="tech_dl",
                type=RelationType.SUB_CLASS_OF,
                weight=1.0,
            ),
            Relation(
                id="rel_6",
                from_entity="tech_transformer",
                to_entity="tech_nlp",
                type=RelationType.SUB_CLASS_OF,
                weight=1.0,
            ),
            Relation(
                id="rel_7",
                from_entity="tech_bert",
                to_entity="tech_transformer",
                type=RelationType.SUB_CLASS_OF,
                weight=1.0,
            ),
            Relation(
                id="rel_8",
                from_entity="tech_gpt",
                to_entity="tech_transformer",
                type=RelationType.SUB_CLASS_OF,
                weight=1.0,
            ),
        ]

        for relation in relations:
            self._relations[relation.id] = relation

        logger.info("✅ 模拟知识图谱构建完成")

    async def search_entities(
        self, query: str, entity_type: EntityType | None = None, limit: int = 10
    ) -> list[Entity]:
        """搜索实体"""
        query_lower = query.lower()
        results = []

        for entity in self._entities.values():
            # 类型过滤
            if entity_type and entity.type != entity_type:
                continue

            # 名称匹配
            if query_lower in entity.name.lower() or any(query_lower in str(v).lower() for v in entity.properties.values()):
                results.append(entity)

        return results[:limit]

    async def get_entity(self, entity_id: str) -> Entity | None:
        """获取实体详情"""
        return self._entities.get(entity_id)

    async def get_relations(
        self, entity_id: str, relation_type: RelationType | None = None, direction: str = "out"
    ) -> list[Relation]:
        """获取实体的关系"""
        results = []

        for relation in self._relations.values():
            # 类型过滤
            if relation_type and relation.type != relation_type:
                continue

            # 方向过滤
            if direction == "out" and relation.from_entity != entity_id:
                continue
            if direction == "in" and relation.to_entity != entity_id:
                continue
            if (
                direction == "both"
                and relation.from_entity != entity_id
                and relation.to_entity != entity_id
            ):
                continue

            results.append(relation)

        return results

    async def find_paths(
        self, from_entity: str, to_entity: str, max_depth: int = 3, max_paths: int = 10
    ) -> list[GraphPath]:
        """查找两个实体之间的路径(BFS)"""
        if from_entity not in self._entities or to_entity not in self._entities:
            return []

        paths = []
        queue = [(from_entity, [])]  # (current_entity, path_so_far)
        visited = set()

        while queue and len(paths) < max_paths:
            current, path = queue.pop(0)

            if current == to_entity:
                # 找到路径,构建GraphPath
                entities = [self._entities[from_entity]]
                relations = []

                for rel_id in path:
                    rel = self._relations[rel_id]
                    relations.append(rel)
                    entities.append(self._entities[rel.to_entity])

                paths.append(GraphPath(entities=entities, relations=relations, score=1.0))
                continue

            if len(path) >= max_depth:
                continue

            if current in visited:
                continue
            visited.add(current)

            # 添加邻居到队列
            for rel in self._relations.values():
                if rel.from_entity == current:
                    queue.append((rel.to_entity, [*path, rel.id]))

        return paths

    async def get_neighbors(
        self, entity_id: str, depth: int = 1, relation_types: list[RelationType] | None = None
    ) -> dict[str, list[Entity]]:
        """获取邻居实体"""
        result = {}

        async def _get_neighbors_recursive(
            current_id: str, current_depth: int, visited: set[str]
        ) -> list[Entity]:
            if current_depth > depth or current_id in visited:
                return []

            visited.add(current_id)
            neighbors = []

            for rel in self._relations.values():
                if rel.from_entity == current_id:
                    # 类型过滤
                    if relation_types and rel.type not in relation_types:
                        continue

                    neighbor = self._entities.get(rel.to_entity)
                    if neighbor:
                        neighbors.append(neighbor)
                        # 递归获取
                        sub_neighbors = await _get_neighbors_recursive(
                            rel.to_entity, current_depth + 1, visited
                        )
                        neighbors.extend(sub_neighbors)

            return neighbors

        neighbors = await _get_neighbors_recursive(entity_id, 0, set())
        result["neighbors"] = list(set(neighbors))  # 去重

        return result

    async def expand_concept(self, concept: str, expand_type: str = "hierarchy") -> list[Entity]:
        """扩展概念"""
        # 首先搜索概念
        matches = await self.search_entities(concept, limit=1)

        if not matches:
            return []

        concept_entity = matches[0]
        results = []

        if expand_type in ["hierarchy", "both"]:
            # 获取父概念和子概念
            for rel in self._relations.values():
                if rel.to_entity == concept_entity.id and rel.type == RelationType.SUB_CLASS_OF:
                    # 父概念
                    parent = self._entities.get(rel.from_entity)
                    if parent:
                        results.append(parent)

                if rel.from_entity == concept_entity.id and rel.type == RelationType.SUB_CLASS_OF:
                    # 子概念
                    child = self._entities.get(rel.to_entity)
                    if child:
                        results.append(child)

        if expand_type in ["related", "both"]:
            # 获取相关概念(这里简化为同级别的其他概念)
            for rel in self._relations.values():
                if rel.from_entity == concept_entity.id:
                    sibling = self._entities.get(rel.to_entity)
                    if sibling:
                        results.append(sibling)

        return list(set(results))  # 去重


class GraphEnhancer:
    """
    图谱增强器

    使用知识图谱增强意图理解
    """

    def __init__(self, kg_client: KnowledgeGraphClient):
        """
        初始化增强器

        Args:
            kg_client: 知识图谱客户端
        """
        self.kg_client = kg_client

    async def expand_query(
        self, query: str, expand_strategy: str = "concept_hierarchy"
    ) -> dict[str, Any]:
        """
        扩展查询

        Args:
            query: 原始查询
            expand_strategy: 扩展策略
                - concept_hierarchy: 概念层级扩展
                - related_entities: 相关实体扩展
                - both: 两者都扩展

        Returns:
            增强结果
        """
        result = {
            "original_query": query,
            "expanded_terms": [],
            "related_entities": [],
            "concepts": [],
        }

        # 搜索相关实体
        entities = await self.kg_client.search_entities(query, limit=5)

        for entity in entities:
            result["related_entities"].append(entity.to_dict())

            # 概念扩展
            if entity.type in [EntityType.CONCEPT, EntityType.TECH_FIELD]:
                if expand_strategy in ["concept_hierarchy", "both"]:
                    expanded = await self.kg_client.expand_concept(
                        entity.name, expand_type="hierarchy"
                    )
                    for exp_entity in expanded:
                        result["expanded_terms"].append(exp_entity.name)
                        result["concepts"].append(exp_entity.to_dict())

        return result

    async def enrich_intent(self, intent: str, entities: dict[str, Any]) -> dict[str, Any]:
        """
        使用知识图谱丰富意图理解

        Args:
            intent: 意图
            entities: 已提取的实体

        Returns:
            丰富后的信息
        """
        enriched = {
            "original_intent": intent,
            "enriched_entities": [],
            "relations": [],
            "inferred_attributes": {},
        }

        # 对每个实体进行增强
        for entity_name, _entity_info in entities.items():
            # 搜索匹配的实体
            matches = await self.kg_client.search_entities(entity_name, limit=3)

            for match in matches:
                enriched["enriched_entities"].append(match.to_dict())

                # 获取关系
                relations = await self.kg_client.get_relations(match.id)
                for rel in relations:
                    enriched["relations"].append(rel.to_dict())

        return enriched


# 全局单例
_kg_client: KnowledgeGraphClient | None = None
_graph_enhancer: GraphEnhancer | None = None


def get_kg_client() -> KnowledgeGraphClient:
    """获取知识图谱客户端单例"""
    global _kg_client
    if _kg_client is None:
        # 默认使用模拟客户端
        # 实际使用时应该替换为真实客户端
        _kg_client = MockKnowledgeGraphClient()
        logger.info("✅ 知识图谱客户端初始化完成")
    return _kg_client


def get_graph_enhancer() -> GraphEnhancer:
    """获取图谱增强器单例"""
    global _graph_enhancer
    if _graph_enhancer is None:
        _graph_enhancer = GraphEnhancer(get_kg_client())
        logger.info("✅ 图谱增强器初始化完成")
    return _graph_enhancer


# 便捷函数
async def search_concepts(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """搜索概念"""
    client = get_kg_client()
    entities = await client.search_entities(query, entity_type=EntityType.CONCEPT, limit=limit)
    return [e.to_dict() for e in entities]


async def expand_query(query: str) -> dict[str, Any]:
    """扩展查询"""
    enhancer = get_graph_enhancer()
    return await enhancer.expand_query(query)


async def find_entity_relations(entity_name: str) -> list[dict[str, Any]]:
    """查找实体关系"""
    client = get_kg_client()
    entities = await client.search_entities(entity_name, limit=1)

    if not entities:
        return []

    entity = entities[0]
    relations = await client.get_relations(entity.id)

    return [r.to_dict() for r in relations]
