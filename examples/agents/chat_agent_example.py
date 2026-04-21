"""
示例Agent：ChatAgent
====================

一个使用LLM的Agent示例，展示如何在Agent中调用LLM。

功能：使用LLM进行智能对话
"""

from typing import Dict
import logging

from core.agents.xiaona.base_component import (
    BaseXiaonaComponent,
    AgentCapability,
    AgentExecutionContext,
    AgentExecutionResult,
    AgentStatus,
)

logger = logging.getLogger(__name__)


class ChatAgent(BaseXiaonaComponent):
    """
    对话Agent - 示例

    使用LLM进行智能对话的Agent
    """

    def _initialize(self) -> None:
        """初始化Agent"""
        # 注册能力
        self._register_capabilities([
            AgentCapability(
                name="chat",
                description="使用LLM进行智能对话",
                input_types=["用户消息"],
                output_types=["AI回复"],
                estimated_time=5.0,
            ),
        ])

        # 初始化LLM
        from core.llm.unified_llm_manager import UnifiedLLMManager
        self.llm = UnifiedLLMManager()

        logger.info(f"ChatAgent初始化完成: {self.agent_id}")

    def get_system_prompt(self) -> str:
        """返回系统提示词"""
        return """你是一个友好、专业的AI助手。

对话原则：
1. 简洁明了，直接回答问题
2. 如果不知道答案，诚实告知
3. 保持友好和专业的语气
4. 用中文回复

输出格式：
请直接返回回复内容，不需要额外的格式标记。
"""

    async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
        """执行任务"""
        try:
            # 获取用户消息
            user_message = context.input_data.get("message", "")
            if not user_message:
                return AgentExecutionResult(
                    agent_id=self.agent_id,
                    status=AgentStatus.ERROR,
                    error_message="缺少message参数",
                )

            # 获取配置
            model = context.config.get("model", "kimi-k2.5")
            max_tokens = context.config.get("max_tokens", 1000)

            # 构建提示词
            prompt = f"""用户消息：{user_message}

请回复："""

            # 调用LLM
            logger.info(f"调用LLM: {model}")
            response = await self.llm.generate(
                prompt=prompt,
                system_prompt=self.get_system_prompt(),
                model=model,
                max_tokens=max_tokens,
            )

            # 清理响应
            response = response.strip()
            if response.startswith("```"):
                lines = response.split("\n")
                response = "\n".join(lines[1:-1]) if len(lines) > 2 else response

            # 返回成功结果
            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.COMPLETED,
                output_data={
                    "response": response,
                    "model": model,
                },
                metadata={
                    "input_length": len(user_message),
                    "output_length": len(response),
                    "model": model,
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
def create_chat_agent(agent_id: str = "chat_agent_001", model: str = "kimi-k2.5") -> ChatAgent:
    """创建ChatAgent实例"""
    return ChatAgent(agent_id=agent_id, config={"model": model})


# 测试入口
async def main():
    """测试入口"""
    import asyncio

    # 创建Agent
    agent = ChatAgent(agent_id="chat_agent_001")

    # 打印信息
    print("=== ChatAgent示例 ===")
    info = agent.get_info()
    print(f"Agent ID: {info['agent_id']}")
    print(f"能力: {[c['name'] for c in info['capabilities']]}")

    # 测试对话
    print("\n=== 对话示例 ===")
    test_message = "请用一句话介绍一下Python"

    context = AgentExecutionContext(
        session_id="SESSION_001",
        task_id="TASK_001",
        input_data={"message": test_message},
        config={"model": "kimi-k2.5"},
        metadata={},
    )

    print(f"用户: {test_message}")
    result = await agent.execute(context)

    if result.status == AgentStatus.COMPLETED:
        print(f"AI: {result.output_data['response']}")
    else:
        print(f"错误: {result.error_message}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
