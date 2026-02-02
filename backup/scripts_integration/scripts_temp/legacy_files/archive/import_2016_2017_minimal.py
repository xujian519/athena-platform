#!/usr/bin/env python3
"""
2016-2017年专利数据最小化导入脚本
只导入核心必需字段
"""

import csv
import logging
import os
import sys
import time

import psycopg2

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('import_2016_2017_minimal.log'),
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

def import_year_minimal(year, batch_size=1000, limit=10000):
    """最小化导入一年的专利数据"""
    file_path = f"/Volumes/xujian/patent_data/china_patents/中国专利数据库{year}年.csv"

    logger.info(f"开始处理{year}年数据: {file_path}")
    logger.info(f"限制导入前 {limit} 条记录用于测试")

    # 检查文件是否存在
    if not os.path.exists(file_path):
        logger.error(f"文件不存在: {file_path}")
        return False

    try:
        conn = get_connection()
        if not conn:
            return False

        cursor = conn.cursor()

        with open(file_path, 'r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)

            records = []
            processed = 0
            row_num = 0

            for row in reader:
                row_num += 1
                if row_num > limit:
                    break

                try:
                    # 只提取核心必需字段
                    patent_name = row.get('专利名称', '').strip()
                    patent_name = patent_name[:1000] if patent_name else None  # 限制长度

                    patent_type = row.get('专利类型', '').strip()
                    patent_type = patent_type[:50] if patent_type else None

                    applicant = row.get('申请人', '').strip()
                    applicant = applicant[:500] if applicant else None

                    application_number = row.get('申请号', '').strip()
                    application_number = application_number[:100] if application_number else None

                    # 如果没有申请号，跳过
                    if not application_number:
                        continue

                    # 只插入必需字段
                    cursor.execute("""
                        INSERT INTO patents (
                            patent_name, patent_type, application_number,
                            applicant, source_year, source_file
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (application_number) DO NOTHING
                    """, (
                        patent_name,
                        patent_type,
                        application_number,
                        applicant,
                        year,
                        f'中国专利数据库{year}年.csv'
                    ))

                    processed += 1

                    # 每1000条提交一次
                    if processed % batch_size == 0:
                        conn.commit()
                        logger.info(f"已处理 {processed:,} 条记录")

                except Exception as e:
                    logger.error(f"处理第{row_num}行失败: {e}")
                    continue

            # 最终提交
            conn.commit()
            cursor.close()
            conn.close()

            logger.info(f"✅ {year}年最小化导入完成")
            logger.info(f"  处理: {processed:,} 条")
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
    logger.info('开始最小化导入2016-2017年专利数据（仅核心字段）')
    logger.info('=' * 80)

    years = [2016, 2017]

    for year in years:
        logger.info(f"\n开始处理 {year} 年数据...")
        success = import_year_minimal(year, batch_size=1000, limit=10000)

        if not success:
            logger.error(f"❌ {year}年数据导入失败")
            return False

        logger.info(f"{year}年数据处理完成，休息10秒...")
        time.sleep(10)

    logger.info('✅ 所有年份数据导入成功！')
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)