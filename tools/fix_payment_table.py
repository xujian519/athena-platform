#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复缴费表结构
Fix Payment Table Structure
"""

import psycopg2
import os

# PostgreSQL配置
db_config = {
    "host": "localhost",
    "port": 5432,
    "database": "patent_archive",
    "user": "xujian",
    "password": ""
}

# 检查PostgreSQL路径
postgres_path = "/opt/homebrew/opt/postgresql@17/bin"
if postgres_path not in os.environ.get("PATH", ""):
    os.environ["PATH"] = postgres_path + ":" + os.environ.get("PATH", "")

conn = psycopg2.connect(**db_config)
cursor = conn.cursor()

# 检查表是否存在
cursor.execute("""
    SELECT table_name FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name = 'patent_payments'
""")

table_exists = cursor.fetchone()

if table_exists:
    print("✅ patent_payments 表已存在")

    # 检查patent_id列是否存在
    cursor.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'patent_payments' AND column_name = 'patent_id'
    """)

    column_exists = cursor.fetchone()

    if not column_exists:
        # 添加patent_id列
        cursor.execute("""
            ALTER TABLE patent_payments
            ADD COLUMN patent_id INTEGER
        """)
        print("✅ 已添加 patent_id 列")
    else:
        print("✅ patent_id 列已存在")
else:
    print("❌ patent_payments 表不存在")

# 检查索引是否存在
cursor.execute("""
    SELECT indexname FROM pg_indexes
    WHERE tablename = 'patent_payments' AND indexname = 'idx_payments_patent_id'
""")

index_exists = cursor.fetchone()

if not index_exists:
    # 创建索引
    cursor.execute("""
        CREATE INDEX idx_payments_patent_id ON patent_payments(patent_id)
    """)
    print("✅ 已创建 patent_id 索引")
else:
    print("✅ patent_id 索引已存在")

conn.commit()
cursor.close()
conn.close()

print("\n✅ 表结构修复完成")