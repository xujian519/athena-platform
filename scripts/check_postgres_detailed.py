#!/usr/bin/env python3
"""检查PostgreSQL数据库详细数据"""
import psycopg2
import os

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    user="xujian",
    dbname="athena"
)

cursor = conn.cursor()

# 获取所有表
cursor.execute("""
    SELECT schemaname, tablename
    FROM pg_tables
    WHERE schemaname = 'public'
    ORDER BY tablename
""")

tables = cursor.fetchall()

print(f"athena数据库共有 {len(tables)} 个表:\n")

# 检查每个表的数据量
for schema, table in tables:
    try:
        cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
        count = cursor.fetchone()[0]
        print(f"  {table}: {count:,} 行")
    except Exception as e:
        print(f"  {table}: 错误 - {e}")

cursor.close()
conn.close()
