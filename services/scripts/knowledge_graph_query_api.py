#!/usr/bin/env python3
"""
知识图谱查询API服务
作者：小娜
日期：2025-12-07
"""

import os
from datetime import datetime
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from neo4j import GraphDatabase
from pydantic import BaseModel

from core.logging_config import setup_logging

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

# FastAPI应用
app = FastAPI(
    title='Athena知识图谱查询API',
    description='基于neo4j的智能知识图谱查询服务',
    version='1.0.0'
)

# Neo4j连接配置
NEO4J_URI = 'bolt://localhost:7687'
NEO4J_USER = 'neo4j'
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

class KnowledgeGraphService:
    """知识图谱服务类"""

    def __init__(self):
        self.driver = None
        self.connect()

    def connect(self) -> Any:
        """连接neo4j数据库"""
        try:
            self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
            logger.info('成功连接neo4j数据库')
        except Exception as e:
            logger.error(f"连接neo4j失败: {e}")
            raise

    def close(self) -> Any:
        """关闭连接"""
        if self.driver:
            self.driver.close()

    def execute_query(self, query: str, parameters: dict = None) -> list[dict]:
        """执行查询"""
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"查询执行失败: {e}")
            raise

# 全局服务实例
kg_service = KnowledgeGraphService()

# API模型定义
class QueryRequest(BaseModel):
    """查询请求模型"""
    query: str
    parameters: dict[str, Any] | None = {}

class NodeResponse(BaseModel):
    """节点响应模型"""
    id: str
    labels: list[str]
    properties: dict[str, Any]

class RelationshipResponse(BaseModel):
    """关系响应模型"""
    id: str
    type: str
    start_node: str
    end_node: str
    properties: dict[str, Any]

class GraphResponse(BaseModel):
    """图响应模型"""
    nodes: list[NodeResponse]
    relationships: list[RelationshipResponse]

# API路由
@app.on_event('shutdown')
async def shutdown_event():
    """关闭服务时的清理"""
    kg_service.close()

@app.get('/')
async def root():
    """根路径"""
    return {
        'service': 'Athena知识图谱查询API',
        'status': 'running',
        'timestamp': datetime.now().isoformat()
    }

@app.get('/health')
async def health_check():
    """健康检查"""
    try:
        result = kg_service.execute_query('RETURN 1 as test')
        if result and result[0]['test'] == 1:
            return {
                'status': 'healthy',
                'database': 'connected',
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return JSONResponse(
            status_code=503,
            content={
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        )

@app.get('/stats')
async def get_statistics():
    """获取知识图谱统计信息"""
    try:
        # 节点统计
        node_query = """
        MATCH (n)
        RETURN labels(n) as labels, count(n) as count
        ORDER BY count DESC
        """
        node_stats = kg_service.execute_query(node_query)

        # 关系统计
        rel_query = """
        MATCH ()-[r]->()
        RETURN type(r) as type, count(r) as count
        ORDER BY count DESC
        """
        rel_stats = kg_service.execute_query(rel_query)

        # 总计
        total_nodes = kg_service.execute_query('MATCH (n) RETURN count(n) as count')[0]['count']
        total_rels = kg_service.execute_query('MATCH ()-[r]->() RETURN count(r) as count')[0]['count']

        return {
            'total_nodes': total_nodes,
            'total_relationships': total_rels,
            'node_labels': node_stats,
            'relationship_types': rel_stats,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.post('/query')
async def execute_query(request: QueryRequest):
    """执行自定义Cypher查询"""
    try:
        # 安全检查，只允许SELECT查询
        if any(keyword in request.query.upper() for keyword in ['DELETE', 'DROP', 'CREATE', 'MERGE', 'SET']):
            raise HTTPException(status_code=400, detail='只允许执行查询操作')

        results = kg_service.execute_query(request.query, request.parameters)
        return {
            'query': request.query,
            'results': results,
            'count': len(results),
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"查询执行失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.get('/search/nodes')
async def search_nodes(
    label: str | None = Query(None, description='节点标签'),
    property_key: str | None = Query(None, description='属性键'),
    property_value: str | None = Query(None, description='属性值'),
    limit: int = Query(10, le=100, description='返回数量限制')
):
    """搜索节点"""
    try:
        # 构建查询
        conditions = []
        if label:
            conditions.append(f"n:{label}")
        if property_key and property_value:
            conditions.append(f"n.{property_key} CONTAINS $property_value")

        where_clause = ' AND '.join(conditions) if conditions else 'true'
        query = f"""
        MATCH (n)
        WHERE {where_clause}
        RETURN n
        LIMIT $limit
        """

        parameters = {'limit': limit}
        if property_value:
            parameters['property_value'] = property_value

        results = kg_service.execute_query(query, parameters)
        nodes = []
        for result in results:
            node = result['n']
            nodes.append(NodeResponse(
                id=str(node.id),
                labels=list(node.labels),
                properties=dict(node)
            ))

        return {'nodes': nodes, 'count': len(nodes)}

    except Exception as e:
        logger.error(f"搜索节点失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.get('/search/path')
async def find_path(
    start_id: str = Query(..., description='起始节点ID'),
    end_id: str = Query(..., description='结束节点ID'),
    max_depth: int = Query(5, le=10, description='最大深度')
):
    """查找节点间路径"""
    try:
        query = """
        MATCH path = shortest_path((start)-[*1..%d]-(end))
        WHERE id(start) = $start_id AND id(end) = $end_id
        RETURN path
        """ % max_depth

        parameters = {'start_id': int(start_id), 'end_id': int(end_id)}
        results = kg_service.execute_query(query, parameters)

        paths = []
        for result in results:
            path = result['path']
            nodes = []
            relationships = []

            for node in path.nodes:
                nodes.append(NodeResponse(
                    id=str(node.id),
                    labels=list(node.labels),
                    properties=dict(node)
                ))

            for rel in path.relationships:
                relationships.append(RelationshipResponse(
                    id=str(rel.id),
                    type=rel.type,
                    start_node=str(rel.start_node.id),
                    end_node=str(rel.end_node.id),
                    properties=dict(rel)
                ))

            paths.append({'nodes': nodes, 'relationships': relationships})

        return {'paths': paths, 'count': len(paths)}

    except Exception as e:
        logger.error(f"查找路径失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.get('/memory/entities')
async def get_memory_entities():
    """获取记忆实体"""
    try:
        query = """
        MATCH (n:MemoryEntity)
        RETURN n
        ORDER BY n.name
        """
        results = kg_service.execute_query(query)

        entities = []
        for result in results:
            node = result['n']
            entities.append({
                'name': node.get('name', ''),
                'type': node.get('type', ''),
                'observations': node.get('observations', []),
                'id': str(node.id)
            })

        return {'entities': entities, 'count': len(entities)}

    except Exception as e:
        logger.error(f"获取记忆实体失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.get('/memory/relations')
async def get_memory_relations():
    """获取记忆关系"""
    try:
        query = """
        MATCH (a:MemoryEntity)-[r:MEMORY_RELATION]->(b:MemoryEntity)
        RETURN a.name as from_entity, r.type as relation_type, b.name as to_entity
        """
        results = kg_service.execute_query(query)

        relations = []
        for result in results:
            relations.append({
                'from': result['from_entity'],
                'type': result['relation_type'],
                'to': result['to_entity']
            })

        return {'relations': relations, 'count': len(relations)}

    except Exception as e:
        logger.error(f"获取记忆关系失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

if __name__ == '__main__':
    uvicorn.run(
        'knowledge_graph_query_api:app',
        host='0.0.0.0',
        port=8088,
        reload=True,
        log_level='info'
    )
