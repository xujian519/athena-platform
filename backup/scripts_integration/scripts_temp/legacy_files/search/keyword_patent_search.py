#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能关键词专利检索引擎
Smart Keyword Patent Search Engine

策略：先关键词检索，再向量验证
作者: 小诺
创建时间: 2025-12-10
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import jieba
import psycopg2

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SearchQuery:
    """检索查询参数"""
    keywords: str
    boolean_logic: str | None = None  # AND, OR, NOT
    filters: Dict | None = None  # 专利类型、年份、申请人等
    limit: int = 500
    boost_recent: bool = True  # 是否加权近期专利

@dataclass
class SearchResult:
    """检索结果"""
    total_count: int
    patents: List[Dict]
    search_time: float
    query_used: str

class KeywordPatentSearch:
    """关键词专利检索引擎"""

    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'patent_db',
            'user': 'postgres',
            'password': 'postgres'
        }
        self.connection = None

        # 同义词映射
        self.synonyms = {
            '人工智能': ['AI', '机器智能', '智能系统', '智能化'],
            '机器学习': ['ML', '深度学习', '神经网络', '学习算法'],
            '通信': ['通讯', '传输', '信息传输', '数据传输'],
            '电动汽车': ['新能源车', '电动车', 'EV', '纯电动车'],
            '区块链': ['分布式账本', 'blockchain', '分布式存储'],
            '物联网': ['IoT', 'Internet of Things', '智能设备'],
            '云计算': ['cloud computing', '云服务', '云端计算']
        }

    def connect(self):
        """连接数据库"""
        try:
            self.connection = psycopg2.connect(**self.db_config)
            logger.info('✅ 数据库连接成功')
            return True
        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            return False

    def parse_boolean_logic(self, query: SearchQuery) -> Tuple[str, List]:
        """解析布尔逻辑查询"""
        keywords = query.keywords

        # 简化处理：暂时不使用同义词扩展，避免过度复杂
        words = jieba.lcut(keywords)
        main_word = words[0] if words else keywords  # 取主要关键词

        # 简化的搜索条件
        search_conditions = f"search_vector @@ phraseto_tsquery('chinese', '{main_word}')"

        # 如果需要AND逻辑，构建多个词的AND条件
        if query.boolean_logic == 'AND' and len(words) > 1:
            and_conditions = [f"search_vector @@ phraseto_tsquery('chinese', '{word}')" for word in words[:3]]  # 最多3个词
            search_conditions = ' AND '.join(and_conditions)

        return search_conditions, [main_word]

    def build_filters(self, query: SearchQuery) -> Tuple[str, List]:
        """构建筛选条件"""
        conditions = []
        params = []

        # 专利类型筛选
        if query.filters and 'patent_type' in query.filters and query.filters['patent_type']:
            conditions.append('patent_type = ANY(%s)')
            params.append(query.filters['patent_type'])

        # 年份范围筛选
        if query.filters and 'year_range' in query.filters:
            year_range = query.filters['year_range']
            if year_range and isinstance(year_range, dict):
                if 'start' in year_range:
                    conditions.append('source_year >= %s')
                    params.append(year_range['start'])
                if 'end' in year_range:
                    conditions.append('source_year <= %s')
                    params.append(year_range['end'])

        # 申请人筛选
        if query.filters and 'applicant' in query.filters:
            conditions.append('applicant ILIKE %s')
            params.append(f"%{query.filters['applicant']}%")

        # IPC分类筛选
        if query.filters and 'ipc_code' in query.filters:
            conditions.append('ipc_main_class LIKE %s')
            params.append(f"{query.filters['ipc_code']}%")

        return ' AND '.join(conditions) if conditions else '', params

    def build_ordering(self, query: SearchQuery) -> str:
        """构建排序条件"""
        if query.boost_recent:
            # 加权近期专利
            return """
            ORDER BY
                CASE
                    WHEN source_year >= 2020 THEN 1
                    WHEN source_year >= 2015 THEN 2
                    ELSE 3
                END ASC,
                ts_rank(search_vector, phraseto_tsquery('chinese', %s)) DESC,
                application_date DESC NULLS LAST
            """
        else:
            # 标准相关性排序
            return """
            ORDER BY
                ts_rank(search_vector, phraseto_tsquery('chinese', %s)) DESC,
                application_date DESC NULLS LAST
            """

    def search(self, query: SearchQuery) -> SearchResult:
        """执行关键词检索"""
        start_time = datetime.now()

        if not self.connection:
            raise ConnectionError('数据库未连接')

        try:
            # 解析查询
            search_conditions, expanded_words = self.parse_boolean_logic(query)
            filter_conditions, filter_params = self.build_filters(query)
            order_clause = self.build_ordering(query)

            # 构建完整SQL
            sql = f"""
            SELECT
                id,
                patent_name,
                patent_type,
                application_number,
                application_date,
                applicant,
                ipc_main_class,
                abstract,
                ts_rank(search_vector, phraseto_tsquery('chinese', %s)) as relevance_score
            FROM patents
            WHERE ({search_conditions})
            {f"AND {filter_conditions}' if filter_conditions else '"}
            {order_clause}
            LIMIT %s
            """

            # 准备参数：搜索关键词 + 排序关键词 + 筛选参数 + LIMIT
            search_keyword = expanded_words[0] if expanded_words else query.keywords
            main_params = [search_keyword] + [search_keyword] + filter_params + [query.limit]

            # 计数查询（不需要排序参数）
            count_sql = f"""
            SELECT COUNT(*)
            FROM patents
            WHERE ({search_conditions})
            {f"AND {filter_conditions}' if filter_conditions else '"}
            """
            count_params = [search_keyword] + filter_params

            # 执行查询
            with self.connection.cursor() as cursor:
                cursor.execute(sql, main_params)
                results = cursor.fetchall()

                # 获取总数
                cursor.execute(count_sql, count_params)
                total_count = cursor.fetchone()[0]

            # 转换结果格式
            patents = []
            for row in results:
                patents.append({
                    'id': row[0],
                    'patent_name': row[1],
                    'patent_type': row[2],
                    'application_number': row[3],
                    'application_date': row[4],
                    'applicant': row[5],
                    'ipc_main_class': row[6],
                    'abstract': row[7],
                    'relevance_score': float(row[8])
                })

            search_time = (datetime.now() - start_time).total_seconds()

            logger.info(f"✅ 关键词检索完成: {total_count}条记录，耗时{search_time:.3f}秒")

            return SearchResult(
                total_count=total_count,
                patents=patents,
                search_time=search_time,
                query_used=f"关键词: {query.keywords}, 逻辑: {query.boolean_logic}, 扩展词: {expanded_words}"
            )

        except Exception as e:
            logger.error(f"❌ 关键词检索失败: {e}")
            raise

    def get_suggestions(self, partial_query: str, limit: int = 10) -> List[str]:
        """获取查询建议"""
        if len(partial_query) < 2:
            return []

        try:
            with self.connection.cursor() as cursor:
                sql = """
                SELECT DISTINCT
                    CASE
                        WHEN length(patent_name) > 50 THEN substring(patent_name, 1, 47) || '...'
                        ELSE patent_name
                    END as suggestion,
                    ts_rank(search_vector, phraseto_tsquery('chinese', %s)) as rank
                FROM patents
                WHERE search_vector @@ phraseto_tsquery('chinese', %s)
                ORDER BY rank DESC
                LIMIT %s
                """

                cursor.execute(sql, [partial_query, partial_query, limit])
                suggestions = [row[0] for row in cursor.fetchall()]

                return suggestions

        except Exception as e:
            logger.error(f"❌ 获取建议失败: {e}")
            return []

    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            logger.info('🔒 数据库连接已关闭')

# 测试用例
def test_keyword_search():
    """测试关键词检索"""
    search_engine = KeywordPatentSearch()

    if not search_engine.connect():
        return

    try:
        # 测试1：基础关键词检索
        query1 = SearchQuery(
            keywords='人工智能',
            limit=10,
            boost_recent=True
        )

        result1 = search_engine.search(query1)
        logger.info(f"测试1 - 关键词检索: {result1.total_count}条结果")
        logger.info(f"前3条结果: {[p['patent_name'][:30] for p in result1.patents[:3]]}")

        # 测试2：布尔逻辑检索
        query2 = SearchQuery(
            keywords='机器学习 深度学习',
            boolean_logic='OR',
            limit=10,
            filters={'year_range': {'start': 2020}}
        )

        result2 = search_engine.search(query2)
        logger.info(f"测试2 - 布尔逻辑检索: {result2.total_count}条结果")

        # 测试3：申请人筛选
        query3 = SearchQuery(
            keywords='通信',
            filters={'applicant': '华为'},
            limit=5
        )

        result3 = search_engine.search(query3)
        logger.info(f"测试3 - 申请人筛选: {result3.total_count}条结果")

        # 测试4：获取建议
        suggestions = search_engine.get_suggestions('人工智能', 5)
        logger.info(f"测试4 - 查询建议: {suggestions}")

    finally:
        search_engine.close()

if __name__ == '__main__':
    test_keyword_search()