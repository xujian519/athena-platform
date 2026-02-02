#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实专利数据库连接器
Real Patent Database Connector

连接PostgreSQL专利数据库，加载真实专利数据
"""

import logging
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

# 导入标准化数据库工具
from shared.database.db_utils import DatabaseManager, build_safe_query

# 配置日志
logger = logging.getLogger(__name__)

class RealPatentConnector:
    """真实专利数据库连接器"""

    def __init__(
        self,
        host='localhost',
        port=5432,
        database='patent_db',
        username='postgres',
        password='password'
    ):
        """初始化连接器

        Args:
            host: 数据库主机
            port: 数据库端口
            database: 数据库名称
            username: 用户名
            password: 密码
        """
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
        finally:
            pass

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

    def get_patent_statistics(self) -> Dict[str, Any]:
        """获取专利数据库统计信息"""
        stats = {}

        try:
            with self.get_cursor() as cursor:
                # 检查是否存在专利表
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name IN ('patents', 'patent_applications', 'inventors', 'companies');
                """)
                tables = [row[0] for row in cursor.fetchall()]

                if not tables:
                    logger.warning('未找到专利相关表，可能需要初始化数据库')
                    return {'error': '未找到专利相关表'}

                # 统计专利总数
                if 'patents' in tables:
                    cursor.execute('SELECT COUNT(*) FROM patents;')
                    stats['total_patents'] = cursor.fetchone()[0]

                # 统计申请总数
                if 'patent_applications' in tables:
                    cursor.execute('SELECT COUNT(*) FROM patent_applications;')
                    stats['total_applications'] = cursor.fetchone()[0]

                # 按类型统计
                if 'patents' in tables:
                    cursor.execute("""
                        SELECT patent_type, COUNT(*)
                        FROM patents
                        GROUP BY patent_type;
                    """)
                    stats['by_type'] = dict(cursor.fetchall())

                # 按年份统计
                if 'patent_applications' in tables:
                    cursor.execute("""
                        SELECT EXTRACT(YEAR FROM application_date)::INTEGER as year, COUNT(*)
                        FROM patent_applications
                        WHERE application_date IS NOT NULL
                        GROUP BY year
                        ORDER BY year DESC
                        LIMIT 10;
                    """)
                    stats['by_year'] = dict(cursor.fetchall())

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
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """加载专利数据

        Args:
            limit: 限制加载数量
            include_abstract: 是否包含摘要
            include_claims: 是否包含权利要求
            filters: 过滤条件

        Returns:
            专利数据列表
        """
        patents = []

        try:
            with self.get_cursor() as cursor:
                # 构建查询
                query_parts = ['SELECT']
                query_fields = ['p.patent_id', 'p.title', 'p.publication_number',
                               'p.publication_date', 'p.patent_type',
                               'pa.application_number', 'pa.application_date']

                if include_abstract:
                    query_fields.append('p.abstract')

                if include_claims:
                    query_fields.append('p.claims')

                query_parts.append(', '.join(query_fields))
                query_parts.append('FROM patents p')
                query_parts.append('LEFT JOIN patent_applications pa ON p.patent_id = pa.patent_id')

                # 添加过滤条件
                where_clauses = []
                if filters:
                    if 'patent_type' in filters:
                        where_clauses.append(f"p.patent_type = '{filters['patent_type']}'")
                    if 'year_from' in filters:
                        where_clauses.append(f"EXTRACT(YEAR FROM p.publication_date) >= {filters['year_from']}")
                    if 'year_to' in filters:
                        where_clauses.append(f"EXTRACT(YEAR FROM p.publication_date) <= {filters['year_to']}")
                    if 'keywords' in filters:
                        keywords = filters['keywords']
                        where_clauses.append(f"(p.title ILIKE '%{keywords}%' OR p.abstract ILIKE '%{keywords}%')")

                if where_clauses:
                    query_parts.append('WHERE ' + ' AND '.join(where_clauses))

                query_parts.append('ORDER BY p.publication_date DESC')
                query_parts.append(f"LIMIT {limit}")

                query = ' '.join(query_parts)
                logger.info(f"执行查询: {query[:200]}...")

                cursor.execute(query)
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()

                # 转换为字典列表
                for row in rows:
                    patent = dict(zip(columns, row))
                    patents.append(patent)

                logger.info(f"成功加载 {len(patents)} 条专利数据")

        except Exception as e:
            logger.error(f"加载专利数据失败: {e}")

        return patents

    def load_patent_with_details(self, patent_id: str) -> Dict[str, Any | None]:
        """加载单个专利的详细信息

        Args:
            patent_id: 专利ID

        Returns:
            专利详细信息
        """
        patent_detail = None

        try:
            with self.get_cursor() as cursor:
                # 获取基本信息
                cursor.execute("""
                    SELECT p.*, pa.*, i.inventor_name, c.company_name
                    FROM patents p
                    LEFT JOIN patent_applications pa ON p.patent_id = pa.patent_id
                    LEFT JOIN patent_inventors pi ON p.patent_id = pi.patent_id
                    LEFT JOIN inventors i ON pi.inventor_id = i.inventor_id
                    LEFT JOIN patent_companies pc ON p.patent_id = pc.patent_id
                    LEFT JOIN companies c ON pc.company_id = c.company_id
                    WHERE p.patent_id = %s
                    LIMIT 1;
                """, (patent_id,))

                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    patent_detail = dict(zip(columns, row))

                    # 获取分类号
                    cursor.execute("""
                        SELECT ipc_code, classification_level
                        FROM patent_ipc_classifications
                        WHERE patent_id = %s
                        ORDER BY classification_level;
                    """, (patent_id,))
                    patent_detail['ipc_codes'] = [row[0] for row in cursor.fetchall()]

                    # 获取引用文献
                    cursor.execute("""
                        SELECT citation_type, cited_patent_id, cited_document_id
                        FROM patent_citations
                        WHERE patent_id = %s
                        ORDER BY citation_type;
                    """, (patent_id,))
                    patent_detail['citations'] = cursor.fetchall()

                    # 获取同族专利
                    cursor.execute("""
                        SELECT family_patent_id, family_relation
                        FROM patent_families
                        WHERE patent_id = %s;
                    """, (patent_id,))
                    patent_detail['family_members'] = cursor.fetchall()

        except Exception as e:
            logger.error(f"加载专利详情失败 {patent_id}: {e}")

        return patent_detail

    def search_patents_by_ipc(self, ipc_codes: List[str], limit: int = 100) -> List[Dict[str, Any]]:
        """根据IPC分类号搜索专利

        Args:
            ipc_codes: IPC分类号列表
            limit: 返回数量限制

        Returns:
            匹配的专利列表
        """
        patents = []

        try:
            with self.get_cursor() as cursor:
                # 构建IPC条件
                ipc_conditions = ' OR '.join([f"ipc_code LIKE '{code}%'" for code in ipc_codes])

        # TODO: 检查SQL注入风险 - cursor.execute(f"""
                        cursor.execute(f"""
                    SELECT DISTINCT p.patent_id, p.title, p.publication_number,
                           p.publication_date, p.patent_type, p.abstract
                    FROM patents p
                    INNER JOIN patent_ipc_classifications pic ON p.patent_id = pic.patent_id
                    WHERE {ipc_conditions}
                    ORDER BY p.publication_date DESC
                    LIMIT {limit};
                """)

                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()

                for row in rows:
                    patent = dict(zip(columns, row))
                    patents.append(patent)

                logger.info(f"通过IPC分类找到 {len(patents)} 条专利")

        except Exception as e:
            logger.error(f"IPC分类搜索失败: {e}")

        return patents

    def get_patents_for_vectorization(self, batch_size: int = 1000) -> List[Dict[str, Any]]:
        """获取需要向量化的专利数据

        Args:
            batch_size: 批次大小

        Returns:
            专利数据列表（包含文本内容）
        """
        patents = []

        try:
            with self.get_cursor() as cursor:
        # TODO: 检查SQL注入风险 - cursor.execute(f"""
                        cursor.execute(f"""
                    SELECT p.patent_id, p.title, p.abstract, p.claims, p.description,
                           p.publication_date, p.patent_type,
                           STRING_AGG(pic.ipc_code, ', ') as ipc_codes
                    FROM patents p
                    LEFT JOIN patent_ipc_classifications pic ON p.patent_id = pic.patent_id
                    WHERE p.abstract IS NOT NULL OR p.claims IS NOT NULL
                    GROUP BY p.patent_id, p.title, p.abstract, p.claims, p.description,
                             p.publication_date, p.patent_type
                    ORDER BY p.publication_date DESC
                    LIMIT {batch_size};
                """)

                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()

                for row in rows:
                    patent = dict(zip(columns, row))
                    # 合并文本内容用于向量化
                    text_parts = []
                    if patent.get('title'):
                        text_parts.append(patent['title'])
                    if patent.get('abstract'):
                        text_parts.append(patent['abstract'])
                    if patent.get('claims'):
                        text_parts.append(patent['claims'][:1000])  # 限制长度
                    patent['text_for_embedding'] = ' '.join(text_parts)
                    patents.append(patent)

                logger.info(f"获取 {len(patents)} 条专利用于向量化")

        except Exception as e:
            logger.error(f"获取向量化数据失败: {e}")

        return patents

    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info('数据库连接已关闭')

# 初始化脚本
def init_sample_patent_data():
    """初始化示例专利数据（如果数据库为空）"""
    connector = RealPatentConnector()

    if not connector.test_connection():
        logger.error('无法连接到数据库')
        return

    # 检查是否已有数据
    stats = connector.get_patent_statistics()
    if 'total_patents' in stats and stats['total_patents'] > 0:
        logger.info('数据库中已有专利数据')
        connector.close()
        return

    # 创建示例数据
    logger.info('创建示例专利数据...')

    try:
        with connector.get_cursor() as cursor:
            # 创建专利表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS patents (
                    patent_id VARCHAR(50) PRIMARY KEY,
                    title TEXT NOT NULL,
                    abstract TEXT,
                    claims TEXT,
                    description TEXT,
                    publication_number VARCHAR(50),
                    publication_date DATE,
                    patent_type VARCHAR(20) CHECK (patent_type IN ('invention', 'utility_model', 'design')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 创建专利申请表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS patent_applications (
                    application_id VARCHAR(50) PRIMARY KEY,
                    patent_id VARCHAR(50) REFERENCES patents(patent_id),
                    application_number VARCHAR(50) UNIQUE,
                    application_date DATE,
                    applicant_name VARCHAR(200)
                );
            """)

            # 创建IPC分类表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS patent_ipc_classifications (
                    id SERIAL PRIMARY KEY,
                    patent_id VARCHAR(50) REFERENCES patents(patent_id),
                    ipc_code VARCHAR(20),
                    classification_level INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 插入示例数据
            sample_patents = [
                {
                    'patent_id': 'CN202410001234',
                    'title': '一种新型电池管理系统及其控制方法',
                    'abstract': '本发明公开了一种新型电池管理系统及其控制方法，包括电池状态监测模块、均衡控制模块和中央处理单元。该系统能够实时监测电池组中每个单体电池的电压、温度和内阻，并根据监测结果进行智能均衡控制，有效延长电池使用寿命。',
                    'claims': '1. 一种新型电池管理系统，其特征在于，包括：电池状态监测模块，用于实时监测电池组中每个单体电池的电压、温度和内阻；均衡控制模块，用于根据监测结果对电池进行均衡控制；中央处理单元，用于协调各模块工作。',
                    'publication_number': 'CN118765432A',
                    'publication_date': '2024-06-15',
                    'patent_type': 'invention'
                },
                {
                    'patent_id': 'CN202420005678',
                    'title': '智能防丢蓝牙追踪器',
                    'abstract': '本实用新型公开了一种智能防丢蓝牙追踪器，包括蓝牙模块、GPS定位模块、震动传感器和报警装置。当物品与用户距离超过设定值时，追踪器会发出警报提醒用户。',
                    'claims': '1. 一种智能防丢蓝牙追踪器，其特征在于，包括：蓝牙模块，用于与用户设备建立通信连接；GPS定位模块，用于获取物品位置信息；震动传感器，用于检测物品移动；报警装置，用于发出提醒信号。',
                    'publication_number': 'CN218765432U',
                    'publication_date': '2024-07-20',
                    'patent_type': 'utility_model'
                }
            ]

            for patent in sample_patents:
                cursor.execute("""
                    INSERT INTO patents (patent_id, title, abstract, claims,
                                      publication_number, publication_date, patent_type)
                    VALUES (%(patent_id)s, %(title)s, %(abstract)s, %(claims)s,
                            %(publication_number)s, %(publication_date)s, %(patent_type)s)
                    ON CONFLICT (patent_id) DO NOTHING;
                """, patent)

                # 添加申请信息
                cursor.execute("""
                    INSERT INTO patent_applications (application_id, patent_id, application_number, application_date)
                    VALUES (%s || '_APP', %s, %s || '_APP', %s - INTERVAL '1 year')
                    ON CONFLICT (application_id) DO NOTHING;
                """, (patent['patent_id'], patent['patent_id'], patent['patent_id'], patent['publication_date']))

                # 添加IPC分类
                ipc_codes = ['H01M10/42', 'H02J7/00'] if patent['patent_type'] == 'invention' else ['G08B21/24', 'H04B5/00']
                for ipc in ipc_codes:
                    cursor.execute("""
                        INSERT INTO patent_ipc_classifications (patent_id, ipc_code, classification_level)
                        VALUES (%s, %s, %s)
                        ON CONFLICT DO NOTHING;
                    """, (patent['patent_id'], ipc, 1))

            connector.connection.commit()
            logger.info('示例专利数据创建成功')

    except Exception as e:
        logger.error(f"初始化数据失败: {e}")
        if connector.connection:
            connector.connection.rollback()
    finally:
        connector.close()

if __name__ == '__main__':
    # 初始化示例数据
    init_sample_patent_data()