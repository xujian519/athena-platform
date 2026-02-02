#!/usr/bin/env python3
"""
优化专利数据库性能
创建索引、分析查询计划、优化配置
"""

import logging
import sqlite3
import time
from pathlib import Path

# 导入标准化数据库工具
from shared.database.db_utils import DatabaseManager, build_safe_query

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PatentDBOptimizer:
    """专利数据库优化器"""

    def __init__(self, db_path='data/patents/processed/china_patents_enhanced.db'):
        self.db_path = db_path
        self.conn = None

    def connect(self):
        """连接数据库"""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()

        # 优化设置
        cursor.execute('PRAGMA journal_mode = WAL')
        cursor.execute('PRAGMA synchronous = NORMAL')
        cursor.execute('PRAGMA cache_size = -500000')  # 500MB缓存
        cursor.execute('PRAGMA page_size = 32768')
        cursor.execute('PRAGMA temp_store = MEMORY')

        logger.info('数据库连接并优化设置完成')

    def analyze_table(self):
        """分析表结构"""
        cursor = self.conn.cursor()

        # 获取表信息
        cursor.execute('PRAGMA table_info(patents)')
        columns = cursor.fetchall()

        logger.info("\npatents表结构:")
        for col in columns:
            logger.info(f"  {col[1]}: {col[2]} {'NOT NULL' if col[3] else ''} {'PK' if col[5] else ''}")

        # 获取索引信息
        cursor.execute('PRAGMA index_list(patents)')
        indexes = cursor.fetchall()

        logger.info("\n现有索引:")
        for idx in indexes:
        # TODO: 检查SQL注入风险 - cursor.execute(f"PRAGMA index_info({idx[1]})")
                    cursor.execute(f"PRAGMA index_info({idx[1]})")
            idx_cols = cursor.fetchall()
            cols = ', '.join([col[2] for col in idx_cols])
            logger.info(f"  {idx[1]} ({idx[2]}): [{cols}]")

    def create_optimal_indexes(self):
        """创建优化索引"""
        cursor = self.conn.cursor()
        start_time = time.time()

        logger.info("\n开始创建优化索引...")

        # 定义要创建的索引
        indexes_to_create = [
            # 基础索引
            ('idx_patent_name', 'CREATE INDEX IF NOT EXISTS idx_patent_name ON patents(patent_name)'),
            ('idx_applicant', 'CREATE INDEX IF NOT EXISTS idx_applicant ON patents(applicant)'),
            ('idx_inventor', 'CREATE INDEX IF NOT EXISTS idx_inventor ON patents(inventor)'),
            ('idx_application_number', 'CREATE INDEX IF NOT EXISTS idx_application_number ON patents(application_number)'),
            ('idx_publication_number', 'CREATE INDEX IF NOT EXISTS idx_publication_number ON patents(publication_number)'),
            ('idx_year', 'CREATE INDEX IF NOT EXISTS idx_year ON patents(year)'),

            # 日期索引
            ('idx_application_date', 'CREATE INDEX IF NOT EXISTS idx_application_date ON patents(application_date)'),
            ('idx_publication_date', 'CREATE INDEX IF NOT EXISTS idx_publication_date ON patents(publication_date)'),
            ('idx_authorization_date', 'CREATE INDEX IF NOT EXISTS idx_authorization_date ON patents(authorization_date)'),

            # IPC分类索引
            ('idx_ipc_classification', 'CREATE INDEX IF NOT EXISTS idx_ipc_classification ON patents(ipc_classification)'),

            # 复合索引（常用查询组合）
            ('idx_year_applicant', 'CREATE INDEX IF NOT EXISTS idx_year_applicant ON patents(year, applicant)'),
            ('idx_year_ipc', 'CREATE INDEX IF NOT EXISTS idx_year_ipc ON patents(year, ipc_classification)'),
            ('idx_patent_type_year', 'CREATE INDEX IF NOT EXISTS idx_patent_type_year ON patents(patent_type, year)'),
        ]

        for idx_name, sql in indexes_to_create:
            logger.info(f"  创建索引: {idx_name}")
            cursor.execute(sql)

        self.conn.commit()
        elapsed = time.time() - start_time
        logger.info(f"\n索引创建完成，耗时: {elapsed:.2f}秒")

    def optimize_database(self):
        """优化数据库"""
        cursor = self.conn.cursor()

        logger.info("\n执行数据库优化...")
        start_time = time.time()

        # 分析表统计信息
        logger.info('  分析表统计信息...')
        cursor.execute('ANALYZE')

        # 优化数据库
        logger.info('  执行VACUUM...')
        cursor.execute('VACUUM')

        elapsed = time.time() - start_time
        logger.info(f"\n数据库优化完成，耗时: {elapsed:.2f}秒")

    def test_query_performance(self):
        """测试查询性能"""
        cursor = self.conn.cursor()

        logger.info("\n测试查询性能...")

        # 测试查询列表
        test_queries = [
            ('按申请号查询', "SELECT COUNT(*) FROM patents WHERE application_number LIKE 'CN2023%'"),
            ('按申请人查询', "SELECT COUNT(*) FROM patents WHERE applicant LIKE '%华为%'"),
            ('按年份查询', 'SELECT COUNT(*) FROM patents WHERE year = 2023'),
            ('按IPC查询', "SELECT COUNT(*) FROM patents WHERE ipc_classification LIKE 'G06F%'"),
            ('复合查询', "SELECT COUNT(*) FROM patents WHERE year = 2023 AND applicant LIKE '%华为%'"),
        ]

        for desc, sql in test_queries:
            start_time = time.time()
            cursor.execute(sql)
            result = cursor.fetchone()
            elapsed = time.time() - start_time

            logger.info(f"\n  {desc}:")
            logger.info(f"    SQL: {sql}")
            logger.info(f"    结果: {result[0]:,} 条")
            logger.info(f"    耗时: {elapsed:.3f}秒")

    def get_database_stats(self):
        """获取数据库统计信息"""
        cursor = self.conn.cursor()

        # 基本统计
        cursor.execute('SELECT COUNT(*) FROM patents')
        total_patents = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(DISTINCT year) FROM patents')
        years_count = cursor.fetchone()[0]

        cursor.execute('SELECT MIN(year), MAX(year) FROM patents')
        min_year, max_year = cursor.fetchone()

        # 计算数据库大小
        db_size = Path(self.db_path).stat().st_size / (1024 * 1024)  # MB

        logger.info("\n数据库统计信息:")
        logger.info(f"  总专利数: {total_patents:,}")
        logger.info(f"  涉及年数: {years_count}")
        logger.info(f"  年份范围: {min_year} - {max_year}")
        logger.info(f"  数据库大小: {db_size:.2f} MB")

        # 索引统计
        cursor.execute('PRAGMA index_list(patents)')
        indexes = cursor.fetchall()
        logger.info(f"\n索引数量: {len(indexes)}")

    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()

    def run_full_optimization(self):
        """执行完整优化流程"""
        logger.info('='*60)
        logger.info('专利数据库性能优化')
        logger.info('='*60)

        try:
            self.connect()
            self.get_database_stats()
            self.analyze_table()
            self.create_optimal_indexes()
            self.optimize_database()
            self.test_query_performance()
            self.get_database_stats()

            logger.info("\n✅ 数据库优化完成!")

        except Exception as e:
            logger.error(f"\n❌ 优化过程出错: {str(e)}")
        finally:
            self.close()

def main():
    optimizer = PatentDBOptimizer()
    optimizer.run_full_optimization()

if __name__ == '__main__':
    main()