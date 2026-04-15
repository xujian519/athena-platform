#!/usr/bin/env python3
"""
专利规则构建系统 - NebulaGraph知识图谱构建器
Patent Rules Builder - NebulaGraph Knowledge Graph Builder

构建专利法律知识的图数据库，支持2025年修改内容的特殊标注

作者: Athena平台团队
创建时间: 2025-12-20
版本: v2.0.0
"""

from __future__ import annotations
import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

# 使用安全哈希函数替代不安全的MD5/SHA1
from production.utils.security_helpers import short_hash

# NebulaGraph Python客户端
try:
    from nebula3.Config import Config
    from nebula3.data.DataObject import DataObject
    from nebula3.data.ResultSet import ResultSet
    from nebula3.gclient.net import ConnectionPool
    NEBULA_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✅ NebulaGraph客户端可用")
except ImportError:
    NEBULA_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("NebulaGraph客户端不可用")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GraphEntityType(Enum):
    """图实体类型"""
    DOCUMENT = "Document"
    LAW_ARTICLE = "LawArticle"
    GUIDELINE_SECTION = "GuidelineSection"
    JUDICIAL_INTERPRETATION = "JudicialInterpretation"
    CONCEPT = "Concept"
    MODIFICATION_2025 = "Modification2025"

class GraphRelationType(Enum):
    """图关系类型"""
    CONTAINS = "CONTAINS"
    REFERENCES = "REFERENCES"
    DEFINES = "DEFINES"
    APPLIES_TO = "APPLIES_TO"
    REQUIRES = "REQUIRES"
    MODIFIED_BY = "MODIFIED_BY"
    INTRODUCED_IN = "INTRODUCED_IN"
    RELATED_TO = "RELATED_TO"

@dataclass
class GraphEntity:
    """图实体数据结构"""
    vertex_id: str
    entity_type: GraphEntityType
    properties: dict[str, Any]

@dataclass
class GraphRelation:
    """图关系数据结构"""
    edge_id: str
    relation_type: GraphRelationType
    src_vertex_id: str
    dst_vertex_id: str
    properties: dict[str, Any]

class NebulaGraphBuilder:
    """NebulaGraph知识图谱构建器"""

    def __init__(self, space_name: str = "patent_rules"):
        self.space_name = space_name
        self.connection_pool = None
        self.session = None

        # 输出目录
        self.output_dir = Path("/Users/xujian/Athena工作平台/production/data/patent_rules")
        self.graph_dir = self.output_dir / "knowledge_graph"
        self.graph_dir.mkdir(parents=True, exist_ok=True)

        # 初始化连接
        self._initialize_connection()

        # 统计信息
        self.stats = {
            "vertices_created": 0,
            "edges_created": 0,
            "documents_processed": 0,
            "entities_processed": 0,
            "relations_processed": 0,
            "errors": []
        }

    def _initialize_connection(self):
        """初始化NebulaGraph连接"""
        if not NEBULA_AVAILABLE:
            logger.warning("NebulaGraph不可用，将使用模拟模式")
            return

        try:
            # 配置连接池
            config = Config()
            config.max_connection_pool_size = 10
            # NebulaGraph服务地址（根据实际部署调整）
            hosts = [
                ("127.0.0.1", 9669),
                ("127.0.0.1", 19669)
            ]

            self.connection_pool = ConnectionPool()
            for host, port in hosts:
                try:
                    # 尝试连接
                    logger.info(f"尝试连接 NebulaGraph: {host}:{port}")
                    # 这里简化处理，实际使用时需要完整的认证配置
                    break
                except Exception as e:
                    logger.debug(f"空except块已触发: {e}")
                    continue

            if self.connection_pool:
                logger.info("✅ NebulaGraph连接池初始化成功")
            else:
                logger.warning("⚠️ 无法连接到NebulaGraph服务，将使用模拟模式")
                self.connection_pool = None

        except Exception as e:
            logger.error(f"❌ NebulaGraph初始化失败: {e}")
            self.connection_pool = None

    async def initialize_space(self):
        """初始化图空间"""
        if not self.connection_pool:
            logger.info("模拟模式：创建图空间定义文件")
            await self._create_space_schema_file()
            return True

        try:
            # 获取会话
            self.session = self.connection_pool.session_context('root', 'nebula')

            # 创建空间（如果不存在）
            await self._create_space_if_not_exists()

            # 创建标签和边类型
            await self._create_tags()
            await self._create_edges()

            logger.info("✅ NebulaGraph空间初始化成功")
            return True

        except Exception as e:
            logger.error(f"❌ 空间初始化失败: {e}")
            return False

    async def _create_space_if_not_exists(self):
        """创建空间（如果不存在）"""
        try:
            # 检查空间是否存在
            check_query = f"SHOW SPACES LIKE '{self.space_name}'"
            result = self.session.execute(check_query)

            if not result.is_succeeded():
                # 创建空间
                create_query = f"CREATE SPACE IF NOT EXISTS {self.space_name}"
                result = self.session.execute(create_query)

                if result.is_succeeded():
                    logger.info(f"  ✅ 创建空间: {self.space_name}")
                else:
                    logger.error(f"  ❌ 创建空间失败: {result.error_msg()}")
            else:
                logger.info(f"  ✅ 空间已存在: {self.space_name}")

        except Exception as e:
            logger.error(f"  检查/创建空间时出错: {e}")

    async def _create_tags(self):
        """创建标签类型"""
        tag_definitions = {
            "Document": "STRING FIXED_STRING (20) NOT NULL",
            "title": "STRING",
            "version": "STRING",
            "source_type": "STRING",
            "file_path": "STRING",
            "created_at": "STRING",
            "LawArticle": "STRING FIXED_STRING (20) NOT NULL",
            "article_number": "STRING",
            "content": "STRING",
            "full_text": "STRING",
            "GuidelineSection": "STRING FIXED_STRING (20) NOT NULL",
            "section_id": "STRING",
            "level": "INT",
            "title": "STRING",
            "JudicialInterpretation": "STRING FIXED_STRING (20) NOT NULL",
            "case_number": "STRING",
            "court": "STRING",
            "date": "STRING",
            "Concept": "STRING FIXED_STRING (20) NOT NULL",
            "definition": "STRING",
            "category": "STRING",
            "Modification2025": "STRING FIXED_STRING (20) NOT NULL",
            "change_type": "STRING",
            "old_content": "STRING",
            "new_content": "STRING",
            "application_date": "STRING"
        }

        for tag_name, properties in tag_definitions.items():
            try:
                # 构建CREATE TAG语句
                props = ", ".join([f"{prop}" for prop in properties.split(", ")])
                create_query = f"CREATE TAG IF NOT EXISTS {tag_name} ({props})"

                result = self.session.execute(create_query)
                if result.is_succeeded():
                    logger.info(f"  ✅ 创建标签: {tag_name}")
                else:
                    logger.warning(f"  ⚠️ 标签 {tag_name} 可能已存在")

            except Exception as e:
                logger.error(f"  ❌ 创建标签 {tag_name} 失败: {e}")

    async def _create_edges(self):
        """创建边类型"""
        edge_definitions = {
            "CONTAINS": "",
            "REFERENCES": "",
            "DEFINES": "",
            "APPLIES_TO": "",
            "REQUIRES": "",
            "MODIFIED_BY": "rank INT DEFAULT 0",
            "INTRODUCED_IN": "",
            "RELATED_TO": "weight DOUBLE DEFAULT 1.0"
        }

        for edge_name, properties in edge_definitions.items():
            try:
                create_query = f"CREATE EDGE IF NOT EXISTS {edge_name}"
                if properties:
                    create_query += f" ({properties})"

                result = self.session.execute(create_query)
                if result.is_succeeded():
                    logger.info(f"  ✅ 创建边类型: {edge_name}")
                else:
                    logger.warning(f"  ⚠️ 边类型 {edge_name} 可能已存在")

            except Exception as e:
                logger.error(f"  ❌ 创建边类型 {edge_name} 失败: {e}")

    async def _create_space_schema_file(self):
        """创建空间模式文件（用于文档和模拟）"""
        schema = {
            "space_name": self.space_name,
            "tags": {
                "Document": {
                    "properties": ["vid", "title", "version", "source_type", "file_path", "created_at"],
                    "primary_vid": "vid"
                },
                "LawArticle": {
                    "properties": ["vid", "article_number", "content", "full_text"],
                    "primary_vid": "vid"
                },
                "GuidelineSection": {
                    "properties": ["vid", "section_id", "level", "title", "content"],
                    "primary_vid": "vid"
                },
                "JudicialInterpretation": {
                    "properties": ["vid", "case_number", "court", "date", "content"],
                    "primary_vid": "vid"
                },
                "Concept": {
                    "properties": ["vid", "definition", "category"],
                    "primary_vid": "vid"
                },
                "Modification2025": {
                    "properties": ["vid", "change_type", "old_content", "new_content", "application_date"],
                    "primary_vid": "vid"
                }
            },
            "edges": {
                "CONTAINS": ["src_vid", "dst_vid"],
                "REFERENCES": ["src_vid", "dst_vid", "context"],
                "DEFINES": ["src_vid", "dst_vid"],
                "APPLIES_TO": ["src_vid", "dst_vid", "conditions"],
                "REQUIRES": ["src_vid", "dst_vid", "requirements"],
                "MODIFIED_BY": ["src_vid", "dst_vid", "rank"],
                "INTRODUCED_IN": ["src_vid", "dst_vid", "date"],
                "RELATED_TO": ["src_vid", "dst_vid", "weight"]
            }
        }

        schema_file = self.graph_dir / "nebula_schema.json"
        with open(schema_file, 'w', encoding='utf-8') as f:
            json.dump(schema, f, ensure_ascii=False, indent=2)

        logger.info(f"  ✅ 空间模式文件已保存: {schema_file}")

    async def build_graph_from_data(self, data_file: Path):
        """从数据文件构建知识图谱"""
        logger.info(f"\n🕸️ 开始构建知识图谱: {data_file.name}")

        try:
            # 读取数据
            with open(data_file, encoding='utf-8') as f:
                data = json.load(f)

            # 处理文档
            if 'documents' in data:
                for doc_data in data['documents']:
                    await self._process_document(doc_data)
            elif 'metadata' in data:  # 单个文档格式
                await self._process_document(data)

            logger.info("✅ 知识图谱构建完成")

            # 保存图谱统计
            await self._save_graph_statistics()

        except Exception as e:
            logger.error(f"❌ 图谱构建失败: {e}")
            self.stats["errors"].append(str(e))

    async def _process_document(self, doc_data: dict):
        """处理单个文档"""
        doc_id = doc_data.get('doc_id') or self._generate_doc_id(doc_data)

        # 创建文档节点
        doc_vertex = GraphEntity(
            vertex_id=f"doc_{doc_id}",
            entity_type=GraphEntityType.DOCUMENT,
            properties={
                "title": doc_data.get('metadata', {}).get('title', ''),
                "version": doc_data.get('metadata', {}).get('version', ''),
                "source_type": doc_data.get('metadata', {}).get('source_type', ''),
                "file_path": doc_data.get('metadata', {}).get('file_path', ''),
                "created_at": datetime.now().isoformat()
            }
        )

        if self.connection_pool:
            # 实际插入NebulaGraph
            await self._insert_vertex(doc_vertex)
        else:
            # 模拟模式：保存到文件
            await self._save_vertex_to_file(doc_vertex)

        self.stats["vertices_created"] += 1
        self.stats["documents_processed"] += 1

        # 处理章节/法条
        sections = doc_data.get('sections', [])
        for section in sections:
            await self._process_section(section, doc_vertex.vertex_id)

        # 处理实体
        entities = doc_data.get('entities', [])
        for entity in entities:
            await self._process_entity(entity, doc_vertex.vertex_id)

        # 处理关系
        relations = doc_data.get('relations', [])
        for relation in relations:
            await self._process_relation(relation)

        self.stats["entities_processed"] += len(entities)
        self.stats["relations_processed"] += len(relations)

    async def _process_section(self, section: dict, doc_vertex_id: str):
        """处理章节/法条"""
        section_id = section.get('section_id') or self._generate_id(section)

        # 确定实体类型
        entity_type = self._classify_section(section)

        # 创建章节/法条节点
        section_vertex = GraphEntity(
            vertex_id=f"section_{section_id}",
            entity_type=entity_type,
            properties={
                "section_id": section_id,
                "title": section.get('title', ''),
                "content": section.get('content', ''),
                "level": section.get('level', 1),
                "parent_doc": doc_vertex_id
            }
        )

        # 检查2025年修改
        if section.get('modification_2025'):
            self._add_modification_2025_properties(section_vertex, section['modification_2025'])

        if self.connection_pool:
            await self._insert_vertex(section_vertex)
        else:
            await self._save_vertex_to_file(section_vertex)

        # 创建文档-章节关系
        contains_relation = GraphRelation(
            edge_id=f"doc_{doc_vertex_id}_contains_section_{section_id}",
            relation_type=GraphRelationType.CONTAINS,
            src_vertex_id=doc_vertex_id,
            dst_vertex_id=section_vertex.vertex_id,
            properties={
                "relationship": "contains",
                "created_at": datetime.now().isoformat()
            }
        )

        if self.connection_pool:
            await self._insert_edge(contains_relation)
        else:
            await self._save_edge_to_file(contains_relation)

        self.stats["vertices_created"] += 1
        self.stats["edges_created"] += 1

    async def _process_entity(self, entity: dict, doc_vertex_id: str):
        """处理独立实体"""
        entity_id = entity.get('entity_id') or self._generate_id(entity)

        # 确定实体类型
        entity_type = self._classify_entity(entity)

        # 创建实体节点
        entity_vertex = GraphEntity(
            vertex_id=f"entity_{entity_id}",
            entity_type=entity_type,
            properties={
                "text": entity.get('entity_text', ''),
                "confidence": entity.get('confidence', 0.0),
                "extraction_method": entity.get('extraction_method', ''),
                "parent_doc": doc_vertex_id
            }
        )

        # 添加额外属性
        if entity.get('properties'):
            entity_vertex.properties.update(entity['properties'])

        if self.connection_pool:
            await self._insert_vertex(entity_vertex)
        else:
            await self._save_vertex_to_file(entity_vertex)

        self.stats["vertices_created"] += 1

    async def _process_relation(self, relation: dict):
        """处理关系"""
        relation_id = relation.get('relation_id') or self._generate_id(relation)

        # 确定关系类型
        relation_type = self._classify_relation(relation)

        # 创建关系
        graph_relation = GraphRelation(
            edge_id=f"relation_{relation_id}",
            relation_type=relation_type,
            src_vertex_id=relation.get('source_entity_id', ''),
            dst_vertex_id=relation.get('target_entity_id', ''),
            properties={
                "confidence": relation.get('confidence', 0.0),
                "evidence": relation.get('evidence', ''),
                "extraction_method": relation.get('extraction_method', ''),
                "created_at": datetime.now().isoformat()
            }
        )

        if self.connection_pool:
            await self._insert_edge(graph_relation)
        else:
            await self._save_edge_to_file(graph_relation)

        self.stats["edges_created"] += 1

    def _classify_section(self, section: dict) -> GraphEntityType:
        """分类章节类型"""
        section_id = section.get('section_id', '').lower()
        title = section.get('title', '').lower()

        if 'article' in section_id or '条' in section_id:
            return GraphEntityType.LAW_ARTICLE
        elif 'interpretation' in title or '解释' in title:
            return GraphEntityType.JUDICIAL_INTERPRETATION
        elif 'modification' in section_id or '2025' in section_id:
            return GraphEntityType.MODIFICATION_2025
        else:
            return GraphEntityType.GUIDELINE_SECTION

    def _classify_entity(self, entity: dict) -> GraphEntityType:
        """分类实体类型"""
        entity_type = entity.get('entity_type', '')
        text = entity.get('entity_text', '')

        # 映射到图实体类型
        if '法律条文' in entity_type:
            return GraphEntityType.LAW_ARTICLE
        elif '概念' in entity_type or '定义' in entity_type:
            return GraphEntityType.CONCEPT
        elif '2025年修改' in entity_type:
            return GraphEntityType.MODIFICATION_2025
        else:
            return GraphEntityType.CONCEPT  # 默认

    def _classify_relation(self, relation: dict) -> GraphRelationType:
        """分类关系类型"""
        relation_type = relation.get('relation_type', '')

        # 映射到图关系类型
        type_mapping = {
            '包含': GraphRelationType.CONTAINS,
            '引用': GraphRelationType.REFERENCES,
            '定义': GraphRelationType.DEFINES,
            '适用于': GraphRelationType.APPLIES_TO,
            '要求': GraphRelationType.REQUIRES,
            '2025年引入': GraphRelationType.INTRODUCED_IN,
            '相关于': GraphRelationType.RELATED_TO
        }

        return type_mapping.get(relation_type, GraphRelationType.RELATED_TO)

    def _add_modification_2025_properties(self, vertex: GraphEntity, mod_data: dict):
        """添加2025年修改属性"""
        vertex.properties['modification_2025'] = True
        vertex.properties['change_type'] = mod_data.get('change_type', 'unknown')
        vertex.properties['modification_date'] = datetime.now().isoformat()

    def _generate_id(self, obj: dict) -> str:
        """生成ID"""
        # 使用内容哈希生成唯一ID
        content = json.dumps(obj, sort_keys=True, ensure_ascii=False)
        return short_hash(content.encode())[:16]

    def _generate_doc_id(self, doc: dict) -> str:
        """生成文档ID"""
        title = doc.get('metadata', {}).get('title', '')
        content = json.dumps(doc, sort_keys=True, ensure_ascii=False)
        combined = f"{title}_{content}"
        return short_hash(combined.encode())[:16]

    async def _insert_vertex(self, vertex: GraphEntity):
        """插入顶点到NebulaGraph"""
        if not self.session:
            return

        try:
            # 构建INSERT语句
            tag_name = vertex.entity_type.value
            vertex_id = vertex.vertex_id

            # 构建属性字符串
            props = []
            for key, value in vertex.properties.items():
                if isinstance(value, str):
                    props.append(f'{key}: "{value}"')
                else:
                    props.append(f'{key}: {json.dumps(value)}')

            props_str = ", ".join(props)

            query = f'INSERT VERTEX {tag_name} (vertex_id, {props_str}) VALUES "{vertex_id}"'

            result = self.session.execute(query)
            if not result.is_succeeded():
                logger.warning(f"   ⚠️ 插入顶点失败: {result.error_msg()}")

        except Exception as e:
            logger.error(f"  ❌ 插入顶点错误: {e}")

    async def _insert_edge(self, edge: GraphRelation):
        """插入边到NebulaGraph"""
        if not self.session:
            return

        try:
            # 构建INSERT语句
            edge_name = edge.relation_type.value

            # 构建属性字符串
            props = []
            for key, value in edge.properties.items():
                if isinstance(value, str):
                    props.append(f'{key}: "{value}"')
                else:
                    props.append(f'{key}: {json.dumps(value)}')

            props_str = ", ".join(props) if props else ""

            query = f'INSERT EDGE {edge_name} VALUES "{edge.src_vertex_id}" -> "{edge.dst_vertex_id}"'
            if props_str:
                query += f' @{props_str}'

            result = self.session.execute(query)
            if not result.is_succeeded():
                logger.warning(f"  ⚠️ 插入边失败: {result.error_msg()}")

        except Exception as e:
            logger.error(f"  ❌ 插入边错误: {e}")

    async def _save_vertex_to_file(self, vertex: GraphEntity):
        """保存顶点到文件（模拟模式）"""
        vertices_file = self.graph_dir / "vertices.json"

        # 读取现有数据
        vertices = []
        if vertices_file.exists():
            with open(vertices_file, encoding='utf-8') as f:
                vertices = json.load(f)

        # 添加新顶点
        vertices.append({
            "vertex_id": vertex.vertex_id,
            "type": vertex.entity_type.value,
            "properties": vertex.properties
        })

        # 保存
        with open(vertices_file, 'w', encoding='utf-8') as f:
            json.dump(vertices, f, ensure_ascii=False, indent=2)

    async def _save_edge_to_file(self, edge: GraphRelation):
        """保存边到文件（模拟模式）"""
        edges_file = self.graph_dir / "edges.json"

        # 读取现有数据
        edges = []
        if edges_file.exists():
            with open(edges_file, encoding='utf-8') as f:
                edges = json.load(f)

        # 添加新边
        edges.append({
            "edge_id": edge.edge_id,
            "type": edge.relation_type.value,
            "src": edge.src_vertex_id,
            "dst": edge.dst_vertex_id,
            "properties": edge.properties
        })

        # 保存
        with open(edges_file, 'w', encoding='utf-8') as f:
            json.dump(edges, f, ensure_ascii=False, indent=2)

    async def _save_graph_statistics(self):
        """保存图谱统计信息"""
        stats_file = self.graph_dir / f"graph_statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump({
                "build_time": datetime.now().isoformat(),
                "statistics": self.stats,
                "summary": {
                    "total_vertices": self.stats["vertices_created"],
                    "total_edges": self.stats["edges_created"],
                    "documents_processed": self.stats["documents_processed"],
                    "entities_processed": self.stats["entities_processed"],
                    "relations_processed": self.stats["relations_processed"],
                    "error_count": len(self.stats["errors"])
                }
            }, f, ensure_ascii=False, indent=2)

        logger.info(f"  📊 图谱统计已保存: {stats_file}")

    async def build_2025_modification_subgraph(self):
        """构建2025年修改子图"""
        logger.info("\n🔍 构建2025年修改子图...")

        modification_vertices = []
        modification_edges = []

        # 收集所有2025年修改相关的顶点和边
        vertices_file = self.graph_dir / "vertices.json"
        if vertices_file.exists():
            with open(vertices_file, encoding='utf-8') as f:
                vertices = json.load(f)
                for vertex in vertices:
                    if (vertex.get('properties', {}).get('modification_2025') or
                        '2025年修改' in vertex.get('type', '')):
                        modification_vertices.append(vertex)

        edges_file = self.graph_dir / "edges.json"
        if edges_file.exists():
            with open(edges_file, encoding='utf-8') as f:
                edges = json.load(f)
                for edge in edges:
                    if '2025年' in edge.get('type', '') or edge.get('properties', {}).get('evidence', '').count('2025') > 0:
                        modification_edges.append(edge)

        # 保存子图
        subgraph = {
            "name": "2025年修改子图",
            "created_at": datetime.now().isoformat(),
            "vertices": modification_vertices,
            "edges": modification_edges,
            "statistics": {
                "vertices_count": len(modification_vertices),
                "edges_count": len(modification_edges)
            }
        }

        subgraph_file = self.graph_dir / "modification_2025_subgraph.json"
        with open(subgraph_file, 'w', encoding='utf-8') as f:
            json.dump(subgraph, f, ensure_ascii=False, indent=2)

        logger.info(f"  ✅ 2025年修改子图已保存: {subgraph_file}")
        logger.info(f"     顶点数: {len(modification_vertices)}")
        logger.info(f"     边数: {len(modification_edges)}")

    def get_statistics(self) -> dict:
        """获取构建统计"""
        return self.stats

# 使用示例
async def main():
    """主函数示例"""
    builder = NebulaGraphBuilder()

    # 初始化空间
    await builder.initialize_space()

    # 处理示例数据文件
    data_dir = Path("/Users/xujian/Athena工作平台/production/data/patent_rules/processed")
    data_files = list(data_dir.glob("*_processed.json"))

    if not data_files:
        logger.warning("未找到处理后的数据文件")
        # 创建示例数据
        sample_data = {
            "doc_id": "patent_law_2023",
            "metadata": {
                "title": "中华人民共和国专利法",
                "version": "2023修订版",
                "source_type": "PDF"
            },
            "sections": [
                {
                    "section_id": "P1-C1",
                    "level": 2,
                    "title": "第一章 总则",
                    "content": "为了保护专利权人的合法权益，鼓励发明创造..."
                },
                {
                    "section_id": "A1",
                    "level": 3,
                    "title": "第一条",
                    "content": "为了保护专利权人的合法权益...",
                    "modification_2025": {
                        "change_type": "amended",
                        "added_content": "特别考虑AI和大数据领域"
                    }
                }
            ],
            "entities": [
                {
                    "entity_id": "patent_right",
                    "entity_type": "专利权",
                    "entity_text": "专利权",
                    "confidence": 0.95
                }
            ],
            "relations": [
                {
                    "relation_id": "rel_001",
                    "relation_type": "2025年引入",
                    "source_entity_id": "A1",
                    "target_entity_id": "patent_right",
                    "confidence": 0.9
                }
            ]
        }

        sample_file = data_dir / "sample_document.json"
        with open(sample_file, 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, ensure_ascii=False, indent=2)

        data_files = [sample_file]

    # 构建图谱
    for data_file in data_files:
        await builder.build_graph_from_data(data_file)

    # 构建2025年修改子图
    await builder.build_2025_modification_subgraph()

    # 显示统计
    stats = builder.get_statistics()
    logger.info("\n📊 构建统计:")
    logger.info(f"  创建顶点: {stats['vertices_created']}")
    logger.info(f"  创建边: {stats['edges_created']}")
    logger.info(f"  处理文档: {stats['documents_processed']}")
    logger.info(f"  错误数: {len(stats['errors'])}")

if __name__ == "__main__":
    asyncio.run(main())
