#!/usr/bin/env python3
"""
监控向量字段添加进度
Monitor Vector Field Addition Progress
"""

import logging
import sys
import time

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

def check_vector_field_progress():
    """检查向量字段添加进度"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # 1. 检查字段是否存在
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'patents'
            AND (column_name LIKE 'embedding_%' OR column_name = 'vectorized_at')
            ORDER BY column_name
        """)
        vector_fields = cursor.fetchall()

        logger.info(f"📊 向量字段状态 ({len(vector_fields)}/5 个字段已添加):")
        for field in vector_fields:
            logger.info(f"   ✅ {field[0]}: {field[1]}")

        # 2. 检查正在运行的ALTER TABLE
        cursor.execute("""
            SELECT pid, now() - query_start AS duration,
                   regexp_replace(query, E'[\\n\\r\\s]+', ' ', 'g') as query
            FROM pg_stat_activity
            WHERE datname = 'patent_db'
            AND state = 'active'
            AND query LIKE '%ALTER TABLE patents%'
            ORDER BY query_start
        """)
        alter_processes = cursor.fetchall()

        if alter_processes:
            logger.info(f"\n🔄 正在运行的ALTER TABLE进程:")
            for proc in alter_processes:
                logger.info(f"   PID: {proc[0]}, 持续时间: {proc[1]}")
                logger.info(f"   SQL: {proc[2][:100]}...")

        # 3. 检查表锁状态
        cursor.execute("""
            SELECT pg_class.relname, pg_locks.mode, pg_locks.granted
            FROM pg_class, pg_locks
            WHERE pg_class.relfilenode = pg_locks.relation
            AND pg_class.relname = 'patents'
            AND pg_locks.mode LIKE '%ACCESS%'
            ORDER BY pg_locks.granted, pg_locks.mode
        """)
        table_locks = cursor.fetchall()

        if table_locks:
            logger.info(f"\n🔒 patnets表锁状态:")
            for lock in table_locks:
                status = '✅ 已获取' if lock[2] else '⏳ 等待中'
                logger.info(f"   {lock[1]}: {status}")

        cursor.close()
        conn.close()

        # 4. 判断状态
        if len(vector_fields) >= 5:
            logger.info(f"\n🎉 向量字段添加完成！")
            return True
        elif alter_processes:
            logger.info(f"\n⏳ 向量字段正在添加中...")
            return False
        else:
            logger.info(f"\n⚠️ 没有发现正在运行的ALTER TABLE进程")
            return False

    except Exception as e:
        logger.info(f"❌ 检查失败: {e}")
        return False

def main():
    """主函数"""
    logger.info('🔍 监控向量字段添加进度')
    logger.info(str('=' * 50))

    completed = False
    attempts = 0
    max_attempts = 1000  # 最大检查次数

    while not completed and attempts < max_attempts:
        attempts += 1
        logger.info(f"\n第 {attempts} 次检查:")
        logger.info(str('-' * 30))

        completed = check_vector_field_progress()

        if not completed:
            logger.info('⏳ 等待30秒后再次检查...')
            time.sleep(30)
        else:
            logger.info("\n✅ 监控完成，向量字段已成功添加！")
            logger.info("\n下一步建议:")
            logger.info('1. 运行: python3 scripts/search/patent_vectorizer.py --limit 100')
            logger.info('2. 测试向量化功能')
            logger.info('3. 创建向量索引')
            break

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n⚠️ 监控被中断")
        sys.exit(0)