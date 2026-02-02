#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用Python直接导入知识图谱数据
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

# Gremlin Python客户端
from gremlin_python.driver import client, serializer
from gremlin_python.process.anonymous_traversal import traversal

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class KnowledgeGraphImporter:
    """知识图谱导入器"""

    def __init__(self):
        self.gremlin_url = "ws://localhost:8182/gremlin"
        self.client = None
        self.g = None

    async def connect(self):
        """连接到JanusGraph"""
        try:
            self.client = client.Client(
                self.gremlin_url,
                'g',
                message_serializer=serializer.GraphSONSerializersV2d0()
            )
            self.g = traversal().withRemote(self.client)

            # 测试连接
            result = await self.client.submit("1+1").all()
            logger.info("✅ 成功连接到JanusGraph")
            return True
        except Exception as e:
            logger.error(f"❌ 连接JanusGraph失败: {e}")
            return False

    async def close(self):
        """关闭连接"""
        if self.client:
            await self.client.close()

    async def create_indexes(self):
        """创建索引"""
        logger.info("📊 创建索引...")
        try:
            # 创建entity_id索引
            await self.client.submit("""
                mgmt = graph.openManagement()
                if (!mgmt.containsPropertyKey('entity_id')) {
                    entityIdKey = mgmt.makePropertyKey('entity_id').dataType(String.class).make()
                    mgmt.buildIndex('byEntityId', Vertex.class).addKey(entityIdKey).buildCompositeIndex()
                }
                mgmt.commit()
            """).all()
            logger.info("✅ 索引创建成功")
        except Exception as e:
            logger.warning(f"⚠️ 索引创建可能失败: {e}")

    async def import_patents(self, count=1000):
        """导入专利数据"""
        logger.info(f"📚 开始导入专利数据 (数量: {count})...")

        try:
            # 批量创建专利顶点
            for i in range(1, count + 1):
                await self.client.submit(f"""
                    g.addV('Patent')
                    .property('entity_id', 'patent_{i}')
                    .property('patent_number', 'CN{str(i).zfill(9)}A')
                    .property('title', '深度学习专利示例 {i}')
                    .property('abstract', '这是第{i}个专利的摘要内容，涉及深度学习技术创新')
                    .property('inventors', '发明人{i}')
                    .property('assignee', '申请人{i}')
                    .property('application_date', '2023-01-01')
                    .property('grant_date', '2024-01-01')
                    .next()
                """).all()

                # 每100条记录提交一次
                if i % 100 == 0:
                    logger.info(f"已导入 {i} 个专利")

            logger.info(f"✅ 专利数据导入完成，共 {count} 条")
            return count

        except Exception as e:
            logger.error(f"❌ 导入专利数据失败: {e}")
            return 0

    async def import_companies(self, count=100):
        """导入公司数据"""
        logger.info(f"🏢 开始导入公司数据 (数量: {count})...")

        try:
            for i in range(1, count + 1):
                await self.client.submit(f"""
                    g.addV('Company')
                    .property('entity_id', 'company_{i}')
                    .property('company_id', 'COMP{str(i).zfill(6)}')
                    .property('name', '科技公司{i}')
                    .property('industry', '人工智能')
                    .property('location', '北京市')
                    .property('founded_date', '2010-01-01')
                    .next()
                """).all()

                if i % 50 == 0:
                    logger.info(f"已导入 {i} 个公司")

            logger.info(f"✅ 公司数据导入完成，共 {count} 条")
            return count

        except Exception as e:
            logger.error(f"❌ 导入公司数据失败: {e}")
            return 0

    async def import_relations(self, count=500):
        """导入关系数据"""
        logger.info(f"🔗 开始导入关系数据 (数量: {count})...")

        try:
            relations_count = 0

            for i in range(1, count + 1):
                # 创建专利与公司的关系
                patent_id = i % 1000 + 1  # 循环使用专利ID
                company_id = (i % 100) + 1  # 循环使用公司ID

                result = await self.client.submit(f"""
                    patent = g.V().has('entity_id', 'patent_{patent_id}').tryNext()
                    company = g.V().has('entity_id', 'company_{company_id}').tryNext()

                    if (patent.isPresent() && company.isPresent()) {{
                        patent.get().addEdge('OWNED_BY', company.get())
                            .property('relationship_type', 'owner')
                            .property('percentage', '100%')
                            .next()
                        {i}
                    }}
                """).all()

                if result and result[0]:
                    relations_count += 1

                if i % 100 == 0:
                    logger.info(f"已创建 {relations_count} 个关系")

            logger.info(f"✅ 关系数据导入完成，共 {relations_count} 条")
            return relations_count

        except Exception as e:
            logger.error(f"❌ 导入关系数据失败: {e}")
            return 0

    async def validate_import(self):
        """验证导入结果"""
        logger.info("🔍 验证导入结果...")

        try:
            # 获取顶点总数
            vertex_count = await self.client.submit("g.V().count()").all()

            # 获取边总数
            edge_count = await self.client.submit("g.E().count()").all()

            # 按类型统计顶点
            vertex_types = await self.client.submit("g.V().groupCount().by(label)").all()

            # 按类型统计边
            edge_types = await self.client.submit("g.E().groupCount().by(label)").all()

            logger.info("\n📊 导入统计:")
            logger.info(f"  顶点总数: {vertex_count[0]}")
            logger.info(f"  边总数: {edge_count[0]}")

            logger.info("\n📋 按类型统计顶点:")
            if vertex_types[0]:
                for label, count in vertex_types[0].items():
                    logger.info(f"  {label}: {count}")

            logger.info("\n📋 按类型统计边:")
            if edge_types[0]:
                for label, count in edge_types[0].items():
                    logger.info(f"  {label}: {count}")

            # 获取示例数据
            logger.info("\n📝 示例数据:")
            examples = await self.client.submit("g.V().limit(5)").all()
            for example in examples[0][:3]:
                logger.info(f"  {example}")

            return {
                "vertex_count": vertex_count[0],
                "edge_count": edge_count[0],
                "vertex_types": vertex_types[0],
                "edge_types": edge_types[0]
            }

        except Exception as e:
            logger.error(f"❌ 验证失败: {e}")
            return None

async def main():
    """主函数"""
    importer = KnowledgeGraphImporter()

    # 连接到JanusGraph
    if not await importer.connect():
        return

    try:
        # 1. 创建索引
        await importer.create_indexes()

        # 2. 导入数据
        patent_count = await importer.import_patents(1000)
        company_count = await importer.import_companies(100)
        relation_count = await importer.import_relations(500)

        # 3. 验证结果
        stats = await importer.validate_import()

        logger.info("\n✅ 导入完成！")
        logger.info(f"导入统计: 专利 {patent_count}, 公司 {company_count}, 关系 {relation_count}")

        # 测试API
        logger.info("\n🔧 测试API服务...")
        import requests

        try:
            response = requests.post(
                "http://localhost:8080/api/v1/search/hybrid",
                json={
                    "query": "深度学习",
                    "limit": 5
                },
                timeout=5
            )

            if response.status_code == 200:
                logger.info("✅ API服务测试成功")
                result = response.json()
                logger.info(f"搜索结果: {len(result.get('results', []))} 条")
            else:
                logger.warning(f"⚠️ API测试返回状态码: {response.status_code}")

        except Exception as e:
            logger.error(f"❌ API测试失败: {e}")

    finally:
        await importer.close()

if __name__ == "__main__":
    asyncio.run(main())