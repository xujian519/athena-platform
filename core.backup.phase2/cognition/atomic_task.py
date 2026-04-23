#!/usr/bin/env python3
from __future__ import annotations
"""
原子化任务分解系统 - Minitap式原子任务管理
Atomic Task Decomposition System - Minitap-Style Atomic Task Management

将复杂任务分解为原子级别的可执行单元，确保：
1. 每个任务是原子的（要么全部成功，要么全部失败）
2. 明确的输入契约（Input Contract）
3. 明确的输出契约（Output Contract）
4. 独立可验证（Verifiable）
5. 幂等性（Idempotent）

Author: Athena Team
Version: 1.0.0
Date: 2026-02-26
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from core.cognition.xiaonuo_planner_engine import ExecutionStep

logger = logging.getLogger(__name__)


# ========== 原子任务状态 ==========


class AtomicTaskStatus(Enum):
    """原子任务状态"""
    PENDING = "pending"
    READY = "ready"  # 输入契约满足，准备执行
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


# ========== 输入输出契约 ==========


@dataclass
class InputContract:
    """输入契约 - 定义任务执行的前置条件"""
    required_parameters: set[str] = field(default_factory=set)  # 必需参数
    optional_parameters: set[str] = field(default_factory=set)  # 可选参数
    parameter_types: dict[str, str] = field(default_factory=dict)  # 参数类型
    parameter_validation: dict[str, Callable] = field(default_factory=dict)  # 参数验证函数
    pre_conditions: list[str] = field(default_factory=list)  # 前置条件描述

    def validate(self, parameters: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        验证输入参数是否满足契约

        Args:
            parameters: 输入参数

        Returns:
            (is_valid, errors): 是否有效，错误列表
        """
        errors = []

        # 检查必需参数
        for param in self.required_parameters:
            if param not in parameters:
                errors.append(f"缺少必需参数: {param}")

        # 检查参数类型
        for param, expected_type in self.parameter_types.items():
            if param in parameters:
                value = parameters[param]
                if not self._check_type(value, expected_type):
                    errors.append(f"参数 {param} 类型错误: 期望 {expected_type}, 实际 {type(value).__name__}")

        # 执行自定义验证
        for param, validator in self.parameter_validation.items():
            if param in parameters:
                try:
                    if not validator(parameters[param]):
                        errors.append(f"参数 {param} 验证失败")
                except Exception as e:
                    errors.append(f"参数 {param} 验证异常: {e}")

        return len(errors) == 0, errors

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """检查类型"""
        type_map = {
            "str": str,
            "int": int,
            "float": (int, float),
            "bool": bool,
            "list": list,
            "dict": dict,
            "any": object,
        }

        expected = type_map.get(expected_type, object)
        return isinstance(value, expected)


@dataclass
class OutputContract:
    """输出契约 - 定义任务执行的结果规范"""
    required_fields: set[str] = field(default_factory=set)  # 必需输出字段
    optional_fields: set[str] = field(default_factory=set)  # 可选输出字段
    field_types: dict[str, str] = field(default_factory=dict)  # 字段类型
    output_format: str | None = None  # 输出格式 (json/xml/text)
    min_quality_score: float = 0.0  # 最低质量分数
    post_conditions: list[str] = field(default_factory=list)  # 后置条件描述

    def validate(self, output: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        验证输出是否满足契约

        Args:
            output: 输出数据

        Returns:
            (is_valid, errors): 是否有效，错误列表
        """
        errors = []

        # 检查必需字段
        for field_name in self.required_fields:
            if field_name not in output:
                errors.append(f"缺少必需输出字段: {field_name}")

        # 检查字段类型
        for field_name, expected_type in self.field_types.items():
            if field_name in output:
                value = output[field_name]
                if not self._check_type(value, expected_type):
                    errors.append(f"输出字段 {field_name} 类型错误: 期望 {expected_type}, 实际 {type(value).__name__}")

        return len(errors) == 0, errors

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """检查类型"""
        type_map = {
            "str": str,
            "int": int,
            "float": (int, float),
            "bool": bool,
            "list": list,
            "dict": dict,
            "any": object,
        }

        expected = type_map.get(expected_type, object)
        return isinstance(value, expected)


# ========== 原子任务 ==========


@dataclass
class AtomicTask:
    """
    原子任务 - 最小的不可分割的执行单元

    特性:
    1. 原子性: 要么全部成功，要么全部失败
    2. 独立性: 可以独立执行和验证
    3. 幂等性: 多次执行产生相同结果
    """
    id: str
    action: str  # 操作类型
    agent: str  # 执行智能体
    description: str  # 任务描述

    # 契约
    input_contract: InputContract
    output_contract: OutputContract

    # 执行参数
    parameters: dict[str, Any] = field(default_factory=dict)

    # 元数据
    timeout_ms: int = 30000  # 超时时间
    retry_count: int = 0  # 当前重试次数
    max_retries: int = 3  # 最大重试次数
    dependencies: list[str] = field(default_factory=list)  # 依赖的其他原子任务ID

    # 状态
    status: AtomicTaskStatus = AtomicTaskStatus.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: dict[str, Any] | None = None
    error: str | None = None

    def is_ready(self, completed_tasks: set[str]) -> bool:
        """检查任务是否准备好执行（所有依赖已完成）"""
        return all(dep in completed_tasks for dep in self.dependencies)

    def validate_input(self) -> tuple[bool, list[str]]:
        """验证输入参数"""
        return self.input_contract.validate(self.parameters)

    def validate_output(self, output: dict[str, Any]) -> tuple[bool, list[str]]:
        """验证输出结果"""
        return self.output_contract.validate(output)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "action": self.action,
            "agent": self.agent,
            "description": self.description,
            "parameters": self.parameters,
            "status": self.status.value,
            "dependencies": self.dependencies,
            "timeout_ms": self.timeout_ms,
        }


# ========== 原子任务分解器 ==========


class AtomicTaskDecomposer:
    """
    原子任务分解器

    将复杂的ExecutionStep分解为多个原子任务
    """

    def __init__(self):
        """初始化分解器"""
        # 注册的原子任务模板
        self._atomic_templates: dict[str, dict[str, Any]] = {
            "patent_search": {
                "input_contract": InputContract(
                    required_parameters={"query"},
                    optional_parameters={"limit", "database", "date_range"},
                    parameter_types={"query": "str", "limit": "int"},
                ),
                "output_contract": OutputContract(
                    required_fields={"results", "total_count"},
                    field_types={"results": "list", "total_count": "int"},
                ),
                "timeout_ms": 30000,
            },
            "patent_analyze": {
                "input_contract": InputContract(
                    required_parameters={"patent_id"},
                    optional_parameters={"aspects"},
                    parameter_types={"patent_id": "str", "aspects": "list"},
                ),
                "output_contract": OutputContract(
                    required_fields={"analysis", "patent_id"},
                    field_types={"analysis": "str", "patent_id": "str"},
                ),
                "timeout_ms": 60000,
            },
            "claim_draft": {
                "input_contract": InputContract(
                    required_parameters={"invention_content"},
                    optional_parameters={"claim_type", "technical_field"},
                    parameter_types={"invention_content": "str"},
                ),
                "output_contract": OutputContract(
                    required_fields={"claims", "claim_count"},
                    field_types={"claims": "str", "claim_count": "int"},
                ),
                "timeout_ms": 90000,
            },
            "data_extraction": {
                "input_contract": InputContract(
                    required_parameters={"source"},
                    optional_parameters={"format", "fields"},
                    parameter_types={"source": "str"},
                ),
                "output_contract": OutputContract(
                    required_fields={"data", "record_count"},
                    field_types={"data": "list", "record_count": "int"},
                ),
                "timeout_ms": 45000,
            },
        }

    def decompose_step(
        self,
        step: ExecutionStep,
        parent_task_id: str | None = None,
    ) -> list[AtomicTask]:
        """
        将ExecutionStep分解为原子任务

        Args:
            step: 执行步骤
            parent_task_id: 父任务ID

        Returns:
            List[AtomicTask]: 原子任务列表
        """
        action = step.action
        template = self._atomic_templates.get(action)

        if not template:
            # 没有模板，创建通用原子任务
            return [self._create_generic_atomic_task(step, parent_task_id)]

        # 使用模板创建原子任务
        return [self._create_templated_atomic_task(step, template, parent_task_id)]

    def _create_generic_atomic_task(
        self,
        step: ExecutionStep,
        parent_task_id: str | None = None,
    ) -> AtomicTask:
        """创建通用原子任务"""
        task_id = f"{parent_task_id or 'task'}_{step.id}" if parent_task_id else step.id

        return AtomicTask(
            id=task_id,
            action=step.action,
            agent=step.agent,
            description=step.description,
            input_contract=InputContract(
                required_parameters=set(step.parameters.keys()) if step.parameters else set(),
            ),
            output_contract=OutputContract(),
            parameters=step.parameters or {},
            dependencies=step.dependencies or [],
            timeout_ms=30000,
        )

    def _create_templated_atomic_task(
        self,
        step: ExecutionStep,
        template: dict[str, Any],
        parent_task_id: str | None = None,
    ) -> AtomicTask:
        """创建基于模板的原子任务"""
        task_id = f"{parent_task_id or 'task'}_{step.id}" if parent_task_id else step.id

        return AtomicTask(
            id=task_id,
            action=step.action,
            agent=step.agent,
            description=step.description,
            input_contract=template["input_contract"],
            output_contract=template["output_contract"],
            parameters=step.parameters or {},
            dependencies=step.dependencies or [],
            timeout_ms=template.get("timeout_ms", 30000),
        )

    def decompose_complex_step(
        self,
        step: ExecutionStep,
        parent_task_id: str | None = None,
    ) -> list[AtomicTask]:
        """
        分解复杂步骤为多个原子任务

        某些复杂步骤需要分解为多个原子任务才能保证原子性

        Args:
            step: 执行步骤
            parent_task_id: 父任务ID

        Returns:
            List[AtomicTask]: 原子任务列表
        """
        atomic_tasks = []

        # 根据action类型进行智能分解
        if step.action == "patent_search_and_analyze":
            # 复合操作：搜索 + 分析
            # 任务1: 搜索
            search_task = AtomicTask(
                id=f"{step.id}_search",
                action="patent_search",
                agent=step.agent,
                description=f"{step.description} - 搜索",
                input_contract=self._atomic_templates["patent_search"]["input_contract"],
                output_contract=self._atomic_templates["patent_search"]["output_contract"],
                parameters=step.parameters or {},
                timeout_ms=30000,
            )
            atomic_tasks.append(search_task)

            # 任务2: 分析（依赖搜索结果）
            analyze_task = AtomicTask(
                id=f"{step.id}_analyze",
                action="patent_analyze",
                agent=step.agent,
                description=f"{step.description} - 分析",
                input_contract=self._atomic_templates["patent_analyze"]["input_contract"],
                output_contract=self._atomic_templates["patent_analyze"]["output_contract"],
                parameters={"patent_id": "from_search"},  # 从搜索结果获取
                dependencies=[search_task.id],
                timeout_ms=60000,
            )
            atomic_tasks.append(analyze_task)

        else:
            # 简单步骤，直接创建原子任务
            atomic_tasks = self.decompose_step(step, parent_task_id)

        return atomic_tasks


# ========== 原子任务执行器 ==========


class AtomicTaskExecutor:
    """
    原子任务执行器

    执行单个原子任务，保证原子性和幂等性
    """

    def __init__(self):
        """初始化执行器"""
        from core.agents.base import AgentRegistry

        self.agent_registry = AgentRegistry

    async def execute(
        self,
        task: AtomicTask,
        context: dict[str, Any] | None = None,
    ) -> AtomicTask:
        """
        执行原子任务

        Args:
            task: 原子任务
            context: 执行上下文（包含前置任务的输出）

        Returns:
            AtomicTask: 执行后的任务（包含结果）
        """
        logger.info(f"⚛️ 执行原子任务: {task.id}")
        logger.info(f"   操作: {task.action}")
        logger.info(f"   智能体: {task.agent}")

        task.status = AtomicTaskStatus.RUNNING
        task.started_at = datetime.now()

        try:
            # 验证输入契约
            is_valid, errors = task.validate_input()
            if not is_valid:
                raise ValueError(f"输入契约验证失败: {', '.join(errors)}")

            # 解析参数（可能引用上下文）
            resolved_params = self._resolve_parameters(task.parameters, context)

            # 获取Agent
            agent = self.agent_registry.get(task.agent)
            if not agent:
                raise ValueError(f"智能体 {task.agent} 不存在")

            # 创建请求
            from core.agents.base import AgentRequest

            request = AgentRequest(
                request_id=task.id,
                action=task.action,
                parameters=resolved_params,
            )

            # 执行（带超时）
            response = await asyncio.wait_for(
                agent.safe_process(request),
                timeout=task.timeout_ms / 1000,
            )

            if not response.success:
                raise Exception(response.error or "执行失败")

            # 验证输出契约
            is_valid, errors = task.validate_output(response.data)
            if not is_valid:
                raise ValueError(f"输出契约验证失败: {', '.join(errors)}")

            # 成功
            task.status = AtomicTaskStatus.COMPLETED
            task.result = response.data
            task.completed_at = datetime.now()

            logger.info(f"   ✅ 原子任务完成: {task.id}")

        except asyncio.TimeoutError:
            task.status = AtomicTaskStatus.FAILED
            task.error = f"执行超时 ({task.timeout_ms}ms)"
            task.completed_at = datetime.now()
            logger.error(f"   ❌ 原子任务超时: {task.id}")

        except Exception as e:
            task.status = AtomicTaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()
            logger.error(f"   ❌ 原子任务失败: {task.id} - {e}")

        return task

    def _resolve_parameters(
        self,
        parameters: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        解析参数（处理引用和动态值）

        Args:
            parameters: 原始参数
            context: 上下文（前置任务的输出）

        Returns:
            解析后的参数
        """
        if not context:
            return parameters

        resolved = {}
        for key, value in parameters.items():
            if isinstance(value, str) and value.startswith("from_"):
                # 引用上下文中的值
                ref_key = value.replace("from_", "")
                if ref_key in context:
                    resolved[key] = context[ref_key]
                else:
                    resolved[key] = value  # 保持原值
            else:
                resolved[key] = value

        return resolved


# ========== 导出 ==========


__all__ = [
    "AtomicTaskStatus",
    "InputContract",
    "OutputContract",
    "AtomicTask",
    "AtomicTaskDecomposer",
    "AtomicTaskExecutor",
]
