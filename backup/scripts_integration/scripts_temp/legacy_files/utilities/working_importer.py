#!/usr/bin/env python3
"""
可工作的专利导入脚本
"""

import csv
import logging
import sys
import time
from pathlib import Path

import psycopg2
from psycopg2.extras import DictCursor

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_data():
    """导入数据"""
    # 连接数据库
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='patent_db',
        user='postgres',
        password='postgres'
    )

    cursor = conn.cursor()

    # 准备SQL - 包含所有字段
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
            source_year, source_file, created_at, updated_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        )
        ON CONFLICT (application_number) DO NOTHING
    """

    # 测试单条记录
    csv_file = '/Volumes/xujian/patent_data/china_patents/中国专利数据库2010年.csv'
    with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f)
        next(reader)  # 跳过标题

        # 读取一条数据
        row = next(reader)

        # 构建元组（36个值）
        values = (
            row[0],  # patent_name
            '发明' if '发明' in (row[1] or '') else ('实用新型' if '实用' in (row[1] or '') else '外观设计'),  # patent_type
            row[8],  # application_number
            None,  # application_date
            row[11],  # publication_number
            None,  # publication_date
            row[15],  # authorization_number
            None,  # authorization_date
            row[2] or '未知',  # applicant
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
            0,  # citation_count
            0,  # cited_count
            0,  # self_citation_count
            0,  # other_citation_count
            0,  # cited_by_self_count
            0,  # cited_by_others_count
            0,  # family_citation_count
            0,  # family_cited_count
            2010,  # source_year
            '中国专利数据库2010年.csv',  # source_file
            None,  # file_hash
        )

        logger.info(f"元组长度: {len(values)}")
        logger.info(f"SQL占位符数: {insert_sql.count('%s')}")

        try:
            cursor.execute(insert_sql, values)
            conn.commit()
            logger.info('✅ 测试插入成功！')
        except Exception as e:
            logger.info(f"❌ 插入失败: {str(e)}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

if __name__ == '__main__':
    import_data()