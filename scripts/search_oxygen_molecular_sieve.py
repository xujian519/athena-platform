#!/usr/bin/env python3
"""
高效制氧机分子筛配方专利检索
Athena工作平台 - 专业专利检索

检索目标：高效制氧机分子筛配方相关专利
检索重点：配方组成、制备方法、材料配比
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


def search_oxygen_molecular_sieve():
    """检索制氧机分子筛配方专利"""

    print_section("🔍 高效制氧机分子筛配方专利检索")
    print(f"检索时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"数据库: localhost:5432/patent_db")

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

        # ========== 检索1: 核心关键词检索（分子筛配方） ==========
        print_section("【检索1】核心关键词：分子筛配方")

        # 核心关键词组合：专门针对配方
        formula_keywords = [
            "分子筛", "配方"
        ]

        print(f"\n检索条件: 关键词 = {formula_keywords}")
        print("检索策略: 专利名称中同时包含'分子筛'和'配方'")

        patents = retriever.search_by_keywords(
            keywords=formula_keywords,
            limit=20,
            require_publication_number=True
        )

        print(f"\n✅ 找到 {len(patents)} 条专利\n")

        for i, p in enumerate(patents[:10], 1):
            print(f"{i}. 【{p.patent_name}】")
            print(f"   申请号: {p.application_number}")
            print(f"   公开号: {p.publication_number}")
            print(f"   申请人: {p.applicant}")
            print(f"   申请日: {p.application_date}")
            if p.abstract:
                abstract_preview = p.abstract[:100] + "..." if len(p.abstract) > 100 else p.abstract
                print(f"   摘要: {abstract_preview}")
            print()

        # 保存结果
        if patents:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = result_dir / f"molecular_sieve_formula_{timestamp}.json"
            export_data = [p.to_dict() for p in patents]
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
            print(f"💾 结果已保存至: {output_file}")

        # ========== 检索2: 制氧机分子筛组合检索 ==========
        print_section("【检索2】关键词：制氧机 + 分子筛")

        oxygen_keywords = [
            "制氧机", "分子筛"
        ]

        print(f"\n检索条件: 关键词 = {oxygen_keywords}")
        print("检索策略: 专利名称中包含'制氧机'和'分子筛'")

        patents = retriever.search_by_keywords(
            keywords=oxygen_keywords,
            limit=20,
            require_publication_number=True
        )

        print(f"\n✅ 找到 {len(patents)} 条专利\n")

        for i, p in enumerate(patents[:10], 1):
            print(f"{i}. 【{p.patent_name}】")
            print(f"   申请号: {p.application_number}")
            print(f"   公开号: {p.publication_number}")
            print(f"   申请人: {p.applicant}")
            print(f"   申请日: {p.application_date}")
            if p.ipc_main_class:
                print(f"   IPC分类: {p.ipc_main_class}")
            print()

        # 保存结果
        if patents:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = result_dir / f"oxygen_molecular_sieve_{timestamp}.json"
            export_data = [p.to_dict() for p in patents]
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
            print(f"💾 结果已保存至: {output_file}")

        # ========== 检索3: 分子筛组成/制备检索 ==========
        print_section("【检索3】关键词：分子筛组成/制备方法")

        composition_keywords = [
            "分子筛", "组成"
        ]

        print(f"\n检索条件: 关键词 = {composition_keywords}")
        print("检索策略: 专利名称中包含'分子筛'和'组成'")

        patents = retriever.search_by_keywords(
            keywords=composition_keywords,
            limit=20,
            require_publication_number=True
        )

        print(f"\n✅ 找到 {len(patents)} 条专利\n")

        for i, p in enumerate(patents[:10], 1):
            print(f"{i}. 【{p.patent_name}】")
            print(f"   申请号: {p.application_number}")
            print(f"   公开号: {p.publication_number}")
            print(f"   申请人: {p.applicant}")
            if p.abstract:
                abstract_preview = p.abstract[:100] + "..." if len(p.abstract) > 100 else p.abstract
                print(f"   摘要: {abstract_preview}")
            print()

        # 保存结果
        if patents:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = result_dir / f"molecular_sieve_composition_{timestamp}.json"
            export_data = [p.to_dict() for p in patents]
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
            print(f"💾 结果已保存至: {output_file}")

        # ========== 检索4: 沸石分子筛检索 ==========
        print_section("【检索4】关键词：沸石分子筛")

        zeolite_keywords = [
            "沸石", "分子筛"
        ]

        print(f"\n检索条件: 关键词 = {zeolite_keywords}")
        print("检索策略: 专利名称中包含'沸石'和'分子筛'")

        patents = retriever.search_by_keywords(
            keywords=zeolite_keywords,
            limit=20,
            require_publication_number=True
        )

        print(f"\n✅ 找到 {len(patents)} 条专利\n")

        for i, p in enumerate(patents[:10], 1):
            print(f"{i}. 【{p.patent_name}】")
            print(f"   申请号: {p.application_number}")
            print(f"   公开号: {p.publication_number}")
            print(f"   申请人: {p.applicant}")
            print(f"   申请日: {p.application_date}")
            print()

        # 保存结果
        if patents:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = result_dir / f"zeolite_molecular_sieve_{timestamp}.json"
            export_data = [p.to_dict() for p in patents]
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
            print(f"💾 结果已保存至: {output_file}")

        # ========== 检索5: 使用SQL直接检索摘要和权利要求 ==========
        print_section("【检索5】深度检索：摘要中包含配方相关内容")

        print("\n检索策略: 在摘要和权利要求中检索'配方'、'组成'、'制备'等关键词")

        deep_search_query = """
            SELECT
                patent_name,
                application_number,
                patent_type,
                publication_number,
                application_date,
                publication_date,
                applicant,
                inventor,
                ipc_main_class,
                ipc_classification,
                abstract,
                claims_content
            FROM patents
            WHERE (
                patent_name ILIKE '%分子筛%'
                OR abstract ILIKE '%分子筛%'
                OR claims_content ILIKE '%分子筛%'
            )
            AND (
                patent_name ILIKE '%配方%'
                OR abstract ILIKE '%配方%'
                OR claims_content ILIKE '%配方%'
                OR patent_name ILIKE '%组成%'
                OR abstract ILIKE '%组成%'
                OR claims_content ILIKE '%组成%'
                OR patent_name ILIKE '%制备%'
                OR abstract ILIKE '%制备%'
                OR claims_content ILIKE '%制备%'
            )
            AND publication_number IS NOT NULL
            ORDER BY application_date DESC
            LIMIT 30
        """

        retriever.cursor.execute(deep_search_query)
        results = retriever.cursor.fetchall()

        col_names = [desc[0] for desc in retriever.cursor.description]
        patents = []

        for result in results:
            patent_dict = dict(zip(col_names, result, strict=False))
            # 使用PatentInfo类来处理（虽然字段可能不完全匹配）
            from core.patent.enhanced_patent_retriever_v2 import PatentInfo
            # 过滤掉不存在的字段
            filtered_dict = {k: v for k, v in patent_dict.items()
                           if k in ['patent_name', 'application_number', 'patent_type',
                                   'publication_number', 'application_date', 'publication_date',
                                   'applicant', 'inventor', 'ipc_main_class', 'ipc_classification',
                                   'abstract', 'claims_content', 'pdf_path', 'pdf_downloaded']}
            # 补充缺失的字段
            if 'pdf_path' not in filtered_dict:
                filtered_dict['pdf_path'] = None
            if 'pdf_downloaded' not in filtered_dict:
                filtered_dict['pdf_downloaded'] = False
            patents.append(PatentInfo(**filtered_dict))

        print(f"\n✅ 深度检索找到 {len(patents)} 条专利\n")

        for i, p in enumerate(patents[:15], 1):
            print(f"{i}. 【{p.patent_name}】")
            print(f"   申请号: {p.application_number}")
            print(f"   公开号: {p.publication_number}")
            print(f"   申请人: {p.applicant}")
            print(f"   申请日: {p.application_date}")
            if p.abstract:
                abstract_preview = p.abstract[:150] + "..." if len(p.abstract) > 150 else p.abstract
                print(f"   摘要: {abstract_preview}")
            print()

        # 保存深度检索结果
        if patents:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = result_dir / f"deep_search_formula_{timestamp}.json"
            export_data = [p.to_dict() for p in patents]
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
            print(f"💾 深度检索结果已保存至: {output_file}")

        # ========== 检索6: 统计分析 ==========
        print_section("【检索6】分子筛专利统计分析")

        stats_query = """
            SELECT
                applicant,
                COUNT(*) as patent_count
            FROM patents
            WHERE patent_name ILIKE '%分子筛%'
               OR abstract ILIKE '%分子筛%'
               OR claims_content ILIKE '%分子筛%'
            GROUP BY applicant
            ORDER BY patent_count DESC
            LIMIT 10
        """

        print("\n📊 分子筛专利申请人Top10:\n")
        retriever.cursor.execute(stats_query)
        results = retriever.cursor.fetchall()

        for i, (applicant, count) in enumerate(results, 1):
            print(f"{i:2d}. {applicant}: {count} 件")

        # ========== 总结 ==========
        print_section("✅ 检索完成")

        summary = f"""
📊 检索总结:
  - 检索主题: 高效制氧机分子筛配方
  - 检索时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
  - 执行检索: 6种不同策略

🔍 检索策略:
  1. 核心关键词：分子筛配方
  2. 组合关键词：制氧机 + 分子筛
  3. 组成相关：分子筛组成
  4. 材料相关：沸石分子筛
  5. 深度检索：摘要和权利要求全文检索
  6. 统计分析：申请人分布

💾 结果保存位置:
  - /Users/xujian/Athena工作平台/data/patents/search_results/

📝 下一步建议:
  - 查看JSON文件获取完整专利信息
  - 筛选出与配方最相关的专利
  - 下载核心专利PDF进行深度分析
  - 使用AI工具进行专利对比分析

⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        print(summary)


if __name__ == "__main__":
    try:
        search_oxygen_molecular_sieve()
    except Exception as e:
        print(f"\n❌ 执行出错: {e}")
        import traceback
        traceback.print_exc()
