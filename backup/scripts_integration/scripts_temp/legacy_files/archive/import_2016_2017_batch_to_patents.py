#!/usr/bin/env python3
"""
将2016年和2017年大数据量专利文件分批导入到patents主表
专门处理35列的CSV文件格式
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
        logging.FileHandler('import_2016_2017_batch.log'),
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

def get_csv_header(file_path):
    """获取CSV文件的表头"""
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        return header

def create_field_mapping(header):
    """根据实际的CSV表头创建字段映射"""
    # 基础字段映射
    base_mapping = {
        '专利名称': 'patent_name',
        '专利类型': 'patent_type',
        '申请号': 'application_number',
        '申请日': 'application_date',
        '申请人': 'applicant',
        '发明人': 'inventor',
        'IPC分类号': 'ipc_code',
        '摘要': 'abstract'
    }

    # 扩展字段映射（2016-2017年特有）
    extended_mapping = {
        '申请人类型': 'applicant_type',
        '申请人地址': 'applicant_address',
        '申请人所在地区': 'applicant_region',
        '申请人所在市': 'applicant_city',
        '申请人所在区县': 'applicant_district',
        '当前专利权人': 'current_assignee',
        '当前专利权人地址': 'current_assignee_address',
        '专利权人类型': 'assignee_type',
        '统一社会信用代码': 'credit_code',
        '公开号': 'publication_number',
        '公开日': 'publication_date',
        '授权号': 'authorization_number',
        '授权公告日': 'authorization_date',
        '主权项': 'claims',
        '说明书': 'description',
        '代理机构': 'agent',
        '代理人': 'agent_person',
        '优先权': 'priority',
        'PCT进入国家阶段日期': 'pct_entry_date',
        '分案原申请号': 'division_original_app',
        '相关申请': 'related_app',
        '专利引用': 'patent_citations',
        '非专利引用': 'non_patent_citations',
        '同族专利数量': 'family_count',
        '引证次数': 'citation_count',
        '被引证次数': 'cited_count',
        '法律状态': 'legal_status',
        '法律状态公告日': 'legal_status_date',
        '诉讼状态': 'litigation_status',
        '许可备案': 'license_record',
        '质押备案': 'pledge_record',
        '实施许可': 'implementation_license',
        '转让': 'assignment',
        '无效宣告': 'invalidation',
        '中止': 'suspension',
        '恢复': 'restoration',
        '期限届满': 'expiry'
    }

    # 合并映射
    full_mapping = {**base_mapping, **extended_mapping}

    # 创建实际映射字典
    field_mapping = {}
    for csv_field in header:
        csv_field = csv_field.strip()
        if csv_field in full_mapping:
            field_mapping[csv_field] = full_mapping[csv_field]
        else:
            # 处理可能的字段名变体
            for key, value in full_mapping.items():
                if key in csv_field or csv_field in key:
                    field_mapping[csv_field] = value
                    break

    logger.info(f"字段映射结果: {len(field_mapping)} 个字段")
    return field_mapping

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

    # 获取CSV表头
    header = get_csv_header(file_path)
    logger.info(f"CSV文件有 {len(header)} 列")

    # 创建字段映射
    field_mapping = create_field_mapping(header)

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

        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            records = []
            for row_num, row in enumerate(reader, 1):
                # 处理每行数据
                patent_data = {}
                for csv_field, db_field in field_mapping.items():
                    value = row.get(csv_field, '').strip()
                    patent_data[db_field] = value if value else None

                # 确保所有patents表字段都有值
                records.append((
                    patent_data.get('patent_name'),  # patent_name
                    patent_data.get('patent_type'),  # patent_type
                    patent_data.get('application_number'),  # application_number
                    patent_data.get('application_date'),  # application_date
                    patent_data.get('publication_number'),  # publication_number
                    patent_data.get('publication_date'),  # publication_date
                    patent_data.get('authorization_number'),  # authorization_number
                    patent_data.get('authorization_date'),  # authorization_date
                    patent_data.get('applicant'),  # applicant
                    patent_data.get('applicant_type'),  # applicant_type
                    patent_data.get('applicant_address'),  # applicant_address
                    patent_data.get('applicant_region'),  # applicant_region
                    patent_data.get('applicant_city'),  # applicant_city
                    patent_data.get('applicant_district'),  # applicant_district
                    patent_data.get('current_assignee'),  # current_assignee
                    patent_data.get('current_assignee_address'),  # current_assignee_address
                    patent_data.get('assignee_type'),  # assignee_type
                    patent_data.get('credit_code'),  # credit_code
                    patent_data.get('inventor'),  # inventor
                    patent_data.get('ipc_code'),  # ipc_code
                    patent_data.get('ipc_code')[:4] if patent_data.get('ipc_code') else None,  # ipc_main_class
                    patent_data.get('ipc_code'),  # ipc_classification
                    patent_data.get('abstract'),  # abstract
                    patent_data.get('description'),  # claims_content
                    patent_data.get('claims'),  # claims
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

                    # 根据速度调整批次大小
                    if batch_time < 10:
                        batch_size = min(batch_size * 2, 5000)
                    elif batch_time > 60:
                        batch_size = max(batch_size // 2, 500)

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
    logger.info('开始分批导入2016-2017年专利数据到patents主表')
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