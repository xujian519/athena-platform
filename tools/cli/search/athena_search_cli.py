#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Athena搜索平台命令行工具
Athena Search Platform CLI Tool

小诺和小娜的全功能搜索命令行接口

控制者: 小诺 & 小娜
创建时间: 2025-12-11
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
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tools.search.athena_search_platform import (
    AthenaSearchPlatform,
    analyze_competitor,
    get_search_platform,
    patent_research,
    quick_search,
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
    logger.info('║                    Athena搜索平台                          ║')
    logger.info('║                 命令行工具 v1.0.0                           ║')
    logger.info('║                   控制者: 小诺 & 小娜                        ║')
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
    total_found = results.get('total_found', 0)
    search_time = results.get('search_time', 0)
    sources_used = results.get('sources_used', [])
    results_list = results.get('results', [])

    print_result(f"搜索结果 - 查询: '{query}'")
    logger.info(f"   找到: {total_found} 个结果")
    logger.info(f"   耗时: {search_time:.2f}秒")
    logger.info(f"   来源: {', '.join(sources_used)}")
    logger.info(str('-' * 60))

    for i, result in enumerate(results_list, 1):
        rank = result.get('rank', i)
        title = result.get('title', '无标题')
        relevance = result.get('relevance_score', 0)
        source = result.get('source', 'unknown')
        url = result.get('url', '')

        logger.info(f"{rank}. {title}")
        logger.info(f"   相关性: {relevance:.2f} | 来源: {source}")

        if url and show_details:
            logger.info(f"   链接: {url}")

        content = result.get('content', '')
        if show_details and content:
            # 显示内容摘要
            preview = content[:200] + '...' if len(content) > 200 else content
            logger.info(f"   预览: {preview}")

        print()

def format_research_results(results: Dict[str, Any], show_details: bool = False):
    """格式化研究结果显示"""
    if results.get('status') == 'error':
        print_error(f"研究失败: {results.get('error', '未知错误')}")
        return

    topic = results.get('research_topic', '')
    total_patents = results.get('total_patents_found', 0)
    iterations = results.get('total_iterations', 0)
    unique_patents = results.get('unique_patents', 0)

    print_result(f"智能专利研究 - 主题: '{topic}'")
    logger.info(f"   总专利数: {total_patents}")
    logger.info(f"   唯一专利: {unique_patents}")
    logger.info(f"   迭代轮数: {iterations}")
    logger.info(str('-' * 60))

    # 显示迭代结果
    iteration_list = results.get('iterations', [])
    if show_details and iteration_list:
        logger.info('🔄 搜索迭代详情:')
        for iteration in iteration_list:
            iter_num = iteration.get('iteration', 0)
            query = iteration.get('query', '')
            count = iteration.get('results_count', 0)
            logger.info(f"   第{iter_num}轮: '{query}' -> 找到{count}个结果")

    # 显示研究摘要
    summary = results.get('research_summary', {})
    if summary:
        logger.info("\n📋 研究摘要:")

        insights = summary.get('main_insights', [])
        if insights:
            logger.info('   💡 主要发现:')
            for insight in insights[:3]:  # 显示前3个
                logger.info(f"     • {insight}")

        companies = summary.get('key_companies', [])
        if companies:
            logger.info(f"   🏢 关键公司: {', '.join(companies[:5])}")  # 显示前5个

        trends = summary.get('technology_trends', [])
        if trends:
            logger.info('   📈 技术趋势:')
            for trend in trends[:3]:  # 显示前3个
                logger.info(f"     • {trend}")

def format_analysis_results(results: Dict[str, Any], show_details: bool = False):
    """格式化竞争分析结果显示"""
    if results.get('status') == 'error':
        print_error(f"分析失败: {results.get('error', '未知错误')}")
        return

    company = results.get('company_name', '')
    domain = results.get('technology_domain', '全部领域')
    total_patents = results.get('total_patents', 0)

    print_result(f"竞争分析 - 公司: '{company}'")
    logger.info(f"   技术领域: {domain}")
    logger.info(f"   专利总数: {total_patents}")
    logger.info(str('-' * 60))

    # 显示分析摘要
    summary = results.get('analysis_summary', {})
    if summary:
        logger.info('📊 分析摘要:')

        strength = summary.get('patent_strength', 'unknown')
        position = summary.get('technology_position', 'unknown')
        logger.info(f"   💪 专利实力: {strength}")
        logger.info(f"   🎯 技术定位: {position}")

        advantages = summary.get('market_advantages', [])
        if advantages and show_details:
            logger.info('   ✅ 市场优势:')
            for advantage in advantages[:3]:
                logger.info(f"     • {advantage}")

        threats = summary.get('competitive_threats', [])
        if threats and show_details:
            logger.info('   ⚠️ 竞争威胁:')
            for threat in threats[:3]:
                logger.info(f"     • {threat}")

async def handle_search_command(args):
    """处理搜索命令"""
    print_info(f"开始搜索: '{args.query}'")

    try:
        if args.quick:
            # 使用快速搜索
            results = await quick_search(args.query, args.max_results)
        else:
            # 使用平台搜索
            platform = get_search_platform()
            results = await platform.simple_search(
                query=args.query,
                max_results=args.max_results,
                search_type=args.type
            )

        format_search_results(results, show_details=args.verbose)

    except Exception as e:
        print_error(f"搜索过程中出错: {e}")

async def handle_research_command(args):
    """处理研究命令"""
    print_info(f"开始专利研究: '{args.topic}'")

    try:
        results = await patent_research(args.topic, args.depth)
        format_research_results(results, show_details=args.verbose)

    except Exception as e:
        print_error(f"研究过程中出错: {e}")

async def handle_analysis_command(args):
    """处理分析命令"""
    company_info = args.company
    if args.domain:
        company_info += f" (领域: {args.domain})"

    print_info(f"开始竞争分析: '{company_info}'")

    try:
        results = await analyze_competitor(args.company, args.domain)
        format_analysis_results(results, show_details=args.verbose)

    except Exception as e:
        print_error(f"分析过程中出错: {e}")

async def handle_status_command(args):
    """处理状态命令"""
    print_info('获取平台状态...')

    try:
        platform = get_search_platform()
        status = await platform.platform_status()

        print_result('Athena搜索平台状态')
        logger.info(str('-' * 40))
        logger.info(f"平台名称: {status['platform']['name']}")
        logger.info(f"版本: {status['platform']['version']}")
        logger.info(f"控制者: {', '.join(status['platform']['controllers'])}")
        logger.info(f"状态: {status['platform']['uptime']}")
        logger.info(f"整体健康: {status.get('overall_health', 'unknown')}")

        logger.info("\n组件状态:")
        for component, comp_status in status['components'].items():
            logger.info(f"  {component}: {comp_status}")

        logger.info("\n配置状态:")
        for config_item, config_status in status['configuration'].items():
            logger.info(f"  {config_item}: {config_status}")

        if args.verbose:
            logger.info(f"\n最后更新: {status['timestamp']}")
            health_check = status.get('health_check', {})
            if health_check:
                logger.info('健康检查详情:')
                for key, value in health_check.items():
                    logger.info(f"  {key}: {value}")

    except Exception as e:
        print_error(f"获取状态失败: {e}")

async def handle_manual_command(args):
    """处理手册命令"""
    print_info('显示用户手册...')

    try:
        platform = get_search_platform()
        manual = platform.get_user_manual()

        print_result(f"{manual['title']} v{manual['version']}")
        logger.info(f"控制者: {', '.join(manual['controllers'])}")

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

            # 搜索类型
            search_types = manual.get('search_types', {})
            if search_types:
                logger.info("\n搜索类型:")
                for stype, desc in search_types.items():
                    logger.info(f"  {stype}: {desc}")

            # 搜索深度
            depths = manual.get('search_depths', {})
            if depths:
                logger.info("\n搜索深度:")
                for depth, desc in depths.items():
                    logger.info(f"  {depth}: {desc}")

            # 功能特性
            features = manual.get('features', {})
            if features:
                logger.info("\n🎯 核心功能:")
                for feature, desc in features.items():
                    logger.info(f"  {feature}: {desc}")

    except Exception as e:
        print_error(f"获取手册失败: {e}")

def create_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description='Athena搜索平台命令行工具 - 小诺和小娜的全功能搜索接口',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 简单搜索
  python athena_search_cli.py search '人工智能专利' --max-results 5

  # 快速搜索
  python athena_search_cli.py search '机器学习' --quick

  # 专利研究
  python athena_search_cli.py research '深度学习算法' --depth comprehensive

  # 竞争分析
  python athena_search_cli.py analysis '华为' --domain '5G通信'

  # 平台状态
  python athena_search_cli.py status --verbose

  # 用户手册
  python athena_search_cli.py manual
        """
    )

    parser.add_argument(
        '--version',
        action='version',
        version='Athena搜索平台 v1.0.0'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='显示详细信息'
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # 搜索命令
    search_parser = subparsers.add_parser('search', help='执行搜索查询')
    search_parser.add_argument('query', help='搜索查询字符串')
    search_parser.add_argument('--max-results', '-n', type=int, default=10, help='最大结果数量 (默认: 10)')
    search_parser.add_argument('--type', '-t', choices=['internal', 'external', 'hybrid'],
                               default='hybrid', help='搜索类型 (默认: hybrid)')
    search_parser.add_argument('--quick', '-q', action='store_true', help='使用快速搜索模式')

    # 研究命令
    research_parser = subparsers.add_parser('research', help='执行智能专利研究')
    research_parser.add_argument('topic', help='研究主题')
    research_parser.add_argument('--depth', '-d',
                                choices=['quick', 'standard', 'comprehensive', 'deep'],
                                default='comprehensive', help='搜索深度 (默认: comprehensive)')

    # 分析命令
    analysis_parser = subparsers.add_parser('analysis', help='执行竞争分析')
    analysis_parser.add_argument('company', help='公司名称')
    analysis_parser.add_argument('--domain', help='技术领域')

    # 状态命令
    status_parser = subparsers.add_parser('status', help='显示平台状态')

    # 手册命令
    manual_parser = subparsers.add_parser('manual', help='显示用户手册')

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
        elif args.command == 'research':
            await handle_research_command(args)
        elif args.command == 'analysis':
            await handle_analysis_command(args)
        elif args.command == 'status':
            await handle_status_command(args)
        elif args.command == 'manual':
            await handle_manual_command(args)
        else:
            print_error(f"未知命令: {args.command}")
            parser.print_help()

    except KeyboardInterrupt:
        print_warning("\n用户中断操作")
    except Exception as e:
        print_error(f"程序执行出错: {e}")

if __name__ == '__main__':
    asyncio.run(main())