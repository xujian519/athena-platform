#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Neo4j 知识图谱导入工具
Neo4j Knowledge Graph Import Tool

将分层质量处理的专利知识图谱数据导入Neo4j数据库
支持批量导入和关系网络构建

作者: Athena AI系统
创建时间: 2025年12月6日
版本: 1.0.0
"""

import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from neo4j import Driver, GraphDatabase, Session

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Neo4jKnowledgeGraphImporter:
    """Neo4j 知识图谱导入器"""

    def __init__(self, uri: str = 'bolt://localhost:7687',
                 user: str = 'neo4j', password: str = 'password'):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver: Driver | None = None

    def connect(self) -> bool:
        """连接到Neo4j数据库"""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            # 测试连接
            with self.driver.session() as session:
                session.run('RETURN 1')
            logger.info('✅ 成功连接到Neo4j数据库')
            return True
        except Exception as e:
            logger.error(f"❌ 连接Neo4j失败: {e}")
            return False

    def setup_constraints_and_indexes(self):
        """设置约束和索引"""
        constraints_queries = [
            # 实体唯一性约束
            'CREATE CONSTRAINT IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE',

            # 实体类型索引
            'CREATE INDEX IF NOT EXISTS FOR (e:Entity) ON (e.type)',
            'CREATE INDEX IF NOT EXISTS FOR (e:Entity) ON (e.value)',
            'CREATE INDEX IF NOT EXISTS FOR (e:Entity) ON (e.quality_layer)',

            # 关系索引
            'CREATE INDEX IF NOT EXISTS FOR ()-[r:RELATED_TO]-() ON (r.type)',
            'CREATE INDEX IF NOT EXISTS FOR ()-[r:RELATED_TO]-() ON (r.confidence)'
        ]

        with self.driver.session() as session:
            for query in constraints_queries:
                try:
                    session.run(query)
                    logger.info(f"✅ 执行约束/索引: {query[:50]}...")
                except Exception as e:
                    logger.warning(f"⚠️ 约束/索引可能已存在: {e}")

    def import_entities_batch(self, entities: List[Dict], batch_size: int = 1000) -> int:
        """批量导入实体"""
        imported_count = 0

        with self.driver.session() as session:
            # 分批处理
            for i in range(0, len(entities), batch_size):
                batch = entities[i:i + batch_size]

                # 构建Cypher查询
                query = """
                UNWIND $entities AS entity
                CREATE (e:Entity {
                    id: entity.id,
                    type: entity.type,
                    value: entity.value,
                    source: entity.source,
                    confidence: entity.confidence,
                    context: entity.context,
                    quality_layer: entity.quality_layer,
                    created_at: datetime()
                })
                """

                try:
                    result = session.run(query, entities=batch)
                    batch_count = result.consume().counters.nodes_created
                    imported_count += batch_count
                    logger.info(f"📊 导入实体批次 {i//batch_size + 1}: {batch_count} 个实体")
                except Exception as e:
                    logger.error(f"❌ 导入实体批次失败: {e}")

        return imported_count

    def import_relations_batch(self, relations: List[Dict], batch_size: int = 1000) -> int:
        """批量导入关系"""
        imported_count = 0

        with self.driver.session() as session:
            # 分批处理
            for i in range(0, len(relations), batch_size):
                batch = relations[i:i + batch_size]

                # 构建Cypher查询
                query = """
                UNWIND $relations AS rel
                MATCH (from_entity:Entity {id: rel.from})
                MATCH (to_entity:Entity {id: rel.to})
                CREATE (from_entity)-[r:RELATED_TO {
                    type: rel.type,
                    source: rel.source,
                    confidence: rel.confidence,
                    distance: rel.distance,
                    created_at: datetime()
                }]->(to_entity)
                """

                try:
                    result = session.run(query, relations=batch)
                    batch_count = result.consume().counters.relationships_created
                    imported_count += batch_count
                    logger.info(f"📊 导入关系批次 {i//batch_size + 1}: {batch_count} 个关系")
                except Exception as e:
                    logger.error(f"❌ 导入关系批次失败: {e}")

        return imported_count

    def import_from_layered_results(self, results_file: str) -> Dict[str, Any]:
        """从分层处理结果导入数据"""
        logger.info(f"📂 开始导入分层处理结果: {results_file}")

        try:
            # 读取结果文件
            with open(results_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            results = data.get('results', [])
            layer_stats = data.get('processing_stats', {}).get('layer_stats', {})

            if not results:
                logger.warning('⚠️ 没有找到处理结果')
                return {'success': False, 'message': '没有找到处理结果'}

            # 收集所有实体和关系
            all_entities = []
            all_relations = []

            for result in results:
                entities = result.get('entities', [])
                relations = result.get('relations', [])
                quality_layer = result.get('quality', {}).get('quality_layer', 'basic')

                # 为实体添加质量分层信息
                for entity in entities:
                    entity['quality_layer'] = quality_layer
                    all_entities.append(entity)

                all_relations.extend(relations)

            logger.info(f"📊 统计: 实体 {len(all_entities)} 个, 关系 {len(all_relations)} 个")

            # 设置约束和索引
            logger.info('🔧 设置数据库约束和索引...')
            self.setup_constraints_and_indexes()

            # 导入实体
            logger.info('📥 开始导入实体...')
            start_time = time.time()
            imported_entities = self.import_entities_batch(all_entities)
            entity_time = time.time() - start_time

            # 导入关系
            logger.info('🔗 开始导入关系...')
            start_time = time.time()
            imported_relations = self.import_relations_batch(all_relations)
            relation_time = time.time() - start_time

            # 返回导入统计
            import_stats = {
                'success': True,
                'total_documents': len(results),
                'layer_stats': layer_stats,
                'imported_entities': imported_entities,
                'imported_relations': imported_relations,
                'entity_import_time': entity_time,
                'relation_import_time': relation_time,
                'total_import_time': entity_time + relation_time
            }

            logger.info(f"🏆 导入完成!")
            logger.info(f"   文档数: {import_stats['total_documents']}")
            logger.info(f"   实体数: {import_stats['imported_entities']}")
            logger.info(f"   关系数: {import_stats['imported_relations']}")
            logger.info(f"   导入时间: {import_stats['total_import_time']:.1f}秒")

            return import_stats

        except Exception as e:
            logger.error(f"❌ 导入过程中发生错误: {e}")
            import logging
            logging.exception('详细错误信息:')
            return {'success': False, 'message': str(e)}

    def create_quality_layer_views(self):
        """为不同质量层创建视图"""
        view_queries = [
            {
                'name': 'EliteEntities',
                'query': '''
                CREATE OR REPLACE VIEW EliteEntities AS
                MATCH (e:Entity {quality_layer: 'elite'})
                RETURN e.id, e.type, e.value, e.confidence, e.source
                '''
            },
            {
                'name': 'HighQualityEntities',
                'query': '''
                CREATE OR REPLACE VIEW HighQualityEntities AS
                MATCH (e:Entity {quality_layer: 'high_quality'})
                RETURN e.id, e.type, e.value, e.confidence, e.source
                '''
            },
            {
                'name': 'BasicEntities',
                'query': '''
                CREATE OR REPLACE VIEW BasicEntities AS
                MATCH (e:Entity {quality_layer: 'basic'})
                RETURN e.id, e.type, e.value, e.confidence, e.source
                '''
            },
            {
                'name': 'KnowledgeGraphStats',
                'query': '''
                CREATE OR REPLACE VIEW KnowledgeGraphStats AS
                MATCH (e:Entity)
                OPTIONAL MATCH (e)-[r]-()
                WITH e.type AS entityType, count(DISTINCT e) AS entityCount, count(DISTINCT r) AS relationCount
                RETURN entityType, entityCount, relationCount
                '''
            }
        ]

        with self.driver.session() as session:
            for view in view_queries:
                try:
                    session.run(view['query'])
                    logger.info(f"✅ 创建视图: {view['name']}")
                except Exception as e:
                    logger.warning(f"⚠️ 创建视图失败 {view['name']}: {e}")

    def get_graph_summary(self) -> Dict[str, Any]:
        """获取知识图谱摘要统计"""
        summary_queries = {
            'total_nodes': 'MATCH (n) RETURN count(n) AS count',
            'total_relationships': 'MATCH ()-[r]->() RETURN count(r) AS count',
            'entity_types': 'MATCH (e:Entity) RETURN e.type, count(e) AS count ORDER BY count DESC',
            'quality_layers': 'MATCH (e:Entity) RETURN e.quality_layer, count(e) AS count ORDER BY count DESC',
            'relation_types': 'MATCH ()-[r:RELATED_TO]->() RETURN r.type, count(r) AS count ORDER BY count DESC',
            'avg_confidence': 'MATCH (e:Entity) RETURN avg(e.confidence) AS avg_confidence'
        }

        summary = {}

        with self.driver.session() as session:
            for name, query in summary_queries.items():
                try:
                    result = session.run(query)
                    if name in ['total_nodes', 'total_relationships', 'avg_confidence']:
                        summary[name] = result.single()[0]
                    else:
                        summary[name] = [dict(record) for record in result]
                except Exception as e:
                    logger.warning(f"⚠️ 查询失败 {name}: {e}")
                    summary[name] = None

        return summary

    def close(self):
        """关闭数据库连接"""
        if self.driver:
            self.driver.close()

def main():
    """主函数"""
    logger.info('🔗 Neo4j 专利知识图谱导入工具')
    logger.info(str('=' * 50))
    logger.info('📥 将分层处理结果导入Neo4j图数据库')
    logger.info('🎯 支持批量导入和质量分层管理')
    logger.info(str('=' * 50))

    # 配置参数
    results_file = '/tmp/patent_layered_output/patent_layered_results_20251206_*.json'

    # 查找最新的结果文件
    import glob
    result_files = glob.glob(results_file)
    if not result_files:
        latest_file = None
    else:
        latest_file = max(result_files)
        logger.info(f"📂 找到结果文件: {latest_file}")

    if not latest_file:
        logger.info('❌ 未找到处理结果文件，请先运行分层处理系统')
        return 1

    # 创建导入器
    importer = Neo4jKnowledgeGraphImporter()

    try:
        # 连接数据库
        if not importer.connect():
            logger.info('❌ 无法连接到Neo4j数据库，请确保数据库已启动')
            return 1

        # 导入数据
        logger.info(f"\n🎯 开始导入知识图谱数据...")
        start_time = datetime.now()

        import_stats = importer.import_from_layered_results(latest_file)

        if import_stats['success']:
            # 创建质量分层视图
            logger.info(f"\n🔧 创建质量分层视图...")
            importer.create_quality_layer_views()

            # 获取图谱摘要
            logger.info(f"\n📊 生成知识图谱摘要...")
            summary = importer.get_graph_summary()

            logger.info(f"\n🏆 导入完成!")
            logger.info(str('=' * 50))
            logger.info(f"📊 导入统计:")
            logger.info(f"   处理文档: {import_stats['total_documents']:,}")
            logger.info(f"   导入实体: {import_stats['imported_entities']:,}")
            logger.info(f"   导入关系: {import_stats['imported_relations']:,}")
            logger.info(f"   导入时间: {import_stats['total_import_time']:.1f}秒")

            if summary.get('total_nodes'):
                logger.info(f"\n📈 图谱统计:")
                logger.info(f"   总节点数: {summary['total_nodes']:,}")
                logger.info(f"   总关系数: {summary['total_relationships']:,}")
                logger.info(f"   平均置信度: {summary.get('avg_confidence', 0):.3f}")

            logger.info(f"\n💡 接下来可以:")
            logger.info(f"   1. 访问 Neo4j Browser: http://localhost:7474")
            logger.info(f"   2. 查询精英实体: MATCH (e:Entity {quality_layer: 'elite'}) RETURN e")
            logger.info(f"   3. 分析关系网络: MATCH (e1)-[r]->(e2) RETURN e1.type, r.type, e2.type LIMIT 10")

        else:
            logger.info(f"❌ 导入失败: {import_stats['message']}")
            return 1

    except Exception as e:
        logger.info(f"❌ 导入过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        importer.close()

    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.info("\n👋 导入被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.info(f"\n❌ 导入异常: {e}")
        sys.exit(1)