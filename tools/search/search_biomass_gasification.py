#!/usr/bin/env python3
"""
生物质气化发生炉专利检索脚本
检索关于生物质气化的发生炉技术，特别是上下双火层、上火层去除煤焦油的技术
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
from datetime import datetime
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor

from config.database import get_patent_connection_params


class BiomassGasificationRetriever:
    """生物质气化发生炉专利检索器"""

    def __init__(self):
        """初始化数据库连接"""
        conn_params = get_patent_connection_params()
        conn_params['cursor_factory'] = RealDictCursor
        self.conn = psycopg2.connect(**conn_params)
        self.cursor = self.conn.cursor()

    def search_patents(self, query_keywords: list[str], limit: int = 50) -> list[dict[str, Any]]:
        """
        使用PostgreSQL全文搜索检索专利

        Args:
            query_keywords: 检索关键词列表
            limit: 返回结果数量

        Returns:
            检索结果列表
        """
        # 构建检索式 - 使用AND逻辑组合所有关键词
        search_query = " & ".join(query_keywords)

        # 使用PostgreSQL全文搜索
        sql = """
        SELECT
            patent_name as title,
            abstract,
            claims,
            claims_content,
            ipc_classification,
            applicant,
            inventor,
            application_date,
            publication_number,
            application_number,
            authorization_number,
            ts_rank_cd(
                search_vector,
                plainto_tsquery('chinese', %s)
            ) as relevance_score,
            ts_headline('chinese', patent_name, plainto_tsquery('chinese', %s),
                       'MaxWords=100, MinWords=30, ShortWord=3') as title_highlight,
            ts_headline('chinese', abstract, plainto_tsquery('chinese', %s),
                       'MaxWords=200, MinWords=50, ShortWord=3') as abstract_highlight
        FROM patents
        WHERE search_vector @@ plainto_tsquery('chinese', %s)
        ORDER BY relevance_score DESC
        LIMIT %s
        """

        self.cursor.execute(sql, (*([search_query] * 3), search_query, limit))
        results = self.cursor.fetchall()

        return [dict(row) for row in results]

    def search_with_or_logic(self, query_groups: list[list[str]], limit: int = 50) -> list[dict[str, Any]]:
        """
        使用OR逻辑组合检索 - 检索包含任意一组关键词的专利

        Args:
            query_groups: 关键词组列表，每个组内使用AND逻辑，组间使用OR逻辑
            limit: 返回结果数量

        Returns:
            检索结果列表
        """
        # 构建复杂的检索式
        group_queries = []
        for group in query_groups:
            if group:
                group_query = " & ".join(group)
                group_queries.append(f"({group_query})")

        if not group_queries:
            return []

        search_query = " | ".join(group_queries)

        sql = """
        SELECT
            patent_name as title,
            abstract,
            claims,
            claims_content,
            ipc_classification,
            applicant,
            inventor,
            application_date,
            publication_number,
            application_number,
            authorization_number,
            ts_rank_cd(
                search_vector,
                plainto_tsquery('chinese', %s)
            ) as relevance_score,
            ts_headline('chinese', patent_name, plainto_tsquery('chinese', %s),
                       'MaxWords=100, MinWords=30, ShortWord=3') as title_highlight,
            ts_headline('chinese', abstract, plainto_tsquery('chinese', %s),
                       'MaxWords=200, MinWords=50, ShortWord=3') as abstract_highlight
        FROM patents
        WHERE search_vector @@ plainto_tsquery('chinese', %s)
        ORDER BY relevance_score DESC
        LIMIT %s
        """

        self.cursor.execute(sql, (*([search_query] * 3), search_query, limit))
        results = self.cursor.fetchall()

        return [dict(row) for row in results]

    def close(self):
        """关闭数据库连接"""
        self.cursor.close()
        self.conn.close()


def summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    """
    总结检索结果

    Args:
        results: 检索结果列表

    Returns:
        总结报告
    """
    if not results:
        return {
            "total": 0,
            "message": "未找到相关专利"
        }

    summary = {
        "total": len(results),
        "time_range": {
            "earliest": None,
            "latest": None
        },
        "top_applicants": {},
        "ipc_distribution": {},
        "key_inventions": [],
        "technical_features": {
            "dual_fire_layer": [],  # 双火层技术
            "tar_removal": [],      # 焦油去除技术
            "biomass_gasification": []  # 生物质气化技术
        }
    }

    # 统计分析
    for patent in results:
        # 申请时间统计
        if patent.get('application_date'):
            app_date = str(patent['application_date'])[:4]
            if not summary["time_range"]["earliest"] or app_date < summary["time_range"]["earliest"]:
                summary["time_range"]["earliest"] = app_date
            if not summary["time_range"]["latest"] or app_date > summary["time_range"]["latest"]:
                summary["time_range"]["latest"] = app_date

        # 申请人统计
        applicant = patent.get('applicant', '未知')
        if applicant:
            summary["top_applicants"][applicant] = summary["top_applicants"].get(applicant, 0) + 1

        # IPC分类统计
        ipc = patent.get('ipc_main_class', '')
        if ipc:
            summary["ipc_distribution"][ipc] = summary["ipc_distribution"].get(ipc, 0) + 1

        # 技术特征分类
        title = patent.get('title', '')
        abstract = patent.get('abstract', '')
        text = (title + ' ' + abstract).lower()

        # 双火层特征
        if any(keyword in text for keyword in ['双火层', '双层', '上火层', '下火层', '双段']):
            summary["technical_features"]["dual_fire_layer"].append({
                "patent_id": patent.get('publication_number'),
                "title": patent.get('title'),
                "applicant": patent.get('applicant')
            })

        # 焦油去除特征
        if any(keyword in text for keyword in ['焦油', '除焦', '裂解', '重整']):
            summary["technical_features"]["tar_removal"].append({
                "patent_id": patent.get('publication_number'),
                "title": patent.get('title'),
                "applicant": patent.get('applicant')
            })

        # 生物质气化特征
        if any(keyword in text for keyword in ['生物质', '气化', '气化炉', '发生炉']):
            summary["technical_features"]["biomass_gasification"].append({
                "patent_id": patent.get('publication_number'),
                "title": patent.get('title'),
                "applicant": patent.get('applicant')
            })

    # 排序
    summary["top_applicants"] = dict(sorted(summary["top_applicants"].items(), key=lambda x: x[1], reverse=True)[:10])
    summary["ipc_distribution"] = dict(sorted(summary["ipc_distribution"].items(), key=lambda x: x[1], reverse=True)[:10])

    # 提取关键发明（前10个）
    summary["key_inventions"] = [
        {
            "title": r.get('title'),
            "applicant": r.get('applicant'),
            "abstract": r.get('abstract', '')[:300] + '...' if r.get('abstract') else '',
            "ipc": r.get('ipc_main_class'),
            "score": r.get('relevance_score')
        }
        for r in results[:10]
    ]

    return summary


def main():
    """主函数"""
    print("=" * 80)
    print("生物质气化发生炉专利检索系统")
    print("=" * 80)

    # 初始化检索器
    retriever = BiomassGasificationRetriever()

    # 构建检索式 - 核心技术特征
    # 第一组：生物质气化相关
    biomass_keywords = ['生物质', '气化炉', '发生炉', '气化']

    # 第二组：双火层特征
    dual_layer_keywords = ['双火层', '双层', '上火层', '下火层', '双段']

    # 第三组：焦油处理特征
    tar_keywords = ['焦油', '除焦', '裂解', '重整', '催化']

    print("\n=== 检索策略 ===")
    print("检索目标：生物质气化发生炉技术，重点关注上下双火层和焦油去除技术")
    print("核心关键词：")
    print(f"  - 生物质气化：{', '.join(biomass_keywords)}")
    print(f"  - 双火层特征：{', '.join(dual_layer_keywords)}")
    print(f"  - 焦油处理：{', '.join(tar_keywords)}")

    # 执行检索 - 使用组合策略
    print("\n=== 开始检索 ===")

    # 策略1：精确检索 - 必须包含生物质和气化炉
    print("\n[1/3] 精确检索：生物质气化炉...")
    exact_results = retriever.search_patents(
        ['生物质', '气化炉'],
        limit=20
    )
    print(f"  找到 {len(exact_results)} 条结果")

    # 策略2：扩展检索 - 包含双火层特征
    print("\n[2/3] 扩展检索：双火层发生炉技术...")
    dual_layer_results = retriever.search_with_or_logic([
        ['生物质', '气化', '双火层'],
        ['气化炉', '双层', '上火层'],
        ['发生炉', '双段']
    ], limit=20)
    print(f"  找到 {len(dual_layer_results)} 条结果")

    # 策略3：焦油处理技术检索
    print("\n[3/3] 技术检索：焦油去除技术...")
    tar_results = retriever.search_with_or_logic([
        ['生物质', '气化', '焦油'],
        ['气化炉', '除焦', '裂解'],
        ['发生炉', '催化', '重整']
    ], limit=20)
    print(f"  找到 {len(tar_results)} 条结果")

    # 合并去重结果
    all_results = []
    seen_ids = set()

    for result_list in [exact_results, dual_layer_results, tar_results]:
        for result in result_list:
            pub_num = result.get('publication_number')
            if pub_num and pub_num not in seen_ids:
                seen_ids.add(pub_num)
                all_results.append(result)

    print("\n=== 检索完成 ===")
    print(f"总计找到 {len(all_results)} 条不重复的专利")

    # 生成总结报告
    print("\n=== 生成分析报告 ===")
    summary = summarize_results(all_results)

    # 输出报告
    print(f"\n{'=' * 80}")
    print("检索结果分析报告")
    print(f"{'=' * 80}")

    print("\n【基本统计】")
    print(f"  检索结果总数：{summary['total']} 条")
    print(f"  时间跨度：{summary['time_range']['earliest']} - {summary['time_range']['latest']}")

    print("\n【主要申请人】（Top 10）")
    for i, (applicant, count) in enumerate(list(summary['top_applicants'].items())[:10], 1):
        print(f"  {i:2d}. {applicant}: {count} 条")

    print("\n【IPC分类分布】（Top 10）")
    for i, (ipc, count) in enumerate(list(summary['ipc_distribution'].items())[:10], 1):
        print(f"  {i:2d}. {ipc}: {count} 条")

    print("\n【技术特征统计】")
    print(f"  - 双火层技术：{len(summary['technical_features']['dual_fire_layer'])} 条")
    print(f"  - 焦油去除技术：{len(summary['technical_features']['tar_removal'])} 条")
    print(f"  - 生物质气化：{len(summary['technical_features']['biomass_gasification'])} 条")

    # 输出关键发明详情
    print("\n【重点专利】（相关性最高的前10条）")
    print("-" * 80)
    for i, invention in enumerate(summary['key_inventions'], 1):
        print(f"\n{i}. {invention['title']}")
        print(f"   申请人：{invention['applicant']}")
        print(f"   IPC分类：{invention['ipc']}")
        print(f"   相关性评分：{invention['score']:.4f}")
        print(f"   摘要：{invention['abstract']}")

    # 保存结果到文件
    output_file = f"/Users/xujian/Athena工作平台/biomass_gasification_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "summary": summary,
            "detailed_results": all_results
        }, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 80}")
    print(f"详细结果已保存至：{output_file}")
    print(f"{'=' * 80}")

    # 关闭连接
    retriever.close()


if __name__ == "__main__":
    main()
