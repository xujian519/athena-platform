#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Athena工作平台 - DeepSeek API服务器
提供RESTful API接口，集成DeepSeek-Coder能力
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
from deepseek_coder_service import (
    CodeGenerationRequest,
    CodeGenerationResponse,
    DeepSeekCoderAPI,
    ProgrammingLanguage,
    get_deepseek_client,
)
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# 导入统一认证模块
from shared.auth.auth_middleware import create_auth_middleware, setup_cors

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = logging.getLogger('AthenaDeepSeekServer')

# FastAPI应用
app = FastAPI(
    title='Athena工作平台 - DeepSeek API',
    description='为Athena工作平台提供智能代码生成服务',
    version='1.0.0',
    docs_url='/docs',
    redoc_url='/redoc'
)

# CORS配置

# Pydantic模型
class CodeGenerationRequestModel(BaseModel):
    prompt: str = Field(..., description='代码生成提示词', min_length=1, max_length=4000)
    language: str = Field(..., description='编程语言')
    max_tokens: int = Field(default=2000, description='最大生成tokens数', ge=1, le=8000)
    temperature: float = Field(default=0.1, description='生成温度', ge=0.0, le=2.0)
    context: Optional[str] = Field(default=None, description='专利上下文信息(JSON格式)')

class PatentContextModel(BaseModel):
    title: str | None = None
    abstract: str | None = None
    field: str | None = None
    key_technologies: List[str] = []

class BatchCodeRequestModel(BaseModel):
    requests: List[CodeGenerationRequestModel] = Field(..., description='批量代码生成请求', min_items=1, max_items=10)

class CodeGenerationResponseModel(BaseModel):
    success: bool
    code: str
    explanation: str
    language: str
    tokens_used: int
    response_time: float
    timestamp: str
    error: str | None = None

class StatisticsResponseModel(BaseModel):
    total_requests: int
    total_tokens: int
    success_rate: float
    average_tokens_per_request: float
    model: str

class HealthResponseModel(BaseModel):
    status: str
    timestamp: str
    deepseek_connected: bool
    server_uptime: str

# 全局变量
server_start_time = datetime.now()
_deepseek_client: DeepSeekCoderAPI | None = None

async def get_deepseek_service() -> DeepSeekCoderAPI:
    """获取DeepSeek服务实例"""
    global _deepseek_client
    if _deepseek_client is None:
        _deepseek_client = DeepSeekCoderAPI()
        await _deepseek_client.__aenter__()
    return _deepseek_client

def parse_language(language_str: str) -> ProgrammingLanguage:
    """解析编程语言字符串"""
    language_map = {
        'python': ProgrammingLanguage.PYTHON,
        'py': ProgrammingLanguage.PYTHON,
        'javascript': ProgrammingLanguage.JAVASCRIPT,
        'js': ProgrammingLanguage.JAVASCRIPT,
        'java': ProgrammingLanguage.JAVA,
        'cpp': ProgrammingLanguage.CPP,
        'c++': ProgrammingLanguage.CPP,
        'csharp': ProgrammingLanguage.CSHARP,
        'c#': ProgrammingLanguage.CSHARP,
        'go': ProgrammingLanguage.GO,
        'rust': ProgrammingLanguage.RUST,
        'php': ProgrammingLanguage.PHP,
        'ruby': ProgrammingLanguage.RUBY,
        'swift': ProgrammingLanguage.SWIFT,
        'kotlin': ProgrammingLanguage.KOTLIN,
        'typescript': ProgrammingLanguage.TYPESCRIPT,
        'ts': ProgrammingLanguage.TYPESCRIPT
    }

    language_lower = language_str.lower()
    return language_map.get(language_lower, ProgrammingLanguage.PYTHON)  # 默认Python

@app.on_event('startup')
async def startup_event():
    """应用启动事件"""
    logger.info('🚀 Athena DeepSeek API服务器启动中...')

    # 初始化DeepSeek客户端
    try:
        client = await get_deepseek_service()
        connected = await client.test_connection()

        if connected:
            logger.info('✅ DeepSeek-Coder API连接成功!')
        else:
            logger.warning('⚠️ DeepSeek-Coder API连接失败，但服务器继续运行')

    except Exception as e:
        logger.error(f"❌ DeepSeek初始化失败: {str(e)}")

@app.on_event('shutdown')
async def shutdown_event():
    """应用关闭事件"""
    global _deepseek_client
    if _deepseek_client:
        await _deepseek_client.__aexit__(None, None, None)
        logger.info('🛑 Athena DeepSeek API服务器已关闭')

@app.get('/', response_model=Dict[str, str])
async def root():
    """根路径"""
    return {
        'message': 'Athena工作平台 - DeepSeek API服务',
        'version': '1.0.0',
        'docs': '/docs'
    }

@app.get('/health', response_model=HealthResponseModel)
async def health_check():
    """健康检查"""
    try:
        client = await get_deepseek_service()
        deepseek_connected = await client.test_connection()

        uptime = datetime.now() - server_start_time

        return HealthResponseModel(
            status='healthy' if deepseek_connected else 'degraded',
            timestamp=datetime.now().isoformat(),
            deepseek_connected=deepseek_connected,
            server_uptime=str(uptime).split('.')[0]  # 去掉微秒
        )
    except Exception as e:
        return HealthResponseModel(
            status='unhealthy',
            timestamp=datetime.now().isoformat(),
            deepseek_connected=False,
            server_uptime='unknown'
        )

@app.post('/generate-code', response_model=CodeGenerationResponseModel)
async def generate_code(request: CodeGenerationRequestModel):
    """生成单个代码请求"""
    try:
        client = await get_deepseek_service()

        # 解析编程语言
        language = parse_language(request.language)

        # 创建请求对象
        code_request = CodeGenerationRequest(
            prompt=request.prompt,
            language=language,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            context=request.context
        )

        # 调用DeepSeek API
        response = await client.generate_code(code_request)

        return CodeGenerationResponseModel(
            success=len(response.code) > 0,
            code=response.code,
            explanation=response.explanation,
            language=response.language,
            tokens_used=response.tokens_used,
            response_time=response.response_time,
            timestamp=response.timestamp.isoformat(),
            error=None if response.code else response.explanation
        )

    except Exception as e:
        logger.error(f"代码生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/generate-code/patent', response_model=CodeGenerationResponseModel)
async def generate_patent_code(
    prompt: str,
    language: str = 'python',
    patent_context: PatentContextModel = None
):
    """基于专利信息生成代码"""
    try:
        client = await get_deepseek_service()

        # 解析编程语言
        lang_enum = parse_language(language)

        # 构建专利上下文
        context_json = None
        if patent_context:
            context_json = json.dumps({
                'title': patent_context.title,
                'abstract': patent_context.abstract,
                'field': patent_context.field,
                'key_technologies': patent_context.key_technologies
            }, ensure_ascii=False)

        # 创建增强的提示词
        enhanced_prompt = f"""
基于以下专利技术需求，请生成相应的实现代码：

{prompt}

请确保代码体现专利的创新点和核心技术特点。
"""

        # 创建请求对象
        code_request = CodeGenerationRequest(
            prompt=enhanced_prompt,
            language=lang_enum,
            max_tokens=3000,
            temperature=0.1,
            context=context_json
        )

        # 调用DeepSeek API
        response = await client.generate_code(code_request)

        return CodeGenerationResponseModel(
            success=len(response.code) > 0,
            code=response.code,
            explanation=response.explanation,
            language=response.language,
            tokens_used=response.tokens_used,
            response_time=response.response_time,
            timestamp=response.timestamp.isoformat(),
            error=None if response.code else response.explanation
        )

    except Exception as e:
        logger.error(f"专利代码生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/generate-code/batch', response_model=List[CodeGenerationResponseModel])
async def generate_batch_code(request: BatchCodeRequestModel):
    """批量生成代码"""
    try:
        client = await get_deepseek_service()

        results = []

        for idx, req_model in enumerate(request.requests):
            try:
                language = parse_language(req_model.language)

                code_request = CodeGenerationRequest(
                    prompt=req_model.prompt,
                    language=language,
                    max_tokens=req_model.max_tokens,
                    temperature=req_model.temperature,
                    context=req_model.context
                )

                response = await client.generate_code(code_request)

                results.append(CodeGenerationResponseModel(
                    success=len(response.code) > 0,
                    code=response.code,
                    explanation=response.explanation,
                    language=response.language,
                    tokens_used=response.tokens_used,
                    response_time=response.response_time,
                    timestamp=response.timestamp.isoformat(),
                    error=None if response.code else response.explanation
                ))

            except Exception as e:
                logger.error(f"批量请求第{idx+1}项失败: {str(e)}")
                results.append(CodeGenerationResponseModel(
                    success=False,
                    code='',
                    explanation='',
                    language=req_model.language,
                    tokens_used=0,
                    response_time=0.0,
                    timestamp=datetime.now().isoformat(),
                    error=str(e)
                ))

        return results

    except Exception as e:
        logger.error(f"批量代码生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/languages', response_model=List[str])
async def get_supported_languages():
    """获取支持的编程语言列表"""
    return [lang.value for lang in ProgrammingLanguage]

@app.get('/statistics', response_model=StatisticsResponseModel)
async def get_usage_statistics():
    """获取使用统计信息"""
    try:
        client = await get_deepseek_service()
        stats = client.get_statistics()

        return StatisticsResponseModel(**stats)

    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/reset-statistics')
async def reset_statistics():
    """重置统计信息"""
    try:
        global _deepseek_client
        if _deepseek_client:
            _deepseek_client.total_requests = 0
            _deepseek_client.total_tokens = 0
            _deepseek_client.success_rate = 0.0

        return {'message': '统计信息已重置'}

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
        'athena_deepseek_server:app',
        host='0.0.0.0',
        port=8088,
        reload=True,
        log_level='info',
        access_log=True
    )