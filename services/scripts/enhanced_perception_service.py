#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强感知服务
Enhanced Perception Service

提供优化后的多模态感知处理服务

作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import asyncio
from core.async_main import async_main
import json
import logging
from core.logging_config import setup_logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

# 添加项目路径
sys.path.insert(0, '/Users/xujian/Athena工作平台')

import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# 感知模块导入
from core.perception import InputType, PerceptionEngine, PerceptionResult

# 导入统一认证模块
from shared.auth.auth_middleware import create_auth_middleware, setup_cors

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

# FastAPI应用
app = FastAPI(
    title='Athena增强感知服务',
    description='提供企业级多模态感知处理能力',
    version='1.0.0',
    docs_url='/docs',
    openapi_url='/openapi.json'
)

# CORS中间件

# 全局感知引擎
perception_engine: PerceptionEngine | None = None

# 请求模型
class TextInputRequest(BaseModel):
    text: str = Field(..., description='输入文本')
    options: Optional[Dict[str, Any]] = Field(default={}, description='处理选项')

class MultimodalInputRequest(BaseModel):
    data: Dict[str, Any] = Field(..., description='多模态数据')
    options: Optional[Dict[str, Any]] = Field(default={}, description='处理选项')

class BatchProcessRequest(BaseModel):
    items: List[Dict[str, Any]] = Field(..., description='批量处理项目')
    options: Optional[Dict[str, Any]] = Field(default={}, description='处理选项')

# 响应模型
class PerceptionResponse(BaseModel):
    success: bool
    input_type: str
    confidence: float
    processed_content: Optional[Any]
    features: Dict[str, Any]
    metadata: Dict[str, Any]
    processing_time: float
    timestamp: str

class StatusResponse(BaseModel):
    status: str
    processor_count: int
    available_processors: List[str]
    engine_initialized: bool
    optimization_enabled: bool
    monitoring_enabled: bool

@app.on_event('startup')
async def startup_event():
    """启动事件"""
    global perception_engine

    try:
        logger.info('🚀 启动增强感知服务...')

        # 创建感知引擎
        perception_engine = PerceptionEngine(
            agent_id='enhanced_perception_service',
            config={
                'use_enhanced_multimodal': True,  # 启用增强多模态处理器
                'performance': {
                    'enable_cache': True,
                    'enable_batch_processing': True,
                    'cache_ttl': 3600
                },
                'monitoring': {
                    'enabled': True,
                    'collect_interval': 10,
                    'health_check_interval': 30
                },
                'multimodal': {
                    'fusion_strategy': 'attention_fusion',
                    'enable_cross_modal': True,
                    'max_modalities': 5,
                    'min_confidence': 0.3
                }
            }
        )

        # 初始化感知引擎
        await perception_engine.initialize()

        logger.info('✅ 增强感知服务启动成功')
        logger.info(f"📊 可用处理器: {[p.value for p in perception_engine.processors.keys()]}")

    except Exception as e:
        logger.error(f"❌ 增强感知服务启动失败: {e}")
        raise

@app.on_event('shutdown')
async def shutdown_event():
    """关闭事件"""
    global perception_engine

    if perception_engine:
        try:
            logger.info('🔄 关闭增强感知服务...')
            await perception_engine.shutdown()
            perception_engine = None
            logger.info('✅ 增强感知服务已关闭')
        except Exception as e:
            logger.error(f"❌ 关闭增强感知服务失败: {e}")

@app.get('/health')
async def health_check():
    """健康检查"""
    return {
        'status': 'healthy',
        'service': 'enhanced_perception',
        'timestamp': datetime.now().isoformat()
    }

@app.get('/status', response_model=StatusResponse)
async def get_status():
    """获取服务状态"""
    if not perception_engine:
        raise HTTPException(status_code=503, detail='感知服务未初始化')

    try:
        status = await perception_engine.get_status()

        return StatusResponse(
            status='running' if perception_engine.initialized else 'stopped',
            processor_count=status['processor_count'],
            available_processors=[p.value for p in status['available_processors']],
            engine_initialized=status['initialized'],
            optimization_enabled=getattr(perception_engine, 'optimizer') is not None,
            monitoring_enabled=getattr(perception_engine, 'monitor') is not None
        )
    except Exception as e:
        logger.error(f"获取状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/process/text', response_model=PerceptionResponse)
async def process_text(request: TextInputRequest):
    """处理文本输入"""
    if not perception_engine:
        raise HTTPException(status_code=503, detail='感知服务未初始化')

    try:
        start_time = datetime.now()

        # 处理文本
        result = await perception_engine.process(request.text, InputType.TEXT.value)

        # 计算处理时间
        processing_time = (datetime.now() - start_time).total_seconds()

        return PerceptionResponse(
            success=True,
            input_type=result.input_type.value,
            confidence=result.confidence,
            processed_content=result.processed_content,
            features=result.features,
            metadata=result.metadata,
            processing_time=processing_time,
            timestamp=result.timestamp.isoformat()
        )

    except Exception as e:
        logger.error(f"文本处理失败: {e}")
        return PerceptionResponse(
            success=False,
            input_type='text',
            confidence=0.0,
            processed_content=None,
            features={'error': str(e)},
            metadata={'error': True},
            processing_time=0.0,
            timestamp=datetime.now().isoformat()
        )

@app.post('/process/multimodal', response_model=PerceptionResponse)
async def process_multimodal(request: MultimodalInputRequest):
    """处理多模态输入"""
    if not perception_engine:
        raise HTTPException(status_code=503, detail='感知服务未初始化')

    try:
        start_time = datetime.now()

        # 处理多模态数据
        result = await perception_engine.process(request.data, 'multimodal')

        # 计算处理时间
        processing_time = (datetime.now() - start_time).total_seconds()

        return PerceptionResponse(
            success=True,
            input_type=result.input_type.value,
            confidence=result.confidence,
            processed_content=result.processed_content,
            features=result.features,
            metadata=result.metadata,
            processing_time=processing_time,
            timestamp=result.timestamp.isoformat()
        )

    except Exception as e:
        logger.error(f"多模态处理失败: {e}")
        return PerceptionResponse(
            success=False,
            input_type='multimodal',
            confidence=0.0,
            processed_content=None,
            features={'error': str(e)},
            metadata={'error': True},
            processing_time=0.0,
            timestamp=datetime.now().isoformat()
        )

@app.post('/process/batch', response_model=List[PerceptionResponse])
async def process_batch(request: BatchProcessRequest):
    """批量处理"""
    if not perception_engine:
        raise HTTPException(status_code=503, detail='感知服务未初始化')

    try:
        results = []

        # 并发处理
        tasks = []
        for item in request.items:
            input_type = item.get('input_type', 'text')
            data = item.get('data', '')

            task = perception_engine.process(data, input_type)
            tasks.append(task)

        # 等待所有任务完成
        process_results = await asyncio.gather(*tasks, return_exceptions=True)

        # 转换结果
        for i, result in enumerate(process_results):
            if isinstance(result, Exception):
                results.append(PerceptionResponse(
                    success=False,
                    input_type=request.items[i].get('input_type', 'unknown'),
                    confidence=0.0,
                    processed_content=None,
                    features={'error': str(result)},
                    metadata={'error': True},
                    processing_time=0.0,
                    timestamp=datetime.now().isoformat()
                ))
            else:
                results.append(PerceptionResponse(
                    success=True,
                    input_type=result.input_type.value,
                    confidence=result.confidence,
                    processed_content=result.processed_content,
                    features=result.features,
                    metadata=result.metadata,
                    processing_time=0.0,  # 简化处理
                    timestamp=result.timestamp.isoformat()
                ))

        return results

    except Exception as e:
        logger.error(f"批量处理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/performance/dashboard')
async def get_performance_dashboard():
    """获取性能仪表板"""
    if not perception_engine:
        raise HTTPException(status_code=503, detail='感知服务未初始化')

    try:
        dashboard = await perception_engine.get_performance_dashboard()
        return dashboard
    except Exception as e:
        logger.error(f"获取性能仪表板失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/performance/report')
async def get_performance_report(time_range: int = 3600):
    """获取性能报告"""
    if not perception_engine:
        raise HTTPException(status_code=503, detail='感知服务未初始化')

    try:
        report = await perception_engine.get_performance_report(time_range)
        return report
    except Exception as e:
        logger.error(f"获取性能报告失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/processors')
async def get_processors():
    """获取处理器列表"""
    if not perception_engine:
        raise HTTPException(status_code=503, detail='感知服务未初始化')

    try:
        status = await perception_engine.get_status()
        processors = []

        for input_type, processor_info in status['processor_status'].items():
            processors.append({
                'type': input_type,
                'processor_id': processor_info['processor_id'],
                'initialized': processor_info['initialized'],
                'config_keys': processor_info['config_keys']
            })

        return {'processors': processors}
    except Exception as e:
        logger.error(f"获取处理器列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    # 服务配置
    HOST = '0.0.0.0'
    PORT = 8009

    logger.info(f"🌟 启动Athena增强感知服务...")
    logger.info(f"📊 服务地址: http://{HOST}:{PORT}")
    logger.info(f"📚 API文档: http://{HOST}:{PORT}/docs")

    # 启动服务
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level='info'
    )