#!/usr/bin/env python3
"""
技术方案迭代式搜索完整示例
演示如何检索与目标技术方案接近的技术
"""

import asyncio
import json
import logging
import sys
from datetime import datetime

logger = logging.getLogger(__name__)

# 设置Python路径
sys.path.append('/Users/xujian/Athena工作平台')

from services.athena_iterative_search import AthenaIterativeSearchAgent
from services.athena_iterative_search.config import SearchDepth


async def iterative_technology_search():
    """
    完整的迭代式技术搜索流程
    """

    logger.info('🎯 迭代式技术搜索系统')
    logger.info(str('='*60))

    # 第一步：定义搜索参数
    logger.info("\n📋 第一步：配置搜索参数")
    logger.info(str('-'*40))

    target_technology = '基于深度学习的医疗影像诊断系统'
    research_objectives = [
        '了解现有医疗影像AI诊断技术',
        '识别关键技术创新点',
        '分析主要技术路径',
        '发现潜在改进方向'
    ]

    focus_areas = [
        '深度学习算法',
        '医学影像处理',
        '人工智能诊断',
        '系统优化方法'
    ]

    logger.info(f"🎯 目标技术: {target_technology}")
    logger.info("📚 研究目标:")
    for i, obj in enumerate(research_objectives, 1):
        logger.info(f"   {i}. {obj}")
    logger.info(f"🔍 关注领域: {', '.join(focus_areas)}")

    # 第二步：初始化搜索代理
    logger.info("\n🔧 第二步：初始化智能搜索代理")
    logger.info(str('-'*40))

    try:
        agent = AthenaIterativeSearchAgent()
        logger.info('✅ 搜索代理初始化成功')
    except Exception as e:
        logger.info(f"❌ 初始化失败: {e}")
        return

    # 第三步：执行迭代搜索
    logger.info("\n🔄 第三步：执行迭代式深度搜索")
    logger.info(str('-'*40))

    session = await agent.intelligent_patent_research(
        research_topic=target_technology,
        max_iterations=5,
        depth=SearchDepth.COMPREHENSIVE,
        focus_areas=focus_areas,
        progress_callback=lambda current, total, msg:
            logger.info(f"⏳ 进度: [{current}/{total}] - {msg}")
    )

    # 第四步：展示搜索结果
    logger.info(str("\n" + '='*60))
    logger.info('📊 第四步：搜索结果分析')
    logger.info(str('='*60))

    # 基本统计
    logger.info("\n📈 搜索统计:")
    logger.info(f"   • 总迭代轮数: {session.current_iteration}")
    logger.info(f"   • 发现技术方案: {session.total_patents_found}个")
    logger.info(f"   • 唯一技术方案: {session.unique_patents}个")
    logger.info(f"   • 平均每轮发现: {session.total_patents_found / session.current_iteration:.1f}个")

    # 每轮详情
    logger.info("\n🔍 各轮搜索详情:")
    for iteration in session.iterations:
        logger.info(f"\n   第{iteration.iteration_number}轮:")
        logger.info(f"   • 搜索查询: {iteration.query.text}")
        logger.info(f"   • 结果数量: {iteration.total_results}个")
        logger.info(f"   • 质量评分: {iteration.quality_score:.2f}/1.00")

        if iteration.insights:
            logger.info('   • 关键洞察:')
            for insight in iteration.insights:
                logger.info(f"     - {insight}")

        if iteration.next_query_suggestion:
            logger.info(f"   • 下一轮建议: {iteration.next_query_suggestion}")

    # 第五步：研究摘要
    logger.info(str("\n' + '="*60))
    logger.info('📝 第五步：研究摘要与建议')
    logger.info(str('='*60))

    if session.research_summary:
        summary = session.research_summary

        # 置信度和完整度
        logger.info("\n📊 研究质量评估:")
        logger.info(f"   • 置信度: {summary.confidence_level:.1%}")
        logger.info(f"   • 完整度: {summary.completeness_score:.1%}")

        # 关键发现
        if summary.key_findings:
            logger.info(f"\n💡 关键发现 ({len(summary.key_findings)}条):")
            for i, finding in enumerate(summary.key_findings, 1):
                logger.info(f"   {i}. {finding}")

        # 主要技术方案
        if summary.main_patents:
            logger.info(f"\n🏆 核心技术方案 ({len(summary.main_patents)}个):")
            for i, patent in enumerate(summary.main_patents[:5], 1):
                logger.info(f"   {i}. {patent[:80]}...")

        # 技术趋势
        if summary.technological_trends:
            logger.info("\n📈 技术发展趋势:")
            for trend in summary.technological_trends:
                logger.info(f"   • {trend}")

        # 创新洞察
        if summary.innovation_insights:
            logger.info("\n💭 创新洞察:")
            for insight in summary.innovation_insights:
                logger.info(f"   • {insight}")

        # 竞争分析
        if summary.competing_applicants:
            logger.info("\n🏢 主要技术提供者:")
            for applicant in summary.competing_applicants[:5]:
                logger.info(f"   • {applicant}")

        # 战略建议
        if summary.recommendations:
            logger.info("\n🎯 战略建议:")
            for rec in summary.recommendations:
                logger.info(f"   • {rec}")

    # 第六步：保存研究报告
    logger.info(str("\n' + '="*60))
    logger.info('💾 第六步：保存研究报告')
    logger.info(str('='*60))

    # 构建完整报告
    research_report = {
        'search_metadata': {
            'timestamp': datetime.now().isoformat(),
            'target_technology': target_technology,
            'research_objectives': research_objectives,
            'focus_areas': focus_areas
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
        'research_summary': {
            'confidence_level': session.research_summary.confidence_level if session.research_summary else 0,
            'completeness_score': session.research_summary.completeness_score if session.research_summary else 0,
            'key_findings': session.research_summary.key_findings if session.research_summary else [],
            'main_patents': session.research_summary.main_patents if session.research_summary else [],
            'technological_trends': session.research_summary.technological_trends if session.research_summary else [],
            'competing_applicants': session.research_summary.competing_applicants if session.research_summary else [],
            'innovation_insights': session.research_summary.innovation_insights if session.research_summary else [],
            'recommendations': session.research_summary.recommendations if session.research_summary else []
        }
    }

    # 保存到文件
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"technology_search_report_{timestamp}.json"
    filepath = f"/Users/xujian/Athena工作平台/services/athena_iterative_search/reports/{filename}"

    import os
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(research_report, f, ensure_ascii=False, indent=2)

    logger.info(f"✅ 研究报告已保存至: {filepath}")

    # 总结建议
    logger.info(str("\n' + '="*60))
    logger.info('🎯 后续行动建议')
    logger.info(str('='*60))

    logger.info("""
1. 📖 深入分析高相关性技术方案
   - 重点关注质量评分>0.7的方案
   - 研究其具体实现细节
   - 分析技术可行性

2. 🔬 进行技术对比分析
   - 选择2-3个最相似的技术方案
   - 对比其优缺点
   - 评估适用场景

3. 💡 思考创新改进方向
   - 基于现有方案识别改进空间
   - 结合最新技术趋势
   - 探索跨领域应用

4. 📋 制定实施计划
   - 明确技术路线图
   - 评估资源需求
   - 设定里程碑

5. 🔄 持续跟踪发展
   - 定期更新搜索
   - 关注新技术涌现
   - 调整研究方向
    """)

    logger.info("\n✅ 迭代式搜索完成！")
    logger.info(f"📊 发现了 {session.total_patents_found} 个相关技术方案")
    logger.info(f"🔍 经过 {session.current_iteration} 轮深度搜索")
    logger.info(str(f"🎯 研究完整度: {session.research_summary.completeness_score*100:.1f}%' if session.research_summary else '"))

if __name__ == '__main__':
    asyncio.run(iterative_technology_search())
