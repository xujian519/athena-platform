#!/usr/bin/env python3
from __future__ import annotations
"""
多平台提示词适配器

支持 Claude、GPT、GLM、DeepSeek 等不同 LLM 平台的提示词格式转换。
确保同一份提示词能够在不同平台上正确渲染。

支持的平台:
- Claude (Anthropic)
- GPT (OpenAI)
- GLM (智谱)
- DeepSeek

核心特性:
1. 平台特定的系统提示词格式
2. 多轮对话格式转换
3. 工具调用格式适配
4. 思维链/推理格式处理

作者: Athena平台团队
创建_time: 2026-03-19
版本: v1.0.0
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class PlatformType(Enum):
    """支持的平台类型"""

    CLAUDE = "claude"
    GPT = "gpt"
    GLM = "glm"
    DEEPSEEK = "deepseek"
    QWEN = "qwen"


@dataclass
class Message:
    """统一消息格式"""

    role: str  # system, user, assistant, function
    content: str
    name: Optional[str] = None
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: Optional[str] = None

    def to_claude_format(self) -> dict[str, Any]:
        """转换为 Claude 格式"""
        if self.role == "system":
            # Claude 系统提示词单独传递
            return {"type": "system", "text": self.content}
        elif self.role == "user":
            return {"role": "user", "content": self.content}
        elif self.role == "assistant":
            msg: dict[str, Any] = {"role": "assistant", "content": self.content}
            if self.tool_calls:
                msg["content"] = [
                    {"type": "text", "text": self.content},
                ]
                for tool_call in self.tool_calls:
                    msg["content"].append(
                        {
                            "type": "tool_use",
                            "id": tool_call["id"],
                            "name": tool_call["function"]["name"],
                            "input": tool_call["function"]["arguments"],
                        }
                    )
            return msg
        else:  # function / tool
            return {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": self.tool_call_id,
                        "content": self.content,
                    }
                ],
            }

    def to_gpt_format(self) -> dict[str, Any]:
        """转换为 GPT 格式"""
        msg: dict[str, Any] = {"role": self.role, "content": self.content}

        if self.name:
            msg["name"] = self.name
        if self.tool_calls:
            msg["tool_calls"] = self.tool_calls
        if self.tool_call_id:
            msg["tool_call_id"] = self.tool_call_id

        return msg

    def to_glm_format(self) -> dict[str, Any]:
        """转换为 GLM 格式"""
        # GLM 基本兼容 GPT 格式
        return self.to_gpt_format()

    def to_deepseek_format(self) -> dict[str, Any]:
        """转换为 DeepSeek 格式"""
        msg = self.to_gpt_format()

        # DeepSeek Reasoner 特殊处理
        if self.role == "assistant" and hasattr(self, "reasoning_content"):
            msg["reasoning_content"] = getattr(self, "reasoning_content", "")

        return msg

    def to_qwen_format(self) -> dict[str, Any]:
        """转换为 Qwen 格式"""
        # Qwen 基本兼容 GPT 格式
        return self.to_gpt_format()


@dataclass
class PromptConfig:
    """提示词配置"""

    system_prompt: str = ""
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 0.9
    stream: bool = False
    enable_thinking: bool = False  # 启用思维链 (DeepSeek/GPT-o1)
    tools: list[dict[str, Any]] = field(default_factory=list)


class PlatformAdapter:
    """
    多平台适配器

    统一不同 LLM 平台的接口。
    """

    def __init__(self, default_platform: PlatformType = PlatformType.CLAUDE):
        """
        初始化适配器

        Args:
            default_platform: 默认平台类型
        """
        self.default_platform = default_platform
        self.platform_configs: dict[PlatformType, PromptConfig] = {}

        # 为每个平台设置默认配置
        self._init_default_configs()

        logger.info(f"🔀 PlatformAdapter 初始化完成 (默认平台: {default_platform.value})")

    def _init_default_configs(self) -> None:
        """初始化各平台默认配置"""
        # Claude 配置
        self.platform_configs[PlatformType.CLAUDE] = PromptConfig(
            system_prompt="",
            temperature=0.7,
            max_tokens=4096,
            top_p=0.9,
        )

        # GPT 配置
        self.platform_configs[PlatformType.GPT] = PromptConfig(
            system_prompt="",
            temperature=0.7,
            max_tokens=4096,
            top_p=0.9,
        )

        # GLM 配置
        self.platform_configs[PlatformType.GLM] = PromptConfig(
            system_prompt="",
            temperature=0.95,  # GLM 倾向于更高的 temperature
            max_tokens=8192,
            top_p=0.95,
        )

        # DeepSeek 配置
        self.platform_configs[PlatformType.DEEPSEEK] = PromptConfig(
            system_prompt="",
            temperature=0.7,
            max_tokens=4096,
            top_p=0.9,
            enable_thinking=False,  # 需要 reasoner 模型才启用
        )

        # Qwen 配置
        self.platform_configs[PlatformType.QWEN] = PromptConfig(
            system_prompt="",
            temperature=0.85,
            max_tokens=4096,
            top_p=0.9,
        )

    def adapt_messages(
        self,
        messages: list[Message],
        platform: PlatformType | None = None,
    ) -> list[dict[str, Any]]:
        """
        适配消息到目标平台格式

        Args:
            messages: 消息列表
            platform: 目标平台 (None 使用默认)

        Returns:
            list[dict]: 适配后的消息列表
        """
        target_platform = platform or self.default_platform

        converters = {
            PlatformType.CLAUDE: lambda m: m.to_claude_format(),
            PlatformType.GPT: lambda m: m.to_gpt_format(),
            PlatformType.GLM: lambda m: m.to_glm_format(),
            PlatformType.DEEPSEEK: lambda m: m.to_deepseek_format(),
            PlatformType.QWEN: lambda m: m.to_qwen_format(),
        }

        converter = converters.get(target_platform, lambda m: m.to_gpt_format())

        return [converter(msg) for msg in messages]

    def build_request(
        self,
        messages: list[Message],
        config: PromptConfig | None = None,
        platform: PlatformType | None = None,
    ) -> dict[str, Any]:
        """
        构建请求参数

        Args:
            messages: 消息列表
            config: 提示词配置
            platform: 目标平台

        Returns:
            dict: 完整的请求参数
        """
        target_platform = platform or self.default_platform
        use_config = config or self.platform_configs.get(target_platform, PromptConfig())

        adapted_messages = self.adapt_messages(messages, target_platform)

        # 基础请求参数
        request: dict[str, Any] = {
            "messages": adapted_messages,
            "temperature": use_config.temperature,
            "max_tokens": use_config.max_tokens,
            "top_p": use_config.top_p,
        }

        # 平台特定处理
        if target_platform == PlatformType.CLAUDE:
            # Claude 单独传递系统提示词
            system_messages = [msg for msg in adapted_messages if msg.get("type") == "system"]
            if system_messages:
                request["system"] = system_messages[0].get("text", "")
                # 从 messages 中移除系统消息
                request["messages"] = [
                    msg for msg in adapted_messages if msg.get("type") != "system"
                ]

            # 添加工具
            if use_config.tools:
                request["tools"] = self._adapt_tools(use_config.tools, target_platform)

        elif target_platform in (
            PlatformType.GPT,
            PlatformType.GLM,
            PlatformType.QWEN,
        ):
            # OpenAI 风格的系统提示词
            if use_config.system_prompt:
                # 添加系统消息到开头
                request["messages"].insert(
                    0,
                    {"role": "system", "content": use_config.system_prompt},
                )

            # 添加工具
            if use_config.tools:
                request["tools"] = self._adapt_tools(use_config.tools, target_platform)

        elif target_platform == PlatformType.DEEPSEEK:
            # DeepSeek 特殊处理
            if use_config.system_prompt:
                request["messages"].insert(
                    0,
                    {"role": "system", "content": use_config.system_prompt},
                )

            # 思维链模式
            if use_config.enable_thinking:
                request["reasoning_format"] = "raw"

            if use_config.tools:
                request["tools"] = self._adapt_tools(use_config.tools, target_platform)

        return request

    def _adapt_tools(
        self,
        tools: list[dict[str, Any]],
        platform: PlatformType,
    ) -> list[dict[str, Any]]:
        """
        适配工具格式

        Args:
            tools: 工具列表
            platform: 目标平台

        Returns:
            list[dict]: 适配后的工具列表
        """
        adapted_tools = []

        for tool in tools:
            if platform == PlatformType.CLAUDE:
                # Claude 工具格式
                adapted = {
                    "name": tool.get("function", {}).get("name", ""),
                    "description": tool.get("function", {}).get("description", ""),
                    "input_schema": tool.get("function", {}).get("parameters", {}),
                }
            else:
                # OpenAI 风格工具格式
                adapted = tool

            adapted_tools.append(adapted)

        return adapted_tools

    def get_platform_prompt(
        self,
        task_type: str,
        domain: str,
        platform: PlatformType | None = None,
    ) -> str:
        """
        获取平台特定的提示词模板

        Args:
            task_type: 任务类型
            domain: 领域
            platform: 目标平台

        Returns:
            str: 提示词模板
        """
        target_platform = platform or self.default_platform

        # 基础提示词
        base_prompt = f"你是一个专业的{domain}领域的AI助手。\n\n"

        # 平台特定增强
        if target_platform == PlatformType.CLAUDE:
            base_prompt += "请使用清晰的思维链进行推理，并给出详细的解释。\n"
        elif target_platform == PlatformType.DEEPSEEK:
            base_prompt += "请在回答前先进行深度思考，然后给出全面的答案。\n"
        elif target_platform == PlatformType.GLM:
            base_prompt += "请提供全面、专业的分析。\n"

        # 任务特定提示词
        if task_type == "patent_search":
            base_prompt += "\n在专利检索任务中，请注意以下几点：\n"
            base_prompt += "1. 使用专业的检索语法\n"
            base_prompt += "2. 考虑同义词和技术术语变体\n"
            base_prompt += "3. 综合多个数据源的结果\n"
        elif task_type == "legal_analysis":
            base_prompt += "\n在法律分析任务中，请注意以下几点：\n"
            base_prompt += "1. 引用具体的法律条文\n"
            base_prompt += "2. 提供案例参考\n"
            base_prompt += "3. 考虑法律的时效性\n"

        return base_prompt

    def get_statistics(self) -> dict[str, Any]:
        """获取适配器统计信息"""
        return {
            "default_platform": self.default_platform.value,
            "supported_platforms": [p.value for p in PlatformType],
            "configured_platforms": list(self.platform_configs.keys()),
        }


# ========================================
# 全局适配器实例
# ========================================
_global_adapter: PlatformAdapter | None = None


def get_platform_adapter(
    default_platform: PlatformType = PlatformType.CLAUDE,
) -> PlatformAdapter:
    """获取全局平台适配器"""
    global _global_adapter
    if _global_adapter is None:
        _global_adapter = PlatformAdapter(default_platform)
    return _global_adapter


__all__ = [
    "Message",
    "PlatformAdapter",
    "PlatformType",
    "PromptConfig",
    "get_platform_adapter",
]
