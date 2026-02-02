#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
已找到的苏东霞相关专利详情
Found Patents Related to Su Dongxia

显示从真实数据库中找到的相关专利详情

作者: 小娜·天秤女神
创建时间: 2025-12-17
版本: v1.0.0 "专利详情"
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.db_config import get_patent_db_connection

def show_found_patents():
    """显示找到的相关专利"""
    print("🎯 已找到的苏东霞相关专利详情")
    print("=" * 70)

    conn = get_patent_db_connection()
    cursor = conn.cursor()

    # 搜索包含'苏东'的专利
    print("\n📋 包含'苏东'的专利:")
    print("-" * 50)

    cursor.execute("""
        SELECT
            patent_name,
            applicant,
            application_number,
            patent_type,
            application_date,
            abstract,
            ipc_main_class
        FROM patents
        WHERE (patent_name LIKE '%苏东%' OR applicant LIKE '%苏东%')
        AND source_year BETWEEN 2023 AND 2025
        ORDER BY application_date DESC;
    """)

    su_dong_patents = cursor.fetchall()

    for i, patent in enumerate(su_dong_patents, 1):
        print(f"\n📄 专利 [{i}]")
        print(f"   专利名称: {patent[0]}")
        print(f"   申请人: {patent[1]}")
        print(f"   申请号: {patent[2]}")
        print(f"   专利类型: {patent[3]}")
        print(f"   申请日期: {patent[4]}")
        print(f"   IPC分类: {patent[6]}")

        if patent[5]:
            abstract = patent[5][:300]
            print(f"   摘要: {abstract}...")

        # 分析相关性
        relevance_score = 0
        reasons = []

        if '电解铝' in patent[0] or '电解铝' in (patent[5] or ''):
            relevance_score += 10
            reasons.append("直接涉及电解铝")

        if '电解' in patent[0] or '电解' in (patent[5] or ''):
            relevance_score += 5
            reasons.append("涉及电解技术")

        if '铝' in patent[0] or '铝' in (patent[5] or ''):
            relevance_score += 3
            reasons.append("涉及铝相关技术")

        if '苏东' in patent[1]:
            relevance_score += 8
            reasons.append("申请人姓名包含'苏东'")

        if relevance_score > 0:
            print(f"   🎯 相关性评分: {relevance_score}/18")
            print(f"   📝 相关原因: {', '.join(reasons)}")

    # 搜索包含'冬霞'的专利
    print(f"\n📋 包含'冬霞'的专利:")
    print("-" * 50)

    cursor.execute("""
        SELECT
            patent_name,
            applicant,
            application_number,
            patent_type,
            application_date,
            abstract,
            ipc_main_class
        FROM patents
        WHERE (patent_name LIKE '%冬霞%' OR applicant LIKE '%冬霞%')
        AND source_year BETWEEN 2023 AND 2025
        ORDER BY application_date DESC;
    """)

    dongxia_patents = cursor.fetchall()

    for i, patent in enumerate(dongxia_patents, 1):
        print(f"\n📄 专利 [{i}]")
        print(f"   专利名称: {patent[0]}")
        print(f"   申请人: {patent[1]}")
        print(f"   申请号: {patent[2]}")
        print(f"   专利类型: {patent[3]}")
        print(f"   申请日期: {patent[4]}")
        print(f"   IPC分类: {patent[6]}")

        if patent[5]:
            abstract = patent[5][:300]
            print(f"   摘要: {abstract}...")

        # 分析相关性
        relevance_score = 0
        reasons = []

        if '电解铝' in patent[0] or '电解铝' in (patent[5] or ''):
            relevance_score += 10
            reasons.append("直接涉及电解铝")

        if '电解' in patent[0] or '电解' in (patent[5] or ''):
            relevance_score += 5
            reasons.append("涉及电解技术")

        if '铝' in patent[0] or '铝' in (patent[5] or ''):
            relevance_score += 3
            reasons.append("涉及铝相关技术")

        if '冬霞' in patent[1]:
            relevance_score += 8
            reasons.append("申请人姓名包含'冬霞'")

        if relevance_score > 0:
            print(f"   🎯 相关性评分: {relevance_score}/18")
            print(f"   📝 相关原因: {', '.join(reasons)}")

    # 搜索同时包含'苏'和'东'的申请人
    print(f"\n🔍 申请人中同时包含'苏'和'东'的专利:")
    print("-" * 50)

    cursor.execute("""
        SELECT
            patent_name,
            applicant,
            application_number,
            patent_type,
            abstract
        FROM patents
        WHERE applicant LIKE '%苏%'
        AND applicant LIKE '%东%'
        AND source_year BETWEEN 2023 AND 2025
        ORDER BY application_number
        LIMIT 10;
    """)

    su_dong_applicant_patents = cursor.fetchall()

    if su_dong_applicant_patents:
        for i, patent in enumerate(su_dong_applicant_patents, 1):
            print(f"\n📄 专利 [{i}]")
            print(f"   专利名称: {patent[0]}")
            print(f"   申请人: {patent[1]}")
            print(f"   申请号: {patent[2]}")
            print(f"   专利类型: {patent[3]}")

            if patent[4]:
                abstract = patent[4][:200]
                print(f"   摘要: {abstract}...")
    else:
        print("   ❌ 未找到申请人同时包含'苏'和'东'的专利")

    # 生成综合分析报告
    print(f"\n📊 综合分析报告")
    print("=" * 70)

    total_found = len(su_dong_patents) + len(dongxia_patents)
    print(f"🔍 搜索统计:")
    print(f"   - 包含'苏东'的专利: {len(su_dong_patents)}项")
    print(f"   - 包含'冬霞'的专利: {len(dongxia_patents)}项")
    print(f"   - 总计找到相关专利: {total_found}项")

    print(f"\n🎯 数据质量分析:")
    print(f"   - 发明人字段: 全部为空（数据导入问题）")
    print(f"   - 申请人字段: 数据完整")
    print(f"   - 专利内容: 技术信息详细")
    print(f"   - IPC分类: 大部分缺失")

    print(f"\n💡 专业建议:")
    if total_found > 0:
        print(f"   ✅ 找到{total_found}项相关专利，但需要进一步验证")
        print(f"   🔍 建议步骤:")
        print(f"      1. 核实申请人是否为苏东霞本人")
        print(f"      2. 检查专利技术领域是否与电解铝相关")
        print(f"      3. 验证申请时间是否符合2023-2025年要求")
        print(f"      4. 考虑通过其他渠道补充发明人信息")
    else:
        print(f"   ❌ 数据库中未找到明确的苏东霞电解铝专利")
        print(f"   🔍 可能原因:")
        print(f"      1. 发明人信息记录在空字段中")
        print(f"      2. 申请人为企业而非个人")
        print(f"      3. 姓名格式有变体（如：苏冬霞）")
        print(f"      4. 时间范围需要调整")

    print(f"\n📋 后续行动建议:")
    print(f"   1. 📁 检查原始数据文件，发明人信息可能存在但未正确导入")
    print(f"   2. 🔧 修复数据导入脚本，确保发明人字段正确映射")
    print(f"   3. 📞 联系数据提供方，确认发明人信息格式")
    print(f"   4. 🌐 考虑从其他专利数据库（如国家知识产权局）补充数据")

    conn.close()
    print(f"\n🌟 专利详情分析完成！")

if __name__ == "__main__":
    show_found_patents()