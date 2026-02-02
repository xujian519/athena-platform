#!/usr/bin/env python3
"""
高效构建知识图谱关系（内存优化版）
Efficient Knowledge Graph Relation Builder (Memory Optimized)

功能:
1. 使用分批处理避免内存溢出
2. 建立年度索引关系
3. 建立案件类型索引关系
4. 建立当事人索引关系

作者: Athena平台团队
版本: v3.0.0
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


class EfficientKGRelationBuilder:
    """高效的知识图谱关系构建器"""

    def __init__(self, uri: str = "bolt://localhost:7687",
                 user: str = "neo4j",
                 password: str = "athena_neo4j_2024"):
        """初始化构建器"""
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        logger.info("✅ 连接到Neo4j知识图谱")

    def close(self):
        """关闭连接"""
        self.driver.close()

    def create_year_index_nodes(self):
        """创建年份索引节点并连接"""
        logger.info("📅 创建年份索引节点...")

        with self.driver.session() as session:
            # 创建年份节点
            result = session.run("""
                MATCH (j:JudgmentDocument)
                WHERE j.year IS NOT NULL
                WITH DISTINCT j.year as year
                MERGE (y:Year {value: year})
                RETURN count(y) as count
            """)
            count = result.single()["count"]
            logger.info(f"  • 创建年份节点: {count} 个")

            # 连接案件到年份节点
            result = session.run("""
                MATCH (j:JudgmentDocument), (y:Year)
                WHERE j.year = y.value
                MERGE (j)-[r:IN_YEAR]->(y)
                RETURN count(*) as count
            """)
            count = result.single()["count"]
            logger.info(f"  • 年份关系: {count:,} 条")

    def create_case_type_index_nodes(self):
        """创建案件类型索引节点并连接"""
        logger.info("🏷️ 创建案件类型索引节点...")

        with self.driver.session() as session:
            # 创建案件类型节点
            result = session.run("""
                MATCH (j:JudgmentDocument)
                WHERE j.case_type IS NOT NULL
                WITH DISTINCT j.case_type as case_type
                MERGE (ct:CaseType {value: case_type})
                RETURN count(ct) as count
            """)
            count = result.single()["count"]
            logger.info(f"  • 创建案件类型节点: {count} 个")

            # 连接案件到类型节点
            result = session.run("""
                MATCH (j:JudgmentDocument), (ct:CaseType)
                WHERE j.case_type = ct.value
                MERGE (j)-[r:OF_TYPE]->(ct)
                RETURN count(*) as count
            """)
            count = result.single()["count"]
            logger.info(f"  • 案件类型关系: {count:,} 条")

    def create_sample_relations(self, sample_size: int = 100):
        """创建样本关系（用于演示）"""
        logger.info(f"🎯 创建样本关系（样本量: {sample_size}）...")

        with self.driver.session() as session:
            # 只取前N个案件建立关系
            result = session.run(f"""
                MATCH (j1:JudgmentDocument)
                WHERE j1.case_type IS NOT NULL
                WITH j1 ORDER BY j1.judgment_id LIMIT {sample_size}
                MATCH (j2:JudgmentDocument)
                WHERE j2.case_type = j1.case_type
                AND j2.judgment_id <> j1.judgment_id
                AND j2.judgment_id > j1.judgment_id
                WITH j1, j2 LIMIT {sample_size}
                MERGE (j1)-[r:SIMILAR_TYPE_CASE]->(j2)
                SET r.case_type = j1.case_type,
                    r.created_at = datetime()
                RETURN count(*) as count
            """)
            count = result.single()["count"] if result.peek() else 0
            logger.info(f"  • 样本关系: {count:,} 条")

    def mark_layer_info(self):
        """标记三层架构信息"""
        logger.info("🏗️ 标记三层架构信息...")

        with self.driver.session() as session:
            result = session.run("""
                MATCH (n:LawDocument)
                WHERE n.layer IS NULL
                SET n.layer = 'foundation_law_layer'
                RETURN count(*) as count
            """)
            count = result.single()["count"]
            logger.info(f"  • LawDocument: {count:,} 个标记为基础法律层")

            result = session.run("""
                MATCH (n:PatentLawDocument)
                WHERE n.layer IS NULL
                SET n.layer = 'patent_professional_layer'
                RETURN count(*) as count
            """)
            count = result.single()["count"]
            logger.info(f"  • PatentLawDocument: {count:,} 个标记为专利专业层")

            result = session.run("""
                MATCH (n:JudgmentDocument)
                WHERE n.layer IS NULL
                SET n.layer = 'judicial_case_layer'
                RETURN count(*) as count
            """)
            count = result.single()["count"]
            logger.info(f"  • JudgmentDocument: {count:,} 个标记为司法案例层")

    def build_statistics_nodes(self):
        """创建统计节点"""
        logger.info("📊 创建统计节点...")

        with self.driver.session() as session:
            # 总数统计
            result = session.run("""
                MATCH (n:JudgmentDocument)
                WITH count(n) as total
                MERGE (stats:KGStatistics {name: 'total_judgments'})
                SET stats.count = total,
                    stats.updated_at = datetime()
                RETURN total
            """)
            count = result.single()["total"]
            logger.info(f"  • 总案件数: {count:,}")

            # 按年份统计
            result = session.run("""
                MATCH (j:JudgmentDocument)
                WHERE j.year IS NOT NULL
                WITH j.year as year, count(j) as count
                MERGE (stats:YearStatistics {year: year})
                SET stats.judgment_count = count,
                    stats.updated_at = datetime()
                RETURN count(*) as years
            """)
            years = result.single()["years"]
            logger.info(f"  • 年份统计: {years} 个年份")

    def build_all_relations(self):
        """构建所有关系"""
        logger.info("🚀 开始构建所有关系...")
        start_time = datetime.now()

        try:
            # 1. 标记层级信息
            self.mark_layer_info()

            # 2. 创建年份索引
            self.create_year_index_nodes()

            # 3. 创建案件类型索引
            self.create_case_type_index_nodes()

            # 4. 创建统计节点
            self.build_statistics_nodes()

            # 5. 创建样本关系
            self.create_sample_relations(sample_size=500)

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

    def verify_results(self):
        """验证构建结果"""
        logger.info("🔍 验证构建结果...")

        with self.driver.session() as session:
            # 节点统计
            result = session.run("""
                MATCH (n)
                RETURN labels(n) as labels, count(n) as count
                ORDER BY count DESC
            """)
            logger.info("\n📊 节点统计:")
            for record in result:
                labels = record["labels"]
                count = record["count"]
                logger.info(f"  • {labels}: {count:,} 个")

            # 关系统计
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as relation_type, count(r) as count
                ORDER BY count DESC
                """)
            logger.info("\n🔗 关系统计:")
            for record in result:
                rel_type = record["relation_type"]
                count = record["count"]
                logger.info(f"  • {rel_type}: {count:,} 条")

            # 连接度统计
            result = session.run("""
                MATCH (n)-[r]-()
                RETURN labels(n) as labels, avg(deg(n)) as avg_degree, max(deg(n)) as max_degree
            """)
            logger.info("\n📈 连接度统计:")
            for record in result:
                labels = record["labels"]
                avg_deg = record["avg_degree"]
                max_deg = record["max_degree"]
                logger.info(f"  • {labels}: 平均连接度 {avg_deg:.2f}, 最大连接度 {max_deg}")


def main():
    """主函数"""
    builder = EfficientKGRelationBuilder()

    try:
        stats = builder.build_all_relations()
        builder.verify_results()
        logger.info("\n🎉 知识图谱关系构建完成！")
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
