#!/usr/bin/env python3
"""
优化的分批专利数据迁移脚本
支持大数据量分批处理，错峰执行，索引优化
"""

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
        logging.FileHandler('migration.log'),
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

class OptimizedMigrator:
    def __init__(self):
        self.conn = None
        self.connect_db()

    def connect_db(self):
        """连接数据库"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.conn.autocommit = False
            logger.info('数据库连接成功')
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            sys.exit(1)

    def drop_indexes(self):
        """暂时删除不必要的索引以提高迁移速度"""
        cursor = self.conn.cursor()
        try:
            logger.info('删除非必要索引以提高迁移速度...')

            # 删除patents表的次要索引
            indexes_to_drop = [
                'idx_patents_applicant',
                'idx_patents_inventor',
                'idx_patents_ipc_code',
                'idx_patents_source_year',
                'idx_patents_application_date'
            ]

            for index_name in indexes_to_drop:
        # TODO: 检查SQL注入风险 - cursor.execute(f"""
                        cursor.execute(f"""
                    SELECT 1 FROM pg_indexes
                    WHERE tablename = 'patents' AND indexname = '{index_name}'
                """)
                if cursor.fetchone():
        # TODO: 检查SQL注入风险 - cursor.execute(f"DROP INDEX IF EXISTS {index_name}")
                            cursor.execute(f"DROP INDEX IF EXISTS {index_name}")
                    logger.info(f"删除索引: {index_name}")

            self.conn.commit()
            logger.info('索引删除完成')
        except Exception as e:
            logger.error(f"删除索引时出错: {e}")
            self.conn.rollback()
        finally:
            cursor.close()

    def create_indexes(self):
        """重新创建索引"""
        cursor = self.conn.cursor()
        try:
            logger.info('重建索引...')

            # 重建索引
            indexes_to_create = [
                ('CREATE INDEX CONCURRENTLY idx_patents_applicant ON patents(applicant)', '申请人索引'),
                ('CREATE INDEX CONCURRENTLY idx_patents_inventor ON patents(inventor)', '发明人索引'),
                ('CREATE INDEX CONCURRENTLY idx_patents_ipc_code ON patents(ipc_code)', 'IPC索引'),
                ('CREATE INDEX CONCURRENTLY idx_patents_source_year ON patents(source_year)', '年份索引'),
                ('CREATE INDEX CONCURRENTLY idx_patents_application_date ON patents(application_date)', '申请日索引')
            ]

            for sql, desc in indexes_to_create:
                logger.info(f"创建{desc}...")
                cursor.execute(sql)
                self.conn.commit()
                logger.info(f"{desc}创建完成")

            logger.info('所有索引重建完成')
        except Exception as e:
            logger.error(f"创建索引时出错: {e}")
            self.conn.rollback()
        finally:
            cursor.close()

    def migrate_year_batched(self, year, batch_size=50000):
        """分批迁移一年的数据"""
        cursor = self.conn.cursor()

        # 获取总记录数
        cursor.execute("""
            SELECT COUNT(*) FROM patents_simple WHERE source_year = %s
        """, (year,))
        total_records = cursor.fetchone()[0]

        if total_records == 0:
            logger.info(f"{year}年没有数据需要迁移")
            return 0

        logger.info(f"开始迁移{year}年数据，共{total_records:,}条记录")
        logger.info(f"批次大小: {batch_size:,}")

        # 检查已迁移数量
        cursor.execute("""
            SELECT COUNT(*) FROM patents WHERE source_year = %s
        """, (year,))
        already_migrated = cursor.fetchone()[0]

        if already_migrated >= total_records:
            logger.info(f"{year}年数据已全部迁移")
            return total_records

        # 计算需要迁移的起始位置
        offset = already_migrated
        total_migrated = already_migrated

        # 分批迁移
        batch_num = 1
        while offset < total_records:
            start_time = time.time()

            # 执行批量插入
            cursor.execute("""
                INSERT INTO patents (
                    patent_name, patent_type, application_number, application_date,
                    applicant, inventor, ipc_code, abstract, source_year, source_file
                )
                SELECT
                    patent_name, patent_type, application_number, application_date,
                    applicant, inventor, ipc_code, abstract, source_year,
                    '中国专利数据库' || source_year || '年.csv'
                FROM patents_simple
                WHERE source_year = %s
                ORDER BY id
                LIMIT %s OFFSET %s
                ON CONFLICT (application_number) DO NOTHING
            """, (year, batch_size, offset))

            batch_migrated = cursor.rowcount
            total_migrated += batch_migrated
            offset += batch_size

            # 提交事务
            self.conn.commit()

            # 计算批次耗时和速度
            batch_time = time.time() - start_time
            speed = batch_migrated / batch_time if batch_time > 0 else 0
            progress = (total_migrated / total_records) * 100

            logger.info(f"批次 {batch_num}: 迁移 {batch_migrated:,} 条记录，"
                       f"耗时 {batch_time:.1f}s，速度 {speed:.0f} 条/秒，"
                       f"总进度 {progress:.1f}% ({total_migrated:,}/{total_records:,})")

            batch_num += 1

            # 短暂休息，避免系统负载过高
            time.sleep(0.1)

        cursor.close()
        logger.info(f"{year}年数据迁移完成，共迁移 {total_migrated:,} 条记录")
        return total_migrated

    def vacuum_analyze(self):
        """执行VACUUM和ANALYZE"""
        cursor = self.conn.cursor()
        try:
            logger.info('执行VACUUM ANALYZE...')
            cursor.execute('VACUUM ANALYZE patents')
            self.conn.commit()
            logger.info('VACUUM ANALYZE完成')
        except Exception as e:
            logger.error(f"VACUUM ANALYZE失败: {e}")
        finally:
            cursor.close()

def main():
    """主函数"""
    migrator = OptimizedMigrator()

    # 获取要迁移的年份
    years = [2015, 2020, 2021, 2025]  # 可以根据需要调整

    if len(sys.argv) > 1:
        try:
            years = [int(arg) for arg in sys.argv[1:]]
        except ValueError:
            logger.error('年份参数必须是数字')
            sys.exit(1)

    logger.info(f"计划迁移年份: {', '.join(map(str, years))}")

    # 选择操作模式
    logger.info("\n请选择操作模式:")
    logger.info('1. 完整迁移（删除索引 -> 迁移 -> 创建索引 -> VACUUM）')
    logger.info('2. 仅迁移数据')
    logger.info('3. 仅重建索引')

    choice = input("\n请输入选择 (1-3): ").strip()

    if choice == '1':
        # 完整迁移流程
        migrator.drop_indexes()

        for year in years:
            migrator.migrate_year_batched(year, batch_size=50000)

        migrator.create_indexes()
        migrator.vacuum_analyze()

    elif choice == '2':
        # 仅迁移数据
        for year in years:
            migrator.migrate_year_batched(year, batch_size=50000)

    elif choice == '3':
        # 仅重建索引
        migrator.create_indexes()

    else:
        logger.error('无效的选择')
        sys.exit(1)

    logger.info('所有任务完成！')

if __name__ == '__main__':
    main()