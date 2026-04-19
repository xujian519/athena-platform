#!/usr/bin/env python3
"""
Athena知识图谱统一API服务
Unified Knowledge Graph API Service

提供统一的知识图谱查询、管理和分析接口
支持SQLite和Neo4j图数据库后端
"""

import json
import logging
import os

# 添加项目路径
import sys
from datetime import datetime
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

# 导入统一认证模块

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.knowledge.patent_analysis.knowledge_graph import (
    NodeType,
    RelationType,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title='Athena知识图谱API',
    description='统一的知识图谱查询和管理接口',
    version='1.0.0',
    docs_url='/docs',
    redoc_url='/redoc',
)

# CORS配置


# 数据模型
class GraphNode(BaseModel):
    """图谱节点模型"""

    id: str
    type: str
    properties: dict[str, Any]
    created_at: datetime | None = None


class GraphEdge(BaseModel):
    """图谱边模型"""

    id: str
    source: str
    target: str
    type: str
    properties: dict[str, Any]
    weight: float | None = 1.0
    created_at: datetime | None = None


class GraphQuery(BaseModel):
    """图查询模型"""

    query: str
    parameters: dict[str, Any] | None = None
    limit: int | None = 100
    offset: int | None = 0


class GraphSearch(BaseModel):
    """图搜索模型"""

    node_type: str | None = None
    domain: str | None = None
    properties: dict[str, Any] | None = None
    limit: int | None = 100


class PathQuery(BaseModel):
    """路径查询模型"""

    source: str
    target: str
    max_depth: int | None = 5
    relationship_types: list[str] | None = None


class IndexInitRequest(BaseModel):
    create_constraints: bool | None = True
    create_indexes: bool | None = True
    create_fulltext: bool | None = True


class NeighborsQuery(BaseModel):
    id: str
    max_depth: int | None = 2
    relation_types: list[str] | None = None
    node_type_filter: str | None = None


class FullTextSearchRequest(BaseModel):
    q: str
    limit: int | None = 20


# 全局变量
kg_connections = {}
graph_stats = {}


class KnowledgeGraphManager:
    """知识图谱管理器"""

    def __init__(self):
        self.neo4j_uri = os.getenv('KNOWLEDGE_GRAPH_NEO4J_URI', 'bolt://localhost:7687')
        self.neo4j_user = os.getenv('KNOWLEDGE_GRAPH_NEO4J_USER', 'neo4j')
        self.neo4j_password = os.getenv('KNOWLEDGE_GRAPH_NEO4J_PASSWORD', '')
        self.neo4j_database = os.getenv('KNOWLEDGE_GRAPH_NEO4J_DATABASE', 'neo4j')
        self.load_config()
        self.initialize_connections()

    async def initialize_connections(self):
        """初始化连接"""
        try:
            # Neo4j连接
            await self.connect_neo4j()

            # 统计信息
            await self.update_statistics()

            logger.info('知识图谱连接初始化完成')

        except Exception as e:
            logger.error(f"知识图谱连接初始化失败: {e}")

    def load_config(self) -> Any | None:
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            cfg_path = os.path.join(
                base_dir,
                'infrastructure',
                'config',
                'database',
                'knowledge_graph_config.json',
            )
            if os.path.exists(cfg_path):
                with open(cfg_path, encoding='utf-8') as f:
                    cfg = json.load(f)
                    neo = cfg.get('knowledge_graph', {}).get('neo4j', {})
                    self.neo4j_uri = neo.get('uri', self.neo4j_uri)
                    self.neo4j_user = neo.get('user', self.neo4j_user)
                    self.neo4j_database = neo.get('database', self.neo4j_database)
        except Exception as e:
            # 记录异常但不中断流程
            logger.debug(f"[knowledge_graph_api] Exception: {e}")

    async def connect_neo4j(self):
        """连接Neo4j图数据库"""
        try:
            from neo4j import GraphDatabase

            # 测试Neo4j连接
            driver = GraphDatabase.driver(
                self.neo4j_uri, auth=(self.neo4j_user, self.neo4j_password)
            )

            with driver.session(database=self.neo4j_database) as session:
                result = session.run('RETURN 1 as test')
                test_value = result.single()['test']
                if test_value == 1:
                    kg_connections['neo4j'] = driver
                    logger.info('Neo4j连接成功')
                    return True
                else:
                    logger.warning('Neo4j连接测试失败')
                    driver.close()
                    return False

        except Exception as e:
            logger.warning(f"Neo4j连接异常: {e}")
            return False

    async def update_statistics(self):
        """更新统计信息"""
        try:
            stats = {}

            # Neo4j统计
            try:
                if 'neo4j' in kg_connections:
                    driver = kg_connections['neo4j']
                    with driver.session(database=self.neo4j_database) as session:
                        # 节点统计
                        result = session.run('MATCH (n) RETURN COUNT(n) as count')
                        stats['neo4j_nodes'] = result.single()['count']

                        # 关系统计
                        result = session.run(
                            'MATCH ()-[r]->() RETURN COUNT(r) as count'
                        )
                        stats['neo4j_edges'] = result.single()['count']

                        # 按类型统计
                        result = session.run(
                            'MATCH (n) RETURN n.entity_type as type, COUNT(n) as count'
                        )
                        stats['neo4j_nodes_by_type'] = {
                            record['type']: record['count'] for record in result
                        }

                        stats['neo4j_status'] = 'connected'
                else:
                    stats['neo4j_status'] = 'disconnected'
            except Exception as e:
                stats['neo4j_status'] = 'error'
                logger.warning(f"Neo4j统计获取失败: {e}")

            global graph_stats
            graph_stats = stats

        except Exception as e:
            logger.error(f"更新统计信息失败: {e}")


# 创建管理器实例
kg_manager = KnowledgeGraphManager()


@app.on_event('startup')
async def startup_event():
    """应用启动事件"""
    await kg_manager.initialize_connections()
    logger.info('知识图谱API服务启动成功')


@app.on_event('shutdown')
async def shutdown_event():
    """应用关闭事件"""
    for name, conn in kg_connections.items():
        if name == 'neo4j' and conn:
            conn.close()
    logger.info('知识图谱API服务已关闭')


# API接口
@app.get('/')
async def root():
    """根路径"""
    return {
        'service': 'Athena知识图谱API',
        'status': 'running',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat(),
        'connections': {'neo4j': 'neo4j' in kg_connections},
    }


@app.get('/health')
async def health_check():
    """健康检查"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {'neo4j': 'neo4j' in kg_connections},
        'statistics': graph_stats,
    }


@app.get('/graphs')
async def list_graphs():
    """列出所有知识图谱"""
    try:
        graphs = []

        if 'neo4j' in kg_connections:
            driver = kg_connections['neo4j']
            mem_nodes = 0
            mem_edges = 0
            pro_nodes = 0
            pro_edges = 0
            with driver.session(database=kg_manager.neo4j_database) as session:
                r1 = session.run(
                    "MATCH (n:Entity{kg_domain:'memory'}) RETURN COUNT(n) as c"
                )
                mem_nodes = r1.single()['c'] if r1.peek() else 0
                r2 = session.run(
                    "MATCH (:Entity{kg_domain:'memory'})-[r]->(:Entity{kg_domain:'memory'}) RETURN COUNT(r) as c"
                )
                mem_edges = r2.single()['c'] if r2.peek() else 0
                r3 = session.run(
                    "MATCH (n:Entity) WHERE coalesce(n.kg_domain,'professional') <> 'memory' RETURN COUNT(n) as c"
                )
                pro_nodes = r3.single()['c'] if r3.peek() else 0
                r4 = session.run(
                    "MATCH (a:Entity)-[r]->(b:Entity) WHERE coalesce(a.kg_domain,'professional') <> 'memory' AND coalesce(b.kg_domain,'professional') <> 'memory' RETURN COUNT(r) as c"
                )
                pro_edges = r4.single()['c'] if r4.peek() else 0
            graphs.append(
                {
                    'id': 'neo4j_memory',
                    'name': 'Neo4j记忆图谱',
                    'type': 'neo4j',
                    'node_count': mem_nodes,
                    'edge_count': mem_edges,
                    'status': 'active',
                }
            )
            graphs.append(
                {
                    'id': 'neo4j_professional',
                    'name': 'Neo4j专业知识图谱',
                    'type': 'neo4j',
                    'node_count': pro_nodes,
                    'edge_count': pro_edges,
                    'status': 'active',
                }
            )

        return {'total_graphs': len(graphs), 'graphs': graphs}

    except Exception as e:
        logger.error(f"获取图列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post('/graphs/{graph_id}/indexes/init')
async def init_indexes(graph_id: str, req: IndexInitRequest):
    try:
        if graph_id != 'neo4j_main' or 'neo4j' not in kg_connections:
            raise HTTPException(status_code=400, detail='不支持的图ID')
        driver = kg_connections['neo4j']
        with driver.session(database=kg_manager.neo4j_database) as session:
            if req.create_constraints:
                try:
                    session.run(
                        'CREATE CONSTRAINT entity_id_unique IF NOT EXISTS FOR (n:Entity) REQUIRE n.id IS UNIQUE'
                    )
                except Exception as e:
                    # 记录异常但不中断流程
                    logger.debug(f"[knowledge_graph_api] Exception: {e}")
            if req.create_indexes:
                try:
                    session.run(
                        'CREATE INDEX entity_type_index IF NOT EXISTS FOR (n:Entity) ON (n.entity_type)'
                    )
                except Exception as e:
                    # 记录异常但不中断流程
                    logger.debug(f"[knowledge_graph_api] Exception: {e}")
                try:
                    session.run(
                        'CREATE INDEX entity_title_index IF NOT EXISTS FOR (n:Entity) ON (n.title)'
                    )
                except Exception as e:
                    # 记录异常但不中断流程
                    logger.debug(f"[knowledge_graph_api] Exception: {e}")
            if req.create_fulltext:
                try:
                    session.run(
                        "CALL db.index.fulltext.create_node_index('entity_text_index', ['Entity'], ['title','description'])"
                    )
                except Exception as e:
                    # 记录异常但不中断流程
                    logger.debug(f"[knowledge_graph_api] Exception: {e}")
        return {'success': True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"初始化索引失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get('/graphs/{graph_id}/indexes')
async def list_indexes(graph_id: str):
    try:
        if graph_id != 'neo4j_main' or 'neo4j' not in kg_connections:
            raise HTTPException(status_code=400, detail='不支持的图ID')
        driver = kg_connections['neo4j']
        with driver.session(database=kg_manager.neo4j_database) as session:
            res = session.run('SHOW INDEXES')
            records = [r.data() for r in res]
            return {'indexes': records}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取索引失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get('/graphs/{graph_id}/schema/constraints')
async def list_constraints(graph_id: str):
    try:
        if graph_id != 'neo4j_main' or 'neo4j' not in kg_connections:
            raise HTTPException(status_code=400, detail='不支持的图ID')
        driver = kg_connections['neo4j']
        with driver.session(database=kg_manager.neo4j_database) as session:
            res = session.run('SHOW CONSTRAINTS')
            records = [r.data() for r in res]
            return {'constraints': records}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取约束失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get('/graphs/{graph_id}/nodes')
async def get_nodes(
    graph_id: str,
    node_type: str | None = None,
    domain: str | None = None,
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
):
    """获取图谱节点"""
    try:
        if (
            graph_id in ('neo4j_main', 'neo4j_memory', 'neo4j_professional')
            and 'neo4j' in kg_connections
        ):
            driver = kg_connections['neo4j']
            nodes = []
            with driver.session(database=kg_manager.neo4j_database) as session:
                where_clauses = []
                params: dict[str, Any] = {'limit': limit, 'offset': offset}
                if graph_id == 'neo4j_memory':
                    where_clauses.append(
                        "coalesce(n.kg_domain,'professional') = 'memory'"
                    )
                elif graph_id == 'neo4j_professional':
                    where_clauses.append(
                        "coalesce(n.kg_domain,'professional') <> 'memory'"
                    )
                    if domain:
                        where_clauses.append('n.kg_domain = $domain')
                        params['domain'] = domain
                if node_type:
                    where_clauses.append('n.entity_type = $type')
                    params['type'] = node_type
                cypher = 'MATCH (n:Entity)'
                if where_clauses:
                    cypher += ' WHERE ' + ' AND '.join(where_clauses)
                cypher += ' RETURN id(n) as id, n.entity_type as type, properties(n) as props LIMIT $limit SKIP $offset'
                result = session.run(cypher, **params)
                for record in result:
                    nodes.append(
                        {
                            'id': str(record['id']),
                            'type': record.get('type') or 'Entity',
                            'properties': record.get('props') or {},
                            'created_at': (record.get('props') or {}).get('created_at'),
                        }
                    )
            return {'graph_id': graph_id, 'nodes': nodes, 'total': len(nodes)}
        return {
            'graph_id': graph_id,
            'nodes': [],
            'message': f"图 {graph_id} 的节点查询功能待实现",
        }

    except Exception as e:
        logger.error(f"获取节点失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get('/graphs/{graph_id}/edges')
async def get_edges(
    graph_id: str,
    edge_type: str | None = None,
    domain: str | None = None,
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
):
    """获取图谱边"""
    try:
        if (
            graph_id in ('neo4j_main', 'neo4j_memory', 'neo4j_professional')
            and 'neo4j' in kg_connections
        ):
            driver = kg_connections['neo4j']
            edges = []
            with driver.session(database=kg_manager.neo4j_database) as session:
                where_clauses = []
                params: dict[str, Any] = {'limit': limit, 'offset': offset}
                if graph_id == 'neo4j_memory':
                    where_clauses.append(
                        "coalesce(a.kg_domain,'professional') = 'memory'"
                    )
                    where_clauses.append(
                        "coalesce(b.kg_domain,'professional') = 'memory'"
                    )
                elif graph_id == 'neo4j_professional':
                    where_clauses.append(
                        "coalesce(a.kg_domain,'professional') <> 'memory'"
                    )
                    where_clauses.append(
                        "coalesce(b.kg_domain,'professional') <> 'memory'"
                    )
                    if domain:
                        where_clauses.append('a.kg_domain = $domain')
                        where_clauses.append('b.kg_domain = $domain')
                        params['domain'] = domain
                if edge_type:
                    where_clauses.append('type(r) = $type')
                    params['type'] = edge_type
                cypher = 'MATCH (a:Entity)-[r]->(b:Entity)'
                if where_clauses:
                    cypher += ' WHERE ' + ' AND '.join(where_clauses)
                cypher += ' RETURN id(r) as id, id(a) as source, id(b) as target, type(r) as type, properties(r) as props LIMIT $limit SKIP $offset'
                result = session.run(cypher, **params)
                for record in result:
                    props = record.get('props') or {}
                    edges.append(
                        {
                            'id': str(record['id']),
                            'source': str(record['source']),
                            'target': str(record['target']),
                            'type': record['type'],
                            'properties': props,
                            'weight': props.get('weight', 1.0),
                            'created_at': props.get('created_at'),
                        }
                    )
            return {'graph_id': graph_id, 'edges': edges, 'total': len(edges)}
        return {
            'graph_id': graph_id,
            'edges': [],
            'message': f"图 {graph_id} 的边查询功能待实现",
        }

    except Exception as e:
        logger.error(f"获取边失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post('/graphs/{graph_id}/search')
async def search_graph(graph_id: str, search: GraphSearch):
    """搜索图谱"""
    try:
        if (
            graph_id in ('neo4j_main', 'neo4j_memory', 'neo4j_professional')
            and 'neo4j' in kg_connections
        ):
            driver = kg_connections['neo4j']
            results = []
            with driver.session(database=kg_manager.neo4j_database) as session:
                where_clauses = []
                params: dict[str, Any] = {'limit': search.limit}
                if graph_id == 'neo4j_memory':
                    where_clauses.append(
                        "coalesce(n.kg_domain,'professional') = 'memory'"
                    )
                elif graph_id == 'neo4j_professional':
                    where_clauses.append(
                        "coalesce(n.kg_domain,'professional') <> 'memory'"
                    )
                    if search.domain:
                        where_clauses.append('n.kg_domain = $domain')
                        params['domain'] = search.domain
                if search.node_type:
                    where_clauses.append('n.entity_type = $type')
                    params['type'] = search.node_type
                cypher = 'MATCH (n:Entity)'
                if where_clauses:
                    cypher += ' WHERE ' + ' AND '.join(where_clauses)
                cypher += ' RETURN id(n) as id, n.entity_type as type, properties(n) as props LIMIT $limit'
                result = session.run(cypher, **params)
                for record in result:
                    props = record.get('props') or {}
                    results.append(
                        {
                            'id': str(record['id']),
                            'type': record.get('type') or 'Entity',
                            'title': props.get('title'),
                            'description': props.get('description'),
                            'properties': props,
                        }
                    )
            return {
                'graph_id': graph_id,
                'query': search.dict(),
                'results': results,
                'total': len(results),
            }
        if graph_id == 'sqlite_main' and 'sqlite' in kg_connections:
            conn = kg_connections['sqlite']
            cursor = conn.cursor()

            # 构建搜索查询
            query_parts = ['SELECT * FROM entities WHERE 1=1']
            params = []

            if search.node_type:
                query_parts.append('type = ?')
                params.append(search.node_type)

            if search.properties:
                for key, value in search.properties.items():
                    query_parts.append('properties LIKE ?')
                    params.append(f"%{key}%{value}%")

            query_parts.append("LIMIT ?")
            params.append(search.limit)

            query = ' AND '.join(query_parts)
            cursor.execute(query, params)

            columns = [description[0] for description in cursor.description]
            results = []

            for row in cursor.fetchall():
                result_dict = dict(zip(columns, row, strict=False))
                results.append(
                    {
                        'id': result_dict.get('id'),
                        'type': result_dict.get('type'),
                        'title': result_dict.get('title'),
                        'description': result_dict.get('description'),
                        'properties': {
                            'category': result_dict.get('category'),
                            'score': 1.0,  # 简单评分
                        },
                    }
                )

            return {
                'graph_id': graph_id,
                'query': search.dict(),
                'results': results,
                'total': len(results),
            }

        else:
            return {
                'graph_id': graph_id,
                'query': search.dict(),
                'results': [],
                'message': f"图 {graph_id} 的搜索功能待实现",
            }

    except Exception as e:
        logger.error(f"图谱搜索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post('/graphs/{graph_id}/query')
async def execute_query(graph_id: str, query: GraphQuery):
    """执行图查询"""
    try:
        if graph_id == 'neo4j_main' and 'neo4j' in kg_connections:
            driver = kg_connections['neo4j']
            with driver.session(database=kg_manager.neo4j_database) as session:
                result = session.run(query.query, **(query.parameters or {}))
                records = [r.data() for r in result]
                return {
                    'graph_id': graph_id,
                    'query': query.query,
                    'type': 'cypher',
                    'results': records,
                    'total': len(records),
                }
        if graph_id == 'sqlite_main' and 'sqlite' in kg_connections:
            conn = kg_connections['sqlite']
            cursor = conn.cursor()

            # 执行SQL查询（简化实现）
            cursor.execute(query.query, (query.parameters or {}))

            if query.query.strip().upper().startswith('SELECT'):
                # 查询操作
                columns = [description[0] for description in cursor.description]
                results = []

                for row in cursor.fetchall():
                    result_dict = dict(zip(columns, row, strict=False))
                    results.append(result_dict)

                return {
                    'graph_id': graph_id,
                    'query': query.query,
                    'type': 'select',
                    'results': results,
                    'total': len(results),
                }
            else:
                # 更新操作
                conn.commit()
                return {
                    'graph_id': graph_id,
                    'query': query.query,
                    'type': 'update',
                    'affected_rows': cursor.rowcount,
                }

        else:
            return {
                'graph_id': graph_id,
                'query': query.query,
                'results': [],
                'message': f"图 {graph_id} 的查询功能待实现",
            }

    except Exception as e:
        logger.error(f"执行查询失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get('/graphs/{graph_id}/statistics')
async def get_graph_statistics(graph_id: str):
    """获取图谱统计信息"""
    try:
        if graph_id == 'neo4j_main' and 'neo4j' in kg_connections:
            driver = kg_connections['neo4j']
            with driver.session(database=kg_manager.neo4j_database) as session:
                node_types = {}
                relation_types = {}
                res1 = session.run(
                    'MATCH (n) RETURN n.entity_type as type, COUNT(n) as count'
                )
                for r in res1:
                    node_types[r['type']] = r['count']
                res2 = session.run(
                    'MATCH ()-[r]->() RETURN type(r) as type, COUNT(r) as count'
                )
                for r in res2:
                    relation_types[r['type']] = r['count']
                return {
                    'graph_id': graph_id,
                    'total_nodes': sum(node_types.values()),
                    'total_edges': sum(relation_types.values()),
                    'node_types': node_types,
                    'relation_types': relation_types,
                    'last_updated': datetime.now().isoformat(),
                }
        if graph_id == 'sqlite_main' and 'sqlite' in kg_connections:
            conn = kg_connections['sqlite']
            cursor = conn.cursor()

            # 节点统计
            cursor.execute('SELECT type, COUNT(*) FROM entities GROUP BY type')
            node_types = dict(cursor.fetchall())

            # 关系统计
            cursor.execute('SELECT type, COUNT(*) FROM relations GROUP BY type')
            relation_types = dict(cursor.fetchall())

            return {
                'graph_id': graph_id,
                'total_nodes': sum(node_types.values()),
                'total_edges': sum(relation_types.values()),
                'node_types': node_types,
                'relation_types': relation_types,
                'last_updated': datetime.now().isoformat(),
            }

        else:
            return {
                'graph_id': graph_id,
                'total_nodes': 0,
                'total_edges': 0,
                'node_types': {},
                'relation_types': {},
                'message': f"图 {graph_id} 的统计信息待实现",
            }

    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get('/node-types')
async def get_node_types():
    """获取节点类型列表"""
    return {
        'node_types': [nt.value for nt in NodeType],
        'descriptions': {
            'patent': '专利',
            'technology': '技术',
            'company': '公司',
            'inventor': '发明人',
            'category': '分类',
            'keyword': '关键词',
            'legal_case': '法律案例',
            'prior_art': '现有技术',
        },
    }


@app.get('/relation-types')
async def get_relation_types():
    """获取关系类型列表"""
    return {
        'relation_types': [rt.value for rt in RelationType],
        'descriptions': {
            'cites': '引用',
            'similar_to': '相似',
            'invented_by': '发明',
            'assigned_to': '转让',
            'belongs_to': '属于',
            'related_to': '相关',
            'precedes': '先于',
            'improves': '改进',
        },
    }


@app.post('/graphs/{graph_id}/path')
async def find_path(graph_id: str, pq: PathQuery):
    try:
        if graph_id != 'neo4j_main' or 'neo4j' not in kg_connections:
            raise HTTPException(status_code=400, detail='不支持的图ID')
        depth = max(1, min((pq.max_depth or 5), 10))
        pattern = f"[*..{depth}]"
        driver = kg_connections['neo4j']
        with driver.session(database=kg_manager.neo4j_database) as session:
            cypher = (
                'MATCH (a:Entity {id: $source}), (b:Entity {id: $target}) '
                f"MATCH p = shortest_path((a)-{pattern}->(b)) "
                'RETURN p LIMIT 1'
            )
            res = session.run(cypher, source=pq.source, target=pq.target)
            rec = res.single()
            if not rec:
                return {'path': None}
            path = rec[0]
            nodes = [n.get('id') for n in path.nodes]
            rels = [type(r).__name__ for r in path.relationships]
            return {'nodes': nodes, 'relationships': rels}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"路径查询失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post('/graphs/{graph_id}/neighbors')
async def neighbors(graph_id: str, nq: NeighborsQuery):
    try:
        if graph_id != 'neo4j_main' or 'neo4j' not in kg_connections:
            raise HTTPException(status_code=400, detail='不支持的图ID')
        depth = max(1, min((nq.max_depth or 2), 5))
        driver = kg_connections['neo4j']
        with driver.session(database=kg_manager.neo4j_database) as session:
            if nq.relation_types:
                rt = '|'.join([t.upper() for t in nq.relation_types])
                hop = f"[:{rt}*..{depth}]"
            else:
                hop = f"[*..{depth}]"
            filter_clause = ''
            if nq.node_type_filter:
                filter_clause = ' WHERE n.entity_type = $type_filter'
            cypher = (
                'MATCH (a:Entity {id: $id})'
                f"MATCH (a)-{hop}->(n)"
                + filter_clause
                + ' RETURN DISTINCT id(n) as id, n.entity_type as type, properties(n) as props LIMIT 200'
            )
            res = session.run(cypher, id=nq.id, type_filter=nq.node_type_filter)
            out = []
            for r in res:
                out.append(
                    {
                        'id': str(r['id']),
                        'type': r.get('type'),
                        'properties': r.get('props') or {},
                    }
                )
            return {'neighbors': out, 'count': len(out)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"邻居查询失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post('/graphs/{graph_id}/search/fulltext')
async def fulltext_search(graph_id: str, req: FullTextSearchRequest):
    try:
        if graph_id != 'neo4j_main' or 'neo4j' not in kg_connections:
            raise HTTPException(status_code=400, detail='不支持的图ID')
        driver = kg_connections['neo4j']
        with driver.session(database=kg_manager.neo4j_database) as session:
            res = session.run(
                "CALL db.index.fulltext.query_nodes('entity_text_index', $q) YIELD node, score RETURN id(node) as id, node.entity_type as type, node.title as title, node.description as description, score LIMIT $limit",
                q=req.q,
                limit=req.limit,
            )
            results = []
            for r in res:
                results.append(
                    {
                        'id': str(r['id']),
                        'type': r.get('type'),
                        'title': r.get('title'),
                        'description': r.get('description'),
                        'score': r.get('score'),
                    }
                )
            return {'results': results, 'total': len(results)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"全文检索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post('/graphs/{graph_id}/node')
async def create_node(graph_id: str, node: GraphNode):
    """创建节点"""
    try:
        if graph_id == 'neo4j_main' and 'neo4j' in kg_connections:
            driver = kg_connections['neo4j']
            with driver.session(database=kg_manager.neo4j_database) as session:
                cypher = (
                    'MERGE (n:Entity {id: $id}) '
                    'SET n.entity_type = $type, n.created_at = $created_at '
                    'SET n += $props'
                )
                session.run(
                    cypher,
                    id=node.id,
                    type=node.type,
                    created_at=(node.created_at or datetime.now().isoformat()),
                    props=node.properties or {},
                )
            return {
                'success': True,
                'node_id': node.id,
                'graph_id': graph_id,
                'message': '节点创建成功',
            }
        if graph_id == 'sqlite_main' and 'sqlite' in kg_connections:
            conn = kg_connections['sqlite']
            cursor = conn.cursor()

            cursor.execute(
                """INSERT INTO entities (id, type, title, description, properties, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    node.id,
                    node.type,
                    node.properties.get('title', ''),
                    node.properties.get('description', ''),
                    json.dumps(node.properties),
                    node.created_at or datetime.now(),
                ),
            )

            conn.commit()

            return {
                'success': True,
                'node_id': node.id,
                'graph_id': graph_id,
                'message': '节点创建成功',
            }

        else:
            raise HTTPException(status_code=501, detail=f"图 {graph_id} 不支持节点创建")

    except Exception as e:
        logger.error(f"创建节点失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post('/graphs/{graph_id}/edge')
async def create_edge(graph_id: str, edge: GraphEdge):
    """创建边"""
    try:
        if graph_id == 'neo4j_main' and 'neo4j' in kg_connections:
            driver = kg_connections['neo4j']
            rel_type = (edge.type or 'RELATED_TO').upper()
            with driver.session(database=kg_manager.neo4j_database) as session:
                cypher = (
                    'MATCH (a:Entity {id: $source}) MATCH (b:Entity {id: $target}) '
                    f"MERGE (a)-[r:{rel_type}]->(b) "
                    'SET r.weight = $weight, r.created_at = $created_at '
                    'SET r += $props'
                )
                session.run(
                    cypher,
                    source=edge.source,
                    target=edge.target,
                    weight=edge.weight or 1.0,
                    created_at=(edge.created_at or datetime.now().isoformat()),
                    props=edge.properties or {},
                )
            return {
                'success': True,
                'edge_id': edge.id,
                'graph_id': graph_id,
                'message': '边创建成功',
            }
        if graph_id == 'sqlite_main' and 'sqlite' in kg_connections:
            conn = kg_connections['sqlite']
            cursor = conn.cursor()

            cursor.execute(
                """INSERT INTO relations (id, source_id, target_id, type, properties, weight, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    edge.id,
                    edge.source,
                    edge.target,
                    edge.type,
                    json.dumps(edge.properties),
                    edge.weight,
                    edge.created_at or datetime.now(),
                ),
            )

            conn.commit()

            return {
                'success': True,
                'edge_id': edge.id,
                'graph_id': graph_id,
                'message': '边创建成功',
            }

        else:
            raise HTTPException(status_code=501, detail=f"图 {graph_id} 不支持边创建")

    except Exception as e:
        logger.error(f"创建边失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


if __name__ == '__main__':
    logger.info('🚀 启动Athena知识图谱API服务')
    logger.info('📍 服务地址: http://localhost:9030')
    logger.info('📊 健康检查: http://localhost:9030/health')
    logger.info('📖 API文档: http://localhost:9030/docs')
    logger.info('')

    uvicorn.run(
        'knowledge_graph_api:app',
        host='0.0.0.0',
        port=9030,
        reload=False,
        log_level='info',
    )
