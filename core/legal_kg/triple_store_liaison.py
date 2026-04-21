#!/usr/bin/env python3
"""
法律知识三库联动系统 (NebulaGraph版本 - 已废弃)

版本: v3.0.0
技术决策: TD-001 - 统一图数据库选择为Neo4j

⚠️ 迁移说明 ⚠️
此文件使用NebulaGraph实现,推荐迁移到Neo4j版本。
新版本应实现 PostgreSQL + Qdrant + Neo4j 三库联动查询。

Triple Store Liaison System for Legal Knowledge

实现 PostgreSQL + Qdrant + Neo4j 三库联动查询

作者: Athena平台团队
创建时间: 2025-01-06
更新时间: 2026-01-25 (TD-001: 标记为迁移)
"""

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import psycopg2
from nebula3.Config import Config
from nebula3.gclient.net import ConnectionPool
from qdrant_client import QdrantClient


# 配置
POSTGRES_CONFIG = {
    "host": "localhost",
    "port": 15432,  # Docker PostgreSQL映射端口
    "database": "phoenix_prod",
    "user": "phoenix_user",
    "password": "",  # 使用Docker连接
}

QDRANT_CONFIG = {
    "host": "localhost",
    "port": 6333,
}

NEBULA_CONFIG = {
    "host": "127.0.0.1",
    "port": 9669,
    "user": "root",
    "password": "nebula",
    "space": "legal_kg",
}

# 验证space名称(防止nGQL注入)
if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", NEBULA_CONFIG["space"]):
    raise ValueError(f"Invalid space name: {NEBULA_CONFIG['space']}")


@dataclass
class LegalDocument:
    """法律文档统一数据模型"""

    # PostgreSQL数据
    pg_id: int
    title: str
    category: str
    content: str
    file_path: str

    # Qdrant数据
    vector_id: int | None = None
    similarity: float | None = None

    # NebulaGraph数据
    graph_entities: list[dict] | None = None
    graph_relations: list[dict] | None = None

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "pg_id": self.pg_id,
            "title": self.title,
            "category": self.category,
            "content": self.content,
            "file_path": self.file_path,
            "vector_id": self.vector_id,
            "similarity": self.similarity,
            "graph_entities": self.graph_entities,
            "graph_relations": self.graph_relations,
        }


class LegalTripleStoreLiaison:
    """法律知识三库联动系统"""

    def __init__(self):
        """初始化三库连接"""
        # PostgreSQL连接
        self.pg_conn = psycopg2.connect(**POSTGRES_CONFIG)

        # Qdrant连接
        self.qdrant = QdrantClient(**QDRANT_CONFIG, check_compatibility=False)

        # NebulaGraph连接
        config = Config()
        config.max_connection_pool_size = 10
        self.nebula_pool = ConnectionPool()
        self.nebula_pool.init([(NEBULA_CONFIG["host"], NEBULA_CONFIG["port"])], config)
        self.nebula_session = self.nebula_pool.get_session(
            NEBULA_CONFIG["user"], NEBULA_CONFIG["password"]
        )

        print("✅ 三库连接初始化完成")

    def close(self) -> Any:
        """关闭所有连接"""
        self.pg_conn.close()
        self.nebula_session.release()
        self.nebula_pool.close()
        print("✅ 所有连接已关闭")

    # ==================== PostgreSQL操作 ====================

    def search_postgres(self, query: str, limit: int = 10) -> list[dict]:
        """在PostgreSQL中搜索法律文档"""
        cursor = self.pg_conn.cursor()

        # 全文搜索
        sql = """
            SELECT
                id, title, category, subcategory,
                left(content, 500) as content_preview,
                file_path
            FROM legal_documents
            WHERE
                title ILIKE %s OR
                content ILIKE %s OR
                category ILIKE %s
            ORDER BY
                CASE
                    WHEN title ILIKE %s THEN 1
                    ELSE 2
                END
            LIMIT %s
        """

        search_pattern = f"%{query}%"
        cursor.execute(sql, (search_pattern, search_pattern, search_pattern, search_pattern, limit))
        results = cursor.fetchall()

        documents = []
        for row in results:
            documents.append(
                {
                    "pg_id": row[0],
                    "title": row[1],
                    "category": row[2],
                    "content": row[4],
                    "file_path": row[5],
                    "source": "postgresql",
                }
            )

        cursor.close()
        return documents

    def get_document_by_id(self, doc_id: int) -> dict | None:
        """根据ID获取文档"""
        cursor = self.pg_conn.cursor()

        sql = """
            SELECT id, title, category, subcategory, content, file_path
            FROM legal_documents
            WHERE id = %s
        """

        cursor.execute(sql, (doc_id,))
        row = cursor.fetchone()
        cursor.close()

        if row:
            return {
                "pg_id": row[0],
                "title": row[1],
                "category": row[2],
                "content": row[4],
                "file_path": row[5],
            }
        return None

    # ==================== Qdrant操作 ====================

    def search_vectors(self, query_text: str, limit: int = 10) -> list[dict]:
        """在Qdrant中进行向量搜索"""
        from sentence_transformers import SentenceTransformer

        # 加载模型
        model_path = "http://127.0.0.1:8766/v1/embeddings"
        model = SentenceTransformer(model_path, device="mps")

        # 生成查询向量
        query_vector = model.encode([query_text], normalize_embeddings=True)[0]

        # 搜索
        search_result = self.qdrant.search(
            collection_name="legal_high_quality_v2", query_vector=query_vector.tolist(), limit=limit
        )

        results = []
        for hit in search_result:
            results.append(
                {
                    "vector_id": hit.id,
                    "similarity": hit.score,
                    "payload": hit.payload,
                    "source": "qdrant",
                }
            )

        return results

    # ==================== NebulaGraph操作 ====================

    def search_knowledge_graph(self, keyword: str, limit: int = 10) -> dict:
        """在知识图谱中搜索"""
        # space名称已验证安全
        self.nebula_session.execute(f"USE {NEBULA_CONFIG['space']}")

        # 转义keyword,防止nGQL注入
        escaped_keyword = keyword.replace("\\", "\\\\").replace('"', '\\"')

        # 查找相关法律
        query = f"""
            MATCH (v:law)
            WHERE v.law.name CONTAINS "{escaped_keyword}"
            RETURN v
            LIMIT {limit}
        """
        result = self.nebula_session.execute(query)

        laws = []
        if result.is_succeeded():
            for record in result:
                laws.append(record.values()[0].as_node())

        # 查找相关条文
        query = f"""
            MATCH (v:article)
            WHERE v.article.title CONTAINS "{keyword}" OR v.article.content CONTAINS "{keyword}"
            RETURN v
            LIMIT {limit}
        """
        result = self.nebula_session.execute(query)

        articles = []
        if result.is_succeeded():
            for record in result:
                articles.append(record.values()[0].as_node())

        # 查找相关概念
        query = f"""
            MATCH (v:concept)
            WHERE v.concept.name CONTAINS "{keyword}"
            RETURN v
            LIMIT {limit}
        """
        result = self.nebula_session.execute(query)

        concepts = []
        if result.is_succeeded():
            for record in result:
                concepts.append(record.values()[0].as_node())

        return {"laws": laws, "articles": articles, "concepts": concepts, "source": "nebulagraph"}

    def get_article_relations(self, law_id: str) -> list[dict]:
        """获取条文的关系"""
        # space名称已验证安全
        self.nebula_session.execute(f"USE {NEBULA_CONFIG['space']}")

        # 转义law_id,防止nGQL注入
        escaped_law_id = law_id.replace("\\", "\\\\").replace('"', '\\"')

        query = f"""
            MATCH (a:article {{law_id: "{escaped_law_id}"}})-[r]->(b)
            RETURN a, type(r) as relation_type, b
            LIMIT 50
        """
        result = self.nebula_session.execute(query)

        relations = []
        if result.is_succeeded():
            for record in result:
                relations.append(
                    {
                        "from": record.values()[0].as_node(),
                        "relation": record.values()[1],
                        "to": record.values()[2].as_node(),
                    }
                )

        return relations

    # ==================== 三库联动查询 ====================

    def unified_search(self, query: str, limit: int = 10) -> dict[str, Any]:
        """
        统一搜索 - 三库联动

        返回结构:
        {
            'query': '查询文本',
            'postgresql': [PostgreSQL结果],
            'qdrant': [Qdrant结果],
            'nebulagraph': [NebulaGraph结果],
            'fused': [融合后的结果]
        }
        """
        results = {"query": query, "postgresql": [], "qdrant": [], "nebulagraph": [], "fused": []}

        # 1. PostgreSQL全文搜索
        print("🔍 PostgreSQL全文搜索...")
        pg_results = self.search_postgres(query, limit)
        results["postgresql"] = pg_results
        print(f"   找到 {len(pg_results)} 个结果")

        # 2. Qdrant向量搜索
        print("🔍 Qdrant向量搜索...")
        qdrant_results = self.search_vectors(query, limit)
        results["qdrant"] = qdrant_results
        print(f"   找到 {len(qdrant_results)} 个结果")

        # 3. NebulaGraph知识图谱搜索
        print("🔍 NebulaGraph知识图谱搜索...")
        kg_results = self.search_knowledge_graph(query, limit)
        results["nebulagraph"] = kg_results
        print(
            f"   找到法律: {len(kg_results['laws'])}, 条文: {len(kg_results['articles'])}, 概念: {len(kg_results['concepts'])}"
        )

        # 4. 结果融合
        results["fused"] = self._fuse_results(results)

        return results

    def _fuse_results(self, raw_results: dict) -> list[LegalDocument]:
        """融合三库结果"""

        # 创建文档映射表(按标题)
        doc_map = {}

        # 添加PostgreSQL结果
        for pg_doc in raw_results["postgresql"]:
            title = pg_doc["title"]
            if title not in doc_map:
                doc_map[title] = LegalDocument(
                    pg_id=pg_doc["pg_id"],
                    title=pg_doc["title"],
                    category=pg_doc["category"],
                    content=pg_doc["content"],
                    file_path=pg_doc["file_path"],
                )

        # 添加Qdrant结果
        for qdrant_doc in raw_results["qdrant"]:
            title = qdrant_doc["payload"]["title"]
            if title in doc_map:
                doc_map[title].vector_id = qdrant_doc["vector_id"]
                doc_map[title].similarity = qdrant_doc["similarity"]
            else:
                doc_map[title] = LegalDocument(
                    pg_id=None,
                    title=title,
                    category="",
                    content=qdrant_doc["payload"]["text"],
                    file_path="",
                    vector_id=qdrant_doc["vector_id"],
                    similarity=qdrant_doc["similarity"],
                )

        # 添加NebulaGraph结果
        for law in raw_results["nebulagraph"]["laws"]:
            title = law.get("name", "")
            if title and title in doc_map:
                doc_map[title].graph_entities = [law]

        # 按相似度排序
        sorted_docs = sorted(
            doc_map.values(), key=lambda x: x.similarity if x.similarity else 0, reverse=True
        )

        return sorted_docs[:10]

    # ==================== 数据导入 ====================

    def sync_vector_to_postgres(self) -> Any:
        """将Qdrant向量数据同步到PostgreSQL"""
        cursor = self.pg_conn.cursor()

        # 创建向量映射表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS legal_vector_mappings (
                id SERIAL PRIMARY KEY,
                law_id VARCHAR(100),
                element_id VARCHAR(200) UNIQUE,
                vector_id BIGINT,
                element_type VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 从Qdrant获取所有向量
        self.qdrant.get_collection("legal_high_quality_v2")

        # 分批获取
        batch_size = 100
        current_offset = None
        while True:
            records, next_offset = self.qdrant.scroll(
                collection_name="legal_high_quality_v2", limit=batch_size, offset=current_offset
            )

            if not records:
                break

            for record in records:
                law_id = record.payload.get("law_id", "")
                element_id = record.payload.get("element_id", "")
                element_type = record.payload.get("element_type", "")

                cursor.execute(
                    """
                    INSERT INTO legal_vector_mappings (law_id, element_id, vector_id, element_type)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (element_id) DO UPDATE SET
                        vector_id = EXCLUDED.vector_id,
                        law_id = EXCLUDED.law_id
                """,
                    (law_id, element_id, record.id, element_type),
                )

            self.pg_conn.commit()
            synced_count = sum(1 for _ in records)
            print(f"   同步批次: {synced_count} 条记录")

            if next_offset is None:
                break
            current_offset = next_offset

        cursor.close()
        print("✅ 向量数据同步完成")

    def sync_graph_to_postgres(self) -> Any:
        """将NebulaGraph数据同步到PostgreSQL"""
        cursor = self.pg_conn.cursor()

        # 创建图映射表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS legal_graph_mappings (
                id SERIAL PRIMARY KEY,
                law_id VARCHAR(100),
                graph_vertex_id VARCHAR(100) UNIQUE,
                vertex_type VARCHAR(50),
                properties JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # space名称已验证安全
        self.nebula_session.execute(f"USE {NEBULA_CONFIG['space']}")

        # 获取所有法律节点
        result = self.nebula_session.execute("MATCH (v:law) RETURN v")
        if result.is_succeeded():
            for record in result:
                node = record.values()[0].as_node()
                law_id = node.get("law_id", "")
                vertex_id = node.get_id().hex()

                cursor.execute(
                    """
                    INSERT INTO legal_graph_mappings (law_id, graph_vertex_id, vertex_type, properties)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (graph_vertex_id) DO UPDATE SET
                        law_id = EXCLUDED.law_id,
                        properties = EXCLUDED.properties
                """,
                    (law_id, vertex_id, "law", json.dumps(dict(node))),
                )

        self.pg_conn.commit()
        cursor.close()
        print("✅ 知识图谱数据同步完成")


def main() -> None:
    """测试三库联动"""
    print("\n" + "=" * 70)
    print("🔗 法律知识三库联动系统")
    print("=" * 70 + "\n")

    # 初始化
    liaison = LegalTripleStoreLiaison()

    try:
        # 同步数据
        print("\n📊 同步数据到PostgreSQL...")
        liaison.sync_vector_to_postgres()
        liaison.sync_graph_to_postgres()

        # 测试查询
        print("\n🔍 测试统一查询...")
        query = "知识产权保护"
        results = liaison.unified_search(query, limit=5)

        print(f"\n查询: {query}")
        print(f"PostgreSQL结果: {len(results['postgresql'])} 条")
        print(f"Qdrant结果: {len(results['qdrant'])} 条")
        print(f"融合结果: {len(results['fused'])} 条")

        # 显示融合结果
        print("\n📋 融合结果:")
        for i, doc in enumerate(results["fused"][:3], 1):
            print(f"\n{i}. {doc.title}")
            print(f"   分类: {doc.category}")
            print(f"   相似度: {doc.similarity:.4f}" if doc.similarity else "")
            print(f"   内容: {doc.content[:100]}...")

    finally:
        liaison.close()

    print("\n" + "=" * 70)
    print("✅ 测试完成")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
