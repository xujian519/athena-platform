#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Athena优化版知识图谱API服务
Optimized Knowledge Graph API Service

包含查询缓存、分页、流式处理和性能优化

作者: Athena AI系统
创建时间: 2025-12-08
版本: 2.0.0
"""

import asyncio
import hashlib
import json
import logging
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import lru_cache, wraps
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query

# 导入统一认证模块
from concurrent.futures import ThreadPoolExecutor

import redis
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from neo4j import GraphDatabase
from pydantic import BaseModel, Field

from shared.auth.auth_middleware import create_auth_middleware, setup_cors

    FASTAPI_AVAILABLE = True
except ImportError as e:
    logger.info(f"⚠️ 依赖库未安装: {e}")
    logger.info('请运行: pip install fastapi uvicorn neo4j redis')
    FASTAPI_AVAILABLE = False

# 配置常量
CACHE_TTL = 300  # 缓存5分钟
MAX_PAGE_SIZE = 1000
DEFAULT_PAGE_SIZE = 50
QUERY_TIMEOUT = 30  # 秒

@dataclass
class QueryParams:
    """查询参数"""
    skip: int = Field(default=0, ge=0, description='跳过记录数')
    limit: int = Field(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description='返回记录数')
    order_by: Optional[str] = Field(default=None, description='排序字段')
    order_direction: str = Field(default='ASC', pattern='^(ASC|DESC)$', description='排序方向')

@dataclass
class CacheConfig:
    """缓存配置"""
    enabled: bool = True
    ttl: int = CACHE_TTL
    max_size: int = 1000

class QueryCache:
    """查询缓存管理器"""

    def __init__(self, config: CacheConfig = None):
        self.config = config or CacheConfig()
        self._cache = {}
        self._timestamps = {}

    def _generate_key(self, query: str, params: Dict = None) -> str:
        """生成缓存键"""
        content = f"{query}:{json.dumps(params or {}, sort_keys=True)}"
        return hashlib.md5(content.encode('utf-8'), usedforsecurity=False).hexdigest()

    def get(self, query: str, params: Dict = None) -> Any | None:
        """获取缓存结果"""
        if not self.config.enabled:
            return None

        key = self._generate_key(query, params)

        # 检查是否过期
        if key in self._timestamps:
            if time.time() - self._timestamps[key] > self.config.ttl:
                self.invalidate(key)
                return None

        return self._cache.get(key)

    def set(self, query: str, result: Any, params: Dict = None) -> None:
        """设置缓存结果"""
        if not self.config.enabled:
            return

        key = self._generate_key(query, params)

        # LRU策略：如果缓存满了，删除最旧的条目
        if len(self._cache) >= self.config.max_size:
            oldest_key = min(self._timestamps.keys(), key=lambda k: self._timestamps[k])
            self.invalidate(oldest_key)

        self._cache[key] = result
        self._timestamps[key] = time.time()

    def invalidate(self, key: str = None) -> None:
        """删除缓存条目"""
        if key:
            self._cache.pop(key, None)
            self._timestamps.pop(key, None)
        else:
            # 清空所有缓存
            self._cache.clear()
            self._timestamps.clear()

    def cleanup_expired(self) -> int:
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = [
            key for key, timestamp in self._timestamps.items()
            if current_time - timestamp > self.config.ttl
        ]

        for key in expired_keys:
            self.invalidate(key)

        return len(expired_keys)

class OptimizedNodeResponse(BaseModel):
    """优化的节点响应模型"""
    id: str
    labels: List[str]
    properties: Dict[str, Any]
    degree: int | None = None  # 节点度数

class OptimizedRelationshipResponse(BaseModel):
    """优化的关系响应模型"""
    id: str
    type: str
    start_node: str
    end_node: str
    properties: Dict[str, Any]
    weight: float | None = None

class PaginatedResponse(BaseModel):
    """分页响应模型"""
    items: List[Any]
    total: int
    skip: int
    limit: int
    has_next: bool
    has_prev: bool
    execution_time: float

class OptimizedQueryResponse(BaseModel):
    """优化的查询响应模型"""
    nodes: List[OptimizedNodeResponse]
    relationships: List[OptimizedRelationshipResponse]
    query: str
    execution_time: float
    cache_hit: bool = False

class OptimizedKnowledgeGraphAPI:
    """优化版知识图谱API服务"""

    def __init__(self):
        self.app = None
        self.driver = None
        self.cache = QueryCache()
        self.executor = ThreadPoolExecutor(max_workers=10)

        if FASTAPI_AVAILABLE:
            self.app = FastAPI(
                title='Athena优化版知识图谱API',
                description='高性能知识图谱查询和管理服务',
                version='2.0.0',
                docs_url='/docs',
                redoc_url='/redoc'
            )
            self.setup_middleware()
            self.setup_routes()
            self.setup_neo4j()
            self.setup_background_tasks()

    def setup_middleware(self):
        """设置中间件"""

    def setup_neo4j(self):
        """设置Neo4j连接"""
        try:
            self.driver = GraphDatabase.driver(
                'bolt://localhost:7687',
                auth=('neo4j', 'password'),
                max_connection_lifetime=30 * 60,  # 30分钟
                max_connection_pool_size=50,
                connection_acquisition_timeout=60  # 60秒
            )
            logger.info('✅ Neo4j连接成功（优化配置）')
        except Exception as e:
            logger.info(f"❌ Neo4j连接失败: {str(e)}")
            self.driver = None

    def setup_background_tasks(self):
        """设置后台任务"""
        @self.app.on_event('startup')
        async def startup_event():
            # 启动缓存清理任务
            asyncio.create_task(self.cache_cleanup_task())

    async def cache_cleanup_task(self):
        """缓存清理后台任务"""
        while True:
            try:
                await asyncio.sleep(60)  # 每分钟清理一次
                expired_count = self.cache.cleanup_expired()
                if expired_count > 0:
                    logger.info(f"🧹 清理了 {expired_count} 个过期缓存条目")
            except Exception as e:
                logger.info(f"⚠️ 缓存清理任务错误: {e}")

    def cache_query_result(self):
        """查询结果缓存装饰器"""
        def decorator(func):
            @wraps(func)
            def wrapper(query: str, *args, **kwargs):
                # 检查缓存
                cache_params = kwargs.get('params', {})
                cached_result = self.cache.get(query, cache_params)

                if cached_result:
                    cached_result['cache_hit'] = True
                    return cached_result

                # 执行查询
                start_time = time.time()
                result = func(query, *args, **kwargs)
                execution_time = time.time() - start_time

                # 添加执行时间
                if isinstance(result, dict):
                    result['execution_time'] = execution_time

                # 缓存结果（仅缓存小结果集）
                if isinstance(result, dict) and result.get('total', 0) < 1000:
                    self.cache.set(query, result, cache_params)

                result['cache_hit'] = False
                return result

            return wrapper
        return decorator

    def setup_routes(self):
        """设置路由"""

        @self.app.get('/')
        async def root():
            return {
                'message': 'Athena优化版知识图谱API',
                'version': '2.0.0',
                'status': 'running',
                'features': [
                    '查询缓存',
                    '分页支持',
                    '流式处理',
                    '性能优化'
                ],
                'timestamp': datetime.now().isoformat()
            }

        @self.app.get('/health')
        async def health_check():
            """健康检查"""
            neo4j_status = 'connected' if self.driver else 'disconnected'
            cache_stats = {
                'cache_size': len(self.cache._cache),
                'cache_enabled': self.cache.config.enabled
            }

            return {
                'status': 'healthy',
                'neo4j': neo4j_status,
                'cache': cache_stats,
                'timestamp': datetime.now().isoformat()
            }

        @self.app.get('/nodes', response_model=PaginatedResponse)
        async def get_nodes_paginated(
            params: QueryParams = Depends(),
            label: Optional[str] = Query(None, description='节点标签过滤')
        ):
            """分页获取节点列表"""
            if not self.driver:
                raise HTTPException(status_code=503, detail='Neo4j未连接')

            start_time = time.time()

            # 构建查询
            if label:
                count_query = f"MATCH (n:{label}) RETURN count(n) as total"
                data_query = f"MATCH (n:{label}) RETURN n SKIP $skip LIMIT $limit"
            else:
                count_query = 'MATCH (n) RETURN count(n) as total'
                data_query = 'MATCH (n) RETURN n SKIP $skip LIMIT $limit'

            # 添加排序
            if params.order_by:
                order_clause = f"ORDER BY n.{params.order_by} {params.order_direction}"
                data_query = data_query.replace('SKIP $skip', f"{order_clause} SKIP $skip")

            try:
                with self.driver.session() as session:
                    # 获取总数
                    count_result = session.run(count_query)
                    total = count_result.single()['total']

                    # 获取分页数据
                    data_result = session.run(
                        data_query,
                        skip=params.skip,
                        limit=params.limit
                    )

                    nodes = []
                    for record in data_result:
                        node = record['n']
                        nodes.append(OptimizedNodeResponse(
                            id=str(node.id),
                            labels=list(node.labels),
                            properties=dict(node),
                            degree=self._get_node_degree(str(node.id))
                        ))

                    execution_time = time.time() - start_time

                    return PaginatedResponse(
                        items=nodes,
                        total=total,
                        skip=params.skip,
                        limit=params.limit,
                        has_next=params.skip + params.limit < total,
                        has_prev=params.skip > 0,
                        execution_time=execution_time
                    )

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"查询执行失败: {str(e)}")

        @self.app.get('/nodes/stream')
        async def stream_nodes(
            label: Optional[str] = Query(None, description='节点标签过滤'),
            batch_size: int = Query(100, ge=1, le=1000, description='批次大小')
        ):
            """流式获取节点"""
            if not self.driver:
                raise HTTPException(status_code=503, detail='Neo4j未连接')

            async def generate():
                try:
                    with self.driver.session() as session:
                        if label:
                            query = f"MATCH (n:{label}) RETURN n"
                        else:
                            query = 'MATCH (n) RETURN n'

                        result = session.run(query)
                        batch = []

                        for record in result:
                            node = record['n']
                            node_data = OptimizedNodeResponse(
                                id=str(node.id),
                                labels=list(node.labels),
                                properties=dict(node)
                            )
                            batch.append(node_data.dict())

                            if len(batch) >= batch_size:
                                yield f"data: {json.dumps(batch)}\\n\\n"
                                batch = []

                        # 发送剩余数据
                        if batch:
                            yield f"data: {json.dumps(batch)}\\n\\n"

                        yield "data: [DONE]\\n\\n"

                except Exception as e:
                    yield f"data: {{'error': '{str(e)}'}}\\n\\n"

            return StreamingResponse(
                generate(),
                media_type='text/plain',
                headers={'Cache-Control': 'no-cache'}
            )

        @self.app.post('/query', response_model=OptimizedQueryResponse)
        async def execute_optimized_cypher(query_data: Dict[str, Any]):
            """执行优化的Cypher查询"""
            if not self.driver:
                raise HTTPException(status_code=503, detail='Neo4j未连接')

            query = query_data.get('query', '')
            if not query:
                raise HTTPException(status_code=400, detail='查询语句不能为空')

            # 安全检查
            dangerous_keywords = ['DELETE', 'DROP', 'REMOVE', 'CREATE', 'MERGE']
            query_upper = query.upper()
            for keyword in dangerous_keywords:
                if keyword in query_upper:
                    raise HTTPException(
                        status_code=400,
                        detail=f"不允许使用{keyword}操作"
                    )

            # 提取参数
            params = query_data.get('parameters', {})

            try:
                # 使用缓存装饰器执行查询
                result = self._execute_cached_query(query, params)

                return OptimizedQueryResponse(**result)

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"查询执行失败: {str(e)}"
                )

        @self.app.get('/statistics')
        async def get_optimized_statistics():
            """获取优化的统计信息"""
            if not self.driver:
                raise HTTPException(status_code=503, detail='Neo4j未连接')

            cache_key = 'kg_statistics'

            # 检查缓存
            cached_stats = self.cache.get(cache_key)
            if cached_stats:
                return {
                    **cached_stats,
                    'cache_hit': True,
                    'timestamp': datetime.now().isoformat()
                }

            try:
                with self.driver.session() as session:
                    # 并行执行多个统计查询
                    futures = {
                        'nodes': self.executor.submit(
                            session.run, 'MATCH (n) RETURN labels(n) as label, count(n) as count'
                        ),
                        'relationships': self.executor.submit(
                            session.run, 'MATCH ()-[r]->() RETURN type(r) as type, count(r) as count'
                        ),
                        'density': self.executor.submit(
                            session.run, """
                            MATCH (n)
                            WITH count(n) as nodes
                            MATCH ()-[r]->()
                            WITH nodes, count(r) as rels
                            RETURN to_float(rels) / (to_float(nodes) * (to_float(nodes) - 1)) as density
                            """
                        )
                    }

                    # 收集结果
                    node_stats = {}
                    for record in futures['nodes'].result():
                        label = record['label'][0] if record['label'] else 'Unknown'
                        node_stats[label] = record['count']

                    rel_stats = {}
                    for record in futures['relationships'].result():
                        rel_stats[record['type']] = record['count']

                    density = 0.0
                    density_record = list(futures['density'].result())
                    if density_record:
                        density = density_record[0]['density']

                    stats = {
                        'node_statistics': node_stats,
                        'relationship_statistics': rel_stats,
                        'total_nodes': sum(node_stats.values()),
                        'total_relationships': sum(rel_stats.values()),
                        'graph_density': density,
                        'cache_stats': {
                            'cache_size': len(self.cache._cache),
                            'cache_enabled': self.cache.config.enabled
                        }
                    }

                    # 缓存结果
                    self.cache.set(cache_key, stats)

                    return {
                        **stats,
                        'cache_hit': False,
                        'timestamp': datetime.now().isoformat()
                    }

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"统计信息获取失败: {str(e)}"
                )

        @self.app.delete('/cache')
        async def clear_cache():
            """清空缓存"""
            self.cache.invalidate()
            return {
                'message': '缓存已清空',
                'timestamp': datetime.now().isoformat()
            }

    def _execute_cached_query(self, query: str, params: Dict) -> Dict:
        """执行缓存查询"""
        @self.cache_query_result()
        def _execute(query: str, params: Dict = None):
            start_time = time.time()

            with self.driver.session() as session:
                result = session.run(query, **params)

                nodes = []
                relationships = []

                for record in result:
                    for key, value in record.items():
                        if hasattr(value, 'labels'):  # Neo4j节点
                            nodes.append(OptimizedNodeResponse(
                                id=str(value.id),
                                labels=list(value.labels),
                                properties=dict(value)
                            ))
                        elif hasattr(value, 'type'):  # Neo4j关系
                            relationships.append(OptimizedRelationshipResponse(
                                id=str(value.id),
                                type=value.type,
                                start_node=str(value.start_node.id),
                                end_node=str(value.end_node.id),
                                properties=dict(value)
                            ))

                return {
                    'nodes': [n.dict() for n in nodes],
                    'relationships': [r.dict() for r in relationships],
                    'query': query,
                    'execution_time': time.time() - start_time
                }

        return _execute(query, params)

    def _get_node_degree(self, node_id: str) -> int:
        """获取节点度数"""
        try:
            with self.driver.session() as session:
                result = session.run(
                    'MATCH (n)-[r]-(m) WHERE id(n) = $node_id RETURN count(r) as degree',
                    node_id=int(node_id)
                )
                return result.single()['degree']
        except:
            return 0

    def run(self, host: str = '0.0.0.0', port: int = 8087):
        """运行优化版API服务"""
        if not FASTAPI_AVAILABLE:
            logger.info('❌ 依赖库未安装，无法启动服务')
            return False

        if not self.driver:
            logger.info('❌ Neo4j未连接，请确保Neo4j服务正在运行')
            return False

        logger.info('🚀 启动Athena优化版知识图谱API服务')
        logger.info(f"📍 服务地址: http://{host}:{port}")
        logger.info('📚 API文档: http://{host}:{port}/docs')
        logger.info('🔍 健康检查: http://{host}:{port}/health')
        logger.info('⚡ 优化特性: 查询缓存、分页、流式处理、性能优化')

        try:
            uvicorn.run(
                self.app,
                host=host,
                port=port,
                workers=1,  # 单worker模式，避免连接池冲突
                loop='asyncio'
            )
            return True
        except Exception as e:
            logger.info(f"❌ 启动失败: {str(e)}")
            return False

def main():
    """主函数"""
    api_service = OptimizedKnowledgeGraphAPI()
    success = api_service.run(port=8087)

    if not success:
        logger.info("\\n💡 请确保:")
        logger.info('1. 安装依赖: pip install fastapi uvicorn neo4j redis')
        logger.info('2. 启动Neo4j: neo4j start')
        logger.info('3. 检查端口: 确保端口8087未被占用')

if __name__ == '__main__':
    main()