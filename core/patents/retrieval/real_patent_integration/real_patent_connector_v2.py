#!/usr/bin/env python3
"""
真实专利数据库连接器（适配真实表结构）
Real Patent Database Connector (Adapted to Real Schema)
"""

import logging
from contextlib import contextmanager
from typing import Any

import psycopg2

# 配置日志
logger = logging.getLogger(__name__)

class RealPatentConnectorV2:
    """真实专利数据库连接器（V2）"""

    def __init__(
        self,
        host='localhost',
        port=5432,
        database='patent_db',
        username='postgres',
        password='password'
    ):
        """初始化连接器"""
        self.connection_params = {
            'host': host,
            'port': port,
            'database': database,
            'user': username,
            'password': password
        }
        self.connection = None

    @contextmanager
    def get_cursor(self):
        """获取数据库游标的上下文管理器"""
        try:
            if not self.connection:
                self.connection = psycopg2.connect(**self.connection_params)
                self.connection.autocommit = False
            cursor = self.connection.cursor()
            yield cursor
            cursor.close()
        except Exception as e:
            if self.connection:
                self.connection.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise

    def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute('SELECT version();')
                version = cursor.fetchone()[0]
                logger.info(f"数据库连接成功: {version}")
                return True
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            return False

    def get_patent_statistics(self) -> dict[str, Any]:
        """获取专利数据库统计信息"""
        stats = {}

        try:
            with self.get_cursor() as cursor:
                # 统计专利总数
                cursor.execute('SELECT COUNT(*) FROM patents;')
                stats['total_patents'] = cursor.fetchone()[0]

                # 按类型统计
                cursor.execute("""
                    SELECT patent_type, COUNT(*)
                    FROM patents
                    WHERE patent_type IS NOT NULL
                    GROUP BY patent_type
                    ORDER BY count DESC;
                """)
                stats['by_type'] = dict(cursor.fetchall())

                # 按年份统计（最近10年）
                cursor.execute("""
                    SELECT EXTRACT(YEAR FROM publication_date)::INTEGER as year, COUNT(*)
                    FROM patents
                    WHERE publication_date IS NOT NULL
                    AND EXTRACT(YEAR FROM publication_date) >= 2014
                    GROUP BY year
                    ORDER BY year DESC
                    LIMIT 10;
                """)
                stats['by_year'] = dict(cursor.fetchall())

                # 统计已向量化的数量
                cursor.execute('SELECT COUNT(*) FROM patents WHERE vectorized_at IS NOT NULL;')
                stats['vectorized_count'] = cursor.fetchone()[0]

                logger.info(f"专利统计信息: {stats}")

        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            stats['error'] = str(e)

        return stats

    def load_patents(
        self,
        limit: int = 10000,
        include_abstract: bool = True,
        include_claims: bool = True,
        filters: Optional[dict[str, Any]] = None
    ) -> list[dict[str, Any]]:
        """加载专利数据"""
        patents = []

        try:
            with self.get_cursor() as cursor:
                # 构建查询
                query_parts = ['SELECT']
                query_fields = [
                    'id', 'patent_name', 'patent_type',
                    'application_number', 'application_date',
                    'publication_number', 'publication_date',
                    'authorization_number', 'authorization_date',
                    'applicant', 'applicant_type',
                    'current_assignee', 'assignee_type',
                    'inventor', 'ipc_code', 'ipc_main_class',
                    'citation_count', 'cited_count'
                ]

                if include_abstract:
                    query_fields.append('abstract')

                if include_claims:
                    query_fields.append('claims')

                query_parts.append(', '.join(query_fields))
                query_parts.append('FROM patents')

                # 添加过滤条件
                where_clauses = []
                params = {}

                if filters:
                    if 'patent_type' in filters:
                        where_clauses.append('patent_type = %(patent_type)s')
                        params['patent_type'] = filters['patent_type']

                    if 'year_from' in filters:
                        where_clauses.append('EXTRACT(YEAR FROM publication_date) >= %(year_from)s')
                        params['year_from'] = filters['year_from']

                    if 'year_to' in filters:
                        where_clauses.append('EXTRACT(YEAR FROM publication_date) <= %(year_to)s')
                        params['year_to'] = filters['year_to']

                    if 'keywords' in filters:
                        where_clauses.append(
                            '(patent_name ILIKE %(keywords)s OR abstract ILIKE %(keywords)s)'
                        )
                        params['keywords'] = f"%{filters['keywords']}%"

                    if 'ipc_code' in filters:
                        where_clauses.append('ipc_code LIKE %(ipc_code)s')
                        params['ipc_code'] = f"{filters['ipc_code']}%"

                if where_clauses:
                    query_parts.append('WHERE ' + ' AND '.join(where_clauses))

                query_parts.append('ORDER BY publication_date DESC NULLS LAST')
                query_parts.append('LIMIT %(limit)s')
                params['limit'] = limit

                query = ' '.join(query_parts)
                logger.info(f"执行查询: {query[:200]}...")

                cursor.execute(query, params)
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()

                # 转换为字典列表
                for row in rows:
                    patent = dict(zip(columns, row, strict=False))
                    # 添加专利ID字段（使用id作为标识）
                    patent['patent_id'] = str(patent['id'])
                    patents.append(patent)

                logger.info(f"成功加载 {len(patents)} 条专利数据")

        except Exception as e:
            logger.error(f"加载专利数据失败: {e}")

        return patents

    def search_patents(
        self,
        query: str,
        limit: int = 100,
        search_fields: Optional[list[str]] = None
    ) -> list[dict[str, Any]]:
        """全文搜索专利"""
        if search_fields is None:
            search_fields = ['patent_name', 'abstract', 'claims']

        patents = []

        try:
            with self.get_cursor() as cursor:
                # 构建搜索查询
                search_conditions = []
                for field in search_fields:
                    search_conditions.append(f"{field} ILIKE %s")

                query_sql = f"""
                    SELECT id, patent_name, patent_type, abstract,
                           ts_headline('chinese', patent_name, plainto_tsquery('chinese', %s)) as title_highlight,
                           ts_rank(search_vector, plainto_tsquery('chinese', %s)) as rank
                    FROM patents
                    WHERE ({' OR '.join(search_conditions)})
                        AND search_vector IS NOT NULL
                    ORDER BY rank DESC
                    LIMIT %s;
                """

                # 准备参数
                params = []
                for _ in search_fields:
                    params.append(f"%{query}%")
                params.extend([query, query, limit])

                cursor.execute(query_sql, params)
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()

                for row in rows:
                    patent = dict(zip(columns, row, strict=False))
                    patent['patent_id'] = str(patent['id'])
                    patents.append(patent)

                logger.info(f"全文搜索找到 {len(patents)} 条结果")

        except Exception as e:
            logger.error(f"全文搜索失败: {e}")

        return patents

    def get_patent_details(self, patent_id: str) -> Optional[dict[str, Any]]:
        """获取专利详细信息"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM patents
                    WHERE id = %s::uuid;
                """, (patent_id,))

                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    patent = dict(zip(columns, row, strict=False))
                    patent['patent_id'] = str(patent['id'])

                    # 获取IPC分类详情
                    if patent.get('ipc_code'):
                        ipc_codes = patent['ipc_code'].split(';') if patent['ipc_code'] else []
                        patent['ipc_codes'] = [code.strip() for code in ipc_codes if code.strip()]

                    return patent

        except Exception as e:
            logger.error(f"获取专利详情失败 {patent_id}: {e}")

        return None

    def get_patents_for_vectorization(self, batch_size: int = 1000, offset: int = 0) -> list[dict[str, Any]]:
        """获取需要向量化的专利数据"""
        patents = []

        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, patent_name, abstract, claims, ipc_code,
                           publication_date, patent_type
                    FROM patents
                    WHERE (patent_name IS NOT NULL OR abstract IS NOT NULL)
                      AND vectorized_at IS NULL
                    ORDER BY publication_date DESC NULLS LAST
                    LIMIT %s OFFSET %s;
                """, (batch_size, offset))

                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()

                for row in rows:
                    patent = dict(zip(columns, row, strict=False))
                    patent['patent_id'] = str(patent['id'])

                    # 合并文本内容用于向量化
                    text_parts = []
                    if patent.get('patent_name'):
                        text_parts.append(f"标题: {patent['patent_name']}")
                    if patent.get('abstract'):
                        text_parts.append(f"摘要: {patent['abstract']}")
                    if patent.get('claims'):
                        text_parts.append(f"权利要求: {patent['claims'][:1000]}")  # 限制长度
                    if patent.get('ipc_code'):
                        text_parts.append(f"IPC分类: {patent['ipc_code']}")

                    patent['text_for_embedding'] = ' '.join(text_parts)
                    patents.append(patent)

                logger.info(f"获取 {len(patents)} 条专利用于向量化（offset: {offset}）")

        except Exception as e:
            logger.error(f"获取向量化数据失败: {e}")

        return patents

    def update_patent_vectors(self, patent_ids: list[str], vectors: list[dict]) -> bool:
        """更新专利向量数据"""
        try:
            with self.get_cursor() as cursor:
                for i, patent_id in enumerate(patent_ids):
                    vector_data = vectors[i]
                    cursor.execute("""
                        UPDATE patents
                        SET embedding_title = %s,
                            embedding_abstract = %s,
                            embedding_claims = %s,
                            embedding_combined = %s,
                            vectorized_at = CURRENT_TIMESTAMP
                        WHERE id = %s::uuid;
                    """, (
                        vector_data.get('title'),
                        vector_data.get('abstract'),
                        vector_data.get('claims'),
                        vector_data.get('combined'),
                        patent_id
                    ))

                self.connection.commit()
                logger.info(f"更新 {len(patent_ids)} 条专利向量")
                return True

        except Exception as e:
            logger.error(f"更新向量失败: {e}")
            if self.connection:
                self.connection.rollback()
            return False

    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info('数据库连接已关闭')

# 测试函数
def test_connector():
    """测试连接器"""
    logger.info('=== 测试真实专利数据库连接器V2 ===')

    connector = RealPatentConnectorV2()

    try:
        # 测试连接
        if not connector.test_connection():
            logger.info('❌ 数据库连接失败')
            return

        # 获取统计
        logger.info("\n获取专利统计...")
        stats = connector.get_patent_statistics()
        logger.info(f"专利总数: {stats.get('total_patents', 0):,}")
        logger.info(f"已向量化: {stats.get('vectorized_count', 0):,}")

        # 加载示例
        logger.info("\n加载专利示例...")
        patents = connector.load_patents(limit=3, include_abstract=True)

        for i, patent in enumerate(patents, 1):
            logger.info(f"\n{i}. {patent.get('patent_name', '无标题')}")
            logger.info(f"   ID: {patent.get('patent_id')}")
            logger.info(f"   类型: {patent.get('patent_type')}")
            abstract = patent.get('abstract', '')
            if abstract:
                logger.info(f"   摘要: {abstract[:150]}...")

        # 搜索测试
        logger.info("\n\n执行搜索测试...")
        results = connector.search_patents('电池', limit=3)
        logger.info(f"找到 {len(results)} 条结果")

        for result in results:
            logger.info(f"\n- {result.get('title_highlight', result.get('patent_name'))}")
            logger.info(f"  相关度: {result.get('rank', 0):.3f}")

    except Exception as e:
        logger.info(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        connector.close()

if __name__ == '__main__':
    test_connector()
