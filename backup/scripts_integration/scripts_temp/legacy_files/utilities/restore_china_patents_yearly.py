#!/usr/bin/env python3
"""
逐年恢复中国专利数据库
包含数据验证功能
"""

import csv
import json
import logging
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 路径配置
SOURCE_DIR = '/Volumes/xujian/patent_data/china_patents'
DB_PATH = 'data/patents/processed/china_patents_enhanced.db'
BACKUP_DIR = 'data/patents/processed/backups'

class ChinaPatentRestorer:
    """中国专利数据库恢复器"""

    def __init__(self):
        self.conn = None
        self.processed_years = []
        self.stats = {
            'total_files': 0,
            'processed_files': 0,
            'total_patents': 0,
            'successful_years': [],
            'failed_years': [],
            'validation_results': {}
        }

    def connect_db(self):
        """连接数据库"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

            self.conn = sqlite3.connect(DB_PATH)
            self.conn.execute('PRAGMA journal_mode=WAL')
            self.conn.execute('PRAGMA synchronous=NORMAL')
            self.conn.execute('PRAGMA cache_size=100000')
            self.conn.execute('PRAGMA temp_store=MEMORY')

            # 创建专利表（如果不存在）
            self.create_patent_table()

            logger.info('数据库连接成功')
            return True
        except Exception as e:
            logger.error(f"数据库连接失败: {str(e)}")
            return False

    def create_patent_table(self):
        """创建专利表"""
        cursor = self.conn.cursor()

        # 检查表是否存在
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='patents'
        """)
        table_exists = cursor.fetchone()

        if not table_exists:
            # 创建完整的专利表
            cursor.execute("""
                CREATE TABLE patents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patent_name TEXT,
                    patent_type TEXT,
                    applicant TEXT,
                    inventor TEXT,
                    application_number TEXT,
                    application_date TEXT,
                    publication_number TEXT,
                    publication_date TEXT,
                    authorization_number TEXT,
                    authorization_date TEXT,
                    ipc_classification TEXT,
                    abstract TEXT,
                    claims TEXT,
                    year INTEGER,
                    source_file TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(application_number)
                )
            """)

            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_applicant ON patents(applicant)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_inventor ON patents(inventor)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_application_number ON patents(application_number)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_publication_number ON patents(publication_number)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_year ON patents(year)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ipc ON patents(ipc_classification)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_application_date ON patents(application_date)')

            logger.info('专利表创建成功')
        else:
            # 检查并添加缺失的列
            cursor.execute('PRAGMA table_info(patents)')
            columns = {col[1] for col in cursor.fetchall()}

            required_columns = {
                'patent_name', 'patent_type', 'applicant', 'inventor',
                'application_number', 'application_date', 'publication_number',
                'publication_date', 'authorization_number', 'authorization_date',
                'ipc_classification', 'abstract', 'claims', 'year', 'source_file'
            }

            for col in required_columns:
                if col not in columns:
        # TODO: 检查SQL注入风险 - cursor.execute(f"ALTER TABLE patents ADD COLUMN {col} TEXT")
                            cursor.execute(f"ALTER TABLE patents ADD COLUMN {col} TEXT")

    def get_year_from_filename(self, filename):
        """从文件名提取年份"""
        try:
            # 提取四位数字年份
            year = int(''.join(filter(str.isdigit, filename.split('年')[0])))
            return year
        except:
            return None

    def analyze_csv_structure(self, filepath):
        """分析CSV文件结构"""
        try:
            # 读取前100行分析结构
            df_sample = pd.read_csv(filepath, nrows=100, encoding='utf-8', on_bad_lines='skip')

            # 列名映射（根据常见的中文列名）
            column_mapping = {
                '专利名称': 'patent_name',
                '专利类型': 'patent_type',
                '申请人': 'applicant',
                '发明人': 'inventor',
                '申请号': 'application_number',
                '申请日': 'application_date',
                '公开号': 'publication_number',
                '公开日': 'publication_date',
                '授权公告号': 'authorization_number',
                '授权公告日': 'authorization_date',
                'IPC分类号': 'ipc_classification',
                '摘要': 'abstract',
                '主权项': 'claims'
            }

            # 检查哪些列存在
            available_columns = {}
            for chinese_col, english_col in column_mapping.items():
                for col in df_sample.columns:
                    if chinese_col in col or english_col.lower() in col.lower():
                        available_columns[english_col] = col
                        break

            return available_columns, df_sample.columns.tolist()
        except Exception as e:
            logger.error(f"分析CSV结构失败 {filepath}: {str(e)}")
            return {}, []

    def import_year_data(self, year):
        """导入特定年份的数据"""
        pattern = f"中国专利数据库{year}年*.csv"
        matching_files = list(Path(SOURCE_DIR).glob(pattern))

        if not matching_files:
            logger.warning(f"未找到{year}年的数据文件")
            return False

        # 使用第一个匹配的文件
        filepath = matching_files[0]
        logger.info(f"处理文件: {filepath}")

        try:
            # 分析CSV结构
            column_mapping, all_columns = self.analyze_csv_structure(filepath)

            if not column_mapping:
                logger.error(f"无法识别{filepath}的列结构")
                return False

            logger.info(f"识别的列映射: {json.dumps(column_mapping, ensure_ascii=False, indent=2)}")

            # 分批导入数据
            batch_size = 1000
            total_imported = 0
            skipped_count = 0

            # 使用pandas读取大文件
            chunks = pd.read_csv(
                filepath,
                chunksize=batch_size,
                encoding='utf-8',
                on_bad_lines='skip',
                dtype=str  # 所有列都作为字符串处理
            )

            for chunk_idx, chunk in enumerate(chunks):
                cursor = self.conn.cursor()

                for _, row in chunk.iterrows():
                    # 准备数据
                    patent_data = {
                        'patent_name': self.get_value(row, column_mapping.get('patent_name')),
                        'patent_type': self.get_value(row, column_mapping.get('patent_type')),
                        'applicant': self.get_value(row, column_mapping.get('applicant')),
                        'inventor': self.get_value(row, column_mapping.get('inventor')),
                        'application_number': self.get_value(row, column_mapping.get('application_number')),
                        'application_date': self.normalize_date(self.get_value(row, column_mapping.get('application_date'))),
                        'publication_number': self.get_value(row, column_mapping.get('publication_number')),
                        'publication_date': self.normalize_date(self.get_value(row, column_mapping.get('publication_date'))),
                        'authorization_number': self.get_value(row, column_mapping.get('authorization_number')),
                        'authorization_date': self.normalize_date(self.get_value(row, column_mapping.get('authorization_date'))),
                        'ipc_classification': self.get_value(row, column_mapping.get('ipc_classification')),
                        'abstract': self.get_value(row, column_mapping.get('abstract')),
                        'claims': self.get_value(row, column_mapping.get('claims')),
                        'year': year,
                        'source_file': filepath.name
                    }

                    # 检查必要字段
                    if not patent_data['application_number']:
                        skipped_count += 1
                        continue

                    # 插入或更新数据
                    try:
                        cursor.execute("""
                            INSERT OR REPLACE INTO patents
                            (patent_name, patent_type, applicant, inventor, application_number,
                             application_date, publication_number, publication_date,
                             authorization_number, authorization_date, ipc_classification,
                             abstract, claims, year, source_file, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            patent_data['patent_name'], patent_data['patent_type'],
                            patent_data['applicant'], patent_data['inventor'],
                            patent_data['application_number'], patent_data['application_date'],
                            patent_data['publication_number'], patent_data['publication_date'],
                            patent_data['authorization_number'], patent_data['authorization_date'],
                            patent_data['ipc_classification'], patent_data['abstract'],
                            patent_data['claims'], patent_data['year'],
                            patent_data['source_file'], datetime.now().isoformat()
                        ))
                        total_imported += 1
                    except Exception as e:
                        skipped_count += 1
                        continue

                # 提交批次
                self.conn.commit()

                if chunk_idx % 10 == 0:  # 每10000行报告一次
                    logger.info(f"{year}年: 已处理 {(chunk_idx+1)*batch_size} 行，导入 {total_imported} 条")

            logger.info(f"{year}年数据导入完成: 总计导入 {total_imported} 条，跳过 {skipped_count} 条")

            # 验证导入的数据
            validation_result = self.validate_year_data(year)
            self.stats['validation_results'][year] = validation_result

            return True

        except Exception as e:
            logger.error(f"导入{year}年数据失败: {str(e)}")
            return False

    def get_value(self, row, column_name):
        """安全获取值"""
        if not column_name:
            return None
        try:
            value = row.get(column_name, '')
            return str(value).strip() if pd.notna(value) else None
        except:
            return None

    def normalize_date(self, date_str):
        """标准化日期格式"""
        if not date_str or pd.isna(date_str):
            return None

        try:
            date_str = str(date_str).strip()

            # 处理常见格式
            if '.' in date_str:
                date_str = date_str.replace('.', '-')
            if '/' in date_str:
                date_str = date_str.replace('/', '-')

            # 确保格式为YYYY-MM-DD
            if len(date_str) == 8 and date_str.isdigit():
                date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"

            return date_str
        except:
            return date_str  # 返回原始值

    def validate_year_data(self, year):
        """验证特定年份的数据"""
        cursor = self.conn.cursor()

        # 统计数据
        cursor.execute('SELECT COUNT(*) FROM patents WHERE year = ?', (year,))
        total_count = cursor.fetchone()[0]

        # 检查关键字段的非空率
        cursor.execute("""
            SELECT
                COUNT(application_number) as total_applications,
                COUNT(applicant) as total_applicants,
                COUNT(abstract) as total_abstracts,
                COUNT(ipc_classification) as total_ipc,
                COUNT(DISTINCT applicant) as unique_applicants
            FROM patents
            WHERE year = ?
        """, (year,))
        stats = cursor.fetchone()

        # 随机抽样检查几条数据
        cursor.execute("""
            SELECT patent_name, applicant, application_number, ipc_classification, abstract
            FROM patents
            WHERE year = ? AND patent_name IS NOT NULL
            LIMIT 5
        """, (year,))
        samples = cursor.fetchall()

        validation_result = {
            'year': year,
            'total_patents': total_count,
            'has_application_number': stats[0],
            'has_applicant': stats[1],
            'has_abstract': stats[2],
            'has_ipc': stats[3],
            'unique_applicants': stats[4],
            'sample_data': [
                {
                    'patent_name': row[0],
                    'applicant': row[1],
                    'application_number': row[2],
                    'ipc': row[3],
                    'abstract_preview': row[4][:100] + '...' if row[4] and len(row[4]) > 100 else row[4]
                }
                for row in samples
            ]
        }

        return validation_result

    def backup_database(self):
        """备份数据库"""
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(BACKUP_DIR, f"china_patents_backup_{timestamp}.db")

        try:
            # 关闭当前连接
            self.conn.close()

            # 复制文件
            import shutil
            shutil.copy2(DB_PATH, backup_file)

            # 重新连接
            self.connect_db()

            logger.info(f"数据库已备份到: {backup_file}")
            return backup_file
        except Exception as e:
            logger.error(f"备份失败: {str(e)}")
            return None

    def restore_all_years(self, start_year=None, end_year=None):
        """恢复所有年份的数据"""
        # 获取所有可用年份
        csv_files = list(Path(SOURCE_DIR).glob('中国专利数据库*.csv'))
        available_years = sorted(set([
            self.get_year_from_filename(f.name)
            for f in csv_files
            if self.get_year_from_filename(f.name)
        ]))

        logger.info(f"找到 {len(available_years)} 年的数据: {available_years}")

        # 确定处理范围
        if start_year:
            available_years = [y for y in available_years if y >= start_year]
        if end_year:
            available_years = [y for y in available_years if y <= end_year]

        self.stats['total_files'] = len(available_years)

        # 逐年处理
        for year in available_years:
            logger.info(f"\n{'='*50}")
            logger.info(f"开始处理 {year} 年数据")
            logger.info(f"{'='*50}")

            if self.import_year_data(year):
                self.stats['processed_files'] += 1
                self.stats['successful_years'].append(year)
            else:
                self.stats['failed_years'].append(year)

            # 每年处理完后备份
            if self.stats['processed_files'] % 5 == 0:
                self.backup_database()

        # 更新统计
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM patents')
        self.stats['total_patents'] = cursor.fetchone()[0]

    def print_summary(self):
        """打印恢复摘要"""
        logger.info("\n" + '='*50)
        logger.info('中国专利数据库恢复摘要')
        logger.info('='*50)

        logger.info(f"总文件数: {self.stats['total_files']}")
        logger.info(f"成功处理: {self.stats['processed_files']}")
        logger.info(f"失败年份: {self.stats['failed_years']}")
        logger.info(f"总专利数: {self.stats['total_patents']:,}")

        logger.info("\n数据验证摘要:")
        for year, result in self.stats['validation_results'].items():
            logger.info(f"\n{year}年:")
            logger.info(f"  - 总专利数: {result['total_patents']:,}")
            logger.info(f"  - 有申请号: {result['has_application_number']:,}")
            logger.info(f"  - 有申请人: {result['has_applicant']:,}")
            logger.info(f"  - 有摘要: {result['has_abstract']:,}")
            logger.info(f"  - 有IPC分类: {result['has_ipc']:,}")
            logger.info(f"  - 独立申请人: {result['unique_applicants']:,}")

            if result['sample_data']:
                logger.info('  - 样本数据:')
                for i, sample in enumerate(result['sample_data'][:2], 1):
                    logger.info(f"    {i}. {sample['patent_name'][:50]}...")
                    logger.info(f"       申请人: {sample['applicant']}")
                    logger.info(f"       申请号: {sample['application_number']}")

    def test_search_functionality(self):
        """测试搜索功能"""
        logger.info("\n测试搜索功能...")

        cursor = self.conn.cursor()

        # 测试1: 按申请人搜索
        test_applicants = ['华为', '腾讯', '阿里巴巴', '中科院', '清华大学']
        for applicant in test_applicants:
            cursor.execute(
                'SELECT COUNT(*) FROM patents WHERE applicant LIKE ?',
                (f"%{applicant}%",)
            )
            count = cursor.fetchone()[0]
            if count > 0:
                logger.info(f"  - {applicant}: {count} 条专利")

        # 测试2: 按IPC分类搜索
        cursor.execute(
            'SELECT ipc_classification, COUNT(*) FROM patents WHERE ipc_classification IS NOT NULL GROUP BY ipc_classification LIMIT 10'
        )
        ipc_stats = cursor.fetchall()
        logger.info('  - IPC分类统计（前10）:')
        for ipc, count in ipc_stats:
            logger.info(f"    {ipc}: {count} 条")

        # 测试3: 按年份统计
        cursor.execute(
            'SELECT year, COUNT(*) FROM patents GROUP BY year ORDER BY year'
        )
        year_stats = cursor.fetchall()
        logger.info('  - 按年份统计:')
        for year, count in year_stats:
            logger.info(f"    {year}年: {count:,} 条")

def main():
    """主函数"""
    import argparse

# 导入标准化数据库工具
from shared.database.db_utils import DatabaseManager, build_safe_query

    parser = argparse.ArgumentParser(description='恢复中国专利数据库')
    parser.add_argument('--start-year', type=int, help='开始年份')
    parser.add_argument('--end-year', type=int, help='结束年份')
    args = parser.parse_args()

    restorer = ChinaPatentRestorer()

    # 连接数据库
    if not restorer.connect_db():
        logger.error('无法连接数据库')
        return

    try:
        # 备份现有数据库
        logger.info('备份现有数据库...')
        restorer.backup_database()

        # 恢复数据
        restorer.restore_all_years(args.start_year, args.end_year)

        # 打印摘要
        restorer.print_summary()

        # 测试搜索功能
        restorer.test_search_functionality()

    except Exception as e:
        logger.error(f"恢复过程出错: {str(e)}")
    finally:
        restorer.conn.close()

if __name__ == '__main__':
    main()