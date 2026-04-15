#!/usr/bin/env python3
"""
Athena统一智能搜索API
Unified Intelligent Search API

集成向量搜索、知识图谱搜索和外部搜索引擎
提供智能化的语义搜索和知识发现能力
"""

# Numpy兼容性导入
import asyncio
import logging
import os

# 添加项目路径
import sys
from datetime import datetime
from enum import Enum
from typing import Any

import aiohttp
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from config.numpy_compatibility import random

# 导入统一认证模块

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title='Athena统一智能搜索API',
    description='集成向量搜索、知识图谱和外部搜索引擎的统一智能接口',
    version='1.0.0',
    docs_url='/docs',
    redoc_url='/redoc'
)

# CORS配置

# 搜索类型枚举
class SearchType(Enum):
    SEMANTIC = 'semantic'           # 语义搜索（向量）
    KNOWLEDGE_GRAPH = 'knowledge'   # 知识图谱搜索
    EXTERNAL = 'external'           # 外部搜索引擎
    HYBRID = 'hybrid'               # 混合搜索
    COMPREHENSIVE = 'comprehensive' # 全面搜索

class QueryIntent(Enum):
    FACT_SEARCH = 'fact_search'           # 事实查询
    SIMILARITY_SEARCH = 'similarity'     # 相似性搜索
    RELATIONSHIP_SEARCH = 'relationship' # 关系查询
    DISCOVERY_SEARCH = 'discovery'       # 发现式搜索
    ANALYTIC_SEARCH = 'analytic'         # 分析性搜索

# 数据模型
class SearchRequest(BaseModel):
    """搜索请求模型"""
    query: str
    search_type: SearchType | None = SearchType.HYBRID
    intent: QueryIntent | None = QueryIntent.FACT_SEARCH
    context: dict[str, Any] = Field(default_factory=dict)
    filters: dict[str, Any] = Field(default_factory=dict)
    limit: int | None = 20
    include_reasoning: bool | None = True

class SearchResult(BaseModel):
    """搜索结果模型"""
    id: str
    title: str
    content: str
    source: str
    source_type: str  # vector, knowledge_graph, external
    score: float
    relevance: float
    metadata: dict[str, Any] = Field(default_factory=dict)
    reasoning: str | None = None

class SearchResponse(BaseModel):
    """搜索响应模型"""
    success: bool
    query: str
    search_type: str
    intent: str
    total_results: int
    processing_time: float
    results: list[SearchResult]
    aggregation: dict[str, Any] = Field(default_factory=dict)
    reasoning: str | None = None
    suggestions: list[str] = Field(default_factory=list)

class UnifiedSearchEngine:
    """统一搜索引擎"""

    def __init__(self):
        self.vector_client = None
        self.kg_client = None
        self.external_client = None
        self.search_cache = {}
        self.initialize_engines()

    async def initialize_engines(self):
        """初始化各个搜索引擎"""
        try:
            # 初始化向量搜索客户端
            await self.init_vector_search()

            # 初始化知识图谱客户端
            await self.init_knowledge_graph()

            # 初始化外部搜索引擎客户端
            await self.init_external_search()

            logger.info('统一搜索引擎初始化完成')

        except Exception as e:
            logger.error(f"搜索引擎初始化失败: {e}")

    async def init_vector_search(self):
        """初始化向量搜索"""
        try:
            from qdrant_client import QdrantClient
            self.vector_client = QdrantClient(host='localhost', port=6333)

            # 测试连接
            collections = self.vector_client.get_collections()
            logger.info(f"向量搜索初始化成功，发现 {len(collections.collections)} 个集合")

        except Exception as e:
            logger.warning(f"向量搜索初始化失败: {e}")

    async def init_knowledge_graph(self):
        """初始化知识图谱"""
        try:
            async with aiohttp.ClientSession() as session:
                # 测试知识图谱API
                async with session.get('http://localhost:9030/health', timeout=5) as response:
                    if response.status == 200:
                        self.kg_client = session
                        logger.info('知识图谱API连接成功')
                    else:
                        logger.warning(f"知识图谱API连接失败: HTTP {response.status}")
        except Exception as e:
            logger.warning(f"知识图谱初始化失败: {e}")

    async def init_external_search(self):
        """初始化外部搜索引擎"""
        try:
            # 测试外部搜索引擎API
            async with aiohttp.ClientSession() as session:
                async with session.get('http://localhost:8081/health', timeout=5) as response:
                    if response.status == 200:
                        self.external_client = session
                        logger.info('外部搜索引擎API连接成功')
                    else:
                        logger.warning(f"外部搜索引擎API连接失败: HTTP {response.status}")
        except Exception as e:
            logger.warning(f"外部搜索引擎初始化失败: {e}")

    async def search(self, request: SearchRequest) -> SearchResponse:
        """执行搜索"""
        start_time = datetime.now()

        try:
            # 根据搜索类型执行不同的搜索策略
            if request.search_type == SearchType.SEMANTIC:
                results = await self.semantic_search(request)
            elif request.search_type == SearchType.KNOWLEDGE_GRAPH:
                results = await self.knowledge_graph_search(request)
            elif request.search_type == SearchType.EXTERNAL:
                results = await self.external_search(request)
            elif request.search_type == SearchType.HYBRID:
                results = await self.hybrid_search(request)
            elif request.search_type == SearchType.COMPREHENSIVE:
                results = await self.comprehensive_search(request)
            else:
                results = []

            # 处理和排序结果
            processed_results = await self.process_results(results, request)

            # 生成推理和建议
            reasoning = None
            suggestions = []
            if request.include_reasoning:
                reasoning = await self.generate_reasoning(request, processed_results)
                suggestions = await self.generate_suggestions(request, processed_results)

            processing_time = (datetime.now() - start_time).total_seconds()

            return SearchResponse(
                success=True,
                query=request.query,
                search_type=request.search_type.value,
                intent=request.intent.value,
                total_results=len(processed_results),
                processing_time=processing_time,
                results=processed_results,
                reasoning=reasoning,
                suggestions=suggestions
            )

        except Exception as e:
            logger.error(f"搜索执行失败: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()

            return SearchResponse(
                success=False,
                query=request.query,
                search_type=request.search_type.value,
                intent=request.intent.value,
                total_results=0,
                processing_time=processing_time,
                results=[],
                reasoning=f"搜索失败: {str(e)}"
            )

    async def semantic_search(self, request: SearchRequest) -> list[SearchResult]:
        """语义搜索（向量搜索）"""
        try:
            if not self.vector_client:
                return []

            # 这里需要实际的向量化逻辑
            # 简化实现：使用随机向量
            query_vector = random(128).astype(float).tolist()

            # 搜索相似向量
            search_results = self.vector_client.search(
                collection_name='test_collection',
                query_vector=query_vector,
                limit=request.limit,
                with_payload=True
            )

            results = []
            for hit in search_results:
                results.append(SearchResult(
                    id=str(hit.id),
                    title=hit.payload.get('text', ''),
                    content=hit.payload.get('text', ''),
                    source='vector_database',
                    source_type='vector',
                    score=hit.score,
                    relevance=hit.score,
                    metadata={
                        'vector_id': hit.id,
                        'collection': 'test_collection'
                    }
                ))

            return results

        except Exception as e:
            logger.error(f"语义搜索失败: {e}")
            return []

    async def knowledge_graph_search(self, request: SearchRequest) -> list[SearchResult]:
        """知识图谱搜索"""
        try:
            if not self.kg_client:
                return []

            # 构建图谱搜索查询
            search_data = {
                'node_type': None,
                'properties': {'title': request.query},
                'limit': request.limit
            }

            async with self.kg_client.post(
                "http://localhost:9030/graphs/sqlite_main/search",
                json=search_data,
                timeout=10
            ) as response:
                if response.status == 200:
                    data = await response.json()

                    results = []
                    for item in data.get('results', []):
                        results.append(SearchResult(
                            id=item.get('id', ''),
                            title=item.get('title', ''),
                            content=item.get('description', ''),
                            source='knowledge_graph',
                            source_type='knowledge_graph',
                            score=item.get('properties', {}).get('score', 0.5),
                            relevance=item.get('properties', {}).get('score', 0.5),
                            metadata={
                                'graph_id': 'sqlite_main',
                                'category': item.get('properties', {}).get('category')
                            }
                        ))

                    return results
                else:
                    logger.warning(f"知识图谱搜索失败: HTTP {response.status}")
                    return []

        except Exception as e:
            logger.error(f"知识图谱搜索失败: {e}")
            return []

    async def external_search(self, request: SearchRequest) -> list[SearchResult]:
        """外部搜索引擎"""
        try:
            if not self.external_client:
                return []

            search_data = {
                'query': request.query,
                'max_results': request.limit
            }

            async with self.external_client.post(
                'http://localhost:8081/search',
                json=search_data,
                timeout=30
            ) as response:
                if response.status == 200:
                    data = await response.json()

                    results = []
                    for item in data.get('results', []):
                        results.append(SearchResult(
                            id=item.get('url', ''),
                            title=item.get('title', ''),
                            content=item.get('content', ''),
                            source='external_search',
                            source_type='external',
                            score=0.8,  # 外部搜索结果的基础分数
                            relevance=0.8,
                            metadata={
                                'engine': item.get('source_engine', ''),
                                'url': item.get('url', '')
                            }
                        ))

                    return results
                else:
                    logger.warning(f"外部搜索失败: HTTP {response.status}")
                    return []

        except Exception as e:
            logger.error(f"外部搜索失败: {e}")
            return []

    async def hybrid_search(self, request: SearchRequest) -> list[SearchResult]:
        """混合搜索"""
        try:
            # 并行执行多种搜索
            tasks = [
                self.semantic_search(request),
                self.knowledge_graph_search(request),
                self.external_search(request)
            ]

            results_lists = await asyncio.gather(*tasks, return_exceptions=True)

            # 合并结果
            all_results = []
            for results in results_lists:
                if isinstance(results, list):
                    all_results.extend(results)

            # 按分数排序
            all_results.sort(key=lambda x: x.relevance, reverse=True)

            # 去重和限制数量
            seen_ids = set()
            unique_results = []
            for result in all_results:
                if result.id not in seen_ids:
                    seen_ids.add(result.id)
                    unique_results.append(result)
                    if len(unique_results) >= request.limit:
                        break

            return unique_results

        except Exception as e:
            logger.error(f"混合搜索失败: {e}")
            return []

    async def comprehensive_search(self, request: SearchRequest) -> list[SearchResult]:
        """全面搜索"""
        try:
            # 执行混合搜索
            hybrid_results = await self.hybrid_search(request)

            # 扩展搜索：包含相关概念
            expanded_query = await self.expand_query(request.query)
            if expanded_query != request.query:
                expanded_request = SearchRequest(
                    query=expanded_query,
                    search_type=request.search_type,
                    intent=request.intent,
                    limit=request.limit // 2
                )
                expanded_results = await self.hybrid_search(expanded_request)

                # 合并和重排序
                all_results = hybrid_results + expanded_results
                all_results.sort(key=lambda x: x.relevance, reverse=True)

                # 去重
                seen_ids = set()
                final_results = []
                for result in all_results:
                    if result.id not in seen_ids:
                        seen_ids.add(result.id)
                        final_results.append(result)
                        if len(final_results) >= request.limit:
                            break

                return final_results

            return hybrid_results

        except Exception as e:
            logger.error(f"全面搜索失败: {e}")
            return []

    async def process_results(self, results: list[SearchResult], request: SearchRequest) -> list[SearchResult]:
        """处理和优化搜索结果"""
        try:
            # 应用过滤器
            if request.filters:
                results = self.apply_filters(results, request.filters)

            # 重新计算相关性分数
            results = self.recalculate_relevance(results, request)

            # 限制结果数量
            results = results[:request.limit]

            return results

        except Exception as e:
            logger.error(f"结果处理失败: {e}")
            return results

    async def generate_reasoning(self, request: SearchRequest, results: list[SearchResult]) -> str:
        """生成搜索推理"""
        try:
            if not results:
                return '未找到相关结果'

            # 简化的推理生成
            reasoning_parts = [
                f"针对查询 '{request.query}'",
                f"执行{request.search_type.value}搜索",
                f"找到 {len(results)} 个相关结果"
            ]

            # 根据意图添加推理
            if request.intent == QueryIntent.FACT_SEARCH:
                reasoning_parts.append('主要基于事实匹配和语义相似性')
            elif request.intent == QueryIntent.SIMILARITY_SEARCH:
                reasoning_parts.append('基于语义向量的相似度计算')
            elif request.intent == QueryIntent.RELATIONSHIP_SEARCH:
                reasoning_parts.append('基于知识图谱中的关系路径')
            elif request.intent == QueryIntent.DISCOVERY_SEARCH:
                reasoning_parts.append('通过多源搜索发现相关信息')

            return '。'.join(reasoning_parts) + '。'

        except Exception as e:
            logger.error(f"推理生成失败: {e}")
            return '搜索推理生成失败'

    async def generate_suggestions(self, request: SearchRequest, results: list[SearchResult]) -> list[str]:
        """生成搜索建议"""
        try:
            suggestions = []

            # 基于结果生成建议
            if len(results) == 0:
                suggestions.append('尝试使用更具体的关键词')
                suggestions.append('检查拼写是否正确')
            elif len(results) < 5:
                suggestions.append('尝试使用同义词或相关概念')
                suggestions.append('考虑使用全面的搜索模式')

            # 基于搜索类型生成建议
            if request.search_type == SearchType.SEMANTIC:
                suggestions.append('尝试混合搜索以获得更全面的结果')
            elif request.search_type == SearchType.EXTERNAL:
                suggestions.append('结合知识图谱搜索获得更深入的信息')

            return suggestions[:5]  # 限制建议数量

        except Exception as e:
            logger.error(f"建议生成失败: {e}")
            return []

    async def expand_query(self, query: str) -> str:
        """扩展查询"""
        try:
            # 简化的查询扩展
            # 实际实现中可以使用同义词词典、概念图谱等
            expansions = {
                'AI': '人工智能',
                'ML': '机器学习',
                'DL': '深度学习',
                '专利': '发明 专利权 知识产权',
                '技术': '科技 技术方案 技术创新'
            }

            for term, expansion in expansions.items():
                if term.lower() in query.lower():
                    query += f" {expansion}"

            return query

        except Exception as e:
            logger.error(f"查询扩展失败: {e}")
            return query

    def apply_filters(self, results: list[SearchResult], filters: dict[str, Any]) -> list[SearchResult]:
        """应用过滤器"""
        try:
            filtered_results = []

            for result in results:
                include = True

                # 来源过滤
                if 'source' in filters:
                    if isinstance(filters['source'], list):
                        if result.source not in filters['source']:
                            include = False
                    else:
                        if result.source != filters['source']:
                            include = False

                # 分数过滤
                if 'min_score' in filters:
                    if result.score < filters['min_score']:
                        include = False

                # 相关性过滤
                if 'min_relevance' in filters:
                    if result.relevance < filters['min_relevance']:
                        include = False

                if include:
                    filtered_results.append(result)

            return filtered_results

        except Exception as e:
            logger.error(f"过滤器应用失败: {e}")
            return results

    def recalculate_relevance(self, results: list[SearchResult], request: SearchRequest) -> list[SearchResult]:
        """重新计算相关性分数"""
        try:
            # 基于搜索类型调整权重
            type_weights = {
                'vector': 1.0,
                'knowledge_graph': 0.9,
                'external': 0.8
            }

            for result in results:
                weight = type_weights.get(result.source_type, 0.5)
                result.relevance = result.score * weight

            return results

        except Exception as e:
            logger.error(f"相关性重计算失败: {e}")
            return results

# 创建搜索引擎实例
search_engine = UnifiedSearchEngine()

@app.on_event('startup')
async def startup_event():
    """应用启动事件"""
    await search_engine.initialize_engines()
    logger.info('统一智能搜索API服务启动成功')

@app.on_event('shutdown')
async def shutdown_event():
    """应用关闭事件"""
    logger.info('统一智能搜索API服务已关闭')

# API接口
@app.get('/')
async def root():
    """根路径"""
    return {
        'service': 'Athena统一智能搜索API',
        'status': 'running',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat(),
        'engines': {
            'vector_search': search_engine.vector_client is not None,
            'knowledge_graph': search_engine.kg_client is not None,
            'external_search': search_engine.external_client is not None
        }
    }

@app.get('/health')
async def health_check():
    """健康检查"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'engines': {
            'vector_search': search_engine.vector_client is not None,
            'knowledge_graph': search_engine.kg_client is not None,
            'external_search': search_engine.external_client is not None
        }
    }

@app.get('/engines')
async def list_engines():
    """列出搜索引擎"""
    return {
        'engines': {
            'semantic_search': {
                'name': '语义搜索',
                'description': '基于向量的语义相似性搜索',
                'status': 'available' if search_engine.vector_client else 'unavailable'
            },
            'knowledge_graph': {
                'name': '知识图谱搜索',
                'description': '基于知识图谱的关系和实体搜索',
                'status': 'available' if search_engine.kg_client else 'unavailable'
            },
            'external_search': {
                'name': '外部搜索引擎',
                'description': '集成多个外部搜索引擎的结果',
                'status': 'available' if search_engine.external_client else 'unavailable'
            }
        }
    }

@app.post('/search', response_model=SearchResponse)
async def search(request: SearchRequest):
    """执行统一搜索"""
    try:
        response = await search_engine.search(request)
        return response
    except Exception as e:
        logger.error(f"搜索请求失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.get('/search/types')
async def get_search_types():
    """获取搜索类型"""
    return {
        'search_types': [st.value for st in SearchType],
        'descriptions': {
            'semantic': '语义搜索（向量）',
            'knowledge': '知识图谱搜索',
            'external': '外部搜索引擎',
            'hybrid': '混合搜索（推荐）',
            'comprehensive': '全面搜索'
        }
    }

@app.get('/search/intents')
async def get_search_intents():
    """获取搜索意图"""
    return {
        'intents': [si.value for si in QueryIntent],
        'descriptions': {
            'fact_search': '事实查询',
            'similarity': '相似性搜索',
            'relationship': '关系查询',
            'discovery': '发现式搜索',
            'analytic': '分析性搜索'
        }
    }

if __name__ == '__main__':
    logger.info('🚀 启动Athena统一智能搜索API')
    logger.info('📍 服务地址: http://localhost:9040')
    logger.info('📊 健康检查: http://localhost:9040/health')
    logger.info('📖 API文档: http://localhost:9040/docs')
    logger.info('🔍 搜索接口: http://localhost:9040/search')
    logger.info('')

    uvicorn.run(
        'unified_intelligent_search:app',
        host='0.0.0.0',
        port=9040,
        reload=False,
        log_level='info'
    )
