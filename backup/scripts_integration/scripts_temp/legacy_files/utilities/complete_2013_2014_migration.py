#!/usr/bin/env python3
"""
完成2013-2014年剩余数据迁移的脚本
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
        logging.FileHandler('complete_2013_2014.log'),
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

def check_remaining_data(year):
    """检查某年剩余待迁移的数据"""
    conn = get_connection()
    if not conn:
        return 0, 0

    try:
        cursor = conn.cursor()

        # 检查简化表中的总数
        cursor.execute("""
            SELECT COUNT(*) FROM patents_simple
            WHERE source_year = %s
        """, (year,))
        simple_count = cursor.fetchone()[0]

        # 检查主表中已存在的数量
        cursor.execute("""
            SELECT COUNT(*) FROM patents
            WHERE source_year = %s
        """, (year,))
        main_count = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        remaining = simple_count - main_count
        logger.info(f"{year}年: 简化表 {simple_count:,}, 主表 {main_count:,}, 剩余 {remaining:,}")

        return remaining, simple_count

    except Exception as e:
        logger.error(f"检查{year}年数据失败: {e}")
        conn.close()
        return 0, 0

def migrate_remaining_data(year, batch_size=10000):
    """迁移某年剩余的数据"""
    conn = get_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        # 获取需要迁移的记录数
        cursor.execute("""
            SELECT COUNT(*) FROM patents_simple ps
            LEFT JOIN patents p ON ps.application_number = p.application_number
            WHERE ps.source_year = %s AND p.application_number IS NULL
        """, (year,))
        remaining_count = cursor.fetchone()[0]

        if remaining_count == 0:
            logger.info(f"{year}年没有需要迁移的数据")
            conn.close()
            return True

        logger.info(f"开始迁移{year}年剩余的 {remaining_count:,} 条记录")

        # 使用批量插入，每次处理batch_size条
        offset = 0
        total_migrated = 0

        while offset < remaining_count:
            start_time = time.time()

            # 插入尚未迁移的数据
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
                    '中国专利数据库' || ps.source_year || '年.csv'
                FROM patents_simple ps
                LEFT JOIN patents p ON ps.application_number = p.application_number
                WHERE ps.source_year = %s AND p.application_number IS NULL
                ORDER BY ps.id
                LIMIT %s
            """, (year, batch_size))

            batch_migrated = cursor.rowcount
            total_migrated += batch_migrated

            # 提交事务
            conn.commit()

            # 计算速度和进度
            batch_time = time.time() - start_time
            speed = batch_migrated / batch_time if batch_time > 0 else 0
            progress = (total_migrated / remaining_count) * 100

            logger.info(f"{year}年批次: 迁移 {batch_migrated:,} 条, "
                       f"耗时 {batch_time:.1f}s, 速度 {speed:.0f} 条/秒, "
                       f"总进度 {progress:.1f}% ({total_migrated:,}/{remaining_count:,})")

            # 如果这一批迁移的记录数少于batch_size，说明已经完成
            if batch_migrated < batch_size:
                break

            offset += batch_size

            # 短暂休息
            time.sleep(0.1)

        cursor.close()
        conn.close()

        logger.info(f"{year}年剩余数据迁移完成，共迁移 {total_migrated:,} 条记录")
        return True

    except Exception as e:
        logger.error(f"{year}年迁移失败: {e}")
        conn.rollback()
        conn.close()
        return False

def main():
    """主函数"""
    logger.info('=' * 80)
    logger.info('开始完成2013-2014年数据迁移')
    logger.info('=' * 80)

    years = [2013, 2014]

    # 检查每个年份的剩余数据
    for year in years:
        remaining, total = check_remaining_data(year)
        if remaining > 0:
            logger.info(f"{year}年还有 {remaining:,} 条数据待迁移")

    # 开始迁移
    success = True
    for year in years:
        remaining, total = check_remaining_data(year)
        if remaining > 0:
            if not migrate_remaining_data(year, batch_size=5000):
                success = False
                logger.error(f"{year}年迁移失败")
            else:
                # 再次验证
                remaining_after, _ = check_remaining_data(year)
                if remaining_after > 0:
                    logger.warning(f"{year}年仍有 {remaining_after:,} 条数据未迁移完成")

    # 最终报告
    logger.info('=' * 80)
    logger.info('2013-2014年数据迁移完成报告')
    logger.info('=' * 80)

    for year in years:
        remaining, total = check_remaining_data(year)
        completion_rate = ((total - remaining) / total * 100) if total > 0 else 0
        logger.info(f"{year}年: 完成率 {completion_rate:.2f}% ({total-remaining:,}/{total:,})")

    if success:
        logger.info('所有任务完成！')
    else:
        logger.error('部分任务失败！')

    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)