#!/usr/bin/env python3
"""
Athena通用迭代式搜索工具
支持专利、技术方案、学术研究等多领域深度搜索
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# 设置Python路径
sys.path.append('/Users/xujian/Athena工作平台')

from services.athena_iterative_search import AthenaIterativeSearchAgent
from services.athena_iterative_search.config import SearchDepth


class UniversalSearchTool:
    """通用搜索工具类"""

    def __init__(self):
        """初始化搜索工具"""
        self.agent = None
        self.reports_dir = '/Users/xujian/Athena工作平台/search_reports'
        os.makedirs(self.reports_dir, exist_ok=True)

    async def initialize(self):
        """初始化搜索代理"""
        try:
            self.agent = AthenaIterativeSearchAgent()
            logger.info('✅ 搜索代理初始化成功')
            return True
        except Exception as e:
            logger.info(f"❌ 搜索代理初始化失败: {e}")
            return False

    async def simple_search(self, query: str, max_results: int = 10) -> List[Dict]:
        """简单搜索"""
        if not self.agent:
            await self.initialize()

        try:
            # 使用核心搜索引擎
            from services.athena_iterative_search.core import (
                AthenaIterativeSearchEngine,
            )
            engine = AthenaIterativeSearchEngine()

            results = await engine.search(
                query=query,
                max_results=max_results,
                strategy='hybrid',
                use_cache=True
            )

            # 转换结果为字典格式
            search_results = []
            for result in results:
                search_results.append({
                    'patent_id': getattr(result, 'patent_id', ''),
                    'title': getattr(result, 'title', ''),
                    'abstract': getattr(result, 'abstract', ''),
                    'relevance_score': getattr(result, 'relevance_score', 0.0),
                    'metadata': getattr(result, 'metadata', {})
                })

            await engine.close()
            return search_results

        except Exception as e:
            logger.info(f"❌ 搜索失败: {e}")
            return []

    async def deep_search(
        self,
        research_topic: str,
        max_iterations: int = 5,
        depth: str = 'comprehensive',
        focus_areas: List[str] = None
    ) -> Dict[str, Any]:
        """深度迭代搜索"""
        if not self.agent:
            await self.initialize()

        try:
            # 使用已经验证的技术搜索示例的方法
            logger.info(f"🎯 开始深度研究: {research_topic}")
            logger.info(f"📊 最大迭代轮数: {max_iterations}")
            logger.info(f"🔍 搜索深度: {depth}")

            # 转换深度参数
            if depth == 'comprehensive':
                search_depth = SearchDepth.COMPREHENSIVE
            elif depth == 'deep':
                search_depth = SearchDepth.DEEP
            else:
                search_depth = SearchDepth.STANDARD

            # 执行搜索
            session = await self.agent.intelligent_patent_research(
                research_topic=research_topic,
                max_iterations=max_iterations,
                depth=search_depth,
                focus_areas=focus_areas or [],
                progress_callback=lambda current, total, msg:
                    logger.info(f"⏳ 进度: [{current}/{total}] - {msg}")
            )

            # 构建搜索报告
            search_report = {
                'search_metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'research_topic': research_topic,
                    'max_iterations': max_iterations,
                    'search_depth': depth,
                    'focus_areas': focus_areas or []
                },
                'search_statistics': {
                    'total_iterations': session.current_iteration,
                    'total_solutions': session.total_patents_found,
                    'unique_solutions': session.unique_patents,
                    'average_solutions_per_iteration': session.total_patents_found / session.current_iteration if session.current_iteration > 0 else 0
                },
                'search_iterations': [
                    {
                        'iteration': iteration.iteration_number,
                        'query': iteration.query.text,
                        'results_count': iteration.total_results,
                        'quality_score': iteration.quality_score,
                        'insights': iteration.insights,
                        'next_suggestion': iteration.next_query_suggestion
                    }
                    for iteration in session.iterations
                ],
                'research_summary': {}
            }

            # 添加研究摘要
            if session.research_summary:
                search_report['research_summary'] = {
                    'confidence_level': session.research_summary.confidence_level,
                    'completeness_score': session.research_summary.completeness_score,
                    'key_findings': session.research_summary.key_findings,
                    'main_solutions': session.research_summary.main_patents,
                    'technological_trends': session.research_summary.technological_trends,
                    'competing_entities': session.research_summary.competing_applicants,
                    'innovation_insights': session.research_summary.innovation_insights,
                    'recommendations': session.research_summary.recommendations
                }

            # 保存报告
            filename = f"deep_search_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(self.reports_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(search_report, f, ensure_ascii=False, indent=2)

            logger.info(f"✅ 搜索完成！报告已保存至: {filepath}")
            return search_report

        except Exception as e:
            logger.info(f"❌ 深度搜索失败: {e}")
            return {}

    async def close(self):
        """关闭搜索代理"""
        if self.agent:
            try:
                await self.agent.close()
                logger.info('✅ 搜索代理已关闭')
            except Exception as e:
                logger.info(f"⚠️ 关闭搜索代理时出错: {e}")

def print_header():
    """打印工具头部信息"""
    logger.info(str('='*60))
    logger.info('🔍 Athena通用迭代式搜索工具')
    logger.info(str('='*60))
    logger.info('支持功能:')
    logger.info('• 🎯 简单搜索: 快速检索相关专利和技术')
    logger.info('• 🔄 深度搜索: 智能迭代式深度研究')
    logger.info('• 📊 多领域应用: 专利、技术、学术研究等')
    logger.info('• 💾 智能报告: 自动生成详细分析报告')
    logger.info(str('='*60))

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Athena通用迭代式搜索工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 简单搜索
  python athena_universal_search.py --search '人工智能' --results 10

  # 深度搜索
  python athena_universal_search.py --deep-research '深度学习在医疗诊断中的应用' --iterations 5

  # 指定关注领域
  python athena_universal_search.py --deep-research '机器学习算法' --focus '深度学习,神经网络,自然语言处理'
        """
    )

    # 搜索选项
    search_group = parser.add_mutually_exclusive_group(required=True)
    search_group.add_argument(
        '--search', '-s',
        help='简单搜索查询'
    )
    search_group.add_argument(
        '--deep-research', '-d',
        help='深度研究主题'
    )

    # 搜索参数
    parser.add_argument(
        '--results', '-r',
        type=int,
        default=10,
        help='简单搜索结果数量 (默认: 10)'
    )
    parser.add_argument(
        '--iterations', '-i',
        type=int,
        default=5,
        help='深度搜索迭代轮数 (默认: 5)'
    )
    parser.add_argument(
        '--depth',
        choices=['standard', 'comprehensive', 'deep'],
        default='comprehensive',
        help='搜索深度 (默认: comprehensive)'
    )
    parser.add_argument(
        '--focus',
        help='关注领域，用逗号分隔'
    )

    args = parser.parse_args()

    # 打印头部信息
    print_header()

    # 创建搜索工具
    tool = UniversalSearchTool()

    try:
        if args.search:
            # 简单搜索
            logger.info(f"\n🔍 执行简单搜索: {args.search}")
            logger.info(f"📊 最大结果数: {args.results}")
            logger.info(str('-' * 40))

            results = await tool.simple_search(args.search, args.results)

            if results:
                logger.info(f"\n✅ 找到 {len(results)} 个相关结果:")
                for i, result in enumerate(results, 1):
                    logger.info(f"\n{i}. {result['title']}")
                    logger.info(f"   📋 摘要: {result['abstract'][:100]}...")
                    logger.info(f"   🎯 相关性: {result['relevance_score']:.3f}")
                    if result['patent_id']:
                        logger.info(f"   📛 专利号: {result['patent_id']}")
            else:
                logger.info('❌ 未找到相关结果')

        elif args.deep_research:
            # 深度搜索
            logger.info(f"\n🎯 执行深度研究: {args.deep_research}")

            focus_areas = []
            if args.focus:
                focus_areas = [area.strip() for area in args.focus.split(',')]
                logger.info(f"🔍 关注领域: {', '.join(focus_areas)}")

            logger.info(str('-' * 40))

            report = await tool.deep_search(
                research_topic=args.deep_research,
                max_iterations=args.iterations,
                depth=args.depth,
                focus_areas=focus_areas
            )

            if report:
                # 显示搜索统计
                stats = report['search_statistics']
                logger.info(f"\n📊 搜索统计:")
                logger.info(f"   • 总迭代轮数: {stats['total_iterations']}")
                logger.info(f"   • 发现技术方案: {stats['total_solutions']}个")
                logger.info(f"   • 唯一技术方案: {stats['unique_solutions']}个")
                logger.info(f"   • 平均每轮发现: {stats['average_solutions_per_iteration']:.1f}个")

                # 显示研究摘要
                summary = report.get('research_summary', {})
                if summary:
                    logger.info(f"\n💡 研究摘要:")
                    if summary.get('confidence_level'):
                        logger.info(f"   • 置信度: {summary['confidence_level']:.1%}")
                    if summary.get('completeness_score'):
                        logger.info(f"   • 完整度: {summary['completeness_score']:.1%}")

                    if summary.get('key_findings'):
                        logger.info(f"\n🔍 关键发现:")
                        for finding in summary['key_findings'][:3]:
                            logger.info(f"   • {finding}")

                    if summary.get('recommendations'):
                        logger.info(f"\n📋 建议:")
                        for rec in summary['recommendations'][:3]:
                            logger.info(f"   • {rec}")

                logger.info(f"\n📄 详细报告已保存至: {tool.reports_dir}")
            else:
                logger.info('❌ 深度搜索失败')

    except KeyboardInterrupt:
        logger.info("\n⚠️ 搜索被用户中断")
    except Exception as e:
        logger.info(f"\n❌ 搜索过程中出错: {e}")
    finally:
        await tool.close()
        logger.info("\n👋 感谢使用Athena通用搜索工具！")

if __name__ == '__main__':
    asyncio.run(main())