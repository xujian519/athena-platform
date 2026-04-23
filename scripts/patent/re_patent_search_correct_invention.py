#!/usr/bin/env python3
"""
重新专利检索 - 基于正确的发明点
现有技术：塑料覆膜+保温草垫
本发明：简易可移动的保护罩（类似农业大棚）
"""

import sys

sys.path.insert(0, "/Users/xujian/Athena工作平台")

import json
from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor

print("=" * 70)
print("🔍 重新专利检索 - 基于正确发明点")
print("=" * 70)
print()

print("📋 发明点明确:")
print("-" * 70)
print("现有技术: 塑料覆膜 + 保温草垫")
print("本发明: 简易可移动的保护罩（类似农业大棚）")
print()

# 连接patent_db数据库
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="patent_db",
    user="postgres",
    password="postgres",
    connect_timeout=10
)
cursor = conn.cursor(cursor_factory=RealDictCursor)

# 新的检索策略
search_terms = [
    # 现有技术相关
    ("塑料 覆膜", "plastic film mulching"),
    ("保温 草垫", "insulation straw mat"),
    ("地膜 覆盖", "plastic mulching"),
    ("育苗 地膜", "nursery plastic film"),

    # 与本发明相关的
    ("简易 大棚", "simple greenhouse"),
    ("移动 大棚", "mobile greenhouse"),
    ("育苗 大棚", "nursery greenhouse"),
    ("便携 大棚", "portable greenhouse"),
    ("小型 大棚", "mini greenhouse"),
    ("可移动 保护罩", "movable protection cover"),
    ("农业 大棚 简易", "simple agricultural greenhouse"),
]

all_results = []

print("=" * 70)
print("🔍 开始检索")
print("=" * 70)
print()

# 第一类：检索现有技术（塑料覆膜+保温草垫）
print("【第一类：检索现有技术 - 塑料覆膜+保温草垫】")
print("-" * 70)

for term_cn, _term_en in [
    ("塑料 覆膜", "plastic film"),
    ("保温 草垫", "insulation straw"),
    ("地膜 覆盖", "mulching film"),
    ("育苗 地膜", "nursery mulch"),
]:
    print(f"🔎 检索: {term_cn}")

    cursor.execute("""
        SELECT
            patent_name,
            application_number as app_num,
            abstract,
            applicant,
            ipc_main_class,
            application_date,
            patent_type
        FROM patents
        WHERE patent_name ILIKE %s
           OR abstract ILIKE %s
        ORDER BY application_date DESC
        LIMIT 5
    """, (f'%{term_cn.replace(" ", "%")}%', f'%{term_cn.replace(" ", "%")}%'))

    results = cursor.fetchall()

    if results:
        print(f"✅ 找到 {len(results)} 条:")
        for r in results[:2]:
            print(f"  • {r.get('patent_name', '未命名')}")
            if r.get('app_num'):
                print(f"    {r['app_num']}")
            all_results.append(dict(r))
    else:
        print("  未找到结果")
    print()

# 第二类：检索与本发明相关的（简易/移动/小型大棚）
print()
print("【第二类：检索与本发明相关 - 简易/移动/小型大棚】")
print("-" * 70)

for term_cn, _term_en in [
    ("简易 大棚", "simple greenhouse"),
    ("移动 大棚", "mobile greenhouse"),
    ("便携 温室", "portable greenhouse"),
    ("小型 育苗 大棚", "mini nursery greenhouse"),
    ("可移动 保护罩", "movable protection"),
]:
    print(f"🔎 检索: {term_cn}")

    cursor.execute("""
        SELECT
            patent_name,
            application_number as app_num,
            abstract,
            applicant,
            ipc_main_class,
            application_date,
            patent_type
        FROM patents
        WHERE patent_name ILIKE %s
           OR abstract ILIKE %s
        ORDER BY application_date DESC
        LIMIT 5
    """, (f'%{term_cn.replace(" ", "%")}%', f'%{term_cn.replace(" ", "%")}%'))

    results = cursor.fetchall()

    if results:
        print(f"✅ 找到 {len(results)} 条:")
        for r in results[:2]:
            print(f"  • {r.get('patent_name', '未命名')}")
            if r.get('app_num'):
                print(f"    {r['app_num']}")
            all_results.append(dict(r))
    else:
        print("  未找到结果")
    print()

# 按IPC分类检索 A01G（农业园艺）
print()
print("【第三类：按IPC分类 A01G 检索大棚/温室相关】")
print("-" * 70)

cursor.execute("""
    SELECT
        patent_name,
        application_number as app_num,
        abstract,
        applicant,
        ipc_main_class,
        application_date
    FROM patents
    WHERE ipc_main_class LIKE 'A01G%'
    AND (patent_name ILIKE ANY(ARRAY[%s, %s, %s, %s, %s])
         OR abstract ILIKE ANY(ARRAY[%s, %s, %s, %s, %s]))
    ORDER BY application_date DESC
    LIMIT 20
""", ['%大棚%', '%温室%', '%保护罩%', '%育苗%', '%覆膜%'] * 2)

ipc_results = cursor.fetchall()

if ipc_results:
    print(f"✅ 找到 {len(ipc_results)} 条A01G分类相关专利:")
    for r in ipc_results[:5]:
        print(f"  • {r.get('patent_name', '未命名')}")
        if r.get('app_num'):
            print(f"    {r['app_num']}")
        all_results.append(dict(r))
else:
    print("未找到结果")

print()

# 去重并分析
print("=" * 70)
print("📊 检索结果分析")
print("=" * 70)
print()

# 分类整理
existing_tech = []  # 现有技术（覆膜+草垫）
related_tech = []   # 相关技术（简易大棚）

for r in all_results:
    name = (r.get('patent_name', '') + r.get('abstract', '')).lower()
    app_num = r.get('app_num', '')

    # 分类
    if any(kw in name for kw in ['覆膜', '地膜', '草垫', 'mulch', 'film']):
        r['category'] = 'existing'
        r['relevance'] = '现有技术（覆膜+草垫）'
        existing_tech.append(r)
    elif any(kw in name for kw in ['大棚', '温室', '保护罩', 'greenhouse', '罩']):
        r['category'] = 'related'
        r['relevance'] = '相关技术（简易/移动大棚）'
        related_tech.append(r)

print("【现有技术 - 塑料覆膜+保温草垫】")
print("-" * 70)
if existing_tech:
    for i, r in enumerate(existing_tech[:3], 1):
        print(f"E{i}. {r.get('patent_name', '未命名')}")
        print(f"    专利号: {r.get('app_num', 'N/A')}")
        if r.get('abstract'):
            abstract = r['abstract'][:120] + '...' if len(r['abstract']) > 120 else r['abstract']
            print(f"    摘要: {abstract}")
        print()
else:
    print("未找到相关现有技术专利")

print()
print("【相关技术 - 简易/移动大棚】")
print("-" * 70)
if related_tech:
    for i, r in enumerate(related_tech[:5], 1):
        print(f"R{i}. {r.get('patent_name', '未命名')}")
        print(f"    专利号: {r.get('app_num', 'N/A')}")
        if r.get('abstract'):
            abstract = r['abstract'][:120] + '...' if len(r['abstract']) > 120 else r['abstract']
            print(f"    摘要: {abstract}")
        print()
else:
    print("未找到相关技术专利")

# 选择最相关的对比文件
print()
print("=" * 70)
print("📋 推荐对比文件")
print("=" * 70)
print()

# 按相关性排序
sorted_related = sorted(
    related_tech,
    key=lambda x: (
        '简易' in (x.get('patent_name', '') + x.get('abstract', '')) +
        '移动' in (x.get('patent_name', '') + x.get('abstract', '')) +
        '可移动' in (x.get('patent_name', '') + x.get('abstract', '')) +
        '便携' in (x.get('patent_name', '') + x.get('abstract', ''))
    ),
    reverse=True
)

# 选择前4个最相关的
selected_comparisons = sorted_related[:4]

for i, r in enumerate(selected_comparisons, 1):
    print(f"【对比文件{i}】")
    print(f"专利号: {r.get('app_num', 'N/A')}")
    print(f"发明名称: {r.get('patent_name', '未命名')}")
    if r.get('applicant'):
        print(f"申请人: {r['applicant']}")
    if r.get('ipc_main_class'):
        print(f"IPC分类: {r['ipc_main_class']}")
    if r.get('application_date'):
        print(f"申请日: {r['application_date']}")
    if r.get('abstract'):
        abstract = r['abstract'][:200] + '...' if len(r['abstract']) > 200 else r['abstract']
        print(f"摘要: {abstract}")
    print()

# 保存检索结果
report = {
    "timestamp": datetime.now().isoformat(),
    "search_topic": "农作物简易幼苗保护罩（可移动大棚式）",
    "database": "patent_db.patents",
    "invention_points": {
        "existing_technology": "塑料覆膜 + 保温草垫",
        "target_invention": "简易可移动的保护罩（类似农业大棚）"
    },
    "existing_technology_found": len(existing_tech),
    "related_technology_found": len(related_tech),
    "recommended_comparisons": [
        {
            "编号": f"D{i}",
            "专利号": r.get('app_num', 'N/A'),
            "标题": r.get('patent_name', '未命名'),
            "申请人": r.get('applicant', ''),
            "IPC分类": r.get('ipc_main_class', ''),
            "申请日": str(r.get('application_date', '')) if r.get('application_date') else '',
            "摘要": r.get('abstract', ''),
            "类别": r.get('category', ''),
            "相关性说明": r.get('relevance', '')
        }
        for i, r in enumerate(selected_comparisons, 1)
    ]
}

report_path = "/Users/xujian/Athena工作平台/data/reports"
from pathlib import Path

Path(report_path).mkdir(parents=True, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
report_file = f"{report_path}/专利检索结果_可移动大棚式_{timestamp}.json"

with open(report_file, 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print("=" * 70)
print("✅ 重新检索完成")
print("=" * 70)
print()
print(f"📄 报告已保存: {report_file}")
print()
print("📊 检索统计:")
print(f"  • 现有技术（覆膜+草垫）: {len(existing_tech)} 条")
print(f"  • 相关技术（简易/移动大棚）: {len(related_tech)} 条")
print(f"  • 推荐对比文件: {len(selected_comparisons)} 个")
print()
print("💡 建议的对比文件:")
print("  • 优先选择简易/移动/便携式大棚类专利")
print("  • 对比固定式塑料大棚的结构差异")
print("  • 强调可移动、快速部署的优势")

cursor.close()
conn.close()
