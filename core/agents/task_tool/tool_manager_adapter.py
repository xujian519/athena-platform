from __future__ import annotations
"""
TaskTool-ToolManager集成适配器

提供TaskTool与ToolManager系统的无缝集成。
"""

from typing import Any

from core.agents.task_tool.task_tool import TaskTool
from core.tools.base import ToolCategory, ToolRegistry, get_global_registry
from core.tools.tool_group import ActivationRule, GroupActivationRule, ToolGroupDef
from core.tools.tool_manager import ToolManager


class TaskToolAdapter:
    """TaskTool与ToolManager的集成适配器

    负责将TaskTool注册到ToolManager系统，
    并创建相应的工具组。
    """

    def __init__(
        self,
        task_tool: TaskTool | None = None,
        tool_manager: ToolManager | None = None,
        registry: ToolRegistry | None = None,
    ):
        """初始化适配器

        Args:
            task_tool: TaskTool实例
            tool_manager: ToolManager实例
            registry: 工具注册中心
        """
        self.task_tool = task_tool or TaskTool()
        self.tool_manager = tool_manager or ToolManager(registry)
        self.registry = registry or get_global_registry()

    def register(self) -> bool:
        """将TaskTool注册到ToolManager系统

        Returns:
            是否注册成功
        """
        tool_definition = self.task_tool.to_tool_definition()
        self.registry.register(tool_definition)

        task_tool_group = self._create_task_tool_group()

        self.tool_manager.register_group(task_tool_group)

        return True

    def _create_task_tool_group(self) -> ToolGroupDef:
        """创建TaskTool工具组定义

        Returns:
            ToolGroupDef对象
        """
        return ToolGroupDef(
            name="task-tools",
            display_name="任务工具组",
            description="AI任务执行工具，支持子代理调用和并行执行",
            categories=[ToolCategory.MCP_SERVICE],
            tools=["task-tool"],
            activation_rules=[
                ActivationRule(
                    rule_type=GroupActivationRule.KEYWORD,
                    keywords=[
                        "任务",
                        "task",
                        "执行",
                        "execute",
                        "子代理",
                        "subagent",
                        "并行",
                        "parallel",
                    ],
                    priority=10,
                ),
                ActivationRule(
                    rule_type=GroupActivationRule.TASK_TYPE,
                    task_types=["task_execution", "subagent_spawn"],
                    priority=9,
                ),
                ActivationRule(
                    rule_type=GroupActivationRule.DOMAIN,
                    domains=["all"],
                    priority=5,
                ),
            ],
        )

    def execute_task(
        self,
        prompt: str,
        tools: list[str],
        model: str | None = None,
        agent_type: str | None = None,
        background: bool = False,
    ) -> dict[str, Any]:
        """执行任务

        Args:
            prompt: 任务提示词
            tools: 可用工具列表
            model: 模型名称
            agent_type: 代理类型
            background: 是否后台执行

        Returns:
            任务执行结果
        """
        return self.task_tool.execute(
            prompt=prompt,
            tools=tools,
            model=model,
            agent_type=agent_type,
            background=background,
        )
