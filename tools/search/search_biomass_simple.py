#!/usr/bin/env python3
"""
生物质气化发生炉专利检索脚本 - 简化版
使用更高效的检索策略
"""

import json
from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor


def main():
    """主函数"""
    print("=" * 80)
    print("生物质气化发生炉专利检索系统")
    print("=" * 80)

    # 直接连接数据库
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='patent_db',
        user='postgres',
        password='postgres',
        cursor_factory=RealDictCursor
    )
    cursor = conn.cursor()

    # 构建检索式
    # 检索目标：生物质气化发生炉，上下双火层，上火层去除煤焦油

    print("\n=== 检索式构建 ===")
    print("目标技术：生物质气化发生炉技术")
    print("核心特征：")
    print("  1. 上下双火层结构")
    print("  2. 上火层可以去除煤焦油")
    print("  3. 生物质气化工艺")

    # 关键词组合

    print("\n=== 检索策略 ===")
    print("策略1：精确匹配 - 生物质气化炉")
    print("策略2：结构特征 - 双层/双火层")
    print("策略3：功能特征 - 焦油去除/裂解")

    # 执行检索
    results = []

    # 检索1：生物质气化相关
    print("\n【检索1】生物质气化炉...")
    sql1 = """
    SELECT
        patent_name,
        abstract,
        ipc_main_class,
        applicant,
        inventor,
        application_date,
        publication_number,
        authorization_number
    FROM patents
    WHERE patent_name LIKE ANY(ARRAY['%生物质%', '%气化炉%', '%发生炉%'])
    ORDER BY application_date DESC
    LIMIT 30
    """
    cursor.execute(sql1)
    batch1 = cursor.fetchall()
    print(f"  找到 {len(batch1)} 条结果")
    results.extend([dict(r) for r in batch1])

    # 检索2：双火层结构
    print("\n【检索2】双火层/双层结构...")
    sql2 = """
    SELECT
        patent_name,
        abstract,
        ipc_main_class,
        applicant,
        inventor,
        application_date,
        publication_number,
        authorization_number
    FROM patents
    WHERE patent_name LIKE ANY(ARRAY['%双火层%', '%双层气化%', '%上火层%', '%下火层%', '%双段气化%'])
       OR abstract LIKE ANY(ARRAY['%双火层%', '%双层气化%', '%上火层%', '%下火层%', '%双段气化%'])
    ORDER BY application_date DESC
    LIMIT 30
    """
    cursor.execute(sql2)
    batch2 = cursor.fetchall()
    print(f"  找到 {len(batch2)} 条结果")
    results.extend([dict(r) for r in batch2])

    # 检索3：焦油处理技术
    print("\n【检索3】焦油去除/裂解技术...")
    sql3 = """
    SELECT
        patent_name,
        abstract,
        ipc_main_class,
        applicant,
        inventor,
        application_date,
        publication_number,
        authorization_number
    FROM patents
    WHERE (patent_name LIKE ANY(ARRAY['%气化%', '%发生炉%'])
       OR abstract LIKE ANY(ARRAY['%气化%', '%发生炉%']))
       AND (patent_name LIKE ANY(ARRAY['%焦油%', '%除焦%', '%裂解%', '%重整%'])
       OR abstract LIKE ANY(ARRAY['%焦油%', '%除焦%', '%裂解%', '%重整%']))
    ORDER BY application_date DESC
    LIMIT 30
    """
    cursor.execute(sql3)
    batch3 = cursor.fetchall()
    print(f"  找到 {len(batch3)} 条结果")
    results.extend([dict(r) for r in batch3])

    # 去重
    seen = set()
    unique_results = []
    for r in results:
        pub_num = r.get('publication_number') or r.get('patent_name')
        if pub_num and pub_num not in seen:
            seen.add(pub_num)
            unique_results.append(r)

    print("\n=== 检索完成 ===")
    print(f"总计找到 {len(unique_results)} 条不重复的专利")

    if not unique_results:
        print("\n未找到相关专利，请尝试调整检索关键词")
        cursor.close()
        conn.close()
        return

    # 分析结果
    print("\n=== 专利分析 ===")

    # 按技术特征分类
    dual_layer = []  # 双火层技术
    tar_removal = []  # 焦油去除
    biomass = []  # 生物质气化

    for patent in unique_results:
        title = patent.get('patent_name', '')
        abstract = patent.get('abstract', '')
        text = (title + ' ' + (abstract or '')).lower()

        if '双火层' in text or '双层' in text or '上火层' in text:
            dual_layer.append(patent)
        if '焦油' in text or '除焦' in text or '裂解' in text:
            tar_removal.append(patent)
        if '生物质' in text or '气化' in text:
            biomass.append(patent)

    print(f"  - 双火层技术: {len(dual_layer)} 条")
    print(f"  - 焦油去除: {len(tar_removal)} 条")
    print(f"  - 生物质气化: {len(biomass)} 条")

    # 输出重点专利
    print("\n=== 重点专利展示 ===")

    # 1. 双火层技术专利
    if dual_layer:
        print("\n【双火层/双层结构专利】")
        for i, p in enumerate(dual_layer[:5], 1):
            print(f"\n{i}. {p.get('patent_name')}")
            print(f"   公开号: {p.get('publication_number')}")
            print(f"   申请人: {p.get('applicant')}")
            print(f"   IPC分类: {p.get('ipc_main_class')}")
            print(f"   申请日期: {p.get('application_date')}")
            if p.get('abstract'):
                abstract = p['abstract'][:200] + '...' if len(p['abstract']) > 200 else p['abstract']
                print(f"   摘要: {abstract}")

    # 2. 焦油处理专利
    if tar_removal:
        print("\n【焦油去除/裂解技术专利】")
        for i, p in enumerate(tar_removal[:5], 1):
            print(f"\n{i}. {p.get('patent_name')}")
            print(f"   公开号: {p.get('publication_number')}")
            print(f"   申请人: {p.get('applicant')}")
            print(f"   IPC分类: {p.get('ipc_main_class')}")
            if p.get('abstract'):
                abstract = p['abstract'][:200] + '...' if len(p['abstract']) > 200 else p['abstract']
                print(f"   摘要: {abstract}")

    # 3. 相关技术统计
    print("\n=== 技术统计 ===")

    # 申请人统计
    applicants = {}
    for p in unique_results:
        applicant = p.get('applicant', '未知')
        if applicant:
            applicants[applicant] = applicants.get(applicant, 0) + 1

    print("\n主要申请人（Top 10）:")
    for i, (applicant, count) in enumerate(sorted(applicants.items(), key=lambda x: x[1], reverse=True)[:10], 1):
        print(f"  {i:2d}. {applicant}: {count} 条")

    # IPC分类统计
    ipc_stats = {}
    for p in unique_results:
        ipc = p.get('ipc_main_class', '')
        if ipc:
            ipc_stats[ipc] = ipc_stats.get(ipc, 0) + 1

    print("\nIPC分类分布（Top 10）:")
    for i, (ipc, count) in enumerate(sorted(ipc_stats.items(), key=lambda x: x[1], reverse=True)[:10], 1):
        print(f"  {i:2d}. {ipc}: {count} 条")

    # 保存结果
    output_file = f"/Users/xujian/Athena工作平台/biomass_gasification_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "search_time": datetime.now().isoformat(),
            "total_results": len(unique_results),
            "statistics": {
                "dual_layer_count": len(dual_layer),
                "tar_removal_count": len(tar_removal),
                "biomass_count": len(biomass),
                "top_applicants": dict(sorted(applicants.items(), key=lambda x: x[1], reverse=True)[:10]),
                "ipc_distribution": dict(sorted(ipc_stats.items(), key=lambda x: x[1], reverse=True)[:10])
            },
            "patents": unique_results
        }, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 80}")
    print(f"详细结果已保存至：{output_file}")
    print(f"{'=' * 80}")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()
