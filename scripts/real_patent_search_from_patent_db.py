#!/usr/bin/env python3
"""
使用patent_db数据库进行真实专利检索
检索"幼苗培育保护罩"相关的专利
"""

import sys

sys.path.insert(0, "/Users/xujian/Athena工作平台")

import json
from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor

print("=" * 70)
print("🔍 真实专利检索 - 农作物幼苗培育保护罩")
print("=" * 70)
print()
print("数据库: patent_db.patents (75,217,242 条记录)")
print("检索时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
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

# 检索策略
search_terms = [
    ("幼苗 保护罩", "seedling protection cover"),
    ("育苗 保护", "nursery protection"),
    ("幼苗 培育 装置", "seedling cultivation device"),
    ("植物 保护罩", "plant protection cover"),
    ("农业 育苗 罩", "agricultural nursery cover"),
    ("幼苗 防护", "seedling guard"),
]

# IPC分类
ipc_codes = ["A01G 9/00", "A01G 13/00", "A01G 9/14"]

all_results = []

print("=" * 70)
print("📋 检索策略")
print("=" * 70)
print()
print("IPC分类:", ", ".join(ipc_codes))
print("关键词:", ", ".join([t[0] for t in search_terms]))
print()

# 执行检索
print("=" * 70)
print("🔍 开始检索")
print("=" * 70)
print()

for term_cn, _term_en in search_terms:
    print(f"🔎 检索: {term_cn}")
    print("-" * 70)

    # 使用模糊匹配检索
    cursor.execute("""
        SELECT
            patent_name,
            application_number,
            application_number as app_num,
            abstract,
            applicant,
            ipc_main_class,
            application_date,
            authorization_number,
            patent_type
        FROM patents
        WHERE patent_name ILIKE %s
           OR abstract ILIKE %s
        ORDER BY application_date DESC
        LIMIT 10
    """, (f'%{term_cn.replace(" ", "%")}%', f'%{term_cn.replace(" ", "%")}%'))

    results = cursor.fetchall()

    if results:
        print(f"✅ 找到 {len(results)} 条结果:")

        for r in results[:3]:  # 只显示前3条
            print(f"\n  📄 {r.get('patent_name', '未命名')}")
            print(f"     申请号: {r.get('app_num', 'N/A')}")
            if r.get('applicant'):
                print(f"     申请人: {r['applicant']}")
            if r.get('ipc_main_class'):
                print(f"     IPC分类: {r['ipc_main_class']}")
            if r.get('application_date'):
                print(f"     申请日: {r['application_date']}")
            if r.get('abstract'):
                abstract = r['abstract'][:120] + '...' if len(r['abstract']) > 120 else r['abstract']
                print(f"     摘要: {abstract}")

            all_results.append(dict(r))
    else:
        print("  未找到匹配结果")

    print()

# 使用IPC分类检索
print("=" * 70)
print("🔎 按IPC分类检索 (A01G)")
print("-" * 70)
print()

for ipc in ipc_codes:
    cursor.execute("""
        SELECT
            patent_name,
            application_number as app_num,
            abstract,
            applicant,
            ipc_main_class,
            application_date
        FROM patents
        WHERE ipc_main_class LIKE %s
        ORDER BY application_date DESC
        LIMIT 5
    """, (f'{ipc[:8]}%',))

    results = cursor.fetchall()

    if results:
        print(f"IPC {ipc}: 找到 {len(results)} 条:")
        for r in results[:2]:
            print(f"  • {r.get('patent_name', '未命名')}")
            if r.get('app_num'):
                print(f"    {r['app_num']}")
        print()

# 去重并排序相关性
print("=" * 70)
print("📊 检索结果汇总")
print("=" * 70)
print()

# 去重（按申请号）
unique_patents = {}
for r in all_results:
    app_num = r.get('app_num')
    if app_num and app_num not in unique_patents:
        unique_patents[app_num] = r

# 按相关性排序
sorted_patents = sorted(
    unique_patents.values(),
    key=lambda x: (
        '幼苗' in (x.get('patent_name', '') + x.get('abstract', '')) +
        '保护' in (x.get('patent_name', '') + x.get('abstract', '')) +
        '育苗' in (x.get('patent_name', '') + x.get('abstract', ''))
    ),
    reverse=True
)

print(f"去重后共找到 {len(sorted_patents)} 条相关专利:")
print()

# 显示最相关的10条
for i, patent in enumerate(sorted_patents[:10], 1):
    print(f"【对比文件D{i}】")
    print(f"专利号: {patent.get('app_num', 'N/A')}")
    print(f"发明名称: {patent.get('patent_name', '未命名')}")

    if patent.get('applicant'):
        print(f"申请人: {patent['applicant']}")

    if patent.get('ipc_main_class'):
        print(f"IPC分类: {patent['ipc_main_class']}")

    if patent.get('application_date'):
        print(f"申请日: {patent['application_date']}")

    if patent.get('abstract'):
        abstract = patent['abstract']
        if len(abstract) > 200:
            abstract = abstract[:200] + '...'
        print(f"摘要: {abstract}")

    # 计算相关性分数
    name = patent.get('patent_name', '')
    abstract_text = patent.get('abstract', '')
    text = (name + ' ' + abstract_text).lower()

    score = 0
    if '幼苗' in text or '育苗' in text:
        score += 0.3
    if '保护' in text or '防护' in text:
        score += 0.3
    if '罩' in text:
        score += 0.2
    if '装置' in text or '器' in text:
        score += 0.1
    if '温室' in text or '大棚' in text:
        score += 0.1

    print(f"相关性: {score:.0%}")
    print()

# 保存检索结果
report = {
    "timestamp": datetime.now().isoformat(),
    "search_topic": "农作物幼苗培育保护罩",
    "database": "patent_db.patents",
    "total_records": 75217242,
    "found_results": len(sorted_patents),
    "comparison_documents": [
        {
            "编号": f"D{i+1}",
            "专利号": p.get('app_num', 'N/A'),
            "标题": p.get('patent_name', '未命名'),
            "申请人": p.get('applicant', ''),
            "IPC分类": p.get('ipc_main_class', ''),
            "申请日": str(p.get('application_date', '')) if p.get('application_date') else '',
            "摘要": p.get('abstract', '')
        }
        for i, p in enumerate(sorted_patents[:10])
    ]
}

# 保存报告
with open('/Users/xujian/Athena工作平台/data/reports/真实专利检索结果_幼苗保护罩.json', 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print("=" * 70)
print("✅ 检索完成")
print("=" * 70)
print()
print("📄 报告已保存: /Users/xujian/Athena工作平台/data/reports/真实专利检索结果_幼苗保护罩.json")
print()
print("📊 检索统计:")
print("  • 数据库记录总数: 75,217,242")
print(f"  • 检索到相关专利: {len(sorted_patents)}")
print(f"  • 推荐对比文件: {min(4, len(sorted_patents))} 个")
print()

cursor.close()
conn.close()
