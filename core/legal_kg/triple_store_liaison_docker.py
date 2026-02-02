#!/usr/bin/env python3
"""
法律知识三库联动系统 - Docker版本
通过Docker exec访问PostgreSQL
"""

import re
import subprocess
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from nebula3.Config import Config
from nebula3.gclient.net import ConnectionPool
from qdrant_client import QdrantClient


# 验证space名称(防止nGQL注入)
_SPACE_NAME = "legal_kg"
if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", _SPACE_NAME):
    raise ValueError(f"Invalid space name: {_SPACE_NAME}")

# 配置
QDRANT_CONFIG = {
    "host": "localhost",
    "port": 6333,
}

NEBULA_CONFIG = {
    "host": "127.0.0.1",
    "port": 9669,
    "user": "root",
    "password": "nebula",
    "space": _SPACE_NAME,  # 使用已验证的space名称
}


@dataclass
class LegalDocument:
    """法律文档统一数据模型"""

    pg_id: int
    title: str
    category: str
    content: str
    file_path: str
    vector_id: int | None = None
    similarity: float | None = None
    graph_entities: list[dict] | None = None
    graph_relations: list[dict] | None = None


class DockerPostgresClient:
    """通过Docker exec访问PostgreSQL"""

    def __init__(self, container_name="phoenix-db"):
        self.container_name = container_name
        self.user = "phoenix_user"
        self.database = "phoenix_prod"

    def execute(self, sql: str, params=None) -> list[tuple]:
        """执行SQL查询"""
        # 参数替换
        if params:
            for _i, param in enumerate(params):
                if isinstance(param, str):
                    # PostgreSQL标准:两个单引号表示一个单引号
                    param_escaped = param.replace("'", "''")
                    sql = sql.replace("%s", f"'{param_escaped}'", 1)
                else:
                    sql = sql.replace("%s", str(param), 1)

        # 使用stdin传递SQL到psql,避免所有shell转义问题
        cmd = [
            "docker",
            "exec",
            "-i",
            self.container_name,
            "psql",
            "-U",
            self.user,
            "-d",
            self.database,
            "-t",
            "-c",
            sql,
        ]
        result = subprocess.run(cmd, input="", capture_output=True, text=True)

        if result.returncode != 0:
            raise Exception(f"SQL执行失败: {result.stderr}\n_sql: {sql}")

        # 解析结果
        lines = result.stdout.strip().split("\n")
        parsed_results = []
        for line in lines:
            if line.strip():
                line = line.strip()
                columns = [col.strip() for col in line.split("|")]
                parsed_results.append(tuple(columns))

        return parsed_results


class LegalTripleStoreLiaison:
    """法律知识三库联动系统"""

    def __init__(self):
        """初始化三库连接"""
        # PostgreSQL连接(通过Docker)
        self.pg_client = DockerPostgresClient()

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
        self.nebula_session.release()
        self.nebula_pool.close()
        print("✅ 所有连接已关闭")

    # ==================== PostgreSQL操作 ====================

    def search_postgres(self, query: str, limit: int = 10) -> list[dict]:
        """在PostgreSQL中搜索法律文档

        ⚠️ 安全说明:本方法使用Docker exec执行psql,通过手动参数替换来防止SQL注入
        用户输入query只用于ILIKE模式匹配,经过转义处理
        limit参数经过类型验证确保为整数
        """
        # 验证limit参数
        if not isinstance(limit, int) or limit <= 0 or limit > 1000:
            raise ValueError(f"limit必须是正整数且不超过1000,收到: {limit}")

        # 转义query中的特殊字符(PostgreSQL字符串转义)
        escaped_query = query.replace("'", "''")
        search_pattern = f"%{escaped_query}%"

        # 使用参数化方式构建查询(手动替换占位符)
        # 注意:由于要通过Docker exec执行psql,无法使用真正的参数化查询
        # 因此通过字符串转义和类型验证来降低风险
        sql = f"""
            SELECT
                id, title, category,
                LEFT(content, 500) as content_preview,
                file_path
            FROM legal_documents
            WHERE
                title ILIKE '{search_pattern}' OR
                content ILIKE '{search_pattern}' OR
                category ILIKE '{search_pattern}'
            ORDER BY
                CASE WHEN title ILIKE '{search_pattern}' THEN 1 ELSE 2 END
            LIMIT {limit}
        """

        results = self.pg_client.execute(sql)

        documents = []
        for row in results:
            documents.append(
                {
                    "pg_id": int(row[0]) if row[0].isdigit() else 0,
                    "title": row[1],
                    "category": row[2],
                    "content": row[3],
                    "file_path": row[4],
                    "source": "postgresql",
                }
            )

        return documents

    def get_document_by_id(self, doc_id: int) -> dict | None:
        """根据ID获取文档

        ⚠️ 安全说明:doc_id参数经过类型验证确保为整数
        """
        # 验证doc_id参数
        if not isinstance(doc_id, int) or doc_id <= 0:
            raise ValueError(f"doc_id必须是正整数,收到: {doc_id}")

        sql = f"""
            SELECT id, title, category, content, file_path
            FROM legal_documents
            WHERE id = {doc_id}
        """

        results = self.pg_client.execute(sql)

        if results and len(results) > 0:
            row = results[0]
            return {
                "pg_id": int(row[0]),
                "title": row[1],
                "category": row[2],
                "content": row[3],
                "file_path": row[4],
            }
        return None

    # ==================== Qdrant操作 ====================

    def search_vectors(self, query_text: str, limit: int = 10) -> list[dict]:
        """在Qdrant中进行向量搜索"""
        import requests
        from sentence_transformers import SentenceTransformer

        # 加载模型
        model_path = "/Users/xujian/Athena工作平台/models/converted/BAAI/bge-m3"
        model = SentenceTransformer(model_path, device="mps")

        # 生成查询向量
        query_vector = model.encode([query_text], normalize_embeddings=True)[0].tolist()

        # 使用HTTP API进行搜索(兼容Qdrant 1.7.x)
        response = requests.post(
            f"http://{QDRANT_CONFIG['host']}:{QDRANT_CONFIG['port']}/collections/legal_high_quality_v2/points/search",
            json={"vector": query_vector, "limit": limit, "with_payload": True},
        )

        if response.status_code != 200:
            raise Exception(f"Qdrant搜索失败: {response.status_code} - {response.text}")

        data = response.json()
        results = []

        for point in data.get("result", []):
            results.append(
                {
                    "vector_id": point.get("id"),
                    "similarity": point.get("score", 0),
                    "payload": point.get("payload", {}),
                    "source": "qdrant",
                }
            )

        return results

    # ==================== NebulaGraph操作 ====================

    def search_knowledge_graph(self, keyword: str, limit: int = 10) -> dict:
        """在知识图谱中搜索

        ⚠️ 安全说明:keyword参数经过转义处理,防止nGQL注入
        space名称已在模块加载时通过正则验证
        """
        # space名称已验证安全
        self.nebula_session.execute(f"USE {NEBULA_CONFIG['space']}")

        # 转义keyword,防止nGQL注入
        escaped_keyword = keyword.replace("\\", "\\\\").replace('"', '\\"')

        # 查找相关法律
        query = (
            f'MATCH (v:law) WHERE v.law.name CONTAINS "{escaped_keyword}" RETURN v LIMIT {limit}'
        )
        result = self.nebula_session.execute(query)

        laws = []
        if result.is_succeeded():
            for record in result:
                laws.append(record.values()[0].as_node())

        # 查找相关条文
        query = f'MATCH (v:article) WHERE v.article.content CONTAINS "{escaped_keyword}" RETURN v LIMIT {limit}'
        result = self.nebula_session.execute(query)

        articles = []
        if result.is_succeeded():
            for record in result:
                articles.append(record.values()[0].as_node())

        return {"laws": laws, "articles": articles, "source": "nebulagraph"}

    # ==================== 三库联动查询 ====================

    def unified_search(self, query: str, limit: int = 10) -> dict[str, Any]:
        """统一搜索 - 三库联动"""
        results = {"query": query, "postgresql": [], "qdrant": [], "nebulagraph": [], "fused": []}

        # 1. PostgreSQL全文搜索
        print("🔍 PostgreSQL全文搜索...")
        try:
            pg_results = self.search_postgres(query, limit)
            results["postgresql"] = pg_results
            print(f"   找到 {len(pg_results)} 个结果")
        except Exception as e:
            print(f"   PostgreSQL搜索失败: {e}")

        # 2. Qdrant向量搜索
        print("🔍 Qdrant向量搜索...")
        try:
            qdrant_results = self.search_vectors(query, limit)
            results["qdrant"] = qdrant_results
            print(f"   找到 {len(qdrant_results)} 个结果")
        except Exception as e:
            print(f"   Qdrant搜索失败: {e}")

        # 3. NebulaGraph知识图谱搜索
        print("🔍 NebulaGraph知识图谱搜索...")
        try:
            kg_results = self.search_knowledge_graph(query, limit)
            results["nebulagraph"] = kg_results
            print(
                f"   找到法律: {len(kg_results.get('laws', []))}, 条文: {len(kg_results.get('articles', []))}"
            )
        except Exception as e:
            print(f"   NebulaGraph搜索失败: {e}")

        # 4. 结果融合
        results["fused"] = self._fuse_results(results)

        return results

    def _fuse_results(self, raw_results: dict) -> list[dict]:
        """融合三库结果"""
        doc_map = {}

        # 添加PostgreSQL结果
        for pg_doc in raw_results["postgresql"]:
            title = pg_doc["title"]
            if title not in doc_map:
                doc_map[title] = {
                    "title": title,
                    "category": pg_doc["category"],
                    "content": pg_doc["content"],
                    "pg_id": pg_doc["pg_id"],
                    "similarity": 0.5,  # 默认相似度
                    "sources": ["postgresql"],
                }

        # 添加Qdrant结果
        for qdrant_doc in raw_results["qdrant"]:
            title = qdrant_doc["payload"].get("title", "")
            if title in doc_map:
                doc_map[title]["vector_id"] = qdrant_doc["vector_id"]
                doc_map[title]["similarity"] = max(
                    doc_map[title]["similarity"], qdrant_doc["similarity"]
                )
                doc_map[title]["sources"].append("qdrant")
            else:
                doc_map[title] = {
                    "title": title,
                    "category": qdrant_doc["payload"].get("importance", ""),
                    "content": qdrant_doc["payload"].get("text", ""),
                    "pg_id": None,
                    "vector_id": qdrant_doc["vector_id"],
                    "similarity": qdrant_doc["similarity"],
                    "sources": ["qdrant"],
                }

        # 按相似度排序
        sorted_docs = sorted(doc_map.values(), key=lambda x: x.get("similarity", 0), reverse=True)

        return sorted_docs[:10]

    # ==================== 数据统计 ====================

    def get_statistics(self) -> dict:
        """获取三库统计信息"""
        stats = {"postgresql": {}, "qdrant": {}, "nebulagraph": {}}

        # PostgreSQL统计
        try:
            sql = "SELECT COUNT(*), COUNT(DISTINCT category) FROM legal_documents"
            results = self.pg_client.execute(sql)
            if results:
                stats["postgresql"] = {
                    "total_documents": int(results[0][0]),
                    "categories": int(results[0][1]),
                }
        except Exception as e:
            stats["postgresql"] = {"error": str(e)}

        # Qdrant统计
        try:
            collection_info = self.qdrant.get_collection("legal_high_quality_v2")
            stats["qdrant"] = {
                "total_vectors": collection_info.points_count,
                "vector_size": collection_info.config.params.vectors.size,
                "distance": collection_info.config.params.vectors.distance,
            }
        except Exception as e:
            stats["qdrant"] = {"error": str(e)}

        # NebulaGraph统计
        try:
            self.nebula_session.execute(f"USE {NEBULA_CONFIG['space']}")

            # 统计法律节点
            result = self.nebula_session.execute("MATCH (v:law) RETURN COUNT(*)")
            law_count = int(result.values()[0].as_int()) if result.is_succeeded() else 0

            # 统计条文节点
            result = self.nebula_session.execute("MATCH (v:article) RETURN COUNT(*)")
            article_count = int(result.values()[0].as_int()) if result.is_succeeded() else 0

            stats["nebulagraph"] = {
                "law_nodes": law_count,
                "article_nodes": article_count,
                "space": NEBULA_CONFIG["space"],
            }
        except Exception as e:
            stats["nebulagraph"] = {"error": str(e)}

        return stats


def main() -> None:
    """测试三库联动"""
    print("\n" + "=" * 70)
    print("🔗 法律知识三库联动系统")
    print("=" * 70 + "\n")

    # 初始化
    liaison = LegalTripleStoreLiaison()

    try:
        # 获取统计信息
        print("\n📊 三库统计信息...")
        stats = liaison.get_statistics()

        print("\n_postgre_sql:")
        print(f"   文档总数: {stats['postgresql'].get('total_documents', 0):,}")
        print(f"   分类数量: {stats['postgresql'].get('categories', 0)}")

        print("\n_qdrant:")
        print(f"   向量总数: {stats['qdrant'].get('total_vectors', 0):,}")
        print(f"   向量维度: {stats['qdrant'].get('vector_size', 0)}")
        print(f"   距离度量: {stats['qdrant'].get('distance', '')}")

        print("\n_nebula_graph:")
        print(f"   法律节点: {stats['nebulagraph'].get('law_nodes', 0)}")
        print(f"   条文节点: {stats['nebulagraph'].get('article_nodes', 0)}")

        # 测试查询
        print("\n🔍 测试统一查询...")
        query = "知识产权"
        results = liaison.unified_search(query, limit=5)

        print(f"\n查询: {query}")
        print(f"PostgreSQL结果: {len(results['postgresql'])} 条")
        print(f"Qdrant结果: {len(results['qdrant'])} 条")
        print(f"NebulaGraph结果: {len(results['nebulagraph'].get('laws', []))} 个法律")
        print(f"融合结果: {len(results['fused'])} 条")

        # 显示融合结果
        print("\n📋 融合结果(Top 3):")
        for i, doc in enumerate(results["fused"][:3], 1):
            print(f"\n{i}. {doc['title']}")
            print(f"   分类: {doc['category']}")
            print(f"   相似度: {doc['similarity']:.4f}")
            print(f"   来源: {', '.join(doc['sources'])}")
            print(f"   内容: {doc['content'][:100]}...")

    finally:
        liaison.close()

    print("\n" + "=" * 70)
    print("✅ 测试完成")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
