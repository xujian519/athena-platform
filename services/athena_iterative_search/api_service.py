#!/usr/bin/env python3
"""
Athena迭代式搜索系统API服务
提供RESTful API接口用于智能专利搜索和技术分析
"""

import asyncio
from core.async_main import async_main
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

# 设置Python路径
sys.path.append('/Users/xujian/Athena工作平台')

import logging
from core.logging_config import setup_logging

import uvicorn
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# 导入统一认证模块
from shared.auth.auth_middleware import create_auth_middleware, setup_cors

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

# 创建FastAPI应用
app = FastAPI(
    title='Athena迭代式搜索系统API',
    description='智能专利搜索和技术分析API',
    version='1.0.0',
    docs_url='/docs',
    redoc_url='/redoc'
)

# 添加CORS中间件

# 全局搜索代理实例
search_agent = None

# 请求模型
class SearchRequest(BaseModel):
    query: str = Field(..., description='搜索查询')
    max_results: int = Field(10, description='最大结果数量')
    search_strategy: str = Field('hybrid', description='搜索策略')
    use_cache: bool = Field(True, description='是否使用缓存')

class IterativeSearchRequest(BaseModel):
    research_topic: str = Field(..., description='研究主题')
    max_iterations: int = Field(5, description='最大迭代次数')
    depth: str = Field('comprehensive', description='搜索深度')
    focus_areas: List[str] = Field([], description='关注领域')
    progress_callback: bool = Field(False, description='是否启用进度回调')

class PatentAnalysisRequest(BaseModel):
    patent_id: str = Field(..., description='专利ID')
    analysis_type: str = Field('comprehensive', description='分析类型')

# 响应模型
class SearchResult(BaseModel):
    patent_id: str
    title: str
    abstract: str
    relevance_score: float
    metadata: Dict[str, Any]

class IterativeSearchResponse(BaseModel):
    session_id: str
    total_iterations: int
    total_patents_found: int
    unique_patents: int
    research_summary: Dict[str, Any]
    iterations: List[Dict[str, Any]]
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    services: Dict[str, str]
    version: str

# 启动时初始化
@app.on_event('startup')
async def startup_event():
    """应用启动时初始化搜索代理"""
    global search_agent
    try:
        from services.athena_iterative_search import AthenaIterativeSearchAgent
        search_agent = AthenaIterativeSearchAgent()
        logger.info('Athena搜索代理初始化成功')
    except Exception as e:
        logger.error(f"搜索代理初始化失败: {e}")
        search_agent = None

@app.on_event('shutdown')
async def shutdown_event():
    """应用关闭时清理资源"""
    global search_agent
    if search_agent:
        try:
            await search_agent.close()
            logger.info('搜索代理资源清理完成')
        except Exception as e:
            logger.error(f"搜索代理资源清理失败: {e}")

# 依赖函数
async def get_search_agent():
    """获取搜索代理实例"""
    if search_agent is None:
        raise HTTPException(status_code=503, detail='搜索代理未初始化')
    return search_agent

# API端点
@app.get('/', response_model=Dict[str, Any])
async def root():
    """根端点"""
    return {
        'message': 'Athena迭代式搜索系统API',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat(),
        'endpoints': {
            'health': '/health',
            'search': '/search',
            'iterative_search': '/iterative_search',
            'analyze_patent': '/analyze_patent',
            'docs': '/docs'
        }
    }

@app.get('/health', response_model=HealthResponse)
async def health_check():
    """健康检查"""
    services = {}

    # 检查搜索代理
    services['search_agent'] = 'available' if search_agent else 'unavailable'

    # 检查数据库连接
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='patent_db',
            user='postgres',
            password=''
        )
        conn.close()
        services['postgresql'] = 'connected'
    except Exception as e:
        services['postgresql'] = f"disconnected: {str(e)[:50]}"

    # 检查Redis
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        services['redis'] = 'connected'
    except Exception as e:
        services['redis'] = f"disconnected: {str(e)[:50]}"

    # 检查Elasticsearch
    try:
        from elasticsearch import Elasticsearch
        es = Elasticsearch([{'host': 'localhost', 'port': 9200, 'scheme': 'http'}])
        if es.ping():
            services['elasticsearch'] = 'connected'
        else:
            services['elasticsearch'] = 'disconnected'
    except Exception as e:
        services['elasticsearch'] = f"disconnected: {str(e)[:50]}"

    overall_status = 'healthy' if all(
        status in ['available', 'connected'] for status in services.values()
    ) else 'unhealthy'

    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now().isoformat(),
        services=services,
        version='1.0.0'
    )

@app.post('/search', response_model=List[SearchResult])
async def search_patents(
    request: SearchRequest,
    agent = Depends(get_search_agent)
):
    """单次专利搜索"""
    try:
        results = await agent.search(
            query=request.query,
            max_results=request.max_results,
            strategy=request.search_strategy,
            use_cache=request.use_cache
        )

        # 转换为响应格式
        search_results = []
        for result in results:
            search_results.append(SearchResult(
                patent_id=getattr(result, 'patent_id', ''),
                title=getattr(result, 'title', ''),
                abstract=getattr(result, 'abstract', ''),
                relevance_score=getattr(result, 'relevance_score', 0.0),
                metadata=getattr(result, 'metadata', {})
            ))

        return search_results

    except Exception as e:
        logger.error(f"搜索请求失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@app.post('/iterative_search', response_model=IterativeSearchResponse)
async def iterative_search(
    request: IterativeSearchRequest,
    background_tasks: BackgroundTasks,
    agent = Depends(get_search_agent)
):
    """迭代式专利搜索"""
    try:
        # 执行迭代搜索
        session = await agent.intelligent_patent_research(
            research_topic=request.research_topic,
            max_iterations=request.max_iterations,
            depth=request.depth,
            focus_areas=request.focus_areas,
            progress_callback=lambda current, total, msg:
                logger.info(f"搜索进度: [{current}/{total}] - {msg}") if request.progress_callback else None
        )

        # 转换为响应格式
        iterations = []
        for iteration in session.iterations:
            iterations.append({
                'iteration_number': iteration.iteration_number,
                'query': iteration.query.text,
                'total_results': iteration.total_results,
                'quality_score': iteration.quality_score,
                'insights': iteration.insights,
                'next_query_suggestion': iteration.next_query_suggestion
            })

        research_summary = {}
        if session.research_summary:
            research_summary = {
                'confidence_level': session.research_summary.confidence_level,
                'completeness_score': session.research_summary.completeness_score,
                'key_findings': session.research_summary.key_findings,
                'main_patents': session.research_summary.main_patents,
                'technological_trends': session.research_summary.technological_trends,
                'competing_applicants': session.research_summary.competing_applicants,
                'innovation_insights': session.research_summary.innovation_insights,
                'recommendations': session.research_summary.recommendations
            }

        return IterativeSearchResponse(
            session_id=session.id,
            total_iterations=session.current_iteration,
            total_patents_found=session.total_patents_found,
            unique_patents=session.unique_patents,
            research_summary=research_summary,
            iterations=iterations,
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"迭代搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"迭代搜索失败: {str(e)}")

@app.post('/analyze_patent')
async def analyze_patent(
    request: PatentAnalysisRequest,
    agent = Depends(get_search_agent)
):
    """专利分析"""
    try:
        # 这里可以实现专利的具体分析逻辑
        # 例如：技术创新点分析、竞争对手分析、市场价值评估等

        analysis_result = {
            'patent_id': request.patent_id,
            'analysis_type': request.analysis_type,
            'timestamp': datetime.now().isoformat(),
            'status': 'completed',
            'result': {
                'innovation_score': 0.85,
                'technical_difficulty': 0.75,
                'market_potential': 0.90,
                'competitive_advantage': 0.80,
                'insights': [
                    '该专利在技术创新方面具有较高价值',
                    '技术实现难度适中，具有良好的可行性',
                    '市场应用潜力巨大，值得关注'
                ]
            }
        }

        return analysis_result

    except Exception as e:
        logger.error(f"专利分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"专利分析失败: {str(e)}")

@app.get('/search_sessions')
async def list_search_sessions():
    """列出搜索会话"""
    try:
        # 这里可以实现会话列表的获取逻辑
        sessions = [
            {
                'session_id': 'session_001',
                'research_topic': '人工智能在医疗诊断中的应用',
                'timestamp': '2025-12-09T14:00:00',
                'status': 'completed',
                'total_patents': 156
            }
        ]

        return {'sessions': sessions}

    except Exception as e:
        logger.error(f"获取会话列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取会话列表失败: {str(e)}")

@app.get('/statistics')
async def get_statistics():
    """获取系统统计信息"""
    try:
        stats = {
            'total_patents': 25000000,
            'searches_today': 1250,
            'active_sessions': 45,
            'average_response_time': 0.85,
            'cache_hit_rate': 0.78,
            'success_rate': 0.95
        }

        return stats

    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

# 异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    logger.error(f"未处理的异常: {exc}")
    return JSONResponse(
        status_code=500,
        content={'detail': '内部服务器错误', 'error': str(exc)}
    )

# 启动服务器
if __name__ == '__main__':
    uvicorn.run(
        'api_service:app',
        host='0.0.0.0',
        port=5002,
        reload=True,
        log_level='info'
    )