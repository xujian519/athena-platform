#!/usr/bin/env python3
"""
增强专利API服务
Enhanced Patent API Service
"""

import logging
import sys
from datetime import datetime
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# 添加认知层路径
sys.path.append('/Users/xujian/Athena工作平台/patent-platform/workspace/src/cognition')

app = FastAPI(
    title='增强专利分析API',
    description='集成认知决策层的专利分析服务',
    version='2.0.0'
)

# 数据模型
class PatentAnalysisRequest(BaseModel):
    patent_id: str
    title: str
    abstract: str
    description: str | None = ''
    claims: str | None = ''
    task_type: str | None = 'comprehensive_analysis'
    processing_mode: str | None = 'balanced'

class PatentAnalysisResponse(BaseModel):
    success: bool
    patent_id: str
    analysis_result: dict[str, Any] | None = None
    error_message: str | None = None
    timestamp: str

# 全局认知集成客户端
cognitive_client = None

async def get_cognitive_client():
    global cognitive_client
    if cognitive_client is None:
        try:
            from cognitive_integration_layer import CognitiveIntegrationLayer
            cognitive_client = CognitiveIntegrationLayer()
        except Exception as e:
            logger.info(f"认知层初始化失败: {e}")
            cognitive_client = None
    return cognitive_client

@app.get('/')
async def root():
    return {
        'message': '增强专利分析API服务',
        'version': '2.0.0',
        'status': 'running',
        'features': [
            '智能专利分析',
            '认知决策集成',
            '多模态理解',
            '大模型对话',
            '知识图谱'
        ]
    }

@app.get('/health')
async def health_check():
    """健康检查"""
    return {
        'status': 'healthy',
        'service': 'enhanced_patent_api',
        'version': '2.0.0',
        'cognitive_layer': 'connected' if cognitive_client else 'disconnected'
    }

@app.post('/api/v2/analyze', response_model=PatentAnalysisResponse)
async def analyze_patent(request: PatentAnalysisRequest):
    """专利分析主接口"""
    try:
        # 获取认知客户端
        client = await get_cognitive_client()
        if not client:
            raise HTTPException(status_code=503, detail='认知决策层服务不可用')

        # 构建专利数据
        patent_data = {
            'patent_id': request.patent_id,
            'title': request.title,
            'text': f"{request.abstract}\n\n{request.description or ''}\n\n{request.claims or ''}",
            'abstract': request.abstract,
            'claims': request.claims,
            'timestamp': datetime.now().isoformat()
        }

        # 处理请求
        from cognitive_integration_layer import CognitiveRequest, ProcessingMode

        processing_mode = ProcessingMode.BALANCED
        if request.processing_mode == 'fast':
            processing_mode = ProcessingMode.FAST
        elif request.processing_mode == 'comprehensive':
            processing_mode = ProcessingMode.COMPREHENSIVE

        cognitive_request = CognitiveRequest(
            request_id=f"api_{request.patent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            patent_data=patent_data,
            processing_mode=processing_mode,
            task_type=request.task_type
        )

        result = await client.process_request(cognitive_request)

        return PatentAnalysisResponse(
            success=True,
            patent_id=request.patent_id,
            analysis_result={
                'decision': result.results.get('decision', '分析完成'),
                'confidence': result.confidence,
                'summary': result.summary,
                'recommendations': result.recommendations,
                'modules_used': result.modules_used,
                'processing_time': result.processing_time,
                'detailed_results': result.results
            },
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        return PatentAnalysisResponse(
            success=False,
            patent_id=request.patent_id,
            error_message=str(e),
            timestamp=datetime.now().isoformat()
        )

@app.get('/api/v2/status')
async def get_system_status():
    """获取系统状态"""
    client = await get_cognitive_client()
    status = {
        'api_service': 'running',
        'cognitive_layer': 'connected' if client else 'disconnected',
        'timestamp': datetime.now().isoformat()
    }

    if client:
        try:
            cognitive_status = client.get_system_status()
            status['cognitive_status'] = cognitive_status
        except Exception as e:
            status['cognitive_error'] = str(e)

    return {'success': True, 'status': status}

if __name__ == '__main__':
    logger.info('🚀 启动增强专利API服务...')
    uvicorn.run(app, host='0.0.0.0', port=8000, log_level='info')
