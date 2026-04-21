from __future__ import annotations
"""
SubagentRegistry - 子代理注册表

支持专利代理类型的管理和配置，包括：
- 专利分析师
- 专利检索员
- 法律研究员
- 专利撰写员

每个代理类型都有特定的模型配置和工具权限配置。
"""

import logging
from dataclasses import dataclass, field
from typing import Any

from core.agents.task_tool.model_mapper import ModelMapper
from core.agents.task_tool.models import ModelChoice

logger = logging.getLogger(__name__)


@dataclass
class SubagentConfig:
    """子代理配置数据类

    Attributes:
        agent_type: 代理类型标识
        display_name: 显示名称
        description: 代理描述
        default_model: 默认模型选择
        capabilities: 代理能力列表
        system_prompt: 系统提示词模板
        allowed_tools: 允许使用的工具列表（支持通配符*）
        max_concurrent_tasks: 最大并发任务数
        priority: 代理优先级（1-10，数字越小优先级越高）
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


class SubagentRegistry:
    """子代理注册表类

    管理所有子代理类型的配置和注册信息。

    功能：
    1. 注册新的子代理类型
    2. 获取子代理配置
    3. 查询可用的子代理类型
    4. 集成ModelMapper进行模型映射

    Examples:
        >>> registry = SubagentRegistry()
        >>> config = registry.get_agent("patent-analyst")
        >>> print(config.display_name)
        '专利分析师'
    """

    # 预定义的4种专利代理类型
    PREDEFINED_AGENTS: dict[str, SubagentConfig] = {}

    def __init__(self):
        """初始化SubagentRegistry"""
        self._agents: dict[str, SubagentConfig] = {}
        self._model_mapper: ModelMapper = ModelMapper()

        # 注册预定义的代理类型
        self._register_predefined_agents()

        logger.info("✅ SubagentRegistry初始化完成")

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
4. 评估技术方案的可行性和价值

分析框架：
- 技术领域：明确专利所属的技术领域
- 技术问题：分析专利要解决的技术问题
- 技术方案：详细说明专利的技术方案
- 创新点：识别专利的核心创新点
- 技术效果：评估技术方案带来的有益效果
- 对比分析：与现有技术进行对比

分析原则：
- 基于事实，客观中立
- 关注技术本质，而非表面表述
- 识别真正的创新，避免过度解读
- 结合技术背景和市场环境评估价值""",
                allowed_tools=[
                    "code_analyzer",
                    "knowledge_graph",
                    "patent_search",
                    "web_search",
                ],
                max_concurrent_tasks=5,
                priority=1,  # 高优先级
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
4. 筛选和评估对比文件

检索流程：
1. 需求分析：明确检索目标和技术领域
2. 关键词提取：从技术方案中提取关键技术特征
3. 关键词扩展：使用同义词、上下位词、缩写等扩展关键词
4. 分类号选择：选择合适的IPC/CPC分类号
5. 检索式构建：组合关键词和分类号构建检索式
6. 结果筛选：根据相关性筛选对比文件
7. 对比分析：分析对比文件与目标专利的异同

检索原则：
- 全面覆盖，避免遗漏
- 精准定位，提高效率
- 多角度检索，交叉验证
- 及时调整，优化策略""",
                allowed_tools=[
                    "patent_search",
                    "web_search",
                    "knowledge_graph",
                ],
                max_concurrent_tasks=10,  # 可以处理更多并发任务
                priority=2,
            )
        )

        # 3. 法律研究员
        self.register_agent(
            SubagentConfig(
                agent_type="legal-researcher",
                display_name="法律研究员",
                description="负责法律法规检索、案例分析、法律条文解读",
                default_model=ModelChoice.OPUS,  # 需要深度分析
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
4. 评估法律风险

研究框架：
1. 法律条文分析：
   - 条文的立法目的
   - 条文的适用范围
   - 条文的适用条件
   - 条文的法律后果

2. 案例分析：
   - 案例的基本事实
   - 争议焦点
   - 法院观点
   - 判决理由
   - 判决结果

3. 风险评估：
   - 识别潜在的法律风险
   - 评估风险发生的可能性
   - 评估风险的影响程度
   - 提出风险应对建议

研究原则：
- 严格依据法律条文
- 参考权威案例
- 保持客观中立
- 关注最新法律动态""",
                allowed_tools=[
                    "legal_search",
                    "knowledge_graph",
                    "web_search",
                    "document_processor",
                ],
                max_concurrent_tasks=3,
                priority=1,  # 高优先级，需要深度分析
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
4. 撰写专利答复文件

撰写原则：
1. 权利要求书撰写：
   - 清晰、准确地限定保护范围
   - 采用"包括...的..."结构
   - 避免使用模糊词汇
   - 合理设置从属权利要求

2. 说明书撰写：
   - 充分公开技术方案
   - 详细描述实施例
   - 提供技术效果
   - 满足说明书支持要求

3. 答复文件撰写：
   - 有针对性地答复审查意见
   - 修改权利要求
   - 陈述理由和证据
   - 保持礼貌和专业

撰写标准：
- 语言准确、简洁
- 逻辑清晰、严谨
- 符合专利法规要求
- 便于审查员理解""",
                allowed_tools=[
                    "document_processor",
                    "code_analyzer",
                    "knowledge_graph",
                ],
                max_concurrent_tasks=4,
                priority=2,
            )
        )

        logger.info(f"✅ 已注册 {len(self._agents)} 个预定义代理类型")

    def register_agent(self, config: SubagentConfig) -> None:
        """注册子代理类型

        Args:
            config: 子代理配置

        Raises:
            ValueError: 如果代理类型已存在

        Examples:
            >>> registry = SubagentRegistry()
            >>> config = SubagentConfig(
            ...     agent_type="custom-analyst",
            ...     display_name="自定义分析师",
            ...     description="自定义分析代理",
            ...     default_model=ModelChoice.SONNET
            ... )
            >>> registry.register_agent(config)
        """
        if config.agent_type in self._agents:
            logger.warning(f"⚠️ 代理类型已存在: {config.agent_type}，将被覆盖")

        self._agents[config.agent_type] = config
        logger.info(f"✅ 已注册代理类型: {config.display_name} ({config.agent_type})")

    def get_agent(self, agent_type: str) -> SubagentConfig | None:
        """获取子代理配置

        Args:
            agent_type: 代理类型标识

        Returns:
            SubagentConfig实例，如果不存在返回None

        Examples:
            >>> registry = SubagentRegistry()
            >>> config = registry.get_agent("patent-analyst")
            >>> print(config.display_name)
            '专利分析师'
        """
        return self._agents.get(agent_type)

    def get_available_agents(self, priority: int | None = None) -> list[SubagentConfig]:
        """获取可用的子代理类型列表

        Args:
            priority: 可选的优先级过滤，只返回指定优先级的代理

        Returns:
            SubagentConfig列表，按优先级排序

        Examples:
            >>> registry = SubagentRegistry()
            >>> agents = registry.get_available_agents()
            >>> for agent in agents:
            ...     print(agent.display_name)
        """
        agents = list(self._agents.values())

        if priority is not None:
            agents = [a for a in agents if a.priority == priority]

        # 按优先级排序（数字越小优先级越高）
        agents.sort(key=lambda x: x.priority)

        return agents

    def get_agent_config(
        self, agent_type: str, model_mapper: ModelMapper | None = None
    ) -> dict[str, Any]:
        """获取子代理的完整配置（包括模型映射）

        Args:
            agent_type: 代理类型标识
            model_mapper: 可选的模型映射器，如果不提供则使用内部实例

        Returns:
            完整的配置字典

        Raises:
            ValueError: 如果代理类型不存在

        Examples:
            >>> registry = SubagentRegistry()
            >>> config = registry.get_agent_config("patent-analyst")
            >>> print(config['display_name'])
            '专利分析师'
            >>> print(config['model_config'])
            {'name': 'task', 'temperature': 0.5, ...}
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
        """检查代理类型是否存在

        Args:
            agent_type: 代理类型标识

        Returns:
            如果存在返回True，否则返回False

        Examples:
            >>> registry = SubagentRegistry()
            >>> registry.agent_exists("patent-analyst")
            True
            >>> registry.agent_exists("unknown-agent")
            False
        """
        return agent_type in self._agents

    def get_agent_count(self) -> int:
        """获取已注册的代理类型数量

        Returns:
            代理类型数量
        """
        return len(self._agents)

    def list_agent_types(self) -> list[str]:
        """列出所有已注册的代理类型标识

        Returns:
            代理类型标识列表
        """
        return list(self._agents.keys())

    def get_agents_by_capability(self, capability: str) -> list[SubagentConfig]:
        """根据能力查询代理类型

        Args:
            capability: 能力关键词

        Returns:
            具有该能力的代理类型列表

        Examples:
            >>> registry = SubagentRegistry()
            >>> agents = registry.get_agents_by_capability("专利检索")
            >>> for agent in agents:
            ...     print(agent.display_name)
        """
        return [agent for agent in self._agents.values() if capability in agent.capabilities]

    def update_agent_config(self, agent_type: str, **_kwargs  # noqa: ARG001) -> None:
        """更新代理配置

        Args:
            agent_type: 代理类型标识
            **_kwargs  # noqa: ARG001: 要更新的配置项

        Raises:
            ValueError: 如果代理类型不存在

        Examples:
            >>> registry = SubagentRegistry()
            >>> registry.update_agent_config(
            ...     "patent-analyst",
            ...     max_concurrent_tasks=10
            ... )
        """
        config = self.get_agent(agent_type)
        if config is None:
            raise ValueError(f"代理类型不存在: {agent_type}")

        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
                logger.info(f"✅ 已更新 {agent_type} 的 {key}: {value}")
            else:
                logger.warning(f"⚠️ 未知配置项: {key}")


# 全局单例
_registry_instance: SubagentRegistry | None = None


def get_subagent_registry() -> SubagentRegistry:
    """获取全局SubagentRegistry单例

    Returns:
        SubagentRegistry实例
    """
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = SubagentRegistry()
    return _registry_instance


__all__ = [
    "SubagentConfig",
    "SubagentRegistry",
    "get_subagent_registry",
]
