#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Athena搜索平台 - 统一搜索工具接口
Athena Search Platform - Unified Search Tool Interface

提供小诺和小娜全量控制的搜索功能平台

控制者: 小诺 & 小娜
创建时间: 2025-12-11
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

# 导入搜索组件
from core.search import AthenaSearchEngine, SearchType
from core.search.api.search_api import SearchAPI, SearchRequest
from services.athena_iterative_search.agent import AthenaIterativeSearchAgent
from services.athena_iterative_search.config import SearchDepth

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SearchPlatformConfig:
    """搜索平台配置"""
    enable_internal_search: bool = True
    enable_external_search: bool = True
    enable_iterative_search: bool = True
    enable_api_service: bool = True
    default_max_results: int = 10
    default_search_depth: str = 'comprehensive'
    cache_enabled: bool = True
    debug_mode: bool = False

class AthenaSearchPlatform:
    """
    Athena搜索平台主类
    为小诺和小娜提供全量控制的搜索功能
    """

    def __init__(self, config: SearchPlatformConfig | None = None):
        """
        初始化搜索平台

        Args:
            config: 平台配置
        """
        self.config = config or SearchPlatformConfig()
        self.version = '1.0.0'
        self.controllers = ['小诺', '小娜']

        # 初始化各个搜索组件
        self.search_engine = None
        self.search_api = None
        self.iterative_agent = None

        # 平台状态
        self.initialized = False
        self.last_health_check = None

        logger.info(f"🔍 Athena搜索平台 v{self.version} - 控制者: {', '.join(self.controllers)}")

    async def initialize(self):
        """初始化搜索平台"""
        if self.initialized:
            return

        logger.info('🚀 初始化Athena搜索平台...')

        try:
            # 1. 初始化基础搜索引擎
            if self.config.enable_internal_search or self.config.enable_external_search:
                engine_config = {
                    'internal': {'enabled': self.config.enable_internal_search},
                    'external': {'enabled': self.config.enable_external_search},
                    'cache': {'enabled': self.config.cache_enabled}
                }
                self.search_engine = AthenaSearchEngine(engine_config)
                await self.search_engine.initialize()
                logger.info('✅ 基础搜索引擎初始化完成')

            # 2. 初始化搜索API
            if self.config.enable_api_service:
                self.search_api = SearchAPI()
                await self.search_api.initialize()
                logger.info('✅ 搜索API接口初始化完成')

            # 3. 初始化迭代式搜索代理
            if self.config.enable_iterative_search:
                self.iterative_agent = AthenaIterativeSearchAgent()
                logger.info('✅ 迭代式搜索代理初始化完成')

            self.initialized = True
            logger.info('🎉 Athena搜索平台初始化完成！')

        except Exception as e:
            logger.error(f"❌ 搜索平台初始化失败: {e}")
            raise

    async def simple_search(self,
                          query: str,
                          max_results: int = None,
                          search_type: str = 'hybrid') -> Dict[str, Any]:
        """
        简单搜索 - 小诺和小娜的快速搜索入口

        Args:
            query: 搜索查询
            max_results: 最大结果数量
            search_type: 搜索类型 (internal/external/hybrid)

        Returns:
            搜索结果字典
        """
        if not self.initialized:
            await self.initialize()

        max_results = max_results or self.config.default_max_results

        logger.info(f"🔍 执行简单搜索: '{query}' (类型: {search_type}, 限制: {max_results})")

        try:
            # 创建搜索请求
            request = SearchRequest(
                query=query,
                limit=max_results,
                search_type=SearchType(search_type)
            )

            # 执行搜索
            response = await self.search_api.search(request)

            # 格式化结果
            results = {
                'status': 'success',
                'query': query,
                'search_type': search_type,
                'total_found': response.total_found,
                'search_time': response.search_time,
                'sources_used': response.sources_used,
                'results': [],
                'metadata': {
                    'platform_version': self.version,
                    'controllers': self.controllers,
                    'timestamp': datetime.now().isoformat()
                }
            }

            # 处理搜索结果
            for i, result in enumerate(response.results):
                result_dict = {
                    'rank': i + 1,
                    'title': getattr(result, 'title', '无标题'),
                    'content': getattr(result, 'content', '')[:500] + '...' if len(getattr(result, 'content', '')) > 500 else getattr(result, 'content', ''),
                    'url': getattr(result, 'url', ''),
                    'relevance_score': getattr(result, 'score', 0.0),
                    'source': getattr(result, 'source', 'unknown')
                }
                results['results'].append(result_dict)

            logger.info(f"✅ 搜索完成: 找到 {len(results['results'])} 个结果")
            return results

        except Exception as e:
            logger.error(f"❌ 搜索失败: {e}")
            return {
                'status': 'error',
                'query': query,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def intelligent_patent_search(self,
                                       research_topic: str,
                                       max_iterations: int = 5,
                                       depth: str = 'comprehensive') -> Dict[str, Any]:
        """
        智能专利搜索 - 小诺和小娜的专业研究入口

        Args:
            research_topic: 研究主题
            max_iterations: 最大迭代次数
            depth: 搜索深度

        Returns:
            详细的研究结果
        """
        if not self.initialized:
            await self.initialize()

        logger.info(f"🧠 执行智能专利搜索: '{research_topic}' (深度: {depth}, 轮数: {max_iterations})")

        try:
            # 执行智能研究
            session = await self.iterative_agent.intelligent_patent_research(
                research_topic=research_topic,
                max_iterations=max_iterations,
                depth=SearchDepth(depth)
            )

            # 格式化研究结果
            research_results = {
                'status': 'success',
                'research_topic': research_topic,
                'session_id': getattr(session, 'session_id', 'unknown'),
                'total_iterations': getattr(session, 'current_iteration', 0),
                'total_patents_found': getattr(session, 'total_patents_found', 0),
                'unique_patents': getattr(session, 'unique_patents', 0),
                'search_depth': depth,
                'iterations': [],
                'research_summary': {},
                'metadata': {
                    'platform_version': self.version,
                    'controllers': self.controllers,
                    'timestamp': datetime.now().isoformat()
                }
            }

            # 处理迭代结果
            if hasattr(session, 'iterations'):
                for i, iteration in enumerate(session.iterations):
                    iteration_data = {
                        'iteration': i + 1,
                        'query': getattr(iteration, 'query', ''),
                        'results_count': len(getattr(iteration, 'results', [])),
                        'search_time': getattr(iteration, 'search_time', 0.0),
                        'key_findings': getattr(iteration, 'key_findings', [])
                    }
                    research_results['iterations'].append(iteration_data)

            # 处理研究摘要
            if hasattr(session, 'research_summary'):
                summary = session.research_summary
                research_results['research_summary'] = {
                    'main_insights': getattr(summary, 'main_insights', []),
                    'key_companies': getattr(summary, 'key_companies', []),
                    'technology_trends': getattr(summary, 'technology_trends', []),
                    'recommendations': getattr(summary, 'recommendations', [])
                }

            logger.info(f"✅ 智能研究完成: {research_results['total_iterations']} 轮, {research_results['total_patents_found']} 个专利")
            return research_results

        except Exception as e:
            logger.error(f"❌ 智能研究失败: {e}")
            return {
                'status': 'error',
                'research_topic': research_topic,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def competitive_analysis(self,
                                 company_name: str,
                                 technology_domain: str = None) -> Dict[str, Any]:
        """
        竞争分析 - 小诺和小娜的战略分析入口

        Args:
            company_name: 公司名称
            technology_domain: 技术领域

        Returns:
            竞争分析结果
        """
        if not self.initialized:
            await self.initialize()

        logger.info(f"📊 执行竞争分析: 公司='{company_name}', 领域='{technology_domain or '全部'}'")

        try:
            # 执行竞争分析
            session = await self.iterative_agent.patent_competitive_analysis(
                company_name=company_name,
                technology_domain=technology_domain
            )

            # 格式化分析结果
            analysis_results = {
                'status': 'success',
                'company_name': company_name,
                'technology_domain': technology_domain,
                'analysis_type': 'patent_competitive',
                'total_patents': getattr(session, 'total_patents_found', 0),
                'analysis_summary': {},
                'key_patents': [],
                'technology_focus': [],
                'timeline_analysis': {},
                'metadata': {
                    'platform_version': self.version,
                    'controllers': self.controllers,
                    'timestamp': datetime.now().isoformat()
                }
            }

            # 处理分析摘要
            if hasattr(session, 'research_summary'):
                summary = session.research_summary
                analysis_results['analysis_summary'] = {
                    'patent_strength': getattr(summary, 'patent_strength', 'unknown'),
                    'technology_position': getattr(summary, 'technology_position', 'unknown'),
                    'market_advantages': getattr(summary, 'market_advantages', []),
                    'competitive_threats': getattr(summary, 'competitive_threats', [])
                }

            logger.info(f"✅ 竞争分析完成: 分析了 {analysis_results['total_patents']} 个专利")
            return analysis_results

        except Exception as e:
            logger.error(f"❌ 竞争分析失败: {e}")
            return {
                'status': 'error',
                'company_name': company_name,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def platform_status(self) -> Dict[str, Any]:
        """
        获取平台状态 - 小诺和小娜的系统监控入口

        Returns:
            平台状态信息
        """
        logger.info('📋 获取平台状态...')

        status = {
            'platform': {
                'name': 'Athena搜索平台',
                'version': self.version,
                'controllers': self.controllers,
                'initialized': self.initialized,
                'uptime': '运行中' if self.initialized else '未初始化'
            },
            'components': {
                '基础搜索引擎': '🟢 运行正常' if self.search_engine else '🔴 未启动',
                '搜索API接口': '🟢 运行正常' if self.search_api else '🔴 未启动',
                '迭代式搜索': '🟢 运行正常' if self.iterative_agent else '🔴 未启动'
            },
            'configuration': {
                '内部搜索': '✅ 启用' if self.config.enable_internal_search else '❌ 禁用',
                '外部搜索': '✅ 启用' if self.config.enable_external_search else '❌ 禁用',
                '迭代搜索': '✅ 启用' if self.config.enable_iterative_search else '❌ 禁用',
                'API服务': '✅ 启用' if self.config.enable_api_service else '❌ 禁用',
                '缓存系统': '✅ 启用' if self.config.cache_enabled else '❌ 禁用'
            },
            'health_check': {},
            'timestamp': datetime.now().isoformat()
        }

        # 执行健康检查
        try:
            if self.search_engine:
                engine_health = await self.search_engine.health_check()
                status['health_check']['搜索引擎'] = engine_health.get('overall_status', 'unknown')

            status['overall_health'] = 'healthy' if self.initialized else 'uninitialized'

        except Exception as e:
            status['health_check'] = {'error': str(e)}
            status['overall_health'] = 'degraded'

        return status

    def get_user_manual(self) -> Dict[str, Any]:
        """
        获取用户手册 - 小诺和小娜的使用指南

        Returns:
            用户使用指南
        """
        return {
            'title': 'Athena搜索平台用户手册',
            'controllers': self.controllers,
            'version': self.version,
            'quick_start': {
                'simple_search': {
                    'description': '快速搜索，适合一般查询',
                    'usage': "platform.simple_search('你的查询')",
                    'example': "platform.simple_search('人工智能专利', max_results=10)"
                },
                'intelligent_search': {
                    'description': '智能专利研究，深度分析',
                    'usage': "platform.intelligent_patent_search('研究主题')",
                    'example': "platform.intelligent_patent_search('机器学习算法', max_iterations=5)"
                },
                'competitive_analysis': {
                    'description': '竞争对手专利分析',
                    'usage': "platform.competitive_analysis('公司名称')",
                    'example': "platform.competitive_analysis('华为', technology_domain='5G通信')"
                }
            },
            'search_types': {
                'internal': '内部知识库搜索',
                'external': '外部网络搜索',
                'hybrid': '混合搜索（推荐）'
            },
            'search_depths': {
                'quick': '快速搜索，1-2轮',
                'standard': '标准搜索，3-5轮',
                'comprehensive': '全面搜索，5-8轮',
                'deep': '深度搜索，8-12轮'
            },
            'features': {
                '🔍 智能查询扩展': '自动优化搜索关键词',
                '📊 结果智能排序': '基于相关性和重要性排序',
                '🧠 迭代式优化': '根据结果动态调整搜索策略',
                '⚡ 高速缓存': '提高重复查询速度',
                '📈 分析报告': '自动生成分析摘要'
            },
            'control_panel': {
                'status_monitoring': '使用 platform_status() 监控系统状态',
                'configuration': '通过 SearchPlatformConfig 自定义配置',
                'debug_mode': '启用调试模式查看详细日志'
            }
        }

# 便捷函数 - 为小诺和小娜提供的快捷入口
async def quick_search(query: str, max_results: int = 10) -> Dict[str, Any]:
    """
    快速搜索 - 最简单的搜索方式
    """
    platform = AthenaSearchPlatform()
    return await platform.simple_search(query, max_results)

async def patent_research(topic: str, depth: str = 'comprehensive') -> Dict[str, Any]:
    """
    专利研究 - 专业的专利分析
    """
    platform = AthenaSearchPlatform()
    return await platform.intelligent_patent_search(topic, depth=depth)

async def analyze_competitor(company: str, domain: str = None) -> Dict[str, Any]:
    """
    竞争对手分析 - 战略分析工具
    """
    platform = AthenaSearchPlatform()
    return await platform.competitive_analysis(company, domain)

# 创建全局实例（单例模式）
_global_platform = None

def get_search_platform() -> AthenaSearchPlatform:
    """获取全局搜索平台实例"""
    global _global_platform
    if _global_platform is None:
        _global_platform = AthenaSearchPlatform()
    return _global_platform

# 导出主要接口
__all__ = [
    'AthenaSearchPlatform',
    'SearchPlatformConfig',
    'quick_search',
    'patent_research',
    'analyze_competitor',
    'get_search_platform'
]

if __name__ == '__main__':
    # 演示用法
    async def demo():
        logger.info('🎉 欢迎使用Athena搜索平台！')
        logger.info('👥 控制者: 小诺 & 小娜')

        # 创建平台实例
        platform = AthenaSearchPlatform()

        # 显示用户手册
        manual = platform.get_user_manual()
        logger.info(f"\n📖 {manual['title']} v{manual['version']}")
        logger.info(f"👮 控制者: {', '.join(manual['controllers'])}")

        # 获取平台状态
        status = await platform.platform_status()
        logger.info(f"\n📊 平台状态: {status['overall_health']}")

        logger.info("\n🚀 Athena搜索平台准备就绪！小诺和小娜可以开始使用啦！")

    asyncio.run(demo())