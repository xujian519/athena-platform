#!/usr/bin/env python3
"""
增强的专利检索器
Enhanced Patent Retriever

集成真实专利数据的混合检索系统
"""

import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from neo4j import GraphDatabase
from qdrant_client import QdrantClient
from real_patent_connector import RealPatentConnector
from sentence_transformers import SentenceTransformer

# 配置日志
logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """搜索结果"""
    patent_id: str
    title: str
    abstract: str
    score: float
    source: str  # 'vector', 'graph', 'keyword', 'bm25'
    metadata: dict[str, Any]
    explanation: str | None = None

@dataclass
class RetrievalStats:
    """检索统计"""
    total_time: float
    vector_time: float
    graph_time: float
    keyword_time: float
    fusion_time: float
    results_count: int

class EnhancedPatentRetriever:
    """增强的专利检索器"""

    def __init__(
        self,
        embedding_model: str = '/Users/xujian/Athena工作平台/models/BAAI/bge-large-zh-v1.5',
        enable_cache: bool = True
    ):
        """初始化检索器

        Args:
            embedding_model: 向量化模型路径
            enable_cache: 是否启用缓存
        """
        # 连接器
        self.patent_connector = RealPatentConnector()
        self.qdrant_client = QdrantClient(host='localhost', port=6333)
        self.neo4j_driver = GraphDatabase.driver(
            'bolt://localhost:7687',
            auth=('neo4j', 'password')
        )

        # 向量化模型
        model_path = embedding_model if embedding_model.startswith('/') else '/Users/xujian/Athena工作平台/models/bge-large-zh-v1.5'
        self.embedding_model = SentenceTransformer(
            model_path,
            cache_folder='/Users/xujian/Athena工作平台/models'
        )
        self.embedding_dim = 1024

        # 缓存
        self.enable_cache = enable_cache
        self.query_cache = {}

        # 统计
        self.stats = {
            'total_queries': 0,
            'total_results': 0,
            'cache_hits': 0
        }

    def search(
        self,
        query: str,
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
        search_modes: list[str] | None = None,
        weights: dict[str, float] | None = None
    ) -> tuple[list[SearchResult], RetrievalStats]:
        """执行增强专利检索

        Args:
            query: 查询文本
            top_k: 返回结果数量
            filters: 过滤条件
            search_modes: 搜索模式 ['vector', 'graph', 'keyword', 'bm25']
            weights: 各模式权重

        Returns:
            检索结果和统计信息
        """
        start_time = datetime.now()

        # 检查缓存
        cache_key = f"{query}_{top_k}_{str(filters)}"
        if self.enable_cache and cache_key in self.query_cache:
            self.stats['cache_hits'] += 1
            cached_results, cached_stats = self.query_cache[cache_key]
            logger.info(f"缓存命中: {cache_key}")
            return cached_results, cached_stats

        # 默认搜索模式
        if not search_modes:
            search_modes = ['vector', 'graph', 'keyword', 'bm25']

        # 默认权重
        if not weights:
            weights = {
                'vector': 0.4,
                'graph': 0.3,
                'keyword': 0.2,
                'bm25': 0.1
            }

        logger.info(f"执行检索: {query}")
        logger.info(f"搜索模式: {search_modes}, 权重: {weights}")

        # 并行执行不同搜索
        all_results = {}
        times = {}

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {}

            # 向量搜索
            if 'vector' in search_modes:
                futures['vector'] = executor.submit(self._vector_search, query, top_k * 2, filters)

            # 图搜索
            if 'graph' in search_modes:
                futures['graph'] = executor.submit(self._graph_search, query, top_k * 2, filters)

            # 关键词搜索
            if 'keyword' in search_modes:
                futures['keyword'] = executor.submit(self._keyword_search, query, top_k * 2, filters)

            # BM25搜索
            if 'bm25' in search_modes:
                futures['bm25'] = executor.submit(self._bm25_search, query, top_k * 2, filters)

            # 收集结果
            for mode, future in futures.items():
                try:
                    mode_results, mode_time = future.result()
                    all_results[mode] = mode_results
                    times[mode] = mode_time
                except Exception as e:
                    logger.error(f"{mode}搜索失败: {e}")
                    all_results[mode] = []
                    times[mode] = 0

        # 融合结果
        fusion_start = datetime.now()
        merged_results = self._merge_results(all_results, weights, top_k)
        fusion_time = (datetime.now() - fusion_start).total_seconds()

        # 生成统计信息
        total_time = (datetime.now() - start_time).total_seconds()
        stats = RetrievalStats(
            total_time=total_time,
            vector_time=times.get('vector', 0),
            graph_time=times.get('graph', 0),
            keyword_time=times.get('keyword', 0),
            bm25_time=times.get('bm25', 0),
            fusion_time=fusion_time,
            results_count=len(merged_results)
        )

        # 更新统计
        self.stats['total_queries'] += 1
        self.stats['total_results'] += len(merged_results)

        # 缓存结果
        if self.enable_cache:
            self.query_cache[cache_key] = (merged_results, stats)
            # 限制缓存大小
            if len(self.query_cache) > 1000:
                self.query_cache.clear()

        return merged_results, stats

    def _vector_search(
        self,
        query: str,
        top_k: int,
        filters: dict[str, Any] | None = None
    ) -> tuple[list[SearchResult], float]:
        """执行向量搜索"""
        start_time = datetime.now()

        try:
            # 编码查询
            query_vector = self.embedding_model.encode(query, normalize_embeddings=True)

            # 构建过滤器
            qdrant_filter = None
            if filters:
                from qdrant_client.models import FieldCondition, Filter, MatchValue
                conditions = []

                if 'patent_type' in filters:
                    conditions.append(
                        FieldCondition(key='patent_type', match=MatchValue(value=filters['patent_type']))
                    )
                if 'year_from' in filters:
                    conditions.append(
                        FieldCondition(key='publication_date', match=MatchValue(value=int(filters['year_from'])))
                    )
                if 'ipc_codes' in filters:
                    conditions.append(
                        FieldCondition(key='ipc_codes', match=MatchValue(value=filters['ipc_codes']))
                    )

                if conditions:
                    qdrant_filter = Filter(must=conditions)

            # 搜索Qdrant
            search_result = self.qdrant_client.search(
                collection_name='real_patents',
                query_vector=query_vector,
                query_filter=qdrant_filter,
                limit=top_k,
                with_payload=True,
                with_score=True
            )

            # 转换结果
            results = []
            for hit in search_result:
                result = SearchResult(
                    patent_id=hit.payload.get('patent_id', ''),
                    title=hit.payload.get('title', ''),
                    abstract=hit.payload.get('abstract', ''),
                    score=hit.score,
                    source='vector',
                    metadata=hit.payload,
                    explanation=f"语义相似度: {hit.score:.3f}"
                )
                results.append(result)

            search_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"向量搜索完成: {len(results)} 个结果，耗时 {search_time:.3f}s")

            return results, search_time

        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            return [], (datetime.now() - start_time).total_seconds()

    def _graph_search(
        self,
        query: str,
        top_k: int,
        filters: dict[str, Any] | None = None
    ) -> tuple[list[SearchResult], float]:
        """执行图搜索"""
        start_time = datetime.now()

        try:
            results = []
            with self.neo4j_driver.session() as session:
                # 基础查询
                cypher_query = """
                    MATCH (p:Patent)
                    WHERE p.title CONTAINS $query OR p.abstract CONTAINS $query
                """

                params = {'query': query, 'limit': top_k}

                # 添加过滤条件
                if filters:
                    if 'patent_type' in filters:
                        cypher_query += ' AND p.patent_type = $patent_type'
                        params['patent_type'] = filters['patent_type']

                    if 'ipc_codes' in filters:
                        for ipc in filters['ipc_codes']:
                            cypher_query += f"""
                                AND EXISTS {{
                                    MATCH (p)-[:BELONGS_TO]->(i:IPC)
                                    WHERE i.ipc_code STARTS WITH '{ipc}'
                                }}
                            """

                cypher_query += """
                    RETURN p, score(1) as score
                    ORDER BY score DESC
                    LIMIT $limit
                """

                cursor = session.run(cypher_query, params)

                for record in cursor:
                    patent = record['p']
                    result = SearchResult(
                        patent_id=patent['patent_id'],
                        title=patent.get('title', ''),
                        abstract=patent.get('abstract', ''),
                        score=record['score'],
                        source='graph',
                        metadata=dict(patent),
                        explanation='知识图谱匹配'
                    )
                    results.append(result)

            search_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"图搜索完成: {len(results)} 个结果，耗时 {search_time:.3f}s")

            return results, search_time

        except Exception as e:
            logger.error(f"图搜索失败: {e}")
            return [], (datetime.now() - start_time).total_seconds()

    def _keyword_search(
        self,
        query: str,
        top_k: int,
        filters: dict[str, Any] | None = None
    ) -> tuple[list[SearchResult], float]:
        """执行关键词搜索"""
        start_time = datetime.now()

        try:
            results = []
            with self.patent_connector.get_cursor() as cursor:
                # 构建SQL查询
                sql_query = """
                    SELECT DISTINCT patent_id, title, abstract, patent_type,
                           publication_date, application_number
                    FROM patents
                    WHERE (title ILIKE %s OR abstract ILIKE %s)
                """

                params = [f'%{query}%', f'%{query}%']

                # 添加过滤
                if filters:
                    if 'patent_type' in filters:
                        sql_query += ' AND patent_type = %s'
                        params.append(filters['patent_type'])

                sql_query += ' ORDER BY publication_date DESC LIMIT %s'
                params.append(top_k)

                cursor.execute(sql_query, params)
                rows = cursor.fetchall()

                for row in rows:
                    result = SearchResult(
                        patent_id=row[0],
                        title=row[1],
                        abstract=row[2] or '',
                        score=1.0,  # 关键词匹配固定分数
                        source='keyword',
                        metadata={
                            'patent_id': row[0],
                            'title': row[1],
                            'abstract': row[2],
                            'patent_type': row[3],
                            'publication_date': row[4],
                            'application_number': row[5]
                        },
                        explanation='关键词完全匹配'
                    )
                    results.append(result)

            search_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"关键词搜索完成: {len(results)} 个结果，耗时 {search_time:.3f}s")

            return results, search_time

        except Exception as e:
            logger.error(f"关键词搜索失败: {e}")
            return [], (datetime.now() - start_time).total_seconds()

    def _bm25_search(
        self,
        query: str,
        top_k: int,
        filters: dict[str, Any] | None = None
    ) -> tuple[list[SearchResult], float]:
        """执行BM25搜索（简化版）"""
        # 这里简化处理，实际应该使用PostgreSQL的全文搜索
        # 直接返回关键词搜索的结果，但降低分数
        results, time = self._keyword_search(query, top_k, filters)

        # 调整分数
        for result in results:
            result.score *= 0.8
            result.source = 'bm25'
            result.explanation = 'BM25文本相关性'

        return results, time

    def _merge_results(
        self,
        all_results: dict[str, list[SearchResult]],
        weights: dict[str, float],
        top_k: int
    ) -> list[SearchResult]:
        """融合不同搜索的结果"""
        # 收集所有结果
        merged = {}

        for mode, results in all_results.items():
            weight = weights.get(mode, 0)
            if weight <= 0:
                continue

            for result in results:
                patent_id = result.patent_id

                if patent_id not in merged:
                    merged[patent_id] = {
                        'patent_id': patent_id,
                        'title': result.title,
                        'abstract': result.abstract,
                        'metadata': result.metadata,
                        'sources': [],
                        'total_score': 0,
                        'explanations': []
                    }

                # 更新分数
                merged[patent_id]['total_score'] += result.score * weight
                merged[patent_id]['sources'].append((mode, result.score))
                merged[patent_id]['explanations'].append(result.explanation)

        # 排序并创建最终结果
        final_results = []
        for patent_id, data in sorted(merged.items(), key=lambda x: x[1]['total_score'], reverse=True):
            # 生成综合解释
            explanation = f"综合评分: {data['total_score']:.3f}"
            if data['explanations']:
                explanation += f" | {', '.join(filter(None, data['explanations'][:2]))}"

            result = SearchResult(
                patent_id=patent_id,
                title=data['title'],
                abstract=data['abstract'],
                score=data['total_score'],
                source='hybrid',
                metadata=data['metadata'],
                explanation=explanation
            )
            final_results.append(result)

            if len(final_results) >= top_k:
                break

        return final_results

    def get_patent_details(self, patent_id: str) -> dict[str, Any | None]:
        """获取专利详细信息"""
        try:
            # 先从数据库获取
            patent = self.patent_connector.load_patent_with_details(patent_id)
            if patent:
                return patent

            # 再从Neo4j获取
            with self.neo4j_driver.session() as session:
                cursor = session.run("""
                    MATCH (p:Patent {patent_id: $patent_id})
                    OPTIONAL MATCH (p)-[:BELONGS_TO]->(i:IPC)
                    OPTIONAL MATCH (a:Applicant)-[:APPLIES_FOR]->(p)
                    RETURN p, collect(DISTINCT i.ipc_code) as ipc_codes,
                           collect(DISTINCT a.applicant_name) as applicants
                """, {'patent_id': patent_id})

                record = cursor.single()
                if record:
                    patent_data = dict(record['p'])
                    patent_data['ipc_codes'] = record['ipc_codes']
                    patent_data['applicants'] = record['applicants']
                    return patent_data

        except Exception as e:
            logger.error(f"获取专利详情失败 {patent_id}: {e}")

        return None

    def get_search_statistics(self) -> dict[str, Any]:
        """获取搜索统计信息"""
        return {
            'total_queries': self.stats['total_queries'],
            'total_results': self.stats['total_results'],
            'cache_hits': self.stats['cache_hits'],
            'cache_hit_rate': self.stats['cache_hits'] / max(1, self.stats['total_queries']),
            'avg_results_per_query': self.stats['total_results'] / max(1, self.stats['total_queries'])
        }

    def clear_cache(self):
        """清空缓存"""
        self.query_cache.clear()
        logger.info('缓存已清空')

    def cleanup(self):
        """清理资源"""
        if self.patent_connector:
            self.patent_connector.close()
        if self.neo4j_driver:
            self.neo4j_driver.close()
        logger.info('检索器资源清理完成')

# 测试函数
def test_enhanced_retriever():
    """测试增强检索器"""
    logger.info('=== 测试增强专利检索器 ===')

    retriever = EnhancedPatentRetriever()

    test_queries = [
        '电池管理系统',
        '蓝牙追踪器',
        '新能源技术',
        '智能设备'
    ]

    try:
        for query in test_queries:
            logger.info(f"\n查询: {query}")
            logger.info(str('-' * 50))

            results, stats = retriever.search(
                query=query,
                top_k=5,
                filters={'patent_type': 'invention'},
                search_modes=['vector', 'graph', 'keyword'],
                weights={'vector': 0.4, 'graph': 0.3, 'keyword': 0.3}
            )

            logger.info("\n检索统计:")
            logger.info(f"  总耗时: {stats.total_time:.3f}s")
            logger.info(f"  向量搜索: {stats.vector_time:.3f}s")
            logger.info(f"  图搜索: {stats.graph_time:.3f}s")
            logger.info(f"  关键词搜索: {stats.keyword_time:.3f}s")
            logger.info(f"  结果融合: {stats.fusion_time:.3f}s")
            logger.info(f"  结果数量: {stats.results_count}")

            logger.info("\nTop 5 结果:")
            for i, result in enumerate(results[:5], 1):
                logger.info(f"\n{i}. 【专利ID】{result.patent_id}")
                logger.info(f"   标题: {result.title}")
                logger.info(f"   分数: {result.score:.3f}")
                logger.info(f"   摘要: {result.abstract[:100]}...")
                logger.info(f"   说明: {result.explanation}")

        # 显示总体统计
        logger.info("\n总体统计:")
        stats = retriever.get_search_statistics()
        for key, value in stats.items():
            logger.info(f"  {key}: {value}")

    except Exception as e:
        logger.info(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

    finally:
        retriever.cleanup()

if __name__ == '__main__':
    test_enhanced_retriever()
