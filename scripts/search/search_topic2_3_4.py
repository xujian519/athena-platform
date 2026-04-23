#!/usr/bin/env python3
"""
课题二、三、四专利检索 - 实用版
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

def search_topic2():
    """课题二：多功能反应釜专利检索"""

    print("=" * 70)
    print("🔍 课题二专利检索：一种带有复合搅拌系统的多功能反应釜")
    print("=" * 70)
    print()

    conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
    cursor = conn.cursor()

    # 第1轮：反应釜 + 搅拌
    print("📊 第1轮：反应釜 + 复合搅拌特征")
    print("-" * 70)

    query1 = """
    SELECT
        patent_name,
        application_number,
        publication_number,
        applicant,
        ipc_main_class,
        abstract,
        application_date,
        CASE
            WHEN patent_name LIKE '反应釜%' THEN 1.0
            WHEN patent_name LIKE '%反应釜%搅拌%' THEN 0.9
            WHEN patent_name LIKE '多功能反应釜%' THEN 0.95
            WHEN patent_name LIKE '%反应釜%' AND patent_name LIKE '%搅拌%' THEN 0.85
            ELSE 0.5
        END as relevance_score
    FROM patents
    WHERE patent_name LIKE '反应釜%'
       OR patent_name LIKE '%反应釜%搅拌%'
       OR (patent_name LIKE '%反应釜%' AND patent_name LIKE '%复合%')
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

    # 第2轮：超声波乳化特征
    print("📊 第2轮：超声波辅助乳化特征")
    print("-" * 70)

    query2 = """
    SELECT
        patent_name,
        application_number,
        publication_number,
        applicant,
        ipc_main_class,
        abstract,
        CASE
            WHEN patent_name LIKE '%超声波%' AND patent_name LIKE '%反应%' THEN 1.0
            WHEN patent_name LIKE '%超声波%' AND patent_name LIKE '%乳化%' THEN 0.95
            WHEN abstract LIKE '%超声波%' AND abstract LIKE '%反应%' THEN 0.8
            ELSE 0.5
        END as relevance_score
    FROM patents
    WHERE patent_name LIKE '%超声波%'
       OR (abstract LIKE '%超声波%' AND abstract LIKE '%反应%')
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
        if r['abstract'] and ('超声波' in r['abstract']):
            preview = r['abstract'][:150].replace('\n', ' ')
            print(f"      特征: {preview}...")
        print()

    # 第3轮：夹套温控
    print("📊 第3轮：夹套式温控系统")
    print("-" * 70)

    query3 = """
    SELECT
        patent_name,
        application_number,
        publication_number,
        applicant,
        ipc_main_class,
        abstract,
        CASE
            WHEN patent_name LIKE '%反应釜%' AND (patent_name LIKE '%夹套%' OR patent_name LIKE '%温控%') THEN 1.0
            WHEN patent_name LIKE '%夹套%' THEN 0.8
            ELSE 0.5
        END as relevance_score
    FROM patents
    WHERE patent_name LIKE '%反应釜%'
       AND (patent_name LIKE '%夹套%' OR patent_name LIKE '%盘管%')
    ORDER BY relevance_score DESC
    LIMIT 10;
    """

    cursor.execute(query3)
    results3 = cursor.fetchall()

    print(f"✅ 找到 {len(results3)} 条")
    print()

    for idx, r in enumerate(results3[:3], 1):
        print(f"  [{idx}] {r['patent_name']}")
        print(f"      申请号: {r['application_number']}")
        print()

    cursor.close()
    conn.close()

    print("=" * 70)
    print("📊 课题二检索汇总")
    print("=" * 70)
    print(f"反应釜+复合搅拌: {len(results1)} 条")
    print(f"超声波乳化: {len(results2)} 条")
    print(f"夹套温控: {len(results3)} 条")

    return {"round1": results1, "round2": results2, "round3": results3}


def search_topic3():
    """课题三：填料塔分离装置专利检索"""

    print("\n")
    print("=" * 70)
    print("🔍 课题三专利检索：一种高效填料塔分离装置")
    print("=" * 70)
    print()

    conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
    cursor = conn.cursor()

    # 第1轮：填料塔
    print("📊 第1轮：填料塔分离装置")
    print("-" * 70)

    query1 = """
    SELECT
        patent_name,
        application_number,
        publication_number,
        applicant,
        ipc_main_class,
        abstract,
        application_date,
        CASE
            WHEN patent_name LIKE '填料塔%' THEN 1.0
            WHEN patent_name LIKE '%填料塔%' THEN 0.9
            WHEN patent_name LIKE '%填料%分离%' THEN 0.85
            ELSE 0.5
        END as relevance_score
    FROM patents
    WHERE patent_name LIKE '填料塔%'
       OR patent_name LIKE '%填料塔%分离%'
       OR patent_name LIKE '%填料%装置%'
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
        print(f"      申请人: {r['applicant']}")
        print(f"      IPC: {r['ipc_main_class'] or '-'}")
        print()

    # 第2轮：液体分布器
    print("📊 第2轮：液体分布器特征")
    print("-" * 70)

    query2 = """
    SELECT
        patent_name,
        application_number,
        publication_number,
        applicant,
        ipc_main_class,
        abstract,
        CASE
            WHEN patent_name LIKE '%填料%' AND patent_name LIKE '%分布器%' THEN 1.0
            WHEN patent_name LIKE '%液体分布%' THEN 0.9
            WHEN abstract LIKE '%分布器%' AND abstract LIKE '%填料%' THEN 0.8
            ELSE 0.5
        END as relevance_score
    FROM patents
    WHERE patent_name LIKE '%填料%'
       AND (patent_name LIKE '%分布器%' OR patent_name LIKE '%分布%')
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
        print()

    # 第3轮：压降调节
    print("📊 第3轮：压降自动调节系统")
    print("-" * 70)

    query3 = """
    SELECT
        patent_name,
        application_number,
        publication_number,
        applicant,
        ipc_main_class,
        abstract,
        CASE
            WHEN patent_name LIKE '%填料%' AND (patent_name LIKE '%压降%' OR patent_name LIKE '%压差%') THEN 1.0
            WHEN patent_name LIKE '%分离%' AND patent_name LIKE '%压降%' THEN 0.9
            ELSE 0.5
        END as relevance_score
    FROM patents
    WHERE (patent_name LIKE '%填料%' OR patent_name LIKE '%分离%')
       AND (patent_name LIKE '%压降%' OR patent_name LIKE '%压差%')
    ORDER BY relevance_score DESC
    LIMIT 10;
    """

    cursor.execute(query3)
    results3 = cursor.fetchall()

    print(f"✅ 找到 {len(results3)} 条")
    print()

    for idx, r in enumerate(results3[:3], 1):
        print(f"  [{idx}] {r['patent_name']}")
        print(f"      申请号: {r['application_number']}")
        print()

    cursor.close()
    conn.close()

    print("=" * 70)
    print("📊 课题三检索汇总")
    print("=" * 70)
    print(f"填料塔分离装置: {len(results1)} 条")
    print(f"液体分布器: {len(results2)} 条")
    print(f"压降调节: {len(results3)} 条")

    return {"round1": results1, "round2": results2, "round3": results3}


def search_topic4():
    """课题四：双层储罐专利检索"""

    print("\n")
    print("=" * 70)
    print("🔍 课题四专利检索：一种带有智能监测系统的双层储罐")
    print("=" * 70)
    print()

    conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
    cursor = conn.cursor()

    # 第1轮：双层储罐
    print("📊 第1轮：双层储罐结构")
    print("-" * 70)

    query1 = """
    SELECT
        patent_name,
        application_number,
        publication_number,
        applicant,
        ipc_main_class,
        abstract,
        application_date,
        CASE
            WHEN patent_name LIKE '双层储罐%' THEN 1.0
            WHEN patent_name LIKE '%双层%储罐%' THEN 0.95
            WHEN patent_name LIKE '%双层%罐%' THEN 0.9
            WHEN patent_name LIKE '%储罐%' AND patent_name LIKE '%双层%' THEN 0.85
            ELSE 0.5
        END as relevance_score
    FROM patents
    WHERE patent_name LIKE '双层储罐%'
       OR patent_name LIKE '%双层%储罐%'
       OR (patent_name LIKE '%储罐%' AND patent_name LIKE '%双层%')
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
        print(f"      申请人: {r['applicant']}")
        print(f"      IPC: {r['ipc_main_class'] or '-'}")
        print()

    # 第2轮：光纤传感
    print("📊 第2轮：光纤传感监测")
    print("-" * 70)

    query2 = """
    SELECT
        patent_name,
        application_number,
        publication_number,
        applicant,
        ipc_main_class,
        abstract,
        CASE
            WHEN patent_name LIKE '%储罐%' AND patent_name LIKE '%光纤%' THEN 1.0
            WHEN patent_name LIKE '%光纤%监测%' THEN 0.9
            WHEN abstract LIKE '%光纤%' AND abstract LIKE '%储罐%' THEN 0.8
            ELSE 0.5
        END as relevance_score
    FROM patents
    WHERE (patent_name LIKE '%储罐%' OR patent_name LIKE '%容器%')
       AND (patent_name LIKE '%光纤%' OR patent_name LIKE '%传感%')
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
        print()

    # 第3轮：氮封系统
    print("📊 第3轮：氮封系统")
    print("-" * 70)

    query3 = """
    SELECT
        patent_name,
        application_number,
        publication_number,
        applicant,
        ipc_main_class,
        abstract,
        CASE
            WHEN patent_name LIKE '%储罐%' AND (patent_name LIKE '%氮封%' OR patent_name LIKE '%氮气%') THEN 1.0
            WHEN patent_name LIKE '%氮封%' THEN 0.9
            WHEN abstract LIKE '%氮封%' AND abstract LIKE '%储罐%' THEN 0.8
            ELSE 0.5
        END as relevance_score
    FROM patents
    WHERE (patent_name LIKE '%储罐%' OR patent_name LIKE '%容器%')
       AND (patent_name LIKE '%氮封%' OR patent_name LIKE '%氮气保护%')
    ORDER BY relevance_score DESC
    LIMIT 10;
    """

    cursor.execute(query3)
    results3 = cursor.fetchall()

    print(f"✅ 找到 {len(results3)} 条")
    print()

    for idx, r in enumerate(results3[:3], 1):
        print(f"  [{idx}] {r['patent_name']}")
        print(f"      申请号: {r['application_number']}")
        print()

    cursor.close()
    conn.close()

    print("=" * 70)
    print("📊 课题四检索汇总")
    print("=" * 70)
    print(f"双层储罐结构: {len(results1)} 条")
    print(f"光纤传感监测: {len(results2)} 条")
    print(f"氮封系统: {len(results3)} 条")

    return {"round1": results1, "round2": results2, "round3": results3}


if __name__ == "__main__":
    # 课题二
    topic2_results = search_topic2()

    # 课题三
    topic3_results = search_topic3()

    # 课题四
    topic4_results = search_topic4()

    print("\n")
    print("=" * 70)
    print("🎉 全部检索完成")
    print("=" * 70)
