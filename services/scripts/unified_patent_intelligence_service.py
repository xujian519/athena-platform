#!/usr/bin/env python3
"""
统一专利智能服务
Unified Patent Intelligence Service

集成向量数据库(Qdrant)和知识图谱(Neo4j)，提供综合专利分析功能
"""

import json
from datetime import datetime
from typing import Any

import requests
from fastapi import FastAPI, HTTPException
from neo4j import GraphDatabase
from pydantic import BaseModel, Field

from core.logging_config import setup_logging

# 导入统一认证模块

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

# 创建FastAPI应用
app = FastAPI(
    title='统一专利智能服务',
    description='集成向量数据库和知识图谱的综合专利分析服务',
    version='1.0.0'
)

# 配置CORS

# 配置信息
QDRANT_URL = 'http://localhost:6333'
NEO4J_URI = 'bolt://localhost:7687'
NEO4J_AUTH = ('neo4j', 'password')

# 全局连接
qdrant_available = False
neo4j_driver = None

class SearchRequest(BaseModel):
    query: str = Field(..., description='搜索查询')
    search_type: str = Field('hybrid', regex='^(vector|graph|hybrid)$', description='搜索类型')
    limit: int = Field(10, ge=1, le=100, description='结果数量限制')
    filters: dict[str, Any] | None = Field(None, description='过滤条件')

class SearchResponse(BaseModel):
    query: str
    search_type: str
    results: list[dict[str, Any]]
    execution_time: float
    vector_results: int | None = None
    graph_results: int | None = None

class PatentInsight(BaseModel):
    patent_id: str
    title: str
    abstract: str
    vector_similarity: float | None = None
    graph_relationships: list[dict[str, Any]] = []
    insights: list[str] = []

@app.on_event('startup')
async def startup_event():
    """服务启动事件"""
    global qdrant_available, neo4j_driver

    # 检查Qdrant连接
    try:
        response = requests.get(f"{QDRANT_URL}/collections", timeout=5)
        if response.status_code == 200:
            qdrant_available = True
            logger.info('✅ Qdrant向量数据库连接成功')
    except Exception as e:
        logger.warning(f"⚠️ Qdrant连接失败: {str(e)}")
        qdrant_available = False

    # 连接Neo4j
    try:
        neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
        with neo4j_driver.session() as session:
            session.run('RETURN 1')
        logger.info('✅ Neo4j知识图谱连接成功')
    except Exception as e:
        logger.warning(f"⚠️ Neo4j连接失败: {str(e)}")
        neo4j_driver = None

    logger.info('🚀 统一专利智能服务启动完成')

@app.on_event('shutdown')
async def shutdown_event():
    """服务关闭事件"""
    global neo4j_driver
    if neo4j_driver:
        neo4j_driver.close()
        logger.info('📌 Neo4j连接已关闭')

@app.get('/')
async def root():
    """根路径"""
    return {
        'service': '统一专利智能服务',
        'status': 'running',
        'qdrant': 'connected' if qdrant_available else 'disconnected',
        'neo4j': 'connected' if neo4j_driver else 'disconnected',
        'timestamp': datetime.now().isoformat()
    }

@app.get('/health')
async def health_check():
    """健康检查"""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {}
    }

    # 检查Qdrant
    try:
        response = requests.get(f"{QDRANT_URL}/collections", timeout=3)
        if response.status_code == 200:
            collections = len(response.json().get('result', {}).get('collections', []))
            health_status['services']['qdrant'] = {
                'status': 'healthy',
                'collections': collections
            }
        else:
            health_status['services']['qdrant'] = {'status': 'error', 'message': 'API error'}
    except (json.JSONDecodeError, TypeError, ValueError):
        health_status['services']['qdrant'] = {'status': 'disconnected'}

    # 检查Neo4j
    if neo4j_driver:
        try:
            with neo4j_driver.session() as session:
                session.run('RETURN 1')
                health_status['services']['neo4j'] = {'status': 'healthy'}
        except (ConnectionError, OSError, TimeoutError):
            health_status['services']['neo4j'] = {'status': 'error'}
    else:
        health_status['services']['neo4j'] = {'status': 'disconnected'}

    return health_status

@app.post('/api/v1/search', response_model=SearchResponse)
async def search_patents(request: SearchRequest):
    """
    综合专利搜索
    支持向量搜索、知识图谱搜索和混合搜索
    """
    start_time = datetime.now()

    results = []
    vector_count = 0
    graph_count = 0

    try:
        # 向量搜索
        if request.search_type in ['vector', 'hybrid'] and qdrant_available:
            vector_results = await vector_search(request.query, request.limit)
            results.extend(vector_results)
            vector_count = len(vector_results)

        # 知识图谱搜索
        if request.search_type in ['graph', 'hybrid'] and neo4j_driver:
            graph_results = await graph_search(request.query, request.limit)
            results.extend(graph_results)
            graph_count = len(graph_results)

        # 混合搜索去重和排序
        if request.search_type == 'hybrid' and vector_results and graph_results:
            results = merge_search_results(vector_results, graph_results)

        execution_time = (datetime.now() - start_time).total_seconds()

        return SearchResponse(
            query=request.query,
            search_type=request.search_type,
            results=results[:request.limit],
            execution_time=execution_time,
            vector_results=vector_count,
            graph_results=graph_count
        )

    except Exception as e:
        logger.error(f"搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}") from e

async def vector_search(query: str, limit: int) -> list[dict]:
    """向量搜索"""
    try:
        # 获取集合列表
        response = requests.get(f"{QDRANT_URL}/collections")
        collections = response.json().get('result', {}).get('collections', [])

        # 选择合适的集合（优先选择patent相关的）
        target_collection = None
        for collection in collections:
            if 'patent' in collection['name'].lower():
                target_collection = collection['name']
                break

        if not target_collection and collections:
            target_collection = collections[0]['name']

        if not target_collection:
            return []

        # 获取集合信息
        collection_info = requests.get(f"{QDRANT_URL}/collections/{target_collection}")
        vector_size = collection_info.json().get('result', {}).get('config', {}).get('params', {}).get('vectors', {}).get('size', 768)

        # 生成查询向量（这里使用随机向量，实际应该使用embedding模型）
        import random
        query_vector = [random.random() for _ in range(vector_size)]

        # 执行搜索
        search_payload = {
            'vector': query_vector,
            'limit': limit,
            'with_payload': True,
            'with_vector': False
        }

        response = requests.post(
            f"{QDRANT_URL}/collections/{target_collection}/points/search",
            json=search_payload
        )

        if response.status_code == 200:
            points = response.json().get('result', [])
            return [
                {
                    'id': point['id'],
                    'type': 'vector_search',
                    'similarity': point['score'],
                    'source': target_collection,
                    'data': point.get('payload', {})
                }
                for point in points
            ]

        return []

    except Exception as e:
        logger.error(f"向量搜索失败: {str(e)}")
        return []

async def graph_search(query: str, limit: int) -> list[dict]:
    """知识图谱搜索"""
    try:
        with neo4j_driver.session() as session:
            # 多种搜索模式
            cypher_queries = [
                # 按专利名称搜索
                """
                MATCH (p:Patent)
                WHERE to_lower(p.name) CONTAINS to_lower($query)
                OPTIONAL MATCH (p)<-[r:INVENTED]-(i:Inventor)
                OPTIONAL MATCH (p)-[:APPLIED_TO]->(c:Company)
                RETURN p, collect(i.name) as inventors, c.name as company
                LIMIT $limit
                """,
                # 按技术领域搜索
                """
                MATCH (p:Patent)-[:HAS_TYPE]->(t:Technology)
                WHERE to_lower(t.name) CONTAINS to_lower($query)
                RETURN p, [] as inventors, '' as company
                LIMIT $limit
                """,
                # 按关键词搜索
                """
                MATCH (p:Patent)-[:HAS_KEYWORD]->(k:Keyword)
                WHERE to_lower(k.name) CONTAINS to_lower($query)
                RETURN p, [] as inventors, '' as company
                LIMIT $limit
                """
            ]

            results = []
            for query_text in cypher_queries:
                result = session.run(query_text, query=query, limit=limit)
                for record in result:
                    patent_node = record['p']
                    results.append({
                        'id': patent_node.get('id', ''),
                        'type': 'graph_search',
                        'source': 'neo4j',
                        'data': {
                            'title': patent_node.get('name', ''),
                            'field': patent_node.get('field', ''),
                            'date': patent_node.get('date', ''),
                            'inventors': record.get('inventors', []),
                            'company': record.get('company', ''),
                            'labels': list(patent_node.labels)
                        }
                    })

            return results[:limit]

    except Exception as e:
        logger.error(f"知识图谱搜索失败: {str(e)}")
        return []

def merge_search_results(vector_results: list[dict], graph_results: list[dict]) -> list[dict]:
    """合并搜索结果"""
    # 简单的合并策略，按相关性排序
    merged = []

    # 添加向量搜索结果
    for result in vector_results:
        merged.append({
            **result,
            'combined_score': result.get('similarity', 0) * 0.6
        })

    # 添加图搜索结果
    for result in graph_results:
        merged.append({
            **result,
            'combined_score': 0.4  # 给图搜索固定分数
        })

    # 按分数排序
    merged.sort(key=lambda x: x.get('combined_score', 0), reverse=True)

    # 去重（基于ID或标题）
    seen = set()
    unique_results = []
    for result in merged:
        key = result.get('id') or result.get('data', {}).get('title', '')
        if key not in seen:
            seen.add(key)
            unique_results.append(result)

    return unique_results

@app.get('/api/v1/patent/{patent_id}/insights')
async def get_patent_insights(patent_id: str):
    """获取专利深度洞察"""
    insights = {
        'patent_id': patent_id,
        'vector_analysis': {},
        'graph_analysis': {},
        'combined_insights': []
    }

    # 向量分析
    if qdrant_available:
        # 查找相似的专利
        similar_patents = await find_similar_patents_vector(patent_id)
        insights['vector_analysis'] = {
            'similar_patents': similar_patents[:5],
            'total_similar': len(similar_patents)
        }

    # 知识图谱分析
    if neo4j_driver:
        graph_insights = await get_patent_graph_insights(patent_id)
        insights['graph_analysis'] = graph_insights

    # 生成综合洞察
    insights['combined_insights'] = generate_combined_insights(insights)

    return insights

async def find_similar_patents_vector(patent_id: str, limit: int = 10) -> list[dict]:
    """在向量空间中查找相似专利"""
    # 这里需要实现具体的向量相似度查找逻辑
    # 暂时返回空列表
    return []

async def get_patent_graph_insights(patent_id: str) -> dict:
    """获取专利在知识图谱中的洞察"""
    try:
        with neo4j_driver.session() as session:
            # 获取专利的完整关系网络
            cypher = """
            MATCH (p:Patent {id: $patent_id})
            OPTIONAL MATCH (p)<-[r:INVENTED]-(i:Inventor)
            OPTIONAL MATCH (p)-[:APPLIED_TO]->(c:Company)
            OPTIONAL MATCH (p)-[:HAS_TYPE]->(t:Technology)
            OPTIONAL MATCH (p)-[:HAS_KEYWORD]->(k:Keyword)
            OPTIONAL MATCH (p)-[:REFERENCES]->(ref:Patent)
            OPTIONAL MATCH (other:Patent)-[:REFERENCES]->(p)
            RETURN
                p,
                collect(DISTINCT i.name) as inventors,
                c.name as company,
                collect(DISTINCT t.name) as technologies,
                collect(DISTINCT k.name) as keywords,
                collect(DISTINCT ref.id) as references,
                count(DISTINCT other) as cited_by_count
            """

            result = session.run(cypher, patent_id=patent_id)
            record = result.single()

            if record:
                return {
                    'inventors': record['inventors'],
                    'company': record['company'],
                    'technologies': record['technologies'],
                    'keywords': record['keywords'],
                    'references': record['references'],
                    'cited_by_count': record['cited_by_count'],
                    'network_strength': len(record['inventors']) + len(record['technologies']) + len(record['keywords'])
                }

            return {}

    except Exception as e:
        logger.error(f"获取图洞察失败: {str(e)}")
        return {}

def generate_combined_insights(insights: dict) -> list[str]:
    """生成综合洞察"""
    combined_insights = []

    # 基于向量相似度的洞察
    vector_similar = insights.get('vector_analysis', {}).get('total_similar', 0)
    if vector_similar > 10:
        combined_insights.append(f"该专利有{vector_similar}个相似专利，属于热门技术领域")

    # 基于图关系的洞察
    graph_analysis = insights.get('graph_analysis', {})
    inventors = graph_analysis.get('inventors', [])
    technologies = graph_analysis.get('technologies', [])

    if len(inventors) > 3:
        combined_insights.append(f"该专利有{len(inventors)}位发明人，可能是重要发明")

    if len(technologies) > 2:
        combined_insights.append(f"该专利涉及{len(technologies)}个技术领域，具有跨领域特征")

    # 组合洞察
    if vector_similar > 5 and len(technologies) > 1:
        combined_insights.append('该专利在相似技术中具有跨领域应用价值')

    return combined_insights

@app.get('/api/v1/statistics')
async def get_statistics():
    """获取系统统计信息"""
    stats = {
        'timestamp': datetime.now().isoformat(),
        'qdrant': {},
        'neo4j': {}
    }

    # Qdrant统计
    if qdrant_available:
        try:
            response = requests.get(f"{QDRANT_URL}/collections")
            collections = response.json().get('result', {}).get('collections', [])

            total_vectors = 0
            for collection in collections[:5]:  # 只统计前5个集合
                try:
                    coll_info = requests.get(f"{QDRANT_URL}/collections/{collection['name']}")
                    vectors_count = coll_info.json().get('result', {}).get('vectors_count', 0)
                    total_vectors += vectors_count
                except Exception as e:
                    logger.error(f"Error: {e}", exc_info=True)

            stats['qdrant'] = {
                'collections': len(collections),
                'estimated_total_vectors': total_vectors
            }
        except (json.JSONDecodeError, TypeError, ValueError):
            stats['qdrant'] = {'error': 'Failed to get statistics'}

    # Neo4j统计
    if neo4j_driver:
        try:
            with neo4j_driver.session() as session:
                # 节点统计
                node_result = session.run('MATCH (n) RETURN count(n) as count')
                node_count = node_result.single()['count']

                # 关系统计
                rel_result = session.run('MATCH ()-[r]->() RETURN count(r) as count')
                rel_count = rel_result.single()['count']

                # 标签统计
                label_result = session.run('CALL db.labels()')
                labels = [record['label'] for record in label_result]

                stats['neo4j'] = {
                    'nodes': node_count,
                    'relationships': rel_count,
                    'labels': labels
                }
        except (ConnectionError, OSError, TimeoutError):
            stats['neo4j'] = {'error': 'Failed to get statistics'}

    return stats

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        'unified_patent_intelligence_service:app',
        host='0.0.0.0',
        port=8010,
        reload=True,
        log_level='info'
    )
