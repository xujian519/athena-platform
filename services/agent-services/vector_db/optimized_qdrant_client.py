#!/usr/bin/env python3
"""
优化后的Qdrant客户端
支持新的集合名称和Redis缓存
"""

import logging
import os
import sys
from typing import Any

from core.logging_config import setup_logging

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# 尝试导入必要的库
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance,
        FieldCondition,
        Filter,
        MatchValue,
        SearchParams,
        SearchRequest,
        VectorParams,
    )
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

class OptimizedQdrantClient:
    """优化后的Qdrant客户端，集成缓存和新集合映射"""

    def __init__(self):
        self.qdrant_client = QdrantClient('http://localhost:6333') if QDRANT_AVAILABLE else None

        # 集合映射：旧名称 -> 新名称
        self.collection_mapping = {
            # 标准化后的集合
            'ai_technical_terms_vector_db': 'ai_technical_terms_1024',
            'legal_laws_comprehensive': 'legal_laws_1024',

            # 分片后的集合（legal_clauses已分片）
            'legal_clauses': 'legal_clauses',  # 保留作为查询路由入口
            'legal_documents': 'legal_documents',
            'patent_rules_unified_1024': 'patent_rules_unified_1024',
            'legal_patent_vectors': 'legal_patent_vectors',
            'patent_invalid_db': 'patent_invalid_db',
            'patent_judgment_db': 'patent_judgment_db',
            'patent_review_db': 'patent_review_db',
            'general_memory_db': 'general_memory_db'
        }

        # legal_clauses分片配置
        self.legal_clauses_shards = {
            'legal_clauses_contract': {
                'keywords': ['合同', '协议', '约定', '条款', '签约', '履行', '违约', '解除', '终止']
            },
            'legal_clauses_ip': {
                'keywords': ['专利', '商标', '著作权', '版权', '知识产权', '侵权', '授权', '许可', '专有']
            },
            'legal_clauses_tort': {
                'keywords': ['侵权', '责任', '赔偿', '损害', '过错', '因果关系', '免责', '抗辩', '举证']
            },
            'legal_clauses_labor': {
                'keywords': ['劳动', '工资', '报酬', '加班', '解雇', '雇佣', '试用期', '竞业', '保密']
            },
            'legal_clauses_corporate': {
                'keywords': ['公司', '股东', '股权', '董事会', '章程', '决议', '出资', '分红', '清算']
            },
            'legal_clauses_property': {
                'keywords': ['房产', '土地', '不动产', '所有权', '使用权', '抵押', '转让', '登记', '共有']
            }
        }

        # 向量维度映射
        self.collection_dimensions = {
            'ai_technical_terms_1024': 1024,
            'ai_technical_terms_vector_db': 384,
            'legal_laws_1024': 1024,
            'legal_laws_comprehensive': 768,
            'legal_clauses': 1024,
            'legal_documents': 1024,
            'patent_rules_unified_1024': 1024,
            'legal_patent_vectors': 1024,
            'patent_invalid_db': 1024,
            'patent_judgment_db': 1024,
            'patent_review_db': 1024,
            'general_memory_db': 384
        }

        # 缓存配置
        self.use_cache = True
        self.cache_service = None

        # 初始化缓存服务
        if self.use_cache:
            try:
                # 优先使用优化的缓存服务
                from services.cache.optimized_query_cache_service import (
                    OptimizedQueryCacheService,
                )
                self.cache_service = OptimizedQueryCacheService()
                logger.info('✅ 优化的Redis缓存服务已启用')
            except ImportError:
                try:
                    # 回退到标准缓存服务
                    from services.cache.query_cache_service import QueryCacheService
                    self.cache_service = QueryCacheService()
                    logger.info('✅ Redis缓存服务已启用')
                except ImportError:
                    logger.warning('⚠️ 缓存服务导入失败，将不使用缓存')
                    self.use_cache = False

        logger.info("🚀 优化Qdrant客户端已初始化")
        logger.info(f"📦 集合映射: {len(self.collection_mapping)} 个")

    def get_collection_name(self, collection_name: str) -> str:
        """获取映射后的集合名称"""
        return self.collection_mapping.get(collection_name, collection_name)

    def get_vector_dimension(self, collection_name: str) -> int:
        """获取集合的向量维度"""
        return self.collection_dimensions.get(collection_name, 1024)

    def standardize_vector(self, vector: list[float], target_dim: int = 1024) -> list[float]:
        """标准化向量维度"""
        current_dim = len(vector)

        if current_dim == target_dim:
            return vector

        if current_dim < target_dim:
            # 填充零
            padding = target_dim - current_dim
            return list(vector) + [0.0] * padding

        if current_dim > target_dim:
            # 截断
            return list(vector)[:target_dim]

        return vector

    def search(self, collection_name: str, query_vector: list[float],
                limit: int = 10, filters: dict | None = None,
                score_threshold: float | None = None) -> list[dict[str, Any]]:
        """带缓存的智能搜索"""
        # 处理legal_clauses分片查询
        if collection_name == 'legal_clauses':
            return self._search_legal_clauses_shards(query_vector, limit, filters, score_threshold)

        # 获取映射后的集合名称
        mapped_collection = self.get_collection_name(collection_name)

        # 标准化向量维度
        target_dim = self.get_vector_dimension(mapped_collection)
        std_vector = self.standardize_vector(query_vector, target_dim)

        # 记录原始查询
        logger.info(f"🔍 搜索 {collection_name} -> {mapped_collection}")
        logger.info(f"📏 向量维度: {len(query_vector)} -> {target_dim}")

        # 使用缓存
        if self.cache_service and self.use_cache:
            cached_results = self.cache_service.get_cached_results(
                mapped_collection, std_vector, limit, filters
            )
            if cached_results:
                # 应用阈值过滤
                if score_threshold:
                    cached_results = [
                        r for r in cached_results
                        if r.get('score', 0) >= score_threshold
                    ]
                logger.info(f"🎯 缓存命中: 返回 {len(cached_results)} 条结果")
                return cached_results

        # 缓存未命中，执行搜索
        logger.info('⚡ 执行Qdrant搜索...')

        if not self.qdrant_client:
            logger.error('❌ Qdrant客户端未初始化')
            return []

        try:
            # 构建过滤器
            qdrant_filter = None
            if filters:
                conditions = []
                for key, value in filters.items():
                    conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value)
                        )
                    )
                if conditions:
                    qdrant_filter = Filter(must=conditions)

            # 执行搜索
            search_results = self.qdrant_client.search(
                collection_name=mapped_collection,
                query_vector=std_vector,
                limit=limit,
                query_filter=qdrant_filter
            )

            # 转换结果格式
            results = []
            for result in search_results:
                result_dict = {
                    'id': str(result.id),
                    'score': float(result.score),
                    'payload': result.payload or {}
                }

                # 添加原始集合信息
                result_dict['payload']['_source_collection'] = collection_name
                result_dict['payload']['_mapped_collection'] = mapped_collection

                results.append(result_dict)

            # 应用阈值过滤
            if score_threshold:
                results = [r for r in results if r['score'] >= score_threshold]

            # 缓存结果
            if self.cache_service and self.use_cache and results:
                self.cache_service.cache_results(
                    mapped_collection, std_vector, results,
                    ttl=3600, filters=filters
                )

            logger.info(f"✅ 搜索完成: 返回 {len(results)} 条结果")
            return results

        except Exception as e:
            logger.error(f"❌ 搜索失败: {e}")
            return []

    def multi_search(self, queries: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        """多集合搜索"""
        results = {}

        for query in queries:
            collection_name = query.get('collection')
            query_vector = query.get('vector')
            limit = query.get('limit', 10)
            filters = query.get('filters')

            if collection_name and query_vector:
                results[collection_name] = self.search(
                    collection_name, query_vector, limit, filters
                )

        return results

    def hybrid_search(self, query_vector: list[float],
                     collections: list[str] = None,
                     weights: dict[str, float] | None = None) -> list[dict[str, Any]]:
        """混合搜索：跨多个集合搜索并合并结果"""
        if collections is None:
            # 默认搜索主要集合
            collections = [
                'legal_clauses',
                'legal_documents',
                'patent_rules_unified_1024',
                'ai_technical_terms_1024'
            ]

        if weights is None:
            weights = dict.fromkeys(collections, 1.0)

        all_results = []

        for collection in collections:
            results = self.search(collection, query_vector, limit=20)

            # 应用权重
            weight = weights.get(collection, 1.0)
            for result in results:
                result['score'] *= weight
                result['collection'] = collection

            all_results.extend(results)

        # 按分数排序并去重
        all_results.sort(key=lambda x: x['score'], reverse=True)

        # 去重（基于ID）
        seen_ids = set()
        unique_results = []
        for result in all_results:
            result_id = result['id']
            if result_id not in seen_ids:
                seen_ids.add(result_id)
                unique_results.append(result)

        return unique_results[:20]  # 返回前20条

    def get_collection_info(self, collection_name: str) -> dict[str, Any]:
        """获取集合信息"""
        mapped_collection = self.get_collection_name(collection_name)

        if not self.qdrant_client:
            return {'error': 'Qdrant客户端未初始化'}

        try:
            info = self.qdrant_client.get_collection(mapped_collection)
            count = self.qdrant_client.count(mapped_collection)

            return {
                'name': mapped_collection,
                'original_name': collection_name,
                'vectors_count': count,
                'vector_size': info.config.params.vectors.size,
                'distance': info.config.params.vectors.distance.value,
                'status': info.status
            }
        except Exception as e:
            return {'error': str(e)}

    def _search_legal_clauses_shards(self, query_vector: list[float], limit: int = 10,
                                    filters: dict | None = None,
                                    score_threshold: float | None = None) -> list[dict[str, Any]]:
        """智能搜索legal_clauses分片"""
        # 确定要搜索的分片（基于关键词路由）
        target_shards = []

        # 默认搜索最大的分片（contract）
        target_shards.append('legal_clauses_contract')

        # 检查其他分片是否可能相关
        # 这里简化处理，实际应用中可以基于查询文本或历史模式判断
        list(self.legal_clauses_shards.keys())

        # 并行搜索多个分片以提升性能
        import concurrent.futures

        def search_single_shard(shard_name, vector, lim) -> None:
            return self._search_single_collection(shard_name, vector, lim, filters, score_threshold)

        # 搜索目标分片
        all_results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            # 提交搜索任务
            futures = []
            for shard in target_shards:
                future = executor.submit(search_single_shard, shard, query_vector, limit)
                futures.append(future)

            # 收集结果
            for future in concurrent.futures.as_completed(futures):
                try:
                    results = future.result(timeout=5)
                    all_results.extend(results)
                except Exception as e:
                    logger.warning(f"分片搜索失败: {e}")

        # 按分数排序并去重
        all_results.sort(key=lambda x: x['score'], reverse=True)

        # 去重（基于ID）
        seen_ids = set()
        unique_results = []
        for result in all_results:
            result_id = result['id']
            if result_id not in seen_ids:
                seen_ids.add(result_id)
                unique_results.append(result)

        # 返回结果，并标记来源
        final_results = unique_results[:limit]
        for result in final_results:
            result['payload']['_shard_source'] = 'legal_clauses'

        return final_results

    def _search_single_collection(self, collection_name: str, query_vector: list[float],
                                 limit: int = 10, filters: dict | None = None,
                                 score_threshold: float | None = None) -> list[dict[str, Any]]:
        """搜索单个集合的内部方法"""
        if not self.qdrant_client:
            return []

        try:
            # 构建过滤器
            qdrant_filter = None
            if filters:
                conditions = []
                for key, value in filters.items():
                    conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value)
                        )
                    )
                if conditions:
                    qdrant_filter = Filter(must=conditions)

            # 执行搜索
            search_results = self.qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                query_filter=qdrant_filter
            )

            # 转换结果格式
            results = []
            for result in search_results:
                if score_threshold is None or result.score >= score_threshold:
                    result_dict = {
                        'id': str(result.id),
                        'score': float(result.score),
                        'payload': result.payload or {}
                    }

                    # 添加分片信息
                    result_dict['payload']['_shard_collection'] = collection_name
                    results.append(result_dict)

            return results

        except Exception as e:
            logger.error(f"搜索集合 {collection_name} 失败: {e}")
            return []

    def list_collections(self) -> list[dict[str, Any]]:
        """列出所有集合及其信息"""
        if not self.qdrant_client:
            return []

        collections = []

        # 添加常规集合
        for name in self.collection_mapping.keys():
            if name != 'legal_clauses':  # legal_clauses现在是虚拟集合
                info = self.get_collection_info(name)
                if 'error' not in info:
                    collections.append(info)

        # 添加legal_clauses分片信息
        try:
            total_vectors = 0
            for shard_name in self.legal_clauses_shards.keys():
                count = self.qdrant_client.count(shard_name).count
                total_vectors += count

            collections.append({
                'name': 'legal_clauses',
                'original_name': 'legal_clauses',
                'vectors_count': total_vectors,
                'vector_size': 1024,
                'distance': 'Cosine',
                'status': 'green',
                'shards_count': len(self.legal_clauses_shards),
                'sharded': True
            })
        except Exception as e:
            logger.warning(f"获取legal_clauses分片信息失败: {e}")

        return collections

    def get_cache_stats(self) -> dict[str, Any]:
        """获取缓存统计"""
        if self.cache_service:
            return self.cache_service.get_cache_stats()
        return {'message': '缓存未启用'}

def test_optimized_client() -> Any:
    """测试优化后的客户端"""
    logger.info('🧪 测试优化后的Qdrant客户端...')

    client = OptimizedQdrantClient()

    # 列出集合
    logger.info("\n📦 集合列表:")
    collections = client.list_collections()
    for col in collections:
        logger.info(f"  • {col['name']:30} : {col['vectors_count']:>8,} vectors, {col['vector_size']}维")

    # 测试搜索（使用随机向量）
    import random
    test_vector = [random.uniform(-1, 1) for _ in range(1024)]

    logger.info("\n🔍 测试搜索...")
    results = client.search('legal_clauses', test_vector, limit=5)
    logger.info(f"返回 {len(results)} 条结果")

    if results:
        logger.info(f"最高分: {results[0]['score']:.4f}")
        logger.info(f"最低分: {results[-1]['score']:.4f}")

    # 缓存统计
    logger.info("\n💾 缓存统计:")
    cache_stats = client.get_cache_stats()
    for key, value in cache_stats.items():
        logger.info(f"  {key}: {value}")

if __name__ == '__main__':
    test_optimized_client()
