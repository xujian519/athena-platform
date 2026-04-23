"""
示例Agent：HelloAgent
======================

这是一个最简单的Agent示例，展示了Agent的基本结构。

功能：返回问候语
"""

import logging

from core.framework.agents.xiaona.base_component import (
    AgentCapability,
    AgentExecutionContext,
    AgentExecutionResult,
    AgentStatus,
    BaseXiaonaComponent,
)

logger = logging.getLogger(__name__)


class HelloAgent(BaseXiaonaComponent):
    """
    问候Agent - 示例

    简单的问候Agent，用于学习Agent接口的基本结构。
    """

    def _initialize(self) -> None:
        """初始化Agent"""
        # 注册能力
        self._register_capabilities([
            AgentCapability(
                name="greet",
                description="返回问候语",
                input_types=["姓名"],
                output_types=["问候语"],
                estimated_time=1.0,
            ),
        ])

        logger.info(f"HelloAgent初始化完成: {self.agent_id}")

    def get_system_prompt(self) -> str:
        """返回系统提示词"""
        return """你是HelloAgent，一个友好的问候助手。

核心能力：
- greet: 向用户打招呼

工作原则：
- 友好热情
- 简洁明了
- 根据时间选择适当的问候语
"""

    async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
        """执行任务"""
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


# 便捷函数
def create_hello_agent(agent_id: str = "hello_agent_001") -> HelloAgent:
    """创建HelloAgent实例"""
    return HelloAgent(agent_id=agent_id)


# 测试入口
async def main():
    """测试入口"""

    # 创建Agent
    agent = HelloAgent(agent_id="hello_agent_001")

    # 打印信息
    print("=== HelloAgent示例 ===")
    info = agent.get_info()
    print(f"Agent ID: {info['agent_id']}")
    print(f"类型: {info['agent_type']}")
    print(f"能力: {[c['name'] for c in info['capabilities']}")

    # 测试执行
    print("\n=== 执行示例 ===")
    context = AgentExecutionContext(
        session_id="SESSION_001",
        task_id="TASK_001",
        input_data={"name": "开发者"},
        config={},
        metadata={},
    )

    result = await agent.execute(context)

    if result.status == AgentStatus.COMPLETED:
        print(f"问候语: {result.output_data['greeting']}")
    else:
        print(f"错误: {result.error_message}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
