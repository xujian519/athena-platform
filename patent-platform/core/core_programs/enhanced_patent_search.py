#!/usr/bin/env python3
"""
增强版专利检索系统
Enhanced Patent Search System

集成优化的网络客户端，解决专利数据获取问题
支持多种数据源和智能重试机制

作者: 小诺 (Athena AI助手)
创建时间: 2025-12-08
版本: 2.0.0
"""

import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# 导入优化网络客户端
from optimized_network_client import OptimizedNetworkClient

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """搜索结果数据结构"""
    title: str
    application_number: str = ''
    abstract: str = ''
    url: str = ''
    source: str = ''
    relevance_score: float = 0.0
    extraction_date: str = ''
    additional_info: dict[str, Any] = None

class EnhancedPatentSearch:
    """增强版专利检索系统"""

    def __init__(self, config: dict[str, Any] | None = None):
        """初始化专利检索系统"""
        self.config = config or self._get_default_config()
        self.network_client = OptimizedNetworkClient(self.config.get('network', {}))
        self.search_history = []
        self.cache = {}
        self.cache_enabled = self.config.get('cache_enabled', True)
        self.cache_ttl = self.config.get('cache_ttl', 3600)  # 1小时

    def _get_default_config(self) -> dict[str, Any]:
        """获取默认配置"""
        return {
            'max_results_per_source': 10,
            'max_total_results': 50,
            'cache_enabled': True,
            'cache_ttl': 3600,
            'similarity_threshold': 0.7,
            'network': {
                'request_delay': {
                    'min': 1.0,
                    'max': 3.0,
                    'base': 2.0
                }
            },
            'sources': {
                'google_patents': {
                    'enabled': True,
                    'priority': 1,
                    'weight': 0.6
                },
                'google_patents_api': {
                    'enabled': True,
                    'priority': 2,
                    'weight': 0.4
                }
            }
        }

    def search(
        self,
        query: str,
        max_results: int = 20,
        sources: list[str] | None = None,
        use_cache: bool = True
    ) -> list[SearchResult]:
        """
        执行专利搜索

        Args:
            query: 搜索关键词
            max_results: 最大返回结果数
            sources: 指定数据源，None表示使用所有可用源
            use_cache: 是否使用缓存

        Returns:
            搜索结果列表
        """
        logger.info(f"开始专利搜索: {query}")

        # 生成缓存键
        cache_key = f"{query}_{max_results}_{str(sources)}"

        # 检查缓存
        if use_cache and self.cache_enabled:
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                logger.info(f"从缓存返回结果: {len(cached_result)} 个")
                return cached_result

        # 确定使用的数据源
        enabled_sources = self._get_enabled_sources(sources)

        # 并行搜索
        results = []
        for source_name, _source_config in enabled_sources.items():
            try:
                source_results = self._search_source(
                    source_name,
                    query,
                    max_results // len(enabled_sources) + 5  # 稍微多获取一些
                )
                results.extend(source_results)
                logger.info(f"{source_name} 返回 {len(source_results)} 个结果")
            except Exception as e:
                logger.error(f"搜索源 {source_name} 失败: {e}")
                continue

        # 去重和排序
        unique_results = self._deduplicate_results(results)
        sorted_results = self._sort_results(unique_results, query)
        final_results = sorted_results[:max_results]

        # 缓存结果
        if use_cache and self.cache_enabled:
            self._save_to_cache(cache_key, final_results)

        # 记录搜索历史
        self.search_history.append({
            'query': query,
            'timestamp': time.time(),
            'result_count': len(final_results),
            'sources_used': list(enabled_sources.keys())
        })

        logger.info(f"搜索完成: {query}, 返回 {len(final_results)} 个结果")
        return final_results

    def _get_enabled_sources(self, sources: list[str] | None) -> dict[str, dict[str, Any]]:
        """获取启用的数据源"""
        all_sources = self.config.get('sources', {})

        if sources is None:
            # 返回所有启用的源，按优先级排序
            enabled = {
                name: config for name, config in all_sources.items()
                if config.get('enabled', False)
            }
            # 按优先级排序
            return dict(sorted(enabled.items(), key=lambda x: x[1].get('priority', 999)))
        else:
            # 返回指定的源
            return {
                name: all_sources.get(name, {})
                for name in sources
                if name in all_sources and all_sources[name].get('enabled', False)
            }

    def _search_source(self, source_name: str, query: str, max_results: int) -> list[SearchResult]:
        """从指定源搜索"""
        if source_name == 'google_patents':
            return self._search_google_patents(query, max_results)
        elif source_name == 'google_patents_api':
            return self._search_google_patents_api(query, max_results)
        else:
            raise ValueError(f"不支持的数据源: {source_name}")

    def _search_google_patents(self, query: str, max_results: int) -> list[SearchResult]:
        """从Google Patents网页搜索"""
        logger.info(f"Google Patents网页搜索: {query}")

        try:
            raw_results = self.network_client.search_google_patents(query, max_results)
            return [self._convert_to_search_result(r, 'google_patents') for r in raw_results]
        except Exception as e:
            logger.error(f"Google Patents网页搜索失败: {e}")
            return []

    def _search_google_patents_api(self, query: str, max_results: int) -> list[SearchResult]:
        """从Google Patents API搜索"""
        logger.info(f"Google Patents API搜索: {query}")

        try:
            raw_results = self.network_client.search_google_patents_api(query, max_results)
            return [self._convert_to_search_result(r, 'google_patents_api') for r in raw_results]
        except Exception as e:
            logger.error(f"Google Patents API搜索失败: {e}")
            return []

    def _convert_to_search_result(self, raw_data: dict[str, Any], source: str) -> SearchResult:
        """将原始数据转换为SearchResult对象"""
        return SearchResult(
            title=raw_data.get('title', ''),
            application_number=raw_data.get('application_number', ''),
            abstract=raw_data.get('abstract', ''),
            url=raw_data.get('url', ''),
            source=source,
            extraction_date=time.strftime('%Y-%m-%d %H:%M:%S'),
            additional_info={
                k: v for k, v in raw_data.items()
                if k not in ['title', 'application_number', 'abstract', 'url']
            }
        )

    def _deduplicate_results(self, results: list[SearchResult]) -> list[SearchResult]:
        """去重搜索结果"""
        unique_results = []
        seen_titles = set()
        seen_numbers = set()

        for result in results:
            # 基于标题去重
            title_key = result.title.lower().strip()
            number_key = result.application_number.lower().strip()

            if title_key in seen_titles or (number_key and number_key in seen_numbers):
                continue

            unique_results.append(result)
            seen_titles.add(title_key)
            if number_key:
                seen_numbers.add(number_key)

        return unique_results

    def _sort_results(self, results: list[SearchResult], query: str) -> list[SearchResult]:
        """对结果进行排序"""
        # 简单的相关性评分
        for result in results:
            result.relevance_score = self._calculate_relevance(result, query)

        # 按相关性评分排序
        return sorted(results, key=lambda x: x.relevance_score, reverse=True)

    def _calculate_relevance(self, result: SearchResult, query: str) -> float:
        """计算结果与查询的相关性"""
        query_terms = set(query.lower().split())
        title_terms = set(result.title.lower().split())
        abstract_terms = set(result.abstract.lower().split()) if result.abstract else set()

        # 标题匹配权重
        title_score = len(query_terms & title_terms) / len(query_terms) if query_terms else 0

        # 摘要匹配权重
        abstract_score = len(query_terms & abstract_terms) / len(query_terms) / 2 if query_terms else 0

        # 源权重
        source_weights = {
            'google_patents': 1.0,
            'google_patents_api': 1.2  # API数据通常更准确
        }
        source_weight = source_weights.get(result.source, 1.0)

        return (title_score + abstract_score) * source_weight

    def _get_from_cache(self, cache_key: str) -> list[SearchResult | None]:
        """从缓存获取结果"""
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if time.time() - cached_data['timestamp'] < self.cache_ttl:
                return cached_data['results']
            else:
                # 缓存过期
                del self.cache[cache_key]
        return None

    def _save_to_cache(self, cache_key: str, results: list[SearchResult]):
        """保存结果到缓存"""
        self.cache[cache_key] = {
            'results': results,
            'timestamp': time.time()
        }

    def get_search_statistics(self) -> dict[str, Any]:
        """获取搜索统计信息"""
        network_stats = self.network_client.get_statistics()

        return {
            'search_history_count': len(self.search_history),
            'cache_size': len(self.cache),
            'cache_enabled': self.cache_enabled,
            'recent_searches': [
                {
                    'query': h['query'],
                    'timestamp': h['timestamp'],
                    'result_count': h['result_count']
                }
                for h in self.search_history[-5:]
            ],
            'network_statistics': network_stats
        }

    def export_results(self, results: list[SearchResult], filename: str, format: str = 'json'):
        """导出搜索结果"""
        filepath = Path(filename)

        if format.lower() == 'json':
            data = [
                {
                    'title': r.title,
                    'application_number': r.application_number,
                    'abstract': r.abstract,
                    'url': r.url,
                    'source': r.source,
                    'relevance_score': r.relevance_score,
                    'extraction_date': r.extraction_date
                }
                for r in results
            ]

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        elif format.lower() == 'csv':
            import csv

            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Title', 'Application Number', 'Abstract', 'URL', 'Source', 'Score'])

                for r in results:
                    writer.writerow([
                        r.title,
                        r.application_number,
                        r.abstract,
                        r.url,
                        r.source,
                        r.relevance_score
                    ])

        logger.info(f"结果已导出到: {filepath}")

# 使用示例
if __name__ == '__main__':
    # 配置日志
    logging.basicConfig(level=logging.INFO)

    # 创建检索系统
    search_system = EnhancedPatentSearch()

    # 执行搜索
    logger.info('🔍 开始搜索专利...')
    results = search_system.search(
        query='artificial intelligence machine learning',
        max_results=10
    )

    # 显示结果
    logger.info(f"\n📊 找到 {len(results)} 个相关专利:\n")

    for i, result in enumerate(results, 1):
        logger.info(f"{'='*60}")
        logger.info(f"{i}. 【{result.source}】{result.title}")
        logger.info(f"   申请号: {result.application_number}")
        logger.info(f"   相关性: {result.relevance_score:.2f}")

        if result.abstract:
            logger.info(f"   摘要: {result.abstract[:150]}...")

        logger.info(f"   链接: {result.url}")
        logger.info(f"   提取时间: {result.extraction_date}")

    # 显示统计信息
    stats = search_system.get_search_statistics()
    logger.info(f"\n📈 搜索统计: {json.dumps(stats, ensure_ascii=False, indent=2)}")

    # 导出结果
    if results:
        search_system.export_results(results, 'patent_search_results.json')
        logger.info("\n💾 结果已保存到 patent_search_results.json")
