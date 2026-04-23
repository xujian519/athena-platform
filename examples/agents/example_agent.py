"""
示例Agent - 演示如何实现统一Agent接口

这是一个完整的示例，展示如何创建符合统一接口标准的Agent。
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

from core.framework.agents.xiaona.base_component import (
    AgentCapability,
    AgentExecutionContext,
    AgentExecutionResult,
    AgentStatus,
    BaseXiaonaComponent,
)

logger = logging.getLogger(__name__)


class ExampleAgent(BaseXiaonaComponent):
    """
    示例Agent

    演示如何正确实现统一Agent接口。
    """

    def _initialize(self) -> None:
        """
        Agent初始化钩子

        在此方法中：
        1. 注册能力
        2. 初始化依赖
        3. 加载配置
        """
        # 注册能力
        self._register_capabilities([
            AgentCapability(
                name="example_capability",
                description="这是一个示例能力",
                input_types=["文本输入"],
                output_types=["文本输出"],
                estimated_time=5.0,
            ),
            AgentCapability(
                name="another_capability",
                description="这是另一个示例能力",
                input_types=["数字输入"],
                output_types=["数字输出"],
                estimated_time=3.0,
            ),
        ])

        # 初始化配置
        self.max_retries = self.config.get("max_retries", 3)
        self.timeout = self.config.get("timeout", 30.0)

        self.logger.info(
            f"示例Agent初始化完成: {self.agent_id}, "
            f"能力数: {len(self.get_capabilities())}"
        )

    def get_system_prompt(self) -> str:
        """
        获取系统提示词

        Returns:
            系统提示词字符串
        """
        return """你是一个示例Agent，用于演示如何实现统一Agent接口。

你的能力：
1. 处理文本输入
2. 处理数字输入

工作原则：
- 始终返回结构化的结果
- 正确处理错误情况
- 记录详细的日志
"""

    async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
        """
        执行Agent任务

        Args:
            context: 执行上下文

        Returns:
            执行结果
        """
        start_time = datetime.now()

        try:
            self.logger.info(f"开始执行任务: {context.task_id}")

            # 验证输入
            if not self.validate_input(context):
                return AgentExecutionResult(
                    agent_id=self.agent_id,
                    status=AgentStatus.ERROR,
                    output_data=None,
                    error_message="输入验证失败",
                )

            # 获取输入数据
            user_input = context.input_data.get("user_input", "")
            operation = context.input_data.get("operation", "example_capability")

            # 根据操作类型执行不同的逻辑
            if operation == "example_capability":
                result = await self._execute_example_capability(user_input, context)
            elif operation == "another_capability":
                result = await self._execute_another_capability(user_input, context)
            else:
                raise ValueError(f"未知的操作类型: {operation}")

            # 返回成功结果
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.COMPLETED,
                output_data=result,
                execution_time=execution_time,
                metadata={
                    "operation": operation,
                    "input_length": len(user_input),
                },
            )

        except Exception as e:
            # 错误处理
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            self.logger.exception(f"任务执行失败: {context.task_id}")

            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.ERROR,
                output_data=None,
                error_message=str(e),
                execution_time=execution_time,
                metadata={
                    "error_type": type(e).__name__,
                },
            )

    async def _execute_example_capability(
        self,
        user_input: str,
        context: AgentExecutionContext
    ) -> dict[str, Any]:
        """
        执行示例能力

        Args:
            user_input: 用户输入
            context: 执行上下文

        Returns:
            结果数据
        """
        self.logger.info(f"执行示例能力，输入: {user_input[:50]}...")

        # 模拟异步处理
        await asyncio.sleep(1)

        # 处理输入
        result = {
            "processed_input": user_input.upper(),
            "input_length": len(user_input),
            "word_count": len(user_input.split()),
            "timestamp": datetime.now().isoformat(),
        }

        self.logger.info(f"示例能力执行完成，处理了 {result['word_count']} 个词")

        return result

    async def _execute_another_capability(
        self,
        user_input: str,
        context: AgentExecutionContext
    ) -> dict[str, Any]:
        """
        执行另一个能力

        Args:
            user_input: 用户输入
            context: 执行上下文

        Returns:
            结果数据
        """
        self.logger.info(f"执行另一个能力，输入: {user_input}")

        # 模拟异步处理
        await asyncio.sleep(0.5)

        # 尝试将输入转换为数字
        try:
            number = float(user_input)
        except ValueError:
            raise ValueError(f"无法将输入转换为数字: {user_input}")

        # 处理数字
        result = {
            "input_number": number,
            "square": number ** 2,
            "cube": number ** 3,
            "timestamp": datetime.now().isoformat(),
        }

        self.logger.info(f"另一个能力执行完成，处理了数字 {number}")

        return result


# 使用示例
async def main():
    """演示如何使用ExampleAgent"""
    from core.framework.agents.xiaona.base_component import AgentExecutionContext

    # 创建Agent
    agent = ExampleAgent(
        agent_id="example_agent_001",
        config={
            "max_retries": 3,
            "timeout": 30.0,
        },
    )

    # 查看Agent信息
    info = agent.get_info()
    print(f"Agent信息: {info}")

    # 创建执行上下文
    context = AgentExecutionContext(
        session_id="SESSION_001",
        task_id="TASK_001",
        input_data={
            "user_input": "Hello, World!",
            "operation": "example_capability",
        },
        config={
            "timeout": 30.0,
        },
        metadata={
            "priority": "high",
        },
    )

    # 执行任务
    result = await agent._execute_with_monitoring(context)

    # 查看结果
    print(f"执行状态: {result.status}")
    print(f"执行时间: {result.execution_time:.2f}秒")
    print(f"输出数据: {result.output_data}")

    if result.status == AgentStatus.ERROR:
        print(f"错误信息: {result.error_message}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
