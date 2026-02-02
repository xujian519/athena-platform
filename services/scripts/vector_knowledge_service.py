#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量检索和知识图谱API服务
Vector Retrieval and Knowledge Graph API Service

统一的向量搜索和知识图谱查询API
"""

# Numpy兼容性导入
from config.numpy_compatibility import array, zeros, ones, random, mean, sum, dot
import asyncio
from core.async_main import async_main
import json
import logging
from core.logging_config import setup_logging
import os

# 添加项目路径
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 导入统一认证模块
from shared.auth.auth_middleware import create_auth_middleware, setup_cors

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.vector.qdrant_adapter import QdrantVectorAdapter

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

# 创建FastAPI应用
app = FastAPI(
    title='Vector & Knowledge API Service',
    description='向量检索和知识图谱API服务',
    version='1.0.0'
)

# CORS配置

# 全局变量
vector_adapter = None

# 请求模型
class VectorSearchRequest(BaseModel):
    query: str
    collection_type: str
    limit: int = 10
    threshold: float = 0.3

class VectorSearchResponse(BaseModel):
    status: str
    results: List[Dict[str, Any]]
    query_time: float
    total_results: int

class HealthResponse(BaseModel):
    status: str
    service: str
    collections: List[str]
    qdrant_status: str

# 初始化
async def initialize_services():
    """初始化服务"""
    global vector_adapter
    
    try:
        # 初始化Qdrant适配器
        vector_adapter = QdrantVectorAdapter()
        logger.info('✅ Qdrant适配器初始化成功')
        
    except Exception as e:
        logger.error(f"❌ 服务初始化失败: {e}")
        raise

@app.on_event('startup')
async def startup_event():
    """应用启动事件"""
    logger.info('🚀 正在启动向量检索和知识图谱API服务...')
    await initialize_services()
    logger.info('✅ 服务启动完成')

@app.on_event('shutdown')
async def shutdown_event():
    """应用关闭事件"""
    logger.info('🔄 正在关闭服务...')

@app.get('/', response_model=Dict[str, Any])
async def root():
    """根路径"""
    return {
        'service': 'vector-knowledge-api',
        'status': 'running',
        'version': '1.0.0',
        'description': '向量检索和知识图谱API服务',
        'endpoints': [
            '/health',
            '/api/v1/vector/search',
            '/api/v1/collections',
            '/api/v1/collections/{collection_name}'
        ]
    }

@app.get('/health', response_model=HealthResponse)
async def health_check():
    """健康检查"""
    try:
        # 检查Qdrant连接
        collections = vector_adapter.client.get_collections().collections
        collection_names = [col.name for col in collections]
        
        return HealthResponse(
            status='healthy',
            service='vector-knowledge-api',
            collections=collection_names,
            qdrant_status='connected'
        )
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=503, detail='服务不可用')

@app.get('/api/v1/collections', response_model=Dict[str, Any])
async def list_collections():
    """列出所有向量集合"""
    try:
        collections = vector_adapter.client.get_collections().collections
        
        collection_info = []
        for col in collections:
            try:
                col_details = vector_adapter.client.get_collection(col.name)
                collection_info.append({
                    'name': col.name,
                    'vectors_count': col_details.points_count,
                    'status': 'active'
                })
            except Exception as e:
                collection_info.append({
                    'name': col.name,
                    'status': f"error: {str(e)}"
                })
        
        return {
            'status': 'success',
            'collections': collection_info,
            'total_collections': len(collection_info)
        }
    except Exception as e:
        logger.error(f"获取集合列表失败: {e}")
        raise HTTPException(status_code=500, detail='获取集合列表失败')

@app.get('/api/v1/collections/{collection_name}')
async def get_collection_info(collection_name: str):
    """获取指定集合信息"""
    try:
        collection = vector_adapter.client.get_collection(collection_name)
        
        return {
            'status': 'success',
            'collection': {
                'name': collection_name,
                'vectors_count': collection.points_count,
                'config': {
                    'vector_size': collection.config.params.vectors.size,
                    'distance': collection.config.params.vectors.distance
                }
            }
        }
    except Exception as e:
        logger.error(f"获取集合信息失败: {e}")
        raise HTTPException(status_code=404, detail='集合不存在')

@app.post('/api/v1/vector/search', response_model=VectorSearchResponse)
async def search_vectors(request: VectorSearchRequest):
    """向量搜索"""
    start_time = datetime.now()
    
    try:
        # 简单的文本到向量转换（这里应该使用实际的嵌入模型）
        import numpy as np
        query_vector = random((1024)).tolist()
        
        # 执行搜索
        results = await vector_adapter.search_vectors(
            collection_type=request.collection_type,
            query_vector=query_vector,
            limit=request.limit,
            threshold=request.threshold
        )
        
        # 计算查询时间
        query_time = (datetime.now() - start_time).total_seconds()
        
        return VectorSearchResponse(
            status='success',
            results=results,
            query_time=query_time,
            total_results=len(results)
        )
        
    except Exception as e:
        logger.error(f"向量搜索失败: {e}")
        raise HTTPException(status_code=500, detail='搜索失败')

@app.post('/api/v1/vector/add')
async def add_vectors(collection_type: str, vectors: List[Dict[str, Any]]):
    """添加向量"""
    try:
        success = await vector_adapter.add_vectors(collection_type, vectors)
        
        if success:
            return {
                'status': 'success',
                'message': f"成功添加 {len(vectors)} 个向量到集合 {collection_type}"
            }
        else:
            raise HTTPException(status_code=500, detail='添加向量失败')
            
    except Exception as e:
        logger.error(f"添加向量失败: {e}")
        raise HTTPException(status_code=500, detail='添加向量失败')

@app.get('/api/v1/knowledge/graph/status')
async def knowledge_graph_status():
    """知识图谱状态"""
    # 简化的知识图谱状态检查
    try:
        return {
            'status': 'active',
            'graph_database': 'TuGraph',
            'nodes_count': '未知',
            'relationships_count': '未知',
            'last_updated': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"知识图谱状态检查失败: {e}")
        raise HTTPException(status_code=500, detail='知识图谱状态检查失败')

@app.get('/api/v1/stats')
async def get_service_stats():
    """获取服务统计信息"""
    try:
        collections = vector_adapter.client.get_collections().collections
        
        stats = {
            'service': 'vector-knowledge-api',
            'uptime': '运行中',
            'total_collections': len(collections),
            'available_collections': [col.name for col in collections],
            'qdrant_connection': '正常',
            'timestamp': datetime.now().isoformat()
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail='获取统计信息失败')

if __name__ == '__main__':
    logger.info('🚀 启动向量和知识图谱API服务...')
    uvicorn.run(
        'vector_knowledge_service:app',
        host='0.0.0.0',
        port=8085,
        reload=True,
        log_level='info'
    )