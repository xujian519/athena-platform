#!/usr/bin/env python3
"""
优化的专利数据导入脚本
解决死锁问题，支持断点续传和错误恢复
"""

import argparse
import csv
import hashlib
import json
import logging
import os
import signal
import sys
import threading
import time
from contextlib import contextmanager
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
        logging.FileHandler('documentation/logs/optimized_import.log'),
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

# 全局变量用于优雅停止
stop_flag = False

class OptimizedPatentImporter:
    """优化的专利数据导入器"""

    def __init__(self):
        self.source_dir = '/Volumes/xujian/patent_data/china_patents'
        self.batch_size = 1000  # 减小批次大小，避免死锁
        self.checkpoint_file = 'cache/import_checkpoint.json'
        self.lock_timeout = 30  # 锁等待超时时间

        # 创建必要目录
        os.makedirs('logs', exist_ok=True)
        os.makedirs('cache', exist_ok=True)

        # 信号处理
        signal.signal(signal.SIGINT, self._handle_interrupt)
        signal.signal(signal.SIGTERM, self._handle_interrupt)

    def _handle_interrupt(self, signum, frame):
        """处理中断信号"""
        global stop_flag
        logger.info("\n接收到中断信号，正在优雅停止...")
        stop_flag = True

    @contextmanager
    def get_db_connection(self, retry_count=3):
        """获取数据库连接，支持重试"""
        conn = None
        for attempt in range(retry_count):
            try:
                conn = psycopg2.connect(
                    **DB_CONFIG,
                    cursor_factory=DictCursor,
                    connect_timeout=10,
                    application_name='patent_importer'
                )
                # 设置锁超时
                conn.autocommit = False
                with conn.cursor() as cursor:
                    cursor.execute("SET lock_timeout = '30s'")
                yield conn
                break
            except Exception as e:
                logger.warning(f"数据库连接失败 (尝试 {attempt + 1}/{retry_count}): {str(e)}")
                if attempt == retry_count - 1:
                    raise
                time.sleep(2 ** attempt)  # 指数退避
            finally:
                if conn and conn.closed == 0:
                    conn.close()

    def load_checkpoint(self):
        """加载检查点"""
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载检查点失败: {e}")
        return {}

    def save_checkpoint(self, data):
        """保存检查点"""
        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"保存检查点失败: {e}")

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

        # 基本验证
        application_number = safe_get(row[8]) if len(row) > 8 else None
        if not application_number or len(application_number) < 5:
            return None  # 跳过无效记录

        # 使用安全的方式访问字段
        def get_field(index, default=''):
            return safe_get(row[index]) if len(row) > index else default

        patent_data = {
            'patent_name': get_field(0),
            'patent_type': self.normalize_patent_type(get_field(1)),
            'application_number': application_number,
            'application_date': parse_date(get_field(9)),
            'publication_number': get_field(11),
            'publication_date': parse_date(get_field(12)),
            'authorization_number': get_field(15),
            'authorization_date': parse_date(get_field(16)),
            'applicant': get_field(2) or '未知申请人',
            'applicant_type': get_field(3),
            'applicant_address': get_field(4),
            'applicant_region': get_field(5),
            'applicant_city': get_field(6),
            'applicant_district': get_field(7),
            'current_assignee': get_field(22),
            'current_assignee_address': get_field(23),
            'assignee_type': get_field(24),
            'credit_code': get_field(25),
            'inventor': get_field(19),
            'ipc_code': get_field(17),
            'ipc_main_class': self.extract_ipc_main_class(get_field(17)),
            'ipc_classification': get_field(17),
            'abstract': get_field(20),
            'claims_content': get_field(21),
            'claims': get_field(21),
            'citation_count': self.safe_int(get_field(26)),
            'cited_count': self.safe_int(get_field(27)),
            'self_citation_count': self.safe_int(get_field(28)),
            'other_citation_count': self.safe_int(get_field(29)),
            'cited_by_self_count': self.safe_int(get_field(30)),
            'cited_by_others_count': self.safe_int(get_field(31)),
            'family_citation_count': self.safe_int(get_field(32)),
            'family_cited_count': self.safe_int(get_field(33)),
            'source_year': int(get_field(10)) if get_field(10) and get_field(10).isdigit() else None,
            'source_file': file_name if file_name else ''
        }

        return patent_data

    def extract_ipc_main_class(self, ipc_code):
        """提取IPC主分类号"""
        if not ipc_code:
            return None
        parts = ipc_code.split()
        if parts:
            main_class = parts[0]
            if len(main_class) >= 4:
                return main_class[:4]
        return None

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

    def import_batch(self, records, conn):
        """批量导入专利记录（使用COPY命令）"""
        if not records:
            return 0, 0

        cursor = conn.cursor()

        try:
            # 准备插入语句（使用ON CONFLICT处理重复）
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

            # 将字典转换为元组列表，按照SQL字段顺序
            batch_data = []
            for i, record in enumerate(records):
                # 确保record是字典类型
                if not isinstance(record, dict):
                    logger.error(f"记录类型错误: {type(record)}")
                    continue

                # 创建元组 - 36个值（不包括id、search_vector、created_at、updated_at）
                values = (
                    record.get('patent_name'),          # 1
                    record.get('patent_type'),          # 2
                    record.get('application_number'),   # 3
                    record.get('application_date'),      # 4
                    record.get('publication_number'),   # 5
                    record.get('publication_date'),      # 6
                    record.get('authorization_number'), # 7
                    record.get('authorization_date'),   # 8
                    record.get('applicant'),            # 9
                    record.get('applicant_type'),        # 10
                    record.get('applicant_address'),     # 11
                    record.get('applicant_region'),      # 12
                    record.get('applicant_city'),         # 13
                    record.get('applicant_district'),    # 14
                    record.get('current_assignee'),      # 15
                    record.get('current_assignee_address'), # 16
                    record.get('assignee_type'),         # 17
                    record.get('credit_code'),            # 18
                    record.get('inventor'),              # 19
                    record.get('ipc_code'),              # 20
                    record.get('ipc_main_class'),        # 21
                    record.get('ipc_classification'),    # 22
                    record.get('abstract'),              # 23
                    record.get('claims_content'),         # 24
                    record.get('claims'),                # 25
                    record.get('citation_count', 0),     # 26
                    record.get('cited_count', 0),        # 27
                    record.get('self_citation_count', 0), # 28
                    record.get('other_citation_count', 0), # 29
                    record.get('cited_by_self_count', 0), # 30
                    record.get('cited_by_others_count', 0), # 31
                    record.get('family_citation_count', 0), # 32
                    record.get('family_cited_count', 0),  # 33
                    record.get('source_year'),           # 34
                    record.get('source_file'),           # 35
                    None,                                # 36 - file_hash
                )

                # 验证元组长度（36个值，不包括id、search_vector、created_at、updated_at）
                if len(values) != 36:
                    logger.error(f"第{i}条记录元组长度错误: {len(values)}, 期望36")

                batch_data.append(values)

            logger.info(f"准备批量插入 {len(batch_data)} 条记录")

            # 批量插入
            cursor.executemany(insert_sql, batch_data)
            conn.commit()

            return len(records), 0

        except Exception as e:
            conn.rollback()
            import traceback
            logger.error(f"❌ 批量导入失败: {str(e)}")
            logger.error(f"错误类型: {type(e).__name__}")
            if batch_data:
                logger.error(f"batch_data第一条记录长度: {len(batch_data[0])}")
                logger.error(f"batch_data第一条记录前5个值: {batch_data[0][:5]}")
            logger.error(f"完整错误堆栈: {traceback.format_exc()}")
            return 0, len(records)

    def import_file_with_checkpoint(self, file_path):
        """带检查点的文件导入"""
        file_name = Path(file_path).name
        source_year = self.extract_year_from_filename(file_name)

        if not source_year:
            logger.error(f"❌ 无法从文件名提取年份: {file_name}")
            return False, 0

        # 加载检查点
        checkpoint = self.load_checkpoint()
        checkpoint_key = file_name

        # 获取文件总行数
        total_lines = self.count_lines(file_path)
        logger.info(f"文件总行数: {total_lines:,}")

        # 检查是否有未完成的导入
        start_line = checkpoint.get(checkpoint_key, {}).get('start_line', 1)
        if start_line > 1:
            logger.info(f"从检查点恢复: 行 {start_line:,}")

        records = []
        success_records = 0
        failed_records = 0
        processed_lines = 0

        logger.info(f"\n{'='*60}")
        logger.info(f"开始导入: {file_name}")
        logger.info(f"年份: {source_year}")
        logger.info(f"文件大小: {Path(file_path).stat().st_size / (1024*1024):.1f} MB")
        logger.info(f"从行: {start_line:,}")
        logger.info(f"{'='*60}\n")

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.reader(f)

                # 跳过到起始行
                for _ in range(start_line - 1):
                    try:
                        next(reader)
                    except StopIteration:
                        break

                # 逐行处理
                current_line = start_line
                for row in reader:
                    # 检查是否需要停止
                    global stop_flag
                    if stop_flag:
                        logger.info('导入已中断')
                        break

                    try:
                        # 解析数据
                        patent_data = self.parse_patent_data(row, file_name)

                        # 跳过无效记录
                        if patent_data is None:
                            failed_records += 1
                            continue

                        patent_data['source_year'] = source_year
                        records.append(patent_data)

                        # 批量处理
                        if len(records) >= self.batch_size:
                            with self.get_db_connection() as conn:
                                s, f = self.import_batch(records, conn)
                                success_records += s
                                failed_records += f
                                records = []

                            # 显示进度
                            if current_line % 10000 == 0:
                                logger.info(f"  进度: {current_line:,} 条记录 (成功: {success_records:,}, 失败: {failed_records:,})")

                                # 保存检查点
                                checkpoint[checkpoint_key] = {
                                    'start_line': current_line + 1,
                                    'success_records': success_records,
                                    'failed_records': failed_records,
                                    'timestamp': datetime.now().isoformat()
                                }
                                self.save_checkpoint(checkpoint)

                    except Exception as e:
                        logger.warning(f"  警告: 第{current_line}行解析失败: {str(e)[:100]}")
                        failed_records += 1
                        continue

                    current_line += 1
                    processed_lines += 1

                # 处理剩余记录
                if records and not stop_flag:
                    with self.get_db_connection() as conn:
                        s, f = self.import_batch(records, conn)
                        success_records += s
                        failed_records += f

            # 最终统计
            total_records = success_records + failed_records
            if not stop_flag:
                # 导入完成，清理检查点
                if checkpoint_key in checkpoint:
                    del checkpoint[checkpoint_key]
                    self.save_checkpoint(checkpoint)

            logger.info(f"\n{'='*60}")
            logger.info(f"导入{'完成' if not stop_flag else '中断'}!")
            logger.info(f"  处理行数: {processed_lines:,}")
            logger.info(f"  有效记录: {success_records:,}")
            logger.info(f"  失败记录: {failed_records:,}")
            if processed_lines > 0:
                logger.info(f"  成功率: {success_records/processed_lines*100:.1f}%")
            logger.info(f"{'='*60}\n")

            return not stop_flag, success_records

        except Exception as e:
            logger.error(f"❌ 导入文件失败: {str(e)}")
            return False, 0

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

    def import_year(self, year):
        """导入单年数据"""
        csv_file = Path(self.source_dir) / f"中国专利数据库{year}年.csv"

        if not csv_file.exists():
            logger.warning(f"⚠️  {year}年文件不存在")
            return False, 0

        success, count = self.import_file_with_checkpoint(csv_file)

        if success:
            logger.info(f"✅ {year}年导入成功，共 {count:,} 条记录")
        else:
            logger.info(f"⏸️  {year}年导入中断，已导入 {count:,} 条记录")

        return success, count

    def cleanup(self):
        """清理资源"""
        logger.info('导入器已停止')

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='优化的专利数据导入工具')
    parser.add_argument('--year', type=int, help='导入指定年份数据')
    parser.add_argument('--resume', action='store_true', help='从检查点恢复导入')
    parser.add_argument('--clean', action='store_true', help='清理检查点文件')

    args = parser.parse_args()

    # 清理检查点
    if args.clean:
        checkpoint_file = 'cache/import_checkpoint.json'
        if os.path.exists(checkpoint_file):
            os.remove(checkpoint_file)
            logger.info(f"已删除检查点文件: {checkpoint_file}")

    # 创建导入器
    importer = OptimizedPatentImporter()

    try:
        if args.year:
            # 导入单年
            start_time = time.time()
            success, count = importer.import_year(args.year)
            duration = time.time() - start_time

            if count > 0:
                logger.info(f"\n处理速度: {count/duration:.1f} 记录/秒")

            logger.info(f"\n总耗时: {duration:.1f}秒")
            logger.info(f"状态: {'成功完成' if success else '已中断'}")

        else:
            logger.error('❌ 请指定要导入的年份')
            parser.print_help()

    except KeyboardInterrupt:
        logger.info("\n用户取消导入")

    finally:
        importer.cleanup()

if __name__ == '__main__':
    main()