#!/usr/bin/env python3
"""
检查数据库表的实际列数
"""

import logging

import psycopg2

from database.db_config import get_patent_db_connection

logger = logging.getLogger(__name__)

def check_columns():
    """检查数据库表的实际列数"""
    conn = get_patent_db_connection()
    cursor = conn.cursor()

    # 获取表的所有列
    cursor.execute("""
        SELECT column_name, ordinal_position
        FROM information_schema.columns
        WHERE table_name = 'patents'
        ORDER BY ordinal_position
    """)

    columns = cursor.fetchall()
    logger.info(f"patents表实际有 {len(columns)} 列：")
    for i, (col_name, pos) in enumerate(columns, 1):
        logger.info(f"  {i}. {col_name} (位置: {pos})")

    # 检查是否有search_vector列
    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'patents' AND column_name = 'search_vector'
    """)
    search_vector = cursor.fetchone()
    if search_vector:
        logger.info(f"\n✓ 找到search_vector列: {search_vector[0]} ({search_vector[1]})")
    else:
        logger.info("\n✗ 没有找到search_vector列")

    # 获取实际的INSERT语句需要的列数（排除自动生成的）
    manual_columns = [col for col in columns if col[0] not in ['id', 'search_vector', 'created_at', 'updated_at']]
    logger.info(f"\n手动插入需要的列数: {len(manual_columns)}")

    cursor.close()
    conn.close()

if __name__ == '__main__':
    check_columns()