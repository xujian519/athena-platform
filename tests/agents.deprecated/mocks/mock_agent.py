"""
Mock Agent - 用于测试的模拟Agent

提供可配置的行为，用于测试各种场景。
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from core.agents.xiaona.base_component import (
    BaseXiaonaComponent,
    AgentCapability,
    AgentExecutionContext,
    AgentExecutionResult,
    AgentStatus,
)


class MockAgent(BaseXiaonaComponent):
    """
    Mock Agent

    用于测试的模拟Agent，支持可配置的行为。
    """

    def __init__(
        self,
        agent_id: str,
        config: Optional[Dict[str, Any]] = None,
        mock_behavior: Optional[Dict[str, Any]] = None
    ):
        """
        初始化Mock Agent

        Args:
            agent_id: Agent ID
            config: 配置参数
            mock_behavior: 模拟行为配置
                - execute_delay: 执行延迟（秒）
                - execute_result: 预设的执行结果
                - execute_error: 预设的执行错误
                - should_fail: 是否执行失败
        """
        self.mock_behavior = mock_behavior or {}
        super().__init__(agent_id, config)

    def _initialize(self) -> None:
        """初始化Mock Agent"""
        # 注册默认能力
        self._register_capabilities([
            AgentCapability(
                name="mock_capability",
                description="Mock能力",
                input_types=["任意输入"],
                output_types=["任意输出"],
                estimated_time=1.0,
            ),
        ])

        # 从配置中注册额外能力
        extra_capabilities = self.config.get("capabilities", [])
        if extra_capabilities:
            self._register_capabilities(extra_capabilities)

        self.logger.info(f"Mock Agent初始化完成: {self.agent_id}")

    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return self.config.get(
            "system_prompt",
            "你是一个Mock Agent，用于测试。"
        )

    async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
        """
        执行任务

        Args:
            context: 执行上下文

        Returns:
            执行结果
        """
        start_time = datetime.now()

        try:
            # 模拟执行延迟
            delay = self.mock_behavior.get("execute_delay", 0)
            if delay > 0:
                import asyncio
                await asyncio.sleep(delay)

            # 检查是否应该失败
            should_fail = self.mock_behavior.get("should_fail", False)
            if should_fail:
                error_message = self.mock_behavior.get(
                    "execute_error",
                    "Mock执行失败"
                )
                raise Exception(error_message)

            # 返回预设的结果
            preset_result = self.mock_behavior.get("execute_result")
            if preset_result is not None:
                result = preset_result
            else:
                # 默认结果
                result = {
                    "mock_output": "Mock结果",
                    "input_received": context.input_data,
                    "timestamp": datetime.now().isoformat(),
                }

            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.COMPLETED,
                output_data=result,
                execution_time=execution_time,
                metadata={
                    "mock": True,
                    "delay": delay,
                },
            )

        except Exception as e:
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            self.logger.exception(f"Mock Agent执行失败: {context.task_id}")

            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.ERROR,
                output_data=None,
                error_message=str(e),
                execution_time=execution_time,
                metadata={
                    "mock": True,
                    "error": True,
                },
            )


class ConfigurableMockAgent(MockAgent):
    """
    可配置的Mock Agent

    支持链式配置，方便测试。
    """

    def __init__(self, agent_id: str = "configurable_mock_agent"):
        super().__init__(agent_id)
        self.behavior_config = {}

    def with_capability(
        self,
        name: str,
        description: str = "",
        estimated_time: float = 1.0
    ):
        """
        添加能力

        Args:
            name: 能力名称
            description: 能力描述
            estimated_time: 预估时间

        Returns:
            self（支持链式调用）
        """
        capability = AgentCapability(
            name=name,
            description=description or f"{name}能力",
            input_types=["输入"],
            output_types=["输出"],
            estimated_time=estimated_time,
        )

        # 追加能力而不是替换
        current_capabilities = self.get_capabilities()
        self._register_capabilities(current_capabilities + [capability])
        return self

    def with_delay(self, delay: float):
        """
        设置执行延迟

        Args:
            delay: 延迟时间（秒）

        Returns:
            self（支持链式调用）
        """
        self.mock_behavior["execute_delay"] = delay
        return self

    def with_result(self, result: Any):
        """
        设置执行结果

        Args:
            result: 执行结果

        Returns:
            self（支持链式调用）
        """
        self.mock_behavior["execute_result"] = result
        return self

    def with_error(self, error_message: str):
        """
        设置执行错误

        Args:
            error_message: 错误消息

        Returns:
            self（支持链式调用）
        """
        self.mock_behavior["should_fail"] = True
        self.mock_behavior["execute_error"] = error_message
        return self


# ==================== 测试工具函数 ====================

def create_success_mock(
    agent_id: str = "success_mock",
    result: Optional[Dict[str, Any]] = None
) -> MockAgent:
    """
    创建一个总是成功的Mock Agent

    Args:
        agent_id: Agent ID
        result: 预设的执行结果

    Returns:
        Mock Agent实例
    """
    return MockAgent(
        agent_id=agent_id,
        mock_behavior={
            "execute_result": result or {"status": "success"},
            "should_fail": False,
        }
    )


def create_failure_mock(
    agent_id: str = "failure_mock",
    error_message: str = "Mock执行失败"
) -> MockAgent:
    """
    创建一个总是失败的Mock Agent

    Args:
        agent_id: Agent ID
        error_message: 错误消息

    Returns:
        Mock Agent实例
    """
    return MockAgent(
        agent_id=agent_id,
        mock_behavior={
            "should_fail": True,
            "execute_error": error_message,
        }
    )


def create_delayed_mock(
    agent_id: str = "delayed_mock",
    delay: float = 1.0
) -> MockAgent:
    """
    创建一个有延迟的Mock Agent

    Args:
        agent_id: Agent ID
        delay: 延迟时间（秒）

    Returns:
        Mock Agent实例
    """
    return MockAgent(
        agent_id=agent_id,
        mock_behavior={
            "execute_delay": delay,
            "should_fail": False,
        }
    )


# ==================== 使用示例 ====================

async def example_usage():
    """演示如何使用Mock Agent"""

    # 1. 使用默认Mock Agent
    print("=== 示例1: 默认Mock Agent ===")
    mock1 = MockAgent(agent_id="mock1")
    from core.agents.xiaona.base_component import AgentExecutionContext
    context1 = AgentExecutionContext(
        session_id="SESSION_001",
        task_id="TASK_001",
        input_data={"test": "data"},
        config={},
        metadata={},
    )
    result1 = await mock1.execute(context1)
    print(f"结果: {result1.status}")
    print(f"输出: {result1.output_data}")

    # 2. 使用预设结果的Mock Agent
    print("\n=== 示例2: 预设结果的Mock Agent ===")
    mock2 = create_success_mock(
        agent_id="mock2",
        result={"custom": "result"}
    )
    result2 = await mock2.execute(context1)
    print(f"结果: {result2.status}")
    print(f"输出: {result2.output_data}")

    # 3. 使用失败的Mock Agent
    print("\n=== 示例3: 失败的Mock Agent ===")
    mock3 = create_failure_mock(
        agent_id="mock3",
        error_message="自定义错误"
    )
    result3 = await mock3.execute(context1)
    print(f"结果: {result3.status}")
    print(f"错误: {result3.error_message}")

    # 4. 使用可配置的Mock Agent（链式配置）
    print("\n=== 示例4: 可配置的Mock Agent ===")
    mock4 = (ConfigurableMockAgent(agent_id="mock4")
             .with_capability("test_capability", "测试能力", 2.0)
             .with_delay(0.5)
             .with_result({"chained": "result"}))

    # 重新初始化以注册能力
    mock4._initialize()

    result4 = await mock4.execute(context1)
    print(f"结果: {result4.status}")
    print(f"输出: {result4.output_data}")
    print(f"能力: {len(mock4.get_capabilities())}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
