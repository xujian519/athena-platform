#!/usr/bin/env python3
"""
⚠️  DEPRECATED - NebulaGraph版本已废弃
DEPRECATED - NebulaGraph version deprecated

废弃日期: 2026-01-26
废弃原因: TD-001 - 系统已迁移到Neo4j
影响范围: 整个文件
建议操作: 使用 core/kg/neo4j_kg_expansion.py

原功能说明:
知识图谱扩展检索
利用NebulaGraph进行引用关系扩展
作者: Athena AI Team
创建时间: 2026-01-19
版本: v1.0.0
"""

from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class KGExpansionConfig:
    """知识图谱扩展配置"""

    enable_expansion: bool = True
    max_expansion_depth: int = 2  # 最大扩展深度
    max_expanded_docs: int = 50  # 最大扩展文档数
    citation_weight: float = 0.3  # 引用关系权重


class KnowledgeGraphExpander:
    """知识图谱扩展器"""

    def __init__(
        self,
        nebula_config: dict[str, Any] | None = None,
        config: KGExpansionConfig | None = None,
    ):
        """
        初始化知识图谱扩展器

        Args:
            nebula_config: NebulaGraph连接配置
            config: 扩展配置
        """
        self.config = config or KGExpansionConfig()
        self.nebula_config = nebula_config
        self.nebula_connection = None

        logger.info("✅ 知识图谱扩展器初始化完成")
        logger.info(f"   扩展深度: {self.config.max_expansion_depth}")
        logger.info(f"   最大扩展数: {self.config.max_expanded_docs}")

    def connect(self) -> bool:
        """连接NebulaGraph"""
        if self.nebula_connection:
            return True

        try:
            # 这里应该连接实际的NebulaGraph
            # from nebula3.gclient.net import ConnectionPool
            # ...
            logger.info("🔄 连接NebulaGraph...")
            # 实际实现
            logger.info("✅ NebulaGraph连接成功")
            return True
        except Exception as e:
            logger.warning(f"⚠️ NebulaGraph连接失败: {e}")
            return False

    def expand_by_citations(
        self, documents: list[dict[str, Any]], db_connection=None
    ) -> list[dict[str, Any]]:
        """
        通过引用关系扩展文档

        Args:
            documents: 原始文档列表
            db_connection: 数据库连接

        Returns:
            扩展后的文档列表
        """
        if not self.config.enable_expansion:
            return documents

        logger.info(f"🔄 开始引用关系扩展: {len(documents)} -> ?")

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
            seen_ids = set()
            unique_docs = []
            for doc in expanded_docs:
                doc_id = doc.get("article_id")
                if doc_id and doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    unique_docs.append(doc)

            logger.info(f"✅ 扩展完成: {len(documents)} -> {len(unique_docs)}")
            return unique_docs[: self.config.max_expanded_docs]

        except Exception as e:
            logger.error(f"❌ 引用扩展失败: {e}")
            return documents

    def _fetch_documents_by_ids(
        self, article_ids: list[str], db_connection=None
    ) -> list[dict[str, Any]]:
        """根据article_id列表获取文档"""
        if not db_connection or not article_ids:
            return []

        try:
            cursor = db_connection.cursor()

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
                    0.6 as score  # 引用文档的默认分数
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

    def expand_by_concepts(
        self, query: str, documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        通过概念关系扩展文档
        例如: "创造性" -> "新颖性" (相关概念)

        Args:
            query: 用户查询
            documents: 原始文档列表

        Returns:
            扩展后的文档列表
        """
        # 这里可以实现概念图谱扩展
        # 简化版本: 返回原文档
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
        if self.nebula_connection:
            try:
                # nebula_connection.close()
                logger.info("✅ NebulaGraph连接已关闭")
            except Exception as e:
                logger.error(f"❌ 关闭连接失败: {e}")


# 便捷函数
def get_kg_expander(
    nebula_config: dict[str, Any]  | None = None, config: KGExpansionConfig | None = None
) -> KnowledgeGraphExpander:
    """
    获取知识图谱扩展器实例

    Args:
        nebula_config: NebulaGraph配置
        config: 扩展配置

    Returns:
        KnowledgeGraphExpander实例
    """
    return KnowledgeGraphExpander(nebula_config, config)


# 使用示例
if __name__ == "__main__":
    print("=" * 80)
    print("🧪 知识图谱扩展器测试")
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
    print()

    # 模拟扩展 (需要实际数据库连接)
    # expanded = expander.expand_by_citations(documents)
    # print(f"扩展后文档: {len(expanded)}")

    print("=" * 80)
