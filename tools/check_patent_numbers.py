#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查专利申请号格式
Check Patent Number Format
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

# 检查申请号格式
cursor.execute("""
    SELECT patent_number
    FROM patents
    WHERE patent_number IS NOT NULL
    AND patent_number LIKE '2025%'
    LIMIT 10
""")

results = cursor.fetchall()
print("数据库中的2025年申请号示例：")
for row in results:
    print(f"  {row[0]}")

# 检查缴费记录中的申请号
print("\n缴费记录中的申请号示例：")
payment_numbers = [
    "2025226088686",
    "2025226400610",
    "2025200455369"
]

for num in payment_numbers:
    cursor.execute("""
        SELECT patent_number, patent_name
        FROM patents
        WHERE patent_number = %s OR patent_number LIKE %s
    """, (num, f"%{num[-6:]}"))  # 尝试匹配后6位

    result = cursor.fetchone()
    if result:
        print(f"  {num} -> 找到: {result[0]} ({result[1][:30]}...)")
    else:
        print(f"  {num} -> 未找到")

cursor.close()
conn.close()