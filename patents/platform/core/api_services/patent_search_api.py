#!/usr/bin/env python3
"""
Athena工作平台 - 专利检索API服务
Patent Search API Service for Athena Platform

统一的专利检索服务入口，集成Google Patents等多种数据源

作者: Athena (智慧女神)
创建时间: 2025-12-07
版本: 1.0.0
"""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import (
    BackgroundTasks,
    FastAPI,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from google_patents_retriever import PatentPriority

# 导入专利服务管理器
from patent_service_manager import (
    PatentServiceManager,
    PatentSource,
    SearchStatus,
    cleanup_patent_service_manager,
    get_patent_service_manager,
)
from pydantic import BaseModel, Field
from pydantic.types import constr

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局变量
patent_manager: PatentServiceManager | None = None

# WebSocket连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # 移除失效连接
                self.active_connections.remove(connection)

websocket_manager = ConnectionManager()

# 请求模型
class PatentSearchRequest(BaseModel):
    query: constr(min_length=1, max_length=500) = Field(..., description='搜索查询')
    max_results: int = Field(default=20, ge=1, le=100, description='最大结果数')
    source: str = Field(default='google_patents', description='数据源')
    priority: str = Field(default='medium', pattern='^(low|medium|high)$', description='搜索优先级')
    filters: Optional[Dict[str, Any]] = Field(default=None, description='搜索筛选器')

class BatchSearchRequest(BaseModel):
    queries: List[constr(min_length=1, max_length=500)] = Field(..., description='查询列表')
    max_results_per_query: int = Field(default=10, ge=1, le=50, description='每个查询的最大结果数')
    source: str = Field(default='google_patents', description='数据源')
    max_concurrent: int = Field(default=3, ge=1, le=10, description='最大并发数')

class TaskListRequest(BaseModel):
    status: Optional[str] = Field(default=None, pattern='^(pending|running|completed|failed|cancelled)$', description='任务状态')
    source: Optional[str] = Field(default=None, description='数据源')
    limit: int = Field(default=50, ge=1, le=200, description='最大任务数')

# 响应模型
class TaskStatusResponse(BaseModel):
    task_id: str
    source: str
    query: str
    status: str
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    result_count: int
    error: Optional[str]

class SearchResultsResponse(BaseModel):
    task_id: str
    status: str
    query: str
    source: str
    total_found: int
    patents: List[Dict[str, Any]]
    search_time: Optional[str]
    duration: Optional[float]

# 应用生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global patent_manager

    # 启动时初始化
    logger.info('🚀 Athena专利检索API服务启动中...')
    try:
        patent_manager = await get_patent_service_manager()
        logger.info('✅ 专利检索服务管理器初始化成功')

        yield

    except Exception as e:
        logger.error(f"❌ 初始化失败: {e}")
        yield
    finally:
        # 关闭时清理
        await cleanup_patent_service_manager()
        logger.info('🔒 专利检索服务管理器已关闭')

# 创建FastAPI应用
app = FastAPI(
    title='Athena专利检索API服务',
    description='Athena工作平台 - 统一专利检索服务',
    version='1.0.0',
    docs_url='/docs',
    redoc_url='/redoc',
    lifespan=lifespan
)

# 静态文件服务
app.mount('/static', StaticFiles(directory='static'), name='static')

# 根路径
@app.get('/')
async def root():
    """根路径"""
    return {
        'service': 'Athena专利检索API服务',
        'status': 'running',
        'description': 'Athena工作平台 - 统一专利检索服务',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat(),
        'endpoints': {
            'search': '/api/v1/patents/search',
            'batch_search': '/api/v1/patents/batch_search',
            'task_status': '/api/v1/patents/tasks/{task_id}',
            'task_results': '/api/v1/patents/tasks/{task_id}/results',
            'tasks_list': '/api/v1/patents/tasks',
            'cancel_task': '/api/v1/patents/tasks/{task_id}/cancel',
            'statistics': '/api/v1/patents/statistics',
            'sources': '/api/v1/patents/sources',
            'health': '/api/v1/patents/health'
        }
    }

# 健康检查
@app.get('/health')
@app.get('/api/v1/patents/health')
async def health():
    """健康检查"""
    global patent_manager

    if not patent_manager:
        return {
            'status': 'uninitialized',
            'service': 'patent_search_api',
            'timestamp': datetime.now().isoformat()
        }

    try:
        stats = await patent_manager.get_service_statistics()
        status = 'healthy' if stats['performance']['concurrent_searches'] < stats['performance']['max_concurrent'] else 'busy'

        return {
            'status': status,
            'service': 'patent_search_api',
            'timestamp': datetime.now().isoformat(),
            'active_searches': stats['performance']['concurrent_searches'],
            'max_concurrent': stats['performance']['max_concurrent']
        }

    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            'status': 'error',
            'service': 'patent_search_api',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }

# 获取支持的数据源
@app.get('/api/v1/patents/sources')
async def get_patent_sources():
    """获取支持的专利数据源"""
    sources = []
    for source in PatentSource:
        sources.append({
            'value': source.value,
            'name': source.value.replace('_', ' ').title(),
            'available': source == PatentSource.GOOGLE_PATENTS  # 目前只支持Google Patents
        })

    return {
        'sources': sources,
        'total': len(sources)
    }

# 专利搜索
@app.post('/api/v1/patents/search')
async def search_patents(request: PatentSearchRequest):
    """搜索专利"""
    global patent_manager

    if not patent_manager:
        raise HTTPException(status_code=503, detail='专利检索服务未初始化')

    try:
        # 转换数据源
        try:
            source = PatentSource(request.source)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"不支持的数据源: {request.source}")

        # 转换优先级
        try:
            priority = PatentPriority(request.priority)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的优先级: {request.priority}")

        # 执行搜索
        task_id = await patent_manager.search_patents(
            query=request.query,
            max_results=request.max_results,
            source=source,
            priority=priority,
            filters=request.filters
        )

        # 广播新任务通知
        await websocket_manager.broadcast(json.dumps({
            'type': 'task_created',
            'task_id': task_id,
            'query': request.query
        }))

        return {
            'success': True,
            'task_id': task_id,
            'message': '搜索任务已创建',
            'estimated_time': '10-30秒'
        }

    except Exception as e:
        logger.error(f"搜索专利失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 批量搜索
@app.post('/api/v1/patents/batch_search')
async def batch_search_patents(request: BatchSearchRequest):
    """批量搜索专利"""
    global patent_manager

    if not patent_manager:
        raise HTTPException(status_code=503, detail='专利检索服务未初始化')

    if len(request.queries) > 20:
        raise HTTPException(status_code=400, detail='批量搜索最多支持20个查询')

    try:
        # 转换数据源
        try:
            source = PatentSource(request.source)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"不支持的数据源: {request.source}")

        # 执行批量搜索
        task_ids = await patent_manager.batch_search_patents(
            queries=request.queries,
            max_results_per_query=request.max_results_per_query,
            source=source,
            max_concurrent=request.max_concurrent
        )

        # 广播批量任务通知
        await websocket_manager.broadcast(json.dumps({
            'type': 'batch_tasks_created',
            'task_ids': task_ids,
            'total_queries': len(request.queries)
        }))

        return {
            'success': True,
            'batch_id': f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'task_ids': task_ids,
            'total_queries': len(request.queries),
            'message': '批量搜索任务已创建',
            'estimated_time': f"{len(request.queries) * 15}-{len(request.queries) * 30}秒"
        }

    except Exception as e:
        logger.error(f"批量搜索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 获取任务状态
@app.get('/api/v1/patents/tasks/{task_id}', response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """获取搜索任务状态"""
    global patent_manager

    if not patent_manager:
        raise HTTPException(status_code=503, detail='专利检索服务未初始化')

    try:
        status = await patent_manager.get_search_status(task_id)
        if not status:
            raise HTTPException(status_code=404, detail='任务不存在')

        return TaskStatusResponse(**status)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 获取搜索结果
@app.get('/api/v1/patents/tasks/{task_id}/results', response_model=SearchResultsResponse)
async def get_task_results(task_id: str):
    """获取搜索结果"""
    global patent_manager

    if not patent_manager:
        raise HTTPException(status_code=503, detail='专利检索服务未初始化')

    try:
        results = await patent_manager.get_search_results(task_id)
        if not results:
            raise HTTPException(status_code=404, detail='任务不存在或结果不可用')

        return SearchResultsResponse(**results)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取搜索结果失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 取消任务
@app.post('/api/v1/patents/tasks/{task_id}/cancel')
async def cancel_task(task_id: str):
    """取消搜索任务"""
    global patent_manager

    if not patent_manager:
        raise HTTPException(status_code=503, detail='专利检索服务未初始化')

    try:
        success = await patent_manager.cancel_search(task_id)
        if not success:
            raise HTTPException(status_code=404, detail='任务不存在或无法取消')

        # 广播取消通知
        await websocket_manager.broadcast(json.dumps({
            'type': 'task_cancelled',
            'task_id': task_id
        }))

        return {
            'success': True,
            'message': '任务已取消'
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 获取任务列表
@app.post('/api/v1/patents/tasks')
async def list_tasks(request: TaskListRequest):
    """获取任务列表"""
    global patent_manager

    if not patent_manager:
        raise HTTPException(status_code=503, detail='专利检索服务未初始化')

    try:
        # 转换状态
        status = None
        if request.status:
            try:
                status = SearchStatus(request.status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的状态: {request.status}")

        # 转换数据源
        source = None
        if request.source:
            try:
                source = PatentSource(request.source)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"不支持的数据源: {request.source}")

        tasks = await patent_manager.list_search_tasks(
            status=status,
            source=source,
            limit=request.limit
        )

        return {
            'tasks': tasks,
            'total': len(tasks)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 获取服务统计
@app.get('/api/v1/patents/statistics')
async def get_statistics():
    """获取服务统计信息"""
    global patent_manager

    if not patent_manager:
        raise HTTPException(status_code=503, detail='专利检索服务未初始化')

    try:
        stats = await patent_manager.get_service_statistics()
        return stats

    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket实时通知
@app.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket实时通知端点"""
    await websocket_manager.connect(websocket)
    try:
        while True:
            # 保持连接活跃
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)

# 清理旧任务（后台任务）
@app.post('/api/v1/patents/cleanup')
async def cleanup_old_tasks(max_age_days: int = 7):
    """清理旧任务"""
    global patent_manager

    if not patent_manager:
        raise HTTPException(status_code=503, detail='专利检索服务未初始化')

    try:
        await patent_manager.cleanup_old_tasks(max_age_days)
        return {
            'success': True,
            'message': f"已清理 {max_age_days} 天前的旧任务"
        }

    except Exception as e:
        logger.error(f"清理旧任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 错误处理
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """HTTP异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            'error': {
                'code': exc.status_code,
                'message': exc.detail,
                'path': str(request.url),
                'timestamp': datetime.now().isoformat()
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """通用异常处理"""
    logger.error(f"未处理的异常: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            'error': {
                'code': 500,
                'message': '内部服务器错误',
                'path': str(request.url),
                'timestamp': datetime.now().isoformat()
            }
        }
    )

def create_directories():
    """创建必要的目录"""
    directories = [
        'data/patents',
        'data/patents/results',
        'data/patents/tasks',
        'static/patents',
        'logs/patents'
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

def main():
    """主函数"""
    # 创建目录
    create_directories()

    # 启动服务器
    uvicorn.run(
        'patent_search_api:app',
        host='0.0.0.0',
        port=8017,
        reload=False,
        log_level='info',
        access_log=True
    )

if __name__ == '__main__':
    main()