#!/usr/bin/env python3
"""
Neo4j to ArangoDB 迁移脚本
Migration script from Neo4j to ArangoDB
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from neo4j import GraphDatabase
from arango import ArangoClient
from arango.database import StandardDatabase
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Neo4jToArangoDBMigrator:
    def __init__(
        self,
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_user: str = "neo4j",
        neo4j_password: str = "password",
        arangodb_uri: str = "http://localhost:8529",
        arangodb_user: str = "root",
        arangodb_password: str = "password"
    ):
        self.neo4j_driver = GraphDatabase.driver(
            neo4j_uri,
            auth=(neo4j_user, neo4j_password)
        )
        self.arango_client = ArangoClient(arangodb_uri)
        self.arango_user = arangodb_user
        self.arango_password = arangodb_password

        # ArangoDB数据库映射
        self.db_mappings = {
            "patent_graph": {
                "node_labels": ["Patent", "Company", "Inventor", "IPC"],
                "relationship_types": ["CITED_BY", "OWNED_BY", "INVENTED_BY", "CLASSIFIED_AS"],
                "collection_mappings": {
                    "Patent": "patents",
                    "Company": "companies",
                    "Inventor": "inventors",
                    "IPC": "ipc_classes"
                }
            },
            "knowledge_graph": {
                "node_labels": ["Concept", "Domain", "Entity"],
                "relationship_types": ["RELATED_TO", "BELONGS_TO", "IS_A"],
                "collection_mappings": {
                    "Concept": "concepts",
                    "Domain": "domains",
                    "Entity": "entities"
                }
            }
        }

    async def migrate_all(self):
        """执行完整的迁移流程"""
        logger.info("🚀 开始Neo4j到ArangoDB的迁移...")

        migration_stats = {}

        for db_name, config in self.db_mappings.items():
            logger.info(f"\n📂 迁移数据库: {db_name}")
            stats = await self.migrate_database(db_name, config)
            migration_stats[db_name] = stats

        await self.print_migration_summary(migration_stats)

    async def migrate_database(self, db_name: str, config: Dict[str, Any]) -> Dict[str, int]:
        """迁移单个数据库"""
        # 连接到目标ArangoDB数据库
        arango_db = self.arango_client.db(
            db_name,
            username=self.arango_user,
            password=self.arango_password
        )

        stats = {
            "nodes_migrated": 0,
            "relationships_migrated": 0,
            "errors": 0
        }

        # 1. 迁移节点
        for label in config["node_labels"]:
            logger.info(f"  📝 迁移节点标签: {label}")
            node_stats = await self.migrate_nodes_by_label(
                label,
                arango_db,
                config["collection_mappings"].get(label, label.lower())
            )
            stats["nodes_migrated"] += node_stats["migrated"]
            stats["errors"] += node_stats["errors"]

        # 2. 迁移关系
        for rel_type in config["relationship_types"]:
            logger.info(f"  🔗 迁移关系类型: {rel_type}")
            rel_stats = await self.migrate_relationships_by_type(
                rel_type,
                arango_db,
                config
            )
            stats["relationships_migrated"] += rel_stats["migrated"]
            stats["errors"] += rel_stats["errors"]

        return stats

    async def migrate_nodes_by_label(
        self,
        label: str,
        arango_db: StandardDatabase,
        collection_name: str
    ) -> Dict[str, int]:
        """按标签迁移节点"""
        collection = arango_db.collection(collection_name)

        # 批量大小
        batch_size = 1000
        skip = 0
        migrated = 0
        errors = 0

        with self.neo4j_driver.session() as session:
            while True:
                # 获取一批节点
                query = f"""
                MATCH (n:{label})
                RETURN n
                SKIP {skip}
                LIMIT {batch_size}
                """

                try:
                    result = session.run(query)
                    nodes = list(result)

                    if not nodes:
                        break

                    # 准备ArangoDB文档
                    documents = []
                    for record in nodes:
                        node = record["n"]
                        doc = dict(node)

                        # 保留Neo4j内部ID
                        doc["_neo4j_id"] = node.id
                        doc["_neo4j_labels"] = list(node.labels)

                        # 使用属性作为文档_key
                        if "id" in doc:
                            doc["_key"] = str(doc["id"])
                        elif "patent_id" in doc:
                            doc["_key"] = str(doc["patent_id"])
                        elif "company_id" in doc:
                            doc["_key"] = str(doc["company_id"])
                        elif "name" in doc:
                            doc["_key"] = str(doc["name"]).replace(" ", "_")

                        documents.append(doc)

                    # 批量插入ArangoDB
                    try:
                        collection.import_bulk(documents)
                        migrated += len(documents)
                        logger.info(f"    ✓ 插入 {len(documents)} 个{label}节点")
                    except Exception as e:
                        # 如果批量导入失败，逐个插入
                        for doc in documents:
                            try:
                                collection.insert(doc)
                                migrated += 1
                            except Exception as e:
                                logger.warning(f"    ⚠️ 节点插入失败: {e}")
                                errors += 1

                    skip += batch_size

                except Exception as e:
                    logger.error(f"    ❌ 查询失败: {e}")
                    errors += 1
                    break

        return {"migrated": migrated, "errors": errors}

    async def migrate_relationships_by_type(
        self,
        rel_type: str,
        arango_db: StandardDatabase,
        config: Dict[str, Any]
    ) -> Dict[str, int]:
        """按类型迁移关系"""
        # 确定边集合名称
        edge_collection = self.get_edge_collection_name(rel_type, config)

        # 批量大小
        batch_size = 1000
        skip = 0
        migrated = 0
        errors = 0

        with self.neo4j_driver.session() as session:
            while True:
                # 获取一批关系
                query = f"""
                MATCH ()-[r:{rel_type}]->()
                RETURN r, startNode(r) as start, endNode(r) as end
                SKIP {skip}
                LIMIT {batch_size}
                """

                try:
                    result = session.run(query)
                    relationships = list(result)

                    if not relationships:
                        break

                    # 准备ArangoDB边文档
                    edges = []
                    for record in relationships:
                        rel = record["r"]
                        start_node = record["start"]
                        end_node = record["end"]

                        # 构建边文档
                        edge_doc = {
                            "_from": self.get_arango_id(start_node, config),
                            "_to": self.get_arango_id(end_node, config),
                            "_neo4j_id": rel.id,
                            "_neo4j_type": rel_type
                        }

                        # 添加关系属性
                        edge_doc.update(dict(rel))

                        edges.append(edge_doc)

                    # 批量插入边
                    try:
                        arango_db.collection(edge_collection).import_bulk(edges)
                        migrated += len(edges)
                        logger.info(f"    ✓ 插入 {len(edges)} 个{rel_type}关系")
                    except Exception as e:
                        # 如果批量导入失败，逐个插入
                        for edge in edges:
                            try:
                                arango_db.collection(edge_collection).insert(edge)
                                migrated += 1
                            except Exception as e:
                                logger.warning(f"    ⚠️ 关系插入失败: {e}")
                                errors += 1

                    skip += batch_size

                except Exception as e:
                    logger.error(f"    ❌ 查询失败: {e}")
                    errors += 1
                    break

        return {"migrated": migrated, "errors": errors}

    def get_arango_id(self, node, config: Dict[str, Any]) -> str:
        """获取节点在ArangoDB中的ID"""
        labels = list(node.labels)

        # 找到对应的集合
        collection_name = None
        for label in labels:
            if label in config["collection_mappings"]:
                collection_name = config["collection_mappings"][label]
                break
        else:
            collection_name = labels[0].lower() + "s"

        # 获取_key
        props = dict(node)
        if "id" in props:
            key = str(props["id"])
        elif "patent_id" in props:
            key = str(props["patent_id"])
        elif "company_id" in props:
            key = str(props["company_id"])
        elif "name" in props:
            key = str(props["name"]).replace(" ", "_")
        else:
            key = str(node.id)

        return f"{collection_name}/{key}"

    def get_edge_collection_name(self, rel_type: str, config: Dict[str, Any]) -> str:
        """获取边集合名称"""
        # 关系类型到集合名的映射
        edge_mappings = {
            "CITED_BY": "cited_by",
            "OWNED_BY": "owned_by",
            "INVENTED_BY": "invented_by",
            "CLASSIFIED_AS": "classified_as",
            "RELATED_TO": "related_to",
            "BELONGS_TO": "belongs_to",
            "IS_A": "is_a"
        }
        return edge_mappings.get(rel_type, rel_type.lower())

    async def print_migration_summary(self, stats: Dict[str, Dict[str, int]]):
        """打印迁移总结"""
        logger.info("\n" + "="*50)
        logger.info("📊 迁移总结")
        logger.info("="*50)

        total_nodes = sum(s["nodes_migrated"] for s in stats.values())
        total_rels = sum(s["relationships_migrated"] for s in stats.values())
        total_errors = sum(s["errors"] for s in stats.values())

        for db_name, db_stats in stats.items():
            logger.info(f"\n📂 {db_name}:")
            logger.info(f"  - 节点: {db_stats['nodes_migrated']:,}")
            logger.info(f"  - 关系: {db_stats['relationships_migrated']:,}")
            logger.info(f"  - 错误: {db_stats['errors']}")

        logger.info(f"\n📈 总计:")
        logger.info(f"  - 总节点数: {total_nodes:,}")
        logger.info(f"  - 总关系数: {total_rels:,}")
        logger.info(f"  - 总错误数: {total_errors}")

        if total_errors == 0:
            logger.info("\n✅ 迁移成功完成！")
        else:
            logger.warning(f"\n⚠️ 迁移完成，但有 {total_errors} 个错误")

    async def verify_migration(self):
        """验证迁移结果"""
        logger.info("\n🔍 验证迁移结果...")

        for db_name, config in self.db_mappings.items():
            arango_db = self.arango_client.db(
                db_name,
                username=self.arango_user,
                password=self.arango_password
            )

            # 检查集合和文档数
            logger.info(f"\n📂 {db_name}:")

            for collection in arango_db.collections():
                if not collection["system"]:
                    coll = arango_db.collection(collection["name"])
                    count = coll.count()
                    logger.info(f"  - {collection['name']}: {count:,} 文档")

    async def close(self):
        """关闭连接"""
        self.neo4j_driver.close()


async def main():
    """主函数"""
    migrator = Neo4jToArangoDBMigrator(
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="your_neo4j_password",
        arangodb_uri="http://localhost:8529",
        arangodb_user="root",
        arangodb_password="your_arangodb_password"
    )

    try:
        await migrator.migrate_all()
        await migrator.verify_migration()
    finally:
        await migrator.close()


if __name__ == "__main__":
    asyncio.run(main())