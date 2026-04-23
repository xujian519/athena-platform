#!/usr/bin/env python3
"""
课题一专利检索 - 实用版
使用可索引的前缀匹配，快速检索相关专利
"""

import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "patent_db",
    "user": "postgres"
}

def practical_search():
    """实用的专利检索"""

    print("=" * 70)
    print("🚀 课题一专利检索 - 快速检索版")
    print("=" * 70)
    print()

    conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
    cursor = conn.cursor()

    # 第1轮：精确前缀匹配（可以使用索引）
    print("🔍 第1轮：检索'管壳式换热器'相关专利")
    print("-" * 70)

    query1 = """
    SELECT
        patent_name,
        application_number,
        publication_number,
        authorization_number,
        applicant,
        ipc_main_class,
        abstract,
        application_date,
        CASE
            WHEN patent_name LIKE '管壳式换热器%' THEN 1.0
            WHEN patent_name LIKE '管壳式换热器%' THEN 0.9
            WHEN patent_name LIKE '管壳%换热器%' THEN 0.8
            WHEN patent_name LIKE '%管壳式换热器%' THEN 0.7
            ELSE 0.5
        END as relevance_score
    FROM patents
    WHERE patent_name LIKE '管壳式换热器%'
       OR patent_name LIKE '管壳%换热器%'
       OR (patent_name LIKE '%管壳%' AND patent_name LIKE '%换热器%')
    ORDER BY relevance_score DESC, application_date DESC
    LIMIT 10;
    """

    cursor.execute(query1)
    results1 = cursor.fetchall()

    print(f"✅ 找到 {len(results1)} 条")
    print()

    for idx, r in enumerate(results1[:5], 1):
        print(f"  [{idx}] {r['patent_name']}")
        print(f"      申请号: {r['application_number']}")
        print(f"      公开号: {r['publication_number'] or '待公开'}")
        print(f"      申请人: {r['applicant']}")
        print(f"      IPC: {r['ipc_main_class'] or '-'}")
        print(f"      相关度: {r['relevance_score']:.2f}")
        if r['abstract']:
            preview = r['abstract'][:100].replace('\n', ' ')
            print(f"      摘要: {preview}...")
        print()

    if len(results1) > 0:
        # 第2轮：在管壳式换热器中找带扰流元件的
        print("🔍 第2轮：在管壳式换热器中检索扰流特征")
        print("-" * 70)

        # 先获取第1轮结果的申请号列表
        app_nums = [r['application_number'] for r in results1[:100]

        query2 = """
        SELECT
            patent_name,
            application_number,
            publication_number,
            applicant,
            ipc_main_class,
            abstract,
            CASE
                WHEN patent_name LIKE '%扰流%' OR patent_name LIKE '%弹簧%' THEN 1
                WHEN abstract LIKE '%扰流%' OR abstract LIKE '%弹簧%' THEN 0.8
                ELSE 0.5
            END as relevance_score
        FROM patents
        WHERE patent_name LIKE '管壳式换热器%'
        ORDER BY relevance_score DESC
        LIMIT 10;
        """

        cursor.execute(query2)
        results2 = cursor.fetchall()

        print(f"✅ 找到 {len(results2)} 条")
        print()

        for idx, r in enumerate(results2[:3], 1):
            print(f"  [{idx}] {r['patent_name']}")
            print(f"      申请号: {r['application_number']}")
            if r['abstract'] and ('扰流' in r['abstract'] or '弹簧' in r['abstract']):
                preview = r['abstract'][:150].replace('\n', ' ')
                print(f"      特征: {preview}...")
            print()

    # 第3轮：IPC分类检索
    print("🔍 第3轮：IPC分类检索（F28F-换热器）")
    print("-" * 70)

    query3 = """
    SELECT
        patent_name,
        application_number,
        publication_number,
        applicant,
        ipc_main_class,
        LEFT(abstract, 100) as abstract_preview
    FROM patents
    WHERE ipc_main_class LIKE 'F28F%'
       OR ipc_main_class LIKE 'F28D%'
    ORDER BY application_date DESC
    LIMIT 10;
    """

    cursor.execute(query3)
    results3 = cursor.fetchall()

    print(f"✅ 找到 {len(results3)} 条")
    print()

    for idx, r in enumerate(results3[:3], 1):
        print(f"  [{idx}] {r['patent_name']}")
        print(f"      申请号: {r['application_number']}")
        print(f"      IPC: {r['ipc_main_class']}")
        print()

    cursor.close()
    conn.close()

    print("=" * 70)
    print("📊 检索汇总")
    print("=" * 70)
    print(f"管壳式换热器相关: {len(results1)} 条")
    if 'results2' in locals():
        print(f"带扰流特征: {len(results2)} 条")
    print(f"F28F/F28D分类: {len(results3)} 条")

if __name__ == "__main__":
    practical_search()
