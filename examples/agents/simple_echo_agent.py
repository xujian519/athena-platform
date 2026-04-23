"""
简单Echo Agent - 最简单的Agent示例
==================================

这是一个最简单的Agent示例，展示了Agent的基本结构。
不依赖任何外部服务，适合学习Agent接口的基础概念。

功能：回显用户输入，添加时间戳和统计信息

作者: Athena平台团队
版本: 1.0.0
"""

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


class SimpleEchoAgent(BaseXiaonaComponent):
    """
    简单回显Agent

    最简单的Agent示例，用于学习Agent接口的基本结构。
    不使用LLM或工具，直接返回输入数据。

    Attributes:
        echo_count: 回显次数统计

    Examples:
        >>> agent = SimpleEchoAgent(agent_id="echo_001")
        >>> result = await agent.execute(context)
        >>> assert result.status == AgentStatus.COMPLETED
        >>> assert "echo" in result.output_data
    """

    __version__ = "1.0.0"
    __category__ = "example"

    def _initialize(self) -> None:
        """初始化Agent"""
        # 注册能力
        self._register_capabilities([
            AgentCapability(
                name="echo",
                description="回显用户输入，添加时间戳",
                input_types=["任意文本"],
                output_types=["带时间戳的回显"],
                estimated_time=0.1,
            ),
            AgentCapability(
                name="reverse",
                description="反转输入文本",
                input_types=["文本"],
                output_types=["反转后的文本"],
                estimated_time=0.1,
            ),
        ])

        # 初始化统计
        self.echo_count = 0
        self.char_count = 0

        logger.info(f"SimpleEchoAgent初始化完成: {self.agent_id}")

    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是SimpleEchoAgent，一个简单的回显助手。

核心能力：
- echo: 回显用户输入，添加时间戳
- reverse: 反转输入文本

工作原则：
- 精确回显，不做修改
- 添加处理时间戳
- 统计处理字符数

输出格式：
JSON格式的回显结果
"""

    async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
        """执行任务"""
        start_time = datetime.now()

        try:
            # 获取操作类型
            operation = context.input_data.get("operation", "echo")
            text = context.input_data.get("text", "")

            # 根据操作类型处理
            if operation == "echo":
                result = self._echo(text)
            elif operation == "reverse":
                result = self._reverse(text)
            else:
                raise ValueError(f"未知的操作类型: {operation}")

            # 更新统计
            self.echo_count += 1
            self.char_count += len(text)

            # 返回结果
            execution_time = (datetime.now() - start_time).total_seconds()

            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.COMPLETED,
                output_data=result,
                execution_time=execution_time,
                metadata={
                    "operation": operation,
                    "input_length": len(text),
                    "echo_count": self.echo_count,
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

    def _echo(self, text: str) -> dict[str, Any]:
        """回显文本"""
        return {
            "operation": "echo",
            "original": text,
            "echo": text,
            "timestamp": datetime.now().isoformat(),
            "length": len(text),
        }

    def _reverse(self, text: str) -> dict[str, Any]:
        """反转文本"""
        return {
            "operation": "reverse",
            "original": text,
            "reversed": text[::-1],
            "timestamp": datetime.now().isoformat(),
            "length": len(text),
        }

    def get_stats(self) -> dict[str, int]:
        """获取统计信息"""
        return {
            "echo_count": self.echo_count,
            "char_count": self.char_count,
        }


# 便捷函数
def create_simple_echo_agent(agent_id: str = "simple_echo_001") -> SimpleEchoAgent:
    """创建SimpleEchoAgent实例"""
    return SimpleEchoAgent(agent_id=agent_id)


# 测试入口
async def main():
    """测试入口"""

    # 配置日志
    logging.basicConfig(level=logging.INFO)

    # 创建Agent
    agent = SimpleEchoAgent(agent_id="echo_test")

    # 测试echo
    print("=== Echo测试 ===")
    context = AgentExecutionContext(
        session_id="SESSION_001",
        task_id="TASK_001",
        input_data={"operation": "echo", "text": "Hello, Athena!"},
        config={},
        metadata={},
    )

    result = await agent.execute(context)
    print(f"状态: {result.status.value}")
    print(f"结果: {result.output_data}")
    print(f"耗时: {result.execution_time:.3f}秒")

    # 测试reverse
    print("\n=== Reverse测试 ===")
    context.input_data = {"operation": "reverse", "text": "Athena"}
    result = await agent.execute(context)
    print(f"状态: {result.status.value}")
    print(f"结果: {result.output_data}")

    # 统计
    print("\n=== 统计 ===")
    stats = agent.get_stats()
    print(f"回显次数: {stats['echo_count']}")
    print(f"字符总数: {stats['char_count']}")


if __name__ == "__main__":
    asyncio.run(main())
