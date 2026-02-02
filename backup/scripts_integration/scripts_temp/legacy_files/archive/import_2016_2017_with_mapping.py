#!/usr/bin/env python3
"""
2016-2017年专利数据导入脚本（含专利类型映射）
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
        logging.FileHandler('import_2016_2017_with_mapping.log'),
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

    # 如果无法识别，返回原始值或None
    # 返回None会导致约束错误，返回原始值可能可以通过
    return raw_type

def count_lines(file_path):
    """快速统计CSV文件的行数"""
    count = 0
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        for line in f:
            count += 1
    return count - 1  # 减去表头

def import_year_data(year, batch_size=2000, max_records=None):
    """导入一年的专利数据"""
    file_path = f"/Volumes/xujian/patent_data/china_patents/中国专利数据库{year}年.csv"

    logger.info(f"开始处理{year}年数据: {file_path}")
    if max_records:
        logger.info(f"限制导入最多 {max_records:,} 条记录")

    # 检查文件是否存在
    if not os.path.exists(file_path):
        logger.error(f"文件不存在: {file_path}")
        return False

    try:
        total_lines = count_lines(file_path)
        if max_records:
            total_lines = min(total_lines, max_records)
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
            logger.warning(f"{year}年数据已存在 {existing:,} 条，将跳过已导入的数据")

        cursor.close()
        conn.close()
    except Exception as e:
        logger.error(f"检查现有数据失败: {e}")
        conn.close()
        return False

    # 分批读取并导入
    processed = 0
    skipped = 0
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
                if max_records and row_num > max_records:
                    break

                try:
                    # 提取数据
                    patent_name = row.get('专利名称', '').strip()
                    patent_name = patent_name[:1000] if patent_name else None  # 限制长度

                    patent_type_raw = row.get('专利类型', '').strip()
                    patent_type = map_patent_type(patent_type_raw)

                    # 如果映射后仍不合法，跳过
                    if patent_type not in ['发明', '实用新型', '外观设计', None]:
                        logger.warning(f"跳过无效专利类型: {patent_type_raw} (第{row_num}行)")
                        skipped += 1
                        continue

                    applicant = row.get('申请人', '').strip()
                    applicant = applicant[:500] if applicant else None

                    applicant_type = row.get('申请人类型', '').strip()
                    applicant_type = applicant_type[:50] if applicant_type else None

                    applicant_address = row.get('申请人地址', '').strip()
                    applicant_address = applicant_address[:500] if applicant_address else None

                    applicant_region = row.get('申请人地区', '').strip()
                    applicant_region = applicant_region[:100] if applicant_region else None

                    applicant_city = row.get('申请人城市', '').strip()
                    applicant_city = applicant_city[:100] if applicant_city else None

                    applicant_district = row.get('申请人区县', '').strip()
                    applicant_district = applicant_district[:100] if applicant_district else None

                    application_number = row.get('申请号', '').strip()
                    application_number = application_number[:100] if application_number else None

                    application_date = row.get('申请日', '').strip()
                    application_date = application_date[:20] if application_date else None

                    publication_number = row.get('公开公告号', '').strip()
                    publication_number = publication_number[:50] if publication_number else None

                    publication_date = row.get('公开公告日', '').strip()
                    publication_date = publication_date[:20] if publication_date else None

                    authorization_number = row.get('授权公告号', '').strip()
                    authorization_number = authorization_number[:50] if authorization_number else None

                    authorization_date = row.get('授权公告日', '').strip()
                    authorization_date = authorization_date[:20] if authorization_date else None

                    ipc_code = row.get('IPC分类号', '').strip()
                    ipc_code = ipc_code[:100] if ipc_code else None

                    ipc_main_class = row.get('IPC主分类号', '').strip()
                    ipc_main_class = ipc_main_class[:20] if ipc_main_class else None

                    inventor = row.get('发明人', '').strip()
                    inventor = inventor[:1000] if inventor else None

                    abstract = row.get('摘要文本', '').strip()
                    abstract = abstract[:5000] if abstract else None

                    claims_content = row.get('主权项内容', '').strip()
                    claims_content = claims_content[:10000] if claims_content else None

                    current_assignee = row.get('当前权利人', '').strip()
                    current_assignee = current_assignee[:500] if current_assignee else None

                    current_assignee_address = row.get('当前专利权人地址', '').strip()
                    current_assignee_address = current_assignee_address[:500] if current_assignee_address else None

                    assignee_type = row.get('专利权人类型', '').strip()
                    assignee_type = assignee_type[:50] if assignee_type else None

                    credit_code = row.get('统一社会信用代码', '').strip()
                    credit_code = credit_code[:50] if credit_code else None

                    # 如果没有申请号，跳过
                    if not application_number:
                        skipped += 1
                        continue

                    # 构建完整的数据元组
                    records.append((
                        patent_name,  # patent_name
                        patent_type,  # patent_type
                        application_number,  # application_number
                        application_date,  # application_date
                        publication_number,  # publication_number
                        publication_date,  # publication_date
                        authorization_number,  # authorization_number
                        authorization_date,  # authorization_date
                        applicant,  # applicant
                        applicant_type,  # applicant_type
                        applicant_address,  # applicant_address
                        applicant_region,  # applicant_region
                        applicant_city,  # applicant_city
                        applicant_district,  # applicant_district
                        current_assignee,  # current_assignee
                        current_assignee_address,  # current_assignee_address
                        assignee_type,  # assignee_type
                        credit_code,  # credit_code
                        inventor,  # inventor
                        ipc_code,  # ipc_code
                        ipc_main_class,  # ipc_main_class
                        ipc_code,  # ipc_classification (使用完整的IPC分类号)
                        abstract,  # abstract
                        claims_content,  # claims_content
                        None,  # claims
                        0, 0, 0, 0, 0, 0, 0, 0,  # 所有引证次数字段设为0
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
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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

                        # 短暂休息，避免数据库压力过大
                        time.sleep(0.1)

                except Exception as e:
                    logger.error(f"处理第{row_num}行失败: {e}")
                    skipped += 1
                    continue

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
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (application_number) DO NOTHING
                """, records)
                conn.commit()
                processed += len(records)
                logger.info(f"{year}年: 处理最后 {len(records):,} 条, 累计 {processed:,} 条")

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
        if conn:
            conn.rollback()
            conn.close()
        return False

def main():
    """主函数"""
    logger.info('=' * 80)
    logger.info('开始导入2016-2017年专利数据（含专利类型映射）')
    logger.info('=' * 80)

    years = [2016, 2017]

    for year in years:
        logger.info(f"\n开始处理 {year} 年数据...")
        # 先测试少量数据
        success = import_year_data(year, batch_size=1000, max_records=10000)

        if not success:
            logger.error(f"❌ {year}年数据导入失败")
            return False

        logger.info(f"{year}年测试导入成功！")
        logger.info('如果需要导入完整数据，请移除 max_records 参数限制')

        # 年份之间休息一下
        logger.info(f"{year}年数据处理完成，休息10秒...")
        time.sleep(10)

    logger.info('✅ 所有年份数据导入测试成功！')
    logger.info("\n要导入完整数据，请修改脚本中的 max_records 参数")
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)