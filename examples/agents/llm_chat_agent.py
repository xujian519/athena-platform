"""
LLM Chat Agent - 带LLM的Agent示例
==================================

这是一个使用LLM的Agent示例，展示如何在Agent中集成LLM能力。
支持多轮对话、上下文管理和响应生成。

功能：基于LLM的对话Agent，支持多轮对话

作者: Athena平台团队
版本: 1.0.0

依赖:
- core.llm.unified_llm_manager
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


class LLMChatAgent(BaseXiaonaComponent):
    """
    LLM对话Agent

    使用LLM生成响应的对话Agent，支持：
    - 多轮对话管理
    - 上下文保持
    - 流式响应

    Attributes:
        llm: LLM管理器实例
        conversation_history: 对话历史
        max_history: 最大历史记录数

    Examples:
        >>> agent = LLMChatAgent(agent_id="chat_001")
        >>> result = await agent.execute(context)
        >>> response = result.output_data["response"]
    """

    __version__ = "1.0.0"
    __category__ = "general"

    def _initialize(self) -> None:
        """初始化Agent"""
        # 注册能力
        self._register_capabilities([
            AgentCapability(
                name="chat",
                description="与用户进行对话",
                input_types=["用户消息"],
                output_types=["AI回复"],
                estimated_time=5.0,
            ),
            AgentCapability(
                name="summarize",
                description="总结对话内容",
                input_types=["对话历史"],
                output_types=["摘要"],
                estimated_time=3.0,
            ),
        ])

        # 初始化LLM
        try:
            from core.llm.unified_llm_manager import UnifiedLLMManager
            self.llm = UnifiedLLMManager()
            self.llm_available = True
        except ImportError:
            self.llm = None
            self.llm_available = False
            logger.warning("LLM不可用，Agent将以模拟模式运行")

        # 配置
        self.model = self.config.get("model", "gpt-4")
        self.temperature = self.config.get("temperature", 0.7)
        self.max_tokens = self.config.get("max_tokens", 2000)

        # 对话管理
        self.conversation_history: List[Dict[str, str]] = []
        self.max_history = self.config.get("max_history", 10)

        logger.info(f"LLMChatAgent初始化完成: {self.agent_id}, LLM可用: {self.llm_available}")

    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是LLMChatAgent，一个友好的AI对话助手。

核心能力：
- chat: 与用户进行自然语言对话
- summarize: 总结对话内容

工作原则：
- 友好热情，乐于助人
- 保持对话上下文连贯
- 提供准确、有用的信息
- 遇到不确定的问题时坦诚说明

对话风格：
- 使用简体中文回复
- 保持专业但不失亲和力
- 适当使用表情符号增加亲和力

输出格式：
自然语言的对话回复
"""

    async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
        """执行任务"""
        start_time = datetime.now()

        try:
            # 获取操作类型
            operation = context.input_data.get("operation", "chat")

            if operation == "chat":
                result = await self._chat(context)
            elif operation == "summarize":
                result = await self._summarize(context)
            elif operation == "clear":
                result = self._clear_history()
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
                    "history_length": len(self.conversation_history),
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

    async def _chat(self, context: AgentExecutionContext) -> Dict[str, Any]:
        """处理对话"""
        user_message = context.input_data.get("message", "")

        if not user_message:
            raise ValueError("消息不能为空")

        # 添加用户消息到历史
        self.conversation_history.append({
            "role": "user",
            "content": user_message,
        })

        # 生成响应
        if self.llm_available and self.llm:
            # 使用真实LLM
            response = await self._generate_with_llm(user_message)
        else:
            # 模拟响应
            response = self._generate_mock_response(user_message)

        # 添加助手响应到历史
        self.conversation_history.append({
            "role": "assistant",
            "content": response,
        })

        # 限制历史长度
        if len(self.conversation_history) > self.max_history * 2:
            self.conversation_history = self.conversation_history[-self.max_history * 2:]

        return {
            "operation": "chat",
            "user_message": user_message,
            "response": response,
            "history_length": len(self.conversation_history) // 2,
        }

    async def _generate_with_llm(self, user_message: str) -> str:
        """使用LLM生成响应"""
        try:
            # 构建消息列表
            messages = [
                {"role": "system", "content": self.get_system_prompt()},
                *self.conversation_history[-10:],  # 限制上下文长度
            ]

            # 调用LLM
            response = await self.llm.generate(
                messages=messages,
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            return response.strip()

        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            return self._generate_mock_response(user_message)

    def _generate_mock_response(self, user_message: str) -> str:
        """生成模拟响应（LLM不可用时使用）"""
        responses = [
            f"你说的是：{user_message}，这是一个很有趣的话题！",
            f"关于'{user_message}'，我理解你的意思了。",
            f"感谢你的消息：{user_message}。有什么我可以帮助你的吗？",
        ]

        import random
        return random.choice(responses)

    async def _summarize(self, context: AgentExecutionContext) -> Dict[str, Any]:
        """总结对话"""
        if not self.conversation_history:
            return {
                "operation": "summarize",
                "summary": "暂无对话历史",
            }

        # 构建对话文本
        conversation_text = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in self.conversation_history
        ])

        # 生成摘要
        if self.llm_available and self.llm:
            summary = await self._generate_summary_with_llm(conversation_text)
        else:
            summary = f"对话包含{len(self.conversation_history)//2}轮交流"

        return {
            "operation": "summarize",
            "summary": summary,
            "conversation_count": len(self.conversation_history) // 2,
        }

    async def _generate_summary_with_llm(self, conversation_text: str) -> str:
        """使用LLM生成摘要"""
        try:
            response = await self.llm.generate(
                messages=[{
                    "role": "system",
                    "content": "请用简练的语言总结以下对话的主要内容，不超过100字。"
                }, {
                    "role": "user",
                    "content": conversation_text
                }],
                model=self.model,
                max_tokens=200,
            )
            return response.strip()
        except Exception as e:
            logger.error(f"摘要生成失败: {e}")
            return "摘要生成失败"

    def _clear_history(self) -> Dict[str, Any]:
        """清空历史"""
        count = len(self.conversation_history)
        self.conversation_history.clear()
        return {
            "operation": "clear",
            "message": f"已清空{count}条历史记录",
        }

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """获取对话历史"""
        return self.conversation_history.copy()

    def clear_history(self) -> None:
        """清空对话历史"""
        self.conversation_history.clear()


# 便捷函数
def create_llm_chat_agent(
    agent_id: str = "llm_chat_001",
    model: str = "gpt-4",
    temperature: float = 0.7,
) -> LLMChatAgent:
    """创建LLMChatAgent实例"""
    return LLMChatAgent(
        agent_id=agent_id,
        config={
            "model": model,
            "temperature": temperature,
        }
    )


# 测试入口
async def main():
    """测试入口"""
    import asyncio

    # 配置日志
    logging.basicConfig(level=logging.INFO)

    # 创建Agent
    agent = LLMChatAgent(agent_id="chat_test")

    print("=== LLM Chat Agent测试 ===")

    # 测试对话
    test_messages = [
        "你好，我是Athena平台的开发者",
        "我想了解一下Agent的开发流程",
        "谢谢你的介绍",
    ]

    for msg in test_messages:
        print(f"\n用户: {msg}")
        context = AgentExecutionContext(
            session_id="SESSION_001",
            task_id=f"TASK_{len(agent.conversation_history)//2 + 1}",
            input_data={"operation": "chat", "message": msg},
            config={},
            metadata={},
        )

        result = await agent.execute(context)
        if result.status == AgentStatus.COMPLETED:
            print(f"助手: {result.output_data['response']}")
            print(f"  [耗时: {result.execution_time:.2f}秒]")

    # 测试总结
    print("\n=== 对话总结 ===")
    context = AgentExecutionContext(
        session_id="SESSION_001",
        task_id="SUMMARY",
        input_data={"operation": "summarize"},
        config={},
        metadata={},
    )

    result = await agent.execute(context)
    print(f"摘要: {result.output_data['summary']}")


if __name__ == "__main__":
    asyncio.run(main())
