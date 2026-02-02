#!/usr/bin/env python3
"""
Athena迭代式搜索智能代理
基于LLM的智能查询生成和结果分析
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from .config import AthenaSearchConfig, SearchDepth
from .core import AthenaIterativeSearchEngine
from .types import (
    PatentMetadata,
    PatentSearchResult,
    QueryExpansion,
    ResearchSummary,
    SearchQuery,
    SearchSession,
)

logger = logging.getLogger(__name__)

class AthenaIterativeSearchAgent:
    """Athena迭代式搜索智能代理"""

    def __init__(self, config: AthenaSearchConfig | None = None):
        """
        初始化搜索代理

        Args:
            config: 搜索配置
        """
        self.config = config or AthenaSearchConfig()
        self.search_engine = AthenaIterativeSearchEngine(config)
        self.llm_client = None  # 可以集成OpenAI或其他LLM服务

        logger.info('Athena迭代式搜索代理初始化完成')

    async def intelligent_patent_research(
        self,
        research_topic: str,
        max_iterations: int = 5,
        depth: SearchDepth = SearchDepth.DEEP,
        focus_areas: Optional[List[str]] = None,
        progress_callback: callable | None = None
    ) -> SearchSession:
        """
        执行智能专利研究

        Args:
            research_topic: 研究主题
            max_iterations: 最大迭代轮数
            depth: 搜索深度
            focus_areas: 关注领域列表
            progress_callback: 进度回调函数

        Returns:
            完整的搜索会话，包含研究摘要
        """
        logger.info(f"开始智能专利研究: 主题='{research_topic}'")

        # 生成初始查询策略
        initial_queries = await self._generate_initial_queries(research_topic, focus_areas)

        # 选择最佳初始查询
        best_query = await self._select_best_initial_query(initial_queries, research_topic)

        # 执行迭代搜索
        session = await self.search_engine.iterative_search(
            initial_query=best_query,
            max_iterations=max_iterations,
            depth=depth,
            progress_callback=progress_callback
        )

        # 智能分析和优化
        session = await self._intelligent_analysis(session, research_topic)

        logger.info(f"智能专利研究完成: 总轮数={session.current_iteration}, 总专利数={session.total_patents_found}")

        return session

    async def patent_competitive_analysis(
        self,
        company_name: str,
        technology_domain: str | None = None,
        time_range: Optional[Tuple[str, str]] = None
    ) -> SearchSession:
        """
        执行专利竞争分析

        Args:
            company_name: 公司名称
            technology_domain: 技术领域
            time_range: 时间范围 (开始日期, 结束日期)

        Returns:
            竞争分析搜索会话
        """
        logger.info(f"开始专利竞争分析: 公司='{company_name}'")

        # 构建竞争分析查询
        query_parts = [f"申请人:{company_name}"]
        if technology_domain:
            query_parts.append(technology_domain)

        analysis_query = ' AND '.join(query_parts)

        # 执行深度搜索
        session = await self.search_engine.iterative_search(
            initial_query=analysis_query,
            max_iterations=4,
            depth=SearchDepth.DEEP
        )

        # 生成竞争分析报告
        session.research_summary = await self._generate_competitive_analysis_report(
            session, company_name, technology_domain
        )

        return session

    async def patent_technology_trend_analysis(
        self,
        technology: str,
        time_period: str = '5年'  # 支持: 3年, 5年, 10年
    ) -> SearchSession:
        """
        执行专利技术趋势分析

        Args:
            technology: 技术名称
            time_period: 分析时间段

        Returns:
            技术趋势分析会话
        """
        logger.info(f"开始专利技术趋势分析: 技术='{technology}', 时间段='{time_period}'")

        # 构建趋势分析查询
        trend_query = f"{technology} 技术发展 专利"

        # 执行多轮搜索以获得趋势数据
        session = await self.search_engine.iterative_search(
            initial_query=trend_query,
            max_iterations=3,
            depth=SearchDepth.STANDARD
        )

        # 生成技术趋势报告
        session.research_summary = await self._generate_trend_analysis_report(
            session, technology, time_period
        )

        return session

    async def patent_infringement_risk_assessment(
        self,
        target_patent_id: str,
            technology_keywords: List[str]
    ) -> SearchSession:
        """
        执行专利侵权风险评估

        Args:
            target_patent_id: 目标专利ID
            technology_keywords: 技术关键词列表

        Returns:
            侵权风险评估会话
        """
        logger.info(f"开始专利侵权风险评估: 专利ID='{target_patent_id}'")

        # 首先获取目标专利信息
        target_patent = await self._get_patent_by_id(target_patent_id)
        if not target_patent:
            raise ValueError(f"未找到专利: {target_patent_id}")

        # 构建侵权风险评估查询
        risk_query = f"{' '.join(technology_keywords)} 专利侵权风险"

        # 执行深度搜索
        session = await self.search_engine.iterative_search(
            initial_query=risk_query,
            max_iterations=4,
            depth=SearchDepth.COMPREHENSIVE
        )

        # 生成侵权风险评估报告
        session.research_summary = await self._generate_infringement_risk_report(
            session, target_patent, technology_keywords
        )

        return session

    async def _generate_initial_queries(
        self,
        research_topic: str,
        focus_areas: Optional[List[str]] = None
    ) -> List[str]:
        """生成初始查询列表"""
        queries = []

        # 基础查询
        queries.append(research_topic)

        # 添加技术术语查询
        if focus_areas:
            for area in focus_areas:
                queries.append(f"{research_topic} {area}")

        # 添加专利特定查询
        queries.append(f"{research_topic} 专利")
        queries.append(f"{research_topic} 发明专利")
        queries.append(f"{research_topic} 技术方案")

        # 添加应用场景查询
        application_queries = [
            f"{research_topic} 应用",
            f"{research_topic} 实现",
            f"{research_topic} 系统"
        ]
        queries.extend(application_queries)

        return queries

    async def _select_best_initial_query(
        self,
        queries: List[str],
        research_topic: str
    ) -> str:
        """选择最佳初始查询"""
        # 简单策略：选择包含专利相关词汇的查询
        patent_keywords = ['专利', '发明', '技术', '方案', '系统']

        for query in queries:
            for keyword in patent_keywords:
                if keyword in query:
                    return query

        # 如果没有找到包含专利关键词的查询，返回第一个
        return queries[0]

    async def _intelligent_analysis(
        self,
        session: SearchSession,
        research_topic: str
    ) -> SearchSession:
        """智能分析搜索结果"""
        # 聚类分析专利
        clustered_patents = await self._cluster_patents(session.iterations[-1].results)

        # 识别关键技术趋势
        tech_trends = await self._identify_technology_trends(session.iterations)

        # 分析竞争格局
        competitive_landscape = await self._analyze_competitive_landscape(session)

        # 生成战略建议
        strategic_recommendations = await self._generate_strategic_recommendations(
            session, research_topic
        )

        # 更新研究摘要
        if session.research_summary:
            session.research_summary.technological_trends.extend(tech_trends)
            session.research_summary.competing_applicants.extend(competitive_landscape)
            session.research_summary.recommendations.extend(strategic_recommendations)

        return session

    async def _cluster_patents(
        self,
        patents: List[PatentSearchResult]
    ) -> Dict[str, List[PatentSearchResult]]:
        """聚类专利结果"""
        clusters = {}

        # 按专利类型聚类
        for patent in patents:
            if patent.patent_metadata and patent.patent_metadata.patent_type:
                patent_type = patent.patent_metadata.patent_type.value
                if patent_type not in clusters:
                    clusters[patent_type] = []
                clusters[patent_type].append(patent)

        # 按IPC分类聚类
        ipc_clusters = {}
        for patent in patents:
            if patent.patent_metadata and patent.patent_metadata.ipc_main_class:
                ipc_class = patent.patent_metadata.ipc_main_class
                if ipc_class not in ipc_clusters:
                    ipc_clusters[ipc_class] = []
                ipc_clusters[ipc_class].append(patent)

        # 合并聚类结果
        clusters.update({f"IPC_{ipc}": patents for ipc, patents in ipc_clusters.items()})

        return clusters

    async def _identify_technology_trends(
        self,
        iterations: List[SearchQuery]
    ) -> List[str]:
        """识别技术趋势"""
        trends = []

        # 分析查询演进趋势
        query_evolution = []
        for iteration in iterations:
            if hasattr(iteration, 'query') and iteration.query:
                query_evolution.append(iteration.query.text)

        if query_evolution:
            trends.append('搜索查询逐步精细化，技术方向更加明确')

        return trends

    async def _analyze_competitive_landscape(
        self,
        session: SearchSession
    ) -> List[str]:
        """分析竞争格局"""
        landscape = []

        # 收集所有申请人信息
        applicants = set()
        for iteration in session.iterations:
            for result in iteration.results:
                if result.patent_metadata and result.patent_metadata.applicant:
                    applicants.add(result.patent_metadata.applicant)

        if len(applicants) > 10:
            landscape.append(f"该领域竞争激烈，涉及{len(applicants)}个不同的申请人")
        elif len(applicants) > 5:
            landscape.append(f"该领域竞争适中，涉及{len(applicants)}个主要申请人")
        else:
            landscape.append(f"该领域竞争较少，主要由{len(applicants)}个申请人主导")

        return landscape

    async def _generate_strategic_recommendations(
        self,
        session: SearchSession,
        research_topic: str
    ) -> List[str]:
        """生成战略建议"""
        recommendations = []

        # 基于搜索结果数量给出建议
        if session.total_patents_found < 10:
            recommendations.append('该领域专利较少，可能存在创新机会')
        elif session.total_patents_found > 100:
            recommendations.append('该领域专利密集，建议进一步细分技术方向')

        # 基于搜索深度给出建议
        if session.current_iteration >= session.max_iterations:
            recommendations.append('已进行深度搜索，建议基于现有结果进行详细分析')

        return recommendations

    async def _generate_competitive_analysis_report(
        self,
        session: SearchSession,
        company_name: str,
        technology_domain: str | None = None
    ) -> ResearchSummary:
        """生成竞争分析报告"""
        # 统计目标公司的专利
        target_company_patents = []
        other_company_patents = []

        for iteration in session.iterations:
            for result in iteration.results:
                if result.patent_metadata:
                    if company_name.lower() in result.patent_metadata.applicant.lower():
                        target_company_patents.append(result)
                    else:
                        other_company_patents.append(result)

        # 生成竞争分析
        summary = ResearchSummary(
            topic=f"{company_name} 竞争分析",
            key_findings=[
                f"{company_name}拥有{len(target_company_patents)}项相关专利",
                f"竞争对手拥有{len(other_company_patents)}项相关专利"
            ],
            main_patents=[p.title for p in target_company_patents[:5]],
            technological_trends=[
                f"专利数量比例: {company_name} vs 竞争对手 = {len(target_company_patents)}:{len(other_company_patents)}"
            ],
            competing_applicants=self._extract_top_competitors(other_company_patents),
            innovation_insights=[
                f"{company_name}在该领域的专利布局策略分析"
            ],
            recommendations=[
                '建议监控主要竞争对手的专利申请动态',
                '加强技术创新和专利布局'
            ]
        )

        return summary

    async def _generate_trend_analysis_report(
        self,
        session: SearchSession,
        technology: str,
        time_period: str
    ) -> ResearchSummary:
        """生成技术趋势分析报告"""
        # 分析技术发展趋势
        all_patents = []
        for iteration in session.iterations:
            all_patents.extend(iteration.results)

        summary = ResearchSummary(
            topic=f"{technology} 技术趋势分析",
            key_findings=[
                f"在过去{time_period}内发现{len(all_patents)}项相关专利"
            ],
            main_patents=[p.title for p in all_patents[:10]],
            technological_trends=self._extract_technology_trends(all_patents),
            innovation_insights=[
                f"{technology}技术的发展方向和应用前景"
            ],
            recommendations=[
                '持续关注该技术领域的发展动态',
                '加强相关技术的研发投入'
            ]
        )

        return summary

    async def _generate_infringement_risk_report(
        self,
        session: SearchSession,
        target_patent: PatentMetadata,
        technology_keywords: List[str]
    ) -> ResearchSummary:
        """生成侵权风险评估报告"""
        summary = ResearchSummary(
            topic=f"专利 {target_patent.patent_id} 侵权风险评估",
            key_findings=[
                f"目标专利: {target_patent.patent_name}",
                f"风险关键词: {', '.join(technology_keywords)}"
            ],
            main_patents=[target_patent.patent_name],
            technological_trends=[
                '相关技术的专利布局情况'
            ],
            innovation_insights=[
                '潜在侵权风险点分析'
            ],
            recommendations=[
                '建议进行详细的专利侵权分析',
                '考虑申请专利无效或规避设计'
            ]
        )

        return summary

    async def _get_patent_by_id(self, patent_id: str) -> PatentMetadata | None:
        """根据专利ID获取专利信息"""
        # 这里可以集成数据库查询来获取专利信息
        return None

    def _extract_top_competitors(self, patents: List[PatentSearchResult]) -> List[str]:
        """提取主要竞争对手"""
        competitor_counts = {}
        for patent in patents:
            if patent.patent_metadata and patent.patent_metadata.applicant:
                applicant = patent.patent_metadata.applicant
                competitor_counts[applicant] = competitor_counts.get(applicant, 0) + 1

        # 返回专利数量最多的前5个竞争对手
        top_competitors = sorted(competitor_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        return [f"{competitor} ({count}项专利)" for competitor, count in top_competitors]

    def _extract_technology_trends(self, patents: List[PatentSearchResult]) -> List[str]:
        """提取技术趋势"""
        trends = []

        # 分析IPC分类分布
        ipc_distribution = {}
        for patent in patents:
            if patent.patent_metadata and patent.patent_metadata.ipc_main_class:
                ipc_class = patent.patent_metadata.ipc_main_class
                ipc_distribution[ipc_class] = ipc_distribution.get(ipc_class, 0) + 1

        if ipc_distribution:
            top_ipc = max(ipc_distribution, key=ipc_distribution.get)
            trends.append(f"主要技术方向: {top_ipc} ({ipc_distribution[top_ipc]}项专利)")

        # 分析专利类型分布
        type_distribution = {}
        for patent in patents:
            if patent.patent_metadata and patent.patent_metadata.patent_type:
                patent_type = patent.patent_metadata.patent_type.value
                type_distribution[patent_type] = type_distribution.get(patent_type, 0) + 1

        if type_distribution:
            for patent_type, count in type_distribution.items():
                trends.append(f"{patent_type}专利: {count}项")

        return trends

    async def search(
        self,
        query: str,
        max_results: int = 10,
        strategy: str = 'hybrid',
        use_cache: bool = True
    ) -> List[PatentSearchResult]:
        """
        执行单次专利搜索

        Args:
            query: 搜索查询
            max_results: 最大结果数量
            strategy: 搜索策略 (hybrid, text, vector)
            use_cache: 是否使用缓存

        Returns:
            搜索结果列表
        """
        logger.info(f"执行专利搜索: 查询='{query}', 最大结果={max_results}, 策略={strategy}")

        try:
            # 调用搜索引擎执行搜索
            results = await self.search_engine.search(
                query=query,
                max_results=max_results,
                strategy=strategy,
                use_cache=use_cache
            )

            logger.info(f"搜索完成，返回 {len(results)} 个结果")
            return results

        except Exception as e:
            logger.error(f"搜索失败: {e}")
            raise

    async def close(self):
        """关闭搜索代理，清理资源"""
        logger.info('正在关闭Athena迭代式搜索代理...')

        try:
            if hasattr(self.search_engine, 'close'):
                await self.search_engine.close()
            logger.info('Athena迭代式搜索代理已关闭')
        except Exception as e:
            logger.error(f"关闭搜索代理时出错: {e}")