#!/usr/bin/env python3
"""
国际专利申请主控制器

整合所有模块，提供完整的国际专利申请支持。
"""
import asyncio
import logging
from typing import List, Dict, Any

try:
    from .pct_assistant import PCTAssistant, PCTApplication
    from .legal_adapter import LegalAdapter
    from .translation_assistant import TranslationAssistant
except ImportError:
    from core.patents.international.pct_assistant import PCTAssistant, PCTApplication
    from core.patents.international.legal_adapter import LegalAdapter
    from core.patents.international.translation_assistant import TranslationAssistant

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InternationalFilingManager:
    """国际专利申请管理器"""

    def __init__(self):
        """初始化管理器"""
        self.pct_assistant = PCTAssistant()
        self.legal_adapter = LegalAdapter()
        self.translation_assistant = TranslationAssistant()
        logger.info("✅ 国际专利申请管理器初始化成功")

    async def prepare_international_application(
        self,
        chinese_app: Dict[str, Any],
        target_countries: List[str],
        options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        准备国际专利申请

        Args:
            chinese_app: 中国专利申请信息
            target_countries: 目标国家列表
            options: 可选配置

        Returns:
            完整的国际申请方案
        """
        logger.info(f"🌍 准备国际申请: {chinese_app.get('patent_id')}")

        # 步骤1: 准备PCT申请
        pct_application = self.pct_assistant.prepare_pct_application(
            chinese_app,
            target_countries
        )

        # 步骤2: 获取各国法律信息
        country_info = {}
        for country in target_countries:
            info = self.legal_adapter.get_country_info(country)
            if info:
                country_info[country] = info.to_dict()

        # 步骤3: 对比法律差异
        comparison = self.legal_adapter.compare_countries(target_countries)

        # 步骤4: 准备翻译
        terms = ["权利要求", "说明书", "摘要", "发明", "申请人", "优先权"]
        target_langs = ["英语", "日语", "德语"]
        glossary = self.translation_assistant.get_translation_glossary(
            terms,
            target_langs
        )

        # 步骤5: 生成检查清单
        checklist = self.pct_assistant.generate_checklist(pct_application)

        return {
            "patent_id": chinese_app.get("patent_id"),
            "pct_application": pct_application.to_dict(),
            "country_info": country_info,
            "legal_comparison": comparison,
            "translation_glossary": glossary,
            "checklist": checklist,
            "summary": self._generate_summary(
                pct_application,
                target_countries,
                comparison
            )
        }

    def _generate_summary(
        self,
        pct_app: PCTApplication,
        countries: List[str],
        comparison: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成摘要"""
        return {
            "total_countries": len(countries),
            "grace_period_countries": comparison["grace_period_countries"],
            "recommended_route": "PCT" if len(countries) >= 3 else "巴黎公约",
            "estimated_cost": pct_app.metadata.get("estimated_fees", {}).get("total", 0),
            "timeline": "优先权日起12个月内提交PCT申请"
        }


async def test_international_filing_manager():
    """测试国际专利申请管理器"""
    manager = InternationalFilingManager()

    print("\n" + "="*80)
    print("🌍 国际专利申请管理器测试")
    print("="*80)

    # 测试数据
    chinese_app = {
        "patent_id": "CN202010123456.7",
        "title": "基于人工智能的智能控制系统",
        "applicant": "××科技公司",
        "inventor": "张三",
        "filing_date": "2025-04-15",
        "abstract": "本发明涉及一种基于深度学习的智能控制方法...",
        "claims": ["1. 一种智能控制方法..."],
        "description": "本发明提供了一种智能控制系统..."
    }

    target_countries = ["US", "EP", "JP"]

    # 准备国际申请
    result = await manager.prepare_international_application(
        chinese_app,
        target_countries
    )

    print(f"\n✅ 国际申请准备完成:")
    print(f"   专利号: {result['patent_id']}")
    print(f"   目标国家数: {result['summary']['total_countries']}")
    print(f"   推荐路线: {result['summary']['recommended_route']}")
    print(f"   预计费用: {result['summary']['estimated_cost']:.0f}元")

    print(f"\n   各国法律信息:")
    for country, info in result['country_info'].items():
        print(f"      {country}: {info['country_name']} - {info['language']}")

    print(f"\n   检查清单:")
    for item in result['checklist']['timeline'][:2]:
        print(f"      - {item}")

    print("\n" + "="*80)
    print("✅ 测试完成")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_international_filing_manager())
