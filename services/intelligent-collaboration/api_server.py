"""
协作中枢API服务
提供任务提交、状态查询和结果获取的接口
"""

import logging

from fastapi import FastAPI, HTTPException

logger = logging.getLogger(__name__)

from datetime import datetime
from typing import Any

import uvicorn
from collaboration_controller import (
    TaskStatus,
    collaboration_controller,
)
from pydantic import BaseModel

# 导入统一认证模块

# FastAPI应用
app = FastAPI(
    title='智能协作中枢',
    description='Athena和小诺的协作协调服务',
    version='1.0.0'
)

# 配置CORS

# 请求/响应模型
class TaskRequest(BaseModel):
    """任务请求模型"""
    type: str
    description: str
    complexity: float = 0.5
    priority: int = 1
    requirements: dict[str, Any] | None = {}
    deadline: str | None = None

class TaskResponse(BaseModel):
    """任务响应模型"""
    task_id: str
    status: str
    message: str

class TaskStatusResponse(BaseModel):
    """任务状态响应模型"""
    task_id: str
    status: str
    created_at: str
    results: list[dict[str, Any]
    execution_summary: dict[str, Any] | None = None

class CollaborationInsight(BaseModel):
    """协作洞察模型"""
    total_tasks: int
    active_tasks: int
    completed_tasks: int
    failed_tasks: int
    average_execution_time: float | None
    ai_utilization: dict[str, float]

# API端点
@app.get('/')
async def root():
    """根端点"""
    return {
        'service': '智能协作中枢',
        'status': 'running',
        'timestamp': datetime.now().isoformat()
    }

@app.post('/api/v1/tasks', response_model=TaskResponse)
async def submit_task(task_request: TaskRequest):
    """提交任务"""
    try:
        task_id = await collaboration_controller.submit_task(task_request.dict())
        return TaskResponse(
            task_id=task_id,
            status='submitted',
            message='任务已成功提交，正在处理中'
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"任务提交失败: {str(e)}") from e

@app.get('/api/v1/tasks/{task_id}', response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """获取任务状态"""
    status_info = collaboration_controller.get_task_status(task_id)

    if not status_info:
        raise HTTPException(status_code=404, detail='任务未找到')

    task = status_info['task']
    results = status_info['results']

    # 计算执行摘要
    execution_summary = None
    if results:
        completed_results = [r for r in results if r['status'] == 'completed']
        if completed_results:
            total_time = sum(r.get('execution_time', 0) for r in completed_results)
            execution_summary = {
                'total_executions': len(completed_results),
                'total_execution_time': total_time,
                'average_execution_time': total_time / len(completed_results),
                'ai_participants': list({r['executor'] for r in completed_results}),
                'confidence_scores': [r.get('confidence') for r in completed_results if r.get('confidence')]
            }

    return TaskStatusResponse(
        task_id=task_id,
        status=status_info['status'],
        created_at=task['created_at'],
        results=results,
        execution_summary=execution_summary
    )

@app.delete('/api/v1/tasks/{task_id}')
async def cancel_task(task_id: str):
    """取消任务"""
    success = await collaboration_controller.cancel_task(task_id)

    if not success:
        raise HTTPException(status_code=404, detail='任务未找到或无法取消')

    return {
        'message': '任务已成功取消',
        'task_id': task_id
    }

@app.get('/api/v1/tasks', response_model=list[str])
async def get_active_tasks():
    """获取活跃任务列表"""
    return collaboration_controller.get_active_tasks()

@app.get('/api/v1/insights', response_model=CollaborationInsight)
async def get_collaboration_insights():
    """获取协作洞察"""
    # 统计任务
    all_tasks = list(collaboration_controller.tasks.values())
    all_results = list(collaboration_controller.results.values())

    total_tasks = len(all_tasks)
    active_tasks = len(collaboration_controller.get_active_tasks())

    completed_tasks = 0
    failed_tasks = 0
    execution_times = []
    ai_usage = {'athena': 0, 'xiaonuo': 0}

    for task_results in all_results:
        for result in task_results:
            if result.status == TaskStatus.COMPLETED:
                completed_tasks += 1
                if result.execution_time:
                    execution_times.append(result.execution_time)
            elif result.status == TaskStatus.FAILED:
                failed_tasks += 1

            # 统计AI使用情况
            if result.executor in ai_usage:
                ai_usage[result.executor] += 1

    # 计算平均执行时间
    avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else None

    # 计算AI利用率
    total_executions = sum(ai_usage.values())
    ai_utilization = {
        ai: count / total_executions if total_executions > 0 else 0
        for ai, count in ai_usage.items()
    }

    return CollaborationInsight(
        total_tasks=total_tasks,
        active_tasks=active_tasks,
        completed_tasks=completed_tasks,
        failed_tasks=failed_tasks,
        average_execution_time=avg_execution_time,
        ai_utilization=ai_utilization
    )

@app.post('/api/v1/cleanup')
async def cleanup_old_tasks(older_than_hours: int = 24):
    """清理旧任务"""
    await collaboration_controller.cleanup_completed_tasks(older_than_hours)
    return {
        'message': f"已清理超过{older_than_hours}小时的已完成任务",
        'timestamp': datetime.now().isoformat()
    }

@app.post('/api/v1/collaboration/suggest')
async def suggest_collaboration_mode(task_info: dict[str, Any]):
    """建议协作模式"""
    task_info.get('type', '')
    description = task_info.get('description', '')
    complexity = task_info.get('complexity', 0.5)

    # 简单的规则引擎
    suggestions = {
        'mode': 'delegate',
        'primary_ai': 'athena',
        'secondary_ai': None,
        'reason': '',
        'estimated_efficiency': 1.0
    }

    # 基于任务内容提供建议
    if any(keyword in description.lower() for keyword in ['分析', '策略', '评估', '方案']):
        suggestions['primary_ai'] = 'athena'
        suggestions['reason'] = '任务需要深度分析能力'

    elif any(keyword in description.lower() for keyword in ['实现', '开发', '代码', '优化']):
        suggestions['primary_ai'] = 'xiaonuo'
        suggestions['reason'] = '任务需要技术实现能力'

    elif complexity > 0.7:
        suggestions['mode'] = 'synergy'
        suggestions['primary_ai'] = 'athena'
        suggestions['secondary_ai'] = 'xiaonuo'
        suggestions['reason'] = '高复杂度任务需要协作处理'
        suggestions['estimated_efficiency'] = 1.5

    elif '创意' in description or '设计' in description:
        suggestions['mode'] = 'parallel'
        suggestions['primary_ai'] = 'athena'
        suggestions['secondary_ai'] = 'xiaonuo'
        suggestions['reason'] = '创意任务需要多角度思考'
        suggestions['estimated_efficiency'] = 1.3

    return suggestions

@app.get('/api/v1/health')
async def health_check():
    """健康检查"""
    return {
        'status': 'healthy',
        'service': 'intelligent-collaboration',
        'active_tasks': len(collaboration_controller.get_active_tasks()),
        'total_tasks_processed': len(collaboration_controller.tasks),
        'timestamp': datetime.now().isoformat()
    }

# 启动服务
if __name__ == '__main__':
    logger.info('🚀 启动智能协作中枢...')
    logger.info('服务地址: http://localhost:8091')
    logger.info('API文档: http://localhost:8091/docs')

    uvicorn.run(
        'api_server:app',
        host='0.0.0.0',
        port=8091,
        reload=True,
        log_level='info'
    )
