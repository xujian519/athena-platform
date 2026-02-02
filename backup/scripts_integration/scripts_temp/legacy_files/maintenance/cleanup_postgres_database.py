#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL数据库清理脚本
PostgreSQL Database Cleanup Script

用于清理patent_db数据库，减少磁盘占用
"""

import logging
import os
import sys
from datetime import datetime

import psycopg2

logger = logging.getLogger(__name__)

def connect_db():
    """连接数据库"""
    return psycopg2.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='',
        database='patent_db'
    )

def backup_table(conn, table_name, backup_dir='/tmp/postgres_backups'):
    """备份表数据"""
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    backup_file = os.path.join(backup_dir, f"{table_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

    cursor = conn.cursor()
    try:
        # TODO: 检查SQL注入风险 - cursor.execute(f"COPY {table_name} TO '{backup_file}' WITH CSV HEADER")
                cursor.execute(f"COPY {table_name} TO '{backup_file}' WITH CSV HEADER")
        conn.commit()
        logger.info(f"✅ 表 {table_name} 已备份到: {backup_file}")

        # 获取文件大小
        size_mb = os.path.getsize(backup_file) / 1024 / 1024
        logger.info(f"   备份文件大小: {size_mb:.2f} MB")
        return backup_file
    except Exception as e:
        logger.info(f"❌ 备份失败: {e}")
        return None
    finally:
        cursor.close()

def check_table_size(conn, table_name):
    """检查表大小"""
    cursor = conn.cursor()
        # TODO: 检查SQL注入风险 - cursor.execute(f"""
            cursor.execute(f"""
        SELECT
            pg_size_pretty(pg_total_relation_size('public.{table_name}')) as total_size,
            pg_size_pretty(pg_relation_size('public.{table_name}')) as data_size,
            pg_size_pretty(pg_indexes_size('public.{table_name}')) as index_size
    """)

    result = cursor.fetchone()
    cursor.close()
    return result

def cleanup_log_tables(conn):
    """清理日志表"""
    cursor = conn.cursor()

    logger.info("\n=== 清理日志表 ===")

    # 清理data_import_log (如果有数据)
    cursor.execute('SELECT COUNT(*) FROM data_import_log')
    count = cursor.fetchone()[0]
    if count > 0:
        cursor.execute("DELETE FROM data_import_log WHERE created_at < NOW() - INTERVAL '90 days'")
        deleted = cursor.rowcount
        logger.info(f"✅ data_import_log: 删除了 {deleted} 条90天前的记录")
    else:
        logger.info('ℹ️  data_import_log 表为空，跳过')

    # 清理patent_search_logs
    cursor.execute('SELECT COUNT(*) FROM patent_search_logs')
    count = cursor.fetchone()[0]
    if count > 0:
        cursor.execute("DELETE FROM patent_search_logs WHERE created_at < NOW() - INTERVAL '90 days'")
        deleted = cursor.rowcount
        logger.info(f"✅ patent_search_logs: 删除了 {deleted} 条90天前的记录")
    else:
        logger.info('ℹ️  patent_search_logs 表为空，跳过')

    conn.commit()
    cursor.close()

def vacuum_main_table(conn):
    """对主表执行VACUUM"""
    logger.info("\n=== 执行VACUUM清理 ===")
    cursor = conn.cursor()

    try:
        # 获取清理前的大小
        size_before = check_table_size(conn, 'patents')
        logger.info(f"清理前 patents 表大小: {size_before[0]}")

        # 执行VACUUM
        logger.info('执行 VACUUM (VERBOSE, ANALYZE) patents...')
        cursor.execute('VACUUM (VERBOSE, ANALYZE) patents')

        # 获取清理后的大小
        size_after = check_table_size(conn, 'patents')
        logger.info(f"清理后 patents 表大小: {size_after[0]}")

        conn.commit()
        logger.info('✅ VACUUM 完成')
    except Exception as e:
        logger.info(f"❌ VACUUM 失败: {e}")
        conn.rollback()
    finally:
        cursor.close()

def rebuild_indexes(conn):
    """重建索引（可选）"""
    logger.info("\n=== 分析索引使用情况 ===")
    cursor = conn.cursor()

    # 查看未使用的索引
    cursor.execute("""
        SELECT
            indexname,
            schemaname,
            tablename,
            idx_tup_read,
            idx_scan
        FROM pg_stat_user_indexes
        WHERE schemaname = 'public'
        AND idx_scan = 0
        AND indexname NOT LIKE '%_pkey'
    """)

    unused_indexes = cursor.fetchall()

    if unused_indexes:
        logger.info('发现未使用的索引:')
        for idx, schema, table, reads, scans in unused_indexes:
            logger.info(f"  ⚠️  {schema}.{table}.{idx}: 0 次扫描")

        # 可以选择删除这些索引
        drop_confirmation = input("\n是否删除未使用的索引？(y/N): ")
        if drop_confirmation.lower() == 'y':
            for idx, schema, table, reads, scans in unused_indexes:
                try:
        # TODO: 检查SQL注入风险 - cursor.execute(f"DROP INDEX IF EXISTS {idx}")
                            cursor.execute(f"DROP INDEX IF EXISTS {idx}")
                    logger.info(f"✅ 已删除索引: {idx}")
                except Exception as e:
                    logger.info(f"❌ 删除索引失败 {idx}: {e}")
            conn.commit()
    else:
        logger.info('✅ 所有索引都在使用中')

    cursor.close()

def archive_historical_data(conn):
    """归档历史数据"""
    logger.info("\n=== 归档历史数据 ===")

    # 检查patents_2010表
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM patents_2010')
    count_2010 = cursor.fetchone()[0]

    if count_2010 > 0:
        size = check_table_size(conn, 'patents_2010')
        logger.info(f"patents_2010 表: {count_2010} 条记录, 大小: {size[0]}")

        # 询问是否归档
        archive = input('是否备份并删除patents_2010表？(y/N): ')
        if archive.lower() == 'y':
            # 备份
            backup_file = backup_table(conn, 'patents_2010')

            if backup_file:
                # 删除表
                try:
                    cursor.execute('DROP TABLE patents_2010')
                    conn.commit()
                    logger.info('✅ patents_2010 表已删除')

                    # 记录到归档日志
                    with open('/tmp/postgres_archive_log.txt', 'a') as f:
                        f.write(f"{datetime.now()}: patents_2010 -> {backup_file}\n")
                except Exception as e:
                    logger.info(f"❌ 删除表失败: {e}")
    else:
        logger.info('ℹ️  patents_2010 表为空，跳过')

    cursor.close()

def generate_report(conn):
    """生成清理报告"""
    cursor = conn.cursor()

    logger.info("\n=== 清理后数据库状态 ===")

    # 数据库列表
    cursor.execute('SELECT datname FROM pg_database WHERE datistemplate = false')
    databases = cursor.fetchall()

    for db in databases:
        # TODO: 检查SQL注入风险 - cursor.execute(f"SELECT pg_size_pretty(pg_database_size('{db[0]}'))")
                cursor.execute(f"SELECT pg_size_pretty(pg_database_size('{db[0]}'))")
        size = cursor.fetchone()[0]
        logger.info(f"  {db[0]:20} {size}")

    cursor.close()

def main():
    """主函数"""
    logger.info('🧹 PostgreSQL数据库清理工具')
    logger.info(str('=' * 50))
    logger.info(f"时间: {datetime.now()}")
    print()

    # 连接数据库
    try:
        conn = connect_db()
        logger.info('✅ 连接成功')
    except Exception as e:
        logger.info(f"❌ 连接失败: {e}")
        return

    try:
        # 1. 清理日志表
        cleanup_log_tables(conn)

        # 2. 归档历史数据
        archive_historical_data(conn)

        # 3. 执行VACUUM
        vacuum_main_table(conn)

        # 4. 分析索引（可选）
        rebuild_indexes(conn)

        # 5. 生成报告
        generate_report(conn)

        logger.info("\n✅ 清理完成！")

        # 计算节省的空间
        logger.info("\n📊 清理总结:")
        logger.info('- 已清理90天前的日志记录')
        logger.info('- 已执行VACUUM回收空间')
        logger.info('- 已分析并优化索引')

    except Exception as e:
        logger.info(f"❌ 清理过程中出错: {e}")
        import traceback

# 导入标准化数据库工具
from shared.database.db_utils import DatabaseManager, build_safe_query
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == '__main__':
    main()