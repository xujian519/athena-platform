#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL全文搜索适配器
PostgreSQL Full-text Search Adapter

使用PostgreSQL内置的全文搜索功能实现BM25类似的检索
"""

import logging
import os
import re
from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


def _get_db_config() -> Dict[str, str]:
    """从环境变量获取数据库配置，支持多种配置源"""
    # 优先使用POSTGRES_前缀的配置（.env中的主要配置）
    config = {
        'host': os.getenv('POSTGRES_HOST', os.getenv('DB_HOST', 'localhost')),
        'port': os.getenv('POSTGRES_PORT', os.getenv('DB_PORT', '5432')),
        'database': os.getenv('POSTGRES_DBNAME', os.getenv('DB_NAME', 'patent_db')),
        'user': os.getenv('POSTGRES_USER', os.getenv('DB_USER', 'postgres')),
        'password': os.getenv('POSTGRES_PASSWORD', os.getenv('DB_PASSWORD', 'password')),
    }

    # 如果指定了patent数据库相关的环境变量，优先使用
    if 'PATENT_DB_HOST' in os.environ:
        config['host'] = os.getenv('PATENT_DB_HOST', config['host'])
    if 'PATENT_DB_NAME' in os.environ:
        config['database'] = os.getenv('PATENT_DB_NAME', config['database'])
    if 'PATENT_DB_USER' in os.environ:
        config['user'] = os.getenv('PATENT_DB_USER', config['user'])
    if 'PATENT_DB_PASSWORD' in os.environ:
        config['password'] = os.getenv('PATENT_DB_PASSWORD', config['password'])

    return config


class FullTextSearchAdapter:
    """PostgreSQL全文搜索适配器"""

    def __init__(self, host=None, database=None, user=None, password=None, port=None):
        """
        初始化全文搜索适配器

        Args:
            host: PostgreSQL主机地址（为None时从环境变量读取）
            database: 数据库名（为None时从环境变量读取）
            user: 用户名（为None时从环境变量读取）
            password: 密码（为None时从环境变量读取）
            port: 端口号（为None时从环境变量读取）
        """
        # 从环境变量获取默认配置
        default_config = _get_db_config()

        # 使用传入参数覆盖环境变量配置
        self.host = host if host is not None else default_config['host']
        self.database = database if database is not None else default_config['database']
        self.user = user if user is not None else default_config['user']
        self.password = password if password is not None else default_config['password']
        self.port = port if port is not None else default_config['port']
        self.conn = None

        logger.info(f"数据库配置: {self.user}@{self.host}:{self.port}/{self.database}")

        # 连接数据库
        self._connect()

        # 创建必要的索引（如果不存在）
        self._ensure_indexes()

    def _connect(self):
        """连接PostgreSQL数据库"""
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password,
                port=self.port
            )
            self.conn.autocommit = True
            logger.info('PostgreSQL全文搜索连接成功')
        except Exception as e:
            logger.error(f"PostgreSQL连接失败: {e}")
            self.conn = None

    def _ensure_indexes(self):
        """确保全文搜索索引存在"""
        if not self.conn:
            return

        try:
            with self.conn.cursor() as cur:
                # 创建全文搜索向量列（如果不存在）
                cur.execute("""
                    ALTER TABLE patents
                    ADD COLUMN IF NOT EXISTS search_vector tsvector;
                """)

                # 更新搜索向量（使用实际的列名）
                cur.execute("""
                    UPDATE patents
                    SET search_vector =
                        setweight(to_tsvector('chinese', patent_name), 'A') ||
                        setweight(to_tsvector('chinese', abstract), 'B') ||
                        setweight(to_tsvector('chinese', claims_content), 'C') ||
                        setweight(to_tsvector('chinese', coalesce(claims, '')), 'C')
                    WHERE search_vector IS NULL;
                """)

                # 创建GIN索引
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_patents_search_vector
                    ON patents USING GIN(search_vector);
                """)

                logger.info('全文搜索索引创建完成')

        except Exception as e:
            logger.error(f"创建索引失败: {e}")

    def search(self, query: str, limit: int = 20,
               offset: int = 0) -> List[Dict[str, Any]]:
        """
        执行全文搜索

        Args:
            query: 查询文本
            limit: 返回结果数量限制
            offset: 偏移量

        Returns:
            搜索结果列表
        """
        if not self.conn:
            logger.error('数据库未连接')
            return []

        results = []
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 清理查询文本
                cleaned_query = self._clean_query(query)

                # 使用ts_rank_cd计算相关性分数（类似BM25）
                # 注意：使用实际的列名
                sql = """
                SELECT
                    id as patent_id,
                    patent_name as title,
                    abstract,
                    claims_content as claims,
                    ipc_code as ipc_codes,
                    publication_date,
                    applicant,
                    ts_rank_cd(
                        search_vector,
                        plainto_tsquery('chinese', %s),
                        32  -- 标准化参数
                    ) as rank,
                    ts_headline(
                        'chinese',
                        patent_name,
                        plainto_tsquery('chinese', %s),
                        'StartSel=<mark>, StopSel=</mark>, MaxWords=10, MinWords=3'
                    ) as title_highlight,
                    ts_headline(
                        'chinese',
                        abstract,
                        plainto_tsquery('chinese', %s),
                        'StartSel=<mark>, StopSel=</mark>, MaxWords=30, MinWords=5'
                    ) as abstract_highlight
                FROM patents
                WHERE search_vector @@ plainto_tsquery('chinese', %s)
                ORDER BY rank DESC
                LIMIT %s OFFSET %s;
                """

                cur.execute(sql, (cleaned_query, cleaned_query,
                                cleaned_query, cleaned_query,
                                limit, offset))

                rows = cur.fetchall()

                for row in rows:
                    results.append({
                        'patent_id': str(row['patent_id']),
                        'title': row['title'],
                        'abstract': row['abstract'],
                        'claims': row['claims'],
                        'ipc_codes': row['ipc_codes'],
                        'publication_date': str(row['publication_date']) if row['publication_date'] else None,
                        'applicant': row['applicant'],
                        'score': float(row['rank']),
                        'highlights': {
                            'title': row['title_highlight'],
                            'abstract': row['abstract_highlight']
                        },
                        'source': 'fulltext'
                    })

        except Exception as e:
            logger.error(f"全文搜索出错: {e}")

        return results

    def search_with_filters(self, query: str, filters: Dict[str, Any] = None,
                          limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """
        带过滤条件的全文搜索

        Args:
            query: 查询文本
            filters: 过滤条件
            limit: 返回结果数量限制
            offset: 偏移量

        Returns:
            搜索结果列表
        """
        if not self.conn:
            return []

        results = []
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cleaned_query = self._clean_query(query)

                # 构建WHERE条件
                where_clauses = ["search_vector @@ plainto_tsquery('chinese', %s)"]
                params = [cleaned_query]

                # 添加过滤条件
                if filters:
                    if 'ipc_codes' in filters and filters['ipc_codes']:
                        placeholders = ','.join(['%s'] * len(filters['ipc_codes']))
                        where_clauses.append(f"ipc_codes && ARRAY[{placeholders}]")
                        params.extend(filters['ipc_codes'])

                    if 'date_range' in filters and filters['date_range']:
                        date_filter = filters['date_range']
                        if 'start' in date_filter:
                            where_clauses.append('publication_date >= %s')
                            params.append(date_filter['start'])
                        if 'end' in date_filter:
                            where_clauses.append('publication_date <= %s')
                            params.append(date_filter['end'])

                    if 'applicants' in filters and filters['applicants']:
                        placeholders = ','.join(['%s'] * len(filters['applicants']))
                        where_clauses.append(f"applicant = ANY(ARRAY[{placeholders}])")
                        params.extend(filters['applicants'])

                # 构建完整SQL
                sql = f"""
                SELECT
                    patent_id,
                    title,
                    abstract,
                    ipc_codes,
                    publication_date,
                    applicant,
                    ts_rank_cd(search_vector, plainto_tsquery('chinese', %s), 32) as rank,
                    ts_headline('chinese', title, plainto_tsquery('chinese', %s),
                              'StartSel=<mark>, StopSel=</mark>') as title_highlight,
                    ts_headline('chinese', abstract, plainto_tsquery('chinese', %s),
                              'StartSel=<mark>, StopSel=</mark>') as abstract_highlight
                FROM patents
                WHERE {' AND '.join(where_clauses)}
                ORDER BY rank DESC
                LIMIT %s OFFSET %s;
                """

                params.extend([cleaned_query, cleaned_query, cleaned_query, limit, offset])

                cur.execute(sql, params)
                rows = cur.fetchall()

                for row in rows:
                    results.append({
                        'patent_id': row['patent_id'],
                        'title': row['title'],
                        'abstract': row['abstract'],
                        'ipc_codes': row['ipc_codes'],
                        'publication_date': row['publication_date'],
                        'applicant': row['applicant'],
                        'score': float(row['rank']),
                        'highlights': {
                            'title': row['title_highlight'],
                            'abstract': row['abstract_highlight']
                        },
                        'source': 'fulltext'
                    })

        except Exception as e:
            logger.error(f"带条件的全文搜索出错: {e}")

        return results

    def get_similar_patents(self, patent_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        基于相似性查找相关专利

        Args:
            patent_id: 专利ID
            limit: 返回结果数量限制

        Returns:
            相似专利列表
        """
        if not self.conn:
            return []

        results = []
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 使用相似性搜索
                sql = """
                WITH target_patent AS (
                    SELECT search_vector, ipc_codes
                    FROM patents
                    WHERE patent_id = %s
                    LIMIT 1
                )
                SELECT
                    p.patent_id,
                    p.title,
                    p.abstract,
                    p.ipc_codes,
                    p.publication_date,
                    p.applicant,
                    ts_rank_cd(p.search_vector, t.search_vector, 32) *
                    CASE
                        WHEN p.ipc_codes && t.ipc_codes THEN 1.5
                        ELSE 1.0
                    END as similarity_score,
                    array_length(p.ipc_codes & t.ipc_codes, 1) as common_ipcs
                FROM patents p, target_patent t
                WHERE p.patent_id != %s
                  AND p.search_vector @@ plainto_tsquery('chinese',
                    array_to_tsvector(string_to_array(substring(t.search_vector::text, 1, 1000), ' ')))
                ORDER BY similarity_score DESC, common_ipcs DESC
                LIMIT %s;
                """

                cur.execute(sql, (patent_id, patent_id, limit))
                rows = cur.fetchall()

                for row in rows:
                    results.append({
                        'patent_id': row['patent_id'],
                        'title': row['title'],
                        'abstract': row['abstract'],
                        'ipc_codes': row['ipc_codes'],
                        'publication_date': row['publication_date'],
                        'applicant': row['applicant'],
                        'score': float(row['similarity_score']),
                        'common_ipcs': row['common_ipcs'],
                        'source': 'fulltext_similarity'
                    })

        except Exception as e:
            logger.error(f"相似专利搜索出错: {e}")

        return results

    def _clean_query(self, query: str) -> str:
        """
        清理查询文本

        Args:
            query: 原始查询文本

        Returns:
            清理后的查询文本
        """
        # 移除特殊字符
        cleaned = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', query)
        # 移除多余空格
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned

    def get_search_stats(self) -> Dict[str, Any]:
        """获取搜索统计信息"""
        stats = {
            'connected': self.conn is not None,
            'database': self.database,
            'host': self.host
        }

        if self.conn:
            try:
                with self.conn.cursor() as cur:
                    # 获取专利总数
                    cur.execute('SELECT COUNT(*) FROM patents')
                    stats['total_patents'] = cur.fetchone()[0]

                    # 获取索引信息
                    cur.execute("""
                        SELECT indexname
                        FROM pg_indexes
                        WHERE tablename = 'patents'
                        AND indexname LIKE '%search%'
                    """)
                    stats['search_indexes'] = [row[0] for row in cur.fetchall()]

            except Exception as e:
                stats['error'] = str(e)

        return stats

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            logger.info('PostgreSQL连接已关闭')

# 测试函数
def test_fulltext_search():
    """测试全文搜索功能"""
    logger.info(str("\n" + '='*60))
    logger.info('🔍 PostgreSQL全文搜索测试')
    logger.info(str('='*60))

    # 初始化搜索适配器
    fts = FullTextSearchAdapter()

    # 显示统计信息
    logger.info("\n📊 搜索系统状态:")
    stats = fts.get_search_stats()
    for key, value in stats.items():
        logger.info(f"  {key}: {value}")

    # 测试查询
    test_queries = [
        '深度学习',
        '图像识别',
        '数据存储',
        '自然语言处理'
    ]

    for query in test_queries:
        logger.info(f"\n🔎 搜索: {query}")
        logger.info(str('-' * 40))

        results = fts.search(query, limit=3)

        if results:
            for i, result in enumerate(results, 1):
                logger.info(f"\n{i}. 专利ID: {result['patent_id']}")
                logger.info(f"   评分: {result['score']:.4f}")
                logger.info(f"   标题: {result['highlights']['title']}")
                logger.info(f"   摘要片段: {result['highlights']['abstract'][:100]}...")
        else:
            logger.info('  未找到相关专利')

    # 测试相似专利搜索
    if results:
        logger.info(f"\n🔗 查找与 {results[0]['patent_id']} 相似的专利")
        similar = fts.get_similar_patents(results[0]['patent_id'], limit=3)
        for i, patent in enumerate(similar, 1):
            patent_id = patent.get('patent_id', '')
            score = patent.get('score', 0)
            common_ipcs = patent.get('common_ipcs', 0)
            title = patent.get('title', '')
            logger.info(f"\n{i}. 相似专利ID: {patent_id}")
            logger.info(f"   相似度: {score:.4f}")
            logger.info(f"   共同IPC: {common_ipcs}个")
            logger.info(f"   标题: {title}")

    # 关闭连接
    fts.close()
    logger.info("\n✅ 测试完成！")

if __name__ == '__main__':
    test_fulltext_search()