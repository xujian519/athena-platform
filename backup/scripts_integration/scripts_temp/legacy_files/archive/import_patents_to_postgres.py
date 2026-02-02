#!/usr/bin/env python3
"""
PostgreSQL专利数据导入脚本
高效批量导入CSV数据到PostgreSQL，支持并行处理和事务管理
"""

import argparse
import csv
import hashlib
import logging
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import psycopg2
import psycopg2.extras

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('documentation/logs/postgresql_import.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 导入数据库配置
try:
    from database.db_config import DB_CONFIG
except ImportError:
    logger.error('❌ 未找到数据库配置，请先运行 setup_postgresql_patent_db.py')
    sys.exit(1)

class PostgreSQLPatentImporter:
    """PostgreSQL专利数据导入器"""

    def __init__(self):
        self.source_dir = '/Volumes/xujian/patent_data/china_patents'
        self.batch_size = 2000
        self.max_workers = 4
        self.lock = threading.Lock()

        # 创建日志目录
        os.makedirs('logs', exist_ok=True)

        # 获取数据库连接池
        try:
            from psycopg2 import pool
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                minconn=2,
                maxconn=20,
                **DB_CONFIG
            )
            logger.info('✅ 数据库连接池创建成功')
        except Exception as e:
            logger.error(f"❌ 创建连接池失败: {str(e)}")
            sys.exit(1)

    def get_connection(self):
        """从连接池获取连接"""
        return self.connection_pool.getconn()

    def release_connection(self, conn):
        """释放连接到连接池"""
        self.connection_pool.putconn(conn)

    def parse_patent_data(self, row, file_name=None):
        """解析专利数据行"""
        # CSV字段映射（根据实际文件调整）
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
                # 处理多种日期格式
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

        # 根据实际CSV结构映射字段
        # CSV结构: 专利名称,专利类型,申请人,申请人类型,申请人地址,申请人地区,申请人城市,申请人区县,
        #          申请号,申请日,申请年份,公开公告号,公开公告日,公开公告年份,
        #          授权公告号,授权公告日,授权公告年份,IPC分类号,IPC主分类号,
        #          发明人,摘要文本,主权项内容,当前权利人,当前专利权人地址,专利权人类型,
        #          统一社会信用代码,引证次数,被引证次数,自引次数,他引次数,
        #          被自引次数,被他引次数,家族引证次数,家族被引证次数

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
            'applicant': safe_get(row[2]),
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

        # 只返回有效的专利类型
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

    def extract_ipc_main_class(self, ipc_code):
        """提取IPC主分类号"""
        if not ipc_code:
            return None

        # IPC格式：A01B 33/00，取前4位作为主分类
        parts = ipc_code.split()
        if parts:
            main_class = parts[0]
            if len(main_class) >= 4:
                return main_class[:4]
        return None

    def import_batch(self, records, source_year, source_file):
        """批量导入专利记录"""
        if not records:
            return 0, 0

        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

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

            # 提交事务
            conn.commit()

            return len(records), 0

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ 批量导入失败: {str(e)}")
            return 0, len(records)

        finally:
            if conn:
                self.release_connection(conn)

    def import_file(self, file_path):
        """导入单个CSV文件"""
        file_name = Path(file_path).name
        source_year = self.extract_year_from_filename(file_name)

        if not source_year:
            logger.error(f"❌ 无法从文件名提取年份: {file_name}")
            return False, 0

        logger.info(f"\n{'='*60}")
        logger.info(f"开始导入: {file_name}")
        logger.info(f"年份: {source_year}")
        logger.info(f"文件大小: {Path(file_path).stat().st_size / (1024*1024):.1f} MB")
        logger.info(f"{'='*60}")

        # 记录导入开始
        start_time = time.time()
        log_id = None

        conn = None
        try:
            # 创建导入日志记录
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO data_import_log (
                    source_file, source_year, total_records,
                    success_records, failed_records, start_time
                ) VALUES (%s, %s, 0, 0, 0, to_timestamp(%s))
                RETURNING id
            """, (file_name, source_year, start_time))

            log_id = cursor.fetchone()[0]
            conn.commit()

            # 读取CSV文件
            total_records = 0
            success_records = 0
            failed_records = 0
            batch = []

            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # 跳过标题行（如果有）
                # f.readline()

                reader = csv.reader(f)
                for row_num, row in enumerate(reader, 1):
                    try:
                        # 解析数据
                        patent_data = self.parse_patent_data(row, file_name)
                        patent_data['source_year'] = source_year

                        batch.append(patent_data)
                        total_records += 1

                        # 批量处理
                        if len(batch) >= self.batch_size:
                            s, f = self.import_batch(batch, source_year, file_name)
                            success_records += s
                            failed_records += f
                            batch = []

                            # 显示进度
                            if total_records % 10000 == 0:
                                logger.info(f"  进度: {total_records:,} 条记录")

                    except Exception as e:
                        logger.warning(f"  警告: 第{row_num}行解析失败: {str(e)[:100]}")
                        failed_records += 1
                        continue

                # 处理剩余记录
                if batch:
                    s, f = self.import_batch(batch, source_year, file_name)
                    success_records += s
                    failed_records += f

            # 更新导入日志
            end_time = time.time()
            cursor.execute("""
                UPDATE data_import_log SET
                    total_records = %s,
                    success_records = %s,
                    failed_records = %s,
                    end_time = to_timestamp(%s),
                    status = 'completed'
                WHERE id = %s
            """, (total_records, success_records, failed_records, end_time, log_id))

            conn.commit()

            # 统计结果
            duration = end_time - start_time
            logger.info(f"\n✅ 导入完成!")
            logger.info(f"  总记录数: {total_records:,}")
            logger.info(f"  成功: {success_records:,}")
            logger.info(f"  失败: {failed_records:,}")
            logger.info(f"  耗时: {duration:.1f}秒")
            logger.info(f"  速度: {total_records/duration:.1f} 记录/秒")

            return True, success_records

        except Exception as e:
            logger.error(f"❌ 导入文件失败: {str(e)}")
            if conn:
                cursor.execute("""
                    UPDATE data_import_log SET
                        status = 'failed',
                        error_message = %s,
                        end_time = to_timestamp(%s)
                    WHERE id = %s
                """, (str(e)[:500], time.time(), log_id))
                conn.commit()

            return False, 0

        finally:
            if conn:
                self.release_connection(conn)

    def extract_year_from_filename(self, filename):
        """从文件名提取年份"""
        try:
            # 文件名格式：中国专利数据库1985年.csv
            year_str = filename.split('中国专利数据库')[1].split('年')[0]
            return int(year_str)
        except:
            return None

    def import_single_year(self, year):
        """导入单年数据"""
        csv_file = Path(self.source_dir) / f"中国专利数据库{year}年.csv"

        if not csv_file.exists():
            logger.warning(f"⚠️  {year}年文件不存在")
            return False, 0

        return self.import_file(csv_file)

    def import_year_range(self, start_year, end_year):
        """导入多年数据（并行处理）"""
        years = list(range(start_year, end_year + 1))

        logger.info(f"\n开始批量导入 {start_year}-{end_year} 年数据")
        logger.info(f"共 {len(years)} 年，使用 {self.max_workers} 个线程并行处理")

        total_success = 0
        failed_years = []

        # 限制并发数，避免数据库压力过大
        with ThreadPoolExecutor(max_workers=2) as executor:
            # 提交任务
            future_to_year = {
                executor.submit(self.import_single_year, year): year
                for year in years
            }

            # 收集结果
            for future in as_completed(future_to_year):
                year = future_to_year[future]
                try:
                    success, count = future.result()
                    if success:
                        total_success += count
                        logger.info(f"✅ {year}年导入成功: {count:,} 条")
                    else:
                        failed_years.append(year)
                        logger.error(f"❌ {year}年导入失败")
                except Exception as e:
                    failed_years.append(year)
                    logger.error(f"❌ {year}年导入异常: {str(e)}")

        # 最终统计
        logger.info(f"\n{'='*60}")
        logger.info('批量导入完成!')
        logger.info(f"成功年份: {len(years) - len(failed_years)}/{len(years)}")
        logger.info(f"总记录数: {total_success:,}")
        if failed_years:
            logger.info(f"失败年份: {failed_years}")

        return len(failed_years) == 0, total_success

    def test_database_connection(self):
        """测试数据库连接"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT version();')
            version = cursor.fetchone()[0]
            cursor.close()
            self.release_connection(conn)
            logger.info(f"✅ 数据库连接成功: {version[:50]}...")
            return True
        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {str(e)}")
            return False

    def cleanup(self):
        """清理资源"""
        if hasattr(self, 'connection_pool'):
            self.connection_pool.closeall()
            logger.info('✅ 数据库连接池已关闭')

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='PostgreSQL专利数据导入工具')
    parser.add_argument('--year', type=int, help='导入指定年份数据')
    parser.add_argument('--batch', help='批量导入年份范围，格式：1985-2025')
    parser.add_argument('--test', action='store_true', help='测试数据库连接')
    parser.add_argument('--source-dir', help='源数据目录')

    args = parser.parse_args()

    # 创建导入器
    importer = PostgreSQLPatentImporter()

    try:
        # 更新源目录（如果指定）
        if args.source_dir:
            importer.source_dir = args.source_dir

        # 测试连接
        if args.test:
            importer.test_database_connection()
            return

        # 检查源目录
        if not Path(importer.source_dir).exists():
            logger.error(f"❌ 源目录不存在: {importer.source_dir}")
            return

        # 执行导入
        start_time = time.time()

        if args.year:
            # 导入单年
            success, count = importer.import_single_year(args.year)
            if success:
                logger.info(f"\n🎉 {args.year}年数据导入成功，共 {count:,} 条记录")
            else:
                logger.error(f"\n❌ {args.year}年数据导入失败")

        elif args.batch:
            # 批量导入
            try:
                start_year, end_year = map(int, args.batch.split('-'))
                success, total = importer.import_year_range(start_year, end_year)
                if success:
                    logger.info(f"\n🎉 批量导入完成，共 {total:,} 条记录")
                else:
                    logger.error("\n❌ 部分年份导入失败")
            except ValueError:
                logger.error('❌ 年份范围格式错误，请使用格式：1985-2025')

        else:
            logger.error('❌ 请指定导入年份或年份范围')
            parser.print_help()

        duration = time.time() - start_time
        logger.info(f"\n总耗时: {duration:.1f}秒")

    finally:
        importer.cleanup()

if __name__ == '__main__':
    main()