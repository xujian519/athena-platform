#!/usr/bin/env python3
"""
批量迁移专利数据脚本
优化版本，支持高效迁移大量数据
"""

import logging
import sys
import time
from datetime import datetime

import psycopg2

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
        logger.info(f"❌ 数据库连接失败: {e}")
        return None

def get_migration_years():
    """获取需要迁移的年份"""
    years = []

    # 从命令行参数获取年份
    if len(sys.argv) > 1:
        years = [int(arg) for arg in sys.argv[1:]]
    else:
        # 默认迁移所有待处理的年份
        years = [2015, 2020, 2021, 2025]

    return years

def check_year_status(conn, year):
    """检查某年的迁移状态"""
    cursor = conn.cursor()

    # 检查简化表中的数据量
    cursor.execute("""
        SELECT COUNT(*)
        FROM patents_simple
        WHERE source_year = %s
    """, (year,))
    simple_count = cursor.fetchone()[0]

    # 检查主表中的数据量
    cursor.execute("""
        SELECT COUNT(*)
        FROM patents
        WHERE source_year = %s
    """, (year,))
    main_count = cursor.fetchone()[0]

    cursor.close()

    return simple_count, main_count

def migrate_year(conn, year, batch_size=10000):
    """迁移一年的数据，使用批量处理"""
    cursor = conn.cursor()

    logger.info(f"\n🚀 开始迁移 {year} 年数据...")

    # 获取总记录数
    cursor.execute("""
        SELECT COUNT(*)
        FROM patents_simple
        WHERE source_year = %s
    """, (year,))
    total_records = cursor.fetchone()[0]

    if total_records == 0:
        logger.info(f"⚠️  {year} 年没有数据需要迁移")
        cursor.close()
        return 0

    logger.info(f"📊 {year} 年共有 {total_records:,} 条记录需要迁移")

    # 使用批量插入
    offset = 0
    migrated = 0

    while offset < total_records:
        # 获取一批数据
        cursor.execute("""
            SELECT
                patent_name,
                patent_type,
                application_number,
                application_date,
                applicant,
                inventor,
                ipc_code,
                abstract,
                source_year
            FROM patents_simple
            WHERE source_year = %s
            ORDER BY id
            LIMIT %s OFFSET %s
        """, (year, batch_size, offset))

        batch_data = cursor.fetchall()

        if not batch_data:
            break

        # 准备插入数据
        insert_data = []
        for row in batch_data:
            try:
                # 确保行有正确的字段数
                if len(row) != 9:
                    logger.info(f"⚠️  跳过字段数不正确的行: {len(row)}个字段")
                    continue

                patent_name, patent_type, application_number, application_date, applicant, inventor, ipc_code, abstract, source_year = row

                # 处理可能的None值
                ipc_code = ipc_code if ipc_code else ''
                abstract = abstract if abstract else ''

                insert_data.append((
                    patent_name,
                    patent_type,
                    application_number,
                    application_date,
                    None,  # publication_number
                    None,  # publication_date
                    None,  # authorization_number
                    None,  # authorization_date
                    applicant,
                    None,  # applicant_type
                    None,  # applicant_address
                    None,  # applicant_region
                    None,  # applicant_city
                    None,  # applicant_district
                    None,  # current_assignee
                    None,  # current_assignee_address
                    None,  # assignee_type
                    None,  # credit_code
                    inventor,
                    ipc_code,
                    ipc_code[:4] if ipc_code and len(ipc_code) >= 4 else None,  # ipc_main_class
                    ipc_code,  # ipc_classification
                    abstract,
                    None,  # claims_content
                    None,  # claims
                    0,  # citation_count
                    0,  # cited_count
                    0,  # self_citation_count
                    0,  # other_citation_count
                    0,  # cited_by_self_count
                    0,  # cited_by_others_count
                    0,  # family_citation_count
                    0,  # family_cited_count
                    source_year,
                    f'中国专利数据库{source_year}年.csv',  # source_file
                    None  # file_hash
                ))
            except Exception as e:
                logger.info(f"⚠️  处理行数据时出错: {e}, 行数据: {row[:2]}...")
                continue

        # 执行批量插入
        try:
            cursor.executemany("""
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
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (application_number) DO NOTHING
            """, insert_data)

            conn.commit()
            migrated += len(insert_data)
            offset += batch_size

            # 显示进度
            progress = (offset / total_records) * 100
            logger.info(f"✅ {year} 年迁移进度: {migrated:,}/{total_records:,} ({progress:.1f}%)")

        except Exception as e:
            conn.rollback()
            logger.info(f"❌ {year} 年迁移失败: {e}")
            cursor.close()
            return migrated

    cursor.close()
    return migrated

def main():
    """主函数"""
    logger.info(str('=' * 80))
    logger.info('📊 专利数据批量迁移工具')
    logger.info(str('=' * 80))

    # 获取要迁移的年份
    years = get_migration_years()
    logger.info(f"📋 计划迁移年份: {', '.join(map(str, years))}")

    # 创建数据库连接
    conn = create_connection()
    if not conn:
        return

    try:
        # 显示初始状态
        logger.info("\n📈 迁移前状态:")
        logger.info(str('-' * 60))
        for year in years:
            simple_count, main_count = check_year_status(conn, year)
            logger.info(f"{year}年: 简化表 {simple_count:,}, 主表 {main_count:,}")

        # 开始迁移
        total_migrated = 0
        start_time = time.time()

        for year in years:
            migrated = migrate_year(conn, year, batch_size=5000)
            total_migrated += migrated

            if migrated > 0:
                logger.info(f"✅ {year} 年成功迁移 {migrated:,} 条记录")
            else:
                logger.info(f"⚠️  {year} 年没有新增迁移记录")

        # 显示最终结果
        end_time = time.time()
        elapsed = end_time - start_time

        logger.info(str("\n" + '=' * 80))
        logger.info('📊 迁移完成统计')
        logger.info(str('=' * 80))
        logger.info(f"🕐 总耗时: {elapsed:.1f} 秒")
        logger.info(f"📈 总迁移记录数: {total_migrated:,}")
        logger.info(f"⚡ 平均速度: {total_migrated/elapsed:.0f} 条/秒")

        logger.info("\n📋 迁移后状态:")
        logger.info(str('-' * 60))
        for year in years:
            simple_count, main_count = check_year_status(conn, year)
            percentage = (main_count / simple_count * 100) if simple_count > 0 else 0
            logger.info(f"{year}年: 简化表 {simple_count:,}, 主表 {main_count:,} ({percentage:.1f}%)")

    except Exception as e:
        logger.info(f"❌ 迁移过程出错: {e}")
    finally:
        conn.close()

    logger.info("\n🎉 迁移任务完成!")

if __name__ == '__main__':
    main()