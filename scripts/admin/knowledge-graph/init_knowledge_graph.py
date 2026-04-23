#!/usr/bin/env python3
"""
Athena知识图谱初始化脚本
Knowledge Graph Initialization Script

创建初始的知识图谱数据和结构

作者: Athena AI系统
创建时间: 2025-12-08
版本: 1.0.0
"""

import asyncio
import logging
import os
import sys

logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logger.info('⚠️ Neo4j驱动未安装，请运行: pip install neo4j')

class KnowledgeGraphInitializer:
    """知识图谱初始化器"""

    def __init__(self):
        self.driver = None
        if NEO4J_AVAILABLE:
            try:
                self.driver = GraphDatabase.driver(
                    'bolt://localhost:7687',
                    auth=('neo4j', 'password')  # 默认密码
                )
                logger.info('✅ Neo4j连接成功')
            except Exception as e:
                logger.info(f"❌ Neo4j连接失败: {str(e)}")
                logger.info('💡 请检查Neo4j是否运行，密码是否正确')
                self.driver = None

    async def initialize_patent_knowledge_graph(self):
        """初始化专利知识图谱"""
        logger.info("\n🗺️ 初始化专利知识图谱")

        if not self.driver:
            logger.info('❌ Neo4j驱动未初始化')
            return False

        try:
            with self.driver.session() as session:
                # 创建约束
                logger.info('  📝 创建节点约束...')
                constraints = [
                    'CREATE CONSTRAINT IF NOT EXISTS FOR (p:Patent) REQUIRE p.id IS UNIQUE',
                    'CREATE CONSTRAINT IF NOT EXISTS FOR (t:Technology) REQUIRE t.name IS UNIQUE',
                    'CREATE CONSTRAINT IF NOT EXISTS FOR (c:Company) REQUIRE c.name IS UNIQUE',
                    'CREATE CONSTRAINT IF NOT EXISTS FOR (i:Inventor) REQUIRE i.name IS UNIQUE',
                    'CREATE CONSTRAINT IF NOT EXISTS FOR (k:Keyword) REQUIRE k.name IS UNIQUE'
                ]

                for constraint in constraints:
                    try:
                        session.run(constraint)
                        logger.info(f"    ✅ {constraint.split('FOR')[1].split('REQUIRE')[0].strip()}")
                    except Exception as e:
                        logger.info(f"    ⚠️ 约束已存在或创建失败: {str(e)}")

                # 创建示例专利数据
                logger.info('  📄 创建示例专利数据...')
                patent_data = [
                    {
                        'id': 'CN202310000001A',
                        'title': '基于深度学习的图像识别方法',
                        'abstract': '本发明涉及一种基于深度学习的图像识别方法...',
                        'application_date': '2023-01-01',
                        'inventors': ['张三', '李四'],
                        'company': 'AI科技有限公司',
                        'technologies': ['深度学习', '图像识别', '卷积神经网络'],
                        'keywords': ['人工智能', '机器学习', '计算机视觉']
                    },
                    {
                        'id': 'CN202310000002A',
                        'title': '智能语音识别系统及其实现方法',
                        'abstract': '本发明提供了一种智能语音识别系统...',
                        'application_date': '2023-02-01',
                        'inventors': ['王五', '赵六'],
                        'company': '语音技术有限公司',
                        'technologies': ['语音识别', '自然语言处理', '深度学习'],
                        'keywords': ['语音处理', 'NLP', 'AI算法']
                    },
                    {
                        'id': 'CN202310000003A',
                        'title': '基于区块链的数据安全存储方法',
                        'abstract': '本发明涉及一种基于区块链的数据安全存储技术...',
                        'application_date': '2023-03-01',
                        'inventors': ['钱七', '孙八'],
                        'company': '区块链科技公司',
                        'technologies': ['区块链', '数据加密', '分布式存储'],
                        'keywords': ['网络安全', '加密技术', '分布式']
                    }
                ]

                # 创建专利节点
                for patent in patent_data:
                    # 创建专利节点
                    session.run(
                        """
                        MERGE (p:Patent {id: $id})
                        SET p.title = $title,
                            p.abstract = $abstract,
                            p.application_date = $application_date,
                            p.created_at = datetime()
                        """,
                        **patent
                    )

                    # 创建公司节点和关系
                    session.run(
                        """
                        MERGE (c:Company {name: $company})
                        WITH c
                        MATCH (p:Patent {id: $id})
                        MERGE (p)-[:ASSIGNED_TO]->(c)
                        """,
                        company=patent['company'],
                        id=patent['id']
                    )

                    # 创建发明人节点和关系
                    for inventor in patent['inventors']:
                        session.run(
                            """
                            MERGE (i:Inventor {name: $name})
                            WITH i
                            MATCH (p:Patent {id: $id})
                            MERGE (i)-[:INVENTED]->(p)
                            """,
                            name=inventor,
                            id=patent['id']
                        )

                    # 创建技术节点和关系
                    for tech in patent['technologies']:
                        session.run(
                            """
                            MERGE (t:Technology {name: $name})
                            WITH t
                            MATCH (p:Patent {id: $id})
                            MERGE (p)-[:USES_TECHNOLOGY]->(t)
                            """,
                            name=tech,
                            id=patent['id']
                        )

                    # 创建关键词节点和关系
                    for keyword in patent['keywords']:
                        session.run(
                            """
                            MERGE (k:Keyword {name: $name})
                            WITH k
                            MATCH (p:Patent {id: $id})
                            MERGE (p)-[:HAS_KEYWORD]->(k)
                            """,
                            name=keyword,
                            id=patent['id']
                        )

                logger.info(f"    ✅ 创建了 {len(patent_data)} 个专利节点及相关关系")

                # 创建一些技术之间的关系
                logger.info('  🔗 创建技术关系...')
                tech_relations = [
                    ('深度学习', '机器学习', 'IS_TYPE_OF'),
                    ('卷积神经网络', '深度学习', 'IS_TYPE_OF'),
                    ('图像识别', '计算机视觉', 'RELATED_TO'),
                    ('语音识别', '自然语言处理', 'RELATED_TO'),
                    ('区块链', '数据加密', 'ENABLES'),
                    ('分布式存储', '区块链', 'ENABLES')
                ]

                for tech1, tech2, relation in tech_relations:
                    session.run(
                        """
                        MATCH (t1:Technology {name: $tech1}), (t2:Technology {name: $tech2})
                        MERGE (t1)-[r:{relation}]->(t2)
                        """,
                        tech1=tech1,
                        tech2=tech2,
                        relation=relation
                    )

                logger.info(f"    ✅ 创建了 {len(tech_relations)} 个技术关系")

                # 统计创建的节点数量
                result = session.run('MATCH (n) RETURN count(n) as count')
                node_count = result.single()['count']
                logger.info(f"  📊 总计创建 {node_count} 个节点")

                return True

        except Exception as e:
            logger.info(f"❌ 初始化失败: {str(e)}")
            return False

    async def initialize_legal_knowledge_graph(self):
        """初始化法律知识图谱"""
        logger.info("\n⚖️ 初始化法律知识图谱")

        if not self.driver:
            logger.info('❌ Neo4j驱动未初始化')
            return False

        try:
            with self.driver.session() as session:
                # 创建法律相关约束
                legal_constraints = [
                    'CREATE CONSTRAINT IF NOT EXISTS FOR (l:Law) REQUIRE l.id IS UNIQUE',
                    'CREATE CONSTRAINT IF NOT EXISTS FOR (c:Case) REQUIRE c.id IS UNIQUE',
                    'CREATE CONSTRAINT IF NOT EXISTS FOR (a:Article) REQUIRE a.number IS UNIQUE'
                ]

                logger.info('  📝 创建法律节点约束...')
                for constraint in legal_constraints:
                    try:
                        session.run(constraint)
                        logger.info(f"    ✅ {constraint.split('FOR')[1].split('REQUIRE')[0].strip()}")
                    except Exception:
                        logger.info("    ⚠️ 约束已存在或创建失败")

                # 创建示例法律数据
                legal_data = [
                    {
                        'id': 'LAW001',
                        'name': '中华人民共和国专利法',
                        'type': '法律',
                        'year': '2020',
                        'articles': [
                            {'number': '第26条', 'content': '说明书应当对发明作出清楚、完整的说明...'},
                            {'number': '第33条', 'content': '申请人可以对其专利申请文件进行修改...'}
                        ]
                    },
                    {
                        'id': 'CASE001',
                        'name': '某公司诉某专利侵权案',
                        'type': '案例',
                        'court': '最高人民法院',
                        'year': '2022',
                        'related_laws': ['中华人民共和国专利法']
                    }
                ]

                # 创建法律节点
                for law in legal_data:
                    if law['type'] == '法律':
                        session.run(
                            """
                            MERGE (l:Law {id: $id})
                            SET l.name = $name,
                                l.type = $type,
                                l.year = $year,
                                l.created_at = datetime()
                            """,
                            **law
                        )

                        # 创建法条节点
                        for article in law['articles']:
                            session.run(
                                """
                                MERGE (a:Article {number: $number})
                                SET a.content = $content,
                                    a.created_at = datetime()
                                WITH a
                                MATCH (l:Law {id: $id})
                                MERGE (l)-[:HAS_ARTICLE]->(a)
                                """,
                                number=article['number'],
                                content=article['content'],
                                id=law['id']
                            )

                    elif law['type'] == '案例':
                        session.run(
                            """
                            MERGE (c:Case {id: $id})
                            SET c.name = $name,
                                c.type = $type,
                                c.court = $court,
                                c.year = $year,
                                c.created_at = datetime()
                            """,
                            **law
                        )

                        # 关联法律
                        for law_name in law.get('related_laws', []):
                            session.run(
                                """
                                MATCH (c:Case {id: $id}), (l:Law {name: $law_name})
                                MERGE (c)-[:REFERENCES]->(l)
                                """,
                                id=law['id'],
                                law_name=law_name
                            )

                logger.info("    ✅ 创建了法律知识图谱数据")

                return True

        except Exception as e:
            logger.info(f"❌ 法律知识图谱初始化失败: {str(e)}")
            return False

    async def create_missing_directories(self):
        """创建缺失的目录结构"""
        logger.info("\n📁 创建知识图谱目录结构")

        directories_to_create = [
            '/Users/xujian/Athena工作平台/domains/legal/data/professional_knowledge_graphs',
            '/Users/xujian/Athena工作平台/data/knowledge_graph',
            '/Users/xujian/Athena工作平台/data/athena_knowledge_graph'
        ]

        for directory in directories_to_create:
            try:
                os.makedirs(directory, exist_ok=True)
                logger.info(f"  ✅ 创建目录: {directory}")
            except Exception as e:
                logger.info(f"  ❌ 创建目录失败: {directory} - {str(e)}")

    async def run_initialization(self):
        """运行完整的初始化流程"""
        logger.info('🚀 Athena知识图谱初始化')
        logger.info(str('=' * 60))

        # 创建目录结构
        await self.create_missing_directories()

        # 初始化专利知识图谱
        patent_success = await self.initialize_patent_knowledge_graph()

        # 初始化法律知识图谱
        legal_success = await self.initialize_legal_knowledge_graph()

        # 生成总结报告
        logger.info(str("\n" + '=' * 60))
        logger.info('📈 初始化总结报告')
        logger.info(str('=' * 60))

        if patent_success:
            logger.info('✅ 专利知识图谱初始化成功')
        else:
            logger.info('❌ 专利知识图谱初始化失败')

        if legal_success:
            logger.info('✅ 法律知识图谱初始化成功')
        else:
            logger.info('❌ 法律知识图谱初始化失败')

        overall_success = patent_success and legal_success
        logger.info(f"\n🎯 总体状态: {'成功' if overall_success else '部分成功'}")

        if overall_success:
            logger.info("\n💡 后续建议:")
            logger.info('  1. 访问 Neo4j Browser: http://localhost:7474')
            logger.info('  2. 运行知识图谱查询测试')
            logger.info('  3. 集成到业务应用中')
        else:
            logger.info("\n💡 故障排除:")
            logger.info('  1. 检查Neo4j服务状态')
            logger.info('  2. 验证认证信息')
            logger.info('  3. 查看详细错误日志')

        # 清理连接
        if self.driver:
            self.driver.close()

async def main():
    """主函数"""
    initializer = KnowledgeGraphInitializer()
    await initializer.run_initialization()

if __name__ == '__main__':
    asyncio.run(main())
