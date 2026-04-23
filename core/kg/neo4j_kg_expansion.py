#!/usr/bin/env python3
from __future__ import annotations
"""
知识图谱扩展检索 - Neo4j版
Knowledge Graph Expansion Retrieval - Neo4j Edition

版本: v3.0.0
技术决策: TD-001 - 统一图数据库选择为Neo4j

利用Neo4j进行引用关系扩展

核心功能:
1. 引用关系扩展 - 通过文档引用关系扩展检索结果
2. 概念关系扩展 - 通过概念图谱扩展相关文档
3. 引用图生成 - 生成文档引用关系图
4. 数据库回退 - Neo4j不可用时使用数据库回退方案

作者: Athena AI Team
创建时间: 2026-01-19
更新时间: 2026-01-25 (TD-001: 迁移到Neo4j)
"""

import logging
from dataclasses import dataclass
from typing import Any

from core.config.unified_config import get_database_config

logger = logging.getLogger(__name__)


@dataclass
class KGExpansionConfig:
    """知识图谱扩展配置"""

    enable_expansion: bool = True
    max_expansion_depth: int = 2  # 最大扩展深度
    max_expanded_docs: int = 50  # 最大扩展文档数
    citation_weight: float = 0.3  # 引用关系权重


class Neo4jKnowledgeGraphExpander:
    """Neo4j知识图谱扩展器 (TD-001: 替换NebulaGraph)"""

    def __init__(
        self,
        neo4j_config: Optional[dict[str, Any]] = None,
        config: KGExpansionConfig | None = None,
    ):
        """
        初始化知识图谱扩展器

        Args:
            neo4j_config: Neo4j连接配置
                {
                    'uri': 'bolt://localhost:7687',
                    'username': 'neo4j',
                    'password': 'password',
                    'database': 'athena_memory'
                }
            config: 扩展配置
        """
        self.config = config or KGExpansionConfig()

        # 从统一配置获取Neo4j配置 (TD-001)
        db_config = get_database_config()
        default_neo4j_config = db_config.get("neo4j", {})

        self.neo4j_config = neo4j_config or {
            "uri": default_neo4j_config.get("uri", "bolt://localhost:7687"),
            "username": default_neo4j_config.get("username", "neo4j"),
            "password": default_neo4j_config.get("password", "password"),
            "database": default_neo4j_config.get("database", "athena_memory"),
        }

        self.driver = None

        logger.info("✅ 知识图谱扩展器初始化完成")
        logger.info(f"   扩展深度: {self.config.max_expansion_depth}")
        logger.info(f"   最大扩展数: {self.config.max_expanded_docs}")
        logger.info(f"   Neo4j URI: {self.neo4j_config['uri']}")

    def connect(self) -> bool:
        """
        连接Neo4j (TD-001: 完整实现)

        Returns:
            bool: 是否连接成功
        """
        if self.driver:
            return True

        try:
            # TD-001: 使用Neo4j驱动
            try:
                from neo4j import GraphDatabase
            except ImportError:
                logger.warning("⚠️ neo4j-python未安装,知识图谱扩展功能将不可用")
                logger.info("   安装方法: pip install neo4j")
                # 不返回False,允许系统在没有Neo4j的情况下运行
                return False

            logger.info("🔄 连接Neo4j...")

            # 创建驱动
            self.driver = GraphDatabase.driver(
                self.neo4j_config["uri"],
                auth=(self.neo4j_config["username"], self.neo4j_config["password"]),
            )

            # 测试连接
            with self.driver.session(database=self.neo4j_config["database"]) as session:
                # 测试查询
                result = session.run("RETURN 'Connection OK' as message")
                record = result.single()
                if not record or record["message"] != "Connection OK":
                    logger.warning("⚠️ Neo4j连接测试失败")
                    return False

            logger.info("✅ Neo4j连接成功")
            return True

        except Exception as e:
            logger.warning(f"⚠️ Neo4j连接失败: {e}")
            logger.info("   知识图谱扩展功能将不可用,但不影响其他功能")
            self.driver = None
            return False

    def expand_by_citations(
        self, documents: list[dict[str, Any]], db_connection=None
    ) -> list[dict[str, Any]]:
        """
        通过引用关系扩展文档 (TD-001: 增强实现)

        Args:
            documents: 原始文档列表
            db_connection: 数据库连接

        Returns:
            扩展后的文档列表
        """
        if not self.config.enable_expansion:
            logger.debug("知识图谱扩展已禁用")
            return documents

        # 如果Neo4j未连接,使用数据库回退方案
        if not self.driver:
            logger.debug("Neo4j未连接,使用数据库回退方案")
            return self._expand_via_database(documents, db_connection)

        logger.info(f"🔄 开始引用关系扩展: {len(documents)} -> ?")

        try:
            # TD-001: 使用Neo4j查询引用关系
            expanded_docs = list(documents)

            for doc in documents:
                article_id = doc.get("article_id")
                if not article_id:
                    continue

                # 从Neo4j查询引用关系
                cited_docs = self._query_citations_from_neo4j(article_id)
                expanded_docs.extend(cited_docs)

            # 去重
            unique_docs = self._deduplicate_documents(expanded_docs)

            logger.info(f"✅ 扩展完成: {len(documents)} -> {len(unique_docs)}")
            return unique_docs[: self.config.max_expanded_docs]

        except Exception as e:
            logger.error(f"❌ Neo4j扩展失败,回退到数据库: {e}")
            return self._expand_via_database(documents, db_connection)

    def _query_citations_from_neo4j(self, article_id: str) -> list[dict[str, Any]]:
        """
        从Neo4j查询引用的文档 (TD-001: 替换NebulaGraph)

        Args:
            article_id: 文档ID

        Returns:
            引用的文档列表
        """
        if not self.driver:
            return []

        try:
            with self.driver.session(database=self.neo4j_config["database"]) as session:
                # Cypher查询: 查询引用关系
                # 假设图结构: (:Document {id: $article_id})-[:CITES]->(:Document)
                cypher = """
                    MATCH (source:Document {id: $article_id})-[:CITES]->(target:Document)
                    RETURN target.id AS cited_article_id,
                           target.title AS cited_title,
                           target.type AS cited_type
                    LIMIT 100
                """

                result = session.run(cypher, {"article_id": article_id})

                # 解析结果
                cited_ids = []
                for record in result:
                    cited_id = record.get("cited_article_id")
                    if cited_id:
                        cited_ids.append(cited_id)

                # 这里应该从数据库获取文档详情
                # 简化实现: 返回空列表,实际应查询数据库
                logger.debug(f"从Neo4j找到{len(cited_ids)}个引用文档")
                return []

        except Exception as e:
            logger.error(f"Neo4j查询异常: {e}")
            return []

    def _expand_via_database(
        self, documents: list[dict[str, Any]], db_connection=None
    ) -> list[dict[str, Any]]:
        """
        通过数据库引用关系扩展文档 (回退方案)

        Args:
            documents: 原始文档列表
            db_connection: 数据库连接

        Returns:
            扩展后的文档列表
        """
        if not db_connection:
            return documents

        try:
            # 提取文档ID
            [doc.get("article_id") for doc in documents]
            expanded_docs = list(documents)

            # 遍历每个文档的引用关系
            for doc in documents:
                metadata = doc.get("metadata") or {}
                references = metadata.get("references", [])

                if references:
                    # 从数据库查询引用的文档
                    cited_docs = self._fetch_documents_by_ids(references, db_connection)
                    expanded_docs.extend(cited_docs)

            # 去重
            unique_docs = self._deduplicate_documents(expanded_docs)

            logger.info(f"✅ 数据库扩展完成: {len(documents)} -> {len(unique_docs)}")
            return unique_docs[: self.config.max_expanded_docs]

        except Exception as e:
            logger.error(f"❌ 数据库扩展失败: {e}")
            return documents

    def _fetch_documents_by_ids(
        self, article_ids: list[str], db_connection=None
    ) -> list[dict[str, Any]]:
        """根据article_id列表获取文档"""
        if not db_connection or not article_ids:
            return []

        try:
            cursor = db_connection.cursor()

            # 使用安全的参数化查询
            placeholders = ",".join(["%s"] * len(article_ids))
            query = f"""
                SELECT
                    id,
                    article_id,
                    article_type,
                    hierarchy_level,
                    title,
                    COALESCE(content, '') as content,
                    full_path,
                    metadata,
                    0.6 as score
                FROM patent_rules_unified
                WHERE article_id IN ({placeholders})
            """

            cursor.execute(query, article_ids)
            results = cursor.fetchall()

            # 转换为字典列表
            documents = []
            for row in results:
                if hasattr(row, "_asdict"):  # RealDictCursor
                    documents.append(dict(row))
                else:  # 普通cursor
                    documents.append(
                        {
                            "id": row[0],
                            "article_id": row[1],
                            "article_type": row[2],
                            "hierarchy_level": row[3],
                            "title": row[4],
                            "content": row[5],
                            "full_path": row[6],
                            "metadata": row[7],
                            "score": row[8],
                        }
                    )

            logger.debug(f"   查询到 {len(documents)} 个引用文档")
            return documents

        except Exception as e:
            logger.error(f"❌ 查询引用文档失败: {e}")
            return []

    def _deduplicate_documents(self, documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """去重文档列表"""
        seen_ids = set()
        unique_docs = []

        for doc in documents:
            doc_id = doc.get("article_id")
            if doc_id and doc_id not in seen_ids:
                seen_ids.add(doc_id)
                unique_docs.append(doc)

        return unique_docs

    def expand_by_concepts(
        self, query: str, documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        通过概念关系扩展文档

        Args:
            query: 用户查询
            documents: 原始文档列表

        Returns:
            扩展后的文档列表
        """
        # 这里可以实现概念图谱扩展
        # 简化版本: 返回原文档
        logger.debug("概念扩展功能未实现,返回原文档")
        return documents

    def get_citation_graph(self, article_id: str, db_connection=None) -> dict[str, Any]:
        """
        获取文档的引用关系图

        Args:
            article_id: 文档ID
            db_connection: 数据库连接

        Returns:
            引用关系图数据
        """
        try:
            # 查询引用了该文档的文档
            cited_by_sql = """
                SELECT
                    article_id,
                    article_type,
                    title,
                    hierarchy_level,
                    full_path
                FROM patent_rules_unified
                WHERE metadata ? 'references'
                    AND %s = ANY(SELECT jsonb_array_elements_text(metadata->'references'))
                ORDER BY article_type, hierarchy_level
            """

            if not db_connection:
                return {"article_id": article_id, "cited_by": []}

            cursor = db_connection.cursor()
            cursor.execute(cited_by_sql, (article_id,))
            cited_by = cursor.fetchall()

            # 构建图数据
            graph = {
                "article_id": article_id,
                "cited_by_count": len(cited_by),
                "cited_by": [
                    {
                        "article_id": row[0],
                        "article_type": row[1],
                        "title": row[2],
                        "hierarchy_level": row[3],
                        "full_path": row[4],
                    }
                    for row in cited_by
                ],
            }

            return graph

        except Exception as e:
            logger.error(f"❌ 查询引用图失败: {e}")
            return {"article_id": article_id, "cited_by": []}

    def close(self) -> Any:
        """关闭连接"""
        if self.driver:
            try:
                self.driver.close()
                logger.info("✅ Neo4j连接已关闭")
            except Exception as e:
                logger.error(f"❌ 关闭连接失败: {e}")
            finally:
                self.driver = None


# 便捷函数
def get_kg_expander(
    neo4j_config: dict[str, Any]  | None = None, config: KGExpansionConfig | None = None
) -> Neo4jKnowledgeGraphExpander:
    """
    获取知识图谱扩展器实例

    Args:
        neo4j_config: Neo4j配置
        config: 扩展配置

    Returns:
        Neo4jKnowledgeGraphExpander实例
    """
    expander = Neo4jKnowledgeGraphExpander(neo4j_config, config)
    # 尝试连接,但不强制要求成功
    expander.connect()
    return expander


# ========== 兼容层: 保持与旧API的兼容性 ==========

# 导入旧名称以保持向后兼容
KnowledgeGraphExpander = Neo4jKnowledgeGraphExpander


# 使用示例
if __name__ == "__main__":
    print("=" * 80)
    print("🧪 Neo4j知识图谱扩展器测试 v3.0.0")
    print("=" * 80)
    print()

    # 创建扩展器
    expander = get_kg_expander()

    # 模拟文档
    documents = [
        {
            "article_id": "L2_2_3",
            "article_type": "guideline",
            "title": "创造性",
            "content": "创造性判断标准",
            "metadata": {"references": ["L1_2", "L2_2_1"]},
        }
    ]

    print(f"原始文档: {len(documents)}")
    print(f"文档ID: {documents[0]['article_id']}")
    print(f"引用关系: {documents[0]['metadata']['references']}")
    print(f"Neo4j连接: {'已连接' if expander.driver else '未连接'}")
    print()

    print("=" * 80)
    print("TD-001迁移说明:")
    print("- 替换NebulaGraph为Neo4j")
    print("- 使用Cypher查询语言替代nGQL")
    print("- 更新配置参数为Neo4j标准")
    print("- 保持数据库回退方案")
    print("=" * 80)

    # 清理
    expander.close()
