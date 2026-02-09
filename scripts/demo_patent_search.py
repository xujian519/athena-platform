#!/usr/bin/env python3
"""
中国专利数据库检索演示
Athena工作平台 - 专利检索工作流程演示
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.patent.enhanced_patent_retriever_v2 import EnhancedPatentRetriever


def print_section(title: str):
    """打印分节标题"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_result(label: str, content: str):
    """打印结果标签和内容"""
    print(f"\n{label}")
    print("-" * 80)
    print(content)


def demo_patent_search():
    """专利检索演示主函数"""

    print_section("🔍 中国专利数据库检索演示")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"数据库: localhost:5432/patent_db")
    print(f"专利总数: 75,217,242 条")

    # 准备结果保存目录
    result_dir = Path("/Users/xujian/Athena工作平台/data/patents/search_results")
    result_dir.mkdir(parents=True, exist_ok=True)

    # 初始化检索器
    db_config = {
        "host": "localhost",
        "port": 5432,
        "database": "patent_db",
        "user": "postgres",
        "password": "postgres",
    }

    with EnhancedPatentRetriever(db_config) as retriever:

        # ========== 检索1: 按申请号精确检索 ==========
        print_section("【检索1】按申请号精确检索")

        application_number = "CN202310123456.7"
        print(f"\n检索条件: 申请号 = {application_number}")

        patent = retriever.search_by_application_number(application_number)

        if patent:
            print_result("检索结果", patent.to_summary())

            # 保存结果

            output_file = result_dir / f"search_by_application_number_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(patent.to_dict(), f, ensure_ascii=False, indent=2, default=str)
            print(f"\n💾 结果已保存至: {output_file}")
        else:
            print("未找到匹配的专利")

        # ========== 检索2: 按关键词检索 ==========
        print_section("【检索2】按关键词检索")

        keywords = ["人工智能", "深度学习", "神经网络"]
        print(f"\n检索条件: 关键词 = {keywords}")
        print("限制: 10条结果，要求有公开号")

        patents = retriever.search_by_keywords(
            keywords=keywords,
            limit=10,
            require_publication_number=True
        )

        print_result("检索结果摘要", f"找到 {len(patents)} 条专利\n")

        for i, p in enumerate(patents[:5], 1):
            print(f"{i}. 【{p.patent_name}】")
            print(f"   申请号: {p.application_number}")
            print(f"   公开号: {p.publication_number}")
            print(f"   申请人: {p.applicant}")
            print(f"   申请日: {p.application_date}")
            print(f"   IPC分类: {p.ipc_main_class}")
            print()

        # 保存结果
        if patents:
            output_file = result_dir / f"search_by_keywords_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            export_data = [p.to_dict() for p in patents]
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
            print(f"💾 结果已保存至: {output_file}")

        # ========== 检索3: 按申请人检索 ==========
        print_section("【检索3】按申请人检索")

        applicant = "华为"
        print(f"\n检索条件: 申请人包含 '{applicant}'")
        print("限制: 5条结果")

        patents = retriever.search_by_applicant(
            applicant=applicant,
            limit=5,
            require_publication_number=True
        )

        print_result("检索结果摘要", f"找到 {len(patents)} 条专利\n")

        for i, p in enumerate(patents, 1):
            print(f"{i}. 【{p.patent_name}】")
            print(f"   申请号: {p.application_number}")
            print(f"   申请人: {p.applicant}")
            print(f"   发明人: {p.inventor}")
            print(f"   IPC分类: {p.ipc_main_class}")
            print()

        # 保存结果
        if patents:
            output_file = result_dir / f"search_by_applicant_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            export_data = [p.to_dict() for p in patents]
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
            print(f"💾 结果已保存至: {output_file}")

        # ========== 检索4: 统计分析 ==========
        print_section("【检索4】数据库统计分析")

        # 使用原始SQL查询获取统计信息
        stats_queries = {
            "按专利类型统计": """
                SELECT patent_type, COUNT(*) as count
                FROM patents
                GROUP BY patent_type
                ORDER BY count DESC
            """,
            "按年份统计(最近5年)": """
                SELECT source_year, COUNT(*) as count
                FROM patents
                WHERE source_year >= 2020
                GROUP BY source_year
                ORDER BY source_year DESC
            """,
            "按IPC主分类统计(Top10)": """
                SELECT ipc_main_class, COUNT(*) as count
                FROM patents
                WHERE ipc_main_class IS NOT NULL
                GROUP BY ipc_main_class
                ORDER BY count DESC
                LIMIT 10
            """,
            "申请人统计(Top10)": """
                SELECT applicant, COUNT(*) as count
                FROM patents
                WHERE applicant IS NOT NULL
                GROUP BY applicant
                ORDER BY count DESC
                LIMIT 10
            """
        }

        for title, query in stats_queries.items():
            print(f"\n{title}")
            print("-" * 80)
            retriever.cursor.execute(query)
            results = retriever.cursor.fetchall()

            if results:
                col_names = [desc[0] for desc in retriever.cursor.description]
                for row in results:
                    print(f"  {' | '.join(str(v) for v in row)}")

        # ========== 总结 ==========
        print_section("✅ 检索演示完成")

        summary = f"""
📊 数据库信息:
  - 数据库: localhost:5432/patent_db
  - 专利总数: 75,217,242 条
  - 包含字段: 40+ 个
  - 向量嵌入: 768维 BERT向量

🔍 支持的检索方式:
  1. 按申请号精确检索
  2. 按关键词模糊匹配
  3. 按申请人检索
  4. 按IPC分类检索
  5. 向量语义检索(需要额外配置)

💾 结果保存位置:
  - /Users/xujian/Athena工作平台/data/patents/search_results/

📝 工作流程记录:
  - 连接数据库 ✅
  - 执行多种检索 ✅
  - 统计分析 ✅
  - 保存结果 ✅

⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        print(summary)


if __name__ == "__main__":
    try:
        demo_patent_search()
    except Exception as e:
        print(f"\n❌ 执行出错: {e}")
        import traceback
        traceback.print_exc()
