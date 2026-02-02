#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生产级专利爬虫启动器
Production Patent Crawler Launcher

启动增强版专利爬虫系统，提供完整的专利数据抓取服务
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# 导入增强版爬虫
from domains.patent.crawlers.enhanced_google_patents_crawler import (
    EnhancedGooglePatentsCrawler,
)
from domains.patent.tools.production_patent_search import ProductionPatentSearchTool

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('documentation/logs/production_crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ProductionCrawlerService:
    """生产级专利爬虫服务"""

    def __init__(self):
        self.crawler = None
        self.langchain_tool = None
        self.stats = {
            'start_time': datetime.now(),
            'total_searches': 0,
            'successful_searches': 0,
            'total_patents': 0,
            'errors': 0
        }

    async def initialize(self):
        """初始化服务"""
        try:
            logger.info('🚀 初始化生产级专利爬虫服务...')

            # 加载环境配置
            if not os.getenv('SCRAPINGBEE_API_KEY'):
                logger.error('❌ 未配置SCRAPINGBEE_API_KEY环境变量')
                return False

            # 初始化爬虫
            self.crawler = EnhancedGooglePatentsCrawler()
            self.langchain_tool = ProductionPatentSearchTool()

            # 检查API可用性
            api_available = self.crawler.check_api_availability()
            if not api_available:
                logger.error('❌ ScrapingBee API不可用')
                return False

            logger.info('✅ 生产级专利爬虫服务初始化成功')
            return True

        except Exception as e:
            logger.error(f"❌ 初始化失败: {str(e)}")
            return False

    async def search_patents(self, query, **kwargs):
        """搜索专利"""
        try:
            self.stats['total_searches'] += 1
            logger.info(f"🔍 搜索专利: {query}")

            # 使用LangChain工具搜索
            result = await self.langchain_tool._arun(
                query=query,
                **kwargs
            )

            result_data = json.loads(result)

            if result_data['success']:
                self.stats['successful_searches'] += 1
                self.stats['total_patents'] += result_data['total_results']
                logger.info(f"✅ 搜索成功: 找到 {result_data['total_results']} 个专利")
                return result_data
            else:
                self.stats['errors'] += 1
                logger.warning(f"⚠️  搜索失败: {result_data['message']}")
                return result_data

        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"❌ 搜索异常: {str(e)}")
            return {
                'success': False,
                'message': f'搜索异常: {str(e)}',
                'patents': [],
                'total_results': 0
            }

    async def batch_search(self, queries, max_results_per_query=5):
        """批量搜索专利"""
        logger.info(f"📊 开始批量搜索: {len(queries)} 个查询")

        all_results = []

        for i, query in enumerate(queries, 1):
            logger.info(f"处理查询 {i}/{len(queries)}: {query}")

            result = await self.search_patents(
                query=query,
                max_results=max_results_per_query
            )

            all_results.append({
                'query': query,
                'result': result
            })

            # 添加延迟避免频率限制
            await asyncio.sleep(1)

        # 保存批量结果
        batch_result = {
            'batch_time': datetime.now().isoformat(),
            'total_queries': len(queries),
            'results': all_results,
            'stats': self.get_stats()
        }

        output_file = f"patent_search_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(batch_result, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ 批量搜索完成，结果已保存到: {output_file}")
        return batch_result

    def get_stats(self):
        """获取服务统计"""
        uptime = datetime.now() - self.stats['start_time']
        return {
            **self.stats,
            'uptime_seconds': uptime.total_seconds(),
            'uptime_formatted': str(uptime).split('.')[0],
            'success_rate': (self.stats['successful_searches'] / self.stats['total_searches'] * 100) if self.stats['total_searches'] > 0 else 0,
            'average_patents_per_search': (self.stats['total_patents'] / self.stats['successful_searches']) if self.stats['successful_searches'] > 0 else 0
        }

    async def health_check(self):
        """健康检查"""
        try:
            # 测试基本搜索
            test_result = await self.search_patents('test', max_results=1)

            health_status = {
                'status': 'healthy' if test_result['success'] else 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'api_available': self.crawler.check_api_availability(),
                'stats': self.get_stats()
            }

            return health_status

        except Exception as e:
            return {
                'status': 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'stats': self.get_stats()
            }

async def main():
    """主函数 - 启动生产服务"""
    logger.info('🚀 启动生产级专利爬虫服务')
    logger.info(str('=' * 50))

    # 创建日志目录
    os.makedirs('logs', exist_ok=True)

    # 初始化服务
    service = ProductionCrawlerService()

    if not await service.initialize():
        logger.info('❌ 服务初始化失败，退出')
        return

    # 示例搜索
    logger.info("\n📋 执行示例搜索...")
    logger.info(str('-' * 30))

    # 单个搜索示例
    result = await service.search_patents(
        query='artificial intelligence',
        max_results=5,
        country='US'
    )

    logger.info(f"搜索结果: {result['success']}")
    logger.info(f"找到专利: {result['total_results']} 个")

    if result['patents']:
        for i, patent in enumerate(result['patents'][:3], 1):
            logger.info(f"\n专利{i}:")
            logger.info(f"  标题: {patent.get('title', 'N/A')[:60]}...")
            logger.info(f"  专利号: {patent.get('patent_number', 'N/A')}")

    # 批量搜索示例
    logger.info("\n📊 执行批量搜索...")
    logger.info(str('-' * 30))

    batch_queries = [
        'machine learning',
        'neural network',
        'blockchain technology'
    ]

    batch_result = await service.batch_search(batch_queries, max_results_per_query=3)

    # 健康检查
    logger.info("\n🔍 执行健康检查...")
    logger.info(str('-' * 30))

    health = await service.health_check()
    logger.info(f"服务状态: {health['status']}")
    logger.info(f"API可用: {health['api_available']}")
    logger.info(f"总搜索数: {health['stats']['total_searches']}")
    logger.info(f"成功率: {health['stats']['success_rate']:.1f}%")
    logger.info(f"平均专利数: {health['stats']['average_patents_per_search']:.1f}")

    # 保存最终统计
    final_stats = service.get_stats()
    final_stats_file = f"crawler_final_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(final_stats_file, 'w', encoding='utf-8') as f:
        json.dump({
            'service_end_time': datetime.now().isoformat(),
            'final_stats': final_stats
        }, f, ensure_ascii=False, indent=2)

    logger.info(f"\n✅ 服务统计已保存到: {final_stats_file}")

    logger.info(str("\n" + '=' * 50))
    logger.info('🎉 生产级专利爬虫服务运行完成')
    logger.info(str('=' * 50))

if __name__ == '__main__':
    asyncio.run(main())
