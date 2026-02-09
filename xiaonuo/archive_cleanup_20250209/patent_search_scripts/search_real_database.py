#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
连接真实PostgreSQL专利数据库搜索苏东霞电解铝专利
Search for Su Dongxia's Patents in Real Database

连接项目真实的PostgreSQL专利数据库进行搜索

作者: 小娜·天秤女神
创建时间: 2025-12-17
版本: v1.0.0 "真实数据搜索"
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.db_config import get_patent_db_connection
from typing import List, Dict, Any

def search_patents_database():
    """在真实专利数据库中搜索"""
    print("🔍 连接真实PostgreSQL专利数据库")
    print("=" * 60)

    try:
        conn = get_patent_db_connection()
        cursor = conn.cursor()
        print("✅ 数据库连接成功")

        # 1. 检查发明人字段数据情况
        cursor.execute("""
            SELECT COUNT(*) FROM patents
            WHERE source_year BETWEEN 2023 AND 2025
            AND inventor IS NOT NULL
            AND inventor != '';
        """)
        valid_inventor_count = cursor.fetchone()[0]
        print(f"📊 有效发明人字段的专利数量: {valid_inventor_count}")

        # 2. 搜索苏东霞（如果发明人字段有数据）
        cursor.execute("""
            SELECT
                patent_name,
                inventor,
                applicant,
                application_number,
                patent_type,
                application_date,
                abstract,
                ipc_main_class
            FROM patents
            WHERE (inventor LIKE '%苏东霞%' OR applicant LIKE '%苏东霞%')
            AND source_year BETWEEN 2023 AND 2025
            ORDER BY application_date DESC
            LIMIT 10;
        """)
        su_dongxia_patents = cursor.fetchall()

        print(f"\n👤 直接搜索'苏东霞'相关专利: {len(su_dongxia_patents)}项")

        # 3. 搜索电解铝相关专利
        cursor.execute("""
            SELECT
                patent_name,
                inventor,
                applicant,
                application_number,
                patent_type,
                application_date,
                abstract,
                ipc_main_class
            FROM patents
            WHERE (patent_name LIKE '%电解铝%' OR abstract LIKE '%电解铝%')
            AND source_year BETWEEN 2023 AND 2025
            ORDER BY application_date DESC
            LIMIT 20;
        """)
        aluminum_patents = cursor.fetchall()

        print(f"\n⚡ 电解铝相关专利: {len(aluminum_patents)}项")

        # 4. 分离包含'苏'或'东'的专利
        su_aluminum_patents = []
        for patent in aluminum_patents:
            if patent[1] and ('苏' in patent[1] or '东' in patent[1]):
                su_aluminum_patents.append(patent)
            elif patent[2] and ('苏' in patent[2] or '东' in patent[2]):
                su_aluminum_patents.append(patent)

        # 5. 显示搜索结果
        if su_dongxia_patents:
            print(f"\n🎯 找到直接包含'苏东霞'的专利:")
            print("=" * 60)
            for i, patent in enumerate(su_dongxia_patents, 1):
                print(f"\n📄 专利 [{i}]")
                print(f"   名称: {patent[0]}")
                print(f"   发明人: {patent[1] if patent[1] else '未填写'}")
                print(f"   申请人: {patent[2]}")
                print(f"   申请号: {patent[3]}")
                print(f"   类型: {patent[4]}")
                print(f"   申请日期: {patent[5]}")
                print(f"   IPC分类: {patent[7]}")
                if patent[6]:
                    print(f"   摘要: {patent[6][:150]}...")
        else:
            print(f"\n❌ 未找到直接包含'苏东霞'的专利")

        if su_aluminum_patents:
            print(f"\n🎯 包含'苏'或'东'的电解铝相关专利:")
            print("=" * 60)
            for i, patent in enumerate(su_aluminum_patents, 1):
                print(f"\n📄 专利 [{i}]")
                print(f"   名称: {patent[0]}")
                print(f"   发明人: {patent[1] if patent[1] else '未填写'}")
                print(f"   申请人: {patent[2]}")
                print(f"   申请号: {patent[3]}")
                print(f"   类型: {patent[4]}")
                print(f"   申请日期: {patent[5]}")
                print(f"   IPC分类: {patent[7]}")
                if patent[6]:
                    print(f"   摘要: {patent[6][:150]}...")
        else:
            print(f"\n❌ 未找到包含'苏'或'东'的电解铝专利")

        # 6. 显示电解铝专利示例
        print(f"\n⚡ 电解铝专利示例（前5项）:")
        print("=" * 60)
        for i, patent in enumerate(aluminum_patents[:5], 1):
            print(f"\n📄 专利 [{i}]")
            print(f"   名称: {patent[0]}")
            print(f"   发明人: {patent[1] if patent[1] else '未填写'}")
            print(f"   申请人: {patent[2]}")
            print(f"   申请号: {patent[3]}")
            print(f"   类型: {patent[4]}")
            print(f"   申请日期: {patent[5]}")
            print(f"   IPC分类: {patent[7]}")
            if patent[6]:
                print(f"   摘要: {patent[6][:150]}...")

        # 7. 数据统计分析
        print(f"\n📊 数据库统计分析")
        print("=" * 60)

        # 总专利数
        cursor.execute("SELECT COUNT(*) FROM patents WHERE source_year BETWEEN 2023 AND 2025;")
        total_count = cursor.fetchone()[0]
        print(f"   2023-2025年专利总数: {total_count:,}")

        # 电解铝专利按类型分布
        cursor.execute("""
            SELECT patent_type, COUNT(*)
            FROM patents
            WHERE (patent_name LIKE '%电解铝%' OR abstract LIKE '%电解铝%')
            AND source_year BETWEEN 2023 AND 2025
            GROUP BY patent_type;
        """)
        type_dist = cursor.fetchall()
        print(f"   电解铝专利类型分布:")
        for pt, count in type_dist:
            print(f"     - {pt}: {count}项")

        # 电解铝专利按年分布
        cursor.execute("""
            SELECT source_year, COUNT(*)
            FROM patents
            WHERE (patent_name LIKE '%电解铝%' OR abstract LIKE '%电解铝%')
            AND source_year BETWEEN 2023 AND 2025
            GROUP BY source_year ORDER BY source_year;
        """)
        year_dist = cursor.fetchall()
        print(f"   电解铝专利年度分布:")
        for year, count in year_dist:
            print(f"     - {year}年: {count}项")

        # 搜索建议
        print(f"\n💡 搜索建议:")
        if valid_inventor_count == 0:
            print("   ⚠️ 发明人字段数据缺失，建议:")
            print("      1. 检查数据导入过程是否正确处理发明人信息")
            print("      2. 查看原始数据文件中发明人信息格式")
            print("      3. 考虑从申请人信息中进行推断")

        if len(su_dongxia_patents) == 0:
            print("   ❌ 未找到苏东霞相关专利，可能原因:")
            print("      1. 发明人姓名格式可能不同（如：苏冬霞、苏东霞等变体）")
            print("      2. 发明人可能作为申请人出现")
            print("      3. 时间范围可能需要调整")
            print("      4. 发明人信息可能记录在其他字段")

        print(f"\n🌟 真实数据库搜索完成！")

        conn.close()

    except Exception as e:
        print(f"❌ 数据库搜索出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    search_patents_database()