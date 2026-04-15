from __future__ import annotations
from dataclasses import asdict

#!/usr/bin/env python3
"""
Athena集成搜索引擎的增强版知识图谱API
Enhanced Knowledge Graph API with Search Engine Integration

结合内部知识图谱和外部搜索引擎，提供全面的信息检索和内容理解服务

作者: Athena AI系统
创建时间: 2025-12-08
版本: 3.0.0
"""

import logging
import os
import sys
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # 导入统一认证模块
    import uvicorn
    from external_search_engine import SearchIntegrationService, SearchQuery, SearchScope
    from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
    from fastapi.middleware.cors import CORSMiddleware
    from neo4j import GraphDatabase
    from pydantic import BaseModel, Field
    from shared.auth.auth_middleware import create_auth_middleware, setup_cors

    FASTAPI_AVAILABLE = True
except ImportError as e:
    logger.info(f"⚠️ 依赖库未安装: {e}")
    FASTAPI_AVAILABLE = False
    # 提供fallback占位，避免F821未定义错误
    SearchQuery = None
    SearchScope = None
    SearchIntegrationService = None

# 搜索范围枚举
class SearchScopeEnum(str, Enum):
    GENERAL = 'general'
    PROFESSIONAL = 'professional'
    ACADEMIC = 'academic'
    LEGAL = 'legal'
    TECHNICAL = 'technical'

# 数据模型
class EnhancedSearchRequest(BaseModel):
    """增强搜索请求"""
    query: str = Field(..., description='搜索查询')
    scope: SearchScopeEnum = Field(default=SearchScopeEnum.GENERAL, description='搜索范围')
    include_external: bool = Field(default=True, description='是否包含外部搜索')
    include_knowledge_graph: bool = Field(default=True, description='是否包含知识图谱搜索')
    limit: int = Field(default=20, ge=1, le=100, description='结果数量限制')

class ContentAnalysisRequest(BaseModel):
    """内容分析请求"""
    content: str = Field(..., description='待分析的内容')
    scope: SearchScopeEnum = Field(default=SearchScopeEnum.GENERAL, description='分析范围')

class EnhancedSearchResponse(BaseModel):
    """增强搜索响应"""
    query: str
    scope: str
    content_analysis: dict[str, Any]
    knowledge_graph_results: list[dict[str, Any]]
    external_search_results: list[dict[str, Any]]
    total_results: int
    execution_time: float
    timestamp: str

class ContentAnalysisResponse(BaseModel):
    """内容分析响应"""
    original_input: str
    key_concepts: list[str]
    entities: list[dict[str, str]]
    intent: str
    context: str
    suggestions: list[str]
    search_terms: list[str]
    execution_time: float

class IntelligentQueryResponse(BaseModel):
    """智能查询响应"""
    original_query: str
    enhanced_query: str
    understanding: dict[str, Any]
    recommended_actions: list[str]
    related_queries: list[str]
    execution_time: float

class EnhancedKnowledgeGraphAPI:
    """集成搜索引擎的增强版知识图谱API"""

    def __init__(self):
        self.app = None
        self.driver = None
        self.search_service = None

        if FASTAPI_AVAILABLE:
            self.app = FastAPI(
                title='Athena增强版知识图谱API',
                description='集成外部搜索引擎的智能知识图谱服务',
                version='3.0.0',
                docs_url='/docs',
                redoc_url='/redoc'
            )
            self.setup_middleware()
            self.setup_routes()
            self.setup_connections()

    def setup_middleware(self):
        """设置中间件"""

    def setup_connections(self):
        """设置连接"""
        # Neo4j连接
        try:
            self.driver = GraphDatabase.driver(
                'bolt://localhost:7687',
                auth=('neo4j', 'password'),
                max_connection_lifetime=30 * 60,
                max_connection_pool_size=50
            )
            logger.info('✅ Neo4j连接成功')
        except Exception as e:
            logger.info(f"❌ Neo4j连接失败: {str(e)}")
            self.driver = None

        # 搜索服务连接
        try:
            self.search_service = SearchIntegrationService()
            logger.info('✅ 搜索服务初始化成功')
        except Exception as e:
            logger.info(f"❌ 搜索服务初始化失败: {str(e)}")
            self.search_service = None

    def setup_routes(self):
        """设置路由"""

        @self.app.get('/')
        async def root():
            return {
                'message': 'Athena增强版知识图谱API',
                'version': '3.0.0',
                'status': 'running',
                'features': [
                    '知识图谱查询',
                    '外部搜索引擎集成',
                    '内容智能理解',
                    '增强搜索建议'
                ],
                'search_engines': [
                    'One Search',
                    'Web Search Prime',
                    '多引擎并行搜索'
                ],
                'timestamp': datetime.now().isoformat()
            }

        @self.app.get('/health')
        async def health_check():
            """健康检查"""
            return {
                'status': 'healthy',
                'neo4j': 'connected' if self.driver else 'disconnected',
                'search_service': 'available' if self.search_service else 'unavailable',
                'timestamp': datetime.now().isoformat()
            }

        @self.app.post('/enhanced-search', response_model=EnhancedSearchResponse)
        async def enhanced_search(request: EnhancedSearchRequest):
            """增强搜索 - 结合知识图谱和外部搜索引擎"""
            if not self.search_service:
                raise HTTPException(status_code=503, detail='搜索服务不可用')

            start_time = time.time()

            try:
                # 执行增强搜索
                search_scope = SearchScope(request.scope.value)
                result = await self.search_service.enhanced_search(
                    query=request.query,
                    scope=search_scope
                )

                execution_time = time.time() - start_time

                # 根据请求过滤结果
                if not request.include_knowledge_graph:
                    result['knowledge_graph_results'] = []

                if not request.include_external:
                    result['external_search_results'] = []

                # 限制结果数量
                if request.limit < result['total_results']:
                    kg_count = min(len(result['knowledge_graph_results']), request.limit // 2)
                    ext_count = request.limit - kg_count

                    result['knowledge_graph_results'] = result['knowledge_graph_results'][:kg_count]
                    result['external_search_results'] = result['external_search_results'][:ext_count]
                    result['total_results'] = kg_count + ext_count

                return EnhancedSearchResponse(
                    query=result['query'],
                    scope=result['scope'],
                    content_analysis=result['content_analysis'],
                    knowledge_graph_results=result['knowledge_graph_results'],
                    external_search_results=result['external_search_results'],
                    total_results=result['total_results'],
                    execution_time=execution_time,
                    timestamp=result['timestamp']
                )

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"增强搜索失败: {str(e)}") from e

        @self.app.post('/analyze-content', response_model=ContentAnalysisResponse)
        async def analyze_content(request: ContentAnalysisRequest):
            """内容智能分析"""
            if not self.search_service:
                raise HTTPException(status_code=503, detail='搜索服务不可用')

            start_time = time.time()

            try:
                search_scope = SearchScope(request.scope.value)
                analysis = await self.search_service.search_engine.understand_content(
                    content=request.content,
                    scope=search_scope
                )

                execution_time = time.time() - start_time

                return ContentAnalysisResponse(
                    original_input=analysis.original_input,
                    key_concepts=analysis.key_concepts,
                    entities=[{'type': e['type'], 'value': e['value']} for e in analysis.entities],
                    intent=analysis.intent,
                    context=analysis.context,
                    suggestions=analysis.suggestions,
                    search_terms=analysis.search_terms,
                    execution_time=execution_time
                )

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"内容分析失败: {str(e)}") from e

        @self.app.post('/intelligent-query', response_model=IntelligentQueryResponse)
        async def intelligent_query(query_data: dict[str, str]):
            """智能查询 - 理解用户意图并提供增强查询建议"""
            if not self.search_service:
                raise HTTPException(status_code=503, detail='搜索服务不可用')

            query = query_data.get('query', '')
            if not query:
                raise HTTPException(status_code=400, detail='查询内容不能为空')

            start_time = time.time()

            try:
                # 理解查询内容
                analysis = await self.search_service.search_engine.understand_content(
                    content=query,
                    scope=SearchScope.GENERAL
                )

                # 生成增强查询
                enhanced_query = self._enhance_query(query, analysis)

                # 生成推荐行动
                recommended_actions = self._generate_actions(analysis)

                # 生成相关查询建议
                related_queries = self._generate_related_queries(analysis)

                execution_time = time.time() - start_time

                return IntelligentQueryResponse(
                    original_query=query,
                    enhanced_query=enhanced_query,
                    understanding={
                        'intent': analysis.intent,
                        'key_concepts': analysis.key_concepts,
                        'entities': [{'type': e['type'], 'value': e['value']} for e in analysis.entities],
                        'context': analysis.context[:200] + '...'
                    },
                    recommended_actions=recommended_actions,
                    related_queries=related_queries,
                    execution_time=execution_time
                )

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"智能查询失败: {str(e)}") from e

        @self.app.get('/search-suggestions')
        async def get_search_suggestions(
            query: str = Query(..., description='基础查询'),
            scope: SearchScopeEnum = Query(default=SearchScopeEnum.GENERAL, description='搜索范围')
        ):
            """获取搜索建议"""
            if not self.search_service:
                raise HTTPException(status_code=503, detail='搜索服务不可用')

            try:
                search_scope = SearchScope(scope.value)
                analysis = await self.search_service.search_engine.understand_content(
                    content=query,
                    scope=search_scope
                )

                return {
                    'query': query,
                    'scope': scope.value,
                    'suggestions': analysis.search_terms[:5],
                    'related_concepts': analysis.key_concepts[:5],
                    'intent': analysis.intent,
                    'recommended_actions': analysis.suggestions[:3]
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"搜索建议生成失败: {str(e)}") from e

        @self.app.get('/patent-intelligent-search')
        async def patent_intelligent_search(
            query: str = Query(..., description='专利相关查询'),
            limit: int = Query(default=10, ge=1, le=50, description='结果数量限制')
        ):
            """专利智能搜索"""
            if not self.driver and not self.search_service:
                raise HTTPException(status_code=503, detail='服务不可用')

            try:
                results = []

                # 内部知识图谱搜索
                if self.driver:
                    with self.driver.session() as session:
                        patent_query = """
                        MATCH (p:Patent)
                        WHERE p.title CONTAINS $query OR p.abstract CONTAINS $query
                        OPTIONAL MATCH (p)-[:USES_TECHNOLOGY]->(t:Technology)
                        OPTIONAL MATCH (p)-[:ASSIGNED_TO]->(c:Company)
                        RETURN p.id as id,
                               p.title as title,
                               p.abstract as abstract,
                               COLLECT(DISTINCT t.name) as technologies,
                               COLLECT(DISTINCT c.name) as companies,
                               'patent' as source_type
                        LIMIT $limit
                        """

                        patent_result = session.run(patent_query, query=query, limit=limit)
                        for record in patent_result:
                            results.append({
                                'id': record['id'],
                                'title': record['title'],
                                'abstract': record['abstract'][:300] + '...',
                                'technologies': record['technologies'],
                                'companies': record['companies'],
                                'source_type': record['source_type'],
                                'relevance_score': 0.9
                            })

                # 外部搜索引擎补充
                if self.search_service and len(results) < limit:
                    search_query = SearchQuery(
                        query=f"{query} 专利 技术",
                        scope=SearchScope.PROFESSIONAL,
                        limit=limit - len(results)
                    )

                    external_results = await self.search_service.search_engine.search(search_query)
                    for result in external_results:
                        results.append({
                            'id': result.url,
                            'title': result.title,
                            'abstract': result.snippet,
                            'url': result.url,
                            'domain': result.domain,
                            'source_type': 'external_search',
                            'relevance_score': result.relevance_score
                        })

                # 按相关性排序
                results.sort(key=lambda x: x['relevance_score'], reverse=True)

                return {
                    'query': query,
                    'total_results': len(results),
                    'results': results[:limit],
                    'sources': list({r['source_type'] for r in results}),
                    'timestamp': datetime.now().isoformat()
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"专利智能搜索失败: {str(e)}") from e

        @self.app.get('/cross-domain-search')
        async def cross_domain_search(
            query: str = Query(..., description='跨领域查询'),
            domains: str = Query(default='patent,technology,legal', description='搜索领域，逗号分隔')
        ):
            """跨领域搜索"""
            if not self.search_service:
                raise HTTPException(status_code=503, detail='搜索服务不可用')

            try:
                domain_list = [d.strip() for d in domains.split(',')]
                results = {}

                for domain in domain_list:
                    # 根据领域调整查询和范围
                    domain_query = f"{query} {self._get_domain_keyword(domain)}"

                    if domain == 'patent':
                        scope = SearchScope.PROFESSIONAL
                    elif domain == 'legal':
                        scope = SearchScope.LEGAL
                    elif domain == 'technology':
                        scope = SearchScope.TECHNICAL
                    elif domain == 'academic':
                        scope = SearchScope.ACADEMIC
                    else:
                        scope = SearchScope.GENERAL

                    search_query_obj = SearchQuery(
                        query=domain_query,
                        scope=scope,
                        limit=5
                    )

                    domain_results = await self.search_service.search_engine.search(search_query_obj)
                    results[domain] = [asdict(r) for r in domain_results]

                total_results = sum(len(domain_results) for domain_results in results.values())

                return {
                    'query': query,
                    'domains': domain_list,
                    'results': results,
                    'total_results': total_results,
                    'timestamp': datetime.now().isoformat()
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"跨领域搜索失败: {str(e)}") from e

    def _enhance_query(self, original_query: str, analysis) -> str:
        """增强查询"""
        # 基于分析结果增强查询
        if analysis.key_concepts:
            # 添加关键概念
            enhanced = f"{original_query} {analysis.key_concepts[0]}"
        else:
            enhanced = original_query

        # 根据意图添加限定词
        if '专利' in analysis.intent:
            enhanced = f"{enhanced} 专利 技术"
        elif '法律' in analysis.intent:
            enhanced = f"{enhanced} 法律 条例"
        elif '分析' in analysis.intent:
            enhanced = f"{enhanced} 研究 报告"

        return enhanced

    def _generate_actions(self, analysis) -> list[str]:
        """生成推荐行动"""
        actions = []

        if '专利' in analysis.intent:
            actions.extend([
                '建议查询专利数据库获取详细信息',
                '可以查看专利引用关系',
                '考虑分析技术发展趋势'
            ])

        if '技术' in analysis.intent:
            actions.extend([
                '建议查阅技术文档和白皮书',
                '可以搜索相关技术标准',
                '考虑查看技术发展路线图'
            ])

        if analysis.entities:
            actions.append(f"发现{len(analysis.entities)}个相关实体，建议进一步分析")

        return actions[:5]

    def _generate_related_queries(self, analysis) -> list[str]:
        """生成相关查询建议"""
        related_queries = []

        # 基于关键概念生成相关查询
        if len(analysis.key_concepts) >= 2:
            related_queries.append(f"{analysis.key_concepts[0]} {analysis.key_concepts[1]}")

        # 基于实体生成相关查询
        for entity in analysis.entities[:2]:
            if entity['type'] == 'technology':
                related_queries.append(f"{entity['value']} 应用案例")
            elif entity['type'] == 'patent':
                related_queries.append(f"专利 {entity['value']} 技术分析")

        # 基于意图生成相关查询
        if '对比' in analysis.intent:
            related_queries.append(f"{analysis.key_concepts[0] if analysis.key_concepts else ''} 优势劣势分析")

        return related_queries[:5]

    def _get_domain_keyword(self, domain: str) -> str:
        """获取领域关键词"""
        domain_keywords = {
            'patent': '专利',
            'technology': '技术',
            'legal': '法律',
            'academic': '研究',
            'market': '市场'
        }
        return domain_keywords.get(domain, '')

    def run(self, host: str = '0.0.0.0', port: int = 8090):
        """运行增强版API服务"""
        if not FASTAPI_AVAILABLE:
            logger.info('❌ 依赖库未安装，无法启动服务')
            return False

        if not self.driver and not self.search_service:
            logger.info('❌ 没有可用的服务连接')
            return False

        logger.info('🚀 启动Athena增强版知识图谱API服务')
        logger.info(f"📍 服务地址: http://{host}:{port}")
        logger.info('📚 API文档: http://{host}:{port}/docs')
        logger.info('🔍 健康检查: http://{host}:{port}/health')
        logger.info('⚡ 增强特性: 外部搜索引擎、内容理解、智能查询')

        try:
            uvicorn.run(self.app, host=host, port=port)
            return True
        except Exception as e:
            logger.info(f"❌ 启动失败: {str(e)}")
            return False

    def close(self):
        """关闭连接"""
        if self.search_service:
            self.search_service.close()
        if self.driver:
            self.driver.close()

# 需要导入time模块
import time


def main():
    """主函数"""
    api_service = EnhancedKnowledgeGraphAPI()
    try:
        success = api_service.run(port=8090)
        if not success:
            logger.info("\n💡 请确保:")
            logger.info('1. 安装依赖: pip install fastapi uvicorn neo4j aiohttp')
            logger.info('2. 启动Neo4j: neo4j start')
            logger.info('3. 确保MCP搜索引擎服务可用')
    finally:
        api_service.close()

if __name__ == '__main__':
    main()
