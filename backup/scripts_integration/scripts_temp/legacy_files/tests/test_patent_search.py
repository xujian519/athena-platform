#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专利搜索系统测试脚本
Test Script for Patent Search System
"""

import asyncio
import json
import logging
import sys
from datetime import datetime

logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.append('/Users/xujian/Athena工作平台')

from core.iterative_patent_search import IterativePatentSearcher, PatentInfo


async def test_basic_search():
    """测试基本搜索功能"""
    logger.info(str("\n" + '='*60))
    logger.info('🔍 测试1: 基本搜索功能')
    logger.info(str('='*60))

    searcher = IterativePatentSearcher()

    try:
        searcher.connect()

        # 测试查询
        test_queries = [
            '深度学习',
            '人工智能 图像识别',
            '机器学习 算法',
            '神经网络',
            '区块链'
        ]

        for query in test_queries:
            logger.info(f"\n📝 搜索查询: {query}")
            logger.info(str('-' * 40))

            results = await searcher.search(query, max_results=10)

            logger.info(f"找到 {len(results)} 个专利")

            for i, patent in enumerate(results[:3], 1):
                logger.info(f"\n{i}. 📄 {patent.patent_name}")
                logger.info(f"   申请号: {patent.application_number}")
                logger.info(f"   申请人: {patent.applicant}")
                logger.info(f"   IPC分类: {patent.ipc_main_class}")
                logger.info(f"   摘要: {patent.abstract[:100]}...")
                logger.info(f"   相关性评分: {patent.relevance_score:.3f}")

                if patent.google_meta:
                    logger.info(f"   Google Meta - 引用数: {patent.google_meta.citations_count}")
                    logger.info(f"   Google Meta - 发明人: {', '.join(patent.google_meta.inventors[:2])}")

    finally:
        searcher.disconnect()

async def test_iterative_optimization():
    """测试迭代优化功能"""
    logger.info(str("\n" + '='*60))
    logger.info('🔄 测试2: 迭代优化功能')
    logger.info(str('='*60))

    searcher = IterativePatentSearcher()

    try:
        searcher.connect()

        # 复杂查询测试
        query = '基于深度学习的医学图像分析系统'
        logger.info(f"\n📝 复杂查询: {query}")
        logger.info(str('-' * 40))

        results = await searcher.search(query, max_results=15)

        logger.info(f"\n✨ 搜索结果分析:")
        logger.info(f"总结果数: {len(results)}")
        logger.info(f"平均相关性评分: {sum(p.relevance_score for p in results) / len(results):.3f}")

        # 分析结果分布
        high_relevance = [p for p in results if p.relevance_score > 0.7]
        medium_relevance = [p for p in results if 0.4 <= p.relevance_score <= 0.7]
        low_relevance = [p for p in results if p.relevance_score < 0.4]

        logger.info(f"\n📊 相关性分布:")
        logger.info(f"高相关性 (>0.7): {len(high_relevance)} 个")
        logger.info(f"中相关性 (0.4-0.7): {len(medium_relevance)} 个")
        logger.info(f"低相关性 (<0.4): {len(low_relevance)} 个")

        # 查看搜索历史
        if searcher.search_history:
            logger.info(f"\n📚 搜索历史:")
            for i, history in enumerate(searcher.search_history[-3:], 1):
                logger.info(f"{i}. 查询: {history['query']}")
                logger.info(f"   结果数: {history['results_count']}")
                logger.info(f"   迭代次数: {history['iterations']}")
                logger.info(f"   时间: {history['timestamp'].strftime('%H:%M:%S')}")

    finally:
        searcher.disconnect()

async def test_google_meta_extraction():
    """测试Google专利meta信息提取"""
    logger.info(str("\n" + '='*60))
    logger.info('🌐 测试3: Google专利Meta信息提取')
    logger.info(str('='*60))

    searcher = IterativePatentSearcher()

    try:
        searcher.connect()

        # 搜索并提取meta信息
        query = '神经网络'
        results = await searcher.search(query, max_results=5)

        logger.info(f"\n📋 Meta信息提取结果:")
        logger.info(str('-' * 40))

        for i, patent in enumerate(results, 1):
            logger.info(f"\n{i}. 专利名称: {patent.patent_name}")

            if patent.google_meta:
                meta = patent.google_meta
                logger.info(f"\n   🏷️ Google Patent Meta:")
                logger.info(f"   - 标题: {meta.title}")
                logger.info(f"   - 申请人: {meta.assignee}")
                logger.info(f"   - 发明人: {', '.join(meta.inventors[:3])}")
                if len(meta.inventors) > 3:
                    logger.info(f"     (共{len(meta.inventors)}位发明人)")
                logger.info(f"   - 申请日: {meta.application_date}")
                logger.info(f"   - 公开日: {meta.publication_date}")
                logger.info(f"   - 引用数: {meta.citations_count}")
                logger.info(f"   - 被引用数: {meta.cited_by_count}")
                logger.info(f"   - IPC分类: {', '.join(meta.ipc_codes[:5])}")
                if len(meta.ipc_codes) > 5:
                    logger.info(f"     (共{len(meta.ipc_codes)}个分类)")
                logger.info(f"   - CPC分类: {', '.join(meta.cpc_codes[:5])}")

                # 显示权利要求数量
                if meta.claims:
                    logger.info(f"   - 权利要求: {len(meta.claims)} 项")
                    logger.info(f"   - 主权项: {meta.claims[0][:100]}...")
            else:
                logger.info('   ⚠️ 未提取到Meta信息')

    finally:
        searcher.disconnect()

async def test_export_functionality():
    """测试导出功能"""
    logger.info(str("\n" + '='*60))
    logger.info('💾 测试4: 搜索结果导出功能')
    logger.info(str('='*60))

    searcher = IterativePatentSearcher()

    try:
        searcher.connect()

        # 执行搜索
        query = '机器学习 专利'
        results = await searcher.search(query, max_results=20)

        # 导出为JSON
        json_file = f"test_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        searcher.export_results(results, json_file, format='json')
        logger.info(f"✅ JSON导出完成: {json_file}")

        # 导出为CSV
        csv_file = f"test_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        searcher.export_results(results, csv_file, format='csv')
        logger.info(f"✅ CSV导出完成: {csv_file}")

        # 显示导出统计
        logger.info(f"\n📊 导出统计:")
        logger.info(f"- 导出专利数: {len(results)}")
        logger.info(f"- 平均相关性: {sum(p.relevance_score for p in results) / len(results):.3f}")
        logger.info(f"- 包含Meta信息: {sum(1 for p in results if p.google_meta)} 个")

    finally:
        searcher.disconnect()

async def test_database_connection():
    """测试数据库连接和基本查询"""
    logger.info(str("\n" + '='*60))
    logger.info('🗄️ 测试5: 数据库连接和查询')
    logger.info(str('='*60))

    searcher = IterativePatentSearcher()

    try:
        searcher.connect()

        # 获取数据库统计信息
        with searcher.conn.cursor() as cursor:
            # 专利总数
            cursor.execute('SELECT COUNT(*) as total FROM patents')
            total_patents = cursor.fetchone()['total']
            logger.info(f"📈 数据库统计:")
            logger.info(f"- 专利总数: {total_patents:,}")

            # 各年专利数量
            cursor.execute("""
                SELECT source_year, COUNT(*) as count
                FROM patents
                WHERE source_year IS NOT NULL
                GROUP BY source_year
                ORDER BY source_year DESC
                LIMIT 5
            """)
            yearly_stats = cursor.fetchall()
            logger.info(f"\n📅 近年专利数量:")
            for stat in yearly_stats:
                logger.info(f"- {stat['source_year']}: {stat['count']:,} 项")

            # IPC分类统计
            cursor.execute("""
                SELECT ipc_main_class, COUNT(*) as count
                FROM patents
                WHERE ipc_main_class IS NOT NULL
                GROUP BY ipc_main_class
                ORDER BY count DESC
                LIMIT 10
            """)
            ipc_stats = cursor.fetchall()
            logger.info(f"\n🏷️ 热门IPC分类:")
            for stat in ipc_stats[:5]:
                logger.info(f"- {stat['ipc_main_class']}: {stat['count']:,} 项")

            # 申请人统计
            cursor.execute("""
                SELECT applicant, COUNT(*) as count
                FROM patents
                WHERE applicant IS NOT NULL
                GROUP BY applicant
                ORDER BY count DESC
                LIMIT 10
            """)
            applicant_stats = cursor.fetchall()
            logger.info(f"\n🏢 Top 10 申请人:")
            for i, stat in enumerate(applicant_stats, 1):
                logger.info(f"{i:2d}. {stat['applicant']}: {stat['count']} 项")

    finally:
        searcher.disconnect()

async def main():
    """主测试函数"""
    logger.info(str("\n" + '🚀' * 30))
    logger.info('专利搜索系统测试开始')
    logger.info(str('🚀' * 30))
    logger.info(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # 运行所有测试
        await test_database_connection()
        await test_basic_search()
        await test_iterative_optimization()
        await test_google_meta_extraction()
        await test_export_functionality()

        logger.info(str("\n" + '='*60))
        logger.info('✅ 所有测试完成！')
        logger.info(str('='*60))

    except Exception as e:
        logger.info(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main())