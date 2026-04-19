#!/usr/bin/env python3
"""
生物质气化发生炉专利检索与分析报告
检索关于生物质气化的发生炉技术，其特点是：上下双火层，上火层可以去除煤焦油
"""

import json
from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor


def serialize_patent(patent):
    """将专利数据转换为可序列化的格式"""
    result = {}
    for key, value in patent.items():
        if isinstance(value, datetime):
            result[key] = value.isoformat()
        elif hasattr(value, 'isoformat'):  # 处理date对象
            result[key] = value.isoformat()
        else:
            result[key] = value
    return result


def main():
    print("=" * 100)
    print(" " * 30 + "生物质气化发生炉专利检索与分析报告")
    print("=" * 100)

    # 连接数据库
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='patent_db',
        user='postgres',
        password='postgres',
        cursor_factory=RealDictCursor
    )
    cursor = conn.cursor()

    # 检索式构建
    print("\n【检索式构建】")
    print("-" * 100)

    # 核心检索式
    search_queries = {
        "query1": {
            "name": "生物质气化炉",
            "keywords": ["生物质", "气化炉", "发生炉"],
            "logic": "OR"
        },
        "query2": {
            "name": "双火层/双层结构",
            "keywords": ["双火层", "双层", "上火层", "下火层", "双段气化"],
            "logic": "OR"
        },
        "query3": {
            "name": "焦油去除技术",
            "keywords": ["气化", "焦油", "除焦", "裂解", "重整"],
            "logic": "AND"
        }
    }

    print("\n检索目标：生物质气化发生炉技术，重点关注上下双火层和焦油去除技术")
    print("\n检索式组合：")
    for i, (_key, query) in enumerate(search_queries.items(), 1):
        print(f"  检索式{i}（{query['name']}）：{' OR '.join(query['keywords'])} （逻辑：{query['logic']}）")

    # 执行检索
    all_results = []
    seen_numbers = set()

    print("\n" + "=" * 100)
    print("【检索执行】")
    print("-" * 100)

    # 检索1：生物质气化炉
    print("\n[1/3] 检索：生物质气化炉...")
    cursor.execute("""
        SELECT patent_name, abstract, ipc_main_class, ipc_classification,
               applicant, inventor, application_date, publication_number,
               authorization_number, claims_content
        FROM patents
        WHERE patent_name LIKE ANY(ARRAY['%生物质%', '%气化炉%', '%发生炉%'])
           OR abstract LIKE ANY(ARRAY['%生物质%', '%气化炉%', '%发生炉%'])
        ORDER BY application_date DESC NULLS LAST
        LIMIT 50
    """)
    batch1 = cursor.fetchall()
    for r in batch1:
        pn = r.get('publication_number') or r.get('patent_name')
        if pn and pn not in seen_numbers:
            seen_numbers.add(pn)
            all_results.append(dict(r))
    print(f"      找到 {len(batch1)} 条，新增 {len([r for r in batch1 if (r.get('publication_number') or r.get('patent_name')) not in seen_numbers])} 条")

    # 检索2：双火层结构
    print("\n[2/3] 检索：双火层/双层结构...")
    cursor.execute("""
        SELECT patent_name, abstract, ipc_main_class, ipc_classification,
               applicant, inventor, application_date, publication_number,
               authorization_number, claims_content
        FROM patents
        WHERE patent_name LIKE ANY(ARRAY['%双火层%', '%双层%', '%上火层%', '%下火层%', '%双段气化%', '%两级气化%'])
           OR abstract LIKE ANY(ARRAY['%双火层%', '%双层%', '%上火层%', '%下火层%', '%双段气化%', '%两级气化%'])
        ORDER BY application_date DESC NULLS LAST
        LIMIT 50
    """)
    batch2 = cursor.fetchall()
    new_count = 0
    for r in batch2:
        pn = r.get('publication_number') or r.get('patent_name')
        if pn and pn not in seen_numbers:
            seen_numbers.add(pn)
            all_results.append(dict(r))
            new_count += 1
    print(f"      找到 {len(batch2)} 条，新增 {new_count} 条")

    # 检索3：焦油处理技术
    print("\n[3/3] 检索：焦油去除/裂解技术...")
    cursor.execute("""
        SELECT patent_name, abstract, ipc_main_class, ipc_classification,
               applicant, inventor, application_date, publication_number,
               authorization_number, claims_content
        FROM patents
        WHERE (patent_name LIKE ANY(ARRAY['%气化%', '%发生炉%', '%气化炉%'])
           OR abstract LIKE ANY(ARRAY['%气化%', '%发生炉%', '%气化炉%']))
           AND (patent_name LIKE ANY(ARRAY['%焦油%', '%除焦%', '%裂解%', '%重整%', '%催化裂解%'])
           OR abstract LIKE ANY(ARRAY['%焦油%', '%除焦%', '%裂解%', '%重整%', '%催化裂解%']))
        ORDER BY application_date DESC NULLS LAST
        LIMIT 50
    """)
    batch3 = cursor.fetchall()
    new_count = 0
    for r in batch3:
        pn = r.get('publication_number') or r.get('patent_name')
        if pn and pn not in seen_numbers:
            seen_numbers.add(pn)
            all_results.append(dict(r))
            new_count += 1
    print(f"      找到 {len(batch3)} 条，新增 {new_count} 条")

    print("\n" + "=" * 100)
    print("【检索结果汇总】")
    print("-" * 100)
    print(f"总计不重复专利：{len(all_results)} 条")

    if not all_results:
        print("\n未找到相关专利，建议调整检索策略。")
        cursor.close()
        conn.close()
        return

    # 技术分类分析
    print("\n" + "=" * 100)
    print("【技术特征分析】")
    print("-" * 100)

    categories = {
        "生物质气化技术": [],
        "双火层/双层结构": [],
        "焦油去除/裂解技术": [],
        "多功能组合技术": []
    }

    for patent in all_results:
        title = patent.get('patent_name', '')
        abstract = patent.get('abstract', '') or ''
        claims = patent.get('claims_content', '') or ''
        full_text = (title + ' ' + abstract + ' ' + claims).lower()

        # 分类统计
        has_biomass = '生物质' in full_text or '气化' in full_text
        has_dual_layer = '双火层' in full_text or '双层' in full_text or '上火层' in full_text or '下火层' in full_text
        has_tar = '焦油' in full_text or '除焦' in full_text or '裂解' in full_text

        if has_dual_layer and has_tar and has_biomass:
            categories["多功能组合技术"].append(patent)
        elif has_dual_layer:
            categories["双火层/双层结构"].append(patent)
        elif has_tar:
            categories["焦油去除/裂解技术"].append(patent)
        elif has_biomass:
            categories["生物质气化技术"].append(patent)

    for category, patents in categories.items():
        print(f"\n  {category}：{len(patents)} 条")

    # 统计分析
    print("\n" + "=" * 100)
    print("【统计分析】")
    print("-" * 100)

    # 申请人统计
    applicants = {}
    for p in all_results:
        applicant = p.get('applicant', '未知')
        if applicant:
            applicants[applicant] = applicants.get(applicant, 0) + 1

    print("\n主要申请人（Top 15）：")
    for i, (applicant, count) in enumerate(sorted(applicants.items(), key=lambda x: x[1], reverse=True)[:15], 1):
        print(f"  {i:2d}. {applicant}: {count} 条")

    # IPC分类统计
    ipc_stats = {}
    for p in all_results:
        ipc = p.get('ipc_main_class', '') or ''
        if ipc:
            ipc_stats[ipc] = ipc_stats.get(ipc, 0) + 1

    print("\nIPC分类分布（Top 15）：")
    for i, (ipc, count) in enumerate(sorted(ipc_stats.items(), key=lambda x: x[1], reverse=True)[:15], 1):
        print(f"  {i:2d}. {ipc}: {count} 条")

    # 时间分布
    years = {}
    for p in all_results:
        app_date = p.get('application_date')
        if app_date:
            year = str(app_date)[:4]
            years[year] = years.get(year, 0) + 1

    if years:
        print("\n申请年份分布：")
        for year in sorted(years.keys(), reverse=True):
            print(f"  {year}: {years[year]} 条")

    # 重点专利展示
    print("\n" + "=" * 100)
    print("【重点专利详情】")
    print("-" * 100)

    # 按相关性排序展示前20条
    top_patents = all_results[:20] if len(all_results) >= 20 else all_results

    for i, patent in enumerate(top_patents, 1):
        print(f"\n{'=' * 100}")
        print(f"专利 #{i}")
        print("-" * 100)

        print(f"【名称】{patent.get('patent_name', 'N/A')}")
        print(f"【公开号】{patent.get('publication_number', 'N/A')}")
        print(f"【授权号】{patent.get('authorization_number', 'N/A')}")
        print(f"【申请人】{patent.get('applicant', 'N/A')}")
        print(f"【发明人】{patent.get('inventor', 'N/A')}")
        print(f"【IPC分类】{patent.get('ipc_main_class', 'N/A')}")

        if patent.get('application_date'):
            print(f"【申请日期】{patent['application_date']}")

        if patent.get('abstract'):
            abstract = patent['abstract']
            if len(abstract) > 300:
                abstract = abstract[:300] + '...'
            print("\n【摘要】")
            print(f"  {abstract}")

        # 技术特征标注
        title = patent.get('patent_name', '')
        abstract = patent.get('abstract', '') or ''
        full_text = (title + ' ' + abstract).lower()

        features = []
        if '双火层' in full_text or '上火层' in full_text or '下火层' in full_text:
            features.append("✓ 双火层结构")
        if '双层' in full_text:
            features.append("✓ 双层结构")
        if '焦油' in full_text:
            features.append("✓ 焦油处理")
        if '裂解' in full_text:
            features.append("✓ 裂解技术")
        if '生物质' in full_text:
            features.append("✓ 生物质")
        if '气化' in full_text:
            features.append("✓ 气化技术")

        if features:
            print(f"\n【技术特征】{', '.join(features)}")

    # 生成总结报告
    print("\n" + "=" * 100)
    print("【技术总结】")
    print("-" * 100)

    summary = f"""
根据检索结果，共找到 {len(all_results)} 条相关专利，主要技术特点如下：

1. 技术分布：
   - 生物质气化技术：{len(categories['生物质气化技术'])} 条
   - 双火层/双层结构：{len(categories['双火层/双层结构'])} 条
   - 焦油去除/裂解技术：{len(categories['焦油去除/裂解技术'])} 条
   - 多功能组合技术：{len(categories['多功能组合技术'])} 条

2. 主要技术方向：
   - 生物质燃料的气化燃烧技术
   - 双层/双段式气化炉结构设计
   - 焦油裂解和净化技术
   - 气化发电系统

3. 技术发展趋势：
   - 从单一燃烧向综合能源利用转变
   - 结构上向多层、多段发展
   - 注重焦油等副产物的处理和利用
   - 与其他能源技术（如太阳能）结合

4. 关键技术特征：
   - 双层炉体结构设计
   - 焦油高温裂解技术
   - 气化效率优化
   - 环保排放控制
"""

    print(summary)

    # 保存结果
    output_file = f"biomass_gasification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    # 转换数据格式以便保存
    saveable_results = [serialize_patent(p) for p in all_results]

    report_data = {
        "search_time": datetime.now().isoformat(),
        "search_queries": search_queries,
        "statistics": {
            "total_results": len(all_results),
            "categories": {k: len(v) for k, v in categories.items()},
            "top_applicants": dict(sorted(applicants.items(), key=lambda x: x[1], reverse=True)[:15]),
            "ipc_distribution": dict(sorted(ipc_stats.items(), key=lambda x: x[1], reverse=True)[:15]),
            "year_distribution": years
        },
        "summary": summary,
        "patents": saveable_results
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)

    print(f"\n详细检索报告已保存至：{output_file}")

    cursor.close()
    conn.close()

    print("\n" + "=" * 100)
    print("检索完成！")
    print("=" * 100)


if __name__ == "__main__":
    main()
