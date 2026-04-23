#!/usr/bin/env python3
"""
许可协议主控制器

整合所有模块，提供完整的许可协议起草功能。
"""
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

try:
    from .clause_generator import ClauseGenerator
    from .patent_valuator import PatentValuator
except ImportError:
    from core.patents.licensing.clause_generator import ClauseGenerator
    from core.patents.licensing.patent_valuator import PatentValuator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class LicensingOptions:
    """许可协议选项"""
    agreement_type: str = "standard"  # standard, simple, detailed
    include_exhibits: bool = True
    include_english: bool = False


@dataclass
class LicensingResult:
    """许可协议起草结果"""
    patent_id: str
    licensor: str
    licensee: str
    valuation: dict[str, Any]
    terms: dict[str, Any]
    agreement_text: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "patent_id": self.patent_id,
            "licensor": self.licensor,
            "licensee": self.licensee,
            "valuation": self.valuation,
            "terms": self.terms,
            "agreement_text": self.agreement_text,
            "metadata": self.metadata
        }


class LicensingDrafting:
    """许可协议起草主控制器"""

    def __init__(self):
        """初始化控制器"""
        self.valuator = PatentValuator()
        self.clause_generator = ClauseGenerator()
        logger.info("✅ 许可协议起草主控制器初始化成功")

    async def draft_agreement(
        self,
        patent_id: str,
        patent_info: dict[str, Any],
        licensor_info: dict[str, str],
        licensee_info: dict[str, str],
        license_requirements: dict[str, Any],
        options: LicensingOptions | None = None
    ) -> LicensingResult:
        """起草许可协议"""
        logger.info(f"📝 开始起草许可协议: {patent_id}")

        # 步骤1: 专利估值
        valuation = self.valuator.evaluate_patent(patent_id, patent_info)

        # 步骤2: 生成条款
        terms = self.clause_generator.generate_terms(
            valuation.to_dict(),
            license_requirements
        )

        # 步骤3: 撰写协议
        agreement_text = self._write_agreement(
            patent_id,
            licensor_info,
            licensee_info,
            terms,
            valuation,
            license_requirements
        )

        result = LicensingResult(
            patent_id=patent_id,
            licensor=licensor_info.get("name", "许可方"),
            licensee=licensee_info.get("name", "被许可方"),
            valuation=valuation.to_dict(),
            terms=terms.to_dict(),
            agreement_text=agreement_text,
            metadata={
                "drafting_date": datetime.now().strftime("%Y-%m-%d"),
                "license_type": terms.license_type
            }
        )

        logger.info("✅ 许可协议起草完成!")
        return result

    def _write_agreement(
        self,
        patent_id: str,
        licensor_info: dict[str, str],
        licensee_info: dict[str, str],
        terms,
        valuation,
        license_requirements: dict[str, Any]
    ) -> str:
        """撰写协议文本"""
        sections = []

        # 标题
        sections.append("# 专利许可协议\n")
        sections.append(f"**专利号**: {patent_id}\n")
        sections.append(f"**签署日期**: {datetime.now().strftime('%Y年%m月%d日')}\n\n")

        # 当事人
        sections.append("## 当事人\n")
        sections.append(f"**许可方（甲方）**: {licensor_info.get('name', '')}\n")
        sections.append(f"**地址**: {licensor_info.get('address', '')}\n")
        sections.append(f"**被许可方（乙方）**: {licensee_info.get('name', '')}\n")
        sections.append(f"**地址**: {licensee_info.get('address', '')}\n\n")

        # 鉴于条款
        sections.append("## 鉴于\n")
        sections.append(f"甲方是{patent_id}号专利的专利权人，\n")
        sections.append("乙方希望获得该专利的许可使用权。\n\n")

        # 许可条款
        sections.append("## 第一条 许可范围\n")
        sections.append(f"1.1 许可类型: {terms.license_type}\n")
        sections.append(f"1.2 许可地域: {license_requirements.get('scope', '中国境内')}\n")
        sections.append(f"1.3 许可期限: {license_requirements.get('duration', '5年')}\n\n")

        # 许可费用
        sections.append("## 第二条 许可费用\n")
        sections.append(f"2.1 提成率: {terms.royalty_rate:.1%}\n")
        sections.append(f"2.2 预付费用: {terms.upfront_fee:.1f}万元\n")
        sections.append(f"2.3 最低保证金: {terms.minimum_guarantee:.1f}万元\n")
        sections.append(f"2.4 支付方式: {terms.payment_terms}\n\n")

        # 权利义务
        sections.append("## 第三条 权利与义务\n")
        sections.append("### 3.1 甲方权利\n")
        for right in terms.rights:
            sections.append(f"- {right}\n")
        sections.append("\n### 3.2 乙方义务\n")
        for obligation in terms.obligations:
            sections.append(f"- {obligation}\n")
        sections.append("\n")

        # 限制条款
        sections.append("## 第四条 限制条款\n")
        for restriction in terms.restrictions:
            sections.append(f"{restriction}\n")
        sections.append("\n")

        # 终止条款
        sections.append("## 第五条 协议终止\n")
        for idx, condition in enumerate(terms.termination_conditions, 1):
            sections.append(f"5.{idx} {condition}\n")
        sections.append("\n")

        # 争议解决
        sections.append("## 第六条 争议解决\n")
        sections.append("6.1 本协议适用中华人民共和国法律。\n")
        sections.append("6.2 双方发生争议，应协商解决；协商不成的，提交甲方所在地法院诉讼解决。\n\n")

        # 签署
        sections.append("## 签署\n")
        sections.append("**甲方（盖章）**: _________________\n\n")
        sections.append("**乙方（盖章）**: _________________\n\n")
        sections.append("**日期**: _________________\n")

        return "\n".join(sections)


async def test_licensing_drafting():
    """测试许可协议起草"""
    drafting = LicensingDrafting()

    print("\n" + "="*80)
    print("🚀 许可协议起草测试")
    print("="*80)

    result = await drafting.draft_agreement(
        patent_id="CN123456789A",
        patent_info={
            "patent_type": "invention",
            "technology_field": "人工智能",
            "claims_count": 5
        },
        licensor_info={"name": "许可方科技公司", "address": "北京市"},
        licensee_info={"name": "被许可方制造公司", "address": "上海市"},
        license_requirements={
            "license_type": "non-exclusive",
            "scope": "中国境内",
            "duration": "5年"
        }
    )

    print("\n✅ 许可协议起草完成")
    print(f"许可类型: {result.terms['license_type']}")
    print(f"提成率: {result.terms['royalty_rate']:.1%}")

    print("\n协议文本（前300字）:")
    print(result.agreement_text[:300] + "...")

    print("\n" + "="*80)
    print("✅ 测试完成")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_licensing_drafting())
