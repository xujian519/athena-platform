#!/usr/bin/env python3
"""
高级专利检索器 - 支持多条件过滤
"""
import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any

import psycopg2
from psycopg2.extras import RealDictCursor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SearchFilter:
    """搜索过滤器"""
    # IPC分类号过滤
    ipc_codes: Optional[List[str]] = None
    ipc_mode: str = "any"  # "any" (任一匹配) 或 "all" (全部匹配)

    # 申请人过滤
    assignees: Optional[List[str]] = None
    assignee_mode: str = "any"

    # 发明人过滤
    inventors: Optional[List[str]] = None

    # 日期范围过滤
    publication_date_start: Optional[str] = None  # YYYY-MM-DD
    publication_date_end: Optional[str] = None

    # 状态过滤
    status: Optional[str] = None  # "granted", "pending", "all"

    # 排序选项
    sort_by: str = "relevance"  # "relevance", "date", "patent_id"
    sort_order: str = "desc"  # "desc", "asc"


@dataclass
class AdvancedPatentResult:
    """高级专利检索结果"""
    patent_id: str
    title: str
    abstract: str
    claims: str
    applicant: str
    inventor: str
    publication_date: str
    ipc_codes: str
    status: str
    score: float
    matched_fields: List[str] = field(default_factory=list)
    matched_filters: Dict[str, Any] = field(default_factory=dict)
    source: str = "advanced_search"


class AdvancedPatentRetriever:
    """高级专利检索器 - 支持多条件过滤"""

    def __init__(self):
        """初始化数据库连接"""
        self.conn = psycopg2.connect(
            host='localhost',
            port=15432,
            database='athena',
            user='athena',
            password='athena_password_change_me'
        )
        logger.info("✅ 高级专利检索器初始化成功")

    async def search(
        self,
        query: str,
        top_k: int = 20,
        search_fields: List[str] = None,
        filters: Optional[SearchFilter] = None
    ) -> List[AdvancedPatentResult]:
        """
        高级检索 - 支持关键词搜索和多条件过滤

        Args:
            query: 搜索关键词
            top_k: 返回结果数量
            search_fields: 搜索字段列表
            filters: 搜索过滤器

        Returns:
            检索结果列表
        """
        if search_fields is None:
            search_fields = ['title', 'abstract', 'claims']

        if filters is None:
            filters = SearchFilter()

        logger.info(f"🔍 开始高级检索: '{query}'")
        if filters.ipc_codes:
            logger.info(f"   IPC过滤: {filters.ipc_codes}")
        if filters.assignees:
            logger.info(f"   申请人过滤: {filters.assignees}")

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 构建SQL查询
                sql, params = self._build_search_sql(
                    query,
                    top_k,
                    search_fields,
                    filters
                )

                # 执行查询
                cur.execute(sql, params)
                rows = cur.fetchall()

                # 构建结果
                results = []
                for row in rows:
                    result = self._parse_result(row, query, search_fields, filters)
                    if result:
                        # 在Python中计算相关度分数
                        result.score = self._calculate_relevance(result, query, search_fields)
                        results.append(result)

                # 按相关度排序（如果需要）
                if filters.sort_by == "relevance":
                    results.sort(key=lambda x: x.score, reverse=(filters.sort_order == "desc"))

                logger.info(f"✅ 高级检索完成，找到 {len(results)} 条结果")
                return results

        except Exception as e:
            logger.error(f"❌ 高级检索失败: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _build_search_sql(
        self,
        query: str,
        top_k: int,
        search_fields: List[str],
        filters: SearchFilter
    ) -> tuple:
        """
        构建搜索SQL

        Returns:
            (sql, params) 元组
        """
        # WHERE子句和参数
        where_clauses = []
        params = []

        # 1. 关键词搜索
        if query:
            like_pattern = f"%{query}%"
            keyword_conditions = []
            for field in search_fields:
                if field in ['title', 'abstract', 'claims', 'applicant', 'inventor', 'ipc_codes']:
                    keyword_conditions.append(f"{field} LIKE %s")
                    params.append(like_pattern)

            if keyword_conditions:
                where_clauses.append(f"({' OR '.join(keyword_conditions)})")

        # 2. IPC分类号过滤
        if filters.ipc_codes:
            if filters.ipc_mode == "any":
                # 任一匹配
                ipc_conditions = []
                for ipc in filters.ipc_codes:
                    ipc_conditions.append("ipc_codes LIKE %s")
                    params.append(f"%{ipc}%")
                if ipc_conditions:
                    where_clauses.append(f"({' OR '.join(ipc_conditions)})")
            else:
                # 全部匹配
                for ipc in filters.ipc_codes:
                    where_clauses.append("ipc_codes LIKE %s")
                    params.append(f"%{ipc}%")

        # 3. 申请人过滤
        if filters.assignees:
            if filters.assignee_mode == "any":
                assignee_conditions = []
                for assignee in filters.assignees:
                    assignee_conditions.append("applicant LIKE %s")
                    params.append(f"%{assignee}%")
                if assignee_conditions:
                    where_clauses.append(f"({' OR '.join(assignee_conditions)})")
            else:
                for assignee in filters.assignees:
                    where_clauses.append("applicant LIKE %s")
                    params.append(f"%{assignee}%")

        # 4. 发明人过滤
        if filters.inventors:
            for inventor in filters.inventors:
                where_clauses.append("inventor LIKE %s")
                params.append(f"%{inventor}%")

        # 5. 日期范围过滤
        if filters.publication_date_start:
            where_clauses.append("publication_date >= %s")
            params.append(filters.publication_date_start)

        if filters.publication_date_end:
            where_clauses.append("publication_date <= %s")
            params.append(filters.publication_date_end)

        # 6. 状态过滤
        if filters.status and filters.status != "all":
            where_clauses.append("status = %s")
            params.append(filters.status)

        # 组装WHERE子句
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        # 排序 - 在SQL中不使用score
        order_by = "publication_date DESC"  # 默认按日期降序
        if filters.sort_by == "date":
            order_by = f"publication_date {filters.sort_order.upper()}"
        elif filters.sort_by == "patent_id":
            order_by = f"patent_id {filters.sort_order.upper()}"

        # 完整SQL - 不在SQL中计算score
        all_params = params + [top_k]

        sql = f"""
        SELECT
            patent_id,
            title,
            abstract,
            claims,
            applicant,
            inventor,
            publication_date,
            ipc_codes,
            status,
            0.0 as score
        FROM patents
        WHERE {where_sql}
        ORDER BY {order_by}
        LIMIT %s;
        """

        return sql, all_params

    def _calculate_relevance(
        self,
        result: AdvancedPatentResult,
        query: str,
        search_fields: List[str]
    ) -> float:
        """
        在Python中计算相关度分数

        Args:
            result: 专利结果
            query: 查询关键词
            search_fields: 搜索字段

        Returns:
            相关系数 (0-1)
        """
        if not query:
            return 0.3

        score = 0.0
        query_lower = query.lower()

        # 根据搜索字段和匹配情况计算分数
        if 'title' in search_fields and query_lower in result.title.lower():
            score += 0.5
            if query_lower == result.title.lower():
                score += 0.3  # 完全匹配奖励

        if 'abstract' in search_fields and query_lower in result.abstract.lower():
            score += 0.2

        if 'claims' in search_fields and result.claims and query_lower in result.claims.lower():
            score += 0.15

        return min(score, 1.0)

    def _parse_result(
        self,
        row: Dict[str, Any],
        query: str,
        search_fields: List[str],
        filters: SearchFilter
    ) -> Optional[AdvancedPatentResult]:
        """解析数据库结果"""
        try:
            # 检测匹配字段
            matched_fields = []
            query_lower = query.lower() if query else ""

            for field in search_fields:
                if field == 'title' and row['title'] and query_lower in row['title'].lower():
                    matched_fields.append('title')
                if field == 'abstract' and row['abstract'] and query_lower in row['abstract'].lower():
                    matched_fields.append('abstract')
                if field == 'claims' and row['claims'] and query_lower in row['claims'].lower():
                    matched_fields.append('claims')

            # 检测匹配的过滤器
            matched_filters = {}

            if filters.ipc_codes and row['ipc_codes']:
                matched_ipcs = []
                row_ipcs = row['ipc_codes']
                for ipc in filters.ipc_codes:
                    if ipc.lower() in row_ipcs.lower():
                        matched_ipcs.append(ipc)
                if matched_ipcs:
                    matched_filters['ipc_codes'] = matched_ipcs

            if filters.assignees and row['applicant']:
                matched_assignees = []
                row_applicant = row['applicant']
                for assignee in filters.assignees:
                    if assignee.lower() in row_applicant.lower():
                        matched_assignees.append(assignee)
                if matched_assignees:
                    matched_filters['assignees'] = matched_assignees

            if filters.inventors and row['inventor']:
                matched_inventors = []
                row_inventors = row['inventor']
                for inventor in filters.inventors:
                    if inventor.lower() in row_inventors.lower():
                        matched_inventors.append(inventor)
                if matched_inventors:
                    matched_filters['inventors'] = matched_inventors

            return AdvancedPatentResult(
                patent_id=row['patent_id'],
                title=row['title'] or "",
                abstract=row['abstract'] or "",
                claims=row['claims'] or "",
                applicant=row['applicant'] or "",
                inventor=row['inventor'] or "",
                publication_date=str(row['publication_date']) if row['publication_date'] else "",
                ipc_codes=row['ipc_codes'] or "",
                status=row['status'] or "",
                score=float(row.get('score', 0.0)),
                matched_fields=matched_fields,
                matched_filters=matched_filters,
                source="advanced_search"
            )

        except Exception as e:
            logger.warning(f"⚠️ 解析结果失败: {e}")
            return None

    async def get_statistics(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                stats = {}

                # 总专利数
                cur.execute("SELECT COUNT(*) as total FROM patents;")
                stats['total_patents'] = cur.fetchone()['total']

                # 按状态统计
                cur.execute("""
                    SELECT status, COUNT(*) as count
                    FROM patents
                    GROUP BY status;
                """)
                stats['by_status'] = {row['status']: row['count'] for row in cur.fetchall()}

                # 按申请人统计（Top 10）
                cur.execute("""
                    SELECT applicant, COUNT(*) as count
                    FROM patents
                    GROUP BY applicant
                    ORDER BY count DESC
                    LIMIT 10;
                """)
                stats['top_assignees'] = [(row['applicant'], row['count']) for row in cur.fetchall()]

                # IPC分类号统计
                cur.execute("""
                    SELECT ipc_codes, COUNT(*) as count
                    FROM patents
                    WHERE ipc_codes IS NOT NULL AND ipc_codes != ''
                    GROUP BY ipc_codes
                    ORDER BY count DESC
                    LIMIT 10;
                """)
                stats['top_ipc_codes'] = [(row['ipc_codes'], row['count']) for row in cur.fetchall()]

                # 日期范围
                cur.execute("""
                    SELECT
                        MIN(publication_date) as earliest,
                        MAX(publication_date) as latest
                    FROM patents
                    WHERE publication_date IS NOT NULL;
                """)
                date_range = cur.fetchone()
                stats['date_range'] = {
                    'earliest': str(date_range['earliest']) if date_range['earliest'] else None,
                    'latest': str(date_range['latest']) if date_range['latest'] else None
                }

                return stats

        except Exception as e:
            logger.error(f"❌ 获取统计信息失败: {e}")
            return {}

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            logger.info("✅ 高级专利检索器已关闭")


async def test_advanced_search():
    """测试高级检索功能"""
    retriever = AdvancedPatentRetriever()

    print("\n" + "="*80)
    print("🔍 高级专利检索功能测试")
    print("="*80)

    # 获取统计信息
    print("\n📊 数据库统计信息:")
    stats = await retriever.get_statistics()
    print(f"  总专利数: {stats.get('total_patents', 0)}")
    print(f"  按状态分布: {stats.get('by_status', {})}")
    print(f"  Top申请人: {[name for name, _ in stats.get('top_assignees', [])[:5]]}")
    print(f"  日期范围: {stats.get('date_range', {})}")

    # 测试用例
    test_cases = [
        {
            "name": "基础关键词检索",
            "query": "深度学习",
            "filters": None
        },
        {
            "name": "IPC分类号过滤 - G06N (计算机)",
            "query": "网络",
            "filters": SearchFilter(ipc_codes=["G06N"], ipc_mode="any")
        },
        {
            "name": "申请人过滤 - 百度",
            "query": "自动驾驶",
            "filters": SearchFilter(assignees=["百度"])
        },
        {
            "name": "多条件过滤 - IPC + 申请人",
            "query": "智能",
            "filters": SearchFilter(
                ipc_codes=["G06N"],
                assignees=["腾讯"],
                ipc_mode="any"
            )
        },
        {
            "name": "状态过滤 - 已授权",
            "query": "系统",
            "filters": SearchFilter(status="granted")
        },
        {
            "name": "日期范围过滤 - 2023年",
            "query": "专利",
            "filters": SearchFilter(
                publication_date_start="2023-01-01",
                publication_date_end="2023-12-31"
            )
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"测试 {i}: {test_case['name']}")
        print(f"查询: '{test_case['query']}'")
        if test_case['filters']:
            filters = test_case['filters']
            if filters.ipc_codes:
                print(f"IPC过滤: {filters.ipc_codes} ({filters.ipc_mode})")
            if filters.assignees:
                print(f"申请人过滤: {filters.assignees}")
            if filters.status:
                print(f"状态过滤: {filters.status}")
            if filters.publication_date_start or filters.publication_date_end:
                print(f"日期范围: {filters.publication_date_start} ~ {filters.publication_date_end}")
        print('='*80)

        results = await retriever.search(
            query=test_case['query'],
            top_k=5,
            search_fields=['title', 'abstract', 'claims'],
            filters=test_case['filters']
        )

        if results:
            print(f"\n✅ 找到 {len(results)} 条结果:\n")

            for j, result in enumerate(results, 1):
                print(f"{j}. [{result.patent_id}] {result.title}")
                print(f"   申请人: {result.applicant}")
                print(f"   IPC分类号: {result.ipc_codes}")
                print(f"   状态: {result.status}")
                print(f"   公开日: {result.publication_date}")
                print(f"   相关度: {result.score:.2f}")

                if result.matched_fields:
                    print(f"   匹配字段: {', '.join(result.matched_fields)}")

                if result.matched_filters:
                    filter_matches = []
                    for key, values in result.matched_filters.items():
                        filter_matches.append(f"{key}: {values}")
                    print(f"   匹配过滤器: {', '.join(filter_matches)}")

                if result.abstract:
                    abstract_preview = result.abstract[:100] + "..." if len(result.abstract) > 100 else result.abstract
                    print(f"   摘要: {abstract_preview}")

                print()
        else:
            print("❌ 未找到结果\n")

    retriever.close()

    print("="*80)
    print("✅ 测试完成")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_advanced_search())
