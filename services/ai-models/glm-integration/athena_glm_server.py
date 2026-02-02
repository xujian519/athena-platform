#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Athena工作平台 - GLM-4.6 API服务器
提供智能体协调、专利分析、长文本处理等强大能力
"""

import asyncio
from core.async_main import async_main
import json
import logging
from core.logging_config import setup_logging
import os
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from glm_4_6_service import (
    GLM46APIClient,
    GLMModelType,
    GLMRequest,
    GLMResponse,
    TaskType,
    get_glm_client,
)
from pydantic import BaseModel, Field

# 导入统一认证模块
from shared.auth.auth_middleware import create_auth_middleware, setup_cors

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = logging.getLogger('AthenaGLMServer')

# FastAPI应用
app = FastAPI(
    title='Athena工作平台 - GLM-4.6 API',
    description='提供智能体协调、专利分析、长文本处理等GLM-4.6核心能力',
    version='1.0.0',
    docs_url='/docs',
    redoc_url='/redoc'
)

# CORS配置

# Pydantic模型
class PatentAnalysisRequest(BaseModel):
    title: str = Field(..., description='专利标题')
    abstract: str = Field(..., description='专利摘要')
    technical_field: str = Field(default='', description='技术领域')
    background: str = Field(default='', description='背景技术')
    invention: str = Field(default='', description='发明内容')
    implementation: str = Field(default='', description='具体实施方式')

class AgentCoordinationRequest(BaseModel):
    task: str = Field(..., description='需要协调的任务', min_length=1, max_length=2000)
    available_tools: List[str] = Field(..., description='可用工具列表')
    thinking_mode: bool = Field(default=True, description='是否启用思考模式')

class LongTextRequest(BaseModel):
    text: str = Field(..., description='长文本内容', min_length=100)
    analysis_type: str = Field(default='comprehensive', description='分析类型')
    enable_thinking: bool = Field(default=True, description='是否启用思考模式')

class CodeGenerationRequest(BaseModel):
    prompt: str = Field(..., description='代码生成提示', min_length=1, max_length=2000)
    language: str = Field(default='python', description='编程语言')
    enable_thinking: bool = Field(default=True, description='是否启用思考过程')
    max_tokens: int = Field(default=4000, description='最大生成tokens')

class GLMResponseModel(BaseModel):
    success: bool
    content: str
    thinking_process: str | None = None
    tool_calls: Optional[List[Dict]] = None
    usage: Dict = {}
    model: str = ''
    finish_reason: str = ''
    response_time: float
    timestamp: str
    error: str | None = None

class StatisticsResponseModel(BaseModel):
    total_requests: int
    total_tokens: int
    thinking_requests: int
    agent_requests: int
    success_rate: float
    average_response_time: float

class HealthResponseModel(BaseModel):
    status: str
    timestamp: str
    glm_connected: bool
    model_version: str
    capabilities: List[str]

# 全局变量
server_start_time = datetime.now()
_glm_client: GLM46APIClient | None = None

async def get_glm_service() -> GLM46APIClient:
    """获取GLM服务实例"""
    global _glm_client
    if _glm_client is None:
        _glm_client = GLM46APIClient()
        await _glm_client.__aenter__()
    return _glm_client

@app.on_event('startup')
async def startup_event():
    """应用启动事件"""
    logger.info('🚀 Athena GLM-4.6 API服务器启动中...')

    try:
        client = await get_glm_service()
        connected = await client.test_connection()

        if connected:
            logger.info('✅ GLM-4.6 API连接成功!')
        else:
            logger.warning('⚠️ GLM-4.6 API连接失败，但服务器继续运行')

    except Exception as e:
        logger.error(f"❌ GLM初始化失败: {str(e)}")

@app.on_event('shutdown')
async def shutdown_event():
    """应用关闭事件"""
    global _glm_client
    if _glm_client:
        await _glm_client.__aexit__(None, None, None)
        logger.info('🛑 Athena GLM-4.6 API服务器已关闭')

@app.get('/', response_model=Dict[str, str])
async def root():
    """根路径"""
    return {
        'message': 'Athena工作平台 - GLM-4.6 API服务',
        'version': '1.0.0',
        'model': 'GLM-4.6',
        'docs': '/docs',
        'capabilities': [
            '智能体协调',
            '专利深度分析',
            '长文本处理',
            '思考模式推理',
            '工具调用',
            '200K超长上下文'
        ]
    }

@app.get('/health', response_model=HealthResponseModel)
async def health_check():
    """健康检查"""
    try:
        client = await get_glm_service()
        glm_connected = await client.test_connection()

        return HealthResponseModel(
            status='healthy' if glm_connected else 'degraded',
            timestamp=datetime.now().isoformat(),
            glm_connected=glm_connected,
            model_version='GLM-4.6',
            capabilities=[
                'patent_analysis',
                'agent_coordination',
                'long_text_processing',
                'thinking_mode',
                'tool_calls',
                '200k_context'
            ]
        )
    except Exception as e:
        return HealthResponseModel(
            status='unhealthy',
            timestamp=datetime.now().isoformat(),
            glm_connected=False,
            model_version='unknown',
            capabilities=[]
        )

@app.post('/patent-analysis', response_model=GLMResponseModel)
async def analyze_patent(request: PatentAnalysisRequest):
    """专利深度分析"""
    try:
        client = await get_glm_service()

        patent_info = {
            'title': request.title,
            'abstract': request.abstract,
            'technical_field': request.technical_field,
            'background': request.background,
            'invention': request.invention,
            'implementation': request.implementation
        }

        response = await client.analyze_patent(patent_info)

        return GLMResponseModel(
            success=len(response.content) > 0 and not response.content.startswith('API调用失败'),
            content=response.content,
            thinking_process=response.thinking_process,
            tool_calls=response.tool_calls,
            usage=response.usage,
            model=response.model,
            finish_reason=response.finish_reason,
            response_time=response.response_time,
            timestamp=response.timestamp.isoformat(),
            error=None if response.content and not response.content.startswith('API调用失败') else response.content
        )

    except Exception as e:
        logger.error(f"专利分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/agent-coordination', response_model=GLMResponseModel)
async def coordinate_agents(request: AgentCoordinationRequest):
    """智能体协调"""
    try:
        client = await get_glm_service()

        response = await client.coordinate_agents(request.task, request.available_tools)

        return GLMResponseModel(
            success=len(response.content) > 0 and not response.content.startswith('API调用失败'),
            content=response.content,
            thinking_process=response.thinking_process,
            tool_calls=response.tool_calls,
            usage=response.usage,
            model=response.model,
            finish_reason=response.finish_reason,
            response_time=response.response_time,
            timestamp=response.timestamp.isoformat(),
            error=None if response.content and not response.content.startswith('API调用失败') else response.content
        )

    except Exception as e:
        logger.error(f"智能体协调失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/long-text-processing', response_model=GLMResponseModel)
async def process_long_text(request: LongTextRequest):
    """长文本处理"""
    try:
        client = await get_glm_service()

        response = await client.process_long_text(request.text, request.analysis_type)

        return GLMResponseModel(
            success=len(response.content) > 0 and not response.content.startswith('API调用失败'),
            content=response.content,
            thinking_process=response.thinking_process,
            tool_calls=response.tool_calls,
            usage=response.usage,
            model=response.model,
            finish_reason=response.finish_reason,
            response_time=response.response_time,
            timestamp=response.timestamp.isoformat(),
            error=None if response.content and not response.content.startswith('API调用失败') else response.content
        )

    except Exception as e:
        logger.error(f"长文本处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/generate-code-with-thinking', response_model=GLMResponseModel)
async def generate_code_with_thinking(request: CodeGenerationRequest):
    """带思考过程的代码生成"""
    try:
        client = await get_glm_service()

        response = await client.generate_code_with_thinking(request.prompt, request.language)

        return GLMResponseModel(
            success=len(response.content) > 0 and not response.content.startswith('API调用失败'),
            content=response.content,
            thinking_process=response.thinking_process,
            tool_calls=response.tool_calls,
            usage=response.usage,
            model=response.model,
            finish_reason=response.finish_reason,
            response_time=response.response_time,
            timestamp=response.timestamp.isoformat(),
            error=None if response.content and not response.content.startswith('API调用失败') else response.content
        )

    except Exception as e:
        logger.error(f"代码生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/thinking-mode')
async def thinking_mode_chat(
    message: str,
    thinking_type: str = 'step_by_step',
    context: str | None = None
):
    """思考模式对话"""
    try:
        client = await get_glm_service()

        messages = [{'role': 'user', 'content': message}]
        if context:
            messages.insert(0, {'role': 'system', 'content': f"上下文信息：{context}"})

        request = GLMRequest(
            messages=messages,
            model=GLMModelType.GLM_4_6,
            enable_thinking=True,
            thinking_type=thinking_type,
            max_tokens=3000
        )

        response = await client.call_glm_api(request)

        return {
            'success': True,
            'thinking_process': response.thinking_process,
            'response': response.content,
            'usage': response.usage,
            'response_time': response.response_time
        }

    except Exception as e:
        logger.error(f"思考模式对话失败: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'thinking_process': None,
            'response': '',
            'usage': {},
            'response_time': 0
        }

@app.get('/statistics', response_model=StatisticsResponseModel)
async def get_usage_statistics():
    """获取使用统计信息"""
    try:
        client = await get_glm_service()
        stats = client.get_statistics()

        return StatisticsResponseModel(**stats)

    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/model-info')
async def get_model_info():
    """获取模型信息"""
    return {
        'model': 'GLM-4.6',
        'parameters': {
            'total': '355B',
            'active': '32B'
        },
        'context_window': '200K tokens',
        'capabilities': [
            '智能体工具调用',
            '思考模式推理',
            '长文本理解',
            '代码生成',
            '专利分析',
            '多语言支持'
        ],
        'specialties': [
            'Agent Coordination',
            'Patent Analysis',
            'Long Text Processing',
            'Complex Reasoning',
            'Tool Integration'
        ],
        'performance': {
            'coding': '国内最强',
            'reasoning': '业界领先',
            'agent': '专业优化'
        }
    }

@app.post('/reset-statistics')
async def reset_statistics():
    """重置统计信息"""
    try:
        global _glm_client
        if _glm_client:
            _glm_client.stats = {
                'total_requests': 0,
                'total_tokens': 0,
                'thinking_requests': 0,
                'agent_requests': 0,
                'success_rate': 0.0,
                'average_response_time': 0.0
            }

        return {'message': 'GLM统计信息已重置'}

    except Exception as e:
        logger.error(f"重置统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 错误处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    logger.error(f"未处理的异常: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={'detail': '内部服务器错误', 'error': str(exc)}
    )

if __name__ == '__main__':
    # 启动服务器
    uvicorn.run(
        'athena_glm_server:app',
        host='0.0.0.0',
        port=8090,
        reload=True,
        log_level='info',
        access_log=True
    )