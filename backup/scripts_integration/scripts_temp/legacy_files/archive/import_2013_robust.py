#!/usr/bin/env python3
"""
更健壮的2013年专利数据导入脚本
动态处理不同的列数
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

def analyze_csv_structure(csv_file):
    """分析CSV文件的结构"""
    logger.info(f"分析文件结构: {csv_file}")

    # 统计列数分布
    col_counts = {}
    total_rows = 0
    sample_rows = []

    with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f)
        header = next(reader)

        for i, row in enumerate(reader):
            total_rows += 1
            col_count = len(row)
            col_counts[col_count] = col_counts.get(col_count, 0) + 1

            # 保存前5行样本
            if len(sample_rows) < 5:
                sample_rows.append((i+2, col_count, row))

            if total_rows >= 10000:  # 只分析前10000行
                break

    logger.info(f"文件结构分析结果:")
    logger.info(f"  标题列数: {len(header)}")
    logger.info(f"  数据行数统计(前10000行): {total_rows}")
    logger.info('  列数分布:')
    for count, freq in sorted(col_counts.items()):
        logger.info(f"    {count} 列: {freq} 行 ({freq/total_rows*100:.1f}%)")

    return header, col_counts, sample_rows

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

def safe_int(value, default=0):
    """安全转换为整数"""
    try:
        if not value or value.strip() == '':
            return default
        return int(float(value))
    except:
        return default

def import_year(year):
    """导入单年数据"""
    csv_file = f"/Volumes/xujian/patent_data/china_patents/中国专利数据库{year}年.csv"

    if not Path(csv_file).exists():
        logger.error(f"文件不存在: {csv_file}")
        return False

    # 分析文件结构
    header, col_counts, sample_rows = analyze_csv_structure(csv_file)

    # 确定最常见的列数
    most_common_cols = max(col_counts.items(), key=lambda x: x[1])[0]
    logger.info(f"使用最常见的列数: {most_common_cols}")

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
    skip_count = 0
    batch_size = 1000

    logger.info(f"开始导入 {year} 年数据")

    try:
        with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            next(reader)  # 跳过标题行

            batch = []
            for row_num, row in enumerate(reader, start=2):
                try:
                    # 检查列数是否合理
                    if len(row) < 20:  # 如果列数太少，跳过
                        skip_count += 1
                        continue

                    # 补齐行到预期的列数
                    while len(row) < most_common_cols:
                        row.append('')

                    # 获取申请号
                    application_number = safe_get(row, 8)  # 申请号通常在第9列

                    # 跳过无效记录
                    if not application_number or len(application_number) < 5:
                        skip_count += 1
                        continue

                    # 构建值元组，动态适应不同的列数
                    values = (
                        safe_get(row, 0),  # patent_name
                        normalize_patent_type(safe_get(row, 1)),  # patent_type
                        application_number,  # application_number
                        parse_date(safe_get(row, 9)),  # application_date
                        safe_get(row, 11),  # publication_number
                        parse_date(safe_get(row, 12)),  # publication_date
                        safe_get(row, 15),  # authorization_number
                        parse_date(safe_get(row, 16)),  # authorization_date
                        safe_get(row, 2) or '未知申请人',  # applicant
                        safe_get(row, 3),  # applicant_type
                        safe_get(row, 4),  # applicant_address
                        safe_get(row, 5),  # applicant_region
                        safe_get(row, 6),  # applicant_city
                        safe_get(row, 7),  # applicant_district
                        safe_get(row, 22),  # current_assignee
                        safe_get(row, 23),  # current_assignee_address
                        safe_get(row, 24),  # assignee_type
                        safe_get(row, 25),  # credit_code
                        safe_get(row, 19),  # inventor
                        safe_get(row, 17),  # ipc_code
                        safe_get(row, 18),  # ipc_main_class
                        safe_get(row, 17),  # ipc_classification
                        safe_get(row, 20),  # abstract
                        safe_get(row, 21),  # claims_content
                        safe_get(row, 21),  # claims
                        safe_int(safe_get(row, 26)),  # citation_count
                        safe_int(safe_get(row, 27)),  # cited_count
                        safe_int(safe_get(row, 28)),  # self_citation_count
                        safe_int(safe_get(row, 29)),  # other_citation_count
                        safe_int(safe_get(row, 30)),  # cited_by_self_count
                        safe_int(safe_get(row, 31)),  # cited_by_others_count
                        safe_int(safe_get(row, 32)),  # family_citation_count
                        safe_int(safe_get(row, 33)),  # family_cited_count
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
                            logger.info(f"  进度: {total_records:,} 条记录 (成功: {success_count:,}, 跳过: {skip_count:,}, 速度: {speed:.1f} 记录/秒)")

                except Exception as e:
                    logger.warning(f"  第{row_num}行解析失败: {str(e)[:100]}")
                    skip_count += 1
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
        logger.info(f"  跳过记录: {skip_count:,}")
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
        logger.info('用法: python3 import_2013_robust.py <年份>')
        sys.exit(1)

    year = int(sys.argv[1])
    import_year(year)