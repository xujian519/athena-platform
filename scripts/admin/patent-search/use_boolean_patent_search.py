#!/usr/bin/env python3
"""
使用布尔逻辑式构建检索式搜索济南热力阴极保护相关专利
Use Boolean Logic to Build Search Queries for Jinan Heating Patents
"""

import logging
import sys

logger = logging.getLogger(__name__)

sys.path.append('/Users/xujian/Athena工作平台')

import asyncio
import json
from datetime import datetime
from pathlib import Path

# 导入增强专利搜索工具
try:
    from patent-platform/workspace.src.tools.enhanced_patent_search import (
        EnhancedPatentSearchTool,
    )
    BOOLEAN_SEARCH_AVAILABLE = True
    logger.info('✅ 增强专利搜索工具（支持布尔逻辑）可用')
except ImportError as e:
    BOOLEAN_SEARCH_AVAILABLE = False
    logger.info(f"❌ 增强专利搜索工具不可用: {e}")

def build_boolean_queries():
    """构建针对济南热力阴极保护技术的布尔查询式"""

    queries = {
        # 基础查询
        'basic': [
            'cathodic protection AND heating pipeline',
            '阴极保护 AND 供热管道',
            'sacrificial anode AND district heating',
            '牺牲阳极 AND 区域供热'
        ],

        # 排除式查询
        'exclusion': [
            'cathodic protection AND heating NOT oil',
            '阴极保护 AND 供热 NOT 石油',
            'corrosion protection AND pipeline NOT gas',
            '腐蚀防护 AND 管道 NOT 天然气'
        ],

        # 复合查询
        'complex': [
            '(cathodic protection OR corrosion protection) AND (heating OR district heating)',
            '(阴极保护 OR 腐蚀防护) AND (供热 OR 区域供热)',
            'sacrificial anode AND (shallow burial OR shallow soil) AND heating',
            '牺牲阳极 AND (浅埋 OR 浅土层) AND 供热'
        ],

        # 精确匹配
        'exact': [
            "\"forced current\" AND cathodic protection AND heating",
            "\"强制电流\" AND 阴极保护 AND 供热",
            "\"shallow burial\" AND pipeline AND corrosion",
            "\"浅土层\" AND 管道 AND 腐蚀"
        ],

        # 特定技术组合
        'tech_combo': [
            '(solar OR photovoltaic) AND cathodic protection AND pipeline',
            '(太阳能 OR 光伏) AND 阴极保护 AND 管道',
            'low power AND cathodic protection AND heating system',
            '低功耗 AND 阴极保护 AND 供热系统'
        ],

        # 时间限制查询
        'time_limited': [
            'cathodic protection AND heating pipeline after:2015',
            '阴极保护 AND 供热管道 after:2015',
            'smart cathodic protection AND heating after:2018',
            '智能阴极保护 AND 供热 after:2018'
        ]
    }

    return queries

async def run_boolean_search():
    """运行布尔逻辑专利搜索"""
    if not BOOLEAN_SEARCH_AVAILABLE:
        logger.info('❌ 布尔逻辑专利搜索工具不可用')
        return

    logger.info("\n🚀 开始布尔逻辑专利搜索...")

    # 初始化搜索工具
    search_tool = EnhancedPatentSearchTool()

    # 构建查询式
    queries = build_boolean_queries()

    all_results = {}

    # 对每类查询进行搜索
    for query_type, query_list in queries.items():
        logger.info(f"\n🔍 执行 {query_type} 类查询...")
        results = []

        for query in query_list:
            logger.info(f"  搜索: {query}")
            try:
                # 调用搜索工具
                search_result = await search_tool.arun(
                    query=query,
                    max_results=20,
                    include_analysis=True,
                    data_sources=['google_patents'],
                    similarity_threshold=0.6
                )

                # 解析结果
                if isinstance(search_result, str):
                    # 如果返回的是字符串，尝试解析为JSON
                    try:
                        result_data = json.loads(search_result)
                        if isinstance(result_data, dict) and 'patents' in result_data:
                            patents = result_data['patents']
                        else:
                            patents = []
                    except:
                        patents = []
                else:
                    patents = search_result.patents if hasattr(search_result, 'patents') else []

                logger.info(f"    找到 {len(patents)} 个专利")

                # 添加查询信息
                for patent in patents:
                    patent['search_query'] = query
                    patent['query_type'] = query_type
                    patent['search_time'] = datetime.now().isoformat()

                results.extend(patents)

            except Exception as e:
                logger.info(f"    ❌ 搜索失败: {e}")
                continue

        all_results[query_type] = results

        # 保存每类查询的结果
        if results:
            output_file = f"/Users/xujian/Athena工作平台/工作/济南热力集团/boolean_search_{query_type}_results.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'query_type': query_type,
                    'total_patents': len(results),
                    'search_time': datetime.now().isoformat(),
                    'patents': results
                }, f, ensure_ascii=False, indent=2)
            logger.info(f"    结果已保存: {output_file}")

    # 生成综合报告
    total_patents = sum(len(results) for results in all_results.values())

    logger.info(f"\n✅ 布尔逻辑搜索完成！")
    logger.info(f"📊 总计找到 {total_patents} 个专利")
    logger.info(f"📋 各类查询结果:")
    for query_type, results in all_results.items():
        logger.info(f"  - {query_type}: {len(results)} 个")

    # 保存综合结果
    summary_file = '/Users/xujian/Athena工作平台/工作/济南热力集团/boolean_search_summary.json'
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'search_method': 'Boolean Logic Queries',
            'search_time': datetime.now().isoformat(),
            'total_patents': total_patents,
            'query_types': list(queries.keys()),
            'results_summary': {
                qt: len(all_results[qt]) for qt in queries.keys()
            }
        }, f, ensure_ascii=False, indent=2)

    logger.info(f"\n📄 综合报告已保存: {summary_file}")

    return all_results

if __name__ == '__main__':
    asyncio.run(run_boolean_search())