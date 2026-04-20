#!/usr/bin/env python3
"""
专利价值评估器

动态评估专利价值，提供维持决策支持。
"""
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional

try:
    from .patent_list_manager import PatentRecord, PatentType, PatentStatus
    from .patent_classifier import PatentGrade
except ImportError:
    from core.patent.portfolio.patent_list_manager import PatentRecord, PatentType, PatentStatus
    from core.patent.portfolio.patent_classifier import PatentGrade

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ValueAssessment:
    """价值评估结果"""
    patent_id: str
    current_value: float  # 当前价值 (0-100)
    value_trend: str  # 价值趋势 (上升/稳定/下降)
    market_potential: float  # 市场潜力 (0-1)
    maintenance_cost: float  # 维持成本
    roi_score: float  # 投资回报率评分
    recommendation: str  # 维持建议

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "patent_id": self.patent_id,
            "current_value": self.current_value,
            "value_trend": self.value_trend,
            "market_potential": self.market_potential,
            "maintenance_cost": self.maintenance_cost,
            "roi_score": self.roi_score,
            "recommendation": self.recommendation
        }


class ValueAssessor:
    """专利价值评估器"""

    def __init__(self):
        """初始化评估器"""
        logger.info("✅ 专利价值评估器初始化成功")

    def assess_value(
        self,
        patent: PatentRecord,
        grade: PatentGrade,
        market_data: Optional[Dict[str, Any]] = None
    ) -> ValueAssessment:
        """
        评估专利价值

        Args:
            patent: 专利记录
            grade: 专利等级
            market_data: 市场数据（可选）

        Returns:
            ValueAssessment对象
        """
        logger.info(f"💰 评估专利价值: {patent.patent_id}")

        # 计算当前价值
        current_value = self._calculate_current_value(patent, grade)

        # 判断价值趋势
        value_trend = self._determine_value_trend(patent, market_data)

        # 评估市场潜力
        market_potential = self._assess_market_potential(patent, market_data)

        # 计算维持成本
        maintenance_cost = self._calculate_maintenance_cost(patent)

        # 计算投资回报率
        roi_score = self._calculate_roi(current_value, maintenance_cost)

        # 生成建议
        recommendation = self._generate_recommendation(
            current_value,
            roi_score,
            maintenance_cost
        )

        return ValueAssessment(
            patent_id=patent.patent_id,
            current_value=current_value,
            value_trend=value_trend,
            market_potential=market_potential,
            maintenance_cost=maintenance_cost,
            roi_score=roi_score,
            recommendation=recommendation
        )

    def _calculate_current_value(
        self,
        patent: PatentRecord,
        grade: PatentGrade
    ) -> float:
        """计算当前价值"""
        base_score = patent.value_score * 50

        # 根据等级调整
        grade_bonus = {
            PatentGrade.CORE: 30,
            PatentGrade.IMPORTANT: 20,
            PatentGrade.GENERAL: 10,
            PatentGrade.LOW_VALUE: 0
        }.get(grade, 0)

        # 根据专利类型调整
        type_bonus = {
            PatentType.INVENTION: 15,
            PatentType.UTILITY_MODEL: 8,
            PatentType.DESIGN: 5
        }.get(patent.patent_type, 0)

        # 根据状态调整
        status_bonus = {
            PatentStatus.MAINTAINED: 5,
            PatentStatus.GRANTED: 5,
            PatentStatus.EXAMINING: 2
        }.get(patent.status, 0)

        total = base_score + grade_bonus + type_bonus + status_bonus
        return min(100, total)

    def _determine_value_trend(
        self,
        patent: PatentRecord,
        market_data: Optional[Dict[str, Any]]
    ) -> str:
        """判断价值趋势"""
        if not market_data:
            return "稳定"

        growth_rate = market_data.get("market_growth", 0)
        if growth_rate > 0.2:
            return "上升"
        elif growth_rate < -0.1:
            return "下降"
        else:
            return "稳定"

    def _assess_market_potential(
        self,
        patent: PatentRecord,
        market_data: Optional[Dict[str, Any]]
    ) -> float:
        """评估市场潜力"""
        if not market_data:
            return 0.5

        # 综合多个因素
        market_size = market_data.get("market_size", 0.5)
        competition = market_data.get("competition", 0.5)
        growth = market_data.get("market_growth", 0.5)

        return (market_size + (1 - competition) + growth) / 3

    def _calculate_maintenance_cost(self, patent: PatentRecord) -> float:
        """计算维持成本"""
        # 年费 + 管理费用
        annual_fee = patent.annual_fee_amount or 0
        management_fee = 500  # 假设每年500元管理费
        return annual_fee + management_fee

    def _calculate_roi(self, value: float, cost: float) -> float:
        """计算投资回报率"""
        if cost == 0:
            return 0.5
        return min(1.0, value / (cost * 10))  # 简化的ROI计算

    def _generate_recommendation(
        self,
        value: float,
        roi: float,
        cost: float
    ) -> str:
        """生成建议"""
        if value >= 70 and roi >= 0.6:
            return "强烈建议维持"
        elif value >= 50 and roi >= 0.4:
            return "建议维持"
        elif value >= 30 and roi >= 0.2:
            return "可以考虑维持"
        else:
            return "建议放弃或转让"


if __name__ == "__main__":
    import asyncio
    from .patent_list_manager import PatentRecord, PatentType, PatentStatus
    from .patent_classifier import PatentGrade

    assessor = ValueAssessor()

    patent = PatentRecord(
        patent_id="CN123456789A",
        patent_type=PatentType.INVENTION,
        title="智能控制系统",
        application_date="2020-01-15",
        status=PatentStatus.MAINTAINED,
        annual_fee_amount=1200,
        value_score=0.8
    )

    result = assessor.assess_value(patent, PatentGrade.CORE)

    print(f"\n💰 价值评估结果:")
    print(f"   当前价值: {result.current_value:.1f}")
    print(f"   价值趋势: {result.value_trend}")
    print(f"   市场潜力: {result.market_potential:.2f}")
    print(f"   维持成本: {result.maintenance_cost:.0f}元")
    print(f"   ROI评分: {result.roi_score:.2f}")
    print(f"   建议: {result.recommendation}")
