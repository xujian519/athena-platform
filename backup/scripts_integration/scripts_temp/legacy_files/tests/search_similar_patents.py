#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
在中国专利数据库中检索近似专利
Search Similar Patents in Chinese Patent Database
"""

import asyncio
import json
import logging
import sys
from typing import Dict, List

import requests

logger = logging.getLogger(__name__)

sys.path.append('/Users/xujian/Athena工作平台')

from core.iterative_patent_search import IterativePatentSearcher


def build_search_strategy() -> Dict:
    """构建检索策略"""
    strategy = {
        'target_patent': {
            'patent_number': 'CN201390190Y',
            'application_number': '200920113915.8',
            'title': '拉紧器',
            'ipc': 'B65P 7/06'
        },

        'search_keywords': {
            'core_keywords': [
                '拉紧器', '紧固器', '捆绑器', '货物固定',
                '绳索紧固', '货物绑紧', '张紧装置'
            ],
            'structural_features': [
                '螺纹联接', '连接件', '调节件', '手柄',
                '挂钩', '棘轮', '弹簧', '旋转调节'
            ],
            'application_fields': [
                '货物运输', '货物固定', '物流器械',
                '机械紧固', '货物安全'
            ]
        },

        'search_strategy': {
            'primary_search': {
                'title': '拉紧器 OR 紧固器 OR 捆绑器',
                'abstract': '螺纹联接 AND (手柄 OR 旋转)',
                'claims': '(连接件 AND 调节件) OR 挂钩'
            },

            'expansion_search': {
                'similar_functions': '货物固定 OR 紧固 OR 捆绑',
                'similar_structures': '螺纹调节 OR 旋转紧固 OR 杠杆装置',
                'similar_applications': '物流 OR 运输 OR 货物安全'
            },

            'ipc_classification': [
                'B65P',  # 捆扎或紧固物件用的装置
                'B25B',   # 夹具、手钳；钳子
                'F16B',   # 紧固件
                'E04G',   # 紧固件
                'E01F'    # 车辆上的负载固定装置
            ]
        },

        'priority_features': [
            '螺纹联接的连接件和调节件',
            '手柄带动旋转的调节机制',
            '双挂钩设计',
            '棘轮单向转动机构',
            '弹簧辅助定位'
        ]
    }

    return strategy

async def search_patents() -> List[Dict]:
    """执行专利搜索"""
    logger.info('🔍 构建检索策略...')
    strategy = build_search_strategy()

    logger.info("\n📋 检索策略:")
    logger.info(str('='*50))
    logger.info(f"目标专利: {strategy['target_patent']['title']}")
    logger.info(f"IPC分类: {strategy['target_patent']['ipc']}")
    logger.info("\n核心关键词:")
    for kw in strategy['search_keywords']['core_keywords']:
        logger.info(f"  - {kw}")
    logger.info("\n结构特征:")
    for feature in strategy['search_keywords']['structural_features']:
        logger.info(f"  - {feature}")

    # 初始化搜索器
    searcher = IterativePatentSearcher()

    try:
        logger.info("\n🔗 连接专利数据库...")
        searcher.connect()

        results = []

        # 执行多轮搜索
        search_queries = [
            {
                'query': '拉紧器 紧固器 捆绑器',
                'description': '主搜索 - 相同功能产品'
            },
            {
                'query': '螺纹联接 手柄 旋转调节',
                'description': '结构特征搜索'
            },
            {
                'query': '货物固定 物流紧固',
                'description': '应用场景搜索'
            },
            {
                'query': '棘轮机构 紧固装置',
                'description': '技术方案搜索'
            },
            {
                'query': '挂钩 双钩 紧拉',
                'description': '细节特征搜索'
            }
        ]

        for query_info in search_queries:
            logger.info(f"\n🔎 执行搜索: {query_info['description']}")
            logger.info(f"   查询: {query_info['query']}")

            # 搜索专利
            search_results = searcher.search(query_info['query'], max_results=20)

            # 提取关键信息
            for result in search_results[:10]:  # 每个查询最多取10个
                if result.patent_name and result.patent_name not in [r.get('patent_name') for r in results]:
                    patent_info = {
                        'patent_name': result.patent_name,
                        'application_number': result.application_number,
                        'publication_number': result.publication_number,
                        'applicant': result.applicant,
                        'abstract': result.abstract[:200] + '...' if result.abstract and len(result.abstract) > 200 else result.abstract,
                        'ipc_main_class': result.ipc_main_class,
                        'relevance_score': result.relevance_score,
                        'search_type': query_info['description']
                    }
                    results.append(patent_info)
                    logger.info(f"   ✓ 找到: {result.patent_name[:30]}... (相似度: {result.relevance_score:.3f})")

        # 按相关性排序
        results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)

        # 限制为20个
        results = results[:20]

        logger.info(f"\n📊 搜索完成，共找到 {len(results)} 个近似专利")

        searcher.disconnect()
        return results

    except Exception as e:
        logger.info(f"❌ 搜索失败: {str(e)}")
        return []

async def main():
    """主函数"""
    logger.info('🚀 中国专利数据库检索系统')
    logger.info(str('='*60))

    results = asyncio.run(search_patents())

    if results:
        logger.info("\n\n📋 检索结果详情:")
        logger.info(str('='*60))

        for i, patent in enumerate(results, 1):
            logger.info(f"\n{i}. 【专利名称】{patent.get('patent_name', '未知')}")
            logger.info(f"   【申请号】{patent.get('application_number', '未知')}")
            logger.info(f"   【公开号】{patent.get('publication_number', '未知')}")
            logger.info(f"   【申请人】{patent.get('applicant', '未知')}")
            logger.info(f"   【IPC分类】{patent.get('ipc_main_class', '未知')}")
            logger.info(f"   【相似度】{patent.get('relevance_score', 0):.3f}")
            logger.info(f"   【摘要】{patent.get('abstract', '无摘要')[:100]}...")
            logger.info(f"   【检索来源】{patent.get('search_type', '未知')}")

        # 保存结果
        with open('similar_patents_search_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        logger.info(f"\n✅ 检索结果已保存到 similar_patents_search_results.json")
    else:
        logger.info("\n⚠️ 未能找到近似专利")

if __name__ == '__main__':
    results = asyncio.run(main())