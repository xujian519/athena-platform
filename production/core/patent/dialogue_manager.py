#!/usr/bin/env python3
"""
多轮对话管理器
Dialogue Manager

管理申请人与审查员之间的多轮论证对话流程

Author: Athena平台团队
Created: 2026-01-26
Version: v1.0.0
"""

from __future__ import annotations
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from core.patent.examiner_simulator import get_examiner_simulator

logger = logging.getLogger(__name__)


class DialogueTurn:
    """单轮对话记录"""

    def __init__(
        self,
        turn_number: int,
        role: str,
        content: str,
        metadata: dict | None = None
    ):
        self.turn_number = turn_number
        self.role = role  # "applicant" or "examiner"
        self.content = content
        self.metadata = metadata or {}
        self.timestamp = datetime.now()

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "turn_number": self.turn_number,
            "role": self.role,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


class DialogueSession:
    """对话会话"""

    def __init__(
        self,
        session_id: str,
        oa_text: str,
        claims: list[str],
        prior_art_analysis: dict
    ):
        self.session_id = session_id
        self.oa_text = oa_text
        self.claims = claims
        self.prior_art_analysis = prior_art_analysis
        self.turns: list[DialogueTurn] = []
        self.status = "in_progress"  # in_progress, completed, terminated
        self.start_time = datetime.now()
        self.end_time: datetime | None = None

    def add_turn(self, role: str, content: str, metadata: dict | None = None):
        """添加对话轮次"""
        turn_number = len(self.turns) + 1
        turn = DialogueTurn(
            turn_number=turn_number,
            role=role,
            content=content,
            metadata=metadata
        )
        self.turns.append(turn)

    def complete(self):
        """完成会话"""
        self.status = "completed"
        self.end_time = datetime.now()

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "oa_text": self.oa_text[:200] + "...",
            "claims_count": len(self.claims),
            "turns_count": len(self.turns),
            "status": self.status,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "turns": [turn.to_dict() for turn in self.turns]
        }


class DialogueManager:
    """
    多轮对话管理器

    功能：
    1. 管理申请人与审查员的多轮对话
    2. 追踪对话历史和状态
    3. 提供对话策略建议
    4. 评估对话质量和进展
    5. 自动终止无效对话
    """

    # 最大对话轮次
    MAX_ROUNDS = 5

    # 对话终止条件
    TERMINATION_CONDITIONS = {
        "max_rounds_reached": "达到最大对话轮次",
        "agreement_reached": "达成一致",
        "no_progress": "连续两轮无实质性进展",
        "quality_too_low": "答复质量持续低于阈值"
    }

    def __init__(self):
        """初始化对话管理器"""
        self.examiner_simulator = get_examiner_simulator()
        self.current_session: DialogueSession | None = None
        self.session_history: list[DialogueSession] = []

        logger.info("✅ 多轮对话管理器初始化完成")

    def start_dialogue_session(
        self,
        session_id: str,
        oa_text: str,
        claims: list[str],
        prior_art_analysis: dict
    ) -> DialogueSession:
        """
        开始新的对话会话

        Args:
            session_id: 会话ID
            oa_text: 审查意见全文
            claims: 权利要求列表
            prior_art_analysis: 对比文件分析结果

        Returns:
            对话会话对象
        """
        logger.info(f"🎬 开始对话会话: {session_id}")

        # 创建新会话
        session = DialogueSession(
            session_id=session_id,
            oa_text=oa_text,
            claims=claims,
            prior_art_analysis=prior_art_analysis
        )

        # 保存当前会话
        self.current_session = session
        self.session_history.append(session)

        # 生成初始审查意见（审查员第一轮发言）
        initial_review = self.examiner_simulator.simulate_initial_review(
            oa_text=oa_text,
            claims=claims,
            prior_art_analysis=prior_art_analysis
        )

        # 将初始审查意见作为审查员的第一轮
        session.add_turn(
            role="examiner",
            content=self._format_initial_review(initial_review),
            metadata={
                "type": "initial_review",
                "rejection_type": initial_review["rejection_type"],
                "strategy": initial_review["strategy"]
            }
        )

        logger.info(f"✅ 对话会话开始: {len(session.turns)} 轮")

        return session

    def process_applicant_response(
        self,
        applicant_response: str,
        session_id: str | None = None
    ) -> dict[str, Any]:
        """
        处理申请人的答复

        Args:
            applicant_response: 申请人的答复意见
            session_id: 会话ID（可选，默认使用当前会话）

        Returns:
            审查员的回应和对话状态
        """
        session = self._get_session(session_id)

        if not session:
            raise ValueError(f"会话不存在: {session_id}")

        # 添加申请人答复
        session.add_turn(
            role="applicant",
            content=applicant_response,
            metadata={
                "type": "response",
                "length": len(applicant_response)
            }
        )

        # 生成审查员的回应
        current_round = len([t for t in session.turns if t.role == "applicant"])

        if current_round >= self.MAX_ROUNDS:
            # 达到最大轮次，终止对话
            session.complete()
            return {
                "action": "terminate",
                "reason": self.TERMINATION_CONDITIONS["max_rounds_reached"],
                "final_evaluation": self._evaluate_final_response(
                    applicant_response,
                    session.turns
                )
            }

        # 生成审查员回应
        examiner_response = self.examiner_simulator.respond_to_applicant_argument(
            applicant_argument=applicant_response,
            prior_art_analysis=session.prior_art_analysis,
            round_number=current_round
        )

        # 添加审查员回应
        session.add_turn(
            role="examiner",
            content=self._format_examiner_response(examiner_response),
            metadata={
                "type": "rebuttal",
                "strategy": examiner_response["response_strategy"],
                "round": current_round
            }
        )

        # 检查是否应该终止对话
        termination_check = self._check_termination_conditions(session)

        if termination_check["should_terminate"]:
            session.complete()
            return {
                "action": "terminate",
                "reason": termination_check["reason"],
                "final_evaluation": termination_check.get("evaluation"),
                "examiner_response": examiner_response
            }

        # 继续对话
        return {
            "action": "continue",
            "round_number": current_round + 1,
            "examiner_response": examiner_response,
            "suggestions": self._generate_suggestions(session, examiner_response)
        }

    def get_dialogue_summary(
        self,
        session_id: str | None = None
    ) -> dict[str, Any]:
        """
        获取对话摘要

        Args:
            session_id: 会话ID（可选）

        Returns:
            对话摘要
        """
        session = self._get_session(session_id)

        if not session:
            return {"error": "会话不存在"}

        summary = {
            "session_id": session.session_id,
            "status": session.status,
            "total_turns": len(session.turns),
            "applicant_turns": len([t for t in session.turns if t.role == "applicant"]),
            "examiner_turns": len([t for t in session.turns if t.role == "examiner"]),
            "duration_minutes": self._calculate_duration(session),
            "key_topics": self._extract_key_topics(session),
            "progress_indicators": self._calculate_progress_indicators(session)
        }

        return summary

    def export_dialogue_transcript(
        self,
        session_id: str | None = None,
        output_path: str | None = None
    ) -> str:
        """
        导出对话记录

        Args:
            session_id: 会话ID
            output_path: 输出路径（可选）

        Returns:
            导出文件的路径
        """
        session = self._get_session(session_id)

        if not session:
            raise ValueError(f"会话不存在: {session_id}")

        # 生成对话记录
        transcript = self._generate_transcript(session)

        # 确定输出路径
        if not output_path:
            output_path = f"data/dialogue_transcripts/{session.session_id}.md"

        # 确保目录存在
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(transcript)

        logger.info(f"📄 对话记录已导出: {output_path}")

        return output_path

    def _get_session(self, session_id: str | None) -> DialogueSession | None:
        """获取会话"""
        if session_id:
            # 从历史记录中查找
            for session in self.session_history:
                if session.session_id == session_id:
                    return session
            return None
        else:
            # 返回当前会话
            return self.current_session

    def _format_initial_review(self, initial_review: dict) -> str:
        """格式化初始审查意见"""
        content = []

        content.append("# 审查意见\n")
        content.append(f"**驳回类型**: {initial_review['rejection_type']}\n")
        content.append(f"**论证策略**: {initial_review['strategy']}\n\n")

        content.append("## 具体质疑\n")

        for objection in initial_review["objections"]:
            content.append(f"### 权利要求{objection['claim_number']}\n")
            content.append(f"{objection['claim_text']}\n\n")

            for i, feature_objection in enumerate(objection["feature_objections"], 1):
                content.append(f"{i}. {feature_objection}\n")

            content.append(f"\n**结论**: {objection['conclusion']}\n\n")

        content.append("## 总体结论\n")
        content.append(initial_review["overall_conclusion"])

        return "\n".join(content)

    def _format_examiner_response(self, response: dict) -> str:
        """格式化审查员回应"""
        content = []

        content.append(f"# 审查员回应 (第{response['round_number']}轮)\n\n")

        rebuttal = response.get("rebuttal", {})

        if rebuttal.get("rebuttal_points"):
            content.append("## 反驳意见\n")
            for i, point in enumerate(rebuttal["rebuttal_points"], 1):
                content.append(f"{i}. {point}\n")
            content.append("\n")

        if response.get("remaining_concerns"):
            content.append("## 剩余关注点\n")
            for concern in response["remaining_concerns"]:
                content.append(f"- {concern}\n")
            content.append("\n")

        if response.get("suggestions"):
            content.append("## 改进建议\n")
            for suggestion in response["suggestions"]:
                content.append(f"- {suggestion}\n")
            content.append("\n")

        content.append(f"**态度**: {rebuttal.get('tone', 'strict')}\n")

        return "\n".join(content)

    def _check_termination_conditions(self, session: DialogueSession) -> dict[str, Any]:
        """检查终止条件"""
        # 条件1: 达到最大轮次
        if len([t for t in session.turns if t.role == "applicant"]) >= self.MAX_ROUNDS:
            return {
                "should_terminate": True,
                "reason": self.TERMINATION_CONDITIONS["max_rounds_reached"]
            }

        # 条件2: 连续两轮无实质性进展
        if self._check_no_progress(session):
            return {
                "should_terminate": True,
                "reason": self.TERMINATION_CONDITIONS["no_progress"]
            }

        # 条件3: 答复质量持续低于阈值
        if self._check_quality_too_low(session):
            return {
                "should_terminate": True,
                "reason": self.TERMINATION_CONDITIONS["quality_too_low"],
                "evaluation": self._evaluate_final_response(
                    session.turns[-1].content if session.turns else "",
                    session.turns
                )
            }

        return {"should_terminate": False}

    def _check_no_progress(self, session: DialogueSession) -> bool:
        """检查是否无实质性进展"""
        # 获取最近两轮申请人的答复
        applicant_turns = [t for t in session.turns if t.role == "applicant"]

        if len(applicant_turns) < 2:
            return False

        # 简化判断：如果答复长度差异小于20%，认为无进展
        last_two = applicant_turns[-2:]
        length_diff = abs(len(last_two[0].content) - len(last_two[1].content))
        avg_length = (len(last_two[0].content) + len(last_two[1].content)) / 2

        return (length_diff / avg_length) < 0.2

    def _check_quality_too_low(self, session: DialogueSession) -> bool:
        """检查答复质量是否持续低于阈值"""
        applicant_turns = [t for t in session.turns if t.role == "applicant"]

        if len(applicant_turns) < 2:
            return False

        # 评估最近两轮的答复质量
        scores = []
        for turn in applicant_turns[-2:]:
            evaluation = self.examiner_simulator.evaluate_final_response(
                applicant_response=turn.content,
                dialogue_history=session.turns
            )
            scores.append(evaluation["overall_score"])

        # 如果两轮都低于50分，认为质量持续过低
        return all(score < 50 for score in scores)

    def _evaluate_final_response(
        self,
        applicant_response: str,
        dialogue_history: list[DialogueTurn]
    ) -> dict:
        """评估最终答复"""
        return self.examiner_simulator.evaluate_final_response(
            applicant_response=applicant_response,
            dialogue_history=[t.to_dict() for t in dialogue_history]
        )

    def _generate_suggestions(
        self,
        session: DialogueSession,
        examiner_response: dict
    ) -> list[str]:
        """生成改进建议"""
        suggestions = []

        # 基于审查员的态度生成建议
        tone = examiner_response["rebuttal"]["tone"]

        if tone == "strict":
            suggestions.extend([
                "当前答复未能说服审查员，建议：",
                "1. 补充更详细的实验数据",
                "2. 深入分析技术机理",
                "3. 详细对比与对比文件的具体差异"
            ])
        elif tone == "moderate":
            suggestions.extend([
                "答复有一定说服力，但仍有改进空间：",
                "1. 补充对比实验数据",
                "2. 强化技术效果论证"
            ])
        elif tone == "flexible":
            suggestions.extend([
                "答复质量良好，建议：",
                "1. 保持当前论证深度",
                "2. 可适当补充细节"
            ])

        # 基于剩余关注点生成建议
        if examiner_response["remaining_concerns"]:
            suggestions.append("\n需要特别关注的问题：")
            for concern in examiner_response["remaining_concerns"]:
                suggestions.append(f"- {concern}")

        return suggestions

    def _calculate_duration(self, session: DialogueSession) -> float:
        """计算会话持续时间"""
        if session.end_time:
            delta = session.end_time - session.start_time
            return delta.total_seconds() / 60
        else:
            # 会话仍在进行
            delta = datetime.now() - session.start_time
            return delta.total_seconds() / 60

    def _extract_key_topics(self, session: DialogueSession) -> list[str]:
        """提取关键话题"""
        topics = set()

        for turn in session.turns:
            content = turn.content.lower()

            # 检测关键话题
            if "四要素" in content or "协同" in content:
                topics.add("四要素协同效应")
            if "预料不到" in content or "技术效果" in content:
                topics.add("技术效果")
            if "对比文件" in content:
                topics.add("对比文件对比")
            if "参数" in content or "数据" in content:
                topics.add("技术参数")

        return list(topics)

    def _calculate_progress_indicators(self, session: DialogueSession) -> dict[str, Any]:
        """计算进展指标"""
        applicant_turns = [t for t in session.turns if t.role == "applicant"]

        if not applicant_turns:
            return {
                "rounds": 0,
                "avg_response_length": 0,
                "trend": "no_data"
            }

        # 计算平均答复长度
        lengths = [len(t.content) for t in applicant_turns]
        avg_length = sum(lengths) / len(lengths)

        # 计算趋势
        if len(applicant_turns) >= 2:
            if lengths[-1] > lengths[-2]:
                trend = "increasing"
            elif lengths[-1] < lengths[-2]:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"

        return {
            "rounds": len(applicant_turns),
            "avg_response_length": avg_length,
            "trend": trend,
            "last_response_length": lengths[-1] if lengths else 0
        }

    def _generate_transcript(self, session: DialogueSession) -> str:
        """生成对话记录文本"""
        lines = []

        lines.append("# 审查意见答复对话记录\n")
        lines.append(f"**会话ID**: {session.session_id}\n")
        lines.append(f"**状态**: {session.status}\n")
        lines.append(f"**开始时间**: {session.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        if session.end_time:
            lines.append(f"**结束时间**: {session.end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        lines.append(f"**总轮次**: {len(session.turns)}\n\n")
        lines.append("---\n\n")

        # 生成对话内容
        for turn in session.turns:
            role_name = "申请人" if turn.role == "applicant" else "审查员"
            lines.append(f"## {role_name} - 第{turn.turn_number}轮\n")
            lines.append(f"{turn.content}\n\n")
            lines.append("---\n\n")

        return "\n".join(lines)


# 便捷函数
def get_dialogue_manager() -> DialogueManager:
    """获取对话管理器单例"""
    return DialogueManager()


# 测试代码
if __name__ == "__main__":
    # 测试对话管理器
    manager = get_dialogue_manager()

    # 开始对话会话
    session = manager.start_dialogue_session(
        session_id="test_session_001",
        oa_text="根据专利法第22条第3款，权利要求1不具备创造性。",
        claims=[
            "1. 一种吊水净化处理罗非鱼泥腥味的方法，包括盐水处理步骤。"
        ],
        prior_art_analysis={
            "d1": {
                "undisclosed_features": ["盐水处理"],
                "implementation": "对比文件使用清水处理"
            }
        }
    )

    print(f"✅ 对话会话已开始: {session.session_id}")
    print(f"   初始轮次: {len(session.turns)}")

    # 模拟申请人答复
    applicant_response = """
    尊敬的审查员：
    关于权利要求1的创造性，申请人认为：
    1. 对比文件未公开盐水处理步骤。
    2. 盐水处理产生了预料不到的技术效果。
    """

    result = manager.process_applicant_response(applicant_response)

    print("\n=== 审查员回应 ===")
    print(f"操作: {result['action']}")
    print(f"轮次: {result.get('round_number', 'N/A')}")
    if result['action'] == 'continue':
        print(f"建议数量: {len(result.get('suggestions', []))}")

    # 导出对话记录
    transcript_path = manager.export_dialogue_transcript(
        output_path="data/temp_dialogue_transcript.md"
    )

    print(f"\n📄 对话记录已导出: {transcript_path}")
