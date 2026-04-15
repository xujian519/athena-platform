#!/usr/bin/env python3
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="patent_db",
    user="postgres",
    password="postgres",
    connect_timeout=10
)
cursor = conn.cursor()

# 查询迷你便携温室专利详情
cursor.execute("""
    SELECT patent_name, application_number, abstract, claims
    FROM patents
    WHERE application_number = 'CN201220273269.3'
    LIMIT 1
""")

r = cursor.fetchone()
if r:
    print("【对比文件D1】迷你便携温室")
    print("=" * 50)
    print(f"专利号: {r[1]}")
    print(f"发明名称: {r[0]}")
    if r[2]:
        print(f"摘要: {r[2]}")
    if r[3]:
        print(f"权利要求: {r[3]}")
else:
    print("未找到该专利")

cursor.close()
conn.close()
