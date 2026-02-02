#!/usr/bin/env python3
"""
2018-2020年专利数据导入脚本 - 修复版本
基于2016-2017成功的脚本，修复tuple index错误
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
        logging.FileHandler('import_2018_2020_fixed.log'),
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

def import_year_data(year, batch_size=1000, max_records=10000):
    """导入一年的专利数据"""
    file_path = f"/Volumes/xujian/patent_data/china_patents/中国专利数据库{year}年.csv"

    logger.info(f"开始处理{year}年数据: {file_path}")
    if max_records:
        logger.info(f"限制导入最多 {max_records:,} 条记录")

    # 检查文件是否存在
    if not os.path.exists(file_path):
        logger.error(f"文件不存在: {file_path}")
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
                    # 提取34个字段的数据
                    patent_name = row.get('专利名称', '').strip()[:1000] if row.get('专利名称') else None
                    patent_type_raw = row.get('专利类型', '').strip()
                    patent_type = map_patent_type(patent_type_raw)
                    applicant = row.get('申请人', '').strip()[:500] if row.get('申请人') else None
                    applicant_type = row.get('申请人类型', '').strip()[:50] if row.get('申请人类型') else None
                    applicant_address = row.get('申请人地址', '').strip()[:500] if row.get('申请人地址') else None
                    applicant_region = row.get('申请人地区', '').strip()[:100] if row.get('申请人地区') else None
                    applicant_city = row.get('申请人城市', '').strip()[:100] if row.get('申请人城市') else None
                    applicant_district = row.get('申请人区县', '').strip()[:100] if row.get('申请人区县') else None
                    application_number = row.get('申请号', '').strip()[:100] if row.get('申请号') else None
                    application_date = row.get('申请日', '').strip()[:20] if row.get('申请日') else None
                    publication_number = row.get('公开公告号', '').strip()[:50] if row.get('公开公告号') else None
                    publication_date = row.get('公开公告日', '').strip()[:20] if row.get('公开公告日') else None
                    authorization_number = row.get('授权公告号', '').strip()[:50] if row.get('授权公告号') else None
                    authorization_date = row.get('授权公告日', '').strip()[:20] if row.get('授权公告日') else None
                    ipc_code = row.get('IPC分类号', '').strip()[:100] if row.get('IPC分类号') else None
                    ipc_main_class = row.get('IPC主分类号', '').strip()[:20] if row.get('IPC主分类号') else None
                    inventor = row.get('发明人', '').strip()[:1000] if row.get('发明人') else None
                    abstract = row.get('摘要文本', '').strip()[:5000] if row.get('摘要文本') else None
                    claims_content = row.get('主权项内容', '').strip()[:10000] if row.get('主权项内容') else None
                    current_assignee = row.get('当前权利人', '').strip()[:500] if row.get('当前权利人') else None
                    current_assignee_address = row.get('当前专利权人地址', '').strip()[:500] if row.get('当前专利权人地址') else None
                    assignee_type = row.get('专利权人类型', '').strip()[:50] if row.get('专利权人类型') else None
                    credit_code = row.get('统一社会信用代码', '').strip()[:50] if row.get('统一社会信用代码') else None

                    # 引证次数相关字段
                    citation_count = int(float(row.get('引证次数', 0) or 0))
                    cited_count = int(float(row.get('被引证次数', 0) or 0))
                    self_citation_count = int(float(row.get('自引次数', 0) or 0))
                    other_citation_count = int(float(row.get('他引次数', 0) or 0))
                    cited_by_self_count = int(float(row.get('被自引次数', 0) or 0))
                    cited_by_others_count = int(float(row.get('被他引次数', 0) or 0))
                    family_citation_count = int(float(row.get('家族引证次数', 0) or 0))
                    family_cited_count = int(float(row.get('家族被引证次数', 0) or 0))

                    # 如果没有申请号，跳过
                    if not application_number:
                        skipped += 1
                        continue

                    # 如果专利类型无效，跳过
                    if patent_type not in ['发明', '实用新型', '外观设计']:
                        logger.warning(f"跳过无效专利类型: {patent_type_raw} (第{row_num}行)")
                        skipped += 1
                        continue

                    # 构建完整的数据元组 - 36个字段
                    record_data = (
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
                    )

                    # 确保记录有36个字段
                    if len(record_data) != 36:
                        logger.error(f"记录字段数不正确: {len(record_data)} (第{row_num}行)")
                        # 输出详细调试信息
                        logger.error(f"预期字段数: 36, 实际字段数: {len(record_data)}")
                        for i, field in enumerate(record_data):
                            logger.error(f"  字段 {i+1}: {field}")
                        skipped += 1
                        continue

                    # 验证每个字段都不是tuple类型（防止index错误）
                    for i, field in enumerate(record_data):
                        if isinstance(field, tuple):
                            logger.error(f"字段 {i+1} 是tuple类型，应该为单个值: {field}")
                            # 如果是tuple，取第一个元素
                            record_data = list(record_data)
                            record_data[i] = field[0] if len(field) > 0 else None
                            record_data = tuple(record_data)

                    # 再次检查字段数量
                    if len(record_data) != 36:
                        logger.error(f"修正后记录字段数仍不正确: {len(record_data)} (第{row_num}行)")
                        skipped += 1
                        continue

                    # 添加到记录列表
                    records.append(record_data)

                    # 当达到批次大小时，执行插入
                    if len(records) >= batch_size:
                        batch_start = time.time()

                        # 批量插入 - 36个字段
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
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT (application_number) DO NOTHING
                            """, records)
                            conn.commit()
                            processed += len(records)

                            # 显示进度
                            batch_time = time.time() - batch_start
                            speed = len(records) / batch_time if batch_time > 0 else 0
                            total_time = time.time() - start_time
                            avg_speed = processed / total_time if total_time > 0 else 0

                            progress = (row_num / max_records) * 100 if max_records else (row_num / 100000) * 100
                            logger.info(f"{year}年: 处理 {len(records):,} 条, "
                                       f"累计 {processed:,} 条 ({progress:.1f}%), "
                                       f"批次速度 {speed:.0f} 条/秒, 平均速度 {avg_speed:.0f} 条/秒")

                            # 清空记录列表，准备下一批
                            records = []

                            # 短暂休息，避免数据库压力过大
                            time.sleep(0.1)

                        except Exception as e:
                            logger.error(f"插入数据失败: {e}")
                            import traceback
                            traceback.print_exc()
                            records = []
                            continue

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
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
    logger.info('开始导入2018-2020年专利数据（修复版本）')
    logger.info('=' * 80)

    years = [2018, 2019, 2020]

    for year in years:
        logger.info(f"\n开始处理 {year} 年数据...")
        # 测试导入10000条
        success = import_year_data(year, batch_size=1000, max_records=10000)

        if not success:
            logger.error(f"❌ {year}年数据导入失败")
            return False

        logger.info(f"{year}年测试导入成功！")
        logger.info('如果需要导入完整数据，请修改 max_records 参数')

        # 年份之间休息一下
        logger.info(f"{year}年数据处理完成，休息10秒...")
        time.sleep(10)

    logger.info('✅ 所有年份数据导入测试成功！')
    logger.info("\n要导入完整数据，请修改脚本中的 max_records 参数")
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)