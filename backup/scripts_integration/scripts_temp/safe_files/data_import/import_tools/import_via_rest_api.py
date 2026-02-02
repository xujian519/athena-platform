#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用REST API方式导入知识图谱数据到JanusGraph
"""

import requests
import json
import logging
import time
from datetime import datetime
from pathlib import Path
import sys

# 设置UTF-8编码
sys.stdout.reconfigure(encoding='utf-8')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RestAPIImporter:
    """使用REST API导入器"""

    def __init__(self):
        self.janusgraph_rest_url = "http://localhost:8182"
        self.session = requests.Session()
        self.stats = {
            "vertices": {},
            "edges": {},
            "start_time": None,
            "end_time": None
        }

    def test_connection(self):
        """测试连接"""
        logger.info("🔌 测试JanusGraph REST连接...")
        try:
            # 使用简单的图查询测试连接
            query = "g.V().limit(1)"
            response = self.session.post(
                f"{self.janusgraph_rest_url}",
                json={"gremlin": query},
                timeout=5
            )

            if response.status_code == 200:
                logger.info("✅ JanusGraph REST连接成功")
                return True
            else:
                logger.error(f"❌ 连接失败，状态码: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ 连接异常: {e}")
            return False

    def execute_query(self, gremlin_query, description="执行查询"):
        """执行Gremlin查询"""
        try:
            response = self.session.post(
                self.janusgraph_rest_url,
                json={"gremlin": gremlin_query},
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                if "result" in result:
                    return result["result"]
                return result
            else:
                logger.error(f"❌ {description}失败: {response.text}")
                return None
        except Exception as e:
            logger.error(f"❌ {description}异常: {e}")
            return None

    def import_patents(self, count=1000):
        """导入专利数据"""
        logger.info(f"📚 导入专利数据 ({count} 条)...")
        self.stats["vertices"]["Patent"] = 0

        # 分批导入，每批50条
        batch_size = 50
        for batch_start in range(1, count + 1, batch_size):
            batch_end = min(batch_start + batch_size - 1, count)

            # 构建批量查询
            queries = []
            for i in range(batch_start, batch_end + 1):
                query = f'''
                    g.addV('Patent')
                        .property('entity_id', 'patent_{i}')
                        .property('patent_number', 'CN{str(i).zfill(9)}A')
                        .property('title', '深度学习专利 {i}: 创新算法实现')
                        .property('abstract', '本专利涉及深度学习算法优化，通过改进网络结构提升性能。')
                        .property('inventors', '发明人{i%10+1}')
                        .property('assignee', '科技公司{i%50+1}')
                        .property('application_date', '2023-{str(i%12+1).zfill(2)}-01')
                        .property('grant_date', '2024-{str(i%12+1).zfill(2)}-15')
                '''
                queries.append(query.strip())

            # 执行批量查询
            for query in queries:
                result = self.execute_query(query, "导入专利")
                if result:
                    self.stats["vertices"]["Patent"] += 1

            if batch_end % 250 == 0:
                logger.info(f"已导入专利: {batch_end}/{count}")

        logger.info(f"✅ 专利导入完成: {self.stats['vertices']['Patent']} 条")

    def import_companies(self, count=100):
        """导入公司数据"""
        logger.info(f"🏢 导入公司数据 ({count} 条)...")
        self.stats["vertices"]["Company"] = 0

        for i in range(1, count + 1):
            query = f'''
                g.addV('Company')
                    .property('entity_id', 'company_{i}')
                    .property('company_id', 'COMP{str(i).zfill(6)}')
                    .property('name', 'AI科技公司{i}')
                    .property('industry', '人工智能')
                    .property('location', '北京市')
                    .property('founded_date', '2010-{str(i%12+1).zfill(2)}-01')
            '''

            result = self.execute_query(query.strip(), "导入公司")
            if result:
                self.stats["vertices"]["Company"] += 1

            if i % 20 == 0:
                logger.info(f"已导入公司: {i}/{count}")

        logger.info(f"✅ 公司导入完成: {self.stats['vertices']['Company']} 条")

    def import_inventors(self, count=500):
        """导入发明人数据"""
        logger.info(f"👥 导入发明人数据 ({count} 条)...")
        self.stats["vertices"]["Inventor"] = 0

        surnames = ["张", "李", "王", "刘", "陈"]
        names = ["伟", "芳", "娜", "敏", "静"]

        for i in range(1, count + 1):
            surname = surnames[i % 5]
            name = names[i % 5]

            query = f'''
                g.addV('Inventor')
                    .property('entity_id', 'inventor_{i}')
                    .property('inventor_id', 'INV{str(i).zfill(6)}')
                    .property('name', '{surname}{name}')
                    .property('organization', '清华大学')
                    .property('specialization', '深度学习')
                    .property('patent_count', {i % 20 + 1})
            '''

            result = self.execute_query(query.strip(), "导入发明人")
            if result:
                self.stats["vertices"]["Inventor"] += 1

            if i % 100 == 0:
                logger.info(f"已导入发明人: {i}/{count}")

        logger.info(f"✅ 发明人导入完成: {self.stats['vertices']['Inventor']} 条")

    def import_relations(self):
        """导入关系数据"""
        logger.info("🔗 导入关系数据...")

        # 专利-公司关系
        logger.info("  创建专利-公司关系...")
        self.stats["edges"]["OWNED_BY"] = 0

        for i in range(1, 500):
            patent_id = (i % 1000) + 1
            company_id = (i % 100) + 1

            query = f'''
                patent = g.V().has('entity_id', 'patent_{patent_id}').tryNext()
                company = g.V().has('entity_id', 'company_{company_id}').tryNext()

                if (patent.isPresent() && company.isPresent()) {{
                    patent.get().addEdge('OWNED_BY', company.get())
                        .property('relationship_type', 'owner')
                        .property('created_at', new Date())
                    1
                }} else {{
                    0
                }}
            '''

            result = self.execute_query(query.strip(), "创建专利-公司关系")
            if result and result[0]:
                self.stats["edges"]["OWNED_BY"] += 1

        # 专利-发明人关系
        logger.info("  创建专利-发明人关系...")
        self.stats["edges"]["INVENTED_BY"] = 0

        for i in range(1, 1000):
            patent_id = (i % 1000) + 1
            inventor_id = (i % 500) + 1

            query = f'''
                patent = g.V().has('entity_id', 'patent_{patent_id}').tryNext()
                inventor = g.V().has('entity_id', 'inventor_{inventor_id}').tryNext()

                if (patent.isPresent() && inventor.isPresent()) {{
                    patent.get().addEdge('INVENTED_BY', inventor.get())
                        .property('contribution_type', 'main')
                        .property('created_at', new Date())
                    1
                }} else {{
                    0
                }}
            '''

            result = self.execute_query(query.strip(), "创建专利-发明人关系")
            if result and result[0]:
                self.stats["edges"]["INVENTED_BY"] += 1

        logger.info(f"✅ 关系导入完成")
        logger.info(f"  OWNED_BY: {self.stats['edges']['OWNED_BY']}")
        logger.info(f"  INVENTED_BY: {self.stats['edges']['INVENTED_BY']}")

    def validate_import(self):
        """验证导入结果"""
        logger.info("\n🔍 验证导入结果...")
        logger.info("=" * 50)

        # 统计顶点
        vertex_count = self.execute_query("g.V().count()", "统计顶点")
        if vertex_count:
            logger.info(f"\n📊 顶点总数: {vertex_count[0]:,}")

        # 按类型统计顶点
        vertex_types = self.execute_query("g.V().groupCount().by(label)", "统计顶点类型")
        if vertex_types and vertex_types[0]:
            logger.info("\n顶点类型分布:")
            for label, count in vertex_types[0].items():
                logger.info(f"  {label}: {count:,}")

        # 统计边
        edge_count = self.execute_query("g.E().count()", "统计边")
        if edge_count:
            logger.info(f"\n边总数: {edge_count[0]:,}")

        # 按类型统计边
        edge_types = self.execute_query("g.E().groupCount().by(label)", "统计边类型")
        if edge_types and edge_types[0]:
            logger.info("\n边类型分布:")
            for label, count in edge_types[0].items():
                logger.info(f"  {label}: {count:,}")

        # 示例查询
        logger.info("\n📝 示例数据:")
        logger.info("-" * 30)

        # 示例专利
        patents = self.execute_query("g.V().hasLabel('Patent').limit(3).valueMap()", "查询专利示例")
        if patents and patents[0]:
            logger.info("\n示例专利:")
            for i, patent in enumerate(patents[0][:3], 1):
                logger.info(f"  {i}. {patent.get('patent_number', 'N/A')} - {patent.get('title', 'N/A')}")

        # 示例公司
        companies = self.execute_query("g.V().hasLabel('Company').limit(3).valueMap()", "查询公司示例")
        if companies and companies[0]:
            logger.info("\n示例公司:")
            for i, company in enumerate(companies[0][:3], 1):
                logger.info(f"  {i}. {company.get('name', 'N/A')} - {company.get('industry', 'N/A')}")

    def run_import(self):
        """执行完整导入流程"""
        self.stats["start_time"] = datetime.now()
        logger.info(f"⏰ 开始时间: {self.stats['start_time']}")

        # 测试连接
        if not self.test_connection():
            logger.error("❌ 无法连接到JanusGraph")
            return False

        try:
            # 清空现有数据（可选）
            logger.info("\n🗑️ 清空现有数据...")
            self.execute_query("g.V().drop()", "清空顶点")

            # 导入各类数据
            self.import_patents(1000)
            self.import_companies(100)
            self.import_inventors(500)
            self.import_relations()

            # 验证导入结果
            self.validate_import()

            self.stats["end_time"] = datetime.now()
            duration = self.stats["end_time"] - self.stats["start_time"]

            logger.info("\n" + "=" * 50)
            logger.info("✅ 导入完成！")
            logger.info(f"⏱️ 总耗时: {duration}")
            logger.info(f"📊 导入统计:")

            total_vertices = sum(self.stats["vertices"].values())
            total_edges = sum(self.stats["edges"].values())

            logger.info(f"  顶点总数: {total_vertices:,}")
            logger.info(f"  边总数: {total_edges:,}")

            return True

        except Exception as e:
            logger.error(f"❌ 导入过程失败: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """主函数"""
    logger.info("🚀 启动JanusGraph知识图谱REST API导入...")
    logger.info("=" * 60)

    importer = RestAPIImporter()
    success = importer.run_import()

    if success:
        print("\n🎉 JanusGraph知识图谱导入成功！")
        print("\n💡 使用方式:")
        print("1. 通过Gremlin控制台查询数据")
        print("2. 使用可视化工具查看图谱")
        print("3. 通过API进行图分析")

        # 生成测试查询
        print("\n📋 示例查询:")
        print("```")
        print("# 查询所有专利")
        print("g.V().hasLabel('Patent')")
        print("")
        print("# 查询专利-公司关系")
        print("g.V().hasLabel('Patent').out('OWNED_BY')")
        print("")
        print("# 统计各类实体数量")
        print("g.V().groupCount().by(label)")
        print("```")
    else:
        print("\n❌ 导入失败，请检查JanusGraph服务状态")

if __name__ == "__main__":
    main()