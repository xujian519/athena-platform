#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能工具自动执行引擎
Smart Tool Auto-Execution Engine

增强版工具自动调用系统,修复功能降级问题,提供精准的工具选择和执行能力

作者: Athena AI系统
创建时间: 2025-12-08
版本: 2.0.0 (修复版)
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from .intent_engine import IntentResult, recognize_user_intent

logger = logging.getLogger(__name__)

class ToolStatus(Enum):
    """工具状态"""
    AVAILABLE = 'available'      # 可用
    BUSY = 'busy'              # 忙碌
    ERROR = 'error'            # 错误
    MAINTENANCE = 'maintenance' # 维护中

class ExecutionPriority(Enum):
    """执行优先级"""
    CRITICAL = 'critical'    # 关键
    HIGH = 'high'           # 高
    NORMAL = 'normal'       # 普通
    LOW = 'low'            # 低

@dataclass
class ToolCapability:
    """工具能力描述"""
    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    performance_metrics: dict[str, float] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

@dataclass
class ExecutionRequest:
    """执行请求"""
    request_id: str
    tool_name: str
    parameters: dict[str, Any]
    priority: ExecutionPriority = ExecutionPriority.NORMAL
    timeout: float = 30.0
    retry_count: int = 0
    max_retries: int = 3
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ExecutionResult:
    """执行结果"""
    request_id: str
    tool_name: str
    success: bool
    result: Any = None
    error: str | None = None
    execution_time: float = 0.0
    start_time: datetime | None = None
    end_time: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

class ToolAutoExecutionEngine:
    """智能工具自动执行引擎"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # 工具注册表
        self.tools: dict[str, ToolCapability] = {}
        self.tool_status: dict[str, ToolStatus] = {}

        # 执行队列
        self.execution_queue: asyncio.Queue = asyncio.Queue()
        self.active_executions: dict[str, asyncio.Task] = {}

        # 性能统计
        self.performance_stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'average_execution_time': 0.0,
            'tool_usage_stats': {},
            'error_types': {}
        }

        # 执行器配置
        self.config = {
            'max_concurrent_executions': 10,
            'default_timeout': 30.0,
            'enable_retry': True,
            'enable_tool_health_check': True,
            'health_check_interval': 60.0
        }

        # 工具健康检查任务
        self.health_check_task: asyncio.Task | None = None

        self.logger.info('🔧 智能工具自动执行引擎初始化完成')

    async def initialize(self):
        """初始化执行引擎"""
        self.logger.info('🚀 初始化工具执行引擎...')

        # 注册内置工具
        await self._register_builtin_tools()

        # 启动健康检查
        if self.config['enable_tool_health_check']:
            self.health_check_task = asyncio.create_task(self._health_check_loop())

        # 启动执行队列处理器
        asyncio.create_task(self._process_execution_queue())

        self.logger.info('✅ 工具执行引擎初始化完成')

    async def _register_builtin_tools(self):
        """注册内置工具"""
        # 代码生成工具
        await self.register_tool(
            name='code_generator',
            description='代码生成工具,支持多种编程语言',
            input_schema={
                'type': 'object',
                'properties': {
                    'language': {'type': 'string', 'enum': ['python', 'javascript', 'java', 'cpp']},
                    'specification': {'type': 'string'},
                    'requirements': {'type': 'array', 'items': {'type': 'string'}}
                },
                'required': ['language', 'specification']
            },
            output_schema={'type': 'object'},
            tags=['code', 'generation', 'development']
        )

        # 数据分析工具
        await self.register_tool(
            name='data_analyzer',
            description='数据分析工具,支持统计分析、图表生成',
            input_schema={
                'type': 'object',
                'properties': {
                    'data': {'type': 'array'},
                    'analysis_type': {'type': 'string', 'enum': ['statistical', 'visualization', 'trend']},
                    'options': {'type': 'object'}
                },
                'required': ['data', 'analysis_type']
            },
            output_schema={'type': 'object'},
            tags=['data', 'analysis', 'statistics']
        )

        # 文档处理工具
        await self.register_tool(
            name='document_processor',
            description='文档处理工具,支持提取、总结、格式转换',
            input_schema={
                'type': 'object',
                'properties': {
                    'document': {'type': 'string'},
                    'operation': {'type': 'string', 'enum': ['extract', 'summarize', 'convert']},
                    'format': {'type': 'string'}
                },
                'required': ['document', 'operation']
            },
            output_schema={'type': 'object'},
            tags=['document', 'processing', 'nlp']
        )

        # 系统管理工具
        await self.register_tool(
            name='system_manager',
            description='系统管理工具,支持服务管理、监控、部署',
            input_schema={
                'type': 'object',
                'properties': {
                    'operation': {'type': 'string', 'enum': ['start', 'stop', 'restart', 'status', 'deploy']},
                    'target': {'type': 'string'},
                    'options': {'type': 'object'}
                },
                'required': ['operation', 'target']
            },
            output_schema={'type': 'object'},
            tags=['system', 'management', 'deployment']
        )

        # 搜索工具
        await self.register_tool(
            name='search_engine',
            description='搜索引擎工具,支持多源检索',
            input_schema={
                'type': 'object',
                'properties': {
                    'query': {'type': 'string'},
                    'sources': {'type': 'array', 'items': {'type': 'string'}},
                    'filters': {'type': 'object'},
                    'limit': {'type': 'integer', 'default': 10}
                },
                'required': ['query']
            },
            output_schema={'type': 'object'},
            tags=['search', 'retrieval', 'information']
        )

    async def register_tool(self, name: str, description: str,
                          input_schema: dict[str, Any],                          output_schema: dict[str, Any],                          tags: list[str] | None = None,
                          dependencies: list[str] | None = None) -> bool:
        """注册工具"""
        try:
            capability = ToolCapability(
                name=name,
                description=description,
                input_schema=input_schema,
                output_schema=output_schema,
                tags=tags or [],
                dependencies=dependencies or []
            )

            self.tools[name] = capability
            self.tool_status[name] = ToolStatus.AVAILABLE
            self.performance_stats['tool_usage_stats'][name] = 0

            self.logger.info(f"✅ 工具注册成功: {name}")
            return True

        except Exception as e:
            self.logger.error(f"❌ 工具注册失败 {name}: {str(e)}")
            return False

    async def execute_from_intent(self, intent: IntentResult, context: dict[str, Any] | None = None) -> list[ExecutionResult]:
        """
        基于意图自动执行工具

        Args:
            intent: 意图识别结果
            context: 上下文信息

        Returns:
            list[ExecutionResult]: 执行结果列表
        """
        self.logger.info(f"🎯 基于意图执行工具: {intent.intent_type.value}")

        # 选择合适的工具
        selected_tools = await self._select_tools_for_intent(intent, context)

        if not selected_tools:
            self.logger.warning('未找到合适的工具执行该意图')
            return []

        # 创建执行请求
        execution_requests = await self._create_execution_requests(intent, selected_tools, context)

        # 执行工具
        results = await self._execute_tools_batch(execution_requests)

        return results

    async def _select_tools_for_intent(self, intent: IntentResult, context: dict[str, Any] | None = None) -> list[str]:
        """为意图选择合适的工具"""
        candidate_tools = []

        # 基于意图推荐的工具
        for tool_name in intent.suggested_tools:
            if tool_name in self.tools and self.tool_status[tool_name] == ToolStatus.AVAILABLE:
                candidate_tools.append(tool_name)

        # 基于智能选择的工具
        intent_tool_mapping = {
            'information_query': ['search_engine'],
            'analysis_request': ['data_analyzer', 'search_engine'],
            'code_generation': ['code_generator'],
            'data_analysis': ['data_analyzer'],
            'document_processing': ['document_processor'],
            'task_execution': ['system_manager'],
            'problem_solving': ['search_engine', 'data_analyzer']
        }

        if intent.intent_type.value in intent_tool_mapping:
            for tool_name in intent_tool_mapping[intent.intent_type.value]:
                if tool_name not in candidate_tools and tool_name in self.tools:
                    if self.tool_status[tool_name] == ToolStatus.AVAILABLE:
                        candidate_tools.append(tool_name)

        # 基于复杂度的工具选择
        if intent.complexity.value in ['complex', 'expert']:
            # 为复杂任务添加辅助工具
            for tool_name in self.tools:
                if tool_name not in candidate_tools:
                    capability = self.tools[tool_name]
                    if 'analysis' in capability.tags or 'system' in capability.tags:
                        if self.tool_status[tool_name] == ToolStatus.AVAILABLE:
                            candidate_tools.append(tool_name)

        # 限制工具数量
        return candidate_tools[:3]

    async def _create_execution_requests(self, intent: IntentResult,
                                        selected_tools: list[str],
                                        context: dict[str, Any] | None = None) -> list[ExecutionRequest]:
        """创建执行请求"""
        requests = []

        for tool_name in selected_tools:
            request_id = str(uuid.uuid4())

            # 根据工具类型和意图生成参数
            parameters = await self._generate_tool_parameters(tool_name, intent, context)

            # 确定优先级
            priority = self._determine_priority(tool_name, intent)

            # 确定超时时间
            timeout = self._determine_timeout(tool_name, intent.complexity)

            request = ExecutionRequest(
                request_id=request_id,
                tool_name=tool_name,
                parameters=parameters,
                priority=priority,
                timeout=timeout,
                metadata={
                    'intent_type': intent.intent_type.value,
                    'complexity': intent.complexity.value,
                    'key_entities': intent.key_entities,
                    'context': context
                }
            )

            requests.append(request)

        return requests

    async def _generate_tool_parameters(self, tool_name: str, intent: IntentResult,
                                      context: dict[str, Any] | None = None) -> dict[str, Any]:
        """生成工具参数"""
        parameters = {}

        if tool_name == 'search_engine':
            parameters['query'] = ' '.join(intent.key_concepts)
            parameters['limit'] = 10
            if context:
                parameters['context'] = context

        elif tool_name == 'code_generator':
            parameters['language'] = 'python'  # 默认语言
            parameters['specification'] = ' '.join(intent.key_concepts)
            if '代码' in intent.key_entities:
                parameters['language'] = self._detect_programming_language(intent.key_entities)

        elif tool_name == 'data_analyzer':
            parameters['analysis_type'] = 'statistical'
            parameters['options'] = {'include_visualization': intent.complexity.value != 'simple'}

        elif tool_name == 'document_processor':
            parameters['operation'] = 'extract'
            parameters['document'] = ' '.join(intent.key_concepts)

        elif tool_name == 'system_manager':
            parameters['operation'] = 'status'
            parameters['target'] = 'system'

        return parameters

    def _detect_programming_language(self, entities: list[str]) -> str:
        """检测编程语言"""
        language_mapping = {
            'python': ['python', 'Python', 'py'],
            'javascript': ['javascript', 'JavaScript', 'js', 'node'],
            'java': ['java', 'Java'],
            'cpp': ['c++', 'C++', 'cpp']
        }

        for language, keywords in language_mapping.items():
            if any(keyword in entities for keyword in keywords):
                return language

        return 'python'  # 默认

    def _determine_priority(self, tool_name: str, intent: IntentResult) -> ExecutionPriority:
        """确定执行优先级"""
        if intent.complexity.value == 'expert':
            return ExecutionPriority.HIGH
        elif intent.complexity.value == 'complex':
            return ExecutionPriority.NORMAL
        else:
            return ExecutionPriority.NORMAL

    def _determine_timeout(self, tool_name: str, complexity) -> float:
        """确定超时时间"""
        base_timeout = {
            'search_engine': 15.0,
            'code_generator': 30.0,
            'data_analyzer': 45.0,
            'document_processor': 20.0,
            'system_manager': 10.0
        }

        timeout = base_timeout.get(tool_name, 30.0)

        # 根据复杂度调整超时时间
        if complexity.value == 'complex':
            timeout *= 1.5
        elif complexity.value == 'expert':
            timeout *= 2.0

        return timeout

    async def _execute_tools_batch(self, requests: list[ExecutionRequest]) -> list[ExecutionResult]:
        """批量执行工具"""
        results = []

        # 根据优先级排序
        requests.sort(key=lambda x: {
            ExecutionPriority.CRITICAL: 0,
            ExecutionPriority.HIGH: 1,
            ExecutionPriority.NORMAL: 2,
            ExecutionPriority.LOW: 3
        }[x.priority])

        # 并行执行(考虑并发限制)
        semaphore = asyncio.Semaphore(self.config['max_concurrent_executions'])

        async def execute_with_semaphore(request: ExecutionRequest) -> ExecutionResult:
            async with semaphore:
                return await self._execute_tool(request)

        tasks = [execute_with_semaphore(request) for request in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_result = ExecutionResult(
                    request_id=requests[i].request_id,
                    tool_name=requests[i].tool_name,
                    success=False,
                    error=str(result)
                )
                processed_results.append(error_result)
            else:
                processed_results.append(result)

        return processed_results

    async def _execute_tool(self, request: ExecutionRequest) -> ExecutionResult:
        """执行单个工具"""
        start_time = datetime.now()
        self.logger.info(f"🔧 执行工具: {request.tool_name} (ID: {request.request_id})")

        try:
            # 检查工具状态
            if self.tool_status.get(request.tool_name) != ToolStatus.AVAILABLE:
                raise Exception(f"工具 {request.tool_name} 不可用")

            # 模拟工具执行(实际实现中应该调用真实的工具)
            result = await self._simulate_tool_execution(request)

            execution_time = (datetime.now() - start_time).total_seconds()

            # 更新性能统计
            self._update_performance_stats(request.tool_name, True, execution_time)

            self.logger.info(f"✅ 工具执行完成: {request.tool_name} (耗时: {execution_time:.2f}s)")

            return ExecutionResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=True,
                result=result,
                execution_time=execution_time,
                start_time=start_time,
                end_time=datetime.now()
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)

            # 更新性能统计
            self._update_performance_stats(request.tool_name, False, execution_time, error_msg)

            self.logger.error(f"❌ 工具执行失败: {request.tool_name} - {error_msg}")

            # 重试机制
            if request.retry_count < request.max_retries and self.config['enable_retry']:
                self.logger.info(f"🔄 重试工具执行: {request.tool_name} (第{request.retry_count + 1}次)")
                request.retry_count += 1
                await asyncio.sleep(1.0 * request.retry_count)  # 指数退避
                return await self._execute_tool(request)

            return ExecutionResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=False,
                error=error_msg,
                execution_time=execution_time,
                start_time=start_time,
                end_time=datetime.now()
            )

    async def _simulate_tool_execution(self, request: ExecutionRequest) -> Any:
        """模拟工具执行(实际实现中应该调用真实的工具)"""
        tool_name = request.tool_name

        # 模拟执行时间
        execution_time = min(request.timeout, 2.0 + len(str(request.parameters)) * 0.1)
        await asyncio.sleep(execution_time)

        # 根据工具类型返回模拟结果
        if tool_name == 'search_engine':
            return {
                'results': [
                    {'title': f"搜索结果 {i+1}', 'url': f'https://example.com/{i+1}', 'snippet': '相关内容摘要"}
                    for i in range(5)
                ],
                'total_found': 42,
                'query': request.parameters.get('query', '')
            }

        elif tool_name == 'code_generator':
            language = request.parameters.get('language', 'python')
            specification = request.parameters.get('specification', '')
            return {
                'code': f"# {specification}\n\ndef generated_function():\n    pass\n",
                'language': language,
                'explanation': '根据要求生成的代码示例'
            }

        elif tool_name == 'data_analyzer':
            return {
                'analysis': {
                    'summary': '数据分析结果',
                    'insights': ['洞察1', '洞察2', '洞察3'],
                    'statistics': {'mean': 0.0, 'median': 0.0, 'std_dev': 0.0}
                },
                'visualization_url': 'https://example.com/chart.png'
            }

        elif tool_name == 'document_processor':
            operation = request.parameters.get('operation', 'extract')
            return {
                'operation': operation,
                'result': f"文档{operation}结果",
                'extracted_text': '从文档中提取的文本内容'
            }

        elif tool_name == 'system_manager':
            operation = request.parameters.get('operation', 'status')
            return {
                'operation': operation,
                'status': 'success',
                'system_info': {
                    'cpu_usage': 45.2,
                    'memory_usage': 62.8,
                    'disk_usage': 78.1
                }
            }

        return {'message': f"工具 {tool_name} 执行完成", 'parameters': request.parameters}

    def _update_performance_stats(self, tool_name: str, success: bool,
                                execution_time: float, error_msg: str = None):
        """更新性能统计"""
        self.performance_stats['total_executions'] += 1

        if success:
            self.performance_stats['successful_executions'] += 1
        else:
            self.performance_stats['failed_executions'] += 1
            if error_msg:
                error_type = error_msg.split(':')[0] if ':' in error_msg else 'unknown'
                self.performance_stats['error_types'][error_type] = \
                    self.performance_stats['error_types'].get(error_type, 0) + 1

        # 更新工具使用统计
        self.performance_stats['tool_usage_stats'][tool_name] = \
            self.performance_stats['tool_usage_stats'].get(tool_name, 0) + 1

        # 更新平均执行时间
        total = self.performance_stats['total_executions']
        current_avg = self.performance_stats['average_execution_time']
        new_avg = (current_avg * (total - 1) + execution_time) / total
        self.performance_stats['average_execution_time'] = new_avg

    async def _process_execution_queue(self):
        """处理执行队列"""
        while True:
            try:
                request = await self.execution_queue.get()
                task = asyncio.create_task(self._execute_tool(request))
                self.active_executions[request.request_id] = task

                # 任务完成后清理
                task.add_done_callback(lambda t: self.active_executions.pop(request.request_id, None))

            except Exception as e:
                self.logger.error(f"❌ 队列处理异常: {str(e)}")

    async def _health_check_loop(self):
        """健康检查循环"""
        while True:
            try:
                await self._perform_health_check()
                await asyncio.sleep(self.config['health_check_interval'])
            except Exception as e:
                self.logger.error(f"❌ 健康检查异常: {str(e)}")
                await asyncio.sleep(5.0)  # 短暂等待后重试

    async def _perform_health_check(self):
        """执行健康检查"""
        for tool_name in self.tools:
            try:
                # 简单的健康检查(实际实现中应该调用工具的健康检查接口)
                # 这里随机模拟健康状态
                import random
                is_healthy = random.random() > 0.1  # 90% 概率健康

                if is_healthy:
                    if self.tool_status[tool_name] != ToolStatus.AVAILABLE:
                        self.tool_status[tool_name] = ToolStatus.AVAILABLE
                        self.logger.info(f"✅ 工具恢复可用: {tool_name}")
                else:
                    self.tool_status[tool_name] = ToolStatus.ERROR
                    self.logger.warning(f"⚠️ 工具状态异常: {tool_name}")

            except Exception as e:
                self.tool_status[tool_name] = ToolStatus.ERROR
                self.logger.error(f"❌ 工具健康检查失败 {tool_name}: {str(e)}")

    async def auto_execute(self, text: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        自动执行:从文本到工具执行的完整流程

        Args:
            text: 用户输入文本
            context: 上下文信息

        Returns:
            dict[str, Any]: 执行结果
        """
        start_time = datetime.now()

        try:
            # 1. 意图识别
            intent = await recognize_user_intent(text, context)

            # 2. 工具执行
            execution_results = await self.execute_from_intent(intent, context)

            # 3. 结果整合
            integrated_result = await self._integrate_results(intent, execution_results)

            # 4. 生成响应
            response = await self._generate_response(text, intent, integrated_result)

            execution_time = (datetime.now() - start_time).total_seconds()

            return {
                'success': True,
                'intent': {
                    'type': intent.intent_type.value,
                    'confidence': intent.confidence,
                    'complexity': intent.complexity.value
                },
                'executions': [
                    {
                        'tool': result.tool_name,
                        'success': result.success,
                        'execution_time': result.execution_time,
                        'result': result.result if result.success else None,
                        'error': result.error if not result.success else None
                    }
                    for result in execution_results
                ],
                'response': response,
                'execution_time': execution_time,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"❌ 自动执行失败: {str(e)}")

            return {
                'success': False,
                'error': str(e),
                'execution_time': execution_time,
                'timestamp': datetime.now().isoformat()
            }

    async def _integrate_results(self, intent: IntentResult, execution_results: list[ExecutionResult]) -> dict[str, Any]:
        """整合执行结果"""
        integrated = {
            'successful_tools': [],
            'failed_tools': [],
            'combined_output': None,
            'insights': []
        }

        for result in execution_results:
            if result.success:
                integrated['successful_tools'].append(result.tool_name)

                # 特殊处理某些工具的结果整合
                if result.tool_name == 'search_engine' and result.result:
                    if not integrated['combined_output']:
                        integrated['combined_output'] = {'search_results': result.result.get('results', [])}
                    else:
                        integrated['combined_output']['search_results'].extend(
                            result.result.get('results', [])
                        )

                elif result.tool_name == 'data_analyzer' and result.result:
                    integrated['combined_output'] = result.result.get('analysis', {})

                elif result.tool_name == 'code_generator' and result.result:
                    integrated['combined_output'] = {
                        'generated_code': result.result.get('code', ''),
                        'explanation': result.result.get('explanation', '')
                    }

            else:
                integrated['failed_tools'].append({
                    'tool': result.tool_name,
                    'error': result.error
                })

        # 生成洞察
        if len(integrated['successful_tools']) > 1:
            integrated['insights'].append('多工具协作完成复杂任务')
        elif integrated['successful_tools']:
            integrated['insights'].append(f"使用 {integrated['successful_tools'][0]} 工具完成任务")

        return integrated

    async def _generate_response(self, text: str, intent: IntentResult, integrated_result: dict[str, Any]) -> str:
        """生成响应"""
        if not integrated_result['successful_tools']:
            return '抱歉,无法执行您的请求。请检查输入或稍后再试。'

        response_parts = []

        # 基于意图类型生成响应
        if intent.intent_type.value == 'information_query':
            response_parts.append('根据搜索结果,为您找到相关信息:')
            if integrated_result.get('combined_output', {}).get('search_results'):
                for i, result in enumerate(integrated_result['combined_output']['search_results'][:3]):
                    response_parts.append(f"\n{i+1}. {result.get('title', '')}: {result.get('snippet', '')}")

        elif intent.intent_type.value == 'code_generation':
            response_parts.append('已为您生成代码:')
            if integrated_result.get('combined_output', {}).get('generated_code'):
                response_parts.append("\n```python")
                response_parts.append(integrated_result['combined_output']['generated_code'])
                response_parts.append("\n```")
                if integrated_result['combined_output'].get('explanation'):
                    response_parts.append(f"\n说明: {integrated_result['combined_output']['explanation']}")

        elif intent.intent_type.value == 'data_analysis':
            response_parts.append('数据分析完成:')
            if integrated_result.get('combined_output'):
                analysis = integrated_result['combined_output']
                response_parts.append(f"\n关键洞察: {', '.join(analysis.get('insights', []))}")

        else:
            response_parts.append('任务执行完成。')
            if integrated_result['insights']:
                response_parts.extend(integrated_result['insights'])

        # 添加执行信息
        response_parts.append(f"\n\n使用了 {len(integrated_result['successful_tools'])} 个工具完成任务")
        if integrated_result['failed_tools']:
            response_parts.append(f",{len(integrated_result['failed_tools'])} 个工具执行失败")

        return ''.join(response_parts)

    def get_performance_report(self) -> dict[str, Any]:
        """获取性能报告"""
        total = self.performance_stats['total_executions']
        if total == 0:
            return {'message': '暂无执行统计数据'}

        success_rate = self.performance_stats['successful_executions'] / total * 100

        # 最常用的工具
        tool_usage = self.performance_stats['tool_usage_stats']
        most_used_tool = max(tool_usage.items(), key=lambda x: x[1]) if tool_usage else None

        return {
            'total_executions': total,
            'success_rate': f"{success_rate:.1f}%",
            'average_execution_time': f"{self.performance_stats['average_execution_time']:.2f}s",
            'most_used_tool': {
                'name': most_used_tool[0] if most_used_tool else None,
                'usage_count': most_used_tool[1] if most_used_tool else 0
            },
            'tool_usage_stats': tool_usage,
            'error_types': self.performance_stats['error_types'],
            'registered_tools': list(self.tools.keys()),
            'tool_status': {name: status.value for name, status in self.tool_status.items()}
        }

    async def shutdown(self):
        """关闭执行引擎"""
        self.logger.info('🛑 关闭工具执行引擎...')

        # 取消健康检查任务
        if self.health_check_task:
            self.health_check_task.cancel()

        # 等待所有活动执行完成
        if self.active_executions:
            self.logger.info(f"等待 {len(self.active_executions)} 个活动执行完成...")
            await asyncio.gather(*self.active_executions.values(), return_exceptions=True)

        self.logger.info('✅ 工具执行引擎已关闭')


# 创建全局工具执行引擎实例
tool_executor = ToolAutoExecutionEngine()

# 导出的便捷函数
async def auto_execute_request(text: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    """便捷函数:自动执行用户请求"""
    return await tool_executor.auto_execute(text, context)

async def initialize_tool_executor():
    """便捷函数:初始化工具执行引擎"""
    await tool_executor.initialize()

def get_tool_executor_performance() -> dict[str, Any]:
    """便捷函数:获取工具执行引擎性能报告"""
    return tool_executor.get_performance_report()