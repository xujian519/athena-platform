"""
统一Agent使用示例

Author: Athena Team
Version: 1.0.0
Date: 2026-04-24
"""

import asyncio

from core.unified_agents.base import (
    AgentRequest,
    AgentResponse,
    AgentStatus,
    HealthStatus,
    MessageConverter,
    ResponseMessage,
    TaskMessage,
)
from core.unified_agents.adapters import (
    AdapterFactory,
    LegacyAgentAdapter,
)
from core.unified_agents.config import (
    ConfigTemplates,
    UnifiedAgentConfig,
    UnifiedAgentConfigBuilder,
)
from core.unified_agents.base_agent import UnifiedBaseAgent


# ============ 示例1: 最简单的Agent ============


class SimpleEchoAgent(UnifiedBaseAgent):
    """简单的回显Agent - 最小实现示例"""

    @property
    def name(self) -> str:
        return "echo-agent"

    async def initialize(self) -> None:
        """初始化"""
        self.logger.info(f"{self.name} 初始化中...")
        # 模拟初始化工作
        await asyncio.sleep(0.01)
        self._status = AgentStatus.READY
        self.logger.info(f"{self.name} 初始化完成")

    async def process(self, request: AgentRequest) -> AgentResponse:
        """处理请求 - 简单回显"""
        # 获取输入
        input_text = request.parameters.get("input", "")

        # 处理（这里只是简单回显）
        result = f"回显: {input_text}"

        return AgentResponse.success_response(
            request_id=request.request_id,
            data={"output": result}
        )

    async def shutdown(self) -> None:
        """关闭"""
        self.logger.info(f"{self.name} 关闭中...")
        self._status = AgentStatus.SHUTDOWN
        self.logger.info(f"{self.name} 已关闭")

    async def health_check(self) -> HealthStatus:
        """健康检查"""
        return HealthStatus(
            status=self._status,
            message=f"{self.name} 运行正常"
        )


# ============ 示例2: 带状态的Agent ============


class CounterAgent(UnifiedBaseAgent):
    """计数器Agent - 展示状态管理"""

    @property
    def name(self) -> str:
        return "counter-agent"

    async def initialize(self) -> None:
        """初始化计数器"""
        self._count = 0
        self._status = AgentStatus.READY

    async def process(self, request: AgentRequest) -> AgentResponse:
        """处理计数请求"""
        action = request.action

        if action == "increment":
            self._count += 1
            result = self._count
        elif action == "decrement":
            self._count -= 1
            result = self._count
        elif action == "get":
            result = self._count
        elif action == "reset":
            self._count = 0
            result = 0
        else:
            return AgentResponse.error_response(
                request_id=request.request_id,
                error=f"未知操作: {action}"
            )

        return AgentResponse.success_response(
            request_id=request.request_id,
            data={"count": result, "action": action}
        )

    async def shutdown(self) -> None:
        """关闭"""
        self._status = AgentStatus.SHUTDOWN

    async def health_check(self) -> HealthStatus:
        """健康检查"""
        return HealthStatus(
            status=self._status,
            message=f"当前计数: {self._count}"
        )


# ============ 示例3: 传统Agent（用于适配） ============


class LegacyAgent:
    """传统Agent示例 - 只实现简单接口"""

    def __init__(self):
        self.name = "legacy-agent"
        self.role = "legacy-processor"
        self.capabilities = ["process", "echo"]

    def process(self, input_text: str, **kwargs) -> str:
        """传统处理接口"""
        return f"传统处理: {input_text}"

    def get_capabilities(self) -> list:
        """获取能力列表"""
        return self.capabilities


# ============ 使用示例函数 ============


async def example_1_basic_usage():
    """示例1: 基础用法"""
    print("=" * 50)
    print("示例1: 基础Agent用法")
    print("=" * 50)

    # 创建配置
    config = UnifiedAgentConfig.create_minimal("echo-agent", "echo-processor")

    # 创建Agent
    agent = SimpleEchoAgent(config)

    # 初始化
    await agent.initialize()
    print(f"Agent状态: {agent.status.value}")

    # 处理请求
    request = AgentRequest(
        request_id="req-001",
        action="echo",
        parameters={"input": "Hello, Unified Agent!"}
    )

    response = await agent.process(request)
    print(f"响应: {response.data}")

    # 健康检查
    health = await agent.health_check()
    print(f"健康状态: {health.message}")

    # 统计信息
    stats = agent.get_stats()
    print(f"统计: {stats}")

    # 关闭
    await agent.shutdown()
    print()


async def example_2_config_builder():
    """示例2: 使用配置构建器"""
    print("=" * 50)
    print("示例2: 配置构建器用法")
    print("=" * 50)

    # 使用构建器创建配置
    config = (UnifiedAgentConfigBuilder()
              .name("custom-agent")
              .role("custom-processor")
              .model("gpt-4")
              .temperature(0.5)
              .max_tokens(1000)
              .enable_memory(True)
              .build())

    print(f"配置: {config.to_dict()}")

    # 使用配置模板
    legal_config = ConfigTemplates.legal_agent("my-legal-agent")
    print(f"法律Agent配置: {legal_config.to_dict()}")
    print()


async def example_3_counter_agent():
    """示例3: 有状态的Agent"""
    print("=" * 50)
    print("示例3: 有状态的Agent")
    print("=" * 50)

    config = UnifiedAgentConfig.create_minimal("counter-agent", "counter")
    agent = CounterAgent(config)
    await agent.initialize()

    # 执行一系列操作
    for action in ["increment", "increment", "get", "decrement", "get"]:
        request = AgentRequest(
            request_id=f"req-{action}",
            action=action,
            parameters={}
        )
        response = await agent.process(request)
        print(f"{action}: {response.data}")

    await agent.shutdown()
    print()


async def example_4_legacy_adapter():
    """示例4: 传统Agent适配器"""
    print("=" * 50)
    print("示例4: 传统Agent适配器")
    print("=" * 50)

    # 创建传统Agent
    legacy = LegacyAgent()

    # 使用适配器工厂
    adapter = AdapterFactory.create_adapter(legacy)

    # 初始化
    await adapter.initialize()
    print(f"适配器名称: {adapter.name}")

    # 使用新接口调用
    request = AgentRequest(
        request_id="req-legacy",
        action="process",
        parameters={"input": "Hello from new interface!"}
    )

    response = await adapter.process(request)
    print(f"响应数据: {response.data}")
    print(f"响应成功: {response.success}")

    await adapter.shutdown()
    print()


async def example_5_message_conversion():
    """示例5: 消息格式转换"""
    print("=" * 50)
    print("示例5: 消息格式转换")
    print("=" * 50)

    # 传统任务消息
    task_msg = TaskMessage(
        sender_id="user",
        recipient_id="agent",
        task_type="process",
        content={"input": "test"},
        task_id="task-001"
    )

    # 转换为新请求格式
    new_request = MessageConverter.task_to_request(task_msg)
    print(f"转换后请求: {new_request.action}, 参数: {new_request.parameters}")

    # 转换回传统格式
    task_msg_2 = MessageConverter.request_to_task(new_request, "agent")
    print(f"转换回任务: {task_msg_2.task_type}, 内容: {task_msg_2.content}")
    print()


async def example_6_health_check():
    """示例6: 健康检查"""
    print("=" * 50)
    print("示例6: 健康检查详情")
    print("=" * 50)

    config = UnifiedAgentConfig.create_minimal("test-agent", "tester")
    agent = SimpleEchoAgent(config)

    await agent.initialize()

    # 获取健康状态
    health = await agent.health_check()
    print(f"状态: {health.status.value}")
    print(f"健康: {health.is_healthy()}")
    print(f"消息: {health.message}")
    print(f"详情: {health.details}")

    await agent.shutdown()
    print()


# ============ 主函数 ============


async def main():
    """运行所有示例"""
    await example_1_basic_usage()
    await example_2_config_builder()
    await example_3_counter_agent()
    await example_4_legacy_adapter()
    await example_5_message_conversion()
    await example_6_health_check()

    print("=" * 50)
    print("所有示例运行完成!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
