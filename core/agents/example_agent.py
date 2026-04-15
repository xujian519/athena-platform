from __future__ import annotations
"""
示例智能体 - 展示如何使用BaseAgent接口

这是一个完整的示例实现，展示了：
1. 如何继承BaseAgent
2. 如何实现所有必需的方法
3. 如何注册能力
4. 如何处理不同类型的请求
5. 如何进行健康检查

可以作为迁移其他智能体的参考模板。

Author: Athena Team
Version: 1.0.0
Date: 2025-02-21
"""

import asyncio
from datetime import datetime
from typing import Any

from core.agents.base import (
    AgentCapability,
    AgentMetadata,
    AgentRegistry,
    AgentRequest,
    AgentResponse,
    AgentStatus,
    BaseAgent,
    HealthStatus,
)


class ExampleAgent(BaseAgent):
    """
    示例智能体

    这是一个完整的智能体实现示例，展示了BaseAgent的所有功能。
    """

    @property
    def name(self) -> str:
        """智能体唯一标识"""
        return "example-agent"

    def _load_metadata(self) -> AgentMetadata:
        """加载元数据"""
        return AgentMetadata(
            name=self.name,
            version="1.0.0",
            description="示例智能体，展示BaseAgent的使用方法",
            author="Athena Team",
            tags=["example", "demo"]
        )

    def _register_capabilities(self) -> list[AgentCapability]:
        """注册能力列表"""
        return [
            AgentCapability(
                name="echo",
                description="回显输入内容",
                parameters={
                    "message": {
                        "type": "string",
                        "description": "要回显的消息",
                        "required": True
                    }
                },
                examples=[
                    {"message": "Hello World!"},
                    {"message": "测试消息"}
                ]
            ),
            AgentCapability(
                name="add",
                description="加法计算",
                parameters={
                    "a": {"type": "number", "description": "第一个数"},
                    "b": {"type": "number", "description": "第二个数"}
                },
                examples=[
                    {"a": 1, "b": 2},
                    {"a": 10, "b": 20}
                ]
            ),
            AgentCapability(
                name="get-stats",
                description="获取统计信息",
                parameters={},
                examples=[{}]
            )
        ]

    async def initialize(self) -> None:
        """
        初始化智能体

        在这里加载资源、建立连接等。
        """
        self.logger.info("正在初始化示例智能体...")

        # 模拟一些初始化工作
        await asyncio.sleep(0.1)

        # 设置一些初始状态
        self._counter = 0
        self._start_time = datetime.now()

        # 设置为就绪状态
        self._status = AgentStatus.READY
        self.logger.info("示例智能体初始化完成")

    async def process(self, request: AgentRequest) -> AgentResponse:
        """
        处理请求的核心方法

        根据action路由到不同的处理方法。
        """
        action = request.action
        params = request.parameters

        self.logger.info(f"处理请求: action={action}, request_id={request.request_id}")

        # 路由到具体的处理方法
        handler = self._get_handler(action)
        if handler is None:
            return AgentResponse.error_response(
                request_id=request.request_id,
                error=f"不支持的操作: {action}"
            )

        # 执行处理
        try:
            result = await handler(params)
            self._counter += 1

            return AgentResponse.success_response(
                request_id=request.request_id,
                data=result,
                metadata={
                    "action": action,
                    "counter": self._counter,
                    "agent": self.name
                }
            )
        except Exception as e:
            self.logger.error(f"处理失败: {e}", exc_info=True)
            return AgentResponse.error_response(
                request_id=request.request_id,
                error=str(e)
            )

    def _get_handler(self, action: str):
        """获取处理方法"""
        handlers = {
            "echo": self._handle_echo,
            "add": self._handle_add,
            "get-stats": self._handle_get_stats,
            "get-capabilities": self._handle_get_capabilities
        }
        return handlers.get(action)

    async def _handle_echo(self, params: dict[str, Any]) -> dict[str, Any]:
        """处理echo请求"""
        message = params.get("message", "")
        return {
            "echo": message,
            "timestamp": datetime.now().isoformat()
        }

    async def _handle_add(self, params: dict[str, Any]) -> dict[str, Any]:
        """处理add请求"""
        a = params.get("a", 0)
        b = params.get("b", 0)
        return {
            "result": a + b,
            "expression": f"{a} + {b} = {a + b}"
        }

    async def _handle_get_stats(self, params: dict[str, Any]) -> dict[str, Any]:
        """处理get-stats请求"""
        uptime = datetime.now() - self._start_time
        return {
            "counter": self._counter,
            "uptime_seconds": int(uptime.total_seconds()),
            "start_time": self._start_time.isoformat(),
            "status": self._status.value
        }

    async def _handle_get_capabilities(self, params: dict[str, Any]) -> dict[str, Any]:
        """处理get-capabilities请求"""
        return {
            "capabilities": [cap.to_dict() for cap in self.get_capabilities()]
        }

    async def validate_request(self, request: AgentRequest) -> bool:
        """验证请求"""
        # 基础验证
        if not request.action:
            self.logger.warning("请求缺少action字段")
            return False

        # 检查必需参数
        required_params = {
            "echo": ["message"],
            "add": ["a", "b"]
        }

        params_needed = required_params.get(request.action, [])
        for param in params_needed:
            if param not in request.parameters:
                self.logger.warning(f"缺少必需参数: {param}")
                return False

        return True

    async def before_process(self, request: AgentRequest) -> None:
        """处理前钩子"""
        self.logger.debug(f"开始处理请求: {request.request_id}")

    async def after_process(self, request: AgentRequest, response: AgentResponse) -> None:
        """处理后钩子"""
        self.logger.debug(
            f"请求处理完成: {request.request_id}, "
            f"成功={response.success}, "
            f"耗时={response.processing_time_ms}ms"
        )

    async def health_check(self) -> HealthStatus:
        """健康检查"""
        # 检查基本状态
        if self._status == AgentStatus.SHUTDOWN:
            return HealthStatus(
                status=AgentStatus.SHUTDOWN,
                message="智能体已关闭"
            )

        # 检查运行时间
        uptime = datetime.now() - self._start_time
        if uptime.total_seconds() < 60:
            message = f"运行正常 (运行时间: {int(uptime.total_seconds())}秒)"
        else:
            message = f"运行正常 (运行时间: {int(uptime.total_seconds() / 60)}分钟)"

        # 返回健康状态
        return HealthStatus(
            status=AgentStatus.READY,
            message=message,
            details={
                "counter": self._counter,
                "uptime_seconds": int(uptime.total_seconds())
            }
        )

    async def shutdown(self) -> None:
        """关闭智能体"""
        self.logger.info("正在关闭示例智能体...")

        # 保存状态（如果需要）
        # await self._save_state()

        # 清理资源
        self._counter = 0

        # 更新状态
        self._status = AgentStatus.SHUTDOWN
        self.logger.info("示例智能体已关闭")


# ========== 使用示例 ==========

async def example_usage():
    """展示如何使用ExampleAgent"""

    print("=" * 50)
    print("示例智能体使用演示")
    print("=" * 50)

    # 1. 创建智能体
    print("\n1. 创建智能体...")
    agent = ExampleAgent()
    print(f"   智能体名称: {agent.name}")
    print(f"   初始状态: {agent.status.value}")

    # 2. 初始化
    print("\n2. 初始化智能体...")
    await agent.initialize()
    print(f"   当前状态: {agent.status.value}")
    print(f"   就绪状态: {agent.is_ready}")

    # 3. 查看能力
    print("\n3. 智能体能力:")
    for cap in agent.get_capabilities():
        print(f"   - {cap.name}: {cap.description}")

    # 4. 处理请求
    print("\n4. 处理请求:")

    # Echo请求
    request1 = AgentRequest(
        request_id="req-001",
        action="echo",
        parameters={"message": "Hello!"}
    )
    response1 = await agent.safe_process(request1)
    print(f"   Echo: {response1.data}")

    # Add请求
    request2 = AgentRequest(
        request_id="req-002",
        action="add",
        parameters={"a": 10, "b": 20}
    )
    response2 = await agent.safe_process(request2)
    print(f"   Add: {response2.data}")

    # 获取统计
    request3 = AgentRequest(
        request_id="req-003",
        action="get-stats",
        parameters={}
    )
    response3 = await agent.safe_process(request3)
    print(f"   Stats: {response3.data}")

    # 5. 健康检查
    print("\n5. 健康检查...")
    health = await agent.health_check()
    print(f"   状态: {health.status.value}")
    print(f"   消息: {health.message}")

    # 6. 查看统计
    print("\n6. 处理统计:")
    stats = agent.get_stats()
    print(f"   总请求数: {stats['total_requests']}")
    print(f"   成功数: {stats['successful_requests']}")

    # 7. 关闭
    print("\n7. 关闭智能体...")
    await agent.shutdown()
    print(f"   最终状态: {agent.status.value}")

    print("\n" + "=" * 50)
    print("演示完成!")
    print("=" * 50)


async def example_with_registry():
    """展示如何使用AgentRegistry"""

    print("\n" + "=" * 50)
    print("AgentRegistry 使用演示")
    print("=" * 50)

    # 1. 注册智能体
    print("\n1. 注册智能体...")
    agent = ExampleAgent()
    AgentRegistry.register(agent)
    print(f"   已注册: {AgentRegistry.list_agents()}")

    # 2. 从注册中心获取
    print("\n2. 从注册中心获取智能体...")
    retrieved = AgentRegistry.get("example-agent")
    print(f"   获取到: {retrieved.name if retrieved else 'None'}")

    # 3. 初始化所有智能体
    print("\n3. 初始化所有智能体...")
    await AgentRegistry.initialize_all()
    print(f"   就绪智能体: {len(AgentRegistry.get_ready_agents())}")

    # 4. 健康检查所有智能体
    print("\n4. 健康检查...")
    health_results = await AgentRegistry.health_check_all()
    for name, status in health_results.items():
        print(f"   {name}: {status.status.value}")

    # 5. 关闭所有智能体
    print("\n5. 关闭所有智能体...")
    await AgentRegistry.shutdown_all()

    print("\n" + "=" * 50)
    print("AgentRegistry 演示完成!")
    print("=" * 50)


if __name__ == "__main__":
    # 运行示例
    import asyncio

    # 运行基本示例
    asyncio.run(example_usage())

    # 运行注册中心示例
    asyncio.run(example_with_registry())
