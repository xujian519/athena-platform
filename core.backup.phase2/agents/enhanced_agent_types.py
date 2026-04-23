#!/usr/bin/env python3
from __future__ import annotations
"""
增强版智能体类型定义
Enhanced Agent Type Definitions

创建时间: 2026-02-20
版本: 3.0.0
作者: Athena AI系统

此模块定义了Athena工作平台中所有智能体类型、能力和相关配置。
包含原有3个核心智能体和新增8个专业智能体的完整定义。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any


class AgentType(Enum):
    """增强版智能体类型枚举"""

    # 原有核心智能体
    XIAONA_LEGAL = "xiaona_legal"  # 小娜·法律专家
    XIAONUO_COORDINATOR = "xiaonuo_coordinator"  # 小诺·调度官

    # 原有专业智能体
    SEARCH_AGENT = "search_agent"  # 专利检索专家
    ANALYSIS_AGENT = "analysis_agent"  # 技术分析专家
    CREATIVE_AGENT = "creative_agent"  # 创意思维专家

    # 新增专业智能体
    CREATIVE_ANALYSIS = "creative_analysis"  # 创造性分析专家
    NOVELTY_ANALYSIS = "novelty_analysis"  # 新颖性分析专家
    ARTICLE26_ANALYSIS = "article26_analysis"  # 专利法26条专家
    PATENT_REVIEWER = "patent_reviewer"  # 专利审查员专家
    PATENT_ATTORNEY = "patent_attorney"  # 专利律师专家
    IP_CONSULTANT = "ip_consultant"  # IP顾问专家
    DOCUMENTATION = "documentation"  # 文档专家
    TRANSLATION = "translation"  # 翻译专家


class AgentCapability(Enum):
    """智能体能力枚举"""

    # 核心能力
    COGNITIVE_PROCESSING = "cognitive_processing"
    LEGAL_REASONING = "legal_reasoning"
    TECHNICAL_ANALYSIS = "technical_analysis"
    COORDINATION = "coordination"
    MEMORY_MANAGEMENT = "memory_management"
    COMMUNICATION = "communication"
    LEARNING = "learning"

    # 专业能力
    PATENT_SEARCH = "patent_search"
    CREATIVITY_ASSESSMENT = "creativity_assessment"
    NOVELTY_EVALUATION = "novelty_evaluation"
    LEGAL_COMPLIANCE = "legal_compliance"
    PATENT_REVIEW = "patent_review"
    INFRINGEMENT_ANALYSIS = "infringement_analysis"
    IP_STRATEGY = "ip_strategy"
    DOCUMENT_GENERATION = "document_generation"
    MULTILINGUAL_TRANSLATION = "multilingual_translation"
    CLAIM_ANALYSIS = "claim_analysis"
    PRIOR_ART_SEARCH = "prior_art_search"
    TECH_EVALUATION = "tech_evaluation"
    CASE_MATCHING = "case_matching"
    STRATEGIC_PLANNING = "strategic_planning"
    VALUATION = "valuation"
    FORMATTING = "formatting"
    CHART_GENERATION = "chart_generation"
    TERMINOLOGY_NORMALIZATION = "terminology_normalization"


class AgentStatus(Enum):
    """智能体状态枚举"""

    ACTIVE = "active"  # 活跃状态
    IDLE = "idle"  # 空闲状态
    BUSY = "busy"  # 忙碌状态
    MAINTENANCE = "maintenance"  # 维护状态
    ERROR = "error"  # 错误状态
    OFFLINE = "offline"  # 离线状态


class TaskPriority(Enum):
    """任务优先级枚举"""

    CRITICAL = "critical"  # 关键任务
    HIGH = "high"  # 高优先级
    NORMAL = "normal"  # 普通优先级
    LOW = "low"  # 低优先级
    BACKGROUND = "background"  # 后台任务


# 智能体能力映射表
AGENT_CAPABILITIES = {
    AgentType.XIAONA_LEGAL: [
        AgentCapability.LEGAL_REASONING,
        AgentCapability.COORDINATION,
        AgentCapability.COMMUNICATION,
        AgentCapability.LEGAL_COMPLIANCE,
    ],
    AgentType.XIAONUO_COORDINATOR: [
        AgentCapability.COORDINATION,
        AgentCapability.COMMUNICATION,
        AgentCapability.MEMORY_MANAGEMENT,
        AgentCapability.LEARNING,
    ],
    AgentType.SEARCH_AGENT: [
        AgentCapability.PATENT_SEARCH,
        AgentCapability.PRIOR_ART_SEARCH,
        AgentCapability.TECHNICAL_ANALYSIS,
    ],
    AgentType.ANALYSIS_AGENT: [
        AgentCapability.TECHNICAL_ANALYSIS,
        AgentCapability.TECH_EVALUATION,
        AgentCapability.COGNITIVE_PROCESSING,
    ],
    AgentType.CREATIVE_AGENT: [
        AgentCapability.CREATIVITY_ASSESSMENT,
        AgentCapability.COGNITIVE_PROCESSING,
        AgentCapability.LEARNING,
    ],
    AgentType.CREATIVE_ANALYSIS: [
        AgentCapability.CREATIVITY_ASSESSMENT,
        AgentCapability.TECHNICAL_ANALYSIS,
        AgentCapability.TECH_EVALUATION,
        AgentCapability.PRIOR_ART_SEARCH,
    ],
    AgentType.NOVELTY_ANALYSIS: [
        AgentCapability.NOVELTY_EVALUATION,
        AgentCapability.PATENT_SEARCH,
        AgentCapability.PRIOR_ART_SEARCH,
        AgentCapability.TECHNICAL_ANALYSIS,
    ],
    AgentType.ARTICLE26_ANALYSIS: [
        AgentCapability.LEGAL_COMPLIANCE,
        AgentCapability.LEGAL_REASONING,
        AgentCapability.DOCUMENT_GENERATION,
        AgentCapability.CASE_MATCHING,
    ],
    AgentType.PATENT_REVIEWER: [
        AgentCapability.PATENT_REVIEW,
        AgentCapability.LEGAL_COMPLIANCE,
        AgentCapability.CLAIM_ANALYSIS,
        AgentCapability.TECH_EVALUATION,
    ],
    AgentType.PATENT_ATTORNEY: [
        AgentCapability.LEGAL_REASONING,
        AgentCapability.INFRINGEMENT_ANALYSIS,
        AgentCapability.IP_STRATEGY,
        AgentCapability.CASE_MATCHING,
    ],
    AgentType.IP_CONSULTANT: [
        AgentCapability.IP_STRATEGY,
        AgentCapability.STRATEGIC_PLANNING,
        AgentCapability.VALUATION,
        AgentCapability.TECHNICAL_ANALYSIS,
    ],
    AgentType.DOCUMENTATION: [
        AgentCapability.DOCUMENT_GENERATION,
        AgentCapability.FORMATTING,
        AgentCapability.CHART_GENERATION,
        AgentCapability.TECHNICAL_ANALYSIS,
    ],
    AgentType.TRANSLATION: [
        AgentCapability.MULTILINGUAL_TRANSLATION,
        AgentCapability.TERMINOLOGY_NORMALIZATION,
        AgentCapability.TECHNICAL_ANALYSIS,
        AgentCapability.DOCUMENT_GENERATION,
    ],
}


@dataclass
class AgentConfig:
    """智能体配置数据类"""

    agent_type: AgentType
    name: str
    description: str
    capabilities: list[AgentCapability]
    model_config: dict[str, Any]
    max_concurrent_tasks: int = 5
    timeout_seconds: int = 300
    memory_limit_mb: int = 2048
    priority_level: TaskPriority = TaskPriority.NORMAL
    auto_scale: bool = True
    health_check_interval: int = 60


# 智能体配置映射表
AGENT_CONFIGS = {
    AgentType.XIAONA_LEGAL: AgentConfig(
        agent_type=AgentType.XIAONA_LEGAL,
        name="小娜·天秤女神",
        description="专利法律专家，提供专业法律分析和建议",
        capabilities=AGENT_CAPABILITIES[AgentType.XIAONA_LEGAL],
        model_config={
            "language_model": "legal-expert-gpt-v4",
            "knowledge_base": "patent-law-db",
            "specialization": "patent_law",
        },
        max_concurrent_tasks=10,
        priority_level=TaskPriority.HIGH,
    ),
    AgentType.XIAONUO_COORDINATOR: AgentConfig(
        agent_type=AgentType.XIAONUO_COORDINATOR,
        name="小诺·双鱼座",
        description="平台总调度官，协调所有智能体的工作",
        capabilities=AGENT_CAPABILITIES[AgentType.XIAONUO_COORDINATOR],
        model_config={
            "language_model": "coordination-gpt-v3",
            "orchestration_engine": "multi-agent-orchestrator",
            "specialization": "platform_coordination",
        },
        max_concurrent_tasks=20,
        priority_level=TaskPriority.CRITICAL,
    ),
    AgentType.CREATIVE_ANALYSIS: AgentConfig(
        agent_type=AgentType.CREATIVE_ANALYSIS,
        name="创造性分析专家",
        description="专门进行专利创造性评估和技术突破点分析",
        capabilities=AGENT_CAPABILITIES[AgentType.CREATIVE_ANALYSIS],
        model_config={
            "language_model": "patent-creative-bert-v3",
            "knowledge_graph": "patent-technology-graph",
            "specialization": "creativity_assessment",
        },
        max_concurrent_tasks=6,
        timeout_seconds=180,  # 3分钟
    ),
    AgentType.NOVELTY_ANALYSIS: AgentConfig(
        agent_type=AgentType.NOVELTY_ANALYSIS,
        name="新颖性分析专家",
        description="专门进行新颖性分析和现有技术对比",
        capabilities=AGENT_CAPABILITIES[AgentType.NOVELTY_ANALYSIS],
        model_config={
            "language_model": "bert-base-multilingual-cased",
            "vector_similarity_model": "patent-novelty-detector",
            "database_connections": ["uspto", "epo", "jpo", "cnipa"],
            "specialization": "novelty_evaluation",
        },
        max_concurrent_tasks=4,
        timeout_seconds=120,  # 2分钟
    ),
    AgentType.ARTICLE26_ANALYSIS: AgentConfig(
        agent_type=AgentType.ARTICLE26_ANALYSIS,
        name="专利法26条专家",
        description="专门进行专利法第26条合规性检查",
        capabilities=AGENT_CAPABILITIES[AgentType.ARTICLE26_ANALYSIS],
        model_config={
            "rule_engine": "patent-law-rule-engine-v2",
            "case_database": "patent-examination-cases",
            "compliance_checker": "article26-compliance-detector",
            "specialization": "legal_compliance",
        },
        max_concurrent_tasks=8,
        timeout_seconds=60,  # 1分钟
    ),
    AgentType.PATENT_REVIEWER: AgentConfig(
        agent_type=AgentType.PATENT_REVIEWER,
        name="专利审查员专家",
        description="模拟专利审查员进行专业审查",
        capabilities=AGENT_CAPABILITIES[AgentType.PATENT_REVIEWER],
        model_config={
            "review_workflow": "patent-review-workflow-engine",
            "scope_analyzer": "protection-scope-analyzer",
            "grantability_model": "grantability-prediction-model",
            "specialization": "patent_examination",
        },
        max_concurrent_tasks=5,
        timeout_seconds=240,  # 4分钟
    ),
    AgentType.PATENT_ATTORNEY: AgentConfig(
        agent_type=AgentType.PATENT_ATTORNEY,
        name="专利律师专家",
        description="提供专利侵权分析和法律意见",
        capabilities=AGENT_CAPABILITIES[AgentType.PATENT_ATTORNEY],
        model_config={
            "infringement_analyzer": "patent-infringement-analyzer",
            "legal_reasoning_engine": "legal-reasoning-engine",
            "opinion_generator": "legal-opinion-generator",
            "case_law_database": "patent-litigation-cases",
            "specialization": "patent_litigation",
        },
        max_concurrent_tasks=4,
        timeout_seconds=300,  # 5分钟
    ),
    AgentType.IP_CONSULTANT: AgentConfig(
        agent_type=AgentType.IP_CONSULTANT,
        name="IP顾问专家",
        description="提供综合性知识产权咨询服务",
        capabilities=AGENT_CAPABILITIES[AgentType.IP_CONSULTANT],
        model_config={
            "multimodal_kg": "ip-multimodal-knowledge-graph",
            "strategy_planner": "ip-strategy-planner",
            "valuation_model": "ip-valuation-model",
            "specialization": "ip_consulting",
        },
        max_concurrent_tasks=3,
        timeout_seconds=600,  # 10分钟
    ),
    AgentType.DOCUMENTATION: AgentConfig(
        agent_type=AgentType.DOCUMENTATION,
        name="文档专家",
        description="专业文档生成、排版和格式化处理",
        capabilities=AGENT_CAPABILITIES[AgentType.DOCUMENTATION],
        model_config={
            "template_engine": "professional-template-engine",
            "chart_generator": "intelligent-chart-generator",
            "format_converter": "multi-format-converter",
            "specialization": "document_processing",
        },
        max_concurrent_tasks=10,
        timeout_seconds=180,  # 3分钟
    ),
    AgentType.TRANSLATION: AgentConfig(
        agent_type=AgentType.TRANSLATION,
        name="翻译专家",
        description="多语言专利文档翻译和术语标准化",
        capabilities=AGENT_CAPABILITIES[AgentType.TRANSLATION],
        model_config={
            "translation_model": "patent-specialized-gpt-v4",
            "terminology_db": "patent-terminology-database",
            "quality_assessor": "translation-quality-assessor",
            "supported_languages": ["zh", "en", "ja", "ko", "fr", "de"],
            "specialization": "patent_translation",
        },
        max_concurrent_tasks=8,
        timeout_seconds=240,  # 4分钟
    ),
}


class AgentCapabilityRegistry:
    """智能体能力注册器"""

    def __init__(self):
        self._capabilities = {}
        self._agents_by_capability = {}

    def register_capability(self, agent_type: AgentType, capability: AgentCapability):
        """注册智能体能力"""
        if agent_type not in self._capabilities:
            self._capabilities[agent_type] = set()

        self._capabilities[agent_type].add(capability)

        if capability not in self._agents_by_capability:
            self._agents_by_capability[capability] = set()
        self._agents_by_capability[capability].add(agent_type)

    def get_agent_capabilities(self, agent_type: AgentType) -> list[AgentCapability]:
        """获取智能体能力列表"""
        return list(self._capabilities.get(agent_type, set()))

    def get_agents_by_capability(self, capability: AgentCapability) -> list[AgentType]:
        """获取具备特定能力的智能体列表"""
        return list(self._agents_by_capability.get(capability, set()))

    def find_best_agent(self, required_capabilities: list[AgentCapability]) -> AgentType | None:
        """根据所需能力找到最适合的智能体"""
        best_agent = None
        best_score = 0

        for agent_type, capabilities in self._capabilities.items():
            # 计算能力匹配度
            matching_capabilities = len(capabilities.intersection(required_capabilities))
            score = matching_capabilities / len(required_capabilities)

            if score > best_score:
                best_score = score
                best_agent = agent_type

        return best_agent if best_score > 0.8 else None


# 全局能力注册器实例
capability_registry = AgentCapabilityRegistry()

# 初始化能力注册器
for agent_type, capabilities in AGENT_CAPABILITIES.items():
    for capability in capabilities:
        capability_registry.register_capability(agent_type, capability)


# 智能体工厂接口
class BaseAgent(ABC):
    """智能体基类"""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.status = AgentStatus.IDLE
        self.current_tasks = []
        self.performance_metrics = {}

    @abstractmethod
    async def initialize(self):
        """初始化智能体"""
        pass

    @abstractmethod
    async def process_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """处理任务"""
        pass

    @abstractmethod
    async def shutdown(self):
        """关闭智能体"""
        pass

    def get_capabilities(self) -> list[AgentCapability]:
        """获取智能体能力"""
        return self.config.capabilities

    def get_status(self) -> AgentStatus:
        """获取智能体状态"""
        return self.status


# 导出所有公共接口
__all__ = [
    # 枚举类型
    "AgentType",
    "AgentCapability",
    "AgentStatus",
    "TaskPriority",
    # 数据类
    "AgentConfig",
    # 配置映射
    "AGENT_CAPABILITIES",
    "AGENT_CONFIGS",
    # 注册器
    "AgentCapabilityRegistry",
    "capability_registry",
    # 基类
    "BaseAgent",
]
