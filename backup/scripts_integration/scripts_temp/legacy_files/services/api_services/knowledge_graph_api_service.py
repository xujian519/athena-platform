#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识图谱API服务
Knowledge Graph API Service

基于SQLite的知识图谱RESTful API服务
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# 添加项目路径
sys.path.append('/Users/xujian/Athena工作平台')

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

# 导入知识图谱管理器
from sqlite_knowledge_graph_manager import get_knowledge_graph_manager

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 初始化FastAPI应用
app = FastAPI(
    title='Athena知识图谱API',
    description='基于SQLite的企业级知识图谱查询和管理服务',
    version='1.0.0',
    docs_url='/docs',
    redoc_url='/redoc'
)

# 全局知识图谱管理器
kg_manager = None

# API数据模型
class EntityRequest(BaseModel):
    """实体请求模型"""
    name: str
    entity_type: str
    confidence: float = 1.0
    source: str | None = None
    properties: Optional[Dict[str, Any]] = None

class RelationRequest(BaseModel):
    """关系请求模型"""
    source_id: int
    target_id: int
    relation_type: str
    confidence: float = 1.0
    properties: Optional[Dict[str, Any]] = None

class EntitySearchRequest(BaseModel):
    """实体搜索请求模型"""
    query: str
    entity_type: str | None = None
    limit: int = 100

class PathFindRequest(BaseModel):
    """路径查找请求模型"""
    source_id: int
    target_id: int
    max_depth: int = 5

# 启动时初始化
@app.on_event('startup')
async def startup_event():
    """应用启动时初始化知识图谱管理器"""
    global kg_manager
    try:
        kg_manager = get_knowledge_graph_manager()
        logger.info('✅ 知识图谱API服务启动成功')
    except Exception as e:
        logger.error(f"❌ 知识图谱API服务启动失败: {e}")
        raise

# 关闭时清理
@app.on_event('shutdown')
async def shutdown_event():
    """应用关闭时清理资源"""
    global kg_manager
    if kg_manager:
        kg_manager.close()
        logger.info('🔒 知识图谱API服务已关闭')

# API端点
@app.get('/')
async def root():
    """根端点，返回服务信息"""
    return {
        'service': 'Athena知识图谱API',
        'version': '1.0.0',
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
        'endpoints': {
            'health': '/health',
            'statistics': '/api/v1/stats',
            'search_entities': '/api/v1/entities/search',
            'get_entity': '/api/v1/entities/{entity_id}',
            'get_relations': '/api/v1/entities/{entity_id}/relations',
            'find_path': '/api/v1/path/find',
            'export_subgraph': '/api/v1/subgraph/export'
        }
    }

@app.get('/health')
async def health_check():
    """健康检查端点"""
    try:
        stats = kg_manager.get_statistics()
        return {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': {
                'total_entities': stats.get('total_entities', 0),
                'total_relations': stats.get('total_relations', 0)
            }
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=503, detail='Service unavailable')

@app.get('/api/v1/stats')
async def get_statistics():
    """获取知识图谱统计信息"""
    try:
        stats = kg_manager.get_statistics()
        return {
            'success': True,
            'data': stats,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/api/v1/entities/search')
async def search_entities(request: EntitySearchRequest):
    """搜索实体"""
    try:
        results = kg_manager.search_entities(
            query=request.query,
            entity_type=request.entity_type,
            limit=request.limit
        )
        return {
            'success': True,
            'data': {
                'query': request.query,
                'entity_type': request.entity_type,
                'results': results,
                'total': len(results)
            },
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"搜索实体失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/api/v1/entities/{entity_id}')
async def get_entity(entity_id: int):
    """获取单个实体信息"""
    try:
        results = kg_manager.search_entities(query=str(entity_id), limit=1)
        if not results:
            raise HTTPException(status_code=404, detail='Entity not found')

        entity = results[0]
        relations = kg_manager.get_entity_relations(entity_id)

        return {
            'success': True,
            'data': {
                'entity': entity,
                'relations': relations,
                'relation_count': len(relations)
            },
            'timestamp': datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实体信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/api/v1/entities/{entity_id}/relations')
async def get_entity_relations(
    entity_id: int,
    relation_type: Optional[str] = Query(None, description='关系类型过滤'),
    direction: str = Query('both', description='关系方向: outgoing, incoming, both')
):
    """获取实体的关系"""
    try:
        if direction not in ['outgoing', 'incoming', 'both']:
            raise HTTPException(status_code=400, detail='Invalid direction parameter')

        relations = kg_manager.get_entity_relations(
            entity_id=entity_id,
            relation_type=relation_type,
            direction=direction
        )

        return {
            'success': True,
            'data': {
                'entity_id': entity_id,
                'relation_type': relation_type,
                'direction': direction,
                'relations': relations,
                'total': len(relations)
            },
            'timestamp': datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实体关系失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/api/v1/path/find')
async def find_path(request: PathFindRequest):
    """查找实体间路径"""
    try:
        paths = kg_manager.find_path(
            source_id=request.source_id,
            target_id=request.target_id,
            max_depth=request.max_depth
        )

        return {
            'success': True,
            'data': {
                'source_id': request.source_id,
                'target_id': request.target_id,
                'max_depth': request.max_depth,
                'paths': paths,
                'path_count': len(paths)
            },
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"查找路径失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/api/v1/subgraph/export/{center_id}')
async def export_subgraph(
    center_id: int,
    radius: int = Query(2, ge=1, le=5, description='子图半径')
):
    """导出子图"""
    try:
        subgraph = kg_manager.export_subgraph(
            center_id=center_id,
            radius=radius
        )

        return {
            'success': True,
            'data': subgraph,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"导出子图失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/api/v1/entities')
async def create_entity(request: EntityRequest):
    """创建新实体"""
    try:
        entity_id = kg_manager.add_entity(
            name=request.name,
            entity_type=request.entity_type,
            confidence=request.confidence,
            source=request.source,
            properties=request.properties
        )

        if entity_id == -1:
            raise HTTPException(status_code=500, detail='Failed to create entity')

        return {
            'success': True,
            'data': {
                'entity_id': entity_id,
                'message': 'Entity created successfully'
            },
            'timestamp': datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建实体失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/api/v1/relations')
async def create_relation(request: RelationRequest):
    """创建新关系"""
    try:
        relation_id = kg_manager.add_relation(
            source_id=request.source_id,
            target_id=request.target_id,
            relation_type=request.relation_type,
            confidence=request.confidence,
            properties=request.properties
        )

        if relation_id == -1:
            raise HTTPException(status_code=500, detail='Failed to create relation')

        return {
            'success': True,
            'data': {
                'relation_id': relation_id,
                'message': 'Relation created successfully'
            },
            'timestamp': datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建关系失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/api/v1/database/optimize')
async def optimize_database():
    """优化数据库"""
    try:
        success = kg_manager.optimize_database()
        if success:
            return {
                'success': True,
                'message': 'Database optimization completed successfully',
                'timestamp': datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail='Database optimization failed')
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"数据库优化失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 添加查询参数支持的搜索端点
@app.get('/api/v1/entities/search/quick')
async def quick_search_entities(
    q: str = Query(..., description='搜索查询词'),
    type: Optional[str] = Query(None, description='实体类型过滤'),
    limit: int = Query(20, ge=1, le=1000, description='结果数量限制')
):
    """快速搜索实体 (GET方式)"""
    try:
        results = kg_manager.search_entities(
            query=q,
            entity_type=type,
            limit=limit
        )
        return {
            'success': True,
            'data': {
                'query': q,
                'entity_type': type,
                'results': results,
                'total': len(results)
            },
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"快速搜索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 主函数
async def main():
    """主函数"""
    logger.info('🚀 启动Athena知识图谱API服务...')

    # 启动API服务器
    config = uvicorn.Config(
        app,
        host='0.0.0.0',
        port=8030,
        log_level='info',
        access_log=True
    )

    server = uvicorn.Server(config)
    await server.serve()

if __name__ == '__main__':
    # 设置信号处理
    import signal

    def signal_handler(signum, frame):
        logger.info(f"\n⚠️ 收到信号 {signum}，正在关闭知识图谱API服务...")
        if kg_manager:
            kg_manager.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('👋 知识图谱API服务已关闭')
    except Exception as e:
        logger.error(f"❌ 服务启动失败: {e}")
        sys.exit(1)