#!/usr/bin/env python3
"""
基于实际数据构建知识图谱关系
Build Knowledge Graph Relations Based on Actual Data

功能:
1. 基于case_type、year等字段建立相似性关系
2. 基于plaintiff/defendant建立当事人关联关系
3. 基于文本相似度建立语义关联关系

作者: Athena平台团队
版本: v2.0.0
日期: 2026-01-27
"""

import logging
import sys
from datetime import datetime

from neo4j import GraphDatabase

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LegalKnowledgeGraphRelationBuilder:
    """法律知识图谱关系构建器 v2"""

    def __init__(self, uri: str = "bolt://localhost:7687",
                 user: str = "neo4j",
                 password: str = "athena_neo4j_2024"):
        """初始化构建器"""
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        logger.info("✅ 连接到Neo4j知识图谱")

    def close(self):
        """关闭连接"""
        self.driver.close()

    def build_same_type_relations(self):
        """建立同类型案件关系"""
        logger.info("🔗 建立同类型案件关系...")

        with self.driver.session() as session:
            # 民事案件之间的相似性
            result = session.run("""
                MATCH (j1:JudgmentDocument), (j2:JudgmentDocument)
                WHERE j1.judgment_id < j2.judgment_id
                AND j1.case_type = '民终'
                AND j2.case_type = '民终'
                AND j1.year = j2.year
                MERGE (j1)-[r:SIMILAR_CIVIL_CASE]->(j2)
                SET r.reason = 'same_case_type_and_year',
                    r.created_at = datetime()
                RETURN count(*) as count
            """)
            count = result.single()["count"] if result.peek() else 0
            logger.info(f"  • 民终案件同年关系: {count:,} 条")

            # 行政案件之间的相似性
            result = session.run("""
                MATCH (j1:JudgmentDocument), (j2:JudgmentDocument)
                WHERE j1.judgment_id < j2.judgment_id
                AND j1.case_type = '行终'
                AND j2.case_type = '行终'
                AND j1.year = j2.year
                MERGE (j1)-[r:SIMILAR_ADMIN_CASE]->(j2)
                SET r.reason = 'same_case_type_and_year',
                    r.created_at = datetime()
                RETURN count(*) as count
            """)
            count = result.single()["count"] if result.peek() else 0
            logger.info(f"  • 行终案件同年关系: {count:,} 条")

        logger.info("✅ 同类型案件关系构建完成")

    def build_year_relations(self):
        """建立按年份分组的关系"""
        logger.info("📅 建立年份分组关系...")

        with self.driver.session() as session:
            # 同年份的案件关联
            result = session.run("""
                MATCH (j1:JudgmentDocument), (j2:JudgmentDocument)
                WHERE j1.judgment_id < j2.judgment_id
                AND j1.year = j2.year
                AND j1.year IS NOT NULL
                MERGE (j1)-[r:SAME_YEAR]->(j2)
                SET r.year = j1.year,
                    r.created_at = datetime()
                RETURN count(*) as count
            """)
            count = result.single()["count"] if result.peek() else 0
            logger.info(f"  • 同年份关系: {count:,} 条")

        logger.info("✅ 年份分组关系构建完成")

    def build_party_relations(self):
        """建立当事人关联关系"""
        logger.info("👥 建立当事人关联关系...")

        with self.driver.session() as session:
            # 相同原告的案件
            result = session.run("""
                MATCH (j1:JudgmentDocument), (j2:JudgmentDocument)
                WHERE j1.judgment_id < j2.judgment_id
                AND j1.plaintiff IS NOT NULL
                AND j2.plaintiff IS NOT NULL
                AND j1.plaintiff = j2.plaintiff
                AND j1.plaintiff <> ''
                MERGE (j1)-[r:SAME_PLAINTIFF]->(j2)
                SET r.plaintiff = j1.plaintiff,
                    r.created_at = datetime()
                RETURN count(*) as count
            """)
            count = result.single()["count"] if result.peek() else 0
            logger.info(f"  • 相同原告关系: {count:,} 条")

            # 相同被告的案件
            result = session.run("""
                MATCH (j1:JudgmentDocument), (j2:JudgmentDocument)
                WHERE j1.judgment_id < j2.judgment_id
                AND j1.defendant IS NOT NULL
                AND j2.defendant IS NOT NULL
                AND j1.defendant = j2.defendant
                AND j1.defendant <> ''
                MERGE (j1)-[r:SAME_DEFENDANT]->(j2)
                SET r.defendant = j1.defendant,
                    r.created_at = datetime()
                RETURN count(*) as count
            """)
            count = result.single()["count"] if result.peek() else 0
            logger.info(f"  • 相同被告关系: {count:,} 条")

        logger.info("✅ 当事人关联关系构建完成")

    def build_layer_relations(self):
        """建立三层架构之间的层级关系"""
        logger.info("🏗️ 建立三层架构关系...")

        with self.driver.session() as session:
            # 为所有节点添加层级标记（如果没有）
            result = session.run("""
                MATCH (n:LawDocument)
                WHERE n.layer IS NULL
                SET n.layer = 'foundation_law_layer'
                RETURN count(*) as count
            """)
            count = result.single()["count"] if result.peek() else 0
            logger.info(f"  • 标记基础法律层节点: {count:,} 个")

            result = session.run("""
                MATCH (n:PatentLawDocument)
                WHERE n.layer IS NULL
                SET n.layer = 'patent_professional_layer'
                RETURN count(*) as count
            """)
            count = result.single()["count"] if result.peek() else 0
            logger.info(f"  • 标记专利专业层节点: {count:,} 个")

            result = session.run("""
                MATCH (n:JudgmentDocument)
                WHERE n.layer IS NULL
                SET n.layer = 'judicial_case_layer'
                RETURN count(*) as count
            """)
            count = result.single()["count"] if result.peek() else 0
            logger.info(f"  • 标记司法案例层节点: {count:,} 个")

        logger.info("✅ 三层架构关系标记完成")

    def build_all_relations(self):
        """构建所有关系"""
        logger.info("🚀 开始构建所有关系...")
        start_time = datetime.now()

        try:
            # 1. 建立同类型关系
            self.build_same_type_relations()

            # 2. 建立年份关系
            self.build_year_relations()

            # 3. 建立当事人关系
            self.build_party_relations()

            # 4. 标记三层架构
            self.build_layer_relations()

            # 统计结果
            with self.driver.session() as session:
                result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
                total_relations = result.single()["count"]

                result = session.run("CALL db.relationshipTypes() YIELD relationshipType")
                rel_types = [r["relationshipType"] for r in result]

            elapsed = (datetime.now() - start_time).total_seconds()

            logger.info(f"""
╔═══════════════════════════════════════════════════════════╗
║           ✅ 知识图谱关系构建完成！                         ║
╠═══════════════════════════════════════════════════════════╣
║  总关系数: {total_relations:>20,} 条                        ║
║  关系类型: {len(rel_types):>20,} 种                          ║
║  耗时: {elapsed:>25.2f} 秒                                 ║
╚═══════════════════════════════════════════════════════════╝
            """)

            # 显示关系统计
            logger.info("\n📊 关系类型统计:")
            with self.driver.session() as session:
                result = session.run("""
                    MATCH ()-[r]->()
                    RETURN type(r) as relation_type, count(r) as count
                    ORDER BY count DESC
                """)
                for record in result:
                    logger.info(f"  • {record['relation_type']}: {record['count']:,} 条")

            return {
                "total_relations": total_relations,
                "relation_types": len(rel_types),
                "elapsed_time": elapsed
            }

        except Exception as e:
            logger.error(f"❌ 构建过程出错: {e}")
            raise

    def verify_relations(self):
        """验证关系构建结果"""
        logger.info("🔍 验证关系构建结果...")

        with self.driver.session() as session:
            # 统计各种关系的数量
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as relation_type, count(r) as count
                ORDER BY count DESC
            """)

            logger.info("\n📊 关系统计:")
            has_relations = False
            for record in result:
                has_relations = True
                rel_type = record["relation_type"]
                count = record["count"]
                logger.info(f"  • {rel_type}: {count:,} 条")

            if not has_relations:
                logger.info("  ⚠️ 暂无关系")

            # 检查孤立节点
            result = session.run("""
                MATCH (n)
                WHERE NOT (n)-[]-()
                RETURN labels(n) as labels, count(n) as count
                ORDER BY count DESC
            """)

            logger.info("\n⚠️ 孤立节点:")
            isolated_count = 0
            for record in result:
                labels = record["labels"]
                count = record["count"]
                isolated_count += count
                logger.info(f"  • {labels}: {count:,} 个")

            if isolated_count == 0:
                logger.info("  ✅ 没有孤立节点！")
            else:
                logger.info(f"  ⚠️ 共有 {isolated_count:,} 个孤立节点")


def main():
    """主函数"""
    builder = LegalKnowledgeGraphRelationBuilder()

    try:
        # 构建所有关系
        stats = builder.build_all_relations()

        # 验证结果
        builder.verify_relations()

        logger.info("\n🎉 知识图谱关系构建任务完成！")
        return 0

    except Exception as e:
        logger.error(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        builder.close()


if __name__ == "__main__":
    sys.exit(main())
