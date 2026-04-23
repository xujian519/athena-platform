#!/usr/bin/env python3
"""
专利审查辩论协调器
Patent Debate Coordinator

协调审查员、小娜、Athena三方进行专利审查意见答复辩论

作者: Athena平台团队
版本: 1.0.0
创建时间: 2026-02-09
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from core.ai.llm.deepseek_client import DeepSeekClient
from scripts.debate.debate_participants import AthenaDebator, DebateArgument, XiaonaDebator
from scripts.debate.patent_examiner_agent import (
    ExaminerOpinion,
    ExaminerStance,
    PatentExaminerAgent,
)

logger = logging.getLogger(__name__)


@dataclass
class DebateRound:
    """单轮辩论记录"""
    round_num: int
    examiner_opinion: ExaminerOpinion
    xiaona_argument: DebateArgument | None = None
    athena_argument: DebateArgument | None = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "round_num": self.round_num,
            "timestamp": self.timestamp,
            "examiner": self.examiner_opinion.to_dict(),
            "xiaona": self.xiaona_argument.to_dict() if self.xiaona_argument else None,
            "athena": self.athena_argument.to_dict() if self.athena_argument else None,
        }


@dataclass
class DebateResult:
    """辩论结果"""
    total_rounds: int
    final_stance: ExaminerStance
    consensus_reached: bool
    summary: str
    rounds: list[DebateRound] = field(default_factory=list)
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: str | None = None

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "total_rounds": self.total_rounds,
            "final_stance": self.final_stance.value,
            "consensus_reached": self.consensus_reached,
            "summary": self.summary,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "rounds": [r.to_dict() for r in self.rounds],
        }


class DebateCoordinator:
    """
    专利辩论协调器

    职责:
    - 管理三方辩论流程
    - 协调审查员、小娜、Athena的发言
    - 判断是否达成共识
    - 生成辩论报告
    """

    # 共识判断标准
    CONSENSUS_STANCE = {
        ExaminerStance.FULLY_ACCEPT,
        ExaminerStance.LEAN_ACCEPT,
    }

    # 最大辩论轮次
    MAX_ROUNDS = 5

    def __init__(
        self,
        deepseek_client: DeepSeekClient | None = None,
        max_rounds: int = MAX_ROUNDS,
        save_path: str | None = None,
    ):
        self.deepseek_client = deepseek_client or DeepSeekClient(model="deepseek-chat")
        self.max_rounds = max_rounds
        self.save_path = save_path or "/Users/xujian/Athena工作平台/logs/debate_results"

        # 确保保存目录存在
        Path(self.save_path).mkdir(parents=True, exist_ok=True)

        # 初始化参与者
        self.examiner = PatentExaminerAgent(
            name="审查员肖玉林",
            deepseek_client=self.deepseek_client,
            stance=ExaminerStance.FULLY_REJECT,  # 初始反对
        )
        self.xiaona = XiaonaDebator(deepseek_client=self.deepseek_client)
        self.athena = AthenaDebator(deepseek_client=self.deepseek_client)

        # 辩论记录
        self.rounds: list[DebateRound] = []
        self.debate_result: DebateResult | None = None

        logger.info("✅ 辩论协调器初始化完成")

    async def conduct_debate(
        self,
        office_action: str,
        patent_response: str,
        patent_content: str,
    ) -> DebateResult:
        """
        进行完整辩论

        Args:
            office_action: 原审查意见
            patent_response: 申请人的答复
            patent_content: 专利申请内容

        Returns:
            DebateResult: 辩论结果
        """
        logger.info("🎬 开始专利审查辩论...")
        logger.info(f"   最大轮次: {self.max_rounds}")

        try:
            # 第1轮：初步分析
            round_num = 1
            logger.info(f"\n{'='*60}")
            logger.info(f"第{round_num}轮辩论")
            logger.info(f"{'='*60}")

            # 审查员分析答复
            examiner_opinion = await self.examiner.analyze_response(
                patent_response=patent_response,
                office_action=office_action,
                round_num=round_num,
            )

            # 小娜制定初步论点
            xiaona_arg = await self.xiaona.formulate_initial_response(
                office_action=office_action,
                patent_content=patent_content,
            )

            # Athena综合观点
            athena_arg = await self.athena.synthesize_debate(
                examiner_opinion=examiner_opinion,
                xiaona_arguments=[xiaona_arg],
                round_num=round_num,
            )

            # 记录第1轮
            self.rounds.append(DebateRound(
                round_num=round_num,
                examiner_opinion=examiner_opinion,
                xiaona_argument=xiaona_arg,
                athena_argument=athena_arg,
            ))

            # 打印当前状态
            self._print_round_status(round_num, examiner_opinion)

            # 检查是否达成共识
            if self._check_consensus(examiner_opinion):
                logger.info("✅ 第1轮即达成共识！")
                return self._finalize_result()

            # 后续轮次
            for round_num in range(2, self.max_rounds + 1):
                logger.info(f"\n{'='*60}")
                logger.info(f"第{round_num}轮辩论")
                logger.info(f"{'='*60}")

                # 收集小娜的历史论点
                xiaona_args = [r.xiaona_argument for r in self.rounds if r.xiaona_argument]

                # 审查员回应
                # 将小娜和Athena的论点合并为申请人论点
                applicant_args = xiaona_args
                if self.rounds[-1].athena_argument:
                    applicant_args.append(self.rounds[-1].athena_argument)

                # 构建申请人论点文本
                applicant_text = self._combine_arguments(applicant_args)

                examiner_opinion = await self.examiner.respond_to_arguments(
                    applicant_arguments=applicant_text,
                    previous_opinion=self.rounds[-1].examiner_opinion,
                    round_num=round_num,
                )

                # 小娜回应
                xiaona_arg = await self.xiaona.respond_to_examiner(
                    examiner_opinion=examiner_opinion,
                    previous_arguments=xiaona_args,
                )

                # Athena综合
                athena_arg = await self.athena.synthesize_debate(
                    examiner_opinion=examiner_opinion,
                    xiaona_arguments=xiaona_args + [xiaona_arg],
                    round_num=round_num,
                )

                # 记录本轮
                self.rounds.append(DebateRound(
                    round_num=round_num,
                    examiner_opinion=examiner_opinion,
                    xiaona_argument=xiaona_arg,
                    athena_argument=athena_arg,
                ))

                # 打印当前状态
                self._print_round_status(round_num, examiner_opinion)

                # 检查是否达成共识
                if self._check_consensus(examiner_opinion):
                    logger.info(f"✅ 第{round_num}轮达成共识！")
                    return self._finalize_result()

            # 达到最大轮次仍未达成共识
            logger.warning(f"⚠️ 已达最大轮次({self.max_rounds})，结束辩论")
            return self._finalize_result()

        except Exception as e:
            logger.error(f"❌ 辩论过程出错: {e}")
            raise

    def _combine_arguments(self, arguments: list[DebateArgument]) -> str:
        """合并多个论点"""
        combined = []
        for arg in arguments:
            combined.append(f"## {arg.speaker}")
            combined.append(arg.content)
            combined.append("")

        return "\n".join(combined)

    def _check_consensus(self, opinion: ExaminerOpinion) -> bool:
        """检查是否达成共识"""
        return opinion.stance in self.CONSENSUS_STANCE

    def _print_round_status(self, round_num: int, opinion: ExaminerOpinion):
        """打印轮次状态"""
        stance_emoji = {
            ExaminerStance.FULLY_REJECT: "🔴",
            ExaminerStance.PARTIAL_REJECT: "🟠",
            ExaminerStance.NEUTRAL: "🟡",
            ExaminerStance.LEAN_ACCEPT: "🟢",
            ExaminerStance.FULLY_ACCEPT: "✅",
        }

        emoji = stance_emoji.get(opinion.stance, "⚪")

        logger.info(f"{emoji} 审查员立场: {opinion.stance.value}")
        logger.info(f"   置信度: {opinion.confidence:.2f}")

        if opinion.key_concerns:
            logger.info(f"   关键疑虑 ({len(opinion.key_concerns)}个):")
            for concern in opinion.key_concerns[:3]:  # 只显示前3个
                logger.info(f"     - {concern}")

    def _finalize_result(self) -> DebateResult:
        """完成辩论结果"""
        final_opinion = self.rounds[-1].examiner_opinion

        # 生成摘要
        summary = self._generate_summary()

        result = DebateResult(
            total_rounds=len(self.rounds),
            final_stance=final_opinion.stance,
            consensus_reached=self._check_consensus(final_opinion),
            summary=summary,
            rounds=self.rounds,
            end_time=datetime.now().isoformat(),
        )

        self.debate_result = result

        # 保存结果
        self._save_result(result)

        return result

    def _generate_summary(self) -> str:
        """生成辩论摘要"""
        if not self.rounds:
            return "无辩论记录"

        initial_stance = self.rounds[0].examiner_opinion.stance.value
        final_stance = self.rounds[-1].examiner_opinion.stance.value

        summary_parts = [
            "## 辩论摘要",
            "",
            f"**辩论轮次**: {len(self.rounds)}轮",
            f"**初始立场**: {initial_stance}",
            f"**最终立场**: {final_stance}",
            f"**共识状态**: {'✅ 已达成共识' if self._check_consensus(self.rounds[-1].examiner_opinion) else '❌ 未达成共识'}",
            "",
            "**立场演变**:",
        ]

        for i, r in enumerate(self.rounds, 1):
            summary_parts.append(f"  第{i}轮: {r.examiner_opinion.stance.value}")

        summary_parts.append("")
        summary_parts.append("**主要论点**:")

        for i, r in enumerate(self.rounds[-2:], len(self.rounds) - 1):  # 只显示最后2轮
            if r.xiaona_argument:
                summary_parts.append(f"  第{i}轮小娜: {r.xiaona_argument.content[:100]}...")
            if r.athena_argument:
                summary_parts.append(f"  第{i}轮Athena: {r.athena_argument.content[:100]}...")

        return "\n".join(summary_parts)

    def _save_result(self, result: DebateResult):
        """保存辩论结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"patent_debate_{timestamp}.json"
        filepath = Path(self.save_path) / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)

        logger.info(f"💾 辩论结果已保存: {filepath}")

        # 同时保存Markdown格式
        md_filename = f"patent_debate_{timestamp}.md"
        md_filepath = Path(self.save_path) / md_filename

        self._save_markdown_report(result, md_filepath)

    def _save_markdown_report(self, result: DebateResult, filepath: Path):
        """保存Markdown格式报告"""
        lines = [
            "# 专利审查辩论报告",
            "",
            f"**辩论时间**: {result.start_time}",
            f"**辩论轮次**: {result.total_rounds}",
            f"**最终立场**: {result.final_stance}",
            f"**共识状态**: {'✅ 已达成' if result.consensus_reached else '❌ 未达成'}",
            "",
            "---",
            "",
            result.summary,
            "",
            "---",
            "",
            "## 详细记录",
            "",
        ]

        for r in result.rounds:
            lines.append(f"### 第{r.round_num}轮 ({r.timestamp})")
            lines.append("")
            lines.append(f"**审查员立场**: {r.examiner_opinion.stance.value}")
            lines.append("")
            lines.append("**审查员理由**:")
            lines.append(r.examiner_opinion.reasoning)
            lines.append("")

            if r.examiner_opinion.key_concerns:
                lines.append("**关键疑虑**:")
                for c in r.examiner_opinion.key_concerns:
                    lines.append(f"- {c}")
                lines.append("")

            if r.xiaona_argument:
                lines.append(f"**{r.xiaona_argument.speaker}论点**:")
                lines.append(r.xiaona_argument.content)
                lines.append("")

            if r.athena_argument:
                lines.append(f"**{r.athena_argument.speaker}论点**:")
                lines.append(r.athena_argument.content)
                lines.append("")

            lines.append("---")
            lines.append("")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        logger.info(f"📄 Markdown报告已保存: {filepath}")

    def get_debate_report(self) -> str | None:
        """获取辩论报告"""
        if not self.debate_result:
            return None

        return json.dumps(self.debate_result.to_dict(), ensure_ascii=False, indent=2)

    async def close(self):
        """关闭所有客户端"""
        await self.examiner.close()
        await self.xiaona.close()
        await self.athena.close()
        logger.info("🔌 辩论协调器已关闭")
