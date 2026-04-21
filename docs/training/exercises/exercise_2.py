"""
练习2：添加LLM调用能力
======================

目标：扩展Agent，添加LLM调用能力

任务要求：
1. 在_initialize中初始化LLM Manager
2. 在execute中调用LLM生成响应
3. 处理LLM响应并返回结构化结果

你的Agent应该：
- 名称：ChatAgent
- 功能：使用LLM进行对话
- 能力：chat（对话）
"""

from typing import Any, Dict
import logging
import json

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
    对话Agent - 练习2

    使用LLM进行智能对话的Agent
    """

    def _initialize(self) -> None:
        """
        TODO: 初始化Agent

        在此方法中：
        1. 注册能力（chat能力）
        2. 初始化LLM Manager
        """
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

        # TODO: 初始化LLM Manager
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
        """
        TODO: 实现执行方法

        步骤：
        1. 获取用户消息
        2. 构建提示词
        3. 调用LLM
        4. 解析响应
        5. 返回结果
        """
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

            # TODO: 构建提示词
            prompt = f"""用户消息：{user_message}

请回复："""

            # TODO: 调用LLM
            logger.info(f"调用LLM: {model}, message: {user_message[:50]}...")
            response = await self.llm.generate(
                prompt=prompt,
                system_prompt=self.get_system_prompt(),
                model=model,
                max_tokens=max_tokens,
            )

            # 清理响应（移除可能的markdown代码块标记）
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


# 测试代码
async def test_chat_agent():
    """测试ChatAgent"""
    import asyncio

    # 创建Agent
    agent = ChatAgent(agent_id="chat_agent_001")

    # 打印Agent信息
    print("=== Agent信息 ===")
    info = agent.get_info()
    print(f"Agent ID: {info['agent_id']}")
    print(f"能力: {[c['name'] for c in info['capabilities']]}")

    # 测试对话
    test_messages = [
        "你好，请介绍一下你自己",
        "Python中async/await是什么？",
        "今天天气怎么样？",
    ]

    for msg in test_messages:
        print(f"\n=== 用户: {msg} ===")

        context = AgentExecutionContext(
            session_id="SESSION_001",
            task_id=f"TASK_{len(msg)}",
            input_data={"message": msg},
            config={"model": "kimi-k2.5"},
            metadata={},
        )

        result = await agent.execute(context)

        if result.status == AgentStatus.COMPLETED:
            print(f"AI: {result.output_data['response']}")
            print(f"  (模型: {result.output_data['model']}, "
                  f"输入长度: {result.metadata['input_length']}, "
                  f"输出长度: {result.metadata['output_length']})")
        else:
            print(f"错误: {result.error_message}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_chat_agent())
