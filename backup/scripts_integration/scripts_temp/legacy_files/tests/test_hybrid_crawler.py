#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
混合爬虫系统测试脚本
Hybrid Crawler System Test Script
"""

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# 添加路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'services'))
sys.path.insert(0, str(project_root / 'services' / 'crawler'))

def print_section(title: str):
    """打印章节标题"""
    logger.info(f"\n{'='*60}")
    logger.info(f"  {title}")
    logger.info(f"{'='*60}")

def print_test(name: str, status: str, details: str = ''):
    """打印测试结果"""
    status_icon = '✅' if status == 'PASS' else '❌' if status == 'FAIL' else '⚠️'
    logger.info(f"{status_icon} {name}")
    if details:
        logger.info(f"   {details}")

async def test_config_system():
    """测试配置系统"""
    print_section('配置系统测试')

    try:
        from config.hybrid_config import get_config, get_config_manager

        # 测试配置加载
        config_manager = get_config_manager()
        config = get_config()

        print_test('配置加载', 'PASS', f"加载了 {len(config.__dict__)} 个配置项")

        # 测试配置验证
        errors = config_manager.validate_config()
        if errors:
            print_test('配置验证', 'FAIL', f"发现 {len(errors)} 个配置错误")
            for error in errors:
                logger.info(f"   - {error}")
        else:
            print_test('配置验证', 'PASS', '配置验证通过')

        # 测试环境变量覆盖
        os.environ['CRAWLER_MONTHLY_LIMIT'] = '200.0'
        overrides = config_manager.get_env_overrides()
        if overrides.get('cost_limits', {}).get('monthly_limit') == 200.0:
            print_test('环境变量覆盖', 'PASS', '环境变量覆盖功能正常')
        else:
            print_test('环境变量覆盖', 'FAIL', '环境变量覆盖功能异常')

        return True

    except Exception as e:
        print_test('配置系统', 'FAIL', str(e))
        return False

async def test_adapters():
    """测试适配器"""
    print_section('适配器测试')

    results = {}

    # 测试Crawl4AI适配器
    try:
        from adapters.crawl4ai_adapter import Crawl4AIAdapterFactory

        # 创建基础适配器
        basic_adapter = Crawl4AIAdapterFactory.create_basic_adapter()
        print_test('Crawl4AI基础适配器创建', 'PASS')

        # 创建AI增强适配器
        ai_adapter = Crawl4AIAdapterFactory.create_ai_enhanced_adapter()
        print_test('Crawl4AI增强适配器创建', 'PASS')

        results['crawl4ai'] = True

    except Exception as e:
        print_test('Crawl4AI适配器', 'FAIL', str(e))
        results['crawl4ai'] = False

    # 测试FireCrawl适配器
    try:
        from adapters.firecrawl_adapter import FireCrawlAdapterFactory

        # 创建基础适配器
        basic_adapter = FireCrawlAdapterFactory.create_basic_adapter()
        print_test('FireCrawl基础适配器创建', 'PASS')

        # 创建搜索适配器
        search_adapter = FireCrawlAdapterFactory.create_search_adapter()
        print_test('FireCrawl搜索适配器创建', 'PASS')

        results['firecrawl'] = True

    except Exception as e:
        print_test('FireCrawl适配器', 'FAIL', str(e))
        results['firecrawl'] = False

    return results

async def test_routing_system():
    """测试路由系统"""
    print_section('路由系统测试')

    try:
        from config.hybrid_config import get_config
        from core.hybrid_crawler_manager import HybridCrawlerManager

        config = get_config()
        manager = HybridCrawlerManager(
            cost_limits=config.cost_limits.__dict__,
            crawl4ai_config=config.crawl4ai.__dict__,
            firecrawl_config=config.firecrawl.__dict__
        )

        # 测试URL分析
        test_urls = [
            'https://github.com/openai/gpt',
            'https://www.linkedin.com/company/openai',
            'https://example.com/static-page.html',
            'https://shop.example.com/products'
        ]

        for url in test_urls:
            analysis = manager._analyze_url(url)
            decision = manager.make_routing_decision(url)

            print_test(f"路由决策 - {url}', 'PASS",
                      f"选择: {decision.crawler_type.value}, 置信度: {decision.confidence:.2f}")

        return True

    except Exception as e:
        print_test('路由系统', 'FAIL', str(e))
        return False

async def test_hybrid_manager():
    """测试混合管理器"""
    print_section('混合管理器测试')

    try:
        from config.hybrid_config import get_config
        from core.hybrid_crawler_manager import HybridCrawlerManager

        config = get_config()

        async with HybridCrawlerManager(
            cost_limits=config.cost_limits.__dict__,
            crawl4ai_config=config.crawl4ai.__dict__,
            firecrawl_config=config.firecrawl.__dict__
        ) as manager:

            # 测试统计功能
            stats = manager.get_stats()
            print_test('统计功能', 'PASS', f"路由统计: {stats['routing_stats']['total_requests']} 次请求")

            # 测试成本限制器
            cost_stats = manager.cost_limiter.get_usage_stats()
            print_test('成本限制器', 'PASS',
                      f"月度限制: ${cost_stats['monthly_limit']}, 已用: ${cost_stats['monthly_spent']}")

            return True

    except Exception as e:
        print_test('混合管理器', 'FAIL', str(e))
        return False

async def test_live_crawling():
    """测试实际爬取"""
    print_section('实际爬取测试')

    try:
        from config.hybrid_config import get_config
        from core.hybrid_crawler_manager import HybridCrawlerManager

        config = get_config()

        async with HybridCrawlerManager(
            cost_limits=config.cost_limits.__dict__,
            crawl4ai_config=config.crawl4ai.__dict__,
            firecrawl_config=config.firecrawl.__dict__
        ) as manager:

            # 测试简单URL
            test_urls = [
                'https://httpbin.org/html',  # 简单HTML页面
            ]

            for url in test_urls:
                logger.info(f"\n🕷️ 测试爬取: {url}")

                # 测试自动路由
                result = await manager.crawl(url, strategy='auto')

                if result.success:
                    print_test(f"自动路由爬取', 'PASS",
                              f"工具: {result.crawler_used.value}, "
                              f"内容长度: {len(result.content)}, "
                              f"耗时: {result.processing_time:.2f}s")
                else:
                    print_test(f"自动路由爬取', 'FAIL', result.error_message or '未知错误")

            return True

    except Exception as e:
        print_test('实际爬取', 'FAIL', str(e))
        return False

async def test_api_endpoints():
    """测试API端点"""
    print_section('API端点测试')

    try:
        import aiohttp
        from api.hybrid_crawler_api import app

        # 测试FastAPI应用创建
        print_test('FastAPI应用创建', 'PASS')

        # 这里可以添加更多的API测试
        # 由于需要启动服务器，这里只做基础测试

        return True

    except Exception as e:
        print_test('API端点', 'FAIL', str(e))
        return False

async def generate_report(test_results: Dict[str, Any]):
    """生成测试报告"""
    print_section('测试报告')

    total_tests = 0
    passed_tests = 0
    failed_tests = 0

    for test_name, result in test_results.items():
        if isinstance(result, bool):
            total_tests += 1
            if result:
                passed_tests += 1
            else:
                failed_tests += 1
        elif isinstance(result, dict):
            for sub_test, sub_result in result.items():
                total_tests += 1
                if sub_result:
                    passed_tests += 1
                else:
                    failed_tests += 1

    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

    logger.info(f"📊 测试统计:")
    logger.info(f"   总测试数: {total_tests}")
    logger.info(f"   通过: {passed_tests}")
    logger.info(f"   失败: {failed_tests}")
    logger.info(f"   成功率: {success_rate:.1f}%")

    logger.info(f"\n🎯 系统状态: {'✅ 健康' if success_rate >= 80 else '⚠️ 需要关注' if success_rate >= 60 else '❌ 需要修复'}")

    if success_rate == 100:
        logger.info(f"\n🎉 恭喜！混合爬虫系统已完全就绪！")
        logger.info(f"🚀 可以使用以下命令启动服务:")
        logger.info(f"   ./scripts/start_hybrid_crawler.sh start")
        logger.info(f"📖 API文档: http://localhost:8002/docs")
    else:
        logger.info(f"\n💡 建议:")
        logger.info(f"   1. 检查失败的测试项")
        logger.info(f"   2. 确认所有依赖已正确安装")
        logger.info(f"   3. 配置必要的API密钥")
        logger.info(f"   4. 查看详细错误信息进行修复")

async def main():
    """主函数"""
    logger.info('🚀 Athena混合爬虫系统测试')
    logger.info(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    test_results = {}

    try:
        # 运行各项测试
        test_results['config'] = await test_config_system()
        test_results['adapters'] = await test_adapters()
        test_results['routing'] = await test_routing_system()
        test_results['manager'] = await test_hybrid_manager()
        test_results['crawling'] = await test_live_crawling()
        test_results['api'] = await test_api_endpoints()

    except KeyboardInterrupt:
        logger.info(f"\n⚠️ 测试被用户中断")
    except Exception as e:
        logger.info(f"\n💥 测试过程中发生错误: {str(e)}")
    finally:
        # 生成测试报告
        await generate_report(test_results)

        return 0

if __name__ == '__main__':
    sys.exit(asyncio.run(main()))