#!/usr/bin/env python3
"""
将2016年和2017年专利数据直接导入到patents主表
"""

import logging
import sys
import time
from datetime import datetime

import pandas as pd
import psycopg2

# 导入标准化数据库工具
from shared.database.db_utils import DatabaseManager, build_safe_query

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('import_2016_2017_patents.log'),
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
    with open(file_path, 'r', encoding='utf-8') as f:
        return sum(1 for _ in f) - 1  # 减去表头

def import_year_to_patents(year):
    """将一年的数据直接导入到patents主表"""
    file_path = f"/Volumes/xujian/patent_data/china_patents/中国专利数据库{year}年.csv"

    logger.info(f"开始处理{year}年数据: {file_path}")

    # 检查文件是否存在
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
            logger.warning(f"{year}年数据已存在 {existing:,} 条，将跳过导入")
            cursor.close()
            conn.close()
            return True

        cursor.close()
        conn.close()
    except Exception as e:
        logger.error(f"检查现有数据失败: {e}")
        conn.close()
        return False

    # 分块读取并导入
    chunk_size = 5000  # 每批5000条，减少内存压力
    processed = 0

    try:
        # 使用pandas读取CSV
        reader = pd.read_csv(file_path, chunksize=chunk_size, encoding='utf-8')

        conn = get_connection()
        if not conn:
            return False

        cursor = conn.cursor()

        for chunk in reader:
            start_time = time.time()

            # 处理数据
            records = []
            for _, row in chunk.iterrows():
                # 确保字段存在，如果不存在则设为None
                patent_name = str(row.get('专利名称', '')) if pd.notna(row.get('专利名称')) else None
                patent_type = str(row.get('专利类型', '')) if pd.notna(row.get('专利类型')) else None
                application_number = str(row.get('申请号', '')) if pd.notna(row.get('申请号')) else None
                application_date = str(row.get('申请日', '')) if pd.notna(row.get('申请日')) else None
                applicant = str(row.get('申请人', '')) if pd.notna(row.get('申请人')) else None
                inventor = str(row.get('发明人', '')) if pd.notna(row.get('发明人')) else None
                ipc_code = str(row.get('IPC分类号', '')) if pd.notna(row.get('IPC分类号')) else None
                abstract = str(row.get('摘要', '')) if pd.notna(row.get('摘要')) else None

                # 构建完整的patents表记录
                records.append((
                    patent_name,  # patent_name
                    patent_type,  # patent_type
                    application_number,  # application_number
                    application_date,  # application_date
                    None,  # publication_number
                    None,  # publication_date
                    None,  # authorization_number
                    None,  # authorization_date
                    applicant,  # applicant
                    None,  # applicant_type
                    None,  # applicant_address
                    None,  # applicant_region
                    None,  # applicant_city
                    None,  # applicant_district
                    None,  # current_assignee
                    None,  # current_assignee_address
                    None,  # assignee_type
                    None,  # credit_code
                    inventor,  # inventor
                    ipc_code,  # ipc_code
                    ipc_code[:4] if ipc_code and len(ipc_code) >= 4 else None,  # ipc_main_class
                    ipc_code,  # ipc_classification
                    abstract,  # abstract
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
                    year,  # source_year
                    f'中国专利数据库{year}年.csv',  # source_file
                    None  # file_hash
                ))

            # 批量插入到patents表
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
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (application_number) DO NOTHING
                """, records)
            except Exception as e:
                logger.error(f"插入数据失败: {e}")
                # 尝试跳过有问题的记录
                continue

            conn.commit()
            processed += len(records)

            # 显示进度
            chunk_time = time.time() - start_time
            speed = len(records) / chunk_time if chunk_time > 0 else 0
            progress = (processed / total_lines) * 100

            logger.info(f"{year}年: 处理 {len(records):,} 条, "
                       f"累计 {processed:,} 条 ({progress:.1f}%), "
                       f"速度 {speed:.0f} 条/秒")

            # 短暂休息，避免数据库压力过大
            time.sleep(0.1)

        cursor.close()
        conn.close()

        logger.info(f"✅ {year}年数据导入完成，共处理 {processed:,} 条记录")
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
    logger.info('开始导入2016-2017年专利数据到patents主表')
    logger.info('=' * 80)

    years = [2016, 2017]

    for year in years:
        if not import_year_to_patents(year):
            logger.error(f"❌ {year}年数据导入失败")
            return False

    logger.info('✅ 所有年份数据导入成功！')
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)