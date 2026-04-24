"""
Subagent注册表适配器

兼容: core/agents/subagent_registry.py

重定向所有调用到统一注册中心，保持API完全兼容。
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from core.agents.task_tool.model_mapper import ModelMapper
from core.agents.task_tool.models import ModelChoice
from core.registry_center.agent_registry import (
    AgentInfo,
    AgentType,
    UnifiedAgentRegistry,
    get_agent_registry,
)

logger = logging.getLogger(__name__)


# 导出原有类型
__all__ = ["SubagentConfig", "SubagentRegistry", "get_subagent_registry"]


@dataclass
class SubagentConfig:
    """
    子代理配置数据类（兼容层）

    保留原有接口，内部转换为统一AgentInfo。

    Attributes:
        agent_type: 代理类型标识
        display_name: 显示名称
        description: 代理描述
        default_model: 默认模型选择
        capabilities: 代理能力列表
        system_prompt: 系统提示词模板
        allowed_tools: 允许使用的工具列表
        max_concurrent_tasks: 最大并发任务数
        priority: 代理优先级
    """

    agent_type: str
    display_name: str
    description: str
    default_model: ModelChoice
    capabilities: list[str] = field(default_factory=list)
    system_prompt: str = ""
    allowed_tools: list[str] = field(default_factory=list)
    max_concurrent_tasks: int = 3
    priority: int = 5

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "agent_type": self.agent_type,
            "display_name": self.display_name,
            "description": self.description,
            "default_model": self.default_model.value,
            "capabilities": self.capabilities,
            "system_prompt": self.system_prompt,
            "allowed_tools": self.allowed_tools,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "priority": self.priority,
        }

    def to_agent_info(self) -> AgentInfo:
        """转换为统一AgentInfo"""
        return AgentInfo(
            agent_id=self.agent_type,
            agent_type=AgentType.SUBAGENT,
            name=self.display_name,
            description=self.description,
            capabilities=self.capabilities,
            enabled=True,
            priority=self.priority,
            max_concurrent_tasks=self.max_concurrent_tasks,
            system_prompt=self.system_prompt,
            allowed_tools=self.allowed_tools,
            metadata={
                "default_model": self.default_model.value,
                "subagent_config": self.to_dict(),
            },
        )


class SubagentRegistry:
    """
    子代理注册表类（兼容层）

    重定向到UnifiedAgentRegistry，保持原有API完全兼容。

    原模块: core/agents/subagent_registry.py
    """

    # 预定义的4种专利代理类型
    PREDEFINED_AGENTS: dict[str, SubagentConfig] = {}

    def __init__(self):
        """初始化SubagentRegistry"""
        self._impl = get_agent_registry()
        self._model_mapper: ModelMapper = ModelMapper()

        # 注册预定义的代理类型
        self._register_predefined_agents()

        logger.info("✅ SubagentRegistry初始化完成（兼容层）")

    def _register_predefined_agents(self) -> None:
        """注册预定义的4种专利代理类型"""
        # 1. 专利分析师
        self.register_agent(
            SubagentConfig(
                agent_type="patent-analyst",
                display_name="专利分析师",
                description="负责专利技术分析、创新点识别、技术对比分析",
                default_model=ModelChoice.SONNET,
                capabilities=[
                    "专利技术分析",
                    "创新点识别",
                    "技术对比分析",
                    "技术方案评估",
                ],
                system_prompt="""你是一位专业的专利分析师，擅长从技术角度分析专利文件。

你的核心能力：
1. 深入理解技术方案的本质
2. 识别技术创新点
3. 对比分析现有技术
4. 评估技术方案的可行性和价值""",
                allowed_tools=[
                    "code_analyzer",
                    "knowledge_graph",
                    "patent_search",
                    "web_search",
                ],
                max_concurrent_tasks=5,
                priority=1,
            )
        )

        # 2. 专利检索员
        self.register_agent(
            SubagentConfig(
                agent_type="patent-searcher",
                display_name="专利检索员",
                description="负责专利检索、对比文件查找、现有技术分析",
                default_model=ModelChoice.HAIKU,
                capabilities=[
                    "专利检索策略制定",
                    "关键词扩展",
                    "分类号检索",
                    "对比文件筛选",
                ],
                system_prompt="""你是一位专业的专利检索员，擅长制定高效的检索策略。

你的核心能力：
1. 理解专利检索需求
2. 制定检索策略
3. 选择合适的检索工具和数据库
4. 筛选和评估对比文件""",
                allowed_tools=[
                    "patent_search",
                    "web_search",
                    "knowledge_graph",
                ],
                max_concurrent_tasks=10,
                priority=2,
            )
        )

        # 3. 法律研究员
        self.register_agent(
            SubagentConfig(
                agent_type="legal-researcher",
                display_name="法律研究员",
                description="负责法律法规检索、案例分析、法律条文解读",
                default_model=ModelChoice.OPUS,
                capabilities=[
                    "法律法规检索",
                    "案例分析",
                    "法律条文解读",
                    "风险评估",
                ],
                system_prompt="""你是一位资深的法律研究员，精通专利法和相关法律法规。

你的核心能力：
1. 深入理解法律法规
2. 准确解读法律条文
3. 分析典型案例
4. 评估法律风险""",
                allowed_tools=[
                    "legal_search",
                    "knowledge_graph",
                    "web_search",
                    "document_processor",
                ],
                max_concurrent_tasks=3,
                priority=1,
            )
        )

        # 4. 专利撰写员
        self.register_agent(
            SubagentConfig(
                agent_type="patent-drafter",
                display_name="专利撰写员",
                description="负责专利申请文件的撰写和修改",
                default_model=ModelChoice.SONNET,
                capabilities=[
                    "专利申请文件撰写",
                    "权利要求书撰写",
                    "说明书撰写",
                    "专利答复撰写",
                ],
                system_prompt="""你是一位专业的专利撰写员，擅长撰写高质量的专利申请文件。

你的核心能力：
1. 理解技术方案
2. 撰写权利要求书
3. 撰写说明书
4. 撰写专利答复文件""",
                allowed_tools=[
                    "document_processor",
                    "code_analyzer",
                    "knowledge_graph",
                ],
                max_concurrent_tasks=4,
                priority=2,
            )
        )

        logger.info(f"✅ 已注册 {self.get_agent_count()} 个预定义代理类型")

    def register_agent(self, config: SubagentConfig) -> None:
        """
        注册子代理类型

        Args:
            config: 子代理配置

        Raises:
            ValueError: 如果代理类型已存在
        """
        if config.agent_type in self._agents:
            logger.warning(f"⚠️ 代理类型已存在: {config.agent_type}，将被覆盖")

        # 转换为统一AgentInfo并注册
        agent_info = config.to_agent_info()
        self._impl.register_agent(agent_info)

        logger.info(f"✅ 已注册代理类型: {config.display_name} ({config.agent_type})")

    def get_agent(self, agent_type: str) -> Optional[SubagentConfig]:
        """
        获取子代理配置

        Args:
            agent_type: 代理类型标识

        Returns:
            SubagentConfig实例，如果不存在返回None
        """
        agent_info = self._impl.get_agent_info(agent_type)
        if agent_info:
            # 从AgentInfo恢复SubagentConfig
            return SubagentConfig(
                agent_type=agent_info.agent_id,
                display_name=agent_info.name,
                description=agent_info.description,
                default_model=ModelChoice(agent_info.metadata.get("default_model", "sonnet")),
                capabilities=agent_info.capabilities,
                system_prompt=agent_info.system_prompt,
                allowed_tools=agent_info.allowed_tools,
                max_concurrent_tasks=agent_info.max_concurrent_tasks,
                priority=agent_info.priority,
            )
        return None

    def get_available_agents(self, priority: Optional[int] = None) -> list[SubagentConfig]:
        """
        获取可用的子代理类型列表

        Args:
            priority: 可选的优先级过滤

        Returns:
            SubagentConfig列表，按优先级排序
        """
        all_agents = self._impl.list_all()
        subagents = []

        for agent_info in all_agents:
            if isinstance(agent_info, AgentInfo) and agent_info.agent_type == AgentType.SUBAGENT:
                config = SubagentConfig(
                    agent_type=agent_info.agent_id,
                    display_name=agent_info.name,
                    description=agent_info.description,
                    default_model=ModelChoice(agent_info.metadata.get("default_model", "sonnet")),
                    capabilities=agent_info.capabilities,
                    system_prompt=agent_info.system_prompt,
                    allowed_tools=agent_info.allowed_tools,
                    max_concurrent_tasks=agent_info.max_concurrent_tasks,
                    priority=agent_info.priority,
                )

                if priority is None or config.priority == priority:
                    subagents.append(config)

        # 按优先级排序
        subagents.sort(key=lambda x: x.priority)
        return subagents

    def get_agent_config(
        self, agent_type: str, model_mapper: Optional[ModelMapper] = None
    ) -> dict[str, Any]:
        """
        获取子代理的完整配置（包括模型映射）

        Args:
            agent_type: 代理类型标识
            model_mapper: 可选的模型映射器

        Returns:
            完整的配置字典

        Raises:
            ValueError: 如果代理类型不存在
        """
        config = self.get_agent(agent_type)
        if config is None:
            raise ValueError(f"代理类型不存在: {agent_type}")

        # 使用提供的model_mapper或内部实例
        mapper = model_mapper or self._model_mapper

        # 获取模型配置
        model_config = mapper.get_model_config(config.default_model)

        # 构建完整配置
        full_config = config.to_dict()
        full_config["model_config"] = model_config

        return full_config

    def agent_exists(self, agent_type: str) -> bool:
        """
        检查代理类型是否存在

        Args:
            agent_type: 代理类型标识

        Returns:
            如果存在返回True，否则返回False
        """
        return self._impl.exists(agent_type)

    def get_agent_count(self) -> int:
        """
        获取已注册的代理类型数量

        Returns:
            代理类型数量
        """
        return len([a for a in self._impl.list_all() if isinstance(a, AgentInfo) and a.agent_type == AgentType.SUBAGENT])

    def list_agent_types(self) -> list[str]:
        """
        列出所有已注册的代理类型标识

        Returns:
            代理类型标识列表
        """
        all_agents = self._impl.list_all()
        return [a.agent_id for a in all_agents if isinstance(a, AgentInfo) and a.agent_type == AgentType.SUBAGENT]

    def get_agents_by_capability(self, capability: str) -> list[SubagentConfig]:
        """
        根据能力查询代理类型

        Args:
            capability: 能力关键词

        Returns:
            具有该能力的代理类型列表
        """
        agent_infos = self._impl.find_agents_by_capability(capability)
        result = []

        for agent_info in agent_infos:
            if agent_info.agent_type == AgentType.SUBAGENT:
                result.append(
                    SubagentConfig(
                        agent_type=agent_info.agent_id,
                        display_name=agent_info.name,
                        description=agent_info.description,
                        default_model=ModelChoice(agent_info.metadata.get("default_model", "sonnet")),
                        capabilities=agent_info.capabilities,
                        system_prompt=agent_info.system_prompt,
                        allowed_tools=agent_info.allowed_tools,
                        max_concurrent_tasks=agent_info.max_concurrent_tasks,
                        priority=agent_info.priority,
                    )
                )

        return result

    def update_agent_config(self, agent_type: str, **kwargs: Any) -> None:
        """
        更新代理配置

        Args:
            agent_type: 代理类型标识
            **kwargs: 要更新的配置项

        Raises:
            ValueError: 如果代理类型不存在
        """
        agent_info = self._impl.get_agent_info(agent_type)
        if agent_info is None:
            raise ValueError(f"代理类型不存在: {agent_type}")

        # 更新AgentInfo
        for key, value in kwargs.items():
            if hasattr(agent_info, key):
                setattr(agent_info, key, value)
                logger.info(f"✅ 已更新 {agent_type} 的 {key}: {value}")
            else:
                logger.warning(f"⚠️ 未知配置项: {key}")

    @property
    def _agents(self) -> dict[str, SubagentConfig]:
        """内部属性：用于访问已注册的代理（兼容PREDEFINED_AGENTS）"""
        all_agents = self._impl.list_all()
        result = {}

        for agent_info in all_agents:
            if isinstance(agent_info, AgentInfo) and agent_info.agent_type == AgentType.SUBAGENT:
                result[agent_info.agent_id] = SubagentConfig(
                    agent_type=agent_info.agent_id,
                    display_name=agent_info.name,
                    description=agent_info.description,
                    default_model=ModelChoice(agent_info.metadata.get("default_model", "sonnet")),
                    capabilities=agent_info.capabilities,
                    system_prompt=agent_info.system_prompt,
                    allowed_tools=agent_info.allowed_tools,
                    max_concurrent_tasks=agent_info.max_concurrent_tasks,
                    priority=agent_info.priority,
                )

        return result


# 全局单例
_registry_instance: Optional[SubagentRegistry] = None


def get_subagent_registry() -> SubagentRegistry:
    """
    获取全局SubagentRegistry单例

    Returns:
        SubagentRegistry实例
    """
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = SubagentRegistry()
    return _registry_instance
