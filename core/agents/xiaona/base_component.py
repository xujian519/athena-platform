"""
小娜基础组件类

所有小娜专业智能体的基类，定义统一的接口和生命周期。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from enum import Enum
from dataclasses import dataclass
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """智能体状态枚举"""
    IDLE = "idle"           # 空闲
    BUSY = "busy"           # 忙碌
    ERROR = "error"         # 错误
    COMPLETED = "completed" # 完成


@dataclass
class AgentCapability:
    """智能体能力描述"""
    name: str              # 能力名称
    description: str       # 能力描述
    input_types: List[str] # 支持的输入类型
    output_types: List[str] # 输出类型
    estimated_time: float  # 预估执行时间（秒）


@dataclass
class AgentExecutionContext:
    """智能体执行上下文"""
    session_id: str                      # 会话ID
    task_id: str                         # 任务ID
    input_data: Dict[str, Any]          # 输入数据
    config: Dict[str, Any]              # 配置参数
    metadata: Dict[str, Any]            # 元数据
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


@dataclass
class AgentExecutionResult:
    """智能体执行结果"""
    agent_id: str                        # 智能体ID
    status: AgentStatus                  # 执行状态
    output_data: Optional[Dict[str, Any]] # 输出数据
    error_message: Optional[str] = None  # 错误信息
    execution_time: float = 0.0          # 执行时间（秒）
    metadata: Dict[str, Any] = None      # 元数据

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseXiaonaComponent(ABC):
    """
    小娜专业智能体基类

    所有专业智能体都必须继承此类并实现抽象方法。
    提供统一的生命周期管理、能力描述和执行接口。
    """

    def __init__(self, agent_id: str, config: Optional[Dict[str, Any]] = None):
        """
        初始化智能体

        Args:
            agent_id: 智能体唯一标识
            config: 配置参数
        """
        self.agent_id = agent_id
        self.config = config or {}
        self.status = AgentStatus.IDLE
        self._capabilities: List[AgentCapability] = []

        # 初始化日志
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # 子类初始化
        self._initialize()

    @abstractmethod
    def _initialize(self) -> None:
        """
        智能体初始化钩子

        子类应该在此方法中：
        1. 注册能力（self._register_capabilities）
        2. 初始化LLM客户端
        3. 加载提示词
        4. 初始化工具
        """
        pass

    @abstractmethod
    async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
        """
        执行智能体任务

        Args:
            context: 执行上下文

        Returns:
            执行结果
        """
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        获取系统提示词

        Returns:
            系统提示词字符串
        """
        pass

    def _register_capabilities(self, capabilities: List[AgentCapability]) -> None:
        """
        注册智能体能力

        Args:
            capabilities: 能力列表
        """
        self._capabilities = capabilities
        self.logger.info(f"注册 {len(capabilities)} 个能力: {[c.name for c in capabilities]}")

    def get_capabilities(self) -> List[AgentCapability]:
        """
        获取智能体能力列表

        Returns:
            能力列表
        """
        return self._capabilities.copy()

    def has_capability(self, capability_name: str) -> bool:
        """
        检查是否具备某项能力

        Args:
            capability_name: 能力名称

        Returns:
            是否具备该能力
        """
        return any(c.name == capability_name for c in self._capabilities)

    def get_info(self) -> Dict[str, Any]:
        """
        获取智能体信息

        Returns:
            智能体信息字典
        """
        return {
            "agent_id": self.agent_id,
            "agent_type": self.__class__.__name__,
            "status": self.status.value,
            "capabilities": [
                {
                    "name": c.name,
                    "description": c.description,
                    "input_types": c.input_types,
                    "output_types": c.output_types,
                    "estimated_time": c.estimated_time,
                }
                for c in self._capabilities
            ],
            "config": self.config,
        }

    def validate_input(self, context: AgentExecutionContext) -> bool:
        """
        验证输入数据

        Args:
            context: 执行上下文

        Returns:
            验证是否通过
        """
        # 基础验证
        if not context.session_id:
            self.logger.error("缺少session_id")
            return False

        if not context.task_id:
            self.logger.error("缺少task_id")
            return False

        return True

    async def _execute_with_monitoring(
        self,
        context: AgentExecutionContext
    ) -> AgentExecutionResult:
        """
        带监控的执行方法

        Args:
            context: 执行上下文

        Returns:
            执行结果
        """
        import time

        # 更新状态
        self.status = AgentStatus.BUSY
        context.start_time = datetime.now()

        self.logger.info(f"开始执行任务: {context.task_id}")

        try:
            # 执行任务
            result = await self.execute(context)

            # 记录执行时间
            context.end_time = datetime.now()
            execution_time = (context.end_time - context.start_time).total_seconds()
            result.execution_time = execution_time

            # 更新状态
            if result.status == AgentStatus.COMPLETED:
                self.status = AgentStatus.IDLE
                self.logger.info(f"任务完成: {context.task_id}, 耗时: {execution_time:.2f}秒")
            else:
                self.status = AgentStatus.ERROR
                self.logger.error(f"任务失败: {context.task_id}, 错误: {result.error_message}")

            return result

        except Exception as e:
            # 异常处理
            context.end_time = datetime.now()
            execution_time = (context.end_time - context.start_time).total_seconds()

            self.status = AgentStatus.ERROR
            self.logger.exception(f"执行异常: {context.task_id}")

            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.ERROR,
                output_data=None,
                error_message=str(e),
                execution_time=execution_time,
            )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(agent_id='{self.agent_id}', status='{self.status.value}')>"
