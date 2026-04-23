#!/usr/bin/env python3
"""
条款生成器

生成专利许可协议的核心条款。
"""
import logging
from dataclasses import dataclass
from typing import Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class LicenseTerms:
    """许可条款"""
    license_type: str  # exclusive, sole, non-exclusive, sub-license
    license_scope: str  # territory, duration, field
    royalty_rate: float
    upfront_fee: float
    minimum_guarantee: float
    payment_terms: str
    rights: list[str]
    obligations: list[str]
    restrictions: list[str]
    termination_conditions: list[str]

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "license_type": self.license_type,
            "license_scope": self.license_scope,
            "royalty_rate": self.royalty_rate,
            "upfront_fee": self.upfront_fee,
            "minimum_guarantee": self.minimum_guarantee,
            "payment_terms": self.payment_terms,
            "rights": self.rights,
            "obligations": self.obligations,
            "restrictions": self.restrictions,
            "termination_conditions": self.termination_conditions
        }


class ClauseGenerator:
    """条款生成器"""

    def __init__(self):
        """初始化条款生成器"""
        logger.info("✅ 条款生成器初始化成功")

    def generate_terms(
        self,
        patent_valuation: dict[str, Any],
        license_requirements: dict[str, Any]
    ) -> LicenseTerms:
        """
        生成许可条款

        Args:
            patent_valuation: 专利估值结果
            license_requirements: 许可需求

        Returns:
            LicenseTerms对象
        """
        logger.info("📝 开始生成许可条款")

        # 确定许可类型
        license_type = license_requirements.get("license_type", "non-exclusive")

        # 确定提成率
        royalty_rate = patent_valuation.get("recommended_royalty_rate", 0.05)

        # 计算预付费用
        value_range = patent_valuation.get("estimated_value_range", (50, 100))
        upfront_fee = (value_range[0] + value_range[1]) / 2 * 0.1  # 10%作为预付

        # 生成权利条款
        rights = self._generate_rights(license_type, license_requirements)

        # 生成义务条款
        obligations = self._generate_obligations(license_type)

        # 生成限制条款
        restrictions = self._generate_restrictions(license_type)

        # 终止条件
        termination = self._generate_termination_conditions()

        terms = LicenseTerms(
            license_type=license_type,
            license_scope=license_requirements.get("scope", "全球范围"),
            royalty_rate=royalty_rate,
            upfront_fee=upfront_fee,
            minimum_guarantee=upfront_fee * 2,
            payment_terms="按季度支付",
            rights=rights,
            obligations=obligations,
            restrictions=restrictions,
            termination_conditions=termination
        )

        logger.info("✅ 许可条款生成完成")
        logger.info(f"   许可类型: {license_type}")
        logger.info(f"   提成率: {royalty_rate:.1%}")

        return terms

    def _generate_rights(self, license_type: str, requirements: dict[str, Any]) -> list[str]:
        """生成权利条款"""
        rights = [
            "在许可范围内使用专利技术的权利",
            "制造、使用、销售许可产品的权利",
            "进口许可产品的权利"
        ]

        if license_type == "exclusive":
            rights.append("独占性权利，许可方不得再许可第三方")
        elif license_type == "sole":
            rights.append("排他性权利，许可方自身保留使用权")
        elif license_type == "sub-license":
            rights.append("分许可权利，可向第三方发放分许可")

        return rights

    def _generate_obligations(self, license_type: str) -> list[str]:
        """生成义务条款"""
        obligations = [
            "按时支付许可使用费",
            "维持专利的有效性",
            "不得挑战专利的有效性"
        ]

        if license_type == "exclusive":
            obligations.extend([
                "尽最大努力开发市场",
                "定期报告销售情况"
            ])

        return obligations

    def _generate_restrictions(self, license_type: str) -> list[str]:
        """生成限制条款"""
        restrictions = [
            "许可范围限于约定的技术领域",
            "不得超出专利保护范围"
        ]

        if license_type != "exclusive":
            restrictions.append("许可方有权向其他方发放许可")

        return restrictions

    def _generate_termination_conditions(self) -> list[str]:
        """生成终止条件"""
        return [
            "专利期满或无效",
            "一方严重违约",
            "破产或清算",
            "双方协商一致"
        ]
