#!/usr/bin/env python3
"""
Athena工作平台 - GLM全系列模型API服务器
提供智谱AI全系列模型的统一接入服务
"""

import base64
import logging
from datetime import datetime
from typing import Any

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from glm_unified_client import (
    GLMModel,
    GLMRequest,
    ModalityType,
    ZhipuAIUnifiedClient,
)
from pydantic import BaseModel, Field

# 导入统一认证模块

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = logging.getLogger('AthenaGLMFullSuite')

# FastAPI应用
app = FastAPI(
    title='Athena工作平台 - GLM全系列模型API',
    description='提供智谱AI全系列模型的统一服务：GLM-4.6、GLM-4.6-Code、GLM-4V、CogVideoX、CogView等',
    version='1.0.0',
    docs_url='/docs',
    redoc_url='/redoc'
)

# CORS配置

# Pydantic模型
class TextRequest(BaseModel):
    messages: list[dict[str, str]] = Field(..., description='对话消息')
    model: str = Field(default='glm-4.6', description='指定模型')
    max_tokens: int = Field(default=4000, description='最大生成tokens')
    temperature: float = Field(default=0.3, description='生成温度')
    enable_thinking: bool = Field(default=False, description='是否启用思考模式')
    thinking_type: str | None = Field(default=None, description='思考类型')

class PatentAnalysisRequest(BaseModel):
    title: str = Field(..., description='专利标题')
    abstract: str = Field(..., description='专利摘要')
    technical_field: str = Field(default='', description='技术领域')
    background: str = Field(default='', description='背景技术')
    invention: str = Field(default='', description='发明内容')
    model: str = Field(default='glm-4.6', description='指定模型')
    enable_thinking: bool = Field(default=True, description='是否启用思考模式')

class CodeGenerationRequest(BaseModel):
    prompt: str = Field(..., description='代码生成提示')
    language: str = Field(default='python', description='编程语言')
    model: str = Field(default='glm-4.6-code', description='指定模型')
    max_tokens: int = Field(default=4000, description='最大生成tokens')
    enable_thinking: bool = Field(default=True, description='是否启用思考过程')

class ImageGenerationRequest(BaseModel):
    prompt: str = Field(..., description='图像生成提示')
    model: str = Field(default='cogview-4', description='指定模型')
    size: str = Field(default='1024*1024', description='图像尺寸')
    style: str = Field(default='realistic', description='图像风格')

class VideoGenerationRequest(BaseModel):
    prompt: str = Field(..., description='视频生成提示')
    model: str = Field(default='cogvideox', description='指定模型')
    duration: int = Field(default=5, description='视频时长(秒)')
    resolution: str = Field(default='720p', description='视频分辨率')
    num_frames: int = Field(default=16, description='视频帧数')

class MultimodalRequest(BaseModel):
    text: str = Field(..., description='文本内容')
    model: str = Field(default='glm-4v-plus', description='指定模型')
    max_tokens: int = Field(default=2000, description='最大生成tokens')

class GLMResponseModel(BaseModel):
    success: bool
    content: str
    thinking_process: str | None = None
    modality: str
    model: str
    usage: dict = {}
    response_time: float
    timestamp: str
    images: list[str] | None = None
    videos: list[str] | None = None
    error: str | None = None

class ModelCapabilitiesResponse(BaseModel):
    model: str
    modalities: list[str]
    specialties: list[str]
    context_length: int
    cost_per_1k: float
    recommended_for: list[str]

class StatisticsResponse(BaseModel):
    total_requests: int
    total_cost: float
    model_usage: dict[str, int]
    modality_usage: dict[str, int]
    success_rate: float

# 全局变量
server_start_time = datetime.now()
_glm_client: ZhipuAIUnifiedClient | None = None

async def get_glm_service() -> ZhipuAIUnifiedClient:
    """获取GLM服务实例"""
    global _glm_client
    if _glm_client is None:
        _glm_client = ZhipuAIUnifiedClient()
        await _glm_client.__aenter__()
    return _glm_client

@app.on_event('startup')
async def startup_event():
    """应用启动事件"""
    logger.info('🚀 Athena GLM全系列模型API服务器启动中...')

    try:
        client = await get_glm_service()
        capabilities = client.get_model_capabilities()

        logger.info('✅ GLM全系列模型API连接成功!')
        logger.info(f"📋 支持的模型: {list(capabilities.keys())}")

        # 显示支持的能力
        capabilities_list = []
        for model, caps in capabilities.items():
            capabilities_list.append(f"{model}: {caps['specialties']}")

        logger.info(f"🎯 模型能力概览: {len(capabilities_list)}种模型组合")

    except Exception as e:
        logger.error(f"❌ GLM全系列模型初始化失败: {str(e)}")

@app.on_event('shutdown')
async def shutdown_event():
    """应用关闭事件"""
    global _glm_client
    if _glm_client:
        await _glm_client.__aexit__(None, None, None)
        logger.info('🛑 Athena GLM全系列模型API服务器已关闭')

@app.get('/', response_model=dict[str, Any])
async def root():
    """根路径"""
    return {
        'message': 'Athena工作平台 - GLM全系列模型API服务',
        'version': '1.0.0',
        'supported_models': [
            'glm-4.6 - 推理专家',
            'glm-4.6-code - 编程专家',
            'glm-4-flash - 快速响应',
            'glm-4v-plus - 多模态理解',
            'cogvideox - 视频生成',
            'cogview-4 - 文生图(支持汉字)',
            'cogview-3-plus - 高质量文生图'
        ],
        'capabilities': [
            '深度推理与思考',
            '专业代码生成',
            '多模态理解',
            '图像生成',
            '视频生成',
            '专利专业分析',
            '智能体协调',
            '长文档处理'
        ],
        'docs': '/docs'
    }

@app.get('/health', response_model=dict[str, Any])
async def health_check():
    """健康检查"""
    try:
        client = await get_glm_service()
        stats = client.get_statistics()

        return {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'models_available': list(client.get_model_capabilities().keys()),
            'total_requests': stats['total_requests'],
            'success_rate': f"{stats['success_rate']:.2%}",
            'server_uptime': str(datetime.now() - server_start_time).split('.')[0]
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }

@app.post('/chat', response_model=GLMResponseModel)
async def chat_completion(request: TextRequest):
    """通用对话接口"""
    try:
        client = await get_glm_service()

        # 解析模型
        try:
            model = GLMModel(request.model)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"不支持的模型: {request.model}") from None

        glm_request = GLMRequest(
            model=model,
            messages=request.messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            enable_thinking=request.enable_thinking,
            thinking_type=request.thinking_type
        )

        response = await client.generate_response(glm_request)

        return GLMResponseModel(
            success=response.success,
            content=response.content,
            thinking_process=response.thinking_process,
            modality=response.modality.value,
            model=response.model,
            usage=response.usage,
            response_time=response.response_time,
            timestamp=response.timestamp.isoformat(),
            error=response.error
        )

    except Exception as e:
        logger.error(f"对话请求失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.post('/patent-analysis', response_model=GLMResponseModel)
async def patent_analysis(request: PatentAnalysisRequest):
    """专利分析接口"""
    try:
        client = await get_glm_service()

        # 构建专利分析消息
        system_prompt = """你是一位专业的专利分析师，具有深厚的技术背景和法律知识。请对给定的专利信息进行深度分析，包括：
1. 技术创新性评估
2. 专利保护范围分析
3. 实施可行性评估
4. 商业价值分析
5. 竞争优势分析
6. 潜在风险评估

请使用结构化的方式呈现分析结果，并提供具体的建议。"""

        user_prompt = f"""请分析以下专利信息：

专利标题：{request.title}
专利摘要：{request.abstract}
技术领域：{request.technical_field}
背景技术：{request.background}
发明内容：{request.invention}

请提供全面而深入的专利分析报告。"""

        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ]

        # 解析模型
        try:
            model = GLMModel(request.model)
        except ValueError:
            model = GLMModel.GLM_4_6  # 默认使用推理模型

        glm_request = GLMRequest(
            model=model,
            messages=messages,
            max_tokens=6000,
            temperature=0.2,
            enable_thinking=request.enable_thinking,
            thinking_type='step_by_step'
        )

        response = await client.generate_response(glm_request)

        return GLMResponseModel(
            success=response.success,
            content=response.content,
            thinking_process=response.thinking_process,
            modality=response.modality.value,
            model=response.model,
            usage=response.usage,
            response_time=response.response_time,
            timestamp=response.timestamp.isoformat(),
            error=response.error
        )

    except Exception as e:
        logger.error(f"专利分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.post('/code-generation', response_model=GLMResponseModel)
async def code_generation(request: CodeGenerationRequest):
    """代码生成接口"""
    try:
        client = await get_glm_service()

        # 解析模型
        try:
            model = GLMModel(request.model)
        except ValueError:
            model = GLMModel.GLM_4_6_CODE  # 默认使用代码模型

        system_prompt = f"""你是一个顶级的{request.language}开发工程师，请在生成代码时展示你的专业能力。

代码要求：
- 遵循{request.language}最佳实践
- 包含详细的注释和文档字符串
- 考虑错误处理和边界情况
- 优化性能和可读性
- 提供使用示例

请遵循以下步骤：
1. 理解需求
2. 设计解决方案
3. 实现代码
4. 添加文档
5. 提供示例"""

        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': request.prompt}
        ]

        glm_request = GLMRequest(
            model=model,
            messages=messages,
            max_tokens=request.max_tokens,
            temperature=0.1,
            enable_thinking=request.enable_thinking,
            thinking_type='step_by_step'
        )

        response = await client.generate_response(glm_request)

        return GLMResponseModel(
            success=response.success,
            content=response.content,
            thinking_process=response.thinking_process,
            modality=response.modality.value,
            model=response.model,
            usage=response.usage,
            response_time=response.response_time,
            timestamp=response.timestamp.isoformat(),
            error=response.error
        )

    except Exception as e:
        logger.error(f"代码生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.post('/generate-image', response_model=GLMResponseModel)
async def generate_image(request: ImageGenerationRequest):
    """图像生成接口"""
    try:
        client = await get_glm_service()

        # 解析模型
        try:
            model = GLMModel(request.model)
        except ValueError:
            model = GLMModel.COGVIEW_4  # 默认使用文生图模型

        messages = [{'role': 'user', 'content': request.prompt}]

        glm_request = GLMRequest(
            model=model,
            messages=messages,
            modality=ModalityType.IMAGE,
            image_size=request.size
        )

        response = await client.generate_response(glm_request)

        return GLMResponseModel(
            success=response.success,
            content=response.content,
            modality=response.modality.value,
            model=response.model,
            usage=response.usage,
            response_time=response.response_time,
            timestamp=response.timestamp.isoformat(),
            images=response.images,
            error=response.error
        )

    except Exception as e:
        logger.error(f"图像生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.post('/generate-video', response_model=GLMResponseModel)
async def generate_video(request: VideoGenerationRequest):
    """视频生成接口"""
    try:
        client = await get_glm_service()

        # 解析模型
        try:
            model = GLMModel(request.model)
        except ValueError:
            model = GLMModel.COGVIDEOX  # 默认使用视频生成模型

        messages = [{'role': 'user', 'content': request.prompt}]

        glm_request = GLMRequest(
            model=model,
            messages=messages,
            modality=ModalityType.VIDEO,
            video_duration=request.duration,
            resolution=request.resolution,
            num_frames=request.num_frames,
            video_prompt=request.prompt  # 确保视频提示使用
        )

        response = await client.generate_response(glm_request)

        return GLMResponseModel(
            success=response.success,
            content=response.content,
            modality=response.modality.value,
            model=response.model,
            usage=response.usage,
            response_time=response.response_time,
            timestamp=response.timestamp.isoformat(),
            videos=response.videos,
            error=response.error
        )

    except Exception as e:
        logger.error(f"视频生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.post('/analyze-image', response_model=GLMResponseModel)
async def analyze_image_with_text(
    file: UploadFile = File(...),
    text: str = Form(...),
    model: str = Form(default='glm-4v-plus')
):
    """图像分析接口（多模态）"""
    try:
        client = await get_glm_service()

        # 读取并编码图片
        image_data = await file.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')

        # 解析模型
        try:
            model_enum = GLMModel(model)
        except ValueError:
            model_enum = GLMModel.GLM_4V_PLUS

        system_prompt = """你是一个专业的图像分析专家，能够深入理解图像内容并结合文本进行详细分析。

分析能力包括：
1. 图像内容识别和描述
2. 技术图表解读
3. 专利图纸分析
4. 设计图理解
5. 文本与图像的关联分析

请提供详细、准确的分析结果。"""

        messages = [
            {'role': 'system', 'content': system_prompt},
            {
                'role': 'user',
                'content': [
                    {'type': 'text', 'text': text},
                    {'type': 'image_url', 'image_url': {'url': f"data:image/jpeg;base64,{image_base64}"}}
                ]
            }
        ]

        glm_request = GLMRequest(
            model=model_enum,
            messages=messages,
            modality=ModalityType.MULTIMODAL,
            max_tokens=3000,
            images=[image_base64]
        )

        response = await client.generate_response(glm_request)

        return GLMResponseModel(
            success=response.success,
            content=response.content,
            modality=response.modality.value,
            model=response.model,
            usage=response.usage,
            response_time=response.response_time,
            timestamp=response.timestamp.isoformat(),
            error=response.error
        )

    except Exception as e:
        logger.error(f"图像分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.post('/patent-workflow', response_model=dict[str, Any])
async def patent_workflow(
    title: str = Form(...),
    abstract: str = Form(...),
    generate_diagram: bool = Form(default=True),
    generate_code: bool = Form(default=True),
    create_video: bool = Form(default=False)
):
    """专利完整工作流"""
    try:
        await get_glm_service()
        results = {}

        # 1. 专利分析

        analysis_request = PatentAnalysisRequest(
            title=title,
            abstract=abstract,
            model='glm-4.6',
            enable_thinking=True
        )

        analysis_response = await patent_analysis(analysis_request)
        results['analysis'] = {
            'content': analysis_response.content,
            'thinking_process': analysis_response.thinking_process,
            'cost': analysis_response.usage
        }

        total_cost = analysis_response.usage.get('total_tokens', 0) * 0.00015

        # 2. 生成专利配图
        if generate_diagram:
            diagram_prompt = f"专利技术架构图：{title} - {abstract}"
            diagram_request = ImageGenerationRequest(
                prompt=diagram_prompt,
                model='cogview-4',
                style='technical'
            )

            diagram_response = await generate_image(diagram_request)
            results['diagram'] = {
                'content': diagram_response.content,
                'images': diagram_response.images,
                'cost': diagram_response.usage
            }

            total_cost += diagram_response.usage.get('estimated_cost', 0.1)

        # 3. 生成实现代码
        if generate_code:
            code_prompt = f"基于专利《{title}》的技术方案，生成核心算法的Python实现代码"
            code_request = CodeGenerationRequest(
                prompt=code_prompt,
                model='glm-4.6-code',
                enable_thinking=True
            )

            code_response = await code_generation(code_request)
            results['code'] = {
                'content': code_response.content,
                'thinking_process': code_response.thinking_process,
                'cost': code_response.usage
            }

            total_cost += code_response.usage.get('total_tokens', 0) * 0.00015

        # 4. 生成介绍视频
        if create_video:
            video_prompt = f"专利技术介绍视频：{title}，展示专利的核心创新和应用场景"
            video_request = VideoGenerationRequest(
                prompt=video_prompt,
                model='cogvideox',
                duration=8
            )

            video_response = await generate_video(video_request)
            results['video'] = {
                'content': video_response.content,
                'videos': video_response.videos,
                'cost': video_response.usage
            }

            total_cost += video_response.usage.get('estimated_cost', 0.5)

        results['workflow_summary'] = {
            'total_cost': total_cost,
            'patent_title': title,
            'completed_steps': list(results.keys()),
            'timestamp': datetime.now().isoformat()
        }

        return results

    except Exception as e:
        logger.error(f"专利工作流失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.get('/models/capabilities', response_model=list[ModelCapabilitiesResponse])
async def get_model_capabilities():
    """获取所有模型能力信息"""
    try:
        client = await get_glm_service()
        capabilities = client.get_model_capabilities()

        result = []
        for model_name, caps in capabilities.items():
            result.append(ModelCapabilitiesResponse(
                model=model_name,
                modalities=[m.value for m in caps['modalities']],
                specialties=caps['specialties'],
                context_length=caps['context_length'],
                cost_per_1k=caps['cost_per_1k'],
                recommended_for=caps['specialties']
            ))

        return result

    except Exception as e:
        logger.error(f"获取模型能力失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.get('/statistics', response_model=StatisticsResponse)
async def get_statistics():
    """获取使用统计信息"""
    try:
        client = await get_glm_service()
        stats = client.get_statistics()

        return StatisticsResponse(**stats)

    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.post('/smart-completion')
async def smart_completion(
    prompt: str,
    task_type: str = 'auto',
    complexity: str = 'medium'
):
    """智能完成接口 - 自动选择最优模型"""
    try:
        client = await get_glm_service()

        # 根据任务类型和复杂度自动选择模型
        if task_type == 'auto':
            if '代码' in prompt or '编程' in prompt:
                modality = ModalityType.TEXT
                model = GLMModel.GLM_4_6_CODE
            elif '专利' in prompt or '分析' in prompt or '推理' in prompt:
                modality = ModalityType.TEXT
                model = GLMModel.GLM_4_6
            elif '图' in prompt or '画' in prompt or '图像' in prompt:
                modality = ModalityType.IMAGE
                model = GLMModel.COGVIEW_4
            elif '视频' in prompt or '动画' in prompt:
                modality = ModalityType.VIDEO
                model = GLMModel.COGVIDEOX
            else:
                modality = ModalityType.TEXT
                model = client.select_optimal_model(prompt, ModalityType.TEXT, complexity)
        else:
            # 使用指定的任务类型
            modality_mappings = {
                'text': ModalityType.TEXT,
                'image': ModalityType.IMAGE,
                'video': ModalityType.VIDEO,
                'multimodal': ModalityType.MULTIMODAL
            }
            modality = modality_mappings.get(task_type, ModalityType.TEXT)
            model = client.select_optimal_model(prompt, modality, complexity)

        messages = [{'role': 'user', 'content': prompt}]

        glm_request = GLMRequest(
            model=model,
            messages=messages,
            modality=modality,
            max_tokens=4000,
            temperature=0.3,
            enable_thinking=(model in [GLMModel.GLM_4_6, GLMModel.GLM_4_6_CODE])
        )

        response = await client.generate_response(glm_request)

        return {
            'success': response.success,
            'content': response.content,
            'selected_model': response.model,
            'modality': response.modality.value,
            'reasoning': f"基于任务类型 '{task_type}' 和复杂度 '{complexity}' 自动选择了 {response.model}",
            'thinking_process': response.thinking_process,
            'usage': response.usage,
            'response_time': response.response_time,
            'images': response.images,
            'videos': response.videos,
            'error': response.error
        }

    except Exception as e:
        logger.error(f"智能完成失败: {str(e)}")
        return {
            'success': False,
            'content': '',
            'error': str(e),
            'reasoning': '',
            'thinking_process': None,
            'usage': {},
            'response_time': 0,
            'images': None,
            'videos': None,
            'selected_model': '',
            'modality': ''
        }

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
        'athena_glm_full_suite_server:app',
        host='0.0.0.0',
        port=8091,
        reload=True,
        log_level='info',
        access_log=True
    )
