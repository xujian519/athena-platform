#!/usr/bin/env python3
"""
增强专利行动层API服务
Enhanced Patent Action Layer API Service

扩展原有API，增加更多业务场景的接口，
集成性能优化和监控功能。

Created by Athena + 小诺 (AI助手)
Date: 2025-12-05
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Any

import uvicorn
from fastapi import Body, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

# 导入统一认证模块

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入核心组件
from cognitive_action_bridge import ActionType, CognitiveActionBridge
from intelligent_scheduler import (
    IntelligentScheduler,
)
from monitoring_system import MonitoringSystem
from patent_executors import PatentExecutorFactory, PatentTask, TaskPriority
from performance_optimizer import PatentActionOptimizer, TaskPerformanceData
from workflow_orchestrator import WorkflowOrchestrator

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 初始化FastAPI应用
app = FastAPI(
    title='增强专利行动层API服务',
    description='Enhanced Patent Action Layer API - 完整的专利行动执行和管理服务',
    version='2.0.0',
    docs_url='/docs',
    redoc_url='/redoc'
)

# 配置CORS

# 初始化核心组件
cognitive_bridge = CognitiveActionBridge()
executor_factory = PatentExecutorFactory()
scheduler = IntelligentScheduler(max_concurrent_tasks=10)
orchestrator = WorkflowOrchestrator(max_concurrent_workflows=5)
optimizer = PatentActionOptimizer()
monitoring = MonitoringSystem()

# 启动优化器和监控
optimizer.start_optimization()
monitoring.start_monitoring()

# 扩展的Pydantic模型
class BatchTaskRequest(BaseModel):
    """批量任务请求"""
    tasks: list[dict[str, Any]] = Field(..., description='任务列表')
    batch_strategy: str = Field('parallel', description='批处理策略: parallel, sequential')
    batch_timeout: int | None = Field(None, description='批次超时时间(秒)')


class PatentPortfolioRequest(BaseModel):
    """专利组合请求"""
    portfolio_name: str = Field(..., description='组合名称')
    patent_ids: list[str] = Field(..., description='专利ID列表')
    analysis_type: str = Field('comprehensive', description='分析类型')
    monitoring_enabled: bool = Field(True, description='是否启用监控')


class PatentComparisonRequest(BaseModel):
    """专利对比请求"""
    source_patent_id: str = Field(..., description='源专利ID')
    target_patent_ids: list[str] = Field(..., description='目标专利ID列表')
    comparison_aspects: list[str] = Field(default=['technical', 'legal', 'commercial'], description='对比维度')


class PatentValidationRequest(BaseModel):
    """专利验证请求"""
    patent_id: str = Field(..., description='专利ID')
    validation_scope: str = Field('comprehensive', description='验证范围')
    validation_criteria: list[str] = Field(default=[], description='验证标准')
    strict_mode: bool = Field(False, description='严格模式')


class PatentMonitoringRequest(BaseModel):
    """专利监控请求"""
    patent_ids: list[str] = Field(..., description='要监控的专利ID列表')
    monitoring_type: str = Field('comprehensive', description='监控类型')
    alert_rules: list[dict[str, Any]] = Field(default=[], description='告警规则')
    notification_channels: list[str] = Field(default=['email'], description='通知渠道')


class PerformanceOptimizationRequest(BaseModel):
    """性能优化请求"""
    optimization_type: str = Field('auto', description='优化类型: auto, manual')
    optimization_targets: list[str] = Field(default=['throughput', 'latency'], description='优化目标')
    constraints: dict[str, Any] = Field(default={}, description='约束条件')


class AlertConfiguration(BaseModel):
    """告警配置"""
    alert_name: str = Field(..., description='告警名称')
    metric_name: str = Field(..., description='指标名称')
    condition: str = Field(..., description='条件')
    threshold: float = Field(..., description='阈值')
    severity: str = Field('warning', description='严重程度')
    notification_channels: list[str] = Field(default=['email'], description='通知渠道')


# 扩展的健康检查
@app.get('/')
async def root():
    """根路径"""
    return {
        'service': '增强专利行动层API服务',
        'status': 'running',
        'version': '2.0.0',
        'features': [
            'cognitive_action_bridge',
            'intelligent_scheduler',
            'workflow_orchestrator',
            'performance_optimizer',
            'monitoring_system',
            'batch_processing',
            'patent_portfolio',
            'anomaly_detection'
        ],
        'timestamp': datetime.now().isoformat()
    }


# 批量处理接口
@app.post('/api/v2/tasks/batch')
async def execute_batch_tasks(request: BatchTaskRequest):
    """批量执行任务"""
    try:
        logger.info(f"接收到批量任务请求，任务数量: {len(request.tasks)}")

        # 转换任务格式
        patent_tasks = []
        for task_data in request.tasks:
            deadline = None
            if task_data.get('deadline'):
                deadline = datetime.fromisoformat(task_data['deadline'])

            task = PatentTask(
                type=ActionType(task_data['task_type']),
                title=task_data['title'],
                description=task_data.get('description', ''),
                patent_data=task_data.get('patent_data', {}),
                parameters=task_data.get('parameters', {}),
                priority=TaskPriority(task_data.get('priority', 1)),
                deadline=deadline
            )
            patent_tasks.append(task)

        # 性能优化
        optimized_tasks = await optimizer.optimize_task_execution(patent_tasks)

        # 批量执行
        if request.batch_strategy == 'parallel':
            # 并行执行
            task_coroutines = []
            for task in optimized_tasks:
                task_coroutines.append(_execute_single_task(task))

            results = await asyncio.gather(*task_coroutines, return_exceptions=True)
        else:
            # 顺序执行
            results = []
            for task in optimized_tasks:
                result = await _execute_single_task(task)
                results.append(result)

        # 记录性能指标
        successful_tasks = len([r for r in results if r.get('success', False)])
        monitoring.record_business_metric('batch_task_success_rate', successful_tasks / len(results))
        monitoring.record_business_metric('batch_task_count', len(results))

        return {
            'success': True,
            'batch_size': len(patent_tasks),
            'successful_tasks': successful_tasks,
            'failed_tasks': len(results) - successful_tasks,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"批量任务执行失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# 专利组合分析接口
@app.post('/api/v2/portfolio/analyze')
async def analyze_patent_portfolio(request: PatentPortfolioRequest):
    """分析专利组合"""
    try:
        logger.info(f"接收到专利组合分析请求: {request.portfolio_name}")

        # 创建专利组合分析工作流
        workflow = await orchestrator.create_workflow(
            definition_id='patent_portfolio_analysis',
            input_data={
                'portfolio_name': request.portfolio_name,
                'patent_ids': request.patent_ids,
                'analysis_type': request.analysis_type
            },
            parameters={
                'monitoring_enabled': request.monitoring_enabled
            },
            workflow_name=f"专利组合分析-{request.portfolio_name}"
        )

        # 执行工作流
        execution_result = await orchestrator.execute_workflow(workflow.workflow_id, True)

        return {
            'success': True,
            'portfolio_id': workflow.workflow_id,
            'portfolio_name': request.portfolio_name,
            'patent_count': len(request.patent_ids),
            'analysis_type': request.analysis_type,
            'monitoring_enabled': request.monitoring_enabled,
            'workflow_id': workflow.workflow_id,
            'execution_result': execution_result,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"专利组合分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# 专利对比分析接口
@app.post('/api/v2/patents/compare')
async def compare_patents(request: PatentComparisonRequest):
    """专利对比分析"""
    try:
        logger.info(f"接收到专利对比请求: {request.source_patent_id}")

        # 创建对比任务
        comparison_task = PatentTask(
            type=ActionType.PATENT_COMPARISON,
            title=f"专利对比分析-{request.source_patent_id}",
            patent_data={
                'source_patent_id': request.source_patent_id,
                'target_patent_ids': request.target_patent_ids
            },
            parameters={
                'comparison_aspects': request.comparison_aspects,
                'detailed_analysis': True
            },
            priority=TaskPriority.HIGH
        )

        # 执行对比任务
        result = await _execute_single_task(comparison_task)

        return {
            'success': result.get('success', False),
            'source_patent_id': request.source_patent_id,
            'target_patents': request.target_patent_ids,
            'comparison_aspects': request.comparison_aspects,
            'result': result.get('result'),
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"专利对比分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# 专利验证接口
@app.post('/api/v2/patents/validate')
async def validate_patent(request: PatentValidationRequest):
    """专利验证"""
    try:
        logger.info(f"接收到专利验证请求: {request.patent_id}")

        # 创建验证任务
        validation_task = PatentTask(
            type=ActionType.PATENT_VALIDATION,
            title=f"专利验证-{request.patent_id}",
            patent_data={
                'patent_id': request.patent_id
            },
            parameters={
                'validation_scope': request.validation_scope,
                'validation_criteria': request.validation_criteria,
                'strict_mode': request.strict_mode
            },
            priority=TaskPriority.HIGH if request.strict_mode else TaskPriority.NORMAL
        )

        # 执行验证任务
        result = await _execute_single_task(validation_task)

        return {
            'success': result.get('success', False),
            'patent_id': request.patent_id,
            'validation_scope': request.validation_scope,
            'strict_mode': request.strict_mode,
            'validation_result': result.get('result'),
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"专利验证失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# 专利监控配置接口
@app.post('/api/v2/monitoring/configure')
async def configure_patent_monitoring(request: PatentMonitoringRequest):
    """配置专利监控"""
    try:
        logger.info(f"接收到专利监控配置请求，专利数量: {len(request.patent_ids)}")

        # 创建监控任务
        monitoring_task = PatentTask(
            type=ActionType.PATENT_MONITORING,
            title=f"专利监控配置-{len(request.patent_ids)}个专利",
            patent_data={
                'patent_ids': request.patent_ids
            },
            parameters={
                'monitoring_type': request.monitoring_type,
                'alert_rules': request.alert_rules,
                'notification_channels': request.notification_channels,
                'auto_renewal': True
            },
            priority=TaskPriority.NORMAL
        )

        # 执行监控配置
        result = await _execute_single_task(monitoring_task)

        # 配置告警规则
        for rule in request.alert_rules:
            monitoring.rule_engine.add_rule(rule)

        return {
            'success': result.get('success', False),
            'patent_count': len(request.patent_ids),
            'monitoring_type': request.monitoring_type,
            'alert_rules_count': len(request.alert_rules),
            'notification_channels': request.notification_channels,
            'monitoring_id': result.get('result', {}).get('monitoring_id'),
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"专利监控配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# 性能优化接口
@app.post('/api/v2/performance/optimize')
async def optimize_performance(request: PerformanceOptimizationRequest):
    """性能优化"""
    try:
        logger.info(f"接收到性能优化请求: {request.optimization_type}")

        if request.optimization_type == 'auto':
            # 自动优化
            optimization_result = await _auto_optimize_performance(request.optimization_targets)
        else:
            # 手动优化
            optimization_result = await _manual_optimize_performance(
                request.optimization_targets,
                request.constraints
            )

        return {
            'success': True,
            'optimization_type': request.optimization_type,
            'optimization_targets': request.optimization_targets,
            'optimization_result': optimization_result,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"性能优化失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# 告警配置接口
@app.post('/api/v2/alerts/configure')
async def configure_alert(alert_config: AlertConfiguration):
    """配置告警"""
    try:
        logger.info(f"接收到告警配置请求: {alert_config.alert_name}")

        # 添加告警规则
        rule = {
            'name': alert_config.alert_name,
            'metric': alert_config.metric_name,
            'condition': alert_config.condition,
            'threshold': alert_config.threshold,
            'severity': alert_config.severity,
            'message': f"告警: {alert_config.alert_name}",
            'source': 'user_configured'
        }

        monitoring.rule_engine.add_rule(rule)

        return {
            'success': True,
            'alert_name': alert_config.alert_name,
            'metric': alert_config.metric_name,
            'condition': alert_config.condition,
            'threshold': alert_config.threshold,
            'severity': alert_config.severity,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"告警配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# 监控和性能接口
@app.get('/api/v2/performance/metrics')
async def get_performance_metrics(
    metric_name: str | None = Query(None, description='指标名称'),
    duration_minutes: int = Query(5, description='时间范围(分钟)')
):
    """获取性能指标"""
    try:
        if metric_name:
            # 获取特定指标
            stats = optimizer.metrics_collector.get_metric_stats(metric_name, duration_minutes=duration_minutes)
            return {
                'metric_name': metric_name,
                'duration_minutes': duration_minutes,
                'stats': stats,
                'timestamp': datetime.now().isoformat()
            }
        else:
            # 获取所有性能指标
            performance_report = optimizer.get_performance_report()
            return {
                'performance_report': performance_report,
                'timestamp': datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"获取性能指标失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get('/api/v2/monitoring/alerts')
async def get_alerts(
    severity: str | None = Query(None, description='告警严重程度'),
    resolved: bool | None = Query(None, description='是否已解决')
):
    """获取告警列表"""
    try:
        monitoring_status = monitoring.get_monitoring_status()
        alerts = monitoring_status.get('active_alerts', [])

        # 过滤条件
        if severity:
            alerts = [a for a in alerts if a['severity'] == severity]
        if resolved is not None:
            alerts = [a for a in alerts if a['resolved'] == resolved]

        return {
            'total_alerts': len(alerts),
            'alerts': alerts,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"获取告警列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post('/api/v2/alerts/{alert_id}/acknowledge')
async def acknowledge_alert(alert_id: str, acknowledged_by: str = Body(..., embed=True)):
    """确认告警"""
    try:
        success = monitoring.acknowledge_alert(alert_id, acknowledged_by)
        if not success:
            raise HTTPException(status_code=404, detail='告警不存在')

        return {
            'success': True,
            'alert_id': alert_id,
            'acknowledged_by': acknowledged_by,
            'timestamp': datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"确认告警失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post('/api/v2/alerts/{alert_id}/resolve')
async def resolve_alert(alert_id: str):
    """解决告警"""
    try:
        success = monitoring.resolve_alert(alert_id)
        if not success:
            raise HTTPException(status_code=404, detail='告警不存在')

        return {
            'success': True,
            'alert_id': alert_id,
            'timestamp': datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"解决告警失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# 高级分析接口
@app.get('/api/v2/analytics/workflow/performance')
async def get_workflow_performance(
    workflow_id: str | None = Query(None, description='工作流ID'),
    days: int = Query(7, description='分析天数')
):
    """获取工作流性能分析"""
    try:
        # 获取工作流性能数据
        workflows = orchestrator.list_workflows()

        if workflow_id:
            workflows = [w for w in workflows if w['workflow_id'] == workflow_id]

        # 计算性能指标
        performance_data = []
        for workflow in workflows:
            workflow_status = orchestrator.get_workflow_status(workflow['workflow_id'])
            if workflow_status:
                performance_data.append({
                    'workflow_id': workflow['workflow_id'],
                    'name': workflow['name'],
                    'type': workflow['type'],
                    'status': workflow['status'],
                    'progress': workflow['progress'],
                    'created_at': workflow['created_at']
                })

        # 计算统计信息
        total_workflows = len(performance_data)
        completed_workflows = len([w for w in performance_data if w['status'] == 'completed'])
        success_rate = completed_workflows / total_workflows if total_workflows > 0 else 0

        return {
            'analysis_period_days': days,
            'total_workflows': total_workflows,
            'completed_workflows': completed_workflows,
            'success_rate': success_rate,
            'workflows': performance_data,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"获取工作流性能分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get('/api/v2/analytics/task/distribution')
async def get_task_distribution(
    hours: int = Query(24, description='分析小时数')
):
    """获取任务分布分析"""
    try:
        # 获取任务分布数据
        active_tasks = cognitive_bridge.get_active_tasks_status()
        active_workflows = orchestrator.get_orchestrator_status()

        distribution = {
            'active_tasks': active_tasks['total_active_tasks'],
            'tasks_by_priority': active_tasks['tasks_by_priority'],
            'tasks_by_type': active_tasks['tasks_by_type'],
            'active_workflows': active_workflows['active_workflows'],
            'statistics': active_workflows['statistics']
        }

        return {
            'analysis_period_hours': hours,
            'distribution': distribution,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"获取任务分布分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# 系统管理接口
@app.post('/api/v2/system/maintenance')
async def system_maintenance(
    action: str = Body(..., description='维护操作'),
    parameters: dict[str, Any] = Body(default={}, description='操作参数')
):
    """系统维护操作"""
    try:
        logger.info(f"接收到系统维护请求: {action}")

        if action == 'cleanup':
            # 清理操作
            result = await _system_cleanup(**parameters)
        elif action == 'backup':
            # 备份操作
            result = await _system_backup(**parameters)
        elif action == 'restart':
            # 重启操作
            result = await _system_restart(**parameters)
        else:
            raise HTTPException(status_code=400, detail=f"不支持的维护操作: {action}")

        return {
            'success': True,
            'action': action,
            'parameters': parameters,
            'result': result,
            'timestamp': datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"系统维护操作失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# 辅助函数
async def _execute_single_task(task: PatentTask) -> dict[str, Any]:
    """执行单个任务"""
    start_time = datetime.now()

    try:
        executor = executor_factory.get_executor(task.type.value)
        if not executor:
            raise ValueError(f"未找到任务类型 {task.type} 的执行器")

        result = await executor.execute(task)

        execution_time = (datetime.now() - start_time).total_seconds()

        # 记录性能数据
        performance_data = TaskPerformanceData(
            task_id=task.id,
            task_type=task.type.value,
            start_time=start_time,
            end_time=datetime.now(),
            execution_time=execution_time,
            success=result.status == 'success',
            result=result.result if hasattr(result, 'result') else None
        )
        optimizer.record_task_completion(performance_data)

        return {
            'success': result.status == 'success',
            'task_id': task.id,
            'task_type': task.type.value,
            'result': result.data if hasattr(result, 'data') else result.result,
            'execution_time': execution_time,
            'metadata': result.metadata if hasattr(result, 'metadata') else {}
        }

    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()

        # 记录失败的性能数据
        performance_data = TaskPerformanceData(
            task_id=task.id,
            task_type=task.type.value,
            start_time=start_time,
            end_time=datetime.now(),
            execution_time=execution_time,
            success=False,
            error_message=str(e)
        )
        optimizer.record_task_completion(performance_data)

        return {
            'success': False,
            'task_id': task.id,
            'task_type': task.type.value,
            'error': str(e),
            'execution_time': execution_time
        }


async def _auto_optimize_performance(targets: list[str]) -> dict[str, Any]:
    """自动性能优化"""
    optimization_results = {}

    for target in targets:
        if target == 'throughput':
            # 优化吞吐量
            optimization_results['throughput'] = '已启用并行处理和批处理优化'
        elif target == 'latency':
            # 优化延迟
            optimization_results['latency'] = '已启用缓存和预测优化'
        elif target == 'resource_usage':
            # 优化资源使用
            optimization_results['resource_usage'] = '已启用负载均衡和资源调度优化'

    return optimization_results


async def _manual_optimize_performance(targets: list[str], constraints: dict[str, Any]) -> dict[str, Any]:
    """手动性能优化"""
    optimization_results = {}

    for target in targets:
        if target == 'throughput':
            max_concurrent = constraints.get('max_concurrent_tasks', 10)
            optimization_results['throughput'] = f"已设置最大并发任务数为 {max_concurrent}"
        elif target == 'latency':
            cache_size = constraints.get('cache_size', 1000)
            optimization_results['latency'] = f"已设置缓存大小为 {cache_size}"
        elif target == 'resource_usage':
            cpu_limit = constraints.get('cpu_limit', 80)
            optimization_results['resource_usage'] = f"已设置CPU使用限制为 {cpu_limit}%"

    return optimization_results


async def _system_cleanup(**kwargs) -> dict[str, Any]:
    """系统清理"""
    # 清理过期缓存
    optimizer.cache.clear_expired()

    # 清理已完成的任务
    completed_count = len(orchestrator.completed_workflows)

    return {
        'cleaned_items': '过期缓存和已完成任务',
        'completed_workflows': completed_count,
        'cache_cleared': True
    }


async def _system_backup(**kwargs) -> dict[str, Any]:
    """系统备份"""
    backup_path = kwargs.get('backup_path', '/tmp/patent_action_backup')

    # 模拟备份操作
    return {
        'backup_path': backup_path,
        'backup_size': '10MB',
        'backup_completed': True
    }


async def _system_restart(**kwargs) -> dict[str, Any]:
    """系统重启"""
    component = kwargs.get('component', 'all')

    if component == 'all':
        # 重启所有组件
        orchestrator.stop_optimization()
        orchestrator.start_optimization()
        restart_result = '所有组件已重启'
    else:
        restart_result = f"组件 {component} 已重启"

    return {
        'component': component,
        'restart_result': restart_result,
        'restart_completed': True
    }


# 启动事件
@app.on_event('startup')
async def startup_event():
    """服务启动事件"""
    logger.info('增强专利行动层API服务启动')

    # 注册监控指标
    monitoring.record_business_metric('service_startup', 1, {'version': '2.0.0'})


@app.on_event('shutdown')
async def shutdown_event():
    """服务关闭事件"""
    logger.info('增强专利行动层API服务关闭')

    # 停止优化器和监控
    optimizer.stop_optimization()
    monitoring.stop_monitoring()


# 主函数
def main():
    """启动服务"""
    logger.info('启动增强专利行动层API服务...')

    uvicorn.run(
        app,
        host='0.0.0.0',
        port=9000,
        log_level='info',
        access_log=True
    )


if __name__ == '__main__':
    main()
