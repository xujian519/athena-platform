from __future__ import annotations
"""
基础智能体类
提供所有智能体的基础功能

集成Gateway WebSocket通信:
1. 支持通过Gateway与其他Agent通信
2. 保持向后兼容性
3. 自动连接管理

集成统一记忆系统:
1. 智能体初始化时加载记忆
2. 智能体执行时保存工作历史
3. 智能体学习成果自动更新
4. 项目上下文自动读取
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Gateway客户端导入（可选依赖）
try:
    from core.agents.gateway_client import (
        GatewayClient,
        GatewayClientConfig,
        AgentType as GatewayAgentType,
        Message,
        MessageType
    )
    GATEWAY_AVAILABLE = True
except ImportError:
    GATEWAY_AVAILABLE = False
    GatewayClient = None  # type: ignore
    GatewayClientConfig = None  # type: ignore
    GatewayAgentType = None  # type: ignore
    Message = None  # type: ignore
    MessageType = None  # type: ignore

# 统一记忆系统导入（可选依赖）
try:
    from core.memory.unified_memory_system import (
        UnifiedMemorySystem,
        get_project_memory,
        MemoryType,
        MemoryCategory
    )
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    UnifiedMemorySystem = None  # type: ignore
    get_project_memory = None  # type: ignore
    MemoryType = None  # type: ignore
    MemoryCategory = None  # type: ignore


class BaseAgent(ABC):
    """基础智能体抽象类"""

    def __init__(
        self,
        name: str,
        role: str,
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        enable_gateway: bool = True,
        gateway_url: str = "ws://localhost:8005/ws",
        project_path: Optional[str] = None,
        **_kwargs  # noqa: ARG001,
    ):
        """
        初始化基础智能体

        Args:
            name: 智能体名称
            role: 智能体角色
            model: 使用的模型
            temperature: 温度参数
            max_tokens: 最大token数
            enable_gateway: 是否启用Gateway通信
            gateway_url: Gateway WebSocket URL
            project_path: 项目路径（用于记忆系统）
            **_kwargs  # noqa: ARG001: 其他参数
        """
        self.name = name
        self.role = role
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.config = _kwargs or {}

        # 对话历史
        self.conversation_history: list[dict[str, str]] = []

        # 能力
        self.capabilities: list[str] = []

        # 记忆
        self.memory: dict[str, Any] = {}

        # Gateway通信支持
        self._gateway_client: GatewayClient | None = None
        self._gateway_enabled = enable_gateway and GATEWAY_AVAILABLE
        self._gateway_url = gateway_url

        # 统一记忆系统支持
        self.memory_system: Optional[UnifiedMemorySystem] = None
        self.project_path = project_path
        self._memory_enabled = False

        # 初始化记忆系统
        if project_path and MEMORY_AVAILABLE:
            try:
                self.memory_system = get_project_memory(project_path)
                self._memory_enabled = True
                logger.info(f"记忆系统已启用 - 项目: {project_path}")
            except Exception as e:
                logger.warning(f"记忆系统初始化失败: {e}")

        # 根据名称确定Agent类型
        self._agent_type = self._determine_agent_type()

    def _determine_agent_type(self) -> GatewayAgentType | None:
        """根据名称确定Agent类型"""
        if not GATEWAY_AVAILABLE:
            return None

        name_lower = self.name.lower()
        if "xiaona" in name_lower or "小娜" in name_lower:
            return GatewayAgentType.XIAONA
        elif "xiaonuo" in name_lower or "小诺" in name_lower:
            return GatewayAgentType.XIAONUO
        elif "yunxi" in name_lower or "云熙" in name_lower:
            return GatewayAgentType.YUNXI
        else:
            return GatewayAgentType.UNKNOWN

    @abstractmethod
    def process(self, input_text: str, **_kwargs) -> str:  # noqa: ARG001
        """
        处理输入并生成响应

        Args:
            input_text: 输入文本
            **_kwargs  # noqa: ARG001: 其他参数

        Returns:
            响应文本
        """
        pass

    def add_to_history(self, role: str, content: str) -> None:
        """
        添加到对话历史

        Args:
            role: 角色 (user/assistant/system)
            content: 内容
        """
        self.conversation_history.append({"role": role, "content": content})

    def clear_history(self) -> None:
        """清空对话历史"""
        self.conversation_history.clear()

    def get_history(self) -> list[dict[str, str]]:
        """获取对话历史"""
        return self.conversation_history.copy()

    def remember(self, key: str, value: Any) -> None:
        """
        记住信息

        Args:
            key: 键
            value: 值
        """
        self.memory[key] = value

    def recall(self, key: str) -> Any | None:
        """
        回忆信息

        Args:
            key: 键

        Returns:
            值，如果不存在则返回None
        """
        return self.memory.get(key)

    def forget(self, key: str) -> bool:
        """
        忘记信息

        Args:
            key: 键

        Returns:
            是否成功
        """
        if key in self.memory:
            del self.memory[key]
            return True
        return False

    def add_capability(self, capability: str) -> None:
        """
        添加能力

        Args:
            capability: 能力名称
        """
        if capability not in self.capabilities:
            self.capabilities.append(capability)

    def has_capability(self, capability: str) -> bool:
        """
        检查是否具有某个能力

        Args:
            capability: 能力名称

        Returns:
            是否具有该能力
        """
        return capability in self.capabilities

    def get_capabilities(self) -> list[str]:
        """获取所有能力"""
        return self.capabilities.copy()

    def validate_input(self, input_text: str) -> bool:
        """
        验证输入

        Args:
            input_text: 输入文本

        Returns:
            是否有效
        """
        return bool(input_text and input_text.strip())

    def validate_config(self) -> bool:
        """
        验证配置

        Returns:
            是否有效
        """
        return 0.0 <= self.temperature <= 1.0 and self.max_tokens > 0 and bool(self.name)

    def get_info(self) -> dict[str, Any]:
        """
        获取智能体信息

        Returns:
            信息字典
        """
        return {
            "name": self.name,
            "role": self.role,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "capabilities": self.capabilities,
            "history_length": len(self.conversation_history),
            "memory_size": len(self.memory),
        }

    def __repr__(self) -> str:
        """字符串表示"""
        return f"BaseAgent(name={self.name}, role={self.role})"

    def __str__(self) -> str:
        """字符串表示"""
        return self.__repr__()

    # ==================== Gateway通信方法 ====================

    async def connect_gateway(self) -> bool:
        """
        连接到Gateway

        Returns:
            bool: 连接是否成功
        """
        if not GATEWAY_AVAILABLE:
            logger.warning("⚠️ Gateway客户端不可用")
            return False

        if not self._gateway_enabled:
            logger.info("Gateway通信已禁用")
            return False

        if self._gateway_client is None:
            config = GatewayClientConfig(
                gateway_url=self._gateway_url,
                agent_type=self._agent_type or GatewayAgentType.UNKNOWN,
                agent_id=self.name
            )
            self._gateway_client = GatewayClient(config)

        # 注册消息处理器
        self._gateway_client.register_handler(MessageType.TASK, self._handle_gateway_task)
        self._gateway_client.register_handler(MessageType.QUERY, self._handle_gateway_query)
        self._gateway_client.register_handler(MessageType.NOTIFY, self._handle_gateway_notify)

        return await self._gateway_client.connect()

    async def disconnect_gateway(self) -> None:
        """断开Gateway连接"""
        if self._gateway_client:
            await self._gateway_client.disconnect()

    async def send_to_agent(
        self,
        target_agent: str,
        task_type: str,
        parameters: dict[str, Any] | None = None,
        priority: int = 5
    ) -> Any | None:
        """
        发送消息到其他Agent

        Args:
            target_agent: 目标Agent名称（xiaona/xiaonuo/yunxi）
            task_type: 任务类型
            parameters: 任务参数
            priority: 优先级（0-10）

        Returns:
            响应结果
        """
        if not self._gateway_client or not self._gateway_client.is_connected:
            logger.warning("⚠️ 未连接到Gateway")
            return None

        # 确定目标Agent类型
        agent_type_map = {
            "xiaona": GatewayAgentType.XIAONA,
            "小娜": GatewayAgentType.XIAONA,
            "xiaonuo": GatewayAgentType.XIAONUO,
            "小诺": GatewayAgentType.XIAONUO,
            "yunxi": GatewayAgentType.YUNXI,
            "云熙": GatewayAgentType.YUNXI,
        }

        target_type = agent_type_map.get(target_agent.lower(), GatewayAgentType.UNKNOWN)

        response = await self._gateway_client.send_task(
            task_type=task_type,
            target_agent=target_type,
            parameters=parameters,
            priority=priority
        )

        return response.result if response and response.success else None

    async def broadcast(self, data: dict[str, Any]) -> bool:
        """
        广播消息到所有Agent

        Args:
            data: 广播数据

        Returns:
            bool: 是否成功
        """
        if not self._gateway_client or not self._gateway_client.is_connected:
            logger.warning("⚠️ 未连接到Gateway")
            return False

        return await self._gateway_client.broadcast(data)

    def _handle_gateway_task(self, message: Message) -> None:
        """处理Gateway任务消息"""
        logger.info(f"📨 收到任务: {message.data}")

    def _handle_gateway_query(self, message: Message) -> None:
        """处理Gateway查询消息"""
        logger.info(f"📨 收到查询: {message.data}")

    def _handle_gateway_notify(self, message: Message) -> None:
        """处理Gateway通知消息"""
        logger.info(f"📨 收到通知: {message.data}")

    @property
    def gateway_connected(self) -> bool:
        """是否已连接到Gateway"""
        return self._gateway_client is not None and self._gateway_client.is_connected

    @property
    def gateway_session_id(self) -> str:
        """Gateway会话ID"""
        if self._gateway_client:
            return self._gateway_client.session_id
        return ""

    # ==================== 统一记忆系统方法 ====================

    def load_memory(
        self,
        type: MemoryType,
        category: MemoryCategory,
        key: str
    ) -> Optional[str]:
        """
        加载记忆

        Args:
            type: 记忆类型
            category: 记忆分类
            key: 唯一键

        Returns:
            记忆内容，如果不存在或记忆系统未启用则返回None
        """
        if not self._memory_enabled or not self.memory_system:
            return None

        try:
            return self.memory_system.read(type, category, key)
        except Exception as e:
            logger.error(f"记忆加载失败: {e}")
            return None

    def save_memory(
        self,
        type: MemoryType,
        category: MemoryCategory,
        key: str,
        content: str,
        metadata: Optional[dict[str, Any]] = None
    ) -> bool:
        """
        保存记忆

        Args:
            type: 记忆类型
            category: 记忆分类
            key: 唯一键
            content: Markdown内容
            metadata: 元数据

        Returns:
            是否成功
        """
        if not self._memory_enabled or not self.memory_system:
            logger.debug("记忆系统未启用，跳过保存")
            return False

        try:
            self.memory_system.write(type, category, key, content, metadata)
            return True
        except Exception as e:
            logger.error(f"记忆保存失败: {e}")
            return False

    def save_work_history(
        self,
        task: str,
        result: str,
        status: str = "success"
    ) -> bool:
        """
        保存工作历史

        Args:
            task: 任务描述
            result: 任务结果
            status: 任务状态（success/failed/pending）

        Returns:
            是否成功
        """
        if not self._memory_enabled or not self.memory_system:
            return False

        try:
            self.memory_system.append_work_history(
                agent_name=self.name,
                task=task,
                result=result,
                status=status
            )
            return True
        except Exception as e:
            logger.error(f"工作历史保存失败: {e}")
            return False

    def search_memory(
        self,
        query: str,
        type: Optional[MemoryType] = None,
        category: Optional[MemoryCategory] = None,
        limit: int = 10
    ) -> list:
        """
        搜索记忆

        Args:
            query: 搜索查询
            type: 记忆类型过滤（可选）
            category: 记忆分类过滤（可选）
            limit: 返回数量限制

        Returns:
            匹配的记忆条目列表
        """
        if not self._memory_enabled or not self.memory_system:
            return []

        try:
            return self.memory_system.search(query, type, category, limit)
        except Exception as e:
            logger.error(f"记忆搜索失败: {e}")
            return []

    def get_project_context(self) -> Optional[str]:
        """
        获取项目上下文

        Returns:
            项目上下文内容，如果不存在则返回None
        """
        return self.load_memory(
            MemoryType.PROJECT,
            MemoryCategory.PROJECT_CONTEXT,
            "project_context"
        )

    def get_user_preferences(self) -> Optional[str]:
        """
        获取用户偏好

        Returns:
            用户偏好内容，如果不存在则返回None
        """
        return self.load_memory(
            MemoryType.GLOBAL,
            MemoryCategory.USER_PREFERENCE,
            "user_preferences"
        )

    def update_learning(
        self,
        insights: str,
        metadata: Optional[dict[str, Any]] = None
    ) -> bool:
        """
        更新学习成果（仅学习型智能体使用）

        Args:
            insights: 学习洞察
            metadata: 元数据

        Returns:
            是否成功
        """
        learning_key = f"{self.name}_learning"
        return self.save_memory(
            MemoryType.GLOBAL,
            MemoryCategory.AGENT_LEARNING,
            learning_key,
            insights,
            metadata
        )


class AgentUtils:
    """智能体工具类"""

    @staticmethod
    def format_message(role: str, content: str) -> dict[str, str]:
        """
        格式化消息

        Args:
            role: 角色
            content: 内容

        Returns:
            格式化的消息字典
        """
        return {"role": role, "content": content}

    @staticmethod
    def truncate_text(text: str, max_length: int = 1000) -> str:
        """
        截断文本

        Args:
            text: 文本
            max_length: 最大长度

        Returns:
            截断后的文本
        """
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."

    @staticmethod
    def extract_code(text: str) -> list[str]:
        """
        提取代码块

        Args:
            text: 文本

        Returns:
            代码块列表
        """
        import re

        pattern = r"```(?:python|javascript|json)?\n(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        return matches

    @staticmethod
    def sanitize_input(text: str) -> str:
        """
        清理输入

        Args:
            text: 输入文本

        Returns:
            清理后的文本
        """
        # 移除控制字符
        import re

        text = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", text)
        # 移除多余空白
        text = " ".join(text.split())
        return text.strip()


class AgentResponse:
    """智能体响应类"""

    def __init__(self, content: str, success: bool | None = None, metadata: dict[str, Any] | None | None = None):
        """
        初始化响应

        Args:
            content: 响应内容
            success: 是否成功
            metadata: 元数据
        """
        self.content = content
        self.success = success
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {"content": self.content, "success": self.success, "metadata": self.metadata}

    @classmethod
    def error(cls, error_message: str) -> "AgentResponse":
        """
        创建错误响应

        Args:
            error_message: 错误消息

        Returns:
            错误响应
        """
        return cls(content=error_message, success=False, metadata={"error": True})

    @classmethod
    def success_response(cls, content: str, **metadata) -> "AgentResponse":
        """
        创建成功响应

        Args:
            content: 响应内容
            **metadata: 元数据

        Returns:
            成功响应
        """
        return cls(content=content, success=True, metadata=metadata)
