#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
辩论参与者 - 小娜、Athena
Debate Participants - Xiaona, Athena

专利辩论系统中的申请人方参与者

作者: Athena平台团队
版本: 1.0.0
创建时间: 2026-02-09
"""

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from core.llm.deepseek_client import DeepSeekClient
from scripts.debate.patent_examiner_agent import ExaminerOpinion

logger = logging.getLogger(__name__)


class ParticipantRole(Enum):
    """参与者角色"""
    # 小娜 - 专利法律专家
    XIAONA = "xiaona"
    # Athena - 智慧女神，系统协调者
    ATHENA = "athena"
    # 小诺 - 调度官（可选）
    XIAONUO = "xiaonuo"


@dataclass
class DebateArgument:
    """辩论论点"""
    speaker: str
    role: ParticipantRole
    content: str
    legal_basis: List[str]
    evidence: List[str]
    counterarguments: List[str] = None
    confidence: float = 0.8

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "speaker": self.speaker,
            "role": self.role.value,
            "content": self.content,
            "legal_basis": self.legal_basis,
            "evidence": self.evidence,
            "counterarguments": self.counterarguments or [],
            "confidence": self.confidence,
        }


class XiaonaDebator:
    """
    小娜辩论者

    角色: 专利法律专家
    专长:
    - 专利法条文解读
    - 案例检索和引用
    - 审查指南理解
    - 技术方案分析
    """

    XIAONA_SYSTEM_PROMPT = """你是小娜·天秤女神，Athena平台的专利法律专家。

【你的身份】
- 资深专利代理师
- 专利法律专家
- 审查意见答复专家

【你的专长】
1. **专利法精通**
   - 专利法第26条第3款（充分公开要求）
   - 专利法实施细则
   - 专利审查指南

2. **案例丰富**
   - 熟悉大量成功案例（如202423012016.2电梯门间隙测量案例）
   - 掌握审查员接受的各种答复策略
   - 了解审查员的关注点和说服方法

3. **技术理解**
   - 理解机械结构和技术原理
   - 能够分析技术方案的可行性
   - 熟悉本领域的公知常识

4. **辩论技巧**
   - 逻辑严密
   - 证据充分
   - 善于类比和举例
   - 理性与专业性并重

【你的辩论风格】
- 专业严谨，引用法条和案例
- 条理清晰，分点论述
- 以理服人，不卑不亢
- 技术与法律结合

【本次辩论目标】
说服审查员接受申请人的答复观点：
1. 定容计量是本领域的常规技术手段
2. 重力自流灌装是公知常识
3. 不需要称重设备即可实现灌装功能
4. 说明书已满足充分公开要求"""

    def __init__(
        self,
        deepseek_client: Optional[DeepSeekClient] = None,
        system_prompt: Optional[str] = None,
    ):
        self.name = "小娜·天秤女神"
        self.role = ParticipantRole.XIAONA
        self.deepseek_client = deepseek_client or DeepSeekClient(model="deepseek-chat")
        self.system_prompt = system_prompt or self.XIAONA_SYSTEM_PROMPT
        self.debate_history: List[DebateArgument] = []

        logger.info(f"✅ 小娜辩论者初始化完成")

    async def formulate_initial_response(
        self,
        office_action: str,
        patent_content: str,
    ) -> DebateArgument:
        """
        制定初步答复论点

        Args:
            office_action: 审查意见
            patent_content: 专利申请内容

        Returns:
            DebateArgument: 答复论点
        """
        logger.info("📝 小娜制定初步答复...")

        prompt = f"""{self.system_prompt}

【原审查意见】
{office_action}

【专利申请内容摘要】
{patent_content}

【任务】
作为专利代理师，请针对审查意见制定初步答复论点。

请从以下角度论述：
1. 专利法第26条第3款的理解和适用
2. "灌装、计量、称重"技术手段的说明
3. 本领域技术人员的理解能力
4. 与成功案例的类比

【输出格式】
**核心论点**: [一句话总结]

**法律依据**:
1. [法条1]
2. [法条2]
...

**技术分析**:
[详细分析技术方案]

**案例类比**:
[引用相似成功案例]

**结论**: [请求审查员接受答复]"""

        response = await self.deepseek_client.reason(
            problem=prompt,
            task_type="patent_response",
            temperature=0.3,
            max_tokens=3000,
        )

        argument = self._parse_argument(response.answer, self.role)

        self.debate_history.append(argument)
        logger.info("✅ 小娜初步答复完成")

        return argument

    async def respond_to_examiner(
        self,
        examiner_opinion: ExaminerOpinion,
        previous_arguments: List[DebateArgument],
    ) -> DebateArgument:
        """
        回应审查员意见

        Args:
            examiner_opinion: 审查员意见
            previous_arguments: 之前的论点

        Returns:
            DebateArgument: 回应论点
        """
        logger.info("💬 小娜回应审查员...")

        # 构建上下文
        context = self._build_debate_context(previous_arguments)

        prompt = f"""{self.system_prompt}

【辩论上下文】
{context}

【审查员当前意见】
立场: {examiner_opinion.stance.value}
理由: {examiner_opinion.reasoning}

仍存在的疑虑:
{chr(10).join(f"- {c}" for c in examiner_opinion.key_concerns)}

需要澄清的问题:
{chr(10).join(f"- {c}" for c in examiner_opinion.requested_clarifications)}

【任务】
作为专利代理师，请针对审查员的最新意见进行回应。

策略：
1. **直接回应疑虑** - 逐一解决审查员的具体问题
2. **补充技术细节** - 提供更详细的技术说明
3. **强化法律论证** - 引用更多法条和案例支持
4. **展示专业性** - 体现对本领域的深刻理解

【输出格式】
**回应策略**: [策略概述]

**具体回应**:
针对审查员的每个疑虑，提供详细回应。

**补充证据**:
[提供新的证据或论据]

**请求**:
[明确请求审查员接受或进一步说明]

保持专业、理性、有理有节的辩论风格。"""

        response = await self.deepseek_client.reason(
            problem=prompt,
            task_type="patent_debate",
            temperature=0.4,
            max_tokens=3000,
        )

        argument = self._parse_argument(response.answer, self.role)

        self.debate_history.append(argument)
        logger.info("✅ 小娜回应完成")

        return argument

    def _build_debate_context(self, arguments: List[DebateArgument]) -> str:
        """构建辩论上下文"""
        if not arguments:
            return "暂无历史论点"

        context_parts = []
        for i, arg in enumerate(arguments, 1):
            context_parts.append(f"[第{i}轮 - {arg.speaker}]")
            context_parts.append(arg.content[:200] + "..." if len(arg.content) > 200 else arg.content)
            context_parts.append("")

        return "\n".join(context_parts)

    def _parse_argument(self, response_text: str, role: ParticipantRole) -> DebateArgument:
        """解析论点"""
        # 默认值
        legal_basis = []
        evidence = []
        counterarguments = []
        confidence = 0.8

        # 简单解析（实际可以更复杂）
        if "专利法第26条第3款" in response_text:
            legal_basis.append("专利法第26条第3款")

        if "202423012016.2" in response_text or "成功案例" in response_text:
            evidence.append("成功案例类比")

        return DebateArgument(
            speaker=self.name,
            role=role,
            content=response_text,
            legal_basis=legal_basis,
            evidence=evidence,
            counterarguments=counterarguments,
            confidence=confidence,
        )

    async def close(self):
        """关闭客户端"""
        if self.deepseek_client:
            await self.deepseek_client.close()


class AthenaDebator:
    """
    Athena辩论者

    角色: 智慧女神，系统协调者
    专长:
    - 整合多方观点
    - 战略性思考
    - 价值升华
    - 最终决策
    """

    ATHENA_SYSTEM_PROMPT = """你是Athena·智慧女神，Athena平台的核心智能体。

【你的身份】
- 智慧女神，来自奥林匹斯山
- 系统协调者和战略思考者
- 公正的仲裁者

【你的专长】
1. **全局视野**
   - 整合多方观点
   - 发现共同点和分歧点
   - 提供平衡的视角

2. **战略思维**
   - 识别关键争议点
   - 提出创新解决方案
   - 长远考虑

3. **价值判断**
   - 平衡各方利益
   - 坚持公正原则
   - 促进达成共识

4. **优雅智慧**
   - 语言优美
   - 逻辑清晰
   - 说服力强

【你的辩论风格】
- 高屋建瓴，从全局出发
- 理性公正，不偏不倚
- 语言优美，富有感染力
- 促进共识，达成一致

【本次辩论目标】
1. 整合小娜的技术法律论证
2. 发现双方共识点
3. 提出建设性解决方案
4. 说服审查员接受合理观点"""

    def __init__(
        self,
        deepseek_client: Optional[DeepSeekClient] = None,
        system_prompt: Optional[str] = None,
    ):
        self.name = "Athena·智慧女神"
        self.role = ParticipantRole.ATHENA
        self.deepseek_client = deepseek_client or DeepSeekClient(model="deepseek-chat")
        self.system_prompt = system_prompt or self.ATHENA_SYSTEM_PROMPT
        self.debate_history: List[DebateArgument] = []

        logger.info(f"✅ Athena辩论者初始化完成")

    async def synthesize_debate(
        self,
        examiner_opinion: ExaminerOpinion,
        xiaona_arguments: List[DebateArgument],
        round_num: int,
    ) -> DebateArgument:
        """
        综合辩论观点

        Args:
            examiner_opinion: 审查员意见
            xiaona_arguments: 小娜的论点列表
            round_num: 辩论轮次

        Returns:
            DebateArgument: 综合论点
        """
        logger.info("🏛️ Athena综合辩论观点...")

        # 构建辩论历史
        xiaona_context = "\n\n".join([
            f"小娜论点{i+1}: {arg.content[:300]}..."
            for i, arg in enumerate(xiaona_arguments[-2:])  # 只取最近2个
        ])

        prompt = f"""{self.system_prompt}

【辩论进行到第{round_num}轮】

【审查员当前立场】
{examiner_opinion.stance.value}
理由: {examiner_opinion.reasoning}

【小娜的主要论点】
{xiaona_context}

【你的任务】
作为智慧女神Athena，请：

1. **分析共识与分歧**
   - 找出双方的共识点
   - 识别核心争议点
   - 评估各自的合理性

2. **提出建设性观点**
   - 从更高层次审视问题
   - 提供新的视角
   - 促进双方理解

3. **优雅地表达**
   - 用富有感染力的语言
   - 展现智慧与公正
   - 促进达成一致

【输出格式】
**共识识别**: [找出双方共识]

**争议分析**: [分析核心争议]

**Athena的观点**: [从智慧女神角度提出观点]

**建议方案**: [促进共识的建设性方案]

保持智慧女神的优雅与睿智。"""

        response = await self.deepseek_client.reason(
            problem=prompt,
            task_type="debate_synthesis",
            temperature=0.5,  # 稍高，增加创造性
            max_tokens=3000,
        )

        argument = DebateArgument(
            speaker=self.name,
            role=self.role,
            content=response.answer,
            legal_basis=["公正原则", "促进创新"],
            evidence=["整合观点", "战略分析"],
            confidence=0.9,
        )

        self.debate_history.append(argument)
        logger.info("✅ Athena综合完成")

        return argument

    async def make_final_statement(
        self,
        all_arguments: Dict[str, List[DebateArgument]],
        final_stance: str,
    ) -> DebateArgument:
        """
        发表最终陈述

        Args:
            all_arguments: 所有参与者的论点
            final_stance: 最终立场

        Returns:
            DebateArgument: 最终陈述
        """
        logger.info("🏆 Athena发表最终陈述...")

        prompt = f"""{self.system_prompt}

辩论已进行多轮，现在需要做出最终陈述。

【辩论总结】
审查员立场演变: [已记录]

小娜的主要论点: [已记录]

Athena的综合观点: [已记录]

【最终立场】: {final_stance}

【任务】
作为智慧女神，请发表一段优雅、有力的最终陈述。

内容应包括：
1. 对辩论过程的总结
2. 对各方观点的肯定
3. 最终立场的阐述
4. 对未来的展望

【风格要求】
- 语言优美，富有感染力
- 逻辑清晰，层次分明
- 公正客观，不偏不倚
- 展现智慧女神的风采

以"综上所述，"或类似词语开始。"""

        response = await self.deepseek_client.reason(
            problem=prompt,
            task_type="final_statement",
            temperature=0.6,
            max_tokens=2000,
        )

        argument = DebateArgument(
            speaker=self.name,
            role=self.role,
            content=response.answer,
            legal_basis=["专利法精神", "创新促进"],
            evidence=["完整辩论记录"],
            confidence=1.0,
        )

        logger.info("✅ 最终陈述完成")

        return argument

    async def close(self):
        """关闭客户端"""
        if self.deepseek_client:
            await self.deepseek_client.close()
