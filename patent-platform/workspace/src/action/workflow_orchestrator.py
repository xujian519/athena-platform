#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专利工作流编排引擎
Patent Workflow Orchestrator

负责专利工作流的创建、执行、监控和管理，
支持复杂的多步骤专利业务流程自动化。

Created by Athena + 小诺 (AI助手)
Date: 2025-12-05
"""

import asyncio
import json
import logging
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WorkflowStatus(str, Enum):
    """工作流状态"""
    PENDING = 'pending'
    RUNNING = 'running'
    PAUSED = 'paused'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
    TIMEOUT = 'timeout'


class StepStatus(str, Enum):
    """步骤状态"""
    WAITING = 'waiting'
    READY = 'ready'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    SKIPPED = 'skipped'
    CANCELLED = 'cancelled'


class WorkflowType(str, Enum):
    """工作流类型"""
    PATENT_ANALYSIS = 'patent_analysis'
    PATENT_FILING = 'patent_filing'
    PATENT_VALIDATION = 'patent_validation'
    PATENT_MONITORING = 'patent_monitoring'
    PATENT_PORTFOLIO = 'patent_portfolio'
    CUSTOM = 'custom'


@dataclass
class WorkflowStep:
    """工作流步骤"""
    step_id: str
    name: str
    description: str = ''
    executor_name: str = ''
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    timeout: timedelta | None = None
    retry_count: int = 3
    retry_delay: timedelta = timedelta(seconds=30)
    status: StepStatus = StepStatus.WAITING
    result: Optional[Dict[str, Any]] = None
    error: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowInstance:
    """工作流实例"""
    workflow_id: str
    name: str
    workflow_type: WorkflowType
    description: str = ''
    steps: List[WorkflowStep] = field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.PENDING
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    timeout: timedelta | None = None
    parallel_execution: bool = False
    max_parallel_steps: int = 5
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowDefinition:
    """工作流定义"""
    definition_id: str
    name: str
    workflow_type: WorkflowType
    description: str = ''
    steps_template: List[Dict[str, Any]] = field(default_factory=list)
    default_parameters: Dict[str, Any] = field(default_factory=dict)
    estimated_duration: timedelta | None = None
    version: str = '1.0'


class WorkflowOrchestrator:
    """工作流编排器"""

    def __init__(self, max_concurrent_workflows: int = 10):
        """
        初始化工作流编排器

        Args:
            max_concurrent_workflows: 最大并发工作流数
        """
        self.max_concurrent_workflows = max_concurrent_workflows
        self.logger = logging.getLogger(f"{__name__}.WorkflowOrchestrator")

        # 工作流管理
        self.active_workflows: Dict[str, WorkflowInstance] = {}
        self.completed_workflows: Dict[str, WorkflowInstance] = {}
        self.workflow_definitions: Dict[str, WorkflowDefinition] = {}

        # 执行器注册
        self.executors: Dict[str, Any] = {}

        # 线程池
        self.executor_pool = ThreadPoolExecutor(max_workers=20)

        # 监控和统计
        self.workflow_stats = {
            'total_created': 0,
            'total_completed': 0,
            'total_failed': 0,
            'average_execution_time': 0.0,
            'success_rate': 0.0
        }

        # 事件回调
        self.event_callbacks: Dict[str, List[Callable]] = {
            'workflow_started': [],
            'workflow_completed': [],
            'workflow_failed': [],
            'step_started': [],
            'step_completed': [],
            'step_failed'
        }

        # 初始化内置工作流定义
        self._initialize_builtin_workflows()

        self.logger.info('工作流编排器初始化完成')

    def _initialize_builtin_workflows(self):
        """初始化内置工作流定义"""
        # 专利分析工作流
        patent_analysis_workflow = WorkflowDefinition(
            definition_id='patent_analysis_standard',
            name='标准专利分析工作流',
            workflow_type=WorkflowType.PATENT_ANALYSIS,
            description='完整的专利分析流程，包括数据收集、特征提取、认知分析和报告生成',
            steps_template=[
                {
                    'step_id': 'data_collection',
                    'name': '专利数据收集',
                    'description': '收集专利相关的所有必要数据',
                    'executor_name': 'DataCollectionExecutor',
                    'parameters': {
                        'sources': ['patent_office', 'technical_databases', 'web_search'],
                        'data_types': ['full_text', 'claims', 'drawings', 'legal_status']
                    },
                    'timeout': 1800  # 30分钟
                },
                {
                    'step_id': 'data_preprocessing',
                    'name': '数据预处理',
                    'description': '标准化和清理收集到的数据',
                    'executor_name': 'DataPreprocessorExecutor',
                    'parameters': {
                        'format': 'standardized',
                        'quality_check': True,
                        'deduplication': True
                    },
                    'dependencies': ['data_collection'],
                    'timeout': 900  # 15分钟
                },
                {
                    'step_id': 'feature_extraction',
                    'name': '特征提取',
                    'description': '提取专利的技术和法律特征',
                    'executor_name': 'FeatureExtractionExecutor',
                    'parameters': {
                        'extraction_depth': 'comprehensive',
                        'feature_types': ['technical', 'legal', 'semantic']
                    },
                    'dependencies': ['data_preprocessing'],
                    'timeout': 2400  # 40分钟
                },
                {
                    'step_id': 'cognitive_analysis',
                    'name': '认知决策分析',
                    'description': '使用AI进行深度的专利分析',
                    'executor_name': 'CognitiveAnalysisExecutor',
                    'parameters': {
                        'analysis_types': ['novelty', 'inventiveness', 'industrial_applicability'],
                        'depth': 'comprehensive'
                    },
                    'dependencies': ['feature_extraction'],
                    'timeout': 3600  # 1小时
                },
                {
                    'step_id': 'report_generation',
                    'name': '分析报告生成',
                    'description': '生成完整的专利分析报告',
                    'executor_name': 'ReportGeneratorExecutor',
                    'parameters': {
                        'report_format': 'comprehensive',
                        'include_visualizations': True,
                        'language': 'zh-CN'
                    },
                    'dependencies': ['cognitive_analysis'],
                    'timeout': 1200  # 20分钟
                }
            ],
            estimated_duration=timedelta(hours=2, minutes=30)
        )

        # 专利申请工作流
        patent_filing_workflow = WorkflowDefinition(
            definition_id='patent_filing_standard',
            name='标准专利申请工作流',
            workflow_type=WorkflowType.PATENT_FILING,
            description='从发明披露到专利提交的完整流程',
            steps_template=[
                {
                    'step_id': 'disclosure_assessment',
                    'name': '发明披露评估',
                    'description': '评估发明披露的完整性和可专利性',
                    'executor_name': 'InventionDisclosureExecutor',
                    'parameters': {
                        'assessment_criteria': ['patentability', 'commercial_value', 'strategic_fit']
                    },
                    'timeout': 3600  # 1小时
                },
                {
                    'step_id': 'patentability_analysis',
                    'name': '可专利性分析',
                    'description': '进行全面的现有技术检索和可专利性分析',
                    'executor_name': 'PatentabilityAnalysisExecutor',
                    'parameters': {
                        'search_strategy': 'comprehensive',
                        'analysis_depth': 'detailed'
                    },
                    'dependencies': ['disclosure_assessment'],
                    'timeout': 14400  # 4小时
                },
                {
                    'step_id': 'document_drafting',
                    'name': '申请文件起草',
                    'description': '起草专利申请文件',
                    'executor_name': 'DocumentDraftingExecutor',
                    'parameters': {
                        'document_types': ['specification', 'claims', 'drawings', 'abstract'],
                        'jurisdiction': 'CN'
                    },
                    'dependencies': ['patentability_analysis'],
                    'timeout': 21600  # 6小时
                },
                {
                    'step_id': 'internal_review',
                    'name': '内部审核',
                    'description': '进行内部的技术和法律审核',
                    'executor_name': 'InternalReviewExecutor',
                    'parameters': {
                        'review_criteria': ['technical_accuracy', 'legal_compliance', 'claim_scope'],
                        'revision_rounds': 2
                    },
                    'dependencies': ['document_drafting'],
                    'timeout': 7200  # 2小时
                },
                {
                    'step_id': 'filing_preparation',
                    'name': '申请准备',
                    'description': '准备最终提交的申请材料',
                    'executor_name': 'FilingPreparationExecutor',
                    'parameters': {
                        'final_check': True,
                        'format_compliance': True
                    },
                    'dependencies': ['internal_review'],
                    'timeout': 1800  # 30分钟
                }
            ],
            estimated_duration=timedelta(days=1)
        )

        # 注册工作流定义
        self.register_workflow_definition(patent_analysis_workflow)
        self.register_workflow_definition(patent_filing_workflow)

        self.logger.info(f"内置工作流定义初始化完成，共 {len(self.workflow_definitions)} 个")

    def register_executor(self, name: str, executor: Any):
        """注册执行器"""
        self.executors[name] = executor
        self.logger.info(f"注册执行器: {name}")

    def register_workflow_definition(self, definition: WorkflowDefinition):
        """注册工作流定义"""
        self.workflow_definitions[definition.definition_id] = definition
        self.logger.info(f"注册工作流定义: {definition.definition_id}")

    def register_event_callback(self, event: str, callback: Callable):
        """注册事件回调"""
        if event in self.event_callbacks:
            self.event_callbacks[event].append(callback)
            self.logger.info(f"注册事件回调: {event}")

    async def create_workflow(self,
                            definition_id: str,
                            input_data: Dict[str, Any],
                            parameters: Dict[str, Any] = None,
                            workflow_id: str = None) -> WorkflowInstance:
        """
        创建工作流实例

        Args:
            definition_id: 工作流定义ID
            input_data: 输入数据
            parameters: 自定义参数
            workflow_id: 自定义工作流ID

        Returns:
            WorkflowInstance: 工作流实例
        """
        if definition_id not in self.workflow_definitions:
            raise ValueError(f"未找到工作流定义: {definition_id}")

        definition = self.workflow_definitions[definition_id]

        # 创建工作流实例
        workflow_id = workflow_id or f"wf_{uuid.uuid4().hex[:8]}"
        workflow_instance = WorkflowInstance(
            workflow_id=workflow_id,
            name=definition.name,
            workflow_type=definition.workflow_type,
            description=definition.description,
            input_data=input_data,
            context={
                'definition_id': definition_id,
                'definition_version': definition.version,
                'parameters': parameters or {}
            }
        )

        # 创建工作流步骤
        for step_template in definition.steps_template:
            # 合并默认参数和自定义参数
            step_parameters = {**definition.default_parameters, **step_template.get('parameters', {})}
            if parameters:
                step_parameters.update(parameters.get(step_template['step_id'], {}))

            step = WorkflowStep(
                step_id=step_template['step_id'],
                name=step_template['name'],
                description=step_template.get('description', ''),
                executor_name=step_template.get('executor_name', ''),
                parameters=step_parameters,
                dependencies=step_template.get('dependencies', []),
                timeout=timedelta(seconds=step_template.get('timeout', 3600)),
                retry_count=step_template.get('retry_count', 3)
            )

            workflow_instance.steps.append(step)

        # 设置工作流超时
        if definition.estimated_duration:
            workflow_instance.timeout = definition.estimated_duration * 2  # 2倍安全时间

        # 注册工作流实例
        self.active_workflows[workflow_id] = workflow_instance
        self.workflow_stats['total_created'] += 1

        self.logger.info(f"创建工作流实例: {workflow_id} ({definition.name})")

        return workflow_instance

    async def execute_workflow(self,
                             workflow_id: str,
                             parallel_execution: bool = False) -> Dict[str, Any]:
        """
        执行工作流

        Args:
            workflow_id: 工作流ID
            parallel_execution: 是否允许并行执行

        Returns:
            Dict[str, Any]: 执行结果
        """
        if workflow_id not in self.active_workflows:
            raise ValueError(f"未找到工作流实例: {workflow_id}")

        workflow = self.active_workflows[workflow_id]

        if workflow.status != WorkflowStatus.PENDING:
            raise ValueError(f"工作流状态无效: {workflow.status}")

        self.logger.info(f"开始执行工作流: {workflow_id}")

        try:
            # 更新工作流状态
            workflow.status = WorkflowStatus.RUNNING
            workflow.started_at = datetime.now()
            workflow.parallel_execution = parallel_execution

            # 触发工作流开始事件
            await self._trigger_event('workflow_started', workflow)

            # 执行工作流步骤
            if parallel_execution:
                result = await self._execute_workflow_parallel(workflow)
            else:
                result = await self._execute_workflow_sequential(workflow)

            # 更新工作流状态
            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = datetime.now()
            workflow.output_data = result

            # 更新统计
            self._update_workflow_stats(workflow)

            # 移动到已完成列表
            self.completed_workflows[workflow_id] = self.active_workflows.pop(workflow_id)

            # 触发工作流完成事件
            await self._trigger_event('workflow_completed', workflow)

            self.logger.info(f"工作流执行完成: {workflow_id}")

            return {
                'workflow_id': workflow_id,
                'status': 'completed',
                'result': result,
                'execution_time': (workflow.completed_at - workflow.started_at).total_seconds(),
                'steps_completed': len([s for s in workflow.steps if s.status == StepStatus.COMPLETED]),
                'steps_failed': len([s for s in workflow.steps if s.status == StepStatus.FAILED])
            }

        except Exception as e:
            # 处理执行失败
            workflow.status = WorkflowStatus.FAILED
            workflow.completed_at = datetime.now()
            workflow.context['error'] = str(e)

            # 更新统计
            self._update_workflow_stats(workflow)

            # 移动到已完成列表
            self.completed_workflows[workflow_id] = self.active_workflows.pop(workflow_id)

            # 触发工作流失败事件
            await self._trigger_event('workflow_failed', workflow)

            self.logger.error(f"工作流执行失败: {workflow_id}, 错误: {str(e)}")

            return {
                'workflow_id': workflow_id,
                'status': 'failed',
                'error': str(e),
                'execution_time': (workflow.completed_at - workflow.started_at).total_seconds() if workflow.started_at else 0
            }

    async def _execute_workflow_sequential(self, workflow: WorkflowInstance) -> Dict[str, Any]:
        """顺序执行工作流"""
        results = {}

        for step in workflow.steps:
            # 检查依赖
            if not await self._check_step_dependencies(step, workflow):
                self.logger.warning(f"步骤 {step.step_id} 依赖未满足，跳过执行")
                step.status = StepStatus.SKIPPED
                continue

            # 执行步骤
            step_result = await self._execute_step(step, workflow)
            results[step.step_id] = step_result

            # 如果步骤失败且不继续，则停止工作流
            if step.status == StepStatus.FAILED and step.retry_count <= 0:
                raise Exception(f"步骤 {step.step_id} 执行失败: {step.error}")

        return results

    async def _execute_workflow_parallel(self, workflow: WorkflowInstance) -> Dict[str, Any]:
        """并行执行工作流"""
        results = {}
        pending_steps = {step.step_id: step for step in workflow.steps}
        completed_steps = set()
        failed_steps = set()

        while pending_steps and len(failed_steps) == 0:
            # 找出可以执行的步骤
            ready_steps = []
            for step_id, step in pending_steps.items():
                if step_id not in completed_steps and await self._check_step_dependencies(step, workflow):
                    ready_steps.append(step)

            if not ready_steps:
                # 检查是否有循环依赖
                if len(completed_steps) + len(failed_steps) < len(workflow.steps):
                    remaining_steps = set(pending_steps.keys()) - completed_steps - failed_steps
                    if remaining_steps:
                        raise Exception(f"检测到无法执行的步骤，可能存在循环依赖: {remaining_steps}")
                break

            # 限制并行数量
            ready_steps = ready_steps[:workflow.max_parallel_steps]

            # 并行执行步骤
            step_tasks = [self._execute_step(step, workflow) for step in ready_steps]
            step_results = await asyncio.gather(*step_tasks, return_exceptions=True)

            # 处理执行结果
            for step, result in zip(ready_steps, step_results):
                if isinstance(result, Exception):
                    failed_steps.add(step.step_id)
                    step.status = StepStatus.FAILED
                    step.error = str(result)
                    self.logger.error(f"步骤 {step.step_id} 执行失败: {str(result)}")
                else:
                    completed_steps.add(step.step_id)
                    results[step.step_id] = result

                # 从待执行列表中移除
                pending_steps.pop(step.step_id, None)

        if failed_steps:
            raise Exception(f"以下步骤执行失败: {failed_steps}")

        return results

    async def _check_step_dependencies(self, step: WorkflowStep, workflow: WorkflowInstance) -> bool:
        """检查步骤依赖"""
        for dep_id in step.dependencies:
            dep_step = next((s for s in workflow.steps if s.step_id == dep_id), None)
            if not dep_step:
                self.logger.error(f"步骤 {step.step_id} 依赖的步骤 {dep_id} 不存在")
                return False

            if dep_step.status != StepStatus.COMPLETED:
                return False

        return True

    async def _execute_step(self, step: WorkflowStep, workflow: WorkflowInstance) -> Dict[str, Any]:
        """执行单个步骤"""
        self.logger.info(f"开始执行步骤: {step.step_id} - {step.name}")

        step.status = StepStatus.RUNNING
        step.start_time = datetime.now()

        # 触发步骤开始事件
        await self._trigger_event('step_started', step, workflow)

        try:
            # 获取执行器
            executor = self.executors.get(step.executor_name)
            if not executor:
                raise ValueError(f"未找到执行器: {step.executor_name}")

            # 准备执行参数
            execution_params = {
                **step.parameters,
                'workflow_context': workflow.context,
                'input_data': workflow.input_data,
                'step_results': {
                    s.step_id: s.result for s in workflow.steps
                    if s.status == StepStatus.COMPLETED and s.result
                }
            }

            # 执行步骤
            if hasattr(executor, 'execute_async'):
                result = await executor.execute_async(execution_params)
            else:
                result = await asyncio.get_event_loop().run_in_executor(
                    self.executor_pool, executor.execute, execution_params
                )

            # 更新步骤状态
            step.status = StepStatus.COMPLETED
            step.result = result
            step.end_time = datetime.now()
            step.execution_time = (step.end_time - step.start_time).total_seconds()

            # 触发步骤完成事件
            await self._trigger_event('step_completed', step, workflow)

            self.logger.info(f"步骤执行完成: {step.step_id}, 耗时: {step.execution_time:.2f}秒")

            return result

        except Exception as e:
            # 重试逻辑
            if step.retry_count > 0:
                self.logger.warning(f"步骤 {step.step_id} 执行失败，剩余重试次数: {step.retry_count}")
                step.retry_count -= 1
                step.status = StepStatus.WAITING

                # 等待重试延迟
                await asyncio.sleep(step.retry_delay.total_seconds())

                # 递归重试
                return await self._execute_step(step, workflow)
            else:
                # 最终失败
                step.status = StepStatus.FAILED
                step.error = str(e)
                step.end_time = datetime.now()
                step.execution_time = (step.end_time - step.start_time).total_seconds()

                # 触发步骤失败事件
                await self._trigger_event('step_failed', step, workflow)

                self.logger.error(f"步骤执行最终失败: {step.step_id}, 错误: {str(e)}")
                raise

    async def _trigger_event(self, event: str, *args):
        """触发事件"""
        if event in self.event_callbacks:
            for callback in self.event_callbacks[event]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(*args)
                    else:
                        callback(*args)
                except Exception as e:
                    self.logger.error(f"事件回调执行失败: {event}, 错误: {str(e)}")

    def _update_workflow_stats(self, workflow: WorkflowInstance):
        """更新工作流统计"""
        if workflow.status == WorkflowStatus.COMPLETED:
            self.workflow_stats['total_completed'] += 1
        elif workflow.status == WorkflowStatus.FAILED:
            self.workflow_stats['total_failed'] += 1

        # 更新平均执行时间
        total_completed = self.workflow_stats['total_completed']
        if total_completed > 0 and workflow.started_at and workflow.completed_at:
            execution_time = (workflow.completed_at - workflow.started_at).total_seconds()
            current_avg = self.workflow_stats['average_execution_time']
            self.workflow_stats['average_execution_time'] = (
                (current_avg * (total_completed - 1) + execution_time) / total_completed
            )

        # 更新成功率
        total_finished = self.workflow_stats['total_completed'] + self.workflow_stats['total_failed']
        if total_finished > 0:
            self.workflow_stats['success_rate'] = self.workflow_stats['total_completed'] / total_finished

    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any | None]:
        """获取工作流状态"""
        workflow = self.active_workflows.get(workflow_id) or self.completed_workflows.get(workflow_id)
        if not workflow:
            return None

        # 计算进度
        completed_steps = len([s for s in workflow.steps if s.status == StepStatus.COMPLETED])
        total_steps = len(workflow.steps)
        progress = completed_steps / total_steps if total_steps > 0 else 0

        return {
            'workflow_id': workflow_id,
            'name': workflow.name,
            'status': workflow.status,
            'progress': progress,
            'completed_steps': completed_steps,
            'total_steps': total_steps,
            'created_at': workflow.created_at.isoformat(),
            'started_at': workflow.started_at.isoformat() if workflow.started_at else None,
            'completed_at': workflow.completed_at.isoformat() if workflow.completed_at else None,
            'steps_status': [
                {
                    'step_id': step.step_id,
                    'name': step.name,
                    'status': step.status,
                    'execution_time': step.execution_time,
                    'error': step.error
                }
                for step in workflow.steps
            ]
        }

    def list_workflows(self, status: WorkflowStatus | None = None) -> List[Dict[str, Any]]:
        """列出工作流"""
        workflows = []

        all_workflows = {**self.active_workflows, **self.completed_workflows}

        for workflow_id, workflow in all_workflows.items():
            if status is None or workflow.status == status:
                workflows.append({
                    'workflow_id': workflow_id,
                    'name': workflow.name,
                    'type': workflow.workflow_type,
                    'status': workflow.status,
                    'created_at': workflow.created_at.isoformat(),
                    'progress': len([s for s in workflow.steps if s.status == StepStatus.COMPLETED]) / len(workflow.steps)
                })

        return sorted(workflows, key=lambda x: x['created_at'], reverse=True)

    def get_orchestrator_status(self) -> Dict[str, Any]:
        """获取编排器状态"""
        return {
            'active_workflows': len(self.active_workflows),
            'completed_workflows': len(self.completed_workflows),
            'available_executors': list(self.executors.keys()),
            'available_definitions': list(self.workflow_definitions.keys()),
            'statistics': self.workflow_stats,
            'max_concurrent_workflows': self.max_concurrent_workflows
        }

    async def cancel_workflow(self, workflow_id: str) -> bool:
        """取消工作流"""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            return False

        workflow.status = WorkflowStatus.CANCELLED
        workflow.completed_at = datetime.now()

        # 取消正在运行的步骤
        for step in workflow.steps:
            if step.status == StepStatus.RUNNING:
                step.status = StepStatus.CANCELLED
                step.end_time = datetime.now()

        # 移动到已完成列表
        self.completed_workflows[workflow_id] = self.active_workflows.pop(workflow_id)

        self.logger.info(f"工作流已取消: {workflow_id}")
        return True

    async def pause_workflow(self, workflow_id: str) -> bool:
        """暂停工作流"""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow or workflow.status != WorkflowStatus.RUNNING:
            return False

        workflow.status = WorkflowStatus.PAUSED
        self.logger.info(f"工作流已暂停: {workflow_id}")
        return True

    async def resume_workflow(self, workflow_id: str) -> bool:
        """恢复工作流"""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow or workflow.status != WorkflowStatus.PAUSED:
            return False

        workflow.status = WorkflowStatus.RUNNING
        self.logger.info(f"工作流已恢复: {workflow_id}")
        return True


# 测试代码
async def test_workflow_orchestrator():
    """测试工作流编排器"""
    orchestrator = WorkflowOrchestrator()

    # 创建模拟执行器
    class MockExecutor:
        async def execute_async(self, params):
            await asyncio.sleep(1)  # 模拟执行时间
            return {
                'status': 'success',
                'message': f"执行完成: {params}",
                'timestamp': datetime.now().isoformat()
            }

    # 注册执行器
    orchestrator.register_executor('DataCollectionExecutor', MockExecutor())
    orchestrator.register_executor('DataPreprocessorExecutor', MockExecutor())
    orchestrator.register_executor('FeatureExtractionExecutor', MockExecutor())
    orchestrator.register_executor('CognitiveAnalysisExecutor', MockExecutor())
    orchestrator.register_executor('ReportGeneratorExecutor', MockExecutor())

    # 创建工作流实例
    workflow = await orchestrator.create_workflow(
        definition_id='patent_analysis_standard',
        input_data={
            'patent_id': 'CN202410001234.5',
            'title': '测试专利',
            'abstract': '这是一个测试专利的摘要'
        }
    )

    logger.info(f"创建工作流: {workflow.workflow_id}")
    logger.info(f"工作流步骤: {[step.step_id for step in workflow.steps]}")

    # 获取工作流状态
    status = orchestrator.get_workflow_status(workflow.workflow_id)
    logger.info(f"工作流状态: {status}")

    # 执行工作流
    logger.info("\n开始执行工作流...")
    result = await orchestrator.execute_workflow(workflow.workflow_id, parallel_execution=True)

    logger.info(f"工作流执行结果: {result}")

    # 获取最终状态
    final_status = orchestrator.get_workflow_status(workflow.workflow_id)
    logger.info(f"最终状态: {final_status}")

    # 获取编排器状态
    orch_status = orchestrator.get_orchestrator_status()
    logger.info(f"\n编排器状态: {orch_status}")


if __name__ == '__main__':
    asyncio.run(test_workflow_orchestrator())