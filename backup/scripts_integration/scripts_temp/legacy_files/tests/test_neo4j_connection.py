#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Neo4j知识图谱连接测试
Neo4j Knowledge Graph Connection Test
"""

import logging

from neo4j import GraphDatabase

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Neo4j连接配置
NEO4J_CONFIG = {
    'uri': 'bolt://localhost:7687',
    'auth': ('neo4j', 'password')  # 默认密码
}

def test_neo4j_connection():
    """测试Neo4j连接"""
    logger.info('🔍 测试Neo4j连接...')

    try:
        # 创建驱动
        driver = GraphDatabase.driver(**NEO4J_CONFIG)

        # 验证连接
        with driver.session() as session:
            # 执行简单查询
            result = session.run("RETURN 'Hello Neo4j!' as message")
            message = result.single()['message']
            logger.info(f"✅ 连接成功: {message}")

            # 检查数据库信息
            result = session.run('CALL db.info()')
            db_info = result.data()
            logger.info(f"📊 数据库信息: {db_info}")

            # 检查节点数量
            result = session.run('MATCH (n) RETURN count(n) as node_count')
            node_count = result.single()['node_count']
            logger.info(f"📈 节点总数: {node_count:,}")

            # 检查关系数量
            result = session.run('MATCH ()-[r]->() RETURN count(r) as rel_count')
            rel_count = result.single()['rel_count']
            logger.info(f"🔗 关系总数: {rel_count:,}")

            # 检查标签
            result = session.run('CALL db.labels()')
            labels = [record['label'] for record in result]
            logger.info(f"🏷️ 数据库标签: {labels}")

            # 检查关系类型
            result = session.run('CALL db.relationshipTypes()')
            rel_types = [record['relationshipType'] for record in result]
            logger.info(f"📌 关系类型: {rel_types}")

        driver.close()
        return True

    except Exception as e:
        logger.error(f"❌ 连接失败: {str(e)}")
        return False

def create_sample_data():
    """创建示例数据"""
    logger.info('📝 创建示例知识图谱数据...')

    try:
        driver = GraphDatabase.driver(**NEO4J_CONFIG)

        with driver.session() as session:
            # 清除现有数据（可选）
            session.run('MATCH (n) DETACH DELETE n')
            logger.info('🧹 清除现有数据')

            # 创建专利节点
            patents = [
                {
                    'id': 'CN202310123456',
                    'name': '基于深度学习的图像识别方法',
                    'field': '人工智能',
                    'date': '2023-10-15'
                },
                {
                    'id': 'CN202309876543',
                    'name': '区块链数据存储系统',
                    'field': '区块链',
                    'date': '2023-09-20'
                },
                {
                    'id': 'CN202308765432',
                    'name': '量子通信加密方法',
                    'field': '量子技术',
                    'date': '2023-08-25'
                }
            ]

            for patent in patents:
                session.run(
                    """
                    CREATE (p:Patent {
                        id: $id,
                        name: $name,
                        field: $field,
                        date: $date,
                        created_at: datetime()
                    })
                    """,
                    **patent
                )

            logger.info(f"📄 创建了 {len(patents)} 个专利节点")

            # 创建公司节点
            companies = [
                {'name': '北京智能科技有限公司', 'type': '科技公司'},
                {'name': '深圳区块链研究院', 'type': '研究机构'},
                {'name': '上海量子实验室', 'type': '研究机构'}
            ]

            for company in companies:
                session.run(
                    """
                    CREATE (c:Company {
                        name: $name,
                        type: $type,
                        created_at: datetime()
                    })
                    """,
                    **company
                )

            logger.info(f"🏢 创建了 {len(companies)} 个公司节点")

            # 创建发明人节点
            inventors = [
                {'name': '张明', 'specialty': '深度学习'},
                {'name': '李华', 'specialty': '区块链'},
                {'name': '王强', 'specialty': '量子通信'},
                {'name': '刘晓明', 'specialty': '图像处理'}
            ]

            for inventor in inventors:
                session.run(
                    """
                    CREATE (i:Inventor {
                        name: $name,
                        specialty: $specialty,
                        created_at: datetime()
                    })
                    """,
                    **inventor
                )

            logger.info(f"👨‍💼 创建了 {len(inventors)} 个发明人节点")

            # 创建关系
            # 专利-公司关系（申请）
            session.run("""
                MATCH (p:Patent {id: 'CN202310123456'})
                MATCH (c:Company {name: '北京智能科技有限公司'})
                CREATE (p)-[:APPLIED_TO]->(c)
            """)

            session.run("""
                MATCH (p:Patent {id: 'CN202309876543'})
                MATCH (c:Company {name: '深圳区块链研究院'})
                CREATE (p)-[:APPLIED_TO]->(c)
            """)

            session.run("""
                MATCH (p:Patent {id: 'CN202308765432'})
                MATCH (c:Company {name: '上海量子实验室'})
                CREATE (p)-[:APPLIED_TO]->(c)
            """)

            # 专利-发明人关系（发明）
            session.run("""
                MATCH (p:Patent {id: 'CN202310123456'})
                MATCH (i:Inventor {name: '张明'})
                CREATE (i)-[:INVENTED]->(p)
            """)

            session.run("""
                MATCH (p:Patent {id: 'CN202310123456'})
                MATCH (i:Inventor {name: '刘晓明'})
                CREATE (i)-[:INVENTED]->(p)
            """)

            session.run("""
                MATCH (p:Patent {id: 'CN202309876543'})
                MATCH (i:Inventor {name: '李华'})
                CREATE (i)-[:INVENTED]->(p)
            """)

            session.run("""
                MATCH (p:Patent {id: 'CN202308765432'})
                MATCH (i:Inventor {name: '王强'})
                CREATE (i)-[:INVENTED]->(p)
            """)

            logger.info('🔗 创建了节点间的关系')

        driver.close()
        logger.info('✅ 示例数据创建完成')
        return True

    except Exception as e:
        logger.error(f"❌ 创建数据失败: {str(e)}")
        return False

def query_sample_data():
    """查询示例数据"""
    logger.info('🔍 查询知识图谱数据...')

    try:
        driver = GraphDatabase.driver(**NEO4J_CONFIG)

        with driver.session() as session:
            # 查询所有专利
            result = session.run("""
                MATCH (p:Patent)
                RETURN p.name as patent_name, p.field as field, p.date as date
                ORDER BY p.date DESC
            """)

            logger.info("\n📄 专利列表:")
            for record in result:
                logger.info(f"  - {record['patent_name']} ({record['field']}) - {record['date']}")

            # 查询专利关系网络
            result = session.run("""
                MATCH (p:Patent)<-[:INVENTED]-(i:Inventor)-[:APPLIED_TO]->(c:Company)
                RETURN p.name as patent, i.name as inventor, c.name as company
            """)

            logger.info("\n🔗 专利关系网络:")
            for record in result:
                logger.info(f"  - {record['inventor']} 发明了 '{record['patent']}'，申请于 {record['company']}")

            # 查询路径
            result = session.run("""
                MATCH path = (i:Inventor)-[:INVENTED]->(p:Patent)-[:APPLIED_TO]->(c:Company)
                RETURN path
                LIMIT 3
            """)

            logger.info("\n🛤️ 发明人-专利-公司路径:")
            for record in result:
                path = record['path']
                nodes = [node['name'] for node in path.nodes]
                logger.info(f"  路径: {' -> '.join(nodes)}")

        driver.close()
        return True

    except Exception as e:
        logger.error(f"❌ 查询失败: {str(e)}")
        return False

def main():
    """主函数"""
    logger.info('🚀 Neo4j知识图谱测试开始')

    # 测试连接
    if not test_neo4j_connection():
        logger.error('无法连接到Neo4j，请检查服务是否启动')
        return

    # 创建示例数据
    create_sample_data()

    # 查询数据
    query_sample_data()

    logger.info('✅ 测试完成')

if __name__ == '__main__':
    main()