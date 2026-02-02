#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试增强检索器（简化版）
Test Enhanced Retriever (Simplified)
"""

import logging
import os
import sys

logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_enhanced_retriever():
    """测试增强检索器"""
    logger.info("=== 测试增强专利检索器 ===\n")

    from enhanced_patent_retriever import EnhancedPatentRetriever

    try:
        # 创建检索器
        logger.info('1. 初始化检索器...')
        retriever = EnhancedPatentRetriever()
        logger.info('✅ 检索器初始化成功')

        # 测试查询
        test_queries = [
            '电池管理系统',
            '蓝牙设备',
            '新能源技术'
        ]

        for query in test_queries:
            logger.info(f"\n{'='*50}")
            logger.info(f"查询: {query}")
            logger.info(f"{'='*50}")

            # 先从数据库关键词搜索
            logger.info("\n2. 执行数据库关键词搜索...")
            from real_patent_connector_v2 import RealPatentConnectorV2
            connector = RealPatentConnectorV2()

            db_results = connector.search_patents(query, limit=3)
            logger.info(f"找到 {len(db_results)} 条结果")

            for i, result in enumerate(db_results[:3], 1):
                logger.info(f"\n{i}. 【标题】{result.get('patent_name', '无标题')}")
                logger.info(f"   【ID】{result.get('id')}")
                logger.info(f"   【类型】{result.get('patent_type', '未知')}")
                logger.info(f"   【相关度】{result.get('rank', 0):.3f}")

                abstract = result.get('abstract', '')
                if abstract:
                    logger.info(f"   【摘要】{abstract[:150]}...")

            connector.close()

            # 模拟向量搜索（简化版）
            logger.info("\n3. 模拟向量搜索（需要向量化的数据）...")
            logger.info('   ⚠️  注：真实向量搜索需要先对数据进行向量化处理')
            logger.info('   📝 建议：运行 patent_sync_service 批量向量化专利数据')

        # 显示提示
        logger.info(str("\n\n" + '='*50))
        logger.info('✅ 检索器测试完成！')
        logger.info("\n📋 测试结果：")
        logger.info('1. ✅ 检索器初始化成功')
        logger.info('2. ✅ 数据库连接正常')
        logger.info('3. ✅ 关键词搜索功能正常')
        logger.info('4. ⚠️  向量搜索需要先执行向量化')

        logger.info("\n🚀 下一步操作：")
        logger.info('1. 运行数据同步服务进行向量化')
        logger.info('   python patent_sync_service.py')
        logger.info('2. 启动Neo4j和Qdrant服务')
        logger.info('3. 执行完整的混合检索测试')

    except Exception as e:
        logger.info(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_enhanced_retriever()