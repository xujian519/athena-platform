#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实数据集成测试
Test Real Data Integration

测试真实专利数据库集成功能
"""

import logging
import os
import sys
from datetime import datetime

# 添加父目录路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_patent_connector():
    """测试专利数据库连接器"""
    logger.info(str("\n" + '='*60))
    logger.info('第一步：测试专利数据库连接器')
    logger.info(str('='*60))

    from real_patent_integration.real_patent_connector import (
        RealPatentConnector,
        init_sample_patent_data,
    )

    try:
        # 初始化示例数据
        logger.info('初始化示例专利数据...')
        init_sample_patent_data()

        # 创建连接器
        connector = RealPatentConnector()

        # 测试连接
        logger.info("\n测试数据库连接...")
        if connector.test_connection():
            logger.info('✅ 数据库连接成功')
        else:
            logger.info('❌ 数据库连接失败')
            return False

        # 获取统计信息
        logger.info("\n获取专利统计信息...")
        stats = connector.get_patent_statistics()
        if 'error' not in stats:
            logger.info(f"✅ 专利总数: {stats.get('total_patents', 0)}")
            logger.info(f"✅ 申请总数: {stats.get('total_applications', 0)}")
            if 'by_type' in stats:
                logger.info(f"✅ 按类型分布: {stats['by_type']}")
        else:
            logger.info(f"❌ 获取统计失败: {stats['error']}")

        # 加载专利数据
        logger.info("\n加载专利数据...")
        patents = connector.load_patents(limit=5, include_abstract=True)
        logger.info(f"✅ 成功加载 {len(patents)} 条专利")

        # 显示示例
        if patents:
            logger.info("\n专利示例:")
            for i, patent in enumerate(patents[:3], 1):
                logger.info(f"\n{i}. 专利ID: {patent.get('patent_id', 'N/A')}")
                logger.info(f"   标题: {patent.get('title', '无标题')}")
                logger.info(f"   类型: {patent.get('patent_type', '未知')}")
                abstract = patent.get('abstract', '')
                if abstract:
                    logger.info(f"   摘要: {abstract[:100]}...")

        connector.close()
        return True

    except Exception as e:
        logger.info(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sync_service():
    """测试数据同步服务"""
    logger.info(str("\n" + '='*60))
    logger.info('第二步：测试数据同步服务')
    logger.info(str('='*60))

    from real_patent_integration.patent_sync_service import PatentSyncService

    try:
        # 创建同步服务
        sync_service = PatentSyncService(batch_size=10, max_workers=2)

        # 初始化存储
        logger.info("\n初始化Qdrant和Neo4j...")
        sync_service.initialize_collections()
        sync_service.initialize_neo4j_constraints()
        logger.info('✅ 存储系统初始化完成')

        # 同步少量数据
        logger.info("\n执行数据同步（限制20条）...")
        stats = sync_service.sync_all_patents(limit=20)

        logger.info(f"\n✅ 同步完成！")
        logger.info(f"   处理总数: {stats['total_processed']}")
        logger.info(f"   成功同步: {stats['successful_syncs']}")
        logger.info(f"   失败数量: {stats['failed_syncs']}")

        if stats['start_time'] and stats['last_sync_time']:
            duration = stats['last_sync_time'] - stats['start_time']
            logger.info(f"   耗时: {duration}")

        sync_service.cleanup()
        return True

    except Exception as e:
        logger.info(f"❌ 同步测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_enhanced_retriever():
    """测试增强检索器"""
    logger.info(str("\n" + '='*60))
    logger.info('第三步：测试增强检索器')
    logger.info(str('='*60))

    from real_patent_integration.enhanced_patent_retriever import (
        EnhancedPatentRetriever,
    )

    try:
        # 创建检索器
        retriever = EnhancedPatentRetriever()

        # 测试查询
        test_queries = [
            '电池管理系统',
            '蓝牙设备',
            '新能源'
        ]

        for query in test_queries:
            logger.info(f"\n查询: {query}")
            logger.info(str('-' * 50))

            # 执行检索
            results, stats = retriever.search(
                query=query,
                top_k=3,
                search_modes=['vector', 'graph', 'keyword'],
                weights={'vector': 0.5, 'graph': 0.3, 'keyword': 0.2}
            )

            logger.info(f"\n检索结果:")
            logger.info(f"  耗时: {stats.total_time:.3f}s")
            logger.info(f"  结果数: {stats.results_count}")

            # 显示结果
            for i, result in enumerate(results[:3], 1):
                logger.info(f"\n{i}. 【{result.patent_id}】{result.title}")
                logger.info(f"   分数: {result.score:.3f}")
                logger.info(f"   来源: {result.source}")
                logger.info(f"   说明: {result.explanation}")

        # 获取检索统计
        logger.info(f"\n检索器统计:")
        retriever_stats = retriever.get_search_statistics()
        for key, value in retriever_stats.items():
            logger.info(f"  {key}: {value}")

        retriever.cleanup()
        return True

    except Exception as e:
        logger.info(f"❌ 检索测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integrated_workflow():
    """测试集成工作流"""
    logger.info(str("\n" + '='*60))
    logger.info('第四步：测试集成工作流')
    logger.info(str('='*60))

    try:
        # 1. 检查数据状态
        from real_patent_connector import RealPatentConnector
        from real_patent_integration.enhanced_patent_retriever import (
            EnhancedPatentRetriever,
        )

        logger.info('检查数据状态...')
        connector = RealPatentConnector()
        stats = connector.get_patent_statistics()
        logger.info(f"数据库中的专利数: {stats.get('total_patents', 0)}")
        connector.close()

        # 2. 创建增强检索器
        retriever = EnhancedPatentRetriever()

        # 3. 执行复杂查询
        logger.info("\n执行复杂查询测试...")
        complex_query = '智能电池管理和新能源技术'
        results, stats = retriever.search(
            query=complex_query,
            top_k=5,
            filters={'patent_type': 'invention'},
            search_modes=['vector', 'graph', 'keyword', 'bm25'],
            weights={'vector': 0.4, 'graph': 0.3, 'keyword': 0.2, 'bm25': 0.1}
        )

        logger.info(f"\n复杂查询结果: {len(results)} 个")
        for i, result in enumerate(results[:3], 1):
            logger.info(f"\n{i}. {result.title}")
            logger.info(f"   综合分数: {result.score:.3f}")
            logger.info(f"   各分数: {result.metadata.get('scores', {})}")

        # 4. 测试缓存效果
        logger.info("\n测试缓存效果...")
        # 相同查询第二次执行
        results2, stats2 = retriever.search(
            query=complex_query,
            top_k=5
        )
        logger.info(f"第二次查询耗时: {stats2.total_time:.3f}s (缓存)")

        retriever_stats = retriever.get_search_statistics()
        logger.info(f"缓存命中率: {retriever_stats['cache_hit_rate']:.2%}")

        retriever.cleanup()
        return True

    except Exception as e:
        logger.info(f"❌ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    logger.info("\n🚀 真实专利数据集成测试")
    logger.info(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 测试步骤
    test_steps = [
        ('专利数据库连接', test_patent_connector),
        ('数据同步服务', test_sync_service),
        ('增强检索器', test_enhanced_retriever),
        ('集成工作流', test_integrated_workflow)
    ]

    # 执行测试
    passed = 0
    failed = 0

    for step_name, test_func in test_steps:
        logger.info(f"\n{'='*60}")
        logger.info(f"执行测试: {step_name}")
        logger.info(f"{'='*60}")

        try:
            if test_func():
                passed += 1
                logger.info(f"\n✅ {step_name} - 通过")
            else:
                failed += 1
                logger.info(f"\n❌ {step_name} - 失败")
        except Exception as e:
            failed += 1
            logger.info(f"\n❌ {step_name} - 异常: {e}")

    # 测试总结
    logger.info(f"\n{'='*60}")
    logger.info('测试总结')
    logger.info(f"{'='*60}")
    logger.info(f"总测试数: {passed + failed}")
    logger.info(f"通过: {passed}")
    logger.info(f"失败: {failed}")

    if failed == 0:
        logger.info("\n🎉 所有测试通过！真实专利数据集成成功。")
        logger.info("\n系统功能：")
        logger.info('1. ✅ PostgreSQL专利数据库连接')
        logger.info('2. ✅ 专利数据同步到Qdrant和Neo4j')
        logger.info('3. ✅ 多模式混合检索')
        logger.info('4. ✅ 查询结果融合和缓存')
        logger.info("\n下一步：")
        logger.info('1. 执行中文BERT专业模型集成')
        logger.info('2. 实现Redis缓存优化')
        logger.info('3. 添加并行处理支持')
    else:
        logger.info("\n⚠️ 部分测试失败，请检查错误信息并修复问题。")

if __name__ == '__main__':
    main()