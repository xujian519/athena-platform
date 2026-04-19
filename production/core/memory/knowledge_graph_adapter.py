#!/usr/bin/env python3
"""
记忆系统-知识图谱适配器
Memory-Knowledge Graph Adapter

将知识图谱集成到记忆系统中，提供增强的记忆检索和上下文理解
"""

from __future__ import annotations
import contextlib
import json
import logging
import sqlite3
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

class KnowledgeGraphAdapter:
    """知识图谱适配器 - 连接记忆系统与知识图谱"""

    def __init__(self, agent_id: str, config: dict | None = None):
        self.agent_id = agent_id
        self.config = config or {}
        self.knowledge_graph_path = Path('/Users/xujian/Athena工作平台/data/knowledge/kg_main.db')
        self.connection = None
        self.initialized = False

        # 配置参数
        self.max_related_entities = self.config.get('max_related_entities', 5)
        self.similarity_threshold = self.config.get('similarity_threshold', 0.3)
        self.enable_context_enhancement = self.config.get('enable_context_enhancement', True)

    async def initialize(self):
        """初始化适配器"""
        try:
            if self.knowledge_graph_path.exists():
                self.connection = sqlite3.connect(str(self.knowledge_graph_path))
                self.connection.row_factory = sqlite3.Row
                self.initialized = True
                logger.info(f"✅ 知识图谱适配器初始化成功: {self.agent_id}")
            else:
                logger.warning(f"⚠️ 知识图谱文件不存在: {self.knowledge_graph_path}")
        except Exception as e:
            logger.error(f"❌ 知识图谱适配器初始化失败: {e}")

    async def search_related_entities(self, query: str, entity_types: list[str] = None) -> list[dict]:
        """搜索与查询相关的实体"""
        if not self.initialized:
            await self.initialize()

        related_entities = []

        try:
            cursor = self.connection.cursor()

            # 基于关键词搜索实体
            keywords = query.split()[:5]  # 取前5个关键词

            for keyword in keywords:
                # 搜索名称或别名包含关键词的实体
                cursor.execute("""
                    SELECT entity_id, entity_type, name, properties, aliases
                    FROM entities
                    WHERE name LIKE ? OR aliases LIKE ?
                    ORDER BY
                        CASE WHEN name LIKE ? THEN 1 ELSE 2 END
                    LIMIT ?
                """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", self.max_related_entities))

                for row in cursor.fetchall():
                    entity = dict(row)
                    # 解析属性
                    if entity.get('properties'):
                        try:
                            entity['properties'] = json.loads(entity['properties'])
                        except Exception:
                            entity['properties'] = {}

                    # 添加相关性评分
                    entity['relevance_score'] = self._calculate_relevance(query, entity['name'])
                    related_entities.append(entity)

            # 去重并按相关性排序
            seen = set()
            unique_entities = []
            for entity in related_entities:
                if entity['entity_id'] not in seen:
                    seen.add(entity['entity_id'])
                    unique_entities.append(entity)

            unique_entities.sort(key=lambda x: x['relevance_score'], reverse=True)

            return unique_entities[:self.max_related_entities]

        except Exception as e:
            logger.error(f"搜索相关实体失败: {e}")
            return []

    def _calculate_relevance(self, query: str, entity_name: str) -> float:
        """计算查询与实体的相关性"""
        query_words = set(query.lower().split())
        entity_words = set(entity_name.lower().split())

        # 简单的Jaccard相似度
        intersection = query_words.intersection(entity_words)
        union = query_words.union(entity_words)

        if not union:
            return 0.0

        return len(intersection) / len(union)

    async def get_entity_context(self, entity_id: str, depth: int = 2) -> dict[str, Any]:
        """获取实体的上下文信息（包括相关实体和关系）"""
        if not self.initialized:
            await self.initialize()

        try:
            cursor = self.connection.cursor()

            # 获取实体信息
            cursor.execute('SELECT * FROM entities WHERE entity_id = ?', (entity_id,))
            entity_row = cursor.fetchone()

            if not entity_row:
                return {}

            entity = dict(entity_row)
            if entity.get('properties'):
                try:
                    entity['properties'] = json.loads(entity['properties'])
                except Exception:
                    entity['properties'] = {}

            # 获取相关关系
            cursor.execute("""
                SELECT r.*, e1.name as from_name, e2.name as to_name,
                       e1.entity_type as from_type, e2.entity_type as to_type
                FROM relations r
                LEFT JOIN entities e1 ON r.from_entity = e1.entity_id
                LEFT JOIN entities e2 ON r.to_entity = e2.entity_id
                WHERE r.from_entity = ? OR r.to_entity = ?
                LIMIT ?
            """, (entity_id, entity_id, 20))

            relations = []
            for row in cursor.fetchall():
                relation = dict(row)
                if relation.get('properties'):
                    try:
                        relation['properties'] = json.loads(relation['properties'])
                    except Exception:
                        relation['properties'] = {}
                relations.append(relation)

            # 构建上下文
            context = {
                'entity': entity,
                'relations': relations,
                'related_entities': [],
                'summary': self._generate_entity_summary(entity, relations)
            }

            # 收集相关实体
            related_entity_ids = set()
            for rel in relations:
                related_entity_ids.add(rel['from_entity'])
                related_entity_ids.add(rel['to_entity'])
            related_entity_ids.discard(entity_id)

            # 获取相关实体的详细信息
            for related_id in list(related_entity_ids)[:10]:
                cursor.execute('SELECT * FROM entities WHERE entity_id = ?', (related_id,))
                rel_entity = cursor.fetchone()
                if rel_entity:
                    rel_dict = dict(rel_entity)
                    if rel_dict.get('properties'):
                        with contextlib.suppress(BaseException):
                            rel_dict['properties'] = json.loads(rel_dict['properties'])
                    context['related_entities'].append(rel_dict)

            return context

        except Exception as e:
            logger.error(f"获取实体上下文失败: {e}")
            return {}

    def _generate_entity_summary(self, entity: dict, relations: list[dict]) -> str:
        """生成实体摘要"""
        name = entity.get('name', '未知实体')
        entity_type = entity.get('entity_type', '未知类型')

        # 统计关系类型
        relation_types = {}
        for rel in relations:
            rel_type = rel.get('relation_type', '未知关系')
            relation_types[rel_type] = relation_types.get(rel_type, 0) + 1

        # 构建摘要
        summary_parts = [f"{name}是一个{entity_type}"]

        if relation_types:
            relations_desc = ', '.join([f"{count}个{rel_type}" for rel_type, count in relation_types.items()])
            summary_parts.append(f"涉及{relations_desc}")

        return '，'.join(summary_parts) + '。'

    async def enhance_memory_with_knowledge(self, memory_content: str) -> dict[str, Any]:
        """使用知识图谱增强记忆内容"""
        if not self.enable_context_enhancement:
            return {'original': memory_content, 'enhanced': memory_content, 'entities': []}

        # 搜索相关实体
        related_entities = await self.search_related_entities(memory_content)

        if not related_entities:
            return {
                'original': memory_content,
                'enhanced': memory_content,
                'entities': [],
                'context_added': False
            }

        # 构建增强内容
        entity_contexts = []
        for entity in related_entities[:3]:  # 只取前3个最相关的
            context = await self.get_entity_context(entity['entity_id'])
            if context.get('summary'):
                entity_contexts.append(context['summary'])

        # 将实体上下文添加到记忆内容
        if entity_contexts:
            enhanced_content = f"{memory_content}\n\n[相关知识图谱信息]\n' + '\n".join(entity_contexts)
            context_added = True
        else:
            enhanced_content = memory_content
            context_added = False

        return {
            'original': memory_content,
            'enhanced': enhanced_content,
            'entities': related_entities,
            'entity_count': len(related_entities),
            'context_added': context_added
        }

    async def find_knowledge_paths(self, from_entity: str, to_entity: str, max_depth: int = 3) -> list[dict]:
        """在知识图谱中查找两个实体间的路径"""
        if not self.initialized:
            await self.initialize()

        try:
            cursor = self.connection.cursor()

            # 使用递归CTE查找路径
            cursor.execute("""
                WITH RECURSIVE entity_path(
                    from_entity, to_entity, relation_type, depth,
                    path_entities, path_relations, path_str
                ) AS (
                    SELECT from_entity, to_entity, relation_type, 1,
                           [from_entity, to_entity],
                           [relation_type],
                           from_entity || ' -> ' || relation_type || ' -> ' || to_entity
                    FROM relations
                    WHERE from_entity = ?

                    UNION

                    SELECT r.from_entity, r.to_entity, r.relation_type, p.depth + 1,
                           p.path_entities || r.to_entity,
                           p.path_relations || r.relation_type,
                           p.path_str || ' -> ' || r.relation_type || ' -> ' || r.to_entity
                    FROM relations r
                    JOIN entity_path p ON r.from_entity = p.to_entity
                    WHERE p.depth < ? AND r.to_entity NOT IN p.path_entities
                )
                SELECT * FROM entity_path
                WHERE to_entity = ?
                ORDER BY depth, length(path_entities)
                LIMIT 10
            """, (from_entity, max_depth, to_entity))

            paths = []
            for row in cursor.fetchall():
                # 解析JSON数组（SQLite中存储为字符串）
                try:
                    entities = json.loads(row['path_entities']) if isinstance(row['path_entities'], str) else row['path_entities']
                    relations = json.loads(row['path_relations']) if isinstance(row['path_relations'], str) else row['path_relations']
                except Exception:
                    entities = [row['from_entity'], row['to_entity']]
                    relations = [row['relation_type']]

                paths.append({
                    'from': row['from_entity'],
                    'to': row['to_entity'],
                    'depth': row['depth'],
                    'entities': entities,
                    'relations': relations,
                    'path_string': row['path_str']
                })

            return paths

        except Exception as e:
            logger.error(f"查找知识路径失败: {e}")
            return []

    async def get_domain_knowledge(self, domain: str, limit: int = 10) -> list[dict]:
        """获取特定领域的知识"""
        if not self.initialized:
            await self.initialize()

        try:
            cursor = self.connection.cursor()

            # 根据实体类型过滤
            cursor.execute("""
                SELECT * FROM entities
                WHERE entity_type LIKE ? OR name LIKE ?
                ORDER BY
                    CASE WHEN entity_type LIKE ? THEN 1 ELSE 2 END,
                    name
                LIMIT ?
            """, (f"%{domain}%", f"%{domain}%", f"%{domain}%", limit))

            entities = []
            for row in cursor.fetchall():
                entity = dict(row)
                if entity.get('properties'):
                    try:
                        entity['properties'] = json.loads(entity['properties'])
                    except Exception:
                        entity['properties'] = {}
                entities.append(entity)

            return entities

        except Exception as e:
            logger.error(f"获取领域知识失败: {e}")
            return []

    async def shutdown(self):
        """关闭适配器"""
        if self.connection:
            self.connection.close()
            self.initialized = False
            logger.info(f"🔄 知识图谱适配器已关闭: {self.agent_id}")


# 全局适配器实例
_knowledge_adapters = {}

async def get_knowledge_adapter(agent_id: str, config: dict | None = None) -> KnowledgeGraphAdapter:
    """获取知识图谱适配器实例"""
    if agent_id not in _knowledge_adapters:
        adapter = KnowledgeGraphAdapter(agent_id, config)
        await adapter.initialize()
        _knowledge_adapters[agent_id] = adapter

    return _knowledge_adapters[agent_id]

async def shutdown_all_knowledge_adapters():
    """关闭所有知识图谱适配器"""
    for adapter in _knowledge_adapters.values():
        await adapter.shutdown()
    _knowledge_adapters.clear()
