
"""
TaskTool-ToolManager集成适配器

提供TaskTool与ToolManager系统的无缝集成。
"""

from typing import Any, Optional

from core.framework.agents.task_tool.task_tool import TaskTool
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
        task_tool: Optional[TaskTool ] = None,
        tool_manager: Optional[ToolManager ] = None,
        registry: Optional[ToolRegistry ] = None,
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

    def register(self) -> str:
        """将TaskTool注册到ToolManager系统

        Returns:
            是否注册成功
        """
        tool_definition = self.task_tool.to_tool_definition()
        self.registry.register(tool_definition)

        task_tool_group = self._create_task_tool_group()

        self.tool_manager.register_group(task_tool_group)

        return True

    def _create_task_tool_group(self) -> str:
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
            activation_rules=[]

                ActivationRule(
                    rule_type=GroupActivationRule.KEYWORD,
                    keywords=[]

                        "任务",
                        "task",
                        "执行",
                        "execute",
                        "子代理",
                        "subagent",
                        "并行",
                        "parallel",
                    ,
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
            ,
        )

    async def execute_task(
        self,
        prompt: str,
        tools: Optional[list[str],]

        model: Optional[str] = None,
        agent_type: Optional[str] = None,
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
        # 假设 task_tool.execute 是异步的，或者如果它是同步的，我们在内部将其适配为异步
        # 这里将其改造为 async def 并使用 await
        if hasattr(self.task_tool.execute, '__await__') or (hasattr(self.task_tool, 'execute_async') and callable(self.task_tool.execute_async)):
            # 如果 task_tool 有 execute_async 或 execute 本身是协程
            execute_func = getattr(self.task_tool, 'execute_async', self.task_tool.execute)
            return await execute_func(
                prompt=prompt,
                tools=tools,
                model=model,
                agent_type=agent_type,
                background=background,
            )
        else:
            # 如果 task_tool.execute 仍然是完全同步的阻塞函数，可以通过 asyncio.to_thread 进行异步封装
            import asyncio
            import functools
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                None,
                functools.partial(
                    self.task_tool.execute,
                    prompt=prompt,
                    tools=tools,
                    model=model,
                    agent_type=agent_type,
                    background=background,
                )
            )

