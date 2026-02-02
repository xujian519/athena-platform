#!/usr/bin/env python3
"""
Athena迭代式搜索系统核心引擎
基于XiaoXi搜索架构，集成多种搜索引擎，提供专利专业的迭代搜索能力
"""

import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

from .config import AthenaSearchConfig, SearchDepth, SearchStrategy
from .types import (
    PatentMetadata,
    PatentSearchResult,
    PatentType,
    QueryExpansion,
    ResultRelevance,
    SearchCache,
    SearchError,
    SearchFilter,
    SearchIteration,
    SearchQuery,
    SearchSession,
    SearchStatistics,
    SearchStatus,
)

# 配置日志
logger = logging.getLogger(__name__)

class AthenaIterativeSearchEngine:
    """Athena迭代式搜索引擎主类"""

    def __init__(self, config: AthenaSearchConfig | None = None):
        """
        初始化搜索引擎

        Args:
            config: 搜索配置，如果为None则使用默认配置
        """
        self.config = config or AthenaSearchConfig()
        self.elasticsearch_client = None
        self.vector_search_client = None
        self.external_engines = {}
        self.cache = {}
        self.statistics = SearchStatistics()

        # 初始化搜索引擎
        self._initialize_engines()

        logger.info('Athena迭代式搜索引擎初始化完成')

    def _initialize_engines(self) -> Any:
        """初始化各种搜索引擎"""
        try:
            # 初始化Elasticsearch客户端
            self._initialize_elasticsearch()

            # 初始化向量搜索引擎
            self._initialize_vector_search()

            # 初始化外部搜索引擎
            self._initialize_external_engines()

            logger.info('所有搜索引擎初始化成功')

        except Exception as e:
            logger.error(f"搜索引擎初始化失败: {e}")
            raise

    def _initialize_elasticsearch(self) -> Any:
        """初始化Elasticsearch客户端"""
        try:
            from elasticsearch import Elasticsearch

            # 连接到现有的Elasticsearch实例
            self.elasticsearch_client = Elasticsearch([{
                'host': 'localhost',
                'port': 9200,
                'scheme': 'http'
            }])

            # 测试连接
            if self.elasticsearch_client.ping():
                logger.info('Elasticsearch连接成功')
            else:
                logger.warning('Elasticsearch连接失败')

        except ImportError:
            logger.warning('Elasticsearch库未安装，跳过ES初始化')
        except Exception as e:
            logger.error(f"Elasticsearch初始化失败: {e}")

    def _initialize_vector_search(self) -> Any:
        """初始化向量搜索引擎"""
        try:
            # 这里可以集成FAISS或其他向量搜索引擎
            # 暂时使用PostgreSQL的pgvector扩展
            logger.info('向量搜索引擎初始化完成')

        except Exception as e:
            logger.error(f"向量搜索引擎初始化失败: {e}")

    def _initialize_external_engines(self) -> Any:
        """初始化外部搜索引擎"""
        if self.config.external_config.enable_baidu:
            self.external_engines['baidu'] = BaiduSearchEngine()

        if self.config.external_config.enable_bing:
            self.external_engines['bing'] = BingSearchEngine()

        if self.config.external_config.enable_sogou:
            self.external_engines['sogou'] = SogouSearchEngine()

        logger.info(f"初始化了 {len(self.external_engines)} 个外部搜索引擎")

    async def search(
        self,
        query: str,
        strategy: SearchStrategy = SearchStrategy.HYBRID,
        max_results: int = 10,
        filters: Optional[List[SearchFilter]] = None,
        use_cache: bool = True
    ) -> List[PatentSearchResult]:
        """
        执行单次搜索

        Args:
            query: 搜索查询
            strategy: 搜索策略
            max_results: 最大结果数
            filters: 搜索过滤器
            use_cache: 是否使用缓存

        Returns:
            专利搜索结果列表
        """
        start_time = time.time()

        try:
            # 检查缓存
            if use_cache and self.config.performance_config.enable_cache:
                cached_results = self._get_from_cache(query, max_results, filters)
                if cached_results:
                    logger.info(f"从缓存返回 {len(cached_results)} 条结果")
                    return cached_results

            # 根据策略执行搜索
            if strategy == SearchStrategy.HYBRID:
                results = await self._hybrid_search(query, max_results, filters)
            elif strategy == SearchStrategy.FULLTEXT:
                results = await self._fulltext_search(query, max_results, filters)
            elif strategy == SearchStrategy.SEMANTIC:
                results = await self._semantic_search(query, max_results, filters)
            elif strategy == SearchStrategy.EXTERNAL:
                results = await self._external_search(query, max_results)
            else:
                results = await self._hybrid_search(query, max_results, filters)

            # 后处理结果
            results = self._post_process_results(results, query)

            # 缓存结果
            if use_cache and self.config.performance_config.enable_cache:
                self._cache_results(query, results, filters)

            # 更新统计信息
            search_time = time.time() - start_time
            self._update_statistics(True, search_time, len(results))

            logger.info(f"搜索完成: 查询='{query}', 结果数={len(results)}, 耗时={search_time:.2f}s")

            return results

        except Exception as e:
            # 更新错误统计
            search_time = time.time() - start_time
            self._update_statistics(False, search_time, 0)

            logger.error(f"搜索失败: 查询='{query}', 错误={e}")
            raise

    async def iterative_search(
        self,
        initial_query: str,
        max_iterations: int = 3,
        depth: SearchDepth = SearchDepth.STANDARD,
        progress_callback: callable | None = None
    ) -> SearchSession:
        """
        执行迭代式深度搜索

        Args:
            initial_query: 初始查询
            max_iterations: 最大迭代轮数
            depth: 搜索深度
            progress_callback: 进度回调函数

        Returns:
            搜索会话对象，包含所有迭代结果和研究摘要
        """
        # 创建搜索会话
        session = SearchSession(
            topic=initial_query,
            initial_query=initial_query,
            max_iterations=max_iterations,
            status=SearchStatus.RUNNING,
            search_config={
                'depth': depth.value,
                'strategy': self.config.default_strategy.value
            }
        )

        try:
            logger.info(f"开始迭代搜索: 查询='{initial_query}', 最大轮数={max_iterations}")

            current_query = initial_query
            previous_results = []

            for iteration_num in range(1, max_iterations + 1):
                # 执行单轮搜索
                iteration = await self._run_search_iteration(
                    session=session,
                    iteration_number=iteration_num,
                    query=current_query,
                    previous_results=previous_results
                )

                # 添加到会话
                session.add_iteration(iteration)

                # 更新进度
                if progress_callback:
                    progress_callback(iteration_num, max_iterations, f"完成第{iteration_num}轮搜索")

                # 检查是否需要继续
                if iteration_num < max_iterations:
                    # 生成下一轮查询
                    next_query = await self._generate_next_query(
                        current_query, iteration.results, previous_results
                    )

                    if next_query and next_query != current_query:
                        current_query = next_query
                        previous_results.extend(iteration.results)
                    else:
                        logger.info(f"查询已收敛，停止迭代 (第{iteration_num}轮)")
                        break

            # 生成研究摘要
            session.research_summary = await self._generate_research_summary(session)

            # 计算统计信息
            session.total_patents_found = sum(len(iter.results) for iter in session.iterations)
            session.unique_patents = len(set(
                result.patent_metadata.patent_id
                for iter in session.iterations
                for result in iter.results
                if result.patent_metadata
            ))

            session.update_status(SearchStatus.COMPLETED)

            logger.info(f"迭代搜索完成: 总轮数={session.current_iteration}, 总专利数={session.total_patents_found}")

            return session

        except Exception as e:
            session.update_status(SearchStatus.FAILED)
            logger.error(f"迭代搜索失败: {e}")
            raise

    async def _hybrid_search(
        self,
        query: str,
        max_results: int,
        filters: Optional[List[SearchFilter]] = None
    ) -> List[PatentSearchResult]:
        """执行混合搜索（全文+向量+外部）"""
        all_results = []

        # 并行执行多种搜索
        tasks = []

        # Elasticsearch全文搜索
        if self.elasticsearch_client:
            tasks.append(self._elasticsearch_search(query, max_results, filters))

        # 向量搜索
        if self.vector_search_client:
            tasks.append(self._vector_search(query, max_results, filters))

        # 外部搜索引擎
        if self.external_engines:
            tasks.append(self._external_search(query, max_results // 2))

        # 等待所有搜索完成
        if tasks:
            results_lists = await asyncio.gather(*tasks, return_exceptions=True)

            for results in results_lists:
                if isinstance(results, Exception):
                    logger.error(f"搜索任务失败: {results}")
                    continue
                all_results.extend(results)

        # 混合结果排序和去重
        merged_results = self._merge_and_rank_results(all_results, max_results)

        return merged_results[:max_results]

    async def _elasticsearch_search(
        self,
        query: str,
        max_results: int,
        filters: Optional[List[SearchFilter]] = None
    ) -> List[PatentSearchResult]:
        """Elasticsearch全文搜索"""
        if not self.elasticsearch_client:
            return []

        try:
            # 构建ES查询
            es_query = {
                'query': {
                    'multi_match': {
                        'query': query,
                        'fields': [
                            'patent_name^3',
                            'abstract^2',
                            'claims_content^2',
                            'ipc_code',
                            'applicant'
                        ],
                        'type': 'best_fields',
                        'fuzziness': 'AUTO'
                    }
                },
                'size': max_results,
                'sort': [
                    {'_score': {'order': 'desc'}},
                    {'application_date': {'order': 'desc'}}
                ]
            }

            # 添加过滤器
            if filters:
                es_query['filter'] = self._build_es_filters(filters)

            # 执行搜索
            response = self.elasticsearch_client.search(
                index='patents',
                body=es_query
            )

            # 转换结果
            results = []
            for hit in response['hits']['hits']:
                patent_data = hit['_source']
                score = hit['_score']

                # 创建专利元数据
                patent_metadata = PatentMetadata(
                    patent_id=str(patent_data.get('id', '')),
                    patent_name=patent_data.get('patent_name', ''),
                    patent_type=PatentType(patent_data.get('patent_type', '')) if patent_data.get('patent_type') else None,
                    applicant=patent_data.get('applicant', ''),
                    inventor=patent_data.get('inventor', ''),
                    application_number=patent_data.get('application_number', ''),
                    ipc_code=patent_data.get('ipc_code', ''),
                    abstract=patent_data.get('abstract', ''),
                    claims_content=patent_data.get('claims_content', '')
                )

                # 创建搜索结果
                result = PatentSearchResult(
                    title=patent_data.get('patent_name', ''),
                    content=patent_data.get('abstract', ''),
                    score=score,
                    relevance=self._determine_relevance(score),
                    engine_type='elasticsearch',
                    patent_metadata=patent_metadata,
                    text_match_score=score
                )

                results.append(result)

            logger.info(f"Elasticsearch搜索返回 {len(results)} 条结果")
            return results

        except Exception as e:
            logger.error(f"Elasticsearch搜索失败: {e}")
            return []

    async def _vector_search(
        self,
        query: str,
        max_results: int,
        filters: Optional[List[SearchFilter]] = None
    ) -> List[PatentSearchResult]:
        """向量语义搜索"""
        # 这里可以实现向量搜索逻辑
        # 暂时返回空列表，后续可以集成FAISS或pgvector
        return []

    async def _external_search(
        self,
        query: str,
        max_results: int
    ) -> List[PatentSearchResult]:
        """外部搜索引擎"""
        results = []

        for engine_name, engine in self.external_engines.items():
            try:
                engine_results = await engine.search(query, max_results // len(self.external_engines))
                results.extend(engine_results)
            except Exception as e:
                logger.error(f"外部搜索引擎 {engine_name} 失败: {e}")

        return results

    def _merge_and_rank_results(
        self,
        results: List[PatentSearchResult],
        max_results: int
    ) -> List[PatentSearchResult]:
        """合并和排序搜索结果"""
        if not results:
            return []

        # 按专利ID去重
        unique_patents = {}
        for result in results:
            patent_id = None
            if result.patent_metadata:
                patent_id = result.patent_metadata.patent_id
            elif result.metadata.get('patent_id'):
                patent_id = result.metadata['patent_id']

            if patent_id:
                if patent_id not in unique_patents or result.combined_score > unique_patents[patent_id].combined_score:
                    unique_patents[patent_id] = result
            else:
                # 对于没有专利ID的结果，使用title作为key
                title_key = result.title.lower().strip()
                if title_key not in unique_patents or result.combined_score > unique_patents[title_key].combined_score:
                    unique_patents[title_key] = result

        # 按综合分数排序
        sorted_results = sorted(
            unique_patents.values(),
            key=lambda x: x.combined_score,
            reverse=True
        )

        return sorted_results

    def _post_process_results(
        self,
        results: List[PatentSearchResult],
        query: str
    ) -> List[PatentSearchResult]:
        """后处理搜索结果"""
        # 更新相关性等级
        for result in results:
            if result.combined_score >= 0.8:
                result.relevance = ResultRelevance.HIGH
            elif result.combined_score >= 0.5:
                result.relevance = ResultRelevance.MEDIUM
            else:
                result.relevance = ResultRelevance.LOW

        return results

    def _determine_relevance(self, score: float) -> ResultRelevance:
        """根据分数确定相关性等级"""
        if score >= 2.0:
            return ResultRelevance.HIGH
        elif score >= 1.0:
            return ResultRelevance.MEDIUM
        else:
            return ResultRelevance.LOW

    def _get_from_cache(
        self,
        query: str,
        max_results: int,
        filters: Optional[List[SearchFilter]] = None
    ) -> List[PatentSearchResult | None]:
        """从缓存获取搜索结果"""
        query_hash = self._generate_query_hash(query, max_results, filters)

        if query_hash in self.cache:
            cache_item = self.cache[query_hash]

            # 检查缓存是否过期
            if cache_item.expires_at and cache_item.expires_at < datetime.now():
                del self.cache[query_hash]
                return None

            cache_item.hit_count += 1
            return cache_item.results

        return None

    def _cache_results(
        self,
        query: str,
        results: List[PatentSearchResult],
        filters: Optional[List[SearchFilter]] = None
    ):
        """缓存搜索结果"""
        if len(self.cache) >= self.config.performance_config.max_cache_size:
            # 删除最旧的缓存项
            oldest_key = min(self.cache.keys(),
                           key=lambda k: self.cache[k].created_at)
            del self.cache[oldest_key]

        query_hash = self._generate_query_hash(query, len(results), filters)

        cache_item = SearchCache(
            query_hash=query_hash,
            results=results,
            search_time=0.0,  # 这里可以记录实际搜索时间
            total_results=len(results),
            expires_at=datetime.now() + timedelta(seconds=self.config.performance_config.cache_ttl)
        )

        self.cache[query_hash] = cache_item

    def _generate_query_hash(
        self,
        query: str,
        max_results: int,
        filters: Optional[List[SearchFilter]] = None
    ) -> str:
        """生成查询哈希值用于缓存"""
        query_data = {
            'query': query,
            'max_results': max_results,
            'filters': [f.__dict__ for f in filters] if filters else []
        }
        query_str = json.dumps(query_data, sort_keys=True)
        return hashlib.md5(query_str.encode(), usedforsecurity=False).hexdigest()

    def _update_statistics(
        self,
        success: bool,
        search_time: float,
        result_count: int
    ):
        """更新搜索统计信息"""
        self.statistics.total_searches += 1

        if success:
            self.statistics.successful_searches += 1
        else:
            self.statistics.failed_searches += 1

        # 更新平均响应时间
        total_time = self.statistics.average_response_time * (self.statistics.total_searches - 1)
        self.statistics.average_response_time = (total_time + search_time) / self.statistics.total_searches

        # 更新平均结果数
        total_results = self.statistics.average_results_per_search * (self.statistics.total_searches - 1)
        self.statistics.average_results_per_search = (total_results + result_count) / self.statistics.total_searches

    async def _run_search_iteration(
        self,
        session: SearchSession,
        iteration_number: int,
        query: str,
        previous_results: List[PatentSearchResult]
    ) -> SearchIteration:
        """执行单轮搜索迭代"""
        start_time = time.time()

        # 创建查询对象
        search_query = SearchQuery(
            text=query,
            original_text=session.initial_query,
            query_type='iterative'
        )

        # 执行搜索
        results = await self.search(
            query=query,
            strategy=SearchStrategy.HYBRID,
            max_results=self.config.iterative_config.top_k_per_iteration
        )

        # 计算搜索质量分数
        quality_score = self._calculate_iteration_quality(results, previous_results)

        # 生成洞察
        insights = self._generate_iteration_insights(results, iteration_number)

        search_time = time.time() - start_time

        iteration = SearchIteration(
            iteration_number=iteration_number,
            query=search_query,
            results=results,
            search_time=search_time,
            total_results=len(results),
            quality_score=quality_score,
            insights=insights
        )

        logger.info(f"第{iteration_number}轮搜索完成: 查询='{query}', 结果数={len(results)}, 耗时={search_time:.2f}s")

        return iteration

    def _calculate_iteration_quality(
        self,
        results: List[PatentSearchResult],
        previous_results: List[PatentSearchResult]
    ) -> float:
        """计算迭代质量分数"""
        if not results:
            return 0.0

        # 基于结果相关性、多样性、新颖性计算质量分数
        relevance_score = sum(1 for r in results if r.relevance == ResultRelevance.HIGH) / len(results)

        # 计算与之前结果的重复度
        new_results = 0
        for result in results:
            is_new = True
            for prev_result in previous_results:
                if (result.patent_metadata and prev_result.patent_metadata and
                    result.patent_metadata.patent_id == prev_result.patent_metadata.patent_id):
                    is_new = False
                    break
            if is_new:
                new_results += 1

        novelty_score = new_results / len(results) if results else 0.0

        # 综合质量分数
        quality_score = (relevance_score * 0.5 + novelty_score * 0.5)

        return quality_score

    def _generate_iteration_insights(
        self,
        results: List[PatentSearchResult],
        iteration_number: int
    ) -> List[str]:
        """生成迭代洞察"""
        insights = []

        if not results:
            return ['未找到相关专利结果']

        # 分析专利类型分布
        patent_types = {}
        for result in results:
            if result.patent_metadata and result.patent_metadata.patent_type:
                patent_type = result.patent_metadata.patent_type.value
                patent_types[patent_type] = patent_types.get(patent_type, 0) + 1

        if patent_types:
            dominant_type = max(patent_types, key=patent_types.get)
            insights.append(f"本轮搜索主要发现{dominant_type}专利 ({patent_types[dominant_type]}项)")

        # 分析申请人分布
        applicants = {}
        for result in results:
            if result.patent_metadata and result.patent_metadata.applicant:
                applicant = result.patent_metadata.applicant
                applicants[applicant] = applicants.get(applicant, 0) + 1

        if len(applicants) > 1:
            top_applicant = max(applicants, key=applicants.get)
            insights.append(f"主要申请人: {top_applicant} ({applicants[top_applicant]}项专利)")

        # 分析IPC分类
        ipc_classes = set()
        for result in results:
            if result.patent_metadata and result.patent_metadata.ipc_main_class:
                ipc_classes.add(result.patent_metadata.ipc_main_class)

        if len(ipc_classes) > 1:
            insights.append(f"涉及{len(ipc_classes)}个不同的IPC主分类")

        return insights

    async def _generate_next_query(
        self,
        current_query: str,
        current_results: List[PatentSearchResult],
        previous_results: List[PatentSearchResult]
    ) -> str | None:
        """生成下一轮查询"""
        # 这里可以集成LLM来生成更智能的下一轮查询
        # 暂时使用简单的查询扩展策略

        if not current_results:
            return None

        # 提取关键词和技术术语
        keywords = set()
        ipc_terms = set()
        applicant_terms = set()

        for result in current_results[:5]:  # 只考虑前5个结果
            if result.patent_metadata:
                # 提取标题关键词
                title_words = result.patent_metadata.patent_name.split()
                keywords.update([word for word in title_words if len(word) > 2])

                # 提取IPC分类
                if result.patent_metadata.ipc_main_class:
                    ipc_terms.add(result.patent_metadata.ipc_main_class)

                # 提取申请人
                if result.patent_metadata.applicant:
                    applicant_terms.add(result.patent_metadata.applicant)

        # 生成下一轮查询
        next_query_terms = []

        # 添加新的关键词
        if keywords:
            next_query_terms.append(list(keywords)[:3])

        # 添加IPC分类
        if ipc_terms:
            next_query_terms.append(list(ipc_terms)[:2])

        # 如果有新的查询词，生成下一轮查询
        if next_query_terms:
            expanded_query = current_query + ' ' + ' '.join([' '.join(terms) for terms in next_query_terms])
            return expanded_query[:200]  # 限制查询长度

        return None

    async def _generate_research_summary(self, session: SearchSession) -> 'ResearchSummary':
        """生成研究摘要"""
        from .types import ResearchSummary

        if not session.iterations:
            return ResearchSummary(topic=session.topic)

        # 收集所有专利结果
        all_patents = []
        for iteration in session.iterations:
            all_patents.extend(iteration.results)

        # 生成研究摘要
        summary = ResearchSummary(
            topic=session.topic,
            key_findings=[f"通过{len(session.iterations)}轮搜索，发现{len(all_patents)}项相关专利"],
            main_patents=[r.title for r in all_patents[:5] if r.title],
            technological_trends=self._extract_technology_trends(all_patents),
            competing_applicants=self._extract_competing_applicants(all_patents),
            innovation_insights=self._extract_innovation_insights(session.iterations),
            recommendations=self._generate_recommendations(all_patents),
            confidence_level=self._calculate_confidence_level(session),
            completeness_score=self._calculate_completeness_score(session)
        )

        return summary

    def _extract_technology_trends(self, patents: List[PatentSearchResult]) -> List[str]:
        """提取技术趋势"""
        trends = []

        # 分析IPC分类趋势
        ipc_counts = {}
        for patent in patents:
            if patent.patent_metadata and patent.patent_metadata.ipc_main_class:
                ipc = patent.patent_metadata.ipc_main_class
                ipc_counts[ipc] = ipc_counts.get(ipc, 0) + 1

        if ipc_counts:
            top_ipc = max(ipc_counts, key=ipc_counts.get)
            trends.append(f"主要技术领域: {top_ipc}")

        # 分析申请时间趋势
        years = []
        for patent in patents:
            if patent.patent_metadata and patent.patent_metadata.application_date:
                years.append(patent.patent_metadata.application_date.year)

        if years:
            recent_years = [y for y in years if y >= 2020]
            if recent_years:
                trends.append(f"近年来技术活跃度较高 ({len(recent_years)}项专利)")

        return trends

    def _extract_competing_applicants(self, patents: List[PatentSearchResult]) -> List[str]:
        """提取竞争对手"""
        applicant_counts = {}

        for patent in patents:
            if patent.patent_metadata and patent.patent_metadata.applicant:
                applicant = patent.patent_metadata.applicant
                applicant_counts[applicant] = applicant_counts.get(applicant, 0) + 1

        # 返回专利数量最多的前3个申请人
        top_applicants = sorted(applicant_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        return [f"{applicant} ({count}项专利)" for applicant, count in top_applicants]

    def _extract_innovation_insights(self, iterations: List[SearchIteration]) -> List[str]:
        """提取创新洞察"""
        insights = []

        for iteration in iterations:
            insights.extend(iteration.insights)

        # 去重
        return list(set(insights))

    def _generate_recommendations(self, patents: List[PatentSearchResult]) -> List[str]:
        """生成建议"""
        recommendations = []

        if len(patents) > 50:
            recommendations.append('专利数量较多，建议进一步细化搜索范围')

        # 分析专利类型分布
        patent_types = {}
        for patent in patents:
            if patent.patent_metadata and patent.patent_metadata.patent_type:
                patent_type = patent.patent_metadata.patent_type.value
                patent_types[patent_type] = patent_types.get(patent_type, 0) + 1

        if patent_types:
            if '发明' in patent_types and patent_types['发明'] / len(patents) > 0.7:
                recommendations.append('该领域发明专利占主导，技术创新程度较高')

        return recommendations

    def _calculate_confidence_level(self, session: SearchSession) -> float:
        """计算置信度"""
        if not session.iterations:
            return 0.0

        # 基于迭代质量和结果数量计算置信度
        avg_quality = sum(iter.quality_score for iter in session.iterations) / len(session.iterations)
        result_factor = min(session.unique_patents / 10, 1.0)  # 10个专利为满分

        confidence = (avg_quality * 0.7 + result_factor * 0.3)
        return min(confidence, 1.0)

    def _calculate_completeness_score(self, session: SearchSession) -> float:
        """计算完整度分数"""
        if not session.iterations:
            return 0.0

        # 基于迭代轮数和结果多样性计算完整度
        iteration_factor = session.current_iteration / session.max_iterations
        diversity_factor = len(set(r.title for r in session.iterations[-1].results if r.title)) / max(len(session.iterations[-1].results), 1)

        completeness = (iteration_factor * 0.5 + diversity_factor * 0.5)
        return min(completeness, 1.0)

    def _build_es_filters(self, filters: List[SearchFilter]) -> List[Dict]:
        """构建Elasticsearch过滤器"""
        es_filters = []

        for filter_obj in filters:
            if filter_obj.operator == 'eq':
                es_filters.append({
                    'term': {filter_obj.field_name: filter_obj.value}
                })
            elif filter_obj.operator == 'in':
                es_filters.append({
                    'terms': {filter_obj.field_name: filter_obj.value}
                })
            elif filter_obj.operator == 'range':
                es_filters.append({
                    'range': {filter_obj.field_name: filter_obj.value}
                })
            # 可以添加更多操作符支持

        return es_filters

class BaiduSearchEngine:
    """百度搜索引擎"""

    async def search(self, query: str, max_results: int) -> List[PatentSearchResult]:
        """执行百度搜索"""
        # 这里可以实现百度搜索API调用
        # 暂时返回空列表
        return []

class BingSearchEngine:
    """Bing搜索引擎"""

    async def search(self, query: str, max_results: int) -> List[PatentSearchResult]:
        """执行Bing搜索"""
        # 这里可以实现Bing搜索API调用
        # 暂时返回空列表
        return []

class SogouSearchEngine:
    """搜狗搜索引擎"""

    async def search(self, query: str, max_results: int) -> List[PatentSearchResult]:
        """执行搜狗搜索"""
        # 这里可以实现搜狗搜索API调用
        # 暂时返回空列表
        return []