#!/usr/bin/env python3
"""
增强版专利检索器 - 支持在title、abstract、claims中检索
"""
import asyncio
import logging
from typing import List
from dataclasses import dataclass

import psycopg2
from psycopg2.extras import RealDictCursor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class EnhancedPatentResult:
    """增强版专利检索结果"""
    patent_id: str
    title: str
    abstract: str
    claims: str
    applicant: str
    publication_date: str
    score: float
    matched_fields: List[str]  # 匹配的字段列表
    source: str = "enhanced_fulltext"


class EnhancedPatentRetriever:
    """增强版专利检索器 - 支持多字段检索"""

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

    async def search(
        self,
        query: str,
        top_k: int = 20,
        search_fields: List[str] = None
    ) -> List[EnhancedPatentResult]:
        """
        增强版检索 - 支持在多个字段中检索

        Args:
            query: 查询关键词
            top_k: 返回结果数量
            search_fields: 要搜索的字段列表，默认['title', 'abstract', 'claims']

        Returns:
            检索结果列表
        """
        if search_fields is None:
            search_fields = ['title', 'abstract', 'claims']

        logger.info(f"🔍 开始检索: '{query}' (字段: {', '.join(search_fields)})")

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 构建动态SQL
                like_pattern = f"%{query}%"

                # 构建WHERE子句
                where_clauses = []
                for field in search_fields:
                    where_clauses.append(f"{field} LIKE %s")

                where_sql = " OR ".join(where_clauses)

                # 构建评分逻辑
                score_cases = []
                for i, field in enumerate(search_fields):
                    # title匹配权重最高，abstract次之，claims再次之
                    weight = 1.0 if field == 'title' else (0.7 if field == 'abstract' else 0.5)
                    score_cases.append(f"WHEN {field} LIKE %s THEN {weight}")

                score_sql = " ".join(score_cases)

                # 构建完整SQL
                sql = f"""
                SELECT
                    patent_id,
                    title,
                    abstract,
                    claims,
                    applicant,
                    publication_date,
                    CASE
                        {score_sql}
                        ELSE 0.3
                    END as score
                FROM patents
                WHERE {where_sql}
                ORDER BY
                    score DESC,
                    publication_date DESC
                LIMIT %s;
                """

                # 准备参数
                params = []
                for field in search_fields:
                    params.append(like_pattern)
                for field in search_fields:
                    params.append(like_pattern)
                params.append(top_k)

                # 执行查询
                cur.execute(sql, params)
                rows = cur.fetchall()

                # 构建结果
                results = []
                for row in rows:
                    # 检测哪些字段匹配
                    matched = []
                    query_lower = query.lower()

                    if row['title'] and query_lower in row['title'].lower():
                        matched.append('title')
                    if row['abstract'] and query_lower in row['abstract'].lower():
                        matched.append('abstract')
                    if row['claims'] and query_lower in row['claims'].lower():
                        matched.append('claims')

                    results.append(EnhancedPatentResult(
                        patent_id=row['patent_id'],
                        title=row['title'],
                        abstract=row['abstract'] or "",
                        claims=row['claims'] or "",
                        applicant=row['applicant'] or "",
                        publication_date=str(row['publication_date']) if row['publication_date'] else "",
                        score=float(row['score']),
                        matched_fields=matched,
                        source="enhanced_fulltext"
                    ))

                logger.info(f"✅ 检索完成，找到 {len(results)} 条结果")
                return results

        except Exception as e:
            logger.error(f"❌ 检索失败: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def search_with_highlights(
        self,
        query: str,
        top_k: int = 20
    ) -> List[EnhancedPatentResult]:
        """
        检索并高亮显示匹配内容

        Args:
            query: 查询关键词
            top_k: 返回结果数量

        Returns:
            检索结果列表
        """
        results = await self.search(query, top_k)

        # 高亮处理将在展示时进行
        return results

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            logger.info("✅ 数据库连接已关闭")


async def test_retriever():
    """测试增强版检索器"""
    retriever = EnhancedPatentRetriever()

    print("\n" + "="*80)
    print("🔍 增强版专利检索测试")
    print("="*80)

    # 测试用例
    test_cases = [
        {
            "query": "卷积神经网络",
            "description": "检索权利要求中的技术术语",
            "fields": ["title", "abstract", "claims"]
        },
        {
            "query": "路径规划",
            "description": "检索权利要求中的方法步骤",
            "fields": ["title", "abstract", "claims"]
        },
        {
            "query": "区块链",
            "description": "检索应用领域",
            "fields": ["title", "abstract"]
        },
        {
            "query": "深度学习",
            "description": "检索技术关键词",
            "fields": ["title", "abstract", "claims"]
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"测试 {i}: {test_case['description']}")
        print(f"查询: '{test_case['query']}'")
        print(f"字段: {', '.join(test_case['fields'])}")
        print('='*80)

        results = await retriever.search(
            test_case['query'],
            top_k=3,
            search_fields=test_case['fields']
        )

        if results:
            print(f"\n✅ 找到 {len(results)} 条结果:\n")

            for j, result in enumerate(results, 1):
                print(f"{j}. [{result.patent_id}] {result.title}")
                print(f"   申请人: {result.applicant}")
                print(f"   公开日: {result.publication_date}")
                print(f"   相关度: {result.score:.2f}")
                print(f"   匹配字段: {', '.join(result.matched_fields)}")

                # 显示匹配的内容片段
                query_lower = test_case['query'].lower()

                if 'title' in result.matched_fields:
                    print(f"   📌 标题: {result.title}")

                if 'abstract' in result.matched_fields:
                    # 高亮显示摘要中的匹配部分
                    abstract = result.abstract
                    start = abstract.lower().find(query_lower)
                    if start != -1:
                        end = min(start + 100, len(abstract))
                        preview = "..." + abstract[max(0, start-30):end] + "..."
                        print(f"   📄 摘要匹配: {preview}")

                if 'claims' in result.matched_fields:
                    # 显示权利要求匹配片段
                    claims = result.claims.replace('\n', ' ')
                    start = claims.lower().find(query_lower)
                    if start != -1:
                        end = min(start + 100, len(claims))
                        preview = claims[max(0, start-30):end] + "..."
                        print(f"   ⚖️  权利要求匹配: {preview}")

                print()
        else:
            print("❌ 未找到结果\n")

    retriever.close()
    print("\n" + "="*80)
    print("✅ 测试完成")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_retriever())
