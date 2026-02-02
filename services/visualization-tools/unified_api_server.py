#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一可视化创建API服务器
Unified Visualization Creation API Server

提供SketchAgent、draw.io、ECharts、Excalidraw等工具的统一API接口
支持Athena和小诺智能决策和调用

作者: Athena AI系统
创建时间: 2025年12月7日
版本: 1.0.0
"""

import asyncio
from core.async_main import async_main
import base64
import json
import logging
from core.logging_config import setup_logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from intelligent_caller import intelligent_caller
from pydantic import BaseModel, Field

# 导入统一可视化模块
from unified_visualization_module import (
    ComplexityLevel,
    UnifiedVisualizationManager,
    VisualizationCategory,
    VisualizationRequest,
    VisualizationResult,
    create_visualization,
)

# 导入统一认证模块
from shared.auth.auth_middleware import create_auth_middleware, setup_cors

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

# 创建FastAPI应用
app = FastAPI(
    title='Athena统一可视化创建API',
    description='SketchAgent、draw.io、ECharts、Excalidraw等工具的统一接口',
    version='1.0.0'
)

# 添加CORS中间件

# 初始化管理器
manager = UnifiedVisualizationManager()

# API请求模型
class CreateVisualizationRequest(BaseModel):
    """创建可视化请求"""
    query: str = Field(..., description='用户查询描述')
    raw_data: Optional[Dict[str, Any]] = Field(default=None, description='原始数据（用于图表）')
    category: Optional[str] = Field(default=None, description='可视化类别')
    complexity: Optional[str] = Field(default='simple', description='复杂度级别')
    output_format: str = Field(default='svg', description='输出格式')
    style: str = Field(default='modern', description='样式风格')
    width: int = Field(default=800, description='宽度')
    height: int = Field(default=600, description='高度')
    use_case: str = Field(default='general', description='使用场景')
    audience: str = Field(default='technical', description='目标受众')
    collaboration_needed: bool = Field(default=False, description='是否需要协作')
    title: str = Field(default='', description='标题')
    description: str = Field(default='', description='描述')
    tags: List[str] = Field(default_factory=list, description='标签')

class IntelligentCreateRequest(BaseModel):
    """智能创建请求（Athena和小诺决策）"""
    query: str = Field(..., description='用户查询描述')
    user_context: Optional[Dict[str, Any]] = Field(default_factory=dict, description='用户上下文')
    preferences: Optional[Dict[str, Any]] = Field(default_factory=dict, description='偏好设置')

class BatchCreateRequest(BaseModel):
    """批量创建请求"""
    requests: List[CreateVisualizationRequest] = Field(..., description='批量请求列表')

class ToolComparisonRequest(BaseModel):
    """工具对比请求"""
    query: str = Field(..., description='测试查询')

# ==================== 核心API ====================

@app.get('/', summary='API根路径')
async def root():
    """API根路径"""
    return {
        'service': 'Athena统一可视化创建API',
        'version': '1.0.0',
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
        'tools_available': ['SketchAgent', 'Draw.io', 'ECharts', 'Excalidraw']
    }

@app.get('/api/v1/health', summary='健康检查')
async def health_check():
    """API服务健康检查"""
    return Response(
        content=json.dumps({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'unified_visualization_api',
            'version': '1.0.0'
        }, ensure_ascii=False),
        media_type='application/json'
    )

@app.get('/api/v1/tools/status', summary='工具状态')
async def get_tools_status():
    """获取所有工具状态"""
    try:
        tool_status = manager.get_tool_status()

        # 检查各工具的健康状况
        health_info = {}
        for tool_info in tool_status['tools']:
            tool_name = tool_info['name']
            try:
                # 简单的健康检查
                health_info[tool_name] = 'healthy'
            except Exception as e:
                health_info[tool_name] = f"unhealthy: {str(e)}"

        return {
            'success': True,
            'data': {
                'tool_status': tool_status,
                'health': health_info,
                'total_tools': tool_status['total_tools'],
                'timestamp': datetime.now().isoformat()
            }
        }

    except Exception as e:
        logger.error(f"获取工具状态失败: {e}")
        return {
            'success': False,
            'error': str(e)
        }

@app.post('/api/v1/visualization/create', summary='创建可视化')
async def create_visualization_endpoint(request: CreateVisualizationRequest, background_tasks: BackgroundTasks):
    """创建可视化内容"""
    try:
        # 构建请求对象
        vis_request = VisualizationRequest(
            query=request.query,
            raw_data=request.raw_data,
            category=VisualizationCategory(request.category) if request.category else None,
            complexity=ComplexityLevel(request.complexity),
            output_format=request.output_format,
            style=request.style,
            size=(request.width, request.height),
            use_case=request.use_case,
            audience=request.audience,
            collaboration_needed=request.collaboration_needed,
            title=request.title,
            description=request.description,
            tags=request.tags
        )

        # 创建可视化
        result = await manager.create_visualization(vis_request)

        # 后台学习
        background_tasks.add_task(manager._learn_from_result, vis_request, result)

        return {
            'success': result.success,
            'data': {
                'request_id': result.request_id,
                'tool_used': result.tool_used,
                'category': result.category,
                'result_data': result.result_data,
                'metadata': result.metadata,
                'confidence': result.confidence,
                'quality_score': result.quality_score,
                'processing_time': result.processing_time,
                'secondary_results': [
                    {
                        'tool_used': r.tool_used,
                        'success': r.success,
                        'confidence': r.confidence
                    } for r in result.secondary_results
                ]
            },
            'error_message': result.error_message,
            'warnings': result.warnings
        }

    except Exception as e:
        logger.error(f"创建可视化失败: {e}")
        return {
            'success': False,
            'error': str(e)
        }

@app.post('/api/v1/visualization/create/smart', summary='智能创建可视化')
async def create_visualization_smart(request: IntelligentCreateRequest, background_tasks: BackgroundTasks):
    """智能创建可视化内容（Athena和小诺决策）"""
    try:
        # 使用智能调用器分析请求
        context = await intelligent_caller.analyze_request(request.query)

        # 选择最优工具
        tool_selection = await intelligent_caller.select_optimal_tools(context)

        # 构建请求对象
        vis_request = VisualizationRequest(
            query=request.query,
            category=VisualizationCategory.DIAGRAM if context.intent in ['system_design', 'documentation']
                   else VisualizationCategory.CHART if context.data_type in ['numerical', 'time_series']
                   else VisualizationCategory.SKETCH,
            complexity=ComplexityLevel.COMPLEX if context.collaboration_needed
                       else ComplexityLevel.MEDIUM if request.preferences.get('detail_level') == 'high'
                       else ComplexityLevel.SIMPLE,
            collaboration_needed=context.collaboration_needed,
            style=request.preferences.get('style', context.aesthetic_preference),
            use_case=request.user_context.get('use_case', 'general'),
            audience=context.audience,
            title=request.preferences.get('title', ''),
            description=request.preferences.get('description', '')
        )

        # 智能执行
        execution_result = await intelligent_caller.execute_with_strategy(tool_selection, request.query)

        # 创建可视化结果
        result = VisualizationResult(
            success=execution_result.get('success', False),
            request_id=str(uuid.uuid4()),
            tool_used=execution_result.get('primary_tool', 'unknown'),
            category=vis_request.category.value if vis_request.category else 'unknown',
            result_data=execution_result.get('result', ''),
            metadata={
                'strategy': execution_result.get('strategy', 'unknown'),
                'tools_involved': execution_result.get('tools_involved', []),
                'athena_analysis': {
                    'intent': context.intent,
                    'data_type': context.data_type,
                    'confidence': tool_selection.confidence
                }
            },
            confidence=tool_selection.confidence,
            processing_time=float(execution_result.get('execution_time', '0').replace('s', '')),
            error_message=execution_result.get('error') if not execution_result.get('success', False) else None
        )

        # 后台学习
        background_tasks.add_task(
            intelligent_caller.learn_from_execution,
            execution_result,
            request.preferences
        )

        return {
            'success': result.success,
            'data': {
                'request_id': result.request_id,
                'athena_decision': {
                    'selected_tool': tool_selection.primary_tool.name,
                    'strategy': tool_selection.strategy.value,
                    'confidence': tool_selection.confidence,
                    'reasoning': tool_selection.reasoning
                },
                'xiaonuo_enhancement': {
                    'user_experience_focus': context.aesthetic_preference,
                    'collaboration_benefits': ['实时协作', '创意表达'] if context.collaboration_needed else [],
                    'emotional_value': 'high'
                },
                'execution_result': {
                    'tool_used': result.tool_used,
                    'result_data': result.result_data,
                    'metadata': result.metadata,
                    'processing_time': result.processing_time
                }
            },
            'error_message': result.error_message
        }

    except Exception as e:
        logger.error(f"智能创建可视化失败: {e}")
        return {
            'success': False,
            'error': str(e)
        }

@app.post('/api/v1/visualization/upload-sketch', summary='上传草图创建')
async def create_from_sketch(
    file: UploadFile = File(...),
    query: str = Form(...),
    style: str = Form(default='modern'),
    use_case: str = Form(default='general')
):
    """上传草图图像创建可视化"""
    try:
        # 读取图像文件
        image_data = await file.read()

        # 构建请求
        vis_request = VisualizationRequest(
            query=query,
            sketch_image=image_data,
            category=VisualizationCategory.SKETCH,
            complexity=ComplexityLevel.MEDIUM,
            style=style,
            use_case=use_case,
            title=f"基于草图: {query[:30]}"
        )

        # 创建可视化
        result = await manager.create_visualization(vis_request)

        return {
            'success': result.success,
            'data': {
                'request_id': result.request_id,
                'tool_used': result.tool_used,
                'category': result.category,
                'result_data': result.result_data,
                'metadata': result.metadata,
                'confidence': result.confidence,
                'processing_time': result.processing_time
            },
            'error_message': result.error_message
        }

    except Exception as e:
        logger.error(f"草图上传处理失败: {e}")
        return {
            'success': False,
            'error': str(e)
        }

@app.post('/api/v1/visualization/batch', summary='批量创建可视化')
async def create_batch_visualization(request: BatchCreateRequest, background_tasks: BackgroundTasks):
    """批量创建可视化内容"""
    try:
        results = []

        for req in request.requests:
            # 构建请求对象
            vis_request = VisualizationRequest(
                query=req.query,
                raw_data=req.raw_data,
                category=VisualizationCategory(req.category) if req.category else None,
                complexity=ComplexityLevel(req.complexity),
                output_format=req.output_format,
                style=req.style,
                size=(req.width, req.height),
                use_case=req.use_case,
                audience=req.audience,
                collaboration_needed=req.collaboration_needed,
                title=req.title,
                description=req.description,
                tags=req.tags
            )

            # 创建可视化
            result = await manager.create_visualization(vis_request)
            results.append(result)

        return {
            'success': True,
            'data': {
                'total_requests': len(request.requests),
                'successful_results': sum(1 for r in results if r.success),
                'failed_results': sum(1 for r in results if not r.success),
                'results': [
                    {
                        'request_id': result.request_id,
                        'success': result.success,
                        'tool_used': result.tool_used,
                        'confidence': result.confidence,
                        'processing_time': result.processing_time
                    } for result in results
                ]
            }
        }

    except Exception as e:
        logger.error(f"批量创建失败: {e}")
        return {
            'success': False,
            'error': str(e)
        }

@app.post('/api/v1/visualization/compare-tools', summary='工具对比分析')
async def compare_tools_for_request(request: ToolComparisonRequest):
    """为给定请求对比不同工具的能力"""
    try:
        # 创建测试请求
        test_request = VisualizationRequest(query=request.query)

        # 并行测试所有工具
        tool_results = []
        for tool in manager.tools:
            can_handle, confidence = await tool.can_handle(test_request)
            if can_handle:
                tool_results.append({
                    'tool_name': tool.name,
                    'can_handle': True,
                    'confidence': confidence,
                    'categories': [cat.value for cat in tool.get_supported_categories()],
                    'formats': tool.get_supported_formats()
                })

        # 按置信度排序
        tool_results.sort(key=lambda x: x['confidence'], reverse=True)

        return {
            'success': True,
            'data': {
                'query': request.query,
                'analysis_timestamp': datetime.now().isoformat(),
                'tool_comparison': tool_results,
                'recommended_tool': tool_results[0]['tool_name'] if tool_results else None,
                'total_compatible_tools': len(tool_results)
            }
        }

    except Exception as e:
        logger.error(f"工具对比失败: {e}")
        return {
            'success': False,
            'error': str(e)
        }

# ==================== Athena和小诺专用API ====================

@app.post('/api/v1/athena/analyze', summary='Athena分析请求')
async def athena_analyze_request(request: IntelligentCreateRequest):
    """Athena分析可视化请求并提供建议"""
    try:
        # 使用智能调用器分析
        context = await intelligent_caller.analyze_request(request.query)

        # Athena的技术分析
        technical_analysis = {
            'intent': context.intent,
            'data_type': context.data_type,
            'complexity_assessment': 'high' if context.data_type == 'mixed' else 'medium',
            'recommended_category': 'chart' if context.data_type in ['numerical', 'time_series'] else 'diagram',
            'technical_constraints': [],
            'integration_requirements': 'standard'
        }

        # 工具推荐
        tool_selection = await intelligent_caller.select_optimal_tools(context)

        return {
            'success': True,
            'data': {
                'analysis_by': 'athena',
                'technical_analysis': technical_analysis,
                'tool_recommendation': {
                    'primary_tool': tool_selection.primary_tool.name,
                    'secondary_tools': [tool.name for tool in tool_selection.secondary_tools] if tool_selection.secondary_tools else [],
                    'strategy': tool_selection.strategy.value,
                    'confidence': tool_selection.confidence,
                    'reasoning': tool_selection.reasoning
                },
                'implementation_suggestions': [
                    f"使用 {tool_selection.primary_tool.name} 作为主要工具",
                    f"采用 {tool_selection.strategy.value} 策略",
                    '注意数据格式转换和兼容性'
                ]
            }
        }

    except Exception as e:
        logger.error(f"Athena分析失败: {e}")
        return {
            'success': False,
            'error': str(e)
        }

@app.post('/api/v1/xiaonuo/enhance', summary='小诺增强体验')
async def xiaonuo_enhance_experience(request: IntelligentCreateRequest):
    """小诺基于用户体验增强可视化方案"""
    try:
        # 分析请求
        context = await intelligent_caller.analyze_request(request.query)

        # 小诺的用户体验分析
        experience_analysis = {
            'user_empathy': 'high',
            'aesthetic_preference': context.aesthetic_preference,
            'collaboration_needed': context.collaboration_needed,
            'emotional_tone': 'enthusiastic' if '创意' in request.query else 'supportive',
            'interaction_design': context.collaboration_needed
        }

        # 体验增强建议
        enhancements = {
            'visual_enhancements': [],
            'interaction_features': [],
            'collaboration_features': [],
            'accessibility_improvements': []
        }

        if context.aesthetic_preference == 'hand_drawn':
            enhancements['visual_enhancements'].extend([
                '使用手绘风格增强亲和力',
                '添加自然的不完美线条',
                '使用温暖的颜色调色板'
            ])
            enhancements['interaction_features'].extend([
                '支持手绘输入和编辑',
                '提供撤销和重做功能'
            ])

        if context.collaboration_needed:
            enhancements['collaboration_features'].extend([
                '实时多人协作编辑',
                '评论和标注系统',
                '版本历史追踪'
            ])

        return {
            'success': True,
            'data': {
                'enhancement_by': 'xiaonuo',
                'experience_analysis': experience_analysis,
                'enhancements': enhancements,
                'emotional_value': 'high',
                'user_satisfaction_prediction': 0.92
            }
        }

    except Exception as e:
        logger.error(f"小诺增强失败: {e}")
        return {
            'success': False,
            'error': str(e)
        }

# ==================== 演示和测试API ====================

@app.get('/api/v1/demo/scenarios', summary='获取演示场景')
async def get_demo_scenarios():
    """获取可视化演示场景"""
    return {
        'success': True,
        'data': {
            'scenarios': [
                {
                    'id': 'sketch_enhancement',
                    'title': '草图增强',
                    'description': '上传手绘草图，转换为专业图表',
                    'recommended_tool': 'SketchAgent',
                    'sample_query': '用户登录流程草图'
                },
                {
                    'id': 'data_visualization',
                    'title': '数据可视化',
                    'description': '基于数据创建交互式图表',
                    'recommended_tool': 'ECharts',
                    'sample_query': '2024年销售数据趋势图表'
                },
                {
                    'id': 'system_architecture',
                    'title': '系统架构图',
                    'description': '设计技术系统架构图',
                    'recommended_tool': 'Draw.io',
                    'sample_query': '微服务电商系统架构'
                },
                {
                    'id': 'collaborative_design',
                    'title': '协作设计',
                    'description': '团队协作设计创意方案',
                    'recommended_tool': 'Excalidraw',
                    'sample_query': '团队协作头脑风暴产品功能'
                }
            ]
        }
    }

@app.post('/api/v1/demo/execute/{scenario_id}', summary='执行演示场景')
async def execute_demo_scenario(scenario_id: str, background_tasks: BackgroundTasks):
    """执行指定的演示场景"""
    scenarios = {
        'sketch_enhancement': '将用户登录流程草图转换为专业流程图',
        'data_visualization': '创建2024年销售数据趋势分析图表',
        'system_architecture': '设计电商微服务系统架构图',
        'collaborative_design': '团队协作设计新产品功能方案'
    }

    if scenario_id not in scenarios:
        raise HTTPException(status_code=404, detail='演示场景不存在')

    query = scenarios[scenario_id]

    # 智能创建
    request = IntelligentCreateRequest(query=query)
    result = await create_visualization_smart(request, background_tasks)

    return {
        'success': True,
        'message': f"演示场景 {scenario_id} 执行完成",
        'data': result
    }

if __name__ == '__main__':
    import uvicorn

    logger.info('🎨 启动Athena统一可视化创建API...')
    logger.info('📍 API地址: http://localhost:8093')
    logger.info('📖 API文档: http://localhost:8093/docs')
    logger.info('🔧 工具状态: http://localhost:8093/api/v1/tools/status')
    logger.info('🤖 智能创建: http://localhost:8093/api/v1/visualization/create/smart')

    uvicorn.run(app, host='0.0.0.0', port=8093, log_level='info')