#!/usr/bin/env python3
"""
专利无效检索脚本 - 扩展检索 (1985-2017年)
目标专利: 201921401279.9 (CN 210456236 U)
策略: 扩展时间窗口 + 优化关键词 + 扩展IPC分类
"""

import json
from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor


def main():
    print("=" * 110)
    print(" " * 30 + "专利无效检索系统 - 扩展检索版 (1985-2017)")
    print("=" * 110)
    print("\n目标专利: 201921401279.9 (CN 210456236 U)")
    print("申请日: 2019-08-27")
    print("\n本次检索策略:")
    print("  时间范围: 1985-01-01 至 2017-12-31")
    print("  核心特征: 斜向滑轨、间距渐变、联动调节")
    print("  扩展IPC: B65G、B65B、B23Q、F16M等")
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

    # ========== 检索式1: 核心特征 - 斜向/倾斜导轨 + 间距调节 ==========
    print("\n\n" + "=" * 110)
    print("【检索式1】核心特征检索 - 斜向/倾斜导轨 + 间距/角度调节")
    print("=" * 110)

    sql_1 = """
        SELECT patent_name, abstract, ipc_main_class, ipc_classification,
               applicant, inventor, application_date, publication_number,
               authorization_number, claims_content
        FROM patents
        WHERE application_date >= '1985-01-01' AND application_date <= '2017-12-31'
           AND (
               patent_name LIKE ANY(ARRAY['%斜向滑轨%', '%倾斜滑轨%', '%斜滑轨%', '%斜置导轨%',
               '%倾斜导轨%', '%斜导轨%']) OR
               abstract LIKE ANY(ARRAY['%斜向滑轨%', '%倾斜滑轨%', '%斜滑轨%', '%斜置导轨%',
               '%倾斜导轨%', '%斜导轨%'])
           )
           AND (
               patent_name LIKE ANY(ARRAY['%间距%', '%角度%', '%位置%', '%距离%']) OR
               abstract LIKE ANY(ARRAY['%间距%', '%角度%', '%位置%', '%距离%'])
           )
        ORDER BY application_date DESC
        LIMIT 50
    """

    try:
        cursor.execute(sql_1)
        batch1 = cursor.fetchall()

        filtered_batch1 = []
        for p in batch1:
            pn = p.get('publication_number')
            if pn and pn not in seen_numbers:
                seen_numbers.add(pn)
                filtered_batch1.append(p)

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
            if abstract and len(abstract) > 300:
                abstract = abstract[:300] + '...'
            if abstract:
                print(f"  {abstract}")

        all_results.extend(filtered_batch1)

    except Exception as e:
        print(f"\n检索式1执行出错: {e}")

    # ========== 检索式2: 扩展IPC分类检索 - B65G/B65B输送和包装 ==========
    print("\n\n" + "=" * 110)
    print("【检索式2】扩展IPC分类检索 - 输送和包装机械")
    print("=" * 110)

    sql_2 = """
        SELECT patent_name, abstract, ipc_main_class, ipc_classification,
               applicant, application_date, publication_number,
               authorization_number
        FROM patents
        WHERE application_date >= '1995-01-01' AND application_date <= '2017-12-31'
           AND (
               ipc_main_class LIKE 'B65G%' OR
               ipc_main_class LIKE 'B65B%' OR
               ipc_classification LIKE '%B65G%' OR
               ipc_classification LIKE '%B65B%'
           )
           AND (
               patent_name LIKE ANY(ARRAY['%限位板%', '%导向板%', '%侧板%', '%挡板%',
               '%调节机构%', '%可调%', '%自动调节%', '%同步调节%', '%联动调节%']) OR
               abstract LIKE ANY(ARRAY['%限位板%', '%导向板%', '%侧板%', '%挡板%',
               '%调节机构%', '%可调%', '%自动调节%', '%同步调节%', '%联动调节%'])
           )
           AND (
               patent_name LIKE ANY(ARRAY['%传送%', '%输送%', '%移动%', '%定位%']) OR
               abstract LIKE ANY(ARRAY['%传送%', '%输送%', '%移动%', '%定位%'])
           )
        ORDER BY application_date DESC
        LIMIT 50
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

        for i, p in enumerate(batch2[:10], 1):
            print(f"\n{'─' * 110}")
            print(f"专利 #{i}")
            print(f"【名称】{p.get('patent_name', 'N/A')}")
            print(f"【公开号】{p.get('publication_number', 'N/A')}")
            print(f"【IPC分类】{p.get('ipc_main_class', 'N/A')}")
            print(f"【申请人】{p.get('applicant', 'N/A')}")
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

    # ========== 检索式3: 机床/夹具类 - 可能包含斜向滑轨应用 ==========
    print("\n\n" + "=" * 110)
    print("【检索式3】机床夹具类检索 - 斜向导轨应用")
    print("=" * 110)

    sql_3 = """
        SELECT patent_name, abstract, ipc_main_class, ipc_classification,
               applicant, application_date, publication_number,
               authorization_number
        FROM patents
        WHERE application_date >= '1990-01-01' AND application_date <= '2017-12-31'
           AND (
               ipc_main_class LIKE 'B23Q%' OR
               ipc_classification LIKE '%B23Q%'
           )
           AND (
               patent_name LIKE ANY(ARRAY['%导轨%', '%滑轨%', '%滑块%', '%调节%']) OR
               abstract LIKE ANY(ARRAY['%导轨%', '%滑轨%', '%滑块%', '%调节%'])
           )
           AND (
               patent_name LIKE ANY(ARRAY['%斜向%', '%倾斜%', '%角度%', '%楔形%', '%锥形%']) OR
               abstract LIKE ANY(ARRAY['%斜向%', '%倾斜%', '%角度%', '%楔形%', '%锥形%'])
           )
        ORDER BY application_date DESC
        LIMIT 40
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

        for i, p in enumerate(batch3[:8], 1):
            print(f"\n{'─' * 110}")
            print(f"专利 #{i}")
            print(f"【名称】{p.get('patent_name', 'N/A')}")
            print(f"【公开号】{p.get('publication_number', 'N/A')}")
            print(f"【IPC分类】{p.get('ipc_main_class', 'N/A')}")
            if p.get('application_date'):
                print(f"【申请日期】{p['application_date']}")

    except Exception as e:
        print(f"\n检索式3执行出错: {e}")

    # ========== 检索式4: 楔形/锥形导轨 - 几何形状相关 ==========
    print("\n\n" + "=" * 110)
    print("【检索式4】几何形状检索 - 楔形/锥形导轨结构")
    print("=" * 110)

    sql_4 = """
        SELECT patent_name, abstract, ipc_main_class, ipc_classification,
               applicant, application_date, publication_number,
               authorization_number
        FROM patents
        WHERE application_date >= '1990-01-01' AND application_date <= '2017-12-31'
           AND (
               patent_name LIKE ANY(ARRAY['%楔形导轨%', '%楔形滑轨%', '%锥形导轨%', '%锥形滑轨%',
               '%梯形导轨%', '%梯形滑轨%', '%V型导轨%', '%V型滑轨%']) OR
               abstract LIKE ANY(ARRAY['%楔形导轨%', '%楔形滑轨%', '%锥形导轨%', '%锥形滑轨%',
               '%梯形导轨%', '%梯形滑轨%', '%V型导轨%', '%V型滑轨%'])
           )
           AND (
               patent_name LIKE ANY(ARRAY['%调节%', '%调整%', '%移动%', '%滑动%']) OR
               abstract LIKE ANY(ARRAY['%调节%', '%调整%', '%移动%', '%滑动%'])
           )
        ORDER BY application_date DESC
        LIMIT 40
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

        for i, p in enumerate(batch4[:8], 1):
            print(f"\n{'─' * 110}")
            print(f"专利 #{i}")
            print(f"【名称】{p.get('patent_name', 'N/A')}")
            print(f"【公开号】{p.get('publication_number', 'N/A')}")
            print(f"【IPC分类】{p.get('ipc_main_class', 'N/A')}")
            if p.get('application_date'):
                print(f"【申请日期】{p['application_date']}")

    except Exception as e:
        print(f"\n检索式4执行出错: {e}")

    # ========== 检索式5: 纵向+横向联动/同步调节 ==========
    print("\n\n" + "=" * 110)
    print("【检索式5】双维度联动调节检索")
    print("=" * 110)

    sql_5 = """
        SELECT patent_name, abstract, ipc_main_class,
               applicant, application_date, publication_number,
               authorization_number
        FROM patents
        WHERE application_date >= '2000-01-01' AND application_date <= '2017-12-31'
           AND (
               patent_name LIKE ANY(ARRAY['%纵向%', '%横向%', '%上下%', '%左右%', '%前后%']) OR
               abstract LIKE ANY(ARRAY['%纵向%', '%横向%', '%上下%', '%左右%', '%前后%'])
           )
           AND (
               patent_name LIKE ANY(ARRAY['%同步调节%', '%联动调节%', '%协同调节%', '%同时调节%']) OR
               abstract LIKE ANY(ARRAY['%同步调节%', '%联动调节%', '%协同调节%', '%同时调节%'])
           )
           AND (
               ipc_main_class LIKE 'B65G%' OR
               ipc_main_class LIKE 'B65B%' OR
               ipc_main_class LIKE 'B23Q%' OR
               ipc_main_class LIKE 'F16M%'
           )
        ORDER BY application_date DESC
        LIMIT 40
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

        for i, p in enumerate(batch5[:8], 1):
            print(f"\n{'─' * 110}")
            print(f"专利 #{i}")
            print(f"【名称】{p.get('patent_name', 'N/A')}")
            print(f"【公开号】{p.get('publication_number', 'N/A')}")
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

    # ========== 检索式6: 1985-1999年早期技术 ==========
    print("\n\n" + "=" * 110)
    print("【检索式6】早期技术检索 (1985-1999)")
    print("=" * 110)

    sql_6 = """
        SELECT patent_name, abstract, ipc_main_class, ipc_classification,
               applicant, application_date, publication_number,
               authorization_number
        FROM patents
        WHERE application_date >= '1985-01-01' AND application_date <= '1999-12-31'
           AND (
               ipc_main_class LIKE 'B65G%' OR
               ipc_main_class LIKE 'B65B%' OR
               ipc_main_class LIKE 'B23Q%'
           )
           AND (
               patent_name LIKE ANY(ARRAY['%导轨%', '%滑轨%', '%调节%', '%可调%', '%限位%']) OR
               abstract LIKE ANY(ARRAY['%导轨%', '%滑轨%', '%调节%', '%可调%', '%限位%'])
           )
        ORDER BY application_date DESC
        LIMIT 50
    """

    try:
        cursor.execute(sql_6)
        batch6 = cursor.fetchall()

        new_count = 0
        for p in batch6:
            pn = p.get('publication_number')
            if pn and pn not in seen_numbers:
                seen_numbers.add(pn)
                all_results.append(p)
                new_count += 1

        print(f"\n找到 {len(batch6)} 条，其中 {new_count} 条新增")

        for i, p in enumerate(batch6[:10], 1):
            print(f"\n{'─' * 110}")
            print(f"专利 #{i}")
            print(f"【名称】{p.get('patent_name', 'N/A')}")
            print(f"【公开号】{p.get('publication_number', 'N/A')}")
            print(f"【IPC分类】{p.get('ipc_main_class', 'N/A')}")
            print(f"【申请人】{p.get('applicant', 'N/A')}")
            if p.get('application_date'):
                print(f"【申请日期】{p['application_date']}")
            print("\n【摘要】")
            abstract = p.get('abstract', '')
            if abstract and len(abstract) > 200:
                abstract = abstract[:200] + '...'
            if abstract:
                print(f"  {abstract}")

    except Exception as e:
        print(f"\n检索式6执行出错: {e}")

    # ========== 检索式7: 宽松IPC + 关键词组合 ==========
    print("\n\n" + "=" * 110)
    print("【检索式7】宽松IPC + 传送/输送装置导向调节")
    print("=" * 110)

    sql_7 = """
        SELECT patent_name, abstract, ipc_main_class,
               applicant, application_date, publication_number
        FROM patents
        WHERE application_date >= '1995-01-01' AND application_date <= '2017-12-31'
           AND (
               ipc_main_class LIKE 'B65G%' OR
               ipc_main_class LIKE 'B65B%' OR
               ipc_main_class LIKE 'B23Q%' OR
               ipc_main_class LIKE 'B23P%' OR
               ipc_main_class LIKE 'B23K%' OR
               ipc_main_class LIKE 'F16M%' OR
               ipc_main_class LIKE 'B25J%'
           )
           AND (
               (patent_name LIKE '%传送%' OR patent_name LIKE '%输送%' OR
                patent_name LIKE '%导向%' OR patent_name LIKE '%限位%')
               AND
               (patent_name LIKE '%调节%' OR patent_name LIKE '%可调%' OR
                patent_name LIKE '%同步%' OR patent_name LIKE '%联动%')
           )
        ORDER BY application_date DESC
        LIMIT 50
    """

    try:
        cursor.execute(sql_7)
        batch7 = cursor.fetchall()

        new_count = 0
        for p in batch7:
            pn = p.get('publication_number')
            if pn and pn not in seen_numbers:
                seen_numbers.add(pn)
                all_results.append(p)
                new_count += 1

        print(f"\n找到 {len(batch7)} 条，其中 {new_count} 条新增")

        for i, p in enumerate(batch7[:8], 1):
            print(f"\n{'─' * 110}")
            print(f"专利 #{i}")
            print(f"【名称】{p.get('patent_name', 'N/A')}")
            print(f"【公开号】{p.get('publication_number', 'N/A')}")
            print(f"【IPC分类】{p.get('ipc_main_class', 'N/A')}")
            if p.get('application_date'):
                print(f"【申请日期】{p['application_date']}")

    except Exception as e:
        print(f"\n检索式7执行出错: {e}")

    # ========== 统计分析 ==========
    print("\n\n" + "=" * 110)
    print("【检索结果统计分析】")
    print("=" * 110)

    print(f"\n总计不重复专利: {len(all_results)} 条")

    # 按年份统计
    year_stats = {}
    decade_stats = {}
    for p in all_results:
        app_date = p.get('application_date')
        if app_date:
            year = str(app_date)[:4]
            year_stats[year] = year_stats.get(year, 0) + 1
            decade = year[:3] + "0"
            decade_stats[decade] = decade_stats.get(decade, 0) + 1

    print("\n年代分布:")
    for decade in sorted(decade_stats.keys()):
        print(f"  {decade}年代: {decade_stats[decade]} 条")

    print("\n申请年份分布 (Top 15):")
    for year in sorted(year_stats.keys(), reverse=True)[:15]:
        print(f"  {year}: {year_stats[year]} 条")

    # IPC分类统计
    ipc_stats = {}
    for p in all_results:
        ipc = p.get('ipc_main_class', '') or ''
        if ipc:
            ipc_stats[ipc] = ipc_stats.get(ipc, 0) + 1

    print("\nIPC分类分布 (Top 15):")
    for i, (ipc, count) in enumerate(sorted(ipc_stats.items(), key=lambda x: x[1], reverse=True)[:15], 1):
        print(f"  {i:2d}. {ipc}: {count} 条")

    # ========== 相关性评分 ==========
    print("\n\n" + "=" * 110)
    print("【相关性评分 - Top 30 高相关性专利】")
    print("=" * 110)

    scored_patents = []
    for p in all_results:
        score = 0
        reasons = []

        title = p.get('patent_name', '')
        abstract = p.get('abstract', '') or ''
        text = (title + ' ' + abstract).lower()

        # 核心特征评分（最高权重）
        if '斜向滑轨' in text or '倾斜滑轨' in text or '斜滑轨' in text:
            score += 60
            reasons.append("斜向滑轨特征")
        elif '楔形导轨' in text or '楔形滑轨' in text:
            score += 50
            reasons.append("楔形导轨特征")
        elif '锥形导轨' in text:
            score += 45
            reasons.append("锥形导轨特征")

        # 渐变/间距变化特征
        if any(kw in text for kw in ['间距渐变', '间距变化', '逐渐缩短', '逐渐变窄', '渐变']):
            score += 50
            reasons.append("间距渐变特征")
        elif any(kw in text for kw in ['变距', '间距调节', '可变间距']):
            score += 30
            reasons.append("可变间距")

        # 联动调节功能
        if '联动调节' in text or '同步调节' in text:
            score += 35
            reasons.append("联动调节功能")

        # 双维度调节
        if '纵向' in text and ('横向' in text or '宽度' in text):
            score += 25
            reasons.append("纵向+横向调节")

        # 应用场景
        if '限位板' in text or '导向板' in text:
            score += 20
            reasons.append("限位/导向板")
        if '传送' in text or '输送' in text:
            score += 10
            reasons.append("传送/输送装置")
        if '包装机' in text:
            score += 15
            reasons.append("包装机应用")

        # 时间加分（越早越好）
        app_date = p.get('application_date')
        if app_date:
            year = str(app_date)[:4]
            if int(year) <= 1999:
                score += 20
            elif int(year) <= 2005:
                score += 15
            elif int(year) <= 2010:
                score += 10

        if score > 0:
            scored_patents.append({
                'patent': p,
                'score': score,
                'reasons': reasons
            })

    # 排序并展示
    scored_patents.sort(key=lambda x: x['score'], reverse=True)

    for i, item in enumerate(scored_patents[:30], 1):
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
    output_file = f"patent_invalid_search_extended_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    saveable_results = []
    for item in scored_patents[:100]:  # 保存Top 100
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
        'search_strategy': 'Extended 1985-2017',
        'target_patent': '201921401279.9 (CN 210456236 U)',
        'total_results': len(all_results),
        'year_distribution': year_stats,
        'decade_distribution': decade_stats,
        'ipc_distribution': dict(sorted(ipc_stats.items(), key=lambda x: x[1], reverse=True)[:15]),
        'top_results': saveable_results
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n\n{'=' * 110}")
    print(f"检索结果已保存至: {output_file}")
    print(f"{'=' * 110}")

    cursor.close()
    conn.close()

    print("\n扩展检索完成！")


if __name__ == "__main__":
    main()
