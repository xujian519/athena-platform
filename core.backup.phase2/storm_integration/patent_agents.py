#!/usr/bin/env python3
from __future__ import annotations
"""
专利领域专家 Agent 系统

实现专利领域的多专家 Agent,用于模拟专业人员的对话和分析。

Agent 类型:
- PatentExaminerAgent: 专利审查员 - 关注现有技术对比和创造性
- TechnicalExpertAgent: 技术专家 - 关注技术方案和实现细节
- PatentAttorneyAgent: 专利律师 - 关注权利要求和法律保护

作者: Athena 平台团队
创建时间: 2025-01-02
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from core.logging_config import setup_logging

logger = setup_logging()


class AgentRole(Enum):
    """Agent 角色类型"""

    EXAMINER = "patent_examiner"  # 专利审查员
    TECHNICAL_EXPERT = "technical_expert"  # 技术专家
    ATTORNEY = "patent_attorney"  # 专利律师


@dataclass
class Utterance:
    """话语(对话中的单次发言)"""

    agent_id: str  # 发言者 ID
    agent_name: str  # 发言者名称
    content: str  # 发言内容
    queries: list[str] = field(default_factory=list)  # 提出的查询
    citations: list[dict[str, str]] = field(default_factory=list)  # 引用来源
    turn: int = 0  # 轮次

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "content": self.content,
            "queries": self.queries,
            "citations": self.citations,
            "turn": self.turn,
        }


@dataclass
class Conversation:
    """对话记录"""

    topic: str  # 对话主题
    utterances: list[Utterance] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_utterance(self, utterance: Utterance) -> None:
        """添加话语"""
        utterance.turn = len(self.utterances)
        self.utterances.append(utterance)

    def get_history(self, last_n: int | None = None) -> list[Utterance]:
        """获取对话历史"""
        if last_n is None:
            return self.utterances
        return self.utterances[-last_n:]

    def get_all_citations(self) -> list[dict[str, str]]:
        """获取所有引用"""
        citations = []
        for utterance in self.utterances:
            citations.extend(utterance.citations)
        return citations


class BasePatentAgent(ABC):
    """
    专利 Agent 基类

    所有专利专家 Agent 的基类,定义统一的接口和行为。
    """

    def __init__(
        self,
        agent_id: str,
        agent_name: str,
        role: AgentRole,
        system_prompt: str,
    ):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.role = role
        self.system_prompt = system_prompt

        logger.info(f"初始化 Agent: {self.agent_name} ({self.role.value})")

    @abstractmethod
    def speak(
        self,
        conversation_history: list[Utterance],
        current_perspective: str,
        context: dict[str, Any] | None = None,
    ) -> Utterance:
        """
        生成话语

        Args:
            conversation_history: 对话历史
            current_perspective: 当前讨论的视角
            context: 额外上下文信息

        Returns:
            生成的话语对象
        """
        pass

    @abstractmethod
    def ask_questions(self, topic: str, perspective: str) -> list[str]:
        """
        生成问题

        Args:
            topic: 讨论主题
            perspective: 当前视角

        Returns:
            问题列表
        """
        pass

    def format_conversation_history(self, history: list[Utterance], max_turns: int = 5) -> str:
        """
        格式化对话历史为文本

        Args:
            history: 对话历史
            max_turns: 最多保留多少轮

        Returns:
            格式化的对话历史文本
        """
        recent_history = history[-max_turns:] if max_turns else history

        formatted = "之前的对话:\n\n"
        for utterance in recent_history:
            formatted += f"{utterance.agent_name}: {utterance.content}\n"

        return formatted


class PatentExaminerAgent(BasePatentAgent):
    """
    专利审查员 Agent

    专业领域:
    - 现有技术检索和对比
    - 创造性评估(三步法)
    - 新颖性分析
    - 实质性审查

    对话风格: 专业、严谨、关注细节
    """

    # 专利审查员的系统提示词
    SYSTEM_PROMPT = """你是一位经验丰富的专利审查员,专门负责专利申请的实质审查。

你的专业能力:
1. 熟练掌握专利法及相关审查指南
2. 能够全面检索现有技术
3. 准确评估新颖性和创造性(三步法)
4. 识别权利要求的问题

你的工作方式:
- 从现有技术的角度分析问题
- 关注技术方案的区别特征
- 评估技术差异的显而易见性
- 提出建设性的审查意见

对话风格: 专业、严谨、有理有据
"""

    def __init__(self):
        super().__init__(
            agent_id="examiner_001",
            agent_name="专利审查员",
            role=AgentRole.EXAMINER,
            system_prompt=self.SYSTEM_PROMPT,
        )

    def speak(
        self,
        conversation_history: list[Utterance],
        current_perspective: str,
        context: dict[str, Any] | None = None,
    ) -> Utterance:
        """
        生成审查员的话语

        重点关注:
        - 现有技术对比
        - 技术差异分析
        - 创造性评估
        """
        # 分析对话历史,决定发言内容
        if not conversation_history:
            # 第一轮发言:介绍检索结果
            content = self._introduce_prior_art(context)
            queries = ["最接近的现有技术", "对比文献", "技术差异"]
        else:
            # 后续发言:基于对话内容
            last_utterance = conversation_history[-1]
            content = self._analyze_from_examiner_perspective(last_utterance, current_perspective)
            queries = self._generate_examiner_questions(current_perspective)

        return Utterance(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            content=content,
            queries=queries,
            citations=self._get_examiner_citations(context),
        )

    def ask_questions(self, topic: str, perspective: str) -> list[str]:
        """生成审查员的问题"""
        questions = []

        if "技术" in perspective:
            questions = [
                f"关于{topic},现有技术中有没有类似的方案?",
                "这个技术方案和现有技术的主要区别在哪里?",
                "这些区别特征是本领域的公知常识吗?",
            ]
        elif "法律" in perspective:
            questions = [
                f"关于{topic},权利要求的保护范围是否清楚?",
                "是否存在得不到说明书支持的问题?",
                "是否有必要的缺漏?",
            ]

        return questions

    def _introduce_prior_art(self, context: dict,) -> str:
        """介绍现有技术"""
        return """作为一名专利审查员,我已经检索了相关的现有技术。

根据检索结果,我发现了以下对比文献:
1. CN102345678A: 公开了一种类似的图像识别方法,采用卷积神经网络
2. US9876543B2: 涉及深度学习在图像处理中的应用
3. CN112345678A: 公开了相关的特征提取技术

我建议我们从最接近的现有技术开始,逐步分析区别特征。"""

    def _analyze_from_examiner_perspective(
        self, last_utterance: Utterance, perspective: str
    ) -> str:
        """从审查员角度分析"""
        return f"""基于{last_utterance.agent_name}的分析,我从审查员的角度补充几点:

根据三步法,我们需要确定:
1. 最接近的现有技术是什么?
2. 区别特征是什么?
3. 这些区别特征是否显而易见?

我注意到,这个技术方案虽然有一定创新性,但需要进一步证明其非显而易见性。
{last_utterance.agent_name}提到的一些技术特征,在现有技术中已经有类似应用的先例。

我想问的是: 这个技术方案相比现有技术,是否有预料不到的技术效果?"""

    def _generate_examiner_questions(self, perspective: str) -> list[str]:
        """生成审查员的问题"""
        return [
            "该技术方案的最接近现有技术是什么?",
            "区别特征是否属于公知常识?",
            "是否有预料不到的技术效果?",
        ]

    def _get_examiner_citations(self, context: dict,) -> list[dict[str, str]]:
        """获取审查员的引用"""
        return [
            {"source": "专利审查指南", "url": "https://www.cnipa.gov.cn/"},
            {"source": "CN102345678A", "patent_id": "CN102345678A"},
        ]


class TechnicalExpertAgent(BasePatentAgent):
    """
    技术专家 Agent

    专业领域:
    - 技术方案分析
    - 实现细节解释
    - 创新点识别
    - 技术缺陷评估

    对话风格: 专业、深入、关注技术实现
    """

    SYSTEM_PROMPT = """你是一位资深的技术专家,在相关技术领域有深厚的专业背景。

你的专业能力:
1. 深入理解技术方案的原理和实现
2. 识别技术创新点和难点
3. 评估技术的可行性和改进空间
4. 解释复杂的技术概念

你的工作方式:
- 从技术实现的角度分析问题
- 关注技术方案的创新性和实用性
- 评估技术的优势和不足
- 提出技术改进建议

对话风格: 专业、深入、通俗易懂
"""

    def __init__(self):
        super().__init__(
            agent_id="tech_expert_001",
            agent_name="技术专家",
            role=AgentRole.TECHNICAL_EXPERT,
            system_prompt=self.SYSTEM_PROMPT,
        )

    def speak(
        self,
        conversation_history: list[Utterance],
        current_perspective: str,
        context: dict[str, Any] | None = None,
    ) -> Utterance:
        """生成技术专家的话语"""
        if not conversation_history:
            content = self._explain_technical_solution(context)
            queries = ["技术原理", "实现方式", "创新点"]
        else:
            last_utterance = conversation_history[-1]
            content = self._analyze_from_technical_perspective(last_utterance, current_perspective)
            queries = self._generate_technical_questions(current_perspective)

        return Utterance(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            content=content,
            queries=queries,
            citations=self._get_technical_citations(context),
        )

    def ask_questions(self, topic: str, perspective: str) -> list[str]:
        """生成技术专家的问题"""
        return [
            f"关于{topic},核心技术方案是什么?",
            "实现过程中有哪些关键技术难点?",
            "相比现有方案,有哪些创新和改进?",
            "技术的可扩展性如何?",
        ]

    def _explain_technical_solution(self, context: dict,) -> str:
        """解释技术方案"""
        return """从技术专家的角度来看,这个专利的核心创新在于:

1. **技术架构**: 采用了一种新的深度学习架构,结合了CNN和Transformer的优点
2. **关键算法**: 提出了一种改进的注意力机制,能够更好地捕捉图像特征
3. **性能优化**: 通过模型剪枝和量化,在保持精度的同时提高了推理速度

技术亮点:
- 在ImageNet数据集上达到了95%的准确率
- 推理速度比传统方法快3倍
- 内存占用减少了40%

不过,我也注意到一些潜在的技术挑战:
- 对小样本数据的泛化能力有待验证
- 模型的可解释性需要进一步加强"""

    def _analyze_from_technical_perspective(
        self, last_utterance: Utterance, perspective: str
    ) -> str:
        """从技术专家角度分析"""
        return f"""{last_utterance.agent_name}提出了很好的观点。作为技术专家,我想补充:

从技术实现的角度来看,这个创新点并非简单的技术组合,而是:
1. 解决了长期存在的技术难题
2. 提出了具有突破性的技术方案
3. 实现了显著的性能提升

特别是提到的注意力机制改进,这是一个非显而易见的技术创新。
现有技术虽然也有各种注意力机制,但都没有解决这个特定问题。

我认为这体现了"实质性特点"和"进步",应该具有创造性。"""

    def _generate_technical_questions(self, perspective: str) -> list[str]:
        """生成技术问题"""
        return [
            "技术方案的具体实现方式是什么?",
            "是否有具体的技术数据支撑?",
            "技术的实用性和可行性如何?",
        ]

    def _get_technical_citations(self, context: dict,) -> list[dict[str, str]]:
        """获取技术引用"""
        return [
            {"source": "技术论文", "title": "Attention Is All You Need"},
            {"source": "技术文档", "url": "https://arxiv.org/abs/1706.03762"},
        ]


class PatentAttorneyAgent(BasePatentAgent):
    """
    专利律师 Agent

    专业领域:
    - 权利要求分析
    - 保护范围评估
    - 侵权风险分析
    - 法律意见提供

    对话风格: 专业、谨慎、关注法律风险
    """

    SYSTEM_PROMPT = """你是一位资深的专利律师,在专利法律服务方面有丰富的经验。

你的专业能力:
1. 准确理解和分析权利要求
2. 评估专利保护范围和法律状态
3. 识别侵权风险和法律问题
4. 提供专业的法律意见

你的工作方式:
- 从法律保护的角度分析问题
- 关注权利要求的清楚性和支持性
- 评估专利的法律稳定性
- 提供风险防范建议

对话风格: 专业、谨慎、全面
"""

    def __init__(self):
        super().__init__(
            agent_id="attorney_001",
            agent_name="专利律师",
            role=AgentRole.ATTORNEY,
            system_prompt=self.SYSTEM_PROMPT,
        )

    def speak(
        self,
        conversation_history: list[Utterance],
        current_perspective: str,
        context: dict[str, Any] | None = None,
    ) -> Utterance:
        """生成专利律师的话语"""
        if not conversation_history:
            content = self._analyze_claims_protection(context)
            queries = ["权利要求", "保护范围", "法律风险"]
        else:
            last_utterance = conversation_history[-1]
            content = self._analyze_from_legal_perspective(last_utterance, current_perspective)
            queries = self._generate_legal_questions(current_perspective)

        return Utterance(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            content=content,
            queries=queries,
            citations=self._get_legal_citations(context),
        )

    def ask_questions(self, topic: str, perspective: str) -> list[str]:
        """生成专利律师的问题"""
        return [
            f"关于{topic},权利要求的保护范围是否清晰?",
            "是否存在法律风险?",
            "专利的法律稳定性如何?",
            "是否有改进建议?",
        ]

    def _analyze_claims_protection(self, context: dict,) -> str:
        """分析权利要求保护"""
        return """从专利律师的角度,我关注以下几点:

**权利要求分析**:
1. **主权项**: 保护范围适中,涵盖了核心技术方案
2. **从属权利要求**: 形成了多层次的保护体系
3. **用语**: 权利要求用语基本清楚,但有一些可以优化

**法律风险**:
- 部分技术特征可能被认定为功能性限定
- "优选"、"较佳"等建议用语可能影响保护范围
- 建议进一步明确关键技术参数

**稳定性评估**:
- 新颖性: 需要进一步检索确认
- 创造性: 有一定优势,但需要充分证据
- 实用性: 符合要求

建议: 在答复审查意见时,重点强调技术效果和进步。"""

    def _analyze_from_legal_perspective(self, last_utterance: Utterance, perspective: str) -> str:
        """从律师角度分析"""
        return f"""综合{last_utterance.agent_name}的分析,从法律角度我给出以下意见:

**权利要求布局**:
当前的权利要求结构较为合理,但建议:
1. 进一步细化区别特征
2. 增加更多从属权利要求
3. 考虑布局方法权利要求

**法律风险评估**:
- 被无效风险: 中等(需要更多对比文献分析)
- 侵权风险: 较低(权利要求保护范围清晰)
- 审查通过概率: 较高(技术方案有一定创造性)

**建议**:
1. 在后续答复中,强调技术效果的显著性
2. 准备更多的对比数据
3. 考虑分案申请的可能性"""

    def _generate_legal_questions(self, perspective: str) -> list[str]:
        """生成法律问题"""
        return [
            "权利要求是否得到说明书支持?",
            "保护范围是否清晰?",
            "是否有法律风险?",
        ]

    def _get_legal_citations(self, context: dict,) -> list[dict[str, str]]:
        """获取法律引用"""
        return [
            {"source": "专利法", "url": "https://www.cnipa.gov.cn/"},
            {"source": "审查指南", "url": "https://www.cnipa.gov.cn/"},
        ]


class AgentFactory:
    """
    Agent 工厂类

    用于创建和管理专利领域的专家 Agent
    """

    _agents = {
        AgentRole.EXAMINER: PatentExaminerAgent,
        AgentRole.TECHNICAL_EXPERT: TechnicalExpertAgent,
        AgentRole.ATTORNEY: PatentAttorneyAgent,
    }

    @classmethod
    def create_agent(cls, role: AgentRole) -> BasePatentAgent:
        """
        创建 Agent

        Args:
            role: Agent 角色

        Returns:
            Agent 实例
        """
        agent_class = cls._agents.get(role)
        if agent_class is None:
            raise ValueError(f"未知的 Agent 角色: {role}")

        return agent_class()

    @classmethod
    def create_all_agents(cls) -> list[BasePatentAgent]:
        """创建所有预定义的 Agent"""
        return [cls.create_agent(role) for role in cls._agents]


# 便捷函数
def simulate_patent_conversation(
    topic: str, perspectives: list[str], max_turns: int = 3
) -> Conversation:
    """
    模拟专利专家对话

    Args:
        topic: 讨论主题
        perspectives: 讨论视角列表
        max_turns: 最大轮次

    Returns:
        对话记录
    """
    conversation = Conversation(topic=topic)
    agents = AgentFactory.create_all_agents()

    for turn in range(max_turns):
        perspective = perspectives[turn % len(perspectives)]
        agent = agents[turn % len(agents)]

        utterance = agent.speak(
            conversation_history=conversation.utterances,
            current_perspective=perspective,
        )

        conversation.add_utterance(utterance)

    return conversation


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("专利 Agent 系统测试")
    print("=" * 60)

    # 测试1: 创建单个 Agent
    print("\n[测试1] 创建审查员 Agent:")
    examiner = AgentFactory.create_agent(AgentRole.EXAMINER)
    print(f"  Agent 名称: {examiner.agent_name}")
    print(f"  Agent 角色: {examiner.role.value}")

    # 测试2: 模拟对话
    print("\n[测试2] 模拟专家对话:")
    conversation = simulate_patent_conversation(
        topic="基于深度学习的图像识别方法",
        perspectives=["技术分析", "法律分析", "创造性评估"],
        max_turns=6,
    )

    print(f"\n对话主题: {conversation.topic}")
    print(f"对话轮次: {len(conversation.utterances)}\n")

    for utterance in conversation.utterances:
        print(f"[轮次 {utterance.turn + 1}] {utterance.agent_name}:")
        print(f"{utterance.content[:200]}...")
        print()
