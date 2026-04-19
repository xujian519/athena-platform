#!/usr/bin/env python3
"""
联网搜索引擎命令行工具
Web Search Engine CLI Tool

作者: 小娜 & 小诺
创建时间: 2025-12-04
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.search.external.web_search_engines import (
    SearchEngineType,
    get_web_search_manager,
    quick_search,
)


async def search_command(query: str, engine: str = 'tavily', max_results: int = 10):
    """搜索命令"""
    logger.info(f"🔍 正在搜索: {query}")
    logger.info(f"🔧 搜索引擎: {engine}")
    logger.info(f"📊 最大结果数: {max_results}")
    logger.info(str('-' * 60))

    try:
        if engine.lower() == 'all':
            # 多引擎搜索
            manager = get_web_search_manager()
            result = await manager.search(
                query,
                engines=[SearchEngineType.TAVILY, SearchEngineType.GOOGLE_CUSTOM_SEARCH],
                max_results=max_results
            )
        else:
            # 单引擎搜索
            result = await quick_search(query, engine, max_results=max_results)

        if result.success:
            logger.info("✅ 搜索成功!")
            logger.info(f"⏱️  搜索耗时: {result.search_time:.2f}秒")
            logger.info(f"🔑 API密钥: {result.api_key_used}")
            logger.info(f"📈 结果数量: {result.total_results}")
            logger.info(f"🌐 搜索引擎: {result.engine}")
            print()

            # 显示搜索结果
            for i, item in enumerate(result.results, 1):
                logger.info(f"{i}. {item.title}")
                logger.info(f"   🔗 {item.url}")
                logger.info(f"   📝 {item.snippet[:150]}...")
                logger.info(f"   ⭐ 相关性: {item.relevance_score:.2f}")
                if item.metadata:
                    metadata_info = []
                    if 'published_date' in item.metadata and item.metadata['published_date']:
                        metadata_info.append(f"发布日期: {item.metadata['published_date']}")
                    if 'score' in item.metadata:
                        metadata_info.append(f"原始分数: {item.metadata['score']}")
                    if metadata_info:
                        logger.info(f"   📊 {', '.join(metadata_info)}")
                print()
        else:
            logger.info(f"❌ 搜索失败: {result.error_message}")
            logger.info(f"🌐 搜索引擎: {result.engine}")

    except Exception as e:
        logger.info(f"❌ 搜索异常: {e}")
        import traceback
        traceback.print_exc()

async def compare_command(query: str, engines: list = None):
    """对比搜索引擎结果"""
    if engines is None:
        engines = ['tavily', 'bocha']

    logger.info(f"🔍 搜索对比: {query}")
    logger.info(f"🔧 对比引擎: {', '.join(engines)}")
    logger.info(str('=' * 80))

    manager = get_web_search_manager()
    results = {}

    # 逐个引擎搜索
    for engine_name in engines:
        try:
            logger.info(f"\n🌐 搜索引擎: {engine_name}")
            logger.info(str('-' * 40))

            engine_type = SearchEngineType(engine_name)
            result = await manager.search(query, [engine_type], max_results=5)

            if result.success:
                results[engine_name] = result
                logger.info(f"✅ 搜索成功 - {result.total_results}个结果 ({result.search_time:.2f}s)")

                # 显示前2个结果
                for i, item in enumerate(result.results[:2], 1):
                    logger.info(f"  {i}. {item.title}")
                    logger.info(f"     {item.snippet[:100]}...")
            else:
                logger.info(f"❌ 搜索失败: {result.error_message}")
                results[engine_name] = None

        except Exception as e:
            logger.info(f"❌ {engine_name} 搜索异常: {e}")
            results[engine_name] = None

    # 对比总结
    logger.info(str("\n" + '=' * 80))
    logger.info('📊 对比总结:')

    for engine_name, result in results.items():
        if result and result.success:
            logger.info(f"✅ {engine_name:20} | {result.total_results:3} 结果 | {result.search_time:5.2f}s | {result.api_key_used}")
        else:
            logger.info(f"❌ {engine_name:20} | 失败")

async def stats_command():
    """显示搜索引擎统计信息"""
    logger.info('📊 搜索引擎统计信息')
    logger.info(str('=' * 60))

    try:
        manager = get_web_search_manager()
        stats = manager.get_engine_stats()

        logger.info(f"🔧 可用引擎数量: {len(stats['available_engines'])}")
        logger.info("🌐 已配置引擎:")
        for engine_type in stats['available_engines']:
            engine_info = stats.get(engine_type.value, {})
            if engine_info:
                logger.info(f"  ✅ {engine_type.value:20} | {engine_info.get('name', 'N/A'):20} | {engine_info.get('configured_keys', 0)} 密钥")
            else:
                logger.info(f"  ⚠️  {engine_type.value:20} | 未配置")

        logger.info("\n🔑 API密钥统计:")
        api_stats = stats.get('api_key_stats', {})
        for engine_name, engine_stats in api_stats.items():
            if engine_stats and engine_stats.get('usage_stats'):
                logger.info(f"\n🌐 {engine_name}:")
                usage_stats = engine_stats['usage_stats']
                failure_stats = engine_stats['failure_stats']
                last_used = engine_stats['last_used']

                for key, usage in usage_stats.items():
                    failures = failure_stats.get(key, 0)
                    last_time = last_used.get(key, 'N/A')
                    masked_key = key[:8] + '***' if len(key) > 8 else key
                    logger.info(f"  🔑 {masked_key:15} | 使用: {usage:3} | 失败: {failures:3} | 最后使用: {last_time}")

    except Exception as e:
        logger.info(f"❌ 获取统计信息失败: {e}")

async def test_api_rotation_command(query: str, count: int = 5):
    """测试API密钥轮换"""
    logger.info("🔄 测试API密钥轮换")
    logger.info(f"🔍 测试查询: {query}")
    logger.info(f"🔢 测试次数: {count}")
    logger.info(str('=' * 60))

    manager = get_web_search_manager()
    api_keys_used = {}

    for i in range(count):
        try:
            logger.info(f"\n🔍 第 {i+1} 次搜索...")
            result = await manager.search(query, [SearchEngineType.TAVILY], max_results=1)

            if result.success:
                api_key = result.api_key_used
                logger.info(f"✅ 成功 - API密钥: {api_key} - 耗时: {result.search_time:.2f}s")

                if api_key not in api_keys_used:
                    api_keys_used[api_key] = 0
                api_keys_used[api_key] += 1
            else:
                logger.info(f"❌ 失败: {result.error_message}")

        except Exception as e:
            logger.info(f"❌ 异常: {e}")

    # 显示轮换统计
    logger.info("\n📊 API密钥轮换统计:")
    for api_key, times in api_keys_used.items():
        logger.info(f"  🔑 {api_key}: {times} 次")

    if len(api_keys_used) > 1:
        logger.info("✅ API密钥轮换正常工作!")
    else:
        logger.info("⚠️  只使用了1个API密钥，轮换可能未生效")

def create_sample_config():
    """创建示例配置文件"""
    sample_config = {
        'api_keys': {
            'tavily': [
                'tvly-dev-YOUR_FIRST_API_KEY',
                'tvly-dev-YOUR_SECOND_API_KEY'
            ],
            'google_custom_search': [
                'YOUR_GOOGLE_API_KEY'
            ],
            'metaso': [
                'mk-YOUR_METASO_API_KEY_1',
                'mk-YOUR_METASO_API_KEY_2'
            ]
        },
        'engine_configs': {
            'tavily': {
                'timeout': 30,
                'max_results_per_request': 10
            },
            'google_custom_search': {
                'search_engine_id': 'YOUR_SEARCH_ENGINE_ID',
                'timeout': 30
            },
            'metaso': {
                'timeout': 30,
                'max_results_per_request': 10
            }
        },
        'engine_priorities': [
            'tavily',
            'metaso',
            'bocha',
            'google_custom_search'
        ],
        'default_settings': {
            'max_results': 10,
            'language': 'zh-CN',
            'region': 'CN',
            'safe_search': 'moderate'
        }
    }

    config_file = Path('web_search_config.json')
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(sample_config, f, indent=2, ensure_ascii=False)

    logger.info(f"✅ 示例配置文件已创建: {config_file}")
    logger.info("📝 请编辑配置文件，添加您的API密钥")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='联网搜索引擎命令行工具')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # 搜索命令
    search_parser = subparsers.add_parser('search', help='执行搜索')
    search_parser.add_argument('query', help='搜索查询')
    search_parser.add_argument('--engine', default='tavily', help='搜索引擎 (tavily, bocha, metaso, deepsearch, google_custom_search, all)')
    search_parser.add_argument('--max-results', type=int, default=10, help='最大结果数')

    # 对比命令
    compare_parser = subparsers.add_parser('compare', help='对比搜索引擎')
    compare_parser.add_argument('query', help='搜索查询')
    compare_parser.add_argument('--engines', nargs='+', default=['tavily', 'deepsearch'], help='要对比的引擎')

    # 统计命令
    subparsers.add_parser('stats', help='显示统计信息')

    # 测试API轮换命令
    rotation_parser = subparsers.add_parser('test-rotation', help='测试API密钥轮换')
    rotation_parser.add_argument('query', help='测试查询')
    rotation_parser.add_argument('--count', type=int, default=5, help='测试次数')

    # 创建配置文件命令
    subparsers.add_parser('create-config', help='创建示例配置文件')

    args = parser.parse_args()

    if args.command == 'search':
        asyncio.run(search_command(args.query, args.engine, args.max_results))
    elif args.command == 'compare':
        asyncio.run(compare_command(args.query, args.engines))
    elif args.command == 'stats':
        asyncio.run(stats_command())
    elif args.command == 'test-rotation':
        asyncio.run(test_api_rotation_command(args.query, args.count))
    elif args.command == 'create-config':
        create_sample_config()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
