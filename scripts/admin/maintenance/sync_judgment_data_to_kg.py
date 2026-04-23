#!/usr/bin/env python3
"""
司法案例数据同步脚本
Sync Judgment Data from Vector DB to Knowledge Graph

功能:
1. 从Qdrant向量库读取司法案例数据
2. 同步到Neo4j知识图谱
3. 补充缺失的案例节点和关系

作者: Athena平台团队
版本: v1.0.0
日期: 2026-01-27
"""

import logging
import sys
from datetime import datetime

from neo4j import GraphDatabase
from qdrant_client import QdrantClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class JudgmentDataSyncer:
    """司法案例数据同步器"""

    def __init__(
        self,
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_user: str = "neo4j",
        neo4j_password: str = "athena_neo4j_2024",
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333
    ):
        """初始化同步器"""
        self.neo4j_driver = GraphDatabase.driver(
            neo4j_uri,
            auth=(neo4j_user, neo4j_password)
        )
        self.qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)
        logger.info("✅ 连接到Neo4j和Qdrant")

    def close(self):
        """关闭连接"""
        self.neo4j_driver.close()

    def get_vector_judgment_data(self) -> list[dict]:
        """从Qdrant获取所有司法案例数据"""
        logger.info("📥 从Qdrant读取司法案例数据...")

        collection_name = "patent_judgments"

        # 获取集合中所有点的ID和payload
        records, _ = self.qdrant_client.scroll(
            collection_name=collection_name,
            limit=100000,
            with_payload=True
        )

        judgments = []
        for record in records:
            # 使用judgment_id或id作为主键
            judgment_id = record.payload.get("judgment_id") or record.payload.get("id")
            if judgment_id:
                judgments.append({
                    "id": judgment_id,
                    "title": record.payload.get("title", ""),
                    "year": record.payload.get("year"),
                    "case_type": record.payload.get("case_type"),
                    "plaintiff": record.payload.get("plaintiff", ""),
                    "defendant": record.payload.get("defendant", ""),
                    "vector_id": str(record.id)
                })

        logger.info(f"✅ Qdrant中有 {len(judgments):,} 个司法案例")
        return judgments

    def get_neo4j_judgment_ids(self) -> set:
        """从Neo4j获取所有司法案例ID"""
        logger.info("📥 从Neo4j读取司法案例数据...")

        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (j:JudgmentDocument)
                RETURN j.judgment_id as doc_id
            """)

            judgment_ids = {record["doc_id"] for record in result if record["doc_id"]}

        logger.info(f"✅ Neo4j中有 {len(judgment_ids):,} 个司法案例")
        return judgment_ids

    def sync_judgment_nodes(self, vector_data: list[dict], neo4j_ids: set):
        """同步司法案例节点

        将Qdrant中存在但Neo4j中不存在的案例同步到Neo4j
        """
        missing_data = [j for j in vector_data if j["id"] not in neo4j_ids]

        if not missing_data:
            logger.info("✅ 所有案例都已同步")
            return

        logger.info(f"🔄 发现 {len(missing_data):,} 个缺失案例，开始同步...")

        with self.neo4j_driver.session() as session:
            batch_size = 100
            synced_count = 0

            for i in range(0, len(missing_data), batch_size):
                batch = missing_data[i:i+batch_size]

                for judgment in batch:
                    try:
                        # 创建JudgmentDocument节点
                        session.run("""
                            CREATE (j:JudgmentDocument {
                                judgment_id: $judgment_id,
                                title: $title,
                                year: $year,
                                case_type: $case_type,
                                plaintiff: $plaintiff,
                                defendant: $defendant,
                                synced_from: 'qdrant',
                                synced_at: datetime(),
                                layer: 'judicial_case_layer',
                                vector_id: $vector_id
                            })
                        """,
                        judgment_id=judgment["id"],
                        title=judgment["title"],
                        year=judgment["year"],
                        case_type=judgment["case_type"],
                        plaintiff=judgment["plaintiff"],
                        defendant=judgment["defendant"],
                        vector_id=judgment["vector_id"]
                        )

                        synced_count += 1

                        if synced_count % 100 == 0:
                            logger.info(f"  已同步: {synced_count}/{len(missing_data)}")

                    except Exception as e:
                        logger.warning(f"  ⚠️ 同步 {judgment['id']} 失败: {e}")

        logger.info(f"✅ 同步完成: {synced_count:,} 个新案例")

    def verify_sync(self):
        """验证同步结果"""
        logger.info("🔍 验证同步结果...")

        with self.neo4j_driver.session() as session:
            # 统计案例数量
            result = session.run("""
                MATCH (j:JudgmentDocument)
                RETURN count(j) as count
            """)
            count = result.single()["count"]

            logger.info(f"📊 Neo4j司法案例总数: {count:,}")

            # 检查同步状态
            result = session.run("""
                MATCH (j:JudgmentDocument)
                RETURN j.synced_from as source, count(j) as count
            """)
            logger.info("\n按来源统计:")
            for record in result:
                source = record["source"] or "未知"
                count = record["count"]
                logger.info(f"  • {source}: {count:,}")

    def run(self):
        """执行同步"""
        logger.info("🚀 开始司法案例数据同步...")
        start_time = datetime.now()

        try:
            # 1. 获取Qdrant中的案例数据
            vector_data = self.get_vector_judgment_data()

            # 2. 获取Neo4j中的案例ID
            neo4j_ids = self.get_neo4j_judgment_ids()

            # 3. 同步缺失的案例
            self.sync_judgment_nodes(vector_data, neo4j_ids)

            # 4. 验证结果
            self.verify_sync()

            elapsed = (datetime.now() - start_time).total_seconds()

            logger.info(f"""
╔═══════════════════════════════════════════════════════════╗
║           ✅ 司法案例数据同步完成！                         ║
╠═══════════════════════════════════════════════════════════╣
║  Qdrant案例数: {len(vector_data):>18,}                     ║
║  Neo4j案例数: {len(neo4j_ids):>18,}                      ║
║  耗时: {elapsed:>26.2f} 秒                               ║
╚═══════════════════════════════════════════════════════════╝
            """)

        except Exception as e:
            logger.error(f"❌ 同步失败: {e}")
            raise


def main():
    """主函数"""
    syncer = JudgmentDataSyncer()

    try:
        syncer.run()
        return 0
    except Exception as e:
        logger.error(f"❌ 执行失败: {e}")
        return 1
    finally:
        syncer.close()


if __name__ == "__main__":
    sys.exit(main())
