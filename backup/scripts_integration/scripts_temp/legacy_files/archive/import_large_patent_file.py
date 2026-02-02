#!/usr/bin/env python3
"""
大文件专利数据导入脚本
支持分批处理大型CSV文件，提高导入准确率
"""

import argparse
import csv
import hashlib
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import psycopg2
import psycopg2.extras
from psycopg2.extras import DictCursor

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('documentation/logs/large_file_import.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 导入数据库配置
try:
    from database.db_config import DB_CONFIG
except ImportError:
    logger.error('❌ 未找到数据库配置')
    sys.exit(1)

class LargePatentFileImporter:
    """大文件专利数据导入器"""

    def __init__(self):
        self.source_dir = '/Volumes/xujian/patent_data/china_patents'
        self.batch_size = 1000  # 减小批次大小，提高准确性
        self.chunks_per_file = 10  # 每个文件分10批处理
        self.rows_per_chunk = 50000  # 每批处理5万行

        # 创建日志目录
        os.makedirs('logs', exist_ok=True)

        # 获取数据库连接
        self.get_connection()

    def get_connection(self):
        """获取数据库连接"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG, cursor_factory=DictCursor)
            logger.info('✅ 数据库连接成功')
        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {str(e)}")
            sys.exit(1)

    def parse_patent_data(self, row, file_name=None):
        """解析专利数据行"""
        def safe_get(value, default=None):
            """安全获取字段值"""
            if not value or value.strip() == '':
                return default
            return value.strip()

        def parse_date(date_str):
            """解析日期字符串"""
            if not date_str or len(date_str) < 8:
                return None
            try:
                if '.' in date_str:
                    date_str = date_str.replace('.', '')
                if len(date_str) == 8:
                    return datetime.strptime(date_str, '%Y%m%d').date()
                elif len(date_str) == 10:
                    return datetime.strptime(date_str, '%Y-%m-%d').date()
                else:
                    return None
            except:
                return None

        # 确保有足够的列
        while len(row) < 35:
            row.append('')

        patent_data = {
            'patent_name': safe_get(row[0]),
            'patent_type': self.normalize_patent_type(safe_get(row[1])),
            'application_number': safe_get(row[8]),
            'application_date': parse_date(row[9]),
            'publication_number': safe_get(row[11]),
            'publication_date': parse_date(row[12]),
            'authorization_number': safe_get(row[15]),
            'authorization_date': parse_date(row[16]),
            'applicant': safe_get(row[2]) or '未知申请人',  # 避免空值
            'applicant_type': safe_get(row[3]),
            'applicant_address': safe_get(row[4]),
            'applicant_region': safe_get(row[5]),
            'applicant_city': safe_get(row[6]),
            'applicant_district': safe_get(row[7]),
            'current_assignee': safe_get(row[22]),
            'current_assignee_address': safe_get(row[23]),
            'assignee_type': safe_get(row[24]),
            'credit_code': safe_get(row[25]),
            'inventor': safe_get(row[19]),
            'ipc_code': safe_get(row[17]),
            'ipc_main_class': safe_get(row[18]),
            'ipc_classification': safe_get(row[17]),
            'abstract': safe_get(row[20]),
            'claims_content': safe_get(row[21]),
            'claims': safe_get(row[21]),
            'citation_count': self.safe_int(safe_get(row[26])),
            'cited_count': self.safe_int(safe_get(row[27])),
            'self_citation_count': self.safe_int(safe_get(row[28])),
            'other_citation_count': self.safe_int(safe_get(row[29])),
            'cited_by_self_count': self.safe_int(safe_get(row[30])),
            'cited_by_others_count': self.safe_int(safe_get(row[31])),
            'family_citation_count': self.safe_int(safe_get(row[32])),
            'family_cited_count': self.safe_int(safe_get(row[33])),
            'source_year': int(row[10]) if row[10] and row[10].isdigit() else None,
            'source_file': file_name if file_name else ''
        }

        return patent_data

    def normalize_patent_type(self, patent_type):
        """标准化专利类型"""
        if not patent_type:
            return None

        patent_type = patent_type.strip()
        type_mapping = {
            '发明专利': '发明',
            '实用新型专利': '实用新型',
            '外观设计专利': '外观设计',
            '发明': '发明',
            '实用新型': '实用新型',
            '外观设计': '外观设计'
        }

        normalized = type_mapping.get(patent_type, patent_type)
        valid_types = ['发明', '实用新型', '外观设计']
        return normalized if normalized in valid_types else None

    def safe_int(self, value, default=0):
        """安全转换为整数"""
        try:
            if not value or value.strip() == '':
                return default
            return int(float(value))
        except:
            return default

    def import_batch(self, records):
        """批量导入专利记录"""
        if not records:
            return 0, 0

        cursor = self.conn.cursor()

        try:
            # 准备插入语句
            insert_sql = """
                INSERT INTO patents (
                    patent_name, patent_type, application_number, application_date,
                    publication_number, publication_date, authorization_number,
                    authorization_date, applicant, applicant_type, applicant_address,
                    applicant_region, applicant_city, applicant_district,
                    current_assignee, current_assignee_address, assignee_type,
                    credit_code, inventor, ipc_code, ipc_main_class,
                    ipc_classification, abstract, claims_content, claims,
                    source_year, source_file, created_at, updated_at
                ) VALUES (
                    %(patent_name)s, %(patent_type)s, %(application_number)s,
                    %(application_date)s, %(publication_number)s, %(publication_date)s,
                    %(authorization_number)s, %(authorization_date)s, %(applicant)s,
                    %(applicant_type)s, %(applicant_address)s, %(applicant_region)s,
                    %(applicant_city)s, %(applicant_district)s, %(current_assignee)s,
                    %(current_assignee_address)s, %(assignee_type)s, %(credit_code)s,
                    %(inventor)s, %(ipc_code)s, %(ipc_main_class)s,
                    %(ipc_classification)s, %(abstract)s, %(claims_content)s,
                    %(claims)s, %(source_year)s, %(source_file)s,
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
                ON CONFLICT (application_number) DO UPDATE SET
                    patent_name = EXCLUDED.patent_name,
                    patent_type = EXCLUDED.patent_type,
                    publication_number = EXCLUDED.publication_number,
                    publication_date = EXCLUDED.publication_date,
                    authorization_number = EXCLUDED.authorization_number,
                    authorization_date = EXCLUDED.authorization_date,
                    applicant = EXCLUDED.applicant,
                    applicant_address = EXCLUDED.applicant_address,
                    inventor = EXCLUDED.inventor,
                    ipc_code = EXCLUDED.ipc_code,
                    ipc_classification = EXCLUDED.ipc_classification,
                    abstract = EXCLUDED.abstract,
                    claims = EXCLUDED.claims,
                    updated_at = CURRENT_TIMESTAMP
            """

            # 批量插入
            psycopg2.extras.execute_batch(cursor, insert_sql, records)
            self.conn.commit()

            return len(records), 0

        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ 批量导入失败: {str(e)}")
            return 0, len(records)

    def import_file_in_chunks(self, file_path):
        """分块导入大文件"""
        file_name = Path(file_path).name
        source_year = self.extract_year_from_filename(file_name)

        if not source_year:
            logger.error(f"❌ 无法从文件名提取年份: {file_name}")
            return False, 0

        # 获取文件总行数
        total_lines = self.count_lines(file_path)
        logger.info(f"文件总行数: {total_lines:,}")

        # 计算每个块的行数
        lines_per_chunk = max(self.rows_per_chunk, total_lines // self.chunks_per_file)

        total_records = 0
        success_records = 0
        failed_records = 0

        logger.info(f"\n{'='*60}")
        logger.info(f"开始分块导入: {file_name}")
        logger.info(f"年份: {source_year}")
        logger.info(f"文件大小: {Path(file_path).stat().st_size / (1024*1024):.1f} MB")
        logger.info(f"分块数: {self.chunks_per_file}, 每块约 {lines_per_chunk:,} 行")
        logger.info(f"{'='*60}\n")

        # 逐块处理
        for chunk_idx in range(self.chunks_per_file):
            start_line = 1 + chunk_idx * lines_per_chunk
            end_line = min(start_line + lines_per_chunk - 1, total_lines)

            logger.info(f"\n处理第 {chunk_idx + 1}/{self.chunks_per_file} 块 (行 {start_line:,}-{end_line:,})")

            chunk_success, chunk_failed = self.import_file_chunk(
                file_path, start_line, end_line, chunk_idx + 1
            )

            success_records += chunk_success
            failed_records += chunk_failed
            total_records += chunk_success + chunk_failed

            # 显示进度
            progress = (chunk_idx + 1) / self.chunks_per_file * 100
            logger.info(f"  进度: {progress:.1f}% - 成功: {chunk_success:,}, 失败: {chunk_failed:,}")

        # 最终统计
        logger.info(f"\n✅ 文件导入完成!")
        logger.info(f"  总记录数: {total_records:,}")
        logger.info(f"  成功: {success_records:,}")
        logger.info(f"  失败: {failed_records:,}")
        logger.info(f"  成功率: {success_records/total_records*100:.1f}%")

        return True, success_records

    def import_file_chunk(self, file_path, start_line, end_line, chunk_num):
        """导入文件的指定块"""
        file_name = Path(file_path).name
        source_year = self.extract_year_from_filename(file_name)

        success_count = 0
        failed_count = 0
        batch = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.reader(f)

                # 跳过到起始行
                for _ in range(start_line - 1):
                    try:
                        next(reader)
                    except StopIteration:
                        break

                # 处理指定范围的行
                current_line = start_line
                for row in reader:
                    if current_line > end_line:
                        break

                    try:
                        # 解析数据
                        patent_data = self.parse_patent_data(row, file_name)
                        patent_data['source_year'] = source_year

                        batch.append(patent_data)

                        # 批量处理
                        if len(batch) >= self.batch_size:
                            s, f = self.import_batch(batch)
                            success_count += s
                            failed_count += f
                            batch = []

                    except Exception as e:
                        logger.warning(f"  警告: 第{current_line}行解析失败: {str(e)[:100]}")
                        failed_count += 1

                    current_line += 1

                # 处理剩余记录
                if batch:
                    s, f = self.import_batch(batch)
                    success_count += s
                    failed_count += f

        except Exception as e:
            logger.error(f"❌ 处理文件块失败: {str(e)}")
            return 0, end_line - start_line + 1

        return success_count, failed_count

    def count_lines(self, file_path):
        """计算文件总行数"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return sum(1 for _ in f)

    def extract_year_from_filename(self, filename):
        """从文件名提取年份"""
        try:
            year_str = filename.split('中国专利数据库')[1].split('年')[0]
            return int(year_str)
        except:
            return None

    def import_single_year(self, year):
        """导入单年数据（使用分块处理）"""
        csv_file = Path(self.source_dir) / f"中国专利数据库{year}年.csv"

        if not csv_file.exists():
            logger.warning(f"⚠️  {year}年文件不存在")
            return False, 0

        return self.import_file_in_chunks(csv_file)

    def cleanup(self):
        """清理资源"""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
            logger.info('✅ 数据库连接已关闭')

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='大文件专利数据导入工具')
    parser.add_argument('--year', type=int, help='导入指定年份数据')
    parser.add_argument('--start-year', type=int, help='开始年份')
    parser.add_argument('--end-year', type=int, help='结束年份')
    parser.add_argument('--chunks', type=int, default=10, help='每个文件分成的块数')
    parser.add_argument('--batch-size', type=int, default=1000, help='批处理大小')

    args = parser.parse_args()

    # 创建导入器
    importer = LargePatentFileImporter()

    # 设置参数
    if args.chunks:
        importer.chunks_per_file = args.chunks
    if args.batch_size:
        importer.batch_size = args.batch_size

    try:
        # 执行导入
        start_time = time.time()

        if args.year:
            # 导入单年
            success, count = importer.import_single_year(args.year)
            if success:
                logger.info(f"\n🎉 {args.year}年数据导入成功，共 {count:,} 条记录")
            else:
                logger.error(f"\n❌ {args.year}年数据导入失败")

        elif args.start_year and args.end_year:
            # 导入多年份
            years = list(range(args.start_year, args.end_year + 1))
            total_success = 0

            for year in years:
                logger.info(f"\n{'='*60}")
                logger.info(f"开始导入 {year} 年")
                logger.info(f"{'='*60}")

                success, count = importer.import_single_year(year)
                if success:
                    total_success += count
                    logger.info(f"✅ {year}年导入成功: {count:,} 条")
                else:
                    logger.error(f"❌ {year}年导入失败")

            logger.info(f"\n{'='*60}")
            logger.info('多年份导入完成!')
            logger.info(f"总记录数: {total_success:,}")
            logger.info(f"{'='*60}")

        else:
            logger.error('❌ 请指定年份或年份范围')
            parser.print_help()

        duration = time.time() - start_time
        logger.info(f"\n总耗时: {duration:.1f}秒")

    finally:
        importer.cleanup()

if __name__ == '__main__':
    main()