"""
Tool Agent - 使用工具系统的Agent示例
====================================

这是一个使用工具系统的Agent示例，展示如何在Agent中集成和使用工具。
支持动态工具调用、工具链组合等高级功能。

功能：使用工具系统执行各种任务

作者: Athena平台团队
版本: 1.0.0

依赖:
- core.tools.unified_registry
"""

from typing import Any, Dict, List, Optional
import logging
from datetime import datetime

from core.agents.xiaona.base_component import (
    BaseXiaonaComponent,
    AgentCapability,
    AgentExecutionContext,
    AgentExecutionResult,
    AgentStatus,
)

logger = logging.getLogger(__name__)


class ToolAgent(BaseXiaonaComponent):
    """
    工具使用Agent

    展示如何在Agent中使用工具系统。

    Attributes:
        tool_registry: 工具注册表
        available_tools: 可用工具列表

    Examples:
        >>> agent = ToolAgent(agent_id="tool_001")
        >>> result = await agent.execute(context)
    """

    __version__ = "1.0.0"
    __category__ = "general"

    def _initialize(self) -> None:
        """初始化Agent"""
        # 注册能力
        self._register_capabilities([
            AgentCapability(
                name="use_tool",
                description="调用指定工具",
                input_types=["工具名称", "参数"],
                output_types=["工具执行结果"],
                estimated_time=5.0,
            ),
            AgentCapability(
                name="list_tools",
                description="列出可用工具",
                input_types=[],
                output_types=["工具列表"],
                estimated_time=1.0,
            ),
            AgentCapability(
                name="tool_chain",
                description="执行工具链",
                input_types=["工具链配置"],
                output_types=["执行结果"],
                estimated_time=10.0,
            ),
        ])

        # 初始化工具注册表
        try:
            from core.tools.unified_registry import get_unified_registry
            self.tool_registry = get_unified_registry()
            self.tools_available = True
        except ImportError:
            self.tool_registry = None
            self.tools_available = False
            logger.warning("工具注册表不可用")

        # 初始化工具列表
        self.available_tools: List[str] = []
        if self.tools_available:
            self._refresh_tools()

        logger.info(f"ToolAgent初始化完成: {self.agent_id}, 工具可用: {self.tools_available}")

    def _refresh_tools(self) -> None:
        """刷新可用工具列表"""
        if self.tool_registry:
            all_tools = self.tool_registry.list_tools()
            self.available_tools = [tool.name for tool in all_tools]
            logger.info(f"加载了 {len(self.available_tools)} 个工具")

    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是ToolAgent，一个工具使用助手。

核心能力：
- use_tool: 调用指定工具执行任务
- list_tools: 列出所有可用工具
- tool_chain: 执行一系列工具（工具链）

工作原则：
- 根据任务选择合适的工具
- 正确传递工具参数
- 处理工具执行错误
- 记录工具执行日志

输出格式：
结构化的工具执行结果
"""

    async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
        """执行任务"""
        start_time = datetime.now()

        try:
            # 获取操作类型
            operation = context.input_data.get("operation", "use_tool")

            if operation == "use_tool":
                result = await self._use_tool(context)
            elif operation == "list_tools":
                result = self._list_tools()
            elif operation == "tool_chain":
                result = await self._tool_chain(context)
            else:
                raise ValueError(f"未知的操作类型: {operation}")

            execution_time = (datetime.now() - start_time).total_seconds()

            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.COMPLETED,
                output_data=result,
                execution_time=execution_time,
                metadata={
                    "operation": operation,
                },
            )

        except Exception as e:
            logger.exception(f"任务执行失败: {context.task_id}")
            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.ERROR,
                error_message=str(e),
                execution_time=(datetime.now() - start_time).total_seconds(),
            )

    async def _use_tool(self, context: AgentExecutionContext) -> Dict[str, Any]:
        """使用工具"""
        if not self.tools_available or not self.tool_registry:
            return {
                "operation": "use_tool",
                "error": "工具系统不可用",
            }

        tool_name = context.input_data.get("tool_name")
        tool_params = context.input_data.get("params", {})

        if not tool_name:
            raise ValueError("缺少tool_name参数")

        # 检查工具是否存在
        if not self.tool_registry.has(tool_name):
            raise ValueError(f"工具不存在: {tool_name}")

        # 获取工具
        tool = self.tool_registry.get(tool_name)

        if not tool:
            raise ValueError(f"无法获取工具: {tool_name}")

        # 调用工具
        logger.info(f"调用工具: {tool_name}, 参数: {tool_params}")
        tool_result = await tool.function(**tool_params)

        return {
            "operation": "use_tool",
            "tool_name": tool_name,
            "params": tool_params,
            "result": tool_result,
        }

    def _list_tools(self) -> Dict[str, Any]:
        """列出工具"""
        self._refresh_tools()

        tool_info = []
        if self.tool_registry:
            for tool_name in self.available_tools:
                tool = self.tool_registry.get(tool_name)
                if tool:
                    tool_info.append({
                        "name": tool.name,
                        "category": tool.category,
                        "description": tool.description,
                    })

        return {
            "operation": "list_tools",
            "tools": tool_info,
            "total": len(tool_info),
        }

    async def _tool_chain(self, context: AgentExecutionContext) -> Dict[str, Any]:
        """执行工具链"""
        if not self.tools_available:
            return {
                "operation": "tool_chain",
                "error": "工具系统不可用",
            }

        chain_config = context.input_data.get("chain", [])

        if not isinstance(chain_config, list):
            raise ValueError("chain参数必须是列表")

        results = []
        for step in chain_config:
            tool_name = step.get("tool_name")
            tool_params = step.get("params", {})
            output_key = step.get("output_key", "result")

            # 创建上下文
            step_context = AgentExecutionContext(
                session_id=context.session_id,
                task_id=f"{context.task_id}_step_{len(results)}",
                input_data={
                    "operation": "use_tool",
                    "tool_name": tool_name,
                    "params": tool_params,
                },
                config=context.config,
                metadata=context.metadata,
            )

            # 执行
            step_result = await self._use_tool(step_context)
            results.append({
                "step": len(results) + 1,
                "tool_name": tool_name,
                "output_key": output_key,
                "result": step_result,
            })

            # 将结果传递给下一步
            if step_result.get("result") is not None:
                # 更新后续步骤的参数
                for future_step in chain_config[len(results):]:
                    for key, value in future_step.get("params", {}).items():
                        if f"${{{output_key}}}" in str(value):
                            future_step["params"][key] = str(value).replace(
                                f"${{{output_key}}}",
                                str(step_result["result"])
                            )

        return {
            "operation": "tool_chain",
            "steps_completed": len(results),
            "results": results,
        }

    def has_tool(self, tool_name: str) -> bool:
        """检查工具是否存在"""
        return tool_name in self.available_tools

    def get_tool_count(self) -> int:
        """获取工具数量"""
        return len(self.available_tools)


# 便捷函数
def create_tool_agent(agent_id: str = "tool_001") -> ToolAgent:
    """创建ToolAgent实例"""
    return ToolAgent(agent_id=agent_id)


# 测试入口
async def main():
    """测试入口"""
    import asyncio

    # 配置日志
    logging.basicConfig(level=logging.INFO)

    # 创建Agent
    agent = ToolAgent(agent_id="tool_test")

    print("=== Tool Agent测试 ===")

    # 测试列出工具
    print("\n=== 列出工具 ===")
    context = AgentExecutionContext(
        session_id="SESSION_001",
        task_id="TASK_LIST",
        input_data={"operation": "list_tools"},
        config={},
        metadata={},
    )

    result = await agent.execute(context)
    print(f"可用工具数: {result.output_data['total']}")
    for tool in result.output_data['tools'][:5]:  # 只显示前5个
        print(f"  - {tool['name']}: {tool['description']}")

    # 测试使用工具（如果有工具）
    if agent.get_tool_count() > 0:
        print("\n=== 使用工具 ===")
        first_tool = agent.available_tools[0]
        context = AgentExecutionContext(
            session_id="SESSION_001",
            task_id="TASK_USE",
            input_data={
                "operation": "use_tool",
                "tool_name": first_tool,
                "params": {},
            },
            config={},
            metadata={},
        )

        result = await agent.execute(context)
        print(f"工具: {result.output_data['tool_name']}")
        print(f"结果: {result.output_data.get('result', 'N/A')}")


if __name__ == "__main__":
    asyncio.run(main())
