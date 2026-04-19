#!/usr/bin/env python3
"""列出所有PostgreSQL数据库"""
import psycopg2

# 连接到默认的postgres数据库以列出所有数据库
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    user="xujian",
    dbname="postgres"
)

cursor = conn.cursor()

# 列出所有数据库
cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname;")
databases = cursor.fetchall()

print("本地PostgreSQL中的所有数据库:\n")
for (db_name,) in databases:
    print(f"  - {db_name}")

cursor.close()
conn.close()
