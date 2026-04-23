#!/usr/bin/env python3
"""
生物质气化发生炉相关专利摘要展示
展示与生物质气化、双火层结构、焦油去除技术相关的专利摘要
"""

from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor


def format_abstract(abstract):
    """格式化摘要显示"""
    if not abstract:
        return "暂无摘要"
    # 按句号分段，取前6句
    sentences = [s.strip() for s in abstract.split('。') if s.strip()]
    return '。\n  '.join(sentences[:6]) + ('。' if len(sentences) > 6 else '')


def main():
    print("=" * 110)
    print(" " * 35 + "生物质气化发生炉相关专利摘要展示")
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

    all_patents = []

    # ========== 检索1：生物质气化炉专利 ==========
    print("\n" + "=" * 110)
    print("【类别1】生物质气化炉相关专利")
    print("=" * 110)

    cursor.execute("""
        SELECT patent_name, abstract, applicant, ipc_main_class,
               publication_number, application_date, claims_content
        FROM patents
        WHERE (patent_name LIKE '%生物质%' OR patent_name LIKE '%气化炉%')
           AND abstract IS NOT NULL AND LENGTH(abstract) > 50
        ORDER BY application_date DESC NULLS LAST
        LIMIT 8
    """)

    results = cursor.fetchall()
    for i, p in enumerate(results, 1):
        print(f"\n{'─' * 110}")
        print(f"专利 #{i}")
        print(f"【名称】{p.get('patent_name', 'N/A')}")
        print(f"【公开号】{p.get('publication_number', 'N/A')}")
        print(f"【申请人】{p.get('applicant', 'N/A')}")
        print(f"【IPC分类】{p.get('ipc_main_class', 'N/A')}")
        if p.get('application_date'):
            print(f"【申请日期】{p['application_date']}")
        print("\n【摘要内容】")
        print(f"  {format_abstract(p.get('abstract'))}")

        # 提取技术特征
        text = (p.get('patent_name', '') + ' ' + (p.get('abstract', '') or ''))[:500]
        features = []
        if '焦油' in text:
            features.append("焦油处理")
        if '双' in text:
            features.append("多层/多段结构")
        if '催化' in text:
            features.append("催化技术")
        if '裂解' in text:
            features.append("裂解工艺")
        if features:
            print(f"\n【技术特征】{', '.join(features)}")

        all_patents.append(dict(p))

    # ========== 检索2：双层/双段气化技术 ==========
    print("\n\n" + "=" * 110)
    print("【类别2】双层/双段气化技术专利")
    print("=" * 110)

    cursor.execute("""
        SELECT patent_name, abstract, applicant, ipc_main_class,
               publication_number, application_date
        FROM patents
        WHERE (patent_name LIKE '%双层%' OR patent_name LIKE '%双段%'
           OR abstract LIKE '%双层气化%' OR abstract LIKE '%双段气化%')
           AND abstract IS NOT NULL AND LENGTH(abstract) > 50
        ORDER BY application_date DESC NULLS LAST
        LIMIT 8
    """)

    results = cursor.fetchall()
    for i, p in enumerate(results, 1):
        print(f"\n{'─' * 110}")
        print(f"专利 #{i}")
        print(f"【名称】{p.get('patent_name', 'N/A')}")
        print(f"【公开号】{p.get('publication_number', 'N/A')}")
        print(f"【申请人】{p.get('applicant', 'N/A')}")
        print(f"【IPC分类】{p.get('ipc_main_class', 'N/A')}")
        if p.get('application_date'):
            print(f"【申请日期】{p['application_date']}")
        print("\n【摘要内容】")
        print(f"  {format_abstract(p.get('abstract'))}")

        all_patents.append(dict(p))

    # ========== 检索3：焦油去除/裂解技术 ==========
    print("\n\n" + "=" * 110)
    print("【类别3】焦油去除/裂解技术专利")
    print("=" * 110)

    cursor.execute("""
        SELECT patent_name, abstract, applicant, ipc_main_class,
               publication_number, application_date
        FROM patents
        WHERE (patent_name LIKE '%焦油%' OR abstract LIKE '%焦油%')
           AND (patent_name LIKE '%气化%' OR abstract LIKE '%气化%')
           AND abstract IS NOT NULL AND LENGTH(abstract) > 50
        ORDER BY application_date DESC NULLS LAST
        LIMIT 8
    """)

    results = cursor.fetchall()
    for i, p in enumerate(results, 1):
        print(f"\n{'─' * 110}")
        print(f"专利 #{i}")
        print(f"【名称】{p.get('patent_name', 'N/A')}")
        print(f"【公开号】{p.get('publication_number', 'N/A')}")
        print(f"【申请人】{p.get('applicant', 'N/A')}")
        print(f"【IPC分类】{p.get('ipc_main_class', 'N/A')}")
        if p.get('application_date'):
            print(f"【申请日期】{p['application_date']}")
        print("\n【摘要内容】")
        print(f"  {format_abstract(p.get('abstract'))}")

        all_patents.append(dict(p))

    # ========== 检索4：传统气化炉技术 ==========
    print("\n\n" + "=" * 110)
    print("【类别4】传统气化炉技术专利")
    print("=" * 110)

    cursor.execute("""
        SELECT patent_name, abstract, applicant, ipc_main_class,
               publication_number, application_date
        FROM patents
        WHERE patent_name LIKE '%发生炉%'
           AND abstract IS NOT NULL AND LENGTH(abstract) > 50
        ORDER BY application_date DESC NULLS LAST
        LIMIT 6
    """)

    results = cursor.fetchall()
    for i, p in enumerate(results, 1):
        print(f"\n{'─' * 110}")
        print(f"专利 #{i}")
        print(f"【名称】{p.get('patent_name', 'N/A')}")
        print(f"【公开号】{p.get('publication_number', 'N/A')}")
        print(f"【申请人】{p.get('applicant', 'N/A')}")
        print(f"【IPC分类】{p.get('ipc_main_class', 'N/A')}")
        if p.get('application_date'):
            print(f"【申请日期】{p['application_date']}")
        print("\n【摘要内容】")
        print(f"  {format_abstract(p.get('abstract'))}")

        all_patents.append(dict(p))

    # ========== 技术总结 ==========
    print("\n\n" + "=" * 110)
    print("【技术特征总结】")
    print("=" * 110)

    summary = """
根据检索到的专利摘要，生物质气化发生炉的核心技术特征包括：

一、焦油处理技术
1. 物理吸附法：使用过滤介质吸附气体中的焦油
2. 催化裂解法：喷洒催化剂使焦油催化裂解气化排出
3. 高温裂解法：通过高温使焦油裂解为小分子气体
4. 水洗净化法：用水洗涤去除焦油

二、多层/多段结构设计
1. 双层炉体：上下分层燃烧，上层预热干燥，下层高温气化
2. 双段气化：第一段干燥热解，第二段气化燃烧
3. 多级处理：分级处理提高气化效率

三、进料与配料优化
1. 高压定量给料：精确控制进料量
2. 均匀分散进料：使用分料机构均匀布料
3. 连续进料系统：实现连续稳定供料

四、气化工艺控制
1. 水平衡控制：控制合成气带水量
2. 温度控制：保持最佳气化温度（1100-1200℃）
3. 气化剂选择：空气、氧气、水蒸气及其组合

五、环保与安全
1. 在线堵漏技术：防止合成气泄漏
2. 减碳系统：气化后掺烧减碳
3. 废渣利用：气化细渣制备水煤气
"""

    print(summary)

    # 保存结果
    output_file = f"patent_abstracts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 110 + "\n")
        f.write("生物质气化发生炉相关专利摘要报告\n")
        f.write("=" * 110 + "\n\n")
        f.write(f"报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"专利总数：{len(all_patents)} 条\n\n")
        f.write(summary)
        f.write("\n\n" + "=" * 110 + "\n")
        f.write("专利详情\n")
        f.write("=" * 110 + "\n\n")

        for i, p in enumerate(all_patents, 1):
            f.write(f"\n专利 #{i}\n")
            f.write(f"名称：{p.get('patent_name', 'N/A')}\n")
            f.write(f"公开号：{p.get('publication_number', 'N/A')}\n")
            f.write(f"申请人：{p.get('applicant', 'N/A')}\n")
            f.write(f"IPC分类：{p.get('ipc_main_class', 'N/A')}\n")
            if p.get('application_date'):
                f.write(f"申请日期：{p['application_date']}\n")
            f.write(f"摘要：\n{format_abstract(p.get('abstract'))}\n")
            f.write("-" * 110 + "\n")

    print(f"\n详细报告已保存至：{output_file}")

    cursor.close()
    conn.close()

    print("\n" + "=" * 110)
    print("专利摘要展示完成！")
    print("=" * 110)


if __name__ == "__main__":
    main()
