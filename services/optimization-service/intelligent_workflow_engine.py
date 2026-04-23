import os

#!/usr/bin/env python3
"""
Athena平台智能工作流引擎
提供工作流设计、执行、监控和优化功能
"""

import asyncio
import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

# 导入其他优化模块
from intelligent_model_selector import (
    PerformanceTier,
    TaskComplexity,
    TaskRequirement,
    get_intelligent_model_selector,
)
from knowledge_graph_integration import get_knowledge_graph
from multimodal_processor import ProcessingTask, get_multimodal_processor

from core.logging_config import setup_logging

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

class TaskStatus(Enum):
    """任务状态"""
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
    PAUSED = 'paused'

class TaskPriority(Enum):
    """任务优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5

class WorkflowStatus(Enum):
    """工作流状态"""
    DRAFT = 'draft'
    ACTIVE = 'active'
    PAUSED = 'paused'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'

class TaskType(Enum):
    """任务类型"""
    DATA_PROCESSING = 'data_processing'
    MODEL_INFERENCE = 'model_inference'
    TEXT_ANALYSIS = 'text_analysis'
    MULTIMODAL_PROCESSING = 'multimodal_processing'
    KNOWLEDGE_EXTRACTION = 'knowledge_extraction'
    API_CALL = 'api_call'
    FILE_OPERATION = 'file_operation'
    EMAIL_SEND = 'email_send'
    DATABASE_OPERATION = 'database_operation'
    CUSTOM = 'custom'

class TriggerType(Enum):
    """触发器类型"""
    SCHEDULE = 'schedule'
    EVENT = 'event'
    MANUAL = 'manual'
    WEBHOOK = 'webhook'
    CONDITION = 'condition'

@dataclass
class WorkflowTask:
    """工作流任务"""
    task_id: str
    workflow_id: str
    name: str
    task_type: TaskType
    config: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL
    retry_count: int = 0
    max_retries: int = 3
    timeout: int | None = None  # 超时时间（秒）
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    execution_time: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class WorkflowTrigger:
    """工作流触发器"""
    trigger_id: str
    workflow_id: str
    trigger_type: TriggerType
    config: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    last_triggered: datetime | None = None
    trigger_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class WorkflowDefinition:
    """工作流定义"""
    workflow_id: str
    name: str
    description: str
    version: str = '1.0'
    tasks: list[WorkflowTask] = field(default_factory=list)
    triggers: list[WorkflowTrigger] = field(default_factory=list)
    variables: dict[str, Any] = field(default_factory=dict)
    settings: dict[str, Any] = field(default_factory=dict)
    status: WorkflowStatus = WorkflowStatus.DRAFT
    created_by: str = ''
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class WorkflowExecution:
    """工作流执行实例"""
    execution_id: str
    workflow_id: str
    status: WorkflowStatus = WorkflowStatus.ACTIVE
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None
    task_executions: dict[str, WorkflowTask] = field(default_factory=dict)
    variables: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None
    triggered_by: str = ''

class TaskExecutor:
    """任务执行器"""

    def __init__(self):
        """初始化任务执行器"""
        self.model_selector = get_intelligent_model_selector()
        self.multimodal_processor = get_multimodal_processor()
        self.knowledge_graph = get_knowledge_graph()
        self.executor = ThreadPoolExecutor(max_workers=10)

    async def execute_task(self, task: WorkflowTask, context: dict[str, Any]) -> dict[str, Any]:
        """执行任务"""
        logger.info(f"开始执行任务: {task.name} ({task.task_type.value})")

        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()

        try:
            if task.task_type == TaskType.DATA_PROCESSING:
                result = await self._execute_data_processing(task, context)
            elif task.task_type == TaskType.MODEL_INFERENCE:
                result = await self._execute_model_inference(task, context)
            elif task.task_type == TaskType.TEXT_ANALYSIS:
                result = await self._execute_text_analysis(task, context)
            elif task.task_type == TaskType.MULTIMODAL_PROCESSING:
                result = await self._execute_multimodal_processing(task, context)
            elif task.task_type == TaskType.KNOWLEDGE_EXTRACTION:
                result = await self._execute_knowledge_extraction(task, context)
            elif task.task_type == TaskType.API_CALL:
                result = await self._execute_api_call(task, context)
            elif task.task_type == TaskType.FILE_OPERATION:
                result = await self._execute_file_operation(task, context)
            elif task.task_type == TaskType.CUSTOM:
                result = await self._execute_custom_task(task, context)
            else:
                raise ValueError(f"不支持的任务类型: {task.task_type}")

            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.execution_time = (task.completed_at - task.started_at).total_seconds()

            logger.info(f"任务执行成功: {task.name}, 耗时: {task.execution_time:.2f}s")
            return result

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.now()
            task.execution_time = (task.completed_at - task.started_at).total_seconds()

            logger.error(f"任务执行失败: {task.name}, 错误: {e}")
            raise

    async def _execute_data_processing(self, task: WorkflowTask, context: dict[str, Any]) -> dict[str, Any]:
        """执行数据处理任务"""
        config = task.config

        # 获取输入数据
        input_data = config.get('input_data', [])
        if not input_data and 'input_source' in config:
            # 从上下文获取数据
            input_data = context.get(config['input_source'], [])

        # 处理操作
        operation = config.get('operation', 'transform')

        if operation == 'transform':
            # 数据转换
            output_data = []
            for item in input_data:
                transformed_item = self._apply_transformation(item, config.get('transformation_rules', {}))
                output_data.append(transformed_item)

        elif operation == 'filter':
            # 数据过滤
            filter_criteria = config.get('filter_criteria', {})
            output_data = [item for item in input_data if self._meets_criteria(item, filter_criteria)]

        elif operation == 'aggregate':
            # 数据聚合
            aggregation_type = config.get('aggregation_type', 'count')
            output_data = self._aggregate_data(input_data, aggregation_type)

        else:
            raise ValueError(f"不支持的数据处理操作: {operation}")

        return {
            'output_data': output_data,
            'processed_count': len(output_data),
            'operation': operation
        }

    def _apply_transformation(self, item: Any, rules: dict[str, Any]) -> Any:
        """应用转换规则"""
        if isinstance(item, dict):
            transformed_item = item.copy()

            for field, rule in rules.items():
                if field in transformed_item:
                    if rule.get('type') == 'uppercase':
                        transformed_item[field] = str(transformed_item[field]).upper()
                    elif rule.get('type') == 'lowercase':
                        transformed_item[field] = str(transformed_item[field]).lower()
                    elif rule.get('type') == 'format':
                        format_str = rule.get('format', '{}')
                        transformed_item[field] = format_str.format(transformed_item[field])

            return transformed_item

        return item

    def _meets_criteria(self, item: Any, criteria: dict[str, Any]) -> bool:
        """检查是否满足过滤条件"""
        if not isinstance(item, dict):
            return True

        for field_name, condition in criteria.items():
            if field_name not in item:
                return False

            value = item[field_name]
            cond_type = condition.get('type', 'equals')
            cond_value = condition.get('value')

            if cond_type == 'equals':
                if value != cond_value:
                    return False
            elif cond_type == 'contains':
                if cond_value not in str(value):
                    return False
            elif cond_type == 'greater_than':
                if float(value) <= float(cond_value):
                    return False
            elif cond_type == 'less_than':
                if float(value) >= float(cond_value):
                    return False

        return True

    def _aggregate_data(self, data: list[Any], aggregation_type: str) -> Any:
        """聚合数据"""
        if aggregation_type == 'count':
            return len(data)
        elif aggregation_type == 'sum':
            return sum(item for item in data if isinstance(item, (int, float)))
        elif aggregation_type == 'average':
            numeric_data = [item for item in data if isinstance(item, (int, float))]
            return sum(numeric_data) / len(numeric_data) if numeric_data else 0
        elif aggregation_type == 'group_by':
            group_field = data[0].get('group_field') if data else None  # type: ignore[attr-defined]
            if group_field:
                groups = {}
                for item in data:
                    if isinstance(item, dict) and group_field in item:
                        group_value = item[group_field]
                        if group_value not in groups:
                            groups[group_value] = []
                        groups[group_value].append(item)
                return groups

        return data

    async def _execute_model_inference(self, task: WorkflowTask, context: dict[str, Any]) -> dict[str, Any]:
        """执行模型推理任务"""
        config = task.config

        # 获取输入数据
        input_data = config.get('input_data', context.get('input_data'))
        if not input_data:
            raise ValueError('缺少模型推理输入数据')

        # 创建任务需求
        task_type = config.get('task_type', 'text_analysis')
        complexity_str = config.get('complexity', 'medium')
        complexity = TaskComplexity(complexity_str)

        requirement = TaskRequirement(
            task_id=f"workflow_{task.task_id}",
            task_type=task_type,
            complexity=complexity,
            performance_tier=PerformanceTier(config.get('performance_tier', 'medium')),
            cost_budget=config.get('cost_budget'),
            accuracy_requirement=config.get('accuracy_requirement', 0.8)
        )

        # 智能模型选择
        model_selection = await self.model_selector.select_optimal_model(requirement)

        # 模拟模型推理（实际应用中调用具体模型API）
        inference_result = {
            'selected_model': model_selection.selected_model.value,
            'confidence': model_selection.confidence,
            'expected_cost': model_selection.expected_cost,
            'input_processed': len(input_data) if isinstance(input_data, list) else 1,
            'output': f"模型 {model_selection.selected_model.value} 对输入数据的推理结果",
            'reasoning': model_selection.reasoning
        }

        return inference_result

    async def _execute_text_analysis(self, task: WorkflowTask, context: dict[str, Any]) -> dict[str, Any]:
        """执行文本分析任务"""
        config = task.config
        text = config.get('text', context.get('text', ''))

        if not text:
            raise ValueError('缺少文本分析输入')

        analysis_type = config.get('analysis_type', 'general')

        if analysis_type == 'sentiment':
            # 情感分析
            sentiment_score = self._analyze_sentiment(text)
            result = {
                'sentiment': sentiment_score,
                'analysis_type': 'sentiment',
                'text_length': len(text)
            }

        elif analysis_type == 'keyword_extraction':
            # 关键词提取
            keywords = self._extract_keywords(text)
            result = {
                'keywords': keywords,
                'analysis_type': 'keyword_extraction',
                'text_length': len(text)
            }

        elif analysis_type == 'entity_extraction':
            # 实体提取
            entities = self._extract_entities(text)
            result = {
                'entities': entities,
                'analysis_type': 'entity_extraction',
                'text_length': len(text)
            }

        else:
            # 通用文本分析
            result = {
                'char_count': len(text),
                'word_count': len(text.split()),
                'line_count': len(text.split('\n')),
                'analysis_type': 'general'
            }

        return result

    def _analyze_sentiment(self, text: str) -> dict[str, float]:
        """分析情感（简化版）"""
        positive_words = ['好', '优秀', '棒', '喜欢', '满意', '成功']
        negative_words = ['坏', '差', '糟糕', '失败', '不满', '问题']

        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)

        total_sentiment_words = positive_count + negative_count

        if total_sentiment_words == 0:
            return {'positive': 0.5, 'negative': 0.5, 'neutral': 1.0}

        positive_score = positive_count / total_sentiment_words
        negative_score = negative_count / total_sentiment_words
        neutral_score = max(0, 1 - positive_score - negative_score)

        return {
            'positive': positive_score,
            'negative': negative_score,
            'neutral': neutral_score
        }

    def _extract_keywords(self, text: str, max_keywords: int = 10) -> list[str]:
        """提取关键词（简化版）"""
        # 简单的关键词提取：去除停用词后取高频词
        stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}

        words = text.split()
        word_freq = {}

        for word in words:
            if len(word) > 1 and word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1

        # 按频率排序
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)

        return [word for word, freq in sorted_words[:max_keywords]

    def _extract_entities(self, text: str) -> list[dict[str, str]:
        """提取实体（简化版）"""
        entities = []

        # 简单的实体识别模式
        import re

        # 邮箱
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        for email in emails:
            entities.append({'type': 'email', 'value': email})

        # 电话号码
        phones = re.findall(r'\b1[3-9]\d{9}\b', text)
        for phone in phones:
            entities.append({'type': 'phone', 'value': phone})

        # 日期
        dates = re.findall(r'\b\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?\b', text)
        for date in dates:
            entities.append({'type': 'date', 'value': date})

        return entities

    async def _execute_multimodal_processing(self, task: WorkflowTask, context: dict[str, Any]) -> dict[str, Any]:
        """执行多模态处理任务"""
        config = task.config

        # 获取媒体项目
        media_source = config.get('media_source')
        if media_source in context:
            media_item = context[media_source]
        elif 'media_item' in config:
            media_item = config['media_item']
        else:
            raise ValueError('缺少多模态处理输入')

        # 确定处理任务
        processing_tasks = []
        task_types = config.get('processing_tasks', ['analyze_content'])

        for task_type in task_types:
            if task_type == 'extract_text':
                processing_tasks.append(ProcessingTask.EXTRACT_TEXT)
            elif task_type == 'analyze_content':
                processing_tasks.append(ProcessingTask.ANALYZE_CONTENT)
            elif task_type == 'generate_description':
                processing_tasks.append(ProcessingTask.GENERATE_DESCRIPTION)
            elif task_type == 'transcribe_audio':
                processing_tasks.append(ProcessingTask.TRANSCRIBE_AUDIO)
            elif task_type == 'extract_frames':
                processing_tasks.append(ProcessingTask.EXTRACT_FRAMES)

        # 执行多模态处理
        results = await self.multimodal_processor.process_media(media_item, processing_tasks)

        # 整理结果
        processed_results = []
        for result in results:
            processed_results.append({
                'task_type': result.task_type.value,
                'output_data': result.output_data,
                'confidence': result.confidence,
                'model_used': result.model_used,
                'processing_time': result.processing_time
            })

        return {
            'media_item_id': media_item.item_id,
            'modality_type': media_item.modality_type.value,
            'processing_results': processed_results,
            'total_tasks': len(processed_results)
        }

    async def _execute_knowledge_extraction(self, task: WorkflowTask, context: dict[str, Any]) -> dict[str, Any]:
        """执行知识提取任务"""
        config = task.config

        # 获取输入文本
        text = config.get('text', context.get('text', ''))
        if not text:
            raise ValueError('缺少知识提取输入文本')

        # 构建知识图谱
        stats = self.knowledge_graph.build_from_text(text, config.get('context', ''))

        # 获取知识图谱统计
        kg_stats = self.knowledge_graph.get_statistics()

        return {
            'extraction_stats': stats,
            'knowledge_graph_stats': kg_stats,
            'text_length': len(text),
            'context': config.get('context', '')
        }

    async def _execute_api_call(self, task: WorkflowTask, context: dict[str, Any]) -> dict[str, Any]:
        """执行API调用任务"""
        import aiohttp

        config = task.config
        url = config.get('url')
        method = config.get('method', 'GET').upper()
        headers = config.get('headers', {})
        params = config.get('params', {})
        data = config.get('data', {})

        if not url:
            raise ValueError('缺少API调用URL')

        # 替换URL中的变量
        for key, value in context.items():
            if isinstance(value, str):
                url = url.replace(f"{{{key}}}", value)

        async with aiohttp.ClientSession() as session:
            try:
                if method == 'GET':
                    async with session.get(url, headers=headers, params=params) as response:
                        result_data = await response.json()
                        status_code = response.status
                elif method == 'POST':
                    async with session.post(url, headers=headers, json=data) as response:
                        result_data = await response.json()
                        status_code = response.status
                else:
                    raise ValueError(f"不支持的HTTP方法: {method}")

                return {
                    'status_code': status_code,
                    'response_data': result_data,
                    'api_url': url,
                    'method': method
                }

            except Exception as e:
                return {
                    'error': str(e),
                    'api_url': url,
                    'method': method,
                    'status_code': None
                }

    async def _execute_file_operation(self, task: WorkflowTask, context: dict[str, Any]) -> dict[str, Any]:
        """执行文件操作任务"""
        import os
        import shutil

        config = task.config
        operation = config.get('operation')

        if operation == 'read':
            file_path = config.get('file_path', context.get('file_path'))
            if not file_path or not os.path.exists(file_path):
                raise ValueError(f"文件不存在: {file_path}")

            with open(file_path, encoding='utf-8') as f:
                content = f.read()

            return {
                'content': content,
                'file_path': file_path,
                'file_size': os.path.getsize(file_path)
            }

        elif operation == 'write':
            file_path = config.get('file_path')
            content = config.get('content', context.get('content'))

            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return {
                'file_path': file_path,
                'bytes_written': len(content.encode('utf-8'))
            }

        elif operation == 'copy':
            source_path = config.get('source_path', context.get('source_path'))
            target_path = config.get('target_path')

            shutil.copy2(source_path, target_path)

            return {
                'source_path': source_path,
                'target_path': target_path,
                'copied': True
            }

        else:
            raise ValueError(f"不支持的文件操作: {operation}")

    async def _execute_custom_task(self, task: WorkflowTask, context: dict[str, Any]) -> dict[str, Any]:
        """执行自定义任务"""
        config = task.config

        # 这里可以调用用户定义的自定义函数
        # 或者通过插件系统执行

        # 模拟自定义任务执行
        custom_function_name = config.get('function_name', 'default_function')
        parameters = config.get('parameters', {})

        # 合并上下文参数
        merged_parameters = {**context, **parameters}

        # 模拟执行结果
        result = {
            'function_name': custom_function_name,
            'parameters': merged_parameters,
            'execution_result': f"自定义函数 {custom_function_name} 执行完成",
            'timestamp': datetime.now().isoformat()
        }

        return result

class WorkflowEngine:
    """工作流引擎"""

    def __init__(self):
        """初始化工作流引擎"""
        self.workflows = {}  # workflow_id -> WorkflowDefinition
        self.executions = {}  # execution_id -> WorkflowExecution
        self.task_executor = TaskExecutor()
        self.execution_queue = asyncio.Queue()
        self.running = False
        self.scheduler_task = None
        self.executor_task = None

    def create_workflow(self, name: str, description: str, created_by: str = '') -> WorkflowDefinition:
        """创建工作流"""
        workflow = WorkflowDefinition(
            workflow_id=str(uuid.uuid4()),
            name=name,
            description=description,
            created_by=created_by
        )

        self.workflows[workflow.workflow_id] = workflow

        logger.info(f"创建工作流: {name} ({workflow.workflow_id})")
        return workflow

    def add_task_to_workflow(self, workflow_id: str, task_name: str, task_type: TaskType,
                            config: dict[str, Any], dependencies: list[str] = None) -> WorkflowTask:
        """向工作流添加任务"""
        if workflow_id not in self.workflows:
            raise ValueError(f"工作流不存在: {workflow_id}")

        workflow = self.workflows[workflow_id]

        task = WorkflowTask(
            task_id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            name=task_name,
            task_type=task_type,
            config=config,
            dependencies=dependencies or []
        )

        workflow.tasks.append(task)
        workflow.updated_at = datetime.now()

        logger.info(f"向工作流 {workflow_id} 添加任务: {task_name}")
        return task

    def add_trigger_to_workflow(self, workflow_id: str, trigger_type: TriggerType,
                              config: dict[str, Any]) -> WorkflowTrigger:
        """向工作流添加触发器"""
        if workflow_id not in self.workflows:
            raise ValueError(f"工作流不存在: {workflow_id}")

        workflow = self.workflows[workflow_id]

        trigger = WorkflowTrigger(
            trigger_id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            trigger_type=trigger_type,
            config=config
        )

        workflow.triggers.append(trigger)
        workflow.updated_at = datetime.now()

        logger.info(f"向工作流 {workflow_id} 添加触发器: {trigger_type.value}")
        return trigger

    async def execute_workflow(self, workflow_id: str, trigger_context: dict[str, Any] = None,
                             triggered_by: str = 'manual') -> WorkflowExecution:
        """执行工作流"""
        if workflow_id not in self.workflows:
            raise ValueError(f"工作流不存在: {workflow_id}")

        workflow = self.workflows[workflow_id]

        # 创建执行实例
        execution = WorkflowExecution(
            execution_id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            variables=workflow.variables.copy(),
            triggered_by=triggered_by
        )

        # 合并触发器上下文
        if trigger_context:
            execution.variables.update(trigger_context)

        # 复制任务到执行实例
        for task in workflow.tasks:
            execution_task = WorkflowTask(
                task_id=task.task_id,
                workflow_id=task.workflow_id,
                name=task.name,
                task_type=task.task_type,
                config=task.config.copy(),
                dependencies=task.dependencies.copy(),
                inputs=task.inputs.copy(),
                priority=task.priority
            )
            execution.task_executions[task.task_id] = execution_task

        self.executions[execution.execution_id] = execution

        # 加入执行队列
        await self.execution_queue.put(execution)

        logger.info(f"启动工作流执行: {workflow_id} ({execution.execution_id})")
        return execution

    async def start_scheduler(self):
        """启动调度器"""
        self.running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        self.executor_task = asyncio.create_task(self._executor_loop())

        logger.info('工作流调度器已启动')

    async def stop_scheduler(self):
        """停止调度器"""
        self.running = False

        if self.scheduler_task:
            self.scheduler_task.cancel()

        if self.executor_task:
            self.executor_task.cancel()

        logger.info('工作流调度器已停止')

    async def _scheduler_loop(self):
        """调度器循环"""
        while self.running:
            try:
                # 检查触发器
                await self._check_triggers()

                # 等待一段时间再检查
                await asyncio.sleep(10)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"调度器循环异常: {e}")
                await asyncio.sleep(5)

    async def _executor_loop(self):
        """执行器循环"""
        while self.running:
            try:
                # 获取待执行的工作流
                execution = await asyncio.wait_for(self.execution_queue.get(), timeout=1.0)

                # 执行工作流
                await self._execute_workflow_tasks(execution)

            except TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"执行器循环异常: {e}")

    async def _check_triggers(self):
        """检查触发器"""
        current_time = datetime.now()

        for workflow in self.workflows.values():
            for trigger in workflow.triggers:
                if not trigger.enabled:
                    continue

                should_trigger = False

                if trigger.trigger_type == TriggerType.SCHEDULE:
                    # 检查定时触发
                    should_trigger = self._check_schedule_trigger(trigger, current_time)

                elif trigger.trigger_type == TriggerType.CONDITION:
                    # 检查条件触发
                    should_trigger = self._check_condition_trigger(trigger)

                if should_trigger:
                    await self.execute_workflow(
                        workflow.workflow_id,
                        trigger.config.get('context', {}),
                        f"trigger_{trigger.trigger_id}"
                    )

                    trigger.last_triggered = current_time
                    trigger.trigger_count += 1

    def _check_schedule_trigger(self, trigger: WorkflowTrigger, current_time: datetime) -> bool:
        """检查定时触发器"""
        config = trigger.config

        # 简单的定时触发检查
        if 'cron' in config:
            # 这里可以实现完整的cron表达式解析
            # 简化版：每小时检查
            return True

        elif 'interval' in config:
            # 间隔触发
            interval_seconds = config['interval']
            if trigger.last_triggered:
                elapsed = (current_time - trigger.last_triggered).total_seconds()
                return elapsed >= interval_seconds
            else:
                return True

        return False

    def _check_condition_trigger(self, trigger: WorkflowTrigger) -> bool:
        """检查条件触发器"""
        config = trigger.config

        # 这里可以实现复杂的条件检查逻辑
        # 简化版：检查环境变量或系统状态
        condition_type = config.get('type')

        if condition_type == 'file_exists':
            file_path = config.get('file_path')
            return file_path and os.path.exists(file_path)

        elif condition_type == 'time_based':
            # 基于时间的条件
            target_hour = config.get('hour')
            if target_hour is not None:
                return datetime.now().hour == target_hour

        return False

    async def _execute_workflow_tasks(self, execution: WorkflowExecution):
        """执行工作流任务"""
        workflow = self.workflows[execution.workflow_id]

        # 构建任务依赖图
        self._build_task_graph(workflow.tasks)

        # 执行任务
        completed_tasks = set()
        failed_tasks = set()

        while len(completed_tasks) + len(failed_tasks) < len(workflow.tasks):
            # 找到可以执行的任务（依赖已完成）
            ready_tasks = []
            for task in workflow.tasks:
                if (task.task_id not in completed_tasks and
                    task.task_id not in failed_tasks and
                    all(dep in completed_tasks for dep in task.dependencies)):
                    ready_tasks.append(task)

            if not ready_tasks:
                # 没有可执行的任务，检查是否有失败的任务
                if failed_tasks:
                    execution.status = WorkflowStatus.FAILED
                    execution.error_message = '任务执行失败'
                break

            # 并发执行就绪的任务
            tasks_to_execute = []
            for task in ready_tasks:
                execution_task = execution.task_executions[task.task_id]

                # 准备任务上下文
                task_context = execution.variables.copy()

                # 添加已完成任务的输出
                for completed_task_id in completed_tasks:
                    completed_task = execution.task_executions[completed_task_id]
                    task_context[f"task_{completed_task_id}_output"] = completed_task.outputs

                tasks_to_execute.append((execution_task, task_context))

            # 执行任务
            if len(tasks_to_execute) == 1:
                # 单任务执行
                task, context = tasks_to_execute[0]
                try:
                    result = await self.task_executor.execute_task(task, context)
                    task.outputs = result
                    completed_tasks.add(task.task_id)

                except Exception as e:
                    task.error_message = str(e)
                    failed_tasks.add(task.task_id)
                    logger.error(f"任务执行失败: {task.name}, 错误: {e}")

            else:
                # 多任务并发执行
                semaphore = asyncio.Semaphore(5)  # 限制并发数

                async def execute_single_task(task_info):
                    task, context = task_info
                    async with semaphore:
                        try:
                            result = await self.task_executor.execute_task(task, context)
                            task.outputs = result
                            return task.task_id, None
                        except Exception as e:
                            task.error_message = str(e)
                            return task.task_id, str(e)

                # 并发执行
                results = await asyncio.gather(
                    *[execute_single_task(task_info) for task_info in tasks_to_execute],
                    return_exceptions=True
                )

                # 处理结果
                for task_id, error in results:
                    if error:
                        failed_tasks.add(task_id)
                    else:
                        completed_tasks.add(task_id)

        # 更新执行状态
        if len(failed_tasks) == 0:
            execution.status = WorkflowStatus.COMPLETED
        elif len(completed_tasks) > 0:
            execution.status = WorkflowStatus.FAILED  # 部分完成也算失败
        else:
            execution.status = WorkflowStatus.FAILED

        execution.completed_at = datetime.now()

        logger.info(f"工作流执行完成: {execution.execution_id}, 状态: {execution.status.value}")

    def _build_task_graph(self, tasks: list[WorkflowTask]) -> dict[str, list[str]:
        """构建任务依赖图"""
        graph = {}

        for task in tasks:
            graph[task.task_id] = task.dependencies.copy()

        return graph

    def get_workflow_status(self, workflow_id: str) -> dict[str, Any]:
        """获取工作流状态"""
        if workflow_id not in self.workflows:
            return {'error': '工作流不存在'}

        workflow = self.workflows[workflow_id]

        # 获取最近的执行记录
        recent_executions = [
            execution for execution in self.executions.values()
            if execution.workflow_id == workflow_id
        ]
        recent_executions.sort(key=lambda x: x.started_at, reverse=True)

        return {
            'workflow_id': workflow_id,
            'name': workflow.name,
            'status': workflow.status.value,
            'task_count': len(workflow.tasks),
            'trigger_count': len(workflow.triggers),
            'recent_executions': len(recent_executions),
            'last_execution': recent_executions[0].execution_id if recent_executions else None,
            'created_at': workflow.created_at.isoformat(),
            'updated_at': workflow.updated_at.isoformat()
        }

    def get_execution_details(self, execution_id: str) -> dict[str, Any]:
        """获取执行详情"""
        if execution_id not in self.executions:
            return {'error': '执行记录不存在'}

        execution = self.executions[execution_id]

        # 任务执行详情
        task_details = []
        for task in execution.task_executions.values():
            task_details.append({
                'task_id': task.task_id,
                'name': task.name,
                'type': task.task_type.value,
                'status': task.status.value,
                'priority': task.priority.value,
                'execution_time': task.execution_time,
                'error_message': task.error_message,
                'started_at': task.started_at.isoformat() if task.started_at else None,
                'completed_at': task.completed_at.isoformat() if task.completed_at else None
            })

        return {
            'execution_id': execution_id,
            'workflow_id': execution.workflow_id,
            'status': execution.status.value,
            'started_at': execution.started_at.isoformat(),
            'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
            'error_message': execution.error_message,
            'triggered_by': execution.triggered_by,
            'variables': execution.variables,
            'task_count': len(task_details),
            'completed_tasks': len([t for t in task_details if t['status'] == 'completed']),
            'failed_tasks': len([t for t in task_details if t['status'] == 'failed']),
            'task_details': task_details
        }

    def get_engine_stats(self) -> dict[str, Any]:
        """获取引擎统计信息"""
        total_workflows = len(self.workflows)
        total_executions = len(self.executions)

        # 按状态统计工作流
        workflow_status_counts = {}
        for workflow in self.workflows.values():
            status = workflow.status.value
            workflow_status_counts[status] = workflow_status_counts.get(status, 0) + 1

        # 按状态统计执行
        execution_status_counts = {}
        for execution in self.executions.values():
            status = execution.status.value
            execution_status_counts[status] = execution_status_counts.get(status, 0) + 1

        # 队列状态
        queue_size = self.execution_queue.qsize()

        return {
            'total_workflows': total_workflows,
            'total_executions': total_executions,
            'workflow_status_distribution': workflow_status_counts,
            'execution_status_distribution': execution_status_counts,
            'queue_size': queue_size,
            'scheduler_running': self.running,
            'available_task_types': [task_type.value for task_type in TaskType],
            'available_trigger_types': [trigger_type.value for trigger_type in TriggerType]
        }

# 全局工作流引擎实例
_workflow_engine = None

def get_workflow_engine() -> WorkflowEngine:
    """获取工作流引擎实例"""
    global _workflow_engine
    if _workflow_engine is None:
        _workflow_engine = WorkflowEngine()
    return _workflow_engine

# 工具函数
async def create_sample_workflow() -> str:
    """创建示例工作流"""
    engine = get_workflow_engine()

    # 创建文档分析工作流
    workflow = engine.create_workflow(
        '文档智能分析工作流',
        '自动分析文档内容，提取关键信息并进行多模态处理'
    )

    # 添加任务
    # 1. 文件读取任务
    engine.add_task_to_workflow(
        workflow.workflow_id,
        '读取文档文件',
        TaskType.FILE_OPERATION,
        {
            'operation': 'read',
            'file_path': '{{document_path}}'
        }
    )

    # 2. 文本分析任务
    engine.add_task_to_workflow(
        workflow.workflow_id,
        '分析文本内容',
        TaskType.TEXT_ANALYSIS,
        {
            'analysis_type': 'keyword_extraction',
            'text': '{{task_1_output.content}}'
        },
        dependencies=[engine.workflows[workflow.workflow_id].tasks[0].task_id]
    )

    # 3. 模型推理任务
    engine.add_task_to_workflow(
        workflow.workflow_id,
        '智能分类推理',
        TaskType.MODEL_INFERENCE,
        {
            'task_type': 'text_classification',
            'complexity': 'medium',
            'input_data': '{{task_2_output.keywords}}'
        },
        dependencies=[engine.workflows[workflow.workflow_id].tasks[1].task_id]
    )

    # 4. 知识提取任务
    engine.add_task_to_workflow(
        workflow.workflow_id,
        '构建知识图谱',
        TaskType.KNOWLEDGE_EXTRACTION,
        {
            'text': '{{task_1_output.content}}',
            'context': '文档分析'
        },
        dependencies=[engine.workflows[workflow.workflow_id].tasks[0].task_id]
    )

    # 5. API通知任务
    engine.add_task_to_workflow(
        workflow.workflow_id,
        '发送分析结果',
        TaskType.API_CALL,
        {
            'url': 'https://api.example.com/notify',
            'method': 'POST',
            'data': {
                'workflow_id': '{{workflow_id}}',
                'analysis_result': '{{task_2_output}}',
                'classification': '{{task_3_output}}',
                'knowledge_stats': '{{task_4_output.extraction_stats}}'
            }
        },
        dependencies=[
            engine.workflows[workflow.workflow_id].tasks[1].task_id,
            engine.workflows[workflow.workflow_id].tasks[2].task_id,
            engine.workflows[workflow.workflow_id].tasks[3].task_id
        ]
    )

    # 添加定时触发器
    engine.add_trigger_to_workflow(
        workflow.workflow_id,
        TriggerType.SCHEDULE,
        {
            'interval': 3600,  # 每小时执行一次
            'context': {'document_path': '/path/to/document.txt'}
        }
    )

    # 设置为活跃状态
    workflow.status = WorkflowStatus.ACTIVE

    return workflow.workflow_id

if __name__ == '__main__':
    async def test_workflow_engine():
        """测试工作流引擎"""
        engine = get_workflow_engine()

        # 启动调度器
        await engine.start_scheduler()

        # 创建示例工作流
        workflow_id = await create_sample_workflow()
        logger.info(f"创建示例工作流: {workflow_id}")

        # 手动执行工作流
        execution = await engine.execute_workflow(
            workflow_id,
            {'document_path': '/tmp/test_document.txt'},
            'test_manual'
        )

        logger.info(f"启动工作流执行: {execution.execution_id}")

        # 等待执行完成
        await asyncio.sleep(5)

        # 获取执行详情
        details = engine.get_execution_details(execution.execution_id)
        logger.info(f"执行详情: {json.dumps(details, ensure_ascii=False, indent=2)}")

        # 获取引擎统计
        stats = engine.get_engine_stats()
        logger.info(f"引擎统计: {json.dumps(stats, ensure_ascii=False, indent=2)}")

        # 停止调度器
        await engine.stop_scheduler()

    asyncio.run(test_workflow_engine())
