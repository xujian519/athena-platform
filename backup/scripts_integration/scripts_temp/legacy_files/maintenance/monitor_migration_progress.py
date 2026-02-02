#!/usr/bin/env python3
"""
监控专利数据迁移进度
"""

import logging
import sys
from datetime import datetime

import psycopg2

logger = logging.getLogger(__name__)

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres',
    'database': 'patent_db'
}

def create_connection():
    """创建数据库连接"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.info(f"❌ 数据库连接失败: {e}")
        return None

def get_migration_status():
    """获取迁移状态"""
    conn = create_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor()

        # 查询已迁移的年份和数据量
        cursor.execute("""
            SELECT
                source_year,
                COUNT(*) as count
            FROM patents
            WHERE source_year >= 2000
            GROUP BY source_year
            ORDER BY source_year
        """)

        migrated = cursor.fetchall()

        # 查询简化表中的数据
        cursor.execute("""
            SELECT
                source_year,
                COUNT(*) as count
            FROM patents_simple
            WHERE source_year >= 2000
            GROUP BY source_year
            ORDER BY source_year
        """)

        simple_data = cursor.fetchall()

        # 转换为字典便于对比
        migrated_dict = {year: count for year, count in migrated}
        simple_dict = {year: count for year, count in simple_data}

        # 计算总数
        total_migrated = sum(migrated_dict.values())
        total_simple = sum(simple_dict.values())

        return {
            'migrated': migrated_dict,
            'simple': simple_dict,
            'total_migrated': total_migrated,
            'total_simple': total_simple
        }

    except Exception as e:
        logger.info(f"❌ 查询失败: {e}")
        return None
    finally:
        conn.close()

def display_status(status):
    """显示迁移状态"""
    if not status:
        return

    logger.info(str('=' * 80))
    logger.info('📊 专利数据迁移进度报告')
    logger.info(str('=' * 80))
    logger.info(f"报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(str('-' * 80))

    # 表头
    logger.info(f"{'年份':<8} {'简化表':<12} {'已迁移':<12} {'迁移率':<10} {'状态':<10}")
    logger.info(str('-' * 80))

    # 各年份状态
    all_years = sorted(set(status['migrated'].keys()) | set(status['simple'].keys()))

    for year in all_years:
        simple_count = status['simple'].get(year, 0)
        migrated_count = status['migrated'].get(year, 0)

        if simple_count > 0:
            percentage = (migrated_count / simple_count) * 100
            status_str = '✅ 完成' if percentage == 100 else '🔄 进行中'
        else:
            percentage = 0
            status_str = '⚪ 待处理'

        logger.info(f"{year:<8} {simple_count:<12,} {migrated_count:<12,} {percentage:<10.1f}% {status_str:<10}")

    logger.info(str('-' * 80))
    logger.info(f"总计:   {status['total_simple']:<12,} {status['total_migrated']:<12,}")
    logger.info(str('=' * 80))

    # 待迁移年份
    pending_years = []
    for year, count in status['simple'].items():
        if year not in status['migrated'] or status['migrated'].get(year, 0) < count:
            pending_years.append((year, count))

    if pending_years:
        logger.info("\n📋 待迁移年份:")
        for year, count in sorted(pending_years):
            logger.info(f"  - {year}年: {count:,} 条记录")

    # 正在进行的迁移
    logger.info("\n🔄 当前正在进行的迁移任务:")
    logger.info('  - 2015年数据迁移SQL脚本 (bash_id: 6108c6)')

def main():
    """主函数"""
    status = get_migration_status()
    display_status(status)

if __name__ == '__main__':
    main()