#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断专利申请号匹配问题
Diagnose Patent Number Matching Issues
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

# 缴费记录中的申请号
payment_patents = [
    "2025226088686",
    "2025226400610",
    "2025200455369",
    "2025203778244",
    "2021112526268",
    "2021112526268",
    "2015108855163",
    "2015108852625",
    "2021234129942",
    "2021234129891",
    "2022232812900",
    "2019306519805",
    "2019220526677",
    "2017219264301",
    "2021231920852",
    "2021231925396",
    "2021231920975",
    "2017100360759"
]

print("="*80)
print("🔍 专利申请号匹配诊断")
print("="*80)

found_count = 0
not_found = []

for payment_num in payment_patents:
    print(f"\n🔍 查找: {payment_num}")

    # 显示尝试的各种格式
    if len(payment_num) == 13:
        formatted1 = f"{payment_num[:4]}.{payment_num[4:11]}.{payment_num[11]}"
        formatted2 = f"{payment_num[:4]}{payment_num[5:]}"  # 去掉类型码
        print(f"   格式1: {formatted1}")
        print(f"   格式2: {formatted2}")

    # 尝试多种匹配
    patterns = [
        (payment_num, "完全匹配"),
        (f"%{payment_num[-6:]}%", "后6位模糊"),
        (f"%{payment_num[-8:]}%", "后8位模糊"),
        (f"{payment_num[:4]}%", "年份开头"),
    ]

    found = False
    for pattern, desc in patterns:
        cursor.execute("""
            SELECT patent_number, patent_name
            FROM patents
            WHERE patent_number LIKE %s
            LIMIT 3
        """, (pattern,))

        results = cursor.fetchall()
        if results:
            print(f"   ✅ {desc} - 找到 {len(results)} 个:")
            for r in results:
                print(f"      {r[0]} ({r[1][:30]}...)")
            found = True
            found_count += 1
            break

    if not found:
        print(f"   ❌ 未找到")
        not_found.append(payment_num)

print("\n" + "="*80)
print("📊 诊断结果")
print("="*80)
print(f"已找到: {found_count} 个")
print(f"未找到: {len(not_found)} 个")

if not_found:
    print("\n未匹配的申请号:")
    for num in not_found[:5]:  # 只显示前5个
        print(f"  {num}")

# 查看数据库中2025年的申请号格式样例
print("\n\n数据库中的申请号格式样例:")
cursor.execute("""
    SELECT DISTINCT patent_number
    FROM patents
    WHERE patent_number IS NOT NULL
    AND patent_number NOT LIKE '%:%'
    AND patent_number LIKE '2025%'
    LIMIT 10
""")

results = cursor.fetchall()
for r in results:
    print(f"  {r[0]}")

cursor.close()
conn.close()