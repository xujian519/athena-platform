#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据迁移管理器
将SQLite数据迁移到Qdrant和Neo4j
"""

import asyncio
import json
import logging
import os
import sqlite3
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from tqdm import tqdm

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# 尝试导入必要的库
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, Filter, PointStruct, VectorParams
    QDRANT_AVAILABLE = True
except ImportError:
    logger.info('❌ 请安装qdrant-client: pip install qdrant-client')
    QDRANT_AVAILABLE = False

try:
    from neo4j import GraphDatabase

# 导入标准化数据库工具
from shared.database.db_utils import DatabaseManager, build_safe_query
    NEO4J_AVAILABLE = True
except ImportError:
    logger.info('❌ 请安装neo4j: pip install neo4j')
    NEO4J_AVAILABLE = False

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VectorDataMigrator:
    """向量数据迁移器 - SQLite到Qdrant"""

    def __init__(self):
        self.project_root = Path(project_root)
        self.qdrant_client = QdrantClient('http://localhost:6333') if QDRANT_AVAILABLE else None

        # SQLite数据库路径
        self.source_databases = {
            'athena_memory': self.project_root / 'data/support_data/databases/databases/memory_system/athena_memory.db',
            'patent_index': self.project_root / 'data/patents/processed/indexed_patents.db',
            'vector_metadata': self.project_root / 'patent-platform/workspace/data/vector_metadata.db'
        }

        # 迁移配置
        self.batch_size = 1000
        self.migration_stats = {}

    def prepare_qdrant_collection(self, collection_name: str, vector_size: int) -> bool:
        """准备Qdrant集合"""
        if not self.qdrant_client:
            logger.error('❌ Qdrant客户端未初始化')
            return False

        try:
            # 检查集合是否存在
            collections = self.qdrant_client.get_collections().collections
            exists = any(c.name == collection_name for c in collections)

            if not exists:
                # 创建新集合
                self.qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"✅ 创建新集合: {collection_name}")
            else:
                logger.info(f"✅ 集合已存在: {collection_name}")

            return True

        except Exception as e:
            logger.error(f"❌ 准备Qdrant集合失败 {collection_name}: {e}")
            return False

    def extract_vectors_from_sqlite(self, db_path: Path) -> List[Tuple[str, List[float], Dict[str, Any]]]:
        """从SQLite提取向量数据"""
        vectors = []

        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # 检查是否有athena_memories表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='athena_memories'")
            has_memories = cursor.fetchone() is not None

            if has_memories:
                # 从athena_memories表提取
                cursor.execute("""
                    SELECT id, content, embedding_data, embedding_dim, category,
                           importance_score, tags, created_at
                    FROM athena_memories
                    WHERE embedding_data IS NOT NULL
                """)

                for row in cursor.fetchall():
                    memory_id, content, embedding_blob, dim, category, score, tags, created_at = row

                    if embedding_blob and dim > 0:
                        vector = np.frombuffer(embedding_blob, dtype=np.float32).tolist()

                        payload = {
                            'content': content,
                            'category': category,
                            'importance_score': score,
                            'tags': tags,
                            'created_at': created_at,
                            'source_table': 'athena_memories'
                        }

                        vectors.append((str(memory_id), vector, payload))

            # 检查是否有其他表
            tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()

            for table_name, in tables:
                if 'embedding' in table_name.lower() or 'vector' in table_name.lower():
                    try:
        # TODO: 检查SQL注入风险 - cursor.execute(f"SELECT * FROM {table_name} LIMIT 10")
                                cursor.execute(f"SELECT * FROM {table_name} LIMIT 10")
                        columns = [desc[0] for desc in cursor.description]

                        # 查找向量列
                        vector_columns = [col for col in columns if 'embedding' in col.lower() or 'vector' in col.lower()]

                        if vector_columns and table_name != 'athena_memories':
        # TODO: 检查SQL注入风险 - cursor.execute(f"SELECT * FROM {table_name} WHERE {vector_columns[0]} IS NOT NULL")
                                    cursor.execute(f"SELECT * FROM {table_name} WHERE {vector_columns[0]} IS NOT NULL")
                            rows = cursor.fetchall()

                            for row in rows:
                                # 构造payload
                                payload = dict(zip(columns, row))

                                # 获取向量
                                if isinstance(row[0], bytes):
                                    vector = np.frombuffer(row[0], dtype=np.float32).tolist()
                                    vectors.append((str(row[1]) if len(row) > 1 else f"{table_name}_{len(vectors)}",
                                                 vector, payload))

                    except Exception as e:
                        logger.warning(f"⚠️ 处理表 {table_name} 失败: {e}")

            conn.close()
            logger.info(f"📊 从 {db_path.name} 提取了 {len(vectors)} 个向量")

        except Exception as e:
            logger.error(f"❌ 提取向量数据失败 {db_path}: {e}")

        return vectors

    def migrate_vectors_to_qdrant(self, source_db: str, target_collection: str) -> Dict[str, Any]:
        """迁移向量数据到Qdrant"""
        logger.info(f"🚀 开始迁移 {source_db} 到 {target_collection}")

        db_path = self.source_databases.get(source_db)
        if not db_path or not db_path.exists():
            logger.error(f"❌ 源数据库不存在: {db_path}")
            return {'status': 'error', 'message': f"数据库不存在: {db_path}"}

        # 提取向量数据
        vectors = self.extract_vectors_from_sqlite(db_path)
        if not vectors:
            logger.warning(f"⚠️ 没有找到向量数据")
            return {'status': 'warning', 'message': '没有找到向量数据'}

        # 确定向量维度
        vector_size = len(vectors[0][1]) if vectors else 1024

        # 准备Qdrant集合
        if not self.prepare_qdrant_collection(target_collection, vector_size):
            return {'status': 'error', 'message': '准备Qdrant集合失败'}

        # 批量迁移
        migration_stats = {
            'total': len(vectors),
            'migrated': 0,
            'failed': 0,
            'start_time': datetime.now().isoformat()
        }

        logger.info(f"📦 开始批量迁移，批次大小: {self.batch_size}")

        for i in tqdm(range(0, len(vectors), self.batch_size), desc='迁移进度'):
            batch = vectors[i:i + self.batch_size]

            points = []
            for vector_id, vector, payload in batch:
                points.append(PointStruct(
                    id=vector_id,
                    vector=vector,
                    payload=payload
                ))

            try:
                # 上传到Qdrant
                self.qdrant_client.upsert(
                    collection_name=target_collection,
                    points=points
                )
                migration_stats['migrated'] += len(batch)

            except Exception as e:
                logger.error(f"❌ 批次上传失败: {e}")
                migration_stats['failed'] += len(batch)

            # 短暂延迟避免过载
            time.sleep(0.1)

        migration_stats['end_time'] = datetime.now().isoformat()
        migration_stats['status'] = 'completed'

        logger.info(f"✅ 迁移完成: {migration_stats['migrated']}/{migration_stats['total']}")

        return migration_stats

class GraphDataMigrator:
    """知识图谱数据迁移器 - SQLite到Neo4j"""

    def __init__(self):
        self.project_root = Path(project_root)
        self.neo4j_driver = None

        if NEO4J_AVAILABLE:
            try:
                self.neo4j_driver = GraphDatabase.driver(
                    'bolt://localhost:7687',
                    auth=('neo4j', 'password')
                )
                # 测试连接
                with self.neo4j_driver.session() as session:
                    session.run('RETURN 1')
                logger.info('✅ Neo4j连接成功')
            except Exception as e:
                logger.warning(f"⚠️ Neo4j连接失败: {e}")

        # 源数据库路径
        self.knowledge_graph_db = self.project_root / 'data/knowledge_graph_sqlite/databases/patent_knowledge_graph.db'

    def create_indexes(self) -> bool:
        """创建Neo4j索引"""
        if not self.neo4j_driver:
            return False

        try:
            with self.neo4j_driver.session() as session:
                # 创建节点索引
                indexes = [
                    'CREATE INDEX entity_id_index IF NOT EXISTS FOR (e:Entity) ON (e.id)',
                    'CREATE INDEX entity_name_index IF NOT EXISTS FOR (e:Entity) ON (e.name)',
                    'CREATE INDEX entity_type_index IF NOT EXISTS FOR (e:Entity) ON (e.type)',
                    'CREATE INDEX patent_id_index IF NOT EXISTS FOR (p:Patent) ON (p.patent_id)',
                    'CREATE INDEX relation_id_index IF NOT EXISTS FOR ()-[r:RELATES_TO]-() ON (r.id)'
                ]

                for index_query in indexes:
                    session.run(index_query)

            logger.info('✅ Neo4j索引创建完成')
            return True

        except Exception as e:
            logger.error(f"❌ 创建索引失败: {e}")
            return False

    def extract_entities_from_sqlite(self) -> List[Dict[str, Any]]:
        """从SQLite提取实体"""
        entities = []

        if not self.knowledge_graph_db.exists():
            logger.error(f"❌ 知识图谱数据库不存在: {self.knowledge_graph_db}")
            return entities

        try:
            conn = sqlite3.connect(str(self.knowledge_graph_db))
            cursor = conn.cursor()

            # 获取所有表
            tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()

            for table_name, in tables:
                if 'entity' in table_name.lower():
        # TODO: 检查SQL注入风险 - cursor.execute(f"PRAGMA table_info({table_name})")
                            cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = [col[1] for col in cursor.fetchall()]

        # TODO: 检查SQL注入风险 - cursor.execute(f"SELECT * FROM {table_name} LIMIT 100")
                            cursor.execute(f"SELECT * FROM {table_name} LIMIT 100")
                    rows = cursor.fetchall()

                    for row in rows:
                        entity = dict(zip(columns, row))
                        entity['_source_table'] = table_name
                        entities.append(entity)

            conn.close()
            logger.info(f"📊 提取了 {len(entities)} 个实体")

        except Exception as e:
            logger.error(f"❌ 提取实体失败: {e}")

        return entities

    def extract_relationships_from_sqlite(self) -> List[Dict[str, Any]]:
        """从SQLite提取关系"""
        relationships = []

        if not self.knowledge_graph_db.exists():
            return relationships

        try:
            conn = sqlite3.connect(str(self.knowledge_graph_db))
            cursor = conn.cursor()

            # 获取所有表
            tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()

            for table_name, in tables:
                if 'relation' in table_name.lower() or 'edge' in table_name.lower():
        # TODO: 检查SQL注入风险 - cursor.execute(f"PRAGMA table_info({table_name})")
                            cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = [col[1] for col in cursor.fetchall()]

        # TODO: 检查SQL注入风险 - cursor.execute(f"SELECT * FROM {table_name} LIMIT 100")
                            cursor.execute(f"SELECT * FROM {table_name} LIMIT 100")
                    rows = cursor.fetchall()

                    for row in rows:
                        relation = dict(zip(columns, row))
                        relation['_source_table'] = table_name
                        relationships.append(relation)

            conn.close()
            logger.info(f"📊 提取了 {len(relationships)} 个关系")

        except Exception as e:
            logger.error(f"❌ 提取关系失败: {e}")

        return relationships

    def migrate_entities_to_neo4j(self, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """迁移实体到Neo4j"""
        if not self.neo4j_driver:
            return {'status': 'error', 'message': 'Neo4j未连接'}

        stats = {
            'total': len(entities),
            'created': 0,
            'failed': 0
        }

        logger.info(f"🚀 开始迁移 {len(entities)} 个实体")

        with self.neo4j_driver.session() as session:
            for entity in tqdm(entities, desc='迁移实体'):
                try:
                    # 确定实体标签
                    entity_type = entity.get('type', 'Entity')
                    if isinstance(entity_type, str):
                        labels = entity_type.split(',')
                    else:
                        labels = ['Entity']

                    # 构建Cypher查询
                    properties = {k: v for k, v in entity.items()
                                if not k.startswith('_') and v is not None}

                    # 合并实体
                    query = f"""
                    MERGE (e:{':'.join(labels)} {{id: $id}})
                    SET e += $properties
                    """

                    session.run(query, id=entity.get('id'), properties=properties)
                    stats['created'] += 1

                except Exception as e:
                    logger.warning(f"⚠️ 迁移实体失败 {entity.get('id')}: {e}")
                    stats['failed'] += 1

        logger.info(f"✅ 实体迁移完成: {stats['created']}/{stats['total']}")
        return stats

    def migrate_relationships_to_neo4j(self, relationships: List[Dict[str, Any]]) -> Dict[str, Any]:
        """迁移关系到Neo4j"""
        if not self.neo4j_driver:
            return {'status': 'error', 'message': 'Neo4j未连接'}

        stats = {
            'total': len(relationships),
            'created': 0,
            'failed': 0
        }

        logger.info(f"🚀 开始迁移 {len(relationships)} 个关系")

        with self.neo4j_driver.session() as session:
            for relation in tqdm(relationships, desc='迁移关系'):
                try:
                    # 获取关系信息
                    source_id = relation.get('source_id') or relation.get('from_id') or relation.get('entity1_id')
                    target_id = relation.get('target_id') or relation.get('to_id') or relation.get('entity2_id')
                    relation_type = relation.get('type', 'RELATES_TO')

                    if not source_id or not target_id:
                        logger.warning(f"⚠️ 跳过无效关系: {relation}")
                        stats['failed'] += 1
                        continue

                    # 创建关系
                    properties = {k: v for k, v in relation.items()
                                if k not in ['source_id', 'target_id', 'from_id', 'to_id', 'entity1_id', 'entity2_id', '_source_table']
                                and v is not None}

                    query = f"""
                    MATCH (source {{id: $source_id}})
                    MATCH (target {{id: $target_id}})
                    MERGE (source)-[r:{relation_type}]->(target)
                    SET r += $properties
                    """

                    session.run(query, source_id=source_id, target_id=target_id, properties=properties)
                    stats['created'] += 1

                except Exception as e:
                    logger.warning(f"⚠️ 迁移关系失败: {e}")
                    stats['failed'] += 1

        logger.info(f"✅ 关系迁移完成: {stats['created']}/{stats['total']}")
        return stats

class DataMigrationManager:
    """数据迁移管理器"""

    def __init__(self):
        self.vector_migrator = VectorDataMigrator()
        self.graph_migrator = GraphDataMigrator()

        # 迁移配置
        self.migration_plan = {
            'vector_migrations': [
                {
                    'source': 'athena_memory',
                    'target': 'athena_memory_migrated',
                    'priority': 1
                },
                {
                    'source': 'patent_index',
                    'target': 'patent_index_migrated',
                    'priority': 2
                }
            ],
            'graph_migration': {
                'enabled': True,
                'priority': 1
            }
        }

    def run_vector_migration(self) -> Dict[str, Any]:
        """执行向量数据迁移"""
        logger.info('🚀 开始向量数据迁移...')

        results = {}

        for migration in sorted(self.migration_plan['vector_migrations'], key=lambda x: x['priority']):
            source = migration['source']
            target = migration['target']

            logger.info(f"📦 迁移: {source} -> {target}")
            result = self.vector_migrator.migrate_vectors_to_qdrant(source, target)
            results[f"{source}_to_{target}"] = result

        return results

    def run_graph_migration(self) -> Dict[str, Any]:
        """执行知识图谱迁移"""
        if not NEO4J_AVAILABLE:
            logger.warning('⚠️ Neo4j未安装，跳过图数据迁移')
            return {'status': 'skipped', 'reason': 'Neo4j not available'}

        if not self.graph_migrator.neo4j_driver:
            logger.warning('⚠️ Neo4j未连接，跳过图数据迁移')
            return {'status': 'skipped', 'reason': 'Neo4j not connected'}

        logger.info('🚀 开始知识图谱迁移...')

        results = {}

        # 1. 创建索引
        if self.graph_migrator.create_indexes():
            results['indexes'] = {'status': 'success'}
        else:
            results['indexes'] = {'status': 'failed'}

        # 2. 提取数据
        entities = self.graph_migrator.extract_entities_from_sqlite()
        relationships = self.graph_migrator.extract_relationships_from_sqlite()

        # 3. 迁移实体
        if entities:
            results['entities'] = self.graph_migrator.migrate_entities_to_neo4j(entities)

        # 4. 迁移关系
        if relationships:
            results['relationships'] = self.graph_migrator.migrate_relationships_to_neo4j(relationships)

        return results

    def run_full_migration(self) -> Dict[str, Any]:
        """执行完整迁移"""
        logger.info('🎯 开始完整数据迁移...')

        migration_start = datetime.now()

        results = {
            'migration_id': f"full_migration_{migration_start.strftime('%Y%m%d_%H%M%S')}",
            'start_time': migration_start.isoformat(),
            'environment': {
                'qdrant_available': QDRANT_AVAILABLE,
                'neo4j_available': NEO4J_AVAILABLE,
                'qdrant_connected': self.vector_migrator.qdrant_client is not None,
                'neo4j_connected': self.graph_migrator.neo4j_driver is not None
            }
        }

        # 1. 向量数据迁移
        logger.info('🔄 阶段1: 向量数据迁移')
        results['vector_migration'] = self.run_vector_migration()

        # 2. 知识图谱迁移
        logger.info('🔄 阶段2: 知识图谱迁移')
        results['graph_migration'] = self.run_graph_migration()

        # 3. 完成信息
        migration_end = datetime.now()
        results['end_time'] = migration_end.isoformat()
        results['duration_seconds'] = (migration_end - migration_start).total_seconds()

        # 保存迁移报告
        report_path = self.vector_migrator.project_root / 'migration_report.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"📋 迁移报告已保存: {report_path}")

        return results

def main():
    """主函数"""
    logger.info('🔄 Athena工作平台 - 数据迁移工具')
    logger.info(str('='*60))

    # 检查依赖
    if not QDRANT_AVAILABLE and not NEO4J_AVAILABLE:
        logger.info('❌ 请安装必要的依赖:')
        logger.info('  pip install qdrant-client neo4j tqdm')
        return

    # 创建迁移管理器
    migrator = DataMigrationManager()

    # 执行迁移
    try:
        results = migrator.run_full_migration()

        # 打印摘要
        logger.info(str("\n" + '='*60))
        logger.info('📊 迁移摘要')
        logger.info(str('='*60))
        logger.info(f"迁移ID: {results['migration_id']}")
        logger.info(f"开始时间: {results['start_time']}")
        logger.info(f"结束时间: {results['end_time']}")
        logger.info(f"耗时: {results['duration_seconds']:.2f} 秒")

        logger.info("\n环境状态:")
        env = results['environment']
        logger.info(f"  Qdrant可用: {'✅' if env['qdrant_available'] else '❌'}")
        logger.info(f"  Neo4j可用: {'✅' if env['neo4j_available'] else '❌'}")
        logger.info(f"  Qdrant已连接: {'✅' if env['qdrant_connected'] else '❌'}")
        logger.info(f"  Neo4j已连接: {'✅' if env['neo4j_connected'] else '❌'}")

        if 'vector_migration' in results:
            logger.info("\n向量迁移结果:")
            for migration, result in results['vector_migration'].items():
                status = result.get('status', 'unknown')
                if status == 'completed':
                    logger.info(f"  ✅ {migration}: {result.get('migrated', 0)}个向量迁移成功")
                elif status == 'error':
                    logger.info(f"  ❌ {migration}: {result.get('message', '失败')}")

        if 'graph_migration' in results:
            logger.info("\n图迁移结果:")
            graph = results['graph_migration']
            if graph.get('status') == 'skipped':
                logger.info(f"  ⚠️ 跳过: {graph.get('reason', '未知原因')}")
            else:
                if 'entities' in graph:
                    e = graph['entities']
                    logger.info(f"  ✅ 实体: {e.get('created', 0)}/{e.get('total', 0)} 迁移成功")
                if 'relationships' in graph:
                    r = graph['relationships']
                    logger.info(f"  ✅ 关系: {r.get('created', 0)}/{r.get('total', 0)} 迁移成功")

        logger.info("\n✅ 迁移完成！")
        logger.info('请查看 migration_report.json 获取详细信息。')

    except Exception as e:
        logger.error(f"❌ 迁移失败: {e}")
        logger.info(f"\n❌ 迁移过程中出现错误: {e}")
        logger.info('请检查日志并重试。')

if __name__ == '__main__':
    main()