#!/usr/bin/env python3
"""
LLM集成模块
支持Qwen推理模型进行智能查询生成、结果分析和专利洞察
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
import openai
from openai import AsyncOpenAI

from .types import (
    PatentMetadata,
    PatentSearchResult,
    PatentType,
    QueryExpansion,
    ResearchSummary,
    SearchIteration,
    SearchQuery,
    SearchSession,
)

logger = logging.getLogger(__name__)

class QwenLLMIntegration:
    """Qwen推理模型集成"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
        self.model_name = config.get('model_name', 'qwen-turbo')
        self.timeout = config.get('timeout', 60)
        self.max_tokens = config.get('max_tokens', 2000)
        self.temperature = config.get('temperature', 0.7)

        # 初始化OpenAI客户端（兼容Qwen API）
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout
        )

        # 缓存设置
        self.cache_ttl = config.get('cache_ttl', 3600)  # 1小时
        self.response_cache = {}

    async def generate_query_expansion(self, original_query: str, context: Dict | None = None) -> QueryExpansion:
        """生成查询扩展"""
        cache_key = f"query_expansion_{hash(original_query)}"
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result

        try:
            system_prompt = """你是一个专利搜索专家，擅长扩展和优化专利搜索查询。

请根据用户提供的原始查询，生成相关的扩展术语、同义词、相关概念、IPC分类建议和申请人建议。

返回JSON格式：
{
    'expanded_terms': ['扩展术语1', '扩展术语2'],
    'synonyms': ['同义词1', '同义词2'],
    'related_concepts': ['相关概念1', '相关概念2'],
    'ipc_suggestions': ['IPC分类号1', 'IPC分类号2'],
    'applicant_suggestions': ['知名申请人1', '知名申请人2'],
    'expansion_method': 'llm'
}

注意：
1. 扩展术语应该具有技术相关性
2. 考虑专利领域的专业术语
3. IPC分类号要准确对应技术领域
4. 申请人建议包括该领域的主要公司和研究机构
"""

            user_prompt = f"""原始查询：{original_query}

请为这个专利搜索查询生成扩展建议。{f'上下文信息：{context}' if context else ''}

重点考虑：
- 技术同义词和近义词
- 相关技术领域
- 该领域的主要申请人
- 可能的IPC分类号"""

            response = await self._call_llm(system_prompt, user_prompt)
            expansion_data = json.loads(response)

            query_expansion = QueryExpansion(
                original_query=original_query,
                expanded_terms=expansion_data.get('expanded_terms', []),
                synonyms=expansion_data.get('synonyms', []),
                related_concepts=expansion_data.get('related_concepts', []),
                ipc_suggestions=expansion_data.get('ipc_suggestions', []),
                applicant_suggestions=expansion_data.get('applicant_suggestions', []),
                expansion_method='llm',
                confidence=0.8
            )

            self._set_cache(cache_key, query_expansion)
            return query_expansion

        except Exception as e:
            logger.error(f"生成查询扩展失败: {e}")
            return QueryExpansion(
                original_query=original_query,
                expanded_terms=[],
                synonyms=[],
                related_concepts=[],
                ipc_suggestions=[],
                applicant_suggestions=[],
                expansion_method='failed',
                confidence=0.0
            )

    async def analyze_search_results(self, query: str, results: List[PatentSearchResult]) -> List[str]:
        """分析搜索结果并生成洞察"""
        if not results:
            return ['未找到相关专利结果']

        cache_key = f"analyze_results_{hash(query + str(len(results)))}"
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result

        try:
            # 准备结果摘要
            results_summary = []
            for i, result in enumerate(results[:10]):  # 只分析前10个结果
                summary = f"{i+1}. {result.title[:100]}"
                if result.patent_metadata:
                    if result.patent_metadata.applicant:
                        summary += f" - 申请人: {result.patent_metadata.applicant}"
                    if result.patent_metadata.ipc_code:
                        summary += f" - IPC: {result.patent_metadata.ipc_code}"
                results_summary.append(summary)

            system_prompt = """你是一个专利分析专家，擅长从专利搜索结果中提取关键洞察和趋势。

请分析提供的专利搜索结果，识别：
1. 技术趋势和方向
2. 主要申请人及其技术特点
3. 技术创新点
4. 潜在的竞争态势
5. 技术发展机会

返回分析洞察列表，每个洞察应该是简洁、有价值的专业观点。"""

            user_prompt = f"""搜索查询：{query}

搜索结果：
{chr(10).join(results_summary)}

请分析这些专利搜索结果，提供5-8个关键洞察。"""

            response = await self._call_llm(system_prompt, user_prompt)
            insights = self._parse_insights(response)

            self._set_cache(cache_key, insights)
            return insights

        except Exception as e:
            logger.error(f"分析搜索结果失败: {e}")
            return ['结果分析失败']

    async def generate_research_summary(self, session: SearchSession) -> ResearchSummary:
        """生成研究摘要"""
        try:
            # 收集所有迭代的信息
            all_results = []
            for iteration in session.iterations:
                all_results.extend(iteration.results)

            # 专利申请人分布
            applicant_stats = {}
            ipc_stats = {}
            key_patents = []

            for result in all_results[:50]:  # 考虑前50个最重要的专利
                if result.patent_metadata:
                    # 统计申请人
                    applicant = result.patent_metadata.applicant or '未知'
                    applicant_stats[applicant] = applicant_stats.get(applicant, 0) + 1

                    # 统计IPC分类
                    if result.patent_metadata.ipc_code:
                        ipc_main = result.patent_metadata.ipc_code.split('/')[0].split()[0]
                        ipc_stats[ipc_main] = ipc_stats.get(ipc_main, 0) + 1

                    # 收集关键专利
                    if result.combined_score > 0.7 and len(key_patents) < 10:
                        key_patents.append(result.title)

            # 转换为排序后的列表
            competing_applicants = sorted(applicant_stats.items(), key=lambda x: x[1], reverse=True)[:10]
            competing_applicants = [app for app, _ in competing_applicants]

            # 生成技术趋势
            technological_trends = await self._identify_technological_trends(session, all_results)

            # 生成创新洞察
            innovation_insights = await self._generate_innovation_insights(session, all_results)

            # 生成建议
            recommendations = await self._generate_recommendations(session, all_results, competing_applicants)

            # 计算置信度和完整度
            confidence_level = min(0.9, len(all_results) / 100.0)  # 基于结果数量
            completeness_score = min(0.95, session.current_iteration / session.max_iterations)

            research_summary = ResearchSummary(
                topic=session.topic,
                key_findings=[f"发现{len(all_results)}项相关专利', f'完成{session.current_iteration}轮深度搜索"],
                main_patents=key_patents,
                technological_trends=technological_trends,
                competing_applicants=competing_applicants,
                innovation_insights=innovation_insights,
                recommendations=recommendations,
                confidence_level=confidence_level,
                completeness_score=completeness_score
            )

            return research_summary

        except Exception as e:
            logger.error(f"生成研究摘要失败: {e}")
            return ResearchSummary(
                topic=session.topic,
                confidence_level=0.0,
                completeness_score=0.0
            )

    async def suggest_next_query(self, current_iteration: SearchIteration) -> str | None:
        """建议下一轮搜索查询"""
        try:
            # 分析当前搜索结果的质量和覆盖范围
            quality_score = current_iteration.quality_score
            result_count = current_iteration.total_results

            if quality_score > 0.8 and result_count > 20:
                # 如果质量已经很高，可以结束搜索
                return None

            system_prompt = """你是一个专利搜索策略专家，擅长根据当前搜索结果优化后续搜索查询。

请分析当前搜索的结果，并建议一个改进的搜索查询，以便：
1. 找到更多相关专利
2. 提高结果质量
3. 覆盖不同的技术角度
4. 发现更多申请人

返回一个简洁的搜索查询建议，或者返回"NONE"表示搜索已经足够。"""

            user_prompt = f"""当前查询：{current_iteration.query.text}
搜索质量评分：{quality_score:.2f}
结果数量：{result_count}
主要洞察：{'; '.join(current_iteration.insights[:3])}

请建议下一轮搜索查询，或者返回"NONE"如果认为搜索已经充分。"""

            response = await self._call_llm(system_prompt, user_prompt)
            suggestion = response.strip()

            if suggestion.upper() == 'NONE' or len(suggestion) < 3:
                return None

            return suggestion

        except Exception as e:
            logger.error(f"生成下一轮查询建议失败: {e}")
            return None

    async def _identify_technological_trends(self, session: SearchSession, results: List[PatentSearchResult]) -> List[str]:
        """识别技术趋势"""
        try:
            # 按年份分析专利分布
            year_stats = {}
            for result in results[:100]:
                if result.patent_metadata and result.patent_metadata.application_date:
                    year = result.patent_metadata.application_date.year
                    year_stats[year] = year_stats.get(year, 0) + 1

            # 分析关键词趋势
            recent_patents = [r for r in results if r.patent_metadata and
                            r.patent_metadata.application_date and
                            r.patent_metadata.application_date.year >= 2020]

            system_prompt = """你是一个技术趋势分析专家，请基于提供的专利信息，识别当前技术发展趋势。

返回4-6个技术趋势洞察，重点关注：
1. 技术发展方向
2. 创新热点
3. 应用领域扩展
4. 未来发展潜力"""

            user_prompt = f"""研究领域：{session.topic}
专利数量：{len(results)}
近年专利（2020+）：{len(recent_patents)}

请分析这个技术领域的发展趋势。"""

            response = await self._call_llm(system_prompt, user_prompt)
            trends = self._parse_insights(response)

            return trends

        except Exception as e:
            logger.error(f"识别技术趋势失败: {e}")
            return []

    async def _generate_innovation_insights(self, session: SearchSession, results: List[PatentSearchResult]) -> List[str]:
        """生成创新洞察"""
        try:
            system_prompt = """你是一个技术创新分析专家，请基于专利搜索结果，识别技术创新的关键洞察。

重点关注：
1. 核心技术创新点
2. 技术突破方向
3. 创新应用场景
4. 技术演进路径

返回4-6个创新洞察。"""

            user_prompt = f"""研究领域：{session.topic}
搜索轮次：{session.current_iteration}
专利数量：{len(results)}

请分析这个领域的技术创新特点。"""

            response = await self._call_llm(system_prompt, user_prompt)
            insights = self._parse_insights(response)

            return insights

        except Exception as e:
            logger.error(f"生成创新洞察失败: {e}")
            return []

    async def _generate_recommendations(self, session: SearchSession, results: List[PatentSearchResult], competitors: List[str]) -> List[str]:
        """生成建议"""
        try:
            system_prompt = """你是一个专利战略顾问，请基于专利搜索分析，为企业或研发团队提供战略建议。

建议应该涵盖：
1. 技术研发方向
2. 专利布局策略
3. 竞争应对措施
4. 合作机会识别

返回4-6个具体、可执行的建议。"""

            user_prompt = f"""研究领域：{session.topic}
主要竞争对手：{', '.join(competitors[:5])}
专利数量：{len(results)}
搜索完整度：{session.current_iteration/session.max_iterations:.1%}

请基于以上信息提供战略建议。"""

            response = await self._call_llm(system_prompt, user_prompt)
            recommendations = self._parse_insights(response)

            return recommendations

        except Exception as e:
            logger.error(f"生成建议失败: {e}")
            return []

    async def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """调用LLM"""
        try:
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ]

            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            raise

    def _parse_insights(self, response: str) -> List[str]:
        """解析LLM返回的洞察"""
        try:
            # 尝试解析JSON
            if response.strip().startswith('['):
                return json.loads(response)

            # 按行分割
            lines = response.split('\n')
            insights = []

            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('//'):
                    # 移除编号和符号
                    cleaned = line
                    for prefix in ['1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.',
                                 '-', '•', '*', '·', '■', '□', '▪', '▫']:
                        if cleaned.startswith(prefix):
                            cleaned = cleaned[len(prefix):].strip()
                            break

                    if len(cleaned) > 10:
                        insights.append(cleaned)

            return insights[:8]  # 最多返回8个洞察

        except Exception as e:
            logger.error(f"解析洞察失败: {e}")
            return [response[:200]] if response else []

    def _get_from_cache(self, key: str) -> Any:
        """从缓存获取"""
        if key in self.response_cache:
            cached_data, timestamp = self.response_cache[key]
            if time.time() - timestamp < self.cache_ttl:
                return cached_data
            else:
                del self.response_cache[key]
        return None

    def _set_cache(self, key: str, data: Any) -> Any:
        """设置缓存"""
        self.response_cache[key] = (data, time.time())

        # 限制缓存大小
        if len(self.response_cache) > 1000:
            oldest_key = min(self.response_cache.keys(),
                           key=lambda k: self.response_cache[k][1])
            del self.response_cache[oldest_key]

class MockLLMIntegration:
    """Mock LLM集成，用于测试和演示"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def generate_query_expansion(self, original_query: str, context: Dict | None = None) -> QueryExpansion:
        """生成查询扩展（Mock版本）"""
        return QueryExpansion(
            original_query=original_query,
            expanded_terms=[f"{original_query}技术', f'{original_query}系统', f'{original_query}方法"],
            synonyms=[original_query],
            related_concepts=[f"{original_query}应用', f'{original_query}实现"],
            ipc_suggestions=['G06F', 'H04L', 'C06F'],
            applicant_suggestions=['清华大学', '华为技术', '中科院'],
            expansion_method='mock',
            confidence=0.7
        )

    async def analyze_search_results(self, query: str, results: List[PatentSearchResult]) -> List[str]:
        """分析搜索结果（Mock版本）"""
        if not results:
            return ['未找到相关专利结果']

        insights = [
            f"找到{len(results)}项相关专利技术",
            '技术主要集中在人工智能和信息技术领域',
            '主要申请人包括高校和科技企业',
            '近年来该技术发展迅速',
            '建议关注核心技术创新和专利布局'
        ]

        return insights

    async def generate_research_summary(self, session: SearchSession) -> ResearchSummary:
        """生成研究摘要（Mock版本）"""
        all_results = []
        for iteration in session.iterations:
            all_results.extend(iteration.results)

        return ResearchSummary(
            topic=session.topic,
            key_findings=[
                f"通过{session.current_iteration}轮搜索发现{len(all_results)}项相关专利",
                '技术发展呈现多样化和专业化趋势',
                '主要申请人在该领域有较强技术积累'
            ],
            main_patents=[r.title for r in all_results[:5]],
            technological_trends=[
                '技术向智能化、集成化方向发展',
                '应用场景不断扩展',
                '与其他技术融合加深'
            ],
            competing_applicants=['华为技术', '腾讯科技', '阿里巴巴', '百度'],
            innovation_insights=[
                '核心算法持续优化',
                '硬件集成度提升',
                '应用场景创新'
            ],
            recommendations=[
                '加强核心技术专利布局',
                '关注竞争对手技术动态',
                '探索新兴应用场景'
            ],
            confidence_level=0.85,
            completeness_score=session.current_iteration / session.max_iterations
        )

    async def suggest_next_query(self, current_iteration: SearchIteration) -> str | None:
        """建议下一轮搜索查询（Mock版本）"""
        if current_iteration.quality_score > 0.7 and current_iteration.total_results > 15:
            return None

        # 简单的查询扩展逻辑
        original = current_iteration.query.text
        suggestions = [
            f"{original}技术原理",
            f"{original}应用案例",
            f"{original}发展趋势"
        ]

        import random
        return random.choice(suggestions) if random.random() > 0.3 else None