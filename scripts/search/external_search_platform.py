#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Athena外部搜索引擎平台
Athena External Search Engine Platform

集成Tavily、博查、秘塔等外部搜索引擎
为小诺和Athena提供全量控制的搜索能力

控制者: 小诺 & Athena
创建时间: 2025年12月11日
版本: 1.0.0
"""

import asyncio
import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# 导入搜索引擎
from core.search.external.web_search_engines import (
    APIKeyManager,
    BochaSearchEngine,
    MetasoSearchEngine,
    SearchEngineType,
    SearchQuery,
    SearchResponse,
    TavilySearchEngine,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ExternalSearchConfig:
    """外部搜索引擎配置"""
    enable_tavily: bool = True
    enable_bocha: bool = True
    enable_metaso: bool = True
    enable_fallback: bool = True
    max_results: int = 10
    search_timeout: int = 30
    retry_attempts: int = 3
    cache_enabled: bool = True
    debug_mode: bool = False

class ExternalSearchPlatform:
    """
    外部搜索引擎平台主类
    为小诺和Athena提供全量控制的搜索功能
    """

    def __init__(self, config: ExternalSearchConfig | None = None):
        """
        初始化外部搜索平台

        Args:
            config: 平台配置
        """
        self.config = config or ExternalSearchConfig()
        self.version = '1.0.0'
        self.controllers = ['小诺', 'Athena']

        # 搜索引擎实例
        self.tavily_engine = None
        self.bocha_engine = None
        self.metaso_engine = None
        self.api_key_manager = None

        # 平台状态
        self.initialized = False
        self.search_stats = {
            'total_searches': 0,
            'successful_searches': 0,
            'failed_searches': 0,
            'engine_usage': {},
            'last_search_time': None
        }

        logger.info(f"🔍 Athena外部搜索平台 v{self.version} - 控制者: {', '.join(self.controllers)}")

    async def initialize(self):
        """初始化搜索平台"""
        if self.initialized:
            return

        logger.info('🚀 初始化Athena外部搜索平台...')

        try:
            # 1. 加载API密钥配置
            await self._load_api_keys()

            # 2. 初始化搜索引擎
            await self._initialize_engines()

            self.initialized = True
            logger.info('🎉 Athena外部搜索平台初始化完成！')

        except Exception as e:
            logger.error(f"❌ 外部搜索平台初始化失败: {e}")
            raise

    async def _load_api_keys(self):
        """加载API密钥配置"""
        try:
            # 读取配置文件
            config_path = Path(__file__).parent.parent.parent / 'core/search/config/search_api_config.json'

            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            api_keys = {}
            search_config = config_data.get('search_api_keys', {})

            # Tavily API密钥
            if self.config.enable_tavily and search_config.get('tavily', {}).get('enabled'):
                tavily_key = search_config['tavily']['api_key']
                if tavily_key:
                    api_keys['tavily'] = [tavily_key]

            # 博查API密钥
            if self.config.enable_bocha and search_config.get('bocha', {}).get('enabled'):
                bocha_key = search_config['bocha']['api_key']
                if bocha_key:
                    api_keys['bocha'] = [bocha_key]

            # 秘塔API密钥
            if self.config.enable_metaso and search_config.get('metaso', {}).get('enabled'):
                metaso_keys = []
                primary_key = search_config['metaso']['api_key']
                backup_key = search_config['metaso'].get('backup_api_key')

                if primary_key:
                    metaso_keys.append(primary_key)
                if backup_key:
                    metaso_keys.append(backup_key)

                if metaso_keys:
                    api_keys['metaso'] = metaso_keys

            self.api_key_manager = APIKeyManager(api_keys)
            logger.info(f"✅ 加载了 {len(api_keys)} 个搜索引擎的API密钥")

        except Exception as e:
            logger.warning(f"⚠️ 加载API密钥失败，将使用默认配置: {e}")
            # 使用默认API密钥进行测试
            self.api_key_manager = APIKeyManager({
                'tavily': ['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'],
                'metaso': ['mk-C1C2001C283A4EDB2DABBD62E07C5B13', 'mk-CA690CA8375C1E2E0856389E3B0BA587']
            })

    async def _initialize_engines(self):
        """初始化搜索引擎"""
        try:
            # 初始化Tavily
            if self.config.enable_tavily:
                tavily_keys = self.api_key_manager.api_keys.get('tavily', [])
                if tavily_keys:
                    self.tavily_engine = TavilySearchEngine(tavily_keys)
                    logger.info('✅ Tavily搜索引擎初始化完成')

            # 初始化博查
            if self.config.enable_bocha:
                bocha_keys = self.api_key_manager.api_keys.get('bocha', [])
                if bocha_keys:
                    self.bocha_engine = BochaSearchEngine(bocha_keys)
                    logger.info('✅ 博查搜索引擎初始化完成')

            # 初始化秘塔
            if self.config.enable_metaso:
                metaso_keys = self.api_key_manager.api_keys.get('metaso', [])
                if metaso_keys:
                    self.metaso_engine = MetasoSearchEngine(metaso_keys)
                    logger.info('✅ 秘塔搜索引擎初始化完成')

        except Exception as e:
            logger.error(f"❌ 搜索引擎初始化失败: {e}")
            raise

    async def search_with_engine(self,
                                 query: str,
                                 engine: str = 'tavily',
                                 max_results: int = None,
                                 language: str = 'zh-CN',
                                 **kwargs) -> Dict[str, Any]:
        """
        使用指定搜索引擎进行搜索

        Args:
            query: 搜索查询
            engine: 搜索引擎名称 (tavily/bocha/metaso)
            max_results: 最大结果数量
            language: 搜索语言
            **kwargs: 其他搜索参数

        Returns:
            搜索结果字典
        """
        if not self.initialized:
            await self.initialize()

        max_results = max_results or self.config.max_results

        logger.info(f"🔍 执行搜索: '{query}' (引擎: {engine}, 结果数: {max_results})")

        try:
            # 选择搜索引擎
            search_engine = await self._get_engine(engine)
            if not search_engine:
                return {
                    'status': 'error',
                    'query': query,
                    'engine': engine,
                    'error': f"搜索引擎 {engine} 不可用",
                    'timestamp': datetime.now().isoformat()
                }

            # 创建搜索查询
            search_query = SearchQuery(
                query=query,
                max_results=max_results,
                language=language,
                **kwargs
            )

            # 执行搜索
            start_time = datetime.now()
            response = await search_engine.search(search_query)
            search_time = (datetime.now() - start_time).total_seconds()

            # 更新统计
            self.search_stats['total_searches'] += 1
            self.search_stats['engine_usage'][engine] = self.search_stats['engine_usage'].get(engine, 0) + 1
            self.search_stats['last_search_time'] = datetime.now().isoformat()

            if response.success:
                self.search_stats['successful_searches'] += 1
            else:
                self.search_stats['failed_searches'] += 1

            # 格式化结果
            results = {
                'status': 'success' if response.success else 'error',
                'query': query,
                'engine': engine,
                'total_found': response.total_results,
                'search_time': search_time,
                'results': [],
                'metadata': {
                    'platform_version': self.version,
                    'controllers': self.controllers,
                    'api_key_used': getattr(response, 'api_key_used', ''),
                    'timestamp': datetime.now().isoformat()
                }
            }

            if not response.success:
                results['error'] = response.error_message
                return results

            # 处理搜索结果
            for i, result in enumerate(response.results, 1):
                result_dict = {
                    'rank': i,
                    'title': result.title,
                    'url': result.url,
                    'snippet': result.snippet,
                    'relevance_score': result.relevance_score,
                    'position': result.position,
                    'timestamp': result.timestamp,
                    'metadata': result.metadata or {}
                }
                results['results'].append(result_dict)

            logger.info(f"✅ 搜索完成: {engine} 引擎找到 {len(results['results'])} 个结果")
            return results

        except Exception as e:
            logger.error(f"❌ 搜索失败: {e}")
            self.search_stats['failed_searches'] += 1

            return {
                'status': 'error',
                'query': query,
                'engine': engine,
                'error': str(e),
                'search_time': 0,
                'results': [],
                'timestamp': datetime.now().isoformat()
            }

    async def multi_engine_search(self,
                                  query: str,
                                  engines: Optional[List[str] = None,
                                  max_results: int = None,
                                  combine_results: bool = True) -> Dict[str, Any]:
        """
        多引擎并行搜索

        Args:
            query: 搜索查询
            engines: 搜索引擎列表
            max_results: 最大结果数量
            combine_results: 是否合并结果

        Returns:
            搜索结果字典
        """
        if not self.initialized:
            await self.initialize()

        engines = engines or ['tavily', 'metaso']  # 默认使用可用的引擎
        max_results = max_results or self.config.max_results

        logger.info(f"🔄 执行多引擎搜索: '{query}' (引擎: {', '.join(engines)})")

        try:
            # 并行执行搜索
            tasks = []
            for engine in engines:
                task = self.search_with_engine(query, engine, max_results=max_results)
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 处理结果
            engine_results = {}
            all_results = []
            successful_engines = []

            for i, (engine, result) in enumerate(zip(engines, results)):
                if isinstance(result, Exception):
                    logger.warning(f"⚠️ {engine} 引擎搜索失败: {result}")
                    engine_results[engine] = {
                        'status': 'error',
                        'error': str(result),
                        'results': []
                    }
                else:
                    engine_results[engine] = result
                    if result.get('status') == 'success':
                        successful_engines.append(engine)
                        if combine_results:
                            all_results.extend(result.get('results', []))

            # 合并并排序结果
            if combine_results and all_results:
                # 按相关性分数排序
                all_results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
                all_results = all_results[:max_results]  # 限制总结果数

            # 返回最终结果
            final_results = {
                'status': 'success' if successful_engines else 'error',
                'query': query,
                'engines_used': engines,
                'successful_engines': successful_engines,
                'total_found': len(all_results) if combine_results else sum(
                    r.get('total_found', 0) for r in engine_results.values() if r.get('status') == 'success'
                ),
                'engine_results': engine_results,
                'metadata': {
                    'platform_version': self.version,
                    'controllers': self.controllers,
                    'combine_results': combine_results,
                    'timestamp': datetime.now().isoformat()
                }
            }

            if combine_results:
                final_results['results'] = all_results

            logger.info(f"✅ 多引擎搜索完成: {len(successful_engines)}/{len(engines)} 个引擎成功")
            return final_results

        except Exception as e:
            logger.error(f"❌ 多引擎搜索失败: {e}")
            return {
                'status': 'error',
                'query': query,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def smart_search(self,
                           query: str,
                           max_results: int = None,
                           optimize_for: str = 'relevance') -> Dict[str, Any]:
        """
        智能搜索 - 根据查询内容自动选择最佳搜索引擎

        Args:
            query: 搜索查询
            max_results: 最大结果数量
            optimize_for: 优化目标 (relevance/speed/completeness)

        Returns:
            搜索结果字典
        """
        if not self.initialized:
            await self.initialize()

        logger.info(f"🧠 执行智能搜索: '{query}' (优化: {optimize_for})")

        # 根据查询内容和优化目标选择引擎
        selected_engines = await self._select_optimal_engines(query, optimize_for)

        # 执行搜索
        if len(selected_engines) == 1:
            return await self.search_with_engine(query, selected_engines[0], max_results)
        else:
            return await self.multi_engine_search(query, selected_engines, max_results)

    async def _select_optimal_engines(self, query: str, optimize_for: str) -> List[str]:
        """根据查询内容和优化目标选择最佳搜索引擎"""
        available_engines = []

        # 检查可用引擎
        if self.tavily_engine:
            available_engines.append('tavily')
        if self.bocha_engine:
            available_engines.append('bocha')
        if self.metaso_engine:
            available_engines.append('metaso')

        if not available_engines:
            return []

        # 根据优化目标选择引擎
        if optimize_for == 'speed':
            # Tavily通常最快
            return ['tavily'] if 'tavily' in available_engines else available_engines[:1]

        elif optimize_for == 'completeness':
            # 使用多引擎获取最全面结果
            return available_engines

        else:  # relevance (default)
            # 根据查询类型选择
            query_lower = query.lower()

            if any(keyword in query_lower for keyword in ['中文', '中国', '国内', '新闻']):
                # 中文相关查询优先使用博查和秘塔
                chinese_engines = [e for e in available_engines if e in ['bocha', 'metaso']
                if chinese_engines:
                    return chinese_engines[:2]

            # 默认使用Tavily
            return ['tavily'] if 'tavily' in available_engines else available_engines[:1]

    async def _get_engine(self, engine_name: str):
        """获取指定的搜索引擎实例"""
        engine_map = {
            'tavily': self.tavily_engine,
            'bocha': self.bocha_engine,
            'metaso': self.metaso_engine
        }
        return engine_map.get(engine_name.lower())

    async def get_platform_status(self) -> Dict[str, Any]:
        """获取平台状态"""
        logger.info('📋 获取外部搜索平台状态...')

        # 检查各引擎状态
        engine_status = {}
        engines = {
            'tavily': self.tavily_engine,
            'bocha': self.bocha_engine,
            'metaso': self.metaso_engine
        }

        for name, engine in engines.items():
            if engine:
                # 简单的状态检查
                try:
                    api_keys = getattr(engine, 'api_keys', [])
                    engine_status[name] = {
                        'status': 'available',
                        'api_keys_count': len(api_keys),
                        'endpoint': getattr(engine, 'base_url', 'unknown')
                    }
                except Exception as e:
                    engine_status[name] = {
                        'status': 'error',
                        'error': str(e)
                    }
            else:
                engine_status[name] = {
                    'status': 'disabled'
                }

        return {
            'platform': {
                'name': 'Athena外部搜索平台',
                'version': self.version,
                'controllers': self.controllers,
                'initialized': self.initialized
            },
            'engines': engine_status,
            'configuration': {
                'enable_tavily': self.config.enable_tavily,
                'enable_bocha': self.config.enable_bocha,
                'enable_metaso': self.config.enable_metaso,
                'enable_fallback': self.config.enable_fallback,
                'max_results': self.config.max_results,
                'search_timeout': self.config.search_timeout
            },
            'statistics': self.search_stats,
            'timestamp': datetime.now().isoformat()
        }

    def get_user_manual(self) -> Dict[str, Any]:
        """获取用户手册"""
        return {
            'title': 'Athena外部搜索平台用户手册',
            'controllers': self.controllers,
            'version': self.version,
            'engines': {
                'tavily': {
                    'description': 'Tavily AI搜索引擎 - 快速准确的全球搜索',
                    'features': ['实时搜索', '多语言支持', '智能摘要'],
                    'best_for': ['一般查询', '英文搜索', '快速响应']
                },
                'bocha': {
                    'description': '博查AI搜索引擎 - AI优化的中文搜索引擎',
                    'features': ['中文优化', 'AI增强', '知识整合'],
                    'best_for': ['中文查询', '学术搜索', '深度分析']
                },
                'metaso': {
                    'description': '秘塔AI搜索引擎 - 中国版Perplexity',
                    'features': ['智能对话', '深度理解', '中文知识库'],
                    'best_for': ['复杂问题', '知识问答', '中文内容']
                }
            },
            'quick_start': {
                'single_engine_search': {
                    'description': '单引擎搜索',
                    'usage': "platform.search_with_engine('查询', 'tavily')",
                    'example': "platform.search_with_engine('人工智能', 'tavily', max_results=10)"
                },
                'multi_engine_search': {
                    'description': '多引擎并行搜索',
                    'usage': "platform.multi_engine_search('查询', ['tavily', 'metaso'])",
                    'example': "platform.multi_engine_search('机器学习', ['tavily', 'metaso'], max_results=5)"
                },
                'smart_search': {
                    'description': '智能搜索 - 自动选择最佳引擎',
                    'usage': "platform.smart_search('查询', optimize_for='relevance')",
                    'example': "platform.smart_search('深度学习', optimize_for='completeness')"
                }
            },
            'optimization_options': {
                'relevance': '相关性优化 - 优先选择最相关的结果',
                'speed': '速度优化 - 使用最快的搜索引擎',
                'completeness': '完整性优化 - 使用多引擎获取全面结果'
            },
            'control_panel': {
                'engine_selection': '可指定使用特定搜索引擎',
                'result_limiting': '可控制搜索结果数量',
                'language_setting': '支持多语言搜索',
                'customization': '支持自定义搜索参数'
            }
        }

# 便捷函数 - 为小诺和Athena提供的快捷入口
async def quick_web_search(query: str, engine: str = 'tavily', max_results: int = 10) -> Dict[str, Any]:
    """快速网络搜索"""
    platform = ExternalSearchPlatform()
    return await platform.search_with_engine(query, engine, max_results)

async def smart_web_search(query: str, max_results: int = 10, optimize: str = 'relevance') -> Dict[str, Any]:
    """智能网络搜索"""
    platform = ExternalSearchPlatform()
    return await platform.smart_search(query, max_results, optimize)

async def comprehensive_search(query: str, max_results: int = 15) -> Dict[str, Any]:
    """全面搜索 - 使用所有可用引擎"""
    platform = ExternalSearchPlatform()
    return await platform.multi_engine_search(query, max_results=max_results)

# 创建全局实例（单例模式）
_global_external_platform = None

def get_external_search_platform() -> ExternalSearchPlatform:
    """获取全局外部搜索平台实例"""
    global _global_external_platform
    if _global_external_platform is None:
        _global_external_platform = ExternalSearchPlatform()
    return _global_external_platform

# 导出主要接口
__all__ = [
    'ExternalSearchPlatform',
    'ExternalSearchConfig',
    'quick_web_search',
    'smart_web_search',
    'comprehensive_search',
    'get_external_search_platform'
]

if __name__ == '__main__':
    # 演示用法
    async def demo():
        logger.info('🎉 欢迎使用Athena外部搜索平台！')
        logger.info('👥 控制者: 小诺 & Athena')

        # 创建平台实例
        platform = ExternalSearchPlatform()

        # 显示用户手册
        manual = platform.get_user_manual()
        logger.info(f"\n📖 {manual['title']} v{manual['version']}")
        logger.info(f"👮 控制者: {', '.join(manual['controllers'])}")

        # 显示可用引擎
        logger.info(f"\n🔍 可用搜索引擎: {', '.join(manual['engines'].keys())}")

        logger.info("\n🚀 Athena外部搜索平台准备就绪！小诺和Athena可以开始使用啦！")

    asyncio.run(demo())