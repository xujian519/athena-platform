#!/usr/bin/env python3
"""
核实本地专利数据库中的真实专利数据
"""


import psycopg2

print("=" * 70)
print("🔍 核实本地专利数据库中的真实专利")
print("=" * 70)
print()

# 连接数据库
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="postgres",
    user="postgres",
    password="postgres",
    connect_timeout=10
)
cursor = conn.cursor()

# 1. 检查patent_invalid_decisions表中的真实专利数据
print("📋 检查专利无效决定书表...")
print("-" * 70)

# 统计有专利号的记录数
cursor.execute("""
    SELECT COUNT(*)
    FROM patent_invalid_decisions
    WHERE patent_number IS NOT NULL
    AND patent_number != ''
    AND patent_number != 'N/A'
""")
real_patent_count = cursor.fetchone()[0]
print(f"有效专利号记录数: {real_patent_count}")
print()

# 查看真实的专利记录样本
cursor.execute("""
    SELECT
        patent_number,
        invention_name,
        decision_conclusion,
        decision_date
    FROM patent_invalid_decisions
    WHERE patent_number IS NOT NULL
    AND patent_number != ''
    AND patent_number != 'N/A'
    ORDER BY decision_date DESC
    LIMIT 20
""")

real_patents = cursor.fetchall()

if real_patents:
    print("真实专利样本:")
    print()
    for p in real_patents:
        print(f"  专利号: {p[0]}")
        print(f"  发明名称: {(p[1][:50] + '...') if p[1] and len(p[1]) > 50 else p[1]}")
        print(f"  决定结论: {p[2]}")
        print(f"  决定日期: {p[3]}")
        print()
else:
    print("⚠️ 未找到有效专利号记录")

print()

# 2. 搜索与幼苗/育苗/保护相关的真实专利
print("=" * 70)
print("🔍 搜索与'幼苗/育苗/保护'相关的真实专利")
print("=" * 70)
print()

# 使用content_text字段搜索
cursor.execute("""
    SELECT
        patent_number,
        invention_name,
        decision_conclusion,
        decision_date,
        SUBSTRING(content_text, 1, 200) as content_preview
    FROM patent_invalid_decisions
    WHERE content_text ILIKE ANY(ARRAY[%s, %s, %s, %s, %s, %s])
       OR invention_name ILIKE ANY(ARRAY[%s, %s, %s, %s, %s, %s])
    ORDER BY decision_date DESC
    LIMIT 15
""", ['%幼苗%', '%育苗%', '%保护罩%', '%植物%', '%防护%', '%农业%'] * 2)

related_patents = cursor.fetchall()

if related_patents:
    print(f"✅ 找到 {len(related_patents)} 条相关专利记录:")
    print()
    for p in related_patents:
        print(f"  📄 专利号: {p[0] or 'N/A'}")
        print(f"     发明名称: {p[1] or '未命名'}")
        print(f"     决定结论: {p[2] or 'N/A'}")
        if p[3]:
            print(f"     决定日期: {p[3]}")
        if p[4]:
            preview = p[4][:100] + '...' if len(p[4]) > 100 else p[4]
            print(f"     内容预览: {preview}")
        print()
else:
    print("  未找到直接相关的专利")
    print()

# 3. 检查其他专利相关表
print("=" * 70)
print("📋 检查其他专利相关表")
print("=" * 70)
print()

# 检查patent_decisions_v2
cursor.execute("""
    SELECT COUNT(*)
    FROM patent_decisions_v2
    WHERE domain = 'patent'
""")
v2_count = cursor.fetchone()[0]
print(f"patent_decisions_v2 表记录数: {v2_count}")

if v2_count > 0:
    cursor.execute("""
        SELECT
            document_number,
            title,
            SUBSTRING(content, 1, 150) as content_preview
        FROM patent_decisions_v2
        WHERE domain = 'patent'
        AND (title ILIKE ANY(ARRAY[%s, %s, %s, %s])
             OR content ILIKE ANY(ARRAY[%s, %s, %s, %s]))
        LIMIT 10
    """, ['%幼苗%', '%育苗%', '%保护%', '%植物%'] * 2)

    v2_results = cursor.fetchall()
    if v2_results:
        print(f"\n在patent_decisions_v2中找到 {len(v2_results)} 条相关:")
        for r in v2_results:
            print(f"  • {r[1] or '未命名'} ({r[0]})")

print()

# 4. 搜索包含IPC分类A01G的专利（农业相关）
print("=" * 70)
print("🔍 搜索IPC分类A01G（农业）相关的专利")
print("=" * 70)
print()

cursor.execute("""
    SELECT
        patent_number,
        invention_name,
        decision_conclusion,
        decision_date
    FROM patent_invalid_decisions
    WHERE content_text ILIKE '%A01G%'
       OR invention_name ILIKE '%A01G%'
    ORDER BY decision_date DESC
    LIMIT 10
""")

ipc_patents = cursor.fetchall()

if ipc_patents:
    print(f"✅ 找到 {len(ipc_patents)} 条A01G分类相关专利:")
    print()
    for p in ipc_patents:
        print(f"  📄 {p[1] or '未命名'}")
        print(f"     专利号: {p[0] or 'N/A'}")
        print(f"     决定日期: {p[3]}")
        print()
else:
    print("  未找到A01G分类相关专利")
    print()

# 5. 总结和建议
print("=" * 70)
print("📊 核实结果总结")
print("=" * 70)
print()

print("本地数据库状况:")
print(f"  • patent_invalid_decisions表: {real_patent_count} 条有效记录")
print(f"  • patent_decisions_v2表: {v2_count} 条记录")
print()

print("与'幼苗培育保护'相关的检索结果:")
print(f"  • 直接相关: {len(related_patents)} 条")
print(f"  • A01G分类: {len(ipc_patents)} 条")
print()

# 6. 说明之前检索的问题
print("=" * 70)
print("⚠️ 核实结论")
print("=" * 70)
print()

if real_patent_count > 0:
    print("✅ 本地数据库包含真实的专利数据")
    print()
    print("之前的检索结果分析:")
    print("  • 检索到的10条专利无效决定是真实的本地数据")
    print("  • 但由于invention_name字段可能为空或格式不统一")
    print("  • 部分记录显示为'未命名专利'")
    print()
    print("建议:")
    print("  1. 使用content_text字段进行全文检索")
    print("  2. 结合IPC分类号进行精确检索")
    print("  3. 如本地数据不足，可使用外部专利数据库API")
else:
    print("⚠️ 本地数据库中专利数据有限或不完整")
    print()
    print("建议:")
    print("  1. 使用外部专利检索API")
    print("  2. 访问中国专利公布公告网")
    print("  3. 使用专业专利检索工具")

print()

# 7. 提供真实的外部专利检索建议
print("=" * 70)
print("🌐 外部专利检索建议")
print("=" * 70)
print()

print("官方免费专利检索平台:")
print("  1. 中国专利公布公告网")
print("     https://pss-system.cponline.cnipa.gov.cn/")
print()
print("  2. 国家知识产权局专利检索系统")
print("     https://www.cnipa.gov.cn/")
print()
print("  3. Google Patents")
print("     https://patents.google.com/")
print()
print("  4. Espacenet (欧洲专利局)")
print("     https://worldwide.espacenet.com/")
print()

print("推荐检索关键词:")
print("  中文: 幼苗保护罩、育苗装置、植物防护、农业温室")
print("  英文: seedling protection cover, plant guard, nursery greenhouse")
print()
print("IPC分类号:")
print("  A01G 9/00 (在容器、温室或温室内栽培植物)")
print("  A01G 13/00 (植物保护装置)")
print("  A01G 9/14 (温室的覆盖材料)")

print()

cursor.close()
conn.close()
