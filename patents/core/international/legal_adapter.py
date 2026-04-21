#!/usr/bin/env python3
"""
各国法律差异适配

提供主要国家/地区的专利法律差异信息。
"""
import logging
from dataclasses import dataclass
from typing import Dict, List, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CountryLawInfo:
    """国家法律信息"""
    country_code: str  # 国家代码
    country_name: str  # 国家名称
    language: str  # 官方语言
    patent_type: List[str]  # 支持的专利类型
    grace_period: bool  # 是否有宽限期
    grace_period_months: int  # 宽限期月数
    first_to_file: bool  # 先申请原则
    novelty_requirement: str  # 新颖性要求（绝对/相对）
    examination_system: str  # 审查制度
    term_years: int  # 保护期限（年）
    fees_currency: str  # 费用货币

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "country_code": self.country_code,
            "country_name": self.country_name,
            "language": self.language,
            "patent_type": self.patent_type,
            "grace_period": self.grace_period,
            "grace_period_months": self.grace_period_months,
            "first_to_file": self.first_to_file,
            "novelty_requirement": self.novelty_requirement,
            "examination_system": self.examination_system,
            "term_years": self.term_years,
            "fees_currency": self.fees_currency
        }


class LegalAdapter:
    """法律适配器"""

    def __init__(self):
        """初始化适配器"""
        self.country_laws = self._load_country_laws()
        logger.info("✅ 法律适配器初始化成功")

    def _load_country_laws(self) -> Dict[str, CountryLawInfo]:
        """加载各国法律信息"""
        return {
            "US": CountryLawInfo(
                country_code="US",
                country_name="美国",
                language="英语",
                patent_type=["发明", "植物", "外观"],
                grace_period=True,
                grace_period_months=12,
                first_to_file=True,
                novelty_requirement="相对",
                examination_system="实质审查",
                term_years=20,
                fees_currency="USD"
            ),
            "EP": CountryLawInfo(
                country_code="EP",
                country_name="欧洲",
                language="英语/法语/德语",
                patent_type=["发明"],
                grace_period=False,
                grace_period_months=0,
                first_to_file=True,
                novelty_requirement="绝对",
                examination_system="实质审查",
                term_years=20,
                fees_currency="EUR"
            ),
            "JP": CountryLawInfo(
                country_code="JP",
                country_name="日本",
                language="日语",
                patent_type=["发明", "实用新型"],
                grace_period=False,
                grace_period_months=0,
                first_to_file=True,
                novelty_requirement="绝对",
                examination_system="实质审查",
                term_years=20,
                fees_currency="JPY"
            ),
            "KR": CountryLawInfo(
                country_code="KR",
                country_name="韩国",
                language="韩语",
                patent_type=["发明", "实用新型", "外观"],
                grace_period=False,
                grace_period_months=0,
                first_to_file=True,
                novelty_requirement="绝对",
                examination_system="实质审查",
                term_years=20,
                fees_currency="KRW"
            ),
            "CN": CountryLawInfo(
                country_code="CN",
                country_name="中国",
                language="中文",
                patent_type=["发明", "实用新型", "外观"],
                grace_period=False,
                grace_period_months=0,
                first_to_file=True,
                novelty_requirement="绝对",
                examination_system="实质审查",
                term_years=20,
                fees_currency="CNY"
            ),
            "DE": CountryLawInfo(
                country_code="DE",
                country_name="德国",
                language="德语",
                patent_type=["发明", "实用新型"],
                grace_period=False,
                grace_period_months=0,
                first_to_file=True,
                novelty_requirement="绝对",
                examination_system="实质审查",
                term_years=20,
                fees_currency="EUR"
            ),
            "GB": CountryLawInfo(
                country_code="GB",
                country_name="英国",
                language="英语",
                patent_type=["发明"],
                grace_period=False,
                grace_period_months=0,
                first_to_file=True,
                novelty_requirement="绝对",
                examination_system="实质审查",
                term_years=20,
                fees_currency="GBP"
            ),
            "FR": CountryLawInfo(
                country_code="FR",
                country_name="法国",
                language="法语",
                patent_type=["发明", "实用新型"],
                grace_period=False,
                grace_period_months=0,
                first_to_file=True,
                novelty_requirement="绝对",
                examination_system="实质审查",
                term_years=20,
                fees_currency="EUR"
            ),
            "CA": CountryLawInfo(
                country_code="CA",
                country_name="加拿大",
                language="英语/法语",
                patent_type=["发明", "实用新型", "外观"],
                grace_period=True,
                grace_period_months=12,
                first_to_file=True,
                novelty_requirement="相对",
                examination_system="实质审查",
                term_years=20,
                fees_currency="CAD"
            ),
            "AU": CountryLawInfo(
                country_code="AU",
                country_name="澳大利亚",
                language="英语",
                patent_type=["发明", "实用新型", "外观"],
                grace_period=False,
                grace_period_months=0,
                first_to_file=True,
                novelty_requirement="绝对",
                examination_system="实质审查",
                term_years=20,
                fees_currency="AUD"
            )
        }

    def get_country_info(self, country_code: str) -> Optional[CountryLawInfo]:
        """获取国家法律信息"""
        return self.country_laws.get(country_code.upper())

    def compare_countries(self, country_codes: List[str]) -> Dict[str, Any]:
        """对比多个国家的法律"""
        countries = []
        for code in country_codes:
            info = self.get_country_info(code)
            if info:
                countries.append(info.to_dict())

        return {
            "countries": countries,
            "total": len(countries),
            "grace_period_countries": [c["country_code"] for c in countries if c["grace_period"]],
            "absolute_novelty_countries": [c["country_code"] for c in countries if c["novelty_requirement"] == "绝对"]
        }


if __name__ == "__main__":
    adapter = LegalAdapter()

    # 获取美国信息
    us_info = adapter.get_country_info("US")
    print(f"\n🇺🇸 美国专利法:")
    print(f"   语言: {us_info.language}")
    print(f"   宽限期: {us_info.grace_period_months}个月" if us_info.grace_period else "   宽限期: 无")
    print(f"   新颖性: {us_info.novelty_requirement}")
    print(f"   保护期限: {us_info.term_years}年")

    # 对比多个国家
    comparison = adapter.compare_countries(["US", "EP", "JP", "CN"])
    print(f"\n📊 多国对比:")
    print(f"   国家数: {comparison['total']}")
    print(f"   有宽限期: {', '.join(comparison['grace_period_countries'])}")
