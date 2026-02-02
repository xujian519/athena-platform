#!/usr/bin/env python3
"""
修正版：将2016年和2017年专利数据分批导入到patents主表
正确处理34列的CSV文件格式
"""

import csv
import logging
import os
import sys
import time
from datetime import datetime

import psycopg2

# 导入标准化数据库工具
from shared.database.db_utils import DatabaseManager, build_safe_query

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('import_2016_2017_corrected.log'),
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

def count_lines(file_path):
    """快速统计CSV文件的行数"""
    count = 0
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            count += 1
    return count - 1  # 减去表头

def import_year_to_patents(year, batch_size=1000):
    """将一年的数据分批导入到patents主表"""
    file_path = f"/Volumes/xujian/patent_data/china_patents/中国专利数据库{year}年.csv"

    logger.info(f"开始处理{year}年数据: {file_path}")

    # 检查文件是否存在
    if not os.path.exists(file_path):
        logger.error(f"文件不存在: {file_path}")
        return False

    try:
        total_lines = count_lines(file_path)
        logger.info(f"{year}年数据总行数: {total_lines:,}")
    except Exception as e:
        logger.error(f"无法读取文件: {e}")
        return False

    # 检查是否已经导入
    conn = get_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM patents WHERE source_year = %s', (year,))
        existing = cursor.fetchone()[0]

        if existing > 0:
            logger.warning(f"{year}年数据已存在 {existing:,} 条，将检查并只导入新数据")

        cursor.close()
        conn.close()
    except Exception as e:
        logger.error(f"检查现有数据失败: {e}")
        conn.close()
        return False

    # 分批读取并导入
    processed = 0
    start_time = time.time()

    try:
        conn = get_connection()
        if not conn:
            return False

        cursor = conn.cursor()

        with open(file_path, 'r', encoding='utf-8-sig') as csvfile:  # 使用utf-8-sig处理BOM
            reader = csv.DictReader(csvfile)

            records = []
            for row_num, row in enumerate(reader, 1):
                # 处理每行数据
                # 注意：第一列名可能有BOM字符，需要strip
                patent_name = row.get('\ufeff专利名称') or row.get('专利名称') or row.get('﻿专利名称')
                patent_name = patent_name.strip() if patent_name else None

                patent_type = row.get('专利类型', '').strip()
                applicant = row.get('申请人', '').strip()
                applicant_type = row.get('申请人类型', '').strip()
                applicant_address = row.get('申请人地址', '').strip()
                applicant_region = row.get('申请人地区', '').strip()
                applicant_city = row.get('申请人城市', '').strip()
                applicant_district = row.get('申请人区县', '').strip()
                application_number = row.get('申请号', '').strip()
                application_date = row.get('申请日', '').strip()
                publication_number = row.get('公开公告号', '').strip()
                publication_date = row.get('公开公告日', '').strip()
                authorization_number = row.get('授权公告号', '').strip()
                authorization_date = row.get('授权公告日', '').strip()
                ipc_code = row.get('IPC分类号', '').strip()
                ipc_main_class = row.get('IPC主分类号', '').strip()
                inventor = row.get('发明人', '').strip()
                abstract = row.get('摘要文本', '').strip()
                claims_content = row.get('主权项内容', '').strip()
                current_assignee = row.get('当前权利人', '').strip()
                current_assignee_address = row.get('当前专利权人地址', '').strip()
                assignee_type = row.get('专利权人类型', '').strip()
                credit_code = row.get('统一社会信用代码', '').strip()

                # 引证次数相关字段
                citation_count = int(float(row.get('引证次数', 0) or 0))
                cited_count = int(float(row.get('被引证次数', 0) or 0))
                self_citation_count = int(float(row.get('自引次数', 0) or 0))
                other_citation_count = int(float(row.get('他引次数', 0) or 0))
                cited_by_self_count = int(float(row.get('被自引次数', 0) or 0))
                cited_by_others_count = int(float(row.get('被他引次数', 0) or 0))
                family_citation_count = int(float(row.get('家族引证次数', 0) or 0))
                family_cited_count = int(float(row.get('家族被引证次数', 0) or 0))

                # 构建patents表记录
                records.append((
                    patent_name,  # patent_name
                    patent_type if patent_type else None,  # patent_type
                    application_number if application_number else None,  # application_number
                    application_date if application_date else None,  # application_date
                    publication_number if publication_number else None,  # publication_number
                    publication_date if publication_date else None,  # publication_date
                    authorization_number if authorization_number else None,  # authorization_number
                    authorization_date if authorization_date else None,  # authorization_date
                    applicant if applicant else None,  # applicant
                    applicant_type if applicant_type else None,  # applicant_type
                    applicant_address if applicant_address else None,  # applicant_address
                    applicant_region if applicant_region else None,  # applicant_region
                    applicant_city if applicant_city else None,  # applicant_city
                    applicant_district if applicant_district else None,  # applicant_district
                    current_assignee if current_assignee else None,  # current_assignee
                    current_assignee_address if current_assignee_address else None,  # current_assignee_address
                    assignee_type if assignee_type else None,  # assignee_type
                    credit_code if credit_code else None,  # credit_code
                    inventor if inventor else None,  # inventor
                    ipc_code if ipc_code else None,  # ipc_code
                    ipc_main_class if ipc_main_class else None,  # ipc_main_class
                    ipc_code if ipc_code else None,  # ipc_classification
                    abstract if abstract else None,  # abstract
                    claims_content if claims_content else None,  # claims_content
                    None,  # claims
                    citation_count,  # citation_count
                    cited_count,  # cited_count
                    self_citation_count,  # self_citation_count
                    other_citation_count,  # other_citation_count
                    cited_by_self_count,  # cited_by_self_count
                    cited_by_others_count,  # cited_by_others_count
                    family_citation_count,  # family_citation_count
                    family_cited_count,  # family_cited_count
                    year,  # source_year
                    f'中国专利数据库{year}年.csv',  # source_file
                    None  # file_hash
                ))

                # 当达到批次大小时，执行插入
                if len(records) >= batch_size:
                    batch_start = time.time()

                    # 批量插入
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
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (application_number) DO NOTHING
                        """, records)
                    except Exception as e:
                        logger.error(f"插入数据失败: {e}")
                        records = []
                        continue

                    conn.commit()
                    processed += len(records)

                    # 显示进度
                    batch_time = time.time() - batch_start
                    speed = len(records) / batch_time if batch_time > 0 else 0
                    progress = (row_num / total_lines) * 100
                    total_time = time.time() - start_time
                    avg_speed = processed / total_time if total_time > 0 else 0

                    logger.info(f"{year}年: 处理 {len(records):,} 条, "
                               f"累计 {processed:,} 条 ({progress:.1f}%), "
                               f"批次速度 {speed:.0f} 条/秒, 平均速度 {avg_speed:.0f} 条/秒")

                    # 清空记录列表，准备下一批
                    records = []

                    # 短暂休息
                    time.sleep(0.1)

            # 处理最后一批记录
            if records:
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
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (application_number) DO NOTHING
                """, records)
                conn.commit()
                processed += len(records)
                logger.info(f"{year}年: 处理最后 {len(records):,} 条, 累计 {processed:,} 条")

        cursor.close()
        conn.close()

        total_time = time.time() - start_time
        logger.info(f"✅ {year}年数据导入完成，共处理 {processed:,} 条记录，总耗时 {total_time:.1f} 秒")
        return True

    except Exception as e:
        logger.error(f"{year}年导入失败: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

def main():
    """主函数"""
    logger.info('=' * 80)
    logger.info('开始分批导入2016-2017年专利数据到patents主表（修正版）')
    logger.info('=' * 80)

    years = [2016, 2017]

    for year in years:
        logger.info(f"\n开始处理 {year} 年数据...")
        success = import_year_to_patents(year, batch_size=1000)  # 初始批次大小1000

        if not success:
            logger.error(f"❌ {year}年数据导入失败")
            return False

        # 年份之间休息一下
        logger.info(f"{year}年数据处理完成，休息30秒...")
        time.sleep(30)

    logger.info('✅ 所有年份数据导入成功！')
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)