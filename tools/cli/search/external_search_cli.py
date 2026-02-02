#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Athena外部搜索平台命令行工具
Athena External Search Platform CLI Tool

小诺和Athena的全功能外部搜索命令行接口

控制者: 小诺 & Athena
创建时间: 2025年12月11日
版本: 1.0.0
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.search.external_search_platform import (
    ExternalSearchPlatform,
    comprehensive_search,
    get_external_search_platform,
    quick_web_search,
    smart_web_search,
)

# 颜色定义
GREEN = '\033[92m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RED = '\033[91m'
PURPLE = '\033[95m'
CYAN = '\033[96m'
WHITE = '\033[97m'
BOLD = '\033[1m'
END = '\033[0m'

def print_banner():
    """打印平台横幅"""
    logger.info(f"{PURPLE}{BOLD}")
    logger.info('╔════════════════════════════════════════════════════════════╗')
    logger.info('║                Athena外部搜索平台                        ║')
    logger.info('║               命令行工具 v1.0.0                           ║')
    logger.info('║                  控制者: 小诺 & Athena                      ║')
    logger.info('╚════════════════════════════════════════════════════════════╝')
    logger.info(f"{END}")

def print_success(message: str):
    logger.info(f"{GREEN}✅ {message}{END}")

def print_info(message: str):
    logger.info(f"{BLUE}ℹ️  {message}{END}")

def print_warning(message: str):
    logger.info(f"{YELLOW}⚠️  {message}{END}")

def print_error(message: str):
    logger.info(f"{RED}❌ {message}{END}")

def print_result(message: str):
    logger.info(f"{CYAN}📊 {message}{END}")

def format_search_results(results: Dict[str, Any], show_details: bool = False):
    """格式化搜索结果显示"""
    if results.get('status') == 'error':
        print_error(f"搜索失败: {results.get('error', '未知错误')}")
        return

    query = results.get('query', '')
    engine = results.get('engine', 'unknown')
    total_found = results.get('total_found', 0)
    search_time = results.get('search_time', 0)
    results_list = results.get('results', [])

    print_result(f"搜索结果 - 查询: '{query}'")
    logger.info(f"   引擎: {engine}")
    logger.info(f"   找到: {total_found} 个结果")
    logger.info(f"   耗时: {search_time:.2f}秒")
    logger.info(str('-' * 60))

    for i, result in enumerate(results_list, 1):
        rank = result.get('rank', i)
        title = result.get('title', '无标题')
        url = result.get('url', '')
        snippet = result.get('snippet', '')
        relevance = result.get('relevance_score', 0)

        logger.info(f"{rank}. {title}")
        logger.info(f"   🔗 {url}")
        logger.info(f"   📈 相关性: {relevance:.2f}")

        if snippet:
            # 显示内容摘要
            if show_details:
                preview = snippet
            else:
                preview = snippet[:150] + '...' if len(snippet) > 150 else snippet
            logger.info(f"   📄 预览: {preview}")

        print()

def format_multi_engine_results(results: Dict[str, Any], show_details: bool = False):
    """格式化多引擎搜索结果显示"""
    if results.get('status') == 'error':
        print_error(f"多引擎搜索失败: {results.get('error', '未知错误')}")
        return

    query = results.get('query', '')
    engines_used = results.get('engines_used', [])
    successful_engines = results.get('successful_engines', [])
    total_found = results.get('total_found', 0)

    print_result(f"多引擎搜索结果 - 查询: '{query}'")
    logger.info(f"   使用引擎: {', '.join(engines_used)}")
    logger.info(f"   成功引擎: {', '.join(successful_engines)}")
    logger.info(f"   总结果数: {total_found}")
    logger.info(str('-' * 60))

    # 显示各引擎结果
    engine_results = results.get('engine_results', {})
    for engine, result in engine_results.items():
        engine_status = result.get('status', 'unknown')
        engine_results_count = len(result.get('results', []))

        logger.info(f"🔍 {engine.upper()} 引擎:")
        logger.info(f"   状态: {engine_status}")
        logger.info(f"   结果数: {engine_results_count}")

        if engine_status == 'success' and result.get('results'):
            logger.info('   前3个结果:')
            for i, item in enumerate(result['results'][:3], 1):
                title = item.get('title', '无标题')
                url = item.get('url', '')
                logger.info(f"     {i}. {title}")
                logger.info(f"        🔗 {url}")

        print()

    # 显示合并结果（如果有）
    if results.get('results'):
        logger.info('🏆 最佳合并结果:')
        logger.info(str('-' * 30))
        for i, result in enumerate(results['results'][:5], 1):
            title = result.get('title', '无标题')
            url = result.get('url', '')
            relevance = result.get('relevance_score', 0)
            logger.info(f"{i}. {title} (相关性: {relevance:.2f})")
            logger.info(f"   🔗 {url}")
        print()

async def handle_search_command(args):
    """处理单引擎搜索命令"""
    print_info(f"开始搜索: '{args.query}' (引擎: {args.engine})")

    try:
        if args.quick:
            # 使用快速搜索
            results = await quick_web_search(args.query, args.engine, args.max_results)
        else:
            # 使用平台搜索
            platform = get_external_search_platform()
            results = await platform.search_with_engine(
                query=args.query,
                engine=args.engine,
                max_results=args.max_results,
                language=args.language
            )

        format_search_results(results, show_details=args.verbose)

    except Exception as e:
        print_error(f"搜索过程中出错: {e}")

async def handle_multi_search_command(args):
    """处理多引擎搜索命令"""
    engines = args.engines.split(',') if args.engines else ['tavily', 'metaso']
    print_info(f"开始多引擎搜索: '{args.query}' (引擎: {', '.join(engines)})")

    try:
        platform = get_external_search_platform()
        results = await platform.multi_engine_search(
            query=args.query,
            engines=engines,
            max_results=args.max_results,
            combine_results=not args.separate
        )

        if args.separate:
            format_multi_engine_results(results, show_details=args.verbose)
        else:
            format_search_results(results, show_details=args.verbose)

    except Exception as e:
        print_error(f"多引擎搜索过程中出错: {e}")

async def handle_smart_command(args):
    """处理智能搜索命令"""
    print_info(f"开始智能搜索: '{args.query}' (优化: {args.optimize})")

    try:
        if args.quick:
            # 使用快速智能搜索
            results = await smart_web_search(args.query, args.max_results, args.optimize)
        else:
            # 使用平台智能搜索
            platform = get_external_search_platform()
            results = await platform.smart_search(
                query=args.query,
                max_results=args.max_results,
                optimize_for=args.optimize
            )

        format_search_results(results, show_details=args.verbose)

    except Exception as e:
        print_error(f"智能搜索过程中出错: {e}")

async def handle_comprehensive_command(args):
    """处理全面搜索命令"""
    print_info(f"开始全面搜索: '{args.query}'")

    try:
        results = await comprehensive_search(args.query, args.max_results)
        format_multi_engine_results(results, show_details=args.verbose)

    except Exception as e:
        print_error(f"全面搜索过程中出错: {e}")

async def handle_status_command(args):
    """处理状态命令"""
    print_info('获取外部搜索平台状态...')

    try:
        platform = get_external_search_platform()
        status = await platform.get_platform_status()

        print_result('Athena外部搜索平台状态')
        logger.info(str('-' * 40))
        logger.info(f"平台名称: {status['platform']['name']}")
        logger.info(f"版本: {status['platform']['version']}")
        logger.info(f"控制者: {', '.join(status['platform']['controllers'])}")
        logger.info(f"状态: {'已初始化' if status['platform']['initialized'] else '未初始化'}")

        logger.info("\n引擎状态:")
        for engine, eng_status in status['engines'].items():
            status_text = eng_status.get('status', 'unknown')
            if status_text == 'available':
                status_icon = '✅'
            elif status_text == 'disabled':
                status_icon = '⭕'
            else:
                status_icon = '❌'
            logger.info(f"  {status_icon} {engine}: {status_text}")

        logger.info("\n配置状态:")
        for config_item, config_status in status['configuration'].items():
            enabled_text = '✅ 启用' if config_status else '❌ 禁用'
            logger.info(f"  {config_item}: {enabled_text}")

        if args.verbose:
            logger.info(f"\n统计信息:")
            stats = status.get('statistics', {})
            logger.info(f"  总搜索次数: {stats.get('total_searches', 0)}")
            logger.info(f"  成功次数: {stats.get('successful_searches', 0)}")
            logger.info(f"  失败次数: {stats.get('failed_searches', 0)}")

            engine_usage = stats.get('engine_usage', {})
            if engine_usage:
                logger.info('  引擎使用次数:')
                for engine, count in engine_usage.items():
                    logger.info(f"    {engine}: {count}")

    except Exception as e:
        print_error(f"获取状态失败: {e}")

async def handle_manual_command(args):
    """处理手册命令"""
    print_info('显示外部搜索平台用户手册...')

    try:
        platform = get_external_search_platform()
        manual = platform.get_user_manual()

        print_result(f"{manual['title']} v{manual['version']}")
        logger.info(f"控制者: {', '.join(manual['controllers'])}")

        logger.info("\n🔍 可用搜索引擎:")
        logger.info(str('-' * 40))
        engines = manual.get('engines', {})
        for name, info in engines.items():
            logger.info(f"\n{name}:")
            logger.info(f"  描述: {info['description']}")
            logger.info(f"  特性: {', '.join(info['features'])}")
            logger.info(f"  适用: {', '.join(info['best_for'])}")

        logger.info("\n🚀 快速开始:")
        logger.info(str('-' * 40))

        quick_start = manual.get('quick_start', {})
        for key, info in quick_start.items():
            logger.info(f"\n{info['description']}:")
            logger.info(f"  用法: {info['usage']}")
            if 'example' in info:
                logger.info(f"  示例: {info['example']}")

        if args.verbose:
            logger.info("\n📖 详细说明:")
            logger.info(str('-' * 40))

            # 优化选项
            optimizations = manual.get('optimization_options', {})
            if optimizations:
                logger.info("\n搜索优化选项:")
                for opt, desc in optimizations.items():
                    logger.info(f"  {opt}: {desc}")

    except Exception as e:
        print_error(f"获取手册失败: {e}")

async def handle_test_command(args):
    """处理测试命令"""
    print_info('测试外部搜索引擎...')

    try:
        platform = ExternalSearchPlatform()
        await platform.initialize()

        test_query = '人工智能最新发展'

        logger.info(f"\n🧪 测试查询: '{test_query}'")
        logger.info(str('=' * 50))

        # 测试Tavily
        logger.info("\n🔍 测试Tavily搜索引擎:")
        try:
            result = await platform.search_with_engine(test_query, 'tavily', max_results=3)
            if result.get('status') == 'success':
                print_success('✅ Tavily测试成功')
                logger.info(f"   结果数量: {len(result.get('results', []))}")
                logger.info(f"   搜索耗时: {result.get('search_time', 0):.2f}秒")
            else:
                print_warning(f"⚠️ Tavily测试失败: {result.get('error', '')}")
        except Exception as e:
            print_error(f"❌ Tavily测试异常: {e}")

        # 测试秘塔
        logger.info("\n🔍 测试秘塔搜索引擎:")
        try:
            result = await platform.search_with_engine(test_query, 'metaso', max_results=3)
            if result.get('status') == 'success':
                print_success('✅ 秘塔测试成功')
                logger.info(f"   结果数量: {len(result.get('results', []))}")
                logger.info(f"   搜索耗时: {result.get('search_time', 0):.2f}秒")
            else:
                print_warning(f"⚠️ 秘塔测试失败: {result.get('error', '')}")
        except Exception as e:
            print_error(f"❌ 秘塔测试异常: {e}")

        # 测试博查
        logger.info("\n🔍 测试博查搜索引擎:")
        try:
            result = await platform.search_with_engine(test_query, 'bocha', max_results=3)
            if result.get('status') == 'success':
                print_success('✅ 博查测试成功')
                logger.info(f"   结果数量: {len(result.get('results', []))}")
                logger.info(f"   搜索耗时: {result.get('search_time', 0):.2f}秒")
            else:
                print_warning(f"⚠️ 博查测试失败: {result.get('error', '')}")
        except Exception as e:
            print_error(f"❌ 博查测试异常: {e}")

        # 测试智能搜索
        logger.info("\n🧠 测试智能搜索:")
        try:
            result = await platform.smart_search(test_query, max_results=3)
            if result.get('status') == 'success':
                print_success('✅ 智能搜索测试成功')
                logger.info(f"   使用的引擎: {result.get('engine', 'unknown')}")
                logger.info(f"   结果数量: {len(result.get('results', []))}")
            else:
                print_warning(f"⚠️ 智能搜索测试失败: {result.get('error', '')}")
        except Exception as e:
            print_error(f"❌ 智能搜索测试异常: {e}")

        logger.info("\n🎉 外部搜索引擎测试完成！")

    except Exception as e:
        print_error(f"测试过程失败: {e}")

def create_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description='Athena外部搜索平台命令行工具 - 小诺和Athena的全功能搜索接口',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 单引擎搜索
  python external_search_cli.py search '人工智能' --engine tavily

  # 多引擎搜索
  python external_search_cli.py multi '机器学习' --engines 'tavily,metaso'

  # 智能搜索
  python external_search_cli.py smart '深度学习' --optimize completeness

  # 全面搜索
  python external_search_cli.py comprehensive '大数据分析'

  # 平台状态
  python external_search_cli.py status --verbose

  # 测试搜索引擎
  python external_search_cli.py test
        """
    )

    parser.add_argument(
        '--version',
        action='version',
        version='Athena外部搜索平台 v1.0.0'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='显示详细信息'
    )

    parser.add_argument(
        '--quick', '-q',
        action='store_true',
        help='使用快速搜索模式'
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # 单引擎搜索命令
    search_parser = subparsers.add_parser('search', help='执行单引擎搜索')
    search_parser.add_argument('query', help='搜索查询字符串')
    search_parser.add_argument('--engine', '-e', choices=['tavily', 'bocha', 'metaso'],
                               default='tavily', help='搜索引擎 (默认: tavily)')
    search_parser.add_argument('--max-results', '-n', type=int, default=10, help='最大结果数量 (默认: 10)')
    search_parser.add_argument('--language', '-l', default='zh-CN', help='搜索语言 (默认: zh-CN)')

    # 多引擎搜索命令
    multi_parser = subparsers.add_parser('multi', help='执行多引擎并行搜索')
    multi_parser.add_argument('query', help='搜索查询字符串')
    multi_parser.add_argument('--engines', help='搜索引擎列表，逗号分隔 (默认: tavily,metaso)')
    multi_parser.add_argument('--max-results', '-n', type=int, default=10, help='每个引擎最大结果数')
    multi_parser.add_argument('--separate', action='store_true', help='分别显示各引擎结果')

    # 智能搜索命令
    smart_parser = subparsers.add_parser('smart', help='执行智能搜索')
    smart_parser.add_argument('query', help='搜索查询字符串')
    smart_parser.add_argument('--max-results', '-n', type=int, default=10, help='最大结果数量')
    smart_parser.add_argument('--optimize', '-o', choices=['relevance', 'speed', 'completeness'],
                              default='relevance', help='优化目标 (默认: relevance)')

    # 全面搜索命令
    comprehensive_parser = subparsers.add_parser('comprehensive', help='执行全面搜索')
    comprehensive_parser.add_argument('query', help='搜索查询字符串')
    comprehensive_parser.add_argument('--max-results', '-n', type=int, default=15, help='最大结果数量')

    # 状态命令
    status_parser = subparsers.add_parser('status', help='显示平台状态')

    # 手册命令
    manual_parser = subparsers.add_parser('manual', help='显示用户手册')

    # 测试命令
    test_parser = subparsers.add_parser('test', help='测试搜索引擎功能')

    return parser

async def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()

    # 显示横幅
    print_banner()

    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == 'search':
            await handle_search_command(args)
        elif args.command == 'multi':
            await handle_multi_search_command(args)
        elif args.command == 'smart':
            await handle_smart_command(args)
        elif args.command == 'comprehensive':
            await handle_comprehensive_command(args)
        elif args.command == 'status':
            await handle_status_command(args)
        elif args.command == 'manual':
            await handle_manual_command(args)
        elif args.command == 'test':
            await handle_test_command(args)
        else:
            print_error(f"未知命令: {args.command}")
            parser.print_help()

    except KeyboardInterrupt:
        print_warning("\n用户中断操作")
    except Exception as e:
        print_error(f"程序执行出错: {e}")

if __name__ == '__main__':
    asyncio.run(main())