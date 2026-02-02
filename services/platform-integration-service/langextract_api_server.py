#!/usr/bin/env python3
"""
LangExtract API服务器
为Athena平台提供统一的结构化信息提取API服务
"""

import asyncio
from core.async_main import async_main
import json
import logging
from core.logging_config import setup_logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from langextract_integration_service import (
    ExtractionRequest,
    IntegrationMode,
    get_langextract_integration_service,
)
from pydantic import BaseModel, Field

# 导入统一认证模块
from shared.auth.auth_middleware import create_auth_middleware, setup_cors

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

# 创建FastAPI应用
app = FastAPI(
    title='Athena平台LangExtract API服务',
    description='企业级结构化信息提取智能API服务',
    version='1.0.0'
)

# 添加CORS中间件

# 初始化服务
langextract_service = None

# 请求模型
class ExtractionTaskRequest(BaseModel):
    """信息提取任务请求"""
    user_input: str = Field(..., description='用户输入描述')
    mode: str = Field(default='xiaonuo_auto', description='执行模式')
    text_or_documents: Optional[str] = Field(None, description='待提取的文本或文档')
    scenario: Optional[str] = Field(None, description='指定提取场景')
    custom_prompt: Optional[str] = Field(None, description='自定义提取提示')
    config: Dict[str, Any] = Field(default_factory=dict, description='提取配置')
    context: Dict[str, Any] = Field(default_factory=dict, description='上下文信息')
    callback_url: Optional[str] = Field(None, description='回调URL')
    priority: int = Field(default=1, description='任务优先级')

class BatchExtractionRequest(BaseModel):
    """批量提取请求"""
    requests: List[ExtractionTaskRequest]
    max_concurrent: int = Field(default=5, description='最大并发数')

class PatentAnalysisRequest(BaseModel):
    """专利分析请求"""
    patent_text: str = Field(..., description='专利文本')
    analysis_type: str = Field(default='full', description='分析类型')

class XiaoNuoChatRequest(BaseModel):
    """小诺聊天请求"""
    message: str = Field(..., description='用户消息')
    context: Dict[str, Any] = Field(default_factory=dict, description='对话上下文')
    text_or_documents: Optional[str] = Field(None, description='待分析文本')

class VisualizationRequest(BaseModel):
    """可视化请求"""
    extractions: List[Dict[str, Any]] = Field(..., description='提取结果')
    output_path: Optional[str] = Field(None, description='输出路径')

# 响应模型
class APIResponse(BaseModel):
    """API响应基类"""
    success: bool
    message: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    data: Any | None = None
    error: str | None = None

@app.on_event('startup')
async def startup_event():
    """应用启动事件"""
    global langextract_service
    logger.info('启动LangExtract API服务...')

    langextract_service = get_langextract_integration_service()
    await langextract_service.initialize()

    logger.info('LangExtract API服务启动成功')

@app.on_event('shutdown')
async def shutdown_event():
    """应用关闭事件"""
    logger.info('正在关闭LangExtract API服务...')

    if langextract_service:
        await langextract_service.shutdown()

    logger.info('LangExtract API服务已关闭')

@app.get('/')
async def root():
    """根路径"""
    return {
        'service': 'Athena平台LangExtract API服务',
        'version': '1.0.0',
        'status': 'running',
        'features': [
            '智能场景识别',
            '小诺自动控制',
            '多模式执行',
            '批量处理',
            '专利业务增强',
            '可视化结果'
        ],
        'timestamp': datetime.now().isoformat()
    }

@app.get('/api/v1/health')
async def health_check():
    """健康检查"""
    try:
        if langextract_service:
            status = await langextract_service.get_service_status()
            return {
                'status': 'healthy' if status['status'] == 'running' else 'unhealthy',
                'service': 'LangExtractIntegrationService',
                'version': '1.0.0',
                'components': status['components'],
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'status': 'unhealthy',
                'error': '服务未初始化',
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@app.post('/api/v1/extraction/execute')
async def execute_extraction(request: ExtractionTaskRequest):
    """执行信息提取任务"""
    try:
        # 转换模式
        try:
            mode = IntegrationMode(request.mode)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的执行模式: {request.mode}"
            )

        # 创建提取请求
        extraction_request = ExtractionRequest(
            request_id=str(uuid.uuid4()),
            mode=mode,
            user_input=request.user_input,
            text_or_documents=request.text_or_documents,
            scenario=request.scenario,
            custom_prompt=request.custom_prompt,
            config=request.config,
            context=request.context,
            callback_url=request.callback_url,
            priority=request.priority
        )

        # 执行提取
        response = await langextract_service.process_request(extraction_request)

        return APIResponse(
            success=response.success,
            message='信息提取完成' if response.success else '信息提取失败',
            data={
                'request_id': response.request_id,
                'execution_time': response.execution_time,
                'result': response.result,
                'metadata': response.metadata
            },
            error=response.error
        )

    except Exception as e:
        logger.error(f"执行提取任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/api/v1/extraction/batch')
async def execute_batch_extraction(request: BatchExtractionRequest):
    """批量执行信息提取任务"""
    try:
        # 转换请求
        extraction_requests = []
        for req in request.requests:
            try:
                mode = IntegrationMode(req.mode)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"不支持的执行模式: {req.mode}"
                )

            extraction_requests.append(
                ExtractionRequest(
                    request_id=str(uuid.uuid4()),
                    mode=mode,
                    user_input=req.user_input,
                    text_or_documents=req.text_or_documents,
                    scenario=req.scenario,
                    custom_prompt=req.custom_prompt,
                    config=req.config,
                    context=req.context,
                    callback_url=req.callback_url,
                    priority=req.priority
                )
            )

        # 批量执行
        responses = await langextract_service.batch_process(
            extraction_requests,
            request.max_concurrent
        )

        # 转换响应格式
        results = []
        for resp in responses:
            results.append({
                'request_id': resp.request_id,
                'success': resp.success,
                'result': resp.result,
                'error': resp.error,
                'execution_time': resp.execution_time,
                'metadata': resp.metadata
            })

        successful_count = sum(1 for r in results if r['success'])

        return APIResponse(
            success=successful_count > 0,
            message=f"批量处理完成，成功: {successful_count}/{len(results)}",
            data={
                'results': results,
                'summary': {
                    'total_requests': len(results),
                    'successful_requests': successful_count,
                    'success_rate': successful_count / len(results)
                }
            }
        )

    except Exception as e:
        logger.error(f"批量执行提取任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/api/v1/xiaonuo/chat')
async def xiaonuo_chat(request: XiaoNuoChatRequest):
    """小诺智能聊天接口"""
    try:
        # 使用小诺自动模式
        extraction_request = ExtractionRequest(
            request_id=str(uuid.uuid4()),
            mode=IntegrationMode.XIAONUO_AUTO,
            user_input=request.message,
            text_or_documents=request.text_or_documents,
            context=request.context
        )

        # 执行提取
        response = await langextract_service.process_request(extraction_request)

        return APIResponse(
            success=response.success,
            message='小诺智能分析完成' if response.success else '小诺智能分析失败',
            data={
                'request_id': response.request_id,
                'execution_time': response.execution_time,
                'xiaonuo_analysis': response.metadata.get('xiaonuo_analysis'),
                'result': response.result,
                'suggestions': response.metadata.get('suggestions', [])
            },
            error=response.error
        )

    except Exception as e:
        logger.error(f"小诺聊天失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/api/v1/xiaonuo/analyze')
async def xiaonuo_analyze(
    user_input: str,
    context: Optional[Dict[str, Any]] = None
):
    """小诺智能分析接口（仅分析，不执行）"""
    try:
        from xiaonuo_langextract_control import get_xiaonuo_langextract_controller

        xiaonuo_controller = get_xiaonuo_langextract_controller()
        analysis = await xiaonuo_controller.analyze_request(user_input, context)

        return APIResponse(
            success=True,
            message='小诺智能分析完成',
            data=analysis.__dict__
        )

    except Exception as e:
        logger.error(f"小诺分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/api/v1/patent/analyze')
async def analyze_patent(request: PatentAnalysisRequest):
    """专利文档专业分析"""
    try:
        result = await langextract_service.enhance_patent_business(
            request.patent_text,
            request.analysis_type
        )

        return APIResponse(
            success=result['success'],
            message='专利分析完成' if result['success'] else '专利分析失败',
            data=result,
            error=result.get('error')
        )

    except Exception as e:
        logger.error(f"专利分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/api/v1/scenarios')
async def get_available_scenarios():
    """获取可用的提取场景"""
    try:
        from common_tools.langextract_tool import get_langextract_tool

        tool = get_langextract_tool()
        scenarios = await tool.list_scenarios()

        return APIResponse(
            success=True,
            message='获取场景列表成功',
            data=scenarios
        )

    except Exception as e:
        logger.error(f"获取场景列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/api/v1/modes')
async def get_available_modes():
    """获取可用的执行模式"""
    try:
        modes = [
            {
                'value': mode.value,
                'name': mode.value.replace('_', ' ').title(),
                'description': self._get_mode_description(mode)
            }
            for mode in IntegrationMode
        ]

        return APIResponse(
            success=True,
            message='获取执行模式成功',
            data={'modes': modes}
        )

    except Exception as e:
        logger.error(f"获取执行模式失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _get_mode_description(mode: IntegrationMode) -> str:
    """获取模式描述"""
    descriptions = {
        IntegrationMode.XIAONUO_AUTO: '小诺全自动模式 - 智能分析并自动执行提取',
        IntegrationMode.XIAONUO_SEMI: '小诺半自动模式 - 提供建议，用户确认后执行',
        IntegrationMode.DIRECT_API: '直接API模式 - 完全控制参数，精确执行',
        IntegrationMode.CRAWLER_ENHANCED: '爬虫增强模式 - 自动获取内容并分析',
        IntegrationMode.BATCH_PROCESSING: '批量处理模式 - 高效处理大量文档'
    }
    return descriptions.get(mode, '未知模式')

@app.post('/api/v1/visualization/generate')
async def generate_visualization(request: VisualizationRequest):
    """生成交互式可视化"""
    try:
        from common_tools.langextract_tool import get_langextract_tool

        tool = get_langextract_tool()
        html_content = await tool.visualize_results(
            request.extractions,
            request.output_path
        )

        return APIResponse(
            success=True,
            message='可视化生成成功',
            data={
                'html_content': html_content if not request.output_path else 'saved_to_file',
                'output_path': request.output_path,
                'extraction_count': len(request.extractions)
            }
        )

    except Exception as e:
        logger.error(f"生成可视化失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/api/v1/business/integrations')
async def get_business_integrations():
    """获取业务集成信息"""
    try:
        integrations = await langextract_service.get_business_integrations()

        return APIResponse(
            success=True,
            message='获取业务集成信息成功',
            data=integrations
        )

    except Exception as e:
        logger.error(f"获取业务集成信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/api/v1/statistics')
async def get_extraction_statistics():
    """获取提取统计信息"""
    try:
        from xiaonuo_langextract_control import get_xiaonuo_langextract_controller

        xiaonuo_controller = get_xiaonuo_langextract_controller()
        xiaonuo_stats = await xiaonuo_controller.get_extraction_statistics()

        service_status = await langextract_service.get_service_status()

        return APIResponse(
            success=True,
            message='获取统计信息成功',
            data={
                'xiaonuo_statistics': xiaonuo_stats,
                'service_statistics': service_status['statistics'],
                'performance_metrics': {
                    'total_requests': service_status['statistics']['total_requests'],
                    'success_rate': (
                        service_status['statistics']['successful_requests'] /
                        max(service_status['statistics']['total_requests'], 1)
                    )
                }
            }
        )

    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/api/v1/feedback')
async def submit_feedback(
    task_id: str,
    accuracy_rating: float = Query(..., ge=0.0, le=1.0),
    satisfaction_rating: float = Query(..., ge=0.0, le=1.0),
    comments: str | None = None
):
    """提交任务反馈"""
    try:
        from xiaonuo_langextract_control import get_xiaonuo_langextract_controller

        xiaonuo_controller = get_xiaonuo_langextract_controller()

        feedback = {
            'accuracy_rating': accuracy_rating,
            'satisfaction_rating': satisfaction_rating,
            'comments': comments,
            'timestamp': datetime.now().isoformat()
        }

        success = await xiaonuo_controller.learn_from_feedback(task_id, feedback)

        return APIResponse(
            success=success,
            message='反馈提交成功' if success else '反馈提交失败',
            data={'task_id': task_id, 'feedback': feedback}
        )

    except Exception as e:
        logger.error(f"提交反馈失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 专利专用接口
@app.post('/api/v1/patent/claims/analyze')
async def analyze_patent_claims(patent_text: str):
    """分析专利权利要求"""
    try:
        # 使用权利要求分析提示
        result = await langextract_service.langextract_tool.execute_custom_extraction(
            text_or_documents=patent_text,
            prompt_description="""
            从专利权利要求书中提取以下信息：
            1. 独立权利要求的技术特征
            2. 从属权利要求的引用关系
            3. 权利要求的保护范围
            4. 关键技术术语定义
            5. 权利要求的层次结构
            """,
            config={'model_id': 'gemini-2.5-flash'}
        )

        return APIResponse(
            success=result.success,
            message='权利要求分析完成' if result.success else '权利要求分析失败',
            data={
                'extractions': result.extractions,
                'stats': result.stats
            },
            error=result.error
        )

    except Exception as e:
        logger.error(f"权利要求分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/api/v1/patent/technical/extract')
async def extract_technical_features(patent_text: str):
    """提取专利技术特征"""
    try:
        result = await langextract_service.langextract_tool.execute_custom_extraction(
            text_or_documents=patent_text,
            prompt_description="""
            从专利文档中提取技术特征：
            1. 核心技术方案
            2. 技术问题解决方案
            3. 关键技术参数
            4. 创新技术点
            5. 技术效果和优势
            """,
            config={'model_id': 'gemini-2.5-flash'}
        )

        return APIResponse(
            success=result.success,
            message='技术特征提取完成' if result.success else '技术特征提取失败',
            data={
                'extractions': result.extractions,
                'stats': result.stats
            },
            error=result.error
        )

    except Exception as e:
        logger.error(f"技术特征提取失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/api/v1/docs')
async def get_api_documentation():
    """获取API文档"""
    return {
        'title': 'LangExtract API文档',
        'version': '1.0.0',
        'description': 'Athena平台结构化信息提取API服务',
        'endpoints': {
            'extraction': {
                'execute': '/api/v1/extraction/execute - 执行信息提取',
                'batch': '/api/v1/extraction/batch - 批量执行提取'
            },
            'xiaonuo': {
                'chat': '/api/v1/xiaonuo/chat - 小诺智能聊天',
                'analyze': '/api/v1/xiaonuo/analyze - 小诺智能分析'
            },
            'patent': {
                'analyze': '/api/v1/patent/analyze - 专利文档分析',
                'claims': '/api/v1/patent/claims/analyze - 权利要求分析',
                'technical': '/api/v1/patent/technical/extract - 技术特征提取'
            },
            'utilities': {
                'scenarios': '/api/v1/scenarios - 获取可用场景',
                'modes': '/api/v1/modes - 获取执行模式',
                'visualization': '/api/v1/visualization/generate - 生成可视化',
                'statistics': '/api/v1/statistics - 获取统计信息',
                'feedback': '/api/v1/feedback - 提交反馈'
            }
        },
        'examples': {
            'simple_extraction': {
                'url': '/api/v1/extraction/execute',
                'method': 'POST',
                'body': {
                    'user_input': '分析这份技术文档的关键技术点',
                    'text_or_documents': '文档内容...',
                    'mode': 'xiaonuo_auto'
                }
            },
            'patent_analysis': {
                'url': '/api/v1/patent/analyze',
                'method': 'POST',
                'body': {
                    'patent_text': '专利全文...',
                    'analysis_type': 'full'
                }
            }
        }
    }

if __name__ == '__main__':
    # 直接运行服务
    uvicorn.run(
        'langextract_api_server:app',
        host='0.0.0.0',
        port=8016,
        reload=True,
        log_level='info'
    )