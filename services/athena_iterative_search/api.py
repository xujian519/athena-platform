#!/usr/bin/env python3
"""
Athena迭代式搜索系统API服务
提供RESTful API接口，供其他系统调用
"""

import asyncio
from core.async_main import async_main
import json
import logging
from core.logging_config import setup_logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# 导入统一认证模块
from shared.auth.auth_middleware import create_auth_middleware, setup_cors

from .agent import AthenaIterativeSearchAgent
from .config import AthenaSearchConfig, SearchDepth, SearchStrategy
from .core import AthenaIterativeSearchEngine
from .types import PatentSearchResult, SearchSession

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

# 创建FastAPI应用
app = FastAPI(
    title='Athena迭代式搜索系统API',
    description='基于XiaoXi工作平台的专利迭代式深度搜索系统',
    version='1.0.0',
    docs_url='/docs',
    redoc_url='/redoc'
)

# 添加CORS中间件

# 初始化搜索引擎和代理
search_engine = AthenaIterativeSearchEngine()
search_agent = AthenaIterativeSearchAgent()

# 存储搜索会话
search_sessions: Dict[str, SearchSession] = {}

# Pydantic模型定义
class SearchRequest(BaseModel):
    query: str = Field(..., description='搜索查询')
    strategy: str = Field('hybrid', description='搜索策略')
    max_results: int = Field(10, description='最大结果数')
    filters: Optional[Dict[str, Any]] = Field(None, description='搜索过滤器')

class IterativeSearchRequest(BaseModel):
    initial_query: str = Field(..., description='初始查询')
    max_iterations: int = Field(3, description='最大迭代轮数')
    depth: str = Field('standard', description='搜索深度')
    focus_areas: Optional[List[str]] = Field(None, description='关注领域')

class PatentAnalysisRequest(BaseModel):
    company_name: str = Field(..., description='公司名称')
    technology_domain: Optional[str] = Field(None, description='技术领域')
    time_range: Optional[List[str]] = Field(None, description='时间范围')

class TrendAnalysisRequest(BaseModel):
    technology: str = Field(..., description='技术名称')
    time_period: str = Field('5年', description='分析时间段')

class InfringementRiskRequest(BaseModel):
    target_patent_id: str = Field(..., description='目标专利ID')
    technology_keywords: List[str] = Field(..., description='技术关键词')

class SearchResponse(BaseModel):
    success: bool = Field(..., description='是否成功')
    message: str = Field(..., description='响应消息')
    data: Optional[Dict[str, Any]] = Field(None, description='响应数据')
    execution_time: float = Field(..., description='执行时间')

# 工具函数
def create_response(
    success: bool,
    message: str,
    data: Optional[Dict[str, Any]] = None,
    execution_time: float = 0.0
) -> SearchResponse:
    """创建统一响应格式"""
    return SearchResponse(
        success=success,
        message=message,
        data=data,
        execution_time=execution_time
    )

def patent_result_to_dict(result: PatentSearchResult) -> Dict[str, Any]:
    """将专利搜索结果转换为字典"""
    return {
        'id': result.id,
        'title': result.title,
        'content': result.content,
        'score': result.score,
        'relevance': result.relevance.value,
        'engine_type': result.engine_type.value,
        'combined_score': result.combined_score,
        'similarity_score': result.similarity_score,
        'text_match_score': result.text_match_score,
        'patent_metadata': {
            'patent_id': result.patent_metadata.patent_id if result.patent_metadata else None,
            'patent_name': result.patent_metadata.patent_name if result.patent_metadata else None,
            'patent_type': result.patent_metadata.patent_type.value if result.patent_metadata and result.patent_metadata.patent_type else None,
            'applicant': result.patent_metadata.applicant if result.patent_metadata else None,
            'inventor': result.patent_metadata.inventor if result.patent_metadata else None,
            'application_number': result.patent_metadata.application_number if result.patent_metadata else None,
            'application_date': result.patent_metadata.application_date.isoformat() if result.patent_metadata and result.patent_metadata.application_date else None,
            'ipc_code': result.patent_metadata.ipc_code if result.patent_metadata else None,
            'abstract': result.patent_metadata.abstract if result.patent_metadata else None
        } if result.patent_metadata else None
    }

def search_session_to_dict(session: SearchSession) -> Dict[str, Any]:
    """将搜索会话转换为字典"""
    return {
        'id': session.id,
        'topic': session.topic,
        'initial_query': session.initial_query,
        'status': session.status.value,
        'max_iterations': session.max_iterations,
        'current_iteration': session.current_iteration,
        'total_patents_found': session.total_patents_found,
        'unique_patents': session.unique_patents,
        'created_at': session.created_at.isoformat(),
        'updated_at': session.updated_at.isoformat(),
        'iterations': [
            {
                'iteration_number': iter.iteration_number,
                'query': iter.query.text,
                'search_time': iter.search_time,
                'total_results': iter.total_results,
                'quality_score': iter.quality_score,
                'insights': iter.insights,
                'results': [patent_result_to_dict(r) for r in iter.results[:5]]  # 只返回前5个结果
            }
            for iter in session.iterations
        ],
        'research_summary': {
            'topic': session.research_summary.topic if session.research_summary else '',
            'key_findings': session.research_summary.key_findings if session.research_summary else [],
            'main_patents': session.research_summary.main_patents if session.research_summary else [],
            'technological_trends': session.research_summary.technological_trends if session.research_summary else [],
            'competing_applicants': session.research_summary.competing_applicants if session.research_summary else [],
            'innovation_insights': session.research_summary.innovation_insights if session.research_summary else [],
            'recommendations': session.research_summary.recommendations if session.research_summary else [],
            'confidence_level': session.research_summary.confidence_level if session.research_summary else 0.0,
            'completeness_score': session.research_summary.completeness_score if session.research_summary else 0.0
        } if session.research_summary else None
    }

# API端点定义
@app.get('/')
async def root():
    """根端点"""
    return {
        'name': 'Athena迭代式搜索系统API',
        'version': '1.0.0',
        'status': 'running',
        'timestamp': datetime.now().isoformat()
    }

@app.get('/health')
async def health_check():
    """健康检查"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'elasticsearch': 'connected' if search_engine.elasticsearch_client else 'disconnected',
            'vector_search': 'available' if search_engine.vector_search_client else 'unavailable',
            'external_engines': f"{len(search_engine.external_engines)} engines"
        }
    }

@app.post('/api/search', response_model=SearchResponse)
async def search_patents(request: SearchRequest):
    """单次专利搜索"""
    start_time = datetime.now()

    try:
        # 转换搜索策略
        strategy_map = {
            'hybrid': SearchStrategy.HYBRID,
            'fulltext': SearchStrategy.FULLTEXT,
            'semantic': SearchStrategy.SEMANTIC,
            'external': SearchStrategy.EXTERNAL
        }
        strategy = strategy_map.get(request.strategy, SearchStrategy.HYBRID)

        # 执行搜索
        results = await search_engine.search(
            query=request.query,
            strategy=strategy,
            max_results=request.max_results,
            use_cache=True
        )

        # 转换结果格式
        data = {
            'query': request.query,
            'strategy': request.strategy,
            'total_results': len(results),
            'patents': [patent_result_to_dict(result) for result in results]
        }

        execution_time = (datetime.now() - start_time).total_seconds()
        return create_response(
            success=True,
            message=f"搜索完成，找到 {len(results)} 条专利",
            data=data,
            execution_time=execution_time
        )

    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"搜索失败: {e}")
        return create_response(
            success=False,
            message=f"搜索失败: {str(e)}",
            execution_time=execution_time
        )

@app.post('/api/iterative-search', response_model=SearchResponse)
async def iterative_search_patents(request: IterativeSearchRequest):
    """迭代式专利搜索"""
    start_time = datetime.now()

    try:
        # 转换搜索深度
        depth_map = {
            'basic': SearchDepth.BASIC,
            'standard': SearchDepth.STANDARD,
            'deep': SearchDepth.DEEP,
            'comprehensive': SearchDepth.COMPREHENSIVE
        }
        depth = depth_map.get(request.depth, SearchDepth.STANDARD)

        # 进度回调函数
        progress_updates = []

        def progress_callback(current, total, message) -> None:
            progress_updates.append({
                'current': current,
                'total': total,
                'message': message,
                'timestamp': datetime.now().isoformat()
            })
            logger.info(f"搜索进度: {current}/{total} - {message}")

        # 执行迭代搜索
        session = await search_agent.intelligent_patent_research(
            research_topic=request.initial_query,
            max_iterations=request.max_iterations,
            depth=depth,
            focus_areas=request.focus_areas,
            progress_callback=progress_callback
        )

        # 存储会话
        search_sessions[session.id] = session

        # 转换结果格式
        data = {
            'session_id': session.id,
            'session': search_session_to_dict(session),
            'progress_updates': progress_updates
        }

        execution_time = (datetime.now() - start_time).total_seconds()
        return create_response(
            success=True,
            message=f"迭代搜索完成，共 {session.current_iteration} 轮，发现 {session.total_patents_found} 条专利",
            data=data,
            execution_time=execution_time
        )

    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"迭代搜索失败: {e}")
        return create_response(
            success=False,
            message=f"迭代搜索失败: {str(e)}",
            execution_time=execution_time
        )

@app.post('/api/competitive-analysis', response_model=SearchResponse)
async def competitive_analysis(request: PatentAnalysisRequest):
    """专利竞争分析"""
    start_time = datetime.now()

    try:
        # 执行竞争分析
        session = await search_agent.patent_competitive_analysis(
            company_name=request.company_name,
            technology_domain=request.technology_domain,
            time_range=tuple(request.time_range) if request.time_range else None
        )

        # 存储会话
        search_sessions[session.id] = session

        # 转换结果格式
        data = {
            'session_id': session.id,
            'session': search_session_to_dict(session)
        }

        execution_time = (datetime.now() - start_time).total_seconds()
        return create_response(
            success=True,
            message=f"竞争分析完成，发现 {session.total_patents_found} 条相关专利",
            data=data,
            execution_time=execution_time
        )

    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"竞争分析失败: {e}")
        return create_response(
            success=False,
            message=f"竞争分析失败: {str(e)}",
            execution_time=execution_time
        )

@app.post('/api/trend-analysis', response_model=SearchResponse)
async def trend_analysis(request: TrendAnalysisRequest):
    """技术趋势分析"""
    start_time = datetime.now()

    try:
        # 执行趋势分析
        session = await search_agent.patent_technology_trend_analysis(
            technology=request.technology,
            time_period=request.time_period
        )

        # 存储会话
        search_sessions[session.id] = session

        # 转换结果格式
        data = {
            'session_id': session.id,
            'session': search_session_to_dict(session)
        }

        execution_time = (datetime.now() - start_time).total_seconds()
        return create_response(
            success=True,
            message=f"技术趋势分析完成，发现 {session.total_patents_found} 条相关专利",
            data=data,
            execution_time=execution_time
        )

    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"技术趋势分析失败: {e}")
        return create_response(
            success=False,
            message=f"技术趋势分析失败: {str(e)}",
            execution_time=execution_time
        )

@app.post('/api/infringement-risk', response_model=SearchResponse)
async def infringement_risk_assessment(request: InfringementRiskRequest):
    """侵权风险评估"""
    start_time = datetime.now()

    try:
        # 执行侵权风险评估
        session = await search_agent.patent_infringement_risk_assessment(
            target_patent_id=request.target_patent_id,
            technology_keywords=request.technology_keywords
        )

        # 存储会话
        search_sessions[session.id] = session

        # 转换结果格式
        data = {
            'session_id': session.id,
            'session': search_session_to_dict(session)
        }

        execution_time = (datetime.now() - start_time).total_seconds()
        return create_response(
            success=True,
            message=f"侵权风险评估完成",
            data=data,
            execution_time=execution_time
        )

    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"侵权风险评估失败: {e}")
        return create_response(
            success=False,
            message=f"侵权风险评估失败: {str(e)}",
            execution_time=execution_time
        )

@app.get('/api/session/{session_id}', response_model=SearchResponse)
async def get_search_session(session_id: str):
    """获取搜索会话详情"""
    start_time = datetime.now()

    try:
        if session_id not in search_sessions:
            return create_response(
                success=False,
                message='会话不存在',
                execution_time=(datetime.now() - start_time).total_seconds()
            )

        session = search_sessions[session_id]
        data = {
            'session': search_session_to_dict(session)
        }

        execution_time = (datetime.now() - start_time).total_seconds()
        return create_response(
            success=True,
            message='获取会话详情成功',
            data=data,
            execution_time=execution_time
        )

    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"获取会话详情失败: {e}")
        return create_response(
            success=False,
            message=f"获取会话详情失败: {str(e)}",
            execution_time=execution_time
        )

@app.get('/api/sessions', response_model=SearchResponse)
async def list_search_sessions():
    """列出所有搜索会话"""
    start_time = datetime.now()

    try:
        sessions = []
        for session_id, session in search_sessions.items():
            sessions.append({
                'session_id': session_id,
                'topic': session.topic,
                'status': session.status.value,
                'current_iteration': session.current_iteration,
                'total_patents_found': session.total_patents_found,
                'created_at': session.created_at.isoformat()
            })

        data = {
            'total_sessions': len(sessions),
            'sessions': sessions
        }

        execution_time = (datetime.now() - start_time).total_seconds()
        return create_response(
            success=True,
            message=f"获取会话列表成功，共 {len(sessions)} 个会话",
            data=data,
            execution_time=execution_time
        )

    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"获取会话列表失败: {e}")
        return create_response(
            success=False,
            message=f"获取会话列表失败: {str(e)}",
            execution_time=execution_time
        )

@app.delete('/api/session/{session_id}', response_model=SearchResponse)
async def delete_search_session(session_id: str):
    """删除搜索会话"""
    start_time = datetime.now()

    try:
        if session_id not in search_sessions:
            return create_response(
                success=False,
                message='会话不存在',
                execution_time=(datetime.now() - start_time).total_seconds()
            )

        del search_sessions[session_id]

        execution_time = (datetime.now() - start_time).total_seconds()
        return create_response(
            success=True,
            message='会话删除成功',
            execution_time=execution_time
        )

    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"删除会话失败: {e}")
        return create_response(
            success=False,
            message=f"删除会话失败: {str(e)}",
            execution_time=execution_time
        )

@app.get('/api/statistics', response_model=SearchResponse)
async def get_search_statistics():
    """获取搜索统计信息"""
    start_time = datetime.now()

    try:
        stats = search_engine.statistics

        data = {
            'total_searches': stats.total_searches,
            'successful_searches': stats.successful_searches,
            'failed_searches': stats.failed_searches,
            'success_rate': stats.successful_searches / stats.total_searches if stats.total_searches > 0 else 0,
            'average_response_time': stats.average_response_time,
            'average_results_per_search': stats.average_results_per_search,
            'active_sessions': len(search_sessions),
            'cache_size': len(search_engine.cache)
        }

        execution_time = (datetime.now() - start_time).total_seconds()
        return create_response(
            success=True,
            message='获取统计信息成功',
            data=data,
            execution_time=execution_time
        )

    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"获取统计信息失败: {e}")
        return create_response(
            success=False,
            message=f"获取统计信息失败: {str(e)}",
            execution_time=execution_time
        )

def main() -> None:
    """启动API服务"""
    logger.info('启动Athena迭代式搜索系统API服务')

    # 配置服务器
    config = uvicorn.Config(
        app=app,
        host='0.0.0.0',
        port=5002,  # 使用不同的端口避免冲突
        log_level='info',
        access_log=True
    )

    # 启动服务器
    server = uvicorn.Server(config)
    server.run()

if __name__ == '__main__':
    main()