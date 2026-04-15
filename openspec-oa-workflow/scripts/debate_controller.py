#!/usr/bin/env python3
"""
辩论控制器 - 双智能体辩论验证模块
Debate Controller - Dual Agent Debate Validation Module

版本: 1.0.0
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class DebateRound:
    """辩论轮次"""
    round_number: int
    attorney_message: str
    examiner_message: str
    attorney_score: float = 0.0  # 代理师得分
    examiner_score: float = 0.0  # 审查员得分
    consensus: bool = False

@dataclass
class DebateState:
    """辩论状态"""
    case_id: str
    response_draft: str
    rounds: list[DebateRound] = field(default_factory=list)
    controversial_points: list[str] = field(default_factory=list)
    final_verdict: dict | None = None
    started_at: str = ""
    completed_at: str = ""

class DebateController:
    """辩论控制器"""

    def __init__(self):
        self.min_rounds = 5
        self.max_rounds = 20

    async def start_debate(
        self,
        case_id: str,
        response_draft: str,
        analysis_results: dict
    ) -> DebateState:
        """启动辩论"""

        state = DebateState(
            case_id=case_id,
            response_draft=response_draft,
            started_at=datetime.now().isoformat()
        )

        round_num = 0
        while round_num < self.max_rounds:
            round_num += 1

            # 执行一轮辩论
            debate_round = await self._execute_round(
                state, round_num, analysis_results
            )
            state.rounds.append(debate_round)

            # 检查是否达成一致
            if debate_round.consensus:
                break

            # 检查是否达到最少轮数且趋势一致
            if round_num >= self.min_rounds:
                if self._check_trending_consensus(state):
                    break

        # 主智能体裁决
        state.final_verdict = await self._make_verdict(state)
        state.completed_at = datetime.now().isoformat()

        return state

    async def _execute_round(
        self,
        state: DebateState,
        round_num: int,
        analysis_results: dict
    ) -> DebateRound:
        """执行一轮辩论"""

        # 代理师发言
        attorney_message = await self._attorney_speak(
            state, round_num, analysis_results
        )

        # 审查员发言
        examiner_message = await self._examiner_speak(
            state, round_num, attorney_message, analysis_results
        )

        # 评估是否达成一致
        consensus = self._evaluate_consensus(attorney_message, examiner_message)

        return DebateRound(
            round_number=round_num,
            attorney_message=attorney_message,
            examiner_message=examiner_message,
            consensus=consensus
        )

    async def _attorney_speak(
        self,
        state: DebateState,
        round_num: int,
        analysis_results: dict
    ) -> str:
        """代理师发言"""

        if round_num == 1:
            # 第一轮：陈述核心观点
            f"""
你是一位有15年经验的专利代理师。请针对以下答复草案，陈述你的核心观点：

答复草案：
{state.response_draft}

分析结果：
{json.dumps(analysis_results, ensure_ascii=False, indent=2)}

请以【代理师-第1轮发言】的格式输出你的观点。
"""
        else:
            # 后续轮：回应审查员质疑
            last_round = state.rounds[-1]
            f"""
你是一位有15年经验的专利代理师。审查员在第{round_num-1}轮提出了质疑，请回应：

审查员的质疑：
{last_round.examiner_message}

你的答复草案：
{state.response_draft}

请以【代理师-第{round_num}轮发言】的格式输出你的回应。
"""

        # TODO: 实际调用LLM
        # response = await self._call_llm(prompt)
        return f"[代理师第{round_num}轮发言 - 待LLM生成]"

    async def _examiner_speak(
        self,
        state: DebateState,
        round_num: int,
        attorney_message: str,
        analysis_results: dict
    ) -> str:
        """审查员发言"""

        f"""
你是一位严谨的专利审查员。代理师在第{round_num}轮提出了观点，请进行质疑：

代理师的观点：
{attorney_message}

原始分析结果：
{json.dumps(analysis_results, ensure_ascii=False, indent=2)}

请以【审查员-第{round_num}轮发言】的格式输出你的质疑。
请明确指出：接受/部分接受/不接受
"""

        # TODO: 实际调用LLM
        return f"[审查员第{round_num}轮发言 - 待LLM生成]"

    def _evaluate_consensus(self, attorney: str, examiner: str) -> bool:
        """评估是否达成一致"""
        # 检查审查员是否表示"接受"
        if "接受" in examiner and "不接受" not in examiner:
            return True
        return False

    def _check_trending_consensus(self, state: DebateState) -> bool:
        """检查是否趋于一致"""
        if len(state.rounds) < 3:
            return False

        # 检查最近3轮是否都是"部分接受"
        recent = state.rounds[-3:]
        return all("部分接受" in r.examiner_message for r in recent)

    async def _make_verdict(self, state: DebateState) -> dict:
        """主智能体裁决"""

        f"""
你是主智能体，负责对以下辩论做出裁决。

辩论记录：
{json.dumps([{"round": r.round_number, "attorney": r.attorney_message, "examiner": r.examiner_message} for r in state.rounds], ensure_ascii=False, indent=2)}

请输出JSON格式的裁决：
{{
  "verdict": "支持代理师|支持审查员|部分支持",
  "reasoning": "裁决理由",
  "controversial_points": ["争议点列表"],
  "modification_suggestions": ["修改建议"],
  "final_conclusion": "最终结论"
}}
"""

        # TODO: 实际调用LLM
        return {
            "verdict": "部分支持",
            "reasoning": "待LLM生成",
            "controversial_points": [],
            "modification_suggestions": [],
            "final_conclusion": ""
        }

    def generate_debate_report(self, state: DebateState) -> str:
        """生成辩论报告（Markdown格式）"""

        report = f"""# 辩论记录报告

**案例ID**: {state.case_id}
**开始时间**: {state.started_at}
**结束时间**: {state.completed_at}
**总轮数**: {len(state.rounds)}

---

## 辩论过程

"""

        for r in state.rounds:
            report += f"""### 第{r.round_number}轮

**代理师发言**：
{r.attorney_message}

**审查员发言**：
{r.examiner_message}

**是否达成一致**: {'是' if r.consensus else '否'}

---

"""

        report += f"""## 最终裁决

**裁决结果**: {state.final_verdict.get('verdict', 'N/A')}

**裁决理由**:
{state.final_verdict.get('reasoning', 'N/A')}

**争议点**:
{chr(10).join('- ' + p for p in state.final_verdict.get('controversial_points', []))}

**修改建议**:
{chr(10).join('- ' + s for s in state.final_verdict.get('modification_suggestions', []))}

**最终结论**:
{state.final_verdict.get('final_conclusion', 'N/A')}

---

*报告生成时间: {datetime.now().isoformat()}*
"""

        return report


# ==================== 使用示例 ====================

async def example_usage():
    """使用示例"""
    controller = DebateController()

    state = await controller.start_debate(
        case_id="CN202410001234",
        response_draft="这是答复草案内容...",
        analysis_results={"some": "analysis"}
    )

    report = controller.generate_debate_report(state)
    print(report)


if __name__ == "__main__":
    asyncio.run(example_usage())
