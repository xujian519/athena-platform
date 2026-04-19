#!/usr/bin/env python3
"""
NebulaGraph知识图谱构建器 - 集成版本
NebulaGraph Knowledge Graph Builder - Integrated Version

集成了真实NebulaGraph连接和文件模拟的双模式

作者: Athena平台团队
创建时间: 2025-12-20
版本: v2.0.0
"""

from __future__ import annotations
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

class NebulaGraphBuilderIntegrated:
    """NebulaGraph知识图谱构建器 - 集成版本"""

    def __init__(self, use_real_nebula: bool = True):
        """
        初始化知识图谱构建器

        Args:
            use_real_nebula: 是否使用真实的NebulaGraph数据库
        """
        self.use_real_nebula = use_real_nebula
        self.space_name = "patent_rules"
        self.output_path = Path("/Users/xujian/Athena工作平台/production/data/patent_rules/knowledge_graph")
        self.output_path.mkdir(parents=True, exist_ok=True)

        # 尝试导入真实NebulaGraph客户端
        self.real_nebula = None
        if self.use_real_nebula:
            try:
                from .nebula_graph_builder_sync import NebulaGraphBuilderSync
                self.real_nebula = NebulaGraphBuilderSync(space_name=self.space_name)
                logger.info("✅ 已加载真实NebulaGraph客户端")
            except Exception as e:
                logger.warning(f"⚠️ 无法加载真实NebulaGraph客户端: {str(e)}")
                self.use_real_nebula = False

        if not self.use_real_nebula:
            logger.info("✅ 使用文件模拟模式")

    async def initialize_space(self):
        """初始化图空间"""
        if self.use_real_nebula and self.real_nebula:
            try:
                return self.real_nebula.initialize_space()
            except Exception as e:
                logger.warning(f"⚠️ 真实NebulaGraph初始化失败，回退到模拟模式: {str(e)}")
                self.use_real_nebula = False

        # 模拟模式
        logger.info("📝 模拟模式：创建图空间定义文件")
        return self._create_schema_file()

    async def add_entities(self, entities: list[dict[str, Any]]) -> list[str]:
        """添加实体"""
        if self.use_real_nebula and self.real_nebula:
            try:
                entity_ids = self.real_nebula.add_entities(entities)
                logger.info(f"✅ 真实NebulaGraph：添加 {len(entity_ids)} 个实体")
                return entity_ids
            except Exception as e:
                logger.warning(f"⚠️ 真实NebulaGraph添加实体失败: {str(e)}")

        # 模拟模式 - 保存到文件
        logger.info(f"📝 模拟模式：保存 {len(entities)} 个实体到文件")
        return self._save_entities_to_file(entities)

    async def add_relations(self, relations: list[dict[str, Any]]) -> list[str]:
        """添加关系"""
        if self.use_real_nebula and self.real_nebula:
            try:
                relation_ids = self.real_nebula.add_relations(relations)
                logger.info(f"✅ 真实NebulaGraph：添加 {len(relation_ids)} 个关系")
                return relation_ids
            except Exception as e:
                logger.warning(f"⚠️ 真实NebulaGraph添加关系失败: {str(e)}")

        # 模拟模式 - 保存到文件
        logger.info(f"📝 模拟模式：保存 {len(relations)} 个关系到文件")
        return self._save_relations_to_file(relations)

    async def build_subgraph(self, entity_names: list[str], depth: int = 2):
        """构建子图"""
        if self.use_real_nebula and self.real_nebula:
            try:
                logger.info(f"✅ 真实NebulaGraph：构建子图，深度 {depth}")
                # 这里可以实现真实的子图查询
                # subgraph = self.real_nebula.query_subgraph(entity_names, depth)
                # return subgraph
            except Exception as e:
                logger.warning(f"⚠️ 真实NebulaGraph构建子图失败: {str(e)}")

        # 模拟模式
        logger.info("📝 模拟模式：创建子图示例文件")
        self._create_subgraph_example(entity_names, depth)

    def _create_schema_file(self):
        """创建图模式定义文件"""
        schema = {
            "space_name": self.space_name,
            "created_at": datetime.now().isoformat(),
            "tags": {
                "patent": {
                    "description": "专利实体",
                    "properties": [
                        {"name": "patent_type", "type": "string"},
                        {"name": "app_date", "type": "string"},
                        {"name": "grant_date", "type": "string"},
                        {"name": "inventor", "type": "string"},
                        {"name": "assignee", "type": "string"},
                        {"name": "ipc", "type": "string"},
                        {"name": "confidence", "type": "double"},
                        {"name": "source", "type": "string"}
                    ]
                },
                "legal_term": {
                    "description": "法律术语",
                    "properties": [
                        {"name": "definition", "type": "string"},
                        {"name": "category", "type": "string"},
                        {"name": "source", "type": "string"},
                        {"name": "confidence", "type": "double"}
                    ]
                },
                "tech_field": {
                    "description": "技术领域",
                    "properties": [
                        {"name": "description", "type": "string"},
                        {"name": "keywords", "type": "string"},
                        {"name": "level", "type": "string"},
                        {"name": "confidence", "type": "double"}
                    ]
                },
                "document": {
                    "description": "文档",
                    "properties": [
                        {"name": "title", "type": "string"},
                        {"name": "doc_type", "type": "string"},
                        {"name": "publish_date", "type": "string"},
                        {"name": "source", "type": "string"},
                        {"name": "confidence", "type": "double"}
                    ]
                }
            },
            "edge_types": {
                "regulates": {
                    "description": "规范关系",
                    "properties": [
                        {"name": "scope", "type": "string"},
                        {"name": "article", "type": "string"},
                        {"name": "confidence", "type": "double"}
                    ]
                },
                "applies_to": {
                    "description": "应用关系",
                    "properties": [
                        {"name": "context", "type": "string"},
                        {"name": "relevance", "type": "double"},
                        {"name": "confidence", "type": "double"}
                    ]
                },
                "related_to": {
                    "description": "相关关系",
                    "properties": [
                        {"name": "relation_type", "type": "string"},
                        {"name": "strength", "type": "double"},
                        {"name": "confidence", "type": "double"}
                    ]
                },
                "refers_to": {
                    "description": "引用关系",
                    "properties": [
                        {"name": "relationship_type", "type": "string"},
                        {"name": "confidence", "type": "double"}
                    ]
                }
            }
        }

        schema_file = self.output_path / "nebula_schema.json"
        with open(schema_file, 'w', encoding='utf-8') as f:
            json.dump(schema, f, ensure_ascii=False, indent=2)

        logger.info(f"  ✅ 空间模式文件已保存: {schema_file}")
        return True

    def _save_entities_to_file(self, entities: list[dict[str, Any]]) -> list[str]:
        """保存实体到文件"""
        # 转换实体格式
        formatted_entities = []
        entity_ids = []

        for entity in entities:
            formatted_entity = {
                "name": entity.get('name', entity.get('text', '')),
                "type": entity.get('type', ''),
                "properties": entity.get('properties', {})
            }
            if formatted_entity["name"]:
                formatted_entities.append(formatted_entity)
                entity_ids.append(formatted_entity["name"])

        # 按类型分组保存
        entities_by_type = {}
        for entity in formatted_entities:
            etype = entity['type']
            if etype not in entities_by_type:
                entities_by_type[etype] = []
            entities_by_type[etype].append(entity)

        for etype, entity_list in entities_by_type.items():
            entities_file = self.output_path / f"entities_{etype}.json"
            with open(entities_file, 'w', encoding='utf-8') as f:
                json.dump(entity_list, f, ensure_ascii=False, indent=2)
            logger.info(f"  ✅ 保存 {len(entity_list)} 个 {etype} 实体到 {entities_file}")

        return entity_ids

    def _save_relations_to_file(self, relations: list[dict[str, Any]]) -> list[str]:
        """保存关系到文件"""
        # 转换关系格式
        formatted_relations = []
        relation_ids = []

        for relation in relations:
            formatted_relation = {
                "subject": relation.get('subject', ''),
                "object": relation.get('object', ''),
                "relation": relation.get('relation', ''),
                "properties": relation.get('properties', {})
            }
            if formatted_relation["subject"] and formatted_relation["object"]:
                formatted_relations.append(formatted_relation)
                relation_ids.append(f"{formatted_relation['subject']}-{formatted_relation['object']}")

        # 按类型分组保存
        relations_by_type = {}
        for relation in formatted_relations:
            rtype = relation['relation']
            if rtype not in relations_by_type:
                relations_by_type[rtype] = []
            relations_by_type[rtype].append(relation)

        for rtype, relation_list in relations_by_type.items():
            relations_file = self.output_path / f"relations_{rtype}.json"
            with open(relations_file, 'w', encoding='utf-8') as f:
                json.dump(relation_list, f, ensure_ascii=False, indent=2)
            logger.info(f"  ✅ 保存 {len(relation_list)} 个 {rtype} 关系到 {relations_file}")

        return relation_ids

    def _create_subgraph_example(self, entity_names: list[str], depth: int):
        """创建子图示例"""
        subgraph = {
            "query_entities": entity_names,
            "depth": depth,
            "nodes": [],
            "edges": [],
            "created_at": datetime.now().isoformat()
        }

        # 添加查询实体
        for name in entity_names[:5]:  # 限制数量
            subgraph["nodes"].append({
                "id": name,
                "type": "query_entity",
                "properties": {
                    "depth": 0,
                    "highlighted": True
                }
            })

        # 添加示例边
        if len(entity_names) >= 2:
            subgraph["edges"].append({
                "source": entity_names[0],
                "target": entity_names[1],
                "type": "related_to",
                "properties": {
                    "confidence": 0.9,
                    "depth": 1
                }
            })

        subgraph_file = self.output_path / "subgraph_example.json"
        with open(subgraph_file, 'w', encoding='utf-8') as f:
            json.dump(subgraph, f, ensure_ascii=False, indent=2)

        logger.info(f"  ✅ 子图示例已保存: {subgraph_file}")

    def get_statistics(self) -> dict[str, Any]:
        """获取图谱统计信息"""
        if self.use_real_nebula and self.real_nebula:
            try:
                stats = self.real_nebula.get_graph_stats()
                stats["mode"] = "real_nebula"
                return stats
            except Exception as e:
                logger.warning(f"⚠️ 获取真实NebulaGraph统计失败: {str(e)}")

        # 模拟模式 - 从文件统计
        stats = {
            "mode": "simulation",
            "entities": {},
            "relations": {},
            "total_entities": 0,
            "total_relations": 0
        }

        # 统计实体
        for entity_file in self.output_path.glob("entities_*.json"):
            etype = entity_file.stem.split("_")[1]
            try:
                with open(entity_file, encoding='utf-8') as f:
                    entities = json.load(f)
                    stats["entities"][etype] = len(entities)
                    stats["total_entities"] += len(entities)
            except Exception as e:
                logger.debug(f"空except块已触发: {e}")
                pass

        # 统计关系
        for relation_file in self.output_path.glob("relations_*.json"):
            rtype = relation_file.stem.split("_")[1]
            try:
                with open(relation_file, encoding='utf-8') as f:
                    relations = json.load(f)
                    stats["relations"][rtype] = len(relations)
            except Exception as e:
                logger.debug(f"空except块已触发: {e}")

        return stats


# 兼容原接口的包装器
class NebulaGraphBuilder(NebulaGraphBuilderIntegrated):
    """NebulaGraph知识图谱构建器 - 兼容包装器"""
    pass
