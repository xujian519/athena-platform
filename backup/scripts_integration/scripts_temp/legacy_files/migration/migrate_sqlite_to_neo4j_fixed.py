#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将SQLite知识图谱迁移到Neo4j（修复版）
Migrate SQLite Knowledge Graph to Neo4j (Fixed Version)

处理复杂的属性结构，只保留基本属性
"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path

from neo4j import GraphDatabase

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SQLiteToNeo4jMigratorFixed:
    """SQLite到Neo4j的迁移器（修复版）"""

    def __init__(self):
        # SQLite数据库路径
        self.sqlite_path = Path('/Users/xujian/Athena工作平台/data/knowledge/kg_main.db')

        # Neo4j连接配置
        self.neo4j_uri = 'bolt://localhost:7687'
        self.neo4j_user = 'neo4j'
        self.neo4j_password = 'password'
        self.driver = None

        # 统计信息
        self.stats = {
            'entities_migrated': 0,
            'relations_migrated': 0,
            'errors': 0,
            'entities_skipped': 0,
            'relations_skipped': 0
        }

    def connect_neo4j(self):
        """连接Neo4j"""
        try:
            self.driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )
            # 测试连接
            with self.driver.session() as session:
                session.run('RETURN 1')
            logger.info('✅ Neo4j连接成功')
            return True
        except Exception as e:
            logger.error(f"❌ Neo4j连接失败: {e}")
            return False

    def create_constraints_and_indexes(self):
        """创建Neo4j约束和索引"""
        constraints = [
            # 实体约束
            'CREATE CONSTRAINT entity_id_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.entity_id IS UNIQUE',

            # 索引
            'CREATE INDEX entity_type_idx IF NOT EXISTS FOR (e:Entity) ON (e.entity_type)',
            'CREATE INDEX entity_name_idx IF NOT EXISTS FOR (e:Entity) ON (e.name)',
            'CREATE INDEX relation_type_idx IF NOT EXISTS FOR ()-[r:RELATES_TO]-() ON (r.relation_type)'
        ]

        with self.driver.session() as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                    logger.info(f"✅ 创建约束/索引: {constraint[:50]}...")
                except Exception as e:
                    logger.warning(f"⚠️ 约束/索引可能已存在: {e}")

    def flatten_properties(self, props_dict):
        """展平属性字典，只保留基本类型"""
        if not props_dict:
            return {}

        flat_props = {}
        for key, value in props_dict.items():
            # 只保留基本类型和字符串
            if value is None:
                flat_props[key] = None
            elif isinstance(value, (str, int, float, bool)):
                flat_props[key] = value
            elif isinstance(value, list):
                # 展开列表，过滤非基本类型
                flat_list = []
                for item in value:
                    if isinstance(item, (str, int, float, bool)):
                        flat_list.append(item)
                flat_props[key] = flat_list
            elif isinstance(value, dict):
                # 如果是字典，尝试展平到顶级
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, (str, int, float, bool)):
                        flat_props[f"{key}_{sub_key}"] = sub_value
                    elif isinstance(sub_value, list):
                        flat_list = []
                        for item in sub_value:
                            if isinstance(item, (str, int, float, bool)):
                                flat_list.append(item)
                        if flat_list:
                            flat_props[f"{key}_{sub_key}"] = flat_list
            # 忽略其他复杂的嵌套对象

        return flat_props

    def migrate_entities(self, batch_size=100):
        """迁移实体数据"""
        logger.info("\n🔄 开始迁移实体数据（修复版）...")

        # 连接SQLite
        conn = sqlite3.connect(str(self.sqlite_path))
        cursor = conn.cursor()

        # 获取实体总数
        cursor.execute('SELECT COUNT(*) FROM entities')
        total_entities = cursor.fetchone()[0]
        logger.info(f"📊 待迁移实体数: {total_entities:,}")

        # 分批迁移
        offset = 0
        while True:
            cursor.execute("""
                SELECT entity_id, entity_type, name, properties, aliases
                FROM entities
                ORDER BY entity_id
                LIMIT ? OFFSET ?
            """, (batch_size, offset))

            batch = cursor.fetchall()
            if not batch:
                break

            # 准备Neo4j会话
            with self.driver.session() as session:
                for entity_id, entity_type, name, properties, aliases in batch:
                    try:
                        # 解析并展平属性
                        flat_props = self.flatten_properties(json.loads(properties) if properties else {})

                        # 处理别名
                        if aliases:
                            alias_list = json.loads(aliases) if isinstance(aliases, str) else aliases
                            if isinstance(alias_list, list):
                                flat_props['aliases'] = alias_list

                        # 创建节点标签（基于实体类型）
                        labels = ['Entity']
                        if entity_type:
                            # 将实体类型转换为更友好的标签
                            label_map = {
                                'legal_concept': 'LegalConcept',
                                'patent': 'Patent',
                                'technical_term': 'TechnicalTerm',
                                '当事人': 'Party',
                                '判决': 'Judgment',
                                'organization': 'Organization',
                                'person': 'Person',
                                'concept': 'Concept'
                            }
                            main_label = label_map.get(entity_type.lower(), entity_type.title())
                            labels.append(main_label)

                        # 创建Cypher查询
                        label_str = ':'.join(labels)
                        cypher = f"""
                            MERGE (e:{label_str} {{entity_id: $entity_id}})
                            SET e.name = $name,
                                e.entity_type = $entity_type,
                                e.properties = $props,
                                e.created_at = timestamp()
                        """

                        session.run(cypher, {
                            'entity_id': entity_id,
                            'name': name,
                            'entity_type': entity_type,
                            'props': flat_props
                        })

                        self.stats['entities_migrated'] += 1

                    except Exception as e:
                        logger.error(f"❌ 迁移实体失败 {entity_id}: {e}")
                        self.stats['errors'] += 1
                        self.stats['entities_skipped'] += 1

            logger.info(f"✅ 已迁移 {min(offset + batch_size, total_entities):,}/{total_entities:,} 个实体")
            offset += batch_size

        conn.close()
        logger.info(f"✅ 实体迁移完成，成功: {self.stats['entities_migrated']:,}, 跳过: {self.stats['entities_skipped']:,}, 错误: {self.stats['errors']}")

    def migrate_relations(self, batch_size=100):
        """迁移关系数据"""
        logger.info("\n🔄 开始迁移关系数据（修复版）...")

        # 连接SQLite
        conn = sqlite3.connect(str(self.sqlite_path))
        cursor = conn.cursor()

        # 获取关系总数
        cursor.execute('SELECT COUNT(*) FROM relations')
        total_relations = cursor.fetchone()[0]
        logger.info(f"📊 待迁移关系数: {total_relations:,}")

        # 分批迁移
        offset = 0
        while True:
            cursor.execute("""
                SELECT from_entity, to_entity, relation_type, properties
                FROM relations
                ORDER BY from_entity, to_entity
                LIMIT ? OFFSET ?
            """, (batch_size, offset))

            batch = cursor.fetchall()
            if not batch:
                break

            # 准备Neo4j会话
            with self.driver.session() as session:
                for from_entity, to_entity, relation_type, properties in batch:
                    try:
                        # 解析并展平属性
                        flat_props = self.flatten_properties(json.loads(properties) if properties else {})

                        # 创建关系
                        cypher = """
                            MATCH (from_entity:Entity {entity_id: $from_id})
                            MATCH (to_entity:Entity {entity_id: $to_id})
                            MERGE (from_entity)-[r:RELATES_TO]->(to_entity)
                            SET r.relation_type = $relation_type,
                                r.properties = $props,
                                r.created_at = timestamp()
                        """

                        session.run(cypher, {
                            'from_id': from_entity,
                            'to_id': to_entity,
                            'relation_type': relation_type,
                            'props': flat_props
                        })

                        self.stats['relations_migrated'] += 1

                    except Exception as e:
                        logger.error(f"❌ 迁移关系失败 {from_entity}->{to_entity}: {e}")
                        self.stats['errors'] += 1
                        self.stats['relations_skipped'] += 1

            logger.info(f"✅ 已迁移 {min(offset + batch_size, total_relations):,}/{total_relations:,} 个关系")
            offset += batch_size

        conn.close()
        logger.info(f"✅ 关系迁移完成，成功: {self.stats['relations_migrated']:,}, 跳过: {self.stats['relations_skipped']:,}, 错误: {self.stats['errors']}")

    def create_sample_knowledge_graph(self):
        """创建示例知识图谱数据"""
        logger.info("\n📝 创建示例知识图谱...")

        with self.driver.session() as session:
            # 创建一些示例节点
            nodes = [
                ('LG_001', 'LegalConcept', '专利无效性', {'category': '法律概念', 'description': '专利无效性是指在特定条件下，专利权被宣告自始无效的法律状态'}),
                ('LG_002', 'LegalConcept', '新颖性', {'category': '法律概念', 'description': '新颖性是指申请专利的发明不属于现有技术'}),
                ('PAT_001', 'Patent', '发明专利', {'patent_number': 'CN202310000001', 'title': '一种新型设备', 'type': '发明'}),
                ('PARTY_001', 'Party', '原告', {'party_type': '原告', 'party_name': '某某公司'}),
                ('PARTY_002', 'Party', '被告', {'party_type': '被告', 'party_name': '某某公司'})
            ]

            for entity_id, entity_type, name, props in nodes:
                labels = ['Entity', entity_type]
                label_str = ':'.join(labels)
                cypher = f"""
                    CREATE (e:{label_str} {{entity_id: $entity_id, name: $name, entity_type: $entity_type, properties: $props}})
                """
                session.run(cypher, {
                    'entity_id': entity_id,
                    'name': name,
                    'entity_type': entity_type,
                    'props': props
                })

            # 创建一些示例关系
            relations = [
                ('PAT_001', 'PARTY_001', '申请人'),
                ('PAT_001', 'PARTY_002', '被诉侵权'),
                ('LG_001', 'PAT_001', '涉及'),
                ('LG_002', 'PAT_001', '评估')
            ]

            for from_id, to_id, rel_type in relations:
                cypher = """
                    MATCH (from:Entity {entity_id: $from_id})
                    MATCH (to:Entity {entity_id: $to_id})
                    MERGE (from)-[r:RELATES_TO {relation_type: $rel_type}]->(to)
                """
                session.run(cypher, {
                    'from': from_id,
                    'to': to_id,
                    'rel_type': rel_type
                })

        logger.info('✅ 示例知识图谱创建完成')

    def verify_migration(self):
        """验证迁移结果"""
        logger.info("\n✅ 验证迁移结果...")

        with self.driver.session() as session:
            # 节点统计
            node_result = session.run('MATCH (n) RETURN count(n) as count')
            node_count = node_result.single()['count']

            # 关系统计
            rel_result = session.run('MATCH ()-[r]->() RETURN count(r) as count')
            rel_count = rel_result.single()['count']

            # 按类型统计
            label_result = session.run("""
                MATCH (n)
                RETURN labels(n) as labels, count(n) as count
                ORDER BY count DESC
                LIMIT 10
            """)
            labels = list(label_result)

            rel_type_result = session.run("""
                MATCH ()-[r]->()
                RETURN r.relation_type as type, count(r) as count
                ORDER BY count DESC
                LIMIT 10
            """)
            rel_types = list(rel_type_result)

            logger.info(f"\n📊 Neo4j迁移后统计:")
            logger.info(f"  - 节点总数: {node_count:,}")
            logger.info(f"  - 关系总数: {rel_count:,}")

            if labels:
                logger.info(f"\n🏷️ 主要节点类型:")
                for label in labels:
                    logger.info(f"    • {label['labels']}: {label['count']:,}")

            if rel_types:
                logger.info(f"\n🔗 主要关系类型:")
                for rel in rel_types:
                    logger.info(f"    • {rel['type']}: {rel['count']:,}")

    async def run_migration(self):
        """执行完整迁移"""
        logger.info('🚀 开始SQLite到Neo4j知识图谱迁移（修复版）')
        logger.info(str('='*80))

        # 1. 连接Neo4j
        if not self.connect_neo4j():
            logger.error('❌ 无法连接到Neo4j，迁移终止')
            return

        # 2. 创建约束和索引
        logger.info("\n📝 创建Neo4j约束和索引...")
        self.create_constraints_and_indexes()

        # 3. 清空现有数据（如果有）
        logger.info("\n🗑️ 清空现有数据...")
        with self.driver.session() as session:
            session.run('MATCH (n) DETACH DELETE n')
            session.run('MATCH ()-[r]-() DETACH DELETE r')

        # 4. 迁移实体
        self.migrate_entities(batch_size=100)

        # 5. 迁移关系
        self.migrate_relations(batch_size=100)

        # 6. 如果没有数据，创建示例
        with self.driver.session() as session:
            node_count = session.run('MATCH (n) RETURN count(n) as count').single()['count']
            if node_count == 0:
                self.create_sample_knowledge_graph()

        # 7. 验证结果
        self.verify_migration()

        # 8. 关闭连接
        if self.driver:
            self.driver.close()

        logger.info("\n✅ 迁移完成！")
        logger.info(f"📊 迁移统计:")
        logger.info(f"  - 迁移实体数: {self.stats['entities_migrated']:,}")
        logger.info(f"  - 跳过实体数: {self.stats['entities_skipped']:,}")
        logger.info(f"  - 迁移关系数: {self.stats['relations_migrated']:,}")
        logger.info(f"  - 跳过关系数: {self.stats['relations_skipped']:,}")
        logger.info(f"  - 错误数: {self.stats['errors']}")

async def main():
    """主函数"""
    migrator = SQLiteToNeo4jMigratorFixed()
    await migrator.run_migration()

if __name__ == '__main__':
    asyncio.run(main())