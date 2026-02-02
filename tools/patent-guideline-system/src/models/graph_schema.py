#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识图谱Schema定义
Knowledge Graph Schema Definition

定义专利审查指南知识图谱的结构和操作
"""

import logging
from enum import Enum
from typing import Any, Dict, List, Optional

from neo4j import Driver, GraphDatabase
from pydantic import BaseModel

# 配置日志
logger = logging.getLogger(__name__)

class NodeType(Enum):
    """节点类型枚举"""
    DOCUMENT = 'Document'
    PART = 'Part'
    CHAPTER = 'Chapter'
    SECTION = 'Section'
    CONCEPT = 'Concept'
    LAW_ARTICLE = 'LawArticle'
    CASE = 'Case'
    REFERENCE = 'Reference'

class RelationshipType(Enum):
    """关系类型枚举"""
    # 结构关系
    HAS_PART = 'HAS_PART'
    HAS_CHAPTER = 'HAS_CHAPTER'
    HAS_SECTION = 'HAS_SECTION'
    PARENT_OF = 'PARENT_OF'
    CHILD_OF = 'CHILD_OF'

    # 引用关系
    REFERS_TO = 'REFERS_TO'
    REFERENCED_BY = 'REFERENCED_BY'
    CITES = 'CITES'
    CITED_BY = 'CITED_BY'

    # 内容关系
    BASED_ON = 'BASED_ON'
    MENTIONS = 'MENTIONS'
    DEFINES = 'DEFINES'
    EXPLAINS = 'EXPLAINS'

    # 案例关系
    CONTAINS_EXAMPLE = 'CONTAINS_EXAMPLE'
    ILLUSTRATES = 'ILLUSTRATES'
    EXAMPLE_OF = 'EXAMPLE_OF'

    # 逻辑关系
    CONDITION_FOR = 'CONDITION_FOR'
    REQUIREMENT_FOR = 'REQUIREMENT_FOR'
    EXCEPTION_TO = 'EXCEPTION_TO'
    ALTERNATIVE_TO = 'ALTERNATIVE_TO'
    COMPLEMENTS = 'COMPLEMENTS'

class GraphNode(BaseModel):
    """图谱节点基类"""
    id: str
    labels: List[str] = []
    properties: Dict[str, Any] = {}

class DocumentNode(GraphNode):
    """文档节点"""
    title: str
    version: str
    publication_date: str | None = None
    total_pages: int | None = None

class PartNode(GraphNode):
    """部分节点"""
    number: int
    title: str
    description: str | None = None

class ChapterNode(GraphNode):
    """章节节点"""
    number: int
    title: str
    summary: str | None = None

class SectionNode(GraphNode):
    """章节节点"""
    number: str
    title: str
    content: str
    level: int
    start_page: int | None = None
    end_page: int | None = None
    word_count: int | None = None
    parent_id: str | None = None
    hierarchy_path: List[str] = []

class ConceptNode(GraphNode):
    """概念节点"""
    name: str
    definition: str | None = None
    category: str | None = None
    synonyms: List[str] = []

class LawArticleNode(GraphNode):
    """法条节点"""
    law_name: str
    article_number: int
    content: str | None = None
    article_type: str | None = None

class CaseNode(GraphNode):
    """案例节点"""
    case_id: str
    title: str
    content: str
    summary: str | None = None

class Neo4jSchemaManager:
    """Neo4j Schema管理器"""

    def __init__(self, uri='bolt://localhost:7687', username='neo4j', password=os.getenv("DB_PASSWORD", "password"), database='patent_guidelines'):
        """初始化Schema管理器

        Args:
            uri: Neo4j URI
            username: 用户名
            password: 密码
            database: 数据库名称
        """
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.session = self.driver.session(database=database)

    def create_constraints(self):
        """创建约束"""
        logger.info('创建数据库约束')

        constraints = [
            'CREATE CONSTRAINT ON (d:Document) ASSERT d.id IS UNIQUE',
            'CREATE CONSTRAINT ON (p:Part) ASSERT p.id IS UNIQUE',
            'CREATE CONSTRAINT ON (c:Chapter) ASSERT c.id IS UNIQUE',
            'CREATE CONSTRAINT ON (s:Section) ASSERT s.id IS UNIQUE',
            'CREATE CONSTRAINT ON (co:Concept) ASSERT co.name IS UNIQUE',
            'CREATE CONSTRAINT ON (la:LawArticle) ASSERT la.id IS UNIQUE',
            'CREATE CONSTRAINT ON (ca:Case) ASSERT ca.id IS UNIQUE'
        ]

        for constraint in constraints:
            try:
                self.session.run(constraint)
                logger.info(f"约束创建成功: {constraint}")
            except Exception as e:
                logger.warning(f"约束可能已存在: {constraint}")

    def create_indexes(self):
        """创建索引"""
        logger.info('创建索引')

        indexes = [
            'CREATE INDEX section_level_index IF NOT EXISTS FOR (s:Section) ON (s.level)',
            'CREATE INDEX section_title_index IF NOT EXISTS FOR (s:Section) ON (s.title)',
            'CREATE INDEX concept_category_index IF NOT EXISTS FOR (co:Concept) ON (co.category)',
            'CREATE INDEX law_article_number_index IF NOT EXISTS FOR (la:LawArticle) ON (la.article_number)',
            'CREATE INDEX case_case_id_index IF NOT EXISTS FOR (ca:Case) ON (ca.case_id)'
        ]

        for index in indexes:
            try:
                self.session.run(index)
                logger.info(f"索引创建成功: {index}")
            except Exception as e:
                logger.warning(f"索引可能已存在: {index}")

    def create_document_node(self, node: DocumentNode):
        """创建文档节点

        Args:
            node: 文档节点
        """
        cypher = """
        CREATE (d:Document {
            id: $id,
            title: $title,
            version: $version,
            publicationDate: $publicationDate,
            totalPages: $totalPages
        })
        """

        self.session.run(cypher, {
            'id': node.id,
            'title': node.title,
            'version': node.version,
            'publicationDate': node.publication_date,
            'totalPages': node.total_pages
        })

    def create_part_node(self, node: PartNode, document_id: str):
        """创建部分节点

        Args:
            node: 部分节点
            document_id: 文档ID
        """
        cypher = """
        CREATE (p:Part {
            id: $id,
            number: $number,
            title: $title,
            description: $description
        })
        """

        self.session.run(cypher, {
            'id': node.id,
            'number': node.number,
            'title': node.title,
            'description': node.description
        })

        # 创建与文档的关系
        relation_cypher = """
        MATCH (d:Document {id: $documentId})
        MATCH (p:Part {id: $partId})
        CREATE (d)-[:HAS_PART]->(p)
        """

        self.session.run(relation_cypher, {
            'documentId': document_id,
            'partId': node.id
        })

    def create_chapter_node(self, node: ChapterNode, part_id: str):
        """创建章节节点

        Args:
            node: 章节节点
            part_id: 部分ID
        """
        cypher = """
        CREATE (c:Chapter {
            id: $id,
            number: $number,
            title: $title,
            summary: $summary
        })
        """

        self.session.run(cypher, {
            'id': node.id,
            'number': node.number,
            'title': node.title,
            'summary': node.summary
        })

        # 创建与部分的关系
        relation_cypher = """
        MATCH (p:Part {id: $partId})
        MATCH (c:Chapter {id: $chapterId})
        CREATE (p)-[:HAS_CHAPTER]->(c)
        """

        self.session.run(relation_cypher, {
            'partId': part_id,
            'chapterId': node.id
        })

    def create_section_node(self, node: SectionNode, parent_id: str | None = None):
        """创建章节节点

        Args:
            node: 章节节点
            parent_id: 父节点ID
        """
        cypher = """
        CREATE (s:Section {
            id: $id,
            number: $number,
            title: $title,
            content: $content,
            level: $level,
            startPage: $startPage,
            endPage: $endPage,
            wordCount: $wordCount,
            hierarchyPath: $hierarchyPath
        })
        """

        self.session.run(cypher, {
            'id': node.id,
            'number': node.number,
            'title': node.title,
            'content': node.content,
            'level': node.level,
            'startPage': node.start_page,
            'endPage': node.end_page,
            'wordCount': node.word_count,
            'hierarchyPath': node.hierarchy_path
        })

        # 创建与父节点的关系
        if parent_id:
            relation_cypher = """
            MATCH (parent {id: $parentId})
            MATCH (s:Section {id: $sectionId})
            CREATE (parent)-[:HAS_SECTION]->(s)
            """

            self.session.run(relation_cypher, {
                'parentId': parent_id,
                'sectionId': node.id
            })

    def create_concept_node(self, node: ConceptNode):
        """创建概念节点

        Args:
            node: 概念节点
        """
        cypher = """
        CREATE (co:Concept {
            name: $name,
            definition: $definition,
            category: $category,
            synonyms: $synonyms
        })
        """

        self.session.run(cypher, {
            'name': node.name,
            'definition': node.definition,
            'category': node.category,
            'synonyms': node.synonyms
        })

    def create_law_article_node(self, node: LawArticleNode):
        """创建法条节点

        Args:
            node: 法条节点
        """
        cypher = """
        CREATE (la:LawArticle {
            id: $id,
            lawName: $lawName,
            articleNumber: $articleNumber,
            content: $content,
            articleType: $articleType
        })
        """

        self.session.run(cypher, {
            'id': node.id,
            'lawName': node.law_name,
            'articleNumber': node.article_number,
            'content': node.content,
            'articleType': node.article_type
        })

    def create_case_node(self, node: CaseNode):
        """创建案例节点

        Args:
            node: 案例节点
        """
        cypher = """
        CREATE (ca:Case {
            id: $id,
            caseId: $caseId,
            title: $title,
            content: $content,
            summary: $summary
        })
        """

        self.session.run(cypher, {
            'id': node.id,
            'caseId': node.case_id,
            'title': node.title,
            'content': node.content,
            'summary': node.summary
        })

    def create_reference_relationship(
        self,
        source_id: str,
        target_id: str,
        reference_type: str,
        context: str | None = None,
        position: int | None = None
    ):
        """创建引用关系

        Args:
            source_id: 源节点ID
            target_id: 目标节点ID
            reference_type: 引用类型
            context: 引用上下文
            position: 引用位置
        """
        cypher = f"""
        MATCH (source {{id: $sourceId}})
        MATCH (target {{id: $targetId}})
        CREATE (source)-[:{reference_type}]->(target)
        """

        self.session.run(cypher, {
            'sourceId': source_id,
            'targetId': target_id
        })

        # 添加引用详细信息
        if context or position is not None:
            detail_cypher = f"""
            MATCH (source {{id: $sourceId}})-[r:{reference_type}]->(target {{id: $targetId}})
            SET r.context = $context, r.position = $position
            """

            self.session.run(detail_cypher, {
                'sourceId': source_id,
                'targetId': target_id,
                'context': context,
                'position': position
            })

    def build_hierarchy_relationships(self, sections: List[Dict]):
        """构建层级关系

        Args:
            sections: 章节列表
        """
        logger.info('构建层级关系')

        # 根据层级和编号建立父子关系
        for section in sections:
            section_id = section.get('id')
            parent_id = section.get('parent_id')
            level = section.get('level', 0)

            if parent_id:
                self.create_reference_relationship(
                    source_id=section_id,
                    target_id=parent_id,
                    reference_type='PARENT_OF'
                )

                self.create_reference_relationship(
                    source_id=parent_id,
                    target_id=section_id,
                    reference_type='CHILD_OF'
                )

    def close(self):
        """关闭连接"""
        self.session.close()
        self.driver.close()

# 测试函数
def test_schema():
    """测试Schema创建"""
    logger.info('=== 测试Neo4j知识图谱Schema ===')

    try:
        # 创建Schema管理器
        schema_manager = Neo4jSchemaManager()

        # 创建约束
        logger.info("\n1. 创建约束...")
        schema_manager.create_constraints()

        # 创建索引
        logger.info("\n2. 创建索引...")
        schema_manager.create_indexes()

        # 创建测试节点
        logger.info("\n3. 创建测试节点...")

        # 文档节点
        doc_node = DocumentNode(
            id='doc_001',
            title='专利审查指南（最新版）',
            version='2024版',
            total_pages=600
        )
        schema_manager.create_document_node(doc_node)

        # 部分节点
        part_node = PartNode(
            id='part_1',
            number=1,
            title='第一部分 初步审查'
        )
        schema_manager.create_part_node(part_node, 'doc_001')

        # 章节节点
        chapter_node = ChapterNode(
            id='chapter_1_1',
            number=1,
            title='第一章 发明专利申请的初步审查'
        )
        schema_manager.create_chapter_node(chapter_node, 'part_1')

        logger.info("\n✅ Schema创建成功！")

        # 关闭连接
        schema_manager.close()

    except Exception as e:
        logger.info(f"\n❌ 测试失败: {e}")
        import traceback

# 导入安全配置
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "core"))
from security.env_config import get_env_var, get_database_url, get_jwt_secret
        traceback.print_exc()

if __name__ == '__main__':
    test_schema()