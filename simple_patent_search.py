#!/usr/bin/env python3
"""
简化版专利检索器 - 使用LIKE查询
"""
import asyncio
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

import psycopg2
from psycopg2.extras import RealDictCursor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SimplePatentResult:
    """简单专利检索结果"""
    patent_id: str
    title: str
    abstract: str
    score: float
    source: str = "simple_fulltext"


class SimplePatentRetriever:
    """简化版专利检索器 - 使用LIKE查询"""

    def __init__(self):
        """初始化数据库连接"""
        self.conn = psycopg2.connect(
            host='localhost',
            port=15432,
            database='athena',
            user='athena',
            password='athena_password_change_me'
        )
        logger.info("✅ 数据库连接成功")

    async def search(self, query: str, top_k: int = 20) -> List[SimplePatentResult]:
        """
        使用LIKE查询检索专利

        Args:
            query: 查询关键词
            top_k: 返回结果数量

        Returns:
            检索结果列表
        """
        logger.info(f"🔍 开始检索: {query}")

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 使用LIKE查询在title和abstract中搜索
                sql = """
                SELECT
                    patent_id,
                    title,
                    abstract,
                    applicant,
                    publication_date,
                    CASE
                        WHEN title LIKE %s THEN 1.0
                        WHEN abstract LIKE %s THEN 0.7
                        ELSE 0.5
                    END as score
                FROM patents
                WHERE title LIKE %s OR abstract LIKE %s
                ORDER BY
                    score DESC,
                    publication_date DESC
                LIMIT %s;
                """

                like_pattern = f"%{query}%"
                cur.execute(sql, (like_pattern, like_pattern, like_pattern, like_pattern, top_k))
                rows = cur.fetchall()

                results = []
                for row in rows:
                    results.append(SimplePatentResult(
                        patent_id=row['patent_id'],
                        title=row['title'],
                        abstract=row['abstract'] or "",
                        score=float(row['score']),
                        source="simple_fulltext"
                    ))

                logger.info(f"✅ 检索完成，找到 {len(results)} 条结果")
                return results

        except Exception as e:
            logger.error(f"❌ 检索失败: {e}")
            return []

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            logger.info("✅ 数据库连接已关闭")


async def main():
    """测试检索器"""
    retriever = SimplePatentRetriever()

    # 测试检索
    queries = ["人工智能", "自动驾驶", "深度学习", "区块链"]

    for query in queries:
        print(f"\n{'='*60}")
        print(f"查询: {query}")
        print('='*60)

        results = await retriever.search(query, top_k=3)

        if results:
            print(f"找到 {len(results)} 条结果:")
            for i, result in enumerate(results, 1):
                print(f"\n{i}. [{result.patent_id}] {result.title}")
                print(f"   分数: {result.score}")
                if result.abstract:
                    print(f"   摘要: {result.abstract[:80]}...")
        else:
            print("未找到结果")

    retriever.close()


if __name__ == "__main__":
    asyncio.run(main())
