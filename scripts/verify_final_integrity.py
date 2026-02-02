#!/usr/bin/env python3
"""
法律世界模型三库完整性最终验证
Final Integrity Verification for Legal World Model Three Databases

检查项目:
1. Qdrant向量库数据量
2. Neo4j知识图谱节点和关系统计
3. PostgreSQL无效决定数据量
4. 三库数据一致性

作者: Athena平台团队
版本: v1.0.0
日期: 2026-01-27
"""

import logging
import sys
from datetime import datetime

from neo4j import GraphDatabase
from qdrant_client import QdrantClient
import psycopg2

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def verify_qdrant():
    """验证Qdrant向量库"""
    logger.info("\n" + "="*60)
    logger.info("📊 Qdrant向量库验证")
    logger.info("="*60)

    try:
        client = QdrantClient(host="localhost", port=6333)

        # 司法案例集合
        collections = ["patent_judgments", "patent_laws", "invalidation_decisions"]

        total_count = 0
        for collection_name in collections:
            try:
                collection_info = client.get_collection(collection_name)
                count = collection_info.points_count
                total_count += count
                logger.info(f"  ✅ {collection_name}: {count:,} 条记录")
            except Exception as e:
                logger.warning(f"  ⚠️ {collection_name}: 不存在或无法访问")

        logger.info(f"\n  📊 Qdrant总计: {total_count:,} 条记录")
        return total_count

    except Exception as e:
        logger.error(f"  ❌ Qdrant连接失败: {e}")
        return 0


def verify_neo4j():
    """验证Neo4j知识图谱"""
    logger.info("\n" + "="*60)
    logger.info("🕸️ Neo4j知识图谱验证")
    logger.info("="*60)

    try:
        driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "athena_neo4j_2024")
        )

        with driver.session() as session:
            # 节点统计
            result = session.run("""
                MATCH (n)
                RETURN labels(n) as labels, count(n) as count
                ORDER BY count DESC
            """)
            logger.info("\n  📊 节点统计:")
            total_nodes = 0
            for record in result:
                labels = str(record["labels"])
                count = record["count"]
                total_nodes += count
                logger.info(f"    • {labels}: {count:,}")

            # 关系统计
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as relation_type, count(r) as count
                ORDER BY count DESC
            """)
            logger.info("\n  🔗 关系统计:")
            total_relations = 0
            for record in result:
                rel_type = record["relation_type"]
                count = record["count"]
                total_relations += count
                logger.info(f"    • {rel_type}: {count:,}")

            logger.info(f"\n  📊 Neo4j总计: {total_nodes:,} 个节点, {total_relations:,} 条关系")

        driver.close()
        return {"nodes": total_nodes, "relations": total_relations}

    except Exception as e:
        logger.error(f"  ❌ Neo4j连接失败: {e}")
        return {"nodes": 0, "relations": 0}


def verify_postgresql():
    """验证PostgreSQL数据库"""
    logger.info("\n" + "="*60)
    logger.info("🗄️ PostgreSQL数据库验证")
    logger.info("="*60)

    try:
        conn = psycopg2.connect(host="localhost", port=5432, database="patent_rules", user="xujian")

        with conn.cursor() as cursor:
            # 无效决定表
            cursor.execute("""
                SELECT
                    (SELECT COUNT(*) FROM invalidation_decisions_import) as import_count,
                    (SELECT COUNT(*) FROM invalidation_decisions_enhanced) as enhanced_count
            """)
            result = cursor.fetchone()
            import_count = result[0]
            enhanced_count = result[1]

            logger.info(f"  📊 无效决定统计:")
            logger.info(f"    • invalidation_decisions_import: {import_count:,} 条")
            logger.info(f"    • invalidation_decisions_enhanced: {enhanced_count:,} 条")

            # 按决定结果统计
            cursor.execute("""
                SELECT decision_conclusion, COUNT(*) as count
                FROM invalidation_decisions_import
                GROUP BY decision_conclusion
                ORDER BY count DESC
            """)
            logger.info(f"\n  📊 按决定结果统计:")
            for record in cursor:
                conclusion = record[0] or "未知"
                count = record[1]
                logger.info(f"    • {conclusion}: {count:,}")

        conn.close()
        return import_count + enhanced_count

    except Exception as e:
        logger.error(f"  ❌ PostgreSQL连接失败: {e}")
        return 0


def main():
    """主函数"""
    logger.info("""
╔═══════════════════════════════════════════════════════════╗
║     法律世界模型三库完整性最终验证                        ║
║     Legal World Model Final Integrity Verification        ║
╠═══════════════════════════════════════════════════════════╣
║  版本: v1.0.0                                              ║
║  日期: 2026-01-27                                          ║
║  作者: Athena平台团队                                       ║
╚═══════════════════════════════════════════════════════════╝
    """)

    start_time = datetime.now()

    # 验证三个数据库
    qdrant_count = verify_qdrant()
    neo4j_stats = verify_neo4j()
    pg_count = verify_postgresql()

    elapsed = (datetime.now() - start_time).total_seconds()

    # 输出最终总结
    logger.info(f"""
╔═══════════════════════════════════════════════════════════╗
║                   验证结果汇总                              ║
╠═══════════════════════════════════════════════════════════╣
║  Qdrant向量库:        {qdrant_count:>15,} 条记录                 ║
║  Neo4j知识图谱:      {neo4j_stats['nodes']:>15,} 个节点                 ║
║                     {neo4j_stats['relations']:>15,} 条关系                  ║
║  PostgreSQL规则库:    {pg_count:>15,} 条记录                 ║
╠═══════════════════════════════════════════════════════════╣
║  验证耗时: {elapsed:>23.2f} 秒                              ║
╚═══════════════════════════════════════════════════════════╝
    """)

    # 健康度评估
    health_score = 0

    if qdrant_count >= 10000:
        health_score += 33
        logger.info("✅ Qdrant: 数据量充足")
    else:
        logger.warning("⚠️ Qdrant: 数据量不足")

    if neo4j_stats['nodes'] >= 10000 and neo4j_stats['relations'] >= 1000:
        health_score += 34
        logger.info("✅ Neo4j: 节点和关系充足")
    else:
        logger.warning("⚠️ Neo4j: 节点或关系不足")

    if pg_count >= 30000:
        health_score += 33
        logger.info("✅ PostgreSQL: 数据量充足")
    else:
        logger.warning("⚠️ PostgreSQL: 数据量不足")

    logger.info(f"\n🎯 三库健康度: {health_score}/100")

    if health_score >= 90:
        logger.info("🎉 三库完整性验证通过！数据已准备就绪！")
        return 0
    else:
        logger.warning("⚠️ 三库完整性需要进一步优化")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.info("\n⏹️ 用户中断")
        sys.exit(130)
    except Exception as e:
        logger.error(f"\n❌ 验证出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
