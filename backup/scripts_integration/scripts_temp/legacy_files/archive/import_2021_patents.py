#!/usr/bin/env python3
"""
导入2021年中国专利数据到PostgreSQL数据库
优化的并行导入脚本，处理大量数据
"""

import csv
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from multiprocessing import Pool, cpu_count
from threading import Lock

import psycopg2

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('import_2021.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 线程锁，用于统计信息
stats_lock = Lock()
total_processed = 0
total_errors = 0

def get_csv_header(file_path):
    """获取CSV文件的表头"""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f)
        header = next(reader)
        return header

def create_batch_table(cursor):
    """检查专利表结构"""
    cursor.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'patents' AND column_name = 'source_year'
    """)
    result = cursor.fetchone()

    if not result:
        # 如果没有source_year字段，则添加
        cursor.execute("""
            ALTER TABLE patents
            ADD COLUMN source_year INTEGER
        """)
        logger.info('✅ 添加了 source_year 字段')
    else:
        logger.info('✅ source_year 字段已存在')

def process_chunk(args):
    """处理数据块"""
    file_path, chunk_data, batch_id = args

    conn = None
    processed_count = 0
    error_count = 0

    try:
        # 创建独立的数据库连接
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password='postgres',
            database='patent_db'
        )
        conn.autocommit = False
        cursor = conn.cursor()

        # 准备批量插入
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
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """

        batch_values = []

        for row_num, row in enumerate(chunk_data, 1):
            try:
                # 验证数据长度（35个字段）
                if len(row) != 35:
                    logger.warning(f"批次{batch_id} 行{row_num}: 字段数不匹配 {len(row)} != 35")
                    error_count += 1
                    continue

                # 解析日期
                def parse_date(date_str):
                    if not date_str or date_str.strip() == '':
                        return None
                    try:
                        return datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
                    except:
                        return None

                # 解析年份
                def parse_year(year_str):
                    if not year_str or year_str.strip() == '':
                        return None
                    try:
                        return int(year_str.strip())
                    except:
                        return None

                # 解析数字
                def parse_int(num_str):
                    if not num_str or num_str.strip() == '':
                        return 0
                    try:
                        return int(num_str.strip())
                    except:
                        return 0

                # 构建插入数据
                patent_data = [
                    row[0].strip() if row[0] else '',  # patent_name
                    row[1].strip() if row[1] else '',  # patent_type
                    row[2].strip() if row[2] else '',  # applicant
                    row[3].strip() if row[3] else '',  # applicant_type
                    row[4].strip() if row[4] else '',  # applicant_address
                    row[5].strip() if row[5] else '',  # applicant_region
                    row[6].strip() if row[6] else '',  # applicant_city
                    row[7].strip() if row[7] else '',  # applicant_district
                    row[8].strip() if row[8] else '',  # application_number
                    parse_date(row[9]),               # application_date
                    parse_year(row[10]),              # application_year
                    row[11].strip() if row[11] else '', # publication_number
                    parse_date(row[12]),              # publication_date
                    parse_year(row[13]),              # publication_year
                    row[14].strip() if row[14] else '', # authorization_number
                    parse_date(row[15]),              # authorization_date
                    parse_year(row[16]),              # authorization_year
                    row[17].strip() if row[17] else '', # ipc_code
                    row[18].strip() if row[18] else '', # ipc_main_class
                    row[19].strip() if row[19] else '', # inventor
                    row[20].strip() if row[20] else '', # abstract
                    row[21].strip() if row[21] else '', # claims_content
                    row[22].strip() if row[22] else '', # current_owner
                    row[23].strip() if row[23] else '', # current_owner_address
                    row[24].strip() if row[24] else '', # owner_type
                    row[25].strip() if row[25] else '', # unified_social_credit_code
                    parse_int(row[26]),               # citation_count
                    parse_int(row[27]),               # cited_count
                    parse_int(row[28]),               # self_citation_count
                    parse_int(row[29]),               # other_citation_count
                    parse_int(row[30]),               # cited_by_self_count
                    parse_int(row[31]),               # cited_by_others_count
                    parse_int(row[32]),               # family_citation_count
                    parse_int(row[33]),               # family_cited_count
                    2021,                            # source_year
                ]

                batch_values.append(patent_data)

                # 批量插入
                if len(batch_values) >= 1000:
                    cursor.executemany(insert_sql, batch_values)
                    conn.commit()
                    processed_count += len(batch_values)
                    batch_values = []

            except Exception as e:
                logger.error(f"批次{batch_id} 行{row_num}处理失败: {e}")
                error_count += 1
                continue

        # 插入剩余数据
        if batch_values:
            cursor.executemany(insert_sql, batch_values)
            conn.commit()
            processed_count += len(batch_values)

        cursor.close()
        conn.close()

        return processed_count, error_count

    except Exception as e:
        logger.error(f"批次{batch_id}处理失败: {e}")
        if conn:
            try:
                conn.rollback()
                conn.close()
            except:
                pass
        return 0, len(chunk_data)

def import_2021_patents():
    """主导入函数"""
    logger.info('🚀 开始导入2021年专利数据')
    logger.info(f"📅 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 文件路径
    csv_file = '/Volumes/xujian/patent_data/china_patents/中国专利数据库2021年.csv'

    if not os.path.exists(csv_file):
        logger.error(f"❌ 文件不存在: {csv_file}")
        return False

    # 检查文件大小
    file_size = os.path.getsize(csv_file) / 1024 / 1024 / 1024  # GB
    logger.info(f"📊 文件大小: {file_size:.2f} GB")

    # 检查总行数
    total_lines = sum(1 for _ in open(csv_file, 'r', encoding='utf-8', errors='ignore'))
    data_lines = total_lines - 1  # 减去表头
    logger.info(f"📊 总记录数: {data_lines:,}")

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

        # 创建批量导入表
        create_batch_table(cursor)
        conn.commit()
        cursor.close()

        # 分块读取和处理
        chunk_size = 20000  # 每个批次处理2万条
        chunks = []

        logger.info(f"📖 开始读取CSV文件...")

        with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            header = next(reader)  # 跳过表头

            chunk = []
            chunk_id = 0

            for row_num, row in enumerate(reader, 1):
                chunk.append((row_num, row))

                if len(chunk) >= chunk_size:
                    chunks.append((csv_file, chunk, chunk_id))
                    chunk = []
                    chunk_id += 1

                    if len(chunks) >= 10:  # 限制内存中的块数
                        break

            # 处理最后一个块
            if chunk:
                chunks.append((csv_file, chunk, chunk_id))

        logger.info(f"📦 总共生成 {len(chunks)} 个批次")

        # 并行处理
        start_time = time.time()
        global total_processed, total_errors
        total_processed = 0
        total_errors = 0

        # 使用线程池处理
        max_workers = min(4, len(chunks))  # 限制并发数
        logger.info(f"🔧 使用 {max_workers} 个并发线程处理")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_chunk = {executor.submit(process_chunk, chunk): chunk for chunk in chunks}

            # 处理完成的任务
            completed = 0
            for future in as_completed(future_to_chunk):
                chunk_info = future_to_chunk[future]
                try:
                    processed, errors = future.result()

                    with stats_lock:
                        total_processed += processed
                        total_errors += errors
                        completed += 1

                        # 显示进度
                        progress = (completed / len(chunks)) * 100
                        elapsed = time.time() - start_time
                        if elapsed > 0:
                            rate = total_processed / elapsed
                            eta = (len(chunks) - completed) * (elapsed / completed) / 60

                            logger.info(
                                f"✅ 批次完成 {completed}/{len(chunks)} ({progress:.1f}%) "
                                f"处理: {total_processed:,} 条 "
                                f"错误: {total_errors:,} 条 "
                                f"速度: {rate:.1f} 条/秒 "
                                f"预计剩余: {eta:.1f} 分钟"
                            )

                except Exception as e:
                    logger.error(f"批次处理异常: {e}")
                    with stats_lock:
                        total_errors += chunk_size
                        completed += 1

        # 最终统计
        total_time = time.time() - start_time

        logger.info("\n" + '='*60)
        logger.info('🎉 2021年专利数据导入完成!')
        logger.info(f"📊 总处理: {total_processed:,} 条")
        logger.info(f"❌ 总错误: {total_errors:,} 条")
        logger.info(f"⏱️ 总耗时: {total_time:.1f} 秒 ({total_time/60:.1f} 分钟)")
        logger.info(f"🚀 平均速度: {total_processed/total_time:.1f} 条/秒")
        logger.info(f"📅 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 更新数据库统计
        cursor = conn.cursor()
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