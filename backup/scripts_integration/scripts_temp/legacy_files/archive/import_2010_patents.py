#!/usr/bin/env python3
"""
2010年专利数据导入脚本
使用简化导入方式，只导入核心字段
"""

import argparse
import csv
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import psycopg2

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('documentation/logs/import_2010.log'),
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

def create_simple_table(cursor):
    """创建简化表"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patents_2010 (
            id SERIAL PRIMARY KEY,
            patent_name TEXT,
            patent_type TEXT,
            application_number TEXT UNIQUE,
            application_date DATE,
            publication_number TEXT,
            publication_date DATE,
            applicant TEXT,
            inventor TEXT,
            ipc_code TEXT,
            abstract TEXT,
            source_year INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    logger.info('✅ 创建或确认patents_2010表存在')

def import_2010_data(file_path, batch_size=1000):
    """导入2010年数据"""
    conn = create_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        # 创建简化表
        create_simple_table(cursor)

        # 准备插入语句
        insert_sql = """
            INSERT INTO patents_2010 (
                patent_name, patent_type, application_number, application_date,
                publication_number, publication_date, applicant, inventor,
                ipc_code, abstract, source_year
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (application_number) DO NOTHING
        """

        total_rows = 0
        imported_rows = 0
        batch_data = []

        logger.info(f"📂 开始处理文件: {file_path}")

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            # 尝试检测CSV文件的分隔符
            first_line = f.readline()
            f.seek(0)

            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(first_line).delimiter or ','

            reader = csv.reader(f, delimiter=delimiter)

            # 跳过标题行
            headers = next(reader, None)
            if not headers:
                logger.error('❌ 文件为空')
                return False

            logger.info(f"📋 列数: {len(headers)}")
            logger.info(f"📄 前5列: {headers[:5]}")

            for row_num, row in enumerate(reader, 1):
                total_rows += 1

                # 确保行有足够的列
                if len(row) < 10:
                    # 补充缺失的列
                    row = row + [''] * (10 - len(row))

                # 提取核心字段
                patent_name = row[0] if len(row) > 0 else None
                patent_type = row[1] if len(row) > 1 else None
                application_number = row[2] if len(row) > 2 else None
                application_date = row[3] if len(row) > 3 else None
                publication_number = row[4] if len(row) > 4 else None
                publication_date = row[5] if len(row) > 5 else None
                applicant = row[6] if len(row) > 6 else None
                inventor = row[7] if len(row) > 7 else None
                ipc_code = row[8] if len(row) > 8 else None
                abstract = row[9] if len(row) > 9 else None

                # 处理日期格式
                if application_date:
                    try:
                        if len(application_date) == 8:
                            application_date = f"{application_date[:4]}-{application_date[4:6]}-{application_date[6:8]}"
                        datetime.strptime(application_date, '%Y-%m-%d')
                    except:
                        application_date = None

                if publication_date:
                    try:
                        if len(publication_date) == 8:
                            publication_date = f"{publication_date[:4]}-{publication_date[4:6]}-{publication_date[6:8]}"
                        datetime.strptime(publication_date, '%Y-%m-%d')
                    except:
                        publication_date = None

                batch_data.append((
                    patent_name, patent_type, application_number, application_date,
                    publication_number, publication_date, applicant, inventor,
                    ipc_code, abstract, 2010
                ))

                # 批量插入
                if len(batch_data) >= batch_size:
                    try:
                        cursor.executemany(insert_sql, batch_data)
                        conn.commit()
                        imported_rows += len(batch_data)
                        logger.info(f"✅ 已导入 {imported_rows} 条记录，总行数: {total_rows}")
                        batch_data = []
                    except Exception as e:
                        logger.error(f"❌ 批量插入失败: {e}")
                        conn.rollback()
                        batch_data = []

            # 插入剩余数据
            if batch_data:
                try:
                    cursor.executemany(insert_sql, batch_data)
                    conn.commit()
                    imported_rows += len(batch_data)
                    logger.info(f"✅ 最后批次导入完成，总导入: {imported_rows} 条")
                except Exception as e:
                    logger.error(f"❌ 最后批次插入失败: {e}")
                    conn.rollback()

        logger.info(f"🎉 2010年数据导入完成！")
        logger.info(f"📊 总行数: {total_rows}")
        logger.info(f"✅ 成功导入: {imported_rows} 条")

        return True

    except Exception as e:
        logger.error(f"❌ 导入过程出错: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def migrate_to_main_table():
    """将2010年数据迁移到主表"""
    conn = create_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

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
                p2010.patent_name,
                p2010.patent_type,
                p2010.application_number,
                p2010.application_date,
                p2010.publication_number,
                p2010.publication_date,
                p2010.applicant,
                NULL as applicant_type,
                NULL as applicant_address,
                NULL as applicant_region,
                NULL as applicant_city,
                NULL as applicant_district,
                NULL as current_assignee,
                NULL as current_assignee_address,
                NULL as assignee_type,
                NULL as credit_code,
                p2010.inventor,
                p2010.ipc_code,
                CASE
                    WHEN p2010.ipc_code IS NOT NULL AND LENGTH(p2010.ipc_code) >= 4
                    THEN SUBSTRING(p2010.ipc_code, 1, 4)
                    ELSE NULL
                END as ipc_main_class,
                p2010.ipc_code as ipc_classification,
                p2010.abstract,
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
                2010 as source_year,
                '2010年专利数据' as source_file,
                NULL as file_hash
            FROM patents_2010 p2010
            ON CONFLICT (application_number) DO NOTHING
        """

        cursor.execute(migrate_sql)
        conn.commit()

        # 获取迁移数量
        cursor.execute('SELECT COUNT(*) FROM patents WHERE source_year = 2010')
        count = cursor.fetchone()[0]

        logger.info(f"✅ 2010年数据已迁移到主表，共 {count} 条记录")

        return True

    except Exception as e:
        logger.error(f"❌ 迁移失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='导入2010年专利数据')
    parser.add_argument('--file', type=str, help='2010年数据文件路径')
    parser.add_argument('--batch-size', type=int, default=1000, help='批次大小')
    args = parser.parse_args()

    # 创建日志目录
    os.makedirs('logs', exist_ok=True)

    # 如果没有指定文件，尝试查找2010年数据文件
    if not args.file:
        possible_paths = [
            '/Volumes/xujian/patent_data/china_patents/2010年.csv',
            '/Volumes/xujian/patent_data/china_patents/2010.csv',
            '/Users/xujian/Athena工作平台/data/2010年.csv',
            '/Users/xujian/Athena工作平台/data/2010.csv',
            '/Users/xujian/Athena工作平台/data/中国专利数据库/2010年.csv'
        ]

        for path in possible_paths:
            if os.path.exists(path):
                args.file = path
                break

        if not args.file:
            logger.error('❌ 未找到2010年数据文件，请使用 --file 参数指定')
            return

    # 导入数据
    if import_2010_data(args.file, args.batch_size):
        logger.info('✅ 2010年数据导入成功')

        # 迁移到主表
        if migrate_to_main_table():
            logger.info('✅ 2010年数据已成功迁移到主表')
        else:
            logger.error('❌ 迁移到主表失败')
    else:
        logger.error('❌ 2010年数据导入失败')

if __name__ == '__main__':
    main()