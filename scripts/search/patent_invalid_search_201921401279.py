#!/usr/bin/env python3
"""
专利无效检索脚本 - 目标专利 201921401279.9 (CN 210456236 U)
根据检索策略文档执行检索
"""

import json
from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor


def main():
    print("=" * 110)
    print(" " * 35 + "专利无效检索系统")
    print("=" * 110)
    print("\n目标专利: 201921401279.9 (CN 210456236 U)")
    print("名称: 包装机物品传送装置物料限位板调节机构")
    print("申请日: 2019-08-27")
    print("\n核心创新点: 两条斜向滑轨的间距从左往右逐渐缩短")
    print("=" * 110)

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

    all_results = []
    seen_numbers = set()

    # ========== 检索式1: 斜向滑轨渐变组合（最关键） ==========
    print("\n\n" + "=" * 110)
    print("【检索式1】斜向滑轨渐变组合 - 核心特征检索")
    print("=" * 110)
    print("\n检索目标: 寻找具有相同或相似核心发明点的现有技术")
    print("关键词: 斜向滑轨 + 间距渐变/变化/变距")

    keywords_1 = [
        "斜向滑轨", "倾斜滑轨", "斜滑轨", "斜置导轨",
        "倾斜导轨", "斜导轨"
    ]

    # 构建检索条件
    conditions_1 = []
    for kw in keywords_1[:3]:  # 限制查询复杂度
        conditions_1.append(f"patent_name LIKE '%{kw}%'")
        conditions_1.append(f"abstract LIKE '%{kw}%'")

    where_clause_1 = " OR ".join(conditions_1[:6])  # 限制条件数量

    sql_1 = f"""
        SELECT patent_name, abstract, ipc_main_class, ipc_classification,
               applicant, inventor, application_date, publication_number,
               authorization_number, claims_content
        FROM patents
        WHERE ({where_clause_1})
           AND application_date <= '2019-08-27'
           AND application_date >= '2010-01-01'
        ORDER BY application_date DESC NULLS LAST
        LIMIT 50
    """

    try:
        cursor.execute(sql_1)
        batch1 = cursor.fetchall()

        # 筛选包含渐变相关关键词的专利
        filtered_batch1 = []
        for patent in batch1:
            text = (patent.get('patent_name', '') + ' ' + (patent.get('abstract', '') or '')).lower()
            if any(var in text for var in ['间距', '渐变', '变化', '变距', '调节', '调整']):
                pn = patent.get('publication_number')
                if pn and pn not in seen_numbers:
                    seen_numbers.add(pn)
                    filtered_batch1.append(patent)

        print(f"\n找到 {len(filtered_batch1)} 条相关专利")

        for i, p in enumerate(filtered_batch1[:10], 1):
            print(f"\n{'─' * 110}")
            print(f"专利 #{i}")
            print(f"【名称】{p.get('patent_name', 'N/A')}")
            print(f"【公开号】{p.get('publication_number', 'N/A')}")
            print(f"【申请人】{p.get('applicant', 'N/A')}")
            print(f"【IPC分类】{p.get('ipc_main_class', 'N/A')}")
            if p.get('application_date'):
                print(f"【申请日期】{p['application_date']}")
            print("\n【摘要】")
            abstract = p.get('abstract', '')
            if abstract:
                # 取前300字
                if len(abstract) > 300:
                    abstract = abstract[:300] + '...'
                print(f"  {abstract}")

        all_results.extend(filtered_batch1)

    except Exception as e:
        print(f"\n检索式1执行出错: {e}")

    # ========== 检索式2: 联动调节功能 ==========
    print("\n\n" + "=" * 110)
    print("【检索式2】联动调节功能 - 技术效果等同检索")
    print("=" * 110)
    print("\n检索目标: 寻找实现相同技术效果（联动调节）的不同技术方案")


    sql_2 = """
        SELECT patent_name, abstract, ipc_main_class, ipc_classification,
               applicant, application_date, publication_number,
               authorization_number
        FROM patents
        WHERE (patent_name LIKE ANY(ARRAY['%联动调节%', '%同步调节%', '%协同调节%'])
           OR abstract LIKE ANY(ARRAY['%联动调节%', '%同步调节%', '%协同调节%']))
           AND (patent_name LIKE ANY(ARRAY['%限位板%', '%导向板%', '%侧板%', '%传送%', '%输送%'])
           OR abstract LIKE ANY(ARRAY['%限位板%', '%导向板%', '%侧板%', '%传送%', '%输送%']))
           AND application_date <= '2019-08-27'
           AND application_date >= '2014-01-01'
        ORDER BY application_date DESC NULLS LAST
        LIMIT 30
    """

    try:
        cursor.execute(sql_2)
        batch2 = cursor.fetchall()

        new_count = 0
        for p in batch2:
            pn = p.get('publication_number')
            if pn and pn not in seen_numbers:
                seen_numbers.add(pn)
                all_results.append(p)
                new_count += 1

        print(f"\n找到 {len(batch2)} 条，其中 {new_count} 条新增")

        for i, p in enumerate(batch2[:8], 1):
            print(f"\n{'─' * 110}")
            print(f"专利 #{i}")
            print(f"【名称】{p.get('patent_name', 'N/A')}")
            print(f"【公开号】{p.get('publication_number', 'N/A')}")
            print(f"【申请人】{p.get('applicant', 'N/A')}")
            print(f"【IPC分类】{p.get('ipc_main_class', 'N/A')}")
            if p.get('application_date'):
                print(f"【申请日期】{p['application_date']}")
            print("\n【摘要】")
            abstract = p.get('abstract', '')
            if abstract and len(abstract) > 250:
                abstract = abstract[:250] + '...'
            if abstract:
                print(f"  {abstract}")

    except Exception as e:
        print(f"\n检索式2执行出错: {e}")

    # ========== 检索式3: 纵向+横向组合调节 ==========
    print("\n\n" + "=" * 110)
    print("【检索式3】纵向+横向组合调节 - 结构相似检索")
    print("=" * 110)

    sql_3 = """
        SELECT patent_name, abstract, ipc_main_class,
               applicant, application_date, publication_number,
               authorization_number
        FROM patents
        WHERE (patent_name LIKE '%纵向%' OR abstract LIKE '%纵向%')
           AND (patent_name LIKE '%横向%' OR abstract LIKE '%横向%')
           AND (patent_name LIKE ANY(ARRAY['%调节%', '%调整%', '%移动%'])
           OR abstract LIKE ANY(ARRAY['%调节%', '%调整%', '%移动%']))
           AND (ipc_main_class LIKE 'B65G%' OR ipc_main_class LIKE 'B65B%')
           AND application_date <= '2019-08-27'
           AND application_date >= '2014-01-01'
        ORDER BY application_date DESC NULLS LAST
        LIMIT 30
    """

    try:
        cursor.execute(sql_3)
        batch3 = cursor.fetchall()

        new_count = 0
        for p in batch3:
            pn = p.get('publication_number')
            if pn and pn not in seen_numbers:
                seen_numbers.add(pn)
                all_results.append(p)
                new_count += 1

        print(f"\n找到 {len(batch3)} 条，其中 {new_count} 条新增")

        for i, p in enumerate(batch3[:6], 1):
            print(f"\n{'─' * 110}")
            print(f"专利 #{i}")
            print(f"【名称】{p.get('patent_name', 'N/A')}")
            print(f"【公开号】{p.get('publication_number', 'N/A')}")
            print(f"【申请人】{p.get('applicant', 'N/A')}")
            print(f"【IPC分类】{p.get('ipc_main_class', 'N/A')}")
            if p.get('application_date'):
                print(f"【申请日期】{p['application_date']}")

    except Exception as e:
        print(f"\n检索式3执行出错: {e}")

    # ========== 检索式4: 包装机应用场景 ==========
    print("\n\n" + "=" * 110)
    print("【检索式4】包装机应用场景 - 应用领域检索")
    print("=" * 110)

    sql_4 = """
        SELECT patent_name, abstract, ipc_main_class,
               applicant, application_date, publication_number,
               authorization_number
        FROM patents
        WHERE patent_name LIKE '%包装机%'
           AND (patent_name LIKE ANY(ARRAY['%限位%', '%导向%', '%调节%', '%可调%'])
           OR abstract LIKE ANY(ARRAY['%限位%', '%导向%', '%调节%', '%可调%']))
           AND (patent_name LIKE ANY(ARRAY['%传送%', '%输送%'])
           OR abstract LIKE ANY(ARRAY['%传送%', '%输送%']))
           AND application_date <= '2019-08-27'
           AND application_date >= '2015-01-01'
        ORDER BY application_date DESC NULLS LAST
        LIMIT 30
    """

    try:
        cursor.execute(sql_4)
        batch4 = cursor.fetchall()

        new_count = 0
        for p in batch4:
            pn = p.get('publication_number')
            if pn and pn not in seen_numbers:
                seen_numbers.add(pn)
                all_results.append(p)
                new_count += 1

        print(f"\n找到 {len(batch4)} 条，其中 {new_count} 条新增")

        for i, p in enumerate(batch4[:6], 1):
            print(f"\n{'─' * 110}")
            print(f"专利 #{i}")
            print(f"【名称】{p.get('patent_name', 'N/A')}")
            print(f"【公开号】{p.get('publication_number', 'N/A')}")
            print(f"【申请人】{p.get('applicant', 'N/A')}")
            if p.get('application_date'):
                print(f"【申请日期】{p['application_date']}")

    except Exception as e:
        print(f"\n检索式4执行出错: {e}")

    # ========== 检索式5: IPC分类精确检索 ==========
    print("\n\n" + "=" * 110)
    print("【检索式5】IPC分类精确检索 - B65G 47/26 可调节导向装置")
    print("=" * 110)

    sql_5 = """
        SELECT patent_name, abstract, ipc_main_class, ipc_classification,
               applicant, application_date, publication_number,
               authorization_number
        FROM patents
        WHERE (ipc_main_class = 'B65G47/26' OR ipc_main_class = 'B65G 47/26'
           OR ipc_main_class LIKE 'B65G47/24%' OR ipc_main_class LIKE 'B65G 47/24%')
           AND application_date <= '2019-08-27'
           AND application_date >= '2010-01-01'
        ORDER BY application_date DESC NULLS LAST
        LIMIT 50
    """

    try:
        cursor.execute(sql_5)
        batch5 = cursor.fetchall()

        new_count = 0
        for p in batch5:
            pn = p.get('publication_number')
            if pn and pn not in seen_numbers:
                seen_numbers.add(pn)
                all_results.append(p)
                new_count += 1

        print(f"\n找到 {len(batch5)} 条，其中 {new_count} 条新增")

        for i, p in enumerate(batch5[:10], 1):
            print(f"\n{'─' * 110}")
            print(f"专利 #{i}")
            print(f"【名称】{p.get('patent_name', 'N/A')}")
            print(f"【公开号】{p.get('publication_number', 'N/A')}")
            print(f"【申请人】{p.get('applicant', 'N/A')}")
            print(f"【IPC分类】{p.get('ipc_main_class', 'N/A')}")
            if p.get('application_date'):
                print(f"【申请日期】{p['application_date']}")
            print("\n【摘要】")
            abstract = p.get('abstract', '')
            if abstract and len(abstract) > 200:
                abstract = abstract[:200] + '...'
            if abstract:
                print(f"  {abstract}")

    except Exception as e:
        print(f"\n检索式5执行出错: {e}")

    # ========== 统计分析 ==========
    print("\n\n" + "=" * 110)
    print("【检索结果统计分析】")
    print("=" * 110)

    print(f"\n总计不重复专利: {len(all_results)} 条")

    # 按年份统计
    year_stats = {}
    for p in all_results:
        app_date = p.get('application_date')
        if app_date:
            year = str(app_date)[:4]
            year_stats[year] = year_stats.get(year, 0) + 1

    print("\n申请年份分布:")
    for year in sorted(year_stats.keys(), reverse=True):
        print(f"  {year}: {year_stats[year]} 条")

    # 申请人统计
    applicants = {}
    for p in all_results:
        applicant = p.get('applicant', '未知')
        if applicant:
            applicants[applicant] = applicants.get(applicant, 0) + 1

    print("\n主要申请人 (Top 15):")
    for i, (applicant, count) in enumerate(sorted(applicants.items(), key=lambda x: x[1], reverse=True)[:15], 1):
        print(f"  {i:2d}. {applicant}: {count} 条")

    # IPC分类统计
    ipc_stats = {}
    for p in all_results:
        ipc = p.get('ipc_main_class', '') or ''
        if ipc:
            ipc_stats[ipc] = ipc_stats.get(ipc, 0) + 1

    print("\nIPC分类分布 (Top 10):")
    for i, (ipc, count) in enumerate(sorted(ipc_stats.items(), key=lambda x: x[1], reverse=True)[:10], 1):
        print(f"  {i:2d}. {ipc}: {count} 条")

    # ========== 相关性评分 ==========
    print("\n\n" + "=" * 110)
    print("【相关性评分 - Top 20 高相关性专利】")
    print("=" * 110)

    # 评分系统
    scored_patents = []
    for p in all_results:
        score = 0
        reasons = []

        title = p.get('patent_name', '')
        abstract = p.get('abstract', '') or ''
        text = (title + ' ' + abstract).lower()

        # 核心特征评分（高权重）
        if '斜向滑轨' in text or '倾斜滑轨' in text or '斜滑轨' in text:
            score += 50
            reasons.append("斜向滑轨特征")

        if '间距渐变' in text or '间距变化' in text or '变距' in text:
            score += 40
            reasons.append("间距渐变特征")

        # 功能等同评分（中高权重）
        if '联动调节' in text or '同步调节' in text:
            score += 30
            reasons.append("联动调节功能")

        if '纵向' in text and '横向' in text:
            score += 25
            reasons.append("纵向+横向调节")

        # 应用场景评分（中权重）
        if '限位板' in text or '导向板' in text:
            score += 15
            reasons.append("限位/导向板")

        if '包装机' in text:
            score += 10
            reasons.append("包装机应用")

        if '传送' in text or '输送' in text:
            score += 5
            reasons.append("传送/输送装置")

        # 时间评分（越接近申请日权重越高）
        app_date = p.get('application_date')
        if app_date:
            year = str(app_date)[:4]
            if year == '2019':
                score += 10
            elif year == '2018':
                score += 8
            elif year == '2017':
                score += 6

        if score > 0:
            scored_patents.append({
                'patent': p,
                'score': score,
                'reasons': reasons
            })

    # 排序并展示
    scored_patents.sort(key=lambda x: x['score'], reverse=True)

    for i, item in enumerate(scored_patents[:20], 1):
        p = item['patent']
        print(f"\n{'=' * 110}")
        print(f"#{i} 相关性评分: {item['score']} 分")
        print(f"【匹配特征】{', '.join(item['reasons'])}")
        print(f"【名称】{p.get('patent_name', 'N/A')}")
        print(f"【公开号】{p.get('publication_number', 'N/A')}")
        print(f"【申请人】{p.get('applicant', 'N/A')}")
        print(f"【IPC分类】{p.get('ipc_main_class', 'N/A')}")
        if p.get('application_date'):
            print(f"【申请日期】{p['application_date']}")
        print("\n【摘要】")
        abstract = p.get('abstract', '')
        if abstract:
            if len(abstract) > 400:
                abstract = abstract[:400] + '...'
            print(f"  {abstract}")

    # ========== 保存结果 ==========
    output_file = f"patent_invalid_search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    saveable_results = []
    for item in scored_patents[:50]:  # 保存Top 50
        p = item['patent']
        saveable = {
            'score': item['score'],
            'reasons': item['reasons'],
            'patent_name': p.get('patent_name'),
            'publication_number': p.get('publication_number'),
            'applicant': p.get('applicant'),
            'ipc_main_class': p.get('ipc_main_class'),
            'application_date': str(p.get('application_date')) if p.get('application_date') else None,
            'abstract': p.get('abstract')
        }
        saveable_results.append(saveable)

    report = {
        'search_time': datetime.now().isoformat(),
        'target_patent': '201921401279.9 (CN 210456236 U)',
        'total_results': len(all_results),
        'year_distribution': year_stats,
        'top_applicants': dict(sorted(applicants.items(), key=lambda x: x[1], reverse=True)[:15]),
        'ipc_distribution': dict(sorted(ipc_stats.items(), key=lambda x: x[1], reverse=True)[:10]),
        'top_results': saveable_results
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n\n{'=' * 110}")
    print(f"检索结果已保存至: {output_file}")
    print(f"{'=' * 110}")

    cursor.close()
    conn.close()

    print("\n检索完成！")


if __name__ == "__main__":
    main()
