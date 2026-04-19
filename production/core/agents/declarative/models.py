from __future__ import annotations
"""
声明式 Agent 定义数据模型

借鉴 kode-agent 的 AgentConfig 设计，使用 dataclass 定义 Agent 的元数据和行为配置。
通过 YAML frontmatter 从 .md 文件加载，无需编写 Python 代码即可定义新 Agent。

Author: Athena Team
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger("agent.declarative.models")

# 允许的模型名称
ALLOWED_MODELS = {"default", "haiku", "sonnet", "opus"}


class AgentSource(Enum):
    """Agent 定义来源"""
    BUILTIN = "builtin"      # 内置 (core/agents/declarative/builtin/)
    USER = "user"            # 用户级 (~/.athena/agents/)
    PROJECT = "project"      # 项目级 (.athena/agents/)
    PLUGIN = "plugin"        # 插件系统预留


class AgentPermissionMode(Enum):
    """Agent 权限模式"""
    DEFAULT = "default"      # 默认权限，与普通 Agent 一致
    READONLY = "readonly"    # 只读模式，禁止写入和修改操作
    FULL = "full"            # 完全权限


@dataclass
class AgentDefinition:
    """
    声明式 Agent 定义

    从 Markdown + YAML frontmatter 文件加载的 Agent 配置。
    前端 yaml 部分定义元数据和配置，正文 markdown 部分定义 system_prompt。

    Example .md file:
        ---
        name: explorer
        description: "代码探索 Agent"
        tools: ["file_read", "search", "grep", "glob"]
        disallowed_tools: ["file_write", "bash"]
        model: haiku
        permission_mode: readonly
        ---

        你是一个代码探索专家，专注于快速定位和理解代码...
    """
    # 基础信息
    name: str
    description: str = ""

    # 工具配置
    tools: list[str] = field(default_factory=list)           # 允许的工具列表（空=允许全部）
    disallowed_tools: list[str] = field(default_factory=list)  # 明确禁止的工具

    # 模型和权限
    model: str = "default"              # 使用的模型：default / haiku / sonnet / opus
    permission_mode: AgentPermissionMode = AgentPermissionMode.DEFAULT

    # 系统提示词（从 .md 正文加载）
    system_prompt: str = ""

    # 元数据
    source: AgentSource = AgentSource.BUILTIN
    filename: str = ""

    # 扩展配置（供前端 yaml 中的自定义字段使用）
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def is_readonly(self) -> bool:
        """是否为只读模式"""
        return self.permission_mode == AgentPermissionMode.READONLY

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "tools": self.tools,
            "disallowed_tools": self.disallowed_tools,
            "model": self.model,
            "permission_mode": self.permission_mode.value,
            "source": self.source.value,
            "filename": self.filename,
            "is_readonly": self.is_readonly,
            "system_prompt_length": len(self.system_prompt),
        }

    @classmethod
    def from_frontmatter(
        cls,
        metadata: dict[str, Any],
        content: str,
        source: AgentSource = AgentSource.BUILTIN,
        filename: str = "",
    ) -> AgentDefinition:
        """
        从 frontmatter 元数据和正文内容构建 AgentDefinition

        Args:
            metadata: YAML frontmatter 解析后的字典
            content: Markdown 正文（作为 system_prompt）
            source: 定义来源
            filename: 源文件名

        Returns:
            AgentDefinition 实例
        """
        # 提取已知字段
        known_keys = {
            "name", "description", "tools", "disallowed_tools",
            "model", "permission_mode",
        }

        name = metadata.get("name", filename.replace(".md", ""))
        description = metadata.get("description", "")
        tools = metadata.get("tools", [])
        disallowed_tools = metadata.get("disallowed_tools", [])
        model = metadata.get("model", "default")

        # Schema 验证: tools 必须是列表
        if not isinstance(tools, list):
            logger.warning(f"Agent '{name}': tools 应为列表，已自动修正")
            tools = []
        if not isinstance(disallowed_tools, list):
            logger.warning(f"Agent '{name}': disallowed_tools 应为列表，已自动修正")
            disallowed_tools = []

        # Schema 验证: model 必须在允许范围内
        if model not in ALLOWED_MODELS:
            logger.warning(
                f"Agent '{name}': 未知模型 '{model}'，回退到 'default'。"
                f"允许值: {ALLOWED_MODELS}"
            )
            model = "default"

        # Schema 验证: name 不能为空
        if not name or not name.strip():
            logger.warning(f"Agent 名称为空，使用文件名 '{filename}'")
            name = filename.replace(".md", "") if filename else "unnamed"

        # 解析权限模式
        perm_raw = metadata.get("permission_mode", "default")
        try:
            permission_mode = AgentPermissionMode(perm_raw)
        except ValueError:
            logger.warning(
                f"Agent '{name}': 未知权限模式 '{perm_raw}'，回退到 'default'"
            )
            permission_mode = AgentPermissionMode.DEFAULT

        # 验证 tools 列表元素都是字符串
        tools = [str(t) for t in tools]
        disallowed_tools = [str(t) for t in disallowed_tools]

        # 未知字段存入 extra
        extra = {k: v for k, v in metadata.items() if k not in known_keys}

        return cls(
            name=name,
            description=description,
            tools=tools,
            disallowed_tools=disallowed_tools,
            model=model,
            permission_mode=permission_mode,
            system_prompt=content.strip(),
            source=source,
            filename=filename,
            extra=extra,
        )
