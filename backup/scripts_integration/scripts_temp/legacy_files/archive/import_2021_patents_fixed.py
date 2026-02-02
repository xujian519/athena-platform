#!/usr/bin/env python3
"""
修复版：导入2021年中国专利数据到PostgreSQL数据库
解决BOM标记、字段数量和编码问题
"""

import csv
import logging
import os
import sys
import time
from datetime import datetime

import psycopg2

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('import_2021_fixed.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def import_2021_patents():
    """导入2021年专利数据"""
    logger.info('🚀 开始导入2021年专利数据（修复版）')
    logger.info(f"📅 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 文件路径
    csv_file = '/Volumes/xujian/patent_data/china_patents/中国专利数据库2021年.csv'

    if not os.path.exists(csv_file):
        logger.error(f"❌ 文件不存在: {csv_file}")
        return False

    # 检查文件大小
    file_size = os.path.getsize(csv_file) / 1024 / 1024 / 1024  # GB
    logger.info(f"📊 文件大小: {file_size:.2f} GB")

    # 数据库连接
    conn = None
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password='postgres',
            database='patent_db'
        )
        cursor = conn.cursor()

        # 创建批量插入语句
        insert_sql = """
            INSERT INTO patents (
                patent_name, patent_type, applicant, applicant_type, applicant_address,
                applicant_region, applicant_city, applicant_district, application_number,
                application_date, application_year, publication_number, publication_date,
                publication_year, authorization_number, authorization_date, authorization_year,
                ipc_code, ipc_main_class, inventor, abstract, claims_content,
                current_owner, current_owner_address, owner_type, unified_social_credit_code,
                citation_count, cited_count, self_citation_count, other_citation_count,
                cited_by_self_count, cited_by_others_count, family_citation_count,
                family_cited_count, source_year
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (application_number) DO NOTHING
        """

        # 解析函数
        def parse_date(date_str):
            if not date_str or date_str.strip() == '' or date_str.strip() == '0':
                return None
            try:
                # 尝试多种日期格式
                if '-' in date_str:
                    return datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
                elif len(date_str.strip()) == 8:
                    return datetime.strptime(date_str.strip(), '%Y%m%d').date()
                return None
            except:
                return None

        def parse_int(num_str):
            if not num_str or num_str.strip() == '' or num_str.strip() == '0':
                return 0
            try:
                return int(float(num_str.strip()))
            except:
                return 0

        # 批量插入数据
        logger.info('📖 开始读取和导入数据...')

        batch_size = 1000
        batch_values = []
        total_processed = 0
        total_errors = 0
        start_time = time.time()

        with open(csv_file, 'r', encoding='utf-8-sig') as f:  # 使用utf-8-sig自动处理BOM
            reader = csv.reader(f)
            header = next(reader)  # 跳过表头
            logger.info(f"✅ 表头读取成功，字段数: {len(header)}")

            for row_num, row in enumerate(reader, 2):  # 从第2行开始
                try:
                    if len(row) != 34:
                        logger.warning(f"第{row_num}行: 字段数不匹配 {len(row)} != 34")
                        total_errors += 1
                        continue

                    # 处理空值
                    row = [field if field else '' for field in row]

                    patent_data = [
                        row[0].strip(),   # patent_name
                        row[1].strip(),   # patent_type
                        row[2].strip(),   # applicant
                        row[3].strip(),   # applicant_type
                        row[4].strip(),   # applicant_address
                        row[5].strip(),   # applicant_region
                        row[6].strip(),   # applicant_city
                        row[7].strip(),   # applicant_district
                        row[8].strip(),   # application_number
                        parse_date(row[9]),  # application_date
                        parse_int(row[10]),   # application_year
                        row[11].strip(),  # publication_number
                        parse_date(row[12]),  # publication_date
                        parse_int(row[13]),   # publication_year
                        row[14].strip(),  # authorization_number
                        parse_date(row[15]),  # authorization_date
                        parse_int(row[16]),   # authorization_year
                        row[17].strip(),  # ipc_code
                        row[18].strip(),  # ipc_main_class
                        row[19].strip(),  # inventor
                        row[20].strip(),  # abstract
                        row[21].strip(),  # claims_content
                        row[22].strip(),  # current_owner
                        row[23].strip(),  # current_owner_address
                        row[24].strip(),  # owner_type
                        row[25].strip(),  # unified_social_credit_code
                        parse_int(row[26]),   # citation_count
                        parse_int(row[27]),   # cited_count
                        parse_int(row[28]),   # self_citation_count
                        parse_int(row[29]),   # other_citation_count
                        parse_int(row[30]),   # cited_by_self_count
                        parse_int(row[31]),   # cited_by_others_count
                        parse_int(row[32]),   # family_citation_count
                        parse_int(row[33]),   # family_cited_count
                        2021,            # source_year
                    ]

                    batch_values.append(patent_data)
                    total_processed += 1

                    # 批量插入
                    if len(batch_values) >= batch_size:
                        cursor.executemany(insert_sql, batch_values)
                        conn.commit()
                        logger.info(f"✅ 已处理 {total_processed:,} 条记录")
                        batch_values = []

                except Exception as e:
                    logger.error(f"第{row_num}行处理失败: {e}")
                    total_errors += 1
                    continue

                # 进度显示
                if total_processed % 10000 == 0:
                    elapsed = time.time() - start_time
                    rate = total_processed / elapsed if elapsed > 0 else 0
                    logger.info(f"📊 进度: {total_processed:,} 条, 速度: {rate:.1f} 条/秒")

            # 插入剩余数据
            if batch_values:
                cursor.executemany(insert_sql, batch_values)
                conn.commit()
                logger.info(f"✅ 已处理最后一批 {len(batch_values):,} 条记录")

        # 统计结果
        total_time = time.time() - start_time
        rate = total_processed / total_time if total_time > 0 else 0

        logger.info("\n" + '='*60)
        logger.info('🎉 2021年专利数据导入完成!')
        logger.info(f"📊 总处理: {total_processed:,} 条")
        logger.info(f"❌ 总错误: {total_errors:,} 条")
        logger.info(f"⏱️ 总耗时: {total_time:.1f} 秒 ({total_time/60:.1f} 分钟)")
        logger.info(f"🚀 平均速度: {rate:.1f} 条/秒")

        # 更新数据库统计
        cursor.execute('SELECT COUNT(*) FROM patents WHERE source_year = 2021')
        count_2021 = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM patents')
        total_count = cursor.fetchone()[0]
        cursor.close()

        logger.info(f"📈 数据库中2021年专利数: {count_2021:,}")
        logger.info(f"📈 数据库总专利数: {total_count:,}")

        return True

    except Exception as e:
        logger.error(f"❌ 导入过程失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    success = import_2021_patents()
    sys.exit(0 if success else 1)