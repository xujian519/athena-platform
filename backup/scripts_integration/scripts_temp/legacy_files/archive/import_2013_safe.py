#!/usr/bin/env python3
"""
安全导入2013年专利数据
基于实际的34列格式
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

# 定义字段映射（基于分析结果）
FIELD_MAPPING = {
    'patent_name': 0,         # 专利名称
    'patent_type': 1,         # 专利类型
    'applicant': 2,           # 申请人
    'applicant_type': 3,      # 申请人类型
    'applicant_address': 4,   # 申请人地址
    'applicant_region': 5,    # 申请人地区
    'applicant_city': 6,      # 申请人城市
    'applicant_district': 7,  # 申请人区县
    'application_number': 8,  # 申请号
    'application_date': 9,    # 申请日
    'application_year': 10,   # 申请年份
    'publication_number': 11, # 公开公告号
    'publication_date': 12,   # 公开公告日
    'publication_year': 13,   # 公开公告年份
    'authorization_number': 15, # 授权公告号
    'authorization_date': 16,   # 授权公告日
    'authorization_year': 17,   # 授权公告年份
    'ipc_code': 17,           # IPC分类号
    'ipc_main_class': 18,     # IPC主分类号
    'inventor': 19,           # 发明人
    'abstract': 20,           # 摘要文本
    'claims_content': 21,     # 主权项内容
    'current_assignee': 22,   # 当前权利人
    'current_assignee_address': 23, # 当前专利权人地址
    'assignee_type': 24,      # 专利权人类型
    'credit_code': 25,        # 统一社会信用代码
    'citation_count': 26,     # 引证次数
    'cited_count': 27,        # 被引证次数
    'self_citation_count': 28, # 自引次数
    'other_citation_count': 29, # 他引次数
    'cited_by_self_count': 30, # 被自引次数
    'cited_by_others_count': 31, # 被他引次数
    'family_citation_count': 32, # 家族引证次数
    'family_cited_count': 33,   # 家族被引证次数
}

def safe_get(row, index, default=None):
    """安全获取字段值"""
    if index < len(row) and row[index]:
        return row[index].strip() if row[index].strip() else default
    return default

def parse_date(date_str):
    """解析日期字符串"""
    if not date_str or len(date_str) < 8:
        return None
    try:
        # 处理各种日期格式
        date_str = date_str.replace('.', '').replace('-', '')
        if len(date_str) == 8:
            return datetime.strptime(date_str, '%Y%m%d').date()
        elif len(date_str) > 8:
            return datetime.strptime(date_str[:8], '%Y%m%d').date()
    except:
        pass
    return None

def normalize_patent_type(patent_type):
    """标准化专利类型"""
    if not patent_type:
        return None
    if '发明' in patent_type:
        return '发明'
    elif '实用' in patent_type:
        return '实用新型'
    elif '外观' in patent_type:
        return '外观设计'
    return patent_type

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

    # 准备INSERT语句
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
                    # 使用安全的方式获取字段
                    application_number = safe_get(row, FIELD_MAPPING['application_number'])

                    # 跳过无效记录
                    if not application_number or len(application_number) < 5:
                        continue

                    values = (
                        safe_get(row, FIELD_MAPPING['patent_name']),  # patent_name
                        normalize_patent_type(safe_get(row, FIELD_MAPPING['patent_type'])),  # patent_type
                        application_number,  # application_number
                        parse_date(safe_get(row, FIELD_MAPPING['application_date'])),  # application_date
                        safe_get(row, FIELD_MAPPING['publication_number']),  # publication_number
                        parse_date(safe_get(row, FIELD_MAPPING['publication_date'])),  # publication_date
                        safe_get(row, FIELD_MAPPING['authorization_number']),  # authorization_number
                        parse_date(safe_get(row, FIELD_MAPPING['authorization_date'])),  # authorization_date
                        safe_get(row, FIELD_MAPPING['applicant']) or '未知申请人',  # applicant
                        safe_get(row, FIELD_MAPPING['applicant_type']),  # applicant_type
                        safe_get(row, FIELD_MAPPING['applicant_address']),  # applicant_address
                        safe_get(row, FIELD_MAPPING['applicant_region']),  # applicant_region
                        safe_get(row, FIELD_MAPPING['applicant_city']),  # applicant_city
                        safe_get(row, FIELD_MAPPING['applicant_district']),  # applicant_district
                        safe_get(row, FIELD_MAPPING['current_assignee']),  # current_assignee
                        safe_get(row, FIELD_MAPPING['current_assignee_address']),  # current_assignee_address
                        safe_get(row, FIELD_MAPPING['assignee_type']),  # assignee_type
                        safe_get(row, FIELD_MAPPING['credit_code']),  # credit_code
                        safe_get(row, FIELD_MAPPING['inventor']),  # inventor
                        safe_get(row, FIELD_MAPPING['ipc_code']),  # ipc_code
                        safe_get(row, FIELD_MAPPING['ipc_main_class']),  # ipc_main_class
                        safe_get(row, FIELD_MAPPING['ipc_code']),  # ipc_classification
                        safe_get(row, FIELD_MAPPING['abstract']),  # abstract
                        safe_get(row, FIELD_MAPPING['claims_content']),  # claims_content
                        safe_get(row, FIELD_MAPPING['claims_content']),  # claims
                        safe_int(safe_get(row, FIELD_MAPPING['citation_count'])),  # citation_count
                        safe_int(safe_get(row, FIELD_MAPPING['cited_count'])),  # cited_count
                        safe_int(safe_get(row, FIELD_MAPPING['self_citation_count'])),  # self_citation_count
                        safe_int(safe_get(row, FIELD_MAPPING['other_citation_count'])),  # other_citation_count
                        safe_int(safe_get(row, FIELD_MAPPING['cited_by_self_count'])),  # cited_by_self_count
                        safe_int(safe_get(row, FIELD_MAPPING['cited_by_others_count'])),  # cited_by_others_count
                        safe_int(safe_get(row, FIELD_MAPPING['family_citation_count'])),  # family_citation_count
                        safe_int(safe_get(row, FIELD_MAPPING['family_cited_count'])),  # family_cited_count
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

def safe_int(value, default=0):
    """安全转换为整数"""
    try:
        if not value or value.strip() == '':
            return default
        return int(float(value))
    except:
        return default

if __name__ == '__main__':
    if len(sys.argv) != 2:
        logger.info('用法: python3 import_2013_safe.py <年份>')
        sys.exit(1)

    year = int(sys.argv[1])
    import_year(year)