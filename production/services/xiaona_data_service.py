#!/usr/bin/env python3
"""
小娜数据源集成服务
集成Qdrant向量库、PostgreSQL数据库
（已移除NebulaGraph，平台使用Neo4j作为图数据库）
"""

from __future__ import annotations
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class SearchResult:
    """搜索结果"""
    content: str
    source: str
    score: float
    metadata: dict[str, Any]


class XiaonaDataService:
    """小娜数据源集成服务"""

    def __init__(self,
                 qdrant_host: str = None,
                 qdrant_port: int = 6333,
                 db_host: str = None,
                 db_port: int = 5432,
                 db_name: str = "patent_db",
                 db_user: str = "postgres",
                 db_password: str = None):
        """
        初始化数据服务

        Args:
            qdrant_host: Qdrant主机
            qdrant_port: Qdrant端口
            db_host: PostgreSQL主机
            db_port: PostgreSQL端口
            db_name: 数据库名
            db_user: 数据库用户
            db_password: 数据库密码
        """
        self.qdrant_config = {
            "host": qdrant_host or "localhost",
            "port": qdrant_port,
            "collections": {
                "patent_rules": "patent_rules_complete",
                "patent_decisions": "patent_decisions",
                "laws_articles": "laws_articles",
                "patent_guidelines": "patent_guidelines"
            }
        }

        self.db_config = {
            "host": db_host or "localhost",
            "port": db_port,
            "database": db_name,
            "user": db_user,
            "password": db_password
        }

        # 初始化客户端
        self.qdrant_client = None
        self.db_pool = None

        # 日志
        self.logger = logging.getLogger(__name__)

        # 统计
        self.stats = {
            "qdrant_searches": 0,
            "db_queries": 0,
            "total_results": 0
        }

    def initialize(self) -> Any:
        """初始化所有数据源连接"""
        self.logger.info("初始化小娜数据源...")

        # 初始化Qdrant
        try:
            from qdrant_client import QdrantClient
            self.qdrant_client = QdrantClient(
                host=self.qdrant_config["host"],
                port=self.qdrant_config["port"]
            )
            self.logger.info("✅ Qdrant连接成功")
        except Exception as e:
            self.logger.warning(f"⚠️ Qdrant连接失败: {e}")

        # 初始化PostgreSQL
        try:
            import psycopg2

            self.db_pool = psycopg2.pool.SimpleConnectionPool(
                1, 20,
                host=self.db_config["host"],
                port=self.db_config["port"],
                database=self.db_config["database"],
                user=self.db_config["user"],
                password=self.db_config["password"]
            )
            self.logger.info("✅ PostgreSQL连接成功")
        except Exception as e:
            self.logger.warning(f"⚠️ PostgreSQL连接失败: {e}")

    def search_patent_rules(self,
                            query: str,
                            limit: int = 5,
                            threshold: float = 0.75) -> list[SearchResult]:
        """
        搜索专利法条

        Args:
            query: 查询文本
            limit: 返回数量
            threshold: 相似度阈值

        Returns:
            搜索结果列表
        """
        if not self.qdrant_client:
            self.logger.warning("Qdrant客户端未初始化")
            return []

        self.stats["qdrant_searches"] += 1

        try:

            # 这里应该是实际的向量搜索
            # 简化实现: 模拟返回
            results = [
                SearchResult(
                    content="《专利法》第22条第3款: 创造性...",
                    source="patent_rules_complete",
                    score=0.95,
                    metadata={"law_id": "A22.3", "name": "专利法第22条第3款"}
                ),
                SearchResult(
                    content="《专利法实施细则》第20条第1款...",
                    source="patent_rules_complete",
                    score=0.87,
                    metadata={"law_id": "R20.1", "name": "实施细则第20条第1款"}
                )
            ]

            self.stats["total_results"] += len(results)
            return results

        except Exception as e:
            self.logger.error(f"专利法条搜索失败: {e}")
            return []

    def search_patent_decisions(self,
                                query: str,
                                limit: int = 5) -> list[SearchResult]:
        """
        搜索复审无效决定书

        Args:
            query: 查询文本
            limit: 返回数量

        Returns:
            搜索结果列表
        """
        if not self.qdrant_client:
            return []

        self.stats["qdrant_searches"] += 1

        try:
            # 模拟返回
            results = [
                SearchResult(
                    content="决定书#5W123456: 针对专利号CNXXXXXXX的无效宣告请求...",
                    source="patent_decisions",
                    score=0.88,
                    metadata={"decision_id": "5W123456", "date": "2023-06-15"}
                )
            ]

            self.stats["total_results"] += len(results)
            return results

        except Exception as e:
            self.logger.error(f"决定书搜索失败: {e}")
            return []

    def query_law_relations(self,
                           law_id: str) -> dict[str, Any]:
        """
        查询法条关联关系

        Args:
            law_id: 法条ID (如 "A22.3")

        Returns:
            关联关系数据
        """
        try:
            # 模拟返回 (实际应从Neo4j图数据库查询)
            return {
                "law_id": law_id,
                "upper_law": "专利法第22条",
                "related_laws": ["实施细则第20条", "审查指南第2章第4节"],
                "cited_cases": ["5W123456", "4W234567"]
            }
        except Exception as e:
            self.logger.error(f"法条关联查询失败: {e}")
            return {}

    def search_patents(self,
                      query: str,
                      limit: int = 10) -> list[dict[str, Any]]:
        """
        搜索专利

        Args:
            query: 搜索关键词
            limit: 返回数量

        Returns:
            专利列表
        """
        if not self.db_pool:
            return []

        self.stats["db_queries"] += 1

        try:
            conn = self.db_pool.getconn()
            cursor = conn.cursor()

            # 简化实现
            cursor.execute("""
                SELECT publication_number, title, abstract, application_date
                FROM patents
                WHERE title ILIKE %s OR abstract ILIKE %s
                LIMIT %s
            """, (f"%{query}%", f"%{query}%", limit))

            results = []
            for row in cursor.fetchall():
                results.append({
                    "publication_number": row[0],
                    "title": row[1],
                    "abstract": row[2],
                    "application_date": str(row[3])
                })

            cursor.close()
            self.db_pool.putconn(conn)

            self.stats["total_results"] += len(results)
            return results

        except Exception as e:
            self.logger.error(f"专利搜索失败: {e}")
            return []

    def get_comprehensive_search(self,
                                 query: str,
                                 search_laws: bool = True,
                                 search_cases: bool = True,
                                 search_patents: bool = False) -> dict[str, Any]:
        """
        综合搜索

        Args:
            query: 查询文本
            search_laws: 是否搜索法条
            search_cases: 是否搜索案例
            search_patents: 是否搜索专利

        Returns:
            综合搜索结果
        """
        results = {
            "query": query,
            "laws": [],
            "cases": [],
            "patents": [],
            "timestamp": datetime.now().isoformat()
        }

        if search_laws:
            results["laws"] = self.search_patent_rules(query)

        if search_cases:
            results["cases"] = self.search_patent_decisions(query)

        if search_patents:
            results["patents"] = self.search_patents(query)

        # 为法条添加关联关系
        for law_result in results["laws"]:
            law_id = law_result.metadata.get("law_id")
            if law_id:
                law_result.metadata["relations"] = self.query_law_relations(law_id)

        return results

    def health_check(self) -> dict[str, bool]:
        """健康检查"""
        return {
            "qdrant_available": self.qdrant_client is not None,
            "postgres_available": self.db_pool is not None
        }

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()

    def close(self) -> Any:
        """关闭所有连接"""
        if self.db_pool:
            self.db_pool.closeall()
            self.logger.info("PostgreSQL连接池已关闭")


def main() -> None:
    """测试数据服务"""
    print("=" * 60)
    print("小娜数据服务测试")
    print("=" * 60)

    # 初始化服务
    service = XiaonaDataService()
    service.initialize()

    # 健康检查
    print("\n🔍 健康检查:")
    health = service.health_check()
    for key, value in health.items():
        status = "✅" if value else "❌"
        print(f"  {status} {key}: {value}")

    # 测试综合搜索
    print("\n🧪 测试综合搜索:")
    results = service.get_comprehensive_search(
        query="专利创造性",
        search_laws=True,
        search_cases=True
    )

    print(f"  法条结果: {len(results['laws'])} 条")
    print(f"  案例结果: {len(results['cases'])} 条")

    # 统计
    print("\n📊 统计信息:")
    stats = service.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    service.close()


if __name__ == "__main__":
    main()
