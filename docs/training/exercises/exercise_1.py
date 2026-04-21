"""
练习1：创建简单Agent
===================

目标：从零开始创建一个符合统一接口标准的简单Agent

任务要求：
1. 继承BaseXiaonaComponent基类
2. 实现_initialize()方法注册能力
3. 实现execute()方法处理任务
4. 实现get_system_prompt()方法返回提示词

你的Agent应该：
- 名称：HelloAgent
- 功能：返回问候语
- 能力：greet（打招呼）
"""

from typing import Any, Dict
import logging

# TODO: 导入必要的基类和数据类
from core.agents.xiaona.base_component import (
    BaseXiaonaComponent,
    AgentCapability,
    AgentExecutionContext,
    AgentExecutionResult,
    AgentStatus,
)

logger = logging.getLogger(__name__)


class HelloAgent(BaseXiaonaComponent):
    """
    问候Agent - 练习1

    这是一个简单的Agent，用于学习Agent接口的基本结构。
    功能：返回问候语
    """

    def _initialize(self) -> None:
        """
        TODO: 实现初始化方法

        在此方法中：
        1. 使用self._register_capabilities()注册能力
        2. 注册一个名为"greet"的能力
        """
        # 在这里写你的代码
        self._register_capabilities([
            # TODO: 创建AgentCapability实例
            AgentCapability(
                name="greet",  # 能力名称
                description="返回问候语",  # 能力描述
                input_types=["姓名"],  # 输入类型
                output_types=["问候语"],  # 输出类型
                estimated_time=1.0,  # 预估时间（秒）
            ),
        ])

        logger.info(f"HelloAgent初始化完成: {self.agent_id}")

    def get_system_prompt(self) -> str:
        """
        TODO: 返回系统提示词

        返回一个字符串，描述Agent的角色和能力
        """
        return """你是HelloAgent，一个友好的问候助手。

核心能力：
- greet: 向用户打招呼

工作原则：
- 友好热情
- 简洁明了
- 根据时间选择适当的问候语
"""

    async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
        """
        TODO: 实现执行方法

        处理任务并返回结果：
        1. 从context.input_data获取用户输入
        2. 生成问候语
        3. 返回AgentExecutionResult
        """
        try:
            # 获取用户姓名
            name = context.input_data.get("name", "朋友")

            # 生成问候语
            greeting = f"你好，{name}！很高兴见到你！"

            # 返回成功结果
            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.COMPLETED,
                output_data={
                    "greeting": greeting,
                },
                metadata={
                    "name": name,
                    "greeting_length": len(greeting),
                },
            )

        except Exception as e:
            logger.exception(f"任务执行失败: {context.task_id}")
            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.ERROR,
                error_message=f"执行失败: {str(e)}",
            )


# 测试代码
async def test_hello_agent():
    """测试HelloAgent"""
    import asyncio

    # 创建Agent
    agent = HelloAgent(agent_id="hello_agent_001")

    # 打印Agent信息
    print("=== Agent信息 ===")
    info = agent.get_info()
    print(f"Agent ID: {info['agent_id']}")
    print(f"Agent 类型: {info['agent_type']}")
    print(f"能力列表:")
    for cap in info['capabilities']:
        print(f"  - {cap['name']}: {cap['description']}")

    # 创建执行上下文
    context = AgentExecutionContext(
        session_id="SESSION_001",
        task_id="TASK_001",
        input_data={"name": "徐健"},
        config={},
        metadata={},
    )

    # 执行任务
    print("\n=== 执行任务 ===")
    result = await agent.execute(context)

    # 打印结果
    print(f"状态: {result.status.value}")
    if result.status == AgentStatus.COMPLETED:
        print(f"问候语: {result.output_data['greeting']}")
    else:
        print(f"错误: {result.error_message}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_hello_agent())
