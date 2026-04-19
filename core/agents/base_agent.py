from __future__ import annotations
"""
基础智能体类
提供所有智能体的基础功能
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    """基础智能体抽象类"""

    def __init__(
        self,
        name: str,
        role: str,
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ):
        """
        初始化基础智能体

        Args:
            name: 智能体名称
            role: 智能体角色
            model: 使用的模型
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数
        """
        self.name = name
        self.role = role
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.config = kwargs

        # 对话历史
        self.conversation_history: list[dict[str, str]] = []

        # 能力
        self.capabilities: list[str] = []

        # 记忆
        self.memory: dict[str, Any] = {}

    @abstractmethod
    def process(self, input_text: str, **kwargs) -> str:
        """
        处理输入并生成响应

        Args:
            input_text: 输入文本
            **kwargs: 其他参数

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
