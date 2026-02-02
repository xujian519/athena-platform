"""
命令路由器
根据解析的命令路由到相应的智能体
"""

import asyncio
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import logging

from .command_parser import ParsedCommand, AgentType, TaskType
from .imessage_client import IMessageClient

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """执行状态"""
    PENDING = "pending"         # 等待执行
    RUNNING = "running"         # 执行中
    COMPLETED = "completed"     # 已完成
    FAILED = "failed"           # 失败
    TIMEOUT = "timeout"         # 超时


@dataclass
class ExecutionResult:
    """执行结果"""
    task_id: str                    # 任务ID
    status: ExecutionStatus         # 执行状态
    agent: AgentType                # 执行的智能体
    summary: str                    # 结果摘要
    details: Dict[str, Any]         # 详细结果
    obsidian_file: Optional[str]    # Obsidian 文件路径
    error: Optional[str] = None     # 错误信息
    duration: float = 0.0           # 执行时长（秒）


class CommandRouter:
    """
    命令路由器

    职责：
    1. 接收解析后的命令
    2. 根据命令类型路由到对应的智能体
    3. 管理任务执行状态
    4. 收集执行结果
    """

    def __init__(
        self,
        imessage_client: IMessageClient,
        xiaonuo_agent: 'BaseAgent',
        athena_agent: 'BaseAgent'
    ):
        """
        初始化命令路由器

        Args:
            imessage_client: iMessage 客户端
            xiaonuo_agent: 小诺智能体
            athena_agent: Athena 智能体
        """
        self.imessage_client = imessage_client
        self.agents = {
            AgentType.XIAONUO: xiaonuo_agent,
            AgentType.ATHENA: athena_agent
        }
        self.active_tasks: Dict[str, ExecutionResult] = {}
        self.task_counter = 0

    async def route_command(
        self,
        command: ParsedCommand,
        sender_handle: str
    ) -> ExecutionResult:
        """
        路由命令到对应的智能体

        Args:
            command: 解析后的命令
            sender_handle: 发件人标识

        Returns:
            ExecutionResult 对象
        """
        # 生成任务ID
        task_id = self._generate_task_id()

        # 创建执行结果对象
        result = ExecutionResult(
            task_id=task_id,
            status=ExecutionStatus.PENDING,
            agent=command.agent,
            summary="",
            details={},
            obsidian_file=None
        )
        self.active_tasks[task_id] = result

        try:
            # 获取目标智能体
            agent = self.agents.get(command.agent)
            if not agent:
                raise ValueError(f"Agent not found: {command.agent}")

            # 检查智能体是否支持该任务类型
            if not agent.supports_task(command.task_type):
                raise ValueError(
                    f"Agent {command.agent} does not support task type {command.task_type}"
                )

            # 更新状态为执行中
            result.status = ExecutionStatus.RUNNING
            logger.info(f"Routing task {task_id} to {command.agent.value}")

            # 发送执行通知
            await self._send_execution_notification(
                sender_handle,
                command,
                task_id
            )

            # 执行任务（带超时）
            timeout = agent.get_timeout(command.task_type)
            agent_result = await asyncio.wait_for(
                agent.execute(command),
                timeout=timeout
            )

            # 更新结果
            result.status = ExecutionStatus.COMPLETED
            result.summary = agent_result.get("summary", "任务完成")
            result.details = agent_result.get("details", {})
            result.obsidian_file = agent_result.get("obsidian_file")
            result.duration = agent_result.get("duration", 0.0)

            logger.info(f"Task {task_id} completed successfully")

        except asyncio.TimeoutError:
            result.status = ExecutionStatus.TIMEOUT
            result.error = f"任务执行超时（超过 {timeout} 秒）"
            result.summary = "任务超时"
            logger.error(f"Task {task_id} timed out")

        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error = str(e)
            result.summary = "任务执行失败"
            logger.error(f"Task {task_id} failed: {e}")

        return result

    async def _send_execution_notification(
        self,
        sender_handle: str,
        command: ParsedCommand,
        task_id: str
    ) -> None:
        """
        发送执行通知

        Args:
            sender_handle: 发件人标识
            command: 解析后的命令
            task_id: 任务ID
        """
        agent_name = "小诺" if command.agent == AgentType.XIAONUO else "Athena"

        message = f"🔄 {agent_name}正在执行任务...\n"
        message += f"任务: {command.intent}\n"
        message += f"任务ID: {task_id}"

        # 获取聊天ID
        chat_id = await self._get_chat_id(sender_handle)
        if chat_id:
            await self.imessage_client.send_message(chat_id, message)

    async def _get_chat_id(self, handle: str) -> Optional[str]:
        """
        获取联系人对应的聊天ID

        Args:
            handle: 联系人标识

        Returns:
            聊天ID
        """
        # 尝试直接使用 handle 作为 chat_id
        # 对于 iMessage，chat_id 通常就是电话号码或邮箱
        return handle

    def _generate_task_id(self) -> str:
        """
        生成任务ID

        Returns:
            任务ID字符串
        """
        import time
        self.task_counter += 1
        timestamp = int(time.time())
        return f"task_{timestamp}_{self.task_counter}"

    def get_task_status(self, task_id: str) -> Optional[ExecutionResult]:
        """
        获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            ExecutionResult 对象，如果任务不存在则返回 None
        """
        return self.active_tasks.get(task_id)

    def get_active_tasks(self) -> Dict[str, ExecutionResult]:
        """
        获取所有活动任务

        Returns:
            任务字典
        """
        return {
            task_id: result
            for task_id, result in self.active_tasks.items()
            if result.status in [ExecutionStatus.PENDING, ExecutionStatus.RUNNING]
        }

    async def cancel_task(self, task_id: str) -> bool:
        """
        取消任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功取消
        """
        result = self.active_tasks.get(task_id)
        if not result:
            return False

        if result.status in [ExecutionStatus.PENDING, ExecutionStatus.RUNNING]:
            # TODO: 实现任务取消逻辑
            result.status = ExecutionStatus.FAILED
            result.error = "任务已取消"
            return True

        return False


# 基础智能体接口
class BaseAgent:
    """
    智能体基类

    所有智能体都需要实现这个接口
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化智能体

        Args:
            config: 智能体配置
        """
        self.config = config
        self.name = config.get("name", "Unknown")
        self.endpoint = config.get("endpoint")
        self.timeout = config.get("timeout", 300)

    def supports_task(self, task_type: TaskType) -> bool:
        """
        检查是否支持该任务类型

        Args:
            task_type: 任务类型

        Returns:
            是否支持
        """
        supported_types = self.config.get("task_types", [])
        return task_type.value in supported_types

    def get_timeout(self, task_type: TaskType) -> int:
        """
        获取任务超时时间

        Args:
            task_type: 任务类型

        Returns:
            超时时间（秒）
        """
        # 不同任务类型可能有不同的超时时间
        return self.timeout

    async def execute(self, command: ParsedCommand) -> Dict[str, Any]:
        """
        执行命令（子类必须实现）

        Args:
            command: 解析后的命令

        Returns:
            执行结果字典，包含：
            - summary: 结果摘要
            - details: 详细结果
            - obsidian_file: Obsidian 文件路径（可选）
            - duration: 执行时长（秒）
        """
        raise NotImplementedError("Subclasses must implement execute method")


# 测试代码
class MockAgent(BaseAgent):
    """模拟智能体用于测试"""

    async def execute(self, command: ParsedCommand) -> Dict[str, Any]:
        import time
        import random

        # 模拟执行时间
        duration = random.uniform(1, 3)
        await asyncio.sleep(duration)

        return {
            "summary": f"已完成{command.task_type.value}",
            "details": {
                "query": command.query,
                "result_count": random.randint(10, 100)
            },
            "duration": duration
        }


async def test_command_router():
    """测试命令路由器"""
    from .command_parser import CommandParser
    from .imessage_client import IMessageClient

    # 创建组件
    imessage_client = IMessageClient()
    xiaonuo = MockAgent({
        "name": "小诺",
        "task_types": ["patent_search", "patent_analysis", "info_query"],
        "timeout": 300
    })
    athena = MockAgent({
        "name": "Athena",
        "task_types": ["complex_analysis"],
        "timeout": 600
    })

    router = CommandRouter(imessage_client, xiaonuo, athena)
    parser = CommandParser()

    # 测试命令路由
    test_command = "小诺，帮我检索关于人工智能的专利"
    parsed = parser.parse(test_command)

    result = await router.route_command(parsed, "+8613800138000")

    print(f"\n任务ID: {result.task_id}")
    print(f"状态: {result.status.value}")
    print(f"智能体: {result.agent.value}")
    print(f"摘要: {result.summary}")
    print(f"详情: {result.details}")
    print(f"时长: {result.duration:.2f}秒")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_command_router())
