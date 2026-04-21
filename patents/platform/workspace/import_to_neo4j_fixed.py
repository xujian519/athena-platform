#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Neo4j 知识图谱导入工具（修复版）
Neo4j Knowledge Graph Import Tool (Fixed Version)

修复实体ID重复问题，确保唯一性导入

作者: Athena AI系统
创建时间: 2025年12月6日
版本: 1.1.0
"""

import hashlib
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from neo4j import Driver, GraphDatabase, Session

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FixedNeo4jKnowledgeGraphImporter:
    """修复版Neo4j知识图谱导入器"""

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

    def clear_existing_data(self):
        """清空现有数据（谨慎使用）"""
        with self.driver.session() as session:
            # 删除所有关系和节点
            logger.warning('⚠️ 清空现有数据...')
            session.run('MATCH ()-[r]-() DELETE r')
            session.run('MATCH (n) DELETE n')
            logger.info('✅ 数据已清空')

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

    def generate_unique_id(self, entity: Dict, file_path: str) -> str:
        """生成唯一实体ID"""
        # 组合多个字段确保唯一性
        unique_string = f"{entity['type']}_{entity['value']}_{file_path}"
        return hashlib.md5(unique_string.encode('utf-8'), usedforsecurity=False).hexdigest()[:16]

    def import_entities_batch(self, entities: List[Dict], file_path: str, batch_size: int = 100) -> int:
        """批量导入实体（修复版）"""
        imported_count = 0

        # 生成唯一ID
        for entity in entities:
            entity['unique_id'] = self.generate_unique_id(entity, file_path)

        with self.driver.session() as session:
            # 分批处理
            for i in range(0, len(entities), batch_size):
                batch = entities[i:i + batch_size]

                # 构建Cypher查询 - 使用MERGE避免重复
                query = """
                UNWIND $entities AS entity
                MERGE (e:Entity {id: entity.unique_id})
                SET e.type = entity.type,
                    e.value = entity.value,
                    e.source = entity.source,
                    e.confidence = entity.confidence,
                    e.context = entity.context,
                    e.quality_layer = entity.quality_layer,
                    e.created_at = datetime()
                """

                try:
                    result = session.run(query, entities=batch)
                    counters = result.consume().counters
                    batch_count = counters.nodes_created  # 只计算新创建的节点
                    imported_count += batch_count
                    logger.info(f"📊 导入实体批次 {i//batch_size + 1}: 处理 {len(batch)} 个实体 (新建: {batch_count})")
                except Exception as e:
                    logger.error(f"❌ 导入实体批次失败: {e}")

        return imported_count

    def import_relations_batch(self, relations: List[Dict], entities: List[Dict], file_path: str, batch_size: int = 100) -> int:
        """批量导入关系（修复版）"""
        imported_count = 0

        # 创建实体ID映射
        entity_id_map = {}
        for entity in entities:
            entity_id_map[entity['id']] = self.generate_unique_id(entity, file_path)

        # 更新关系中的实体ID
        for relation in relations:
            relation['from_unique_id'] = entity_id_map.get(relation['from'])
            relation['to_unique_id'] = entity_id_map.get(relation['to'])

            # 生成唯一关系ID
            relation['unique_id'] = hashlib.md5(
                f"{relation['from_unique_id']}_{relation['to_unique_id']}_{relation['type']}".encode('utf-8', usedforsecurity=False)
            ).hexdigest()[:16]

        with self.driver.session() as session:
            # 分批处理
            for i in range(0, len(relations), batch_size):
                batch = relations[i:i + batch_size]

                # 构建Cypher查询 - 使用MERGE避免重复
                query = """
                UNWIND $relations AS rel
                MATCH (from_entity:Entity {id: rel.from_unique_id})
                MATCH (to_entity:Entity {id: rel.to_unique_id})
                MERGE (from_entity)-[r:RELATED_TO {id: rel.unique_id}]->(to_entity)
                SET r.type = rel.type,
                    r.source = rel.source,
                    r.confidence = rel.confidence,
                    r.distance = rel.distance,
                    r.created_at = datetime()
                """

                try:
                    result = session.run(query, relations=batch)
                    counters = result.consume().counters
                    batch_count = counters.relationships_created  # 只计算新创建的关系
                    imported_count += batch_count
                    logger.info(f"📊 导入关系批次 {i//batch_size + 1}: 处理 {len(batch)} 个关系 (新建: {batch_count})")
                except Exception as e:
                    logger.error(f"❌ 导入关系批次失败: {e}")

        return imported_count

    def import_from_layered_results(self, results_file: str, clear_data: bool = True) -> Dict[str, Any]:
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

            # 清空现有数据（如果需要）
            if clear_data:
                self.clear_existing_data()

            # 设置约束和索引
            logger.info('🔧 设置数据库约束和索引...')
            self.setup_constraints_and_indexes()

            # 导入实体和关系（按文档分组）
            total_entities_imported = 0
            total_relations_imported = 0
            processed_docs = 0

            logger.info('📥 开始逐个文档导入...')
            start_time = time.time()

            for result in results:
                entities = result.get('entities', [])
                relations = result.get('relations', [])
                file_path = result.get('file', 'unknown')
                quality_layer = result.get('quality', {}).get('quality_layer', 'basic')

                # 为实体添加质量分层信息
                for entity in entities:
                    entity['quality_layer'] = quality_layer

                # 导入该文档的实体和关系
                entities_imported = self.import_entities_batch(entities, file_path)
                relations_imported = self.import_relations_batch(relations, entities, file_path)

                total_entities_imported += entities_imported
                total_relations_imported += relations_imported
                processed_docs += 1

                # 显示进度
                if processed_docs % 100 == 0 or processed_docs == len(results):
                    elapsed = time.time() - start_time
                    speed = processed_docs / elapsed if elapsed > 0 else 0
                    eta = (len(results) - processed_docs) / speed if speed > 0 else 0

                    logger.info(f"📈 进度: {processed_docs}/{len(results)} ({processed_docs/len(results)*100:.1f}%) | "
                              f"实体: {total_entities_imported:,} | 关系: {total_relations_imported:,} | "
                              f"速度: {speed:.1f} 文档/秒 | ETA: {eta/60:.1f}分钟")

            # 计算导入时间
            import_time = time.time() - start_time

            # 返回导入统计
            import_stats = {
                'success': True,
                'total_documents': len(results),
                'layer_stats': layer_stats,
                'imported_entities': total_entities_imported,
                'imported_relations': total_relations_imported,
                'entity_import_time': import_time,
                'relation_import_time': import_time,
                'total_import_time': import_time
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
    logger.info('🔗 Neo4j 专利知识图谱导入工具（修复版）')
    logger.info(str('=' * 55))
    logger.info('📥 修复实体ID重复问题，确保唯一性导入')
    logger.info('🎯 支持批量导入和质量分层管理')
    logger.info(str('=' * 55))

    # 配置参数
    results_file = '/tmp/patent_layered_output/patent_layered_results_20251206_213935.json'

    # 查找最新的结果文件
    import glob
    result_files = glob.glob('/tmp/patent_layered_output/patent_layered_results_*.json')
    if result_files:
        latest_file = max(result_files)
        logger.info(f"📂 找到结果文件: {latest_file}")
        results_file = latest_file

    if not os.path.exists(results_file):
        logger.info('❌ 未找到处理结果文件，请先运行分层处理系统')
        return 1

    # 创建导入器
    importer = FixedNeo4jKnowledgeGraphImporter()

    try:
        # 连接数据库
        if not importer.connect():
            logger.info('❌ 无法连接到Neo4j数据库，请确保数据库已启动')
            return 1

        # 导入数据
        logger.info(f"\n🎯 开始导入知识图谱数据...")
        start_time = datetime.now()

        import_stats = importer.import_from_layered_results(results_file, clear_data=True)

        if import_stats['success']:
            # 获取图谱摘要
            logger.info(f"\n📊 生成知识图谱摘要...")
            summary = importer.get_graph_summary()

            logger.info(f"\n🏆 导入完成!")
            logger.info(str('=' * 55))
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

                if summary.get('quality_layers'):
                    logger.info(f"\n🎯 质量分层分布:")
                    for layer in summary['quality_layers']:
                        logger.info(f"   {layer['quality_layer']}: {layer['count']:,} 个实体")

            logger.info(f"\n💡 接下来可以:")
            logger.info(f"   1. 访问 Neo4j Browser: http://localhost:7474")
            logger.info(f"   2. 查询精英实体: MATCH (e:Entity {quality_layer: 'elite'}) RETURN e")
            logger.info(f"   3. 分析关系网络: MATCH (e1)-[r]->(e2) RETURN e1.type, r.type, e2.type LIMIT 10")
            logger.info(f"   4. 查看质量分布: MATCH (e) RETURN e.quality_layer, count(e)")

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