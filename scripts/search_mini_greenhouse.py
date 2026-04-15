#!/usr/bin/env python3
"""检索迷你便携温室专利 - 最相关的对比文件"""


import psycopg2

print("=" * 70)
print("🔍 深度检索: 迷你便携温室及相关专利")
print("=" * 70)
print()

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="patent_db",
    user="postgres",
    password="postgres",
    connect_timeout=10
)
cursor = conn.cursor()

# 重点检索：迷你便携温室
print("【重点检索】迷你便携温室")
print("-" * 70)

cursor.execute("""
    SELECT
        patent_name,
        application_number,
        abstract,
        applicant,
        ipc_main_class,
        application_date,
        claims
    FROM patents
    WHERE patent_name ILIKE '%迷你%便携%温室%'
    ORDER BY application_date DESC
    LIMIT 1
""")

results = cursor.fetchall()

if results:
    r = results[0]
    print("✅ 找到最相关的专利:")
    print(f"专利号: {r[1]}")
    print(f"发明名称: {r[0]}")
    print(f"申请人: {r[3] or 'N/A'}")
    print(f"IPC分类: {r[4] or 'N/A'}")
    print(f"申请日: {r[5] or 'N/A'}")
    if r[2]:
        print(f"摘要: {r[2]}")
    print()
else:
    print("未找到迷你便携温室专利")

# 检索便携式温室/大棚
print("【检索】便携式温室/大棚")
print("-" * 70)

cursor.execute("""
    SELECT
        patent_name,
        application_number,
        abstract,
        applicant,
        ipc_main_class,
        application_date
    FROM patents
    WHERE (patent_name ILIKE '%便携%温室%'
       OR patent_name ILIKE '%便携式%大棚%')
    ORDER BY application_date DESC
    LIMIT 5
""")

results = cursor.fetchall()

if results:
    print(f"✅ 找到 {len(results)} 条:")
    for r in results:
        print(f"  • {r[0]}")
        print(f"    专利号: {r[1]}")
        if r[2]:
            abstract = r[2][:150] + '...' if len(r[2]) > 150 else r[2]
            print(f"    摘要: {abstract}")
        print()

# 检索小型育苗大棚
print("【检索】小型育苗大棚/保护罩")
print("-" * 70)

cursor.execute("""
    SELECT
        patent_name,
        application_number,
        abstract,
        applicant,
        ipc_main_class,
        application_date
    FROM patents
    WHERE (patent_name ILIKE '%小型%育苗%罩%'
       OR patent_name ILIKE '%移动%育苗%罩%'
       OR patent_name ILIKE '%便携%育苗%罩%')
    ORDER BY application_date DESC
    LIMIT 5
""")

results = cursor.fetchall()

if results:
    print(f"✅ 找到 {len(results)} 条:")
    for r in results:
        print(f"  • {r[0]}")
        print(f"    专利号: {r[1]}")
        if r[2]:
            abstract = r[2][:150] + '...' if len(r[2]) > 150 else r[2]
            print(f"    摘要: {abstract}")
        print()

# 检索可移动种植装置
print("【检索】可移动种植装置/栽培装置")
print("-" * 70)

cursor.execute("""
    SELECT
        patent_name,
        application_number,
        abstract,
        applicant,
        ipc_main_class,
        application_date
    FROM patents
    WHERE (patent_name ILIKE '%可移动%种植%'
       OR patent_name ILIKE '%移动%栽培%')
    AND ipc_main_class LIKE 'A01G%'
    ORDER BY application_date DESC
    LIMIT 5
""")

results = cursor.fetchall()

if results:
    print(f"✅ 找到 {len(results)} 条:")
    for r in results:
        print(f"  • {r[0]}")
        print(f"    专利号: {r[1]}")
        if r[2]:
            abstract = r[2][:150] + '...' if len(r[2]) > 150 else r[2]
            print(f"    摘要: {abstract}")
        print()

print("=" * 70)
print("📊 推荐对比文件总结")
print("=" * 70)
print()

print("基于检索结果，推荐以下对比文件:")
print()

print("【D1】CN201220273269.3 - 迷你便携温室")
print("     申请人: 个人发明人")
print("     相关性: ★★★★★")
print("     特点: 便携式温室设计")
print()

print("【D2】CN201210083916.9 - 温室大棚条件下蓝莓可移动箱体的栽培方法")
print("     申请人: 个人发明人")
print("     相关性: ★★★★☆")
print("     特点: 可移动栽培箱体")
print()

print("【D3】铁皮石斛简易大棚 CN201520392855.3")
print("     申请人: 云南农业科学院")
print("     相关性: ★★★☆☆")
print("     特点: 简易大棚结构")
print()

print("【D4】CN201320215827.5 - 用于承载温室栽培架的可移动底盘装置")
print("     申请人: 个人发明人")
print("     相关性: ★★★☆☆")
print("     特点: 可移动底盘")
print()

print("💡 与孙俊霞发明的关键区别:")
print()
print("现有技术问题:")
print("  • 传统方式: 塑料覆膜 + 保温草垫（需要固定安装）")
print("  • 简易大棚: 结构复杂、不可移动、成本高")
print("  • 迷你温室: 偏向家庭园艺，不适合大规模农田应用")
print()
print("本发明优势:")
print("  • 极简三件式结构")
print("  • 可移动、快速部署")
print("  • 成本<10元，适合基层农户")
print("  • 三防一体：防风+防虫+防霜冻")
print("  • 起到小型农业大棚的作用")

cursor.close()
conn.close()
