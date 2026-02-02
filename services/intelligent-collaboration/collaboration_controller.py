"""
智能协作中枢
协调Athena和小诺的工作，实现智能任务分配和结果融合
"""

import asyncio
import json
import logging
from core.logging_config import setup_logging
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

class CollaborationMode(Enum):
    """协作模式"""
    SEQUENTIAL = 'sequential'    # 顺序执行
    PARALLEL = 'parallel'       # 并行执行
    SYNERGY = 'synergy'         # 协同增效
    DELEGATE = 'delegate'       # 委托执行

class TaskStatus(Enum):
    """任务状态"""
    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'

@dataclass
class Task:
    """任务定义"""
    id: str
    type: str
    description: str
    complexity: float
    priority: int
    requirements: Dict[str, Any]
    created_at: datetime
    deadline: datetime | None = None

@dataclass
class TaskResult:
    """任务结果"""
    task_id: str
    executor: str
    status: TaskStatus
    result: Optional[Dict[str, Any]] = None
    error: str | None = None
    execution_time: float | None = None
    confidence: float | None = None
    metadata: Optional[Dict[str, Any]] = None

class CollaborationController:
    """协作控制器"""

    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.results: Dict[str, List[TaskResult]] = {}
        self.active_sessions: Dict[str, Dict] = {}
        self.executor_pool = ThreadPoolExecutor(max_workers=10)
        self._load_ai_capabilities()

    def _load_ai_capabilities(self) -> Any:
        """加载AI能力配置"""
        self.ai_capabilities = {
            'athena': {
                'strengths': ['analysis', 'strategy', 'planning', 'decision_making'],
                'specialties': ['patent_analysis', 'knowledge_graph', 'strategic_planning'],
                'processing_style': 'deep_thinking',
                'avg_response_time': 3.0,
                'capacity': 5
            },
            'xiaonuo': {
                'strengths': ['implementation', 'optimization', 'troubleshooting', 'development'],
                'specialties': ['code_generation', 'system_optimization', 'technical_implementation'],
                'processing_style': 'rapid_execution',
                'avg_response_time': 1.5,
                'capacity': 8
            }
        }

    async def submit_task(self, task_info: Dict[str, Any]) -> str:
        """提交任务"""
        task = Task(
            id=str(uuid.uuid4()),
            type=task_info['type'],
            description=task_info['description'],
            complexity=task_info.get('complexity', 0.5),
            priority=task_info.get('priority', 1),
            requirements=task_info.get('requirements', {}),
            created_at=datetime.now(),
            deadline=datetime.fromisoformat(task_info['deadline']) if 'deadline' in task_info else None
        )

        self.tasks[task.id] = task
        self.results[task.id] = []

        logger.info(f"任务已提交: {task.id} - {task.description}")

        # 异步执行任务
        asyncio.create_task(self._execute_task(task.id))

        return task.id

    async def _execute_task(self, task_id: str):
        """执行任务"""
        task = self.tasks.get(task_id)
        if not task:
            logger.error(f"任务未找到: {task_id}")
            return

        try:
            # 分析任务，选择执行策略
            strategy = await self._analyze_task(task)

            # 执行任务
            results = await self._execute_with_strategy(task, strategy)

            # 融合结果
            final_result = await self._synthesize_results(task, results)

            # 保存结果
            self.results[task_id].extend(results)

            logger.info(f"任务执行完成: {task_id}")
            return final_result

        except Exception as e:
            logger.error(f"任务执行失败 {task_id}: {str(e)}")
            error_result = TaskResult(
                task_id=task_id,
                executor='system',
                status=TaskStatus.FAILED,
                error=str(e)
            )
            self.results[task_id].append(error_result)

    async def _analyze_task(self, task: Task) -> Dict[str, Any]:
        """分析任务，选择执行策略"""
        # 任务类型分析
        task_characteristics = {
            'analytical': any(keyword in task.description.lower() for keyword in
                            ['分析', '评估', '策略', '方案', '建议']),
            'technical': any(keyword in task.description.lower() for keyword in
                           ['实现', '开发', '优化', '调试', '部署']),
            'creative': any(keyword in task.description.lower() for keyword in
                          ['设计', '创意', '创新', '构思']),
            'urgent': task.priority > 3,
            'complex': task.complexity > 0.7
        }

        # 选择执行策略
        if task_characteristics['analytical'] and task_characteristics['technical']:
            if task.complexity > 0.7:
                strategy = {
                    'mode': CollaborationMode.SYNERGY,
                    'participants': ['athena', 'xiaonuo'],
                    'sequence': ['athena', 'xiaonuo'],
                    'coordination_level': 'high'
                }
            else:
                strategy = {
                    'mode': CollaborationMode.SEQUENTIAL,
                    'participants': ['athena', 'xiaonuo'],
                    'sequence': ['athena', 'xiaonuo'],
                    'coordination_level': 'medium'
                }
        elif task_characteristics['analytical']:
            strategy = {
                'mode': CollaborationMode.DELEGATE,
                'participants': ['athena'],
                'coordination_level': 'low'
            }
        elif task_characteristics['technical']:
            strategy = {
                'mode': CollaborationMode.DELEGATE,
                'participants': ['xiaonuo'],
                'coordination_level': 'low'
            }
        elif task_characteristics['creative']:
            strategy = {
                'mode': CollaborationMode.PARALLEL,
                'participants': ['athena', 'xiaonuo'],
                'coordination_level': 'medium'
            }
        else:
            # 默认策略
            strategy = {
                'mode': CollaborationMode.DELEGATE,
                'participants': ['athena'] if task.complexity > 0.5 else ['xiaonuo'],
                'coordination_level': 'low'
            }

        logger.info(f"任务 {task.id} 选择策略: {strategy['mode'].value}")
        return strategy

    async def _execute_with_strategy(self, task: Task, strategy: Dict[str, Any]) -> List[TaskResult]:
        """根据策略执行任务"""
        mode = strategy['mode']
        participants = strategy['participants']
        sequence = strategy.get('sequence', participants)

        results = []

        if mode == CollaborationMode.DELEGATE:
            # 委托执行
            executor = participants[0]
            result = await self._execute_by_ai(task, executor)
            results.append(result)

        elif mode == CollaborationMode.SEQUENTIAL:
            # 顺序执行
            context = {}
            for executor in sequence:
                task_with_context = task
                if context:
                    # 添加前序执行者的上下文
                    task_with_context.requirements['previous_results'] = context

                result = await self._execute_by_ai(task_with_context, executor)
                results.append(result)

                if result.status == TaskStatus.COMPLETED and result.result:
                    context[executor] = result.result

        elif mode == CollaborationMode.PARALLEL:
            # 并行执行
            futures = [
                self._execute_by_ai(task, executor)
                for executor in participants
            ]

            for future in as_completed(futures):
                results.append(await future)

        elif mode == CollaborationMode.SYNERGY:
            # 协同增效
            synergy_results = await self._execute_synergy(task, participants)
            results.extend(synergy_results)

        return results

    async def _execute_by_ai(self, task: Task, ai_name: str) -> TaskResult:
        """由指定AI执行任务"""
        start_time = datetime.now()

        try:
            # 模拟AI执行
            result_data = await self._simulate_ai_execution(task, ai_name)

            execution_time = (datetime.now() - start_time).total_seconds()

            return TaskResult(
                task_id=task.id,
                executor=ai_name,
                status=TaskStatus.COMPLETED,
                result=result_data,
                execution_time=execution_time,
                confidence=result_data.get('confidence', 0.8),
                metadata={
                    'execution_mode': 'single',
                    'ai_capabilities': self.ai_capabilities[ai_name]
                }
            )

        except Exception as e:
            return TaskResult(
                task_id=task.id,
                executor=ai_name,
                status=TaskStatus.FAILED,
                error=str(e),
                execution_time=(datetime.now() - start_time).total_seconds()
            )

    async def _simulate_ai_execution(self, task: Task, ai_name: str) -> Dict[str, Any]:
        """模拟AI执行过程"""
        # 这里应该调用实际的AI服务
        capabilities = self.ai_capabilities[ai_name]

        # 模拟处理时间
        await asyncio.sleep(capabilities['avg_response_time'])

        # 根据任务类型生成模拟结果
        if '分析' in task.description:
            return {
                'type': 'analysis_result',
                'insights': [f"{ai_name}的分析洞察1', f'{ai_name}的分析洞察2"],
                'recommendations': [f"{ai_name}的建议1', f'{ai_name}的建议2"],
                'confidence': 0.85,
                'ai_perspective': ai_name
            }
        elif '实现' in task.description:
            return {
                'type': 'implementation_result',
                'solution': f"{ai_name}的技术解决方案",
                'code_snippets': [f"#{ai_name}生成的代码示例"],
                'steps': [f"{ai_name}的实施步骤"],
                'confidence': 0.9,
                'ai_perspective': ai_name
            }
        else:
            return {
                'type': 'general_result',
                'content': f"{ai_name}的处理结果",
                'details': ['详细内容1', '详细内容2'],
                'confidence': 0.8,
                'ai_perspective': ai_name
            }

    async def _execute_synergy(self, task: Task, participants: List[str]) -> List[TaskResult]:
        """协同增效执行"""
        results = []

        # 第一阶段：并行探索
        exploration_tasks = []
        for ai_name in participants:
            exploration_task = Task(
                id=f"{task.id}_explore_{ai_name}",
                type='exploration',
                description=f"探索任务: {task.description}",
                complexity=task.complexity * 0.5,
                priority=task.priority,
                requirements=task.requirements,
                created_at=datetime.now()
            )
            exploration_tasks.append((exploration_task, ai_name))

        # 并行执行探索
        exploration_futures = [
            self._execute_by_ai(exp_task, ai_name)
            for exp_task, ai_name in exploration_tasks
        ]

        exploration_results = []
        for future in as_completed(exploration_futures):
            result = await future
            exploration_results.append(result)
            results.append(result)

        # 第二阶段：综合分析
        if all(r.status == TaskStatus.COMPLETED for r in exploration_results):
            # Athena进行综合分析
            synthesis_task = Task(
                id=f"{task.id}_synthesis",
                type='synthesis',
                description=f"综合分析: {task.description}",
                complexity=task.complexity * 0.3,
                priority=task.priority,
                requirements={
                    'original_task': asdict(task),
                    'exploration_results': [r.result for r in exploration_results]
                },
                created_at=datetime.now()
            )

            synthesis_result = await self._execute_by_ai(synthesis_task, 'athena')
            results.append(synthesis_result)

            # 第三阶段：优化实施
            if synthesis_result.status == TaskStatus.COMPLETED:
                implementation_task = Task(
                    id=f"{task.id}_implementation",
                    type='implementation',
                    description=f"优化实施: {task.description}",
                    complexity=task.complexity * 0.2,
                    priority=task.priority,
                    requirements={
                        'synthesis_result': synthesis_result.result
                    },
                    created_at=datetime.now()
                )

                implementation_result = await self._execute_by_ai(implementation_task, 'xiaonuo')
                results.append(implementation_result)

        return results

    async def _synthesize_results(self, task: Task, results: List[TaskResult]) -> Dict[str, Any]:
        """融合结果"""
        if not results:
            return {'status': 'error', 'message': '没有结果可融合'}

        # 如果只有一个结果，直接返回
        if len(results) == 1:
            return results[0].result

        # 多个结果的融合逻辑
        completed_results = [r for r in results if r.status == TaskStatus.COMPLETED]

        if not completed_results:
            return {'status': 'error', 'message': '没有成功的结果'}

        # 按置信度排序
        completed_results.sort(key=lambda x: x.confidence or 0, reverse=True)

        # 融合结果
        synthesized = {
            'status': 'success',
            'task_id': task.id,
            'synthesis_type': 'multi_ai_collaboration',
            'primary_result': completed_results[0].result,
            'supporting_insights': [r.result for r in completed_results[1:]],
            'confidence_score': sum(r.confidence or 0 for r in completed_results) / len(completed_results),
            'execution_summary': {
                'total_participants': len(completed_results),
                'execution_times': [r.execution_time for r in completed_results],
                'ai_contributors': [r.executor for r in completed_results]
            }
        }

        return synthesized

    def get_task_status(self, task_id: str) -> Dict[str, Any | None]:
        """获取任务状态"""
        task = self.tasks.get(task_id)
        if not task:
            return None

        results = self.results.get(task_id, [])

        return {
            'task': asdict(task),
            'results': [asdict(r) for r in results],
            'status': self._determine_overall_status(results)
        }

    def _determine_overall_status(self, results: List[TaskResult]) -> str:
        """确定整体状态"""
        if not results:
            return TaskStatus.PENDING.value

        if all(r.status == TaskStatus.COMPLETED for r in results):
            return TaskStatus.COMPLETED.value
        elif any(r.status == TaskStatus.FAILED for r in results):
            return TaskStatus.FAILED.value
        elif any(r.status == TaskStatus.IN_PROGRESS for r in results):
            return TaskStatus.IN_PROGRESS.value
        else:
            return TaskStatus.PENDING.value

    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = self.tasks.get(task_id)
        if not task:
            return False

        # 标记任务为取消
        # 这里还需要通知正在执行的AI停止
        logger.info(f"任务已取消: {task_id}")
        return True

    def get_active_tasks(self) -> List[str]:
        """获取活跃任务列表"""
        return [
            task_id for task_id, task in self.tasks.items()
            if self._determine_overall_status(self.results.get(task_id, []))
            in [TaskStatus.PENDING.value, TaskStatus.IN_PROGRESS.value]
        ]

    async def cleanup_completed_tasks(self, older_than_hours: int = 24):
        """清理已完成的任务"""
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)

        tasks_to_remove = []
        for task_id, task in self.tasks.items():
            if task.created_at < cutoff_time:
                status = self._determine_overall_status(self.results.get(task_id, []))
                if status in [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value]:
                    tasks_to_remove.append(task_id)

        for task_id in tasks_to_remove:
            del self.tasks[task_id]
            del self.results[task_id]
            logger.info(f"已清理任务: {task_id}")

# 全局协作控制器实例
collaboration_controller = CollaborationController()