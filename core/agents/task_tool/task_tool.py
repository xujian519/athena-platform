from __future__ import annotations
"""
TaskTool - 任务工具主体

提供任务执行、模型选择和工具调用功能。
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from core.agents.fork_context_builder import ForkContext, ForkContextBuilder

if TYPE_CHECKING:
    from core.agents.subagent_registry import SubagentRegistry
from core.agents.task_tool.model_mapper import ModelMapper
from core.agents.task_tool.models import (
    TaskInput,
    TaskRecord,
    TaskStatus,
)
from core.agents.task_tool.tool_filter import ToolFilter
from core.task.task_store import TaskStore
from core.tools.base import ToolCapability, ToolCategory, ToolDefinition, ToolPriority


class TaskTool:
    """任务工具类

    负责任务的执行、模型选择和结果返回。
    """

    def __init__(
        self,
        task_store: TaskStore | None = None,
        model_mapper: ModelMapper | None = None,
        config: dict[str, Any] | None = None,
    ):
        """初始化TaskTool

        Args:
            task_store: 任务存储实例
            model_mapper: 模型映射器实例
            config: 配置字典
        """
        self.config = config or {}
        self.task_store = task_store or TaskStore(self.config)
        self.model_mapper = model_mapper or ModelMapper()

        # 延迟导入以避免循环依赖
        from core.agents.subagent_registry import SubagentRegistry

        self.subagent_registry = SubagentRegistry()
        self.tool_filter = ToolFilter(self.subagent_registry)
        self.fork_context_builder = ForkContextBuilder(
            base_system_prompt=self.config.get("base_system_prompt", "")
        )

    def to_tool_definition(self) -> ToolDefinition:
        """
        将TaskTool转换为ToolDefinition

        Returns:
            ToolDefinition对象,用于ToolManager注册
        """
        return ToolDefinition(
            tool_id="task-tool",
            name="Task Tool",
            description="执行AI任务，支持同步和后台执行，自动模型选择和工具过滤",
            category=ToolCategory.MCP_SERVICE,
            priority=ToolPriority.HIGH,
            capability=ToolCapability(
                input_types=["string", "dict"],
                output_types=["dict"],
                domains=["all"],
                task_types=["task_execution", "subagent_spawn", "parallel_execution"],
                features={
                    "supports_background": True,
                    "supports_tool_filtering": True,
                    "supports_model_selection": True,
                },
            ),
            implementation_type="function",
            implementation_ref="task_tool",
            required_params=["prompt"],
            optional_params=["tools", "model", "agent_type", "background"],
            handler=self._tool_handler,
            timeout=300.0,
            max_retries=3,
            tags={"task", "subagent", "ai", "background"},
            config=self.config,
        )

    def _tool_handler(self, **_kwargs  # noqa: ARG001) -> dict[str, Any]:
        """
        ToolDefinition的处理器函数

        Args:
            **_kwargs  # noqa: ARG001: 任务参数

        Returns:
            任务执行结果
        """
        prompt = kwargs.get("prompt", "")
        tools = kwargs.get("tools", [])
        model = kwargs.get("model")
        agent_type = kwargs.get("agent_type")
        background = kwargs.get("background", False)

        return self.execute(
            prompt=prompt,
            tools=tools,
            model=model,
            agent_type=agent_type,
            background=background,
        )

    def execute(
        self,
        prompt: str,
        tools: list[str],
        model: str | None = None,
        agent_type: str | None = None,
        background: bool = False,
        fork_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """执行任务

        Args:
            prompt: 任务提示词
            tools: 可用工具列表
            model: 模型名称
            agent_type: 代理类型
            background: 是否后台执行
            fork_context: Fork上下文信息

        Returns:
            任务执行结果字典
        """
        # 验证输入
        self._validate_input(prompt, tools)

        # 选择模型
        selected_model = self._select_model(model, agent_type)

        # 生成代理ID
        agent_id = self._generate_agent_id(agent_type)

        # 构建Fork上下文
        fork_ctx = self._build_fork_context(fork_context, agent_type, prompt)

        # 创建任务输入
        task_input = TaskInput(
            prompt=prompt,
            tools=tools,
            agent_type=agent_type,
            fork_context=fork_ctx,
        )

        # 创建任务记录
        task_record = TaskRecord(
            task_id=str(uuid.uuid4()),
            agent_id=agent_id,
            model=selected_model,
            status=TaskStatus.PENDING,
            input=task_input,
        )

        # 保存任务记录
        self.task_store.save_task(task_record)

        # 执行任务
        if background:
            return self._execute_background(task_record)
        else:
            return self._execute_sync(task_record)

    def _build_fork_context(
        self,
        context: dict[str, Any] | None,
        agent_type: str | None,
        prompt: str,
    ) -> ForkContext | None:
        """构建Fork上下文

        Args:
            context: 上下文信息
            agent_type: 代理类型
            prompt: 任务提示词

        Returns:
            ForkContext实例
        """
        if not context:
            return None

        # 从代理注册表获取系统提示词
        agent_config = self.subagent_registry.get_agent(agent_type)
        if agent_config:
            return self.fork_context_builder.build(
                prompt=prompt,
                context={"system_prompt": agent_config.system_prompt},
            )

        return None

    def _select_model(
        self,
        model: str | None,
        agent_type: str | None,
    ) -> str:
        """选择模型

        Args:
            model: 指定的模型名称
            agent_type: 代理类型

        Returns:
            选择的模型名称
        """
        # 如果指定了模型，直接使用
        if model:
            return self.model_mapper.map(model)

        # 根据代理类型选择模型
        if agent_type:
            agent_config = self.subagent_registry.get_agent(agent_type)
            if agent_config:
                return self.model_mapper.map(agent_config.default_model.value)

            # 后备到默认映射
            model_mapping = {
                "analysis": "sonnet",
                "search": "haiku",
                "legal": "opus",
            }
            selected = model_mapping.get(agent_type, "sonnet")
            return self.model_mapper.map(selected)

        # 默认使用sonnet
        return self.model_mapper.map("sonnet")

    def _generate_agent_id(self, agent_type: str | None = None) -> str:
        """生成代理ID

        Args:
            agent_type: 代理类型

        Returns:
            代理ID
        """
        prefix = agent_type or "default"
        return f"{prefix}-agent-{uuid.uuid4().hex[:8]}"

    def _validate_input(self, prompt: str, tools: list[str]) -> None:
        """验证输入

        Args:
            prompt: 任务提示词
            tools: 可用工具列表

        Raises:
            ValueError: 如果输入无效
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt不能为空")

        if not isinstance(tools, list):
            raise ValueError("Tools必须是列表")

    def _execute_sync(self, task_record: TaskRecord) -> dict[str, Any]:
        """同步执行任务

        Args:
            task_record: 任务记录

        Returns:
            任务执行结果
        """
        agent_type = task_record.input.agent_type if task_record.input else None
        if agent_type:
            agent_type_clean = agent_type.replace("-agent", "")
            agent_config = self.subagent_registry.get_agent(agent_type_clean)

            if agent_config:
                filtered_tools = self.tool_filter.filter_tools(
                    task_record.input.tools if task_record.input else [], agent_config
                )
                if task_record.input:
                    task_record.input.tools = filtered_tools

        # TODO: 实现同步执行逻辑
        task_record.status = TaskStatus.COMPLETED
        task_record.updated_at = datetime.utcnow().isoformat() + "F"
        self.task_store.save_task(task_record)

        return {
            "task_id": task_record.task_id,
            "status": task_record.status.value,
            "agent_id": task_record.agent_id,
            "model": task_record.model,
            "filtered_tools": task_record.input.tools if task_record.input else [],
        }

    def _execute_background(self, task_record: TaskRecord) -> dict[str, Any]:
        """后台执行任务

        Args:
            task_record: 任务记录

        Returns:
            任务执行结果
        """
        agent_type = task_record.input.agent_type if task_record.input else None
        if agent_type:
            agent_type_clean = agent_type.replace("-agent", "")
            agent_config = self.subagent_registry.get_agent(agent_type_clean)

            if agent_config:
                filtered_tools = self.tool_filter.filter_tools(
                    task_record.input.tools if task_record.input else [], agent_config
                )
                if task_record.input:
                    task_record.input.tools = filtered_tools

        # TODO: 实现后台执行逻辑
        return {
            "task_id": task_record.task_id,
            "status": "submitted",
            "agent_id": task_record.agent_id,
            "model": task_record.model,
            "filtered_tools": task_record.input.tools if task_record.input else [],
        }
