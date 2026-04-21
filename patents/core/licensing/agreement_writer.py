#!/usr/bin/env python3
"""
许可协议主控制器

整合所有模块，提供完整的许可协议起草功能。
"""
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    from .patent_valuator import PatentValuator, ValuationResult
    from .clause_generator import ClauseGenerator, LicenseTerms
    from .agreement_writer import AgreementWriter
except ImportError:
    from patents.core.licensing.patent_valuator import PatentValuator, ValuationResult
    from patents.core.licensing.clause_generator import ClauseGenerator, LicenseTerms
    from patents.core.licensing.agreement_writer import AgreementWriter

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
    patent_valuation: Dict[str, Any]
    license_terms: Dict[str, Any]
    agreement_text: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "patent_id": self.patent_id,
            "licensor": self.licensor,
            "licensee": self.licensee,
            "patent_valuation": self.patent_valuation,
            "license_terms": self.license_terms,
            "agreement_text": self.agreement_text,
            "metadata": self.metadata
        }

    def save_to_file(self, file_path: str) -> None:
        """保存到文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self.agreement_text)


class LicensingDrafting:
    """许可协议起草主控制器"""

    def __init__(self):
        """初始化控制器"""
        self.valuator = PatentValuator()
        self.clause_generator = ClauseGenerator()
        self.agreement_writer = AgreementWriter()
        logger.info("✅ 许可协议起草主控制器初始化成功")

    async def draft_agreement(
        self,
        patent_id: str,
        patent_info: Dict[str, Any],
        licensor_info: Dict[str, str],
        licensee_info: Dict[str, str],
        license_requirements: Dict[str, Any],
        options: Optional[LicensingOptions] = None
    ) -> LicensingResult:
        """
        起草许可协议

        Args:
            patent_id: 专利号
            patent_info: 专利信息
            licensor_info: 许可方信息
            licensee_info: 被许可方信息
            license_requirements: 许可需求
            options: 起草选项

        Returns:
            LicensingResult对象
        """
        logger.info(f"📝 开始起草许可协议: {patent_id}")

        if options is None:
            options = LicensingOptions()

        try:
            # 步骤1: 专利估值
            logger.info("💰 步骤1: 专利估值")
            valuation = self.valuator.evaluate_patent(
                patent_id,
                patent_info,
                license_requirements.get("market_data")
            )

            # 步骤2: 生成条款
            logger.info("📋 步骤2: 生成许可条款")
            terms = self.clause_generator.generate_terms(
                valuation.to_dict(),
                license_requirements
            )

            # 步骤3: 撰写协议
            logger.info("✍️ 步骤3: 撰写许可协议")
            agreement_text = self.agreement_writer.write_agreement(
                patent_id,
                licensor_info,
                licensee_info,
                terms,
                valuation
            )

            # 组装结果
            result = LicensingResult(
                patent_id=patent_id,
                licensor=licensor_info.get("name", "许可方"),
                licensee=licensee_info.get("name", "被许可方"),
                patent_valuation=valuation.to_dict(),
                license_terms=terms.to_dict(),
                agreement_text=agreement_text,
                metadata={
                    "drafting_date": datetime.now().strftime("%Y-%m-%d"),
                    "license_type": terms.license_type,
                    "royalty_rate": terms.royalty_rate,
                    "upfront_fee": terms.upfront_fee
                }
            )

            logger.info("✅ 许可协议起草完成!")
            logger.info(f"   许可类型: {terms.license_type}")
            logger.info(f"   提成率: {terms.royalty_rate:.1%}")
            logger.info(f"   预付费用: {terms.upfront_fee:.1f}万元")

            return result

        except Exception as e:
            logger.error(f"❌ 许可协议起草失败: {e}")
            import traceback
            traceback.print_exc()
            raise


async def test_licensing_drafting():
    """测试许可协议起草"""
    drafting = LicensingDrafting()

    print("\n" + "="*80)
    print("🚀 许可协议起草测试")
    print("="*80)

    # 测试数据
    patent_id = "CN123456789A"
    patent_info = {
        "patent_type": "invention",
        "technology_field": "人工智能",
        "claims_count": 5,
        "title": "一种智能控制系统"
    }

    licensor_info = {
        "name": "许可方科技公司",
        "address": "北京市XXX区XXX路XXX号"
    }

    licensee_info = {
        "name": "被许可方制造公司",
        "address": "上海市XXX区XXX路XXX号"
    }

    license_requirements = {
        "license_type": "non-exclusive",
        "scope": "中国境内",
        "duration": "5年"
    }

    # 起草协议
    result = await drafting.draft_agreement(
        patent_id,
        patent_info,
        licensor_info,
        licensee_info,
        license_requirements
    )

    # 输出结果
    print(f"\n✅ 许可协议起草完成:\n")
    print(f"专利号: {result.patent_id}")
    print(f"许可方: {result.licensor}")
    print(f"被许可方: {result.licensee}")
    print(f"许可类型: {result.metadata['license_type']}")
    print(f"提成率: {result.metadata['royalty_rate']:.1%}")
    print(f"预付费用: {result.metadata['upfront_fee']:.1f}万元")

    print(f"\n协议文本（前500字）:")
    print(result.agreement_text[:500] + "...")

    # 保存到文件
    import tempfile
    output_file = tempfile.mktemp(suffix='_licensing_agreement.md')
    result.save_to_file(output_file)
    print(f"\n💾 协议已保存到: {output_file}")

    print("\n" + "="*80)
    print("✅ 测试完成")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_licensing_drafting())
