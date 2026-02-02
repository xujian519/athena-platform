#!/usr/bin/env python3
"""
强制导入2015年剩余数据，忽略所有错误
"""

import logging
import sys
import time
from datetime import datetime

import psycopg2

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('import_2015_remaining_force.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres',
    'database': 'patent_db'
}

def get_connection():
    """创建数据库连接"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        return conn
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return None

def force_import_2015_remaining():
    """强制导入2015年剩余数据"""
    logger.info('=' * 80)
    logger.info('开始强制导入2015年剩余数据')
    logger.info('=' * 80)

    conn = get_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        # 查询剩余未迁移的数据
        logger.info('查找2015年未迁移的数据...')
        cursor.execute("""
            INSERT INTO patents (
                patent_name, patent_type, application_number, application_date,
                publication_number, publication_date, authorization_number, authorization_date,
                applicant, applicant_type, applicant_address, applicant_region, applicant_city, applicant_district,
                current_assignee, current_assignee_address, assignee_type, credit_code,
                inventor, ipc_code, ipc_main_class, ipc_classification,
                abstract, claims_content, claims,
                citation_count, cited_count, self_citation_count, other_citation_count,
                cited_by_self_count, cited_by_others_count, family_citation_count, family_cited_count,
                source_year, source_file, file_hash
            )
            SELECT
                ps.patent_name,
                ps.patent_type,
                ps.application_number,
                ps.application_date,
                NULL,  -- publication_number
                NULL,  -- publication_date
                NULL,  -- authorization_number
                NULL,  -- authorization_date
                ps.applicant,
                NULL,  -- applicant_type
                NULL,  -- applicant_address
                NULL,  -- applicant_region
                NULL,  -- applicant_city
                NULL,  -- applicant_district
                NULL,  -- current_assignee
                NULL,  -- current_assignee_address
                NULL,  -- assignee_type
                NULL,  -- credit_code
                ps.inventor,
                ps.ipc_code,
                CASE WHEN ps.ipc_code IS NOT NULL AND LENGTH(ps.ipc_code) >= 4
                     THEN SUBSTRING(ps.ipc_code, 1, 4) ELSE NULL END,
                ps.ipc_code,  -- ipc_classification
                ps.abstract,
                NULL,  -- claims_content
                NULL,  -- claims
                0, 0, 0, 0, 0, 0, 0, 0,  -- 所有引证次数字段设为0
                ps.source_year,
                '中国专利数据库2015年.csv',
                NULL
            FROM patents_simple ps
            LEFT JOIN patents p ON ps.application_number = p.application_number
            WHERE ps.source_year = 2015
            AND p.application_number IS NULL
        """)

        affected_rows = cursor.rowcount
        conn.commit()

        logger.info(f"✅ 强制导入完成，处理了 {affected_rows:,} 条记录")

        # 验证最终结果
        cursor.execute('SELECT COUNT(*) FROM patents WHERE source_year = 2015')
        final_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM patents_simple WHERE source_year = 2015')
        total_count = cursor.fetchone()[0]

        completion_rate = (final_count / total_count * 100) if total_count > 0 else 0

        logger.info("\n最终统计:")
        logger.info(f"patents_simple表: {total_count:,} 条")
        logger.info(f"patents表: {final_count:,} 条")
        logger.info(f"完成率: {completion_rate:.2f}%")

        if completion_rate >= 99.9:
            logger.info('✅ 2015年数据迁移已基本完成！')

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        logger.error(f"强制导入失败: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

def main():
    """主函数"""
    success = force_import_2015_remaining()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()