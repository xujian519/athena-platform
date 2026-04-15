#!/usr/bin/env python3

import psycopg2

print("快速检索: 简易/移动/便携大棚")
print("=" * 50)

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="patent_db",
    user="postgres",
    password="postgres",
    connect_timeout=10
)
cursor = conn.cursor()

# 检索简易大棚相关
cursor.execute("""
    SELECT patent_name, application_number, abstract
    FROM patents
    WHERE patent_name ILIKE '%简易%大棚%'
       OR abstract ILIKE '%简易%大棚%'
    ORDER BY application_date DESC
    LIMIT 5
""")

results = cursor.fetchall()
print(f"简易大棚: {len(results)} 条")
for r in results:
    print(f"  • {r[0]}")
    print(f"    {r[1]}")
print()

# 检索移动大棚相关
cursor.execute("""
    SELECT patent_name, application_number, abstract
    FROM patents
    WHERE patent_name ILIKE '%移动%大棚%'
       OR abstract ILIKE '%移动%大棚%'
    ORDER BY application_date DESC
    LIMIT 5
""")

results = cursor.fetchall()
print(f"移动大棚: {len(results)} 条")
for r in results:
    print(f"  • {r[0]}")
    print(f"    {r[1]}")
print()

# 检索便携/可移动保护罩
cursor.execute("""
    SELECT patent_name, application_number, abstract
    FROM patents
    WHERE patent_name ILIKE ANY(ARRAY['%便携%', '%可移动%'])
       AND patent_name ILIKE ANY(ARRAY['%保护罩%', '%大棚%', '%温室%'])
    ORDER BY application_date DESC
    LIMIT 5
""")

results = cursor.fetchall()
print(f"便携/可移动保护设施: {len(results)} 条")
for r in results:
    print(f"  • {r[0]}")
    print(f"    {r[1]}")
print()

# 检索塑料覆膜相关（现有技术）
cursor.execute("""
    SELECT patent_name, application_number, abstract
    FROM patents
    WHERE patent_name ILIKE '%塑料%覆膜%'
       OR abstract ILIKE '%塑料%覆膜%'
    ORDER BY application_date DESC
    LIMIT 3
""")

results = cursor.fetchall()
print(f"塑料覆膜（现有技术）: {len(results)} 条")
for r in results:
    print(f"  • {r[0]}")
    print(f"    {r[1]}")

cursor.close()
conn.close()
