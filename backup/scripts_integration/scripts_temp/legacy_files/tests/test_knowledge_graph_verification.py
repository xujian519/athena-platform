#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Athena工作平台 - 知识图谱验证工具
Knowledge Graph Verification Tool for Athena Platform

验证SQLite和Neo4j两种知识图谱的完整性和可运行性

作者: 小诺 (AI助手)
创建时间: 2025-12-11
"""

import json
import logging
import os
import sqlite3
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KnowledgeGraphVerifier:
    """知识图谱验证器"""

    def __init__(self):
        self.project_root = project_root
        self.sqlite_kg_path = os.path.join(project_root, 'data/knowledge_graph_sqlite/databases/patent_knowledge_graph.db')
        self.neo4j_config = {
            'uri': 'bolt://localhost:7687',
            'username': 'neo4j',
            'password': 'password',
            'database': 'neo4j'
        }

        # 验证结果
        self.verification_results = {
            'timestamp': datetime.now().isoformat(),
            'sqlite': {},
            'neo4j': {},
            'summary': {}
        }

    def verify_sqlite_knowledge_graph(self) -> Dict[str, Any]:
        """验证SQLite知识图谱"""
        logger.info('🗄️ 开始验证SQLite知识图谱...')

        try:
            result = {
                'status': 'unknown',
                'database_path': self.sqlite_kg_path,
                'exists': False,
                'tables': {},
                'statistics': {},
                'sample_data': {},
                'errors': []
            }

            # 检查数据库文件是否存在
            if not os.path.exists(self.sqlite_kg_path):
                result['exists'] = False
                result['status'] = 'error'
                result['errors'].append('SQLite知识图谱数据库文件不存在')
                return result

            result['exists'] = True

            # 连接数据库
            conn = sqlite3.connect(self.sqlite_kg_path)
            cursor = conn.cursor()

            # 获取所有表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            result['tables']['list'] = tables
            result['tables']['count'] = len(tables)

            # 检查核心表
            core_tables = ['patent_entities', 'patent_relations', 'patent_entities_fts']
            result['tables']['core_present'] = all(table in tables for table in core_tables)

            # 获取统计信息
            if 'patent_entities' in tables:
                cursor.execute('SELECT COUNT(*) FROM patent_entities')
                entity_count = cursor.fetchone()[0]
                result['statistics']['entity_count'] = entity_count

                cursor.execute('SELECT COUNT(*) FROM patent_entities WHERE LENGTH(TRIM(name)) > 0')
                valid_entities = cursor.fetchone()[0]
                result['statistics']['valid_entity_count'] = valid_entities

                # 获取样例实体
                cursor.execute('SELECT id, name, type FROM patent_entities LIMIT 5')
                sample_entities = []
                for row in cursor.fetchall():
                    sample_entities.append({
                        'id': row[0],
                        'name': row[1][:50] + '...' if len(row[1]) > 50 else row[1],
                        'type': row[2]
                    })
                result['sample_data']['entities'] = sample_entities

            if 'patent_relations' in tables:
                cursor.execute('SELECT COUNT(*) FROM patent_relations')
                relation_count = cursor.fetchone()[0]
                result['statistics']['relation_count'] = relation_count

                # 获取样例关系
                cursor.execute('SELECT source, target, relation FROM patent_relations LIMIT 5')
                sample_relations = []
                for row in cursor.fetchall():
                    sample_relations.append({
                        'source': row[0],
                        'target': row[1],
                        'relation': row[2]
                    })
                result['sample_data']['relations'] = sample_relations

            # 检查全文搜索功能
            if 'patent_entities_fts' in tables:
                cursor.execute('SELECT COUNT(*) FROM patent_entities_fts')
                fts_count = cursor.fetchone()[0]
                result['statistics']['fts_count'] = fts_count

                # 测试全文搜索
                try:
                    cursor.execute("SELECT COUNT(*) FROM patent_entities_fts WHERE patent_entities_fts MATCH '专利'")
                    search_results = cursor.fetchone()[0]
                    result['statistics']['search_test_results'] = search_results
                except Exception as e:
                    result['errors'].append(f"全文搜索测试失败: {str(e)}")

            # 获取数据库文件大小
            file_size = os.path.getsize(self.sqlite_kg_path)
            result['statistics']['file_size_mb'] = round(file_size / (1024 * 1024), 2)

            conn.close()

            # 判断总体状态
            if result['tables']['core_present'] and result['statistics'].get('entity_count', 0) > 0:
                result['status'] = 'success'
            else:
                result['status'] = 'partial'

            logger.info(f"✅ SQLite知识图谱验证完成: {result['status']}")
            return result

        except Exception as e:
            logger.error(f"❌ SQLite知识图谱验证失败: {e}")
            result['status'] = 'error'
            result['errors'].append(str(e))
            return result

    def verify_neo4j_knowledge_graph(self) -> Dict[str, Any]:
        """验证Neo4j知识图谱"""
        logger.info('🌐 开始验证Neo4j知识图谱...')

        try:
            result = {
                'status': 'unknown',
                'config': self.neo4j_config,
                'connection': {},
                'schema': {},
                'statistics': {},
                'sample_data': {},
                'errors': []
            }

            # 尝试导入Neo4j库
            try:
                from neo4j import GraphDatabase
                result['connection']['neo4j_available'] = True
            except ImportError:
                result['connection']['neo4j_available'] = False
                result['status'] = 'error'
                result['errors'].append('neo4j库未安装，请使用: pip install neo4j')
                return result

            # 尝试连接
            driver = GraphDatabase.driver(
                self.neo4j_config['uri'],
                auth=(self.neo4j_config['username'], self.neo4j_config['password'])
            )

            try:
                # 测试连接
                with driver.session(database=self.neo4j_config['database']) as session:
                    session.run('RETURN 1')
                    result['connection']['status'] = 'connected'
                    result['connection']['message'] = '成功连接到Neo4j数据库'

                    # 检查数据库状态
                    db_info = session.run('CALL dbms.components() YIELD name, versions').single()
                    result['schema']['neo4j_version'] = db_info['versions'][0]

                    # 获取节点和关系统计
                    node_stats = session.run('MATCH (n) RETURN count(n) as node_count').single()
                    result['statistics']['node_count'] = node_stats['node_count']

                    relation_stats = session.run('MATCH ()-[r]->() RETURN count(r) as relation_count').single()
                    result['statistics']['relation_count'] = relation_stats['relation_count']

                    # 获取节点标签统计
                    label_stats = session.run('MATCH (n) RETURN labels(n) as labels, count(n) as count').data()
                    result['schema']['node_labels'] = {}
                    for stat in label_stats:
                        if stat['labels']:
                            for label in stat['labels']:
                                if label not in result['schema']['node_labels']:
                                    result['schema']['node_labels'][label] = 0
                                result['schema']['node_labels'][label] += stat['count']

                    # 获取关系类型统计
                    rel_type_stats = session.run('MATCH ()-[r]->() RETURN type(r) as type, count(r) as count').data()
                    result['schema']['relation_types'] = {
                        stat['type']: stat['count'] for stat in rel_type_stats
                    }

                    # 获取样例数据
                    if result['statistics']['node_count'] > 0:
                        sample_nodes = session.run('MATCH (n) RETURN n LIMIT 5').data()
                        result['sample_data']['nodes'] = []
                        for node_data in sample_nodes[:3]:  # 只取前3个
                            node = node_data['n']
                            result['sample_data']['nodes'].append({
                                'labels': list(node.labels),
                                'properties': dict(node)
                            })

                    if result['statistics']['relation_count'] > 0:
                        sample_relations = session.run('MATCH ()-[r]->() RETURN r LIMIT 5').data()
                        result['sample_data']['relations'] = []
                        for rel_data in sample_relations[:3]:  # 只取前3个
                            rel = rel_data['r']
                            result['sample_data']['relations'].append({
                                'type': rel.type,
                                'properties': dict(rel)
                            })

                    # 测试基本查询功能
                    try:
                        test_query = 'MATCH (n) RETURN count(n) LIMIT 1'
                        test_result = session.run(test_query).single()
                        result['schema']['query_test'] = 'success'
                    except Exception as e:
                        result['schema']['query_test'] = f"failed: {str(e)}"

                    # 判断总体状态
                    if result['statistics']['node_count'] > 0 or result['statistics']['relation_count'] > 0:
                        result['status'] = 'success'
                    else:
                        result['status'] = 'empty'

            except Exception as e:
                result['connection']['status'] = 'failed'
                result['connection']['message'] = str(e)
                result['status'] = 'error'
                result['errors'].append(f"连接失败: {str(e)}")

            finally:
                driver.close()

            logger.info(f"✅ Neo4j知识图谱验证完成: {result['status']}")
            return result

        except Exception as e:
            logger.error(f"❌ Neo4j知识图谱验证失败: {e}")
            result['status'] = 'error'
            result['errors'].append(str(e))
            return result

    def test_basic_functionality(self) -> Dict[str, Any]:
        """测试知识图谱基本功能"""
        logger.info('🧪 开始测试知识图谱基本功能...')

        test_results = {
            'sqlite_tests': {},
            'neo4j_tests': {},
            'functionality_score': 0
        }

        # SQLite功能测试
        sqlite_tests = self._test_sqlite_functionality()
        test_results['sqlite_tests'] = sqlite_tests

        # Neo4j功能测试
        neo4j_tests = self._test_neo4j_functionality()
        test_results['neo4j_tests'] = neo4j_tests

        # 计算功能评分
        sqlite_score = sqlite_tests.get('success_rate', 0)
        neo4j_score = neo4j_tests.get('success_rate', 0)
        test_results['functionality_score'] = (sqlite_score + neo4j_score) / 2

        logger.info(f"✅ 基本功能测试完成，评分: {test_results['functionality_score']:.1f}%")
        return test_results

    def _test_sqlite_functionality(self) -> Dict[str, Any]:
        """测试SQLite知识图谱功能"""
        test_results = {
            'tests': {},
            'success_count': 0,
            'total_tests': 0,
            'success_rate': 0
        }

        try:
            conn = sqlite3.connect(self.sqlite_kg_path)
            cursor = conn.cursor()

            # 测试1: 实体查询
            try:
                cursor.execute("SELECT COUNT(*) FROM patent_entities WHERE name LIKE '%专利%'")
                count = cursor.fetchone()[0]
                test_results['tests']['entity_search'] = {
                    'status': 'success',
                    'result': count
                }
                test_results['success_count'] += 1
            except Exception as e:
                test_results['tests']['entity_search'] = {
                    'status': 'failed',
                    'error': str(e)
                }

            test_results['total_tests'] += 1

            # 测试2: 关系查询
            try:
                cursor.execute('SELECT COUNT(*) FROM patent_relations LIMIT 10')
                count = cursor.fetchone()[0]
                test_results['tests']['relation_query'] = {
                    'status': 'success',
                    'result': count
                }
                test_results['success_count'] += 1
            except Exception as e:
                test_results['tests']['relation_query'] = {
                    'status': 'failed',
                    'error': str(e)
                }

            test_results['total_tests'] += 1

            # 测试3: 全文搜索
            try:
                cursor.execute("SELECT COUNT(*) FROM patent_entities_fts WHERE patent_entities_fts MATCH '法律' LIMIT 10")
                count = cursor.fetchone()[0]
                test_results['tests']['full_text_search'] = {
                    'status': 'success',
                    'result': count
                }
                test_results['success_count'] += 1
            except Exception as e:
                test_results['tests']['full_text_search'] = {
                    'status': 'failed',
                    'error': str(e)
                }

            test_results['total_tests'] += 1

            # 测试4: 聚合查询
            try:
                cursor.execute('SELECT type, COUNT(*) FROM patent_entities GROUP BY type LIMIT 5')
                results = cursor.fetchall()
                test_results['tests']['aggregate_query'] = {
                    'status': 'success',
                    'result': len(results)
                }
                test_results['success_count'] += 1
            except Exception as e:
                test_results['tests']['aggregate_query'] = {
                    'status': 'failed',
                    'error': str(e)
                }

            test_results['total_tests'] += 1

            conn.close()

        except Exception as e:
            test_results['error'] = str(e)

        # 计算成功率
        if test_results['total_tests'] > 0:
            test_results['success_rate'] = (test_results['success_count'] / test_results['total_tests']) * 100

        return test_results

    def _test_neo4j_functionality(self) -> Dict[str, Any]:
        """测试Neo4j知识图谱功能"""
        test_results = {
            'tests': {},
            'success_count': 0,
            'total_tests': 0,
            'success_rate': 0
        }

        try:
            from neo4j import GraphDatabase

# 导入标准化数据库工具
from shared.database.db_utils import DatabaseManager, build_safe_query

            driver = GraphDatabase.driver(
                self.neo4j_config['uri'],
                auth=(self.neo4j_config['username'], self.neo4j_config['password'])
            )

            with driver.session(database=self.neo4j_config['database']) as session:

                # 测试1: 节点查询
                try:
                    result = session.run('MATCH (n) RETURN count(n) as count').single()
                    count = result['count']
                    test_results['tests']['node_query'] = {
                        'status': 'success',
                        'result': count
                    }
                    test_results['success_count'] += 1
                except Exception as e:
                    test_results['tests']['node_query'] = {
                        'status': 'failed',
                        'error': str(e)
                    }

                test_results['total_tests'] += 1

                # 测试2: 关系查询
                try:
                    result = session.run('MATCH ()-[r]->() RETURN count(r) as count').single()
                    count = result['count']
                    test_results['tests']['relation_query'] = {
                        'status': 'success',
                        'result': count
                    }
                    test_results['success_count'] += 1
                except Exception as e:
                    test_results['tests']['relation_query'] = {
                        'status': 'failed',
                        'error': str(e)
                    }

                test_results['total_tests'] += 1

                # 测试3: 路径查询
                try:
                    result = list(session.run('MATCH (n) WHERE n.name IS NOT NULL RETURN n LIMIT 3'))
                    count = len(result)
                    test_results['tests']['path_query'] = {
                        'status': 'success',
                        'result': count
                    }
                    test_results['success_count'] += 1
                except Exception as e:
                    test_results['tests']['path_query'] = {
                        'status': 'failed',
                        'error': str(e)
                    }

                test_results['total_tests'] += 1

                # 测试4: 聚合查询
                try:
                    result = session.run('MATCH (n) RETURN labels(n) as labels, count(n) as count LIMIT 5')
                    count = len(list(result))
                    test_results['tests']['aggregate_query'] = {
                        'status': 'success',
                        'result': count
                    }
                    test_results['success_count'] += 1
                except Exception as e:
                    test_results['tests']['aggregate_query'] = {
                        'status': 'failed',
                        'error': str(e)
                    }

                test_results['total_tests'] += 1

            driver.close()

        except Exception as e:
            test_results['error'] = str(e)

        # 计算成功率
        if test_results['total_tests'] > 0:
            test_results['success_rate'] = (test_results['success_count'] / test_results['total_tests']) * 100

        return test_results

    def generate_verification_report(self) -> Dict[str, Any]:
        """生成完整的验证报告"""
        logger.info('📋 开始生成知识图谱验证报告...')

        # 执行所有验证
        self.verification_results['sqlite'] = self.verify_sqlite_knowledge_graph()
        self.verification_results['neo4j'] = self.verify_neo4j_knowledge_graph()
        self.verification_results['functionality'] = self.test_basic_functionality()

        # 生成总结
        sqlite_status = self.verification_results['sqlite']['status']
        neo4j_status = self.verification_results['neo4j']['status']
        functionality_score = self.verification_results['functionality']['functionality_score']

        # 计算总体健康度
        health_score = 0
        if sqlite_status == 'success':
            health_score += 40
        elif sqlite_status == 'partial':
            health_score += 20

        if neo4j_status == 'success':
            health_score += 40
        elif neo4j_status == 'empty':
            health_score += 20

        health_score += functionality_score * 0.2  # 功能测试占20%

        self.verification_results['summary'] = {
            'overall_health': round(health_score, 1),
            'sqlite_status': sqlite_status,
            'neo4j_status': neo4j_status,
            'functionality_score': functionality_score,
            'recommendations': self._generate_recommendations()
        }

        logger.info('✅ 知识图谱验证报告生成完成')
        return self.verification_results

    def _generate_recommendations(self) -> List[str]:
        """生成建议"""
        recommendations = []

        sqlite_status = self.verification_results['sqlite']['status']
        neo4j_status = self.verification_results['neo4j']['status']

        if sqlite_status == 'error':
            recommendations.append('SQLite知识图谱数据库存在问题，需要检查数据文件完整性')
        elif sqlite_status == 'partial':
            recommendations.append('SQLite知识图谱部分功能正常，建议检查缺失的表结构')

        if neo4j_status == 'error':
            recommendations.append('Neo4j连接失败，请检查服务状态和配置')
        elif neo4j_status == 'empty':
            recommendations.append('Neo4j数据库为空，建议导入知识图谱数据')

        functionality_score = self.verification_results['functionality']['functionality_score']
        if functionality_score < 80:
            recommendations.append('知识图谱功能测试不完整，建议优化查询性能')

        if sqlite_status == 'success' and neo4j_status == 'success':
            recommendations.append('两种知识图谱都运行正常，建议实施数据同步策略')

        return recommendations

def main():
    """主函数"""
    logger.info('🔍 Athena工作平台 - 知识图谱验证工具')
    logger.info(str('='*60))

    verifier = KnowledgeGraphVerifier()

    # 生成完整验证报告
    report = verifier.generate_verification_report()

    # 显示结果摘要
    logger.info("\n📊 验证结果摘要:")
    logger.info(f"  SQLite知识图谱: {report['sqlite']['status']}")
    logger.info(f"  Neo4j知识图谱: {report['neo4j']['status']}")
    logger.info(f"  功能测试评分: {report['functionality']['functionality_score']:.1f}%")
    logger.info(f"  总体健康度: {report['summary']['overall_health']:.1f}%")

    # SQLite详情
    sqlite_info = report['sqlite']
    logger.info(f"\n🗄️ SQLite知识图谱详情:")
    logger.info(f"  状态: {sqlite_info['status']}")
    logger.info(f"  文件路径: {sqlite_info['database_path']}")
    if sqlite_info.get('statistics'):
        stats = sqlite_info['statistics']
        logger.info(f"  实体数量: {stats.get('entity_count', 0):,}")
        logger.info(f"  关系数量: {stats.get('relation_count', 0):,}")
        logger.info(f"  文件大小: {stats.get('file_size_mb', 0)} MB")

    # Neo4j详情
    neo4j_info = report['neo4j']
    logger.info(f"\n🌐 Neo4j知识图谱详情:")
    logger.info(f"  状态: {neo4j_info['status']}")
    logger.info(f"  连接状态: {neo4j_info.get('connection', {}).get('status', 'unknown')}")
    if neo4j_info.get('statistics'):
        stats = neo4j_info['statistics']
        logger.info(f"  节点数量: {stats.get('node_count', 0)}")
        logger.info(f"  关系数量: {stats.get('relation_count', 0)}")

    # 建议
    recommendations = report['summary']['recommendations']
    if recommendations:
        logger.info(f"\n💡 建议:")
        for i, rec in enumerate(recommendations, 1):
            logger.info(f"  {i}. {rec}")

    # 保存详细报告
    report_path = os.path.join(project_root, '.runtime', 'knowledge_graph_verification_report.json')
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    logger.info(f"\n📄 详细报告已保存到: {report_path}")

    return report

if __name__ == '__main__':
    main()