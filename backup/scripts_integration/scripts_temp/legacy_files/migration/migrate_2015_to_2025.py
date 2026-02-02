#!/usr/bin/env python3
"""
将2015-2025年的专利数据从简化表迁移到主表
"""

import logging
import sys
from datetime import datetime

import psycopg2

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('documentation/logs/migrate_2015_2025.log'),
        logging.StreamHandler(sys.stdout)
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

def create_connection():
    """创建数据库连接"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        return conn
    except Exception as e:
        logger.error(f"❌ 数据库连接失败: {e}")
        return None

def check_years_in_simple_table():
    """检查简化表中有哪些年份的数据"""
    conn = create_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT source_year, COUNT(*) as count
            FROM patents_simple
            WHERE source_year >= 2015
            GROUP BY source_year
            ORDER BY source_year
        """)

        results = cursor.fetchall()
        logger.info('简化表中的2015-2025年数据：')
        for year, count in results:
            logger.info(f"  {year}年: {count:,} 条记录")

        return [year for year, _ in results]
    except Exception as e:
        logger.error(f"❌ 检查失败: {e}")
        return []
    finally:
        conn.close()

def migrate_year(year):
    """迁移指定年份的数据"""
    conn = create_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        # 检查是否已经迁移过
        cursor.execute("""
            SELECT COUNT(*) FROM patents
            WHERE source_year = %s
        """, (year,))
        already_migrated = cursor.fetchone()[0]

        if already_migrated > 0:
            logger.info(f"⚠️ {year}年已有 {already_migrated:,} 条记录在主表中")
            response = input('是否继续迁移？（y/n）: ')
            if response.lower() != 'y':
                return True

        # 迁移SQL
        migrate_sql = """
            INSERT INTO patents (
                patent_name, patent_type, application_number, application_date,
                publication_number, publication_date, applicant, applicant_type,
                applicant_address, applicant_region, applicant_city, applicant_district,
                current_assignee, current_assignee_address, assignee_type,
                credit_code, inventor, ipc_code, ipc_main_class, ipc_classification,
                abstract, claims_content, claims, citation_count, cited_count,
                self_citation_count, other_citation_count, cited_by_self_count,
                cited_by_others_count, family_citation_count, family_cited_count,
                source_year, source_file, file_hash
            )
            SELECT
                ps.patent_name,
                ps.patent_type,
                ps.application_number,
                ps.application_date,
                NULL as publication_number,  -- 简化表中没有此字段
                NULL as publication_date,  -- 简化表中没有此字段
                ps.applicant,
                NULL as applicant_type,
                NULL as applicant_address,
                NULL as applicant_region,
                NULL as applicant_city,
                NULL as applicant_district,
                NULL as current_assignee,
                NULL as current_assignee_address,
                NULL as assignee_type,
                NULL as credit_code,
                ps.inventor,
                ps.ipc_code,
                CASE
                    WHEN ps.ipc_code IS NOT NULL AND LENGTH(ps.ipc_code) >= 4
                    THEN SUBSTRING(ps.ipc_code, 1, 4)
                    ELSE NULL
                END as ipc_main_class,
                ps.ipc_code as ipc_classification,
                ps.abstract,
                NULL as claims_content,
                NULL as claims,
                0 as citation_count,
                0 as cited_count,
                0 as self_citation_count,
                0 as other_citation_count,
                0 as cited_by_self_count,
                0 as cited_by_others_count,
                0 as family_citation_count,
                0 as family_cited_count,
                ps.source_year,
                '中国专利数据库' || ps.source_year || '年.csv' as source_file,
                NULL as file_hash
            FROM patents_simple ps
            WHERE ps.source_year = %s
            ON CONFLICT (application_number) DO NOTHING
        """

        logger.info(f"📦 开始迁移{year}年数据...")
        start_time = datetime.now()

        cursor.execute(migrate_sql, (year,))
        conn.commit()

        # 获取迁移数量
        cursor.execute("""
            SELECT COUNT(*) FROM patents
            WHERE source_year = %s
        """, (year,))
        total_count = cursor.fetchone()[0]

        elapsed = datetime.now() - start_time
        logger.info(f"✅ {year}年数据迁移完成")
        logger.info(f"   主表中该年份记录总数: {total_count:,} 条")
        logger.info(f"   耗时: {elapsed}")

        return True

    except Exception as e:
        logger.error(f"❌ {year}年迁移失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def main():
    """主函数"""
    # 创建日志目录
    import os
    os.makedirs('logs', exist_ok=True)

    logger.info('=' * 60)
    logger.info('2015-2025年专利数据迁移工具')
    logger.info('=' * 60)

    # 检查简化表中的数据
    years = check_years_in_simple_table()

    if not years:
        logger.error('❌ 简化表中没有2015-2025年的数据')
        return

    # 迁移每一年
    for year in years:
        logger.info(f"\n{'='*40}")
        logger.info(f"处理 {year} 年")
        logger.info(f"{'='*40}")

        if migrate_year(year):
            logger.info(f"✅ {year}年迁移成功")
        else:
            logger.error(f"❌ {year}年迁移失败")
            break

    logger.info("\n" + '=' * 60)
    logger.info('迁移任务完成')
    logger.info('=' * 60)

if __name__ == '__main__':
    main()