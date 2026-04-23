#!/usr/bin/env python3
"""
Neo4j 样本知识图谱导入工具
Neo4j Sample Knowledge Graph Import Tool

导入前100个文档的样本数据到Neo4j进行测试

作者: Athena AI系统
创建时间: 2025年12月6日
版本: 1.0.0
"""

import hashlib
import json
import logging
import os
import sys
from typing import Any

from neo4j import Driver, GraphDatabase

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SampleNeo4jImporter:
    """样本Neo4j导入器"""

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
            with self.driver.session() as session:
                session.run('RETURN 1')
            logger.info('✅ 成功连接到Neo4j数据库')
            return True
        except Exception as e:
            logger.error(f"❌ 连接Neo4j失败: {e}")
            return False

    def clear_sample_data(self):
        """清空样本数据（只删除专利相关节点）"""
        with self.driver.session() as session:
            try:
                logger.info('🗑️ 清空现有专利数据...')
                # 分批删除，避免内存问题
                session.run('MATCH (e:Entity) WHERE e.quality_layer IS NOT NULL DELETE e')
                session.run('MATCH ()-[r:RELATED_TO]-() DELETE r')
                logger.info('✅ 样本数据已清空')
            except Exception as e:
                logger.warning(f"⚠️ 清空数据时出现问题: {e}")

    def import_sample_data(self, results_file: str, sample_size: int = 100) -> dict[str, Any]:
        """导入样本数据"""
        logger.info(f"📂 开始导入样本数据: {sample_size}个文档")

        try:
            # 读取结果文件
            with open(results_file, encoding='utf-8') as f:
                data = json.load(f)

            results = data.get('results', [])
            if not results:
                logger.warning('⚠️ 没有找到处理结果')
                return {'success': False, 'message': '没有找到处理结果'}

            # 只取前N个文档作为样本
            sample_results = results[:sample_size]
            logger.info(f"📊 从 {len(results)} 个文档中选择前 {len(sample_results)} 个作为样本")

            # 清空现有样本数据
            self.clear_sample_data()

            # 统计变量
            total_entities = 0
            total_relations = 0

            with self.driver.session() as session:
                # 逐个文档导入
                for i, result in enumerate(sample_results):
                    entities = result.get('entities', [])
                    relations = result.get('relations', [])
                    file_path = result.get('file', 'unknown')
                    quality_layer = result.get('quality', {}).get('quality_layer', 'basic')

                    # 为实体添加质量分层信息
                    for entity in entities:
                        entity['quality_layer'] = quality_layer
                        # 生成唯一ID
                        entity['unique_id'] = hashlib.md5(
                            f"{entity['type']}_{entity['value']}_{file_path}".encode('utf-8', usedforsecurity=False)
                        ).hexdigest()[:16]

                    # 创建实体
                    for entity in entities:
                        try:
                            query = """
                            MERGE (e:Entity {id: $id})
                            SET e.type = $type,
                                e.value = $value,
                                e.source = $source,
                                e.confidence = $confidence,
                                e.context = $context,
                                e.quality_layer = $quality_layer,
                                e.created_at = datetime()
                            """
                            session.run(query,
                                id=entity['unique_id'],
                                type=entity['type'],
                                value=entity['value'],
                                source=entity['source'],
                                confidence=entity['confidence'],
                                context=entity.get('context', '')[:500],  # 限制上下文长度
                                quality_layer=entity['quality_layer']
                            )
                            total_entities += 1
                        except Exception as e:
                            logger.error(f"❌ 导入实体失败: {e}")

                    # 创建实体ID映射
                    entity_id_map = {}
                    for entity in entities:
                        entity_id_map[entity['id'] = entity['unique_id']

                    # 创建关系（只导入部分关系，避免数据过多）
                    relations_to_import = relations[:min(100, len(relations))]  # 每个文档最多100个关系

                    for relation in relations_to_import:
                        try:
                            from_id = entity_id_map.get(relation['from'])
                            to_id = entity_id_map.get(relation['to'])

                            if from_id and to_id:  # 确保实体ID存在
                                query = """
                                MATCH (from_entity:Entity {id: $from_id})
                                MATCH (to_entity:Entity {id: $to_id})
                                MERGE (from_entity)-[r:RELATED_TO]->(to_entity)
                                SET r.type = $type,
                                    r.source = $source,
                                    r.confidence = $confidence,
                                    r.created_at = datetime()
                                """
                                session.run(query,
                                    from_id=from_id,
                                    to_id=to_id,
                                    type=relation['type'],
                                    source=relation['source'],
                                    confidence=relation['confidence']
                                )
                                total_relations += 1
                        except Exception as e:
                            logger.error(f"❌ 导入关系失败: {e}")

                    # 显示进度
                    if (i + 1) % 10 == 0 or i == len(sample_results) - 1:
                        logger.info(f"📈 进度: {i+1}/{len(sample_results)} ({(i+1)/len(sample_results)*100:.1f}%) | "
                                  f"实体: {total_entities} | 关系: {total_relations}")

            import_stats = {
                'success': True,
                'total_documents': len(sample_results),
                'imported_entities': total_entities,
                'imported_relations': total_relations
            }

            logger.info("🏆 样本导入完成!")
            logger.info(f"   文档数: {import_stats['total_documents']}")
            logger.info(f"   实体数: {import_stats['imported_entities']}")
            logger.info(f"   关系数: {import_stats['imported_relations']}")

            return import_stats

        except Exception as e:
            logger.error(f"❌ 导入过程中发生错误: {e}")
            return {'success': False, 'message': str(e)}

    def get_graph_summary(self) -> dict[str, Any]:
        """获取图谱摘要统计"""
        with self.driver.session() as session:
            try:
                # 基本统计
                total_nodes = session.run('MATCH (n) RETURN count(n) AS count').single()['count']
                total_relationships = session.run('MATCH ()-[r]->() RETURN count(r) AS count').single()['count']

                # 质量分层统计
                layer_stats = session.run("""
                    MATCH (e:Entity)
                    WHERE e.quality_layer IS NOT NULL
                    RETURN e.quality_layer, count(e) AS count
                    ORDER BY count DESC
                """).data()

                # 实体类型统计
                type_stats = session.run("""
                    MATCH (e:Entity)
                    WHERE e.quality_layer IS NOT NULL
                    RETURN e.type, count(e) AS count
                    ORDER BY count DESC
                    LIMIT 10
                """).data()

                return {
                    'total_nodes': total_nodes,
                    'total_relationships': total_relationships,
                    'layer_stats': layer_stats,
                    'type_stats': type_stats
                }
            except Exception as e:
                logger.error(f"❌ 获取统计信息失败: {e}")
                return {}

    def close(self):
        """关闭数据库连接"""
        if self.driver:
            self.driver.close()

def main():
    """主函数"""
    logger.info('🔗 Neo4j 样本知识图谱导入工具')
    logger.info(str('=' * 45))
    logger.info('📥 导入前100个文档的样本数据')
    logger.info('🎯 适合测试和演示使用')
    logger.info(str('=' * 45))

    # 配置参数
    results_file = '/tmp/patent_layered_output/patent_layered_results_20251206_213935.json'
    sample_size = 100

    # 查找结果文件
    import glob
    result_files = glob.glob('/tmp/patent_layered_output/patent_layered_results_*.json')
    if result_files:
        latest_file = max(result_files)
        results_file = latest_file
        logger.info(f"📂 找到结果文件: {latest_file}")

    if not os.path.exists(results_file):
        logger.info('❌ 未找到处理结果文件')
        return 1

    # 创建导入器
    importer = SampleNeo4jImporter()

    try:
        # 连接数据库
        if not importer.connect():
            logger.info('❌ 无法连接到Neo4j数据库')
            return 1

        # 导入样本数据
        logger.info("\n🎯 开始导入样本数据...")
        import_stats = importer.import_sample_data(results_file, sample_size)

        if import_stats['success']:
            # 获取图谱摘要
            logger.info("\n📊 生成图谱摘要...")
            summary = importer.get_graph_summary()

            logger.info("\n🏆 样本导入完成!")
            logger.info(str('=' * 45))
            logger.info("📊 导入统计:")
            logger.info(f"   处理文档: {import_stats['total_documents']}")
            logger.info(f"   导入实体: {import_stats['imported_entities']}")
            logger.info(f"   导入关系: {import_stats['imported_relations']}")

            if summary.get('total_nodes'):
                logger.info("\n📈 图谱统计:")
                logger.info(f"   总节点数: {summary['total_nodes']}")
                logger.info(f"   总关系数: {summary['total_relationships']}")

                if summary.get('layer_stats'):
                    logger.info("\n🎯 质量分层:")
                    for layer in summary['layer_stats']:
                        logger.info(f"   {layer['quality_layer']}: {layer['count']} 个实体")

                if summary.get('type_stats'):
                    logger.info("\n🏷️ 实体类型 (前10):")
                    for type_stat in summary['type_stats']:
                        logger.info(f"   {type_stat['type']}: {type_stat['count']} 个")

            logger.info("\n💡 接下来可以:")
            logger.info("   1. 访问 Neo4j Browser: http://localhost:7474")
            logger.info("   2. 查询样本数据: MATCH (e:Entity) RETURN e LIMIT 10")
            logger.info("   3. 查看关系网络: MATCH (e1)-[r]->(e2) RETURN e1, r, e2 LIMIT 5")
            logger.info("   4. 分析质量分层: MATCH (e) RETURN e.quality_layer, count(e)")

        else:
            logger.info(f"❌ 导入失败: {import_stats['message']}")
            return 1

    except Exception as e:
        logger.info(f"❌ 导入过程中发生错误: {e}")
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
