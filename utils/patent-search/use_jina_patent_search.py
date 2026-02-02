#!/usr/bin/env python3
"""
使用Jina AI和Meta标签技术搜索济南热力阴极保护相关专利
Use Jina AI and Meta Tag Technology to Search Jinan Heating Patents
"""

import logging
import sys

logger = logging.getLogger(__name__)

sys.path.append('/Users/xujian/Athena工作平台')

import asyncio
import json
from datetime import datetime

from domains.patent.crawlers.proven_patent_retriever import ProvenPatentRetriever


async def search_with_jina():
    """使用Jina AI技术搜索专利"""
    logger.info('🚀 使用Jina AI和Meta标签技术搜索专利...')

    # 初始化检索器
    retriever = ProvenPatentRetriever()

    # 已知的可能相关的专利号（需要手动搜索获得）
    # 这里用一些示例专利号进行测试
    test_patents = [
        'https://patents.google.com/patent/US20140183934A1',  # cathodic protection example
        'https://patents.google.com/patent/US20130248288A1',  # heating system example
        'https://patents.google.com/patent/US20140060919A1',  # pipeline protection example
    ]

    results = []

    for patent_url in test_patents:
        logger.info(f"\n🔍 正在获取专利: {patent_url}")
        try:
            # 获取专利数据
            patent_data = await retriever.get_patent_data(patent_url)

            # 添加检索信息
            patent_data['search_time'] = datetime.now().isoformat()
            patent_data['retriever'] = 'jina_meta_tags'

            results.append(patent_data)

            # 显示基本信息
            logger.info(f"  标题: {patent_data.get('title', 'N/A')}")
            logger.info(f"  摘要: {patent_data.get('abstract', 'N/A')[:100]}...")
            logger.info(f"  数据质量评分: {patent_data.get('quality_score', 0)}/10")

        except Exception as e:
            logger.info(f"  ❌ 获取失败: {e}")
            continue

    # 保存结果
    output_file = '/Users/xujian/Athena工作平台/工作/济南热力集团/jina_patent_search_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'metadata': {
                'search_time': datetime.now().isoformat(),
                'method': 'Jina AI + Meta Tags',
                'total_patents': len(results),
                'retriever_stats': retriever.stats
            },
            'patents': results
        }, f, ensure_ascii=False, indent=2)

    logger.info(f"\n✅ 搜索完成！")
    logger.info(f"📊 统计信息:")
    logger.info(f"  - 总专利数: {len(results)}")
    logger.info(f"  - Jina成功: {retriever.stats['jina_success']}")
    logger.info(f"  - Meta标签成功: {retriever.stats['meta_tag_success']}")
    logger.info(f"  - 组合成功: {retriever.stats['combined_success']}")
    logger.info(f"  - 错误数: {retriever.stats['errors']}")
    logger.info(f"\n📄 结果已保存到: {output_file}")

    return results

if __name__ == '__main__':
    asyncio.run(search_with_jina())