#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Neo4j专利数据导入监控器
Neo4j Patent Data Import Monitor

监控专利知识图谱数据导入进度和质量

作者: Athena AI系统
创建时间: 2025年12月6日
版本: 1.0.0
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path

from neo4j import GraphDatabase

logger = logging.getLogger(__name__)

class Neo4jImportMonitor:
    """Neo4j导入监控器"""

    def __init__(self, uri='bolt://localhost:7687', username='neo4j', password='password'):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))

    def get_database_stats(self):
        """获取数据库统计信息"""
        with self.driver.session() as session:
            # 总体统计
            total_stats = session.run("""
                MATCH (n)
                OPTIONAL MATCH ()-[r]->()
                RETURN
                    count(DISTINCT n) as total_nodes,
                    count(DISTINCT r) as total_relationships
            """).single()

            # 节点类型统计
            node_types = session.run("""
                MATCH (n)
                RETURN labels(n) as labels, count(n) as count
                ORDER BY count DESC
            """).data()

            # 关系类型统计
            rel_types = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as type, count(r) as count
                ORDER BY count DESC
            """).data()

            # 专利统计
            patent_stats = session.run("""
                MATCH (p:Patent)
                RETURN
                    count(p) as total_patents,
                    count(DISTINCT p.layer) as layer_count,
                    avg(p.quality_score) as avg_quality
            """).single()

            # 按层统计
            layer_stats = session.run("""
                MATCH (p:Patent)
                RETURN p.layer as layer, count(p) as count
                ORDER BY count DESC
            """).data()

            return {
                'total_nodes': total_stats['total_nodes'],
                'total_relationships': total_stats['total_relationships'],
                'node_types': node_types,
                'relationship_types': rel_types,
                'patent_stats': patent_stats,
                'layer_stats': layer_stats
            }

    def get_sample_queries(self):
        """获取示例查询"""
        with self.driver.session() as session:
            # 示例专利
            sample_patents = session.run("""
                MATCH (p:Patent)
                RETURN p.patent_id, p.title, p.quality_score, p.layer
                LIMIT 5
            """).data()

            # 高质量实体
            top_entities = session.run("""
                MATCH (e:Entity)
                WHERE e.confidence > 0.8
                RETURN e.name, e.type, e.confidence
                LIMIT 5
            """).data()

            # 重要关系
            important_rels = session.run("""
                MATCH ()-[r]->()
                WHERE r.confidence > 0.8
                RETURN type(r), r.confidence
                LIMIT 5
            """).data()

            return {
                'sample_patents': sample_patents,
                'top_entities': top_entities,
                'important_rels': important_rels
            }

    def monitor_loop(self, interval=30):
        """监控循环"""
        try:
            while True:
                logger.info(str("\n" + '='*60))
                logger.info(f"📊 Neo4j专利知识图谱监控 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(str('='*60))

                stats = self.get_database_stats()

                logger.info(f"\n📈 总体统计:")
                logger.info(f"   总节点数: {stats['total_nodes']:,}")
                logger.info(f"   总关系数: {stats['total_relationships']:,}")

                logger.info(f"\n🎯 专利统计:")
                patent_stats = stats['patent_stats']
                logger.info(f"   专利总数: {patent_stats['total_patents']:,}")
                logger.info(f"   分层覆盖: {patent_stats['layer_count']}层")
                logger.info(f"   平均质量: {patent_stats['avg_quality']:.3f}")

                logger.info(f"\n📊 分层分布:")
                for layer in stats['layer_stats']:
                    logger.info(f"   {layer['layer']}: {layer['count']:,} 个专利")

                logger.info(f"\n🏷️ 主要节点类型 (前5):")
                for node_type in stats['node_types'][:5]:
                    labels = ', '.join(node_type['labels'])
                    logger.info(f"   {labels}: {node_type['count']:,}")

                logger.info(f"\n🔗 主要关系类型 (前5):")
                for rel_type in stats['relationship_types'][:5]:
                    logger.info(f"   {rel_type['type']}: {rel_type['count']:,}")

                # 检查导入进度
                total_files = len(list(Path('/tmp').glob('patent_*_results_*.json')))
                if total_files > 0:
                    progress = (stats['total_nodes'] / 1000000) * 100  # 假设目标100万节点
                    logger.info(f"\n🚀 导入进度: {min(progress, 100):.1f}% (基于节点数量)")

                logger.info(f"\n⏱️ 下次更新: {interval}秒后")
                logger.info('按 Ctrl+C 退出监控')

                time.sleep(interval)

        except KeyboardInterrupt:
            logger.info("\n👋 监控已停止")
        except Exception as e:
            logger.info(f"❌ 监控出错: {e}")

    def close(self):
        """关闭连接"""
        self.driver.close()

def main():
    """主函数"""
    logger.info('🔍 Neo4j专利数据导入监控器')
    logger.info(str('='*50))

    monitor = Neo4jImportMonitor()

    try:
        # 测试连接
        with monitor.driver.session() as session:
            session.run('RETURN 1')
        logger.info('✅ 成功连接到Neo4j')

        # 显示示例查询
        samples = monitor.get_sample_queries()
        logger.info(f"\n📋 示例专利:")
        for patent in samples['sample_patents']:
            logger.info(f"   {patent['p.patent_id']}: {patent['p.title'][:50]}... (质量: {patent['p.quality_score']:.3f})")

        # 开始监控
        monitor.monitor_loop(interval=30)

    except Exception as e:
        logger.info(f"❌ 启动监控失败: {e}")
    finally:
        monitor.close()

if __name__ == '__main__':
    main()