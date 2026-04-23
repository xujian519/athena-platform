#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专利审查员智能体
Patent Examiner Agent

模拟专利审查员，与Athena、小娜进行专利审查意见答复的辩论

作者: Athena平台团队
版本: 1.0.0
创建时间: 2026-02-09
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from core.llm.deepseek_client import DeepSeekClient

logger = logging.getLogger(__name__)


class ExaminerStance(Enum):
    """审查员立场"""
    # 完全反对 - 审查意见完全成立
    FULLY_REJECT = "fully_reject"
    # 部分反对 - 部分审查意见成立
    PARTIAL_REJECT = "partial_reject"
    # 中立 - 需要更多证据
    NEUTRAL = "neutral"
    # 倾向同意 - 答复有道理但需补充
    LEAN_ACCEPT = "lean_accept"
    # 完全同意 - 答复充分，可授予专利权
    FULLY_ACCEPT = "fully_accept"


@dataclass
class ExaminerOpinion:
    """审查员意见"""
    stance: ExaminerStance
    reasoning: str
    key_concerns: List[str] = field(default_factory=list)
    requested_clarifications: List[str] = field(default_factory=list)
    confidence: float = 0.5

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "stance": self.stance.value,
            "reasoning": self.reasoning,
            "key_concerns": self.key_concerns,
            "requested_clarifications": self.requested_clarifications,
            "confidence": self.confidence,
        }


class PatentExaminerAgent:
    """
    专利审查员智能体

    职责:
    - 代表专利局审查员的视角
    - 基于专利法和审查指南提出质疑
    - 评估申请人答复的充分性
    - 与申请人的代理律师（小娜、Athena）进行辩论
    """

    # 审查员核心关注点
    EXAMINER_CONCERNS = [
        "专利法第26条第3款 - 说明书是否充分公开",
        "技术方案是否清楚、完整",
        "所属技术领域的技术人员能否实现",
        "技术手段是否含糊不清",
        "实施例是否足够",
        "技术效果是否可信",
    ]

    def __init__(
        self,
        name: str = "审查员肖玉林",
        deepseek_client: Optional[DeepSeekClient] = None,
        stance: ExaminerStance = ExaminerStance.FULLY_REJECT,
    ):
        self.name = name
        self.stance = stance
        self.deepseek_client = deepseek_client or DeepSeekClient(model="deepseek-chat")
        self.debate_history: List[Dict[str, Any]] = []

        logger.info(f"✅ 审查员智能体初始化完成: {self.name}")

    async def analyze_response(
        self,
        patent_response: str,
        office_action: str,
        round_num: int = 1,
    ) -> ExaminerOpinion:
        """
        分析申请人答复

        Args:
            patent_response: 申请人的答复意见
            office_action: 原审查意见
            round_num: 辩论轮次

        Returns:
            ExaminerOpinion: 审查员意见
        """
        logger.info(f"🔍 审查员分析答复 (第{round_num}轮)...")

        # 构建分析提示
        analysis_prompt = self._build_analysis_prompt(
            patent_response, office_action, round_num
        )

        # 调用DeepSeek进行分析
        response = await self.deepseek_client.reason(
            problem=analysis_prompt,
            task_type="patent_examination",
            temperature=0.3,  # 保持一定的一致性
            max_tokens=3000,
        )

        # 解析审查员意见
        opinion = self._parse_examiner_opinion(response.answer)

        # 记录历史
        self.debate_history.append({
            "round": round_num,
            "role": "examiner",
            "opinion": opinion.to_dict(),
            "raw_response": response.answer,
        })

        logger.info(f"✅ 审查员分析完成 - 立场: {opinion.stance.value}")

        return opinion

    async def respond_to_arguments(
        self,
        applicant_arguments: str,
        previous_opinion: ExaminerOpinion,
        round_num: int = 1,
    ) -> ExaminerOpinion:
        """
        回应申请人的辩论论点

        Args:
            applicant_arguments: 申请人的辩论论点
            previous_opinion: 之前的审查员意见
            round_num: 辩论轮次

        Returns:
            ExaminerOpinion: 更新后的审查员意见
        """
        logger.info(f"💬 审查员回应辩论 (第{round_num}轮)...")

        # 构建回应提示
        response_prompt = self._build_response_prompt(
            applicant_arguments, previous_opinion, round_num
        )

        # 调用DeepSeek进行回应
        response = await self.deepseek_client.reason(
            problem=response_prompt,
            task_type="patent_debate",
            temperature=0.4,
            max_tokens=3000,
        )

        # 解析更新后的意见
        updated_opinion = self._parse_examiner_opinion(response.answer)

        # 记录历史
        self.debate_history.append({
            "round": round_num,
            "role": "examiner_response",
            "opinion": updated_opinion.to_dict(),
            "raw_response": response.answer,
        })

        logger.info(f"✅ 审查员回应完成 - 更新立场: {updated_opinion.stance.value}")

        return updated_opinion

    def _build_analysis_prompt(
        self, patent_response: str, office_action: str, round_num: int
    ) -> str:
        """构建分析提示词"""
        return f"""你是专利审查员{self.name}，正在审查实用新型专利申请202520560089.0（一种药品生产灌装机）。

【原审查意见】
{office_action}

【申请人的答复】
{patent_response}

【你的任务】
作为审查员，你需要评估申请人的答复是否充分回应了你的审查意见。请从以下角度分析：

1. **专利法第26条第3款角度**
   - 说明书是否清楚、完整地说明了技术方案
   - 所属技术领域的技术人员能否根据说明书实现该实用新型

2. **技术方案清晰度角度**
   - "灌装、计量、称重"的技术手段是否清楚
   - 如何用于药品灌装的原理是否明确

3. **实施可行性角度**
   - 技术人员是否能够根据说明书记载具体实施
   - 是否存在含糊不清的技术手段

请提供你的分析，包括：
- 当前立场（完全反对/部分反对/中立/倾向同意/完全同意）
- 详细理由
- 仍存在的疑虑
- 需要申请人进一步澄清的问题

【输出格式】
请按以下格式输出：

**当前立场**: [立场选择]

**分析理由**:
[详细分析]

**仍存在的疑虑**:
1. [疑虑1]
2. [疑虑2]
...

**需要澄清的问题**:
1. [问题1]
2. [问题2]
...

**置信度**: [0-1之间的数值]

第{round_num}轮分析，请客观公正，基于专利法和审查指南进行判断。"""

    def _build_response_prompt(
        self,
        applicant_arguments: str,
        previous_opinion: ExaminerOpinion,
        round_num: int,
    ) -> str:
        """构建回应提示词"""
        return f"""你是专利审查员{self.name}，正在与申请人的代理律师进行辩论。

【之前的审查意见】
立场: {previous_opinion.stance.value}
理由: {previous_opinion.reasoning}

疑虑:
{chr(10).join(f"- {c}" for c in previous_opinion.key_concerns)}

需要澄清:
{chr(10).join(f"- {c}" for c in previous_opinion.requested_clarifications)}

【代理律师的辩论论点】
{applicant_arguments}

【你的任务】
作为审查员，你需要：

1. **评估代理律师的论点**
   - 论点是否有法律依据
   - 论点是否充分回应了你的疑虑
   - 是否有新的证据或理由

2. **更新你的立场**
   - 如果被说服，可以调整立场
   - 如果仍有疑虑，说明具体原因
   - 如果需要更多信息，明确指出

3. **继续辩论**
   - 提出反驳论点（如有）
   - 指出论证中的漏洞
   - 要求进一步说明

请提供你的回应，按照之前的格式输出。

第{round_num}轮辩论，请保持客观公正，基于事实和法律进行判断。"""

    def _parse_examiner_opinion(self, response_text: str) -> ExaminerOpinion:
        """解析审查员意见"""
        # 默认值
        stance = ExaminerStance.NEUTRAL
        reasoning = response_text
        concerns = []
        clarifications = []
        confidence = 0.5

        # 解析立场
        stance_mapping = {
            "完全反对": ExaminerStance.FULLY_REJECT,
            "部分反对": ExaminerStance.PARTIAL_REJECT,
            "中立": ExaminerStance.NEUTRAL,
            "倾向同意": ExaminerStance.LEAN_ACCEPT,
            "完全同意": ExaminerStance.FULLY_ACCEPT,
        }

        for keyword, stance_value in stance_mapping.items():
            if keyword in response_text:
                stance = stance_value
                break

        # 尝试提取结构化内容
        lines = response_text.split("\n")
        current_section = None

        for line in lines:
            line = line.strip()
            if "当前立场" in line or "立场:" in line:
                # 提取立场
                for keyword, stance_value in stance_mapping.items():
                    if keyword in line:
                        stance = stance_value
                        break
            elif "分析理由" in line or "理由:" in line:
                current_section = "reasoning"
            elif "仍存在的疑虑" in line or "疑虑" in line:
                current_section = "concerns"
            elif "需要澄清的问题" in line or "需要澄清" in line:
                current_section = "clarifications"
            elif "置信度" in line:
                # 提取置信度
                try:
                    import re
                    match = re.search(r"置信度.*?(\d+\.?\d*)", line)
                    if match:
                        confidence = float(match.group(1))
                except:
                    pass
            elif line and (line.startswith("-") or line.startswith("•") or (line[0].isdigit() and "." in line[:3])):
                # 列表项
                content = line.lstrip("- •0123456789.)、.")
                if current_section == "concerns":
                    concerns.append(content)
                elif current_section == "clarifications":
                    clarifications.append(content)
            elif current_section == "reasoning" and line:
                reasoning += "\n" + line

        return ExaminerOpinion(
            stance=stance,
            reasoning=reasoning,
            key_concerns=concerns,
            requested_clarifications=clarifications,
            confidence=confidence,
        )

    def get_debate_summary(self) -> dict:
        """获取辩论摘要"""
        if not self.debate_history:
            return {"message": "暂无辩论记录"}

        # 获取最新立场
        latest_opinion = self.debate_history[-1]["opinion"]

        # 立场演变
        stance_evolution = [entry["opinion"]["stance"] for entry in self.debate_history]

        return {
            "examiner_name": self.name,
            "total_rounds": len(self.debate_history),
            "current_stance": latest_opinion["stance"],
            "stance_evolution": stance_evolution,
            "latest_concerns": latest_opinion["key_concerns"],
            "latest_clarifications": latest_opinion["latest_clarifications"],
            "confidence": latest_opinion["confidence"],
        }

    async def close(self):
        """关闭客户端"""
        if self.deepseek_client:
            await self.deepseek_client.close()
        logger.info("🔌 审查员智能体已关闭")
