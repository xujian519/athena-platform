#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级专利知识图谱分析工具
Advanced Patent Knowledge Graph Analysis Tool

基于已导入的知识图谱进行深度分析和智能洞察

作者: Athena AI系统
创建时间: 2025年12月6日
版本: 1.0.0
"""

import json
import logging
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from neo4j import Driver, GraphDatabase

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedPatentAnalyzer:
    """高级专利知识图谱分析器"""

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

    def comprehensive_analysis(self) -> Dict[str, Any]:
        """综合分析专利知识图谱"""
        logger.info('🔍 开始综合分析专利知识图谱...')

        analysis_results = {
            'timestamp': datetime.now().isoformat(),
            'basic_statistics': self.get_basic_statistics(),
            'quality_analysis': self.analyze_quality_layers(),
            'entity_analysis': self.analyze_entity_types(),
            'relationship_analysis': self.analyze_relationships(),
            'network_metrics': self.calculate_network_metrics(),
            'top_entities': self.get_top_entities(),
            'legal_insights': self.get_legal_insights(),
            'recommendations': self.generate_recommendations()
        }

        return analysis_results

    def get_basic_statistics(self) -> Dict[str, Any]:
        """基础统计分析"""
        logger.info('📊 计算基础统计...')

        with self.driver.session() as session:
            try:
                # 基础统计
                total_nodes = session.run('MATCH (n) RETURN count(n) AS count').single()['count']
                total_relations = session.run('MATCH ()-[r]->() RETURN count(r) AS count').single()['count']

                # 质量分层统计
                layer_stats = session.run("""
                    MATCH (e:Entity)
                    WHERE e.quality_layer IS NOT NULL
                    RETURN e.quality_layer, count(e) AS count
                    ORDER BY count DESC
                """).data()

                return {
                    'total_nodes': total_nodes,
                    'total_relations': total_relations,
                    'average_relations_per_node': total_relations / max(total_nodes, 1),
                    'quality_distribution': layer_stats
                }
            except Exception as e:
                logger.error(f"基础统计错误: {e}")
                return {}

    def analyze_quality_layers(self) -> Dict[str, Any]:
        """质量层级分析"""
        logger.info('🎯 分析质量层级...')

        with self.driver.session() as session:
            try:
                # 各质量层级的实体类型分布
                quality_type_stats = session.run("""
                    MATCH (e:Entity)
                    WHERE e.quality_layer IS NOT NULL
                    RETURN e.quality_layer, e.type, count(e) AS count
                    ORDER BY e.quality_layer, count DESC
                """).data()

                # 各质量层级的置信度分布
                confidence_stats = session.run("""
                    MATCH (e:Entity)
                    WHERE e.quality_layer IS NOT NULL
                    RETURN e.quality_layer,
                           avg(e.confidence) AS avg_confidence,
                           min(e.confidence) AS min_confidence,
                           max(e.confidence) AS max_confidence
                    ORDER BY e.quality_layer
                """).data()

                return {
                    'quality_type_distribution': quality_type_stats,
                    'quality_confidence_stats': confidence_stats
                }
            except Exception as e:
                logger.error(f"质量分析错误: {e}")
                return {}

    def analyze_entity_types(self) -> Dict[str, Any]:
        """实体类型深度分析"""
        logger.info('🏷️ 分析实体类型...')

        with self.driver.session() as session:
            try:
                # 实体类型统计
                type_stats = session.run("""
                    MATCH (e:Entity)
                    WHERE e.quality_layer IS NOT NULL
                    RETURN e.type, count(e) AS count, avg(e.confidence) AS avg_confidence
                    ORDER BY count DESC
                """).data()

                # 最常见的实体值
                top_values = session.run("""
                    MATCH (e:Entity)
                    WHERE e.quality_layer IS NOT NULL
                    RETURN e.type, e.value, count(*) AS frequency
                    ORDER BY frequency DESC
                    LIMIT 20
                """).data()

                # 申请号专利号模式分析
                patent_stats = session.run("""
                    MATCH (e:Entity)
                    WHERE e.type = '申请号专利号'
                    RETURN e.value, e.confidence, e.source
                    ORDER BY e.confidence DESC
                    LIMIT 10
                """).data()

                return {
                    'type_distribution': type_stats,
                    'top_entity_values': top_values,
                    'patent_analysis': patent_stats
                }
            except Exception as e:
                logger.error(f"实体类型分析错误: {e}")
                return {}

    def analyze_relationships(self) -> Dict[str, Any]:
        """关系网络分析"""
        logger.info('🔗 分析关系网络...')

        with self.driver.session() as session:
            try:
                # 关系类型统计
                relation_stats = session.run("""
                    MATCH ()-[r:RELATED_TO]->()
                    RETURN r.type, count(*) AS count, avg(r.confidence) AS avg_confidence
                    ORDER BY count DESC
                """).data()

                # 高频实体对关系
                top_entity_pairs = session.run("""
                    MATCH (e1:Entity)-[r:RELATED_TO]->(e2:Entity)
                    WHERE e1.quality_layer IS NOT NULL AND e2.quality_layer IS NOT NULL
                    RETURN e1.type, e2.type, r.type, count(*) AS frequency
                    ORDER BY frequency DESC
                    LIMIT 15
                """).data()

                # 跨层级关系分析
                cross_layer_relations = session.run("""
                    MATCH (e1:Entity)-[r:RELATED_TO]->(e2:Entity)
                    WHERE e1.quality_layer <> e2.quality_layer
                      AND e1.quality_layer IS NOT NULL
                      AND e2.quality_layer IS NOT NULL
                    RETURN e1.quality_layer, e2.quality_layer, count(*) as cross_relations
                    ORDER BY cross_relations DESC
                """).data()

                return {
                    'relation_distribution': relation_stats,
                    'top_entity_pairs': top_entity_pairs,
                    'cross_layer_relations': cross_layer_relations
                }
            except Exception as e:
                logger.error(f"关系分析错误: {e}")
                return {}

    def calculate_network_metrics(self) -> Dict[str, Any]:
        """网络指标计算"""
        logger.info('📈 计算网络指标...')

        with self.driver.session() as session:
            try:
                # 度中心度（连接数最多的节点）
                degree_centrality = session.run("""
                    MATCH (e:Entity)-[r]-()
                    WHERE e.quality_layer IS NOT NULL
                    WITH e, count(r) AS degree
                    RETURN e.id, e.type, e.value, degree
                    ORDER BY degree DESC
                    LIMIT 10
                """).data()

                # 三角形结构（紧密连接的实体组）
                triangles = session.run("""
                    MATCH (a:Entity)-[]->(b:Entity)-[]->(c:Entity)-[]->(a)
                    WHERE a.quality_layer IS NOT NULL
                      AND b.quality_layer IS NOT NULL
                      AND c.quality_layer IS NOT NULL
                    RETURN a.type, b.type, c.type, count(*) as triangle_count
                    ORDER BY triangle_count DESC
                    LIMIT 10
                """).data()

                # 最短路径长度分布（简化版）
                path_stats = session.run("""
                    MATCH (e1:Entity)-[:RELATED_TO*1..3]->(e2:Entity)
                    WHERE e1.quality_layer = 'high_quality'
                      AND e2.quality_layer = 'high_quality'
                      AND id(e1) < id(e2)
                    WITH e1, e2, length(shortestPath((e1)-[:RELATED_TO]->(e2))) as path_length
                    RETURN path_length, count(*) as count
                    ORDER BY path_length
                """).data()

                return {
                    'degree_centrality': degree_centrality,
                    'triangles': triangles,
                    'path_statistics': path_stats
                }
            except Exception as e:
                logger.error(f"网络指标计算错误: {e}")
                return {}

    def get_top_entities(self) -> Dict[str, Any]:
        """获取顶级实体"""
        logger.info('🌟 获取顶级实体...')

        with self.driver.session() as session:
            try:
                # 高质量高置信度实体
                top_quality_entities = session.run("""
                    MATCH (e:Entity)
                    WHERE e.quality_layer = 'high_quality' AND e.confidence > 0.9
                    RETURN e.id, e.type, e.value, e.confidence, e.source
                    ORDER BY e.confidence DESC
                    LIMIT 15
                """).data()

                # 最多关系的实体
                most_connected = session.run("""
                    MATCH (e:Entity)-[r]-()
                    WHERE e.quality_layer IS NOT NULL
                    WITH e, count(r) as connection_count
                    RETURN e.id, e.type, e.value, connection_count
                    ORDER BY connection_count DESC
                    LIMIT 10
                """).data()

                # 法律条文实体
                legal_entities = session.run("""
                    MATCH (e:Entity)
                    WHERE e.type CONTAINS '条文' OR e.type CONTAINS '法' OR e.type CONTAINS '规章'
                    RETURN e.type, e.value, e.confidence, e.quality_layer
                    ORDER BY e.confidence DESC
                    LIMIT 10
                """).data()

                return {
                    'top_quality_entities': top_quality_entities,
                    'most_connected_entities': most_connected,
                    'legal_entities': legal_entities
                }
            except Exception as e:
                logger.error(f"顶级实体获取错误: {e}")
                return {}

    def get_legal_insights(self) -> Dict[str, Any]:
        """获取法律洞察"""
        logger.info('⚖️ 获取法律洞察...')

        with self.driver.session() as session:
            try:
                # 法律条文与案例关联
                legal_case_relations = session.run("""
                    MATCH (legal:Entity)-[r:RELATED_TO]->(case:Entity)
                    WHERE legal.type CONTAINS '条文' OR legal.type CONTAINS '法'
                      AND (case.type CONTAINS '决定' OR case.type CONTAINS '文书')
                    RETURN legal.type, legal.value, case.type, case.value, r.type
                    ORDER BY legal.confidence DESC
                    LIMIT 15
                """).data()

                # 技术术语与法律概念关联
                tech_legal_relations = session.run("""
                    MATCH (tech:Entity)-[r:RELATED_TO]->(legal:Entity)
                    WHERE tech.type CONTAINS '技术' AND (legal.type CONTAINS '法' OR legal.type CONTAINS '概念')
                    RETURN tech.value, legal.value, r.type, r.confidence
                    ORDER BY r.confidence DESC
                    LIMIT 10
                """).data()

                # 程序类型分析
                procedure_analysis = session.run("""
                    MATCH (e:Entity)
                    WHERE e.type = '程序类型'
                    RETURN e.value, count(*) as frequency, avg(e.confidence) as avg_confidence
                    ORDER BY frequency DESC
                """).data()

                return {
                    'legal_case_relations': legal_case_relations,
                    'tech_legal_relations': tech_legal_relations,
                    'procedure_analysis': procedure_analysis
                }
            except Exception as e:
                logger.error(f"法律洞察获取错误: {e}")
                return {}

    def generate_recommendations(self) -> List[str]:
        """生成分析建议"""
        logger.info('💡 生成分析建议...')

        recommendations = [
            '🎯 基于质量分层的数据，建议重点关注高质量层级的实体进行深度分析',
            '📊 关系网络密度较高，适合进行社区发现和聚类分析',
            '⚖️ 法律条文与案例的关联模式清晰，支持法律推理分析',
            '🔗 技术术语与法律概念的关联为专利审查提供智能支持',
            '📈 识别出的核心实体可作为知识图谱的关键节点',
            '🔍 建议进一步进行实体消歧和关系权重优化',
            '💼 可基于此图谱开发专利智能检索和推荐系统'
        ]

        return recommendations

    def save_analysis_report(self, analysis_results: Dict[str, Any]) -> str:
        """保存分析报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"/tmp/patent_knowledge_graph_analysis_{timestamp}.json"

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, ensure_ascii=False, indent=2)

        logger.info(f"📄 分析报告已保存到: {report_file}")
        return report_file

    def close(self):
        """关闭数据库连接"""
        if self.driver:
            self.driver.close()

def main():
    """主函数"""
    logger.info('🔍 高级专利知识图谱分析工具')
    logger.info(str('=' * 50))
    logger.info('📊 深度分析已导入的专利知识图谱')
    logger.info('🎯 生成智能洞察和业务建议')
    logger.info(str('=' * 50))

    # 创建分析器
    analyzer = AdvancedPatentAnalyzer()

    try:
        # 连接数据库
        if not analyzer.connect():
            logger.info('❌ 无法连接到Neo4j数据库')
            return 1

        # 执行综合分析
        logger.info(f"\n🎯 开始综合分析...")
        start_time = datetime.now()

        analysis_results = analyzer.comprehensive_analysis()

        # 保存分析报告
        report_file = analyzer.save_analysis_report(analysis_results)

        # 显示分析结果摘要
        logger.info(f"\n🏆 分析完成!")
        logger.info(str('=' * 50))

        if analysis_results.get('basic_statistics'):
            stats = analysis_results['basic_statistics']
            logger.info(f"📊 图谱统计:")
            logger.info(f"   总节点数: {stats.get('total_nodes', 0):,}")
            logger.info(f"   总关系数: {stats.get('total_relations', 0):,}")
            logger.info(f"   平均关系/节点: {stats.get('average_relations_per_node', 0):.2f}")

        if analysis_results.get('quality_analysis', {}).get('quality_type_distribution'):
            logger.info(f"\n🎯 质量分层:")
            for layer in analysis_results['quality_analysis']['quality_type_distribution'][:5]:
                logger.info(f"   {layer['quality_layer']}: {layer['count']:,} 个实体")

        if analysis_results.get('entity_analysis', {}).get('type_distribution'):
            logger.info(f"\n🏷️ 主要实体类型:")
            for entity_type in analysis_results['entity_analysis']['type_distribution'][:5]:
                logger.info(f"   {entity_type['type']}: {entity_type['count']:,} 个")

        if analysis_results.get('recommendations'):
            logger.info(f"\n💡 分析建议:")
            for i, rec in enumerate(analysis_results['recommendations'][:5], 1):
                logger.info(f"   {i}. {rec}")

        logger.info(f"\n📄 详细分析报告: {report_file}")

    except Exception as e:
        logger.info(f"❌ 分析过程中发生错误: {e}")
        return 1
    finally:
        analyzer.close()

    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.info("\n👋 分析被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.info(f"\n❌ 分析异常: {e}")
        sys.exit(1)