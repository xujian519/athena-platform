#!/usr/bin/env python3
"""
2019-2020年专利数据导入脚本
基于成功的2018年脚本，专门处理2019-2020年数据
"""

import csv
import logging
import os
import sys
import time
from decimal import Decimal

import psycopg2

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('import_2019_2020.log'),
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

def map_patent_type(raw_type):
    """映射专利类型到标准格式"""
    if not raw_type:
        return None

    # 发明专利类型映射
    if raw_type in ['发明授权', '发明专利授权', '发明']:
        return '发明'
    elif raw_type in ['发明申请', '发明专利申请']:
        return '发明'
    elif raw_type.startswith('发明'):
        return '发明'

    # 实用新型专利类型映射
    elif raw_type in ['实用新型授权', '实用新型专利授权', '实用新型']:
        return '实用新型'
    elif raw_type in ['实用新型申请', '实用新型专利申请']:
        return '实用新型'
    elif raw_type.startswith('实用新型'):
        return '实用新型'

    # 外观设计专利类型映射
    elif raw_type in ['外观设计授权', '外观设计专利授权', '外观设计']:
        return '外观设计'
    elif raw_type in ['外观设计申请', '外观设计专利申请']:
        return '外观设计'
    elif raw_type.startswith('外观设计'):
        return '外观设计'

    # 如果无法识别，返回None以避免约束错误
    return None

def safe_int(value):
    """安全转换为整数"""
    try:
        if value is None or value == '':
            return 0
        # 处理Decimal类型
        if isinstance(value, Decimal):
            return int(value)
        return int(float(value))
    except:
        return 0

def import_year_data(year, batch_size=2000, start_from=0):
    """导入一年的专利数据"""
    file_path = f"/Volumes/xujian/patent_data/china_patents/中国专利数据库{year}年.csv"

    logger.info(f"开始处理{year}年数据: {file_path}")
    logger.info(f"批量大小: {batch_size}")
    logger.info(f"从第 {start_from:,} 条记录开始")

    # 检查文件是否存在
    if not os.path.exists(file_path):
        logger.error(f"文件不存在: {file_path}")
        return False

    # 分批读取并导入
    processed = 0
    skipped = 0
    start_time = time.time()
    last_report_time = start_time

    try:
        conn = get_connection()
        if not conn:
            return False

        cursor = conn.cursor()

        # 构建SQL语句 - 36个字段
        sql = """
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
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (application_number) DO NOTHING
        """

        with open(file_path, 'r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)

            records = []
            # 跳过前面的记录
            for row_num, row in enumerate(reader, 1):
                if row_num <= start_from:
                    continue

                try:
                    # 提取并清理数据
                    patent_name = row.get('专利名称', '').strip()[:1000] if row.get('专利名称') else None
                    patent_type_raw = row.get('专利类型', '').strip()
                    patent_type = map_patent_type(patent_type_raw)
                    applicant = row.get('申请人', '').strip()[:500] if row.get('申请人') else None
                    application_number = row.get('申请号', '').strip()[:100] if row.get('申请号') else None

                    # 如果没有申请号，跳过
                    if not application_number:
                        skipped += 1
                        continue

                    # 如果专利类型无效，跳过
                    if patent_type not in ['发明', '实用新型', '外观设计']:
                        if row_num % 100000 == 1:  # 每10万条记录输出一次警告
                            logger.warning(f"跳过无效专利类型: {patent_type_raw} (第{row_num}行)")
                        skipped += 1
                        continue

                    # 如果专利名称为空，跳过
                    if not patent_name:
                        skipped += 1
                        continue

                    # 构建数据列表（36个字段）
                    values = [
                        patent_name,  # patent_name
                        patent_type,  # patent_type
                        application_number,  # application_number
                        row.get('申请日', '').strip()[:20] if row.get('申请日') else None,  # application_date
                        row.get('公开公告号', '').strip()[:50] if row.get('公开公告号') else None,  # publication_number
                        row.get('公开公告日', '').strip()[:20] if row.get('公开公告日') else None,  # publication_date
                        row.get('授权公告号', '').strip()[:50] if row.get('授权公告号') else None,  # authorization_number
                        row.get('授权公告日', '').strip()[:20] if row.get('授权公告日') else None,  # authorization_date
                        applicant[:500] if applicant else None,  # applicant
                        row.get('申请人类型', '').strip()[:50] if row.get('申请人类型') else None,  # applicant_type
                        row.get('申请人地址', '').strip()[:500] if row.get('申请人地址') else None,  # applicant_address
                        row.get('申请人地区', '').strip()[:100] if row.get('申请人地区') else None,  # applicant_region
                        row.get('申请人城市', '').strip()[:100] if row.get('申请人城市') else None,  # applicant_city
                        row.get('申请人区县', '').strip()[:100] if row.get('申请人区县') else None,  # applicant_district
                        row.get('当前权利人', '').strip()[:500] if row.get('当前权利人') else None,  # current_assignee
                        row.get('当前专利权人地址', '').strip()[:500] if row.get('当前专利权人地址') else None,  # current_assignee_address
                        row.get('专利权人类型', '').strip()[:50] if row.get('专利权人类型') else None,  # assignee_type
                        row.get('统一社会信用代码', '').strip()[:50] if row.get('统一社会信用代码') else None,  # credit_code
                        row.get('发明人', '').strip()[:1000] if row.get('发明人') else None,  # inventor
                        row.get('IPC分类号', '').strip()[:100] if row.get('IPC分类号') else None,  # ipc_code
                        row.get('IPC主分类号', '').strip()[:20] if row.get('IPC主分类号') else None,  # ipc_main_class
                        row.get('IPC分类号', '').strip()[:100] if row.get('IPC分类号') else None,  # ipc_classification
                        row.get('摘要文本', '').strip()[:5000] if row.get('摘要文本') else None,  # abstract
                        row.get('主权项内容', '').strip()[:10000] if row.get('主权项内容') else None,  # claims_content
                        None,  # claims
                        safe_int(row.get('引证次数', 0)),  # citation_count
                        safe_int(row.get('被引证次数', 0)),  # cited_count
                        safe_int(row.get('自引次数', 0)),  # self_citation_count
                        safe_int(row.get('他引次数', 0)),  # other_citation_count
                        safe_int(row.get('被自引次数', 0)),  # cited_by_self_count
                        safe_int(row.get('被他引次数', 0)),  # cited_by_others_count
                        safe_int(row.get('家族引证次数', 0)),  # family_citation_count
                        safe_int(row.get('家族被引证次数', 0)),  # family_cited_count
                        year,  # source_year
                        f'中国专利数据库{year}年.csv',  # source_file
                        None  # file_hash
                    ]

                    # 转换为tuple
                    record_data = tuple(values)

                    # 添加到记录列表
                    records.append(record_data)

                    # 当达到批次大小时，执行插入
                    if len(records) >= batch_size:
                        batch_start = time.time()

                        # 批量插入
                        try:
                            cursor.executemany(sql, records)
                            conn.commit()
                            processed += len(records)

                            # 每10万条记录报告一次进度
                            current_time = time.time()
                            if current_time - last_report_time >= 30:  # 每30秒报告一次
                                batch_time = time.time() - batch_start
                                speed = len(records) / batch_time if batch_time > 0 else 0
                                total_time = current_time - start_time
                                avg_speed = processed / total_time if total_time > 0 else 0

                                logger.info(f"{year}年: 处理 {len(records):,} 条, "
                                           f"累计 {processed:,} 条, "
                                           f"批次速度 {speed:.0f} 条/秒, 平均速度 {avg_speed:.0f} 条/秒")
                                last_report_time = current_time

                            # 清空记录列表，准备下一批
                            records = []

                            # 短暂休息，避免数据库压力过大
                            time.sleep(0.05)

                        except Exception as e:
                            logger.error(f"插入数据失败: {e}")
                            conn.rollback()
                            records = []
                            continue

                except Exception as e:
                    if row_num % 100000 == 1:  # 每10万条记录输出一次错误
                        logger.error(f"处理第{row_num}行失败: {e}")
                    skipped += 1
                    continue

            # 处理最后一批记录
            if records:
                try:
                    cursor.executemany(sql, records)
                    conn.commit()
                    processed += len(records)
                    logger.info(f"{year}年: 处理最后 {len(records):,} 条")
                except Exception as e:
                    logger.error(f"插入最后一批数据失败: {e}")
                    conn.rollback()

        cursor.close()
        conn.close()

        total_time = time.time() - start_time
        logger.info(f"✅ {year}年数据导入完成")
        logger.info(f"  处理: {processed:,} 条")
        logger.info(f"  跳过: {skipped:,} 条")
        logger.info(f"  总耗时: {total_time:.1f} 秒")
        logger.info(f"  平均速度: {processed/total_time:.0f} 条/秒")
        return True

    except Exception as e:
        logger.error(f"{year}年导入失败: {e}")
        import traceback

# 导入标准化数据库工具
from shared.database.db_utils import DatabaseManager, build_safe_query
        traceback.print_exc()
        if conn:
            conn.rollback()
            conn.close()
        return False

def main():
    """主函数"""
    logger.info('=' * 80)
    logger.info('开始导入2019-2020年专利数据')
    logger.info('=' * 80)

    years = [2019, 2020]

    for year in years:
        logger.info(f"\n开始处理 {year} 年数据...")

        # 检查已导入数量
        conn = get_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM patents WHERE source_year = %s', (year,))
            existing_count = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            logger.info(f"数据库中已有 {year} 年数据: {existing_count:,} 条")

            # 如果已有数据，从头开始导入（会自动去重）
            success = import_year_data(year, batch_size=2000, start_from=0)
        else:
            success = False

        if not success:
            logger.error(f"❌ {year}年数据导入失败")
            return False

        logger.info(f"{year}年数据导入成功！")

        # 年份之间休息一下
        logger.info(f"{year}年数据处理完成，休息5秒...")
        time.sleep(5)

    logger.info('✅ 所有年份数据导入完成！')
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)