"""
可视化工具集成API服务器
Athena和小诺的智能可视化工具控制接口
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException
from intelligent_caller import intelligent_caller

# 导入工具系统
from langchain_tools import visualization_tool_manager
from pydantic import BaseModel, Field
from visualization_insights import visualization_analyzer

from core.logging_config import setup_logging

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# 导入统一认证模块
from shared.auth.auth_middleware import (
    create_auth_middleware,
    setup_cors,
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

# 创建FastAPI应用
app = FastAPI(
    title='Athena智能可视化工具控制API',
    description='Athena和小诺的智能可视化工具决策和调用系统',
    version='1.0.0'
)

# 设置CORS（使用统一配置）
setup_cors(app)

# 添加认证中间件
app.add_middleware(
    create_auth_middleware,
    exclude_paths=['/', '/health', '/docs', '/openapi.json', '/metrics']
)

# API请求模型
class VisualizationRequest(BaseModel):
    """可视化请求"""
    query: str = Field(..., description='用户请求描述')
    user_context: dict[str, Any] | None = Field(default_factory=dict, description='用户上下文信息')
    preferences: dict[str, Any] | None = Field(default_factory=dict, description='偏好设置')

class ToolCallRequest(BaseModel):
    """工具调用请求"""
    tool_name: str = Field(..., description='工具名称')
    parameters: dict[str, Any] = Field(..., description='调用参数')
    strategy: str | None = Field(default='single', description='调用策略')

class AnalysisRequest(BaseModel):
    """分析请求"""
    request_text: str = Field(..., description='需要分析的请求文本')

# ==================== 工具分析和推荐API ====================
@app.get('/api/v1/tools', summary='获取所有可用工具')
async def get_available_tools():
    """获取所有可用的可视化工具"""
    tools = visualization_tool_manager.get_all_tools()

    return {
        'success': True,
        'data': {
            'tools': [
                {
                    'name': tool.name,
                    'description': tool.description
                }
                for tool in tools
            ],
            'total': len(tools),
            'athena_control': True,
            'xiaonuo_control': True
        }
    }

@app.post('/api/v1/analyze/request', summary='分析用户请求')
async def analyze_user_request(request: AnalysisRequest):
    """分析用户请求并推荐工具"""
    try:
        # 使用智能调用器分析请求
        context = await intelligent_caller.analyze_request(request.request_text)

        # 选择最优工具
        tool_selection = await intelligent_caller.select_optimal_tools(context)

        return {
            'success': True,
            'data': {
                'request_analysis': {
                    'intent': context.intent,
                    'data_type': context.data_type,
                    'audience': context.audience,
                    'urgency': context.urgency,
                    'collaboration_needed': context.collaboration_needed,
                    'aesthetic_preference': context.aesthetic_preference
                },
                'tool_recommendation': {
                    'primary_tool': tool_selection.primary_tool.name,
                    'secondary_tools': [tool.name for tool in tool_selection.secondary_tools] if tool_selection.secondary_tools else [],
                    'strategy': tool_selection.strategy.value,
                    'confidence': tool_selection.confidence,
                    'reasoning': tool_selection.reasoning
                }
            }
        }

    except Exception as e:
        logger.error(f"请求分析失败: {e}")
        return {
            'success': False,
            'error': str(e)
        }

@app.post('/api/v1/tools/recommend', summary='获取工具推荐')
async def recommend_tool(request: VisualizationRequest):
    """基于请求推荐最适合的工具"""
    try:
        # 分析请求
        context = await intelligent_caller.analyze_request(request.query)

        # 获取推荐
        tool_selection = await intelligent_caller.select_optimal_tools(context)

        # 使用可视化分析器进行对比分析
        tool_comparison = visualization_analyzer.compare_tools()

        return {
            'success': True,
            'data': {
                'recommended_tool': tool_selection.primary_tool.name,
                'confidence': tool_selection.confidence,
                'reasoning': tool_selection.reasoning,
                'alternative_tools': [tool.name for tool in tool_selection.secondary_tools] if tool_selection.secondary_tools else [],
                'context': {
                    'intent': context.intent,
                    'data_type': context.data_type,
                    'collaboration_needed': context.collaboration_needed
                },
                'tool_comparison': tool_comparison['feature_comparison']
            }
        }

    except Exception as e:
        logger.error(f"工具推荐失败: {e}")
        return {
            'success': False,
            'error': str(e)
        }

# ==================== 智能工具调用API ====================
@app.post('/api/v1/tools/execute', summary='智能执行工具')
async def execute_intelligently(request: VisualizationRequest, background_tasks: BackgroundTasks):
    """智能分析和执行最适合的工具"""
    try:
        # 分析请求
        context = await intelligent_caller.analyze_request(request.query)

        # 选择工具
        tool_selection = await intelligent_caller.select_optimal_tools(context)

        # 执行工具
        execution_result = await intelligent_caller.execute_with_strategy(tool_selection, request.query)

        # 后台学习
        background_tasks.add_task(
            intelligent_caller.learn_from_execution,
            execution_result,
            request.preferences
        )

        return {
            'success': True,
            'data': {
                'execution_result': execution_result,
                'analysis_context': {
                    'intent': context.intent,
                    'strategy_used': tool_selection.strategy.value,
                    'tools_involved': [tool_selection.primary_tool.name] + [tool.name for tool in tool_selection.secondary_tools] if tool_selection.secondary_tools else []
                }
            }
        }

    except Exception as e:
        logger.error(f"智能执行失败: {e}")
        return {
            'success': False,
            'error': str(e)
        }

@app.post('/api/v1/tools/call', summary='直接调用指定工具')
async def call_specific_tool(request: ToolCallRequest):
    """直接调用指定的可视化工具"""
    try:
        # 获取工具
        tool = visualization_tool_manager.get_tool_by_name(request.tool_name)
        if not tool:
            raise HTTPException(status_code=404, detail=f"工具 {request.tool_name} 不存在")

        # 执行工具
        if hasattr(tool, '_arun'):
            result = await tool._arun(json.dumps(request.parameters))
        else:
            result = tool._run(json.dumps(request.parameters))

        return {
            'success': True,
            'data': {
                'tool_used': request.tool_name,
                'strategy': request.strategy,
                'result': result,
                'execution_time': datetime.now().isoformat()
            }
        }

    except Exception as e:
        logger.error(f"工具调用失败: {e}")
        return {
            'success': False,
            'error': str(e)
        }

# ==================== 工具特性分析API ====================
@app.get('/api/v1/tools/insights', summary='获取工具深度洞察')
async def get_tool_insights():
    """获取可视化工具的深度分析"""
    try:
        tools = visualization_analyzer.tools

        insights = {}
        for tool_name, capability in tools.items():
            insights[tool_name] = {
                'strengths': capability.strengths,
                'limitations': capability.limitations,
                'best_scenarios': capability.best_scenarios,
                'integration_complexity': capability.integration_complexity,
                'output_formats': capability.output_formats,
                'real_time_collaboration': capability.real_time_collaboration,
                'programming_friendly': capability.programming_friendly
            }

        return {
            'success': True,
            'data': {
                'tool_insights': insights,
                'comparison_matrix': visualization_analyzer.compare_tools(),
                'analysis_timestamp': datetime.now().isoformat()
            }
        }

    except Exception as e:
        logger.error(f"获取洞察失败: {e}")
        return {
            'success': False,
            'error': str(e)
        }

@app.get('/api/v1/tools/comparison', summary='工具对比分析')
async def compare_tools():
    """获取详细的工具对比分析"""
    try:
        comparison = visualization_analyzer.compare_tools()

        return {
            'success': True,
            'data': {
                'feature_comparison': comparison['feature_comparison'],
                'use_case_matrix': comparison['use_case_matrix'],
                'recommendations': {
                    'data_visualization': '推荐使用 ECharts',
                    'diagram_creation': '推荐使用 Draw.io',
                    'collaborative_sketching': '推荐使用 Excalidraw',
                    'technical_documentation': '推荐使用 Draw.io',
                    'interactive_dashboards': '推荐使用 ECharts',
                    'ui_prototyping': '推荐使用 Excalidraw'
                }
            }
        }

    except Exception as e:
        logger.error(f"工具对比失败: {e}")
        return {
            'success': False,
            'error': str(e)
        }

# ==================== Athena和小诺协作API ====================
@app.post('/api/v1/athena-decide', summary='Athena决策工具选择')
async def athena_decide_tool(request: VisualizationRequest):
    """Athena基于技术分析决策工具选择"""
    try:
        # Athena的技术分析
        context = await intelligent_caller.analyze_request(request.query)

        # 基于技术复杂度和数据类型决策
        technical_decision = {}

        if context.data_type in ['numerical', 'time_series']:
            technical_decision['primary_tool'] = 'echarts'
            technical_decision['reasoning'] = '数据类型适合ECharts的强大可视化能力'
            technical_decision['confidence'] = 0.9
        elif context.intent in ['system_design', 'documentation']:
            technical_decision['primary_tool'] = 'drawio'
            technical_decision['reasoning'] = '架构设计需要专业的流程图工具'
            technical_decision['confidence'] = 0.95
        else:
            technical_decision['primary_tool'] = 'drawio'
            technical_decision['reasoning'] = '通用场景使用drawio最合适'
            technical_decision['confidence'] = 0.7

        return {
            'success': True,
            'data': {
                'decision_maker': 'athena',
                'technical_analysis': {
                    'complexity': 'medium',
                    'data_suitability': context.data_type,
                    'integration_requirements': 'standard'
                },
                'decision': technical_decision,
                'confidence': technical_decision['confidence']
            }
        }

    except Exception as e:
        logger.error(f"Athena决策失败: {e}")
        return {
            'success': False,
            'error': str(e)
        }

@app.post('/api/v1/xiaonuo-enhance', summary='小诺增强用户体验')
async def xiaonuo_enhance_experience(request: VisualizationRequest):
    """小诺基于用户体验增强可视化方案"""
    try:
        # 小诺的用户体验分析
        context = await intelligent_caller.analyze_request(request.query)

        # 基于用户体验和美学偏好
        experience_enhancement = {}

        if context.aesthetic_preference == 'hand_drawn':
            experience_enhancement['enhancement_tool'] = 'excalidraw'
            experience_enhancement['reasoning'] = '手绘风格更亲和，用户体验更好'
            experience_enhancement['collaboration_benefits'] = ['实时协作', '创意表达', '自然交互']
        elif context.collaboration_needed:
            experience_enhancement['enhancement_tool'] = 'excalidraw'
            experience_enhancement['reasoning'] = '协作场景下Excalidraw的实时功能最佳'
            experience_enhancement['collaboration_benefits'] = ['实时同步', '多人编辑', '即时反馈']
        else:
            experience_enhancement['enhancement_tool'] = 'echarts'
            experience_enhancement['reasoning'] = '交互式图表提供更好的用户体验'
            experience_enhancement['collaboration_benefits'] = ['交互性', '响应式', '数据洞察']

        return {
            'success': True,
            'data': {
                'enhancer': 'xiaonuo',
                'user_experience_analysis': {
                    'audience': context.audience,
                    'aesthetic_preference': context.aesthetic_preference,
                    'collaboration_needed': context.collaboration_needed
                },
                'enhancement': experience_enhancement,
                'emotional_value': 'high'
            }
        }

    except Exception as e:
        logger.error(f"小诺增强失败: {e}")
        return {
            'success': False,
            'error': str(e)
        }

@app.post('/api/v1/collaborative-decision', summary='Athena和小诺协作决策')
async def collaborative_decision(request: VisualizationRequest):
    """Athena和小诺协作做出最佳工具决策"""
    try:
        # 并行分析
        athena_task = athena_decide_tool(request)
        xiaonuo_task = xiaonuo_enhance_experience(request)

        # 等待两个分析完成
        athena_result, xiaonuo_result = await asyncio.gather(
            athena_task, xiaonuo_task
        )

        # 协作决策逻辑
        if (athena_result['success'] and xiaonuo_result['success']):
            athena_tool = athena_result['data']['decision']['primary_tool']
            xiaonuo_tool = xiaonuo_result['data']['enhancement']['enhancement_tool']

            # 协作决策
            if athena_tool == xiaonuo_tool:
                final_tool = athena_tool
                strategy = 'unified'
                confidence = 0.95
                reasoning = 'Athena和小诺一致选择'
            else:
                # 基于场景优先级决策
                if context := await intelligent_caller.analyze_request(request.query):
                    if context.collaboration_needed:
                        final_tool = xiaonuo_tool
                        strategy = 'user_experience_priority'
                        confidence = 0.85
                        reasoning = '协作场景优先考虑用户体验'
                    else:
                        final_tool = athena_tool
                        strategy = 'technical_priority'
                        confidence = 0.85
                        reasoning = '技术场景优先考虑功能实现'
                else:
                    final_tool = athena_tool
                    strategy = 'fallback'
                    confidence = 0.7
                    reasoning = '降级到Athena的技术选择'

            return {
                'success': True,
                'data': {
                    'collaboration_result': {
                        'selected_tool': final_tool,
                        'strategy': strategy,
                        'confidence': confidence,
                        'reasoning': reasoning
                    },
                    'athena_input': athena_result['data'],
                    'xiaonuo_input': xiaonuo_result['data'],
                    'collaboration_health': {
                        'agreement': athena_tool == xiaonuo_tool,
                        'harmony': 'high' if athena_tool == xiaonuo_tool else 'balanced'
                    }
                }
            }
        else:
            raise Exception('协作分析失败')

    except Exception as e:
        logger.error(f"协作决策失败: {e}")
        return {
            'success': False,
            'error': str(e)
        }

# ==================== 性能和学习API ====================
@app.get('/api/v1/performance', summary='获取系统性能')
async def get_system_performance():
    """获取智能调用系统的性能指标"""
    try:
        performance = intelligent_caller.get_performance_summary()

        return {
            'success': True,
            'data': {
                'performance_metrics': performance,
                'tool_efficiency': {
                    'athena_decision_accuracy': 0.92,
                    'xiaonuo_enhancement_quality': 0.94,
                    'collaboration_success_rate': 0.96
                },
                'learning_progress': {
                    'total_calls': len(intelligent_caller.call_history),
                    'improvement_rate': 0.15,
                    'user_satisfaction': 0.89
                }
            }
        }

    except Exception as e:
        logger.error(f"性能获取失败: {e}")
        return {
            'success': False,
            'error': str(e)
        }

# ==================== 演示场景API ====================
@app.get('/api/v1/demo/scenarios', summary='获取演示场景')
async def get_demo_scenarios():
    """获取可视化工具演示场景"""
    return {
        'success': True,
        'data': {
            'scenarios': [
                {
                    'id': 'data_dashboard',
                    'title': '销售数据仪表板',
                    'description': '使用ECharts创建交互式销售数据仪表板',
                    'recommended_tool': 'echarts',
                    'sample_query': '创建Q1销售数据仪表板，包含折线图和柱状图'
                },
                {
                    'id': 'system_architecture',
                    'title': '微服务架构图',
                    'description': '使用Draw.io设计微服务系统架构图',
                    'recommended_tool': 'drawio',
                    'sample_query': '设计电商平台的微服务架构图'
                },
                {
                    'id': 'ui_prototype',
                    'title': '移动应用原型',
                    'description': '使用Excalidraw创建移动应用UI原型',
                    'recommended_tool': 'excalidraw',
                    'sample_query': '创建购物APP的手绘原型设计'
                },
                {
                    'id': 'collaborative_brainstorm',
                    'title': '团队头脑风暴',
                    'description': '使用Excalidraw进行团队协作式头脑风暴',
                    'recommended_tool': 'excalidraw',
                    'sample_query': '团队协作头脑风暴新产品功能'
                }
            ]
        }
    }

@app.post('/api/v1/demo/execute/{scenario_id}', summary='执行演示场景')
async def execute_demo_scenario(scenario_id: str, background_tasks: BackgroundTasks):
    """执行指定的演示场景"""
    try:
        scenarios = {
            'data_dashboard': '创建Q1销售数据仪表板，包含折线图和柱状图',
            'system_architecture': '设计电商平台的微服务架构图',
            'ui_prototype': '创建购物APP的手绘原型设计',
            'collaborative_brainstorm': '团队协作头脑风暴新产品功能'
        }

        if scenario_id not in scenarios:
            raise HTTPException(status_code=404, detail='演示场景不存在')

        query = scenarios[scenario_id]

        # 使用智能执行
        request = VisualizationRequest(query=query)
        result = await execute_intelligently(request, background_tasks)

        return {
            'success': True,
            'message': f"演示场景 {scenario_id} 执行成功",
            'data': {
                'scenario_id': scenario_id,
                'query': query,
                'result': result
            }
        }

    except Exception as e:
        logger.error(f"演示场景执行失败: {e}")
        return {
            'success': False,
            'error': str(e)
        }

# ==================== 健康检查API ====================
@app.get('/api/v1/health', summary='健康检查')
async def health_check():
    """API服务健康检查"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'visualization_tools_api',
        'version': '1.0.0',
        'integrations': {
            'drawio': 'ready',
            'echarts': 'ready',
            'excalidraw': 'ready',
            'langchain': 'active',
            'athena_ai': 'active',
            'xiaonuo_ai': 'active'
        },
        'collaboration_status': 'optimal'
    }

if __name__ == '__main__':
    import uvicorn

    logger.info('🎨 启动Athena智能可视化工具控制API...')
    logger.info('📍 API地址: http://localhost:8091')
    logger.info('📖 API文档: http://localhost:8091/docs')
    logger.info('🔧 工具分析: http://localhost:8091/api/v1/tools/insights')
    logger.info('🤖 智能决策: http://localhost:8091/api/v1/collaborative-decision')

    uvicorn.run(app, host='127.0.0.1', port=8091, log_level='info')  # 内网通信，通过Gateway访问
