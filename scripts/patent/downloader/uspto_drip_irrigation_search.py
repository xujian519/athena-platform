#!/usr/bin/env python3
"""
USPTO滴灌技术专利检索脚本
搜索滴灌过滤器/滴头相关的自清洁、反冲洗、烧结滤芯专利
"""
import json
import os
from datetime import datetime
from typing import Any

import requests

# USPTO PatentSearch API配置
PATENTSEARCH_BASE_URL = "https://search.patentsview.org/api/v1/patent"
USPTO_API_KEY = os.getenv("USPTO_API_KEY", "")

def search_drip_irrigation_filters() -> dict[str, Any]:
    """
    搜索滴灌技术领域的过滤器专利

    检索策略：
    1. 滴灌(drip irrigation) + 过滤器(filter)
    2. 滴头(emitter) + 自清洁/反冲洗
    3. 微灌(micro irrigation) + 过滤
    """
    headers = {
        "X-Api-Key": USPTO_API_KEY,
        "Content-Type": "application/json"
    }

    # 构建复杂查询：滴灌 + (过滤器 OR 滴头) + (自清洁 OR 反冲洗 OR 烧结)
    query = {
        "q": {
            "_and": [
                {
                    "_or": [
                        {"patent_title": {"_text_any": ["drip", "irrigation", "micro"]}},
                        {"patent_abstract": {"_text_any": ["drip", "irrigation", "micro"]}},
                        {"brief_summary_text": {"_text_any": ["drip", "irrigation", "micro"]}},
                        {"detail_description_text": {"_text_any": ["drip", "irrigation", "micro"]}}
                    ]
                },
                {
                    "_or": [
                        {"patent_title": {"_text_any": ["filter", "emitter", "nozzle"]}},
                        {"patent_abstract": {"_text_any": ["filter", "emitter", "nozzle", "filtration"]}},
                        {"brief_summary_text": {"_text_any": ["filter", "emitter", "nozzle"]}},
                        {"detail_description_text": {"_text_any": ["filter", "emitter", "nozzle", "filtration"]}}
                    ]
                }
            ]
        },
        "f": [
            "patent_number",
            "patent_title",
            "patent_date",
            "patent_abstract",
            "cpc_subclass_id",
            "assignee_organization",
            "inventor_name"
        ],
        "s": [{"patent_date": "desc"}],
        "o": {"per_page": 50, "page": 1}
    }

    print("正在检索USPTO专利数据库...")
    print("查询条件: 滴灌 + (过滤器/滴头)")

    try:
        response = requests.post(PATENTSEARCH_BASE_URL, headers=headers, json=query, timeout=60)
        response.raise_for_status()
        results = response.json()

        patents = results.get('patents', [])
        print(f"\n找到 {len(patents)} 件相关专利\n")

        return {"query": "drip_irrigation_filter", "patents": patents}

    except requests.exceptions.RequestException as e:
        print(f"检索失败: {e}")
        return {"query": "drip_irrigation_filter", "patents": [], "error": str(e)}

def search_backwash_selfcleaning() -> dict[str, Any]:
    """
    搜索反冲洗/自清洁相关的滴灌专利
    """
    headers = {
        "X-Api-Key": USPTO_API_KEY,
        "Content-Type": "application/json"
    }

    # 搜索滴灌 + 自清洁/反冲洗
    query = {
        "q": {
            "_and": [
                {
                    "_or": [
                        {"patent_title": {"_text_any": ["drip", "irrigation"]}},
                        {"patent_abstract": {"_text_any": ["drip", "irrigation"]}}
                    ]
                },
                {
                    "_or": [
                        {"patent_title": {"_text_any": ["backwash", "self-clean", "selfclean", "automatic clean"]}},
                        {"patent_abstract": {"_text_any": ["backwash", "self-clean", "selfclean", "automatic clean", "auto clean"]}},
                        {"brief_summary_text": {"_text_any": ["backwash", "self-clean"]}}
                    ]
                }
            ]
        },
        "f": [
            "patent_number",
            "patent_title",
            "patent_date",
            "patent_abstract",
            "cpc_subclass_id",
            "assignee_organization"
        ],
        "s": [{"patent_date": "desc"}],
        "o": {"per_page": 50, "page": 1}
    }

    print("正在检索USPTO专利数据库...")
    print("查询条件: 滴灌 + (自清洁/反冲洗)")

    try:
        response = requests.post(PATENTSEARCH_BASE_URL, headers=headers, json=query, timeout=60)
        response.raise_for_status()
        results = response.json()

        patents = results.get('patents', [])
        print(f"\n找到 {len(patents)} 件相关专利\n")

        return {"query": "drip_irrigation_backwash", "patents": patents}

    except requests.exceptions.RequestException as e:
        print(f"检索失败: {e}")
        return {"query": "drip_irrigation_backwash", "patents": [], "error": str(e)}

def search_sintered_porous() -> dict[str, Any]:
    """
    搜索烧结/多孔滤芯相关的滴灌专利
    """
    headers = {
        "X-Api-Key": USPTO_API_KEY,
        "Content-Type": "application/json"
    }

    # 搜索滴灌 + 烧结/多孔
    query = {
        "q": {
            "_and": [
                {
                    "_or": [
                        {"patent_title": {"_text_any": ["drip", "irrigation", "emitter"]}},
                        {"patent_abstract": {"_text_any": ["drip", "irrigation", "emitter"]}}
                    ]
                },
                {
                    "_or": [
                        {"patent_title": {"_text_any": ["sinter", "porous", "sintered"]}},
                        {"patent_abstract": {"_text_any": ["sinter", "porous", "sintered", "pore"]}}
                    ]
                }
            ]
        },
        "f": [
            "patent_number",
            "patent_title",
            "patent_date",
            "patent_abstract",
            "cpc_subclass_id",
            "assignee_organization"
        ],
        "s": [{"patent_date": "desc"}],
        "o": {"per_page": 50, "page": 1}
    }

    print("正在检索USPTO专利数据库...")
    print("查询条件: 滴灌 + (烧结/多孔)")

    try:
        response = requests.post(PATENTSEARCH_BASE_URL, headers=headers, json=query, timeout=60)
        response.raise_for_status()
        results = response.json()

        patents = results.get('patents', [])
        print(f"\n找到 {len(patents)} 件相关专利\n")

        return {"query": "drip_irrigation_sintered", "patents": patents}

    except requests.exceptions.RequestException as e:
        print(f"检索失败: {e}")
        return {"query": "drip_irrigation_sintered", "patents": [], "error": str(e)}

def format_patent_info(patent: dict[str, Any]) -> str:
    """格式化专利信息"""
    number = patent.get('patent_number', 'N/A')
    title = patent.get('patent_title', 'N/A')
    date = patent.get('patent_date', 'N/A')
    abstract = patent.get('patent_abstract', '')

    # 截取摘要前200字符
    abstract_short = abstract[:200] + "..." if abstract and len(abstract) > 200 else abstract or ''

    assignee = patent.get('assignee_organization', ['N/A'])[0] if patent.get('assignee_organization') else 'N/A'

    output = f"""
{'='*70}
专利号: {number}
标题: {title}
授权日: {date}
申请人: {assignee}
摘要: {abstract_short}
"""
    return output

def save_results(all_results: list[dict[str, Any]) -> None:
    """保存检索结果到文件"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = "/Users/xujian/Athena工作平台/data/patents_verify"

    # 保存JSON格式
    json_file = f"{output_dir}/uspto_drip_irrigation_search_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\n✅ JSON结果已保存到: {json_file}")

    # 保存Markdown格式
    md_file = f"{output_dir}/uspto_drip_irrigation_search_{timestamp}.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write("# USPTO滴灌技术专利检索报告\n\n")
        f.write(f"**检索时间**: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}\n\n")
        f.write("**检索范围**: 美国专利数据库 (USPTO)\n\n")
        f.write("---\n\n")

        for result in all_results:
            f.write(f"## 检索式: {result['query']}\n\n")
            f.write(f"找到 {len(result.get('patents', []))} 件相关专利\n\n")

            for patent in result.get('patents', []):
                number = patent.get('patent_number', 'N/A')
                title = patent.get('patent_title', 'N/A')
                date = patent.get('patent_date', 'N/A')
                abstract = patent.get('patent_abstract', '')
                assignee = patent.get('assignee_organization', ['N/A'])[0] if patent.get('assignee_organization') else 'N/A'

                f.write(f"### {number} - {title}\n\n")
                f.write(f"- **授权日**: {date}\n")
                f.write(f"- **申请人**: {assignee}\n")
                f.write(f"- **摘要**: {abstract[:500]}...\n\n")

            f.write("---\n\n")

    print(f"✅ Markdown报告已保存到: {md_file}")

def main():
    """主函数"""
    print("="*70)
    print("USPTO滴灌技术专利检索")
    print("="*70)

    all_results = []

    # 执行三个检索
    searches = [
        ("滴灌过滤器专利", search_drip_irrigation_filters),
        ("滴灌反冲洗/自清洁专利", search_backwash_selfcleaning),
        ("滴灌烧结/多孔滤芯专利", search_sintered_porous)
    ]

    for search_name, search_func in searches:
        print(f"\n{'='*70}")
        print(f"检索: {search_name}")
        print(f"{'='*70}\n")

        result = search_func()
        all_results.append(result)

        if result.get('patents'):
            print("\n前10件专利:\n")
            for patent in result['patents'][:10]:
                print(format_patent_info(patent))

    # 保存结果
    save_results(all_results)

    # 统计分析
    print(f"\n{'='*70}")
    print("检索统计")
    print(f"{'='*70}")

    total_patents = sum(len(r.get('patents', [])) for r in all_results)
    print(f"\n总计找到 {total_patents} 件相关专利")

    for result in all_results:
        query = result['query']
        count = len(result.get('patents', []))
        print(f"  - {query}: {count} 件")

    print(f"\n{'='*70}\n")

if __name__ == "__main__":
    main()
