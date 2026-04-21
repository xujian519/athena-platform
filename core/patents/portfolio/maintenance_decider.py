#!/usr/bin/env python3
"""
专利维持决策器

基于价值评估和成本分析，提供专利维持决策建议。
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Any, Optional

try:
    from .patent_list_manager import PatentRecord, PatentStatus
    from .value_assessor import ValueAssessment
except ImportError:
    from patents.core.portfolio.patent_list_manager import PatentRecord, PatentStatus
    from patents.core.portfolio.value_assessor import ValueAssessment

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DecisionType(Enum):
    """决策类型"""
    MAINTAIN = "maintain"  # 维持
    ABANDON = "abandon"  # 放弃
    SELL = "sell"  # 转让
    LICENSE = "license"  # 许可
    MONITOR = "monitor"  # 观察


@dataclass
class MaintenanceDecision:
    """维持决策"""
    patent_id: str
    decision: DecisionType
    confidence: float  # 决策置信度 (0-1)
    reason: str  # 决策理由
    deadline: str  # 决策期限
    action_items: List[str]  # 行动项

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "patent_id": self.patent_id,
            "decision": self.decision.value,
            "confidence": self.confidence,
            "reason": self.reason,
            "deadline": self.deadline,
            "action_items": self.action_items
        }


class MaintenanceDecisionMaker:
    """专利维持决策器"""

    def __init__(self):
        """初始化决策器"""
        logger.info("✅ 专利维持决策器初始化成功")

    def make_decision(
        self,
        patent: PatentRecord,
        value_assessment: ValueAssessment
    ) -> MaintenanceDecision:
        """
        做出维持决策

        Args:
            patent: 专利记录
            value_assessment: 价值评估

        Returns:
            MaintenanceDecision对象
        """
        logger.info(f"🎯 制定维持决策: {patent.patent_id}")

        # 综合评估
        decision = self._determine_decision(patent, value_assessment)
        confidence = self._calculate_confidence(patent, value_assessment)
        reason = self._generate_reason(patent, value_assessment, decision)
        deadline = self._calculate_deadline(patent)
        action_items = self._generate_action_items(decision)

        return MaintenanceDecision(
            patent_id=patent.patent_id,
            decision=decision,
            confidence=confidence,
            reason=reason,
            deadline=deadline,
            action_items=action_items
        )

    def _determine_decision(
        self,
        patent: PatentRecord,
        assessment: ValueAssessment
    ) -> DecisionType:
        """确定决策类型"""
        # 高价值 + 高ROI -> 维持
        if assessment.current_value >= 70 and assessment.roi_score >= 0.6:
            return DecisionType.MAINTAIN

        # 中等价值 + 中等ROI -> 维持或观察
        if assessment.current_value >= 50 and assessment.roi_score >= 0.4:
            return DecisionType.MONITOR

        # 低价值 + 低ROI -> 放弃或许可
        if assessment.current_value < 30 or assessment.roi_score < 0.2:
            # 如果还有许可价值，考虑许可
            if assessment.market_potential > 0.5:
                return DecisionType.LICENSE
            else:
                return DecisionType.ABANDON

        # 默认观察
        return DecisionType.MONITOR

    def _calculate_confidence(
        self,
        patent: PatentRecord,
        assessment: ValueAssessment
    ) -> float:
        """计算决策置信度"""
        confidence = 0.5

        # 价值评估越高，置信度越高
        confidence += assessment.current_value / 200

        # 有效专利置信度高
        if patent.status == PatentStatus.MAINTAINED:
            confidence += 0.1

        # 有明确的年费信息，置信度高
        if patent.annual_fee_amount:
            confidence += 0.1

        return min(1.0, confidence)

    def _generate_reason(
        self,
        patent: PatentRecord,
        assessment: ValueAssessment,
        decision: DecisionType
    ) -> str:
        """生成决策理由"""
        reasons = {
            DecisionType.MAINTAIN: f"当前价值{assessment.current_value:.1f}分，ROI评分{assessment.roi_score:.2f}，建议维持",
            DecisionType.MONITOR: f"当前价值{assessment.current_value:.1f}分，建议观察后续发展",
            DecisionType.ABANDON: f"当前价值{assessment.current_value:.1f}分，ROI较低，建议放弃",
            DecisionType.LICENSE: f"当前价值{assessment.current_value:.1f}分，但市场潜力{assessment.market_potential:.2f}，可考虑许可",
            DecisionType.SELL: f"当前价值{assessment.current_value:.1f}分，建议考虑转让"
        }
        return reasons.get(decision, "建议进一步评估")

    def _calculate_deadline(self, patent: PatentRecord) -> str:
        """计算决策期限"""
        if patent.annual_fee_due:
            # 年费缴纳前30天为决策期限
            due_date = datetime.strptime(patent.annual_fee_due, "%Y-%m-%d")
            deadline = due_date - timedelta(days=30)
            return deadline.strftime("%Y-%m-%d")
        else:
            # 默认30天内
            deadline = datetime.now() + timedelta(days=30)
            return deadline.strftime("%Y-%m-%d")

    def _generate_action_items(self, decision: DecisionType) -> List[str]:
        """生成行动项"""
        actions = {
            DecisionType.MAINTAIN: [
                "按时缴纳下一年度年费",
                "定期监控专利状态",
                "关注相关技术发展"
            ],
            DecisionType.MONITOR: [
                "评估市场变化",
                "监控竞争对手动态",
                "定期重新评估价值"
            ],
            DecisionType.ABANDON: [
                "确认放弃决定",
                "办理放弃手续",
                "清理相关记录"
            ],
            DecisionType.LICENSE: [
                "寻找潜在被许可方",
                "评估许可价值",
                "准备许可协议"
            ],
            DecisionType.SELL: [
                "评估专利市场价值",
                "寻找潜在买家",
                "准备转让材料"
            ]
        }
        return actions.get(decision, [])


if __name__ == "__main__":
    import asyncio
    from .patent_list_manager import PatentRecord, PatentType, PatentStatus
    from .value_assessor import ValueAssessor, ValueAssessor
    from .patent_classifier import PatentGrade

    decision_maker = MaintenanceDecisionMaker()
    assessor = ValueAssessor()

    patent = PatentRecord(
        patent_id="CN123456789A",
        patent_type=PatentType.INVENTION,
        title="智能控制系统",
        application_date="2020-01-15",
        status=PatentStatus.MAINTAINED,
        annual_fee_due="2026-03-20",
        annual_fee_amount=1200,
        value_score=0.8
    )

    assessment = assessor.assess_value(patent, PatentGrade.CORE)
    decision = decision_maker.make_decision(patent, assessment)

    print(f"\n🎯 维持决策:")
    print(f"   决策: {decision.decision.value}")
    print(f"   置信度: {decision.confidence:.2f}")
    print(f"   理由: {decision.reason}")
    print(f"   决策期限: {decision.deadline}")
    print(f"   行动项:")
    for action in decision.action_items:
        print(f"      - {action}")
