#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Neo4j专利知识图谱管理器
Neo4j Patent Knowledge Graph Manager

负责将抽取的实体和关系导入Neo4j图数据库，并提供查询功能
Responsible for importing extracted entities and relationships into Neo4j graph database and providing query functionality

作者: Athena AI系统
创建时间: 2025年12月6日
版本: 1.0.0
"""

import json
import logging
import os
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# Neo4j驱动
try:
    from neo4j import Driver, GraphDatabase, Session
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logger.info('警告: neo4j库未安装，Neo4j功能不可用')
    GraphDatabase = None
    Driver = None
    Session = None

from patent_knowledge_extractor import ExtractionResult

# 本地模块
from patent_knowledge_graph_schema import (
    EntityType,
    KnowledgeEntity,
    KnowledgeRelation,
    PatentKnowledgeGraphSchema,
    RelationType,
)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Neo4jManager:
    """Neo4j图数据库管理器"""

    def __init__(self, uri: str = 'bolt://localhost:7687',
                 username: str = 'neo4j', password: str = 'password',
                 database: str = 'patent_kg'):
        """
        初始化Neo4j管理器

        Args:
            uri: Neo4j服务器URI
            username: 用户名
            password: 密码
            database: 数据库名称
        """
        if not NEO4J_AVAILABLE:
            raise ImportError('neo4j库未安装，请使用: pip install neo4j')

        self.uri = uri
        self.username = username
        self.password = password
        self.database = database
        self.driver: Driver | None = None
        self.schema = PatentKnowledgeGraphSchema()

        # 导入统计
        self.import_stats = {
            'total_entities': 0,
            'total_relations': 0,
            'imported_entities': 0,
            'imported_relations': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }

    def connect(self):
        """连接到Neo4j数据库"""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
            # 测试连接
            with self.driver.session(database=self.database) as session:
                session.run('RETURN 1')
            logger.info(f"成功连接到Neo4j数据库: {self.uri}")
            return True
        except Exception as e:
            logger.error(f"连接Neo4j失败: {str(e)}")
            return False

    def close(self):
        """关闭数据库连接"""
        if self.driver:
            self.driver.close()
            logger.info('Neo4j连接已关闭')

    def create_schema(self):
        """创建知识图谱模式"""
        if not self.driver:
            raise RuntimeError('未连接到Neo4j数据库')

        logger.info('开始创建知识图谱模式...')

        with self.driver.session(database=self.database) as session:
            try:
                # 创建约束（确保实体唯一性）
                self._create_constraints(session)

                # 创建索引（提高查询性能）
                self._create_indexes(session)

                logger.info('知识图谱模式创建完成')
                return True

            except Exception as e:
                logger.error(f"创建模式失败: {str(e)}")
                return False

    def _create_constraints(self, session: Session):
        """创建实体约束"""
        constraints = [
            # 通用实体唯一性约束
            'CREATE CONSTRAINT entity_id_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE',

            # 法律相关实体约束
            'CREATE CONSTRAINT law_unique IF NOT EXISTS FOR (l:Law) REQUIRE l.name IS UNIQUE',
            'CREATE CONSTRAINT legal_article_unique IF NOT EXISTS FOR (la:LegalArticle) REQUIRE la.name IS UNIQUE',

            # 案例相关实体约束
            'CREATE CONSTRAINT case_unique IF NOT EXISTS FOR (c:Case) REQUIRE c.case_number IS UNIQUE',
            'CREATE CONSTRAINT invalidation_unique IF NOT EXISTS FOR (i:InvalidationDecision) REQUIRE i.case_number IS UNIQUE',
            'CREATE CONSTRAINT reexamination_unique IF NOT EXISTS FOR (r:ReexaminationDecision) REQUIRE r.case_number IS UNIQUE',

            # 专利相关实体约束
            'CREATE CONSTRAINT patent_unique IF NOT EXISTS FOR (p:Patent) REQUIRE p.patent_number IS UNIQUE',
            'CREATE CONSTRAINT applicant_unique IF NOT EXISTS FOR (a:Applicant) REQUIRE a.name IS UNIQUE',
            'CREATE CONSTRAINT patent_holder_unique IF NOT EXISTS FOR (ph:PatentHolder) REQUIRE ph.name IS UNIQUE'
        ]

        for constraint in constraints:
            try:
                session.run(constraint)
                logger.debug(f"创建约束: {constraint}")
            except Exception as e:
                logger.warning(f"约束可能已存在: {str(e)}")

    def _create_indexes(self, session: Session):
        """创建索引"""
        indexes = [
            # 通用索引
            'CREATE INDEX entity_type_index IF NOT EXISTS FOR (e:Entity) ON (e.type)',
            'CREATE INDEX entity_name_index IF NOT EXISTS FOR (e:Entity) ON (e.name)',

            # 关系索引
            'CREATE INDEX relation_type_index IF NOT EXISTS FOR ()-[r]-() ON (r.type)',

            # 时间索引
            'CREATE INDEX entity_created_at_index IF NOT EXISTS FOR (e:Entity) ON (e.created_at)',

            # 专用索引
            'CREATE INDEX law_issuing_authority_index IF NOT EXISTS FOR (l:Law) ON (l.issuing_authority)',
            'CREATE INDEX case_decision_date_index IF NOT EXISTS FOR (c:Case) ON (c.decision_date)',
            'CREATE INDEX patent_application_date_index IF NOT EXISTS FOR (p:Patent) ON (p.application_date)'
        ]

        for index in indexes:
            try:
                session.run(index)
                logger.debug(f"创建索引: {index}")
            except Exception as e:
                logger.warning(f"索引可能已存在: {str(e)}")

    def import_entities(self, entities: List[KnowledgeEntity], batch_size: int = 1000) -> Dict[str, Any]:
        """批量导入实体"""
        if not self.driver:
            raise RuntimeError('未连接到Neo4j数据库')

        logger.info(f"开始导入 {len(entities)} 个实体...")
        self.import_stats['start_time'] = datetime.now()

        success_count = 0
        error_count = 0

        with self.driver.session(database=self.database) as session:
            for i in range(0, len(entities), batch_size):
                batch = entities[i:i + batch_size]

                for entity in batch:
                    try:
                        self._import_single_entity(session, entity)
                        success_count += 1
                    except Exception as e:
                        error_count += 1
                        logger.error(f"导入实体失败 {entity.id}: {str(e)}")

                logger.info(f"已处理 {min(i + batch_size, len(entities))}/{len(entities)} 个实体")

        self.import_stats['imported_entities'] += success_count
        self.import_stats['errors'] += error_count

        logger.info(f"实体导入完成: 成功 {success_count}, 失败 {error_count}")

        return {
            'success_count': success_count,
            'error_count': error_count,
            'total_processed': len(entities)
        }

    def _import_single_entity(self, session: Session, entity: KnowledgeEntity):
        """导入单个实体"""
        # 根据实体类型确定标签
        labels = self._get_entity_labels(entity.type)

        # 构建属性字典
        properties = {
            'id': entity.id,
            'name': entity.name,
            'type': entity.type.value,
            'description': entity.description,
            'source': entity.source,
            'confidence': entity.confidence,
            'created_at': entity.created_at.isoformat() if entity.created_at else None,
            'updated_at': entity.updated_at.isoformat() if entity.updated_at else None
        }

        # 添加特定类型的属性
        if entity.properties:
            properties.update(entity.properties)

        # 构建Cypher查询
        properties_str = ', '.join([f"{k}: {self._format_value(v)}" for k, v in properties.items()])
        labels_str = ':'.join(labels)

        cypher = f"""
        MERGE (e:{labels_str} {{id: $id}})
        ON CREATE SET e += $properties
        ON MATCH SET e += $properties
        """

        session.run(cypher, id=entity.id, properties=properties)

    def _get_entity_labels(self, entity_type: EntityType) -> List[str]:
        """获取实体标签"""
        # 所有实体都有Entity基础标签
        labels = ['Entity']

        # 根据实体类型添加特定标签
        type_labels = {
            EntityType.LAW: ['Law'],
            EntityType.REGULATION: ['Regulation'],
            EntityType.JUDICIAL_INTERPRETATION: ['JudicialInterpretation'],
            EntityType.EXAMINATION_GUIDELINE: ['ExaminationGuideline'],
            EntityType.LEGAL_ARTICLE: ['LegalArticle'],
            EntityType.REGULATION_CLAUSE: ['RegulationClause'],
            EntityType.GUIDELINE_SECTION: ['GuidelineSection'],
            EntityType.INVALIDATION_DECISION: ['InvalidationDecision', 'Case'],
            EntityType.REEXAMINATION_DECISION: ['ReexaminationDecision', 'Case'],
            EntityType.COURT_CASE: ['CourtCase', 'Case'],
            EntityType.TECHNICAL_CONCEPT: ['TechnicalConcept'],
            EntityType.PATENT_TYPE: ['PatentType'],
            EntityType.INVENTION_FIELD: ['InventionField'],
            EntityType.LEGAL_CONCEPT: ['LegalConcept'],
            EntityType.APPLICANT: ['Applicant', 'Person'],
            EntityType.PATENT_HOLDER: ['PatentHolder', 'Person'],
            EntityType.PATENT_OFFICE: ['PatentOffice', 'Organization'],
            EntityType.COURT: ['Court', 'Organization'],
            EntityType.EXAMINER: ['Examiner', 'Person'],
            EntityType.PATENT: ['Patent'],
            EntityType.PATENT_APPLICATION: ['PatentApplication'],
            EntityType.CLAIM: ['Claim'],
            EntityType.LEGAL_PROCEDURE: ['LegalProcedure'],
            EntityType.PROCEEDING_STEP: ['ProceedingStep'],
            EntityType.DEADLINE: ['Deadline'],
            EntityType.REQUIREMENT: ['Requirement']
        }

        if entity_type in type_labels:
            labels.extend(type_labels[entity_type])

        return labels

    def _format_value(self, value: Any) -> str:
        """格式化值用于Cypher查询"""
        if value is None:
            return 'null'
        elif isinstance(value, str):
            return f"'{value.replace(\"'\", \"\\'\")}'"
        elif isinstance(value, bool):
            return 'true' if value else 'false'
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, list):
            formatted_items = [self._format_value(item) for item in value]
            return f"[{', '.join(formatted_items)}]"
        elif isinstance(value, dict):
            formatted_items = [f"{k}: {self._format_value(v)}" for k, v in value.items()]
            return f"{{{', '.join(formatted_items)}}}"
        else:
            return f"'{str(value)}'"

    def import_relations(self, relations: List[KnowledgeRelation], batch_size: int = 1000) -> Dict[str, Any]:
        """批量导入关系"""
        if not self.driver:
            raise RuntimeError('未连接到Neo4j数据库')

        logger.info(f"开始导入 {len(relations)} 个关系...")

        success_count = 0
        error_count = 0

        with self.driver.session(database=self.database) as session:
            for i in range(0, len(relations), batch_size):
                batch = relations[i:i + batch_size]

                for relation in batch:
                    try:
                        self._import_single_relation(session, relation)
                        success_count += 1
                    except Exception as e:
                        error_count += 1
                        logger.error(f"导入关系失败 {relation.id}: {str(e)}")

                logger.info(f"已处理 {min(i + batch_size, len(relations))}/{len(relations)} 个关系")

        self.import_stats['imported_relations'] += success_count
        self.import_stats['errors'] += error_count

        logger.info(f"关系导入完成: 成功 {success_count}, 失败 {error_count}")

        return {
            'success_count': success_count,
            'error_count': error_count,
            'total_processed': len(relations)
        }

    def _import_single_relation(self, session: Session, relation: KnowledgeRelation):
        """导入单个关系"""
        # 构建属性字典
        properties = {
            'id': relation.id,
            'type': relation.type.value,
            'confidence': relation.confidence,
            'evidence': relation.evidence,
            'source_document': relation.source_document,
            'created_at': relation.created_at.isoformat() if relation.created_at else None
        }

        # 添加特定类型的属性
        if relation.properties:
            properties.update(relation.properties)

        # 根据关系类型确定关系名称
        relation_name = relation.type.value

        # 构建Cypher查询
        properties_str = ', '.join([f"r.{k} = {self._format_value(v)}" for k, v in properties.items()])

        cypher = f"""
        MATCH (source:Entity {{id: $source_id}})
        MATCH (target:Entity {{id: $target_id}})
        MERGE (source)-[r:{relation_name}]->(target)
        SET {properties_str}
        """

        session.run(cypher,
                    source_id=relation.source,
                    target_id=relation.target)

    def import_extraction_results(self, results: List[ExtractionResult]) -> Dict[str, Any]:
        """导入抽取结果"""
        logger.info('开始导入抽取结果...')

        # 收集所有实体和关系
        all_entities = []
        all_relations = []

        for result in results:
            all_entities.extend(result.entities)
            all_relations.extend(result.relations)

        self.import_stats['total_entities'] = len(all_entities)
        self.import_stats['total_relations'] = len(all_relations)

        # 先导入实体
        entity_result = self.import_entities(all_entities)

        # 再导入关系
        relation_result = self.import_relations(all_relations)

        self.import_stats['end_time'] = datetime.now()

        # 计算导入时间
        duration = (self.import_stats['end_time'] - self.import_stats['start_time']).total_seconds()

        return {
            'entities': entity_result,
            'relations': relation_result,
            'duration_seconds': duration,
            'total_entities': len(all_entities),
            'total_relations': len(all_relations),
            'success_rate': (entity_result['success_count'] + relation_result['success_count']) /
                          (len(all_entities) + len(all_relations)) * 100 if all_entities or all_relations else 0
        }

    def import_from_json(self, entities_file: str, relations_file: str) -> Dict[str, Any]:
        """从JSON文件导入数据"""
        logger.info(f"从JSON文件导入数据: {entities_file}, {relations_file}")

        # 加载实体数据
        with open(entities_file, 'r', encoding='utf-8') as f:
            entities_data = json.load(f)

        # 加载关系数据
        with open(relations_file, 'r', encoding='utf-8') as f:
            relations_data = json.load(f)

        # 转换为对象
        entities = []
        for entity_data in entities_data:
            entity = KnowledgeEntity(
                id=entity_data['id'],
                type=EntityType(entity_data['type']),
                name=entity_data['name'],
                description=entity_data.get('description'),
                properties=entity_data.get('properties', {}),
                source=entity_data.get('source'),
                confidence=entity_data.get('confidence', 1.0)
            )
            entities.append(entity)

        relations = []
        for relation_data in relations_data:
            relation = KnowledgeRelation(
                id=relation_data['id'],
                source=relation_data['source'],
                target=relation_data['target'],
                type=RelationType(relation_data['type']),
                properties=relation_data.get('properties', {}),
                confidence=relation_data.get('confidence', 1.0),
                evidence=relation_data.get('evidence'),
                source_document=relation_data.get('source_document')
            )
            relations.append(relation)

        # 导入数据
        entity_result = self.import_entities(entities)
        relation_result = self.import_relations(relations)

        return {
            'entities': entity_result,
            'relations': relation_result,
            'total_entities': len(entities),
            'total_relations': len(relations)
        }

    def query_entity(self, entity_id: str) -> Dict[str, Any | None]:
        """查询实体"""
        if not self.driver:
            raise RuntimeError('未连接到Neo4j数据库')

        with self.driver.session(database=self.database) as session:
            cypher = """
            MATCH (e:Entity {id: $entity_id})
            RETURN e
            """

            result = session.run(cypher, entity_id=entity_id)
            record = result.single()

            if record:
                return dict(record['e'])
            return None

    def query_relations(self, entity_id: str, direction: str = 'both', relation_type: str | None = None) -> List[Dict[str, Any]]:
        """查询实体的关系"""
        if not self.driver:
            raise RuntimeError('未连接到Neo4j数据库')

        with self.driver.session(database=self.database) as session:
            if direction == 'outgoing':
                match_pattern = 'MATCH (e:Entity {id: $entity_id})-[r]->(related:Entity)'
            elif direction == 'incoming':
                match_pattern = 'MATCH (e:Entity {id: $entity_id})<-[r]-(related:Entity)'
            else:  # both
                match_pattern = 'MATCH (e:Entity {id: $entity_id})-[r]-(related:Entity)'

            if relation_type:
                match_pattern += f" WHERE r.type = '{relation_type}'"

            cypher = f"""
            {match_pattern}
            RETURN e, r, related
            ORDER BY r.confidence DESC
            """

            results = session.run(cypher, entity_id=entity_id)

            relations = []
            for record in results:
                relations.append({
                    'source': dict(record['e']),
                    'relation': dict(record['r']),
                    'target': dict(record['related'])
                })

            return relations

    def search_entities(self, entity_type: str | None = None, name_pattern: str | None = None,
                        limit: int = 100) -> List[Dict[str, Any]]:
        """搜索实体"""
        if not self.driver:
            raise RuntimeError('未连接到Neo4j数据库')

        with self.driver.session(database=self.database) as session:
            cypher_parts = ['MATCH (e:Entity)']
            conditions = []

            if entity_type:
                conditions.append('e.type = $entity_type')

            if name_pattern:
                conditions.append('e.name CONTAINS $name_pattern')

            if conditions:
                cypher_parts.append('WHERE ' + ' AND '.join(conditions))

            cypher_parts.append('RETURN e ORDER BY e.confidence DESC LIMIT $limit')

            cypher = ' '.join(cypher_parts)

            params = {}
            if entity_type:
                params['entity_type'] = entity_type
            if name_pattern:
                params['name_pattern'] = name_pattern
            params['limit'] = limit

            results = session.run(cypher, **params)

            entities = []
            for record in results:
                entities.append(dict(record['e']))

            return entities

    def get_knowledge_graph_statistics(self) -> Dict[str, Any]:
        """获取知识图谱统计信息"""
        if not self.driver:
            raise RuntimeError('未连接到Neo4j数据库')

        with self.driver.session(database=self.database) as session:
            # 实体统计
            entity_stats_query = """
            MATCH (e:Entity)
            RETURN e.type as type, count(e) as count
            ORDER BY count DESC
            """

            entity_stats = {}
            for record in session.run(entity_stats_query):
                entity_stats[record['type']] = record['count']

            # 关系统计
            relation_stats_query = """
            MATCH ()-[r]-()
            RETURN r.type as type, count(r) as count
            ORDER BY count DESC
            """

            relation_stats = {}
            for record in session.run(relation_stats_query):
                relation_stats[record['type']] = record['count']

            # 总体统计
            total_entities = sum(entity_stats.values())
            total_relations = sum(relation_stats.values())

            return {
                'total_entities': total_entities,
                'total_relations': total_relations,
                'entity_types': entity_stats,
                'relation_types': relation_stats,
                'graph_density': total_relations / (total_entities * (total_entities - 1)) if total_entities > 1 else 0,
                'import_stats': self.import_stats
            }

    def execute_cypher_query(self, cypher: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """执行自定义Cypher查询"""
        if not self.driver:
            raise RuntimeError('未连接到Neo4j数据库')

        with self.driver.session(database=self.database) as session:
            results = session.run(cypher, params or {})

            return [dict(record) for record in results]

    def find_path_between_entities(self, source_id: str, target_id: str, max_depth: int = 5) -> List[Dict[str, Any]]:
        """查找实体间路径"""
        if not self.driver:
            raise RuntimeError('未连接到Neo4j数据库')

        with self.driver.session(database=self.database) as session:
            cypher = f"""
            MATCH path = shortestPath((source:Entity {{id: $source_id}})-[*1..{max_depth}]-(target:Entity {{id: $target_id}}))
            RETURN path, length(path) as path_length
            ORDER BY path_length
            LIMIT 10
            """

            results = session.run(cypher, source_id=source_id, target_id=target_id)

            paths = []
            for record in results:
                path = record['path']
                path_info = {
                    'length': record['path_length'],
                    'nodes': [dict(node) for node in path.nodes],
                    'relationships': [dict(rel) for rel in path.relationships]
                }
                paths.append(path_info)

            return paths

    def get_entities_by_type(self, entity_type: EntityType, limit: int = 1000) -> List[Dict[str, Any]]:
        """根据类型获取实体"""
        if not self.driver:
            raise RuntimeError('未连接到Neo4j数据库')

        with self.driver.session(database=self.database) as session:
            cypher = f"""
            MATCH (e:Entity {{type: $entity_type}})
            RETURN e
            ORDER BY e.confidence DESC
            LIMIT $limit
            """

            results = session.run(cypher, entity_type=entity_type.value, limit=limit)

            return [dict(record['e']) for record in results]

    def clear_database(self):
        """清空数据库"""
        if not self.driver:
            raise RuntimeError('未连接到Neo4j数据库')

        logger.warning('正在清空数据库...')

        with self.driver.session(database=self.database) as session:
            # 删除所有关系
            session.run('MATCH ()-[r]-() DELETE r')

            # 删除所有节点
            session.run('MATCH (n) DELETE n')

            logger.info('数据库已清空')

# ============================================================================
# 工具函数和使用示例
# ============================================================================

def setup_neo4j_environment():
    """设置Neo4j环境"""
    logger.info('请确保已安装并启动Neo4j数据库:')
    logger.info('1. 下载并安装Neo4j Desktop或Neo4j Server')
    logger.info('2. 启动Neo4j服务')
    logger.info('3. 创建数据库用户名和密码')
    logger.info('4. 确保可以连接到 bolt://localhost:7687')

def sample_usage():
    """使用示例"""
    # 创建Neo4j管理器
    neo4j_manager = Neo4jManager(
        uri='bolt://localhost:7687',
        username='neo4j',
        password='your_password',
        database='patent_kg'
    )

    # 连接并创建模式
    if neo4j_manager.connect():
        neo4j_manager.create_schema()

        # 导入数据示例
        # results = extractor.process_directory("/path/to/documents", max_files=10)
        # import_result = neo4j_manager.import_extraction_results(results)

        # 查询示例
        entities = neo4j_manager.search_entities(entity_type='law', limit=10)
        logger.info(f"找到 {len(entities)} 个法律实体")

        # 获取统计信息
        stats = neo4j_manager.get_knowledge_graph_statistics()
        logger.info(f"知识图谱统计: {stats}")

        # 关闭连接
        neo4j_manager.close()

if __name__ == '__main__':
    logger.info('Neo4j专利知识图谱管理器')
    logger.info(str('=' * 50))

    setup_neo4j_environment()

    if NEO4J_AVAILABLE:
        logger.info("\n主要功能:")
        logger.info('1. 连接Neo4j数据库')
        logger.info('2. 创建知识图谱模式（约束、索引）')
        logger.info('3. 批量导入实体和关系')
        logger.info('4. 查询实体和关系')
        logger.info('5. 搜索和统计功能')
        logger.info('6. 路径查找功能')

        logger.info("\n使用示例:")
        logger.info('neo4j_manager = Neo4jManager()')
        logger.info('neo4j_manager.connect()')
        logger.info('neo4j_manager.create_schema()')
        logger.info('neo4j_manager.import_extraction_results(results)')

    else:
        logger.info('Neo4j功能不可用，请安装neo4j库:')
        logger.info('pip install neo4j')