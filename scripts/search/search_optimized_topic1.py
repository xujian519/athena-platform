#!/usr/bin/env python3
"""
课题一专利检索 - 优化版
使用PostgreSQL全文搜索和索引，大幅提升查询速度
"""

import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "patent_db",
    "user": "postgres"
}

def optimized_search():
    """优化后的专利检索"""

    print("=" * 70)
    print("🚀 课题一专利检索（优化版）")
    print("=" * 70)
    print()

    conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
    cursor = conn.cursor()

    # 使用全文搜索 - 第1轮
    print("🔍 第1轮：使用全文搜索检索核心特征")
    print("-" * 70)

    # 使用plainto_tsquery进行全文搜索（更灵活）
    query1 = """
    SELECT
        patent_name,
        application_number,
        publication_number,
        authorization_number,
        applicant,
        ipc_main_class,
        application_date,
        ts_rank(search_vector, to_tsquery('chinese', '管壳式 & 换热器 & (扰流 | 螺旋 | 强化)')) as rank
    FROM patents
    WHERE search_vector @@ to_tsquery('chinese', '管壳式 & 换热器 & (扰流 | 螺旋 | 强化)')
    ORDER BY rank DESC, application_date DESC
    LIMIT 10;
    """

    print("⏳ 执行中...")
    cursor.execute(query1)
    results1 = cursor.fetchall()

    print(f"✅ 找到 {len(results1)} 条 (耗时优化)")
    print()

    for idx, r in enumerate(results1[:5], 1):
        print(f"  [{idx}] {r['patent_name']}")
        print(f"      申请号: {r['application_number']}")
        print(f"      申请人: {r['applicant']}")
        print(f"      相关度: {r['rank']:.2f}")
        print()

    # 第2轮：组合特征检索（使用更精确的匹配）
    print("🔍 第2轮：检索管板结构特征")
    print("-" * 70)

    query2 = """
    SELECT
        patent_name,
        application_number,
        publication_number,
        applicant,
        ipc_main_class,
        ts_rank(search_vector, to_tsquery('chinese', '换热器 & (管板 | 可拆卸 | 多管程)')) as rank
    FROM patents
    WHERE search_vector @@ to_tsquery('chinese', '换热器 & (管板 | 可拆卸 | 多管程)')
    ORDER BY rank DESC
    LIMIT 10;
    """

    cursor.execute(query2)
    results2 = cursor.fetchall()

    print(f"✅ 找到 {len(results2)} 条")
    print()

    for idx, r in enumerate(results2[:3], 1):
        print(f"  [{idx}] {r['patent_name']}")
        print(f"      申请号: {r['application_number']}")
        print(f"      申请人: {r['applicant']}")
        print()

    # 第3轮：智能控制特征
    print("🔍 第3轮：检索智能温控特征")
    print("-" * 70)

    query3 = """
    SELECT
        patent_name,
        application_number,
        publication_number,
        applicant,
        ipc_main_class,
        ts_rank(search_vector, to_tsquery('chinese', '换热器 & (温度监控 | 智能控制 | 自动调节)')) as rank
    FROM patents
    WHERE search_vector @@ to_tsquery('chinese', '换热器 & (温度监控 | 智能控制)')
    ORDER BY rank DESC
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
    print("📊 检索完成")
    print("=" * 70)
    print(f"第1轮: {len(results1)} 条")
    print(f"第2轮: {len(results2)} 条")
    print(f"第3轮: {len(results3)} 条")

if __name__ == "__main__":
    optimized_search()
