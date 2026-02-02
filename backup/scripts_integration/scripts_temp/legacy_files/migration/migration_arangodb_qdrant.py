#!/usr/bin/env python3
"""
ArangoDB + PostgreSQL + Qdrant 迁移实施脚本
Migration implementation script for ArangoDB + PostgreSQL + Qdrant
"""

import asyncio
import logging
from typing import Dict, List, Any
import json
from datetime import datetime

# 数据库连接
from neo4j import GraphDatabase
from arango import ArangoClient
import psycopg2
from psycopg2.extras import execute_values
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HybridDatabaseMigration:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

        # 数据库连接
        self.neo4j_driver = GraphDatabase.driver(
            config["neo4j"]["uri"],
            auth=(config["neo4j"]["user"], config["neo4j"]["password"])
        )

        self.arango_client = ArangoClient(config["arangodb"]["uri"])
        self.arango_sys_db = self.arango_client.db(
            "_system",
            username=config["arangodb"]["user"],
            password=config["arangodb"]["password"]
        )

        self.pg_conn = psycopg2.connect(
            host=config["postgres"]["host"],
            port=config["postgres"]["port"],
            database=config["postgres"]["database"],
            user=config["postgres"]["user"],
            password=config["postgres"]["password"]
        )

        self.qdrant_client = QdrantClient(
            host=config["qdrant"]["host"],
            port=config["qdrant"]["port"]
        )

    async def migrate_patents(self):
        """迁移专利数据"""
        logger.info("🚀 开始迁移专利数据...")

        # 1. 从Neo4j获取专利数据
        patents_data = await self.extract_patents_from_neo4j()

        # 2. 插入PostgreSQL（元数据）
        patent_ids = await self.load_patents_to_postgres(patents_data)

        # 3. 插入ArangoDB（图关系）
        await self.load_patent_graph_to_arango(patents_data)

        # 4. 验证Qdrant向量数据
        await self.verify_qdrant_vectors(patent_ids)

        logger.info(f"✅ 成功迁移 {len(patent_ids)} 个专利")

    async def extract_patents_from_neo4j(self) -> List[Dict]:
        """从Neo4j提取专利数据"""
        patents = []

        with self.neo4j_driver.session() as session:
            # 获取所有专利节点及其关系
            query = """
            MATCH (p:Patent)
            OPTIONAL MATCH (p)-[r]->(related)
            RETURN p, r, related
            """

            result = session.run(query)

            patents_dict = {}
            for record in result:
                node = record["p"]
                patent_id = node["patent_id"]

                if patent_id not in patents_dict:
                    patents_dict[patent_id] = {
                        "patent_id": patent_id,
                        "title": node.get("title", ""),
                        "abstract": node.get("abstract", ""),
                        "application_date": node.get("application_date"),
                        "publication_date": node.get("publication_date"),
                        "status": node.get("status", "unknown"),
                        "applicant": node.get("applicant", ""),
                        "relations": []
                    }

                # 添加关系信息
                if record["r"]:
                    relation = {
                        "type": type(record["r"]).__name__,
                        "target_id": record["related"].get("patent_id") if "patent_id" in dict(record["related"]) else None,
                        "properties": dict(record["r"])
                    }
                    patents_dict[patent_id]["relations"].append(relation)

            patents = list(patents_dict.values())

        logger.info(f"从Neo4j提取了 {len(patents)} 个专利")
        return patents

    async def load_patents_to_postgres(self, patents: List[Dict]) -> List[str]:
        """加载专利元数据到PostgreSQL"""
        cursor = self.pg_conn.cursor()

        # 创建专利表（如果不存在）
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS patents (
            patent_id VARCHAR(50) PRIMARY KEY,
            title TEXT NOT NULL,
            abstract TEXT,
            application_date DATE,
            publication_date DATE,
            status VARCHAR(20),
            applicant VARCHAR(200),
            ipc_codes TEXT[],
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # 准备插入数据
        patent_values = []
        for patent in patents:
            patent_values.append((
                patent["patent_id"],
                patent["title"],
                patent["abstract"],
                patent["application_date"],
                patent["publication_date"],
                patent["status"],
                patent["applicant"],
                patent.get("ipc_codes", [])
            ))

        # 批量插入
        execute_values(
            cursor,
            """
            INSERT INTO patents (patent_id, title, abstract, application_date,
                               publication_date, status, applicant, ipc_codes)
            VALUES %s
            ON CONFLICT (patent_id) DO NOTHING
            """,
            patent_values
        )

        self.pg_conn.commit()

        patent_ids = [p["patent_id"] for p in patents]
        logger.info(f"插入PostgreSQL: {len(patent_ids)} 个专利")

        return patent_ids

    async def load_patent_graph_to_arango(self, patents: List[Dict]):
        """加载专利关系到ArangoDB"""
        # 创建专利图数据库
        if not self.arango_sys_db.has_database("patent_graph"):
            self.arango_sys_db.create_database("patent_graph")

        patent_db = self.arango_client.db(
            "patent_graph",
            username=self.config["arangodb"]["user"],
            password=self.config["arangodb"]["password"]
        )

        # 创建集合
        if not patent_db.has_collection("patents"):
            patent_db.create_collection("patents")

        if not patent_db.has_collection("companies"):
            patent_db.create_collection("companies")

        if not patent_db.has_collection("inventors"):
            patent_db.create_collection("inventors")

        if not patent_db.has_collection("cites"):
            patent_db.create_collection("cites", edge=True)

        if not patent_db.has_collection("owned_by"):
            patent_db.create_collection("owned_by", edge=True)

        # 插入专利节点
        patent_collection = patent_db.collection("patents")
        patent_docs = []

        for patent in patents:
            doc = {
                "_key": patent["patent_id"],
                "patent_id": patent["patent_id"],
                "title": patent["title"],
                "abstract": patent["abstract"],
                "status": patent["status"]
            }
            patent_docs.append(doc)

        # 批量插入
        if patent_docs:
            patent_collection.import_bulk(patent_docs)
            logger.info(f"插入ArangoDB: {len(patent_docs)} 个专利节点")

        # 处理关系
        edges_collection = patent_db.collection("cites")
        edge_docs = []

        for patent in patents:
            for rel in patent["relations"]:
                if rel["target_id"] and rel["type"] == "CITED_BY":
                    edge_doc = {
                        "_from": f"patents/{patent['patent_id']}",
                        "_to": f"patents/{rel['target_id']}",
                        "type": "cites"
                    }
                    edge_docs.append(edge_doc)

        if edge_docs:
            edges_collection.import_bulk(edge_docs)
            logger.info(f"插入ArangoDB: {len(edge_docs)} 个关系")

    async def verify_qdrant_vectors(self, patent_ids: List[str]):
        """验证Qdrant中的向量数据"""
        # 检查专利向量集合是否存在
        collections = self.qdrant_client.get_collections().collections

        if not any(c.name == "patents" for c in collections):
            # 创建向量集合
            self.qdrant_client.create_collection(
                collection_name="patents",
                vectors_config=VectorParams(size=768, distance=Distance.COSINE)
            )
            logger.warning("⚠️ Qdrant中patents集合不存在，已创建空集合")
        else:
            # 检查向量数量
            collection_info = self.qdrant_client.get_collection("patents")
            vector_count = collection_info.points_count

            logger.info(f"✅ Qdrant现有 {vector_count} 个向量")

            # 检查是否有缺失的向量
            if vector_count < len(patent_ids):
                missing = len(patent_ids) - vector_count
                logger.warning(f"⚠️ 有 {missing} 个专利缺少向量数据")

    async def create_unified_search_view(self):
        """创建统一搜索视图"""
        # 在PostgreSQL中创建搜索视图
        cursor = self.pg_conn.cursor()

        cursor.execute("""
        CREATE OR REPLACE VIEW patent_search_view AS
        SELECT
            p.patent_id,
            p.title,
            p.abstract,
            p.applicant,
            p.status,
            p.publication_date,
            -- 获取引用数量（需要通过ArangoDB查询）
            0 as citation_count
        FROM patents p
        """)

        self.pg_conn.commit()
        logger.info("✅ 创建PostgreSQL搜索视图")

    async def generate_migration_report(self):
        """生成迁移报告"""
        report = {
            "migration_time": datetime.now().isoformat(),
            "summary": {
                "neo4j_to_arango": "完成",
                "postgres_metadata": "完成",
                "qdrant_vectors": "保持不变",
                "status": "成功"
            },
            "statistics": {
                "patents_migrated": await self.count_patents(),
                "arango_collections": len(self.arango_client.db("patent_graph").collections()),
                "postgres_rows": await self.count_postgres_rows(),
                "qdrant_vectors": self.qdrant_client.get_collection("patents").points_count if self.qdrant_client.collection_exists("patents") else 0
            }
        }

        # 保存报告
        with open("migration_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info("📊 迁移报告已生成: migration_report.json")
        return report

    async def count_patents(self) -> int:
        """统计专利数量"""
        with self.neo4j_driver.session() as session:
            result = session.run("MATCH (p:Patent) RETURN count(p) as count")
            return result.single()["count"]

    async def count_postgres_rows(self) -> int:
        """统计PostgreSQL行数"""
        cursor = self.pg_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM patents")
        return cursor.fetchone()[0]

    async def cleanup(self):
        """清理资源"""
        if hasattr(self, 'neo4j_driver'):
            self.neo4j_driver.close()
        if hasattr(self, 'pg_conn'):
            self.pg_conn.close()


async def main():
    """主函数"""
    # 配置
    config = {
        "neo4j": {
            "uri": "bolt://localhost:7687",
            "user": "neo4j",
            "password": "password"  # 从环境变量获取
        },
        "arangodb": {
            "uri": "http://localhost:8529",
            "user": "root",
            "password": "password"  # 从环境变量获取
        },
        "postgres": {
            "host": "localhost",
            "port": 5432,
            "database": "athena_platform",
            "user": "postgres",
            "password": "password"  # 从环境变量获取
        },
        "qdrant": {
            "host": "localhost",
            "port": 6333
        }
    }

    migrator = HybridDatabaseMigration(config)

    try:
        # 执行迁移
        await migrator.migrate_patents()
        await migrator.create_unified_search_view()

        # 生成报告
        report = await migrator.generate_migration_report()
        print("\n📊 迁移完成！")
        print(json.dumps(report, ensure_ascii=False, indent=2))

    except Exception as e:
        logger.error(f"❌ 迁移失败: {e}")
    finally:
        await migrator.cleanup()


if __name__ == "__main__":
    asyncio.run(main())