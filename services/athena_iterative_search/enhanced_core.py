#!/usr/bin/env python3
"""
增强版核心搜索引擎
集成Qwen LLM、外部搜索引擎、向量搜索和性能优化
"""

import asyncio
import logging
import time
from typing import Any

from .config_enhanced import (
    AthenaEnhancedSearchConfig,
    LLMProvider,
    get_config_by_environment,
)
from .core import ElasticsearchEngine  # 使用原有的Elasticsearch引擎
from .enhanced_vector_search import EnhancedVectorSearch
from .external_search_engines import ExternalSearchEngineManager
from .llm_integration import MockLLMIntegration, QwenLLMIntegration
from .performance_optimizer import (
    PerformanceOptimizer,
    RateLimiter,
)
from .types import (
    PatentSearchResult,
    SearchDepth,
    SearchIteration,
    SearchQuery,
    SearchSession,
    SearchStatus,
    SearchStrategy,
)

logger = logging.getLogger(__name__)

class AthenaEnhancedIterativeSearchEngine:
    """Athena增强迭代式搜索引擎"""

    def __init__(self, config: AthenaEnhancedSearchConfig | None = None):
        # 配置初始化
        self.config = config or get_config_by_environment()
        self.db_config = self._get_db_config()

        # 组件初始化
        self.llm_integration = None
        self.external_manager = None
        self.vector_search = None
        self.elasticsearch = None
        self.performance_optimizer = None

        # 速率限制器
        self.rate_limiters = {
            'search': RateLimiter(100, 60),  # 每分钟100次搜索
            'llm': RateLimiter(50, 60),      # 每分钟50次LLM请求
            'external': RateLimiter(30, 60)  # 每分钟30次外部搜索
        }

        # 搜索会话存储
        self.sessions = {}
        self.session_lock = asyncio.Lock()

        # 初始化组件
        self._init_components()

    def _get_db_config(self) -> dict[str, Any]:
        """获取数据库配置"""
        import os
        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '5432')),
            'database': os.getenv('DB_NAME', 'athena_patents'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', ''),
            'redis_host': os.getenv('REDIS_HOST', 'localhost'),
            'redis_port': int(os.getenv('REDIS_PORT', '6379')),
            'redis_db': int(os.getenv('REDIS_DB', '0')),
            'elasticsearch_host': os.getenv('ES_HOST', 'localhost'),
            'elasticsearch_port': int(os.getenv('ES_PORT', '9200'))
        }

    async def _init_components(self):
        """初始化所有组件"""
        try:
            # 初始化LLM集成
            await self._init_llm_integration()

            # 初始化外部搜索引擎
            self.external_manager = ExternalSearchEngineManager(
                self.config.get_external_engines_config()
            )

            # 初始化向量搜索
            self.vector_search = EnhancedVectorSearch(
                self.config.vector_config,
                self.db_config
            )

            # 初始化Elasticsearch
            self.elasticsearch = ElasticsearchEngine(self.db_config)

            # 初始化性能优化器
            perf_config = {
                'cache_ttl': self.config.cache_config.query_cache_ttl,
                'cache_size': self.config.cache_config.query_cache_size,
                'http_connections': self.config.enhanced_performance.http_connections,
                'redis_connections': self.config.enhanced_performance.redis_connections,
                'max_workers': self.config.enhanced_performance.max_concurrent_llm_requests,
                'enable_monitoring': True
            }

            self.performance_optimizer = PerformanceOptimizer(perf_config)
            await self.performance_optimizer.start()

            # 设置全局优化器
            from .performance_optimizer import initialize_global_optimizer
            await initialize_global_optimizer(perf_config)

            logger.info('增强搜索引擎初始化完成')

        except Exception as e:
            logger.error(f"搜索引擎初始化失败: {e}")
            raise

    async def _init_llm_integration(self):
        """初始化LLM集成"""
        llm_config = self.config.get_llm_config()

        if self.config.llm_config.provider == LLMProvider.QWEN and llm_config.get('api_key'):
            self.llm_integration = QwenLLMIntegration(llm_config)
            logger.info('使用Qwen LLM服务')
        else:
            self.llm_integration = MockLLMIntegration(llm_config)
            logger.info('使用Mock LLM服务')

    async def search(
        self,
        query: str,
        strategy: SearchStrategy = SearchStrategy.HYBRID,
        max_results: int = 10,
        filters: dict[str, Any] | None = None,
        use_cache: bool = True
    ) -> list[PatentSearchResult]:
        """执行单次搜索"""
        await self.rate_limiters['search'].wait_for_slot()

        # 缓存检查
        if use_cache and self.performance_optimizer:
            cache_key = f"search_{strategy.value}_{hash(query)}"
            cached_results = await self.performance_optimizer.cache_manager.get(
                'search', cache_key
            )
            if cached_results:
                return cached_results

        start_time = time.time()
        results = []

        try:
            if strategy == SearchStrategy.HYBRID:
                results = await self._hybrid_search(query, max_results, filters)
            elif strategy == SearchStrategy.FULLTEXT:
                results = await self._fulltext_search(query, max_results, filters)
            elif strategy == SearchStrategy.SEMANTIC:
                results = await self._semantic_search(query, max_results, filters)
            elif strategy == SearchStrategy.EXTERNAL:
                results = await self._external_search(query, max_results)
            else:
                # 默认混合搜索
                results = await self._hybrid_search(query, max_results, filters)

            # 排序结果
            results.sort(key=lambda x: x.combined_score, reverse=True)
            results = results[:max_results]

            # 缓存结果
            if use_cache and self.performance_optimizer:
                await self.performance_optimizer.cache_manager.set(
                    'search', cache_key, results
                )

            search_time = time.time() - start_time
            logger.info(f"搜索完成，返回{len(results)}条结果，耗时{search_time:.3f}秒")

            return results

        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []

    async def _hybrid_search(
        self,
        query: str,
        max_results: int,
        filters: dict[str, Any] | None = None
    ) -> list[PatentSearchResult]:
        """混合搜索（Elasticsearch + 向量 + 外部）"""
        weights = self.config.engine_weights

        # 并行执行各搜索引擎
        tasks = []

        # Elasticsearch搜索
        if weights.elasticsearch_weight > 0:
            tasks.append(self._elasticsearch_search(query, max_results, filters))

        # 向量搜索
        if weights.vector_weight > 0:
            tasks.append(self._vector_search(query, max_results, filters))

        # 外部搜索
        if weights.external_weight > 0:
            tasks.append(self._external_search(query, max_results))

        # 等待所有搜索完成
        results_lists = await asyncio.gather(*tasks, return_exceptions=True)

        # 合并结果
        all_results = {}
        for i, results in enumerate(results_lists):
            if isinstance(results, Exception):
                logger.error(f"搜索引擎{i}失败: {results}")
                continue

            for result in results:
                result_id = result.patent_metadata.patent_id if result.patent_metadata else result.title
                if result_id not in all_results:
                    all_results[result_id] = result
                    result.engine_scores = {}

                # 记录各引擎的分数
                if i == 0:  # Elasticsearch
                    all_results[result_id].engine_scores['elasticsearch'] = result.score
                elif i == 1:  # Vector
                    all_results[result_id].engine_scores['vector'] = result.similarity_score
                elif i == 2:  # External
                    all_results[result_id].engine_scores['external'] = result.score

        # 计算综合分数
        for result in all_results.values():
            scores = result.engine_scores
            combined_score = (
                scores.get('elasticsearch', 0) * weights.elasticsearch_weight +
                scores.get('vector', 0) * weights.vector_weight +
                scores.get('external', 0) * weights.external_weight
            )
            result.combined_score = combined_score

        return list(all_results.values())

    async def _elasticsearch_search(
        self,
        query: str,
        max_results: int,
        filters: dict[str, Any] | None = None
    ) -> list[PatentSearchResult]:
        """Elasticsearch搜索"""
        try:
            # 转换过滤器格式
            es_filters = []
            if filters:
                for key, value in filters.items():
                    if key == 'patent_type':
                        es_filters.append({'term': {'patent_type': value}})
                    elif key == 'applicant':
                        es_filters.append({'match': {'applicant': value}})
                    elif key == 'ipc_code':
                        es_filters.append({'prefix': {'ipc_code': value}})
                    elif key == 'date_range':
                        es_filters.append({
                            'range': {
                                'application_date': {
                                    'gte': value.get('start'),
                                    'lte': value.get('end')
                                }
                            }
                        })

            results = await self.elasticsearch.search(
                query=query,
                max_results=max_results,
                filters=es_filters
            )

            return results

        except Exception as e:
            logger.error(f"Elasticsearch搜索失败: {e}")
            return []

    async def _vector_search(
        self,
        query: str,
        max_results: int,
        filters: dict[str, Any] | None = None
    ) -> list[PatentSearchResult]:
        """向量搜索"""
        try:
            results = await self.vector_search.hybrid_search(
                query_text=query,
                top_k=max_results,
                text_weight=0.3,
                vector_weight=0.7,
                filters=filters
            )
            return results
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            return []

    async def _external_search(self, query: str, max_results: int) -> list[PatentSearchResult]:
        """外部搜索引擎"""
        try:
            await self.rate_limiters['external'].wait_for_slot()
            results = await self.external_manager.search_all(query, max_results)
            return results
        except Exception as e:
            logger.error(f"外部搜索失败: {e}")
            return []

    async def _fulltext_search(
        self,
        query: str,
        max_results: int,
        filters: dict[str, Any] | None = None
    ) -> list[PatentSearchResult]:
        """全文搜索"""
        return await self._elasticsearch_search(query, max_results, filters)

    async def _semantic_search(
        self,
        query: str,
        max_results: int,
        filters: dict[str, Any] | None = None
    ) -> list[PatentSearchResult]:
        """语义搜索"""
        return await self._vector_search(query, max_results, filters)

    async def iterative_search(
        self,
        initial_query: str,
        max_iterations: int = 3,
        depth: SearchDepth = SearchDepth.STANDARD,
        focus_areas: list[str] | None = None,
        progress_callback: callable | None = None
    ) -> SearchSession:
        """迭代式深度搜索"""
        session = SearchSession(
            topic=initial_query,
            initial_query=initial_query,
            max_iterations=max_iterations,
            strategy='iterative'
        )

        session.update_status(SearchStatus.RUNNING)

        try:
            current_query = initial_query
            all_patents = set()

            for iteration_num in range(1, max_iterations + 1):
                if progress_callback:
                    progress_callback(iteration_num, max_iterations, f"执行第{iteration_num}轮搜索")

                # 执行搜索
                iteration_results = await self.search(
                    query=current_query,
                    strategy=SearchStrategy.HYBRID,
                    max_results=self.config.iterative_config.top_k_per_iteration
                )

                # 记录迭代
                iteration = SearchIteration(
                    iteration_number=iteration_num,
                    query=SearchQuery(text=current_query, original_text=initial_query),
                    results=iteration_results,
                    search_time=0.0,  # 实际应该在搜索中记录
                    total_results=len(iteration_results),
                    quality_score=self._calculate_quality_score(iteration_results)
                )

                # 生成洞察
                if self.llm_integration:
                    try:
                        await self.rate_limiters['llm'].wait_for_slot()
                        insights = await self.llm_integration.analyze_search_results(
                            current_query, iteration_results
                        )
                        iteration.insights = insights
                    except Exception as e:
                        logger.error(f"生成洞察失败: {e}")
                        iteration.insights = ['分析失败']

                # 建议下一轮查询
                if iteration_num < max_iterations and self.llm_integration:
                    try:
                        await self.rate_limiters['llm'].wait_for_slot()
                        next_query = await self.llm_integration.suggest_next_query(iteration)
                        if next_query:
                            iteration.next_query_suggestion = next_query
                            current_query = next_query
                    except Exception as e:
                        logger.error(f"生成下一轮查询失败: {e}")

                session.add_iteration(iteration)

                # 更新专利统计
                for result in iteration_results:
                    patent_id = result.patent_metadata.patent_id if result.patent_metadata else result.title
                    all_patents.add(patent_id)

                session.total_patents_found += len(iteration_results)

                # 检查是否应该提前终止
                if iteration.quality_score > 0.85 and iteration_num >= 2:
                    logger.info(f"搜索质量较高，提前终止迭代（第{iteration_num}轮）")
                    break

            # 最终统计
            session.unique_patents = len(all_patents)
            session.update_status(SearchStatus.COMPLETED)

            # 生成研究摘要
            if self.llm_integration:
                try:
                    await self.rate_limiters['llm'].wait_for_slot()
                    session.research_summary = await self.llm_integration.generate_research_summary(session)
                except Exception as e:
                    logger.error(f"生成研究摘要失败: {e}")

            return session

        except Exception as e:
            logger.error(f"迭代搜索失败: {e}")
            session.update_status(SearchStatus.FAILED)
            return session

    def _calculate_quality_score(self, results: list[PatentSearchResult]) -> float:
        """计算搜索质量分数"""
        if not results:
            return 0.0

        # 综合考虑相关性、覆盖度和多样性
        relevance_scores = [r.combined_score for r in results]
        avg_relevance = sum(relevance_scores) / len(relevance_scores)

        # 相关性权重
        quality_score = avg_relevance * 0.6

        # 数量权重（适中的结果数量更好）
        count_score = min(len(results) / 20.0, 1.0) * 0.2

        # 多样性权重（简化版）
        applicants = set()
        for result in results:
            if result.patent_metadata and result.patent_metadata.applicant:
                applicants.add(result.patent_metadata.applicant)
        diversity_score = min(len(applicants) / 10.0, 1.0) * 0.2

        quality_score += count_score + diversity_score

        return min(quality_score, 1.0)

    async def get_session(self, session_id: str) -> SearchSession | None:
        """获取搜索会话"""
        async with self.session_lock:
            return self.sessions.get(session_id)

    async def save_session(self, session: SearchSession) -> str:
        """保存搜索会话"""
        async with self.session_lock:
            self.sessions[session.id] = session
            return session.id

    async def get_statistics(self) -> dict[str, Any]:
        """获取搜索统计"""
        stats = {
            'total_sessions': len(self.sessions),
            'engine_config': {
                'elasticsearch_weight': self.config.engine_weights.elasticsearch_weight,
                'vector_weight': self.config.engine_weights.vector_weight,
                'external_weight': self.config.engine_weights.external_weight
            },
            'enabled_external_engines': self.config.external_engines.get_enabled_engines(),
            'llm_provider': self.config.llm_config.provider.value,
        }

        # 添加性能指标
        if self.performance_optimizer:
            stats['performance'] = self.performance_optimizer.get_metrics()

        # 添加向量搜索统计
        if self.vector_search:
            stats['vector_search'] = self.vector_search.get_statistics()

        return stats

    async def close(self):
        """关闭搜索引擎"""
        if self.performance_optimizer:
            await self.performance_optimizer.stop()

        if self.vector_search:
            await self.vector_search.close()

        if self.external_manager:
            # 外部搜索引擎无需特殊关闭
            pass

        logger.info('增强搜索引擎已关闭')
