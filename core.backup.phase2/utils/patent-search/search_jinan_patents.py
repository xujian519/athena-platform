#!/usr/bin/env python3
from __future__ import annotations
"""
搜索济南热力阴极保护技术相关专利
Search Jinan Heating Cathodic Protection Patents
"""

import logging
import sys

logger = logging.getLogger(__name__)

sys.path.append('/Users/xujian/Athena工作平台')

import asyncio
import json
from datetime import datetime

from core.interfaces.patent_service import PatentRetrievalService
from config.dependency_injection import DIContainer


async def search_patents():
    """搜索相关专利"""
    logger.info('🔍 开始搜索济南热力阴极保护技术相关专利...')

    # 初始化检索器
    retriever = DIContainer.resolve(PatentRetrievalService)
    await retriever.initialize()

    # 搜索查询列表
    search_queries = [
        'cathodic protection heating pipeline',
        'cathodic protection district heating',
        'sacrificial anode heating system',
        'corrosion protection heating pipe',
        'shallow burial cathodic protection',
        '阴极保护 供热管道',
        '阴极保护 区域供热',
        '牺牲阳极 供热系统',
        '管道 防腐蚀 供热'
    ]

    all_results = []

    for query in search_queries:
        logger.info(f"\n🔍 搜索: {query}")
        try:
            # 搜索专利
            results = await retriever.search_patents(
                query=query,
                max_results=10
            )

            # results 是一个字典，包含patents列表
            patents = results.get('patents', [])
            logger.info(f"找到 {len(patents)} 个相关专利")

            # 保存结果
            for patent in patents:
                patent['search_query'] = query
                patent['search_time'] = datetime.now().isoformat()
                all_results.append(patent)

        except Exception as e:
            logger.info(f"搜索失败: {e}")
            continue

    # 保存所有结果
    output_file = '/Users/xujian/Athena工作平台/工作/济南热力集团/patent_search_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    logger.info(f"\n✅ 搜索完成！共找到 {len(all_results)} 个专利")
    logger.info(f"📄 结果已保存到: {output_file}")

    # 统计信息
    logger.info("\n📊 搜索统计:")
    for query in search_queries:
        count = len([p for p in all_results if p.get('search_query') == query])
        if count > 0:
            logger.info(f"  - {query}: {count} 个专利")

    return all_results

if __name__ == '__main__':
    asyncio.run(search_patents())
