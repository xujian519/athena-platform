from __future__ import annotations
"""
ForkContextBuilder - Fork上下文构建器

支持子代理的上下文隔离和系统提示词定制。

核心功能:
1. 构建独立的Fork上下文
2. 合并系统提示词
3. 支持上下文序列化和反序列化
4. 上下文隔离和合并

作者: Athena平台团队
创建时间: 2026-04-05
版本: v1.0.0
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ForkContext:
    """Fork上下文数据类

    用于子代理的上下文隔离和定制。

    Attributes:
        fork_context_messages: 父代理的对话历史
        prompt_messages: 当前任务的prompt消息
        context_variables: 上下文变量字典
        system_prompt: 系统提示词列表
    """

    fork_context_messages: list[dict[str, Any]] = field(default_factory=list)
    prompt_messages: list[dict[str, Any]] = field(default_factory=list)
    context_variables: dict[str, Any] = field(default_factory=dict)
    system_prompt: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典

        Returns:
            序列化的字典
        """
        return asdict(self)

    def to_json(self) -> str:
        """转换为JSON字符串

        Returns:
            JSON格式的字符串
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ForkContext":
        """从字典创建ForkContext

        Args:
            data: 字典数据

        Returns:
            ForkContext实例
        """
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> "ForkContext":
        """从JSON字符串创建ForkContext

        Args:
            json_str: JSON字符串

        Returns:
            ForkContext实例
        """
        data = json.loads(json_str)
        return cls.from_dict(data)


class ForkContextBuilder:
    """Fork上下文构建器

    负责构建和管理子代理的Fork上下文。

    Examples:
        >>> builder = ForkContextBuilder()
        >>> context = builder.build(
        ...     prompt="分析这个专利",
        ...     context={"parent_messages": []}
        ... )
        >>> print(context.system_prompt[0]["content"])
    """

    def __init__(self, base_system_prompt: str = ""):
        """初始化ForkContextBuilder

        Args:
            base_system_prompt: 基础系统提示词
        """
        self.base_system_prompt = base_system_prompt
        logger.debug("🔧 ForkContextBuilder初始化完成")

    def build(
        self,
        prompt: str,
        context: Optional[dict[str, Any]] = None,
        tool_use_id: Optional[str] = None,
    ) -> ForkContext:
        """构建Fork上下文

        Args:
            prompt: 任务提示词
            context: 上下文信息，包含parent_messages等
            tool_use_id: 工具使用ID

        Returns:
            ForkContext: 构建的Fork上下文
        """
        context = context or {}

        # 从context中提取信息
        parent_messages = context.get("parent_messages", [])
        agent_system_prompt = context.get("system_prompt", "")

        # 构建各个组件
        fork_context_messages = self._build_fork_context_messages(parent_messages)
        prompt_messages = self.build_prompt_messages(prompt, tool_use_id)
        context_variables = self._build_context_variables(context)
        system_prompt = self.build_system_prompt(agent_system_prompt, self.base_system_prompt)

        # 创建ForkContext
        fork_context = ForkContext(
            fork_context_messages=fork_context_messages,
            prompt_messages=prompt_messages,
            context_variables=context_variables,
            system_prompt=system_prompt,
        )

        logger.debug(f"✅ Fork上下文构建完成 (parent_messages: {len(parent_messages)})")

        return fork_context

    def build_prompt_messages(
        self,
        prompt: str,
        tool_use_id: Optional[str] = None,
    ) -> list[dict[str, str]]:
        """构建prompt消息

        Args:
            prompt: 任务提示词
            tool_use_id: 工具使用ID (可选)

        Returns:
            格式化的消息列表
        """
        messages = []

        # 添加用户消息
        if prompt:
            user_message = {"role": "user", "content": prompt}
            messages.append(user_message)

        logger.debug(f"📝 构建prompt消息: {len(messages)} 条")

        return messages

    def build_system_prompt(
        self,
        agent_system_prompt: str,
        base_system_prompt: str = "",
    ) -> list[dict[str, str]]:
        """构建系统提示词

        Args:
            agent_system_prompt: 代理特定的系统提示词
            base_system_prompt: 基础系统提示词

        Returns:
            合并后的系统提示词列表
        """
        system_prompt_list = []

        # 添加基础系统提示词
        if base_system_prompt:
            base_message = {"role": "system", "content": base_system_prompt}
            system_prompt_list.append(base_message)

        # 添加代理特定的系统提示词
        if agent_system_prompt:
            agent_message = {"role": "system", "content": agent_system_prompt}
            system_prompt_list.append(agent_message)

        logger.debug(f"🎯 构建系统提示词: {len(system_prompt_list)} 条")

        return system_prompt_list

    def apply_fork_context(
        self,
        messages: list[dict[str, Any]],
        fork_context: ForkContext,
        include_parent_messages: bool = True,
    ) -> list[dict[str, Any]]:
        """应用Fork上下文到消息列表

        Args:
            messages: 原始消息列表
            fork_context: Fork上下文
            include_parent_messages: 是否包含父代理消息

        Returns:
            应用上下文后的消息列表
        """
        result = []

        # 添加系统提示词
        if fork_context.system_prompt:
            result.extend(fork_context.system_prompt)

        # 添加父代理消息 (如果需要)
        if include_parent_messages and fork_context.fork_context_messages:
            result.extend(fork_context.fork_context_messages)

        # 添加当前消息
        result.extend(messages)

        logger.debug(f"🔄 应用Fork上下文: {len(messages)} -> {len(result)} 条消息")

        return result

    def _build_fork_context_messages(
        self,
        parent_messages: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """构建父代理上下文消息

        Args:
            parent_messages: 父代理的对话历史

        Returns:
            父代理上下文消息列表
        """
        # 深拷贝父代理消息，避免污染
        fork_context_messages = [msg.copy() for msg in parent_messages]

        logger.debug(f"👥 构建父代理上下文: {len(fork_context_messages)} 条")

        return fork_context_messages

    def _build_context_variables(
        self,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """构建上下文变量

        Args:
            context: 原始上下文字典

        Returns:
            上下文变量字典
        """
        context_variables = {}

        # 从context中提取变量
        variable_keys = [
            "tool_use_id",
            "message_log_name",
            "fork_number",
            "agent_type",
            "task_id",
        ]

        for key in variable_keys:
            if key in context:
                context_variables[key] = context[key]

        logger.debug(f"📦 构建上下文变量: {len(context_variables)} 个")

        return context_variables

    def merge_system_prompts(
        self,
        prompt1: str,
        prompt2: str,
    ) -> str:
        """合并两个系统提示词

        Args:
            prompt1: 第一个提示词
            prompt2: 第二个提示词

        Returns:
            合并后的提示词
        """
        if not prompt1:
            return prompt2
        if not prompt2:
            return prompt1

        # 合并策略：用换行符连接
        merged = f"{prompt1}\n\n{prompt2}"

        logger.debug("🔀 合并系统提示词")

        return merged

    def validate_fork_context(
        self,
        fork_context: ForkContext,
    ) -> bool:
        """验证Fork上下文

        Args:
            fork_context: 要验证的Fork上下文

        Returns:
            是否验证通过
        """
        try:
            # 检查必需字段
            if not isinstance(fork_context, ForkContext):
                logger.error("❌ Fork上下文类型错误")
                return False

            # 检查消息格式
            all_messages = (
                fork_context.fork_context_messages
                + fork_context.prompt_messages
                + fork_context.system_prompt
            )

            for msg in all_messages:
                if not isinstance(msg, dict):
                    logger.error("❌ 消息格式错误: 不是字典")
                    return False

                if "role" not in msg:
                    logger.error("❌ 消息缺少role字段")
                    return False

                if "content" not in msg:
                    logger.error("❌ 消息缺少content字段")
                    return False

            logger.debug("✅ Fork上下文验证通过")
            return True

        except Exception as e:
            logger.error(f"❌ Fork上下文验证失败: {e}")
            return False


__all__ = [
    "ForkContext",
    "ForkContextBuilder",
]
