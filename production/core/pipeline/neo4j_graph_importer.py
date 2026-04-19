#!/usr/bin/env python3
from __future__ import annotations
"""
Neo4j知识图谱导入模块
Neo4j Knowledge Graph Importer

版本: v3.0.0
技术决策: TD-001 - 统一图数据库选择为Neo4j

将处理好的法律知识导入到Neo4j图数据库

核心变更:
- ConnectionPool → GraphDatabase.driver
- CREATE SPACE/ TAG/ EDGE → CREATE CONSTRAINT/ INDEX
- INSERT VERTEX/EDGE → MERGE (node/relationship)
- nGQL → Cypher

作者: Athena AI系统
创建时间: 2025-01-06
更新时间: 2026-01-25 (TD-001: 迁移到Neo4j)
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from core.config.secure_config import get_config

config = get_config()

logger = logging.getLogger(__name__)


class Neo4jKnowledgeGraphImporter:
    """Neo4j知识图谱导入器 (TD-001: 替换KnowledgeGraphImporter)"""

    def __init__(self, config: dict[str, Any] | None = None):
        """
        初始化导入器

        Args:
            config: 配置字典,包含:
                - uri: Neo4j连接URI (bolt://host:port)
                - database: 数据库名称
                - username: 用户名
                - password: 密码
        """
        self.config = config or {}
        self.uri = self.config.get("uri", "bolt://127.0.0.1:7687")
        self.database = self.config.get("database", "legal_books")
        self.username = self.config.get("username", "neo4j")
        self.password = self.config.get(
            "password", config.get("NEO4J_PASSWORD", "password")
        )

        # 初始化Neo4j驱动
        self.driver = None

        logger.info("🕸️ Neo4j知识图谱导入器初始化完成")
        logger.info(f"   URI: {self.uri}")
        logger.info(f"   Database: {self.database}")

    async def connect(self):
        """连接到Neo4j (TD-001: 使用GraphDatabase.driver)"""
        try:
            from neo4j import GraphDatabase

            # 创建驱动
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password),
            )

            # 测试连接
            with self.driver.session(database=self.database) as session:
                result = session.run("RETURN 'Connection OK' as message")
                record = result.single()
                if record and record["message"] == "Connection OK":
                    logger.info(f"✅ 成功连接到Neo4j: {self.database}")
                else:
                    raise Exception("连接测试失败")

        except Exception as e:
            logger.error(f"❌ 连接Neo4j失败: {e}")
            raise

    async def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()
            logger.info("🔌 Neo4j连接已关闭")

    async def import_knowledge_graph(self, graph_data: dict[str, Any]) -> dict[str, Any]:
        """
        导入知识图谱

        Args:
            graph_data: 图谱数据,包含nodes和relations

        Returns:
            导入结果
        """
        logger.info("🕸️ 开始导入知识图谱到Neo4j")

        # 连接数据库
        await self.connect()

        try:
            # 确保数据库存在
            await self._ensure_database_exists()

            # 创建数据模型(约束和索引)
            await self._create_schema()

            # 导入节点
            nodes_result = await self._import_nodes(graph_data["nodes"])

            # 导入关系
            relations_result = await self._import_relations(graph_data["relations"])

            logger.info("✅ 知识图谱导入完成")

            return {
                "status": "success",
                "nodes_imported": nodes_result["success_count"],
                "relations_imported": relations_result["success_count"],
                "nodes_failed": nodes_result["failed_count"],
                "relations_failed": relations_result["failed_count"],
                "database": self.database,
            }

        except Exception as e:
            logger.error(f"❌ 导入失败: {e}")
            raise

        finally:
            await self.close()

    async def _ensure_database_exists(self):
        """确保数据库存在 (TD-001: 替换_ensure_space_exists)"""
        try:
            with self.driver.session(database="system") as session:
                # 检查数据库是否存在
                check_query = "SHOW DATABASES"
                result = session.run(check_query)

                database_exists = False
                for record in result:
                    db_name = record["name"]
                    if db_name == self.database:
                        database_exists = True
                        break

                if not database_exists:
                    logger.info(f"📦 创建新数据库: {self.database}")
                    create_query = f"CREATE DATABASE {self.database}"
                    session.run(create_query)
                    logger.info(f"✅ 数据库 {self.database} 创建成功")
                    # 等待数据库生效
                    await asyncio.sleep(5)
                else:
                    logger.info(f"📦 数据库 {self.database} 已存在")

        except Exception as e:
            logger.error(f"❌ 数据库操作失败: {e}")
            raise

    async def _create_schema(self):
        """创建数据模型(约束和索引) (TD-001: 替换Tag/Edge为Constraint)"""
        logger.info("📐 创建数据模型")

        with self.driver.session(database=self.database) as session:
            # 创建节点标签(对应NebulaGraph的Tag)
            labels = [
                "Book",
                "Case",
                "LegalRule",
                "Concept",
                "Procedure",
                "Criterion",
            ]

            for label in labels:
                # 创建唯一性约束(自动创建索引)
                constraint_query = f"""
                CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) REQUIRE n.id IS UNIQUE
                """
                try:
                    session.run(constraint_query)
                    logger.info(f"✅ 创建约束: {label}")
                except Exception as e:
                    if "already exists" not in str(e).lower():
                        logger.warning(f"⚠️ 创建约束失败: {label} - {e}")

            # 创建全文索引(用于文本搜索)
            try:
                session.run("""
                    CREATE FULLTEXT INDEX entity_search_index IF NOT EXISTS
                    FOR (n:Book) ON EACH [n.name]
                    OPTIONS {indexConfig: {`fulltext.analyzer`: "chinese"}}
                """)
                logger.info("✅ 创建全文索引")
            except Exception as e:
                if "already exists" not in str(e).lower():
                    logger.warning(f"⚠️ 创建全文索引失败: {e}")

    async def _import_nodes(self, nodes: list[dict[str, Any]]) -> dict[str, Any]:
        """
        导入节点 (TD-001: 使用Cypher MERGE)

        Args:
            nodes: 节点列表

        Returns:
            导入结果
        """
        success_count = 0
        failed_count = 0
        errors = []

        with self.driver.session(database=self.database) as session:
            for node in nodes:
                try:
                    node_id = node["id"]
                    label = node["type"]  # 对应NebulaGraph的Tag
                    properties = node.get("properties", {})

                    # 构建Cypher MERGE语句
                    props_list = []
                    params = {"id": node_id}

                    for k, v in properties.items():
                        param_key = f"prop_{k}"
                        props_list.append(f"n.{k} = ${param_key}")
                        params[param_key] = v

                    set_clause = ", ".join(props_list) if props_list else ""

                    merge_query = f"""
                    MERGE (n:{label} {{id: $id}})
                    {"SET " + set_clause if set_clause else ""}
                    RETURN n.id as id
                    """

                    session.run(merge_query, params)
                    success_count += 1

                except Exception as e:
                    failed_count += 1
                    error_msg = f"节点 {node.get('id')} 处理异常: {e!s}"
                    errors.append(error_msg)
                    logger.warning(error_msg)

        logger.info(f"📊 节点导入完成: 成功 {success_count}, 失败 {failed_count}")

        return {"success_count": success_count, "failed_count": failed_count, "errors": errors}

    async def _import_relations(self, relations: list[dict[str, Any]]) -> dict[str, Any]:
        """
        导入关系 (TD-001: 使用Cypher MERGE)

        Args:
            relations: 关系列表

        Returns:
            导入结果
        """
        success_count = 0
        failed_count = 0
        errors = []

        with self.driver.session(database=self.database) as session:
            for relation in relations:
                try:
                    source_id = relation["source"]
                    target_id = relation["target"]
                    rel_type = relation["type"]  # 对应NebulaGraph的Edge
                    properties = relation.get("properties", {})

                    # 构建Cypher MERGE语句
                    props_list = []
                    params = {
                        "source_id": source_id,
                        "target_id": target_id,
                    }

                    for k, v in properties.items():
                        param_key = f"prop_{k}"
                        props_list.append(f"r.{k} = ${param_key}")
                        params[param_key] = v

                    set_clause = ", ".join(props_list) if props_list else ""

                    merge_query = f"""
                    MATCH (src {{id: $source_id}})
                    MATCH (dst {{id: $target_id}})
                    MERGE (src)-[r:{rel_type}]->(dst)
                    {"SET " + set_clause if set_clause else ""}
                    RETURN type(r) as rel_type
                    """

                    session.run(merge_query, params)
                    success_count += 1

                except Exception as e:
                    failed_count += 1
                    error_msg = (
                        f"关系 {relation.get('source')}->{relation.get('target')} 处理异常: {e!s}"
                    )
                    errors.append(error_msg)
                    logger.warning(error_msg)

        logger.info(f"📊 关系导入完成: 成功 {success_count}, 失败 {failed_count}")

        return {"success_count": success_count, "failed_count": failed_count, "errors": errors}

    async def query_graph(self, query: str) -> list[dict[str, Any]]:
        """
        执行图查询 (TD-001: 执行Cypher查询)

        Args:
            query: Cypher查询语句

        Returns:
            查询结果
        """
        if not self.driver:
            await self.connect()

        with self.driver.session(database=self.database) as session:
            result = session.run(query)

            # 格式化结果
            results = []
            for record in result:
                row = dict(record)
                results.append(row)

            return results


# ========== 兼容层: 保持与旧API的兼容性 ==========

# 导入旧名称以保持向后兼容
KnowledgeGraphImporter = Neo4jKnowledgeGraphImporter


async def main():
    """测试知识图谱导入"""
    # 读取之前生成的图谱数据
    graph_data_file = Path("./data/legal_books/yianshuofa/knowledge_graph_20250106_xxxxxx.json")

    if not graph_data_file.exists():
        print("❌ 知识图谱文件不存在,请先运行 legal_book_pipeline.py")
        return

    with open(graph_data_file, encoding="utf-8") as f:
        graph_data = json.load(f)

    # 配置导入器 (TD-001: 使用Neo4j配置)
    config = {
        "uri": "bolt://127.0.0.1:7687",
        "database": "legal_books_yianshuofa",
        "username": "neo4j",
        "password": config.get("NEO4J_PASSWORD", "password"),
    }

    # 创建并执行导入
    importer = Neo4jKnowledgeGraphImporter(config)
    result = await importer.import_knowledge_graph(graph_data)

    print("\n" + "=" * 50)
    print("🕸️ Neo4j知识图谱导入完成!")
    print("=" * 50)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    print("=" * 80)
    print("🧪 Neo4j知识图谱导入器测试 v3.0.0")
    print("=" * 80)
    print()

    print("TD-001迁移说明:")
    print("- 替换NebulaGraph为Neo4j")
    print("- ConnectionPool → GraphDatabase.driver")
    print("- CREATE SPACE/TAG/EDGE → CREATE CONSTRAINT")
    print("- INSERT VERTEX/EDGE → MERGE (node/relationship)")
    print("- nGQL → Cypher")
    print()
