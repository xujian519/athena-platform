#!/usr/bin/env python3
"""
课题一专利检索 - 在本地PostgreSQL数据库中检索
"""


import psycopg2
from psycopg2.extras import RealDictCursor

# 数据库配置
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "patent_db",
    "user": "postgres",
    "options": "-c client_encoding=UTF8"
}

def search_patents():
    """执行专利检索"""

    print("=" * 70)
    print("🔍 课题一专利检索：一种带有强化传热元件的管壳式换热器")
    print("=" * 70)
    print()

    conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
    cursor = conn.cursor()

    # 第1轮：核心特征检索
    print("📊 第1轮检索：核心特征（管壳式换热器 + 扰流元件）")
    print("-" * 70)

    query1 = """
    SELECT
        patent_name,
        application_number,
        publication_number,
        authorization_number,
        applicant,
        application_date,
        ipc_main_class,
        abstract,
        LEFT(abstract, 200) as abstract_preview,
        (
            CASE WHEN LOWER(patent_name) LIKE '%管壳式%' THEN 1 ELSE 0 END * 0.4 +
            CASE WHEN LOWER(patent_name) LIKE '%换热器%' THEN 1 ELSE 0 END * 0.3 +
            CASE WHEN LOWER(abstract) LIKE '%扰流%' THEN 1 ELSE 0 END * 0.2 +
            CASE WHEN LOWER(abstract) LIKE '%螺旋弹簧%' THEN 1 ELSE 0 END * 0.1
        ) as relevance_score
    FROM patents
    WHERE (
        LOWER(patent_name) LIKE '%管壳式%'
        OR LOWER(patent_name) LIKE '%换热器%'
    )
    AND (
        LOWER(patent_name) LIKE '%扰流%'
        OR LOWER(patent_name) LIKE '%螺旋弹簧%'
        OR LOWER(patent_name) LIKE '%强化传热%'
        OR LOWER(abstract) LIKE '%扰流%'
        OR LOWER(abstract) LIKE '%弹簧%'
    )
    ORDER BY relevance_score DESC, application_date DESC
    LIMIT 10;
    """

    cursor.execute(query1)
    results1 = cursor.fetchall()

    print(f"✅ 找到 {len(results1)} 条相关专利")
    print()

    for idx, r in enumerate(results1[:5], 1):
        print(f"  [{idx}] {r['patent_name']}")
        print(f"      申请号: {r['application_number']}")
        print(f"      公开号: {r['publication_number'] or '无'}")
        print(f"      申请人: {r['applicant']}")
        print(f"      IPC分类: {r['ipc_main_class'] or '无'}")
        print(f"      相关度: {r['relevance_score']:.2f}")
        if r['abstract_preview']:
            print(f"      摘要: {r['abstract_preview']}...")
        print()

    # 第2轮：结构特征检索
    print("📊 第2轮检索：结构特征（管板 + 多管程）")
    print("-" * 70)

    query2 = """
    SELECT
        patent_name,
        application_number,
        publication_number,
        authorization_number,
        applicant,
        application_date,
        ipc_main_class,
        LEFT(abstract, 200) as abstract_preview,
        (
            CASE WHEN LOWER(patent_name) LIKE '%管板%' THEN 1 ELSE 0 END * 0.4 +
            CASE WHEN LOWER(patent_name) LIKE '%多管程%' THEN 1 ELSE 0 END * 0.3 +
            CASE WHEN LOWER(patent_name) LIKE '%可拆卸%' THEN 1 ELSE 0 END * 0.3
        ) as relevance_score
    FROM patents
    WHERE (
        LOWER(patent_name) LIKE '%换热器%'
        OR LOWER(abstract) LIKE '%换热器%'
    )
    AND (
        LOWER(patent_name) LIKE '%管板%'
        OR LOWER(patent_name) LIKE '%多管程%'
        OR LOWER(abstract) LIKE '%管板%'
    )
    ORDER BY relevance_score DESC, application_date DESC
    LIMIT 10;
    """

    cursor.execute(query2)
    results2 = cursor.fetchall()

    print(f"✅ 找到 {len(results2)} 条相关专利")
    print()

    for idx, r in enumerate(results2[:3], 1):
        print(f"  [{idx}] {r['patent_name']}")
        print(f"      申请号: {r['application_number']}")
        print(f"      申请人: {r['applicant']}")
        print(f"      相关度: {r['relevance_score']:.2f}")
        print()

    # 第3轮：智能控制检索
    print("📊 第3轮检索：智能控制特征")
    print("-" * 70)

    query3 = """
    SELECT
        patent_name,
        application_number,
        publication_number,
        applicant,
        LEFT(abstract, 200) as abstract_preview,
        (
            CASE WHEN LOWER(patent_name) LIKE '%温度监控%' THEN 1 ELSE 0 END * 0.5 +
            CASE WHEN LOWER(patent_name) LIKE '%智能控制%' THEN 1 ELSE 0 END * 0.5
        ) as relevance_score
    FROM patents
    WHERE (
        LOWER(patent_name) LIKE '%换热器%'
        OR LOWER(abstract) LIKE '%换热器%'
    )
    AND (
        LOWER(patent_name) LIKE '%温度监控%'
        OR LOWER(patent_name) LIKE '%智能控制%'
        OR LOWER(abstract) LIKE '%温度监控%'
        OR LOWER(abstract) LIKE '%智能控制%'
    )
    ORDER BY relevance_score DESC, application_date DESC
    LIMIT 10;
    """

    cursor.execute(query3)
    results3 = cursor.fetchall()

    print(f"✅ 找到 {len(results3)} 条相关专利")
    print()

    for idx, r in enumerate(results3[:3], 1):
        print(f"  [{idx}] {r['patent_name']}")
        print(f"      申请号: {r['application_number']}")
        print(f"      摘要: {r['abstract_preview']}...")
        print()

    # 保存所有结果
    all_results = {
        "round1": [dict(r) for r in results1],
        "round2": [dict(r) for r in results2],
        "round3": [dict(r) for r in results3]
    }

    # 统计信息
    print("=" * 70)
    print("📊 检索统计")
    print("=" * 70)
    print(f"第1轮（核心特征）: {len(results1)} 条")
    print(f"第2轮（结构特征）: {len(results2)} 条")
    print(f"第3轮（智能控制）: {len(results3)} 条")
    print(f"总计: {len(results1) + len(results2) + len(results3)} 条")
    print()

    cursor.close()
    conn.close()

    return all_results

if __name__ == "__main__":
    results = search_patents()
