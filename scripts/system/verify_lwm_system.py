#!/usr/bin/env python3
"""
法律世界模型综合验证脚本
验证：向量搜索、图谱查询、整体功能
"""

import logging
import time

import psycopg2
from neo4j import GraphDatabase

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LegalWorldModelVerifier:
    """法律世界模型验证器"""

    def __init__(self):
        """初始化连接"""
        # PostgreSQL连接配置
        self.pg_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'legal_world_model',
            'user': 'postgres',
            'password': 'nxLVXyZ3e87L0kE8Xqx3AB9NK1z74pwOdjugqpc7hc'
        }

        # Neo4j连接配置
        self.neo4j_uri = 'bolt://localhost:7687'
        self.neo4j_user = 'neo4j'
        self.neo4j_password = 'athena_neo4j_2024'

        self.pg_conn = None
        self.neo4j_driver = None

        # 验证结果
        self.results = {
            'vector_search': {},
            'graph_query': {},
            'overall': {}
        }

    def connect(self):
        """建立数据库连接"""
        try:
            # 连接PostgreSQL
            logger.info("🔗 连接PostgreSQL...")
            self.pg_conn = psycopg2.connect(**self.pg_config)
            logger.info("✅ PostgreSQL连接成功")

            # 连接Neo4j
            logger.info("🔗 连接Neo4j...")
            self.neo4j_driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )
            with self.neo4j_driver.session() as session:
                session.run("RETURN 1")
            logger.info("✅ Neo4j连接成功")

        except Exception as e:
            logger.error(f"❌ 连接失败: {e}")
            raise

    def close(self):
        """关闭连接"""
        if self.pg_conn:
            self.pg_conn.close()
        if self.neo4j_driver:
            self.neo4j_driver.close()

    def test_vector_search(self):
        """测试向量搜索性能"""
        logger.info("=" * 60)
        logger.info("🔍 测试1：向量搜索性能")
        logger.info("=" * 60)

        tests = [
            {
                'name': '法律条款向量搜索',
                'table': 'legal_articles_v2_embeddings',
                'description': '搜索相似法律条款'
            },
            {
                'name': '专利无效向量搜索',
                'table': 'patent_invalid_embeddings',
                'description': '搜索相似专利无效决定'
            },
            {
                'name': '判决向量搜索',
                'table': 'judgment_embeddings',
                'description': '搜索相似判决'
            }
        ]

        for test in tests:
            logger.info(f"\n📊 测试: {test['name']}")
            logger.info(f"   描述: {test['description']}")

            try:
                # 获取查询向量
                query = f"""
                SELECT vector FROM {test['table']}
                ORDER BY random()
                LIMIT 1
                """

                cursor = self.pg_conn.cursor()
                cursor.execute(query)
                result = cursor.fetchone()
                if not result:
                    logger.warning(f"   ⚠️  {test['name']} - 无数据")
                    continue

                query_vector = result[0]

                # 测试查询性能
                test_query = f"""
                EXPLAIN ANALYZE
                SELECT
                    article_id,
                    vector <=> %s::vector as distance
                FROM {test['table']}
                ORDER BY vector <=> %s::vector
                LIMIT 10
                """

                cursor.execute(test_query, (query_vector, query_vector))
                explain_result = cursor.fetchall()

                # 提取执行时间
                for line in explain_result:
                    line_str = str(line[0])
                    if 'Execution Time' in line_str:
                        exec_time = float(line_str.split(':')[1].strip().split()[0])
                        self.results['vector_search'][test['name'] = {
                            'status': 'success',
                            'time_ms': exec_time
                        }
                        logger.info(f"   ✅ 查询时间: {exec_time:.2f} ms")

                        # 评估性能
                        if exec_time < 20:
                            logger.info("   🟢 性能优秀")
                        elif exec_time < 50:
                            logger.info("   🟡 性能良好")
                        else:
                            logger.info("   🔴 需要优化")
                        break

            except Exception as e:
                logger.error(f"   ❌ 测试失败: {e}")
                self.results['vector_search'][test['name'] = {
                    'status': 'failed',
                    'error': str(e)
                }

    def test_graph_query(self):
        """测试图谱查询"""
        logger.info("\n" + "=" * 60)
        logger.info("🔍 测试2：Neo4j图谱查询")
        logger.info("=" * 60)

        queries = [
            {
                'name': '节点总数统计',
                'cypher': 'MATCH (n) RETURN count(n) as count',
                'description': '统计所有节点'
            },
            {
                'name': 'Case节点查询',
                'cypher': 'MATCH (c:Case) RETURN count(c) as count',
                'description': '统计Case节点'
            },
            {
                'name': 'Entity节点查询',
                'cypher': 'MATCH (e:Entity) RETURN count(e) as count',
                'description': '统计Entity节点'
            },
            {
                'name': 'Case节点示例',
                'cypher': 'MATCH (c:Case) RETURN c.title, c.case_cause LIMIT 3',
                'description': '查看Case节点示例'
            },
            {
                'name': 'Entity节点示例',
                'cypher': 'MATCH (e:Entity) RETURN e.text, e.type LIMIT 3',
                'description': '查看Entity节点示例'
            }
        ]

        with self.neo4j_driver.session() as session:
            for query in queries:
                logger.info(f"\n📊 测试: {query['name']}")
                logger.info(f"   Cypher: {query['cypher']}")
                logger.info(f"   描述: {query['description']}")

                try:
                    start_time = time.time()
                    result = session.run(query['cypher'])
                    records = list(result)
                    exec_time = (time.time() - start_time) * 1000

                    self.results['graph_query'][query['name'] = {
                        'status': 'success',
                        'time_ms': exec_time,
                        'record_count': len(records)
                    }

                    logger.info(f"   ✅ 查询时间: {exec_time:.2f} ms")
                    logger.info(f"   📄 返回记录: {len(records)}条")

                    # 显示前几条记录
                    for i, record in enumerate(records[:3]):
                        logger.info(f"   记录{i+1}: {dict(record)}")

                except Exception as e:
                    logger.error(f"   ❌ 测试失败: {e}")
                    self.results['graph_query'][query['name'] = {
                        'status': 'failed',
                        'error': str(e)
                    }

    def test_overall_functionality(self):
        """测试整体功能"""
        logger.info("\n" + "=" * 60)
        logger.info("🔍 测试3：整体功能验证")
        logger.info("=" * 60)

        tests = [
            {
                'name': 'PostgreSQL数据统计',
                'function': self._check_postgres_stats
            },
            {
                'name': '向量索引验证',
                'function': self._check_vector_indexes
            },
            {
                'name': 'Neo4j图谱统计',
                'function': self._check_neo4j_stats
            },
            {
                'name': '综合查询测试',
                'function': self._test_integrated_query
            }
        ]

        for test in tests:
            logger.info(f"\n📊 测试: {test['name']}")
            try:
                result = test['function']()
                self.results['overall'][test['name'] = {
                    'status': 'success',
                    'data': result
                }
                logger.info(f"   ✅ {test['name']} - 成功")
            except Exception as e:
                logger.error(f"   ❌ {test['name']} - 失败: {e}")
                self.results['overall'][test['name'] = {
                    'status': 'failed',
                    'error': str(e)
                }

    def _check_postgres_stats(self):
        """检查PostgreSQL统计"""
        cursor = self.pg_conn.cursor()

        # 获取表统计
        cursor.execute("""
            SELECT
                tablename,
                (SELECT count(*) FROM information_schema.tables t2 WHERE t2.tablename = t1.tablename) as row_count
            FROM pg_tables t1
            WHERE schemaname = 'public'
            AND tablename LIKE '%embedding%'
            ORDER BY tablename
        """)

        stats = {}
        for row in cursor.fetchall():
            table_name, row_count = row
            stats[table_name] = row_count
            logger.info(f"   {table_name}: {row_count}条")

        return stats

    def _check_vector_indexes(self):
        """检查向量索引"""
        cursor = self.pg_conn.cursor()

        cursor.execute("""
            SELECT
                tablename,
                indexname,
                indexdef
            FROM pg_indexes
            WHERE indexdef LIKE '%ivfflat%'
            ORDER BY tablename
        """)

        indexes = {}
        for row in cursor.fetchall():
            table_name, index_name, index_def = row
            indexes[table_name] = {
                'name': index_name,
                'definition': index_def
            }
            logger.info(f"   {table_name}: {index_name}")

        return indexes

    def _check_neo4j_stats(self):
        """检查Neo4j统计"""
        with self.neo4j_driver.session() as session:
            # 节点统计
            node_result = session.run("MATCH (n) RETURN labels(n) as labels, count(*) as count")
            node_stats = {}
            total_nodes = 0
            for record in node_result:
                labels = record['labels']
                count = record['count']
                label = labels[0] if labels else 'Unknown'
                node_stats[label] = count
                total_nodes += count
                logger.info(f"   {label}: {count}个")

            logger.info(f"   总计: {total_nodes}个节点")

            # 关系统计
            rel_result = session.run("MATCH ()-[r]->() RETURN type(r) as type, count(*) as count")
            rel_stats = {}
            total_rels = 0
            for record in rel_result:
                rel_type = record['type']
                count = record['count']
                rel_stats[rel_type] = count
                total_rels += count

            logger.info(f"   总计: {total_rels}条关系")

            return {'nodes': node_stats, 'relationships': rel_stats}

    def _test_integrated_query(self):
        """测试综合查询"""
        # 从PostgreSQL查询一个Case
        cursor = self.pg_conn.cursor()
        cursor.execute("""
            SELECT judgment_id, title
            FROM patent_judgments
            LIMIT 1
        """)
        case_data = cursor.fetchone()

        if not case_data:
            logger.warning("   无Case数据")
            return {}

        case_id, case_title = case_data
        logger.info(f"   Case ID: {case_id}")
        logger.info(f"   标题: {case_title[:100]}...")

        # 在Neo4j中查找对应节点
        with self.neo4j_driver.session() as session:
            result = session.run(
                "MATCH (c:Case {id: $case_id}) RETURN c",
                case_id=str(case_id)
            )
            nodes = list(result)

            logger.info(f"   Neo4j中找到{len(nodes)}个匹配节点")

            return {
                'postgres_case': case_id,
                'neo4j_matches': len(nodes)
            }

    def print_summary(self):
        """打印验证摘要"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 验证摘要")
        logger.info("=" * 60)

        # 向量搜索摘要
        logger.info("\n🔍 向量搜索性能:")
        for name, result in self.results['vector_search'].items():
            if result['status'] == 'success':
                logger.info(f"   ✅ {name}: {result['time_ms']:.2f} ms")
            else:
                logger.info(f"   ❌ {name}: 失败")

        # 图谱查询摘要
        logger.info("\n🔍 图谱查询:")
        for name, result in self.results['graph_query'].items():
            if result['status'] == 'success':
                logger.info(f"   ✅ {name}: {result['time_ms']:.2f} ms ({result['record_count']}条记录)")
            else:
                logger.info(f"   ❌ {name}: 失败")

        # 整体功能摘要
        logger.info("\n🔍 整体功能:")
        for name, result in self.results['overall'].items():
            if result['status'] == 'success':
                logger.info(f"   ✅ {name}")
            else:
                logger.info(f"   ❌ {name}")

        # 总体评估
        logger.info("\n" + "=" * 60)
        logger.info("📈 总体评估")

        vector_success = sum(1 for r in self.results['vector_search'].values() if r['status'] == 'success')
        vector_total = len(self.results['vector_search'])

        graph_success = sum(1 for r in self.results['graph_query'].values() if r['status'] == 'success')
        graph_total = len(self.results['graph_query'])

        overall_success = sum(1 for r in self.results['overall'].values() if r['status'] == 'success')
        overall_total = len(self.results['overall'])

        logger.info(f"   向量搜索: {vector_success}/{vector_total} 通过")
        logger.info(f"   图谱查询: {graph_success}/{graph_total} 通过")
        logger.info(f"   整体功能: {overall_success}/{overall_total} 通过")

        total_success = vector_success + graph_success + overall_success
        total_tests = vector_total + graph_total + overall_total
        success_rate = (total_success / total_tests * 100) if total_tests > 0 else 0

        logger.info(f"   总通过率: {success_rate:.1f}%")

        if success_rate >= 80:
            logger.info("   🟢 系统状态: 优秀")
        elif success_rate >= 60:
            logger.info("   🟡 系统状态: 良好")
        else:
            logger.info("   🔴 系统状态: 需要改进")

        logger.info("=" * 60)

    def run_verification(self):
        """执行完整验证"""
        try:
            # 连接数据库
            self.connect()

            # 执行测试
            self.test_vector_search()
            self.test_graph_query()
            self.test_overall_functionality()

            # 打印摘要
            self.print_summary()

        except Exception as e:
            logger.error(f"❌ 验证失败: {e}")
            raise
        finally:
            self.close()


def main():
    """主函数"""
    verifier = LegalWorldModelVerifier()
    verifier.run_verification()


if __name__ == "__main__":
    main()
