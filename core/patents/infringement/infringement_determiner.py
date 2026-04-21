#!/usr/bin/env python3
"""
侵权判定器

基于全面覆盖原则判定是否构成侵权。
"""
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any

try:
    from .feature_comparator import FeatureComparison
except ImportError:
    from patents.core.infringement.feature_comparator import FeatureComparison

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InfringementType(Enum):
    """侵权类型"""
    LITERAL = "literal"  # 字面侵权
    DOCTRINE_OF_EQUIVALENTS = "doe"  # 等同侵权
    NO_INFRINGEMENT = "none"  # 不侵权
    UNCERTAIN = "uncertain"  # 不确定


@dataclass
class InfringementConclusion:
    """侵权判定结论"""
    claim_number: int
    infringement_type: InfringementType
    infringement_found: bool
    confidence: float
    reasoning: str
    missing_features: List[str]
    risk_level: str  # high, medium, low

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "claim_number": self.claim_number,
            "infringement_type": self.infringement_type.value,
            "infringement_found": self.infringement_found,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "missing_features": self.missing_features,
            "risk_level": self.risk_level
        }


@dataclass
class InfringementResult:
    """侵权判定结果"""
    patent_id: str
    product_name: str
    conclusions: List[InfringementConclusion]
    overall_infringement: bool
    overall_risk: str
    legal_basis: List[str]
    recommendations: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "patent_id": self.patent_id,
            "product_name": self.product_name,
            "conclusions": [c.to_dict() for c in self.conclusions],
            "overall_infringement": self.overall_infringement,
            "overall_risk": self.overall_risk,
            "legal_basis": self.legal_basis,
            "recommendations": self.recommendations,
            "metadata": self.metadata
        }


class InfringementDeterminer:
    """侵权判定器"""

    # 全面覆盖原则阈值
    COVERAGE_THRESHOLD_LITERAL = 1.0  # 字面侵权需要100%覆盖
    COVERAGE_THRESHOLD_DOE = 0.8  # 等同侵权需要80%覆盖

    def __init__(self):
        """初始化判定器"""
        logger.info("✅ 侵权判定器初始化成功")

    def determine(
        self,
        comparisons: List[FeatureComparison],
        patent_id: str,
        product_name: str
    ) -> InfringementResult:
        """
        判定是否构成侵权

        Args:
            comparisons: 特征对比结果列表
            patent_id: 专利号
            product_name: 产品名称

        Returns:
            InfringementResult对象
        """
        logger.info(f"⚖️ 开始侵权判定分析")
        logger.info(f"   专利: {patent_id}")
        logger.info(f"   产品: {product_name}")

        conclusions = []

        # 对每条权利要求进行判定
        for comparison in comparisons:
            conclusion = self._determine_single_claim(comparison)
            conclusions.append(conclusion)

        # 综合判定
        overall_infringement, overall_risk = self._determine_overall(conclusions)

        # 生成法律依据和建议
        legal_basis = self._generate_legal_basis(conclusions)
        recommendations_list = self._generate_recommendations(conclusions, overall_risk)

        result = InfringementResult(
            patent_id=patent_id,
            product_name=product_name,
            conclusions=conclusions,
            overall_infringement=overall_infringement,
            overall_risk=overall_risk,
            legal_basis=legal_basis,
            recommendations=recommendations_list
        )

        logger.info(f"✅ 侵权判定完成")
        logger.info(f"   总体侵权: {'是' if overall_infringement else '否'}")
        logger.info(f"   风险等级: {overall_risk}")

        return result

    def _determine_single_claim(self, comparison: FeatureComparison) -> InfringementConclusion:
        """
        判定单条权利要求是否被侵权

        Args:
            comparison: 特征对比结果

        Returns:
            InfringementConclusion对象
        """
        claim_number = comparison.claim_number
        coverage = comparison.coverage_ratio
        missing = comparison.missing_features

        # 提取缺失特征列表
        missing_features = [
            m.claim_feature_text
            for m in comparison.mappings
            if m.correspondence_type == "missing"
        ]

        # 判定侵权类型
        if coverage >= self.COVERAGE_THRESHOLD_LITERAL:
            # 字面侵权
            infringement_type = InfringementType.LITERAL
            infringement_found = True
            confidence = 0.95
            reasoning = "产品完全覆盖权利要求的所有技术特征，构成字面侵权。"
            risk_level = "high"

        elif coverage >= self.COVERAGE_THRESHOLD_DOE:
            # 可能构成等同侵权
            # 检查缺失特征是否为核心创新点
            if missing <= 1:  # 只缺失1个特征
                infringement_type = InfringementType.DOCTRINE_OF_EQUIVALENTS
                infringement_found = True
                confidence = 0.75
                reasoning = f"产品覆盖{coverage:.1%}的权利要求特征，缺失特征可能适用等同原则。"
                risk_level = "medium"
            else:
                infringement_type = InfringementType.UNCERTAIN
                infringement_found = False
                confidence = 0.5
                reasoning = f"产品覆盖{coverage:.1%}的权利要求特征，但缺失{missing}个特征，需进一步分析。"
                risk_level = "medium"

        else:
            # 不侵权
            infringement_type = InfringementType.NO_INFRINGEMENT
            infringement_found = False
            confidence = 0.85
            reasoning = f"产品仅覆盖{coverage:.1%}的权利要求特征，未满足全面覆盖原则，不构成侵权。"
            risk_level = "low"

        conclusion = InfringementConclusion(
            claim_number=claim_number,
            infringement_type=infringement_type,
            infringement_found=infringement_found,
            confidence=confidence,
            reasoning=reasoning,
            missing_features=missing_features,
            risk_level=risk_level
        )

        logger.info(f"   权利要求 {claim_number}: {infringement_type.value} (置信度: {confidence:.2%})")

        return conclusion

    def _determine_overall(self, conclusions: List[InfringementConclusion]) -> tuple[bool, str]:
        """
        综合判定总体侵权情况

        Args:
            conclusions: 各权利要求的判定结论

        Returns:
            (是否侵权, 风险等级)
        """
        # 检查是否有独立权利要求被侵权
        independent_infringed = any(
            c.infringement_found and c.claim_number == 1
            for c in conclusions
        )

        # 检查高风险案件数量
        high_risk_count = sum(1 for c in conclusions if c.risk_level == "high")
        medium_risk_count = sum(1 for c in conclusions if c.risk_level == "medium")

        # 判定总体风险
        if independent_infringed:
            overall_infringement = True
            overall_risk = "high"
        elif high_risk_count > 0:
            overall_infringement = True
            overall_risk = "high"
        elif medium_risk_count >= 2:
            overall_infringement = True
            overall_risk = "medium"
        elif medium_risk_count > 0:
            overall_infringement = False
            overall_risk = "medium"
        else:
            overall_infringement = False
            overall_risk = "low"

        return overall_infringement, overall_risk

    def _generate_legal_basis(self, conclusions: List[InfringementConclusion]) -> List[str]:
        """
        生成法律依据

        Args:
            conclusions: 判定结论

        Returns:
            法律依据列表
        """
        legal_basis = []

        # 专利法第11条（发明和实用新型专利权）
        legal_basis.append("《专利法》第11条：发明和实用新型专利权被授予后，除本法另有规定的以外，任何单位或者个人未经专利权人许可，都不得实施其专利。")

        # 根据侵权类型添加法律依据
        has_literal = any(c.infringement_type == InfringementType.LITERAL for c in conclusions)
        has_doe = any(c.infringement_type == InfringementType.DOCTRINE_OF_EQUIVALENTS for c in conclusions)

        if has_literal:
            legal_basis.append("字面侵权：涉案产品包含了权利要求记载的全部技术特征，落入专利权的保护范围。")

        if has_doe:
            legal_basis.append("等同侵权：根据最高人民法院《关于审理专利纠纷案件应用法律若干问题的解释》，涉案产品虽然与权利要求记载的技术特征不完全相同，但属于以基本相同的手段，实现基本相同的功能，达到基本相同的效果，并且本领域普通技术人员无需经过创造性劳动就能够联想到的特征。")

        return legal_basis

    def _generate_recommendations(
        self,
        conclusions: List[InfringementConclusion],
        overall_risk: str
    ) -> List[str]:
        """
        生成建议措施

        Args:
            conclusions: 判定结论
            overall_risk: 总体风险

        Returns:
            建议列表
        """
        recommendations = []

        if overall_risk == "high":
            recommendations.extend([
                "建议立即停止涉嫌侵权产品的生产、销售、许诺销售、使用或进口行为",
                "建议进行专利无效宣告请求，评估目标专利的稳定性",
                "建议寻求专利许可，与专利权人协商许可事宜",
                "建议对产品进行规避设计，避免落入专利保护范围"
            ])

        elif overall_risk == "medium":
            recommendations.extend([
                "建议进一步分析技术特征，确认是否适用等同原则",
                "建议检索对比文件，评估专利无效宣告的成功概率",
                "建议咨询专业专利律师，制定应对策略",
                "建议保留相关技术文档，为潜在诉讼做准备"
            ])

        else:  # low risk
            recommendations.extend([
                "当前侵权风险较低，但仍需持续关注专利动态",
                "建议建立专利预警机制，定期检索相关专利",
                "建议完善自主创新，建立自己的专利布局"
            ])

        return recommendations
