#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Athena知识图谱系统状态检查
Knowledge Graph System Status Check

检查知识图谱各组件的运行状态和数据情况

作者: Athena AI系统
创建时间: 2025-12-08
版本: 1.0.0
"""

import asyncio
import logging
import os
import sqlite3
import sys
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class KnowledgeGraphChecker:
    """知识图谱检查器"""

    def __init__(self):
        self.check_results = []

    async def run_all_checks(self):
        """运行所有检查"""
        logger.info('🔍 Athena知识图谱系统状态检查')
        logger.info(str('=' * 60))

        # 检查1: SQLite知识图谱数据库
        logger.info("\n🗄️ 检查1: SQLite知识图谱数据库")
        await self.check_sqlite_knowledge_graph()

        # 检查2: Neo4j图数据库
        logger.info("\n🌐 检查2: Neo4j图数据库")
        await self.check_neo4j_database()

        # 检查3: 知识图谱构建工具
        logger.info("\n🔧 检查3: 知识图谱构建工具")
        await self.check_graph_builders()

        # 检查4: 知识图谱API接口
        logger.info("\n📡 检查4: 知识图谱API接口")
        await self.check_graph_apis()

        # 生成检查报告
        self.generate_report()

    async def check_sqlite_knowledge_graph(self):
        """检查SQLite知识图谱数据库"""
        try:
            # 检查SQLite数据库文件
            db_files = [
                '/Users/xujian/Athena工作平台/data/athena_knowledge_graph.db',
                '/Users/xujian/Athena工作平台/data/knowledge_graph.db',
                '/Users/xujian/Athena工作平台/patent_cache.db'
            ]

            for db_file in db_files:
                if os.path.exists(db_file):
                    try:
                        conn = sqlite3.connect(db_file)
                        cursor = conn.cursor()

                        # 获取表列表
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                        tables = cursor.fetchall()

                        # 统计数据
                        table_stats = {}
                        for table_name, in tables:
        # TODO: 检查SQL注入风险 - cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                            count = cursor.fetchone()[0]
                            table_stats[table_name] = count

                        self.check_results.append({
                            'check': 'sqlite_database',
                            'database': db_file,
                            'success': True,
                            'tables': len(tables),
                            'table_stats': table_stats
                        })

                        logger.info(f"  ✅ {db_file}")
                        logger.info(f"    表数量: {len(tables)}")
                        if table_stats:
                            logger.info('    数据统计:')
                            for table, count in list(table_stats.items())[:3]:
                                logger.info(f"      - {table}: {count}条记录")

                        conn.close()

                    except Exception as e:
                        logger.info(f"  ⚠️ {db_file} - 连接失败: {str(e)}")
                        self.check_results.append({
                            'check': 'sqlite_database',
                            'database': db_file,
                            'success': False,
                            'error': str(e)
                        })
                else:
                    logger.info(f"  ❌ {db_file} - 文件不存在")

        except Exception as e:
            logger.info(f"  ❌ SQLite检查失败: {str(e)}")
            self.check_results.append({
                'check': 'sqlite_database',
                'success': False,
                'error': str(e)
            })

    async def check_neo4j_database(self):
        """检查Neo4j图数据库"""
        try:
            # 检查Neo4j服务状态
            import requests

            # 尝试连接Neo4j
            try:
                response = requests.get('http://localhost:7474/db/data/', timeout=5)
                if response.status_code == 200:
                    logger.info('  ✅ Neo4j服务连接正常')

                    # 尝试获取节点统计
                    try:
                        # 使用简单的Cypher查询
                        query_data = {
                            'query': 'MATCH (n) RETURN count(n) as node_count, labels(n) as labels LIMIT 1'
                        }

                        cypher_response = requests.post(
                            'http://localhost:7474/db/data/cypher',
                            json=query_data,
                            timeout=5
                        )

                        if cypher_response.status_code == 200:
                            data = cypher_response.json()
                            if data.get('results'):
                                result = data['results'][0]
                                if result.get('data'):
                                    node_count = result['data'][0]['row'][0]
                                    logger.info(f"    节点数量: {node_count}")

                                    self.check_results.append({
                                        'check': 'neo4j_database',
                                        'success': True,
                                        'node_count': node_count,
                                        'connection': '正常'
                                    })
                                else:
                                    logger.info('    节点数量: 0 (空数据库)')
                                    self.check_results.append({
                                        'check': 'neo4j_database',
                                        'success': True,
                                        'node_count': 0,
                                        'connection': '正常，但数据库为空'
                                    })
                            else:
                                logger.info('    ⚠️ 无法获取节点统计')
                                self.check_results.append({
                                    'check': 'neo4j_database',
                                    'success': True,
                                    'node_count': '未知',
                                    'connection': '正常'
                                })
                        else:
                            logger.info(f"    ⚠️ Cypher查询失败: {cypher_response.status_code}")
                            self.check_results.append({
                                'check': 'neo4j_database',
                                'success': True,
                                'node_count': '未知',
                                'connection': '正常，但查询失败'
                            })

                    except Exception as e:
                        logger.info(f"    ⚠️ 查询执行失败: {str(e)}")
                        self.check_results.append({
                            'check': 'neo4j_database',
                            'success': True,
                            'node_count': '未知',
                            'connection': '正常',
                            'query_error': str(e)
                        })
                else:
                    logger.info(f"  ❌ Neo4j连接失败: {response.status_code}")
                    self.check_results.append({
                        'check': 'neo4j_database',
                        'success': False,
                        'error': f"HTTP {response.status_code}"
                    })

            except Exception as e:
                logger.info(f"  ❌ Neo4j连接异常: {str(e)}")
                self.check_results.append({
                    'check': 'neo4j_database',
                    'success': False,
                    'error': str(e)
                })

        except Exception as e:
            logger.info(f"  ❌ Neo4j检查失败: {str(e)}")
            self.check_results.append({
                'check': 'neo4j_database',
                'success': False,
                'error': str(e)
            })

    async def check_graph_builders(self):
        """检查知识图谱构建工具"""
        try:
            # 检查主要的图谱构建模块
            builders_to_check = [
                ('专利知识图谱构建器', 'domains.patent.services.patent_knowledge_graph_builder'),
                ('专利分析图谱构建器', 'core.knowledge.patent_analysis.knowledge_graph'),
                ('法律图谱导入器', 'domains.legal.tools.neo4j_law_importer'),
                ('统一知识管理器', 'domains.legal.apis.unified_knowledge_manager'),
            ]

            successful_imports = 0

            for name, module_path in builders_to_check:
                try:
                    # 尝试导入模块
                    module_parts = module_path.split('.')
                    module = __import__('.'.join(module_parts[:-1]), fromlist=[module_parts[-1])
                    class_ = getattr(module, module_parts[-1], None)

                    if class_:
                        logger.info(f"  ✅ {name} - 导入成功")
                        successful_imports += 1
                    else:
                        logger.info(f"  ⚠️ {name} - 模块存在但无主类")

                except ImportError as e:
                    logger.info(f"  ❌ {name} - 导入失败: {str(e)}")
                except Exception as e:
                    logger.info(f"  ❌ {name} - 其他错误: {str(e)}")

            self.check_results.append({
                'check': 'graph_builders',
                'success': successful_imports > 0,
                'successful_imports': successful_imports,
                'total_builders': len(builders_to_check)
            })

            logger.info(f"  📊 成功导入: {successful_imports}/{len(builders_to_check)}")

        except Exception as e:
            logger.info(f"  ❌ 图谱构建工具检查失败: {str(e)}")
            self.check_results.append({
                'check': 'graph_builders',
                'success': False,
                'error': str(e)
            })

    async def check_graph_apis(self):
        """检查知识图谱API接口"""
        try:
            # 检查API服务是否运行
            api_endpoints = [
                ('知识图谱API', 'http://localhost:8080'),
                ('统一知识API', 'http://localhost:8081'),
            ]

            running_apis = 0

            for name, endpoint in api_endpoints:
                try:
                    response = requests.get(f"{endpoint}/health", timeout=3)
                    if response.status_code == 200:
                        logger.info(f"  ✅ {name} - 运行正常")
                        running_apis += 1
                    else:
                        logger.info(f"  ⚠️ {name} - 响应异常: {response.status_code}")
                except requests.exceptions.ConnectionError:
                    logger.info(f"  ❌ {name} - 连接失败")
                except Exception as e:
                    logger.info(f"  ❌ {name} - 其他错误: {str(e)}")

            # 检查FastAPI配置
            try:
                from domains.legal.apis.knowledge_graph_api import app

# 导入标准化数据库工具
from shared.database.db_utils import DatabaseManager, build_safe_query
                logger.info('  ✅ FastAPI知识图谱应用 - 配置正常')
                running_apis += 1
            except Exception as e:
                logger.info(f"  ❌ FastAPI知识图谱应用 - 配置失败: {str(e)}")

            self.check_results.append({
                'check': 'graph_apis',
                'success': running_apis > 0,
                'running_apis': running_apis,
                'total_apis': len(api_endpoints) + 1
            })

            logger.info(f"  📊 运行中的API: {running_apis}/{len(api_endpoints) + 1}")

        except Exception as e:
            logger.info(f"  ❌ API接口检查失败: {str(e)}")
            self.check_results.append({
                'check': 'graph_apis',
                'success': False,
                'error': str(e)
            })

    def generate_report(self):
        """生成检查报告"""
        logger.info(str("\n" + '=' * 60))
        logger.info('📈 知识图谱系统状态报告')
        logger.info(str('=' * 60))

        total_checks = len(self.check_results)
        successful_checks = sum(1 for r in self.check_results if r.get('success', False))
        failed_checks = total_checks - successful_checks

        logger.info(f"总检查项目: {total_checks}")
        logger.info(f"成功: {successful_checks} ({successful_checks/total_checks:.1%})")
        logger.info(f"失败: {failed_checks} ({failed_checks/total_checks:.1%})")

        logger.info("\n📊 详细结果:")
        for result in self.check_results:
            check_type = result.get('check', 'unknown')
            status = '✅' if result.get('success', False) else '❌'
            details = []

            if check_type == 'sqlite_database':
                db_name = os.path.basename(result.get('database', 'unknown'))
                details.append(f"数据库: {db_name}")
                if result.get('tables'):
                    details.append(f"表数: {result['tables']}")
            elif check_type == 'neo4j_database':
                details.append(f"连接: {result.get('connection', '未知')}")
                if result.get('node_count'):
                    details.append(f"节点: {result['node_count']}")
            elif check_type == 'graph_builders':
                successful = result.get('successful_imports', 0)
                total = result.get('total_builders', 0)
                details.append(f"导入: {successful}/{total}")
            elif check_type == 'graph_apis':
                running = result.get('running_apis', 0)
                total = result.get('total_apis', 0)
                details.append(f"运行: {running}/{total}")

            detail_str = ', '.join(details)
            logger.info(f"  {status} {check_type}: {detail_str}")

        # 系统评估
        health_score = successful_checks / total_checks
        logger.info(f"\n🎯 知识图谱系统健康度: {health_score:.1%}")

        if health_score >= 0.75:
            logger.info('🟢 优秀 - 知识图谱系统运行良好')
        elif health_score >= 0.5:
            logger.info('🟡 良好 - 知识图谱系统基本可用')
        else:
            logger.info('🔴 需要改进 - 知识图谱系统存在较多问题')

        # 改进建议
        logger.info("\n💡 改进建议:")
        if health_score < 1.0:
            logger.info('  1. 优先修复失败的检查项目')
            logger.info('  2. 确保数据库服务正常运行')
            logger.info('  3. 完善知识图谱数据导入流程')

        if successful_checks >= 2:
            logger.info('  4. 知识图谱基础功能可用，可以开始业务集成')
            logger.info('  5. 考虑添加更多的知识图谱可视化功能')

async def main():
    """主函数"""
    checker = KnowledgeGraphChecker()
    await checker.run_all_checks()

if __name__ == '__main__':
    asyncio.run(main())