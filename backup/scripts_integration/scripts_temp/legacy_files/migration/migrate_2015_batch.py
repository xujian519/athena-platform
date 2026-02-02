#!/usr/bin/env python3
"""
专门用于迁移2015年数据的批量脚本
"""

import logging
import sys
import time
from datetime import datetime

import psycopg2

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migrate_2015.log'),
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

def check_progress():
    """检查当前进度"""
    conn = get_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()

        # 检查总数和已迁移数
        cursor.execute('SELECT COUNT(*) FROM patents_simple WHERE source_year = 2015')
        total = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM patents WHERE source_year = 2015')
        migrated = cursor.fetchone()[0]

        remaining = total - migrated
        percentage = (migrated / total * 100) if total > 0 else 0

        logger.info(f"2015年数据状态: 总数 {total:,}, 已迁移 {migrated:,}, 剩余 {remaining:,}, 完成率 {percentage:.2f}%")

        cursor.close()
        conn.close()
        return remaining, total

    except Exception as e:
        logger.error(f"检查进度失败: {e}")
        conn.close()
        return None, None

def migrate_batch(batch_size=10000):
    """执行批量迁移"""
    conn = get_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        # 使用SQL的LIMIT和OFFSET进行分批
        offset = 0
        total_migrated = 0

        while True:
            start_time = time.time()

            # 查询并插入新数据
            cursor.execute("""
                INSERT INTO patents (
                    patent_name, patent_type, application_number, application_date,
                    applicant, inventor, ipc_code, abstract, source_year, source_file
                )
                SELECT
                    ps.patent_name,
                    ps.patent_type,
                    ps.application_number,
                    ps.application_date,
                    ps.applicant,
                    ps.inventor,
                    ps.ipc_code,
                    ps.abstract,
                    ps.source_year,
                    '中国专利数据库2015年.csv'
                FROM patents_simple ps
                WHERE ps.source_year = 2015
                AND ps.application_number NOT IN (
                    SELECT application_number FROM patents WHERE source_year = 2015
                )
                ORDER BY ps.id
                LIMIT %s
            """, (batch_size,))

            batch_count = cursor.rowcount

            if batch_count == 0:
                logger.info('没有更多数据需要迁移')
                break

            # 提交事务
            conn.commit()

            total_migrated += batch_count
            batch_time = time.time() - start_time
            speed = batch_count / batch_time if batch_time > 0 else 0

            logger.info(f"批次完成: 迁移 {batch_count:,} 条, 耗时 {batch_time:.1f}s, 速度 {speed:.0f} 条/秒, 总计 {total_migrated:,}")

            # 短暂休息
            time.sleep(0.1)

            # 调整批次大小以提高效率
            if batch_time < 5:
                batch_size = min(batch_size * 2, 50000)
            elif batch_time > 30:
                batch_size = max(batch_size // 2, 5000)

        cursor.close()
        conn.close()

        logger.info(f"2015年数据迁移完成，共迁移 {total_migrated:,} 条记录")
        return True

    except Exception as e:
        logger.error(f"迁移失败: {e}")
        conn.rollback()
        conn.close()
        return False

def main():
    """主函数"""
    logger.info('=' * 80)
    logger.info('开始迁移2015年专利数据')
    logger.info('=' * 80)

    # 检查初始状态
    remaining, total = check_progress()
    if remaining is None:
        logger.error('无法获取当前状态')
        return False

    if remaining == 0:
        logger.info('2015年数据已全部迁移完成')
        return True

    logger.info(f"开始迁移剩余的 {remaining:,} 条数据")

    # 执行迁移
    success = migrate_batch(batch_size=20000)

    # 检查最终状态
    logger.info("\n最终状态检查:")
    remaining_final, total_final = check_progress()

    if success and remaining_final == 0:
        logger.info('✅ 2015年数据迁移成功完成！')
    else:
        logger.error(f"❌ 迁移未完全完成，还有 {remaining_final:,} 条数据")

    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)