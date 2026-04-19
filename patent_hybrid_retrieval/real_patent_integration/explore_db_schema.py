#!/usr/bin/env python3
"""
探索真实专利数据库结构
Explore Real Patent Database Schema
"""

import logging
import os
import sys

# 导入标准化数据库工具

logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from real_patent_connector import RealPatentConnector


def explore_schema():
    """探索数据库结构"""
    logger.info("\n=== 探索专利数据库结构 ===\n")

    connector = RealPatentConnector()

    try:
        with connector.get_cursor() as cursor:
            # 1. 查看所有表
            logger.info('1. 数据库中的表：')
            cursor.execute("""
                SELECT table_name, table_type
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)

            tables = cursor.fetchall()
            for table_name, table_type in tables:
                logger.info(f"   - {table_name} ({table_type})")

            # 2. 查看主表结构
            main_tables = ['patent', 'patents', 'application', 'applications']
            for table in main_tables:
                if any(t[0] == table for t in tables):
                    logger.info(f"\n2. 表 '{table}' 的结构：")
                    cursor.execute("""
                        SELECT column_name, data_type, is_nullable, column_default
                        FROM information_schema.columns
                        WHERE table_name = %s
                        ORDER BY ordinal_position;
                    """, (table,))

                    columns = cursor.fetchall()
                    for col in columns:
                        logger.info(f"   - {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")

            # 3. 查看数据量
            logger.info("\n3. 各表数据量：")
            for table_name, _ in tables[:10]:  # 只查看前10个表
                try:
                    # TODO: 检查SQL注入风险 - cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                    count = cursor.fetchone()[0]
                    logger.info(f"   - {table_name}: {count:,} 条记录")
                except Exception as e:
                    logger.info(f"   - {table_name}: 无法查询 ({str(e)[:50]})")

            # 4. 查看主要表的前几条数据
            logger.info("\n4. 主要表数据示例：")
            for table_name in ['patent', 'patents', 'application', 'applications']:
                # TODO: 检查SQL注入风险 - cursor.execute(f"""
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_name = %s
                    );
                """, (table_name,))
                exists = cursor.fetchone()[0]

                if exists:
                    try:
                        # TODO: 检查SQL注入风险 - cursor.execute(f"SELECT * FROM {table_name} LIMIT 1;")
                        cursor.execute(f"SELECT * FROM {table_name} LIMIT 1;")
                        record = cursor.fetchone()
                        if record:
                            # 获取列名
                            # TODO: 检查SQL注入风险 - cursor.execute(f"""
                            cursor.execute("""
                                SELECT column_name
                                FROM information_schema.columns
                                WHERE table_name = %s
                                ORDER BY ordinal_position;
                            """, (table_name,))
                            columns = [col[0] for col in cursor.fetchall()]

                            logger.info(f"\n   表 '{table_name}' 示例：")
                            for i, (col, val) in enumerate(zip(columns, record, strict=False)):
                                if i >= 10:  # 只显示前10个字段
                                    logger.info("     ...")
                                    break
                                val_str = str(val) if val is not None else 'NULL'
                                if len(val_str) > 50:
                                    val_str = val_str[:50] + '...'
                                logger.info(f"     {col}: {val_str}")
                    except Exception as e:
                        logger.info(f"\n   表 '{table_name}' 查询失败: {e}")

    except Exception as e:
        logger.info(f"\n❌ 探索失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        connector.close()

    logger.info("\n✅ 结构探索完成！")

if __name__ == '__main__':
    explore_schema()
