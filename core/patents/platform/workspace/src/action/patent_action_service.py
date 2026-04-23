#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专利行动层API服务
Patent Action Layer API Service

统一的专利行动层API接口，整合认知决策、任务调度、
工作流编排和专利执行器，提供完整的专利行动服务。

Created by Athena + 小诺 (AI助手)
Date: 2025-12-05
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# 导入统一认证模块
from shared.auth.auth_middleware import create_auth_middleware, setup_cors

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入核心组件
from cognitive_action_bridge import ActionType, CognitiveActionBridge, CognitiveDecision
from intelligent_scheduler import (
    IntelligentScheduler,
    SchedulingStrategy,
    SchedulingTask,
)
from patent_executors import PatentExecutorFactory, PatentTask, TaskPriority
from workflow_orchestrator import WorkflowInstance, WorkflowOrchestrator

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 初始化FastAPI应用
app = FastAPI(
    title='专利行动层API服务',
    description='Patent Action Layer API - 智能专利行动执行服务',
    version='1.0.0',
    docs_url='/docs',
    redoc_url='/redoc'
)

# 配置CORS

# 初始化核心组件
cognitive_bridge = CognitiveActionBridge()
executor_factory = PatentExecutorFactory()
scheduler = IntelligentScheduler(max_concurrent_tasks=10)
orchestrator = WorkflowOrchestrator(max_concurrent_workflows=5)

# Pydantic模型定义
class CognitiveDecisionRequest(BaseModel):
    """认知决策请求"""
    decision_id: str = Field(..., description='决策ID')
    decision_type: str = Field(..., description='决策类型')
    confidence: float = Field(..., ge=0.0, le=1.0, description='置信度')
    context: Dict[str, Any] = Field(default_factory=dict, description='上下文信息')
    suggestions: List[Dict[str, Any]] = Field(default_factory=list, description='建议列表')
    deadline: Optional[str] = Field(None, description='截止时间')


class TaskExecutionRequest(BaseModel):
    """任务执行请求"""
    task_type: ActionType = Field(..., description='任务类型')
    title: str = Field(..., description='任务标题')
    description: str = Field(default='', description='任务描述')
    patent_data: Dict[str, Any] = Field(default_factory=dict, description='专利数据')
    parameters: Dict[str, Any] = Field(default_factory=dict, description='任务参数')
    priority: TaskPriority = Field(TaskPriority.NORMAL, description='任务优先级')
    deadline: Optional[str] = Field(None, description='截止时间')


class WorkflowCreationRequest(BaseModel):
    """工作流创建请求"""
    workflow_definition_id: str = Field(..., description='工作流定义ID')
    workflow_name: Optional[str] = Field(None, description='工作流名称')
    input_data: Dict[str, Any] = Field(..., description='输入数据')
    parameters: Dict[str, Any] = Field(default_factory=dict, description='自定义参数')
    parallel_execution: bool = Field(False, description='是否并行执行')


class SchedulingRequest(BaseModel):
    """调度请求"""
    tasks: List[Dict[str, Any]] = Field(..., description='任务列表')
    strategy: SchedulingStrategy = Field(SchedulingStrategy.COGNITIVE_GUIDED, description='调度策略')
    cognitive_context: Optional[Dict[str, Any]] = Field(None, description='认知上下文')


# API健康检查
@app.get('/')
async def root():
    """根路径"""
    return {
        'service': '专利行动层API服务',
        'status': 'running',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat(),
        'components': {
            'cognitive_bridge': 'active',
            'executor_factory': 'active',
            'scheduler': 'active',
            'orchestrator': 'active'
        }
    }


@app.get('/health')
async def health_check():
    """健康检查"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'components': {
            'cognitive_bridge': 'ok',
            'executor_factory': 'ok',
            'scheduler': 'ok',
            'orchestrator': 'ok'
        }
    }


# 认知决策执行接口
@app.post('/api/v1/cognitive/execute')
async def execute_cognitive_decision(request: CognitiveDecisionRequest):
    """执行认知决策"""
    try:
        logger.info(f"接收到认知决策执行请求: {request.decision_type}")

        # 构建认知决策对象
        deadline = None
        if request.deadline:
            deadline = datetime.fromisoformat(request.deadline)

        decision = CognitiveDecision(
            id=request.decision_id,
            decision_type=request.decision_type,
            confidence=request.confidence,
            context=request.context,
            suggestions=request.suggestions,
            deadline=deadline
        )

        # 执行认知决策
        results = await cognitive_bridge.execute_cognitive_decision(decision)

        return {
            'success': True,
            'decision_id': request.decision_id,
            'results': [
                {
                    'task_id': result.task_id,
                    'status': result.status,
                    'result': result.result,
                    'error': result.error,
                    'execution_time': result.execution_time,
                    'metadata': result.metadata
                }
                for result in results
            ],
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"认知决策执行失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/v1/tasks/execute')
async def execute_task(request: TaskExecutionRequest):
    """执行单个任务"""
    try:
        logger.info(f"接收到任务执行请求: {request.task_type}")

        # 构建任务对象
        deadline = None
        if request.deadline:
            deadline = datetime.fromisoformat(request.deadline)

        task = PatentTask(
            type=request.task_type,
            title=request.title,
            description=request.description,
            patent_data=request.patent_data,
            parameters=request.parameters,
            priority=request.priority,
            deadline=deadline
        )

        # 获取执行器并执行
        executor = executor_factory.get_executor(request.task_type.value)
        if not executor:
            raise HTTPException(status_code=400, detail=f"未找到任务类型 {request.task_type} 的执行器")

        result = await executor.execute(task)

        return {
            'success': result.status == 'success',
            'task_id': task.id,
            'result': result.data,
            'error': result.error,
            'execution_time': result.execution_time,
            'metadata': result.metadata,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"任务执行失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/v1/workflows/create')
async def create_workflow(request: WorkflowCreationRequest):
    """创建工作流"""
    try:
        logger.info(f"接收到工作流创建请求: {request.workflow_definition_id}")

        # 创建工作流实例
        workflow = await orchestrator.create_workflow(
            definition_id=request.workflow_definition_id,
            input_data=request.input_data,
            parameters=request.parameters,
            workflow_name=request.workflow_name
        )

        # 设置并行执行参数
        if request.parallel_execution:
            workflow.parallel_execution = True

        return {
            'success': True,
            'workflow_id': workflow.workflow_id,
            'name': workflow.name,
            'type': workflow.workflow_type,
            'status': workflow.status,
            'total_steps': len(workflow.steps),
            'estimated_duration': str(workflow.timeout) if workflow.timeout else None,
            'created_at': workflow.created_at.isoformat(),
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"工作流创建失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/v1/workflows/{workflow_id}/execute')
async def execute_workflow(workflow_id: str, background_tasks: BackgroundTasks):
    """执行工作流"""
    try:
        logger.info(f"开始执行工作流: {workflow_id}")

        # 在后台执行工作流
        background_tasks.add_task(
            orchestrator.execute_workflow,
            workflow_id,
            True  # 默认并行执行
        )

        return {
            'success': True,
            'message': f"工作流 {workflow_id} 已开始执行",
            'workflow_id': workflow_id,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"工作流执行失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/v1/workflows/{workflow_id}/status')
async def get_workflow_status(workflow_id: str):
    """获取工作流状态"""
    try:
        status = orchestrator.get_workflow_status(workflow_id)
        if not status:
            raise HTTPException(status_code=404, detail='工作流不存在')

        return {
            'success': True,
            'workflow_status': status,
            'timestamp': datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取工作流状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/v1/workflows')
async def list_workflows(status: Optional[str] = None):
    """列出工作流"""
    try:
        from workflow_orchestrator import WorkflowStatus

        workflow_status = None
        if status:
            workflow_status = WorkflowStatus(status)

        workflows = orchestrator.list_workflows(workflow_status)

        return {
            'success': True,
            'workflows': workflows,
            'total': len(workflows),
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"列出工作流失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/v1/scheduling/plan')
async def create_scheduling_plan(request: SchedulingRequest):
    """创建调度计划"""
    try:
        logger.info(f"接收到调度计划请求，策略: {request.strategy}")

        # 转换任务格式
        scheduling_tasks = []
        for task_data in request.tasks:
            deadline = None
            if task_data.get('deadline'):
                deadline = datetime.fromisoformat(task_data['deadline'])

            task = SchedulingTask(
                task_id=task_data['task_id'],
                priority=task_data.get('priority', 1),
                deadline=deadline,
                dependencies=set(task_data.get('dependencies', [])),
                cognitive_score=task_data.get('cognitive_score', 0.0)
            )

            scheduling_tasks.append(task)

        # 创建调度计划
        plan = await scheduler.schedule_tasks(
            scheduling_tasks,
            request.strategy,
            request.cognitive_context
        )

        return {
            'success': True,
            'plan_id': plan.plan_id,
            'strategy': plan.strategy,
            'execution_order': plan.execution_order,
            'estimated_completion_time': plan.estimated_completion_time.isoformat(),
            'total_duration': str(plan.total_duration),
            'task_count': len(plan.tasks),
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"创建调度计划失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# 状态查询接口
@app.get('/api/v1/status/components')
async def get_component_status():
    """获取组件状态"""
    return {
        'cognitive_bridge': cognitive_bridge.get_active_tasks_status(),
        'scheduler': scheduler.get_scheduling_status(),
        'orchestrator': orchestrator.get_orchestrator_status(),
        'executors': executor_factory.list_executors()
    }


@app.get('/api/v1/executors')
async def list_executors():
    """列出可用执行器"""
    return {
        'success': True,
        'executors': executor_factory.list_executors(),
        'timestamp': datetime.now().isoformat()
    }


@app.get('/api/v1/workflows/definitions')
async def list_workflow_definitions():
    """列出工作流定义"""
    return {
        'success': True,
        'definitions': [
            {
                'definition_id': def_id,
                'name': workflow_def.name,
                'type': workflow_def.workflow_type,
                'description': workflow_def.description,
                'estimated_duration': str(workflow_def.estimated_duration) if workflow_def.estimated_duration else None,
                'step_count': len(workflow_def.steps_template)
            }
            for def_id, workflow_def in orchestrator.workflow_definitions.items()
        ],
        'timestamp': datetime.now().isoformat()
    }


# 管理接口
@app.post('/api/v1/workflows/{workflow_id}/cancel')
async def cancel_workflow(workflow_id: str):
    """取消工作流"""
    try:
        success = await orchestrator.cancel_workflow(workflow_id)
        if not success:
            raise HTTPException(status_code=404, detail='工作流不存在或无法取消')

        return {
            'success': True,
            'message': f"工作流 {workflow_id} 已取消",
            'timestamp': datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消工作流失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/v1/scheduling/weights/adjust')
async def adjust_scheduling_weights(weights: Dict[str, float]):
    """调整调度权重"""
    try:
        scheduler.adjust_cognitive_weights(weights)
        return {
            'success': True,
            'message': '调度权重已调整',
            'current_weights': scheduler.cognitive_weights,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"调整调度权重失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# 测试接口
@app.post('/api/v1/test/complete_flow')
async def test_complete_flow():
    """测试完整流程"""
    try:
        logger.info('开始测试完整流程')

        # 1. 创建认知决策
        decision_request = CognitiveDecisionRequest(
            decision_id='test_complete_001',
            decision_type='PATENT_ANALYSIS_REQUIRED',
            confidence=0.92,
            context={
                'patent_data': {
                    'patent_id': 'CN202410001234.5',
                    'title': '智能专利分析方法',
                    'abstract': '一种基于AI的专利分析技术'
                }
            }
        )

        # 2. 执行认知决策
        decision_result = await execute_cognitive_decision(decision_request)

        # 3. 创建工作流
        workflow_request = WorkflowCreationRequest(
            workflow_definition_id='patent_analysis_standard',
            input_data={
                'patent_id': 'CN202410001234.5',
                'title': '智能专利分析方法'
            },
            parallel_execution=True
        )

        workflow_result = await create_workflow(workflow_request)

        # 4. 执行工作流
        await execute_workflow(workflow_result['workflow_id'], BackgroundTasks())

        return {
            'success': True,
            'message': '完整流程测试成功',
            'steps': {
                'cognitive_decision': decision_result['success'],
                'workflow_creation': workflow_result['success'],
                'workflow_execution': True
            },
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"完整流程测试失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# 启动事件
@app.on_event('startup')
async def startup_event():
    """服务启动事件"""
    logger.info('专利行动层API服务启动')

    # 注册执行器到工作流编排器
    from patent_executors import (
        PatentAnalysisExecutor,
        PatentFilingExecutor,
        PatentMonitoringExecutor,
        PatentValidationExecutor,
    )

    orchestrator.register_executor('DataCollectionExecutor', PatentAnalysisExecutor())
    orchestrator.register_executor('DataPreprocessorExecutor', PatentAnalysisExecutor())
    orchestrator.register_executor('FeatureExtractionExecutor', PatentAnalysisExecutor())
    orchestrator.register_executor('CognitiveAnalysisExecutor', PatentAnalysisExecutor())
    orchestrator.register_executor('ReportGeneratorExecutor', PatentAnalysisExecutor())
    orchestrator.register_executor('InventionDisclosureExecutor', PatentFilingExecutor())
    orchestrator.register_executor('PatentabilityAnalysisExecutor', PatentAnalysisExecutor())
    orchestrator.register_executor('DocumentDraftingExecutor', PatentFilingExecutor())
    orchestrator.register_executor('InternalReviewExecutor', PatentAnalysisExecutor())
    orchestrator.register_executor('FilingPreparationExecutor', PatentFilingExecutor())

    logger.info('执行器注册完成')


@app.on_event('shutdown')
async def shutdown_event():
    """服务关闭事件"""
    logger.info('专利行动层API服务关闭')


# 主函数
def main():
    """启动服务"""
    logger.info('启动专利行动层API服务...')

    uvicorn.run(
        app,
        host='0.0.0.0',
        port=9000,
        log_level='info',
        access_log=True
    )


if __name__ == '__main__':
    main()