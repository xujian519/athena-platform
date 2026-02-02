#!/usr/bin/env python3
"""
单线程导入单年专利数据
避免死锁问题
"""

import csv
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

import psycopg2

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def import_year(year):
    """导入单年数据"""
    csv_file = f"/Volumes/xujian/patent_data/china_patents/中国专利数据库{year}年.csv"

    if not Path(csv_file).exists():
        logger.error(f"文件不存在: {csv_file}")
        return False

    # 连接数据库
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='patent_db',
        user='postgres',
        password='postgres'
    )

    cursor = conn.cursor()

    # 准备INSERT语句（简化版）
    insert_sql = """
        INSERT INTO patents (
            patent_name, patent_type, application_number, application_date,
            publication_number, publication_date, authorization_number,
            authorization_date, applicant, applicant_type, applicant_address,
            applicant_region, applicant_city, applicant_district,
            current_assignee, current_assignee_address, assignee_type,
            credit_code, inventor, ipc_code, ipc_main_class,
            ipc_classification, abstract, claims_content, claims,
            citation_count, cited_count, self_citation_count,
            other_citation_count, cited_by_self_count, cited_by_others_count,
            family_citation_count, family_cited_count,
            source_year, source_file, file_hash
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (application_number) DO NOTHING
    """

    start_time = time.time()
    total_records = 0
    success_count = 0
    batch_size = 1000

    logger.info(f"开始导入 {year} 年数据")

    try:
        with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            next(reader)  # 跳过标题行

            batch = []
            for row_num, row in enumerate(reader, start=2):
                try:
                    # 解析数据
                    patent_name = row[0] if row[0] else None
                    patent_type = '发明' if '发明' in (row[1] or '') else ('实用新型' if '实用' in (row[1] or '') else '外观设计')
                    application_number = row[8] if len(row) > 8 and row[8] else None

                    # 跳过无效记录
                    if not application_number or len(application_number) < 5:
                        continue

                    values = (
                        patent_name,
                        patent_type,
                        application_number,
                        None,  # application_date
                        row[11] if len(row) > 11 else None,  # publication_number
                        None,  # publication_date
                        row[15] if len(row) > 15 else None,  # authorization_number
                        None,  # authorization_date
                        row[2] if row[2] else '未知申请人',  # applicant
                        None,  # applicant_type
                        None,  # applicant_address
                        None,  # applicant_region
                        None,  # applicant_city
                        None,  # applicant_district
                        row[22] if len(row) > 22 else None,  # current_assignee
                        None,  # current_assignee_address
                        None,  # assignee_type
                        None,  # credit_code
                        row[19] if len(row) > 19 else None,  # inventor
                        row[17] if len(row) > 17 else None,  # ipc_code
                        row[17][:4] if len(row) > 17 and len(row[17]) >= 4 else None,  # ipc_main_class
                        row[17] if len(row) > 17 else None,  # ipc_classification
                        row[20] if len(row) > 20 else None,  # abstract
                        row[21] if len(row) > 21 else None,  # claims_content
                        row[21] if len(row) > 21 else None,  # claims
                        0, 0, 0, 0, 0, 0, 0, 0,  # 引用计数
                        year,  # source_year
                        f'中国专利数据库{year}年.csv',  # source_file
                        None   # file_hash
                    )

                    batch.append(values)
                    total_records += 1

                    # 批量插入
                    if len(batch) >= batch_size:
                        cursor.executemany(insert_sql, batch)
                        conn.commit()
                        success_count += len(batch)
                        batch = []

                        # 显示进度
                        if total_records % 10000 == 0:
                            elapsed = time.time() - start_time
                            speed = total_records / elapsed
                            logger.info(f"  进度: {total_records:,} 条记录 (速度: {speed:.1f} 记录/秒)")

                except Exception as e:
                    logger.warning(f"  第{row_num}行解析失败: {str(e)[:100]}")
                    continue

            # 处理剩余记录
            if batch:
                cursor.executemany(insert_sql, batch)
                conn.commit()
                success_count += len(batch)

        elapsed = time.time() - start_time
        speed = total_records / elapsed if elapsed > 0 else 0

        logger.info(f"\n✅ {year}年导入完成!")
        logger.info(f"  处理记录: {total_records:,}")
        logger.info(f"  成功导入: {success_count:,}")
        logger.info(f"  耗时: {elapsed:.1f}秒")
        logger.info(f"  平均速度: {speed:.1f} 记录/秒")

        return True

    except Exception as e:
        logger.error(f"❌ 导入失败: {str(e)}")
        conn.rollback()
        return False

    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        logger.info('用法: python3 import_single_year.py <年份>')
        sys.exit(1)

    year = int(sys.argv[1])
    import_year(year)