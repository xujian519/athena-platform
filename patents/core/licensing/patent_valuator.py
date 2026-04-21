#!/usr/bin/env python3
"""
专利估值器

评估专利的市场价值，为许可协议提供定价依据。
"""
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ValuationResult:
    """估值结果"""
    patent_id: str
    estimated_value_range: tuple[float, float]  # (最低, 最高)
    recommended_royalty_rate: float  # 建议提成率
    confidence_level: str  # high, medium, low
    valuation_factors: Dict[str, Any] = field(default_factory=dict)
    market_analysis: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "patent_id": self.patent_id,
            "estimated_value_range": self.estimated_value_range,
            "recommended_royalty_rate": self.recommended_royalty_rate,
            "confidence_level": self.confidence_level,
            "valuation_factors": self.valuation_factors,
            "market_analysis": self.market_analysis
        }


class PatentValuator:
    """专利估值器"""

    def __init__(self):
        """初始化估值器"""
        logger.info("✅ 专利估值器初始化成功")

    def evaluate_patent(
        self,
        patent_id: str,
        patent_info: Dict[str, Any],
        market_data: Dict[str, Any] = None
    ) -> ValuationResult:
        """
        评估专利价值

        Args:
            patent_id: 专利号
            patent_info: 专利信息
            market_data: 市场数据

        Returns:
            ValuationResult对象
        """
        logger.info(f"💰 开始评估专利价值: {patent_id}")

        # 提取专利类型
        patent_type = patent_info.get("patent_type", "invention")
        technology_field = patent_info.get("technology_field", "未知")
        claims_count = patent_info.get("claims_count", 1)

        # 计算价值分数
        value_score = self._calculate_value_score(patent_info)

        # 确定价值区间
        value_range = self._determine_value_range(value_score, patent_type)

        # 计算建议提成率
        royalty_rate = self._calculate_royalty_rate(value_score, patent_type)

        # 市场分析
        market_analysis = self._analyze_market(patent_info, market_data)

        result = ValuationResult(
            patent_id=patent_id,
            estimated_value_range=value_range,
            recommended_royalty_rate=royalty_rate,
            confidence_level="medium",
            valuation_factors={
                "patent_type": patent_type,
                "technology_field": technology_field,
                "claims_count": claims_count,
                "value_score": value_score
            },
            market_analysis=market_analysis
        )

        logger.info(f"✅ 专利估值完成")
        logger.info(f"   价值区间: {value_range[0]:.0f}万 - {value_range[1]:.0f}万元")
        logger.info(f"   建议提成率: {royalty_rate:.1%}")

        return result

    def _calculate_value_score(self, patent_info: Dict[str, Any]) -> float:
        """计算价值分数 (0-100)"""
        score = 50.0  # 基础分

        # 专利类型加分
        if patent_info.get("patent_type") == "invention":
            score += 20
        elif patent_info.get("patent_type") == "utility_model":
            score += 10

        # 权利要求数量
        claims_count = patent_info.get("claims_count", 1)
        score += min(claims_count * 3, 15)

        # 技术领域热度
        hot_fields = ["人工智能", "生物技术", "新能源", "半导体"]
        if any(field in patent_info.get("technology_field", "") for field in hot_fields):
            score += 10

        return min(score, 100.0)

    def _determine_value_range(self, score: float, patent_type: str) -> tuple[float, float]:
        """确定价值区间（万元）"""
        base_value = score * 2  # 基础价值

        if patent_type == "invention":
            low = base_value * 0.8
            high = base_value * 1.5
        else:
            low = base_value * 0.5
            high = base_value * 1.0

        return (low, high)

    def _calculate_royalty_rate(self, score: float, patent_type: str) -> float:
        """计算建议提成率"""
        if patent_type == "invention":
            # 发明专利：3%-10%
            rate = 0.03 + (score / 100) * 0.07
        else:
            # 实用新型：1%-5%
            rate = 0.01 + (score / 100) * 0.04

        return round(rate, 3)

    def _analyze_market(self, patent_info: Dict[str, Any], market_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """分析市场情况"""
        return {
            "market_size": "中等" if market_data else "未知",
            "competition_level": "中等",
            "growth_potential": "良好",
            "licensing_demand": "存在需求"
        }
