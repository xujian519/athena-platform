#!/usr/bin/env python3
"""
快速检索：制氧机分子筛配方专利
"""

import json
import sys
import psycopg2
from datetime import datetime
from pathlib import Path

def main():
    # 数据库配置
    db_config = {
        "host": "localhost",
        "port": 5432,
        "database": "patent_db",
        "user": "postgres",
        "password": "postgres",
    }

    # 结果目录
    result_dir = Path("/Users/xujian/Athena工作平台/data/patents/search_results")
    result_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("高效制氧机分子筛配方专利检索")
    print("=" * 80)
    print(f"检索时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        print("✅ 数据库连接成功\n")

        # 检索1：分子筛 + 配方
        print("-" * 80)
        print("【检索1】关键词：分子筛 + 配方")
        print("-" * 80)

        query1 = """
            SELECT patent_name, application_number, publication_number,
                   applicant, application_date, abstract
            FROM patents
            WHERE patent_name ILIKE '%分子筛%'
              AND patent_name ILIKE '%配方%'
              AND publication_number IS NOT NULL
            ORDER BY application_date DESC
            LIMIT 20
        """

        cursor.execute(query1)
        results1 = cursor.fetchall()

        print(f"找到 {len(results1)} 条专利:\n")
        for i, r in enumerate(results1[:10], 1):
            print(f"{i}. {r[0]}")
            print(f"   申请号: {r[1]} | 公开号: {r[2]}")
            print(f"   申请人: {r[3]} | 申请日: {r[4]}")
            if r[5]:
                abstract = r[5][:100] + "..." if len(r[5]) > 100 else r[5]
                print(f"   摘要: {abstract}")
            print()

        # 保存结果1
        if results1:
            col_names = ['patent_name', 'application_number', 'publication_number',
                        'applicant', 'application_date', 'abstract']
            export1 = [dict(zip(col_names, r)) for r in results1]
            output1 = result_dir / f"分子筛配方_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output1, "w", encoding="utf-8") as f:
                json.dump(export1, f, ensure_ascii=False, indent=2, default=str)
            print(f"💾 已保存: {output1}\n")

        # 检索2：制氧机 + 分子筛
        print("-" * 80)
        print("【检索2】关键词：制氧机 + 分子筛")
        print("-" * 80)

        query2 = """
            SELECT patent_name, application_number, publication_number,
                   applicant, application_date, ipc_main_class, abstract
            FROM patents
            WHERE patent_name ILIKE '%制氧机%'
              AND patent_name ILIKE '%分子筛%'
              AND publication_number IS NOT NULL
            ORDER BY application_date DESC
            LIMIT 20
        """

        cursor.execute(query2)
        results2 = cursor.fetchall()

        print(f"找到 {len(results2)} 条专利:\n")
        for i, r in enumerate(results2[:10], 1):
            print(f"{i}. {r[0]}")
            print(f"   申请号: {r[1]} | 公开号: {r[2]}")
            print(f"   申请人: {r[3]} | 申请日: {r[4]}")
            if r[5]:
                print(f"   IPC分类: {r[5]}")
            print()

        # 保存结果2
        if results2:
            col_names = ['patent_name', 'application_number', 'publication_number',
                        'applicant', 'application_date', 'ipc_main_class', 'abstract']
            export2 = [dict(zip(col_names, r)) for r in results2]
            output2 = result_dir / f"制氧机分子筛_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output2, "w", encoding="utf-8") as f:
                json.dump(export2, f, ensure_ascii=False, indent=2, default=str)
            print(f"💾 已保存: {output2}\n")

        # 检索3：深度检索（摘要和权利要求）
        print("-" * 80)
        print("【检索3】深度检索：分子筛 + 配方/组成/制备（全文）")
        print("-" * 80)

        query3 = """
            SELECT patent_name, application_number, publication_number,
                   applicant, application_date, abstract
            FROM patents
            WHERE (patent_name ILIKE '%分子筛%'
                   OR abstract ILIKE '%分子筛%')
              AND (patent_name ILIKE '%配方%'
                   OR abstract ILIKE '%配方%'
                   OR patent_name ILIKE '%组成%'
                   OR abstract ILIKE '%组成%'
                   OR patent_name ILIKE '%制备%'
                   OR abstract ILIKE '%制备%')
              AND publication_number IS NOT NULL
            ORDER BY application_date DESC
            LIMIT 30
        """

        cursor.execute(query3)
        results3 = cursor.fetchall()

        print(f"找到 {len(results3)} 条专利:\n")
        for i, r in enumerate(results3[:15], 1):
            print(f"{i}. {r[0]}")
            print(f"   申请号: {r[1]} | 公开号: {r[2]}")
            print(f"   申请人: {r[3]} | 申请日: {r[4]}")
            if r[5]:
                abstract = r[5][:120] + "..." if len(r[5]) > 120 else r[5]
                print(f"   摘要: {abstract}")
            print()

        # 保存结果3
        if results3:
            col_names = ['patent_name', 'application_number', 'publication_number',
                        'applicant', 'application_date', 'abstract']
            export3 = [dict(zip(col_names, r)) for r in results3]
            output3 = result_dir / f"深度检索_分子筛配方_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output3, "w", encoding="utf-8") as f:
                json.dump(export3, f, ensure_ascii=False, indent=2, default=str)
            print(f"💾 已保存: {output3}\n")

        # 检索4：沸石分子筛
        print("-" * 80)
        print("【检索4】关键词：沸石分子筛")
        print("-" * 80)

        query4 = """
            SELECT patent_name, application_number, publication_number,
                   applicant, application_date, abstract
            FROM patents
            WHERE patent_name ILIKE '%沸石%'
              AND patent_name ILIKE '%分子筛%'
              AND publication_number IS NOT NULL
            ORDER BY application_date DESC
            LIMIT 20
        """

        cursor.execute(query4)
        results4 = cursor.fetchall()

        print(f"找到 {len(results4)} 条专利:\n")
        for i, r in enumerate(results4[:10], 1):
            print(f"{i}. {r[0]}")
            print(f"   申请号: {r[1]} | 公开号: {r[2]}")
            print(f"   申请人: {r[3]} | 申请日: {r[4]}")
            print()

        # 保存结果4
        if results4:
            col_names = ['patent_name', 'application_number', 'publication_number',
                        'applicant', 'application_date', 'abstract']
            export4 = [dict(zip(col_names, r)) for r in results4]
            output4 = result_dir / f"沸石分子筛_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output4, "w", encoding="utf-8") as f:
                json.dump(export4, f, ensure_ascii=False, indent=2, default=str)
            print(f"💾 已保存: {output4}\n")

        # 统计分析
        print("-" * 80)
        print("【统计分析】分子筛专利申请人Top10")
        print("-" * 80)

        stats_query = """
            SELECT applicant, COUNT(*) as count
            FROM patents
            WHERE patent_name ILIKE '%分子筛%'
            GROUP BY applicant
            ORDER BY count DESC
            LIMIT 10
        """

        cursor.execute(stats_query)
        stats_results = cursor.fetchall()

        print("\n申请人排名:\n")
        for i, (applicant, count) in enumerate(stats_results, 1):
            print(f"{i:2d}. {applicant}: {count} 件")

        # 总结
        print("\n" + "=" * 80)
        print("检索完成")
        print("=" * 80)
        print(f"\n📊 检索统计:")
        print(f"   - 分子筛配方: {len(results1)} 件")
        print(f"   - 制氧机分子筛: {len(results2)} 件")
        print(f"   - 深度检索: {len(results3)} 件")
        print(f"   - 沸石分子筛: {len(results4)} 件")
        print(f"\n💾 所有结果已保存至: {result_dir}")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
