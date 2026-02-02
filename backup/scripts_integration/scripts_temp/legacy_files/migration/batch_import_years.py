#!/usr/bin/env python3
"""
批量导入多年份专利数据
自动处理不同年份的格式差异
"""

import argparse
import csv
import logging
import signal
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

# 全局停止标志
stop_flag = False

def signal_handler(signum, frame):
    """处理中断信号"""
    global stop_flag
    logger.info("\n接收到中断信号，正在优雅停止...")
    stop_flag = True

# 注册信号处理器
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def analyze_csv_file(csv_file):
    """分析CSV文件结构"""
    logger.info(f"分析文件: {csv_file}")

    col_counts = {}
    sample_rows = []
    total_lines = 0

    try:
        with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            header = next(reader)

            # 分析前1000行
            for i, row in enumerate(reader):
                if i >= 1000:
                    break
                total_lines += 1
                col_count = len(row)
                col_counts[col_count] = col_counts.get(col_count, 0) + 1

                # 保存样本
                if len(sample_rows) < 5 and col_count >= 20:
                    sample_rows.append((i+2, col_count, row))

        # 找出最常见的列数
        if col_counts:
            most_common = max(col_counts.items(), key=lambda x: x[1])
            logger.info(f"  最常见的列数: {most_common[0]} (出现 {most_common[1]} 次)")
            return header, most_common[0], sample_rows
        else:
            logger.warning(f"  文件为空或格式异常")
            return header, 0, []

    except Exception as e:
        logger.error(f"  分析失败: {str(e)}")
        return None, 0, []

def safe_get(row, index, default=None):
    """安全获取字段值"""
    if index < len(row) and row[index]:
        val = row[index].strip()
        return val if val else default
    return default

def parse_date(date_str):
    """解析日期字符串"""
    if not date_str or len(date_str) < 8:
        return None
    try:
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
    """导入指定年份数据"""
    csv_file = f"/Volumes/xujian/patent_data/china_patents/中国专利数据库{year}年.csv"

    if not Path(csv_file).exists():
        logger.warning(f"⚠️  {year}年文件不存在")
        return False, 0

    # 分析文件结构
    header, expected_cols, sample_rows = analyze_csv_file(csv_file)
    if not header or expected_cols < 20:
        logger.error(f"❌ {year}年文件格式无效")
        return False, 0

    # 连接数据库
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='patent_db',
            user='postgres',
            password='postgres'
        )
        cursor = conn.cursor()
    except Exception as e:
        logger.error(f"❌ 数据库连接失败: {str(e)}")
        return False, 0

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

    # 导入数据
    start_time = time.time()
    total_records = 0
    success_count = 0
    skip_count = 0
    batch_size = 1000

    logger.info(f"\n开始导入 {year} 年数据")

    try:
        with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            next(reader)  # 跳过标题

            batch = []
            for row_num, row in enumerate(reader, start=2):
                # 检查停止标志
                if stop_flag:
                    logger.info('导入已中断')
                    break

                try:
                    # 确保行有足够的列
                    if len(row) < 20:
                        skip_count += 1
                        continue

                    # 补齐列到预期长度
                    while len(row) < expected_cols:
                        row.append('')

                    # 获取申请号（通常在第9列）
                    application_number = safe_get(row, 8)
                    if not application_number or len(application_number) < 5:
                        skip_count += 1
                        continue

                    # 根据数据动态调整字段映射
                    # 基本字段（各年份通用）
                    values = [
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
                    ]

                    # 动态处理字段
                    # 2013年及以后的字段映射
                    if len(row) > 22:
                        values.extend([
                            safe_get(row, 22),  # current_assignee
                            safe_get(row, 23),  # current_assignee_address
                            safe_get(row, 24),  # assignee_type
                            safe_get(row, 25),  # credit_code
                        ])
                    else:
                        values.extend([None, None, None, None])

                    # 发明人和IPC
                    if len(row) > 19:
                        values.append(safe_get(row, 19))  # inventor
                    else:
                        values.append(None)

                    if len(row) > 17:
                        ipc_code = safe_get(row, 17)
                        values.append(ipc_code)  # ipc_code
                        values.append(ipc_code[:4] if ipc_code and len(ipc_code) >= 4 else None)  # ipc_main_class
                        values.append(ipc_code)  # ipc_classification
                    else:
                        values.extend([None, None, None])

                    # 摘要和权利要求
                    if len(row) > 20:
                        values.append(safe_get(row, 20))  # abstract
                    else:
                        values.append(None)

                    if len(row) > 21:
                        claims = safe_get(row, 21)
                        values.extend([claims, claims])  # claims_content, claims
                    else:
                        values.extend([None, None])

                    # 引用计数（如果没有则为0）
                    for i in range(26, 34):
                        if i < len(row):
                            values.append(safe_int(safe_get(row, i)))
                        else:
                            values.append(0)

                    # 源信息
                    values.extend([
                        year,  # source_year
                        f'中国专利数据库{year}年.csv',  # source_file
                        None   # file_hash
                    ])

                    # 确保有36个值
                    while len(values) < 36:
                        values.append(None)

                    batch.append(tuple(values))
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
            if batch and not stop_flag:
                cursor.executemany(insert_sql, batch)
                conn.commit()
                success_count += len(batch)

    except Exception as e:
        logger.error(f"❌ 导入失败: {str(e)}")
        conn.rollback()
        return False, 0

    finally:
        cursor.close()
        conn.close()

    # 统计结果
    elapsed = time.time() - start_time
    speed = total_records / elapsed if elapsed > 0 else 0

    logger.info(f"\n{'='*60}")
    if stop_flag:
        logger.info(f"导入中断!")
    else:
        logger.info(f"✅ {year}年导入完成!")
    logger.info(f"  处理记录: {total_records:,}")
    logger.info(f"  成功导入: {success_count:,}")
    logger.info(f"  跳过记录: {skip_count:,}")
    logger.info(f"  耗时: {elapsed:.1f}秒")
    logger.info(f"  平均速度: {speed:.1f} 记录/秒")
    logger.info(f"{'='*60}")

    return not stop_flag, success_count

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='批量导入多年份专利数据')
    parser.add_argument('--start-year', type=int, default=2013, help='起始年份 (默认: 2013)')
    parser.add_argument('--end-year', type=int, default=2025, help='结束年份 (默认: 2025)')
    parser.add_argument('--year', type=int, help='导入指定年份数据')

    args = parser.parse_args()

    if args.year:
        # 导入单年
        success, count = import_year(args.year)
        if success:
            logger.info(f"\n总导入量: {count:,} 条记录")
        else:
            logger.error(f"\n导入失败")
    else:
        # 导入多年份
        years = list(range(args.start_year, args.end_year + 1))
        total_success = 0
        total_count = 0

        logger.info(f"准备导入 {len(years)} 年的数据: {years}")

        for year in years:
            if stop_flag:
                logger.info("\n批量导入已停止")
                break

            success, count = import_year(year)
            if success:
                total_success += 1
                total_count += count

        logger.info(f"\n批量导入完成!")
        logger.info(f"  成功年份: {total_success}/{len(years)}")
        logger.info(f"  总导入量: {total_count:,} 条记录")

if __name__ == '__main__':
    main()